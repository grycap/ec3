# IM - Infrastructure Manager
# Copyright (C) 2011 - GRyCAP - Universitat Politecnica de Valencia
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import subprocess


class AuthenticationParserError(Exception):
	"""
	Error while parsing a token.

	Args:
	   - line(int, optional): line where the error occurred.
	"""

	def __init__(self, line=-1):
		self.line = line
		Exception.__init__(self, "Error while parsing a token at line %d." % line)


class Authentication:
	"""
	Authentication parser and storage of tokens.

	A token is a dictionary with the keys:

	- id: ID used to refer the token.
	- type: service, one of InfrastructureManager, VMRC, OpenNebula, EC2, OpenStack, OCCI,
		  LibCloud and LibVirt.
	- username: username in the service; in EC2 and OpenStack it is the *Access Key ID*.
	- host(optional): access point of the provider
	  
	Args:

	- auth_data(list or Authentication): list of tokens or instance of this class.
	"""

	def __init__(self, auth_data):
		if isinstance(auth_data, Authentication):
			self.auth_list = auth_data.auth_list
		else:
			self.auth_list = auth_data
		
	def getAuthInfo(self, type):
		"""Return a list of tokens with a type."""

		return [ auth for auth in self.auth_list if auth['type'] == type ]
	
	def getAuthInfoByID(self, id):
		"""Return a list of tokens with a id."""

		return [ auth for auth in self.auth_list if auth['id'] == id ]

	def compare(self, other_auth, type):
		"""Return true if this instance has some token of a type equal to the passed tokens."""

		auth0 = other_auth.getAuthInfo(type)
		for token in self.getAuthInfo(type):
			for token0 in auth0:
				if token == token0:
					return True
		return False

	@staticmethod
	def split_line(line):
		"""
		Split line using ; as separator char
		considering single quotes as a way to delimit
		tokens. (in particular to enable using char ; inside a token)
		"""
		tokens = []
		token = ""
		in_qoutes = False
		in_dqoutes = False
		for char in line:
			if char == '"' and not in_qoutes:
				in_dqoutes = not in_dqoutes
			elif char == "'" and not in_dqoutes:
				in_qoutes = not in_qoutes
			elif char == ";" and not in_qoutes and not in_dqoutes:
				tokens.append(token)
				token = ""
			else:
				token += char
		# Add the last token
		if token.strip() != "":
			tokens.append(token)

		return tokens

	@staticmethod
	# fetch the output using the command
	def run_command(cmd):
		proc = subprocess.Popen(cmd.split(' '), stdout=subprocess.PIPE, 
												stderr=subprocess.PIPE)
		outs, errs = proc.communicate()
		if proc.returncode != 0:
			if errs == b'':
				errs = outs
			raise Exception("Failed to get auth value using command %s: %s" % (cmd, errs.decode('utf-8')))
		return outs.decode('utf-8').replace('\n', '')

	@staticmethod
	def read_auth_data(filename):
		"""
		Read a file to load the Authentication data.
		The file has the following format:

		id = one; type = OpenNebula; host = oneserver:2633; username = user; password = pass
		type = InfrastructureManager; username = user; password = 'pass;test'
		type = VMRC; host = http://server:8080/vmrc; username = user; password = "pass';test"
		id = ec2; type = EC2; username = ACCESS_KEY; password = SECRET_KEY
		id = oshost; type = OpenStack; host = oshost:8773; username = ACCESS_KEY; key = SECRET_KEY
		id = occi; type = OCCI; host = occiserver:4567; username = user; password = file(/tmp/filename)
		id = occi; type = OCCI; proxy = file(/tmp/proxy.pem)
		type = InfrastructureManager; token = command(oidc-token OIDC_ACCOUNT)

		Arguments:
		   - filename(str or list): The filename to read or list of auth lines

		Returns: a list with all the auth data
		"""
		if isinstance(filename, list):
			lines = filename
		else:
			auth_file = open(filename, 'r')
			lines = auth_file.readlines()
			auth_file.close()

		res = []

		i = 0
		for line in lines:
			i += 1
			line = line.strip()
			if len(line) > 0 and not line.startswith("#"):
				auth = {}
				tokens = Authentication.split_line(line)
				for token in tokens:
					key_value = token.split(" = ")
					if len(key_value) != 2:
						raise AuthenticationParserError(i)
					else:
						key = key_value[0].strip()
						value = key_value[1].strip().replace("\\n", "\n")

						# Enable to specify a commnad and set the contents of the output
						if value.startswith("command(") and value.endswith(")"):
							command = value[8:len(value) - 1]
							value = Authentication.run_command(command)

						# Enable to specify a filename and set the contents of
						# it
						if value.startswith("file(") and value.endswith(")"):
							filename = value[5:len(value) - 1]
							try:
								value_file = open(filename, 'r')
								value = value_file.read()
								value_file.close()
							except:
								pass
						auth[key] = value.strip().replace("\\n", "\n")
				res.append(auth)

		return res

	@staticmethod
	def dump(auth):
		"""
		Serialize an Authentication so that it can be read by 'read_auth_data' later.
		"""

		if isinstance(auth, Authentication):
			auth = auth.auth_list
		return [ " ; ".join([ "%s = %s" % (k, v.replace("\n", "\\n")) for k,v in a.items() ]) + "\n" for a in auth ]

	@staticmethod
	def normalize(auth0):
		"""
		Remove repeated entries.
		"""

		auth = auth0.auth_list if isinstance(auth0, Authentication) else auth0
		s, l = set(), []
		for i, a in enumerate(auth):
			if a in s:
				l.insert(0, i)
			else:
				s.add(a)
		for i in l: del auth[i]
		return auth0
