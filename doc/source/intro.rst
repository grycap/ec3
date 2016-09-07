
Introduction
============

Elastic Cloud Computing Cluster (EC3) is a tool to create elastic virtual clusters on top
of Infrastructure as a Service (IaaS) providers, either public (such as `Amazon Web Services`_,
`Google Cloud`_ or `Microsoft Azure`_)
or on-premises (such as `OpenNebula`_ and `OpenStack`_). We offer recipes to deploy `TORQUE`_
(optionally with `MAUI`_) and `SLURM`_ clusters that can be self-managed with `CLUES`_:
it starts with a single-node cluster and working nodes will be dynamically deployed and provisioned
to fit increasing load (number of jobs at the LRMS). Working nodes will be undeployed when they are idle.
This introduces a cost-efficient approach for Cluster-based computing.


Installation
------------

The program `ec3` requires Python 2.6+, `PyYAML`_ and an `IM`_ server, which is used to
launch virtual machines. By default `ec3` uses our public `IM`_ server in
`servproject.i3m.upv.es`. *Optionally* you can deploy a local `IM`_ server executing the
next commands::

    sudo pip install im
    sudo service im start

`PyYAML`_ is usually available in distribution repositories (``python-yaml`` in Debian;
``PyYAML`` in Red Hat; and ``PyYAML`` in pip).
`ec3` can be download from `this <https://github.com/grycap/ec3>`_ git repository::

   git clone https://github.com/grycap/ec3

In the created directory there is the python executable file ``ec3``, which provides the
command-line interface described next.  ``sshpass`` is required to provide the user with ssh access to the cluster.

Basic example with Amazon EC2
-----------------------------

First create a file ``auth.txt`` with a single line like this::

   id = provider ; type = EC2 ; username = <<Access Key ID>> ; password = <<Secret Access Key>>

Replace ``<<Access Key ID>>`` and ``<<Secret Access Key>>`` with the corresponding values
for the AWS account where the cluster will be deployed. It is safer to use the credentials
of an IAM user created within your AWS account.

This file is the authorization file (see `Authorization file`_), and can have more than one set of credentials.

Now we are going to deploy a cluster in Amazon EC2 with a limit number of nodes = 10. This parameter to indicate the maximum size of the cluster is called ``ec3_max_instances`` and it has to be indicated in the RADL file that describes the infrastructure to deploy. In our case, we are going to use the ``ubuntu-ec2`` recipe, available in our github repo. The next command deploys a `TORQUE`_ cluster based on an `Ubuntu`_ image::

   $ ec3 launch mycluster torque ubuntu-ec2 -a auth.txt -y
   WARNING: you are not using a secure connection and this can compromise the secrecy of the passwords and private keys available in the authorization file.
   Creating infrastructure
   Infrastructure successfully created with ID: 60
      ▄▟▙▄¨        Front-end state: running, IP: 132.43.105.28

If you deployed a local `IM`_ server, use the next command instead::

   $ ec3 launch mycluster torque ubuntu-ec2 -a auth.txt -u http://localhost:8899

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

* `EC3 Command-line Interface`_.
* `Templates`_.
* Information about available templates: ``ec3 templates [--search <topic>] [--full-description]``.

.. _`CLUES`: http://www.grycap.upv.es/clues/
.. _`RADL`: http://imdocs.readthedocs.org/en/devel/radl.html
.. _`TORQUE`: http://www.adaptivecomputing.com/products/open-source/torque
.. _`MAUI`: http://www.adaptivecomputing.com/products/open-source/maui/
.. _`SLURM`: http://slurm.schedmd.com/
.. _`Scientific Linux`: https://www.scientificlinux.org/
.. _`Ubuntu`: http://www.ubuntu.com/
.. _`OpenNebula`: http://www.opennebula.org/
.. _`OpenStack`: http://www.openstack.org/
.. _`Amazon Web Services`: https://aws.amazon.com/
.. _`Google Cloud`: http://cloud.google.com/
.. _`Microsoft Azure`: http://azure.microsoft.com/
.. _`IM`: http://www.grycap.upv.es/im
.. _`PyYAML`: http://pyyaml.org/wiki/PyYAML
.. _`EC3 Command-line Interface`: http://ec3.readthedocs.org/en/latest/ec3.html
.. _`Authorization file`: http://servproject.i3m.upv.es/ec3/doc/ec3.html#authorization-file
.. _`Templates`: http://ec3.readthedocs.org/en/latest/templates.html
.. _`EC3aaS`: http://servproject.i3m.upv.es/ec3/
.. _`sshpass`: https://gist.github.com/arunoda/7790979
