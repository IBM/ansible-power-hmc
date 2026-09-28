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
short_description: Validate, migrate, and recover LPARs
notes:
    - All the actions support passwordless authentication.
description:
    - "Validate provided LPAR/s for migration"
    - "Migrate provided LPAR/s"
    - "Recover provided LPAR"
    - "Authenticate HMC"
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
        type: str
    dest_system:
        description:
            - The name of the destination managed system.
            - Valid only for C(validate) and C(migrate) I(action) operation.
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
            - Valid only for C(migrate) I(action).
        type: bool
    remote_ip:
        description:
            - If the destination managed system is not managed by the same management console
              that is managing the source managed system, then use this option to specify the IP address
              or host name of the management console that is managing the destination managed system.
              This option is mandatory for C(authenticate) I(action) and optional for other I(action)
        type: str
    remote_username:
        description:
            - Username of the remote HMC
            - This option can be used only with C(authenticate) I(action)
        type: str
    remote_passwd:
        description:
            - Password of the remote HMC
            - This option can be used only with C(authenticate) I(action)
        type: str
    wait:
        description:
            - The maximum time, in minutes, to wait for operation to complete.
            - This option can be used only with C(migrate) and C(validate) I(action).
        type: int
    shared_proc_pool:
        description:
            - List of the details of the shared processor pools to use on the destination managed system.
            - This parameter supports single and multiple pools.
            - This option can be used only with C(migrate).
        type: list
        elements: dict
        suboptions:
            lpar_name:
                description:
                    - Name of the partition to be migrated.
                    - lpar_name and lpar_id are mutually exclusive.
                    - Use lpar_name only when I(vm_names) is specified at the top level.
                    - When using lpar_name, you must use pool_name (pool_id is not supported).
                type: str
            lpar_id:
                description:
                    - Id of the partition to be migrated.
                    - lpar_name and lpar_id are mutually exclusive.
                    - Use lpar_id only when I(vm_ids) is specified at the top level.
                    - When using lpar_id, you must use pool_id (pool_name is not supported).
                type: int
            pool_id:
                description:
                    - IDs of the shared processor pools to use on the destination managed.
                    - pool_id and pool_name are mutually exclusive.
                    - Use pool_id only when I(vm_ids) is specified at the top level.
                    - Required when using lpar_id.
                type: int
            pool_name:
                description:
                    - Names of the shared processor pools to use on the destination managed.
                    - pool_id and pool_name are mutually exclusive.
                    - Use pool_name only when I(vm_names) is specified at the top level.
                    - Required when using lpar_name.
                type: str
    action:
        description:
            - C(validate) validate a specified partition/s.
            - C(migrate) migrate a specified partition/s from I(src_system) to I(dest_system).
            - C(recover) recover a specified partition.
            - C(authenticate) adds SSH authentication key of remote management console.
        type: str
        required: true
        choices: ['validate', 'migrate', 'recover', 'authenticate']
'''

EXAMPLES = '''
- name: Validate that the input partitions can be migrated to the destination
  ibm.power_hmc.powervm_lpar_migration:
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

- name: Recover specified vm_id from migration failure
  ibm.power_hmc.powervm_lpar_migration:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    src_system: <managed_system_name>
    vm_ids:
      - <id1>
    action: recover

- name: Migrate all partitions of the cec to remote HMC
  ibm.power_hmc.powervm_lpar_migration:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    src_system: <managed_system_name>
    dest_system: <destination_system_name>
    remote_ip: <ipaddress of the remote HMC>
    all_vms: true
    action: migrate

- name: Migrate 2 partitions of the cec to another
  ibm.power_hmc.powervm_lpar_migration:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    src_system: <managed_system_name>
    dest_system: <destination_system_name>
    vm_ids:
      - <id1>
      - <id2>
    shared_proc_pool:
      - lpar_id: <id1>
        pool_id: <poolid1>
      - lpar_id: <id2>
        pool_id: <poolid2>
    action: migrate

- name: Adds SSH authentication key of remote HMC.
  ibm.power_hmc.powervm_lpar_migration:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    remote_ip: <IP Address of the remote HMC>
    remote_username: <Username of the remote HMC>
    remote_passwd: <Password of the remote HMC>
    action: authenticate
'''

RETURN = '''
system_info:
    description: Respective partition migration information
    type: dict
    returned: always
'''

import logging
import os
LOG_FILENAME = "/tmp/ansible_power_hmc_{0}.log".format(os.getpid())
logger = logging.getLogger(__name__)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_resource import Hmc
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import parse_error_response
import sys


def init_logger():
    old_umask = os.umask(0o177)
    try:
        logging.basicConfig(
            filename=LOG_FILENAME,
            format='[%(asctime)s] %(levelname)s: [%(funcName)s] %(message)s',
            level=logging.DEBUG)
    finally:
        os.umask(old_umask)


def validate_parameters(params):
    '''Check that the input parameters satisfy the mutual exclusiveness of HMC'''
    opr = params['action']
    unsupportedList = []

    if opr == 'recover':
        mandatoryList = ['hmc_host', 'hmc_auth', 'src_system']
        unsupportedList = ['dest_system', 'all_vms', 'wait', 'remote_ip', 'shared_proc_pool']
    elif opr == 'validate':
        mandatoryList = ['hmc_host', 'hmc_auth', 'src_system', 'dest_system']
        unsupportedList = ['all_vms', 'shared_proc_pool']
    elif opr == 'authenticate':
        mandatoryList = ['hmc_host', 'hmc_auth', 'remote_ip', 'remote_username', 'remote_passwd']
        unsupportedList = ['all_vms', 'src_system', 'dest_system', 'vm_names', 'vm_ids', 'wait', 'shared_proc_pool']
    elif opr == 'migrate':
        mandatoryList = ['hmc_host', 'hmc_auth', 'src_system', 'dest_system']
        unsupportedList = []

    if params['action'] == 'migrate':
        if params['vm_ids'] is not None and params['vm_names'] is not None:
            raise ParameterError("vm_names and vm_ids are mutually exclusive")
        if params['shared_proc_pool'] is not None:
            unsupportedList += ['all_vms']
            for item in params['shared_proc_pool']:
                if params['vm_names'] is not None:
                    if len(params['shared_proc_pool']) != len(params['vm_names']):
                        raise ParameterError("Specify the pool details for each VMs provided")
                    if item['pool_id'] is not None or item['lpar_id'] is not None:
                        raise ParameterError("pool_id or lpar_id are not supported for migration with partition name.")
                    if item['pool_name'] is None or item['lpar_name'] is None:
                        raise ParameterError("pool_name and lpar_name are mandatory for migration with partition name.")
                elif params['vm_ids'] is not None:
                    if len(params['shared_proc_pool']) != len(params['vm_ids']):
                        raise ParameterError("Specify the pool details for each VMs provided")
                    if item['pool_name'] is not None or item['lpar_name'] is not None:
                        raise ParameterError("pool_name or lpar_name are not supported for migration with partition id.")
                    if item['pool_id'] is None or item['lpar_id'] is None:
                        raise ParameterError("pool_id and lpar_id are mandatory for migration with partition id.")

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
    remote_ip = params['remote_ip']
    wait = params['wait']
    shared_pool = params['shared_proc_pool']
    operation = params['action']
    validate_parameters(params)
    changed = False

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    shared_pool_details = ""
    if shared_pool is not None:
        if len(shared_pool) == 1:
            for item in shared_pool:
                if item['pool_name'] is not None:
                    shared_pool_details += item['pool_name']
                elif item['pool_id'] is not None:
                    shared_pool_details += str(item['pool_id'])
        else:
            for item in shared_pool:
                if item['lpar_name'] is not None:
                    shared_pool_details += item['lpar_name'] + "//" + str(item['pool_name'])
                elif item['lpar_id'] is not None:
                    shared_pool_details += "/" + str(item['lpar_id']) + "/" + str(item['pool_id'])
                shared_pool_details += ","
            shared_pool_details = shared_pool_details[:-1]

    try:
        if vm_names:
            if operation == 'recover' and len(vm_names) > 1:
                module.fail_json(msg="Please provide only one partition name for recover operation")
            hmc.migratePartitions(operation[0], src_system, dest_system, lparNames=",".join(vm_names), lparIDs=None, aLL=False, ip=remote_ip,
                                  wait=wait, pool=shared_pool_details)
        elif vm_ids:
            if operation == 'recover' and len(vm_ids) > 1:
                module.fail_json(msg="Please provide only one partition id for recover operation")
            hmc.migratePartitions(operation[0], src_system, dest_system, lparNames=None, lparIDs=",".join(vm_ids), aLL=False, ip=remote_ip,
                                  wait=wait, pool=shared_pool_details)
        elif all_vms:
            hmc.migratePartitions(operation[0], src_system, dest_system, lparNames=None, lparIDs=None, aLL=True, ip=remote_ip, wait=wait, pool=None)
        else:
            module.fail_json(msg="Please provide one of the lpar details vm_names, vm_ids, all_vms")
        if operation != 'validate':
            changed = True
    except HmcError as on_system_error:
        return changed, repr(on_system_error), None

    return changed, None, None


def make_hmc_authentication(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    remote_ip = params['remote_ip']
    remote_username = params['remote_username']
    remote_passwd = params['remote_passwd']
    validate_parameters(params)
    changed = False

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    try:
        hmc.authenticateHMCs(remote_ip, test=True)
    except HmcError as auth_err:
        error_msg = parse_error_response(auth_err)
        if 'HSCL3653' in error_msg:
            try:
                hmc.authenticateHMCs(remote_ip, username=remote_username, passwd=remote_passwd, test=False)
                changed = True
            except HmcError as on_system_error:
                return changed, repr(on_system_error), None
        else:
            return changed, error_msg, None
    return changed, None, None


def perform_task(module):

    params = module.params
    actions = {
        "migrate": logical_partition_migration,
        "validate": logical_partition_migration,
        "recover": logical_partition_migration,
        "authenticate": make_hmc_authentication,
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
        src_system=dict(type='str'),
        dest_system=dict(type='str'),
        vm_names=dict(type='list', elements='str'),
        vm_ids=dict(type='list', elements='str'),
        all_vms=dict(type='bool'),
        remote_ip=dict(type='str'),
        remote_username=dict(type='str'),
        remote_passwd=dict(type='str', no_log=True),
        wait=dict(type='int'),
        action=dict(type='str', choices=['validate', 'migrate', 'recover', 'authenticate'], required=True),
        shared_proc_pool=dict(type='list', elements='dict',
                              options=dict(
                                  lpar_name=dict(type='str'),
                                  lpar_id=dict(type='int'),
                                  pool_id=dict(type='int'),
                                  pool_name=dict(type='str'),
                              )
                              )
    )

    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=[('vm_names', 'vm_ids', 'all_vms')],
        required_if=[['action', 'validate', ['hmc_host', 'hmc_auth', 'src_system', 'dest_system']],
                     ['action', 'migrate', ['hmc_host', 'hmc_auth', 'src_system', 'dest_system']],
                     ['action', 'recover', ['hmc_host', 'hmc_auth', 'src_system']],
                     ['action', 'authenticate', ['hmc_host', 'hmc_auth', 'remote_ip', 'remote_username', 'remote_passwd']]
                     ],
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
        result['system_info'] = info

    if warning:
        result['warning'] = warning

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
