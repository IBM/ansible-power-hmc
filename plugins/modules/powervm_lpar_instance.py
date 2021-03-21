#!/usr/bin/python

# Copyright: (c) 2018- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
from collections import OrderedDict

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
short_description: Create/Delete an AIX/Linux or IBMi partition
notes:
    - Currently supports creation of partition (powervm instance) with only processor and memory settings on dedicated mode
description:
    - "Creates AIX/Linux or IBMi partition with specified configuration details on mentioned system"
    - "Or Deletes specified AIX/Linux or IBMi partition on specified system"

version_added: "1.1.0"
requirements:
- Python >= 3
options:
    hmc_host:
        description:
            - The ipaddress or hostname of HMC
        required: true
        type: str
    hmc_auth:
        description:
            - Username and Password credential of HMC
        required: true
        type: dict
        suboptions:
            username:
                description:
                    - HMC user name
                required: true
                type: str
            password:
                description:
                    - HMC password
                required: true
                type: str
    system_name:
        description:
            - The name of the managed system
        required: true
        type: str
    vm_name:
        description:
            - The name of the powervm partition to create/delete
        required: true
        type: str
    proc:
        description:
            - The number of dedicated processors to create partition.
            - If C(proc_unit) parameter is set, then this value will work as Virtual Processors for
              shared processor setting
            - Default value is 2. This will not work during shared processor setting
        type: int
    proc_unit:
        description:
            - The number of shared processing units to create partition.
        type: float
    mem:
        description:
            - The value of dedicated memory value in megabytes to create partition.
            - Default value is 2048 MB.
        type: int
    os_type:
        description:
            - Type of logical partition to be created
            - C(aix_linux) or C(linux) or C(aix) for AIX or Linux operating system
            - C(ibmi) for IBMi operating system
        type: str
        choices: ['aix','linux','aix_linux','ibmi']
    state:
        description:
            - C(present) creates a partition of specifed I(os_type), I(vm_name), I(proc) and I(memory) on specified I(system_name)
            - C(absent) deletes a partition of specified I(vm_name) on specified I(system_name)
        required: true
        type: str
        choices: ['present', 'absent']
    volume_config:
        description:
            - Storage volume configurations of partition
            - Attachs the virtual SCSI backing physical volume provided by the Virtual IO Server Partition
            - Give implicit preference to redundancy in case if the identified/provided disk visible by two VIOSes  
        type: dict
        suboptions:
            volume_name:
                description:
                    - Physical volume name visible through vios
                      This option is mutually exclusive with I(volume_size)
                type: str
            volume_size:
                description:
                    - Physical volume size in MB
                type: int
            vios_name:
                description:
                    - Vios name to which mentioned I(volume_name) is present
                      This option is mutually exclusive with I(volume_size)
                type: str
'''

EXAMPLES = '''
- name: Create an IBMi logical partition instance
  powervm_lpar_instance:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
      system_name: <system_name>
      vm_name: <vm_name>
      proc: 4
      mem: 20480
      os_type: ibmi
      state: present

- name: Create an AIX/Linux logical partition instance with default proc and mem values
  powervm_lpar_instance:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
      system_name: <system_name>
      vm_name: <vm_name>
      os_type: aix_linux
      state: present

- name: Delete a logical partition instance
  powervm_lpar_instance:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
      system_name: <system_name>
      vm_name: <vm_name>
      state: absent
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
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_resource import Hmc
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import Error
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import parse_error_response
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import HmcRestClient
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import add_taggedIO_details
from random import randint
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


def validate_proc_mem(system_dom, proc, mem, proc_units=None):

    curr_avail_proc_units = system_dom.xpath('//CurrentAvailableSystemProcessorUnits')[0].text
    int_avail_proc = int(float(curr_avail_proc_units))

    if proc_units:
        min_proc_unit_per_virtproc = system_dom.xpath('//MinimumProcessorUnitsPerVirtualProcessor')[0].text
        float_min_proc_unit_per_virtproc = float(min_proc_unit_per_virtproc)
        if round(float(proc_units) % float_min_proc_unit_per_virtproc, 2) != float_min_proc_unit_per_virtproc:
            raise HmcError("Input processor units: {0} must be a multiple of {1}".format(proc_units, min_proc_unit_per_virtproc))

    curr_avail_mem = system_dom.xpath('//CurrentAvailableSystemMemory')[0].text
    int_avail_mem = int(curr_avail_mem)
    curr_avail_lmb = system_dom.xpath('//CurrentLogicalMemoryBlockSize')[0].text
    lmb = int(curr_avail_lmb)

    if proc > int_avail_proc:
        raise HmcError("Available system proc units is not enough. Provide value on or below {0}".format(str(int_avail_proc)))

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

    if 'volume_config' in sub_key:
        options = set(params.keys())
        together = ['volume_name', 'vios_name']
        mutually_exclusive_list = [('volume_name', 'vios_name'), ('volume_size',)]

    list1 = [each for each in options if each in mutually_exclusive_list[0]]
    list2 = [each for each in options if each in mutually_exclusive_list[1]]
    if list1 and list2:
        raise ParameterError("Parameters: '%s' and '%s' are  mutually exclusive" %
                             (', '.join(mutually_exclusive_list[0]), ', '.join(mutually_exclusive_list[1])))

    list3 = [each for each in options if each in together]
    if len(list3) >= 1 and set(list3) != set(together):
        raise ParameterError("Missing parameters %s" % (', '.join(set(together) - set(list3))))


def validate_parameters(params):
    '''Check that the input parameters satisfy the mutual exclusiveness of HMC'''
    if params['state'] == 'present':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'vm_name', 'os_type']
        unsupportedList = []
    else:
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'vm_name']
        unsupportedList = ['proc', 'mem', 'os_type', 'volume_config']

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
    logger.debug(vios_response)
    vios_uuid_list = []
    if vios_response:
        vios_list = json.loads(vios_response)
        logger.debug(vios_list)

        vios_uuid_list = [(vios['UUID'], vios['PartitionName']) for vios in vios_list if vios['RMCState'] == 'active']
        logger.debug(vios_uuid_list)

        if not vios_uuid_list:
            raise Error("Vioses are not available or RMC down")
    else:
        raise Error("Vioses are not available")

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
            for each in sorted_each_vios_pv_complex.items():
                logger.debug("Sorted Volume Name:%s", each[1].xpath("VolumeName")[0].text)
            keys_list += sorted_each_vios_pv_complex.keys()
            pv_complex.append((sorted_each_vios_pv_complex, vios_uuid, viosname))

    # Since the set is not order, ising OrderedDict to find unique keys
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
    # pick a random volume from any one of the vios
    if pv_complex and not found_list and not user_choice_vios:
        logger.debug("Picking a random single disk..")
        pv_obj = list(pv_complex[0][0].values())[0]
        volume_nm = pv_obj.xpath("VolumeName")[0].text
        return [(volume_nm, pv_complex[0][2], pv_obj)]

    return None


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
    vios_name = None
    temp_template_name = "draft_ansible_powervm_create_{0}".format(str(randint(1000, 9999)))
    temp_copied = False
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

    validate_proc_mem(server_dom, int(proc), int(mem))

    try:
        if os_type in ['aix', 'linux', 'aix_linux']:
            reference_template = "QuickStart_lpar_rpa_2"
        else:
            reference_template = "QuickStart_lpar_IBMi_2"
        rest_conn.copyPartitionTemplate(reference_template, temp_template_name)
        temp_copied = True
        max_lpars = server_dom.xpath("//MaximumPartitions")[0].text
        next_lpar_id = hmc.getNextPartitionID(system_name, max_lpars)
        logger.debug("Next Partiion ID: %s", str(next_lpar_id))
        logger.debug("CEC uuid: %s", system_uuid)

        temporary_temp_dom = rest_conn.getPartitionTemplate(name=temp_template_name)
        temp_uuid = temporary_temp_dom.xpath("//AtomID")[0].text
        # On servers that do not support the IBM i partitions with native I/O capability
        if os_type == 'ibmi' and \
                server_dom.xpath("//IBMiNativeIOCapable") and \
                server_dom.xpath("//IBMiNativeIOCapable")[0].text == 'false':
            srrTag = temporary_temp_dom.xpath("//SimplifiedRemoteRestartEnable")[0]
            srrTag.addnext(etree.XML('<isRestrictedIOPartition kb="CUD" kxe="false">true</isRestrictedIOPartition>'))

        config_dict = {'lpar_id': str(next_lpar_id)}
        config_dict['vm_name'] = vm_name
        config_dict['proc'] = proc
        config_dict['proc_unit'] = str(proc_unit) if proc_unit else None
        config_dict['mem'] = mem
        if os_type == 'ibmi':
            add_taggedIO_details(temporary_temp_dom)

        rest_conn.updateProcMemSettingsToDom(temporary_temp_dom, config_dict)
        rest_conn.updatePartitionTemplate(temp_uuid, temporary_temp_dom)

        resp = rest_conn.checkPartitionTemplate(temp_template_name, system_uuid)
        draft_uuid = resp.xpath("//ParameterName[text()='TEMPLATE_UUID']/following-sibling::ParameterValue")[0].text

        draft_template_dom = rest_conn.getPartitionTemplate(uuid=draft_uuid)
        if not draft_template_dom:
            module.fail_json(msg="Not able to fetch template for partition deploy")

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
                rest_conn.add_vscsi_payload(draft_template_dom, config_dict['lpar_id'], vol_tuple_list)
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
    changed = False
    rest_conn = None
    system_uuid = None
    validate_parameters(params)
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    vm_name = params['vm_name']

    try:
        rest_conn = HmcRestClient(hmc_host, hmc_user, password)
    except Exception as error:
        logger.debug(repr(error))
        module.fail_json(msg="Logon to HMC failed")

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
        if not partition_dom:
            logger.debug("Given partition already absent on the managed system")
            return False, None, None

        if partition_dom.xpath("//PartitionState")[0].text != 'not activated':
            module.fail_json(msg="Given logical partition:{0} is not in shutdown state".format(vm_name))

        rest_conn.deleteLogicalPartition(partition_uuid)
        changed = True
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


def perform_task(module):
    params = module.params
    actions = {
        "present": create_partition,
        "absent": remove_partition
    }

    try:
        return actions[params['state']](module, params)
    except (ParameterError, HmcError, Error) as error:
        return False, repr(error), None


def run_module():

    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        hmc_host=dict(type='str', required=True),
        hmc_auth=dict(type='dict',
                      required=True,
                      no_log=True,
                      options=dict(
                          username=dict(required=True, type='str'),
                          password=dict(required=True, type='str'),
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
        state=dict(required=True, type='str',
                   choices=['present', 'absent'])
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_if=[['state', 'absent', ['hmc_host', 'hmc_auth', 'system_name', 'vm_name']],
                     ['state', 'present', ['hmc_host', 'hmc_auth', 'system_name', 'vm_name',
                      'os_type']]
                     ],
        required_by=dict(
            proc_unit=('proc', ),
        ),

    )

    if module._verbosity >= 1:
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
