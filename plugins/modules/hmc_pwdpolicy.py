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
module: hmc_pwdpolicy
author:
    - Anil Vijayan (@AnilVijayan)
short_description: Manages the list, create, change and remove password policies of the HMC
description:
    - Lists Hardware Management Console password policy information by password policies or password policy status.
    - Creates a password policy.
    - Change password policies on the Hardware Management Console to activate, deactivate or modify password policy.
    - Removes a password policy from the Hardware Management Console.
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
    policy_name:
        description:
            - The name of the password policy.
        type: str
    policy_config:
        description:
            - Configuration parameters required for the HMC password policies.
              This option is valid for state like C(present), C(modified).
        type: dict
        suboptions:
            pwage:
                description:
                    - The number of days that can elapse before a password
                      expires and must be changed. A value of 99999 indicates
                      no password expiration.
                type: str
            description:
                description:
                    - Description for the password policy.
                type: str
            min_pwage:
                description:
                    - The number of days that must elapse before a password can be changed.
                type: str
            warn_pwage:
                description:
                    - The number of days prior to password expiration when a
                      warning message will begin to be displayed.
                type: str
            min_length:
                description:
                    - The minimum password length.
                type: str
            hist_size:
                description:
                    - The number of times a password must be changed before
                      a password can be reused. This value cannot exceed 50.
                type: str
            min_digits:
                description:
                    - The minimum number of digits that a password must contain
                type: str
            min_uppercase_chars:
                description:
                    - The minimum number of uppercase characters that a password must contain.
                type: str
            min_lowercase_chars:
                description:
                    - The minimum number of lowercase characters that a password must contain.
                type: str
            min_special_chars:
                description:
                    - The minimum number of special characters that a password must contain.
                      Special characters include symbols, punctuation, and white space characters.
                type: str
            new_name:
                description:
                    - The new name of the password policy.
                      This option valid only when I(state=modified).
                type: str
    policy_type:
        description:
            - C(policies) list all the password policies on the HMC.
            - C(status) list password policy status information.
        type: str
        choices: ['policies', 'status']
    state:
        description:
            - The desired password policy state of the target HMC.
            - C(present) ensure the target HMC is having the mentioned password policy.
            - C(modified) ensure the policy on target HMC password is modified.
            - C(absent) ensure the policy on the target HMC password is removed.
            - C(facts) does not change anything on the HMC and returns current policy status/settings of HMC.
            - C(activated) ensure the policy on the target HMC password is activated.
            - C(deactivated) ensure the password policy is deactivated on the target HMC.
        required: true
        type: str
        choices: ['present', 'modified', 'absent', 'facts', 'activated', 'deactivated']
'''

EXAMPLES = '''
- name: List the HMC password policy current status
  hmc_pwdpolicy:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    policy_type: status
    state: facts

- name: create the password policy
  hmc_pwdpolicy:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    policy_name: dummy
    state: present
    policy_config:

- name: update the password policy with new settings
  hmc_pwdpolicy:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    policy_name: dummy
    policy_config:
       pwage: 80
       hist_size: 12
    state: modified

- name: activate the password policy
  hmc_pwdpolicy:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    policy_name: dummy
    state: activated

- name: De-activate any active policy on HMC
  hmc_pwdpolicy:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    state: deactivated

- name: remove the password policy
  hmc_pwdpolicy:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    policy_name: dummy
    state: absent
'''

RETURN = '''
policy_info:
    description: Respective policy information
    type: dict
    returned: always
'''

import logging
LOG_FILENAME = "/tmp/ansible_power_hmc.log"
logger = logging.getLogger(__name__)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_resource import Hmc
import sys


def init_logger():
    logging.basicConfig(
        filename=LOG_FILENAME,
        format='[%(asctime)s] %(levelname)s: [%(funcName)s] %(message)s',
        level=logging.DEBUG)


def facts(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    changed = False
    hmc_conn = None

    if params['policy_config']:
        raise ParameterError("not supporting policy_config option")

    if params['policy_name']:
        raise ParameterError("not supporting policy_name option")

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    policy_details = hmc.listPwdPolicy(params['policy_type'])

    return changed, policy_details


def ensure_present(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    hmc_conn = None
    policy_config = {}

    if params['policy_type']:
        raise ParameterError("not supporting policy_type option")

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    existing_policies = hmc.listPwdPolicy('policies')
    for each_policy in existing_policies:
        if each_policy['NAME'] == params['policy_name']:
            return False, each_policy

    if params['policy_config']:
        policy_config = {k: v for k, v in params['policy_config'].items() if params['policy_config'][k] is not None}
        if 'new_name' in policy_config:
            raise ParameterError("not supporting the policy_config option: new_name")

    policy_config.update({'name': params['policy_name']})
    logger.debug(policy_config)

    hmc.createPwdPolicy(policy_config)
    policies = hmc.listPwdPolicy('policies')
    for each_policy in policies:
        if each_policy['NAME'] == params['policy_name']:
            return True, each_policy

    return False, "HmcError: created policy not listing"


def ensure_updation(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    changed = False
    hmc_conn = None
    policy_to_update = None
    policy_updated = None
    policy_curr_config = None
    need_update = False
    policy_name = params['policy_name']

    if not params['policy_config']:
        raise ParameterError("missing parameters on policy_config")

    if params['policy_type']:
        raise ParameterError("not supporting policy_type option")

    policy_config = {k: v for k, v in params['policy_config'].items() if params['policy_config'][k] is not None}
    logger.debug(policy_config)

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    existing_policies = hmc.listPwdPolicy('policies')
    for each_policy in existing_policies:
        if each_policy['NAME'] == policy_name:
            policy_to_update = each_policy
            break

    if policy_to_update:
        for eachKey in policy_config:
            if eachKey != 'new_name' and policy_config[eachKey] != policy_to_update[eachKey.upper()]:
                need_update = True
                break
    else:
        raise ParameterError("given policy does not exist")

    if 'new_name' in policy_config and \
            policy_config['new_name'] != params['policy_name']:
        need_update = True
        policy_name = policy_config['new_name']

    policy_curr_config = policy_to_update
    logger.debug(policy_curr_config)
    if need_update:
        policy_config.update({'name': params['policy_name']})

        hmc.modifyPwdPolicy(policy_config=policy_config)

        policies = hmc.listPwdPolicy('policies')
        for each_policy in policies:
            if each_policy['NAME'] == policy_name:
                policy_updated = each_policy
                break

        policy_config['name'] = policy_name
        if policy_updated:
            for eachKey in policy_config:
                if eachKey != 'new_name' and policy_config[eachKey] != policy_updated[eachKey.upper()]:
                    return False, "HmcError: modified config not reflected"
        changed = True
        policy_curr_config = policy_updated

    logger.debug(policy_curr_config)
    return changed, policy_curr_config


def ensure_activate(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    hmc_conn = None
    policy_identified = None

    if params['policy_type']:
        raise ParameterError("not supporting policy_type option")

    if params['policy_config']:
        raise ParameterError("not supporting policy_config option")

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    policy_name = params['policy_name']
    existing_policies = hmc.listPwdPolicy('policies')
    for each_policy in existing_policies:
        if each_policy['NAME'] == policy_name:
            policy_identified = each_policy
            break

    if not policy_identified:
        raise ParameterError("given policy does not exist")

    if policy_identified['ACTIVE'] == '0':
        hmc.modifyPwdPolicy(policy_name, activate=True)
        existing_policies = hmc.listPwdPolicy('policies')
        for each_policy in existing_policies:
            if each_policy['NAME'] == policy_name:
                return True, each_policy

    return False, policy_identified


def ensure_deactivate(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    hmc_conn = None

    if params['policy_type']:
        raise ParameterError("not supporting policy_type option")

    if params['policy_name']:
        raise ParameterError("not supporting policy_name option")

    if params['policy_config']:
        raise ParameterError("not supporting policy_config option")

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    existing_status = hmc.listPwdPolicy('status')
    if existing_status['ACTIVE'] == '1':
        hmc.modifyPwdPolicy(activate=False)
        return True, None

    return False, None


def ensure_absent(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    hmc_conn = None

    if params['policy_type']:
        raise ParameterError("not supporting policy_type option")

    if params['policy_config']:
        raise ParameterError("not supporting policy_config option")

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    existing_policies = hmc.listPwdPolicy('policies')
    for each_policy in existing_policies:
        if each_policy['NAME'] == params['policy_name']:
            hmc.removePwdPolicy(params['policy_name'])
            return True, None

    return False, None


def perform_task(module):

    params = module.params
    actions = {
        "facts": facts,
        "present": ensure_present,
        "absent": ensure_absent,
        "modified": ensure_updation,
        "activated": ensure_activate,
        "deactivated": ensure_deactivate
    }

    if not params['hmc_auth']:
        return False, "missing credential info"

    try:
        return actions[params['state']](module, params)
    except Exception as error:
        return False, str(error)


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
        policy_name=dict(type='str'),
        policy_config=dict(type='dict',
                           options=dict(
                               description=dict(type='str'),
                               pwage=dict(type='str'),
                               min_pwage=dict(type='str'),
                               warn_pwage=dict(type='str'),
                               min_length=dict(type='str'),
                               hist_size=dict(type='str'),
                               min_digits=dict(type='str'),
                               min_uppercase_chars=dict(type='str'),
                               min_lowercase_chars=dict(type='str'),
                               min_special_chars=dict(type='str'),
                               new_name=dict(type='str')
                           )),
        state=dict(type='str', required=True,
                   choices=['present', 'modified', 'absent', 'facts', 'activated', 'deactivated']),
        policy_type=dict(type='str',
                         choices=['policies', 'status'])
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_if=[['state', 'facts', ['hmc_host', 'hmc_auth', 'policy_type']],
                     ['state', 'present', ['hmc_host', 'hmc_auth', 'policy_name']],
                     ['state', 'modified', ['hmc_host', 'hmc_auth', 'policy_name', 'policy_config']],
                     ['state', 'absent', ['hmc_host', 'hmc_auth', 'policy_name']],
                     ['state', 'activated', ['hmc_host', 'hmc_auth', 'policy_name']],
                     ['state', 'deactivated', ['hmc_host', 'hmc_auth']]
                     ],
    )

    if module._verbosity >= 5:
        init_logger()

    if sys.version_info < (3, 0):
        py_ver = sys.version_info[0]
        module.fail_json("Unsupported Python version {0}, supported python version is 3 and above".format(py_ver))

    changed, result = perform_task(module)

    if isinstance(result, str):
        module.fail_json(msg=result)

    if result:
        module.exit_json(changed=changed, policy_info=result)
    else:
        module.exit_json(changed=changed)


def main():
    run_module()


if __name__ == '__main__':
    main()
