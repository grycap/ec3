#!/usr/bin/env python
# encoding: utf-8
'''
Helper file to download a new proxy file from a MyProxy server
'''
import sys

proxy_file = "/usr/local/ec3/proxy.pem"
auth_file = "/usr/local/ec3/auth.dat"
cadir = "/etc/grid-security/certificates"

if len(sys.argv) > 1:
	auth_file = sys.argv[1]
if len(sys.argv) > 2:
	proxy_file = sys.argv[2]
if len(sys.argv) > 3:
	cadir = sys.argv[3]

myproxyserver = None
myproxyuser = None
myproxypass = None
with open(auth_file) as fa:
	lines = fa.readlines()
	for line in lines:
		if len(line) > 0 and not line.startswith("#"):
			line = line.strip()
			if line.find("myproxyserver = ") != -1:
				proxy_found = True
				tokens = line.split(";")
				for token in tokens:
					key_value = token.split(" = ")
					value = key_value[1].strip().replace("\\n","\n")
					key = key_value[0].strip()
					
					if key == "myproxyserver":
						myproxyserver = value
					elif key == "myproxyuser":
						myproxyuser = value
					elif key == "myproxypass":
						myproxypass = value

if myproxyserver and myproxyuser and myproxypass:
	from myproxy.client import MyProxyClient
	myproxy = MyProxyClient(hostname=myproxyserver, caCertDir=cadir)
	credentials = myproxy.logon(myproxyuser, myproxypass)
	with open(proxy_file, "w") as fp: 
		for cred in credentials:
			fp.write(cred) 
