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
module: hmc_managed_system
author:
    - Anil Vijayan (@AnilVijayan)
    - Navinakumar Kandakur (@nkandak1)
short_description: PowerOn, PowerOff a Managed system
description:
    - "Poweron specified managed system"
    - "Poweroff specified managed system"
version_added: 1.0.0
options:
    hmc_host:
        description:
            - The ipaddress or hostname of HMC.
        required: true
        type: str
    hmc_auth:
        description:
            - Username and Password credential of HMC.
        required: true
        type: dict
        suboptions:
            username:
                description:
                    - Username of HMC to login.
                required: true
                type: str
            password:
                description:
                    - Password of HMC.
                type: str
    system_name:
        description:
            - The name of the managed system.
        required: true
        type: str
    action:
        description:
            - C(poweroff) poweroff a specified I(system_name)
            - C(poweron) poweron a specified I(system_name)
        type: str
        choices: ['poweron', 'poweroff']
    state:
        description:
            - C(facts) fetches destails of specified I(system_name)
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
    system_name: sys_name
    action: poweroff

- name: poweron managed system
  hmc_managed_system:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    system_name: sys_name
    action: poweron

'''

RETURN = '''
system_info:
    description: Respective policy information
    type: dict
    returned: always
'''

import logging
LOG_FILENAME = "/tmp/ansible_power_hmc_navin.log"
logger = logging.getLogger(__name__)
import sys
import json
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_resource import Hmc
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import parse_error_response
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import HmcRestClient


def init_logger():
    logging.basicConfig(
        filename=LOG_FILENAME,
        format='[%(asctime)s] %(levelname)s: [%(funcName)s] %(message)s',
        level=logging.DEBUG)


def powerOnManagedSys(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    try:
        system_state = hmc.getManagedSystemDetails(system_name, 'state')
        if system_state != 'Power Off':
            return False, None, None
        else:
            hmc.managedSystemPowerON(system_name)
    except HmcError as on_system_error:
        return False, repr(on_system_error), None

    return True, None, None


def powerOffManagedSys(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    try:
        system_state = hmc.getManagedSystemDetails(system_name, 'state')
        if system_state == 'Power Off':
            return False, None, None
        else:
            hmc.managedSystemShutdown(system_name)
    except HmcError as on_system_error:
        return False, repr(on_system_error), None

    return True, None, None


def fetchManagedSysDetails(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    system_prop = None
    system_uuid = None
    changed = False

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

    return changed, system_prop, None


def perform_task(module):

    params = module.params
    actions = {
        "poweron": powerOnManagedSys,
        "poweroff": powerOffManagedSys,
        "facts": fetchManagedSysDetails,
    }
    oper = 'action'
    if params['action'] is None:
        oper = 'state'
    try:
        return actions[params[oper]](module, params)
    except Exception as error:
        return False, str(error), None


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
        action=dict(type='str', choices=['poweron', 'poweroff']),
        state=dict(type='str', choices=['facts']),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_one_of=[('state', 'action')],
        required_if=[['state', 'facts', ['hmc_host', 'hmc_auth', 'system_name']],
                     ['action', 'poweron', ['hmc_host', 'hmc_auth', 'system_name']],
                     ['action', 'poweroff', ['hmc_host', 'hmc_auth', 'system_name']],
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
