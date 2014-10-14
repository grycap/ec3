
Elastic Cloud Computing Cluster (EC3)
=====================================

Elastic Cloud Computing Cluster (EC3) is a tool to create elastic virtual clusters on top
of Infrastructure as a Service (IaaS) providers. The cluster are self-managed with
`CLUES`_.

Installation
------------

The program :program:`ec3` requires Python 2.6+ and the python library `paramiko
<http://www.lag.net/paramiko/>`_. The former library is available in Debian and Red Hat
based distribution as ``python-paramiko``. Also can be installed from ``pip``::

   pip install parmiko

:program:`ec3` can be download from `this <https://github.com/gc3-uzh-ch/elasticluster>`_
git repository::

   git clone https://github.com/grycap/ec3

In the created directory there is the executable file ``ec3``, which is command-line
interface described next.

Basic example with Amazon EC2
-----------------------------

First create a file ``auth.txt`` with a single line like this::

   id = provider ; type = EC2 ; username = <<Access Key ID>> ; password = <<Secret Access Key>>

Replace ``<<Access Key ID>>`` and ``<<Secret Access Key>>`` by the corresponding values
for the EC2 account where the cluster will be deployed. This file is the :ref:`authorization
file <auth-file>`, and can have more than one credentials.

The next command deploys a cluster based on `Ubuntu`_ images with `TORQUE`_::

   ec3 launch mycluster torque --add ubuntu-ec2 -a auth.txt 

It can take several minutes...

The next command shows basic information about the deployed clusters::

    $ ec3 list
     name    state          IP        nodes 
    ----------------------------------------
      c0   configured  158.42.105.11    0   
 
EC3 Command-line Interface
--------------------------

The program is called like this::

   $ ec3 [-l <file>] [-ll <level>] [-q]  launch|list|show|destroy [args...]

.. program:: ec3
.. option:: -l <file>, --log-file <file>

  Path to file where logs are written down. Default value is standard output error.

.. option:: -ll <level>, --log-level <level>

  Only write down in the log file messages with level more severe than the indicated:
  ``1`` for `debug`, ``2`` for `info`, ``3`` for `warning` and ``4`` for `error`.

.. option:: -q, --quiet

   Don't show any message in console except front-end IP messages.

Command ``launch``
^^^^^^^^^^^^^^^^^^

The command to deploy a cluster is like this::

   ec3 launch <clustername> <template> -a <file> -u <url>

.. program:: ec3 launch
.. option:: clustername

   Name to refer the new cluster in other commands.

.. option:: template

   `Recipe` name that will be used to deploy the cluster. The tool try to find a file
   with the indicated name and extension ``.radl`` in ``~/.ec3/templates`` and
   ``/etc/ec3/templates``. These recipes are `RADL`_ descriptions of the virtual machines
   (e.g., instance type, disk images, networks, etc.) and contextualization scripts.

   The following recipes are provided:

   * ``torque``: deploys `TORQUE`_ (from distribution repositories), `MAUI`_ and `CLUES`_.
   * ``slurm``: deploys `SLURM`_ and `CLUES`_.
   * ``sge``: deploys Sun Grid Engine and `CLUES`_.

   They have to be combined with another recipe that set the OS disk image, see :option:`--add`.

.. option:: --add <template>

   Add the indicated recipe to the previously specified. Two recipes for Amazon EC2 provider
   are provided:

   * ``ubuntu-ec2``: `Ubuntu`_ 14.04 64 bits.
   * ``sl6-ec2``: `Scientific Linux`_ SL6 64 bits.

.. option:: -u <url>, --xmlrpc-url <url>

   URL to the IM XML-RPC service.

.. option:: -a <file>, --auth-file <file>

   Path to the authorization file, see :ref:`auth-file`. This option is compulsory.

.. option:: --dry-run

   Validate options but do not launch the cluster.

.. option:: -n, --not-store

   The new cluster will not be stored in the local database.
 
.. option:: -p, --print

   Print final RADL description if the cluster after cluster being successfully configured.

.. option:: --json

   If :option:`-p` indicated, print RADL in JSON format instead.

.. option:: --on-error-destroy

   If the process fails, try to destroy the infrastructure.

Command ``reconfigure``
^^^^^^^^^^^^^^^^^^^^^^^

   The command reconfigures an infrastructure launched previously. It can be called after a
   failed launching::

      ec3 reconfigure <clustername>

.. program:: ec3 reconfigure

Command ``destroy``
^^^^^^^^^^^^^^^^^^^

   The command undeploys the cluster and removes the associated information in the local database.::

      ec3 destroy <clustername> [--force]

.. program:: ec3 destroy
.. option:: --force

   Removes local information of the cluster even when the cluster could not be undeployed successfully.

Command ``show``
^^^^^^^^^^^^^^^^

   The command prints the RADL description of the cluster stored in the local database::

       ec3 show <clustername> [--refresh] [--json]

.. program:: ec3 show
.. option:: --refresh

   Get the current state of the cluster before printing the information.

.. option:: --json

   Print RADL description in JSON format.

Command ``list``
^^^^^^^^^^^^^^^^

   The command print a table with information about the clusters that have been launched::

      ec3 list [--refresh] [--json]

.. program:: ec3 list
.. option:: --refresh

   Get the current state of the cluster before printing the information.

.. option:: --json

   Print the information in JSON format.

.. _auth-file:

Authorization File
------------------

The authorization file stores in plain text the credentials to access the cloud providers,
the IM service and the VMRC service. Each line of the file is composed by pairs of key and
value separated by semicolon, and refers to a single credential. The key and value should
be separated by " = ", that is **an equals sign preceded and followed by one white space
at least**, like this::

   id = id_value ; type = value_of_type ; username = value_of_username ; password = value_of_password 

Values can contain "=", and "\\n" is replaced by carriage return. The available keys are:

* ``type`` indicates the service that refers the credential. The services
  supported are ``InfrastructureManager``, ``VMRC``, ``OpenNebula``, ``EC2``,
  ``OpenStack``, ``OCCI``, ``LibCloud`` and ``LibVirt``.

* ``username`` indicates the user name associated to the credential. In EC2 and
  OpenStack it refers to the *Access Key ID*.

* ``password`` indicates the password associated to the credential. In EC2 and
  OpenStack it refers to the *Secret Acess Key*.

* ``host`` indicates the address of the access point to the cloud provider.
  This field is not used in IM and EC2 credentials.

* ``id`` associates an identifier to the credential. The identifier should be
  used as the label in the *deploy* section in the RADL.

.. _`CLUES`: http://www.grycap.upv.es/clues/
.. _`RADL`: http://www.grycap.upv.es/im/doc/radl.html
.. _`TORQUE`: http://www.adaptivecomputing.com/products/open-source/torque
.. _`MAUI`: http://www.adaptivecomputing.com/products/open-source/maui/
.. _`SLURM`: http://slurm.schedmd.com/
.. _`Scientific Linux`: https://www.scientificlinux.org/
.. _`Ubuntu`: http://www.ubuntu.com/
