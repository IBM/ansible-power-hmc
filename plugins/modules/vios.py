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
module: vios
author:
    - Anil Vijayan (@AnilVijayan)
    - Navinakumar Kandakur (@nkandak1)
short_description: Creation and management of VirtualIOServer partition
description:
    - "Creates VIOS partition"
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
    name:
        description:
            - The name of the VirtualIOServer
        required: true
        type: str
    settings:
        description:
            - To configure various supported attributes of VIOS partition
            - Supports all the attributes available for creation of VIOS
              on the mksyscfg command
        type: dict
    state:
        description:
            - C(facts) fetch details of specified I(virtualioserver)
        type: str
        choices: ['facts', 'present']
'''

EXAMPLES = '''
- name: create VIOS with default configuration
  vios:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    system_name: <managed_system_name>
    name: <vios_partition_name>
    state: present

'''

RETURN = '''
vios_info:
    description: Respective VIOS information
    type: dict
'''

import logging
LOG_FILENAME = "/tmp/ansible_power_hmc.log"
logger = logging.getLogger(__name__)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_resource import Hmc
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError


def init_logger():
    logging.basicConfig(
        filename=LOG_FILENAME,
        format='[%(asctime)s] %(levelname)s: [%(funcName)s] %(message)s',
        level=logging.DEBUG)


def fetchViosInfo(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    name = params['name']
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    lpar_config = hmc.getPartitionConfig(system_name, name)
    if lpar_config:
        return False, lpar_config, None
    else:
        return False, None, None


# Collection of attributes not supported by vios partition
not_support_settings = ['lpar_env', 'os400_restricted_io_mode', 'console_slot', 'alt_restart_device_slot',
                        'alt_console_slot', 'op_console_slot', 'load_source_slot', 'hsl_pool_id',
                        'virtual_opti_pool_id', 'vnic_adapters', 'electronic_err_reporting', 'suspend_capable',
                        'simplified_remote_restart_capable', 'remote_restart_capable', 'migration_disabled',
                        'virtual_serial_num', 'min_num_huge_pages', 'desired_num_huge_pages', 'max_num_huge_pages',
                        'name', 'lpar_name', 'rs_device_name', 'powervm_mgmt_capable', 'primary_paging_vios_name',
                        'primary_paging_vios_id', 'secondary_paging_vios_name', 'secondary_paging_vios_id',
                        'primary_rs_vios_name', 'primary_rs_vios_id', 'secondary_rs_vios_name', 'secondary_rs_vios_id']


def validate_settings_param(settings):
    if settings:
        anyPresent = [each for each in settings if each in not_support_settings]
        if anyPresent:
            raise ParameterError("Invalid parameters: %s" % (', '.join(anyPresent)))


def createVios(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    name = params['name']
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    prof_name = None

    validate_settings_param(params['settings'])

    try:
        lpar_config = hmc.getPartitionConfig(system_name, name)
        if lpar_config:
            logger.debug(lpar_config)
            return False, lpar_config, None
    except HmcError as list_error:
        if 'HSCL8012' not in repr(list_error):
            raise

    try:
        hmc.createVirtualIOServer(system_name, name, params['settings'])

        if params.get('settings'):
            # Settings default_profile name to 'default' in case user didnt provide
            prof_name = params.get('settings').get('profile_name', 'default')

        lpar_config = hmc.getPartitionConfig(system_name, name, prof_name)
    except HmcError as vios_error:
        return False, repr(vios_error), None

    return True, lpar_config, None


def perform_task(module):
    params = module.params
    actions = {
        "facts": fetchViosInfo,
        "present": createVios
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
        name=dict(type='str', required=True),
        settings=dict(type='dict'),
        state=dict(type='str', choices=['facts', 'present']),
        action=dict(type='str', choices=['install']),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=[('state', 'action')],
        required_one_of=[('state', 'action')],
        required_if=[['state', 'facts', ['hmc_host', 'hmc_auth', 'system_name', 'name']],
                     ['state', 'present', ['hmc_host', 'hmc_auth', 'system_name', 'name']],
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
        result['vios_info'] = info

    if warning:
        result['warning'] = warning

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
