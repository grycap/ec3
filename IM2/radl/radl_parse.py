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

import os
from ply import lex
from ply import yacc
from . import radl
from .radl import Feature, RADL, configure, contextualize, contextualize_item, \
                  deploy, SoftFeatures, Features, Aspect, RADLParseException
try:
	import yaml
except ImportError:
	yaml = None
try:
	unicode("hola")
except NameError:
	class unicode: pass

class RADLParser:

	def __init__(self, autodefinevars = True, **kwargs):
		outputdir = os.path.expanduser('~/.ec3/')
		self.lexer = lex.lex(module=self, debug=0, optimize=1, outputdir=outputdir, **kwargs)
		self.yacc = yacc.yacc(module=self, debug=0, optimize=1, outputdir=outputdir)

	# LEXER ITEMS
	# Ponemos los estados para gestionan el tema de las recetas
	states = (
	   ('recipe', 'exclusive'),
	   ('body', 'inclusive'),
	)
	
	# Lista de nombres de Token. Esto es obligatorio.
	tokens = (
		'LPAREN',
		'RPAREN',
		'NUMBER',
		'AND',
		'EQ',
		'LT',
		'GT',
		'GE',
		'LE',
		'SOFT',
		'STRING',
		'VAR',
		'CONTAINS',
		'DEPLOY',
		'CONFIGURE',
		'SYSTEM',
		'RECIPE_LINE',
		'RECIPE_BEGIN',
		'RECIPE_END',
		'CONTEXTUALIZE',
		'STEP',
		'newline',
		'OPTION'
	)
	
	# A string containing ignored characters (spaces and tabs)
	t_ignore = ' \t'
	t_recipe_ignore = ''
	t_body_ignore = ' \t'
	
	# Ignore comments.
	def t_comment(self,t):
		r'\#.*'
		pass
	
	def t_body_LE(self,t):
		r'<='
		return t
	
	def t_body_GE(self,t):
		r'>='
		return t
	
	def t_body_EQ(self,t):
		r'='
		return t
	
	def t_body_GT(self,t):
		r'>'
		return t
	
	def t_body_LT(self,t):
		r'<'
		return t
	
	def t_LPAREN(self,t):
		r'\('
		t.lexer.push_state("body")
		return t
	
	def t_RPAREN(self,t):
		r'\)'
		t.lexer.pop_state()
		return t
	
	def t_newline(self,t):
		r'\n'
		t.lexer.lineno += len(t.value)
		return t
	
	def t_body_newline(self,t):
		r'\n'
		t.lexer.lineno += len(t.value)
	
	def t_NUMBER(self,t):
		r'\d+\.?\d*'
		if t.value.find(".") != -1:
			t.value = float(t.value)
		else:
			t.value = int(t.value)
		return t
	
	def t_STRING(self,t):
		r"'([^\\']|\\.)*'"
		t.value = t.value[1:-1].replace("\\'", "'")
		return t
	
	reserved = {
		'soft' : 'SOFT',
		'and' : 'AND',
		'contains' : 'CONTAINS',
		'deploy' : 'DEPLOY',
		'configure': 'CONFIGURE',
		'system': 'SYSTEM',
		'contextualize': 'CONTEXTUALIZE',
		'step':'STEP',
		'option': 'OPTION'
	}
	
	def t_VAR(self, t):
		r'[a-zA-Z_.][\w\d_.-]*'
		t.type = self.reserved.get(t.value, 'VAR')  # Check reserved words
		return t
	
	def t_RECIPE_BEGIN(self, t):
		r'@begin'
		t.lexer.push_state('recipe')
		return t
	
	def t_recipe_RECIPE_END(self, t):
		r'@end'
		t.lexer.pop_state()
		return t
	
	def t_recipe_RECIPE_LINE(self, t):
		r'.*\n'
		t.type = 'RECIPE_LINE'
		t.lexer.lineno += t.value.count("\n")
		return t
	
	# Error handling rule
	def t_ANY_error(self, t):
		#print "Illegal character '%s'" % t.value[0]
		t.lexer.skip(1)

	# PARSER ITEMS

	def p_radl(self, t):
		"""radl : radl radl_sentence_end
		        | radl_sentence_end"""
	
		if len(t) == 2:
			t[0] = RADL()
			if t[1]: t[0].add(t[1])
		else:
			t[0] = t[1]
			if t[2]: t[0].add(t[2])
	
	def p_radl_sentence_end(self, t):
		"""radl_sentence_end : radl_sentence END
		                     | END"""
	
		t[0] = t[1] if len(t) == 3 else None
	
	def p_radl_sentence(self, t):
		"""radl_sentence : configure_sentence
		                 | contextualize_sentence
		                 | deploy_sentence
		                 | cfeatures_sentence"""
		t[0] = t[1]
	
	def p_configure_sentence(self, t):
		"""configure_sentence : CONFIGURE VAR
		                      | CONFIGURE VAR LPAREN RECIPE_BEGIN recipe RECIPE_END RPAREN"""
	
		if len(t) == 3:
			t[0] = configure(t[2], reference=True, line=t.lineno(1))
		else:
			recipe = "".join(t[5])
			if yaml:
				try:
					recipe = yaml.safe_load(recipe)
				except Exception as e:
					raise RADLParseException("Error parsing YAML: %s" % str(e), line=t.lineno(5))
			t[0] = configure(t[2], recipe, line=t.lineno(1))
	
	def p_recipe(self, t):
		"""recipe : recipe RECIPE_LINE
		          | RECIPE_LINE"""
		if len(t) == 3:
			t[0] = t[1]
			t[0].append(t[2])
		else:
			t[0] = [t[1]]
	
	def p_deploy_sentence(self, t):
		"""deploy_sentence : DEPLOY VAR NUMBER
		                   | DEPLOY VAR NUMBER VAR"""
	
		if len(t) == 4:
			t[0] = deploy(t[2], t[3], line=t.lineno(1))
		else:
			t[0] = deploy(t[2], t[3], t[4], line=t.lineno(1))
	
	def p_contextualize_sentence(self, t):
		"""contextualize_sentence : CONTEXTUALIZE LPAREN contextualize_options contextualize_items RPAREN
		                          | CONTEXTUALIZE NUMBER  LPAREN contextualize_options contextualize_items RPAREN"""
	
		if len(t) == 5:
			t[0] = contextualize(t[3], line=t.lineno(1))
		if len(t) == 6:
			t[0] = contextualize(t[4], options=t[3], line=t.lineno(1))
		else:
			t[0] = contextualize(t[5], t[2], options=t[4], line=t.lineno(1))

	def p_contextualize_options(self, t):
		"""contextualize_options : contextualize_options contextualize_option
								 | contextualize_option
								 | empty"""
		if len(t) == 3:
			t[0] = t[1]
			t[0].append(t[2])
		elif t[1]:
			t[0] = [t[1]]
		else:
			t[0] = []

	def p_contextualize_option(self, t):
		"""contextualize_option : OPTION VAR comparator STRING
								| OPTION VAR comparator NUMBER"""

		t[0] = Feature(t[2], t[3], t[4], line=t.lineno(1))

	def p_contextualize_items(self, t):
		"""contextualize_items : contextualize_items contextualize_item 
		                       | contextualize_item
		                       | empty"""
	
		if len(t) == 3:
			t[0] = t[1]
			t[0].append(t[2])
		elif t[1]:
			t[0] = [t[1]]
		else:
			t[0] = []
	
	def p_contextualize_item(self, t):
		"""contextualize_item : SYSTEM VAR CONFIGURE VAR
		                      | SYSTEM VAR CONFIGURE VAR STEP NUMBER"""
	
		if len(t) == 5:
			t[0] = contextualize_item(t[2], t[4], line=t.lineno(1))
		else:
			t[0] = contextualize_item(t[2], t[4], t[6], line=t.lineno(1))
	
	def p_cfeatures_sentence(self, t):
		"""cfeatures_sentence : reference
		                      | nvar VAR LPAREN features RPAREN"""
	
		if len(t) == 2:
			t[0] = t[1]
			return
		try:
			cls = getattr(radl, t[1])
		except:
			raise RADLParseException("'%s' is not an aspect." % t[1], line=t.lineno(1))
		t[0] = cls(t[2], t[4], line=t.lineno(1))
	
	def p_features(self, t):
		"""features : features AND feature
		            | feature
		            | empty"""
	
		if len(t) == 4:
			t[0] = t[1]
			t[0].append(t[3])
		elif t[1]:
			t[0] = [t[1]]
		else:
			t[0] = []
	
	def p_feature(self, t):
		"""feature : feature_soft
		           | feature_simple
		           | feature_features"""
	
		t[0] = t[1]
	
	def p_feature_soft(self, t):
		"""feature_soft : SOFT NUMBER LPAREN features RPAREN"""
	
		t[0] = SoftFeatures(t[2], t[4], line=t.lineno(1))
	
	def p_feature_simple(self, t):
		"""feature_simple : VAR comparator NUMBER VAR
		                  | VAR comparator NUMBER
		                  | VAR comparator STRING
		                  | VAR comparator reference"""
	
		t[0] = Feature(t[1], t[2], t[3], unit=t[4] if len(t) == 5 else None, line=t.lineno(1))
	
	def p_feature_features(self, t):
		"""feature_features : VAR CONTAINS LPAREN features RPAREN"""
	
		t[0] = Feature(t[1], t[2], Features(t[4]), line=t.lineno(1))
	
	def p_reference(self, t):
		"""reference : nvar VAR"""
	
		try:
			cls = getattr(radl, t[1])
		except:
			raise RADLParseException("'%s' is not an aspect." % t[1], line=t.lineno(1))
		t[0] = cls(t[2], reference=True, line=t.lineno(1))
	
	def p_nvar(self, t):
		"""nvar : SYSTEM
		        | VAR"""
	
		t[0] = t[1]
	
	def p_END(self, t):
		"""END : newline"""
	
		t[0] = None
	
	def p_empty(self, t):
		"""empty :"""
	
		t[0] = None
	
	def p_comparator(self, t):
		"""comparator : EQ
		              | LT
		              | GT
		              | GE
		              | LE
		              | CONTAINS"""
	
		t[0] = t[1]
	
	def p_error(self, t):
		raise RADLParseException("Parse error in: " + str(t), line=t.lineno if t else None)
	
	def parse(self, data):
		data = data + "\n"
		self.lexer.lineno = 1
		self.lexer.begin('INITIAL')
		return self.yacc.parse(data, tracking=True, debug=0, lexer=self.lexer)
	
def parse_radl(data):
	"""
	Parse a RADL document.

	Args:
	- data(str): string with RADL content.

	Return: RADL object.
	"""
	parser = RADLParser()
	return parser.parse(data)


def dump_radl(radl, enter="\n", margin="", indent="  "):
	"""
	Dump a RADL document.

	Args.:
	- radl(RADL): RADL to dump.
	- enter(str): string used as new line.
	- margin(str): string inserted before every line.
	- indent(str): string append to margin when increasing level.

	Return(str): a text representing the RADL.
	"""

	return d_radl(radl, enter, margin, indent)

def d_radl(radl, enter, margin, indent):
	assert isinstance(radl, RADL)
	return (enter*2).join([ d_radl_sentence(a, enter, margin, indent) for a in radl.aspects ])

def d_radl_sentence(aspect, *args):
	assert isinstance(aspect, Aspect)
	if isinstance(aspect, configure):
		return d_configure_sentence(aspect, *args)
	elif isinstance(aspect, contextualize):
		return d_contextualize_sentence(aspect, *args)
	elif isinstance(aspect, deploy):
		return d_deploy_sentence(aspect, *args)
	else:
		return d_cfeatures_sentence(aspect, *args)

def d_configure_sentence(a, enter, margin, indent):
	assert isinstance(a, configure)
	if a.reference or not a.recipe:
		return "%sconfigure %s" % (margin, a.name)
	def tostr(r):
		return r if isinstance(r, (str, unicode)) else yaml.safe_dump(r, default_flow_style=False) if yaml else str(r)
	return "{margin}configure {name} ({enter}@begin{enter}{recipe}{enter}@end{enter}{margin})".format(
		name=a.name, recipe=tostr(a.recipe), enter=enter, margin=margin)

def d_deploy_sentence(a, enter, margin, indent):
	assert isinstance(a, deploy)
	return "{margin}deploy {id} {number}{cloud}".format(
		margin=margin, id=a.id, number=a.vm_number,
		cloud=" " + a.cloud_id if a.cloud_id else "")

def d_contextualize_sentence(a, enter, margin, indent):
	assert isinstance(a, contextualize)
	return "{margin}contextualize {number}({enter}{options}{sep}{items}{enter}{margin})".format(
		enter=enter, margin=margin, number="%d " % a.max_time if a.max_time else "", options=enter.join(
			[ d_contextualize_option(i, enter, margin+indent, indent) for i in a.options.values() ]),
		sep=enter if a.options else "",
		items=enter.join(
			[ d_contextualize_item(i, enter, margin+indent, indent) for i in a.items.values() ]))

def d_contextualize_option(a, enter, margin, indent):
	assert isinstance(a, Feature)
	return "{margin}option {option}".format(
		margin=margin, option=d_feature(a, enter, margin, indent))

def d_contextualize_item(a, enter, margin, indent):
	assert isinstance(a, contextualize_item)
	return "{margin}system {sys} configure {conf}{num}".format(
		margin=margin, sys=a.system, conf=a.configure, num=" step %d" % a.num if a.num else "")

def d_cfeatures_sentence(a, enter, margin, indent):
	assert isinstance(a, Features)
	cls = a.__class__.__name__
	return "{margin}{cls} {id}{rest}".format(margin=margin, cls=cls, id=a.getId(),
		rest=" ({enter}{fs}{enter}{margin})".format(enter=enter, margin=margin,
			fs=d_features(a, enter, margin+indent, indent)) if not a.reference else "")

def d_features(a, enter, margin, indent):
	assert isinstance(a, Features)
	return (" and%s" % enter).join([ d_feature(i, enter, margin, indent) for i in a.features ])

def d_feature(a, *args):
	assert isinstance(a, Feature)
	if isinstance(a, SoftFeatures):
		return d_feature_soft(a, *args)
	elif isinstance(a.value, (int, float, str, unicode)):
		return d_feature_number_string(a, *args)
	elif isinstance(a.value, Aspect):
		return d_feature_reference(a, *args)
	else:
		return d_feature_features(a, *args)

def d_feature_soft(a, enter, margin, indent):
	assert isinstance(a, SoftFeatures)
	return "{margin}soft {soft} ({enter}{fs}{enter}{margin})".format(
		enter=enter, margin=margin, soft=a.soft,
		fs=d_features(a, enter, margin+indent, indent))

def d_feature_number_string(a, enter, margin, indent):
	assert isinstance(a, Feature) and isinstance(a.value, (int, float, str, unicode))
	return "{margin}{prop} {op} {val}".format(
		margin=margin, prop=a.prop, op=a.operator,
		val="'%s'" % a.value.replace("'", "\\'") if isinstance(a.value, (str, unicode))
	            else "%s%s" % (a.value, a.unit if a.unit else ""))

def d_feature_reference(a, enter, margin, indent):
	assert isinstance(a, Feature) and isinstance(a.value, Aspect)
	return "{margin}{prop} {op} {cls} {id}".format(
		margin=margin, prop=a.prop, op=a.operator, cls=a.value.__class__.__name__, id=a.value.getId())

def d_feature_features(a, enter, margin, indent):
	assert isinstance(a, Feature) and isinstance(a.value, Features)
	return "{margin}{prop} {op} ({enter}{fs}{enter}{margin})".format(
		margin=margin, enter=enter, prop=a.prop, op=a.operator,
		fs=d_features(a.value, enter, margin+indent, indent))

