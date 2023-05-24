.. ...........................................................................
.. © Copyright IBM Corporation 2020                                          .
.. ...........................................................................

Releases
========

Version 1.0.0
-------------
Notes
  * HMC patch management module for update and upgrade of HMC recovery images, SPs and PTFs
  * Password policy module

Availability
  * `Galaxy v1.0.0`_
  * `GitHub v1.0.0`_

.. _Galaxy v1.0.0:
   https://galaxy.ansible.com/download/ibm-power_hmc-1.0.0.tar.gz

.. _GitHub v1.0.0:
   https://github.com/IBM/ansible-power-hmc/releases/download/v1.0.0/ibm-power_hmc-1.0.0.tar.gz


Version 1.1.0
-------------
Notes
  * Module to create AIX/Linux or IBMi partition with dedicated processor and memory settings
  * Plugin for dynamic inventory of partitions based on HMC

Availability
  * `Galaxy v1.1.0`_
  * `GitHub v1.1.0`_

.. _Galaxy v1.1.0:
   https://galaxy.ansible.com/download/ibm-power_hmc-1.1.0.tar.gz

.. _GitHub v1.1.0:
   https://github.com/IBM/ansible-power-hmc/releases/download/v1.1.0/ibm-power_hmc-1.1.0.tar.gz


Version 1.2.0
-------------
Notes
  * powervm_lpar_instance: Added support for storage configuration during partition create
  * powervm_lpar_instance: Added support for network configuration during partition create
  * powervm_lpar_instance: Added support to configure shared processor units during partition create
  * powervm_lpar_instance: Added support to shutdown and activate the partition
  * powervm_lpar_instance: Added support to delete partition with vconfig and vdisks
  * Fix for incorrectly assigns I/O slots during partition create
  * Enhanced dynamic inventory plugin to accept jinja template for hmc_hosts param

Availability
  * `Galaxy v1.2.0`_
  * `GitHub v1.2.0`_

.. _Galaxy v1.2.0:
   https://galaxy.ansible.com/download/ibm-power_hmc-1.2.0.tar.gz

.. _GitHub v1.2.0:
   https://github.com/IBM/ansible-power-hmc/releases/download/v1.2.0/ibm-power_hmc-1.2.0.tar.gz


Version 1.3.0
-------------
Notes
  * powervm_lpar_instance: Support for storage configuration with NPIV (Virtual Fibre)
  * powervm_lpar_instance: Support for physical IO adapter configuration
  * powervm_lpar_instance: All(full) resource partition create support
  * powervm_lpar_instance: Reboot of partition
  * powervm_lpar_instance: Fetch partition info using 'fact' state
  * powervm_lpar_instance: Added virtual slot param option during network configuration
  * power_system: Power cycle of power servers
  * power_system: System level config support for power servers
  * hmc_update_upgrade: disk option to support update/upgrade from hmc local disk
  * Enhanced dynamic inventory plugin to collect IBMi partition details

Availability
  * `Galaxy v1.3.0`_
  * `GitHub v1.3.0`_

.. _Galaxy v1.3.0:
   https://galaxy.ansible.com/download/ibm-power_hmc-1.3.0.tar.gz

.. _GitHub v1.3.0:
   https://github.com/IBM/ansible-power-hmc/releases/download/v1.3.0/ibm-power_hmc-1.3.0.tar.gz


Version 1.4.0
-------------
Notes
  * powervm_lpar_migration: Live Partition Mobility (partition migration) support
  * vios: Creation and Installation of VIOS partition
  * hmc_command: HMC CLI Generic command module
  * powervm_lpar_instance: Multiple volume and network support during partition create
  * powervm_lpar_instance: NPIV WWPN info on facts state
  * Fixes for #46 and #47

Availability
  * `Galaxy v1.4.0`_
  * `GitHub v1.4.0`_

.. _Galaxy v1.4.0:
   https://galaxy.ansible.com/download/ibm-power_hmc-1.4.0.tar.gz

.. _GitHub v1.4.0:
   https://github.com/IBM/ansible-power-hmc/releases/download/v1.4.0/ibm-power_hmc-1.4.0.tar.gz


Version 1.5.0
-------------
Notes
  * powervm_lpar_migration: Cross HMC (partition migration) support
  * powervm_lpar_instance: Virtual Slot settings support for NPIV config
  * powervm_lpar_instance: Storage details on facts state
  * powervm_lpar_instance: Support for more proc and mem settings including shared processor pool
  * Support to ignore SSH host key using env

Availability
  * `Galaxy v1.5.0`_
  * `GitHub v1.5.0`_

.. _Galaxy v1.5.0:
   https://galaxy.ansible.com/download/ibm-power_hmc-1.5.0.tar.gz

.. _GitHub v1.5.0:
   https://github.com/IBM/ansible-power-hmc/releases/download/v1.5.0/ibm-power_hmc-1.5.0.tar.gz
   
   
Version 1.6.0
-------------
Notes
  * powervm_lpar_instance: VNIC configuration support
  * powervm_lpar_instance: Add VNIC info into facts
  * powervm_lpar_instance: Supports install of AIX and Linux partition using netboot
  * powervm_lpar_instance: Partition ID configuration support
  * hmc_user: User management of HMC
  
  Availability
    * `Galaxy v1.6.0`_
    * `GitHub v1.6.0`_

.. _Galaxy v1.6.0:
   https://galaxy.ansible.com/download/ibm-power_hmc-1.6.0.tar.gz

.. _GitHub v1.6.0:
   https://github.com/IBM/ansible-power-hmc/releases/download/v1.6.0/ibm-power_hmc-1.6.0.tar.gz
   
Version 1.7.0
-------------
Notes
  * firmware_update: Update/Upgrade firmware level on Managed System
  * powervm_dlpar: Dynamically managing proc/mem resources of partition
  * hmc_user: LDAP configuration support
  * powervm_lpar_instance: Managed Sytem made optional for removal of partition
  * powervm_inventory: Support for managed system group
  * powervm_inventory: Introduced new properties like `AssociatedGroups` (Tagged group name), `AssociatedHMC` (HMC IP/Hostname), `AssociatedHMCUserName` (HMC username), `SystemName`
  * powervm_inventory: Renamed parameter value from lpar_name to name for paramters like ansible_host_type and ansible_display_name
  * powervm_inventory: Added more flexible yaml friendly format for configuration input (hmc_hosts as list)
  
  Availability
    * `Galaxy v1.7.0`_
    * `GitHub v1.7.0`_

.. _Galaxy v1.7.0:
   https://galaxy.ansible.com/download/ibm-power_hmc-1.7.0.tar.gz

.. _GitHub v1.7.0:
   https://github.com/IBM/ansible-power-hmc/releases/download/v1.7.0/ibm-power_hmc-1.7.0.tar.gz

Version 1.8.0
-------------
Notes
  * powervm_dlpar: Dlpar support for VSCSI based physical volume
  * powervm_dlpar: Dlpar support for NPIV based physical volume
  * powervm_dlpar: Dlpar support for virtual optical drive
  * powervm_lpar_instance: Fix for issue #91
  * powervm_lpar_instance: Enhanced with system_name made optional for states like facts, absentand actions like shutdown, poweron and restart 
  * vios: Enhancement associated with issue #93
  * vios: Enhanced vios module with facts of free physical volumes and virtual media details 

  Availability
    * `Galaxy v1.8.0`_
    * `GitHub v1.8.0`_

.. _Galaxy v1.8.0:
   https://galaxy.ansible.com/download/ibm-power_hmc-1.8.0.tar.gz

.. _GitHub v1.8.0:
   https://github.com/IBM/ansible-power-hmc/releases/download/v1.8.0/ibm-power_hmc-1.8.0.tar.gz
