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
module: powervm_virtual_switches
author:
    - Sreenidhi (@SreenidhiS1)
short_description: Create and manage PowerVM Virtual Switches
notes:
    - This module supports creating virtual switches and retrieving virtual switch information.
description:
    - Creates a virtual switch with specified configuration on the managed system.
    - Retrieves information about virtual switches on the managed system.
    - Modifies an existing virtual switch (name and/or mode).
    - Deletes an existing virtual switch.
version_added: "1.0.0"
requirements:
- Python >= 3.9
options:
    hmc_host:
        description:
            - The IP address or hostname of the HMC.
        required: true
        type: str
    hmc_auth:
        description:
            - Username and password credential of the HMC.
        required: true
        type: dict
        suboptions:
            username:
                description:
                    - Username of the HMC to log in.
                required: true
                type: str
            password:
                description:
                    - Password of the HMC.
                type: str
    system_name:
        description:
            - The name or MTMS (machine type model serial) of the managed system.
        required: true
        type: str
    virtual_switch_name:
        description:
            - The name of the virtual switch.
            - Required when I(state=present), I(state=modify), or I(state=absent).
            - Optional when I(state=facts). If provided, returns details for the specific switch. If not provided, returns all switches.
        type: str
    virtual_switch_mode:
        description:
            - The mode of the virtual switch.
            - Optional when I(state=present). Defaults to 'Veb' if not specified.
            - Optional when I(state=modify). If not provided, the current mode is retained.
        type: str
        choices: ['Veb', 'Vepa']
    new_switch_name:
        description:
            - The new name for the virtual switch when modifying.
            - Optional when I(state=modify). If not provided, the current name is retained.
            - For I(state=modify), at least one of I(virtual_switch_mode) or I(new_switch_name) must be provided.
        type: str
    state:
        description:
            - C(present) creates a new virtual switch.
            - C(modify) modifies an existing virtual switch (name and/or mode).
            - C(absent) deletes an existing virtual switch.
            - C(facts) retrieves information about virtual switches. If I(virtual_switch_name) is provided, returns details for that specific switch only.
        type: str
        choices: ['present', 'modify', 'absent', 'facts']
        default: 'facts'
'''

EXAMPLES = '''
- name: Create a virtual switch
  ibm.power_hmc.powervm_virtual_switches:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: <managed_system_name>
    virtual_switch_name: ETHERNET1
    virtual_switch_mode: Veb
    state: present

- name: Modify a virtual switch (change mode)
  ibm.power_hmc.powervm_virtual_switches:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: <managed_system_name>
    virtual_switch_name: ETHERNET1
    virtual_switch_mode: Vepa
    state: modify

- name: Modify a virtual switch (change name and mode)
  ibm.power_hmc.powervm_virtual_switches:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: <managed_system_name>
    virtual_switch_name: ETHERNET1
    new_switch_name: ETHERNET2
    virtual_switch_mode: Veb
    state: modify

- name: Delete a virtual switch
  ibm.power_hmc.powervm_virtual_switches:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: <managed_system_name>
    virtual_switch_name: ETHERNET1
    state: absent

- name: Get all virtual switch facts
  ibm.power_hmc.powervm_virtual_switches:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: <managed_system_name>
    state: facts

- name: Get specific virtual switch facts
  ibm.power_hmc.powervm_virtual_switches:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: <managed_system_name>
    virtual_switch_name: ETHERNET1
    state: facts

- name: Get virtual switch facts using MTMS
  ibm.power_hmc.powervm_virtual_switches:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: <machine_type_model_serial>
    state: facts
'''

RETURN = '''
virtual_switch_info:
    description: Information about virtual switches on the managed system.
    type: dict
    returned: on success
    contains:
        virtual_switches:
            description: List of virtual switches on the managed system.
            type: list
            elements: dict
            contains:
                switch_name:
                    description: Name of the virtual switch.
                    type: str
                switch_mode:
                    description: Mode of the virtual switch (C(Veb) or C(Vepa)).
                    type: str
                switch_id:
                    description: Unique numeric identifier of the virtual switch.
                    type: str
'''

import logging
import os
LOG_FILENAME = "/tmp/ansible_power_hmc_{0}.log".format(os.getpid())
logger = logging.getLogger(__name__)
import sys
import re
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import parse_error_response
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import HmcRestClient
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_resource import Hmc
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_constants import HmcConstants


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
    state = params['state']

    if state == 'present':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'virtual_switch_name']
        unsupportedList = ['new_switch_name']
    elif state == 'modify':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'virtual_switch_name']
        unsupportedList = []
        if not params.get('virtual_switch_mode') and not params.get('new_switch_name'):
            raise ParameterError("For modify state, at least one of 'virtual_switch_mode' or 'new_switch_name' must be provided")
    elif state == 'absent':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'virtual_switch_name']
        unsupportedList = ['virtual_switch_mode', 'new_switch_name']
    elif state == 'facts':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name']
        unsupportedList = ['virtual_switch_mode', 'new_switch_name']

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


def create_virtual_switch(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    switch_name = params['virtual_switch_name']

    switch_mode = params.get('virtual_switch_mode') or 'Veb'
    changed = False

    validate_parameters(params)

    if re.match(HmcConstants.MTMS_pattern, system_name):
        hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
        hmc = Hmc(hmc_conn)
        try:
            system_name = hmc.getSystemNameFromMTMS(system_name)
        except HmcError as error:
            error_msg = parse_error_response(error)
            module.fail_json(msg=error_msg)

    try:
        with HmcRestClient(hmc_host, hmc_user, password) as rest_conn:
            system_uuid, server_dom = rest_conn.getManagedSystem(system_name)
            if not system_uuid:
                module.fail_json(msg="Managed system not found: {0}".format(system_name))
            existing_switches = rest_conn.getVirtualSwitches(system_uuid)
            if existing_switches is not None:
                switch_names = existing_switches.xpath("//SwitchName")
                if switch_names:
                    for switch in switch_names:
                        if switch.text == switch_name:
                            module.exit_json(
                                changed=False,
                                msg="Virtual switch '{0}' already exists".format(switch_name))

            result = rest_conn.createVirtualSwitch(system_uuid, switch_name, switch_mode)
            if result:
                changed = True
                switch_info = {
                    'switch_name': switch_name,
                    'switch_mode': switch_mode,
                    'status': 'created'
                }
            else:
                module.fail_json(msg="Failed to create virtual switch")

    except (Exception, HmcError) as error:
        error_msg = parse_error_response(error)
        logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(error))
        module.fail_json(msg=error_msg)

    return changed, switch_info, None


def get_virtual_switches(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    switch_name_filter = params.get('virtual_switch_name')
    changed = False
    validate_parameters(params)

    # Handle MTMS format for system_name
    if re.match(HmcConstants.MTMS_pattern, system_name):
        hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
        hmc = Hmc(hmc_conn)
        try:
            system_name = hmc.getSystemNameFromMTMS(system_name)
        except HmcError as error:
            error_msg = parse_error_response(error)
            module.fail_json(msg=error_msg)

    try:
        with HmcRestClient(hmc_host, hmc_user, password) as rest_conn:
            system_uuid, server_dom = rest_conn.getManagedSystem(system_name)
            if not system_uuid:
                module.fail_json(msg="Managed system not found: {0}".format(system_name))

            virtual_switches_dom = rest_conn.getVirtualSwitches(system_uuid)
            switches_info = []
            if virtual_switches_dom:
                switches = virtual_switches_dom.xpath("//VirtualSwitch")
                for switch in switches:
                    switch_data = {}
                    switch_name_elem = switch.xpath(".//SwitchName")
                    if switch_name_elem:
                        switch_data['switch_name'] = switch_name_elem[0].text
                    switch_mode_elem = switch.xpath(".//SwitchMode")
                    if switch_mode_elem:
                        switch_data['switch_mode'] = switch_mode_elem[0].text
                    switch_id_elem = switch.xpath(".//SwitchID")
                    if switch_id_elem:
                        switch_data['switch_id'] = switch_id_elem[0].text
                    if switch_name_filter:
                        if switch_data.get('switch_name') == switch_name_filter:
                            switches_info.append(switch_data)
                    else:
                        switches_info.append(switch_data)

            if switch_name_filter and not switches_info:
                switch_info = {
                    'virtual_switches': [],
                    'msg': "Virtual switch '{0}' not found in system '{1}'".format(switch_name_filter, system_name)
                }
            else:
                switch_info = {
                    'virtual_switches': switches_info
                }

    except (Exception, HmcError) as error:
        error_msg = parse_error_response(error)
        logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(error))
        module.fail_json(msg=error_msg)

    return changed, switch_info, None


def modify_virtual_switch(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    switch_name = params['virtual_switch_name']
    new_switch_name = params.get('new_switch_name', switch_name)
    switch_mode = params.get('virtual_switch_mode')
    changed = False
    validate_parameters(params)

    # Handle MTMS format for system_name
    if re.match(HmcConstants.MTMS_pattern, system_name):
        hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
        hmc = Hmc(hmc_conn)
        try:
            system_name = hmc.getSystemNameFromMTMS(system_name)
        except HmcError as error:
            error_msg = parse_error_response(error)
            module.fail_json(msg=error_msg)

    try:
        with HmcRestClient(hmc_host, hmc_user, password) as rest_conn:
            system_uuid, server_dom = rest_conn.getManagedSystem(system_name)
            if not system_uuid:
                module.fail_json(msg="Managed system not found: {0}".format(system_name))
            switch_uuid, switch_id, current_mode = rest_conn.getVirtualSwitchByName(system_uuid, switch_name)
            if not switch_uuid:
                module.fail_json(msg="Virtual switch '{0}' not found".format(switch_name))
            if new_switch_name != switch_name:
                existing_switches = rest_conn.getVirtualSwitches(system_uuid)
                if existing_switches is not None:
                    switch_names = existing_switches.xpath("//SwitchName")
                    if switch_names:
                        for switch in switch_names:
                            if switch.text == new_switch_name:
                                module.fail_json(msg="Virtual switch with name '{0}' already exists. \
Cannot rename to an existing switch name.".format(new_switch_name))

            if switch_mode is None:
                switch_mode = current_mode
            if new_switch_name == switch_name and switch_mode == current_mode:
                switch_info = {
                    'switch_name': switch_name,
                    'switch_mode': switch_mode,
                    'status': 'no changes needed'
                }
                changed = False
            else:
                result = rest_conn.updateVirtualSwitch(system_uuid, switch_uuid, new_switch_name, switch_mode, switch_id)
                if result:
                    changed = True
                    switch_info = {
                        'switch_name': new_switch_name,
                        'old_switch_name': switch_name,
                        'switch_mode': switch_mode,
                        'previous_name': switch_name if new_switch_name != switch_name else None,
                        'previous_mode': current_mode if switch_mode != current_mode else None,
                        'status': 'modified'
                    }
                else:
                    module.fail_json(msg="Failed to modify virtual switch")

    except (Exception, HmcError) as error:
        error_msg = parse_error_response(error)
        logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(error))
        module.fail_json(msg=error_msg)

    return changed, switch_info, None


def delete_virtual_switch(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    switch_name = params['virtual_switch_name']
    changed = False
    validate_parameters(params)

    # Handle MTMS format for system_name
    if re.match(HmcConstants.MTMS_pattern, system_name):
        hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
        hmc = Hmc(hmc_conn)
        try:
            system_name = hmc.getSystemNameFromMTMS(system_name)
        except HmcError as error:
            error_msg = parse_error_response(error)
            module.fail_json(msg=error_msg)

    try:
        with HmcRestClient(hmc_host, hmc_user, password) as rest_conn:
            system_uuid, server_dom = rest_conn.getManagedSystem(system_name)
            if not system_uuid:
                module.fail_json(msg="Managed system not found: {0}".format(system_name))
            switch_uuid, switch_id, current_mode = rest_conn.getVirtualSwitchByName(system_uuid, switch_name)

            if not switch_uuid:
                module.exit_json(
                    changed=False,
                    msg="Virtual switch '{0}' not found".format(switch_name))
            result = rest_conn.deleteVirtualSwitch(system_uuid, switch_uuid)
            if result:
                changed = True
                switch_info = {
                    'switch_name': switch_name,
                    'status': 'deleted'
                }
            else:
                module.fail_json(msg="Failed to delete virtual switch")

    except (Exception, HmcError) as error:
        error_msg = parse_error_response(error)
        logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(error))
        module.fail_json(msg=error_msg)

    return changed, switch_info, None


def perform_task(module):
    params = module.params
    actions = {
        "present": create_virtual_switch,
        "modify": modify_virtual_switch,
        "absent": delete_virtual_switch,
        "facts": get_virtual_switches,
    }

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
        system_name=dict(type='str', required=True),
        virtual_switch_name=dict(type='str'),
        new_switch_name=dict(type='str'),
        virtual_switch_mode=dict(type='str', choices=['Veb', 'Vepa']),
        state=dict(type='str', choices=['present', 'modify', 'absent', 'facts'], default='facts'),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_if=[
            ['state', 'present', ['virtual_switch_name']],
            ['state', 'absent', ['virtual_switch_name']],
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
        if isinstance(info, dict) and 'status' in info:
            if info['status'] == 'created':
                result['msg'] = "Virtual switch '{0}' created successfully".format(info['switch_name'])
            elif info['status'] == 'deleted':
                result['msg'] = "Virtual switch '{0}' deleted successfully".format(info['switch_name'])
            elif info['status'] == 'modified':
                old_name = info.get('old_switch_name', info['switch_name'])
                result['msg'] = "Virtual switch '{0}' modified successfully".format(old_name)
            else:
                result['virtual_switch_info'] = info
        else:
            result['virtual_switch_info'] = info

    if warning:
        result['warning'] = warning

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
