
.. _templates:

Templates
=========

EC3 recipes are described in a superset of `RADL`_, which is a specification of virtual
machines (e.g., instance type, disk images, networks, etc.) and contextualization
scripts.

Basic structure
---------------

An RADL document has the following general structure::

   network <network_id> (<features>)

   system <system_id> (<features>)

   configure <configure_id> (<Ansible recipes>)

   deploy <system_id> <num> [<cloud_id>]

The keywords ``network``, ``system`` and ``configure`` assign some *features*
or *recipes* to an identity ``<id>``. The features are a list of constrains
separated by ``and``, and a constrain is formed by
``<feature name> <operator> <value>``. For instance::

   system tomcat_node (
      cpu.count = 4 and
      memory.size >= 1024M and
      net_interface.0.connection = 'net'
   )

This RADL defines a *system* with the feature ``cpu.count`` equal to four, the feature
``memory.size`` greater or equal than ``1024M`` and with the feature
``net_interface.0.connection`` bounded to ``'net'``.

The ``deploy`` keyword is a request to deploy a number of virtual machines.
Some identity of a cloud provider can be specified to deploy on a particular cloud.

EC3 types of Templates 
----------------------
In EC3, there are three types of templates::

* ``images``, that includes the ``system`` section of the basic template. It describes the main features of the machines that will compose the cluster, like the operating system or the CPU and RAM memory required;
* ``main``, that includes the ``deploy`` section of the frontend. Also, they include the configuration of the chosen LRMS.
* ``component``, for all the recipes that install and configure software packages that can be useful for the cluster.

In order to deploy a cluster with EC3, it is mandatory to indicate in the ``ec3 launch`` command, *one* recipe of kind ``main`` and *one* recipe of kind ``image``.
The ``component`` recipes are optional, and you can include all that you need.

To consult the type (*kind*) of template from the ones offered with EC3, 
simply use the ``ec3 templates`` command like in the example above:

   $ ./ec3 templates
   
             name             kind                                         summary                                      
   ---------------------------------------------------------------------------------------------------------------------
             blcr           component Tool for checkpoint the applications.                            			 
          centos-ec2         images   CentOS 6.5 amd64 on EC2.                                               		  
           ckptman          component Tool to automatically checkpoint applications running on Spot instances.    		   
            docker          component An open-source tool to deploy applications inside software containers.      			
           gnuplot          component A program to generate two- and three-dimensional plots.                     		   
             nfs            component Tool to configure shared directories inside a network.                       			 
            octave          component A high-level programming language, primarily intended for numerical computations  			
           openvpn          component Tool to create a VPN network.                                                     		   
             sge              main    Install and configure a cluster SGE from distribution repositories.               			 
            slurm             main    Install and configure a cluster SLURM 14.11 from source code.                      			
            torque            main    Install and configure a cluster TORQUE from distribution repositories.            			
         ubuntu-azure        images   Ubuntu 12.04 amd64 on Azure.                                                      		 
          ubuntu-ec2         images   Ubuntu 14.04 amd64 on EC2.                                                        


Network Features
----------------

Under the keyword ``network`` there are the features describing a Local Area
Network (LAN) that some virtual machines can share in order to communicate
to themselves and to other external networks.
The supported features are:

``outbound = yes|no``
   Indicate whether the IP that will have the virtual machines in this network
   will be public (accessible from any external network) or private.
   If ``yes``, IPs will be public, and if ``no``, they will be private.
   The default value is ``no``.


System Features
---------------

Under the keyword ``system`` there are the features describing a virtual
machine.  The supported features are:

``image_type = vmdk|qcow|qcow2|raw``
   Constrain the virtual machine image disk format.

``virtual_system_type = '<hypervisor>-<version>'``
   Constrain the hypervisor and the version used to deploy the virtual machine.

``price <=|=|=> <positive float value>``
   Constrain the price per hour that will be paid, if the virtual machine is
   deployed in a public cloud.

``cpu.count <=|=|=> <positive integer value>``
   Constrain the number of virtual CPUs in the virtual machine.

``cpu.arch = i686|x86_64``
   Constrain the CPU architecture.

``cpu.performance <=|=|=> <positive float value>ECU|GCEU``
   Constrain the total computational performance of the virtual machine.

``memory.size <=|=|=> <positive integer value>B|K|M|G``
   Constrain the amount of *RAM* memory (main memory) in the virtual
   machine.

``net_interface.<netId>``
   Features under this prefix refer to virtual network interface attached to
   the virtual machine.

``net_interface.<netId>.connection = <network id>``
   Set the virtual network interface is connected to the LAN with ID
   ``<network id>``.

``net_interface.<netId>.ip = <IP>``
   Set a static IP to the interface, if it is supported by the cloud provider.

``net_interface.<netId>.dns_name = <string>``
   Set the string as the DNS name for the IP assigned to this interface. If the
   string contains ``#N#`` they are replaced by a number that is distinct for
   every virtual machine deployed with this ``system`` description.

``disk.<diskId>.<feature>``
   Features under this prefix refer to virtual storage devices attached to
   the virtual machine. ``disk.0`` refers to system boot device.

``disk.<diskId>.image.url = <url>``
   Set the source of the disk image. The URI designates the cloud provider:

   * ``one://<server>:<port>/<image-id>``, for OpenNebula;
   * ``ost://<server>:<port>/<ami-id>``, for OpenStack; and
   * ``aws://<region>/<ami-id>``, for Amazon Web Service.

   Either ``disk.0.image.url`` or ``disk.0.image.name`` must be set.

``disk.<diskId>.image.name = <string>``
   Set the source of the disk image by its name in the VMRC server.
   Either ``disk.0.image.url`` or ``disk.0.image.name`` must be set.

``disk.<diskId>.type = swap|iso|filesystem``
   Set the type of the image.

``disk.<diskId>.device = <string>``
   Set the device name, if it is disk with no source set.

``disk.<diskId>.size = <positive integer value>B|K|M|G``
   Set the size of the disk, if it is a disk with no source set.

``disk.0.free_size = <positive integer value>B|K|M|G``
   Set the free space available in boot disk.

``disk.<diskId>.os.name = linux|windows|mac os x``
   Set the operating system associated to the content of the disk.

``disk.<diskId>.os.flavour = <string>``
   Set the operating system distribution, like ``ubuntu``, ``centos``,
   ``windows xp`` and ``windows 7``.

``disk.<diskId>.os.version = <string>``
   Set the version of the operating system distribution, like ``12.04`` or
   ``7.1.2``.

``disk.0.os.credentials.username = <string>`` and ``disk.0.os.credentials.password = <string>``
   Set a valid username and password to access the operating system.

``disk.0.os.credentials.public_key = <string>`` and ``disk.0.os.credentials.private_key = <string>``
   Set a valid public-private keypair to access the operating system.

``disk.<diskId>.applications contains (name=<string>, version=<string>, preinstalled=yes|no)``
   Set that the disk must have installed the application with name ``name``.
   Optionally a version can be specified. Also if ``preinstalled`` is ``yes``
   the application must have already installed; and if ``no``, the application
   can be installed during the contextualization of the virtual machine if it
   is not installed.

Special EC3 Features
^^^^^^^^^^^^^^^^^^^^

There are also other special features related with EC3. These features enable to customize
the behaviour of EC3:

``ec3_max_instances = <integer value>``
   Set maximum number of nodes with this system configuration; a negative value means no constrain.
   The default value is -1.

``ec3_destroy_interval = <positive integer value>``
   Some cloud providers require paying in advance by the hour, like AWS. Therefore, the node will be destroyed
   only when it is idle and at the end of the interval expressed by this option (in seconds).
   The default value is 0.

``ec3_destroy_safe = <positive integer value>``
   This value (in seconds) stands for a security margin to avoid incurring in a new charge for the next hour.
   The instance will be destroyed (if idle) in up to (``ec3_destroy_interval`` - ``ec3_destroy_safe`) seconds.
   The default value is 0.

``ec3_if_fail = <string>``
   Set the name of the next system configuration to try when no more instances can be allocated from a cloud provider.
   Used for hybrid clusters.
   The default value is ''.

System and network inheritance
------------------------------

It is possible to create a copy of a system or a network and to change and add some
features. If feature ``ec3_inherit_from`` is presented, ec3 replaces that object by a
copy of the object pointed out in ``ec3_inherit_from`` and appends the rest of the
features.

Next example shows a system ``wn_ec2`` that inherits features from system ``wn``::

    system wn (
        ec3_if_fail = 'wn_ec2' and
        disk.0.image.url = 'one://myopennebula.com/999' and
        net_interface.0.connection='public'
    )

    system wn_ec2 (
        ec3_inherit_from = system wn and
        disk.0.image.url = 'aws://us-east-1/ami-e50e888c' and
        spot = 'yes' and
        ec3_if_fail = ''
    )

The system ``wn_ec2`` that ec3 sends finally to IM is::

    system wn_ec2 (
        net_interface.0.connection='public' and
        disk.0.image.url = 'aws://us-east-1/ami-e50e888c' and
        spot = 'yes' and
        ec3_if_fail = ''
    )

In case of systems, if system *A* inherits features from system *B*, the
new configure section is composed by the one from system *A* followed by the one of system *B*.
Following the previous example, these are the configured named after the systems::

    configure wn (
    @begin
    - tasks:
      - user: name=user1   password=1234
    @end
    )

    configure wn_ec2 (
    @begin
    - tasks:
      - apt: name=pkg
    @end
    )

Then the configure ``wn_ec2`` that ec3 sends finally to IM is::

    configure wn_ec2 (
    @begin
    - tasks:
      - user: name=user1   password=1234
    - tasks:
      - apt: name=pkg
    @end
    )

Configure Recipes
-----------------

Contextualization recipes are specified under the keyword ``configure``.
Only Ansible recipes are supported currently. They are enclosed between the
tags ``@begin`` and ``@end``, like that::

   configure add_user1 (
   @begin
   ---
     - tasks:
       - user: name=user1   password=1234
   @end
   )

Exported variables from IM
^^^^^^^^^^^^^^^^^^^^^^^^^^

To easy some contextualization tasks, IM publishes a set of variables that
can be accessed by the recipes and have information about the virtual machine.

``IM_NODE_HOSTNAME``
   Hostname of the virtual machine (without the domain).

``IM_NODE_DOMAIN``
   Domain name of the virtual machine.

``IM_NODE_FQDN``
   Complete FQDN of the virtual machine.

``IM_NODE_NUM``
   The value of the substitution ``#N#`` in the virtual machine.

``IM_MASTER_HOSTNAME``
   Hostname (without the domain) of the virtual machine doing the *master*
   role.

``IM_MASTER_DOMAIN``
   Domain name of the virtual machine doing the *master* role.

``IM_MASTER_FQDN``
   Complete FQDN of the virtual machine doing the *master* role.

.. _cmd-include:
Including a recipe from another
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The next RADL defines two recipes and one of them (``add_user1``) is called by
the other (``add_torque``)::

   configure add_user1 (
   @begin
   ---
     - tasks:
       - user: name=user1   password=1234
   @end
   )

   configure add_torque (
   @begin
   ---
     - tasks:
       - include: add_user1.yml
       - yum: name=torque-client,torque-server state=installed
   @end
   )

Including file content
^^^^^^^^^^^^^^^^^^^^^^

If in a ``vars`` map a variable has a map with key ``ec3_file``, ec3 replaces the map by
the content of file in the value.

For instance, there is a file ``slurm.conf`` with content::

    ControlMachine=slurmserver
    AuthType=auth/munge
    CacheGroups=0

The next ansible recipe will copy the content of ``slurm.conf`` into
``/etc/slurm-llnl/slurm.conf``::

    configure front (
    @begin
      - vars:
          SLURM_CONF_FILE:
            ec3_file: slurm.conf
        tasks:
        - copy:
            dest: /etc/slurm-llnl/slurm.conf
            content: "{{SLURM_CONF_FILE}}"
    @end
    )

.. warning::
    Avoid using variables with file content in compact expressions like this::

        - copy: dest=/etc/slurm-llnl/slurm.conf content={{SLURM_CONF_FILE}}

Include RADL content
^^^^^^^^^^^^^^^^^^^^

Maps with keys ``ec3_xpath`` and ``ec3_jpath`` are useful to refer RADL objects and
features from Ansible vars. The difference is that ``ec3_xpath`` prints the object in RADL
format as string, and ``ec3_jpath`` prints objects as YAML maps.  Both keys support the
next paths:

* ``/<class>/*``: refer to all objects with that ``<class>`` and its references; e.g.,
  ``/system/*`` and ``/network/*``.
* ``/<class>/<id>`` refer to an object of class ``<class>`` with id ``<id>``, including
  its references; e.g., ``/system/front``, ``/network/public``.
* ``/<class>/<id>/*`` refer to an object of class ``<class>`` with id ``<id>``, without
  references; e.g., ``/system/front/*``, ``/network/public/*``


Consider the next example::

    network public ( )

    system front (
        net_interface.0.connection = 'public' and
        net_interface.0.dns_name = 'slurmserver' and
        queue_system = 'slurm'
    )

    system wn (
      net_interface.0.connection='public'
    )

    configure slum_rocks (
    @begin
      - vars:
            JFRONT_AST:
                ec3_jpath: /system/front/*
            XFRONT:
                ec3_xpath: /system/front
        tasks:
        - copy: dest=/tmp/front.radl
          content: "{{XFRONT}}"
          when: JFRONT_AST.queue_system == "slurm"
    @end
    )

RADL configure ``slurm_rocks`` is transformed into::

    configure slum_rocks (
    @begin
    - vars:
        JFRONT_AST:
          class: system
          id: front
          net_interface.0.connection:
            class: network
            id: public
            reference: true
          net_interface.0.dns_name: slurmserver
          queue_system: slurm
        XFRONT: |
           network public ()
           system front (
              net_interface.0.connection = 'public' and
              net_interface.0.dns_name = 'slurmserver' and
              queue_system = 'slurm'
           )
      tasks:
      - content: '{{XFRONT}}'
        copy: dest=/tmp/front.radl
        when: JFRONT_AST.queue_system == "slurm"
    @end
    )

Adding your own templates
-------------------------

If you want to add your own customized templates to EC3, you need to consider some aspects:

* For ``image`` templates, respect the frontend and working nodes nomenclatures. The system section for the frontend *must* receive the name ``front``, while at least one type of working node *must* receive the name ``wn``.
* For ``component`` templates, add a ``configure`` section with the name of the component. You also need to add an ``include`` statement to import the configure in the system that you want. See :ref:`cmd-include` for more details.

Also, it is important to provide a ``description`` section in each new template, to be considered by the ``ec3 templates`` command.

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
