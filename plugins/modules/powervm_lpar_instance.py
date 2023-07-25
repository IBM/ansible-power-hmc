#!/usr/bin/python

# Copyright: (c) 2018- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: powervm_lpar_instance
author:
    - Anil Vijayan (@AnilVijayan)
    - Navinakumar Kandakur (@nkandak1)
short_description: Create, Delete, Shutdown, Activate, Restart, Facts and Install of PowerVM Partitions
notes:
    - The network configuration currently will not support SRIOV configurations.
    - I(retain_vios_cfg) and I(delete_vdisks) options will only be supported from HMC release level on or above V9 R1 M930.
    - Partition creation is not supported for resource role-based user in HMC Version prior to 951.
    - C(install_os) action doesn't support installation of IBMi OS.
    - Only state=absent and action=install_os operations support passwordless authentication.
description:
    - "Creates AIX/Linux or IBMi partition with specified configuration details on mentioned system"
    - "Or Deletes specified AIX/Linux or IBMi partition on specified system"
    - "Or Shutdown specified AIX/Linux or IBMi partition on specified system"
    - "Or Poweron/Activate specified AIX/Linux or IBMi partition, with provided configuration details on the mentioned system"
    - "Or Restart specified AIX/Linux or IBMi partition on specified system"
    - "Or Facts of the specified AIX/Linux or IBMi partition of specified system"
    - "Or Install of PowerVM Partition"

version_added: "1.2.0"
requirements:
- Python >= 3
- lxml
options:
    hmc_host:
        description:
            - IPaddress or hostname of the HMC.
        required: true
        type: str
    hmc_auth:
        description:
            - Username and Password credential of the HMC.
        required: true
        type: dict
        suboptions:
            username:
                description:
                    - HMC username.
                required: true
                type: str
            password:
                description:
                    - HMC password.
                type: str
    system_name:
        description:
            - The name of the managed system.
            - Optional for I(state=absent), I(state=facts), I(action=poweron), I(action=shutdown) and I(action=restart).
        type: str
    vm_name:
        description:
            - The name of the powervm partition.
        required: true
        type: str
    vm_id:
        description:
            - The partition ID to be set while creating a Logical Partition.
            - Optional, if not provided, next available value will be assigned.
        type: int
    proc:
        description:
            - The number of dedicated processors to create a partition.
            - If C(proc_unit) parameter is set, then this value will work as virtual processors for
              shared processor setting.
            - Default value is '2'. This will not work during shared processor setting.
        type: int
    max_proc:
        description:
            - The maximum number of dedicated processors to create a partition.
            - If C(proc_unit) parameter is set, then this value will work as max virtual processors for
              shared processor setting.
            - Default value is C(proc).
            - This value should be always equal or greater than C(proc).
        type: int
    min_proc:
        description:
            - The minimum number of dedicated processors to create a partition.
            - If C(proc_unit) parameter is set, then this value will work as min virtual processors for
              shared processor setting.
            - Default value is '1'.
            - This value should be always equal or less than C(proc).
        type: int
    proc_unit:
        description:
            - The number of shared processing units to create a partition.
        type: float
    shared_proc_pool:
        description:
            - Shared Processor Pool ID or Name.
            - If numeric value provided to this parameter, it will be considered as Shared Processor Pool ID.
            - This parameter can be used only with C(proc_unit).
            - Default value is 'DefaultPool'.
        type: str
    max_proc_unit:
        description:
            - The maximum number of shared processing units to create a partition.
            - This value should be equal or greater than C(proc_unit).
            - This parameter can be used only with C(proc_unit).
            - Default value is C(proc_unit).
        type: float
    min_proc_unit:
        description:
            - The minimum number of shared processing units to create a partition.
            - This value should be equal or less than C(proc_unit).
            - This parameter can be used only with C(proc_unit).
            - Default value is '0.1'.
        type: float
    proc_mode:
        description:
            - The processor mode to be used to create a partition with shared processor settings.
            - Default value is 'uncapped'.
            - This parameter can be used only with C(proc_unit).
        type: str
        choices: ['capped', 'uncapped']
    weight:
        description:
            - The weight to be used for uncapped proc mode while create a partition with shared processor settings.
            - Default value is '128'.
            - This value will be ignored if the C(proc_mode) is set to I(capped).
            - This parameter can be used only with C(proc_mode).
        type: int
    proc_compatibility_mode:
        description:
            - The processor compatibility mode to be configured while creating a partition.
        type: str
    mem:
        description:
            - The value of dedicated memory value in megabytes to create a partition.
            - Default value is '2048 MB'.
        type: int
    max_mem:
        description:
            - The maximum value of dedicated memory value in megabytes to create a partition.
            - Default value is '2048 MB'.
            - This parameter can only be used with C(mem).
        type: int
    min_mem:
        description:
            - The maximum value of dedicated memory value in megabytes to create a partition.
            - Default value is '1024 MB'.
            - This parameter can only be used with C(mem).
        type: int
    os_type:
        description:
            - Type of logical partition to be created.
            - C(aix_linux) or C(linux) or C(aix) for AIX or Linux operating system.
            - C(ibmi) for IBMi operating system.
        type: str
        choices: ['aix','linux','aix_linux','ibmi']
    prof_name:
        description:
            - Partition profile to be used to activate a partition.
            - If the user doesn't provide this option, the current configuration of partition will be used for activation.
            - This option is valid only for C(poweron) I(action).
        type: str
    keylock:
        description:
            - The keylock position to be set while activating a partition.
            - If the user doesn't provide this option, the current setting of this option in partition will be considered.
            - This option is valid only for C(poweron) I(action).
        type: str
        choices: ['manual', 'normal']
    iIPLsource:
        description:
            - The initial program load (IPL) source to be used while activating an IBMi partition.
            - If the user doesn't provide this option, current setting of this option in the partition will be considered.
            - If this option provided for AIX/Linux type partition, operation gives a warning and then ignores this option and proceed with the operation.
            - This option is valid only for C(poweron) I(action).
        type: str
        choices: ['a','b','c','d']
    volume_config:
        description:
            - Storage volume configurations of a partition.
            - Attach Physical Volumes via Virtual SCSI.
            - Redundant paths created by default, if the specified/identified physical volume is visible in more than one VIOS.
            - User needs to provide either I(volume_size) or both I(volume_name) and I(vios_name). If I(volume_size) is provided,
              available physical volume matching or greater than specified size would be attached.
        type: list
        elements: dict
        suboptions:
            volume_name:
                description:
                    - Physical volume name visible through VIOS.
                    - This option is mutually exclusive with I(volume_size).
                type: str
            vios_name:
                description:
                    - VIOS name to which mentioned I(volume_name) is present.
                    - This option is mutually exclusive with I(volume_size).
                type: str
            volume_size:
                description:
                    - Physical volume size in MB.
                type: int
    virt_network_config:
        description:
            - Virtual Network configuration of the partition.
            - This implicitly adds a Virtual Ethernet Adapter with given virtual network to the partition.
            - Make sure provided Virtual Network has been attached to an active Network Bridge for external network communication.
        type: list
        elements: dict
        suboptions:
            network_name:
                description:
                    - Name of the Virtual Network to be attached to the partition.
                    - This option is mandatory.
                required: true
                type: str
            slot_number:
                description:
                    - Virtual slot number of a partition on which virtual network to be attached.
                    - Optional, if not provided, next available value will be assigned.
                type: int
    npiv_config:
        description:
            - To configure N-Port ID Virtualization is also known as Virtual Fibre of the partition.
            - User can provide two fc port configurations and mappings will be created with VIOS implicitly.
        type: list
        elements: dict
        suboptions:
            vios_name:
                description:
                    - The name of the vios in which fc port available.
                    - This option is mandatory.
                required: true
                type: str
            fc_port:
                description:
                    - The port to be used for npiv. User can specify either port name or fully qualified location code.
                    - This option is mandatory.
                required: true
                type: str
            wwpn_pair:
                description:
                    - The WWPN pair value to be configured with client FC adapter.
                    - Both the WWPN value should be separated by semicolon delimiter.
                    - Optional, if not provided the value will be auto assigned.
                type: str
            client_adapter_id:
                description:
                    - The client adapter slot number to be configured with FC adapter.
                    - Optional, if not provided next available value will be assigned.
                type: int
            server_adapter_id:
                description:
                    - The Server adapter slot number to be configured with FC adapter.
                    - Optional, if not provided next available value will be assigned.
                type: int
    all_resources:
        description:
            - Creates a partition with all the resources available in the managed system.
            - When we choose this as true, make sure that all partitions are in a shutdown state, if any exist in the managed system.
            - Default is false
        type: bool
    max_virtual_slots:
        description:
            - Maximum virtual slot configuration of the partition.
            - If the user doesn't provide, it creates partition with I(max_virtual_slots) 20 as default.
        type: int
    physical_io:
        description:
            - Physical IO adapter to be added to the partition.
            - An illustrative pattern for IO location code is XXXXX.XXX.XXXXXXX-P1-T1 or P1-T1.
        type: list
        elements: str
    retain_vios_cfg:
        description:
            - Do not remove the VIOS configuration like server adapters, storage mappings associated with the partition when deleting the partition.
            - Applicable only for C(absent) state.
            - Default is to remove the associated VIOS configuration when deleting the partition.
        type: bool
    delete_vdisks:
        description:
            - Option to delete the Virtual Disks associated with the partition when deleting the partition.
            - Default is to not delete the virtual disks.
        type: bool
    advanced_info:
        description:
            - Option to display advanced information of the logical partition.
            - Applicable only for C(facts) state.
            - Default is false.
            - Currently we are showing only NPIV storage details.
        type: bool
    install_settings:
        description:
            - Settings for installing Operating System on logical partition.
            - User expected to have NIM Server with pull install configuration.
        type: dict
        suboptions:
            vm_ip:
                description:
                    - IP Address to be configured to Logical Partition.
                required: True
                type: str
            nim_ip:
                description:
                    - IP Address of the NIM Server.
                required: True
                type: str
            nim_gateway:
                description:
                    - Logical Partition gateway IP Address.
                required: True
                type: str
            nim_subnetmask:
                description:
                    - Subnetmask IP Address to be configured to Logical Partition.
                required: True
                type: str
            location_code:
                description:
                    - Network adapter location code to be used while installing OS.
                    - If user doesn't provide, it automatically picks the first pingable adapter attached to the partition.
                type: str
            nim_vlan_id:
                description:
                    - Specifies the VLANID(0 to 4094) to use for tagging Ethernet frames during network install for virtual network communication.
                    - Default value is 0.
                type: str
            nim_vlan_priority:
                description:
                    - Specifies the VLAN priority (0 to 7) to use for tagging Ethernet frames during network install for virtual network communication.
                    - Default value is 0.
                type: str
            timeout:
                description:
                    - Max waiting time in mins for OS to bootup fully.
                    - Min timeout should be more than 10 mins.
                    - Default value is 60 min.
                type: int
    vnic_config:
        description:
            - Virtual NIC configuration of the partition.
        type: list
        elements: dict
        suboptions:
            vnic_adapter_id:
                description:
                    - VNIC Adapter ID to be configured while creating a partition.
                    - Optional, if not provided, next available value will be assigned.
                type: int
            backing_devices:
                description:
                    - SRIOV physical ports to be used as a backing device of VNIC.
                    - If user doesn't provide this option, by default it picks the SRIOV Physical port with link status up as backing device.
                    - If there are no SRIOV Physical port with link status as up then it randomly picks physical port which has capacity more than 2.0%.
                type: list
                elements: dict
                suboptions:
                    location_code:
                        description:
                            - SRIOV Physical port location code to be used as backing device.
                            - An illustrative pattern for SRIOV physical port location code is XXXXX.XXX.XXXXXXX-P1-T1 or P1-T1.
                        required: True
                        type: str
                    capacity:
                        description:
                            - Capacity value to be configured for vnic backing device. Default value is 2.0%.
                        type: float
                    hosting_partition:
                        description:
                            - The VIOS name on which SRIOV physical port location code to be configured.
                            - By default picks a random VIOS name with RMC state as active.
                        type: str
    shutdown_option:
        description:
            - Option to shutdown Logical Partition
            - This option is valid only for C(shutdown) I(action).
            - Default value is C(Delayed).
        type: str
        choices: ['Delayed', 'Immediate', 'OperatingSystem', 'OSImmediate']
    restart_option:
        description:
            - Option to reboot Logical Partition
            - This option is valid only for C(restart) I(action).
            - Default value is C(Immediate).
        type: str
        choices: ['Immediate', 'OperatingSystem', 'OSImmediate', 'Dump', 'DumpRetry']
    state:
        description:
            - C(present) creates a partition of the specified I(os_type), I(vm_name), I(proc) and I(memory) on specified I(system_name).
            - C(absent) deletes a partition of the specified I(vm_name).
            - C(facts) fetch the details of the specified I(vm_name) on specified I(system_name).
        type: str
        choices: ['present', 'absent', 'facts']
    action:
        description:
            - C(shutdown) shutdown a partition of the specified I(vm_name) on specified I(system_name).
            - C(poweron) poweron a partition of the specified I(vm_name) with specified I(prof_name), I(keylock), I(iIPLsource) on specified I(system_name).
            - C(restart) restart a partition of the specified I(vm_name) on specified I(system_name).
            - C(install_os) install Aix/Linux OS through NIM Server on specified I(vm_name).
        type: str
        choices: ['poweron', 'shutdown', 'restart', 'install_os']
'''

EXAMPLES = '''
- name: Create an IBMi logical partition instance with shared proc, volume_config's vios_name and volume_name values, PhysicaIO and
        max_virtual_slots.
  powervm_lpar_instance:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
      system_name: <system_name>
      vm_name: <vm_name>
      vm_id: <lpar_id>
      proc: 4
      proc_unit: 4
      mem: 20480
      volume_config:
         - vios_name: <viosname1>
           volume_name: <volumename1>
         - vios_name: <viosname2>
           volume_name: <volumename2>
      physical_io:
         - <physicalIO location code>
         - <physicalio location code>
      max_virtual_slots: 50
      os_type: ibmi
      state: present

- name: Create an AIX/Linux logical partition instance with default proc, mem, virt_network_config, volume_config's volumes_size and
        npiv_config, vnic_config.
  powervm_lpar_instance:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
      system_name: <system_name>
      vm_name: <vm_name>
      volume_config:
         - volume_size: <disk_size>
         - volume_size: <disk_size>
      virt_network_config:
         - network_name: <virtual_nw_name>
           slot_number: <client_slot_no>
      npiv_config:
         - vios_name: <viosname>
           fc_port: <fc_port_name/loc_code>
           wwpn_pair: <wwpn1;wwpn2>
      vnic_config:
         - vnic_adapter_id: <vnic_adapter_id>
           backing_devices:
              - location_code: XXXXX.XXX.XXXXXXX-P1-T1
                capacity: <capacity>
                hosting_partition: <vios_name>
              - location_code: P1-T2
         - backing_devices:
              - location_code: P1-T3
                hosting_partition: <vios_name>
              - location_code: P1-T4
                capacity: <capacity>
         - vnic_adapter_id: <vnic_adapter_id>
      os_type: aix_linux
      state: present

- name: Delete a logical partition instance with retain_vios_cfg and delete_vdisk options.
  powervm_lpar_instance:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
      system_name: <system_name>
      vm_name: <vm_name>
      retain_vios_cfg: True
      delete_vdisks: True
      state: absent

- name: Shutdown a logical partition.
  powervm_lpar_instance:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
      system_name: <system_name>
      vm_name: <vm_name>
      action: shutdown

- name: Activate an AIX/Linux logical partition with user defined profile_name.
  powervm_lpar_instance:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
      system_name: <system_name>
      vm_name: <vm_name>
      prof_name: <profile_name>
      action: poweron

- name: Activate IBMi based on its current configuration with keylock and iIPLsource options.
  powervm_lpar_instance:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
      system_name: <system_name>
      vm_name: <vm_name>
      keylock: 'normal'
      iIPLsource: 'd'
      action: poweron

- name: Create a partition with all resources.
  powervm_lpar_instance:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
      system_name: <system_name>
      vm_name: <vm_name>
      all_resources: True
      os_type: aix_linux
      state: present

- name: Install Aix/Linux OS on LPAR from NIM Server.
  powervm_lpar_instance:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth: "{{ curr_hmc_auth }}"
      system_name: <system_name>
      vm_name: <vm_name>
      install_settings:
         vm_ip: <IP_address of the lpar>
         nim_ip: <IP_address of the NIM Server>
         nim_gateway: <Gateway IP_Addres>
         nim_subnetmask: <Subnetmask IP_Address>
      action: install_os

'''

RETURN = '''
partition_info:
    description: The configuration of the partition after creation
    type: dict
    sample: {"AllocatedVirtualProcessors": null, "AssociatedManagedSystem": "<system-name>", "CurrentMemory": 1024, \
            "CurrentProcessingUnits": null, "CurrentProcessors": 1, "Description": null, "HasDedicatedProcessors": "true", \
            "HasPhysicalIO": "true", "IsVirtualServiceAttentionLEDOn": "false", "LastActivatedProfile": "default_profile", \
            "MemoryMode": "Dedicated", "MigrationState": "Not_Migrating", "OperatingSystemVersion": "Unknown", \
            "PartitionID": 11, "PartitionName": "<partition-name>", "PartitionState": "not activated", \
            "PartitionType": "AIX/Linux", "PowerManagementMode": null, "ProgressState": null, "RMCState": "inactive", \
            "ReferenceCode": "", "RemoteRestartState": "Invalid", "ResourceMonitoringIPAddress": null, "SharingMode": "sre idle proces"}
    returned: on success for state C(present)
'''

import sys
import json
import re
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_resource import Hmc
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import Error
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ProcMemValidationError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import parse_error_response
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import HmcRestClient
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import add_taggedIO_details
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import add_physical_io
from random import randint
from collections import OrderedDict
from decimal import Decimal
try:
    from lxml import etree
except ImportError:
    pass  # Handled by hmc rest client module

# Generic setting for log initializing and log rotation
import logging
LOG_FILENAME = "/tmp/ansible_power_hmc.log"
logger = logging.getLogger(__name__)


def init_logger():
    logging.basicConfig(
        filename=LOG_FILENAME,
        format='[%(asctime)s] %(levelname)s: [%(funcName)s] %(message)s',
        level=logging.DEBUG)


def validate_proc_mem(system_dom, proc, mem, max_proc, min_proc, max_mem, min_mem, weight, min_proc_unit, max_proc_unit, proc_unit=None):
    if not (min_proc <= proc <= max_proc):
        raise ProcMemValidationError("Allocated processor:{0} value should be in-between minimum_processor:{1} and maximum_processor:{2}"
                                     .format(str(proc), str(min_proc), str(max_proc)))
    if not (min_mem <= mem <= max_mem):
        raise ProcMemValidationError("Allocated memory:{0} value should be in-between minimum memory:{1} and  maximum memory:{2}"
                                     .format(str(mem), str(min_mem), str(max_mem)))
    curr_avail_proc_units = system_dom.xpath(
        '//CurrentAvailableSystemProcessorUnits')[0].text
    curr_avail_procs = float(curr_avail_proc_units)

    if proc_unit:
        if weight not in range(256):
            raise ProcMemValidationError(
                "weight value should be in between 0 to 255")
        if not (min_proc_unit <= proc_unit <= max_proc_unit):
            raise ProcMemValidationError("Allocated processor units:{0} value should be in-between minimum processor units:{1} and maximum processor units:{2}"
                                         .format(str(proc_unit), str(min_proc_unit), str(max_proc_unit)))
        min_proc_unit_per_virtproc = system_dom.xpath(
            '//MinimumProcessorUnitsPerVirtualProcessor')[0].text
        if Decimal(str(proc_unit)) % Decimal(min_proc_unit_per_virtproc) != Decimal('0.0'):
            raise ProcMemValidationError("Input processor units: {0} must be a multiple of {1}".format(
                proc_unit, min_proc_unit_per_virtproc))
        if proc_unit > curr_avail_procs:
            raise ProcMemValidationError("{0} Available system proc units is not enough for {1} shared CPUs. Provide value on or below {0}"
                                         .format(str(curr_avail_procs), str(proc_unit)))
    else:
        if proc > curr_avail_procs:
            raise ProcMemValidationError("{2} Available system proc units is not enough for {1} dedicated CPUs. Provide value on or below {0} CPUs"
                                         .format(str(max_proc), str(proc), str(curr_avail_procs)))

    curr_avail_mem = system_dom.xpath('//CurrentAvailableSystemMemory')[0].text
    int_avail_mem = int(curr_avail_mem)
    curr_avail_lmb = system_dom.xpath(
        '//CurrentLogicalMemoryBlockSize')[0].text
    lmb = int(curr_avail_lmb)

    if max_mem < min_mem or mem < min_mem or mem > max_mem:
        raise ProcMemValidationError("Allocated Memory:{0} value should be in-between minimum_memory:{1} and maximum_memory:{2}"
                                     .format(str(mem), str(min_mem), str(max_mem)))

    if mem % lmb > 0:
        raise ProcMemValidationError(
            "Requested mem value not in mutiple of block size:{0}".format(curr_avail_lmb))

    if mem > int_avail_mem:
        raise ProcMemValidationError(
            "Available system memory is not enough. Provide value on or below {0}".format(curr_avail_mem))


def validate_sub_dict(sub_key, params):
    mutually_exclusive_list = []
    together = []

    for each in params.copy():
        if not params[each] or params[each] == '':
            params.pop(each)

    if not params:
        raise ParameterError("Key values of '%s' are invalid" % sub_key)

    if 'volume_config' == sub_key:
        options = params.keys()
        together = ['volume_name', 'vios_name']
        mutually_exclusive_list = [('volume_name', 'vios_name'), ('volume_size',)]

    if mutually_exclusive_list:
        list1 = [each for each in options if each in mutually_exclusive_list[0]]
        list2 = [each for each in options if each in mutually_exclusive_list[1]]
        if list1 and list2:
            raise ParameterError("Parameters: '%s' and '%s' are  mutually exclusive" %
                                 (', '.join(mutually_exclusive_list[0]), ', '.join(mutually_exclusive_list[1])))

    if together:
        list3 = [each for each in options if each in together]
        if len(list3) >= 1 and set(list3) != set(together):
            raise ParameterError("Missing parameters %s" % (', '.join(set(together) - set(list3))))


def validate_parameters(params):
    '''Check that the input parameters satisfy the mutual exclusiveness of HMC'''
    opr = None
    if params['state'] is not None:
        opr = params['state']
    else:
        opr = params['action']

    if opr == 'present':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'vm_name', 'os_type']
        unsupportedList = ['prof_name', 'keylock', 'iIPLsource', 'retain_vios_cfg', 'delete_vdisks', 'advanced_info', 'install_settings',
                           'shutdown_option', 'restart_option']
    elif opr == 'poweron':
        mandatoryList = ['hmc_host', 'hmc_auth', 'vm_name']
        unsupportedList = ['proc', 'mem', 'os_type', 'proc_unit', 'volume_config', 'virt_network_config', 'retain_vios_cfg', 'delete_vdisks',
                           'all_resources', 'max_virtual_slots', 'advanced_info', 'min_proc', 'max_proc', 'min_proc_unit', 'max_proc_unit',
                           'proc_mode', 'weight', 'proc_compatibility_mode', 'shared_proc_pool', 'min_mem', 'max_mem', 'vm_id', 'install_settings',
                           'vnic_config', 'shutdown_option', 'restart_option']
    elif opr == 'absent':
        mandatoryList = ['hmc_host', 'hmc_auth', 'vm_name']
        unsupportedList = ['proc', 'mem', 'os_type', 'proc_unit', 'prof_name', 'keylock', 'iIPLsource', 'volume_config', 'virt_network_config',
                           'all_resources', 'max_virtual_slots', 'advanced_info', 'min_proc', 'max_proc', 'min_proc_unit', 'max_proc_unit',
                           'proc_mode', 'weight', 'proc_compatibility_mode', 'shared_proc_pool', 'min_mem', 'max_mem', 'vm_id', 'install_settings',
                           'vnic_config', 'shutdown_option', 'restart_option']
    elif opr == 'facts':
        mandatoryList = ['hmc_host', 'hmc_auth', 'vm_name']
        unsupportedList = ['proc', 'mem', 'os_type', 'proc_unit', 'prof_name', 'keylock', 'iIPLsource', 'volume_config', 'virt_network_config',
                           'retain_vios_cfg', 'delete_vdisks', 'all_resources', 'max_virtual_slots', 'min_proc', 'max_proc', 'min_proc_unit', 'max_proc_unit',
                           'proc_mode', 'weight', 'proc_compatibility_mode', 'shared_proc_pool', 'min_mem', 'max_mem', 'vm_id', 'install_settings',
                           'vnic_config', 'shutdown_option', 'restart_option']
    elif opr == 'install_os':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'vm_name', 'install_settings']
        unsupportedList = ['proc', 'mem', 'os_type', 'proc_unit', 'keylock', 'iIPLsource', 'volume_config', 'virt_network_config', 'retain_vios_cfg',
                           'delete_vdisks', 'all_resources', 'max_virtual_slots', 'advanced_info', 'min_proc', 'max_proc', 'min_proc_unit', 'max_proc_unit',
                           'proc_mode', 'weight', 'proc_compatibility_mode', 'shared_proc_pool', 'min_mem', 'max_mem', 'vm_id', 'vnic_config',
                           'shutdown_option', 'restart_option']
    elif opr == 'shutdown':
        mandatoryList = ['hmc_host', 'hmc_auth', 'vm_name']
        unsupportedList = ['proc', 'mem', 'os_type', 'proc_unit', 'prof_name', 'keylock', 'iIPLsource', 'volume_config', 'virt_network_config',
                           'retain_vios_cfg', 'delete_vdisks', 'all_resources', 'max_virtual_slots', 'advanced_info', 'min_proc', 'max_proc',
                           'min_proc_unit', 'max_proc_unit', 'proc_mode', 'weight', 'proc_compatibility_mode', 'shared_proc_pool', 'min_mem', 'max_mem',
                           'vm_id', 'install_settings', 'vnic_config', 'restart_option']
    else:
        mandatoryList = ['hmc_host', 'hmc_auth', 'vm_name']
        unsupportedList = ['proc', 'mem', 'os_type', 'proc_unit', 'prof_name', 'keylock', 'iIPLsource', 'volume_config', 'virt_network_config',
                           'retain_vios_cfg', 'delete_vdisks', 'all_resources', 'max_virtual_slots', 'advanced_info', 'min_proc', 'max_proc',
                           'min_proc_unit', 'max_proc_unit', 'proc_mode', 'weight', 'proc_compatibility_mode', 'shared_proc_pool', 'min_mem', 'max_mem',
                           'vm_id', 'install_settings', 'vnic_config', 'shutdown_option']

    collate = []
    for eachMandatory in mandatoryList:
        if not params[eachMandatory]:
            collate.append(eachMandatory)
    if collate:
        if len(collate) == 1:
            raise ParameterError("mandatory parameter '%s' is missing" % (collate[0]))
        else:
            raise ParameterError("mandatory parameters '%s' are missing" % (','.join(collate)))

    collate = []
    for eachUnsupported in unsupportedList:
        if params[eachUnsupported]:
            collate.append(eachUnsupported)

    if collate:
        if len(collate) == 1:
            raise ParameterError("unsupported parameter: %s" % (collate[0]))
        else:
            raise ParameterError("unsupported parameters: %s" % (', '.join(collate)))

    if params['volume_config']:
        for each_volume_config in params['volume_config']:
            validate_sub_dict('volume_config', each_volume_config)


def fetchAllInUsePhyVolumes(rest_conn, vios_uuid):
    pvid_in_use = []
    vios_response = rest_conn.getVirtualIOServer(vios_uuid, group="ViosStorage")
    phy_vol_list = vios_response.xpath("//MoverServicePartition/following-sibling::PhysicalVolumes/PhysicalVolume")
    for each_phy_vol in phy_vol_list:
        if each_phy_vol.xpath("AvailableForUsage")[0].text == "false":
            pvid_in_use.append(each_phy_vol.xpath("UniqueDeviceID")[0].text)

    logger.debug("Disks in use for vios: %s are %s", vios_uuid, pvid_in_use)
    return pvid_in_use


def identifyFreeVolume(rest_conn, system_uuid, volume_name=None, volume_size=0, vios_name=None, pvid_list=None):
    user_choice_vios = None
    user_choice_pvid = None
    vios_response = rest_conn.getVirtualIOServersQuick(system_uuid)
    vios_uuid_list = []
    if vios_response:
        vios_list = json.loads(vios_response)

        vios_uuid_list = [(vios['UUID'], vios['PartitionName']) for vios in vios_list if vios['RMCState'] == 'active']

        if not vios_uuid_list:
            raise Error("VIOSes are not available or RMC down")
    else:
        raise Error("VIOSes are not available")

    if vios_name and volume_name:
        for uuid, name in vios_uuid_list:
            if vios_name == name:
                user_choice_vios = vios_name
                break
        if not user_choice_vios:
            raise Error("Mentioned vios may not have active RMC state")

    pv_complex = []
    keys_list = []
    unique_keys = []
    pvs_in_use = []
    for vios_uuid, viosname in vios_uuid_list:
        logger.debug(vios_uuid)
        each_vios_pv_complex = {}
        pv_xml_list = rest_conn.getFreePhyVolume(vios_uuid)
        pvs_in_use += fetchAllInUsePhyVolumes(rest_conn, vios_uuid)
        logger.debug(len(pv_xml_list))
        for each in pv_xml_list:

            # This condition is to avoid picking already picked UDID in case of mutiple volume config
            if (pvid_list and each.xpath("UniqueDeviceID")[0].text in pvid_list):
                continue

            if volume_size > 0 and int(each.xpath("VolumeCapacity")[0].text) >= volume_size:
                logger.debug("Vios Name: %s", viosname)
                logger.debug("Volume Name: %s", each.xpath("VolumeName")[0].text)
                each_vios_pv_complex.update({each.xpath("UniqueDeviceID")[0].text: each})
            elif user_choice_vios:
                dvid = each.xpath("UniqueDeviceID")[0].text
                each_vios_pv_complex.update({dvid: each})
                if viosname == user_choice_vios and each.xpath("VolumeName")[0].text == volume_name:
                    user_choice_pvid = dvid

        if each_vios_pv_complex:
            sorted_each_vios_pv_complex = dict(sorted(each_vios_pv_complex.items(),
                                               key=lambda x: int(x[1].xpath("VolumeCapacity")[0].text)))
            keys_list += sorted_each_vios_pv_complex.keys()
            pv_complex.append((sorted_each_vios_pv_complex, vios_uuid, viosname))

    # Since the set is not order, using OrderedDict to find unique keys
    ordered_key_d = OrderedDict.fromkeys(keys_list)
    unique_keys = [each[0] for each in ordered_key_d.items()]

    if user_choice_vios:
        if user_choice_pvid:
            unique_keys = [user_choice_pvid]
            logger.debug(unique_keys)
        else:
            unique_keys = []
            raise Error("Not able to identify mentioned volume on free pvs of specified vios")

    found_list = []
    first_singlepath_incidence = []
    in_use_count = 0
    for each_DVID in unique_keys:

        if each_DVID in pvs_in_use:
            logger.debug("Identified pv in use on other vios: %s", each_DVID)
            in_use_count += 1
            continue

        for each_pv_complex in pv_complex:
            if each_DVID in each_pv_complex[0]:
                logger.debug("Adding to found list: %s", each_pv_complex[0][each_DVID].xpath("VolumeName")[0].text)
                found_list += [(each_pv_complex[0][each_DVID].xpath("VolumeName")[0].text,
                                each_pv_complex[2], each_pv_complex[0][each_DVID])]
        if len(found_list) >= 2:
            logger.debug("Identified a volume visible by two vioses")
            singlepath_l = [each for each in found_list if each[2].xpath("ReservePolicy")[0].text == 'SinglePath']

            if user_choice_vios:
                other_pv = []
                match_vios_pv = []
                for each in found_list:
                    if each[1] == user_choice_vios and each in singlepath_l:
                        return [each]
                    elif each[1] == user_choice_vios:
                        match_vios_pv = [each]
                    else:
                        if each not in singlepath_l:
                            other_pv = [each]
                        if match_vios_pv:
                            break
                return match_vios_pv + other_pv

            if singlepath_l and (len(found_list) - len(singlepath_l)) <= 1:
                if not first_singlepath_incidence:
                    first_singlepath_incidence.append(singlepath_l[0])
                logger.debug("Continued...")
                found_list = []
                continue

            return list(set(found_list) - set(singlepath_l))
        elif found_list and user_choice_pvid:
            return found_list
        else:
            found_list = []

    if in_use_count == len(unique_keys):
        logger.debug("All disk reported as free by some vioses is in use on some other vioses")
        return None

    if first_singlepath_incidence:
        logger.debug("Picked the first instance")
        return first_singlepath_incidence

    # if user not specified any vios and could not find volume visible by multiple vioses, then
    # pick a random volume from the vios
    if pv_complex and not found_list and not user_choice_vios:
        logger.debug("Picking a random single disk..")
        first_of_every_vios = []
        for each_pv_complex in pv_complex:
            for eachPVID in each_pv_complex[0].keys():
                if eachPVID in pvs_in_use:
                    continue
                pv_obj = each_pv_complex[0][eachPVID]
                volume_nm = pv_obj.xpath("VolumeName")[0].text
                volume_size = int(pv_obj.xpath("VolumeCapacity")[0].text)
                first_of_every_vios.append(tuple([volume_nm, each_pv_complex[2], pv_obj, volume_size]))
                break

        sort_first_of_every_vios = sorted(first_of_every_vios, key=lambda x: x[3])
        return [sort_first_of_every_vios[0][:-1]]

    return None


def wwpn_pair_is_valid(wwpn):
    # It is expected that wwpn input from the user should have a delimited ':'
    wwpns = wwpn.split(";")
    wwpn_pattern = r"(([0-9a-fA-F]{16})$|((([0-9a-fA-F]{1,2}[:]){7})[0-9a-fA-F]{1,2})$|((([0-9a-fA-F]{1,2}[\-]){7})[0-9a-fA-F]{1,2})$)"
    if len(wwpns) == 2:
        for each in wwpns:
            if not re.match(wwpn_pattern, each):
                raise Error("Given wwpn pair is not valid")
    else:
        raise Error("WWPN pair with semicolon delimiter is expected")

    return True


# Validates and fetch fibre channel port information from VIOS
def fetch_fc_config(rest_conn, system_uuid, fc_config_list):
    vios_response = rest_conn.getVirtualIOServersQuick(system_uuid)
    fcports_identified = []
    for each_fc in fc_config_list:
        vios = None
        if vios_response:
            vios_list = json.loads(vios_response)
            vios = [vios for vios in vios_list if vios['PartitionName'] == each_fc['vios_name']]
        if not vios:
            raise Error("Requested vios: {0} for npiv is not available".format(each_fc['vios_name']))
        elif vios[0]['RMCState'] != 'active':
            raise Error("Requested vios: {0} RMC state is {1} ".format(each_fc['vios_name'], vios[0]['RMCState']))

        if each_fc['fc_port'] is not None:
            vios_fcports = rest_conn.vios_fetch_fcports_info(vios[0]['UUID'])
            port_identified = [v_fcPort for v_fcPort in vios_fcports if v_fcPort['LocationCode'] == each_fc['fc_port']
                               or v_fcPort['PortName'] == each_fc['fc_port']]
            if port_identified:
                port_identified[0].update({'viosname': each_fc['vios_name']})
                if each_fc['wwpn_pair'] is not None and wwpn_pair_is_valid(each_fc['wwpn_pair']):
                    port_identified[0].update({'wwpn_pair': each_fc['wwpn_pair']})
                if each_fc['client_adapter_id'] is not None:
                    port_identified[0].update({'client_adapter_id': str(each_fc['client_adapter_id'])})
                if each_fc['server_adapter_id'] is not None:
                    port_identified[0].update({'server_adapter_id': str(each_fc['server_adapter_id'])})
                fcports_identified.append(port_identified[0])
            else:
                raise Error("Given fc port:{0} is either not NPIV capable or not available".format(each_fc['fc_port']))

    return fcports_identified


# Validates and fetch virtual network information
def fetch_virt_networks(rest_conn, system_uuid, virt_nw_config_list, max_slot_no):
    vnw_response = rest_conn.getVirtualNetworksQuick(system_uuid)
    virt_nws_identified = []
    if vnw_response:
        for ud_nw in virt_nw_config_list:
            nw_uuid = None
            virtual_slot_number = None
            for rr_nw in vnw_response:
                if ud_nw['network_name'] == rr_nw['NetworkName']:
                    if 'slot_number' in ud_nw and ud_nw['slot_number']:
                        virtual_slot_number = int(ud_nw['slot_number'])
                        if int(ud_nw['slot_number']) > int(max_slot_no):
                            raise Error("Virtual slot number: {0} is greater than max virtual slots allowed in a partition".format(ud_nw['slot_number']))
                    nw_uuid = rr_nw['UUID']
                    nw_dict = {'nw_name': rr_nw['NetworkName'], 'nw_uuid': nw_uuid, 'virtual_slot_number': virtual_slot_number}
                    virt_nws_identified.append(nw_dict)
                    break
            if not nw_uuid:
                raise Error("Requested Virtual Network: {0} is not available".format(ud_nw['network_name']))
    else:
        raise Error("There are no Virtual Networks configured on the managed system")
    return virt_nws_identified


def get_MS_names_by_lpar_name(hmc_obj, lpar_name):
    mss = hmc_obj.list_all_managed_system_details("name,state")
    ms_list = []
    for ms in mss:
        ms_name, state = ms.split(',')
        if state == 'Operating':
            lpar_names = hmc_obj.list_all_lpars_details(ms_name, "name")
            if lpar_name in lpar_names:
                ms_list.append(ms_name)
    return ms_list


def identify_ManagedSystem_of_lpar(hmc, vm_name):
    system_name = None
    ms_name = get_MS_names_by_lpar_name(hmc, vm_name)
    if len(ms_name) == 1:
        system_name = ms_name[0]
    elif len(ms_name) > 1:
        err_msg = "Logical Partition Name:'{0}' found in more than one managed systems:'{1}'," \
                  " Please provide the system_name parameter to avoid the confusion".format(vm_name, ms_name)
        raise ParameterError(err_msg)
    else:
        err_msg = "Logical Partition Name:'{0}' not found in any of the managed systems".format(vm_name)
        raise ParameterError(err_msg)
    return system_name


def create_partition(module, params):
    changed = False
    cli_conn = None
    rest_conn = None
    system_uuid = None
    server_dom = None
    warning_msg = None
    validate_parameters(params)
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    vm_name = params['vm_name']
    vm_id = params['vm_id']
    proc = str(params['proc'] or 2)
    max_proc = str(params['max_proc'] or proc)
    min_proc = str(params['min_proc'] or 1)
    proc_mode = params['proc_mode'] or 'uncapped'
    weight = params['weight'] or 128
    mem = str(params['mem'] or 2048)
    max_mem = str(params['max_mem'] or mem)
    min_mem = str(params['min_mem'] or 1024)
    proc_unit = round(params['proc_unit'], 2) if params['proc_unit'] else None
    max_proc_unit = round(params['max_proc_unit'], 2) if params['max_proc_unit'] else proc_unit
    min_proc_unit = round(params['min_proc_unit'] or 0.1, 2)
    os_type = params['os_type']
    all_resources = params['all_resources']
    max_virtual_slots = str(params['max_virtual_slots'] or 20)
    physical_io = params['physical_io']
    proc_compatibility_mode = params['proc_compatibility_mode']
    shared_proc_pool = params['shared_proc_pool']
    vios_name = None
    temp_template_name = "ansible_powervm_create_{0}".format(str(randint(1000, 9999)))
    temp_copied = False
    fcports_config = None
    cli_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(cli_conn)

    try:
        rest_conn = HmcRestClient(hmc_host, hmc_user, password)
    except Exception as error:
        error_msg = parse_error_response(error)
        module.fail_json(msg=error_msg)

    try:
        system_uuid, server_dom = rest_conn.getManagedSystem(system_name)
    except Exception as error:
        try:
            rest_conn.logoff()
        except Exception:
            logger.debug("Logoff error")
        error_msg = parse_error_response(error)
        module.fail_json(msg=error_msg)
    if not system_uuid:
        module.fail_json(msg="Given system is not present")

    try:
        partition_uuid, partition_dom = rest_conn.getLogicalPartition(system_uuid, partition_name=vm_name)
    except Exception as error:
        try:
            rest_conn.logoff()
        except Exception:
            logger.debug("Logoff error")
        error_msg = parse_error_response(error)
        module.fail_json(msg=error_msg)

    if partition_dom:
        try:
            partition_prop = rest_conn.quickGetPartition(partition_uuid)
            partition_prop['AssociatedManagedSystem'] = system_name
        except Exception as error:
            try:
                rest_conn.logoff()
            except Exception:
                logger.debug("Logoff error")
            error_msg = parse_error_response(error)
            module.fail_json(msg=error_msg)
        return False, partition_prop, None

    if all_resources:
        try:
            hmc.createPartitionWithAllResources(system_name, vm_name, os_type)
            try:
                hmc.applyProfileToPartition(system_name, vm_name, "default_profile")
            except HmcError as apply_profile_error:
                hmc.deletePartition(system_name, vm_name, False, False)
                return False, repr(apply_profile_error), None
        except HmcError as crt_lpar_error:
            return False, repr(crt_lpar_error), None

        return True, None, None

    validate_proc_mem(server_dom, int(proc), int(mem), int(max_proc), int(min_proc), int(max_mem),
                      int(min_mem), weight, min_proc_unit, max_proc_unit, proc_unit)
    if shared_proc_pool:
        shared_proc_pool = rest_conn.validateSharedProcessorPoolNameAndID(system_uuid, shared_proc_pool)
        if not shared_proc_pool:
            raise HmcError("Shared Processor Pool ID or Name:{0}, does not exist in the managed system:{1}". format(params['shared_proc_pool'], system_name))

    if proc_compatibility_mode:
        supp_compat_modes = server_dom.xpath("//SupportedPartitionProcessorCompatibilityModes")
        supp_compat_modes = [scm.text.replace('Plus', 'plus') if scm.text != 'default' else 'Default' for scm in supp_compat_modes]
        if proc_compatibility_mode not in supp_compat_modes:
            raise HmcError("unsupported proc_compat_mode:{0}, Supported proc_compat_modes are {1}".format(proc_compatibility_mode, supp_compat_modes))

    try:
        if params['npiv_config']:
            fcports_config = fetch_fc_config(rest_conn, system_uuid, params['npiv_config'])

        if os_type in ['aix', 'linux', 'aix_linux']:
            reference_template = "QuickStart_lpar_rpa_2"
        else:
            reference_template = "QuickStart_lpar_IBMi_2"
        rest_conn.copyPartitionTemplate(reference_template, temp_template_name)
        temp_copied = True
        max_lpars = server_dom.xpath("//MaximumPartitions")[0].text
        logger.debug("CEC uuid: %s", system_uuid)

        temporary_temp_dom = rest_conn.getPartitionTemplate(name=temp_template_name)
        temp_uuid = temporary_temp_dom.xpath("//AtomID")[0].text

        # On servers that do not support the IBM i partitions with native I/O capability
        if os_type == 'ibmi' and \
                server_dom.xpath("//IBMiNativeIOCapable") and \
                server_dom.xpath("//IBMiNativeIOCapable")[0].text == 'false':
            srrTag = temporary_temp_dom.xpath("//SimplifiedRemoteRestartEnable")[0]
            srrTag.addnext(etree.XML('<isRestrictedIOPartition kb="CUD" kxe="false">true</isRestrictedIOPartition>'))
        config_dict = {}
        hmc_version = hmc.listHMCVersion()
        sp_level = int(hmc_version['SERVICEPACK'])
        if sp_level < 951:
            next_lpar_id = hmc.getNextPartitionID(system_name, max_lpars)
            logger.debug("Next Partiion ID: %s", str(next_lpar_id))
            config_dict['lpar_id'] = str(next_lpar_id)
        config_dict['vm_name'] = vm_name
        config_dict['proc'] = proc
        config_dict['max_proc'] = max_proc
        config_dict['min_proc'] = min_proc
        config_dict['proc_unit'] = str(proc_unit) if proc_unit else None
        config_dict['max_proc_unit'] = str(max_proc_unit)
        config_dict['min_proc_unit'] = str(min_proc_unit)
        config_dict['mem'] = mem
        config_dict['max_mem'] = max_mem
        config_dict['min_mem'] = min_mem
        config_dict['max_virtual_slots'] = max_virtual_slots
        config_dict['proc_mode'] = proc_mode
        config_dict['weight'] = str(weight) if proc_mode == 'uncapped' else str(0)
        config_dict['proc_comp_mode'] = proc_compatibility_mode
        config_dict['shared_proc_pool'] = shared_proc_pool if shared_proc_pool else str(0)
        if vm_id:
            config_dict['lpar_id'] = str(vm_id)

        # Tagged IO
        if os_type == 'ibmi':
            add_taggedIO_details(temporary_temp_dom)

        rest_conn.updateLparNameAndIDToDom(temporary_temp_dom, config_dict)

        # Add physical IO adapter
        if physical_io:
            add_physical_io(rest_conn, server_dom, temporary_temp_dom, physical_io)

        rest_conn.updateProcMemSettingsToDom(temporary_temp_dom, config_dict)

        # Add Virtual Networks to partition
        if params['virt_network_config']:
            virt_nw_list = fetch_virt_networks(rest_conn, system_uuid, params['virt_network_config'], max_virtual_slots)
            rest_conn.updateVirtualNWSettingsToDom(temporary_temp_dom, virt_nw_list)

        rest_conn.updatePartitionTemplate(temp_uuid, temporary_temp_dom)

        resp = rest_conn.checkPartitionTemplate(temp_template_name, system_uuid)
        draft_uuid = resp.xpath("//ParameterName[text()='TEMPLATE_UUID']/following-sibling::ParameterValue")[0].text

        draft_template_dom = rest_conn.getPartitionTemplate(uuid=draft_uuid)
        if not draft_template_dom:
            module.fail_json(msg="Not able to fetch template for partition deploy")

        # FC configuration should always be above vscsi configuration, otherwise template leads to marshal error
        if fcports_config:
            rest_conn.updateFCSettingsToDom(draft_template_dom, fcports_config)
            rest_conn.updatePartitionTemplate(draft_uuid, draft_template_dom)

        # Volume configuration settings
        pvid_added = []
        vscsi_clients_payload = ''
        if params['volume_config']:
            for each_vol_config in params['volume_config']:
                if 'vios_name' in each_vol_config and each_vol_config['vios_name']:
                    vios_name = each_vol_config['vios_name']
                    vios_response = rest_conn.getVirtualIOServersQuick(system_uuid)

                    if vios_response:
                        vios_list = json.loads(vios_response)
                        logger.debug(vios_list)
                        vios = [vios for vios in vios_list if vios['PartitionName'] == vios_name]
                        if not vios:
                            raise Error("Requested vios: {0} is not available".format(vios_name))
                    else:
                        raise Error("Requested vios: {0} is not available".format(vios_name))

                    vol_tuple_list = identifyFreeVolume(rest_conn, system_uuid, volume_name=each_vol_config['volume_name'],
                                                        vios_name=each_vol_config['vios_name'], pvid_list=pvid_added)
                else:
                    vol_tuple_list = identifyFreeVolume(rest_conn, system_uuid, volume_size=each_vol_config['volume_size'],
                                                        pvid_list=pvid_added)

                logger.debug(vol_tuple_list)
                if vol_tuple_list:
                    pvid_added.append(vol_tuple_list[0][2].xpath('UniqueDeviceID')[0].text)
                    vscsi_clients_payload += rest_conn.add_vscsi_payload(vol_tuple_list)
                else:
                    module.fail_json(msg="Unable to identify free physical volume")

            if vscsi_clients_payload:
                rest_conn.add_vscsi(draft_template_dom, vscsi_clients_payload)
                rest_conn.updatePartitionTemplate(draft_uuid, draft_template_dom)

        # Virtual NIC Configurations
        if params['vnic_config']:
            vios_response = rest_conn.getVirtualIOServersQuick(system_uuid)
            vios_list = json.loads(vios_response)
            vios_name_list = []
            for vios in vios_list:
                if vios['RMCState'] == 'active':
                    vios_name_list.append(vios['PartitionName'])
            if not vios_name_list:
                module.fail_json(msg="There are no RMC Active VIOS available in the managed system")
            sriov_adapters_dom = server_dom.xpath("//SRIOVAdapters//SRIOVAdapter")
            sriov_dvc_col = rest_conn.create_sriov_collection(sriov_adapters_dom)
            if not sriov_dvc_col:
                module.fail_json(msg="There are no SRIOV Physical ports available in the managed system")
            rest_conn.add_vnic_payload(draft_template_dom, params['vnic_config'], sriov_dvc_col, vios_name_list)
            rest_conn.updatePartitionTemplate(draft_uuid, draft_template_dom)

        resp_dom = rest_conn.deployPartitionTemplate(draft_uuid, system_uuid)
        partition_uuid = resp_dom.xpath("//ParameterName[text()='PartitionUuid']/following-sibling::ParameterValue")[0].text
        partition_prop = rest_conn.quickGetPartition(partition_uuid)
        partition_prop['AssociatedManagedSystem'] = system_name
        changed = True
    except Exception as error:
        error_msg = parse_error_response(error)
        logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(error))
        module.fail_json(msg=error_msg)
    finally:
        if temp_copied:
            try:
                rest_conn.deletePartitionTemplate(temp_template_name)
            except Exception as del_error:
                error_msg = parse_error_response(del_error)
                logger.debug(error_msg)

        try:
            rest_conn.logoff()
        except Exception as logoff_error:
            error_msg = parse_error_response(logoff_error)
            logger.debug(error_msg)

    return changed, partition_prop, warning_msg


def remove_partition(module, params):
    validate_parameters(params)
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    vm_name = params['vm_name']
    retainViosCfg = params['retain_vios_cfg']
    deleteVdisks = params['delete_vdisks']

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    # As this feature is supported only from 930 release
    hmc_version = hmc.listHMCVersion()
    sp_level = int(hmc_version['SERVICEPACK'])
    if sp_level < 930:
        if retainViosCfg or deleteVdisks:
            warn_msg = "retain_vios_cfg and delete_vdisks options are not supported on HMC release level below V9 R1 M930"
            module.warn(warn_msg)
        retainViosCfg = False
        deleteVdisks = False
    else:
        retainViosCfg = not (retainViosCfg)
    try:
        if system_name:
            hmc.deletePartition(system_name, vm_name, retainViosCfg, deleteVdisks)
        else:
            ms_name = identify_ManagedSystem_of_lpar(hmc, vm_name)
            hmc.deletePartition(ms_name, vm_name, retainViosCfg, deleteVdisks)
    except HmcError as del_lpar_error:
        error_msg = parse_error_response(del_lpar_error)
        if 'HSCL8012' in error_msg:
            return False, None, None
        else:
            return False, repr(del_lpar_error), None

    return True, None, None


def poweroff_partition(module, params):
    changed = False
    rest_conn = None
    system_uuid = None
    lpar_uuid = None
    lpar_response = None
    validate_parameters(params)
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    vm_name = params['vm_name']
    shutdown_option = params['shutdown_option'] or 'Delayed'
    restart_option = params['restart_option'] or 'Immediate'
    operation = params['action']

    try:
        rest_conn = HmcRestClient(hmc_host, hmc_user, password)
    except Exception as error:
        logger.debug(repr(error))
        module.fail_json(msg="Logon to HMC failed")

    try:
        if not system_name:
            hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
            hmc = Hmc(hmc_conn)
            system_name = identify_ManagedSystem_of_lpar(hmc, vm_name)

        system_uuid, server_dom = rest_conn.getManagedSystem(system_name)
        if not system_uuid:
            module.fail_json(msg="Given system is not present")
        ms_state = server_dom.xpath("//DetailedState")[0].text
        if ms_state != 'None':
            module.fail_json(msg="Given system is in " + ms_state + " state")

        lpar_response = rest_conn.getLogicalPartitionsQuick(system_uuid)
        if lpar_response is not None:
            lpar_quick_list = json.loads(lpar_response)
            for eachLpar in lpar_quick_list:
                if eachLpar['PartitionName'] == vm_name:
                    partition_dict = eachLpar
                    lpar_uuid = eachLpar['UUID']
                    break
        else:
            module.fail_json(msg="There are no Logical Partitions present on the system")

        if not lpar_uuid:
            module.fail_json(msg="Given Logical Partition is not present on the system")

        partition_state = partition_dict["PartitionState"]

        if partition_state == 'not activated':
            logger.debug("Given partition already in not activated state")
            return False, None, None
        else:
            if operation == 'restart':
                rest_conn.poweroffPartition(lpar_uuid, 'true', restart_option)
                changed = True
            elif operation == 'shutdown':
                rest_conn.poweroffPartition(lpar_uuid, 'false', shutdown_option)
                changed = True

    except (Exception, HmcError) as error:
        error_msg = parse_error_response(error)
        logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(error))
        module.fail_json(msg=error_msg)
    finally:
        try:
            rest_conn.logoff()
        except Exception as logoff_error:
            error_msg = parse_error_response(logoff_error)
            module.warn(error_msg)

    return changed, None, None


def poweron_partition(module, params):
    changed = False
    rest_conn = None
    system_uuid = None
    lpar_uuid = None
    prof_uuid = None
    lpar_response = None
    validate_parameters(params)
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    vm_name = params['vm_name']
    prof_name = params['prof_name']
    keylock = params['keylock']
    iIPLsource = params['iIPLsource']

    try:
        rest_conn = HmcRestClient(hmc_host, hmc_user, password)
    except Exception as error:
        logger.debug(repr(error))
        module.fail_json(msg="Logon to HMC failed")

    try:
        if not system_name:
            hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
            hmc = Hmc(hmc_conn)
            system_name = identify_ManagedSystem_of_lpar(hmc, vm_name)

        system_uuid, server_dom = rest_conn.getManagedSystem(system_name)
        if not system_uuid:
            module.fail_json(msg="Given system is not present")
        ms_state = server_dom.xpath("//DetailedState")[0].text
        if ms_state != 'None':
            module.fail_json(msg="Given system is in " + ms_state + " state")

        lpar_response = rest_conn.getLogicalPartitionsQuick(system_uuid)
        if lpar_response is not None:
            lpar_quick_list = json.loads(rest_conn.getLogicalPartitionsQuick(system_uuid))
            for eachLpar in lpar_quick_list:
                if eachLpar['PartitionName'] == vm_name:
                    partition_dict = eachLpar
                    lpar_uuid = eachLpar['UUID']
                    break
        else:
            module.fail_json(msg="There are no Logical Partitions present on the system")

        if not lpar_uuid:
            module.fail_json(msg="Provided Logical Partition is not present on the system")

        if prof_name:
            profs = rest_conn.getPartitionProfiles(lpar_uuid)
            for prof in profs:
                prof1 = etree.ElementTree(prof)
                pro_nam = prof1.xpath('//ProfileName/text()')[0]
                if prof_name == pro_nam:
                    prof_uuid = prof1.xpath('//AtomID/text()')[0]
                    logger.debug(prof_uuid)
                    break

        if prof_name and not prof_uuid:
            module.fail_json(msg="Provided Logical Partition Profile is not present on the logical Partition")

        partition_state = partition_dict["PartitionState"]
        partition_type = partition_dict["PartitionType"]

        if partition_state == 'not activated':
            warn_msg = 'unsupported parameter iIPLsource provided to a partition type: '
            if partition_type != 'OS400' and iIPLsource:
                module.warn(warn_msg + partition_type)
            try:
                rest_conn.poweronPartition(lpar_uuid, prof_uuid, keylock, iIPLsource, partition_type)
                changed = True
            except HmcError as hmcerr:
                err_msg = parse_error_response(hmcerr)
                resp_dict = json.loads(rest_conn.getLogicalPartitionQuick(lpar_uuid))
                partition_state2 = resp_dict["PartitionState"]
                if partition_state2 == 'error':
                    module.warn(err_msg)
                    changed = True
                else:
                    logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(hmcerr))
                    module.fail_json(msg=err_msg)

        else:
            logger.debug("Given partition already in not activated state")
            return False, None, None

    except Exception as error:
        error_msg = parse_error_response(error)
        logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(error))
        module.fail_json(msg=error_msg)
    finally:
        try:
            rest_conn.logoff()
        except Exception as logoff_error:
            error_msg = parse_error_response(logoff_error)
            module.warn(error_msg)

    return changed, None, None


def install_aix_os(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    vm_name = params['vm_name']
    vm_ip = params['install_settings']['vm_ip']
    nim_ip = params['install_settings']['nim_ip']
    nim_gateway = params['install_settings']['nim_gateway']
    nim_subnetmask = params['install_settings']['nim_subnetmask']
    location_code = params['install_settings']['location_code']
    profile_name = params['prof_name'] or 'default_profile'
    nim_vlan_id = params['install_settings']['nim_vlan_id'] or '0'
    nim_vlan_priority = params['install_settings']['nim_vlan_priority'] or '0'
    timeout = params['install_settings']['timeout'] or 60
    validate_parameters(params)
    changed = False
    warn_msg = None
    vm_property = None

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    if timeout < 10:
        module.fail_json(msg="timeout should be more than 10mins")
    try:
        lpar_details = hmc.getPartitionConfig(system_name, vm_name)
        if lpar_details['lpar_env'] != 'aixlinux':
            module.fail_json(msg="UnSupported logical partitions os type:" + lpar_details['lpar_env'] + ", Supported logical partition os type is aixlinux")

        if location_code:
            hmc.installOSFromNIM(location_code, nim_ip, nim_gateway, vm_ip, nim_vlan_id, nim_vlan_priority, nim_subnetmask, vm_name, profile_name, system_name)
        else:
            dvcdictlt = hmc.fetchIODetailsForNetboot(nim_ip, nim_gateway, vm_ip, vm_name, profile_name, system_name, nim_subnetmask)
            for dvcdict in dvcdictlt:
                if dvcdict['Ping Result'] == 'successful':
                    location_code = dvcdict['Location Code']
                    break
            if location_code:
                hmc.installOSFromNIM(location_code, nim_ip, nim_gateway, vm_ip, nim_vlan_id, nim_vlan_priority, nim_subnetmask,
                                     vm_name, profile_name, system_name)
            else:
                module.fail_json(msg="None of adapters part of the profile is reachable through network. Please attach correct network adapter")

        rmc_state, vm_property, ref_code = hmc.checkForOSToBootUpFully(system_name, vm_name, timeout)
        if rmc_state:
            changed = True
        elif ref_code in ['', '00']:
            changed = True
            warn_msg = "AIX installation has been successfull but RMC didnt come up, please check the HMC firewall and security"
        else:
            module.fail_json(msg="AIX Installation failed even after waiting for " + str(timeout) + " mins and the reference code is " + ref_code)
    except HmcError as install_error:
        return False, repr(install_error), None

    return changed, vm_property, warn_msg


def partition_details(module, params):
    rest_conn = None
    system_uuid = None
    server_dom = None
    partition_prop = None
    lpar_uuid = None
    validate_parameters(params)
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    vm_name = params['vm_name']
    advanced_info = params['advanced_info']

    try:
        rest_conn = HmcRestClient(hmc_host, hmc_user, password)
    except Exception as error:
        error_msg = parse_error_response(error)
        module.fail_json(msg=error_msg)

    try:
        if not system_name:
            hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
            hmc = Hmc(hmc_conn)
            system_name = identify_ManagedSystem_of_lpar(hmc, vm_name)

        system_uuid, server_dom = rest_conn.getManagedSystem(system_name)
        if not system_uuid:
            module.fail_json(msg="Given system is not present")
        ms_state = server_dom.xpath("//DetailedState")[0].text
        if ms_state != 'None':
            module.fail_json(msg="Given system is in " + ms_state + " state")

        lpar_response = rest_conn.getLogicalPartitionsQuick(system_uuid)
        if lpar_response is not None:
            lpar_quick_list = json.loads(lpar_response)
            for eachLpar in lpar_quick_list:
                if eachLpar['PartitionName'] == vm_name:
                    partition_prop = eachLpar
                    partition_prop['AssociatedManagedSystem'] = system_name
                    lpar_uuid = eachLpar['UUID']
                    break
        else:
            module.fail_json(msg="There are no Logical Partitions present on the system")

        if lpar_uuid and advanced_info:
            vios_response = rest_conn.getVirtualIOServersQuick(system_uuid)
            vios_list = []
            if vios_response is not None:
                vios_list = json.loads(vios_response)
            partition_prop['VirtualFiberChannelAdapters'] = rest_conn.fetchFCDetailsFromVIOS(system_uuid, partition_prop['PartitionID'], vios_list)
            partition_prop['VirtualSCSIClientAdapters'] = rest_conn.fetchSCSIDetailsFromVIOS(system_uuid, partition_prop['PartitionID'], vios_list)
            partition_prop['DedicatedVirtualNICs'] = rest_conn.fetchDedicatedVirtualNICs(system_uuid, lpar_uuid, vm_name, vios_list)

            lpar_uuid, partition_dom = rest_conn.getLogicalPartition(system_uuid, partition_uuid=lpar_uuid)
            partition_prop['MinimumMemory'] = partition_dom.xpath("//MinimumMemory")[0].text
            partition_prop['MaximumMemory'] = partition_dom.xpath("//MaximumMemory")[0].text
            isDedicatedProc = rest_conn.isDedicatedProcConfig(partition_dom)
            if isDedicatedProc:
                partition_prop['MinimumProcessors'] = partition_dom.xpath("//MinimumProcessors")[0].text
                partition_prop['MaximumProcessors'] = partition_dom.xpath("//MaximumProcessors")[0].text
            else:
                partition_prop['MinimumProcessingUnits'] = partition_dom.xpath("//MinimumProcessingUnits")[0].text
                partition_prop['MaximumProcessingUnits'] = partition_dom.xpath("//MaximumProcessingUnits")[0].text
                partition_prop['MinimumVirtualProcessors'] = partition_dom.xpath("//MinimumVirtualProcessors")[0].text
                partition_prop['MaximumVirtualProcessors'] = partition_dom.xpath("//MaximumVirtualProcessors")[0].text
                partition_prop['CurrentSharedProcessorPoolID'] = rest_conn.getProcPool(partition_dom)

            modeMapping = {
                'keep idle procs': 'keep_idle_procs',
                'sre idle proces': 'share_idle_procs',
                'sre idle procs active': 'share_idle_procs_active',
                'sre idle procs always': 'share_idle_procs_always',
                'uncapped': 'uncapped',
                'capped': 'capped'
            }

            partition_prop['SharingMode'] = modeMapping[partition_dom.xpath("//SharingMode")[0].text]
            if partition_prop['SharingMode'] == 'uncapped':
                partition_prop['UncappedWeight'] = rest_conn.getProcUncappedWeight(partition_dom)

        if not lpar_uuid:
            module.fail_json(msg="Given Logical Partition is not present on the system")

    except (Exception, HmcError) as error:
        error_msg = parse_error_response(error)
        logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(error))
        module.fail_json(msg=error_msg)
    finally:
        try:
            rest_conn.logoff()
        except Exception as logoff_error:
            error_msg = parse_error_response(logoff_error)
            module.warn(error_msg)

    return False, partition_prop, None


def perform_task(module):
    params = module.params
    actions = {
        "present": create_partition,
        "absent": remove_partition,
        "facts": partition_details,
        "shutdown": poweroff_partition,
        "poweron": poweron_partition,
        "restart": poweroff_partition,
        "install_os": install_aix_os,
    }

    oper = 'state'
    if params['state'] is None:
        oper = 'action'
    try:
        return actions[params[oper]](module, params)
    except (ParameterError, HmcError, Error) as error:
        return False, repr(error), None


def run_module():

    npiv_args = dict(vios_name=dict(type='str', required=True),
                     fc_port=dict(type='str', required=True),
                     wwpn_pair=dict(type='str'),
                     client_adapter_id=dict(type='int'),
                     server_adapter_id=dict(type='int')
                     )
    virt_network_args = dict(network_name=dict(type='str', required=True),
                             slot_number=dict(type='int')
                             )
    pv_args = dict(volume_name=dict(type='str'),
                   vios_name=dict(type='str'),
                   volume_size=dict(type='int')
                   )
    install_os_args = dict(vm_ip=dict(type='str', required=True),
                           nim_ip=dict(type='str', required=True),
                           nim_gateway=dict(type='str', required=True),
                           nim_subnetmask=dict(type='str', required=True),
                           location_code=dict(type='str'),
                           nim_vlan_id=dict(type='str'),
                           nim_vlan_priority=dict(type='str'),
                           timeout=dict(type='int')
                           )
    bck_dvc_args = dict(location_code=dict(type='str', required=True),
                        capacity=dict(type='float'),
                        hosting_partition=dict(type='str')
                        )
    vnic_args = dict(vnic_adapter_id=dict(type='int'),
                     backing_devices=dict(type='list',
                                          elements='dict',
                                          options=bck_dvc_args)
                     )

    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        hmc_host=dict(type='str', required=True),
        hmc_auth=dict(type='dict',
                      required=True,
                      no_log=True,
                      options=dict(
                          username=dict(required=True, type='str'),
                          password=dict(type='str', no_log=True),
                      )
                      ),
        system_name=dict(type='str'),
        vm_name=dict(type='str', required=True),
        vm_id=dict(type='int'),
        proc=dict(type='int'),
        max_proc=dict(type='int'),
        min_proc=dict(type='int'),
        proc_unit=dict(type='float'),
        max_proc_unit=dict(type='float'),
        min_proc_unit=dict(type='float'),
        proc_mode=dict(type='str', choices=['capped', 'uncapped']),
        weight=dict(type='int'),
        mem=dict(type='int'),
        max_mem=dict(type='int'),
        min_mem=dict(type='int'),
        proc_compatibility_mode=dict(type='str'),
        shared_proc_pool=dict(type='str'),
        os_type=dict(type='str', choices=['aix', 'linux', 'aix_linux', 'ibmi']),
        volume_config=dict(type='list',
                           elements='dict',
                           options=pv_args
                           ),
        virt_network_config=dict(type='list',
                                 elements='dict',
                                 options=virt_network_args
                                 ),
        npiv_config=dict(type='list',
                         elements='dict',
                         options=npiv_args
                         ),
        physical_io=dict(type='list', elements='str'),
        prof_name=dict(type='str'),
        all_resources=dict(type='bool'),
        max_virtual_slots=dict(type='int'),
        keylock=dict(type='str', choices=['manual', 'normal']),
        iIPLsource=dict(type='str', choices=['a', 'b', 'c', 'd']),
        retain_vios_cfg=dict(type='bool'),
        delete_vdisks=dict(type='bool'),
        advanced_info=dict(type='bool'),
        install_settings=dict(type='dict',
                              options=install_os_args),
        vnic_config=dict(type='list',
                         elements='dict',
                         options=vnic_args
                         ),
        shutdown_option=dict(type='str', choices=['Delayed', 'Immediate', 'OperatingSystem', 'OSImmediate']),
        restart_option=dict(type='str', choices=['Immediate', 'OperatingSystem', 'OSImmediate', 'Dump', 'DumpRetry']),
        state=dict(type='str',
                   choices=['present', 'absent', 'facts']),
        action=dict(type='str',
                    choices=['shutdown', 'poweron', 'restart', 'install_os'])
    )

    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=[('state', 'action')],
        required_one_of=[('state', 'action')],
        required_if=[['state', 'facts', ['hmc_host', 'hmc_auth', 'vm_name']],
                     ['state', 'absent', ['hmc_host', 'hmc_auth', 'vm_name']],
                     ['state', 'present', ['hmc_host', 'hmc_auth', 'system_name', 'vm_name', 'os_type']],
                     ['action', 'shutdown', ['hmc_host', 'hmc_auth', 'vm_name']],
                     ['action', 'poweron', ['hmc_host', 'hmc_auth', 'vm_name']],
                     ['action', 'restart', ['hmc_host', 'hmc_auth', 'vm_name']],
                     ['action', 'install_os', ['hmc_host', 'hmc_auth', 'system_name', 'vm_name', 'install_settings']],
                     ],
        required_by=dict(
            proc_unit=('proc', ),
            max_proc=('proc', ),
            min_proc=('proc', ),
            max_mem=('mem', ),
            min_mem=('mem', ),
            proc_mode=('proc_unit', ),
            weight=('proc_mode', ),
            max_proc_unit=('proc_unit', ),
            min_proc_unit=('proc_unit', ),
            shared_proc_pool=('proc_unit', ),
        ),
    )

    if module._verbosity >= 5:
        init_logger()

    if sys.version_info < (3, 0):
        py_ver = sys.version_info[0]
        module.fail_json(msg="Unsupported Python version {0}, supported python version is 3 and above".format(py_ver))

    changed, info, warning = perform_task(module)

    if isinstance(info, str):
        module.fail_json(msg=info)

    result = {}
    result['changed'] = changed
    if info:
        result['partition_info'] = info

    if warning:
        result['warning'] = warning

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
