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
    - Navinakumar Kandakur (@nkandak1)
short_description: validate, migrate and recover of the LPAR
description:
    - "Validate provided LPAR/s for migration"
    - "Migrate provided LPAR/s"
    - "Recover provided LPAR"
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
    src_system:
        description:
            - The name of the source managed system.
        required: true
        type: str
    dest_system:
        description:
            - The name of the destination managed system.
            - valid only for C(validate) and C(migrate) I(action) operation.
        type: str
    vm_names:
        description:
            - Name of the partition/s to be migrated/validated.
            - To perform action on multiple partitions, provide comma separated partition names or in list form.
            - For C(recover) I(action) only one partition name is allowed.
        type: list
        elements: str
    vm_ids:
        description:
            - ID/s of the partition to be migrated/validated.
            - To perform action on multiple partitions, provide comma separated partition ids or in list form.
            - For C(recover) I(action) only one partition id is allowed.
        type: list
        elements: str
    all_vms:
        description:
            - All the partitions of the I(src_system) to be migrated.
            - valid only for C(migrate) I(action)
        type: bool
    action:
        description:
            - C(validate) validate a specified partition/s.
            - C(migrate) migrate a specified partition/s from I(src_system) to I(dest_system).
            - C(recover) recover a specified partition.
        type: str
        choices: ['validate', 'migrate', 'recover']
'''

EXAMPLES = '''
- name: Validate that the input partitions can be migrated to the destination
  powervm_lpar_migration:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    src_system: <managed_system_name>
    dest_system: <destination_managed_system>
    vm_names:
      - <vm_name1>
      - <vm_name2>
    action: validate

- name: Recover specifed vm_id from migration failure
  powervm_lpar_migration:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    src_system: <managed_system_name>
    vm_ids:
      - <id1>
    action: recover

- name: Migrate all partitions of the cec
  hmc_managed_system:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    src_system: <managed_system_name>
    dest_system: <destination_system_name>
    all_vms: true
    action: migrate

'''

RETURN = '''
system_info:
    description: Respective partition migration information
    type: dict
    returned: always
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


def validate_parameters(params):
    '''Check that the input parameters satisfy the mutual exclusiveness of HMC'''
    opr = params['action']

    if opr == 'recover':
        mandatoryList = ['hmc_host', 'hmc_auth', 'src_system']
        unsupportedList = ['dest_system', 'all_vms']
    elif opr == 'validate':
        mandatoryList = ['hmc_host', 'hmc_auth', 'src_system', 'dest_system']
        unsupportedList = ['all_vms']
    else:
        mandatoryList = ['hmc_host', 'hmc_auth', 'src_system', 'dest_system']
        unsupportedList = []

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


def logical_partition_migration(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    src_system = params['src_system']
    dest_system = params['dest_system']
    vm_names = params['vm_names']
    vm_ids = params['vm_ids']
    all_vms = params['all_vms']
    operation = params['action']
    validate_parameters(params)
    changed = False

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    try:
        if vm_names:
            if operation == 'recover' and len(vm_names) > 1:
                module.fail_json(msg="Please provide only one partition name for recover operation")
            hmc.migratePartitions(operation[0], src_system, dest_system, lparNames=",".join(vm_names), lparIDs=None, aLL=False)
        elif vm_ids:
            if operation == 'recover' and len(vm_ids) > 1:
                module.fail_json(msg="Please provide only one partition id for recover operation")
            hmc.migratePartitions(operation[0], src_system, dest_system, lparNames=None, lparIDs=",".join(vm_ids), aLL=False)
        elif all_vms:
            hmc.migratePartitions(operation[0], src_system, dest_system, lparNames=None, lparIDs=None, aLL=True)
        else:
            module.fail_json(msg="Please provide one of the lpar details vm_names, vm_ids, all_vms")
        if operation != 'validate':
            changed = True
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
        src_system=dict(type='str', required=True),
        dest_system=dict(type='str'),
        vm_names=dict(type='list', elements='str'),
        vm_ids=dict(type='list', elements='str'),
        all_vms=dict(type='bool'),
        action=dict(type='str', choices=['validate', 'migrate', 'recover']),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_one_of=[('vm_names', 'vm_ids', 'all_vms')],
        mutually_exclusive=[('vm_names', 'vm_ids', 'all_vms')],
        required_if=[['action', 'validate', ['hmc_host', 'hmc_auth', 'src_system', 'dest_system']],
                     ['action', 'migrate', ['hmc_host', 'hmc_auth', 'src_system', 'dest_system']],
                     ['action', 'recover', ['hmc_host', 'hmc_auth', 'src_system']]
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
