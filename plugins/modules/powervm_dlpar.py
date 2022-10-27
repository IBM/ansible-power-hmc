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
module: powervm_dlpar
author:
    - Anil Vijayan(@AnilVijayan)
short_description: Dynamically managing resources of partition
description:
    - "Managing processor resources dynamically"
    - "Managing memory resources dynamically"
version_added: 1.0.0
options:
    hmc_host:
        description:
            - The IP Address or hostname of the HMC.
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
                    - Username of the HMC to login.
                required: true
                type: str
            password:
                description:
                    - Password of the HMC.
                type: str
    system_name:
        description:
            - The name of the managed system.
        required: true
        type: str
    vm_name:
        description:
            - The name of the powervm partition.
        required: true
        type: str
    proc_settings:
        description:
            - Processor related settings
        required: true
        type: dict
        suboptions:
            proc:
                description:
                    - The number of dedicated processors to create a partition.
                    - If C(proc_unit) parameter is set, then this value will work as virtual processors for
                      shared processor setting.
                type: int
            proc_unit:
                description:
                    - The number of shared processing units to create a partition.
                type: float
            sharing_mode:
                description:
                    - The sharing mode of the partition
                    - Valid values for partitions using dedicated processors are
                      C(keep_idle_procs), C(share_idle_procs), C(share_idle_procs_active), C(share_idle_procs_always)
                    - Valid values for partitions using shared processors are
                      C(capped), C(uncapped)
                type: str
            uncapped_weight:
                description:
                    - The uncapped weight of the partition
                type: int
            pool_id:
                description:
                    - Shared Processor Pool ID to be set
                type: int
    mem_settings:
        description:
            - Memory related settings
        required: true
        type: dict
        suboptions:
            mem:
                description:
                    - The value of dedicated memory value in megabytes to create a partition.
                type: int
    timeout:
        description:
            - The maximum time, in seconds, to wait for partition operating system commands issued by the HMC to complete
        required: true
        type: int
    action:
        description:
            - C(update) updates the resources of the partition. Currently it supports
              the update of processor or memory resources.
        type: str
        choices: ['update']

'''

EXAMPLES = '''
- name: Dynamically set the processor and memory values
  powervm_dlpar:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    system_name: <server name>
    vm_name: <vm name>
    proc_settings:
      proc: 3
      proc_unit: 2.5
      sharing_mode: 'uncapped'
      uncapped_weight: 131
      pool_id: 2
    mem_settings:
      mem: 3072
    action: update
'''

RETURN = '''
partition_info:
    description: Return the proc and memory attributes of the partition
    type: dict
    returned: always
'''

import logging
LOG_FILENAME = "/tmp/ansible_power_hmc.log"
logger = logging.getLogger(__name__)
import sys
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_resource import Hmc
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import Error
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import parse_error_response
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import HmcRestClient


def init_logger():
    logging.basicConfig(
        filename=LOG_FILENAME,
        format='[%(asctime)s] %(levelname)s: [%(funcName)s] %(message)s',
        level=logging.DEBUG)


def fetch_facts(rest_conn, partition_dom):
    proc = None
    proc_unit = None
    uncapped_weight = None
    pool_id = None

    isDedicated = rest_conn.isDedicatedProcConfig(partition_dom)
    sharingMode = rest_conn.getProcSharingMode(partition_dom)

    if isDedicated:
        proc = partition_dom.xpath("//CurrentDedicatedProcessorConfiguration/CurrentProcessors")[0].text
    else:
        proc_unit = partition_dom.xpath("//CurrentSharedProcessorConfiguration/CurrentProcessingUnits")[0].text
        proc = partition_dom.xpath("//CurrentSharedProcessorConfiguration/AllocatedVirtualProcessors")[0].text
        if sharingMode == 'uncapped':
            uncapped_weight = rest_conn.getProcUncappedWeight(partition_dom)
        pool_id = rest_conn.getProcPool(partition_dom)

    mem = partition_dom.xpath("//CurrentMemory")[0].text
    powervm_name = partition_dom.xpath("//PartitionName")[0].text
    facts = {
        'proc': proc,
        'sharing_mode': sharingMode,
        'mem': mem,
        'vm_name': powervm_name
    }

    if proc_unit:
        facts.update({'proc_unit': proc_unit})
    if uncapped_weight:
        facts.update({'uncapped_weight': uncapped_weight})
    if pool_id:
        facts.update({'pool_id': pool_id})

    return facts


def update_proc_mem(module, params):
    logger.debug(params)
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    vm_name = params['vm_name']
    operation = params['action']
    timeout = params["timeout"]
    proc = params['proc_settings']['proc'] if params.get('proc_settings') else None
    proc_unit = params['proc_settings']['proc_unit'] if params.get('proc_settings') else None
    sharing_mode = params['proc_settings']['sharing_mode'] if params.get('proc_settings') else None
    uncapped_weight = params['proc_settings']['uncapped_weight'] if params.get('proc_settings') else None
    pool_id = params['proc_settings']['pool_id'] if params.get('proc_settings') else None
    mem = params['mem_settings']['mem'] if params.get('mem_settings') else None
    changed = False
    difference = False
    isDedicated = None
    prevProcUnitValue = None
    prevProcValue = None
    prevPoolID = None
    prevMem = None
    prevSharingMode = None
    prevUncappedWeight = None
    newProcUnitValue = None
    newProcValue = None
    newMem = None
    newSharingMode = None
    newUncappedWeight = None
    newPoolID = None

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
    if partition_uuid is None:
        module.fail_json(msg="Given powervm instance is not present")

    isDedicated = rest_conn.isDedicatedProcConfig(partition_dom)
    if isDedicated and proc_unit is not None:
        raise ParameterError("Given parition is in dedicated configuration.\
Setting proc units is not supported")

    prevProcValue = rest_conn.getProcs(isDedicated, partition_dom)
    if not isDedicated:
        prevProcUnitValue = rest_conn.getProcUnits(partition_dom)
    if (proc is not None and prevProcValue != proc):
        logger.debug("prevProcValue: %s", prevProcValue)
        partition_dom = rest_conn.updateProc(partition_dom, isDedicated, proc=str(proc))
        difference = True
    elif (proc_unit is not None and prevProcUnitValue != proc_unit):
        logger.debug("prevProcUnitValue: %s", prevProcUnitValue)
        partition_dom = rest_conn.updateProc(partition_dom, isDedicated, proc_unit=str(proc_unit))
        difference = True

    if pool_id is not None and pool_id >= 0:
        if isDedicated:
            module.fail_json(msg="Shared processor pool only works with shared processor configuration partition")
        else:
            prevPoolID = rest_conn.getProcPool(partition_dom)
            logger.debug("prevPoolID: %s", prevPoolID)
            if prevPoolID != pool_id:
                partition_dom = rest_conn.updateProcPool(partition_dom, str(pool_id))
                difference = True

    if mem:
        prevMem = rest_conn.getMem(partition_dom)
        logger.debug("prevMem: %s", prevMem)
        if prevMem != mem:
            partition_dom = rest_conn.updateMem(partition_dom, str(mem))
            difference = True

    if sharing_mode:
        prevSharingMode = rest_conn.getProcSharingMode(partition_dom)
        logger.debug("prevSharingMode: %s", prevSharingMode)
        if isDedicated:
            if sharing_mode in ['capped', 'uncapped']:
                module.fail_json(msg="Given sharing mode is not supported with dedicated processor configuration")
        else:
            if sharing_mode not in ['capped', 'uncapped']:
                module.fail_json(msg="Given sharing mode is not supported with shared processor configuration")
        if prevSharingMode != sharing_mode:
            logger.debug("sharing_mode: %s", sharing_mode)
            partition_dom = rest_conn.updateProcSharingMode(partition_dom, sharing_mode)
            difference = True

    if uncapped_weight:
        prevUncappedWeight = rest_conn.getProcUncappedWeight(partition_dom)
        if isDedicated:
            module.fail_json(msg="Uncapped weight is not supported with dedicated processor configuration")
        else:
            if rest_conn.getProcSharingMode(partition_dom) != 'uncapped' or \
                    (sharing_mode is not None and sharing_mode != 'uncapped'):
                module.fail_json(msg="Uncapped weight is not supported in case sharing mode is not uncapped")
        if prevUncappedWeight != uncapped_weight:
            partition_dom = rest_conn.updateProcUncappedWeight(partition_dom, str(uncapped_weight))
            difference = True

    if difference:
        try:
            rest_conn.updateLogicalPartition(partition_dom, timeout)
        except Exception as error:
            error_msg = parse_error_response(error)
            module.fail_json(msg="HmcError: " + error_msg)

        partition_uuid, partition_dom = rest_conn.getLogicalPartition(system_uuid,
                                                                      partition_name=vm_name,
                                                                      partition_uuid=partition_uuid)
        if proc or proc_unit:
            newProcValue = rest_conn.getProcs(isDedicated, partition_dom)
            if not isDedicated:
                newProcUnitValue = rest_conn.getProcUnits(partition_dom)

        if mem:
            newMem = rest_conn.getMem(partition_dom)

        if sharing_mode:
            newSharingMode = rest_conn.getProcSharingMode(partition_dom)

        if uncapped_weight:
            newUncappedWeight = rest_conn.getProcUncappedWeight(partition_dom)

        if pool_id:
            newPoolID = rest_conn.getProcPool(partition_dom)

        logger.debug("difference: %s", difference)
        logger.debug("newProcValue: %s", newProcValue)
        logger.debug("newProcUnitValue: %s", newProcUnitValue)
        logger.debug("newMem: %s", newMem)
        logger.debug("newSharingMode: %s", newSharingMode)
        logger.debug("newPoolID: %s", newPoolID)
    if difference and \
        (newProcValue != prevProcValue or
         newProcUnitValue != prevProcUnitValue or
         newMem != prevMem or
         newSharingMode != prevSharingMode or
         newUncappedWeight != prevUncappedWeight or
         newPoolID != prevPoolID):
        changed = True

    vm_facts = fetch_facts(rest_conn, partition_dom)

    return changed, vm_facts, None


def update_lpar(module, params):
    if any(params['proc_settings'].values()) or any(params['mem_settings'].values()):
        return update_proc_mem(module, params)
    else:
        return False, None, "No valid input configuration"


def perform_task(module):

    params = module.params
    actions = {
        "update": update_lpar,
    }

    try:
        return actions[params['action']](module, params)
    except Exception as error:
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
                          password=dict(type='str', no_log=True),
                      )
                      ),
        system_name=dict(type='str'),
        vm_name=dict(type='str'),
        timeout=dict(type='int'),
        proc_settings=dict(type='dict',
                           options=dict(
                               proc=dict(type='int'),
                               proc_unit=dict(type='float'),
                               sharing_mode=dict(type='str', choices=['keep_idle_procs',
                                                                      'share_idle_procs',
                                                                      'share_idle_procs_active',
                                                                      'share_idle_procs_always',
                                                                      'capped', 'uncapped']),
                               uncapped_weight=dict(type='int'),
                               pool_id=dict(type='int')
                           )
                           ),
        mem_settings=dict(type='dict',
                          options=dict(
                              mem=dict(type='int'),
                          )
                          ),
        action=dict(type='str', choices=['update'], required=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
    )

    if module._verbosity >= 1:
        init_logger()

    if sys.version_info < (3, 0):
        py_ver = sys.version_info[0]
        module.fail_json("Unsupported Python version {0}, supported python version is 3 and above".format(py_ver))

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
