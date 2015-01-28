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

from .ply import lex

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
	'newline'
)

# A string containing ignored characters (spaces and tabs)
t_ignore = ' \t'
t_recipe_ignore = ''
t_body_ignore = ' \t'

# Ignore comments.
def t_comment(t):
	r'\#.*'
	pass

def t_body_LE(t):
	r'<='
	return t

def t_body_GE(t):
	r'>='
	return t

def t_body_EQ(t):
	r'='
	return t

def t_body_GT(t):
	r'>'
	return t

def t_body_LT(t):
	r'<'
	return t

def t_LPAREN(t):
	r'\('
	t.lexer.push_state("body")
	return t

def t_RPAREN(t):
	r'\)'
	t.lexer.pop_state()
	return t

def t_newline(t):
	r'\n'
	t.lexer.lineno += len(t.value)
	return t

def t_body_newline(t):
	r'\n'
	t.lexer.lineno += len(t.value)

def t_NUMBER(t):
	r'\d+\.?\d*'
	if t.value.find(".") != -1:
		t.value = float(t.value)
	else:
		t.value = int(t.value)
	return t

def t_STRING(t):
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
	'step':'STEP'
}

def t_VAR(t):
	r'[a-zA-Z_.][\w\d_.]*'
	t.type = reserved.get(t.value, 'VAR')  # Check reserved words
	return t

def t_RECIPE_BEGIN(t):
	r'@begin'
	t.lexer.push_state('recipe')
	return t

def t_recipe_RECIPE_END(t):
	r'@end'
	t.lexer.pop_state()
	return t

def t_recipe_RECIPE_LINE(t):
	r'.*\n'
	t.type = 'RECIPE_LINE'
	t.lexer.lineno += t.value.count("\n")
	return t

# Error handling rule
def t_ANY_error(t):
	#print "Illegal character '%s'" % t.value[0]
	t.lexer.skip(1)

lexer = lex.lex(optimize=1)
if __name__ == "__main__":
	lex.runmain(lexer)
