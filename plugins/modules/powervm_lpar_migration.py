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
module: powervm_lpar_migration
author:
    - Anil Vijayan (@AnilVijayan)
    - Navinakumar Kandakur (@nkandak1)
short_description: validate, migrate, recover, of the LPAR
description:
    - "validate specified LPAR for migration"
    - "migrate specified LPAR"
    - "recover specified LPAR"
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
    src_system:
        description:
            - The name of the source managed system.
        required: true
        type: str
    dest_system:
        description:
            - The name of the destination managed system.
        required: true
        type: str
    vm_name:
        description:
            - Name of the partition to be migrated/validated/recovered.
        type: str
    vm_ip:
        description:
            - IP Address of the partition to be  migrated/validated/recovered.
        type: str
    vm_id:
        description:
            - ID of the partition to be  migrated/validated/recovered.
        type: str
    all_vm:
        description:
            - All the partitions of the I(src_system) to be migrated/validated/recovered.
        type: str
    action:
        description:
            - C(validate) validate a specified partition.
            - C(migrate) migrate a specified partition from I(src_system) to I(dest_system).
            - C(recover) recover a specified partition .
        type: str
        choices: ['validate', 'migrate', 'recover']
'''

EXAMPLES = '''
- name: validate specified vm_name migration
  powervm_lpar_migration:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    src_system: <managed_system_name>
    dest_system: <destination_managed_system>
    vm_name: <lpar_name>
    action: validate

- name: migrate specified vm_ip from cec1 to cec2
  powervm_lpar_migration:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    src_system: <managed_system_name>
    dest_system: <destination_managed_system>
    vm_ip: <IP address of the lpar>
    action: migrate

- name: recover specifed vm_id
  powervm_lpar_migration:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    src_system: <managed_system_name>
    dest_system: <destination_system>
    vm_id: <id of the vm to be recovered>
    action: recover

- name: migrate all partitions of the cec
  hmc_managed_system:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    src_system: <managed_system_name>
    dest_system: <destination_system_name>
    all_vm: true
    action: migrate

'''

RETURN = '''
system_info:
    description: Respective partition migration information
    type: dict
    returned: always
'''

import logging
LOG_FILENAME = "/tmp/ansible_power_hmc_navin.log"
logger = logging.getLogger(__name__)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_resource import Hmc
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError


def init_logger():
    logging.basicConfig(
        filename=LOG_FILENAME,
        format='[%(asctime)s] %(levelname)s: [%(funcName)s] %(message)s',
        level=logging.DEBUG)


def logical_partition_migration(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    src_system = params['src_system']
    dest_system = params['dest_system']
    vm_name = params['vm_name']
    vm_ip = params['vm_ip']
    vm_id = params['vm_id']
    all_vm = params['all_vm']
    operation = params['action']
    changed = False

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    try:
        if vm_name:
            logger.debug("******************************")
            hmc.migratePartitions(operation[0], src_system, dest_system, lparName=vm_name, lparIP=None, lparID=None, aLL=False)
        elif vm_ip:
            hmc.migratePartitions(operation[0], src_system, dest_system, lparName=None, lparIP=vm_ip, lparID=None, aLL=False)
        elif vm_id:
            hmc.migratePartitions(operation[0], src_system, dest_system, lparName=None, lparIP=None, lparID=vm_id, aLL=False)
        elif all_vm:
            hmc.migratePartitions(operation[0], src_system, dest_system, lparName=None, lparIP=None, lparID=None, aLL=True)
        else:
            module.fail_json(msg="Please provide one of the lpar details vm_name, vm_ip, vm_id, all_vm")
        changed = True
        logger.debug("*************************")
    except HmcError as on_system_error:
        return changed, repr(on_system_error), None

    return changed, None, None


def perform_task(module):

    params = module.params
    actions = {
        "migrate": logical_partition_migration,
        "validate": logical_partition_migration,
        "recover": logical_partition_migration,
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
        src_system=dict(type='str', required=True),
        dest_system=dict(type='str', required=True),
        vm_name=dict(type='str'),
        vm_ip=dict(type='str'),
        vm_id=dict(type='int'),
        all_vm=dict(type='boolean'),
        action=dict(type='str', choices=['validate', 'migrate', 'recover']),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_one_of=[('vm_name', 'vm_ip', 'vm_id', 'all_vm')],
        mutually_exclusive=[('vm_name', 'vm_ip', 'vm_id', 'all_vm')],
        required_if=[['action', 'validate', ['hmc_host', 'hmc_auth', 'src_system', 'dest_system']],
                     ['action', 'migrate', ['hmc_host', 'hmc_auth', 'src_system', 'dest_system']],
                     ['action', 'recover', ['hmc_host', 'hmc_auth', 'src_system', 'dest_system']]
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
