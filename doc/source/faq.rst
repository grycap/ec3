
Frequently Asked Questions
==========================

These are some frequently asked questions that might solve your doubts when using EC3.

General FAQs
------------

**What Cloud Providers are supported by EC3 (Elastic Cloud Computing Cluster)?**

Currently, EC3 supports `OpenNebula`_, `Amazon EC2`_, `OpenStack`_, `OCCI`_, `LibCloud`_, `Docker`_, `Microsoft Azure`_, `Google Cloud Engine`_ and `LibVirt`_.
All providers and interfaces are supported by the `CLI`_ interface.
However, from the `EC3aaS`_ interface, only support for Amazon EC2, Openstack and OpenNebula is provided. More providers will be added soon.

**What Local Resource Management Systems (LRMS) are supported by EC3?**

Currently, EC3 supports `SLURM`_, `Torque`_ and `SGE`_. Support for `Apache Mesos`_ is comming soon, stay tunned!

**Is it secure to provide my credentials to EC3?**

The user credentials that you specify are *only* employed to provision the resources
(Virtual Machines, security groups, keypairs, etc.) on your behalf.
No other resources will be accessed/deleted.
However, if you are concerned about specifying your credentials to EC3, note that you can (and should)
create an additional set of credentials, perhaps with limited privileges, so that EC3 can access the Cloud on your behalf.
In particular, if you are using Amazon Web Services, we suggest you use the Identity and Access Management (`IAM`_)
service to create a user with a new set of credentials. This way, you can rest assured that these credentials can
be cancelled at anytime.

EC3aaS Webpage
--------------

**Is my cluster ready when I receive its IP using the EC3aaS webpage?**

Probably not, because the process of configuring the cluster is a batch process that takes several minutes, depending on the chosen configuration.
However, you are allowed to log in the front-end machine of the cluster since the moment it is deployed.
If you can't find the desired software packages installed or the chosen LRMS commands available, please, wait a little bit.
There is a tricky way to find out when the cluster is already configured: When no Ansible processes (named ansible) are running.

**Why can't I deploy an hybrid cluster using the EC3aaS webpage?**

Because no support is provided yet by the EC3aaS service.
If you want to deploy a hybrid cluster, we encourage you to use the `CLI`_ interface.

**Why can I only access to Amazon EC2, Openstack and OpenNebula Cloud providers while other Cloud providers are supported by EC3?**

Because no support is provided yet by the EC3aaS service.
If you want to use another supported Cloud provider, like `Microsoft Azure`_ or `Google Cloud Engine`_, we encourage you to use the `CLI`_ interface.

**What is the correct format for the *endpoint* in the OpenNebula and Openstack wizards?

The user needs to provide EC3 the endpoint of the on-premises Cloud provider. The correct format is *name_of_the_server:port*. 
For example, for Openstack *ostserver:5000*, or for OpenNebula *oneserver:2633*. 
The same format is employed in the authorization file required to use the CLI interface of EC3.

**Why am I receiving this error "InvalidParameterCombination - Non-Windows instances with a virtualization type of 'hvm' are currently not supported for this instance type" when I deploy a cluster in Amazon EC2?**

This error is shown by the Cloud provider, because the instance type and the Amazon Machine Image selected are incompatible.
The Linux AMI with HVM virtualization cannot be used to launch a non-cluster compute instance.
Select another AMI with a virtualization type of paravirtual and try again.

**Why am I receiving this error "VPCResourceNotSpecified - The specified instance type can only be used in a VPC. A subnet ID or network interface ID is required to carry out the request." when I deploy a cluster in Amazon EC2?**

This error is shown by the Cloud provider, because the instance type selected can only be used in a VPC.
To use a VPC, please, employ the CLI interface of EC3. You can specify the name of an existent VPC in the RADL file.
More info about `Amazon VPC`_.


.. _`CLI`: http://servproject.i3m.upv.es/ec3/doc/ec3.html
.. _`EC3aaS`: http://servproject.i3m.upv.es/ec3/
.. _`OpenNebula`: http://www.opennebula.org/
.. _`OpenStack`: http://www.openstack.org/
.. _`Amazon EC2`: https://aws.amazon.com/en/ec2
.. _`OCCI`: http://occi-wg.org/
.. _`Microsoft Azure`: http://azure.microsoft.com/
.. _`Docker`: https://www.docker.com/
.. _`LibVirt`: http://libvirt.org/
.. _`LibCloud`: https://libcloud.apache.org/
.. _`Google Cloud Engine`: https://cloud.google.com/compute/
.. _`Amazon VPC`: http://aws.amazon.com/vpc/
.. _`IAM`: http://aws.amazon.com/iam/
.. _`SLURM`:http://www.schedmd.com/slurmdocs/slurm.html
.. _`Torque`:http://www.adaptivecomputing.com/products/open-source/torque/
.. _`SGE`:http://sourceforge.net/projects/gridscheduler/
.. _`Apache Mesos`:http://mesos.apache.org/