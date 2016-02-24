#!/usr/bin/env python
# encoding: utf-8
'''
Helper file to extract the proxy file from the IM auth data
'''
import sys

proxy_file = "/usr/local/ec3/proxy.pem"
auth_file = "/usr/local/ec3/auth.dat"

if len(sys.argv) > 1:
	auth_file = sys.argv[1]
if len(sys.argv) > 2:
	proxy_file = sys.argv[2]

proxy_found = False
new_auth_data = ""
with open(auth_file) as fa:
	lines = fa.readlines()
	for line in lines:
		if len(line) > 0 and not line.startswith("#"):
			line = line.strip()
			if line.find("proxy = ") != -1:
				proxy_found = True
				tokens = line.split(";")
				line = ""
				for token in tokens:
					key_value = token.split(" = ")
					value = key_value[1].strip().replace("\\n","\n")
					key = key_value[0].strip()
					
					if key == "proxy" and value.startswith("----"):
						with open(proxy_file, "w") as fp:
							fp.write(value)
						value = "file(%s)" % proxy_file
					
					if line:
						line += ";"
					line += key + " = " + value

			new_auth_data += line + "\n"

if proxy_found:
	with open(auth_file, "w") as fa:
		fa.write(new_auth_data)