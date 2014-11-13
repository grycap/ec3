#!/usr/bin/env python

# Experimental control

import sys, logging, xmlrpclib, argparse, time, imp, threading, subprocess, socket
from IM.auth import Authentication
from IM.radl.radl_parse import parse_radl
from IM.radl.radl import RADL, system, configure, deploy

AUTH = LAUNCH_RADL = LIMITS = DESTROY_INTERVAL = DELAY = None
logger = None

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
            logger.exception()
            return None
        logger.debug("%s(%s) = %s" % (name, ", ".join(map(san, a) + map(lambda a,b: "%s=%s"%(a, san(b)), kw.items())), san(r)))
        return r
    def __getattr__(self, name):
        f = getattr(self.C, name)
        return (lambda *a,**kw: spy.log(f, name, self.exception_filter, *a, **kw)) if callable(f) else f
 
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
        r = {}; s = {}
        for v in Control.vmids.values():
            if v.getValue("ec3_meta_state") == "idle": r.setdefault(v.getValue("ec3_class", "wn"), [0])[0] -= 1
            if v.getValue("ec3_meta_state") == "busy": s.setdefault(v.getValue("ec3_class", "wn"), [0])[0] += 1
        def add_subs_upto(a, b, c): return a+c, b-c
        for c, n in Control.get_queued_jobs().items():
            c0 = c1 = "wn" if LAUNCH_RADL.get(system(c)) is None else c
            # Compensate an idle node with a job in the queue
            while c0 and n > 0:
                r.setdefault(c0, [0])[0], n = add_subs_upto(r.get(c0, [0])[0], n, min(-r.get(c0, [0])[0], n))
                c0 = LAUNCH_RADL.get(system(c0)).getValue("ec3_if_fail")
            # If there is too many of one class, it is launch as the class in `ec3_if_fail`
            while c1 and n > 0:
                m = LAUNCH_RADL.get(system(c1)).getValue("ec3_max_instances", -1)
                if m < 0: r.setdefault(c1, [0])[0] += n; break
                r.setdefault(c1, [0])[0], n = add_subs_upto(r.get(c1, [0])[0], n, min(m-s.get(c1, [0])[0], n))
                c1 = LAUNCH_RADL.get(system(c1)).getValue("ec3_if_fail")
        return dict([ (k,v[0]+s.get(k, [0])[0]) for k,v in r.items() ])

def get_vmid(vmid):
    success, info = IM_SERVER.GetVMInfo(0, str(vmid), AUTH)
    if not success or info.strip().startswith("Deleted VM") or info.strip().startswith("Invalid VM ID"):
        s0 = system("dummy")
        for h, v in Control.vmids.items():
            if v.getValue("ec3_vmid") == vmid:
                hostname = h; break
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
 
def make_decision(wn, n, r):
    STATES = frozenset(["pending", "running", "configured", "failed"])
    for v in Control.vmids.values():
        if v.getValue("ec3_meta_state") and v.getValue("state") in STATES and v.getValue("ec3_class") == wn: n -= 1
    if LIMITS[1] is not None: n = max(n, -LIMITS[1])
    if LIMITS[0] is not None: n = min(n, LIMITS[0])
    if n < 0: destroy(wn, -n); return
    candidates = [ h for h, v in Control.vmids.items() if v.getValue("ec3_meta_state") and v.getValue("state") not in STATES ]
    for hostname in candidates[0:n]:
        get_launch_radl(hostname, wn, r)
        Control.vmids[hostname].setValue("state", "pending")
        Control.vmids[hostname].setValue("ec3_class", wn)

def launch(r):
    if not str(r): return
    success, new_vmids = IM_SERVER.AddResource(0, str(r), AUTH)
    if not success: raise Exception("Error calling AddResource: %s" % new_vmids)
    for vmid in new_vmids: get_vmid(vmid)

def destroy(wn, n):
    # Disable idle nodes
    idle_hostnames = [ h for h,v in Control.vmids.items() if v.getValue("ec3_meta_state") == "idle" and
                                                             v.getValue("ec3_class") == wn ]
    some_change = False
    if DESTROY_INTERVAL:
        t0 = time.time()
        pair = lambda h: (int(Control.vmids[h].getValue("launch_time", 0) - t0) % DESTROY_INTERVAL, h)
        for t, hostname in sorted([ pair(hostname) for hostname in idle_hostnames ])[0:n]:
            if 10 < t and t < max(DELAY, 3*60):
                Control.disable_node(hostname); some_change = True
    else:
        for hostname in idle_hostnames[0:n]:
            Control.disable_node(hostname); some_change = True
    if some_change: update_meta_state()

def consistency():
    INCONSISTENT_STATES = (
        (frozenset(["configured"]), frozenset(["off"]), Control.enable_node),
        (frozenset(["off"]), frozenset(["idle", "busy"]), Control.disable_node),
        (frozenset(["pending", "running", "configured"]), frozenset(["idle-off"]), Control.remove_node)
        (frozenset(["failed"]), frozenset(["off", "idle", "idle-off", "busy"]), Control.remove_node))
    for hostname, v in Control.vmids.items():
        for states, meta_states, f in INCONSISTENT_STATES:
            if v.getValue("state", "off") in states and v.getValue("ec3_meta_state") in meta_states:
                f(hostname)

def loop_body():
    # Collect information about nodes
    get_vmids()
    update_meta_state()
    logger.debug("vmids = %s" % san(Control.vmids, 1000))

    # Take decision and apply correction
    r = RADL()
    for wn, new_nodes in Control.take_decision().items(): make_decision(wn, new_nodes, r)
    launch(r)
    consistency()

def loop_cmd(seconds, cmd):
    if isinstance(cmd, list): cmd = " ".join(cmd)
    while True:
        time0 = time.time()
        try:
            subprocess.check_call(cmd, shell=True)
        except Exception, e:
            logger.warning(str(e))
        time.sleep(max(seconds - (time.time() - time0), 0))

if __name__ == "__main__":
    def int_none(s):
        return None if s is None or s.lower() == "none" else int(s)
    def mins(s):
        try:
            g = [ g0.strip() for g0 in s.split(":") ]
            if len(g) == 1: return int(g[0])
            if len(g) == 2: return int(g[0])*60 + int(g[1])
            raise Exception
        except:
            raise Exception("Invalid time value; it should be <mins> or <hours>:<mins>")

    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--auth", dest="auth", nargs=1, type=argparse.FileType('r'), help="Authorization file")
    parser.add_argument("-r", "--radl", dest="radl", nargs=1, type=argparse.FileType('r'), help="RADL working nodes system content")
    parser.add_argument("-w", "--wrapper", dest="wrapper", nargs="+", type=argparse.FileType('r'), help="Python file to get queued jobs and nodes state")
    parser.add_argument("-l", "--log-file", dest="log_file", nargs=1, type=argparse.FileType('w'), default=[sys.stderr], help="Log output file")
    parser.add_argument("-ll", "--log-level", dest="log_level", nargs=1, type=int, default=[4], help="1: debug; 2: info; 3: warning; 4: error")
    parser.add_argument("-d", "--delay", dest="delay", nargs=1, type=int, default=[20], help="the cluster is checked every this number of seconds")
    parser.add_argument("-ld", "--limit-destroy", dest="limit_destroy", nargs=1, type=int_none, default=[None], help="maximum machines to destroy at once")
    parser.add_argument("-lc", "--limit-create", dest="limit_create", nargs=1, type=int_none, default=[None], help="maximum machines to launch at once")
    parser.add_argument("-di", "--destroy-interval", dest="destroy_interval", nargs=1, type=mins, default=[0],
                        help="destroy machines only when they are at the end of this interval")
    parser.add_argument("-c", "--command", dest="cmds", action="append", nargs="+", help="execute command frequently", default=[])
    parser.add_argument("-tc", "--timed-command", dest="timed_cmds", action="append", nargs="+", help="execute command every the number of seconds passed as the first item", default=[])
    options = parser.parse_args()

    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S',
                        stream=options.log_file[0], level=options.log_level[0]*10)
    logger = logging.getLogger('ec3-control')
    try:
        if not options.auth: raise Exception("option is not set")
        auth_content = options.auth[0].readlines()
        AUTH = Authentication.read_auth_data(auth_content)
    except Exception, e:
        logger.error("Error in -a/--auth: %s\n" % str(e))
        sys.exit(1)
    try:
        if not options.radl: raise Exception("option is not set")
        LAUNCH_RADL = parse_radl(options.radl[0].read())
    except Exception, e:
        logger.error("Error in -r/--radl: %s\n" % str(e))
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
    LIMITS = (options.limit_create[0], options.limit_destroy[0])
    DESTROY_INTERVAL = options.destroy_interval[0]
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
            try: loop_body()
            except: logger.exception("Exception in loop:")
            time.sleep(max(DELAY - (time.time() - time0), 0))
    except KeyboardInterrupt:
        logger.info("Program interrupted by the user.")
    sys.exit(0)
