.. image:: doc/EC3-logo-3d.png
   :height: 50px
   :width: 41 px
   :scale: 50 %
   :alt: alternate text
   :align: right
   
.. Elastic Cloud Computing Cluster (EC3)
=====================================

Elastic Cloud Computing Cluster (EC3) is a tool to create elastic virtual clusters on top
of Infrastructure as a Service (IaaS) providers, either public (such as `Amazon Web Services`_,
`Google Cloud`_ or `Microsoft Azure`_)
or on-premises (such as `OpenNebula`_ and `OpenStack`_). We offer recipes to deploy `TORQUE`_
(optionally with `MAUI`_), `SLURM`_, `SGE`_, `HTCondor`_, `Mesos`_, `Nomad`_ and `Kubernetes`_ clusters that can be self-managed with `CLUES`_:
it starts with a single-node cluster and working nodes will be dynamically deployed and provisioned
to fit increasing load (number of jobs at the LRMS). Working nodes will be undeployed when they are idle.
This introduces a cost-efficient approach for Cluster-based computing.
   
Installation
------------

Requisites
~~~~~~~~~~

The program `ec3` requires Python 2.6+, `PLY`_, `PyYAML`_, `Requests`_, `jsonschema`_ and an `IM`_ server,
which is used to launch the virtual machines.

`PyYAML`_ is usually available in distribution repositories (``python-yaml`` in Debian;
``PyYAML`` in Red Hat; and ``PyYAML`` in pip).

`PLY`_ is usually available in distribution repositories (``python-ply`` and ``ply`` in pip).

`Requests`_ is usually available in distribution repositories (``python-requests`` and ``requests`` in pip).

`jsonschema`_ is usually available in distribution repositories (``python-jsonschema`` and ``jsonschema`` in pip).

By default `ec3` uses our public `IM`_ server in `appsgrycap.i3m.upv.es`. *Optionally* you can deploy a 
local `IM`_ server following the instructions of the `IM manual`_.
 
Also ``sshpass`` command is required to provide the user with ssh access to the cluster.

Installing
~~~~~~~~~~

As Python 2 is no longer supported, we recommend to install ec3 with Python 3.

First you need to install pip tool. To install them in Debian and Ubuntu based distributions, do::

	sudo apt update
	sudo apt install -y python3-pip

In Red Hat based distributions (RHEL, CentOS, Amazon Linux, Oracle Linux, Fedora, etc.), do::

	sudo yum install -y epel-release
	sudo yum install -y which python3-pip
	
Then you only have to call the install command of the pip tool with the `ec3-cli` package::
	
    sudo pip3 install ec3-cli

You can also download the last `ec3` version from `this <https://github.com/grycap/ec3>`_ git repository::

   git clone https://github.com/grycap/ec3

Then you can install it calling the pip tool with the current ec3 directory::
	
    sudo pip3 install ./ec3


Basic example with Amazon EC2
-----------------------------

First create a file ``auth.txt`` with a single line like this::

   id = provider ; type = EC2 ; username = <<Access Key ID>> ; password = <<Secret Access Key>>

Replace ``<<Access Key ID>>`` and ``<<Secret Access Key>>`` with the corresponding values
for the AWS account where the cluster will be deployed. It is safer to use the credentials
of an IAM user created within your AWS account.

This file is the authorization file (see `Authorization file`_), and can have more than one set of credentials.

The next command deploys a `TORQUE`_ cluster based on an `Ubuntu`_ image::

   $ ec3 launch mycluster torque ubuntu-ec2 -a auth.txt -y
   WARNING: you are not using a secure connection and this can compromise the secrecy of the passwords and private keys available in the authorization file.
   Creating infrastructure
   Infrastructure successfully created with ID: 60
      ▄▟▙▄¨        Front-end state: running, IP: 132.43.105.28

If you deployed a local `IM`_ server, use the next command instead::

   $ ec3 launch mycluster torque ubuntu-ec2 -a auth.txt -u http://localhost:8899

This can take several minutes.

Bear in mind that you have to specify a resource manager (like ``torque`` in our example) in addition to the images that you want to deploy (e.g. ``ubuntu-ec2``). For more information about this check the `templates documentation`_.

You can show basic information about the deployed clusters by executing::

    $ ec3 list
        name       state          IP        nodes
     ---------------------------------------------
      mycluster  configured  132.43.105.28    0

Once the cluster has been deployed, open a ssh session to the front-end (you may need to install the ``sshpass`` library)::

   $ ec3 ssh mycluster
   Welcome to Ubuntu 14.04.1 LTS (GNU/Linux 3.13.0-24-generic x86_64)
   Documentation:  https://help.ubuntu.com/
   ubuntu@torqueserver:~$

You may use the cluster as usual, depending on the LRMS.
For Torque, you can decide to submit a couple of jobs using qsub, to test elasticity in the cluster::

   $ for i in 1 2; do echo "/bin/sleep 50" | qsub; done

Notice that CLUES will intercept the jobs submited to the LRMS to deploy additional working nodes if needed.
This might result in a customizable (180 seconds by default) blocking delay when submitting jobs when no additional working nodes are available.
This guarantees that jobs will enter execution as soon as the working nodes are deployed and integrated in the cluster.

Working nodes will be provisioned and relinquished automatically to increase and decrease the cluster size according to the elasticity policies provided by CLUES.

Enjoy your virtual elastic cluster!


EC3 in Docker Hub
-----------------

EC3 has an official Docker container image available in `Docker Hub`_ and `GitHub Container Regitry`_ 
that can be used instead of installing the CLI. You can download it by typing:: 

   $ sudo docker pull grycap/ec3
   or
   $ sudo docker pull ghcr.io/grycap/ec3

You can exploit all the potential of EC3 as if you download the CLI and run it on your computer:: 

   $ sudo docker run grycap/ec3 list
   $ sudo docker run grycap/ec3 templates
 
To launch a cluster, you can use the recipes that you have locally by mounting the folder as a volume. Also it is recommendable to mantain the data of active clusters locally, by mounting a volume as follows::

   $ sudo docker run -v /home/user/:/tmp/ -v /home/user/ec3/templates/:/etc/ec3/templates -v /home/user/.ec3/clusters:/root/.ec3/clusters grycap/ec3 launch mycluster torque ubuntu16 -a /tmp/auth.dat 

Notice that you need to change the local paths to the paths where you store the auth file, the templates folder and the .ec3/clusters folder. So, once the front-end is deployed and configured you can connect to it by using::

   $ sudo docker run -ti -v /home/user/.ec3/clusters:/root/.ec3/clusters grycap/ec3 ssh mycluster

Later on, when you need to destroy the cluster, you can type::

   $ sudo docker run -ti -v /home/user/.ec3/clusters:/root/.ec3/clusters grycap/ec3 destroy mycluster


Additional information
----------------------

* `EC3 Command-line Interface`_.
* `Templates`_.
* Information about available templates: ``ec3 templates [--search <topic>] [--full-description]``.

.. _`CLUES`: http://www.grycap.upv.es/clues/
.. _`RADL`: http://www.grycap.upv.es/im/doc/radl.html
.. _`TORQUE`: http://www.adaptivecomputing.com/products/open-source/torque
.. _`MAUI`: http://www.adaptivecomputing.com/products/open-source/maui/
.. _`SLURM`: http://slurm.schedmd.com/
.. _`SGE`: http://gridscheduler.sourceforge.net/
.. _`Mesos`: http://mesos.apache.org/
.. _`HTCondor`: https://research.cs.wisc.edu/htcondor/
.. _`Nomad`: https://www.nomadproject.io/
.. _`Kubernetes`: https://kubernetes.io/
.. _`Scientific Linux`: https://www.scientificlinux.org/
.. _`Ubuntu`: http://www.ubuntu.com/
.. _`OpenNebula`: http://www.opennebula.org/
.. _`OpenStack`: http://www.openstack.org/
.. _`Amazon Web Services`: https://aws.amazon.com/
.. _`Google Cloud`: http://cloud.google.com/
.. _`Microsoft Azure`: http://azure.microsoft.com/
.. _`IM`: https://github.com/grycap/im
.. _`PyYAML`: http://pyyaml.org/wiki/PyYAML
.. _`PLY`: http://www.dabeaz.com/ply/
.. _`Requests`: http://docs.python-requests.org/
.. _`EC3 Command-line Interface`: http://ec3.readthedocs.org/en/devel/ec3.html
.. _`Command templates`: http://ec3.readthedocs.org/en/devel/ec3.html#command-templates
.. _`Authorization file`: http://ec3.readthedocs.org/en/devel/ec3.html#authorization-file
.. _`Templates`: http://ec3.readthedocs.org/en/devel/templates.html
.. _`templates documentation`: http://ec3.readthedocs.org/en/devel/templates.html#ec3-types-of-templates
.. _`Docker Hub`: https://hub.docker.com/r/grycap/ec3/
.. _`EC3aaS`: http://servproject.i3m.upv.es/ec3/
.. _`sshpass`: https://gist.github.com/arunoda/7790979
.. _`ubuntu-ec2`: https://github.com/grycap/ec3/blob/devel/templates/ubuntu-ec2.radl
.. _`IM manual`: https://imdocs.readthedocs.io/en/latest/manual.html
.. _`jsonschema`: https://github.com/Julian/jsonschema
.. _`GitHub Container Regitry`: https://github.com/grycap/ec3/pkgs/container/ec3