
Frequently Asked Questions
==========================

These are some frequently asked questions that might solve your doubts when using EC3.

General FAQs
------------

**What Cloud Providers are supported by EC3 (Elastic Cloud Computing Cluster)?**

Currently, EC3 supports `OpenNebula`_, `Amazon EC2`_, `OpenStack`_, `OCCI`_, `LibCloud`_, `Docker`_, `Microsoft Azure`_, `Google Cloud Engine`_ and `LibVirt`_.
All providers and interfaces are supported by the `CLI`_ interface.
However, from the `EC3aaS`_ interface, only support for Amazon EC2 and OpenNebula is provided. More providers will be added soon.


**It is secure to provide my credentials to EC3?**

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

**Is my cluster ready when I receive the IP of the cluster using the EC3aaS webpage?**

Probably not, because the process of configuring the cluster might be working.
But this process do not impede you to log in in the front-end machine of the cluster.
If you can't find the desired software packages installed or the chosen LRMS commands available, please, wait a little bit.
A way to know if the cluster is already configured is when no ansible processes are running in the virtual machine.

**Why I can't deploy an hybrid cluster using the EC3aaS webpage?**

Because no support is provided yet by the EC3aaS service. 
If you want to deploy an hybrid cluster, we encourage you to use the `CLI`_ interface.

**Why I only can access to Amazon EC2 and OpenNebula Cloud providers while other Cloud providers are supported by EC3?**

Because no support is provided yet by the EC3aaS service. 
If you want to use another supported Cloud provider, like `Microsoft Azure`_, `Openstack`_ or `Google Cloud Engine`_, we encourage you to use the `CLI`_ interface.


**Why I am receiving this error "InvalidParameterCombination - Non-Windows instances with a virtualization type of 'hvm' are currently not supported for this instance type" when I deploy a cluster in Amazon EC2?**

This error is showed by the Cloud provider, because the instance type and the Amazon Machine Image selected are incompatible.  
The Linux AMI with HVM virtualization cannot be used to launch a non-cluster compute instance. 
Select another AMI with with a virtualization type of paravirtual and try again.


**Why I am receiving this error "VPCResourceNotSpecified - The specified instance type can only be used in a VPC. A subnet ID or network interface ID is required to carry out the request." when I deploy a cluster in Amazon EC2?**

This error is showed by the Cloud provider, because the instance type selected can only be used in a VPC.  
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
.. _`Amazon VPC`: http://aws.amazon.com/es/vpc/
