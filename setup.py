#!/usr/bin/env python

import os
from setuptools import setup

# Add contextualization dir files
install_path = '/etc/ec3/'
datafiles = [(os.path.join(install_path, root), [os.path.join(root, f) for f in files])
             for root, dirs, files in os.walk("templates")]
datafiles.append(('/etc/bash_completion.d', ['bash_completion/ec3']))

setup(
    name="ec3-cli",
    version="2.2.1",
    author="Amanda Calatrava, Eloy Romero, Miguel Caballer",
    author_email="",
    description=("Tool to deploy virtual elastic clusters on the cloud."),
    license="Apache 2.0",
    keywords="cloud cluster elasticity",
    url="http://www.grycap.upv.es/ec3/",
    data_files=datafiles,
    packages=['IM2', 'IM2.radl'],
    package_data={'IM2.radl': ['radl_schema.json']},
    scripts=["ec3"],
    install_requires=["ply", "PyYAML", "jsonschema", "requests"],
    long_description=("Elastic Cloud Computing Cluster (EC3) is a tool to create elastic virtual clusters on top"
                      "of Infrastructure as a Service (IaaS) providers, either public (such as Amazon Web Services,"
                      "Google Cloud or Microsoft Azure)"
                      "or on-premises (such as OpenNebula and OpenStack). We offer recipes to deploy TORQUE"
                      "(optionally with MAUI), SLURM, SGE, HTCondor, Mesos, Nomad and Kubernetes clusters that can be self-managed with CLUES:"
                      "it starts with a single-node cluster and working nodes will be dynamically deployed and provisioned"
                      "to fit increasing load (number of jobs at the LRMS). Working nodes will be undeployed when they are idle."
                      "This introduces a cost-efficient approach for Cluster-based computing."),
)
