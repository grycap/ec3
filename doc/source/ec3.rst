
.. _ec3-cli:

Command-line Interface
======================

The program is called like this::

   $ ec3 [-l <file>] [-ll <level>] [-q] launch|list|show|templates|ssh|reconfigure|destroy [args...]

.. program:: ec3
.. option:: -l <file>, --log-file <file>

   Path to file where logs are written. Default value is standard output error.

.. option:: -ll <level>, --log-level <level>

   Only write in the log file messages with level more severe than the indicated:
   ``1`` for `debug`, ``2`` for `info`, ``3`` for `warning` and ``4`` for `error`.

.. option:: -q, --quiet

   Don't show any message in console except the front-end IP.

Command ``launch``
------------------

To deploy a cluster issue this command::

   ec3 launch <clustername> <template_0> [<template_1> ...] [-a <file>] [-u <url>] [-y]

.. program:: ec3 launch
.. option:: clustername

   Name of the new cluster.

.. option:: template_0 ...

   Template names that will be used to deploy the cluster. ec3 tries to find files
   with these names and extension ``.radl`` in ``~/.ec3/templates`` and
   ``/etc/ec3/templates``. Templates are `RADL`_ descriptions of the virtual machines
   (e.g., instance type, disk images, networks, etc.) and contextualization scripts.
   See :ref:`cmd-templates` to list all available templates.

.. option:: --add

   Add a piece of RADL. This option is useful to set some features. The following example deploys a cluster with the Torque LRMS with up to four working nodes: 

      ./ec3 launch mycluster torque ubuntu-ec2 --add "system wn ( ec3_max_instances = 4 )"

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

   If option -p indicated, print RADL in JSON format instead.

.. option:: --on-error-destroy

   If the cluster deployment fails, try to destroy the infrastructure (and relinquish the resources).

.. option:: -y, --yes

   Do not ask for confirmation when the connection to IM is not secure. Proceed anyway.

Command ``reconfigure``
-----------------------

The command reconfigures a previously deployed clusters. It can be called after a
failed deployment (resources provisioned will be maintained and a new attempt to configure them will take place).
It can also be used to apply a new configuration to a running cluster::

   ec3 reconfigure <clustername>

.. program:: ec3 reconfigure

.. option:: -a <file>, --auth-file <file>

   Append authorization entries in the provided file. See :ref:`auth-file`.

.. option:: --add

   Add a piece of RADL. This option is useful to include additional features to a running cluster.
   The following example updates the maximum number of working nodes to four::

      ./ec3 reconfigure mycluster --add "system wn ( ec3_max_instances = 4 )"

.. option:: -r, --reload

   Reload templates used to launch the cluster and reconfigure it with them
   (useful if some templates were modified).

Command ``ssh``
---------------

The command opens a SSH session to the infrastructure front-end::

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

   ec3 show <clustername> [-r] [--json]

.. program:: ec3 show
.. option:: -r, --refresh

   Get the current state of the cluster before printing the information.

.. option:: --json

   Print RADL description in JSON format.

Command ``list``
----------------

The command print a table with information about the clusters that have been launched::

   ec3 list [-r] [--json]

.. program:: ec3 list
.. option:: -r, --refresh

   Get the current state of the cluster before printing the information.

.. option:: --json

   Print the information in JSON format.

.. _cmd-templates:

Command ``templates``
---------------------

The command displays basic information about the available templates like *name*,
*kind* and a *summary* description::

   ec3 templates [-s/--search <pattern>] [-f/--full-description] [--json]

.. program:: ec3 templates

.. option:: -s, --search

   Show only templates in which the ``<pattern>`` appears in the description.

.. option:: -n, --name

   Show only the template with that name.

.. option:: -f, --full-description

   Instead of the table, it shows all the information about the templates.

.. option:: --json

   Print the information in JSON format.
   
If you want to see more information about templates and its kinds in EC3, visit `Templates`_.

Command ``clone``
-----------------

The command clones an infrastructure front-end previously deployed from one provider to another::

   ec3 clone <clustername> [-a/--auth-file <file>] [-u <url>] [-d/--destination <provider>] [-e]

.. program:: ec3 clone

.. option:: -a <file>, --auth-file <file>

   New authorization file to use to deploy the cloned cluster. See :ref:`auth-file`.

.. option:: -d <provider>, --destination <provider>

   Provider ID, it must match with the id provided in the auth file. See :ref:`auth-file`.

.. option:: -u <url>, --xmlrpc-url <url>

   URL to the IM XML-RPC service. If not indicated, EC3 uses the default value.

.. option:: -e, --eliminate

   Indicate to destroy the original cluster at the end of the clone process. If not indicated, EC3 leaves running the original cluster.

Command ``migrate``
-----------------

The command migrates an infrastructure and its runnign tasks previously deployed from one provider to another. It is mandatory that the original cluster to migrate had been deployed with SLURM and BLCR, if not, the migration process can't be performed.::

   ec3 migrate <clustername> [-b/--bucket <bucket_name>] [-a/--auth-file <file>] [-u <url>] [-d/--destination <provider>] [-e]

.. program:: ec3 migrate

.. option:: -b <bucket_name>, --bucket <bucket_name>

   Bucket name of an already created bucket in the S3 account displayed in the auth file.
   
.. option:: -a <file>, --auth-file <file>

   New authorization file to use to deploy the cloned cluster. It is mandatory to have valid AWS credentials in this file to perform the migration operation, since it uses Amazon S3 to store checkpoint files from jobs running in the cluster. See :ref:`auth-file`.

.. option:: -d <provider>, --destination <provider>

   Provider ID, it must match with the id provided in the auth file. See :ref:`auth-file`.

.. option:: -u <url>, --xmlrpc-url <url>

   URL to the IM XML-RPC service. If not indicated, EC3 uses the default value.

.. option:: -e, --eliminate

   Indicate to destroy the original cluster at the end of the migration process. If not indicated, EC3 leaves running the original cluster.

Configuration file
------------------

Default configuration values are read from ``~/.ec3/config.yml``.
If this file doesn't exist, it is generated with all the available options and their default values.

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
the `IM`_ service and the `VMRC`_ service. Each line of the file is composed by pairs of key and
value separated by semicolon, and refers to a single credential. The key and value should
be separated by " = ", that is **an equals sign preceded and followed by one white space
at least**, like this::

   id = id_value ; type = value_of_type ; username = value_of_username ; password = value_of_password

Values can contain "=", and "\\n" is replaced by carriage return. The available keys are:

* ``type`` indicates the service that refers the credential. The services
  supported are ``InfrastructureManager``, ``VMRC``, ``OpenNebula``, ``EC2``,
  ``OpenStack``, ``OCCI``, ``LibCloud``, ``Docker``, ``GCE``, ``Azure``, and ``LibVirt``.

* ``username`` indicates the user name associated to the credential. In EC2
  it refers to the *Access Key ID*. In Azure it refers to the user 
  Subscription ID. In GCE it refers to *Service Account’s Email Address*. 

* ``password`` indicates the password associated to the credential. In EC2
  it refers to the *Secret Access Key*. In GCE it refers to *Service 
  Private Key*. See how to get it and how to extract the private key file from
  `here info <https://cloud.google.com/storage/docs/authentication#service_accounts>`_).

* ``tenant`` indicates the tenant associated to the credential.
  This field is only used in the OpenStack plugin.

* ``host`` indicates the address of the access point to the cloud provider.
  This field is not used in IM and EC2 credentials.

* ``proxy`` indicates the content of the proxy file associated to the credential.
  To refer to a file you must use the function "file(/tmp/proxyfile.pem)" as shown in the example.
  This field is only used in the OCCI plugin.

* ``project`` indicates the project name associated to the credential.
  This field is only used in the GCE plugin.

* ``public_key`` indicates the content of the public key file associated to the credential.
  To refer to a file you must use the function "file(cert.pem)" as shown in the example.
  This field is only used in the Azure plugin. See how to get it
  `here <https://msdn.microsoft.com/en-us/library/azure/gg551722.aspx>`_

* ``private_key`` indicates the content of the private key file associated to the credential.
  To refer to a file you must use the function "file(key.pem)" as shown in the example.
  This field is only used in the Azure plugin. See how to get it
  `here <https://msdn.microsoft.com/en-us/library/azure/gg551722.aspx>`_

* ``id`` associates an identifier to the credential. The identifier should be
  used as the label in the *deploy* section in the RADL.

An example of the auth file::

   id = one; type = OpenNebula; host = oneserver:2633; username = user; password = pass
   id = ost; type = OpenStack; host = ostserver:5000; username = user; password = pass; tenant = tenant
   type = InfrastructureManager; username = user; password = pass
   type = VMRC; host = http://server:8080/vmrc; username = user; password = pass
   id = ec2; type = EC2; username = ACCESS_KEY; password = SECRET_KEY
   id = gce; type = GCE; username = username.apps.googleusercontent.com; password = pass; project = projectname
   id = docker; type = Docker; host = http://host:2375
   id = occi; type = OCCI; proxy = file(/tmp/proxy.pem); host = https://fc-one.i3m.upv.es:11443
   id = azure; type = Azure; username = subscription-id; public_key = file(cert.pem); private_key = file(key.pem)
   id = kub; type = Kubernetes; host = http://server:8080; username = user; password = pass

Notice that the user credentials that you specify are *only* employed to provision the resources
(Virtual Machines, security groups, keypairs, etc.) on your behalf.
No other resources will be accessed/deleted.
However, if you are concerned about specifying your credentials to EC3, note that you can (and should)
create an additional set of credentials, perhaps with limited privileges, so that EC3 can access the Cloud on your behalf.
In particular, if you are using Amazon Web Services, we suggest you use the Identity and Access Management (`IAM`_)
service to create a user with a new set of credentials. This way, you can rest assured that these credentials can
be cancelled at anytime. 

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
.. _`IM`: http://www.grycap.upv.es/im
.. _`YAML`: http://yaml.org/
.. _`VMRC`: http://www.grycap.upv.es/vmrc
.. _`IAM`: http://aws.amazon.com/iam/
.. _`Templates`: http://ec3.readthedocs.org/en/latest/templates.html

