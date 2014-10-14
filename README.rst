
Elastic Cloud Computing Cluster (EC3)
=====================================

Elastic Cloud Computing Cluster (EC3) is a tool to create elastic virtual clusters on top
of Infrastructure as a Service (IaaS) providers. The cluster can be self-managed with
`CLUES`_.

Installation
------------

The program `ec3` requires Python 2.6+ and the python library `paramiko
<http://www.lag.net/paramiko/>`_. The former library is available in Debian and Red Hat
based distribution as ``python-paramiko``. Also can be installed from ``pip``::

   pip install parmiko

`ec3` can be download from `this <https://github.com/grycap/ec3>`_
git repository::

   git clone https://github.com/grycap/ec3

In the created directory there is the executable file ``ec3``, which is command-line
interface described next.

Basic example with Amazon EC2
-----------------------------

First create a file ``auth.txt`` with a single line like this::

   id = provider ; type = EC2 ; username = <<Access Key ID>> ; password = <<Secret Access Key>>

Replace ``<<Access Key ID>>`` and ``<<Secret Access Key>>`` by the corresponding values
for the EC2 account where the cluster will be deployed. This file is the `authorization
file`, and can have more than one credentials.

The next command deploys a cluster based on `Ubuntu`_ images with `TORQUE`_::

   $ ec3 launch mycluster torque --add clues --add ubuntu-ec2 -a auth.txt 

It can take several minutes... After that, open a ssh session to the front-end::

   $ ec3 ssh mycluster
   Welcome to Ubuntu 14.04.1 LTS (GNU/Linux 3.13.0-24-generic x86_64)
    * Documentation:  https://help.ubuntu.com/
   
   ubuntu@torqueserver:~$

After that, you can execute the next command to show basic information about the deployed cluster::

    $ ec3 list
     name    state          IP        nodes 
    ----------------------------------------
      c0   configured  158.42.105.11    0   

.. _`CLUES`: http://www.grycap.upv.es/clues/
.. _`RADL`: http://www.grycap.upv.es/im/doc/radl.html
.. _`TORQUE`: http://www.adaptivecomputing.com/products/open-source/torque
.. _`MAUI`: http://www.adaptivecomputing.com/products/open-source/maui/
.. _`SLURM`: http://slurm.schedmd.com/
.. _`Scientific Linux`: https://www.scientificlinux.org/
.. _`Ubuntu`: http://www.ubuntu.com/
