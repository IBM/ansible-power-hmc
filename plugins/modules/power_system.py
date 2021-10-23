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
module: power_system
author:
    - Anil Vijayan (@AnilVijayan)
    - Navinakumar Kandakur (@nkandak1)
short_description: PowerOn, PowerOff, modify_syscfg, modify_hwres, facts of the Managed system
description:
    - "Poweron specified managed system"
    - "Poweroff specified managed system"
    - "Modify System configuration of the specified managed system with specified configuration details"
    - "Modify hardware resource of the specified managed system with specified hardware resource details"
    - "Get the facts of the specified managed system"
version_added: 1.0.0
options:
    hmc_host:
        description:
            - The IPaddress or hostname of the HMC.
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
    new_name:
        description:
            - The new name to be configured on specified I(system_name).
            - This option works with C(modify_syscfg) I(action).
        type: str
    power_off_policy:
        description:
            - power off policy to be configured on specified I(system_name).
            - This option works with C(modify_syscfg) I(action).
            - Configuring this option to '1' will power off the Managed System after all partitions are shutdown.
        type: int
        choices: [1, 0]
    power_on_lpar_start_policy:
        description:
            - power on partition start policy to be configured on specified I(system_name) for the next system restart.
            - This option works with C(modify_syscfg) I(action).
        type: str
        choices: ['autostart', 'userinit', 'autorecovery']
    requested_num_sys_huge_pages:
        description:
            - Configures the number of pages of huge page memory.
            - User can change this value only when the managed system is powered off.
            - This option works with C(modify_hwres) I(action).
        type: int
    mem_mirroring_mode:
        description:
            - Configures the memory mirroring mode on specified I(system_name) for the next system poweron or system restart.
            - User can use this option on only managed systems which supports memory mirroring.
            - This option works with C(modify_hwres) I(action).
        type: str
        choices: ['none', 'sys_firmware_only']
    pend_mem_region_size:
        description:
            - Configures the memory region size setting on specified I(system_name).
            - choices are in MB.
            - This option works with C(modify_hwres) I(action).
        type: str
        choices: ['auto', '16', '32', '64', '128', '256']
    action:
        description:
            - C(poweroff) poweroff a specified I(system_name).
            - C(poweron) poweron a specified I(system_name).
            - C(modify_syscfg) Makes system configurations of specified I(system_name).
            - C(modify_hwres) Makes hardware resource configurations of specified I(system_name).
        type: str
        choices: ['poweron', 'poweroff', 'modify_syscfg', 'modify_hwres']
    state:
        description:
            - C(facts) fetch details of specified I(system_name)
        type: str
        choices: ['facts']
'''

EXAMPLES = '''
- name: poweroff managed system
  hmc_managed_system:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    system_name: <managed_system_name>
    action: poweroff

- name: poweron managed system
  hmc_managed_system:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    system_name: <managed_sysystem_name>
    action: poweron

- name: modify managed system name, powerOn lpar start policy and powerOff policy
  hmc_managed_system:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    system_name: <managed_system_name>
    new_name: <system_name_to_be_changed>
    power_off_policy: '1'
    power_on_lpar_start_policy: autostart
    action: modify_syscfg

- name: modify managed system memory settings
  hmc_managed_system:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    system_name: <managed_system_name>
    requested_num_sys_huge_pages: <sys_huge_pages_to_be_set>
    mem_mirroring_mode: sys_firmware_only
    pend_mem_region_size: auto
    action: modify_hwres

- name: fetch the managed system details
  hmc_managed_system:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    system_name: <managed_system_name>
    state: facts

'''

RETURN = '''
system_info:
    description: Respective System information
    type: dict
    returned: always
'''

import logging
LOG_FILENAME = "/tmp/ansible_power_hmc.log"
logger = logging.getLogger(__name__)
import sys
import json
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_resource import Hmc
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import parse_error_response
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import HmcRestClient
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError


def init_logger():
    logging.basicConfig(
        filename=LOG_FILENAME,
        format='[%(asctime)s] %(levelname)s: [%(funcName)s] %(message)s',
        level=logging.DEBUG)


def build_dict(params):
    config_dict = {}
    for key, value in params.items():
        if key in ['action', 'hmc_host', 'hmc_auth', 'system_name']:
            continue
        if value is None:
            continue
        elif isinstance(value, int):
            config_dict[key] = str(value)
        else:
            config_dict[key] = value
    return config_dict


def validate_parameters(params):
    '''Check that the input parameters satisfy the mutual exclusiveness of HMC'''
    opr = None
    if params['state'] is not None:
        opr = params['state']
    else:
        opr = params['action']

    if opr == 'modify_syscfg':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name']
        unsupportedList = ['requested_num_sys_huge_pages', 'mem_mirroring_mode', 'pend_mem_region_size']
    elif opr == 'modify_hwres':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name']
        unsupportedList = ['new_name', 'power_off_policy', 'power_on_lpar_start_policy']
    else:
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name']
        unsupportedList = ['new_name', 'power_off_policy', 'power_on_lpar_start_policy', 'requested_num_sys_huge_pages',
                           'mem_mirroring_mode', 'pend_mem_region_size']

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


def powerOnManagedSys(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    changed = False
    validate_parameters(params)
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    try:
        res = hmc.getManagedSystemDetails(system_name)
        system_state = res.get('state')
        if system_state != 'Power Off':
            changed = False
        else:
            hmc.managedSystemPowerON(system_name)
            if hmc.checkManagedSysState(system_name, ['Operating', 'Standby']):
                changed = True
            else:
                changed = False

    except HmcError as on_system_error:
        return False, repr(on_system_error), None

    return changed, None, None


def powerOffManagedSys(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    changed = False
    validate_parameters(params)
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    try:
        res = hmc.getManagedSystemDetails(system_name)
        system_state = res.get('state')
        if system_state == 'Power Off':
            changed = False
        else:
            hmc.managedSystemShutdown(system_name)
            if hmc.checkManagedSysState(system_name, ['Power Off']):
                changed = True
            else:
                changed = False
    except HmcError as on_system_error:
        return False, repr(on_system_error), None

    return changed, None, None


def modifySystemConfiguration(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    changed = False
    validate_parameters(params)
    sett_dict = build_dict(params)
    if not sett_dict:
        module.fail_json(msg="Atleast one of the System change configuration should to be provided")

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    try:
        attr_dict = hmc.getManagedSystemDetails(system_name)
        attr_dict['new_name'] = attr_dict.pop('name')
        if not sett_dict.items() <= attr_dict.items():
            hmc.confSysGenSettings(system_name, sett_dict)
            changed = True
    except HmcError as on_system_error:
        return changed, repr(on_system_error), None

    return changed, None, None


def modifySystemHardwareResources(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    changed = False
    validate_parameters(params)
    sett_dict = build_dict(params)
    if not sett_dict:
        module.fail_json(msg="Atleast one of the System Hardware Resources should to be provided")

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    try:
        attr_dict = hmc.getManagedSystemHwres(system_name, 'mem', 'sys')
        if 'curr_mem_mirroring_mode' in attr_dict.keys():
            attr_dict['mem_mirroring_mode'] = attr_dict.pop('curr_mem_mirroring_mode')
        attr_dict['pend_mem_region_size'] = attr_dict.pop('mem_region_size')
        if not sett_dict.items() <= attr_dict.items():
            hmc.confSysMem(system_name, sett_dict, 's')
            changed = True
    except HmcError as on_system_error:
        return changed, repr(on_system_error), None

    return changed, None, None


def fetchManagedSysDetails(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    system_prop = None
    system_uuid = None
    changed = False
    validate_parameters(params)
    try:
        rest_conn = HmcRestClient(hmc_host, hmc_user, password)
    except Exception as error:
        error_msg = parse_error_response(error)
        module.fail_json(msg=error_msg)

    try:
        system_uuid, server_dom = rest_conn.getManagedSystem(system_name)
        if not system_uuid:
            module.fail_json(msg="Given system is not present")
        else:
            sys_resp = rest_conn.getManagedSystemQuick(system_uuid)
            system_prop = json.loads(sys_resp)
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

    return changed, system_prop, None


def perform_task(module):

    params = module.params
    actions = {
        "poweron": powerOnManagedSys,
        "poweroff": powerOffManagedSys,
        "facts": fetchManagedSysDetails,
        "modify_syscfg": modifySystemConfiguration,
        "modify_hwres": modifySystemHardwareResources
    }
    oper = 'action'
    if params['action'] is None:
        oper = 'state'
    try:
        return actions[params[oper]](module, params)
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
        system_name=dict(type='str', required=True),
        new_name=dict(type='str'),
        power_off_policy=dict(type='int', choices=[1, 0]),
        power_on_lpar_start_policy=dict(type='str', choices=['autostart', 'userinit', 'autorecovery']),
        requested_num_sys_huge_pages=dict(type='int'),
        mem_mirroring_mode=dict(type='str', choices=['none', 'sys_firmware_only']),
        pend_mem_region_size=dict(type='str', choices=['auto', '16', '32', '64', '128', '256']),
        action=dict(type='str', choices=['poweron', 'poweroff', 'modify_syscfg', 'modify_hwres']),
        state=dict(type='str', choices=['facts']),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=[('state', 'action')],
        required_one_of=[('state', 'action')],
        required_if=[['state', 'facts', ['hmc_host', 'hmc_auth', 'system_name']],
                     ['action', 'poweron', ['hmc_host', 'hmc_auth', 'system_name']],
                     ['action', 'poweroff', ['hmc_host', 'hmc_auth', 'system_name']],
                     ['action', 'modify_syscfg', ['hmc_host', 'hmc_auth', 'system_name']],
                     ['action', 'modify_hwres', ['hmc_host', 'hmc_auth', 'system_name']]
                     ],
    )

    if module._verbosity >= 5:
        init_logger()

    changed, info, warning = perform_task(module)

    if isinstance(info, str):
        module.fail_json(msg=info)

    result = {}
    result['changed'] = changed
    if info:
        result['system_info'] = info

    if warning:
        result['warning'] = warning

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
