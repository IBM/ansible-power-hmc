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
module: vios_maintenance
author:
    - Sreenidhi S (@SreenidhiS1)
short_description: Manage the vios backup
notes:
    - All Operations support passwordless authentication.
description:
    - Create a VIOS backup file
    - List VIOS backup file details
    - Modify the name of the VIOS backup file
    - Remove a VIOS backup file
    - Restore a VIOS backup
version_added: 1.0.0
options:
    hmc_host:
        description:
            - The IP address or hostname of the HMC.
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
    attributes:
        description:
            - Configuration parameters required for VIOS backup and restore.
        type: dict
        required: true
        suboptions:
            types:
                description:
                    - The type of VIOS backup to create.
                    - Valid values are C(viosioconfig) for a VIOS I/O configuration backup,
                      C(vios) for a full VIOS backup, C(ssp) for a Shared Storage Pool configuration backup.
                type: str
                required: true
                choices: ['vios', 'viosioconfig', 'ssp']
            system:
                description:
                    - The name of the managed system which has the VIOS to backup.
                type: str
            vios_id:
                description:
                    - The ID of the VIOS to backup.
                      vios_id, vios_uuid, vios_name are mutually exclusive.
                type: str
            vios_uuid:
                description:
                    - The UUID of the VIOS to backup.
                      vios_id, vios_uuid, vios_name are mutually exclusive.
                type: str
            vios_name:
                description:
                    - The name of the VIOS to backup.
                      vios_id, vios_uuid, vios_name are mutually exclusive.
                type: str
            backup_name:
                description:
                    - The name of the file where the backup will be saved.
                type: str
            file_list:
                description:
                    - The list of the backup files that needs to be removed.
                      This option is for C(remove) state only.
                      Add backup file name as comma-separated values.
                type: list
                elements: str
            nimol_resource:
                description:
                    - Option to include the NIMOL resources.
                      C(1) to include and C(0) to not include the NIMOL resources.
                      This option is only valid when creating a full VIOS backup.
                type: int
                choices: [1, 0]
            media_repository:
                description:
                    - Option to include the contents of the media repository.
                      C(1) to include and C(0) to not include the media resources.
                      This option is only valid when creating a full VIOS backup.
                type: int
                choices: [1, 0]
            volume_group_structure:
                description:
                    - Option to include the volume groups structure of user.
                      C(1) to include and C(0) to not include the volume groups structure of user.
                      This option is only valid when creating a full VIOS backup.
                type: int
                choices: [1, 0]
            restart:
                description:
                    - Specify this option to restart the VIOS if required.
                      C(True) to restart the VIOS and C(False) not to restart the VIOS.
                      Valid for C(restore) state only.
                type: bool
            new_name:
                description:
                    - The attributes to change the name of the backup file.
                      Valid for C(modify) state only.
                type: str
    state:
        description:
            - C(facts) does not change anything on the HMC and returns list of backup files of a VIOS.
            - C(present) ensures the new backup file is created for the specified VIOS.
            - C(absent) ensures the specified backup file/s is removed from the HMC.
            - C(restore) ensures the backup file is restored.
            - C(modify) ensures that the name of the backup file is changed in HMC.
        type: str
        choices: ['facts', 'present', 'absent', 'restore', 'modify']
'''

EXAMPLES = '''
- name: Create a viosioconfig backup file
  ibm.power_hmc.vios_maintenance:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    attributes:
      vios_name: <vios name>
      backup_name: test
      system: <sys>
      types: viosioconfig
    state: present

- name: Restore a vios from test backup file
  ibm.power_hmc.vios_maintenance:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    attributes:
      vios_name: <vios name>
      backup_name: test.tar.gz
      system: <sys>
      types: viosioconfig
    state: restore

- name: Remove a backup file
  ibm.power_hmc.vios_maintenance:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    attributes:
      vios_name: <vios name>
      backup_name: test.tar.gz
      system: <sys>
      types: viosioconfig
    state: absent

- name: Rename the backup file
  ibm.power_hmc.vios_maintenance:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    attributes:
      vios_name: <vios name>
      backup_name: test.tar.gz
      new_name: new.tar.gz
      system: <sys>
      types: viosioconfig
    state: modify
'''

RETURN = '''
command_output:
    description: Respective user configuration.
    type: dict
    returned: on success of all states except C(absent)
'''

import logging
import os
LOG_FILENAME = "/tmp/ansible_power_hmc_{0}.log".format(os.getpid())
logger = logging.getLogger(__name__)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_resource import Hmc
import sys

USER_AUTHORITY_ERR = "HSCL350B The user does not have the appropriate authority"


def init_logger():
    old_umask = os.umask(0o177)
    try:
        logging.basicConfig(
            filename=LOG_FILENAME,
            format='[%(asctime)s] %(levelname)s: [%(funcName)s] %(message)s',
            level=logging.DEBUG)
    finally:
        os.umask(old_umask)


def validate_sub_params(params):
    opr = None
    unsupportedList = []
    mandatoryList = []
    opr = params['state']

    if opr == 'present':
        params = params['attributes']
        mandatoryList = ['types', 'system', 'backup_name']
        unsupportedList = ['restart', 'new_name']
    if opr == 'restore':
        params = params['attributes']
        mandatoryList = ['types', 'system', 'backup_name']
        unsupportedList = ['nimol_resource', 'media_repository', 'volume_group_structure', 'file_list', 'new_name']
    if opr == 'absent':
        params = params['attributes']
        mandatoryList = ['types', 'system', 'file_list']
        unsupportedList = ['restart', 'nimol_resource', 'media_repository', 'volume_group_structure', 'backup_name', 'new_name']
    if opr == 'modify':
        params = params['attributes']
        mandatoryList = ['types', 'system', 'backup_name', 'new_name']
        unsupportedList = ['restart', 'nimol_resource', 'media_repository', 'volume_group_structure', 'file_list']

    if opr in ['present', 'restore', 'absent', 'modify']:
        count = sum(x is not None for x in [params['vios_id'], params['vios_uuid'], params['vios_name']])
        if count == 0:
            raise ParameterError("Missing VIOS details")
        if count != 1:
            raise ParameterError("Parameters 'vios_id', 'vios_uuid' and 'vios_name' are mutually exclusive")
    if opr == 'present':
        if params['nimol_resource'] is not None or params['media_repository'] is not None or params['volume_group_structure'] is not None:
            if params['types'] != 'vios':
                raise ParameterError("Parameters 'nimol_resource', 'media_repository' and 'volume_group_structure' are valid for only full VIOS backup")
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
            raise ParameterError("unsupported parameters: %s" % (','.join(collate)))


def validate_parameters(params):
    '''Check that the input parameters satisfy the mutual exclusiveness of HMC'''
    opr = None
    unsupportedList = []
    mandatoryList = []

    if params['state'] is not None:
        opr = params['state']
    else:
        opr = params['action']

    if opr in ['present', 'restore']:
        mandatoryList = ['hmc_host', 'hmc_auth', 'attributes']

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
            raise ParameterError("unsupported parameters: %s" % (','.join(collate)))
    validate_sub_params(params)


def facts(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    filter_d = {}
    viosbk_details = []

    validate_parameters(params)
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    try:
        viosbk_details = hmc.listViosbk(filt=filter_d)
    except HmcError as error:
        if USER_AUTHORITY_ERR in repr(error):
            logger.debug(repr(error))
            return False, None, None
        else:
            raise
    return False, viosbk_details, None


def ensure_present(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    filter_d = {}

    validate_parameters(params)
    attributes = params.get('attributes')
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    vios_list = []

    vios_name = attributes['vios_name'] or attributes['vios_id'] or attributes['vios_uuid']
    m_system = attributes['system']
    sys_list = (
        hmc_conn.execute("lssyscfg -r sys -F name").splitlines() + hmc_conn.execute("lssyscfg -r sys -F type_model*serial_num").splitlines()
    )
    if m_system not in sys_list:
        module.fail_json(msg="The managed system is not available in HMC")
    else:
        if attributes['vios_name'] is not None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F name".format(m_system)).splitlines())
        elif attributes['vios_id'] is not None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F lpar_id".format(m_system)).splitlines())
        elif attributes['vios_uuid'] is not None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F uuid".format(m_system)).splitlines())
        if vios_name not in vios_list:
            module.fail_json(msg="The vios is not available in the managed system")
        else:
            if attributes['vios_name'] is not None:
                filter_d = {"VIOS_NAMES": attributes['vios_name'], "SYS_NAMES": attributes['system'], "TYPES": attributes['types']}
            elif attributes['vios_id'] is not None:
                filter_d = {"VIOS_IDS": attributes['vios_id'], "SYS_NAMES": attributes['system'], "TYPES": attributes['types']}
            elif attributes['vios_uuid'] is not None:
                filter_d = {"VIOS_UUIDS": attributes['vios_uuid'], "SYS_NAMES": attributes['system'], "TYPES": attributes['types']}
            vios_list = hmc.listViosbk(filter_d)
            vios_list = [item['NAME'].split('.')[0] for item in vios_list]
            if attributes['backup_name'] in vios_list:
                msg = "The backup file {0} already exists".format(attributes['backup_name'])
                return False, None, msg
            else:
                try:
                    hmc.createViosBk(configDict=attributes)
                    if attributes['vios_name'] is not None:
                        filter_d = {"VIOS_NAMES": attributes['vios_name'], "SYS_NAMES": attributes['system'], "TYPES": attributes['types']}
                    elif attributes['vios_id'] is not None:
                        filter_d = {"VIOS_IDS": attributes['vios_id'], "SYS_NAMES": attributes['system'], "TYPES": attributes['types']}
                    elif attributes['vios_uuid'] is not None:
                        filter_d = {"VIOS_UUIDS": attributes['vios_uuid'], "SYS_NAMES": attributes['system'], "TYPES": attributes['types']}
                    viosbk_info = hmc.listViosbk(filter_d)
                except HmcError as error:
                    if USER_AUTHORITY_ERR in repr(error):
                        logger.debug(repr(error))
                        return False, None, None
                    else:
                        raise
                changed = True
                return changed, viosbk_info, None


def ensure_restore(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    filter_d = {}

    validate_parameters(params)
    attributes = params.get('attributes')
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    vios_list = []

    m_system = attributes['system']
    vios_name = attributes['vios_name'] or attributes['vios_id'] or attributes['vios_uuid']
    if attributes['types'] not in ['viosioconfig', 'ssp']:
        module.fail_json(msg="For restore the type can be either viosioconfig or ssp")
    m_system = attributes['system']
    sys_list = (
        hmc_conn.execute("lssyscfg -r sys -F name").splitlines() + hmc_conn.execute("lssyscfg -r sys -F type_model*serial_num").splitlines()
    )
    if m_system not in sys_list:
        module.fail_json(msg="The managed system is not available in HMC")
    else:
        if attributes['vios_name'] is not None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F name".format(m_system)).splitlines())
        elif attributes['vios_id'] is not None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F lpar_id".format(m_system)).splitlines())
        elif attributes['vios_uuid'] is not None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F uuid".format(m_system)).splitlines())
        if vios_name not in vios_list:
            module.fail_json(msg="The vios is not available in the managed system")
        else:
            if attributes['vios_name'] is not None:
                filter_d = {"VIOS_NAMES": attributes['vios_name'], "SYS_NAMES": attributes['system'], "TYPES": attributes['types']}
            elif attributes['vios_id'] is not None:
                filter_d = {"VIOS_IDS": attributes['vios_id'], "SYS_NAMES": attributes['system'], "TYPES": attributes['types']}
            elif attributes['vios_uuid'] is not None:
                filter_d = {"VIOS_UUIDS": attributes['vios_uuid'], "SYS_NAMES": attributes['system'], "TYPES": attributes['types']}
            vios_list = hmc.listViosbk(filter_d)
            vios_list = [item['NAME'] for item in vios_list]
            if attributes['backup_name'] not in vios_list:
                msg = "The backup file {0} does not exists".format(attributes['backup_name'])
                return False, None, msg
            else:
                try:
                    hmc.restoreViosBk(configDict=attributes)
                except HmcError as error:
                    if USER_AUTHORITY_ERR in repr(error):
                        logger.debug(repr(error))
                        return False, None, None
                    else:
                        raise
                changed = True
                return changed, None, None


def ensure_absent(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    filter_d = {}

    validate_parameters(params)
    attributes = params.get('attributes')
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    vios_name = attributes['vios_name'] or attributes['vios_id'] or attributes['vios_uuid']
    m_system = attributes['system']
    sys_list = (
        hmc_conn.execute("lssyscfg -r sys -F name").splitlines() + hmc_conn.execute("lssyscfg -r sys -F type_model*serial_num").splitlines()
    )
    if m_system not in sys_list:
        module.fail_json(msg="The managed system is not available in HMC")
    else:
        if attributes['vios_name'] is not None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F name".format(m_system)).splitlines())
        elif attributes['vios_id'] is not None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F lpar_id".format(m_system)).splitlines())
        elif attributes['vios_uuid'] is not None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F uuid".format(m_system)).splitlines())
        if vios_name not in vios_list:
            module.fail_json(msg="The vios is not available in the managed system")
        else:
            if attributes['vios_name'] is not None:
                filter_d = {"VIOS_NAMES": attributes['vios_name'], "SYS_NAMES": attributes['system'], "TYPES": attributes['types']}
            elif attributes['vios_id'] is not None:
                filter_d = {"VIOS_IDS": attributes['vios_id'], "SYS_NAMES": attributes['system'], "TYPES": attributes['types']}
            elif attributes['vios_uuid'] is not None:
                filter_d = {"VIOS_UUIDS": attributes['vios_uuid'], "SYS_NAMES": attributes['system'], "TYPES": attributes['types']}
            backup_list = hmc.listViosbk(filter_d)
            backup_list = [item['NAME'] for item in backup_list]
            file_list = attributes['file_list']
            removed_list = []
            for each in file_list[:]:
                if each not in backup_list:
                    removed_list.append(each)
                    file_list.remove(each)
            if len(file_list) != 0:
                attributes['backup_name'] = ','.join(map(str, file_list))
            else:
                msg = "Specified backup files are not available"
                return None, None, msg
            try:
                hmc.removeViosBk(configDict=attributes)
            except HmcError as error:
                if USER_AUTHORITY_ERR in repr(error):
                    logger.debug(repr(error))
                    return False, None, None
                else:
                    raise
            changed = True
            return changed, None, None


def ensure_modify(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    filter_d = {}

    validate_parameters(params)
    attributes = params.get('attributes')
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    vios_name = attributes['vios_name'] or attributes['vios_id'] or attributes['vios_uuid']
    m_system = attributes['system']
    sys_list = (
        hmc_conn.execute("lssyscfg -r sys -F name").splitlines() + hmc_conn.execute("lssyscfg -r sys -F type_model*serial_num").splitlines()
    )
    if m_system not in sys_list:
        module.fail_json(msg="The managed system is not available in HMC")
    else:
        if attributes['vios_name'] is not None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F name".format(m_system)).splitlines())
        elif attributes['vios_id'] is not None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F lpar_id".format(m_system)).splitlines())
        elif attributes['vios_uuid'] is not None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F uuid".format(m_system)).splitlines())
        if vios_name not in vios_list:
            module.fail_json(msg="The vios is not available in the managed system")
        else:
            if attributes['vios_name'] is not None:
                filter_d = {"VIOS_NAMES": attributes['vios_name'], "SYS_NAMES": attributes['system'], "TYPES": attributes['types']}
            elif attributes['vios_id'] is not None:
                filter_d = {"VIOS_IDS": attributes['vios_id'], "SYS_NAMES": attributes['system'], "TYPES": attributes['types']}
            elif attributes['vios_uuid'] is not None:
                filter_d = {"VIOS_UUIDS": attributes['vios_uuid'], "SYS_NAMES": attributes['system'], "TYPES": attributes['types']}
            backup_list = hmc.listViosbk(filter_d)
            backup_list = [item['NAME'] for item in backup_list]
            if attributes['backup_name'] not in backup_list:
                msg = "Specified backup files are not available"
                return None, None, msg
            else:
                try:
                    hmc.modifyViosBk(configDict=attributes)
                except HmcError as error:
                    if USER_AUTHORITY_ERR in repr(error):
                        logger.debug(repr(error))
                        return False, None, None
                    else:
                        raise
                changed = True
                return changed, None, None


def perform_task(module):
    params = module.params
    actions = {
        "facts": facts,
        "present": ensure_present,
        "restore": ensure_restore,
        "absent": ensure_absent,
        "modify": ensure_modify,
    }

    if not params['hmc_auth']:
        return False, "missing credential info", None
    try:
        return actions[params['state']](module, params)
    except Exception as error:
        return False, repr(error), None


def run_module():
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
        state=dict(type='str', choices=['facts', 'present', 'absent', 'restore', 'modify']),
        attributes=dict(type='dict',
                        required=True,
                        options=dict(
                            types=dict(required=True, type='str', choices=['viosioconfig', 'vios', 'ssp']),
                            system=dict(type='str'),
                            vios_id=dict(type='str'),
                            vios_uuid=dict(type='str'),
                            vios_name=dict(type='str'),
                            backup_name=dict(type='str'),
                            file_list=dict(type='list', elements='str'),
                            nimol_resource=dict(type='int', choices=[0, 1]),
                            media_repository=dict(type='int', choices=[0, 1]),
                            volume_group_structure=dict(type='int', choices=[0, 1]),
                            restart=dict(type='bool'),
                            new_name=dict(type='str')
                        )
                        ),
    )

    module = AnsibleModule(
        argument_spec=module_args,
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
    result['info'] = info
    if warning:
        result['warning'] = warning

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
