
.. _ec3-cli:

EC3 Command-line Interface
==========================

The program is called like this::

   $ ec3 [-l <file>] [-ll <level>] [-q] launch|list|show|templates|ssh|reconfigure|destroy [args...]

.. program:: ec3
*  -l <file>, --log-file <file>

   Path to file where logs are written down. Default value is standard output error.

*  -ll <level>, --log-level <level>

   Only write down in the log file messages with level more severe than the indicated:
   ``1`` for `debug`, ``2`` for `info`, ``3`` for `warning` and ``4`` for `error`.

*  -q, --quiet

   Don't show any message in console except front-end IP messages.

Command ``launch``
------------------

The command to deploy a cluster is like this::

   ec3 launch <clustername> <template_0> [<template_1> ...] [-a <file>] [-u <url>] [-y]

.. program:: ec3 launch
*  clustername

   Name to refer the new cluster in other commands.

*  template_0 ...

   Template names that will be used to deploy the cluster. The tool try to find files
   with these names and extension ``.radl`` in ``~/.ec3/templates`` and
   ``/etc/ec3/templates``. Templates are `RADL`_ descriptions of the virtual machines
   (e.g., instance type, disk images, networks, etc.) and contextualization scripts.
   See `Command templates`_ to list all available templates. 
   
*  --add

   Add a piece of RADL. This option is useful to set some features. Next example launches a
   torque cluster with up to four working nodes::

      ./ec3 launch mycluster torque ubuntu-ec2 --add "system wn ( ec3_max_instances = 4 )"

*  -u <url>, --xmlrpc-url <url>

   URL to the IM XML-RPC service.

*  -a <file>, --auth-file <file>

   Path to the authorization file, see `Authorization file`_. This option is compulsory.

*  --dry-run

   Validate options but do not launch the cluster.

*  -n, --not-store

   The new cluster will not be stored in the local database.
 
*  -p, --print

   Print final RADL description if the cluster after cluster being successfully configured.

*  --json

   If :option:`-p` indicated, print RADL in JSON format instead.

*  --on-error-destroy

   If the process fails, try to destroy the infrastructure.

*  -y, --yes

   Don't ask to continue when the connection to IM is not secure.

Command ``reconfigure``
-----------------------

The command reconfigures an infrastructure launched previously. It can be called after a
failed launching::

   ec3 reconfigure <clustername>

.. program:: ec3 reconfigure

*  -a <file>, --auth-file <file>

   Append authorization entries in the provided file. See `Authorization file`_.

*  --add

   Add a piece of RADL. This option is useful to set some features. Next example updates
   the maximum number of working nodes to four::

      ./ec3 reconfigure mycluster --add "system wn ( ec3_max_instances = 4 )"

*  -r, --reload

   Reload templates used to launch the cluster and reconfigure the cluster with them
   (useful if some templates were modified).

Command ``ssh``
---------------

The command opens a SSH session into the infrastructure front-end::

   ec3 ssh <clustername>

.. program:: ec3 ssh

*  --show-only

   Print the command line to invoke SSH and exit.

Command ``destroy``
-------------------

The command undeploys the cluster and removes the associated information in the local database.::

   ec3 destroy <clustername> [--force] [-y]

.. program:: ec3 destroy
*  --force

   Removes local information of the cluster even when the cluster could not be undeployed successfully.
   
*  -y, --yes

   Don't ask to confirm the deleting process.

Command ``show``
----------------

The command prints the RADL description of the cluster stored in the local database::

   ec3 show <clustername> [-r] [--json]

.. program:: ec3 show
*  -r, --refresh

   Get the current state of the cluster before printing the information.

*  --json

   Print RADL description in JSON format.

Command ``list``
----------------

The command print a table with information about the clusters that have been launched::

   ec3 list [-r] [--json]

.. program:: ec3 list
*  -r, --refresh

   Get the current state of the cluster before printing the information.

*  --json

   Print the information in JSON format.

.. _cmd-templates:

Command ``Templates``
---------------------

The command displays basic information about the available templates like *name*,
*kind* and a *summary* description::

   ec3 templates [-s/--search <pattern>] [-f/--full-description] [--json]

.. program:: ec3 templates

*  -s, --search

   Show only templates in which the ``<pattern>`` appears in the description.

*  -n, --name

   Show only the template with that name.

*  -f, --full-description

   Instead of the table, it shows all the information about the templates.

*  --json

   Print the information in JSON format.

Configuration file
------------------

Although it is easy to find and change the default values for the command-line options in
the `ec3` python code, we consider an alternative. Default values are read from
``~/.ec3/config.yml``. If this file doesn't exist, it is generated 
with all the available options and their default values.

The file is formated in `YAML`_. The options that are related to files admit the next
values:

* an scalar: it will be treated as the content of the file, e.g.::

   auth_file: |
      type = OpenNebula; host = myone.com:9999; username = user; password = 1234
      type = EC2; username = AKIAAAAAAAAAAAAAAAAA; password = aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        
* a mapping with the key ``filename``: it will be treated as the file path, e.g.::

   auth_file:
      filename: /home/user/auth.txt

* a mapping with the key ``stream``: it will select either standard output (``stdout``)
  or standard error (``stderr``), e.g.::

   log_file:
      stream: stdout

.. _auth-file:

Authorization file
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
.. _`OpenNebula`: http://www.opennebula.org/
.. _`OpenStack`: http://www.openstack.org/
.. _`Amazon Web Services`: https://aws.amazon.com/
.. _`IM`: https://github.com/grycap/im
.. _`YAML`: http://yaml.org/
.. _`EC3 Command-line Interface`: https://github.com/grycap/ec3/blob/devel/doc/build/md/ec3.rst#ec3-command-line-interface
.. _`Command templates`: https://github.com/grycap/ec3/blob/devel/doc/build/md/ec3.rst#command-templates
.. _`Authorization file`: https://github.com/grycap/ec3/blob/devel/doc/build/md/ec3.rst#authorization-file
.. _`Templates`: https://github.com/grycap/ec3/blob/devel/doc/build/md/templates.rst#templates
