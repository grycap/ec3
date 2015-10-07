Elastic Cloud Computing Cluster (EC3)
=====================================

[Elastic Cloud Computing Cluster (EC3)](http://www.grycap.upv.es) is a tool to create elastic virtual clusters across Infrastructure as a Service (IaaS) providers, either public (such as Amazon Web Services, Google Cloud or Microsoft Azure) or on-premises (such as OpenNebula and OpenStack). We offer recipes to deploy TORQUE (optionally with MAUI) and SLURM clusters that can be self-managed with [CLUES](http://www.grycap.upv.es/clues):

It starts with a single-node cluster and working nodes will be dynamically deployed and provisioned to fit increasing load, in terms of the number of jobs at the LRMS (Local Resource Management System). Working nodes will be undeployed when they are idle. This introduces a cost-efficient approach for Cluster-based computing.
