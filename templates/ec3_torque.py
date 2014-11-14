#!/usr/bin/env python

# Experimental control for TORQUE

import sys, subprocess, argparse, xml.etree.ElementTree as ET

def run_command(command):
    try:
        p=subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (out, err) = p.communicate()
        if p.returncode != 0:
            raise Exception("return code: %d\nError output: %s" % (p.returncode, err))
        return out
    except Exception, e:
        raise Exception("Error executing '%s': %s" % (" ".join(command), str(e)))

def get_queued_jobs():
    try:
        root = ET.fromstring(run_command(["qstat", "-x"]))
    except:
        return {"wn": 0}
    jobs = root.iter("job_state") if hasattr(root, "iter") else root.getiterator("job_state")
    return {"wn": len([ 0 for state in jobs if state.text.strip().upper()[0] == "Q" ]) }

def get_meta_state():
    root = ET.fromstring(run_command(["qnodes", "-x"]))
    STATES = { "free": "idle", "offline": "idle-off", "down": "off", "job-exclusive": "busy",
               "busy": "busy", "reserve": "busy" }
    PRIO = { "off": 2, "idle": 0, "idle-off": 1, "busy": 3 }
    def find_state(states):
        if not states: return "off"
        states = [ STATES.get(s.strip(), "off") for s in states ]
        return max([ (PRIO[s], s) for s in states ])[1]
    return dict([ (node.find("name").text, find_state(node.find("state").text.split(",")))
                  for node in root.findall("Node") ])

def disable_node(hostname):
    subprocess.check_call("qnodes -o %s" % hostname, shell=True)

def enable_node(hostname, _=None):
    subprocess.check_call("qnodes -c %s" % hostname, shell=True)

def remove_node(hostname, alsodo=None):
    if alsodo: alsodo(hostname)
    enable_node(hostname)

def ec3_init(Control):
    Control.get_meta_state = staticmethod(get_meta_state)
    Control.get_queued_jobs = staticmethod(get_queued_jobs)
    Control.enable_node = staticmethod(enable_node)
    Control.disable_node = staticmethod(disable_node)
    old_remove_node = Control.remove_node
    Control.remove_node = staticmethod(lambda h: remove_node(h, old_remove_node))
 
def get_queued_jobs_cmd(_):
    sys.stdout.write("%s\n" % get_queued_jobs())

def get_meta_state_cmd(_):
    meta = get_meta_state()
    sys.stdout.write("%s\n" % meta)

def enable_node_cmd(options):
    enable_node(options.hostname)

def disable_node_cmd(options):
    disable_node(options.hostname)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="subcommands", description="valid subcommands", help="additional help")
    parser0 = subparsers.add_parser("queued_jobs", help="return how many queued jobs there are")
    parser0.set_defaults(func=get_queued_jobs_cmd)
    parser0 = subparsers.add_parser("meta_state", help="return the state of the nodes")
    parser0.set_defaults(func=get_meta_state_cmd)
    parser0 = subparsers.add_parser("disable_node", help="disable a node")
    parser0.add_argument("hostname", help="node's hostname")
    parser0.set_defaults(func=disable_node_cmd)
    parser0 = subparsers.add_parser("enable_node", help="enable a node")
    parser0.add_argument("hostname", help="node's hostname")
    parser0.set_defaults(func=enable_node_cmd)
    options = parser.parse_args()
    try:
        options.func(options)
    except KeyboardInterrupt:
        sys.stderr.write("Program interrupted by the user.\n")
    sys.exit(0)
