
Frequently Asked Questions
==========================

These are some frequently asked questions that might solve your doubts when using EC3.

General FAQs
------------

**What Cloud Providers are supported by EC3 (Elastic Cloud Computing Cluster)?**

Currently, EC3 supports `EGI Fedcloud`_, `Fogbow`_, `OpenNebula`_, `Amazon EC2`_, `OpenStack`_, `OCCI`_, `LibCloud`_, `Docker`_, `Microsoft Azure`_, `Google Cloud Engine`_ and `LibVirt`_.
All providers and interfaces are supported by the `CLI`_ interface.
However, from the `EC3aaS`_ ATMOSPHERE interface, only support for Fogbow is provided. 

**What Local Resource Management Systems (LRMS) are supported by EC3?**

Currently, EC3 supports `Kubernetes`_, `SLURM`_, `Torque`_, `Apache Mesos`_, `HTCondor`_, `Nomad`_ and `SGE`_. Support for new LRMSs is comming soon, stay tunned!

**Is it necessary to indicate a LRMS recipe in the deployment?**

Yes, it is *mandatory*, because the cluster needs to have an LRMS system installed. 
This is why the LRMS recipes are considered *main* recipes, needed to perform a deployment with EC3.

**Is it secure to provide my credentials to EC3?**

The user credentials that you specify are *only* employed to provision the resources
(Virtual Machines, security groups, keypairs, etc.) on your behalf.
No other resources will be accessed/deleted.
However, if you are concerned about specifying your credentials to EC3, note that you can (and should)
create an additional set of credentials, perhaps with limited privileges, so that EC3 can access the Cloud on your behalf.

**Can I configure different software packages than the ones provided with EC3 in my cluster?**

Yes, you can configure them by using the EC3 `CLI`_ interface. Thus, you will need to provide a valid Ansible recipe to 
automatically install the dependence. You can also contact us by using the contact section, and we would try to add the software package you need.

**Why am I experimenting problems with Centos 6 when trying to deploy a Mesos cluster?**

Because the recipe of Mesos provided with EC3 is optimized for Centos 7 as well as Ubuntu 14.04. If you want to deploy a Mesos cluster, we encourage you to use one of each operative systems.

**Which is the best combination to deploy a Galaxy cluster?**

The best configuration for a elastic Galaxy cluster is to select Torque as a LRMS and install the NFS package. Support for Galaxy in SGE is not provided. Moreover, we have detected problems when using Galaxy with SLURM. So, we encourage you to use Torque and NFS in the EC3aaS and also with the EC3 CLI.


ATMOSPHERE EC3aaS Webpage
-------------------------

**Is my cluster ready when I receive its IP using the EC3aaS webpage?**

Probably not, because the process of configuring the cluster is a batch process that takes several minutes, depending on the chosen configuration.
However, you are allowed to log in the front-end machine of the cluster since the moment it is deployed. To know if the cluster is configured, you can use the command *is_cluster_ready*. It will check if the cluster has been configured or if the configuration process is still in progress. If the command *is_cluster_ready* is not recognised, wait a few seconds and try again, because this command is also installed in the configuration process.

**Why can't I deploy an hybrid cluster using the EC3aaS webpage?**

Because no support is provided yet by the EC3aaS service.
If you want to deploy a hybrid cluster, we encourage you to use the `CLI`_ interface.

**Why can I only access to Fogbow cloud provider while other Cloud providers are supported by EC3?**

Because this website is specifically developed for the `ATMOSPHERE`_ project.
Other Cloud providers such as `OpenNebula`_, `Amazon EC2`_, `OpenStack`_ and `EGI Fedcloud`_ are supported in the general `EC3aaS website`_.
If you want to use another supported Cloud provider, like `Microsoft Azure`_ or `Google Cloud Engine`_, we encourage you to use the `CLI`_ interface.

**Why can't I download the private key of my cluster?**

If you are experimenting problems downloading the private key of your cluster,
please, try with another browser. The website is currently optimized for Google Chrome.

**Can I configure software packages in my cluster that are not available in the wizard?**

You can configure them by using the EC3 `CLI`_ interface. Thus, you will need to provide a valid Ansible recipe to 
automatically install the dependence. You can also contact us by using the contact section, and we would try to add the software package you need.

.. _`CLI`: http://ec3.readthedocs.org/en/latest/ec3.html
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
.. _`SLURM`: http://www.schedmd.com/slurmdocs/slurm.html
.. _`Torque`: http://www.adaptivecomputing.com/products/open-source/torque/
.. _`SGE`: http://sourceforge.net/projects/gridscheduler/
.. _`Apache Mesos`: http://mesos.apache.org/
.. _`AppDB portal`: https://appdb.egi.eu
.. _`EGI FedCloud`: https://www.egi.eu/infrastructure/cloud/
.. _`HTCondor`: https://research.cs.wisc.edu/htcondor/
.. _`Fogbow`: http://www.fogbowcloud.org/
.. _`EGI Fedcloud`: https://www.egi.eu/services/cloud-compute/
.. _`Kubernetes`: https://kubernetes.io/
.. _`Nomad`: https://www.nomadproject.io/
.. _`ATMOSPHERE`: https://www.atmosphere-eubrazil.eu/
.. _`EC3aaS website`: http://servproject.i3m.upv.es/ec3/


