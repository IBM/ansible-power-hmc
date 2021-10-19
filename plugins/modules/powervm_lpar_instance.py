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
short_description: Create, Delete, Shutdown, Activate, Restart and facts of an AIX/Linux or IBMi partition
notes:
    - The network configuration currently will not support SRIOV or VNIC related configurations.
    - I(retain_vios_cfg) and I(delete_vdisks) options will only be supported from HMC release level on or above V9 R1 M930.
    - Partition creation is not supported for resource role-based user in HMC Version prior to 951.
description:
    - "Creates AIX/Linux or IBMi partition with specified configuration details on mentioned system"
    - "Or Deletes specified AIX/Linux or IBMi partition on specified system"
    - "Or Shutdown specified AIX/Linux or IBMi partition on specified system"
    - "Or Poweron/Activate specified AIX/Linux or IBMi partition, with provided configuration details on the mentioned system"
    - "Or Restart specified AIX/Linux or IBMi partition on specified system"
    - "Or facts of the specified AIX/Linux or IBMi partition of specified system"

version_added: "1.1.0"
requirements:
- Python >= 3
- lxml
options:
    hmc_host:
        description:
            - IPaddress or hostname of the HMC
        required: true
        type: str
    hmc_auth:
        description:
            - Username and Password credential of the HMC
        required: true
        type: dict
        suboptions:
            username:
                description:
                    - HMC username
                required: true
                type: str
            password:
                description:
                    - HMC password
                type: str
    system_name:
        description:
            - The name of the managed system
        required: true
        type: str
    vm_name:
        description:
            - The name of the powervm partition to create/delete/poweron/shutdown/facts
        required: true
        type: str
    proc:
        description:
            - The number of dedicated processors to create a partition.
            - If C(proc_unit) parameter is set, then this value will work as virtual processors for
              shared processor setting.
            - Default value is 2. This will not work during shared processor setting.
        type: int
    proc_unit:
        description:
            - The number of shared processing units to create a partition.
        type: float
    mem:
        description:
            - The value of dedicated memory value in megabytes to create a partition.
            - Default value is 2048 MB.
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
            - This option is valid only for C(poweron) I(action)
        type: str
        choices: ['a','b','c','d']
    volume_config:
        description:
            - Storage volume configurations of a partition.
            - Attaches Physical Volume via Virtual SCSI.
            - Redundant paths created by default, if the specified/identified physical volume is visible in more than one VIOS.
            - User needs to provide either I(volume_size) or both I(volume_name) and I(vios_name). If I(volume_size) is provided,
              available physical volume matching or greater than specified size would be attached.
        type: dict
        suboptions:
            volume_name:
                description:
                    - Physical volume name visible through VIOS.
                      This option is mutually exclusive with I(volume_size)
                type: str
            vios_name:
                description:
                    - VIOS name to which mentioned I(volume_name) is present.
                      This option is mutually exclusive with I(volume_size)
                type: str
            volume_size:
                description:
                    - Physical volume size in MB
                type: int
    virt_network_config:
        description:
            - Virtual Network configuration of the partition
            - This implicitly adds a Virtual Ethernet Adapter with given virtual network to the partition
            - Make sure provided Virtual Network has been attached to an active Network Bridge for external network communication.
        type: dict
        suboptions:
            network_name:
                description:
                    - Name of the Virtual Network to be attached to the partition.
                    - This option is mandatory
                required: true
                type: str
            slot_number:
                description:
                    - Virtual slot number of a partition on which virtual network to be attached.
                    - Optional, if not provided, next available value will be assigned.
                type: int
    npiv_config:
        description:
            - To configure N-Port ID Virtualization is also known as Virtual Fibre of the partition
            - User can provide two fc port configurations and mappings will be created with VIOS implicitly
        type: list
        elements: dict
        suboptions:
            vios_name:
                description:
                    - The name of the vios in which fc port available
                    - This option is mandatory
                required: true
                type: str
            fc_port:
                description:
                    - The port to be used for npiv. User can specify either port name or fully qualified location code
                    - This option is mandatory
                required: true
                type: str
            wwpn_pair:
                description:
                    - The WWPN pair value to be configured with client FC adapter.
                    - Both the WWPN value should be separated by semicolon delimiter
                    - Optional, if not provided the value will be auto assigned
                type: str
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
    state:
        description:
            - C(present) creates a partition of the specified I(os_type), I(vm_name), I(proc) and I(memory) on specified I(system_name).
            - C(absent) deletes a partition of the specified I(vm_name) on specified I(system_name).
            - C(facts) fetch the details of the specified I(vm_name) on specified I(system_name).
        type: str
        choices: ['present', 'absent', 'facts']
    action:
        description:
            - C(shutdown) shutdown a partition of the specified I(vm_name) on specified I(system_name).
            - C(poweron) poweron a partition of the specified I(vm_name) with specified I(prof_name), I(keylock), I(iIPLsource) on specified I(system_name).
            - C(restart) restart a partition of the specified I(vm_name) on specified I(system_name).
        type: str
        choices: ['poweron', 'shutdown', 'restart']
'''

EXAMPLES = '''
- name: Create an IBMi logical partition instance with shared proc, volume_config's vios_name and volume_name values, PhysicaIO and
        max_virtual_slots
  powervm_lpar_instance:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
      system_name: <system_name>
      vm_name: <vm_name>
      proc: 4
      proc_unit: 4
      mem: 20480
      volume_config:
         vios_name: <viosname>
         volume_name: <volumename>
      physical_io: <IO_location_code>
      max_virtual_slots: 50
      os_type: ibmi
      state: present

- name: Create an AIX/Linux logical partition instance with default proc, mem, virt_network_config, volume_config's volumes_size and
        npiv_config
  powervm_lpar_instance:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
      system_name: <system_name>
      vm_name: <vm_name>
      volume_config:
         volume_size: <disk_size>
      virt_network_config:
         network_name: <virtual_nw_name>
         slot_number: <client_slot_no>
      npiv_config:
         - vios_name: <viosname>
           fc_port: <fc_port_name/loc_code>
           wwpn_pair: <wwpn1;wwpn2>
      os_type: aix_linux
      state: present

- name: Delete a logical partition instance with retain_vios_cfg and delete_vdisk options
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

- name: Shutdown a logical partition
  powervm_lpar_instance:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
      system_name: <system_name>
      vm_name: <vm_name>
      action: shutdown

- name: Activate an AIX/Linux logical partition with user defined profile_name
  powervm_lpar_instance:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
      system_name: <system_name>
      vm_name: <vm_name>
      prof_name: <profile_name>
      action: poweron

- name: Activate IBMi based on its current configuration with keylock and iIPLsource options
  powervm_lpar_instance:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
      system_name: <system_name>
      vm_name: <vm_name>
      keylock: 'norm'
      iIPLsource: 'd'
      action: poweron

- name: Create a partition with all resources
  powervm_lpar_instance:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
      system_name: <system_name>
      vm_name: <vm_name>
      all_resources: True
      state: present

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
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import parse_error_response
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import HmcRestClient
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import add_taggedIO_details
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import add_physical_io
from random import randint
from collections import OrderedDict
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


def validate_proc_mem(system_dom, proc, mem, proc_unit=None):

    curr_avail_proc_units = system_dom.xpath('//CurrentAvailableSystemProcessorUnits')[0].text
    curr_avail_procs = float(curr_avail_proc_units)
    int_avail_proc = int(curr_avail_procs)

    if proc_unit:
        min_proc_unit_per_virtproc = system_dom.xpath('//MinimumProcessorUnitsPerVirtualProcessor')[0].text
        float_min_proc_unit_per_virtproc = float(min_proc_unit_per_virtproc)
        if round(float(proc_unit) % float_min_proc_unit_per_virtproc, 2) != float_min_proc_unit_per_virtproc:
            raise HmcError("Input processor units: {0} must be a multiple of {1}".format(proc_unit, min_proc_unit_per_virtproc))

        if proc_unit > curr_avail_procs:
            raise HmcError("{0} Available system proc units is not enough for {1} shared CPUs. Provide value on or below {0}".format(str(curr_avail_procs),str(proc_unit)))

    else:
        if proc > curr_avail_procs:
            raise HmcError("{2} Available system proc units is not enough for {1} dedicated CPUs. Provide value on or below {0} CPUs".format(str(int_avail_proc),str(proc),str(curr_avail_procs)))

    curr_avail_mem = system_dom.xpath('//CurrentAvailableSystemMemory')[0].text
    int_avail_mem = int(curr_avail_mem)
    curr_avail_lmb = system_dom.xpath('//CurrentLogicalMemoryBlockSize')[0].text
    lmb = int(curr_avail_lmb)

    if mem % lmb > 0:
        raise HmcError("Requested mem value not in mutiple of block size:{0}".format(curr_avail_lmb))

    if mem > int_avail_mem:
        raise HmcError("Available system memory is not enough. Provide value on or below {0}".format(curr_avail_mem))


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
        unsupportedList = ['prof_name', 'keylock', 'iIPLsource', 'retain_vios_cfg', 'delete_vdisks']
    elif opr == 'poweron':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'vm_name']
        unsupportedList = ['proc', 'mem', 'os_type', 'proc_unit', 'volume_config', 'virt_network_config', 'retain_vios_cfg', 'delete_vdisks',
                           'all_resources', 'max_virtual_slots']
    elif opr == 'absent':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'vm_name']
        unsupportedList = ['proc', 'mem', 'os_type', 'proc_unit', 'prof_name', 'keylock', 'iIPLsource', 'volume_config', 'virt_network_config',
                           'all_resources', 'max_virtual_slots']
    else:
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'vm_name']
        unsupportedList = ['proc', 'mem', 'os_type', 'proc_unit', 'prof_name', 'keylock', 'iIPLsource', 'volume_config', 'virt_network_config',
                           'retain_vios_cfg', 'delete_vdisks', 'all_resources', 'max_virtual_slots']

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
        validate_sub_dict('volume_config', params['volume_config'])


def fetchAllInUsePhyVolumes(rest_conn, vios_uuid):
    pvid_in_use = []
    vios_response = rest_conn.getVirtualIOServer(vios_uuid, group="ViosStorage")
    phy_vol_list = vios_response.xpath("//MoverServicePartition/following-sibling::PhysicalVolumes/PhysicalVolume")
    for each_phy_vol in phy_vol_list:
        if each_phy_vol.xpath("AvailableForUsage")[0].text == "false":
            pvid_in_use.append(each_phy_vol.xpath("UniqueDeviceID")[0].text)

    logger.debug("Disks in use for vios: %s are %s", vios_uuid, pvid_in_use)
    return pvid_in_use


def identifyFreeVolume(rest_conn, system_uuid, volume_name=None, volume_size=0, vios_name=None):
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

        if each_fc['fc_port'] is not None:
            vios_fcports = rest_conn.vios_fetch_fcports_info(vios[0]['UUID'])
            port_identified = [v_fcPort for v_fcPort in vios_fcports if v_fcPort['LocationCode'] == each_fc['fc_port']
                               or v_fcPort['PortName'] == each_fc['fc_port']]
            if port_identified:
                port_identified[0].update({'viosname': each_fc['vios_name']})
                if each_fc['wwpn_pair'] is not None and wwpn_pair_is_valid(each_fc['wwpn_pair']):
                    port_identified[0].update({'wwpn_pair': each_fc['wwpn_pair']})
                fcports_identified.append(port_identified[0])
            else:
                raise Error("Given fc port:{0} is either not NPIV capable or not available".format(each_fc['fc_port']))

    return fcports_identified


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
    proc = str(params['proc'] or 2)
    mem = str(params['mem'] or 2048)
    proc_unit = params['proc_unit']
    os_type = params['os_type']
    all_resources = params['all_resources']
    max_virtual_slots = str(params['max_virtual_slots'] or 20)
    physical_io = params['physical_io']
    vios_name = None
    temp_template_name = "ansible_powervm_create_{0}".format(str(randint(1000, 9999)))
    temp_copied = False
    nw_uuid = None
    virt_network_name = None
    virtual_slot_number = None
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
        partition_uuid, partition_dom = rest_conn.getLogicalPartition(system_uuid, vm_name)
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

    validate_proc_mem(server_dom, int(proc), int(mem), proc_unit)

    if params['npiv_config']:
        fcports_config = fetch_fc_config(rest_conn, system_uuid, params['npiv_config'])

    try:
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
        config_dict['proc_unit'] = str(proc_unit) if proc_unit else None
        config_dict['mem'] = mem
        config_dict['max_virtual_slots'] = max_virtual_slots

        # Tagged IO
        if os_type == 'ibmi':
            add_taggedIO_details(temporary_temp_dom)

        rest_conn.updateLparNameAndIDToDom(temporary_temp_dom, config_dict)

        # Add physical IO adapter
        if physical_io:
            add_physical_io(rest_conn, server_dom, temporary_temp_dom, physical_io)

        rest_conn.updateProcMemSettingsToDom(temporary_temp_dom, config_dict)
        # Virtual Network Configuration settings
        if params['virt_network_config']:
            if 'network_name' in params['virt_network_config'] and params['virt_network_config']['network_name']:
                virt_network_name = params['virt_network_config']['network_name']
            if 'slot_number' in params['virt_network_config'] and params['virt_network_config']['slot_number']:
                virtual_slot_number = int(params['virt_network_config']['slot_number'])
                if virtual_slot_number > int(max_virtual_slots):
                    raise Error("Virtual slot number: {0} is greater than max virtual slots allowed in a partition".format(virtual_slot_number))

        if virt_network_name:
            vnw_response = rest_conn.getVirtualNetworksQuick(system_uuid)
            if vnw_response:
                for nw in vnw_response:
                    nw_name = nw['NetworkName']
                    if nw_name == virt_network_name:
                        nw_uuid = nw['UUID']
                        nw_dict = {'nw_name': nw_name, 'nw_uuid': nw_uuid, 'virtual_slot_number': virtual_slot_number}
                        rest_conn.updateVirtualNWSettingsToDom(temporary_temp_dom, nw_dict)
                        break
                if not nw_uuid:
                    raise Error("Requested Virtual Network: {0} is not available".format(virt_network_name))

            else:
                raise Error("There are no Virtual Networks present in the system")
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
        if params['volume_config']:
            if 'vios_name' in params['volume_config'] and params['volume_config']['vios_name']:
                vios_name = params['volume_config']['vios_name']
                vios_response = rest_conn.getVirtualIOServersQuick(system_uuid)

                if vios_response:
                    vios_list = json.loads(vios_response)
                    logger.debug(vios_list)
                    vios = [vios for vios in vios_list if vios['PartitionName'] == vios_name]
                    if not vios:
                        raise Error("Requested vios: {0} is not available".format(vios_name))
                else:
                    raise Error("Requested vios: {0} is not available".format(vios_name))

                vol_tuple_list = identifyFreeVolume(rest_conn, system_uuid, volume_name=params['volume_config']['volume_name'],
                                                    vios_name=params['volume_config']['vios_name'])
            else:
                vol_tuple_list = identifyFreeVolume(rest_conn, system_uuid, volume_size=params['volume_config']['volume_size'])

            logger.debug(vol_tuple_list)
            if vol_tuple_list:
                rest_conn.add_vscsi_payload(draft_template_dom, vol_tuple_list)
                rest_conn.updatePartitionTemplate(draft_uuid, draft_template_dom)
            else:
                module.fail_json(msg="Unable to identify free physical volume")

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
        retainViosCfg = not(retainViosCfg)

    try:
        hmc.deletePartition(system_name, vm_name, retainViosCfg, deleteVdisks)
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
    operation = params['action']

    try:
        rest_conn = HmcRestClient(hmc_host, hmc_user, password)
    except Exception as error:
        logger.debug(repr(error))
        module.fail_json(msg="Logon to HMC failed")

    try:
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
                rest_conn.poweroffPartition(lpar_uuid, 'shutdown', 'true')
                changed = True
            elif operation == 'shutdown':
                rest_conn.poweroffPartition(lpar_uuid, 'shutdown')
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

    try:
        rest_conn = HmcRestClient(hmc_host, hmc_user, password)
    except Exception as error:
        error_msg = parse_error_response(error)
        module.fail_json(msg=error_msg)

    try:
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
                     wwpn_pair=dict(type='str')
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
        system_name=dict(type='str', required=True),
        vm_name=dict(type='str', required=True),
        proc=dict(type='int'),
        proc_unit=dict(type='float'),
        mem=dict(type='int'),
        os_type=dict(type='str', choices=['aix', 'linux', 'aix_linux', 'ibmi']),
        volume_config=dict(type='dict',
                           options=dict(
                               volume_name=dict(type='str'),
                               vios_name=dict(type='str'),
                               volume_size=dict(type='int'),
                           )
                           ),
        virt_network_config=dict(type='dict',
                                 options=dict(
                                     network_name=dict(type='str', required=True),
                                     slot_number=dict(type='int'),
                                 )
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
        state=dict(type='str',
                   choices=['present', 'absent', 'facts']),
        action=dict(type='str',
                    choices=['shutdown', 'poweron', 'restart'])
    )

    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=[('state', 'action')],
        required_one_of=[('state', 'action')],
        required_if=[['state', 'facts', ['hmc_host', 'hmc_auth', 'system_name', 'vm_name']],
                     ['state', 'absent', ['hmc_host', 'hmc_auth', 'system_name', 'vm_name']],
                     ['state', 'present', ['hmc_host', 'hmc_auth', 'system_name', 'vm_name', 'os_type']],
                     ['action', 'shutdown', ['hmc_host', 'hmc_auth', 'system_name', 'vm_name']],
                     ['action', 'poweron', ['hmc_host', 'hmc_auth', 'system_name', 'vm_name']],
                     ['action', 'restart', ['hmc_host', 'hmc_auth', 'system_name', 'vm_name']]
                     ],
        required_by=dict(
            proc_unit=('proc', ),
        ),
    )

    if module._verbosity >= 5:
        init_logger()

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
