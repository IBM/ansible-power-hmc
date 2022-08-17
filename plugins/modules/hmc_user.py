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
module: hmc_user
author:
    - Anil Vijayan(@AnilVijayan)
short_description: Manage the hmc users
description:
    - Create a Hardware Management Console user
    - List Hardware Management Console user information
    - Modify a Hardware Management Console user
    - Remove Hardware Management Console users
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
    name:
        description:
            -  The user name of the HMC user.
        type: str
    enable_user:
        description:
            -  To enable an HMC user that was disabled due to inactivity.
            -  This option is only valid if I(state=updated).
        type: bool
    type:
        description:
            -  The type of user. During I(state=updated) to change the default settings of
               HMC user, specify C(default) with this option. The values of this option changes
               during I(state=absent). Supported values are C(all|local|kerberos|ldap|automanage).
               During I(state=facts), valid values are C(default|user).
        type: str
        choices: ['default', 'user', 'all', 'local', 'kerberos', 'ldap', 'automanage']
    attributes:
        description:
            - Configuration attributes used during the create and modify of HMC user
        type: dict
        suboptions:
            new_name:
                description:
                    - The new name to be updated.
                type: str
            taskrole:
                description:
                    - Valid values are C(hmcsuperadmin|hmcoperator|hmcviewer|
                      hmcpe|hmcservicerep|hmcclientliveupdate|<custom user role>).
                type: str
            resourcerole:
                description:
                    - The name of the resource role.
                type: str
            description:
                description:
                    - The description of the user.
                type: str
            passwd:
                description:
                    - Local and Kerberos users only.
                type: str
            current_passwd:
                description:
                    - When changing the password for a Kerberos user, use
                      this attribute to specify the user's current password.
                type: str
            pwage:
                description:
                    - Number of days. Valid only for local user. Default value is 99999
                type: str
            min_pwage:
                description:
                    - Number of days. Valid only for local user. Default value is 0
                type: str
            authentication_type:
                description:
                    - Valid values are C(local|kerberos|ldap).
                type: str
                choices: ['local', 'kerberos', 'ldap']
            session_timeout:
                description:
                    - Number of minutes. Default value is 0
                type: int
            verify_timeout:
                description:
                    - Number of minutes. Default value is 15
                type: int
            idle_timeout:
                description:
                    - Number of minutes. Default value is 120
                type: int
            inactivity_expiration:
                description:
                    - Number of days. Default value is 0
                type: int
            remote_webui_access:
                description:
                    - Allow or not allow the user to log in remotely to the
                      HMC Web user interface. Default value is False
                type: bool
            remote_ssh_access:
                description:
                    - Allow or not allow the user to log in remotely to the
                      HMC using SSH. Default value is True
                type: bool
            passwd_authentication:
                description:
                    - Allow or not allow the user to log in remotely to the
                      HMC using a password.
                type: bool
            remote_user_name:
                description:
                    - Kerberos users only.
                type: str
            max_webui_login_attempts:
                description:
                    - Maximum HMC UI login attempts.
                type: int
            webui_login_suspend_time:
                description:
                    - Number of minutes.
                type: int
    state:
        description:
            - The desired state of the HMC user.
            - C(facts) does not change anything on the HMC and returns the HMC user information or
              the default settings of HMC user attributes.
            - C(updated) ensures the HMC user is updated with provided configuration.
            - C(present) ensures the HMC user is created with provided configuration.
            - C(absent) ensures the HMC user is removed.
        required: true
        type: str
        choices: ['facts', 'present', 'absent', 'updated']

'''

EXAMPLES = '''
- name: List the properties of hmc user
  hmc_user:
    state: facts
    hmc_host: "{{ inventory_hostname }}"
    name: <user_name>
    hmc_auth:
      username: <username>
      password: <password>

- name: Create hmc user
  hmc_user:
    state: present
    hmc_host: "{{ inventory_hostname }}"
    name: <user_name>
    hmc_auth:
      username: <username>
      password: <password>
    attributes:
      authentication_type: local
      taskrole: hmcsuperadmin
      passwd: <new_user_password>

- name: Modify hmc user
  hmc_user:
    state: updated
    hmc_host: "{{ inventory_hostname }}"
    name: <user_name>
    hmc_auth:
      username: <username>
      password: <password>
    attributes:
      new_name: <new_user_name>
      max_webui_login_attempts: 20

- name: Remove hmc user
  hmc_user:
    state: absent
    hmc_host: "{{ inventory_hostname }}"
    name: <user_name>
    hmc_auth:
      username: <username>
      password: <password>

'''

RETURN = '''
Command_output:
    description: Respective user configuration
    type: dict
    returned: on success of all states except C(absent)
'''

import logging
LOG_FILENAME = "/tmp/ansible_power_hmc.log"
logger = logging.getLogger(__name__)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_resource import Hmc
import sys

USER_AUTHORITY_ERR = "HSCL350B The user does not have the appropriate authority"


def init_logger():
    logging.basicConfig(
        filename=LOG_FILENAME,
        format='[%(asctime)s] %(levelname)s: [%(funcName)s] %(message)s',
        level=logging.DEBUG)


def validate_sub_params(params):
    key = None
    supportedList = []
    notSupportedList = []
    notTogetherList = []
    mandatoryList = []
    state = params.get('state')

    if state == 'facts':
        key = 'type'
        supportedList = ['default', 'user']
        if params['type'] == 'default' and params['name']:
            raise ParameterError("%s state will not support parameter: name with default type"
                                 % state)
    elif state == 'present':
        mandatoryList = ['taskrole']
        key = params['attributes']
        notSupportedList = ['new_name', 'current_passwd',
                            'webui_login_suspend_time', 'max_webui_login_attempts']

        if (params.get('attributes').get("authentication_type") == 'local' or params.get('attributes').
           get("authentication_type") is None) and (not params.get('attributes').get('passwd')):
            raise ParameterError("'passwd' attribute is mandatory")
    elif state == 'updated':
        default_support = ['webui_login_suspend_time', 'max_webui_login_attempts',
                           'session_timeout', 'idle_timeout']

        if params['enable_user'] is not None:
            nonSupport = []
            if params['type']:
                nonSupport.append("type")
            if params['attributes']:
                nonSupport.append("attributes")
            if nonSupport:
                nonSupport.append("enable_user")
                raise ParameterError("%s state will not support parameters: %s together" %
                                     (state, ','.join(nonSupport)))
            if params['name'] is None:
                raise ParameterError("mandatory parameter: name missing")
            return

        if params['type'] == 'default' and params['attributes']:
            default_types = [each for each in default_support if params['attributes'][each] is not None]
            all_data = [each for each in params['attributes'] if params['attributes'][each] is not None]
            if len(all_data) > len(default_types):
                raise ParameterError("%s state will support only attributes: %s for default type"
                                     % (state, ','.join(default_support)))
        elif params['type'] == 'default' and params['attributes'] is None:
            raise ParameterError("mandatory parameter: attributes missing")
        elif params['type'] is None and params['name'] is None:
            raise ParameterError("%s state need parameter: name with non default settings"
                                 % (state))
        if params['type'] is None and params['name'] and params['attributes'] is None and \
                params['enable_user'] is None:
            raise ParameterError("%s state with parameter: name either need enable_user or attributes param"
                                 % state)
        if params['name'] is not None and params['attributes'] is not None:
            for each in ['webui_login_suspend_time', 'max_webui_login_attempts']:
                if params['attributes'][each] is not None:
                    raise ParameterError("updated state with parameter: name will not support attributes: %s"
                                         % ','.join(['webui_login_suspend_time', 'max_webui_login_attempts']))
        key = 'type'
        supportedList = ['default']
        notTogetherList = [['name', 'type']]
    elif state == 'absent':
        notTogetherList = [['name', 'type']]
        key = 'type'
        supportedList = ['all', 'local', 'kerberos', 'ldap', 'automanage']

        if params['type'] is None and params['name'] is None:
            raise ParameterError("%s state need either name or type parameter" % (state))

    if isinstance(key, str):
        if params.get(key) and params[key] not in supportedList:
            raise ParameterError("%s state will not support %s: %s" % (state, key, params[key]))
    elif isinstance(key, dict):
        collate = [each for each in notSupportedList if params['attributes'].get(each)]
        if collate:
            singularplural = 'attributes' if len(collate) > 1 else 'attribute'
            raise ParameterError("%s state will not support %s: %s" % (state, singularplural,
                                 ','.join(collate)))

    if notTogetherList:
        for notTogether in notTogetherList:
            if (all(params[each] for each in notTogether)):
                raise ParameterError("%s state will not support parameters: %s together" %
                                     (state, ','.join(notTogether)))
    if mandatoryList:
        if not all(params['attributes'].get(each) for each in mandatoryList):
            singularplural = (('parameters', 'are') if len(mandatoryList) > 1 else ('parameter', 'is'))
            raise ParameterError("mandatory %s %s %s missing"
                                 % (singularplural[0], ','.join(mandatoryList), singularplural[1]))


def validate_parameters(params):
    '''Check that the input parameters satisfy the mutual exclusiveness of HMC'''
    opr = None
    unsupportedList = []
    mandatoryList = []

    if params['state'] is not None:
        opr = params['state']

    if opr == 'present':
        mandatoryList = ['hmc_host', 'hmc_auth', 'name', 'attributes']
        unsupportedList = ['enable_user', 'type']
    elif opr == 'absent':
        mandatoryList = ['hmc_host', 'hmc_auth']
        unsupportedList = ['enable_user', 'attributes']
    elif opr == 'updated':
        mandatoryList = ['hmc_host', 'hmc_auth']
    elif opr == 'facts':
        mandatoryList = ['hmc_host', 'hmc_auth']
        unsupportedList = ['attributes', 'enable_user']

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
    user_details = []

    validate_parameters(params)
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    if params.get('name'):
        filter_d = {"NAMES": params['name']}
    u_type = params.get('type')

    try:
        user_details = hmc.listUsr(filt=filter_d, user_type=u_type)
    except HmcError as error:
        if USER_AUTHORITY_ERR in repr(error):
            logger.debug(repr(error))
            return False, None, None
        else:
            raise
    return False, user_details, None


def ensure_present(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    usr_name = params['name']
    user_info = []

    validate_parameters(params)
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    already_exist = False
    filter_d = {"NAMES": usr_name}
    try:
        user_info = hmc.listUsr(filt=filter_d)
    except HmcError as error:
        if USER_AUTHORITY_ERR in repr(error):
            logger.debug(repr(error))
            return False, None, None
        else:
            raise
    if user_info and usr_name == user_info[0]['NAME']:
        already_exist = True

    changed = False
    if not already_exist:
        config = {"NAME": usr_name}
        config.update(params['attributes'])
        hmc.createUsr(config)
        user_info = hmc.listUsr(filt=filter_d)
        if user_info and usr_name == user_info[0]['NAME']:
            changed = True
    return changed, user_info, None


def is_user_present(user_list, r_type):
    permanent_user = ['root', 'hscroot', 'hscpe']
    for eachUser in user_list:
        if eachUser['NAME'] in permanent_user:
            continue
        elif r_type == 'all':
            return True
        elif eachUser['AUTHENTICATION_TYPE'] == r_type:
            return True
    return False


def ensure_absent(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    usr_name = params.get("name")
    r_type = params['type']
    user_info = []
    filter_d = None

    validate_parameters(params)
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    user_exist = False
    if usr_name:
        filter_d = {"NAMES": usr_name}
    try:
        user_info = hmc.listUsr(filt=filter_d)
    except HmcError as error:
        if USER_AUTHORITY_ERR in repr(error):
            logger.debug(repr(error))
            return False, None, None
        else:
            raise
    if user_info and usr_name == user_info[0]['NAME']:
        user_exist = True

    changed = False
    if user_exist:
        hmc.removeUsr(usr=usr_name, rm_type=r_type)
        user_info = hmc.listUsr(filt=filter_d)
        if not user_info:
            changed = True
    else:
        user_info = hmc.listUsr()
        if not is_user_present(user_info, r_type):
            return False, None, None

        hmc.removeUsr(rm_type=r_type)

        user_info = hmc.listUsr()
        if is_user_present(user_info, r_type):
            return False, None, "user removal not succeeded"
        changed = True
    return changed, None, None


def isDifferent(source, target):
    for each in source:
        if source[each] is not None and isinstance(source.get(each), bool):
            if source[each]:
                source[each] = '1'
            else:
                source[each] = '0'
        if source[each] is not None and str(source[each]) != target.get(each.upper()):
            return True
    if source.get('new_name') is not None:
        if source['new_name'] != source['name']:
            return True
    return False


def ensure_update(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    usr_name = params.get('name')
    m_type = params.get('type')
    usr_name = params.get('name')
    enable_user = params.get('enable_user')
    attributes = params.get('attributes')
    user_info = []

    validate_parameters(params)
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    already_exist = False
    if usr_name:
        filter_d = {"NAMES": usr_name}
        try:
            user_info = hmc.listUsr(filt=filter_d)
        except HmcError as error:
            if USER_AUTHORITY_ERR in repr(error):
                logger.debug(repr(error))
                return False, None, None
            else:
                raise
        if user_info and usr_name == user_info[0]['NAME']:
            already_exist = True
        else:
            return False, None, None

    changed = False
    if already_exist:
        m_config = {"NAME": usr_name}
        if attributes:
            m_config.update(attributes)

        if enable_user:
            user_info_check = hmc.listUsr(filt=filter_d)
            if user_info_check[0].get('DISABLED') == '1':
                hmc.modifyUsr(enable=enable_user, configDict={"NAME": usr_name})
                changed = True
        else:
            user_info_check = hmc.listUsr(filt=filter_d)
            if isDifferent(m_config, user_info_check[0]):
                hmc.modifyUsr(configDict=m_config)
                if attributes and attributes['new_name'] is not None:
                    filter_d['NAMES'] = attributes['new_name']
                changed = True

        user_info = hmc.listUsr(filt=filter_d)
        return changed, user_info[0], None
    elif m_type:
        user_info_check = None
        try:
            user_info_check = hmc.listUsr(user_type=m_type)
        except HmcError as error:
            if USER_AUTHORITY_ERR in repr(error):
                logger.debug(repr(error))
                return False, None, None
            else:
                raise

        if isDifferent(attributes, user_info_check[0]):
            hmc.modifyUsr(modify_type=m_type, configDict=attributes)
            changed = True
        user_info = hmc.listUsr(user_type=m_type)
        return changed, user_info, None
    return changed, None, None


def perform_task(module):
    params = module.params
    actions = {
        "facts": facts,
        "present": ensure_present,
        "absent": ensure_absent,
        "updated": ensure_update
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
        name=dict(type='str'),
        enable_user=dict(type='bool'),
        type=dict(type='str', choices=['default', 'user', 'all', 'local',
                                       'kerberos', 'ldap', 'automanage']),
        state=dict(required=True, type='str',
                   choices=['facts', 'present', 'absent', 'updated']),
        attributes=dict(type='dict',
                        options=dict(
                            new_name=dict(type='str'),
                            taskrole=dict(type='str'),
                            resourcerole=dict(type='str'),
                            description=dict(type='str'),
                            passwd=dict(type='str', no_log=True),
                            current_passwd=dict(type='str', no_log=True),
                            pwage=dict(type='str'),
                            min_pwage=dict(type='str'),
                            authentication_type=dict(type='str',
                                                     choices=['local', 'kerberos', 'ldap']),
                            session_timeout=dict(type='int'),
                            verify_timeout=dict(type='int'),
                            idle_timeout=dict(type='int'),
                            inactivity_expiration=dict(type='int'),
                            remote_webui_access=dict(type='bool'),
                            remote_ssh_access=dict(type='bool'),
                            passwd_authentication=dict(type='bool'),
                            remote_user_name=dict(type='str'),
                            max_webui_login_attempts=dict(type='int'),
                            webui_login_suspend_time=dict(type='int')
                        )
                        ),
    )

    module = AnsibleModule(
        argument_spec=module_args
    )

    if module._verbosity >= 5:
        init_logger()

    if sys.version_info < (3, 0):
        py_ver = sys.version_info[0]
        module.fail_json("Unsupported Python version {0}, supported python version is 3 and above".format(py_ver))

    changed, user_info, warning = perform_task(module)
    if isinstance(user_info, str):
        module.fail_json(msg=user_info)

    result = {}
    result['changed'] = changed
    result['user_info'] = user_info
    if warning:
        result['warning'] = warning

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
