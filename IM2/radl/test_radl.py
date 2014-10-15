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

from radl_parse import parse_radl as parse_radl_text, dump_radl as dump_radl_text
from radl_json import parse_radl as parse_radl_json, dump_radl as dump_radl_json
from radl import (RADL, Features, Feature, RADLParseException, system, network,
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
		self.assertEqual(pub0.getValue("attr0"), "val0")
		self.assertEqual(pub0.getValue("attr1"), "val1")

	def test_system_merge1(self):

		radl = """
network public0 (outbound = 'yes' and attr0 = 'val0')
network public1 (outbound = 'yes' and attr0 = 'val1')
system s0 (
net_interface.0.connection = 'public0'
)
system s1 (
net_interface.0.connection = 'public1'
)		"""

		r = parse_radl_text(radl)
		self.radl_check(r)
		s0, s1 = r.get(system("s0")), r.get(system("s1"))
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

	def test_radl_concrete(self):

		radl = """
network public0 (outbound = 'yes' and attr0 = 'val0')
system s0 (
net_interface.0.connection = 'public0'
)		"""

		r = parse_radl_text(radl)
		self.radl_check(r)
		def f(p, v):
			def f0(r, t):
				self.assertIsNotNone(r.get(t))
				t = t.clone()
				t.setValue(p, v)
				return [RADL([t])]
			return f0
		def concrete(plan, **kwargs):
			c0 = r.concrete(plan, r.get(system("s0")), **kwargs)
			for r0 in c0:
				self.assertIsInstance(r0, RADL)
			return c0
		plan = ("or", f("p", 0), f("p", 1))
		c = concrete(plan)
		self.assertEqual(len(c), 2)
		self.assertItemsEqual(map(lambda x: x.get(system("s0")).getValue("p"), c), (0, 1))
		plan = ("and", f("p", 0), f("q", 1))
		c = concrete(plan)
		self.assertEqual(len(c), 1)
		c = c.pop()
		self.assertItemsEqual((c.get(system("s0")).getValue("p"), c.get(system("s0")).getValue("q")), (0, 1))
		fNone = lambda *_: []
		plan = ("xor", fNone, f("p", 0), f("p", 1))
		c = concrete(plan)
		self.assertEqual(len(c), 1)
		self.assertEqual(c.pop().get(system("s0")).getValue("p"), 0)
		plan = ("and", ("xor", fNone, ("or", f("p", 0), f("p", 1))), ("or", f("p", 0), f("p", 1)))
		c = concrete(plan)
		self.assertEqual(len(c), 2)
		plan = ("and", ("or", f("p", 0), f("p", 1)), ("or", f("q", 0), f("q", 1)))
		c = concrete(plan)
		self.assertEqual(len(c), 4)

	def test_radl_do(self):

		radl = """
network public0 (outbound = 'yes' and attr0 = 'val0')
system s0 (
net_interface.0.connection = 'public0'
)		"""

		r = parse_radl_text(radl)
		self.radl_check(r)
		def f(p, v):
			def f0(r, t):
				self.assertIsNotNone(r.get(t))
				self.assertIsNotNone(r.get(system("s0")).getValue("net_interface.0.connection"))
				return RADL([ system(t.getId(), [ Feature(p, "=", v) ]) ])
			return f0
		fNone = lambda *_: None
		def do(plan, **kwargs):
			r0 = r.do(plan, r.get(system("s0")), **kwargs)
			if r0 is not None: self.assertIsInstance(r0, RADL)
			return r0
		def undo(r0, plan, **kwargs):
			r0 = r0.do(plan, r0.get(system("s0")), reverse=True, **kwargs)
			self.assertIsInstance(r0, RADL)
			self.assertEqual(r.get(system("s0")), r0.get(system("s0")))
		plan = ("or", f("p", 0), f("p", 1))
		r0 = do(plan)
		self.assertEqual(r0.get(system("s0")).getValue("p"), 0)
		undo(r0, plan)
		plan = ("or", fNone, f("p", 1), f("p", 0))
		r0 = do(plan)
		self.assertEqual(r0.get(system("s0")).getValue("p"), 1)
		undo(r0, plan)
		plan = ("and", f("p", 0), f("q", 1))
		r0 = do(plan)
		self.assertEqual([r0.get(system("s0")).getValue(v) for v in ("p","q")], [0, 1])
		plan = ("and", f("p", 0), fNone, f("q", 1))
		self.assertIsNone(do(plan))
		plan = ("and", ("xor", fNone, ("or", f("p", 0), f("p", 1))), ("or", f("q", 0), f("q", 1)))
		r0 = do(plan)
		self.assertEqual([r0.get(system("s0")).getValue(v) for v in ("p","q")], [0, 0])
		undo(r0, plan)

	def test_radl_alternative(self):

		def do(i, t):
			"""
			If t is a system, return::
			  system( net = netork(netmock i, _mock0 = i), _mock0 = i )
			If t is a network, return::
			  network(netmock i, _mock0 = i)
			"""

			self.assertTrue(i is not None)
			self.assertIsInstance(t, (system, network))
			if t.getValue("_mock0", i) != i: return None
			netid = (t.getId() if isinstance(t, network) else 
			         t.getValue("net", network("netmock%d" % i)).getId())
			r0 = RADL([ network(netid, [ Feature("_mock0", "=", i),
			                             Feature("public", "=", ("no","yes")[i]) ]) ])
			if isinstance(t, network): return r0
			r0.add(system(t.getId(), [ Feature("_mock0", "=", i),
			                           Feature("net", "=", r0.get(network(netid))) ]))
			return r0
		def concrete(i):
			def concretef(_, t):
				r = do(i, t[1])
				return [] if r is None else [r]
			return concretef
		def alt(radl):
			"""
			Copy of RADLRequest.do, but failing in launching the
			second system with ``_mock0 = 0``. Systems and networks
			from _mock0 = 0 are better than _mock0 = 1.
			"""

			concretep = ("or", concrete(0), concrete(1))
			scoref = lambda r, a: (r.get(a).getValue("_mock0", 1e9), r)
			dos = {}
			bannings = []
			fail, ok, test0, first = False, False, False, True
			while True:
				r, aspects = radl.alternative(None, concretep, scoref, dos, bannings)
				if r is None: break
				if first:
					self.assertEqual(set([s.getValue("_mock0") for s in r.gets(system)]), set([0]))
					first = False
				self.assertTrue(len(set(radl.props.keys()) - (aspects | set(dos.keys()))) == 0)
				class MyExc(Exception): pass
				try:
					for a in aspects:
						if dos.get(a, RADL()).get(a) and dos[a].get(a).isMoreConcreteThan(r.get(a)):
							continue
						a = r.get(a)
						if isinstance(a, system) and a.getValue("_mock0") == 0:
							if fail:
								bannings.append((None,a))
								raise MyExc
							else: fail = True
						r0 = do(a.getValue("_mock0"), a)
						if not r0: raise Exception("Unexpected!")
						dos[a.getKey()] = r0
					ok = True
					break
				except MyExc:
					test0 = True
					pass
			self.assertTrue(ok)
			self.assertTrue(test0)
			radl0 = RADL()
			[ radl0.merge(r, missing="other", ifpresent="merge") for r in dos.values() ]
			return radl0

		# Test a fail in provider _mock0 = 0, resulting 1 system _mock0 = 0 and
		# 2 systems _mock0 = 1, because the three systems don't have to have a
		# network in common.
		radl = RADL([ system("s%d" % i) for i in range(3) ])
		radl0 = alt(radl)
		self.assertItemsEqual([s.getValue("_mock0") for s in radl0.gets(system)], [0,1,1])

		# Same test but three systems share a network, resulting all systems and the
		# network with _mock0 = 1
		net = network("net")
		radl = RADL([ system("s%d" % i, [ Feature("net", "=", net) ]) for i in range(3) ])
		radl0 = alt(radl)
		self.assertItemsEqual([s.getValue("_mock0") for s in radl0.gets(system)], [1]*3)
		self.assertItemsEqual([s.getValue("net").getValue("_mock0") for s in radl0.gets(system)], [1]*3)

if __name__ == "__main__":
	unittest.main()
