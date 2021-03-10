# IM - Infrastructure Manager
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

import copy
import itertools
from collections import OrderedDict
try:
	from urlparse import urlparse
	le2 = lambda a,b: a <= b
except ImportError:
	from urllib.parse import urlparse
	le2 = lambda a,b: True if a is None else False if b is None else a <= b
import heapq as heap

def UnitToValue(unit):
	"""Return the value of an unit."""

	if not unit or unit.upper() in frozenset(["ECU", "GCEU", "HRZ"]):
		return 1
	unit = unit[0].upper()
	if unit == "K":
		return 1024
	if unit == "M":
		return 1024 * 1024
	if unit == "G":
		return 1024 * 1024 * 1024
	raise Exception("Not valid unit: '%s'" % unit)

class RADLParseException(Exception):
	"""Error parsing RADL document."""

	def __init__(self, msg="", line=None):
		if line:
			msg = "Line %d: %s" % (line, msg)
		self.line = line
		Exception.__init__(self, msg)

class RADLConflict(RADLParseException):
	"""Error adding features to RADL document."""

	def __init__(self, msg="", f0=None, f1=None):
		self.f0, self.f1 = f0, f1
		fs = []
		for fx in [f0, f1]:
			if not fx: continue
			elif isinstance(fx, tuple): fs.extend(fx)
			else: fs.append(fx)
		line = [ f.line for f in fs if hasattr(f, "line") ]
		line = line[0] if line else None
		def pp(a):
			return str([pp(b) for b in a]) if isinstance(a, tuple) else str(a)
		RADLParseException.__init__(self, "%s\nConflicting feature: %s and %s" % (msg,pp(f0),pp(f1)), line=line)

def _combinations(c):
	"""
	Return a sorted list of Cartesian products from weighted iterables.

	>>> _combinations(([(5, 'a'), (2, 'b')], [(4, 'A'), (3, 'B')]))
	[('b', 'B'), ('b', 'A'), ('a', 'B'), ('a', 'A')]

	Args.:
	- c(iterable of iterable)

	Return(iterable of iterable):
	"""

	if not c or not all(c): return
	def n(l):
		heap.heapify(l)
		while l:
			yield heap.heappop(l)
	c = [ n(i) for i in c ]
	try:
		combs = [ (0, tuple([ (next(i), i) for i in c ])) ]
	except StopIteration:
		return
	while combs:
		score0, c = heap.heappop(combs)
		# c: tuple([ ((score, value), iterator), ... ])
		#             [0][0]  [0][1], [1]
		yield [ i[0][1] for i in c ]
		n = len(c)
		c0 = zip(*[ tuple(itertools.tee(ci[1], n)) for ci in c ])
		for i, c0i in enumerate(c0):
			try:
				ci1 = next(c0i[i])
			except StopIteration:
				continue
			c1 = [ ((c[j][0] if j!=i else ci1), c0i[j]) for j in range(n) ]
			heap.heappush(combs, (ci1[0]-c[i][0][0]+score0, c1))


class Feature(object):
	"""
	Every property that can appear in the definitions of a ``network`` and ``system``.

	Args:
	- prop: feature name.
	- operator: ``<=``, ``=``, ``=>`` or ``contains``.
	- value: value associated to the feature.
	- unit: like ``K``, ``M`` and ``G``.
	- line: line number in the RADL document.
	"""

	def __init__(self, prop = None, operator = None, value = None, unit = '', line=None):
		self.prop = prop
		self.operator = operator
		self.value = value
		self.unit = unit
		self.line = line

	def __repr__(self):
		return "%s %s %s" % (self.prop, self.operator, repr(self.getValue()))

	def __eq__(self, other):
		return (isinstance(other, Feature) and self.prop == other.prop and
		        self.getValue() == other.getValue())

	def __ne__(self, other):
		return not Feature.__eq__(self, other)

	__cmp__ = None

	def __hash__(self):
		return hash((self.prop, self.getValue()))

	def clone(self):
		"""Return a copy of this feature."""

		return copy.deepcopy(self)

	def getValue(self, unit=None):
		"""
		Return the value of the feature.

		If the unit is specified and the feature has a unit, the value is converted

		Args:
		- unit(str,optional): A unit to convert the current feature value ('B','K','M','G') 
		"""

		if unit or self.unit:
			try:
				r = float(self.value * UnitToValue(self.unit)) / UnitToValue(unit)
			except Exception as e:
				raise RADLParseException(str(e), line=self.line)
			return int(round(r)) if isinstance(self.value, int) else r
		return self.value

	def _check(self, check, radl):
		"""
		Check type, operator and unit in a feature.

		Args:
		- check(tuple):
		   - v[0]: expected type of the feature value.
		   - v[1]: can be a list of possible values or a function to test the value or None.
		   - v[2] (optional): can be a list of possible units; if None or not set the
		     unit valid is none.
		- radl: second argument passed when calling v[1].
		"""

		# Check type
		if not isinstance(self.value, check[0]):
			raise RADLParseException("Invalid type on '%s': '%s'; expected %s, but %s" % (self.prop, str(self.value), str(check[0]), type(self.value)), line=self.line)
		# Check operator
		if isinstance(self.value, (str, Aspect)):
			if self.operator != "=" and self.operator != "contains":
				raise RADLParseException("Invalid operator; expected '=' or 'contains'",
				                         line=self.line)
		elif isinstance(self.value, (int, float)):
			if self.operator not in ["=", "<=", ">=", ">", "<"]:
				raise RADLParseException("Invalid operator; expected '=', '<=', " +
					 "'>=', '>' or '<'", line=self.line)
		elif isinstance(self.value, Features):
			if self.operator != "contains":
				raise RADLParseException(
					"Invalid operator; expected 'contains'", line=self.line)
		# Check value
		if isinstance(check[1], (set, frozenset, tuple, list)):
			if self.value.upper() not in check[1]:
				raise RADLParseException("Invalid value; expected one of %s" % check[1],
				                         line=self.line)
		elif callable(check[1]):
			if not check[1](self, radl):
				raise RADLParseException("Invalid value in property '%s': %s" % (self.prop, self.value), line=self.line)
		if isinstance(self.value, Aspect) and id(radl.get(self.value)) != id(self.value):
				raise RADLParseException("Object referenced is not in RADL in property '%s': %s, %s" % (self.prop, id(self.value), id(radl.get(self.value))), line=self.line)
			
		# Check unit
		if len(check) < 3 or check[2] == None:
			if self.unit:
				raise RADLParseException("Invalid unit; expected none", line=self.line)
		elif len(check) > 2 and check[2]:
			if self.unit is None:
				if self.unit not in check[2]:
					raise RADLParseException("Empty unit; expected some value", line=self.line)
			else:
				if self.unit.upper() not in check[2]:
					raise RADLParseException("Invalid unit; expected one of %s" % check[2], line=self.line)
		return True

class Features(object):
	"""
	Collects a group of features.
	"""

	def __init__(self, features=None):
		self.props = {}
		for f in (features if features else []):
			self.addFeature(f)

	@property
	def features(self):
		"""List of features."""

		r = []
		for p, inter in self.props.items():
			if isinstance(inter, tuple):
				if (inter[0] and inter[1] and inter[0].getValue() == inter[1].getValue() and
				    inter[0].operator == "=" and inter[1].operator == "="):
					r.append(inter[0])
				else:
					r.extend([f for f in inter if f])
			elif isinstance(inter, dict):
				r.extend(inter.values())
			elif isinstance(inter, (list, set)):
				r.extend(inter)
			else:
				r.append(inter)
		return r

	def __repr__(self):
		return "Features(%s)" % repr(self.features)
	
	def __eq__(self, other):
		return isinstance(other, Features) and not Features.diff(self, other)

	def __ne__(self, other):
		return not Features.__eq__(self, other)

	__cmp__ = None

	def __hash__(self):
		h = 0
		for p in sorted(self.props.keys()):
			inter = self.props[p]
			if isinstance(inter, dict):
				for p0 in sorted(inter.keys()):
					h = hash((h, inter[p0]))
			elif isinstance(inter, (list, set)):
				h = hash((h, tuple(sorted(map(hash, inter)))))
			else:
				h = hash((h, inter))
		return h

	def diff(self, other):
		"""
		Return features in ``self`` whose value is different in ``other``.
		"""

		assert isinstance(other, Features)
		diffs = []
		otherc = other.clone()
		for f in self.features:
			try:
				otherc.addFeature(f, conflict="error", missing="error")
			except RADLConflict:
				diffs.append(f)
		def diff0(f):
			if isinstance(f.value, Features) and f.prop in other.props:
				if f.operator == "=" or f.operator == "*=" or f.operator == ":=":
					return f.value.diff(other.props[f.prop].value)
				elif f.operator == "contains" and f.value.getKey() in other.props[f.prop]:
					return f.value.diff(other.props[f.prop][f.value.getKey()].value)
				elif f.operator == "contains" and f in other.props[f.prop]:
					l = list(other.props[f.prop])
					return f.value.diff(l[l.index(f)].value)
			return f.getValue()
		return [ Feature(f.prop, f.operator, diff0(f)) for f in diffs ]

	def isMoreConcreteThan(self, other):
		"""
		Return whether all ``other`` features are compatible with this.
		"""

		try:
			other.clone().merge(self, conflict="error", missing="error")
			return True
		except:
			return False

	def clone(self):
		"""Return a copy of this aspect."""

		return copy.deepcopy(self)

	def getId(self):
		return self.getValue("id") if self.getValue("id") else self.getValue("name")

	def getKey(self):
		return (str((self.getValue("class", self.__class__.__name__), self.getId()))
		        if self.getId() is not None else None)

	def addFeature(self, f, conflict="error", missing="other"):
		"""
		Add a feature.

		Args:

		- f(Feature): feature to add.
		- conflict(str): if a property hasn't compatible values/constrains, do:
		   - ``"error"``: raise exception.
		   - ``"ignore"``: go on.
		   - ``"me"``: keep the old value.
		   - ``"other"``: set the passed value.
		- missing(str): if a property has not been set yet, do:
		   - ``"error"``: raise exception.
		   - ``"ignore"``: do nothing.
		   - ``"other"``: set the passed value.
		"""

		OPTIONS_CONFLICT = ["error", "ignore", "me", "other"]
		OPTIONS_MISSING = ["error", "ignore", "other"]
		assert missing in OPTIONS_MISSING, "Invalid value in `missing`."
		assert conflict in OPTIONS_CONFLICT, "Invalid value in `conflict`."

		if f.prop not in self.props and missing == "error":
			raise RADLConflict("Property has not set.", f1=f)
		elif f.prop not in self.props and missing == "ignore":
			return
		
		if isinstance(f.value, int) or isinstance(f, float):
			if f.operator == "=":
				inter1 = (f, f)
			elif f.operator[0] == "<":
				inter1 = (None, f)
			elif f.operator[0] == ">":
				inter1 = (f, None)
			inter0 = self.props.get(f.prop, (None, None))
			try:
				self.props[f.prop] = Features._applyInter(inter0, inter1, conflict)
			except Exception as e:
				raise RADLConflict(str(e), f0=inter0, f1=f)
		elif isinstance(f, SoftFeatures):
			self.props.setdefault(f.prop, set()).add(f)
		elif f.operator == "contains":
			if hasattr(f.value, "getKey") and f.value.getKey() is not None:
				if f.value.getKey() in self.props.get(f.prop, {}):
					self.props[f.prop][f.value.getKey()].value.merge(f.value, conflict=conflict, missing=missing)
				else:
					self.props.setdefault(f.prop, {})[f.value.getKey()] = f
			elif isinstance(self.props.get(f.prop, set()), set):
				self.props.setdefault(f.prop, set()).add(f)
			else:
				raise RADLConflict("Conflict adding `%s` because `%s` is not a set, it is '%s'." % (f, f.prop, self.props[f.prop]))
		elif isinstance(f.value, Aspect):
			value0 = self.props.get(f.prop, None)
			if not value0 or not value0.value or value0.value.getId() != f.value.getId():
				self.props[f.prop] = f
			else:
				self.props[f.prop].value.merge(f.value, conflict=conflict, missing=missing)
		else:
			value0 = self.props.get(f.prop, None)
			if not value0 or (value0.value != f.value and
					(conflict == "other" or f.operator == ":=" or
					 (f.operator == "*=" and isinstance(f.value, str) and f.value.startswith(value0.value)))):
				self.props[f.prop] = f
				f.operator = "="
			elif value0.value != f.value and conflict == "error":
				raise RADLConflict("Conflict adding `%s` because `%s` is already set to `%s`." % (f, f.prop, value0.value), f0=value0, f1=f)

	def hasFeature(self, prop):
		"""Return if there is a property with that name."""

		return prop in self.props

	def getValue(self, prop, default=None, iftuple="error"):
		"""Return the value of feature with that name or ``default``."""

		def toVal(v):
			if isinstance(v, (int, float, str, Features)):
				return v
			elif isinstance(v, Feature):
				return toVal(v.value)
			raise Exception("Unexpected value.")
		f = self.props.get(prop, None)
		if not f:
			return default
		if isinstance(f, Feature):
			return f.getValue()
		if isinstance(f, tuple):
			if f[0] and f[1] and f[0].getValue() == f[1].getValue():
				return f[0].getValue()
			if iftuple == "default":
				return default
			raise Exception("Getting value from a property with a constrain")
		if isinstance(f, (list, set)):
			return [ toVal(v) for v in f ]
		if isinstance(f, dict):
			return [ toVal(v) for v in f.values() ]
		raise Exception("Getting value from a not simple property.")

	def getValues(self, prop):
		"""Return a list of pairs of values and score of feature with that name."""

		if self.getValue(prop):
			return [ (self.getValue(prop), None) ]
		return sorted([ (fs.getValue(prop), fs.soft) for fs in self.props.get(SoftFeatures.SOFT, [])
		                if fs.getValue(prop) ], reverse=True, key=lambda x: x[1])

	def setValue(self, prop, value, unit=None, operator="="):
		"""Set the value of feature with that name."""

		if isinstance(value, (int, float)):
			if prop in self.props:
				for i, j in [(0, 1), (1, 0)]:
					if self.props[prop][i] == None:
						self.props[prop] = (self.props[prop][j], self.props[prop][j])
				for v in self.props[prop]:
					v.value, v.unit = value, unit
			else:
				f = Feature(prop, "=", value, unit=unit)
				self.props[prop] = (f, f)
		else:
			self.props[prop] = Feature(prop, operator, value, unit=unit)

	def delValue(self, prop):
		"""Remove the feature with that name."""

		try:
			del self.props[prop]
		except:
			pass

	@staticmethod
	def _applyInter(finter0, finter1, conflict="ignore"):
		"""
		Return the restriction of first interval by the second.

		Args:

		- inter0, inter1 (tuple of Feature): intervals

		Return(tuple of Feature): the resulting interval
		- conflict(str): if a property hasn't compatible values/constrains, do:
		   - ``"error"``: raise exception.
		   - ``"ignore"``: return None.
		   - ``"me"``: return finter0.
		   - ``"other"``: return finter1.
		"""
		
		OPTIONS = ["error", "ignore", "me", "other"]
		assert conflict in OPTIONS, "Invalid value in `conflict`."

		# Compute the comparison of the interval extremes
		# Remember, None <= number and None <= None are True, but number <= None is False.
		inter0 = tuple([f.getValue() if f else None for f in finter0])
		inter1 = tuple([f.getValue() if f else None for f in finter1])
		le00 = le2(inter0[0], inter1[0])                      # finter0[0] <= finter1[0]
		le01 = inter1[1] == None or le2(inter0[0], inter1[1]) # finter0[0] <= finter1[1]
		le11 = inter1[1] == None or (inter0[1] != None and le2(inter0[1], inter1[1]))
		                                                      # finter0[1] <= finter1[1]
		ge00 = not le00 or inter0[0] == inter1[0]             # finter0[0] >= finter1[0]
		ge10 = inter0[1] == None or le2(inter1[0], inter0[1]) # finter0[1] >= finter1[0]

		# First interval is (  ), second interval is [  ]
		if le00 and ge10 and le11:                       # ( [ ) ] chain first-second
			return finter1[0], finter0[1]
		elif le00 and ge10 and not le11:                 # ( [ ] )  second is inside first
			return finter1
		elif ge00 and le01 and le11:                     # [ ( ) ] first is inside second
			return finter0
		elif ge00 and le01 and not le11:                 # [ ( ] ) chain second-first
			return finter0[0], finter1[1]
		elif conflict == "me":
			return finter0
		elif conflict == "other":
			return finter1
		elif conflict == "error":
			raise Exception("Disjoint intervals!")
		return None
		
	def merge(self, other, conflict="error", missing="error"):
		"""
		Add the features in other to this.

		.. warning::
		   Feature instances are only considered, that is, SoftFeatures will be
		   not considered.

		Args:

		- other(Features or list of Feature): features to add
		- conflict(str): if a property hasn't compatible values/constrains, do:
		   - ``"error"``: raise exception.
		   - ``"ignore"``: nothing.
		   - ``"me"``: preserve the original value.
		   - ``"other"``: set like the passed feature.
		- missing(str): if a property is missing in some side, do:
		   - ``"error"``: raise exception.
		   - ``"ignore"``: nothing.
		   - ``"me"``: preserve the original value.
		   - ``"other"``: set like the passed feature.
		"""

		OPTIONS = ["error", "ignore", "me", "other"]
		assert missing in OPTIONS, "Invalid value in `missing`."
		assert conflict in OPTIONS, "Invalid value in `conflict`."

		for self0 in (self.clone(), self):
			for f in (other.features if isinstance(other, Features) else other):
				self0.addFeature(f.clone(), conflict=conflict, missing=missing)
		return self

	def check_simple(self, checks, radl):
		"""Check types, operators and units in simple features."""

		for f in self.features:
			if not isinstance(f, Feature) or f.prop not in checks: continue
			f._check(checks[f.prop], radl)

	def check_num(self, checks, radl):
		"""
		Check types, operators and units in features with numbers.
		
		Args:

		- checks(dict of dict of str:tuples): keys are property name prefixes, and the
		  values are dict with keys are property name suffixes and values are iterable
		  as in ``_check_feature``.
		- radl: passed to ``_check_feature``.
		"""
	
		prefixes = {}
		for f in self.features:
			if not isinstance(f, Feature): continue
			(prefix, sep, tail) = f.prop.partition(".")
			if not sep or prefix not in checks: continue
			checks0 = checks[prefix]
			(num, sep, suffix) = tail.partition(".")
			try:
				num = int(num)
			except:
				raise RADLParseException(
					"Invalid property name; expected an index.", line=f.line)
			if not sep or suffix not in checks0: continue
			f._check(checks0[suffix], radl)
			if prefix not in prefixes: prefixes[prefix] = set()
			prefixes[prefix].add(num)

		# Check consecutive indices for num properties.
		for prefix, nums in prefixes.items():
			if min(nums) != 0 or max(nums) != len(nums)-1:
				raise RADLParseException(
					"Invalid indices values in properties '%s'" % prefix)

		return prefixes

	def alternatives(self, other=None):
		"""
		Return a list of possible aspects sorted by its score.

		Args:

		- other(Featues, optional): aspect to apply just before soft features.

		Return(tuple): tuple of the resulting system and its score.
		"""

		new_system = self.clone().merge(other, missing="other") if other else self
		soft_features = sorted(self.getValue(SoftFeatures.SOFT, []), key=lambda f: f.soft, reverse=True)
		masks = itertools.product([True, False], repeat=len(soft_features))
		for mask in masks:
			try:
				new_system0 = new_system.clone()
				[ new_system0.merge(fs, missing="other")
				  for m, fs in zip(mask, soft_features) if m ]
			except RADLConflict:
				pass
			else:
				yield new_system0

class Aspect:
	"""Element in a RADL, like a network, system, deploy, configure or contextualize."""

	def getId(self):
		"""Return the id of the aspect."""
		return id(self)

	def setId(self, name):
		"""Set a new id for the aspect."""
		raise NotImplementedError( "Should have implemented this" )

	def getKey(self):
		"""Return an id valid in a RADL."""
		return str((self.__class__.__name__, self.getId()))

	def merge(self, aspect, **kargs):
		"""Append features from the passed aspect."""
		raise NotImplementedError( "Should have implemented this" )

	@staticmethod
	def join(aspect0, aspect1, iferror="error", **kargs):
		"""Return a merge of both aspects."""

		aspect0 = aspect0.clone()
		try:
			aspect0.merge(aspect1, **kargs)
		except RADLConflict as e:
			if iferror == "error":
				raise e
			else:
				return None
		return aspect0

	def diff(self, other):
		"""Return parts of this aspect that are not in the other."""
		raise NotImplementedError( "Should have implemented this" )

	def check(self, radl):
		"""Check the aspect."""
		return True

	def clone(self):
		"""Return a copy of this aspect."""
		return copy.deepcopy(self)

	def __eq__(self, other):
		"""Return parts of this aspect that are not in the other."""
		raise NotImplementedError( "Should have implemented this" )

	def __ne__(self, other):
		#NOTE: Force operator '!=' be consistent to '=='
		return not self.__eq__(other)

	reference = False
	"""Whether it is a reference for an aspect already defined."""

	__cmp__ = None

def FrozenAspect(aspect):
	"""Return a read-only aspect."""

	assert isinstance(aspect, Aspect)
	aspect = aspect.clone()
	def ReadOnly(*_, **__):
		raise NotImplementedError("Method not available.")
	aspect.setId = aspect.merge = ReadOnly
	return aspect

class contextualize_item:
	"""Store a line under ``contextualize`` RADL keyword."""
	def __init__(self, system_id, configure_id, num=0, line=None):
		self.system = system_id
		"""System id."""
		self.configure = configure_id
		"""Configure id."""
		self.num = num
		"""Num of steps (optional)."""
		self.line = line
		
	def getId(self):
		"""Return an unique key for this element."""

		return (self.system, self.configure, self.num)

	def check(self, radl):
		"""Check a line under a contextualize."""

		if not radl.get(system(self.system)):
			raise RADLParseException("Invalid system id '%s'" % self.system, line=self.line)
		if not radl.get(configure(self.configure)):
			raise RADLParseException("Invalid configure id '%s'" % self.configure, line=self.line)

	def __hash__(self):
		return hash((self.system, self.configure, self.num))

	def __eq__(self, other):
		return (other is not None and self.system == other.system and
		        self.configure == other.configure and self.num == other.num)


class contextualize(Aspect, object):
	"""Store a ``contextualize`` RADL keyword."""
	def __init__(self, items=None, max_time=0, options=None, line=None):
		self.max_time = max_time
		"""Maximum time."""
		self.items = {}
		"""List of contextualize_item."""
		self.options = None
		""""List of contextualization options"""
		if not items:
			pass
		elif isinstance(items, list):
			self.items = dict([(c.getId(), c) for c in items])
		elif isinstance(items, dict):
			self.items = items
		else:
			raise ValueError("Unexpected type for 'items'.")

		if isinstance(options, list):
			self.options = dict([(o.prop, o) for o in options])
		elif isinstance(options, dict):
			self.options = options
		elif options is not None:
			raise ValueError("Unexpected type for 'options'.")

		self.line = line

	def getId(self):
		#NOTE: only once in a RADL.
		return "contextualize"

	def __hash__(self):
		hash_elems = [ hash(self.items[k]) for k in sorted(self.items.keys()) ]
		hash_elems.extend([ hash(self.options[k]) for k in sorted(self.options.keys()) ])
		return hash(tuple(hash_elems))

	def __eq__(self, other):
		return other is not None and self.items == other.items and self.options == other.options

	def diff(self, other):
		assert isinstance(other, contextualize)
		items = set(self.items.values()).difference(set(other.items.values()))
		options = set(self.options.values()).difference(set(other.options.values()))
		return contextualize(items, options=options)

	def __len__(self):
		return len(self.items) + len(self.options)

	def merge(self, cont, **kargs):
		"""Update this instance with the contextualize passed."""

		self.max_time = max(self.max_time, cont.max_time)
		self.items.update(cont.items)
		self.options.update(cont.options)

	def check(self, radl):
		"""Check a contextualize."""

		if not isinstance(self.max_time, int) or self.max_time < 0:
			raise RADLParseException("Invalid 'max time' in 'contextualize'",
			                         line=self.line)
		for i in self.items.values():
			i.check(radl)
		
class configure(Aspect):
	"""Store a RADL ``configure``."""

	def __init__(self, name, recipe="", reference=False, line=None):
		self.recipe = recipe
		"""Recipe content."""
		self.name = name
		"""Configure id."""
		self.reference = reference
		"""True if it is only a reference and it isn't a definition."""
		self.line = line

	def getId(self):
		return self.name

	def setId(self, name):
		self.name = name

	def getKey(self):
		return "configure", self.name

	def __eq__(self, other):
		return other is not None and self.recipe == other.recipe

	def __hash__(self):
		return configure._hash_yaml(self.recipe)

	def __repr__(self):
		return ("configure(%s, %s)" % (self.name, self.recipe) if not self.reference
		        else "configure(%s, reference=True)" % self.name)

	@staticmethod
	def _hash_yaml(obj):
		if isinstance(obj, dict):
			return reduce(lambda h, p: hash((h, p, configure._hash_yaml(obj[p]))),
			              sorted(obj.keys()), 0)
		elif isinstance(obj, list):
			return reduce(lambda h, p: hash((h, configure._hash_yaml(p))), obj, 0)
		else:
			return hash(obj)

	def merge(self, other, conflict="error", missing="other"):
		OPTIONS_CONFLICT = ["error", "ignore", "me", "other"]
		OPTIONS_MISSING = ["error", "ignore", "other"]
		assert missing in OPTIONS_MISSING, "Invalid value in `missing`."
		assert conflict in OPTIONS_CONFLICT, "Invalid value in `conflict`."

		self.recipe = copy.deepcopy(configure._merge_yaml(self.recipe, other.recipe, conflict, missing))

	@staticmethod
	def _merge_yaml(me, other, conflict="error", missing="other"):
		def resolv(meother=lambda x,_:x):
			if conflict == "error":
				raise RADLConflict("Conflict merging '%s' and '%s'." % (me, other))
			if conflict == "ignore": return me
			return meother(me, other) if conflict == "me" else meother(other, me)
		if me == other: return me
		if not any([ isinstance(me, t) and isinstance(other, t) for t in (list, dict) ]):
			return resolv()
		if isinstance(me, list): return resolv(lambda x,y: y+x)
		if missing == "error":
			for p in other.keys():
				if not p in me: raise RADLConflict("Key '%s' not in '%s'" % (p, me))
		r = dict(other) if missing == "other" else {}
		r.update([ (p, configure._merge_yaml(v, other[p], conflict, missing))
                           if p in other else (p, v) for p,v in me.items() ])
		return r
	
	def check(self, _):
		"""Check this configure."""

		return True

class deploy(Aspect):
	"""Store a RADL ``deploy``."""

	def __init__(self, id, vm_number, cloud_id=None, line=None):
		self.id = id
		"""System id."""
		self.vm_number = vm_number
		"""Number of virtual machines to deploy."""
		self.cloud_id = cloud_id
		"""Cloud provider id."""
		self.line = line
		
	def __eq__(self, other):
		return id(self) == id(other)

	def __hash__(self):
		return id(self)

	def merge(self, aspect, **kargs):
		if self != aspect:
			raise Exception("Don't do this!")

	def check(self, radl):
		"""Check this deploy."""

		if not radl.get(system(self.id)):
			raise RADLParseException("Invalid system id in the deploy.", line=self.line)

		if self.vm_number < 0:
			raise RADLParseException("Invalid number of virtual machines to deploy.",
			                         line=self.line)

class FeaturedAspect(Features, Aspect):
	"""Aspect with features."""

	def __init__(self, id, features=None, reference=False, line=None):
		self.id = id
		"""Aspect id."""
		self.reference = reference
		"""True if it is only a reference and it isn't a definition."""
		Features.__init__(self, features)
		self.line = line

	def getId(self):
		return self.id

	def setId(self, id):
		self.id = id

	def __eq__(self, other):
		return isinstance(other, type(self)) and Features.__eq__(self, other)

	def diff(self, other):
		assert isinstance(other, type(self))
		return type(self)(self.id, Features.diff(self, other))

	def __repr__(self):
		return "{cls}({id}, {fs}, reference={r}, line={l})".format(
			cls=type(self).__name__, id=self.id, fs=self.features, r=self.reference, l=self.line)

	def __str__(self):
		return repr(self)

class outport():
	"""Store OutPorts data"""

	def __init__(self, port_init, port_end, protocol, range=False):
		self.port_init = int(port_init)
		self.port_end = int(port_end)
		self.protocol = protocol
		self.range = range

	def __eq__(self, other):
		return (self.port_init == other.port_init and self.port_end == other.port_end
				and self.protocol == other.protocol and self.range == other.range)

	def __str__(self):
		if self.is_range:
			return "%d:%d/%s" % (self.port_init, self.port_end, self.protocol)
		else:
			return "%d-%d/%s" % (self.port_init, self.port_end, self.protocol)

	def is_range(self):
		return self.range
	
	def get_port_init(self):
		return self.port_init

	def get_port_end(self):
		return self.port_end

	def get_local_port(self):
		return self.port_end

	def get_remote_port(self):
		return self.port_init

	def get_protocol(self):
		return self.protocol

	@staticmethod
	def parseOutPorts(outports):
		"""
		Parse the outports string
		Valid formats:
		8899/tcp-8899/tcp,22/tcp-22/tcp
		8899/tcp-8899,22/tcp-22
		8899-8899,22-22
		8899/tcp,22/udp
		8899,22
		1:10/tcp,9:22/udp
		1:10,9:22
		Returns a list of outport objects
		"""
		res = []
		ports = outports.split(',')
		for port in ports:
			if port.find('-') != -1 and port.find(':') != -1:
				raise RADLParseException('Port range (:) and port mapping (-) cannot be combined.')
			if port.find(':') != -1:
				parts = port.split(':')
				range_init = parts[0]
				range_end = parts[1]
				range_end_parts = range_end.split("/")
				if len(range_end_parts) > 1:
					protocol = range_end_parts[1]
					range_end = range_end_parts[0]
				else:
					protocol = "tcp"
				res.append(outport(range_init, range_end, protocol, True))
			else:
				parts = port.split('-')
				remote_port = parts[0]
				if len(parts) > 1:
					local_port = parts[1]
				else:
					local_port = remote_port
	
				local_port_parts = local_port.split("/")
				if len(local_port_parts) > 1:
					local_protocol = local_port_parts[1]
					local_port = local_port_parts[0]
				else:
					local_protocol = "tcp"
			
				remote_port_parts = remote_port.split("/")	
				if len(remote_port_parts) > 1:
					remote_protocol = remote_port_parts[1]
					remote_port = remote_port_parts[0]
				else:
					remote_protocol = "tcp"

				if remote_protocol != local_protocol:
					raise RADLParseException("Different protocols used in local and remote outports.")

				res.append(outport(remote_port, local_port, local_protocol))
		return res

class network(FeaturedAspect):
	"""Store a RADL ``network``."""

	def check(self, radl):
		"""Check the features in this network."""

		SIMPLE_FEATURES = {
			"outbound": (str, ["YES", "NO"])
		}
		self.check_simple(SIMPLE_FEATURES, radl)

	def isPublic(self):
		"""Return true if outbound = yes."""
		return self.getValue("outbound") == "yes"

	def getOutPorts(self):
		"""
		Get the outports of this network.
		outports format: 22/tcp-22/tcp,8899/tcp,8800
		Returns a list of outport objects
		"""
		outports = self.getValue("outports")
		if outports:
			return outport.parseOutPorts(outports)
		else:
			return None

class FeaturesApp(Features):
	"""Store an RADL application."""

	def __init__(self, features):
		Features.__init__(self, features)

	def check(self, radl):
		"""Check the features in this application."""

		def is_version(version, _):
			if version.value == "":
				return True
			else:
				return all([num.isdigit() for num in version.value.split(".")])

		SIMPLE_FEATURES = {
			"name": (str, True),
			"path": (str, True),
			"version": (str, is_version),
			"preinstalled": (str, ["YES", "NO"])
		}
		self.check_simple(SIMPLE_FEATURES, radl)

class _system(Features):
	"""
	Store a RADL ``system``.

	Basic features:
	- ``auth`` contains Authentication attributes.
	- ``state`` = ``unknown``, ``running``, ``stopped``, ``deleted``
	"""

	UNKNOWN = "unknown"
	PENDING = "pending"
	RUNNING = "running"
	STOPPED = "stopped"
	OFF = "off"
	FAILED = "failed"
	CONFIGURED = "configured"
	UNCONFIGURED = "unconfigured"
	UNKNOWN = "unknown"
	IS_ACCESSIBLE = frozenset(("pending", "running", "stopped", "configured", "failed", "unconfigured"))

	def check(self, radl):
		"""Check the features in this system."""

		def positive(f, _):
			return f.value >= 0

		mem_units = [None, "", "B", "K", "M", "G", "KB", "MB", "GB"]
		SIMPLE_FEATURES = {
			"image_type": (str, ["VMDK", "QCOW", "QCOW2", "RAW"]),
			"virtual_system_type": (str, system._check_virtual_system_type),
			"price": ((int,float), positive, None),
			"cpu.count": (int, positive, None),
			"cpu.arch": (str, ['I386', 'X86_64']),
			"cpu.performance": ((int,float), positive, ["ECU", "GCEU", "HRZ"]),
			"memory.size": ((int,float), positive, mem_units),
			SoftFeatures.SOFT: (SoftFeatures, lambda x, r: x.check(r))
		}
		self.check_simple(SIMPLE_FEATURES, radl)

		net_connections = set()
		def check_net_interface_connection(f, radl0):
			if isinstance(f.value, str):
				net = radl0.get(network(f.value))
				if not net:
					return False
				f.value = net
			net_connections.add(f.prop)
			return True

		def check_app(f, x):
			FeaturesApp(f.value.features).check(x)
			return True
	
		NUM_FEATURES = {
			"net_interface": {
				"connection": ((str,Aspect), check_net_interface_connection),
				"dns_name": (str, None) },
			"disk": {
				"image.url": (str, system._check_disk_image_url),
				"image.name": (str, None),
				"type": (str, None),
				"device": (str, None),
				"size": (int, positive, mem_units),
				"free_size": (int, positive, mem_units),
				"os.name": (str, ["LINUX", "WINDOWS", "MAC OS X"]),
				"os.flavour": (str, None),
				"os.version": (str, None),
				"os.credentials.username": (str, None),
				"os.credentials.password": (str, None),
				"os.credentials.private_key": (str, None),
				"os.credentials.public_key": (str, None),
				"applications": (Features, check_app)
			}
		}
		prefixes = self.check_num(NUM_FEATURES, radl)

		# Check all interfaces
		if len(net_connections) != len(prefixes.get("net_interface", set())):
			raise RADLParseException( "Some net_interface does not have a connection")

		return True

	@staticmethod
	def _check_disk_image_url(f, _):
		guess = _system.parse_image_url(f.value)
		if (not (guess.get("location", None) or guess.get("host", None)) or
		    not guess.get("image", None)):
			raise RADLParseException("Url not valid: %s" % f.value, line=f.line)
		return True

	@staticmethod
	def _check_virtual_system_type(f, radl):
		return True

	@staticmethod
	def parse_image_url(url):
		"""
		Return information about the url.
	
		Possible url patterns:
	
		- ``one://<server>:<port>/<image-id>``, for OpenNebula;
		- ``ost://<server>:<port>/<ami-id>``, for OpenStack; and
		- ``aws://<region>/<ami-id>``, for Amazon Web Service.
		- ``fbw://<image-name>``, for FogBow.
	
		Return(dict): a dict with some of this keys:
	
		- provider: one of "OpenNebula", "OpenStack" or "EC2".
		- host: the server.
		- port: the port
		- location: region on ``aws`` urls.
		- image: image id.
		"""
	
		res = dict([ (k, "") for k in ["provider", "host", "port", "location", "image"] ])
		urlp = urlparse(url)
		SCHEMES = {"one": "OpenNebula", "ost": "OpenStack", "aws": "EC2", "dummy": "DUMMY", "fbw": "FogBow"}
		if urlp.scheme in SCHEMES:
			res["provider"] = SCHEMES[urlp.scheme]
		if urlp.scheme == "aws":
			res["location"] = urlp.netloc
		elif urlp.scheme != "fbw":
			res["host"] = urlp.hostname
			res["port"] = urlp.port
		if urlp.scheme == "fbw":
			res["image"] = urlp.netloc
			res["location"] = "FogBow"
		else:
			res["image"] = urlp.path.lstrip("/")

		return res

	def concrete(self, other=None):
		"""
		Return copy and score after being applied other system and soft features.

		Args:

		- other(system, optional): system to apply just before soft features.

		Return(tuple): tuple of the resulting system and its score.
		"""

		new_system = self.clone()
		if other:
			new_system.merge(other, missing="other")
		soft_features = self.getValue(SoftFeatures.SOFT, [])
		score = 0
		for f in sorted(soft_features, key=lambda f: f.soft, reverse=True):
			try:
				new_system.merge(f, missing="other")
				score += f.soft
			except:
				pass
		new_system.delValue(SoftFeatures.SOFT)
		return new_system, score


class system(FeaturedAspect, _system):
	"""
	Store a RADL ``system``.

	Basic features:
	- ``auth`` contains Authentication attributes.
	- ``state`` = ``unknown``, ``running``, ``stopped``, ``deleted``, ``template``
	- ``groups`` contains groups that this VM is member of.
	"""

	def check(self, radl):
		return _system.check(self, radl)

class SoftFeatures(_system, Feature):
	"""
	Assign a weight to a group of features.

	Args:
	- soft: weight of matching the containing features.
	"""

	SOFT = "__soft__"
	"""Fake property name."""

	def __init__(self, soft, features, line=None):
		self.soft = soft
		self.line = line
		_system.__init__(self, features)
		Feature.__init__(self, SoftFeatures.SOFT, "contains", self)

	def __hash__(self):
		return _system.__hash__(self)

	def __eq__(self, other):
		return isinstance(other, SoftFeatures) and Features.__eq__(self, other)

	def diff(self, other):
		assert isinstance(other, SoftFeatures)
		return SoftFeatures(self.soft, Features.diff(self, other))

class Infrastructure(FeaturedAspect):
	"""
	Store an infrastructure.

	Basic features:
	- ``auth`` contains Authentication attributes.
	- ``state`` = ``unknown``, ``running``, ``stopped``, ``deleted``
	"""

	UNKNOWN = "unknown"
	RUNNING = "running"
	STOPPED = "stopped"
	DELETED = "deleted"
	IS_ACCESSIBLE = frozenset(("running", "stopped"))

class File(FeaturedAspect):
	"""
	Store an information object.

	Basic features:
	- ``auth`` contains Authentication attributes.
	- ``state`` = ``unknown``, ``ready``, ``pending``, ``deleted``.
	- ``content`` object content available is ``state`` is ``ready``.
	"""

	UNKNOWN = "unknown"
	READY = "ready"
	PENDING = "pending"
	DELETED = "deleted"
	IS_ACCESSIBLE = frozenset(("ready", "pending"))

class DeployFile(FeaturedAspect):
	"""
	Store an object that have to be deployed in a system.

	Basic features:
	- ``auth`` contains Authentication attributes.
	- ``state`` = ``unknown``, ``ready``, ``pending``.
	- ``content``: string or ``File``.
	- ``path``: local path to system where saving the file.
	"""

	UNKNOWN = "unknown"
	READY = "ready"
	PENDING = "pending"
	IS_ACCESSIBLE = frozenset(("ready", "pending"))

class DeployScript(FeaturedAspect):
	"""
	Store a script to run in a system.

	Basic features:
	- ``state`` = ``unknown``, ``ready``, ``pending``.
	- ``content``: string or ``File``.
	"""

	UNKNOWN = "unknown"
	READY = "ready"
	PENDING = "pending"
	IS_ACCESSIBLE = frozenset(("ready", "pending"))


class RADL(object):
	"""Parsed RADL document."""
	
	def __init__(self, aspects=[], ifpresent="error", check=True, **kwargs):
		self.props = OrderedDict()
		"""Dict of aspects with key (type, id)."""

		for a in aspects:
			self.add(a, ifpresent=ifpresent, check=False, **kwargs)
		if check: self.check()

	@property
	def aspects(self):
		return self.props.values()

	def keys(self):
		return self.props.keys()

	def __repr__(self):
		return "RADL([ %s ])" % ", ".join(map(repr, self.props.values()))

	def __hash__(self):
		return hash(tuple([ self.props[k] for k in sorted(self.props.keys()) ]))

	def __eq__(self, other):
		return other is not None and isinstance(other, RADL) and self.props == other.props

	def add(self, aspect, ifpresent="error", check=False, addaspects=True, **kwargs):
		"""
		Add an aspect.

		Args:
		- aspect(Aspect): thing to add.
		- ifpresent(str): if it has been defined, do:

		   - ``"ignore"``: not add the aspect.
		   - ``"replace"``: replace the old aspect by the new aspect.
		   - ``"merge"``: apply new aspect features to the old aspect.
		   - ``"error"``: raise an error.
                - addaspects: add also aspects in features.
		- conflict, missing: args passed to ``merge`` if ``ifpresent`` is ``"merge"``.

		Return(bool): True if aspect was added.
		"""

		OPTIONS_IFPRESENT = ["ignore", "replace", "merge", "error"]
		assert ifpresent in OPTIONS_IFPRESENT, "Invalid value in `ifpresent`."
		assert isinstance(aspect, Aspect)

		aspect0 = self.props.get(aspect.getKey(), None)
		if aspect0 and aspect.reference:
			return False
		if aspect0 and aspect0.reference:
			aspect0.merge(aspect, conflict="other", missing="other")
			aspect0.reference = False
			aspect = aspect0
		elif aspect0 and id(aspect0) != id(aspect):
			# If some aspect with the same id is found
			if ifpresent == "error":
				raise Exception("Aspect with the same id was found: `%s`." % str(aspect.getKey()))
			elif ifpresent == "merge":
				aspect0.merge(aspect, **kwargs)
			elif ifpresent == "ignore":
				return False
		else:
			aspect0 = self.props[aspect.getKey()] = aspect
		aspect = aspect0

		# Otherwise add aspect
		if addaspects and isinstance(aspect, Features):
			fs = [f for f in aspect.features if isinstance(f.value, Aspect) and
			      id(self.get(f.value)) != id(f.value) ]
			for self0, i in ((self.clone(check=False), 0), (self, 1)):
				for f in fs:
					self0.add(f.value, ifpresent=ifpresent, check=check, **kwargs)
					if i == 1: f.value = self0.get(f.value)

		if check and addaspects: self.check()
		return True

	def delete(self, aspect, ifnotpresent="error"):
		"""
		Remove an aspect.

		Args:
		- aspect(Aspect): thing to remove.
		- ifnotpresent(str): if it has been defined, do:

		   - ``"ignore"``: not add the aspect.
		   - ``"error"``: raise an error.

		Return(bool): True if aspect was removed.
		"""

		OPTIONS_IFNOTPRESENT = ["ignore", "error"]
		assert ifnotpresent in OPTIONS_IFNOTPRESENT, "Invalid value in `ifnotpresent`."

		if aspect.getKey() not in self.props:
			if ifnotpresent == "error":
				raise Exception("No aspect with the same id was found.")
			elif ifnotpresent == "ignore":
				return False
		del self.props[aspect.getKey()]
		self.check()

	
	def merge(self, radl, ifpresent="merge", cls=None, **kwargs):
		"""
		Add aspects in other RADL.

		Args:
		- radl(RADL): thing to add.
		- ifpresent(str): if it has been defined, do:

		   - ``"ignore"``: not add the aspect.
		   - ``"replace"``: replace the old aspect by the new aspect.
		   - ``"merge"``: apply new aspect features to the old aspect.
		   - ``"error"``: raise an error.
		- cls(list of type): only merge aspects of these types.
		- conflict, missing: args passed to ``merge`` if ``ifpresent`` is ``"merge"``.

		Return(bool): True if aspect was added.
		"""

		for self0 in (self.clone(check=False), self):
			for aspect in radl.aspects:
				if cls and not isinstance(aspect, cls): continue
				self0.add(aspect, ifpresent, **kwargs)
		self.check()
		return True

	def get(self, aspect, default=None):
		"""Get a network, system or configure or contextualize with the same id as aspect passed."""

		aspectkey = aspect.getKey() if isinstance(aspect, Aspect) else aspect
		return self.props.get(aspectkey, default)

	def gets(self, cls):
		"""Return a list of aspects of that type."""

		return [ a for a in self.aspects if isinstance(a, cls) ]

	def diff(self, other):
		assert isinstance(other, RADL)
		return RADL([ (a.diff(other.get(a)) if other.get(a) and a.diff else a)
		              for a in self.aspects if a != other.get(a) ], ifpresent="merge",
		            missing="other")

	def clone(self, check=True):
		r = RADL()
		for a in self.aspects:
			new_a = a.clone()
			r.props[new_a.getKey()] = new_a
		for a in r.aspects:
			for f in (a.features if isinstance(a, Features) else []):
				if isinstance(f.value, Aspect):
					f.value = r.get(f.value)
		if check: r.check()
		return r
	
	def check(self):
		"""Check if it is a valid RADL document."""

		for i in self.aspects:
			i.check(self)
		return True

# NOTE: deprecated
class Application:
	pass
