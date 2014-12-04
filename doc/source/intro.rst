
Elastic Cloud Computing Cluster (EC3)
=====================================

Elastic Cloud Computing Cluster (EC3) is a tool to create elastic virtual clusters on top
of Infrastructure as a Service (IaaS) providers, either public (such as `Amazon Web Services`_)
or on-premise (such as `OpenNebula`_ and `OpenStack`_). We offer recipes to deploy `TORQUE`_
(optionally with `MAUI`_) and `SLURM`_ clusters that can be self-managed with `CLUES`_:
it starts with a single-node cluster and working nodes will be dynamically deployed and provisioned
to fit increasing load (number of jobs at the LRMS). Working nodes will be undeployed when they are idle.
This introduces a cost-efficient approach for Cluster-based computing.


Installation
------------

The program `ec3` requires Python 2.6+ and an `IM`_ server, which is used to launch
virtual machines. By default `ec3` uses our public `IM`_ server in
`servproject.i3m.upv.es`. *Optionally* you can deploy a local `IM`_ server executing
the next commands::

    sudo pip install im
    sudo service im start

`ec3` can be download from `this <https://github.com/grycap/ec3>`_
git repository::

   git clone https://github.com/grycap/ec3

In the created directory there is the python executable file ``ec3``, which provides the
command-line interface described next.

Basic example with Amazon EC2
-----------------------------

First create a file ``auth.txt`` with a single line like this::

   id = provider ; type = EC2 ; username = <<Access Key ID>> ; password = <<Secret Access Key>>

Replace ``<<Access Key ID>>`` and ``<<Secret Access Key>>`` with the corresponding values
for the AWS account where the cluster will be deployed. It is safer to use the credentials
of an IAM user created within your AWS account.

This file is the :ref:`authorization file <auth-file>`, and can have more than one set of credentials.

The next command deploys a `TORQUE`_ cluster based on an `Ubuntu`_ image::

   $ ec3 launch mycluster torque --add ec3_control --add ubuntu-ec2 -a auth.txt -y
   WARNING: you are not using a secure connection and this can compromise the secrecy of the passwords and private keys available in the authorization file.
   Creating infrastructure
   Infrastructure successfully created with ID: 60
      ▄▟▙▄¨        Front-end state: running, IP: 132.43.105.28

If you deployed a local `IM`_ server, use the next command instead::

   $ ec3 launch mycluster torque --add ec3_control --add ubuntu-ec2 -a auth.txt -u http://localhost:8899

This can take several minutes. After that, open a ssh session to the front-end::

   $ ec3 ssh mycluster
   Welcome to Ubuntu 14.04.1 LTS (GNU/Linux 3.13.0-24-generic x86_64)
    * Documentation:  https://help.ubuntu.com/

   ubuntu@torqueserver:~$

Also you can show basic information about the deployed clusters by executing::

    $ ec3 list
       name       state          IP        nodes
    ---------------------------------------------
     mycluster  configured  132.43.105.28    0

Additional information
----------------------

* `ec3 manual <https://github.com/grycap/ec3/blob/devel/doc/source/ec3.rst>`_.
* Documentation about `RADL and templates <https://github.com/grycap/ec3/blob/devel/doc/source/templates.rst>`_.
* Information about available templates: ``ec3 templates [--search <topic>] [--full-description]``.

.. _`CLUES`: http://www.grycap.upv.es/clues/
.. _`RADL`: http://www.grycap.upv.es/im/doc/radl.html
.. _`TORQUE`: http://www.adaptivecomputing.com/products/open-source/torque
.. _`MAUI`: http://www.adaptivecomputing.com/products/open-source/maui/
.. _`SLURM`: http://slurm.schedmd.com/
.. _`Scientific Linux`: https://www.scientificlinux.org/
.. _`Ubuntu`: http://www.ubuntu.com/
.. _`OpenNebula`: http://www.opennebula.org/
.. _`OpenStack`: http://www.openstack.org/
.. _`Amazon Web Services`: https://aws.amazon.com/
.. _`IM`: https://github.com/grycap/im
