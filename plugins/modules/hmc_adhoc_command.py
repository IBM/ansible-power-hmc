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
module: hmc_adhoc_command
author:
    - Navinakumar Kandakur (@nkandak1)
short_description: run an adhoc command on HMC
description:
    - "running HMC command"
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
    cmd:
        description:
            - The command to be executed on HMC.
        required: true
        type: str
    action:
        description:
            - C(run) Runs command on HMC.
        type: str
        choices: ['run']
'''

EXAMPLES = '''
- name: validate specified vm_namemigration
  powervm_lpar_migration:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    cmd: <cmd>
    action: run
'''

RETURN = '''
Command_output:
    description: Respective command output
    type: str
    returned: always
'''

import logging
LOG_FILENAME = "/tmp/ansible_power_hmc.log"
logger = logging.getLogger(__name__)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError


def init_logger():
    logging.basicConfig(
        filename=LOG_FILENAME,
        format='[%(asctime)s] %(levelname)s: [%(funcName)s] %(message)s',
        level=logging.DEBUG)


def run_hmc_adhoc_command(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    cmd = params['cmd']
    changed = False
    result = None

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)

    try:
        result = hmc_conn.execute(cmd)
        output = (result.strip('\n')).split('\n')
        changed = True
    except (HmcError, Exception) as error:
        error_msg = repr(error)
        module.fail_json(msg=error_msg)

    logger.debug(changed)
    return changed, output, None


def perform_task(module):

    params = module.params
    actions = {
        "run": run_hmc_adhoc_command,
    }
    oper = 'action'
    if params['action'] is None:
        oper = 'state'
    try:
        return actions[params[oper]](module, params)
    except (HmcError) as error:
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
        cmd=dict(type='str', required=True),
        action=dict(type='str', choices=['run']),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_if=[['action', 'run', ['hmc_host', 'hmc_auth', 'cmd']],
                     ],
    )

    if module._verbosity >= 5:
        init_logger()

    changed, info, warning = perform_task(module)

    result = {}
    result['changed'] = changed
    if info:
        result['command_output'] = info

    if warning:
        result['warning'] = warning

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
