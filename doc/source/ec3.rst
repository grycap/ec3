

EC3 Command-line Interface
==========================

The program is called like this::

   $ ec3 [-l <file>] [-ll <level>] [-q] launch|list|show|templates|ssh|reconfigure|destroy [args...]

.. program:: ec3
.. option:: -l <file>, --log-file <file>

  Path to file where logs are written down. Default value is standard output error.

.. option:: -ll <level>, --log-level <level>

  Only write down in the log file messages with level more severe than the indicated:
  ``1`` for `debug`, ``2`` for `info`, ``3`` for `warning` and ``4`` for `error`.

.. option:: -q, --quiet

   Don't show any message in console except front-end IP messages.

Command ``launch``
------------------

The command to deploy a cluster is like this::

   ec3 launch <clustername> <template> -a <file> [-u <url>] [-y]

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

.. option:: -y, --yes

   Don't ask to continue when the connection to IM is not secure.

Command ``reconfigure``
-----------------------

The command reconfigures an infrastructure launched previously. It can be called after a
failed launching::

   ec3 reconfigure <clustername>

.. program:: ec3 reconfigure

Command ``ssh``
---------------

The command opens a SSH session into the infrastructure front-end::

   ec3 ssh <clustername>

.. program:: ec3 ssh

.. option:: --show-only

    Print the command line to invoke SSH and exit.

Command ``destroy``
-------------------

The command undeploys the cluster and removes the associated information in the local database.::

   ec3 destroy <clustername> [--force]

.. program:: ec3 destroy
.. option:: --force

   Removes local information of the cluster even when the cluster could not be undeployed successfully.

Command ``show``
----------------

The command prints the RADL description of the cluster stored in the local database::

   ec3 show <clustername> [--refresh] [--json]

.. program:: ec3 show
.. option:: --refresh

   Get the current state of the cluster before printing the information.

.. option:: --json

   Print RADL description in JSON format.

Command ``list``
----------------

The command print a table with information about the clusters that have been launched::

   ec3 list [--refresh] [--json]

.. program:: ec3 list
.. option:: --refresh

   Get the current state of the cluster before printing the information.

.. option:: --json

   Print the information in JSON format.

Command ``templates``
---------------------

The command displays basic information about the available templates like *name*,
*kind* and a *summary* description::

   ec3 templates [-s/--search <pattern>] [-f/--full-description] [--json]

.. program:: ec3 templates

.. option:: -s, --search

   Show only templates in which the ``<pattern>`` appears in the description.

.. option:: -f, --full-description

   Instead of the table, it shows all the information about the templates.

.. option:: --json

   Print the information in JSON format.


.. _auth-file:

Authorization File
==================

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
.. _`OpenNebula`: http://www.opennebula.org/
.. _`OpenStack`: http://www.openstack.org/
.. _`Amazon Web Services`: https://aws.amazon.com/
.. _`IM`: https://github.com/grycap/im
