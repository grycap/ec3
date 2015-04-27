#!/usr/bin/env python

# Experimental monitor

import time
import boto.ec2
from IM.auth import Authentication

try:
    import json
except ImportError:
    import simplejson as json

Control_ref = [None]

def get_price(s, auth):
    """Return price associated to the system."""

    region = s.getValue("disk.0.image.url").split('/')[2]
    instance_type = s.getValue("instance_type")
    availability_zone = s.getValue("availability_zone")

    auth_data = Authentication.read_auth_data(auth)
    for auth in auth_data:
        if auth["type"] == 'EC2':
            access_key = auth["username"]
            secret_key = auth["password"]
            break
    os.environ['AWS_ACCESS_KEY_ID'] = access_key
    os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key

    # Create the EC2 connection
    ec2 = boto.ec2.connect_to_region(region)

    history = ec2.get_spot_price_history(instance_type=instance_type, availability_zone=availability_zone, max_results=1)
    if history and history[0].price:
        return history[0].price
    return None

def on_new_iteration(old_func):
    # Temporally disable price information in spot instances
    #for v in Control_ref[0].vmids.values():
    #    if v.getValue("spot", "no") != "yes": continue
    #    v.setValue("price", get_price(v, Control_ref[0].AUTH))
    f = open('mon.txt', 'a')
    d = dict([ (a,str(b)) for a,b in Control_ref[0].vmids.items() ])
    d["time"] = time.time()
    f.write("$"*80 + "\n" + json.dumps(d) + "\n")
    f.close()
    old_func()

def ec3_init(Control):
    Control_ref[0] = Control
    old_on_new_iteration = Control.on_new_iteration
    Control.on_new_iteration = staticmethod(lambda: on_new_iteration(old_on_new_iteration))

if __name__ == "__main__":
    sys.exit(0)
