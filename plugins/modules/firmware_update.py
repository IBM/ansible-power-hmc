#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: firmware_update
short_description: Change firmware level on Managed Systems
version_added: "1.1.0"
description:
    - Update/Upgrade a managed system
options:
    hmc_host:
        description:
            - IPaddress or hostname of the HMC
        required: true
        type: str
    hmc_auth:
        description:
            - Username and Password credential of the HMC
        required: true
        type: dict
        suboptions:
            username:
                description:
                    - HMC username
                required: true
                type: str
            password:
                description:
                    - HMC password
                type: str
    system_name:
        description:
            - The name of the managed system
        required: true
        type: str
    repository:
        description: Type of image repository for the firmware image
        type: str
        default: ibmwebsite
        choices: ['ibmwebsite', 'ftp', 'sftp']
    remote_repo:
        description: When the image repository needs credentials to be accessed remotely
        type: dict
        suboptions:
            hostname: host for the image repository
                description:
                    - The hostname or IPaddress of the remote server where the
                      firmware image is located.
                type: str
            userid:
                description:
                    - The user ID to use to log in to the remote FTP or SFTP server.
                      This option is required when the firmware image is located on a remote FTP or SFTP server
                      Otherwise, this option is not valid.
                type: str
            passwd:
                description:
                    - The password to use to log in to the remote FTP or SFTP server.
                      The I(passwd) and I(sshkey) options are mutually exclusive in case if I(location_type=sftp).
                      This option is only valid when the firmware image is located on a remote FTP or SFTP server.
                type: str
            sshkey_file:
                description:
                    - The name of the file that contains the SSH private key.
                      This option is only valid if I(location_type=sftp).
                type: str
            directory:
                description:
                    - Location where the images are stored on the host
                type: str

author:
    - Mario Maldonado (@yourGitHubHandle)
'''

EXAMPLES = r'''
# Pass in a message
- name: Update to latest level with default values (latest at ibmwebsite)
  ibm.power_hmc.firmware_update:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
      state: updated

- name: Upgrade system to specific level at an sftp repo
  firmware_update:
    hmc_host: '{{ inventory_hostname }}'
    hmc_auth: '{{ curr_hmc_auth }}'
    system_name: <System name/mtms>
    repository: sftp
    remote_repo:
      hostname: 9.3.147.210
      userid: <user>
      passwd: <password>
     directory: /repo/images/
    level: 01VL941_047
    state: upgraded
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'hello world'
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'goodbye'
'''
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_resource import Hmc
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError

import logging
LOG_FILENAME = "/tmp/ansible_power_hmc.log"
logger = logging.getLogger(__name__)

def init_logger():
    logging.basicConfig(
        filename=LOG_FILENAME,
        format='[%(asctime)s] %(levelname)s: [%(funcName)s] %(message)s',
        level=logging.DEBUG)

def uplevel_system(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    repo = params['repository']
    changed = False
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    level = params['level']
    logger.debug("level: %s", level)
    remote_repo = params['remote_repo']
    if params['state'] == 'upgraded':
        upgrade = True
    else:
        upgrade = False

    try:
        hmc.update_managed_system(system_name, upgrade, repo, level, remote_repo)
    except HmcError as on_system_error:
        return False, repr(on_system_error), None

    changed = True
    return changed, None, None

def install_new_level(module, params):
    logger.debug("install new level")
    changed = False

    return changed, None, None

def remove_level(module, params):
    logger.debug("remove level")
    changed = False

    return changed, None, None

def activate_level(module, params):
    logger.debug("activate level")
    changed = False

    return changed, None, None

def perform_task(module):
    params = module.params
    actions = {
        "updated": uplevel_system,
        "upgraded": uplevel_system,
        "change": install_new_level,
        "remove": remove_level,
        "activate": activate_level
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
        action=dict(type='str', choices=['change', 'remove', 'activate']),
        state=dict(type='str', choices=['updated', 'upgraded',]),
        level=dict(type='str', default='latest'),
        repository=dict(type='str', default='ibmwebsite', choices=['ibmwebsite', 'ftp', 'sftp']),
        remote_repo=dict(type='dict', options=dict(
                              hostname=dict(type='str'),
                              userid=dict(type='str'),
                              passwd=dict(type='str', no_log=True),
                              sshkey_file=dict(type='str'),
                              directory=dict(type='str'),
                              )
                        )
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module._verbosity >= 5:
        init_logger()

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    #result['original_message'] = module.params['name']
    #result['message'] = 'goodbye'
    changed, info, warning = perform_task(module)

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    #if module.params['new']:
        #result['changed'] = True
    result['changed'] = changed
    if info:
        result['message'] = info

    if warning:
        result['warning'] = warning

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    #if module.params['name'] == 'fail me':
        #module.fail_json(msg='You requested this to fail', **result)
    if isinstance(info, str):
        module.fail_json(msg=info)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
