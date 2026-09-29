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
module: powervm_virtual_network
author:
    - Sreenidhi (@SreenidhiS1)
short_description: Create and manage PowerVM Virtual Networks
notes:
    - This module supports creating virtual networks and retrieving virtual network information.
    - Virtual networks are associated with virtual switches on the managed system.
description:
    - Creates a virtual network with specified configuration on the managed system.
    - Retrieves information about virtual networks on the managed system.
    - Updates the name of the virtual network on the managed system.
    - Deletes virtual networks from the managed system.
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
    network_name:
        description:
            - The name of the virtual network.
            - Required when I(state=present), I(state=absent), or I(state=updated).
            - Optional when I(state=facts). If provided, returns details for the specific network. If not provided, returns all networks.
        type: str
    network_vlan_id:
        description:
            - The VLAN ID for the virtual network.
            - Required when I(state=present).
            - Must be a valid VLAN ID between 1 and 4094 (inclusive).
        type: int
    switch_name:
        description:
            - The name of the virtual switch to associate with this network.
            - Mutually exclusive with I(switch_id).
            - Either I(switch_name) or I(switch_id) is required when I(state=present).
        type: str
    switch_id:
        description:
            - The ID of the virtual switch to associate with this network.
            - Mutually exclusive with I(switch_name).
            - Either I(switch_name) or I(switch_id) is required when I(state=present).
        type: int
    tagged_network:
        description:
            - Specifies whether the network is tagged or untagged.
            - Optional when I(state=present). Defaults to C(False) if not specified.
        type: bool
        default: false
    state:
        description:
            - C(present) creates a new virtual network.
            - C(absent) deletes an existing virtual network.
            - C(updated) updates the name of an existing virtual network.
            - C(facts) retrieves information about virtual networks. If I(network_name) is provided, returns details for that specific network only.
        required: true
        type: str
        choices: ['present', 'absent', 'updated', 'facts']
    new_network_name:
        description:
            - The new name for the virtual network when updating.
            - Required when I(state=updated).
        type: str
'''

EXAMPLES = '''
- name: Create a virtual network with switch name
  ibm.power_hmc.powervm_virtual_network:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: <managed_system_name>
    network_name: vnw-lp02
    network_vlan_id: 101
    switch_name: ETHERNET0
    tagged_network: false
    state: present

- name: Create a virtual network with switch ID
  ibm.power_hmc.powervm_virtual_network:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: <managed_system_name>
    network_name: vnw-lp03
    network_vlan_id: 102
    switch_id: 0
    tagged_network: true
    state: present

- name: Update a virtual network name
  ibm.power_hmc.powervm_virtual_network:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: <managed_system_name>
    network_name: vnw-lp02
    new_network_name: vnw-lp02-updated
    state: updated

- name: Delete a virtual network
  ibm.power_hmc.powervm_virtual_network:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: <managed_system_name>
    network_name: vnw-lp02
    state: absent

- name: Get all virtual network facts
  ibm.power_hmc.powervm_virtual_network:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: <managed_system_name>
    state: facts

- name: Get specific virtual network facts
  ibm.power_hmc.powervm_virtual_network:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: <managed_system_name>
    network_name: vnw-lp02
    state: facts

- name: Get virtual network facts using MTMS
  ibm.power_hmc.powervm_virtual_network:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: <machine_type_model_serial>
    state: facts
'''

RETURN = '''
virtual_network_info:
    description: Information about virtual networks on the managed system.
    type: dict
    returned: on success
    sample: {
        "virtual_networks": [
            {
                "network_name": "vnw-lp02",
                "network_vlan_id": "101",
                "switch_name": "ETHERNET0",
                "switch_id": "0",
                "tagged_network": "false"
            }
        ]
    }
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
    '''Check that the input parameters satisfy the mutual exclusiveness of HMC'''
    state = params.get('state')

    if state == 'present':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'network_name', 'network_vlan_id']
        unsupportedList = ['new_network_name']
        if not params.get('switch_name') and params.get('switch_id') is None:
            raise ParameterError("Either 'switch_name' or 'switch_id' is required for present state")
        if params.get('switch_name') and params.get('switch_id') is not None:
            raise ParameterError("Parameters 'switch_name' and 'switch_id' are mutually exclusive")
        vlan_id = params.get('network_vlan_id')
        if vlan_id is not None and (vlan_id < 1 or vlan_id > 4094):
            raise ParameterError("network_vlan_id must be between 1 and 4094 (inclusive), got: %d" % vlan_id)
    elif state == 'absent':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'network_name']
        unsupportedList = ['network_vlan_id', 'switch_name', 'switch_id', 'tagged_network', 'new_network_name']
    elif state == 'updated':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'network_name', 'new_network_name']
        unsupportedList = ['network_vlan_id', 'switch_name', 'switch_id', 'tagged_network']
    elif state == 'facts':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name']
        unsupportedList = ['network_vlan_id', 'switch_name', 'switch_id', 'tagged_network', 'new_network_name']
    else:
        mandatoryList = []
        unsupportedList = []

    collate = []
    for eachMandatory in mandatoryList:
        if not params.get(eachMandatory):
            collate.append(eachMandatory)
    if collate:
        if len(collate) == 1:
            raise ParameterError("mandatory parameter '%s' is missing" % (collate[0]))
        else:
            raise ParameterError("mandatory parameters '%s' are missing" % (','.join(collate)))

    collate = []
    for eachUnsupported in unsupportedList:
        value = params.get(eachUnsupported)
        if value is not None and value is not False:
            collate.append(eachUnsupported)
    if collate:
        if len(collate) == 1:
            raise ParameterError("unsupported parameter: %s" % (collate[0]))
        else:
            raise ParameterError("unsupported parameters: %s" % (', '.join(collate)))


def extract_network_data(network):
    return {
        'network_name': network.xpath(".//NetworkName")[0].text if network.xpath(".//NetworkName") else None,
        'network_vlan_id': network.xpath(".//NetworkVLANID")[0].text if network.xpath(".//NetworkVLANID") else None,
        'switch_name': network.xpath(".//VirtualSwitchName")[0].text if network.xpath(".//VirtualSwitchName") else None,
        'switch_id': network.xpath(".//VswitchID")[0].text if network.xpath(".//VswitchID") else None,
        'tagged_network': network.xpath(".//TaggedNetwork")[0].text if network.xpath(".//TaggedNetwork") else None
    }


def create_virtual_network(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    network_name = params['network_name']
    network_vlan_id = params['network_vlan_id']
    switch_name = params.get('switch_name')
    switch_id = params.get('switch_id')
    tagged_network = params.get('tagged_network', False)
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
            existing_networks_dom = rest_conn.getVirtualNetworks(system_uuid)
            if existing_networks_dom is not None:
                network_names = existing_networks_dom.xpath("//NetworkName")
                if network_names:
                    for network in network_names:
                        if network.text == network_name:
                            module.exit_json(
                                changed=False,
                                msg="Virtual network '{0}' already exists".format(network_name))
            switch_info = {'uuid': None, 'id': None, 'name': None, 'href': None}
            virtual_switches_dom = rest_conn.getVirtualSwitches(system_uuid)
            if not virtual_switches_dom:
                module.fail_json(msg="No virtual switches found on system")
            switches = virtual_switches_dom.xpath("//VirtualSwitch")
            for switch in switches:
                name_elem = switch.xpath(".//SwitchName")
                switch_id_elem = switch.xpath(".//SwitchID")
                current_name = name_elem[0].text if name_elem else None
                current_id = switch_id_elem[0].text if switch_id_elem else None
                if (switch_name and current_name == switch_name) or \
                   (switch_id is not None and current_id == str(switch_id)):
                    uuid_elem = switch.xpath(".//Metadata/Atom/AtomID")
                    if uuid_elem:
                        switch_info['uuid'] = uuid_elem[0].text
                        switch_info['id'] = current_id
                        switch_info['name'] = current_name
                        switch_info['href'] = "https://{0}/rest/api/uom/ManagedSystem/{1}/VirtualSwitch/{2}".format(
                            rest_conn.hmc_ip, system_uuid, switch_info['uuid'])
                        break
            if not switch_info['uuid']:
                if switch_name:
                    module.fail_json(msg="Virtual switch '{0}' not found".format(switch_name))
                else:
                    module.fail_json(msg="Virtual switch with ID '{0}' not found".format(switch_id))
            if existing_networks_dom is not None:
                networks = existing_networks_dom.xpath("//VirtualNetwork")
                for network in networks:
                    net_vlan_elem = network.xpath(".//NetworkVLANID")
                    net_switch_elem = network.xpath(".//VirtualSwitchName")
                    if net_vlan_elem and net_switch_elem:
                        existing_vlan = net_vlan_elem[0].text
                        existing_switch = net_switch_elem[0].text
                        if existing_vlan == str(network_vlan_id) and existing_switch == switch_info['name']:
                            module.exit_json(
                                changed=False,
                                msg="A virtual network already exists for virtual switch '{0}' and VLAN ID {1}".format(
                                    switch_info['name'], network_vlan_id))
            result = rest_conn.createVirtualNetwork(
                system_uuid, network_name, network_vlan_id,
                switch_info['href'], switch_info['id'], switch_info['name'], tagged_network)
            if result:
                changed = True
                network_info = {
                    'network_name': network_name,
                    'network_vlan_id': network_vlan_id,
                    'switch_name': switch_info['name'],
                    'switch_id': switch_info['id'],
                    'tagged_network': tagged_network,
                    'status': 'created'
                }
            else:
                module.fail_json(msg="Failed to create virtual network")
    except (Exception, HmcError) as error:
        error_msg = parse_error_response(error)
        logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(error))
        module.fail_json(msg=error_msg)

    return changed, network_info, None


def get_virtual_networks(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    network_name_filter = params.get('network_name')
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
            virtual_networks_dom = rest_conn.getVirtualNetworks(system_uuid)
            networks_info = []
            if virtual_networks_dom:
                networks = virtual_networks_dom.xpath("//VirtualNetwork")
                if network_name_filter:
                    networks_info = [extract_network_data(net) for net in networks
                                     if net.xpath(".//NetworkName") and net.xpath(".//NetworkName")[0].text == network_name_filter]
                else:
                    networks_info = [extract_network_data(net) for net in networks]
            if network_name_filter and not networks_info:
                network_info = {
                    'virtual_networks': [],
                    'msg': "Virtual network '{0}' not found in system '{1}'".format(network_name_filter, system_name)
                }
            else:
                network_info = {
                    'virtual_networks': networks_info
                }
    except (Exception, HmcError) as error:
        error_msg = parse_error_response(error)
        logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(error))
        module.fail_json(msg=error_msg)

    return changed, network_info, None


def delete_virtual_network(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    network_name = params['network_name']
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
            network_uuid = None
            virtual_networks_dom = rest_conn.getVirtualNetworks(system_uuid)
            if virtual_networks_dom:
                networks = virtual_networks_dom.xpath("//VirtualNetwork")
                for network in networks:
                    network_name_elem = network.xpath(".//NetworkName")
                    if network_name_elem and network_name_elem[0].text == network_name:
                        atom_id_elem = network.xpath(".//Metadata/Atom/AtomID")
                        if atom_id_elem and len(atom_id_elem) > 0:
                            network_uuid = atom_id_elem[0].text
                            break
                        else:
                            atom_elem = network.xpath(".//Metadata/Atom")
                            if atom_elem and len(atom_elem) > 0:
                                atom_link = atom_elem[0].xpath(".//link[@rel='SELF']")
                                if atom_link:
                                    network_href = atom_link[0].get('href')
                                    network_uuid = network_href.split('/')[-1]
                                    break
            if not network_uuid:
                module.exit_json(
                    changed=False,
                    msg="Virtual network '{0}' not found".format(network_name))
            result = rest_conn.deleteVirtualNetwork(system_uuid, network_uuid)
            if result:
                changed = True
                network_info = {
                    'network_name': network_name,
                    'status': 'deleted'
                }
            else:
                module.fail_json(msg="Failed to delete virtual network")

    except (Exception, HmcError) as error:
        error_msg = parse_error_response(error)
        logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(error))
        module.fail_json(msg=error_msg)

    return changed, network_info, None


def update_virtual_network(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    network_name = params['network_name']
    new_network_name = params['new_network_name']
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
            network_uuid = None
            new_network_exists = False
            virtual_networks_dom = rest_conn.getVirtualNetworks(system_uuid)
            if virtual_networks_dom:
                networks = virtual_networks_dom.xpath("//VirtualNetwork")
                for network in networks:
                    network_name_elem = network.xpath(".//NetworkName")
                    if not network_name_elem:
                        continue
                    existing_network_name = network_name_elem[0].text
                    if existing_network_name == new_network_name:
                        new_network_exists = True
                    if existing_network_name == network_name:
                        atom_id_elem = network.xpath(".//Metadata/Atom/AtomID")
                        if atom_id_elem and len(atom_id_elem) > 0:
                            network_uuid = atom_id_elem[0].text
                        else:
                            atom_elem = network.xpath(".//Metadata/Atom")
                            if atom_elem and len(atom_elem) > 0:
                                atom_link = atom_elem[0].xpath(".//link[@rel='SELF']")
                                if atom_link:
                                    network_href = atom_link[0].get('href')
                                    network_uuid = network_href.split('/')[-1]
            if network_name == new_network_name:
                module.exit_json(
                    changed=False,
                    msg="Virtual network already has the name '{0}'".format(new_network_name))
            if not network_uuid:
                if new_network_exists:
                    module.exit_json(
                        changed=False,
                        msg="Virtual network '{0}' already exists".format(new_network_name))
                module.fail_json(
                    msg="Virtual network '{0}' does not exist".format(network_name))
            if new_network_exists:
                module.exit_json(
                    changed=False,
                    msg="Virtual network '{0}' already exists".format(new_network_name))
            result = rest_conn.updateVirtualNetwork(system_uuid, network_uuid, new_network_name)
            if result:
                changed = True
                network_info = {
                    'network_name': network_name,
                    'new_network_name': new_network_name,
                    'status': 'updated'
                }
            else:
                module.fail_json(msg="Failed to update virtual network")
    except (Exception, HmcError) as error:
        error_msg = parse_error_response(error)
        logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(error))
        module.fail_json(msg=error_msg)
    return changed, network_info, None


def perform_task(module):
    params = module.params
    actions = {
        "present": create_virtual_network,
        "absent": delete_virtual_network,
        "updated": update_virtual_network,
        "facts": get_virtual_networks,
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
        network_name=dict(type='str'),
        network_vlan_id=dict(type='int'),
        switch_name=dict(type='str'),
        switch_id=dict(type='int'),
        tagged_network=dict(type='bool', default=False),
        new_network_name=dict(type='str'),
        state=dict(type='str', choices=['present', 'absent', 'updated', 'facts'], required=True),
    )
    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=[
            ['switch_name', 'switch_id']
        ],
        required_if=[
            ['state', 'present', ['network_name', 'network_vlan_id']],
            ['state', 'absent', ['network_name']],
            ['state', 'updated', ['network_name', 'new_network_name']],
        ]
    )
    init_logger()
    changed, info, warning = perform_task(module)
    if isinstance(info, str):
        module.fail_json(msg=info)
    result = {}
    result['changed'] = changed
    if info:
        result['virtual_network_info'] = info
    if warning:
        result['warning'] = warning
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()

# Made with Bob
