# test_radl - Test for module ``radl``.
# Copyright (C) 2014 - GRyCAP - Universitat Politecnica de Valencia
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

from IM2.radl import parse_radl as parse_radl_text, dump_radl as dump_radl_text
from IM2.radl import parse_radl_json, dump_radl_json
from IM2.radl.radl import (RADL, Features, Feature, RADLParseException, system, network,
                           RADLConflict, deploy, configure, contextualize)
import unittest
from mock import Mock

class TestRADL(unittest.TestCase):
	def __init__(self, *args):
		unittest.TestCase.__init__(self, *args)

	def radl_check(self, radl, expected_lengths=None, check_output=True):
		def parse_dump_check(parse, dump):
			radl0 = parse(dump(radl))
			self.radl_check(radl0, expected_lengths, check_output=False)
			for a in radl.aspects:
				if not isinstance(a, deploy):
					self.assertEqual(a, radl0.get(a))
		self.assertIsInstance(radl, RADL)
		radl.check()
		if expected_lengths:
			lengths = [ len([ 0 for a in radl.aspects if isinstance(a, t) ])
			            for t in (network, system, deploy, configure, contextualize) ]
			self.assertEqual(lengths, expected_lengths)
		if check_output:
			parse_dump_check(parse_radl_text, dump_radl_text)
			parse_dump_check(parse_radl_json, dump_radl_json)

	def test_basic(self):

		radl = """
network publica (outbound = 'yes')
system cursoaws (
cpu.arch='x86_64' and
cpu.count>=1 and
memory.size>=512m and
net_interface.0.connection = 'publica' and
net_interface.0.dns_name = 'cursoaws' and
disk.0.os.name='linux' and
disk.0.os.flavour='ubuntu' and
disk.0.os.version='12.04' and
disk.0.applications contains (name='org.grycap.cursoaws') and
disk.0.os.credentials.public_key = 'alucloud00-keypair' and
disk.0.os.credentials.private_key = '-----BEGIN RSA PRIVATE KEY-----
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
-----END RSA PRIVATE KEY-----' and
escape_var = 'this is a \\'test\\'' and
soft 1 (
  cpu.count <= 10 and
  memory.size <= 1G and
  disk.0.os.flavour='ubuntu'
)
)

configure cursoaws (
@begin
---
  - vars:
    ak_00: BBBBBBBBBBBBBBB0AA
    sk_00: ffffffffffff23202m/Sfasf/Ahaspe70efsa
    PBS_SERVER_CONF: |
      create queue batch
      set queue batch queue_type = Execution
      set queue batch resources_default.nodes = 1
      set queue batch enabled = True
      set queue batch started = True
      set server default_queue = batch
    tasks:
    - name: Create user
      user: name=alucloud00 password=1234
    - shell: |
        for i in `seq 0 {{NNODES-1}}`; do
           item="{{VNODES_PREFIX}}${i}{{VNODES_SUFFIX}}";
           grep -q ${item} /etc/hosts || echo "127.0.0.1 ${item}.localdomain ${item}" >> /etc/hosts;
        done
      args:
        sudo: yes
@end
)

configure Ubuntu (
@begin
  TORQUE_PATH: /var/spool/torque
  MOM_SERVICE: torque-mom
@end
)

deploy cursoaws 1
		"""
		r = parse_radl_text(radl)
		self.radl_check(r, [1, 1, 1, 2, 0])
		s = r.get(system("cursoaws"))
		self.assertIsInstance(s, system)
		self.assertEqual(len(s.features), 13)
		self.assertEqual(s.getValue("disk.0.os.name"), "linux")

	def test_basic0(self):

		radl = """
network publica ( outbound = 'yes')
system main (
cpu.arch='x86_64' and
cpu.count>=1 and
memory.size>=512m and
net_interfaces.count = 1 and
net_interface.0.connection='publica' and
disk.0.os.name='linux' and
disk.0.os.flavour='ubuntu'
)
system wn (
cpu.arch='x86_64' and
cpu.count>=1 and
memory.size>=524288k and
disk.0.os.name='linux'
)		"""

		r = parse_radl_text(radl)
		self.radl_check(r, [1, 2, 0, 0, 0])
		s = r.get(system("main"))
		self.assertEqual(s.getValue("cpu.arch"), "x86_64")
		self.assertEqual(s.getValue("net_interface.0.connection").getId(), "publica")

	def test_check_features(self):

		def test(radl):
			with self.assertRaises(RADLParseException):
				parse_radl_text(radl).check()
		test(""" system main ( cpu.count>=1m ) """)
		test(""" system main ( cpu.count>=1q ) """)
		test(""" system main ( cpu.count='error' ) """)
		test(""" system main ( image_type>='error' ) """)
		test(""" system main ( cpu.count contains 1 ) """)
		test(""" system main ( disk.0.applications = (name='app') ) """)
		test(""" system main ( cpu.arch = 'error' ) """)

	def test_references(self):

		radl = """
network publica ( outbound = 'yes')
network ref_publica

system main (
net_interface.0.connection='publica' and
net_interface.1.connection='ref_publica'
)
system wn
contextualize (
system main configure recipe
system wn configure ref_recipe
) 

configure recipe (
@begin
---
  test: True
@end
)
configure ref_recipe
		"""

		r = parse_radl_text(radl)
		self.radl_check(r, [2, 2, 0, 2, 1])

	def test_logic0(self):

		f0 = Feature("prop", ">=", 0)
		f1 = Feature("prop", "<=", 5)
		self.assertEqual(Features._applyInter((None, None), (f0, None)), (f0, None))
		self.assertEqual(Features._applyInter((None, None), (None, f1)), (None, f1))

	def test_dup_features(self):

		radl = """
system main (
cpu.count>=1 and
cpu.count<=0
)		"""

		with self.assertRaises(RADLParseException) as ex:
			parse_radl_text(radl)
		self.assertEqual(ex.exception.line, 3)

		radl = """
system main (
cpu.count=1 and
cpu.count=2
)		"""

		with self.assertRaises(RADLParseException) as ex:
			parse_radl_text(radl)
		self.assertEqual(ex.exception.line, 3)

		radl = """
system main (
cpu.count>=1 and
cpu.count>=5 and
cpu.count>=0
)		"""

		parse_radl_text(radl)

		radl = """
system main (
cpu.count=1 and
cpu.count>=0
)		"""

		parse_radl_text(radl)

		radl = """
system main (
cpu.count>=1 and
cpu.count<=5
)		"""

		parse_radl_text(radl)

		radl = """
system main (
cpu.count>=5 and
cpu.count<=5
)		"""

		parse_radl_text(radl)

	def test_system_concrete(self):

		radl = """
system main (
cpu.arch='x86_64' and
cpu.count>=1 and
memory.size>=512m and
disk.0.os.name='linux' and
disk.0.os.flavour='ubuntu' and
soft 100 (
  cpu.arch='x86_64' and
  cpu.count>=2 and
  memory.size>=1G
) and
soft 101 (
  disk.0.os.flavour='ubuntu' and
  disk.0.os.version='12.04'
) and
soft 50 (
  disk.0.os.name='windows'
)
)
system wn (
cpu.arch='x86_64' and
cpu.count>=1 and
memory.size>=512m and
disk.0.os.name='linux'
)		"""

		r = parse_radl_text(radl)
		self.radl_check(r)
		s = r.get(system("main"))
		self.assertIsInstance(s, system)
		concrete_s, score = s.concrete()
		self.assertIsInstance(concrete_s, system)
		self.assertEqual(score, 201)

	def test_system_merge0(self):

		radl = """
network public0 (outbound = 'yes' and attr0 = 'val0')
network public1 (outbound = 'yes' and attr1 = 'val1')
system s0 (
net_interface.0.connection = 'public0'
)
system s1 (
net_interface.0.connection = 'public1'
)		"""

		r = parse_radl_text(radl)
		self.radl_check(r)
		s0, s1 = r.get(system("s0")), r.get(system("s1"))
		s0.merge(s1, missing="other")
		pub0 = s0.getValue("net_interface.0.connection")
		self.assertIsInstance(pub0, network)
		self.assertEqual(pub0.getValue("attr0", None), None)
		self.assertEqual(pub0.getValue("attr1"), "val1")

	def test_system_merge1(self):

		radl0 = """
network public0 (outbound = 'yes' and attr0 = 'val0')
system s0 (
net_interface.0.connection = 'public0'
)		"""
		radl1 = """
network public0 (outbound = 'yes' and attr0 = 'val1')
system s1 (
net_interface.0.connection = 'public0'
)		"""


		r0 = parse_radl_text(radl0)
		self.radl_check(r0)
		r1 = parse_radl_text(radl1)
		self.radl_check(r1)
		s0, s1 = r0.get(system("s0")), r1.get(system("s1"))
		with self.assertRaises(RADLConflict) as ex:
			s0.merge(s1, missing="other")
		self.assertEqual(ex.exception.f0.prop, "attr0")
		self.assertEqual(ex.exception.f0.value, "val0")
		self.assertEqual(ex.exception.f1.value, "val1")

	def test_features_hash(self):

		radl = """
network public0 (outbound = 'yes' and attr0 = 'val0')
system s0 (
price <= 5.0 and
net_interface.0.connection = 'public0'
)		"""

		r = parse_radl_text(radl)
		self.radl_check(r)
		def f(s, i):
			s = s.clone()
			s.setId(i)
		self.assertEqual(len(set([ f(r.get(system("s0")), i) for i in range(4) ])), 1)

	def test_contextualize_options(self):
		radl = """
system test (
	cpu.count>=1
)
deploy test 1
contextualize (
	option ansible_version <= '2.6.20'
)
			"""
		r = parse_radl_text(radl)
		r.check()
		self.assertEqual(len(r.get(contextualize()).options), 1)
		self.assertEqual(r.get(contextualize()).options['ansible_version'].getValue(), '2.6.20')
		self.assertEqual(r.get(contextualize()).options['ansible_version'].operator, '<=')

		radl_json = dump_radl_json(r)
		print(radl_json)
		r = parse_radl_json(radl_json)
		r.check()
		self.assertEqual(len(r.get(contextualize()).options), 1)
		self.assertEqual(r.get(contextualize()).options['ansible_version'].getValue(), '2.6.20')


if __name__ == "__main__":
	unittest.main()
