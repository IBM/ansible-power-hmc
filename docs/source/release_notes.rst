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
