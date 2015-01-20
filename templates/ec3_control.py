#!/usr/bin/env python

# Experimental control

import sys, logging, xmlrpclib, argparse, time, imp, threading, subprocess, socket
from IM.auth import Authentication
from IM.radl.radl_parse import parse_radl
from IM.radl.radl import RADL, system, configure, deploy

AUTH = LAUNCH_RADL = DELAY = None
logger = None
FAILED = {} # dict from ec3_class to tuple of freedom date and penalty time.

def san(v, maxlen=600):
    cut = lambda r: r if len(r) < maxlen else r[0:maxlen-6] + "..." + r[-3:-1]
    return (cut(v.decode("string_escape")) if isinstance(v, str) else
            "[%s]" % ", ".join(map(lambda s: san(s, maxlen), v)) if isinstance(v, (set, list, tuple)) else
            "{%s}" % ", ".join([ "%s: %s" % (a, san(b, maxlen)) for a,b in v.items() ]) if isinstance(v, dict) else
            cut(str(v)))

class spy(object):
    def __init__(self, C, exception_filter=()): self.C, self.exception_filter = C, exception_filter
    @staticmethod
    def log(f, name, exception_filter, *a, **kw):
        try:
            r = f(*a, **kw)
        except exception_filter:
            logger.exception("%s(%s)" % (name, ", ".join(map(san, a) + map(lambda (a,b): "%s=%s"%(a, san(b)), kw.items()))))
            return None
        logger.debug("%s(%s) = %s" % (name, ", ".join(map(san, a) + map(lambda (a,b): "%s=%s"%(a, san(b)), kw.items())), san(r)))
        return r
    def __getattr__(self, name):
        f = getattr(self.C, name)
        return (lambda *a,**kw: spy.log(f, name, self.exception_filter, *a, **kw)) if callable(f) else f
    def __call__(self, *a, **kw):
        assert callable(self.C)
        return spy.log(self.C, self.C.__name__, self.exception_filter, *a, **kw)
def spyd(x): return spy(x)
 
IM_SERVER = spy(xmlrpclib.ServerProxy("http://localhost:8899", allow_none=True))

class Control:
    """Singleton class with basic data and methods."""

    vmids = {} 
    """dict[hostname]: system"""

    get_meta_state = None
    """function(): return dict[hostname]: one of 'off', 'idle', 'idle-off', 'busy'."""
    get_queued_jobs = None
    """function(): return dict[system ID]: number of systems to deploy."""
    enable_node = None
    """function(host, wn): enable host in some class."""
    disable_node = None
    """function(host): disable host."""

    @staticmethod
    def remove_node(h):
        """function(host): shutdown host."""
        success, info = IM_SERVER.RemoveResource(0, str(Control.vmids[h].getValue("ec3_vmid")), AUTH)
        if not success: raise Exception("Error calling RemoveResource: %s" % info)
        get_vmid(Control.vmids[h].getValue("ec3_vmid"))

    @staticmethod
    def take_decision():
        # Nodes = Queued + Busy
        r = {}
        for v in Control.vmids.values():
            if v.getValue("ec3_meta_state") == "busy": r.setdefault(v.getValue("ec3_class", "wn"), [0])[0] += 1
            elif v.getValue("ec3_class"): r.setdefault(v.getValue("ec3_class"), [0])
        for c, n in Control.get_queued_jobs().items():
            r.setdefault("wn" if LAUNCH_RADL.get(system(c)) is None else c, [0])[0] += n
        for s in LAUNCH_RADL.systems:
            if s.getId() != "front": r.setdefault(s.getId(), [0])
        return dict([ (k,v[0]) for k,v in r.items() ])
        
def get_vmid(vmid):
    vmid = str(vmid) # IM bug: some IM calls return an integer as VM id
    success, info = IM_SERVER.GetVMInfo(0, vmid, AUTH)
    if not success or info.strip().startswith("Deleted VM") or info.strip().startswith("Invalid VM ID"):
        s0, hostname = system("dummy"), None
        for h, v in Control.vmids.items():
            if v.getValue("ec3_vmid") == vmid:
                hostname = h; break
        if not hostname: return
    else: 
        s0 = parse_radl(info).systems[0]
        hostname = s0.getValue("net_interface.0.dns_name")
        if not hostname:
            h, hs, _ = socket.gethostbyaddr(s0.getValue("net_interface.0.ip"))
            hostname = min(map(lambda x: (len(x), x), [h]+hs))[1]
        s0.setValue("ec3_vmid", vmid)
    s0.setValue("ec3_meta_state", Control.vmids.get(hostname, system("dummy")).getValue("ec3_meta_state"))
    Control.vmids[hostname] = s0

def get_vmids():
    success, s = IM_SERVER.GetInfrastructureInfo(0, AUTH)
    if not success: raise Exception("Error calling GetInfrastructureInfo: %s" % s)
    Control.vmids.clear()
    for vmid in s["vm_list"]: get_vmid(vmid)

def update_meta_state():
    for hostname, state in Control.get_meta_state().items():
        Control.vmids.setdefault(hostname, system("dummy")).setValue("ec3_meta_state", state)

def get_launch_radl(hostname, wn, r):
    template = LAUNCH_RADL.clone()
    for n in template.networks: r.add(n, ifpresent="ignore")
    c = template.get(configure(wn))
    c.name = hostname
    r.add(c)
    s = template.get(system(wn))
    s.name = hostname
    s.setValue("ec3_class", wn)
    s.setValue("net_interface.0.dns_name", hostname)
    r.add(s)
    r.add(deploy(hostname, 1))

def timeline(v):
    """ Return a value so that the less the more change to survive. """

    def time_up_to_deadline(v):
        if v.getValue("ec3_meta_state") in frozenset(["idle-off", "busy-off"]):
            return None   #NOTE: None <= anything
        if v.getValue("ec3_meta_state") != "idle":
            return 1e9
        if v.getValue("launch_time") and v.getValue("ec3_destroy_interval", 0) > 60:
            return int(v.getValue("launch_time") - time.time()) % int(v.getValue("ec3_destroy_interval"))
        return int(v.getValue("ec3_max_idle_time", 0) - time.time() + v.getValue("idle_time", time.time()))
    MSTATE = dict([ (a,b) for b,a in enumerate(("busy", "idle", "busy-off", "idle-off", "off")) ])
    STATE = dict([ (a,b) for b,a in enumerate(("configured", "running", "pending", "failed", "off")) ])
    return MSTATE[v.getValue("ec3_meta_state")], STATE.get(v.getValue("state"), 9), time_up_to_deadline(v)

def make_decision(wn, n, r, limits, force=False, create=True, destroy=True):
    card = {}
    for c in [ v.getValue("ec3_class") for v in Control.vmids.values() if v.getValue("ec3_class") in frozenset(wn) ]:
        card[c] = card.get(c, 0) + 1
    change = False
    nodes = [ (timeline(v), h, v) for h, v in Control.vmids.items() if v.getValue("ec3_class") in frozenset(wn) or
              (v.getValue("ec3_meta_state", "off") == "off" and v.getValue("state", "off") == "off") ]
    for t, h, v in sorted(nodes):
        if n > 0 and create:
            if (v.getValue("ec3_meta_state") in frozenset(["busy-off", "idle-off"]) or
                    (v.getValue("state") == "configured" and v.getValue("ec3_meta_state") == "off")):
                Control.enable_node(h); change = True
            elif v.getValue("state", "off") == "off":
                c = launch_radl(wn, h, r, card, limits)
                if c: card[c] = card.get(c, 0) + 1; limits[c][0] -= 1
        elif n < 1 and destroy:
            c = v.getValue("ec3_class")
            if (v.getValue("ec3_meta_state") in frozenset(["idle", "busy"]) and limits[c][1] > 0
                    and (force or t[2] >= LAUNCH_RADL.get(system(c)).getValue("ec3_destroy_safe", None))):
                Control.disable_node(h); limits[c][1] -= 1; change = True
            elif (v.getValue("ec3_meta_state") in frozenset(["idle-off", "off"]) and
                    v.getValue("state", "off") not in frozenset(["running", "pending", "off"]) and
                    int(LAUNCH_RADL.get(system(c)).getValue("ec3_min_instances", 0)) < card[c]):
                Control.remove_node(h); card[c] -= 1
        n -= 1
    if change: update_meta_state()

def launch_radl(wn, hostname, r, card, limits):
    for c in wn + [None]:
        if c: m = int(LAUNCH_RADL.get(system(c)).getValue("ec3_max_instances", -1))
        if c and (time.time() >= FAILED.get(c, (0,))[0]) and (m < 0 or card.get(c, 0) < m) and limits[c][0] > 0: break
    if not c: return None
    # Workaround IM bug: force to launch all systems of the same kind to identify clearly which class failed
    if not r.systems or r.systems[0].getValue("ec3_class") == c: get_launch_radl(hostname, c, r)
    Control.vmids[hostname].setValue("state", "pending")
    Control.vmids[hostname].setValue("ec3_class", c)
    return c

def launch(r):
    if not str(r): return
    success, new_vmids = IM_SERVER.AddResource(0, str(r), AUTH)
    if not success and (new_vmids.find("Error allocating a new virtual machine") >= 0 or
                        new_vmids.find("Some deploys did not proceed successfully") >= 0):
        for s in set([ s.getValue("ec3_class") for s in r.systems ]):
            penalty = min(FAILED.get(s, (None, DELAY))[1]*2, 1e7)
            FAILED[s] = (time.time()+penalty, penalty)
    if success:
        for s in set([ s.getValue("ec3_class") for s in r.systems ]):
            if s in FAILED: FAILED[s][1] = min(1, FAILED[s][1]/2)
        for vmid in new_vmids: get_vmid(vmid)

def toposort(classes):
    v, path = {}, {}
    for c in classes:
        path[c] = visited = []; n = 0
        while c and c not in visited:
            v[c] = max(v.get(c, n), n)
            visited.append(c)
            c, n = LAUNCH_RADL.get(system(c)).getValue("ec3_if_fail"), n+1
    return map(lambda k: path[k[1]], sorted([ (-v[c], c) for c in classes ]))

def loop_body():
    # Collect information about nodes
    get_vmids()
    update_meta_state()
    logger.debug("vmids = %s" % san(Control.vmids, 1000))

    # Failure control
    if any([ v.getId() == "front" and v.getValue("state") == "failed" for v in Control.vmids.values() ]):
        IM_SERVER.Reconfigure(0, "", AUTH); return
    for h, v in Control.vmids.items():
        if v.getValue("state") == "failed": Control.remove_node(h)

    # Compute limits on every class
    limits = dict([ (s.getId(), [s.getValue("ec3_max_creation", 1e7)*DELAY,
                                 s.getValue("ec3_max_remove", 1e7)*DELAY]) for s in LAUNCH_RADL.systems ])
    
    # Take decision and apply correction
    r = RADL()
    decision = Control.take_decision()
    for v in LAUNCH_RADL.systems:
        if v.getId() == "front": continue
        decision.setdefault(v.getId(), 0)
        make_decision([v.getId()], int(v.getValue("ec3_min_instances", 0)), r, limits, destroy=False)
        if int(v.getValue("ec3_max_instances", -1)) >= 0:
            make_decision([v.getId()], int(v.getValue("ec3_max_instances")), r, limits, force=True, create=False)
    for path in toposort(decision.keys()):
        decision_min = decision_max = 0
        for v in [ LAUNCH_RADL.get(system(c)) for c in path ]:
            decision_min += int(v.getValue("ec3_min_instances", 0))
            decision_max += int(v.getValue("ec3_max_instances")) if int(v.getValue("ec3_max_instances", -1)) >= 0 else 1e7
        make_decision(path, min(max(sum([ decision.get(c, 0) for c in path ]), decision_min), decision_max), r, limits)
    launch(r)

def loop_cmd(seconds, cmd):
    if isinstance(cmd, list): cmd = " ".join(cmd)
    while True:
        time0 = time.time()
        try:
            subprocess.check_call(cmd, shell=True)
        except Exception, e:
            logger.warning(str(e))
        time.sleep(max(seconds - (time.time() - time0), 0))

def update_files(auth_file, radl_file):
    AUTH = Authentication.read_auth_data(open(auth_file.name, "r").readlines())
    LAUNCH_RADL = parse_radl(open(radl_file.name, "r").read())
    return AUTH, LAUNCH_RADL

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--auth", dest="auth", nargs=1, type=argparse.FileType('r'), help="Authorization file")
    parser.add_argument("-r", "--radl", dest="radl", nargs=1, type=argparse.FileType('r'), help="RADL working nodes system content")
    parser.add_argument("-w", "--wrapper", dest="wrapper", nargs="+", type=argparse.FileType('r'), help="Python file to get queued jobs and nodes state")
    parser.add_argument("-l", "--log-file", dest="log_file", nargs=1, type=argparse.FileType('w'), default=[sys.stderr], help="Log output file")
    parser.add_argument("-ll", "--log-level", dest="log_level", nargs=1, type=int, default=[4], help="1: debug; 2: info; 3: warning; 4: error")
    parser.add_argument("-d", "--delay", dest="delay", nargs=1, type=int, default=[20], help="the cluster is checked every this number of seconds")
    parser.add_argument("-c", "--command", dest="cmds", action="append", nargs="+", help="execute command frequently", default=[])
    parser.add_argument("-tc", "--timed-command", dest="timed_cmds", action="append", nargs="+", help="execute command every the number of seconds passed as the first item", default=[])
    options = parser.parse_args()

    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S',
                        stream=options.log_file[0], level=options.log_level[0]*10)
    logger = logging.getLogger('ec3-control')
    if not options.auth:
        logger.error("Error in -a/--auth: option is not set")
        sys.exit(1)
    if not options.radl:
        logger.error("Error in -r/--radl: option is not set")
        sys.exit(1)
    description = [ d for d in imp.get_suffixes() if d[0] == ".py" ][0]
    for opt_wrapper in options.wrapper:
        try:
            imp.load_module("wrapper", opt_wrapper, opt_wrapper.name, description).ec3_init(Control)
        except Exception, e:
            logger.error("Error in -w/--wrapper in '%s': %s\n" % (opt_wrapper.name, str(e)))
            sys.exit(1)
    Control = spy(Control, (subprocess.CalledProcessError,))
    DELAY = options.delay[0]
    commands = [ (DELAY, c) for c in options.cmds ]
    try:
        for c in options.timed_cmds:
            if len(c) < 1: raise Exception("Please, two arguments at least")
            try: commands.append((int(c[0]), c[1:]))
            except: raise Exception("First argument should be a number!")
    except Exception, e:
        logger.error("Error in -tc/--timed-command: %s")
    for tc in commands:
        t = threading.Thread(target=loop_cmd, args=tc)
        t.daemon = True
        t.start()
    try:
        while True:
            time0 = time.time()
            logger.info("New iteration")
            try:
                AUTH, LAUNCH_RADL = update_files(options.auth[0], options.radl[0])
                loop_body()
            except:
                logger.exception("Exception in loop:")
            time.sleep(max(DELAY - (time.time() - time0), 0))
    except KeyboardInterrupt:
        logger.info("Program interrupted by the user.")
    sys.exit(0)
