#!/usr/bin/env python

# Experimental control

import sys, logging, xmlrpclib, argparse, time, imp
from IM.auth import Authentication
from IM.radl.radl_parse import parse_radl
from IM.radl.radl import RADL, system, configure, deploy

AUTH = LAUNCH_RADL = LIMITS = DESTROY_INTERVAL = DELAY = None
get_meta_state = get_queued_jobs = enable_node = disable_node = None
logger = None

IM_SERVER = xmlrpclib.ServerProxy("http://localhost:8899", allow_none=True)
    
# vmids: dict[str: hostname] = system
def get_vmids(vmids):
    success, s = IM_SERVER.GetInfrastructureInfo(0, AUTH)
    if not success: Exception("Error calling GetInfrastructureInfo: %s" % s)
    vmids.clear()
    for vmid in s["vm_list"]:
        get_vmid(vmids, vmid)

def get_vmid(vmids, vmid):
    success, info = IM_SERVER.GetVMInfo(0, vmid, AUTH)
    logger.info("GetVMInfo:\n%s" % info)
    if not success: Exception("Error calling GetVMInfo: %s" % info)
    if info.strip().startswith("Deleted VM"):
        s0 = system("dummy")
        for h, v in vmids.items():
            if v.getValue("ec3_vmid") == vmid:
                hostname = h; break
    else: 
        s0 = parse_radl(info).systems[0]
        hostname = s0.getValue("net_interface.0.dns_name")
        s0.setValue("ec3_vmid", vmid)
    s0.setValue("ec3_meta_state", vmids.get(hostname, system("dummy")).getValue("ec3_meta_state"))
    vmids[hostname] = s0
    logger.debug("set vmids[%s]=%s" % (hostname, s0))

def update_meta_state(vmids):
    for hostname, state in get_meta_state().items():
        vmids.setdefault(hostname, system("dummy")).setValue("ec3_meta_state", state)

def take_decision(vmids, queued_jobs):
    return queued_jobs - len([ 0 for v in vmids.values() if v.getValue("ec3_meta_state") == "idle" ])

def get_launch_radl(hostname, r):
    template = LAUNCH_RADL.clone()
    for n in template.networks: r.add(n, ifpresent="ignore")
    for s in template.systems:
        s.name = hostname
        if s.hasFeature("net_interface.0.dns_name"):
            s.setValue("net_interface.0.dns_name", hostname)
        r.add(s)
    for c in template.configures:
        c.name = hostname
        r.add(c)
    return r
        
def launch(vmids, n):
    candidates = []
    STATES = frozenset(["pending", "running", "configured"])
    for hostname, v in vmids.items():
        if not v.getValue("ec3_meta_state"): continue
        if v.getValue("state") in STATES: n -= 1
        else: candidates.append(hostname)
    if not candidates or n <= 0: return

    r = RADL()
    for hostname in candidates[0:n]:
        enable_node(hostname)
        get_launch_radl(hostname, r)
        r.add(deploy(hostname, 1))
    update_meta_state(vmids)
    logger.debug("AddResource: %s" % str(r))
    success, new_vmids = IM_SERVER.AddResource(0, str(r), AUTH)
    if not success: raise Exception("Error calling AddResource: %s" % new_vmids)
    for vmid in new_vmids:
        get_vmid(vmids, vmid)

def destroy(vmids, n):
    # Disable idle nodes
    idle_hostnames = [ hostname for hostname in vmids if vmids[hostname].getValue("ec3_meta_state") == "idle" ]
    some_change = False
    if DESTROY_INTERVAL:
        t0 = time.time()
        pair = lambda h: (int(vmids[h].getValue("launch_time", 0) - t0) % DESTROY_INTERVAL, h)
        for t, hostname in sorted([ pair(hostname) for hostname in idle_hostnames ])[0:n]:
            if 10 < t and t < max(DELAY, 3*60):
                disable_node(hostname); some_change = True
    else:
        for hostname in idle_hostnames[0:n]:
            disable_node(hostname); some_change = True
    if some_change: update_meta_state(vmids)

def consistency(vmids):
    def remove_resource(h):
        logger.info("Destroy %s" % h)
        success, info = IM_SERVER.RemoveResource(0, str(vmids[h].getValue("ec3_vmid")), AUTH)
        if not success: raise Exception("Error calling RemoveResource: %s" % info)
        get_vmid(vmids, vmids[h].getValue("ec3_vmid"))
    INCONSISTENT_STATES = (
        #(frozenset(["off", "pending", "running"]), frozenset(["idle", "busy"]), lambda h: disable_node(h)),
        (frozenset(["pending", "running", "configured"]), frozenset(["idle-off"]), remove_resource),
        (frozenset(["failed"]), frozenset(["off", "idle", "idle-off", "busy"]), remove_resource))
    for hostname, v in vmids.items():
        for states, meta_states, _ in INCONSISTENT_STATES:
            logger.debug("consistency %s %s %s" % (hostname, v.getValue("state") in states, v.getValue("ec3_meta_state") in meta_states))
            if v.getValue("state") in states and v.getValue("ec3_meta_state") in meta_states:
                get_vmid(vmids, v.getValue("ec3_vmid")); v = vmids[hostname]; break
        for states, meta_states, f in INCONSISTENT_STATES:
            if v.getValue("state") in states and v.getValue("ec3_meta_state") in meta_states:
                f(hostname)

def loop_body(vmids):
    # Collect information about jobs
    queued_jobs = get_queued_jobs()
    logger.debug("queued_jobs = %d" % queued_jobs)

    # Collect information about nodes
    update_meta_state(vmids)
    logger.debug("vmids = %s" % str(dict([ (h, v.__str__()) for h,v in vmids.items() ])))

    # Take decision
    new_nodes = take_decision(vmids, queued_jobs)
    new_nodes = max(new_nodes, -LIMITS[1]) if LIMITS[1] is not None else new_nodes
    new_nodes = min(new_nodes, LIMITS[0]) if LIMITS[0] is not None else new_nodes
    logger.debug("decision: %d launch/destroy" % new_nodes)

    # Apply correction
    if new_nodes > 0: launch(vmids, new_nodes)
    elif new_nodes < 0: destroy(vmids, -new_nodes)
    consistency(vmids)

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
    parser.add_argument("-w", "--wrapper", dest="wrapper", nargs=1, type=argparse.FileType('r'), help="Python file to get queued jobs and nodes state")
    parser.add_argument("-l", "--log-file", dest="log_file", nargs=1, type=argparse.FileType('w'), default=[sys.stderr], help="Log output file")
    parser.add_argument("-ll", "--log-level", dest="log_level", nargs=1, type=int, default=[4], help="1: debug; 2: info; 3: warning; 4: error")
    parser.add_argument("-d", "--delay", dest="delay", nargs=1, type=int, default=[20], help="the cluster is checked every this number of seconds")
    parser.add_argument("-ld", "--limit-destroy", dest="limit_destroy", nargs=1, type=int_none, default=[None], help="maximum machines to destroy at once")
    parser.add_argument("-lc", "--limit-create", dest="limit_create", nargs=1, type=int_none, default=[None], help="maximum machines to launch at once")
    parser.add_argument("-di", "--destroy-interval", dest="destroy_interval", nargs=1, type=mins, default=[0],
                        help="destroy machines only when they are at the end of this interval")
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
    try:
        if not options.wrapper: raise Exception("option is not set")
        description = [ d for d in imp.get_suffixes() if d[0] == ".py" ][0]
        wrapper = imp.load_module("wrapper", options.wrapper[0], options.wrapper[0].name, description)
        get_meta_state = wrapper.get_meta_state
        get_queued_jobs = wrapper.get_queued_jobs
        enable_node = wrapper.enable_node
        disable_node = wrapper.disable_node
    except Exception, e:
        logger.error("Error in -w/--wrapper: %s\n" % str(e))
        sys.exit(1)
    DELAY = options.delay[0]
    LIMITS = (options.limit_create[0], options.limit_destroy[0])
    DESTROY_INTERVAL = options.destroy_interval[0]
    try:
        vmids = {}
        while True:
            time0 = time.time()
            logger.info("New iteration")
            try:
                if not vmids:
                    get_vmids(vmids)
                loop_body(vmids)
            except:
                logger.exception("Exception in loop:")
            time.sleep(max(DELAY - (time.time() - time0), 0))
    except KeyboardInterrupt:
        logger.info("Program interrupted by the user.")
    sys.exit(0)
