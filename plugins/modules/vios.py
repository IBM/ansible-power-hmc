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
short_description: Creation and management of Virtual I/O Server partition
description:
    - "Creates VIOS partition"
    - "Installs VIOS"
    - "Displays VIOS information"
    - "Accepts VIOS License"
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
    system_name:
        description:
            - The name of the managed system.
        required: true
        type: str
    name:
        description:
            - The name of the VirtualIOServer.
        required: true
        type: str
    settings:
        description:
            - To configure various supported attributes of VIOS partition.
            - Supports all the attributes available for creation of VIOS
              on the mksyscfg command
            - valid only for C(state) = I(present)
        type: dict
    nim_IP:
        description:
            - IP Address of the NIM Server.
            - valid only for C(action) = I(install)
        type: str
    nim_gateway:
        description:
            - VIOS gateway IP Address.
            - valid only for C(action) = I(install)
        type: str
    vios_IP:
        description:
            - IP Address to be configured to VIOS.
            - valid only for C(action) = I(install)
        type: str
    prof_name:
        description:
            - Profile Name to be used for VIOS install.
            - Default profile name 'default_profile'
            - valid only for C(action) = I(install)
        type: str
    location_code:
        description:
            - Network adapter location code to be used while installing VIOS.
            - If user doesn't provide, it automatically picks the first pingable adapter attached to the partition.
            - valid only for C(action) = I(install)
        type: str
    nim_subnetmask:
        description:
            - Subnetmask IP Address to be configured to VIOS.
            - valid only for C(action) = I(install)
        type: str
    nim_vlan_id:
        description:
            - Specifies the VLANID(0 to 4094) to use for tagging Ethernet frames during network install for virtual network communication.
            - Default value is 0
            - valid only for C(action) = I(install)
        type: str
    nim_vlan_priority:
        description:
            - Specifies the VLAN priority (0 to 7) to use for tagging Ethernet frames during network install for virtual network communication.
            - Default value is 0
            - valid only for C(action) = I(install)
        type: str
    timeout:
        description:
            - Max waiting time in mins for VIOS to bootup fully.
            - Min timeout should be more than 10 mins.
            - Default value is 60 min.
            - valid only for C(action) = I(install)
        type: int
    state:
        description:
            - C(facts) fetch details of specified I(virtualioserver)
            - C(present) creates VIOS with specified I(settings)
        type: str
        choices: ['facts', 'present']
    action:
        description:
            - C(install) install VIOS through NIM Server
            - C(accept_license) Accept license after fresh installation of VIOS
        type: str
        choices: ['install', 'accept_license']
'''

EXAMPLES = '''
- name: Create VIOS with default configuration
  vios:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: <managed_system_name>
    name: <vios_partition_name>
    state: present

- name: Create VIOS with user defined settings
  vios:
    hmc_host: '{{ inventory_hostname }}'
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: <managed_system_name>
    name: <vios_partition_name>
    settings:
      profile_name: <profileName>
      io_slots: <ioslot1>,<ioslot2>
    state: present

- name: Install VIOS using NIM Server
  vios:
    hmc_host: '{{ inventory_hostname }}'
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    system_name: <managed_system_name>
    name: <vios name>
    nim_IP: <NIM Server IP>
    nim_gateway: <vios gateway ip>
    vios_IP: <vios ip>
    nim_subnetmask: <subnetmask>
    action: install

- name: Accept License after VIOS Installation
  vios:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    system_name: <managed_system_name>
    name: <vios_partition_name>
    action: accept_license

'''

RETURN = '''
vios_info:
    description: Respective VIOS information
    type: dict
    returned: on success for action install
'''

import logging
import time
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
    opr = None
    if params['state'] is not None:
        opr = params['state']
    else:
        opr = params['action']

    if opr == 'install':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'name', 'nim_IP', 'nim_gateway', 'vios_IP', 'nim_subnetmask']
        unsupportedList = ['settings']
    elif opr == 'present':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'name']
        unsupportedList = ['nim_IP', 'nim_gateway', 'vios_IP', 'nim_subnetmask', 'prof_name', 'location_code', 'nim_vlan_id', 'nim_vlan_priority', 'timeout']
    else:
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'name']
        unsupportedList = ['nim_IP', 'nim_gateway', 'vios_IP', 'nim_subnetmask', 'prof_name', 'location_code', 'nim_vlan_id', 'nim_vlan_priority',
                           'timeout', 'settings']

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


def checkForVIOSToBootUpFully(hmc, system_name, name, timeoutInMin=60):
    POLL_INTERVAL_IN_SEC = 30
    WAIT_UNTIL_IN_SEC = timeoutInMin * 60 - 600
    waited = 0
    rmcActive = False
    ref_code = None
    # wait for 10 mins before polling
    time.sleep(600)
    while waited < WAIT_UNTIL_IN_SEC:
        conf_dict = hmc.getPartitionConfig(system_name, name)
        if conf_dict['rmc_state'] == 'active':
            rmcActive = True
            break
        else:
            waited += POLL_INTERVAL_IN_SEC
        time.sleep(POLL_INTERVAL_IN_SEC)
    if not rmcActive:
        res = hmc.getPartitionRefcode(system_name, name)
        ref_code = res['REFCODE']
    return rmcActive, conf_dict, ref_code


def fetchViosInfo(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    name = params['name']
    validate_parameters(params)
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
    validate_parameters(params)
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
            # Settings default profile name to 'default_profile' in case user didnt provide
            prof_name = params.get('settings').get('profile_name', 'default_profile')

        lpar_config = hmc.getPartitionConfig(system_name, name, prof_name)
    except HmcError as vios_error:
        return False, repr(vios_error), None

    return True, lpar_config, None


def installVios(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    name = params['name']
    nim_IP = params['nim_IP']
    nim_gateway = params['nim_gateway']
    vios_IP = params['vios_IP']
    prof_name = params['prof_name'] or 'default_profile'
    location_code = params['location_code']
    nim_subnetmask = params['nim_subnetmask']
    nim_vlan_id = params['nim_vlan_id'] or '0'
    nim_vlan_priority = params['nim_vlan_priority'] or '0'
    timeout = params['timeout'] or 60
    validate_parameters(params)
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    changed = False
    vios_property = None
    warn_msg = None

    if timeout < 10:
        module.fail_json(msg="timeout should be more than 10mins")
    try:
        if location_code:
            hmc.installVIOSFromNIM(location_code, nim_IP, nim_gateway, vios_IP, nim_vlan_id, nim_vlan_priority, nim_subnetmask, name, prof_name, system_name)
        else:
            dvcdictlt = hmc.fetchIODetailsForNetboot(nim_IP, nim_gateway, vios_IP, name, prof_name, system_name)
            for dvcdict in dvcdictlt:
                if dvcdict['Ping Result'] == 'successful':
                    location_code = dvcdict['Location Code']
                    break
            if location_code:
                hmc.installVIOSFromNIM(location_code, nim_IP, nim_gateway, vios_IP, nim_vlan_id, nim_vlan_priority, nim_subnetmask,
                                       name, prof_name, system_name)
            else:
                module.fail_json(msg="None of adapters part of the profile is reachable through network. Please attach correct network adapter")

        rmc_state, vios_property, ref_code = checkForVIOSToBootUpFully(hmc, system_name, name, timeout)
        if rmc_state:
            changed = True
        elif ref_code in ['', '00']:
            changed = True
            warn_msg = "VIOS installation has been succefull but RMC didnt come up, please check the HMC firewall and security"
        else:
            module.fail_json(msg="VIOS Installation failed even after waiting for " + str(timeout) + " mins and the reference code is " + ref_code)
    except HmcError as install_error:
        return False, repr(install_error), None

    return changed, vios_property, warn_msg


def viosLicenseAccept(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    name = params['name']
    validate_parameters(params)
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    changed = False
    try:
        vios_config = hmc.getPartitionConfig(system_name, name)
        if vios_config['rmc_state'] == 'active':
            hmc.runCommandOnVIOS(system_name, name, 'license -accept')
            changed = True
        else:
            module.fail_json(msg="Cannot accept the license since the RMC state is " + vios_config['rmc_state'])
    except HmcError as error:
        return False, repr(error), None

    return changed, None, None


def perform_task(module):
    params = module.params
    actions = {
        "facts": fetchViosInfo,
        "present": createVios,
        "install": installVios,
        "accept_license": viosLicenseAccept
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
        name=dict(type='str', required=True),
        settings=dict(type='dict'),
        nim_IP=dict(type='str'),
        nim_gateway=dict(type='str'),
        vios_IP=dict(type='str'),
        prof_name=dict(type='str'),
        location_code=dict(type='str'),
        nim_subnetmask=dict(type='str'),
        nim_vlan_id=dict(type='str'),
        nim_vlan_priority=dict(type='str'),
        timeout=dict(type='int'),
        state=dict(type='str', choices=['facts', 'present']),
        action=dict(type='str', choices=['install', 'accept_license']),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=[('state', 'action')],
        required_one_of=[('state', 'action')],
        required_if=[['state', 'facts', ['hmc_host', 'hmc_auth', 'system_name', 'name']],
                     ['state', 'present', ['hmc_host', 'hmc_auth', 'system_name', 'name']],
                     ['action', 'install', ['hmc_host', 'hmc_auth', 'system_name', 'name', 'nim_IP', 'nim_gateway', 'vios_IP', 'nim_subnetmask']],
                     ['action', 'accept_license', ['hmc_host', 'hmc_auth', 'system_name', 'name']],
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
