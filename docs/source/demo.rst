.. ...........................................................................
.. © Copyright IBM Corporation 2020                                          .
.. ...........................................................................

Demo
====

Following set of example scenarios demonstrate how to use the modules of the
**IBM Power Systems HMC collection** content

hmc_update_upgrade
------------------

Update
""""""
The following gif demonstrates the update of a HMC from V9 R1 M910 to V9 R1 M941
using disk source which takes the image from control node.

.. figure:: ../images/demo_hmc_update.gif
   :alt: 

Upgrade
"""""""

The following gif demonstrates the upgrade of a HMC from V8 R870 to V9 R1 M910 
through NFS server.

.. figure:: ../images/demo_hmc_upgrade.gif
   :alt: 

hmc_pwdpolicy
-------------

Create and Activate
"""""""""""""""""""

The following gif demonstrates the creating of HMC password policy and
activating it.

.. figure:: ../images/demo_password_policy_create.gif
   :alt: 

Deactivate, Modify and Activate
"""""""""""""""""""""""""""""""

The following gif demonstrates the deactivating the active HMC password
policy then modify and activate it.

.. figure:: ../images/demo_password_policy_modify.gif
   :alt: 


powervm_inventory
-----------------

Deletion of multiple inactive partitions using dynamic inventory plugin
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

The following demo illustrates the usage of dynamic inventory plugin for the deletion of multiple partitions.
It uses dynamic inventory plugin to collect the inventory and use it as input to delete multiple partition in iteration. Here each delete task will take care of removing the VIOS disk mapping and vdisk associated with the partition as well.

.. figure:: ../images/demo_powervm_inventory.gif
   :alt:


powervm_lpar_instance
---------------------

Create and Activate lpar instance
"""""""""""""""""""""""""""""""""

The following demo illustrate the use case of creating a partition with memory and shared processor settings along with storage and network configurations. Once created, it activates the partition with default profile.

.. figure:: ../images/demo_create_and_activate_partition.gif
   :alt:

