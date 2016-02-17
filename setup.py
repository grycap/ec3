#!/usr/bin/env python

import os
from setuptools import setup

# Add contextualization dir files
install_path = '/etc/ec3/'
datafiles = [(os.path.join(install_path, root), [os.path.join(root, f) for f in files])
    for root, dirs, files in os.walk("templates")]

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "ec3",
    version = "0.0.1",
    author = "Eloy Romero, Amanda Calatrava",
    author_email = "",
    description = ("Tool to deploy virtual elastic clusters on the cloud."),
    license = "Apache 2.0",
    keywords = "cloud cluster elasticity",
    url = "http://www.grycap.upv.es/ec3/",
	data_files=datafiles,
    packages=['IM2', 'IM2.radl'],
    package_data={'IM2.radl': ['radl_schema.json']},
    scripts=["ec3"],
	install_requires=["ply","PyYAML","jsonschema"],
    long_description=read('README.rst'),
)
