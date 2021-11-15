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
    nimIP:
        description:
            - IP Address of the NIM Server
            - valid only for C(action) = I(install)
        type: str
    gateway:
        description:
            - VIOS gateway IP Address
            - valid only for C(action) = I(install)
        type: str
    viosIP:
        description:
            - IP Address to be configured to VIOS
            - valid only for C(action) = I(install)
        type: str
    prof_name:
        description:
            - Profile Name to be used for VIOS install
            - Default profile name 'default_profile'
            - valid only for C(action) = I(install)
        type: str
    nw_type:
        description:
            - adapter network type used for VIOS install
            - Default network type is 'ent'
            - valid only for C(action) = I(install)
        type: str
    location_code:
        description:
            - network adapter location code to be used while installing VIOS
            - If user doesn't pass, it automatically picks the first successfule adapter attached to partition
            - valid only for C(action) = I(install)
        type: str
    sub_mask:
        description:
            - Subnetmask IP Address to be configured to VIOS
            - valid only for C(action) = I(install)
        type: str
    vlanID:
        description:
            - VLANID to use during VIOS install through network install
            - Default value is 0
            - valid only for C(action) = I(install)
        type: str
    vlanPrio:
        description:
            - VLAN Priority to use during VIOS install through network install
            - Default value is 0
            - valid only for C(action) = I(install)
        type: str
    state:
        description:
            - C(facts) fetch details of specified I(virtualioserver)
            - C(present) creates VIOS with specified I(settings)
        type: str
        choices: ['facts', 'present']
    action:
        description:
            - C(install) install VIOS through NIM Server
        type: str
        choices: ['install']
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

- name: Install VIOS using NIM Server
  vios:
    hmc_host: '{{ inventory_hostname }}'
    hmc_auth:
         username: '{{ ansible_user }}'
         password: '{{ hmc_password }}'
    system_name: <managed_system_name>
    name: <vios name>
    nimIP: <NIM Server IP>
    gateway: <vios gateway ip>
    viosIP: <vios ip>
    sub_mask: <subnetmask>
    action: install

'''

RETURN = '''
vios_info:
    description: Respective VIOS information
    type: dict
    returned: on success for action C(install)
'''

import logging
import time
LOG_FILENAME = "/tmp/ansible_power_hmc_navin.log"
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
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'name', 'nimIP', 'gateway', 'viosIP', 'sub_mask']
        unsupportedList = ['settings']
    elif opr == 'present':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'name']
        unsupportedList = ['nimIP', 'gateway', 'viosIP', 'sub_mask', 'prof_name', 'nw_type', 'location_code', 'vlanID', 'vlanPrio']
    else:
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'name']
        unsupportedList = ['nimIP', 'gateway', 'viosIP', 'sub_mask', 'prof_name', 'nw_type', 'location_code', 'vlanID', 'vlanPrio', 'settings']

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


def fecthDeviceDetails(result):
    lns = result.strip('\n').split('\n')
    res = []
    for ln in lns:
        di = {}
        logger.debug(ln)
        if not ln.lstrip().startswith('#'):
            x = ln.split()
            logger.debug(x)
            di['Type'] = x[0]
            di['Location Code'] = x[1]
            di['MAC Address'] = x[2]
            di['Full Path Name'] = x[3]
            di['Ping Result'] = x[4]
            di['Device Type'] = x[5]
            res.append(di)
    return res


def checkForVIOSToBootUpFully(hmc, system_name, name, timeoutInMin=50):
    POLL_INTERVAL_IN_SEC = 30
    WAIT_UNTIL_IN_SEC = timeoutInMin * 60
    waited = 0
    rmcActive = False
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
    return rmcActive, conf_dict


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


def installVios(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    name = params['name']
    nimIP = params['nimIP']
    gateway = params['gateway']
    viosIP = params['viosIP']
    prof_name = params['prof_name'] or 'default_profile'
    nw_type = params['nw_type'] or 'ent'
    location_code = params['location_code']
    sub_mask = params['sub_mask']
    vlanID = params['vlanID'] or '0'
    vlanPrio = params['vlanPrio'] or '0'
    validate_parameters(params)
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    changed = False
    vios_property = None
    try:
        if location_code:
            hmc.installVIOSFromNIM(nw_type, location_code, nimIP, gateway, viosIP, vlanID, vlanPrio, sub_mask, name, prof_name, system_name)
        else:
            result = hmc.getVIOSPhysicalioDeviceStatus(nw_type, nimIP, gateway, viosIP, name, prof_name, system_name)
            dvcdictlt = fecthDeviceDetails(result)
            for dvcdict in dvcdictlt:
                if dvcdict['Ping Result'] == 'successful':
                    location_code = dvcdict['Location Code']
                    break
            if location_code:
                hmc.installVIOSFromNIM(nw_type, location_code, nimIP, gateway, viosIP, vlanID, vlanPrio, sub_mask, name, prof_name, system_name)
            else:
                module.fail_json(msg="None of the adapters Ping test succeeded, please attach correct network adapter")

        rmc_state, vios_property = checkForVIOSToBootUpFully(hmc, system_name, name)
        if rmc_state:
            changed = True
        else:
            module.fail_json(msg="RMC state of the VIOS didn't come up even after waiting for an hour")
    except HmcError as install_error:
        return False, repr(install_error), None

    return changed, vios_property, None


def perform_task(module):
    params = module.params
    actions = {
        "facts": fetchViosInfo,
        "present": createVios,
        "install": installVios
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
        nimIP=dict(type='str'),
        gateway=dict(type='str'),
        viosIP=dict(type='str'),
        prof_name=dict(type='str'),
        nw_type=dict(type='str'),
        location_code=dict(type='str'),
        sub_mask=dict(type='str'),
        vlanID=dict(type='str'),
        vlanPrio=dict(type='str'),
        state=dict(type='str', choices=['facts', 'present']),
        action=dict(type='str', choices=['install']),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=[('state', 'action')],
        required_one_of=[('state', 'action')],
        required_if=[['state', 'facts', ['hmc_host', 'hmc_auth', 'system_name', 'name']],
                     ['state', 'present', ['hmc_host', 'hmc_auth', 'system_name', 'name']],
                     ['action', 'install', ['hmc_host', 'hmc_auth', 'system_name', 'name', 'nimIP', 'gateway', 'viosIP', 'sub_mask']],
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
