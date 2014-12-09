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
	def read_auth_data(filename):
		"""
		Parser authentication tokens from a file or list of strings.

		Tokens are represented in string as a sequence of pairs separated by semicolon (;),
		where every pair is a key and its value separated by "\ =\ " (space, equal, space).
		Values can contain "=" and blank characters (neither at the beginning nor at the
		end, because they will be stripped). Also the string "\\n" is replaced by carriage
		returns in values.

		Strings or lines that start with "#" are ignored.

		Args:

		- filename(str or list): filename or list of str.

		Return: list of tokens.
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
				tokens = line.split(";")
				for token in tokens:
					key_value = token.split(" = ")
					if len(key_value) != 2:
						raise AuthenticationParserError(i)
					auth[key_value[0].strip()] = key_value[1].strip().replace("\\n","\n")
				res.append(auth)
		
		return res

	@staticmethod
	def dump(auth):
		"""
		Serialize an Authentication so that it can be read by 'read_auth_data' later.
		"""

		if isinstance(auth, Authentication):
			auth = auth.auth_list
		return [ " ; ".join([ "%s = %s" % (k, v.replace("\n", "\\n")) for k,v in a.items() ]) for a in auth ]

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
