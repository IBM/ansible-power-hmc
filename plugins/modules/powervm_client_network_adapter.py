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
module: powervm_client_network_adapter
author:
    - Navinakumar Kandakur (@nkandak1)
short_description: Create, update, delete, and query Client Network Adapters (CNAs) on PowerVM logical partitions and Virtual I/O Servers
notes:
    - This module uses the HMC REST API and requires a password for authentication.
      Passwordless authentication is not supported.
    - A Client Network Adapter (CNA) allows logical partitions and Virtual I/O Servers
      to communicate with each other without assigning physical hardware to the partitions.
    - When I(vios_name) is used with I(state=updated), I(state=absent), or
      I(state=detach_virtual_network), the target VIOS must be in the
      C(not activated) (shut-down) state. The module will fail if the VIOS is
      running, because the HMC does not allow CNA modifications on a running VIOS.
description:
    - Creates a Client Network Adapter on a logical partition or VIOS and attaches it to a virtual network.
    - Updates settings of an existing Client Network Adapter such as MAC address, QoS, and 802.1Qbg settings.
    - Retrieves information about Client Network Adapters attached to a logical partition or VIOS.
    - Deletes a Client Network Adapter from a logical partition or VIOS.
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
                    - Required for this module. Passwordless authentication is not
                      supported because all operations use the HMC REST API.
                required: true
                type: str
    system_name:
        description:
            - The name or MTMS (machine type model serial) of the managed system.
        required: true
        type: str
    vm_name:
        description:
            - The name of the logical partition to which the CNA belongs.
            - Mutually exclusive with I(vios_name).
            - One of I(vm_name) or I(vios_name) is required for all states.
        type: str
    vios_name:
        description:
            - The name of the Virtual I/O Server to which the CNA belongs.
            - Mutually exclusive with I(vm_name).
            - When used with I(state=updated), I(state=absent), or
              I(state=detach_virtual_network), the VIOS must be shut down
              (C(not activated) state). The module fails if the VIOS is running.
            - One of I(vm_name) or I(vios_name) is required for all states.
        type: str
    virtual_network_name:
        description:
            - The name of the virtual network to attach to the CNA.
            - Required when I(state=present).
            - Optional when I(state=facts). If provided, filters results to CNAs associated
              with that virtual network.
            - Mutually exclusive with I(virtual_ethernet_adapter_id) when I(state=facts).
            - Not used when I(state=updated) or I(state=absent).
        type: str
    virtual_ethernet_adapter_id:
        description:
            - The virtual slot number to assign to the CNA.
            - Optional when I(state=present). If not specified the HMC assigns one automatically.
            - Required when I(state=updated) or I(state=absent). Identifies the adapter to modify
              or delete.
            - Optional when I(state=facts). If provided, filters results to the CNA on that slot.
            - Mutually exclusive with I(virtual_network_name) when I(state=facts).
        type: int
    mac_address:
        description:
            - The MAC address to assign to the adapter.
            - Optional when I(state=updated).
            - Use colon-separated format, e.g., C(B6:08:90:7C:A6:08).
        type: str
    os_mac_address_restrictions:
        description:
            - Controls which MAC addresses the operating system is allowed to use on the adapter.
            - C(allow_all) permits any MAC address.
            - C(deny_all) blocks all OS MAC addresses.
            - C(allow_specified) permits only the addresses listed in I(allowed_os_mac_addresses).
            - Optional when I(state=updated).
        type: str
        choices: ['allow_all', 'deny_all', 'allow_specified']
    allowed_os_mac_addresses:
        description:
            - List of MAC addresses the OS is permitted to use on the adapter.
            - Required when I(os_mac_address_restrictions=allow_specified).
            - Each entry should be in colon-separated format, e.g., C(B6:08:90:7C:A6:08).
            - Optional when I(state=updated).
        type: list
        elements: str
    qos_priority_enabled:
        description:
            - Whether Quality of Service (QoS) priority is enabled on the adapter.
            - Optional when I(state=updated).
        type: bool
    qos_priority:
        description:
            - The QoS priority value for the adapter (0-7).
            - Applicable when I(qos_priority_enabled=true).
            - Optional when I(state=updated).
        type: int
    vsi_type_id:
        description:
            - The 802.1Qbg VSI Type ID for the adapter.
            - Optional when I(state=updated).
        type: int
    vsi_manager_id:
        description:
            - The 802.1Qbg VSI Manager ID for the adapter.
            - Optional when I(state=updated).
        type: int
    vsi_type_version:
        description:
            - The 802.1Qbg VSI Type Version for the adapter.
            - Optional when I(state=updated).
        type: int
    state:
        description:
            - C(present) creates a new Client Network Adapter on the logical partition or VIOS.
            - C(updated) modifies settings of an existing Client Network Adapter identified
              by I(virtual_ethernet_adapter_id). Supports updating the adapter MAC address,
              OS MAC address restrictions, QoS settings, and 802.1Qbg settings.
              Virtual network assignment cannot be changed with this state; use
              C(detach_virtual_network) and C(present) instead.
              When I(vios_name) is specified, the VIOS must be in the C(not activated)
              (shut-down) state, otherwise the module fails with an error.
            - C(absent) deletes an existing Client Network Adapter from the logical partition or VIOS.
              Requires I(virtual_ethernet_adapter_id) to identify the adapter to remove.
              When I(vios_name) is specified, the VIOS must be in the C(not activated)
              (shut-down) state, otherwise the module fails with an error.
            - C(detach_virtual_network) detaches a virtual network from an existing Client
              Network Adapter identified by I(virtual_ethernet_adapter_id). Requires both
              I(virtual_ethernet_adapter_id) and I(virtual_network_name). If the adapter has only one
              virtual network attached, the entire adapter is deleted. If the adapter has
              multiple virtual networks, the specified network's link is removed from
              C(VirtualNetworks) and its VLAN ID is stripped from C(TaggedVLANIDs).
              When I(vios_name) is specified, the VIOS must be in the C(not activated)
              (shut-down) state, otherwise the module fails with an error.
            - C(facts) retrieves information about all Client Network Adapters on the
              logical partition or VIOS. If I(virtual_network_name) is provided, filters to
              adapters connected to that virtual network. If I(virtual_ethernet_adapter_id) is provided,
              filters to the adapter on that slot. I(virtual_network_name) and
              I(virtual_ethernet_adapter_id) are mutually exclusive for this state. Either I(vm_name)
              or I(vios_name) identifies the target partition.
        required: true
        type: str
        choices: ['present', 'updated', 'absent', 'detach_virtual_network', 'facts']
'''

EXAMPLES = '''
- name: Create a Client Network Adapter on an LPAR
  ibm.power_hmc.powervm_client_network_adapter:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: '{{ system_name }}'
    vm_name: '{{ vm_name }}'
    virtual_network_name: '{{ virtual_network_name }}'
    state: present

- name: Create a Client Network Adapter with a specific virtual slot number
  ibm.power_hmc.powervm_client_network_adapter:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: '{{ system_name }}'
    vm_name: '{{ vm_name }}'
    virtual_network_name: '{{ virtual_network_name }}'
    virtual_ethernet_adapter_id: '{{ virtual_ethernet_adapter_id }}'
    state: present

- name: Get all Client Network Adapters on an LPAR
  ibm.power_hmc.powervm_client_network_adapter:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: '{{ system_name }}'
    vm_name: '{{ vm_name }}'
    state: facts

- name: Get Client Network Adapters filtered by virtual network
  ibm.power_hmc.powervm_client_network_adapter:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: '{{ system_name }}'
    vm_name: '{{ vm_name }}'
    virtual_network_name: '{{ virtual_network_name }}'
    state: facts

- name: Update CNA MAC address, MAC restrictions, QoS and 802.1Qbg settings on an LPAR
  ibm.power_hmc.powervm_client_network_adapter:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: '{{ system_name }}'
    vm_name: '{{ vm_name }}'
    virtual_ethernet_adapter_id: '{{ virtual_ethernet_adapter_id }}'
    mac_address: '{{ mac_address }}'
    os_mac_address_restrictions: '{{ os_mac_address_restrictions }}'
    allowed_os_mac_addresses: '{{ allowed_os_mac_addresses }}'
    qos_priority_enabled: '{{ qos_priority_enabled }}'
    qos_priority: '{{ qos_priority }}'
    vsi_type_id: '{{ vsi_type_id }}'
    vsi_manager_id: '{{ vsi_manager_id }}'
    vsi_type_version: '{{ vsi_type_version }}'
    state: updated

- name: Delete a Client Network Adapter from an LPAR
  ibm.power_hmc.powervm_client_network_adapter:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: '{{ system_name }}'
    vm_name: '{{ vm_name }}'
    virtual_ethernet_adapter_id: '{{ virtual_ethernet_adapter_id }}'
    state: absent

- name: Detach a virtual network from an LPAR's Client Network Adapter
  ibm.power_hmc.powervm_client_network_adapter:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: '{{ system_name }}'
    vm_name: '{{ vm_name }}'
    virtual_ethernet_adapter_id: '{{ virtual_ethernet_adapter_id }}'
    virtual_network_name: '{{ virtual_network_name }}'
    state: detach_virtual_network

- name: Update CNA MAC address, MAC restrictions, QoS and 802.1Qbg settings on a VIOS
  ibm.power_hmc.powervm_client_network_adapter:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: '{{ system_name }}'
    vios_name: '{{ vios_name }}'
    virtual_ethernet_adapter_id: '{{ virtual_ethernet_adapter_id }}'
    mac_address: '{{ mac_address }}'
    os_mac_address_restrictions: '{{ os_mac_address_restrictions }}'
    allowed_os_mac_addresses: '{{ allowed_os_mac_addresses }}'
    qos_priority_enabled: '{{ qos_priority_enabled }}'
    qos_priority: '{{ qos_priority }}'
    vsi_type_id: '{{ vsi_type_id }}'
    vsi_manager_id: '{{ vsi_manager_id }}'
    vsi_type_version: '{{ vsi_type_version }}'
    state: updated

- name: Detach a virtual network from a VIOS Client Network Adapter
  ibm.power_hmc.powervm_client_network_adapter:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: '{{ system_name }}'
    vios_name: '{{ vios_name }}'
    virtual_ethernet_adapter_id: '{{ virtual_ethernet_adapter_id }}'
    virtual_network_name: '{{ virtual_network_name }}'
    state: detach_virtual_network

- name: Get all Client Network Adapters on a VIOS
  ibm.power_hmc.powervm_client_network_adapter:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: '{{ system_name }}'
    vios_name: '{{ vios_name }}'
    state: facts

- name: Create a Client Network Adapter on a VIOS
  ibm.power_hmc.powervm_client_network_adapter:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: '{{ system_name }}'
    vios_name: '{{ vios_name }}'
    virtual_network_name: '{{ virtual_network_name }}'
    state: present

- name: Delete a Client Network Adapter from a VIOS
  ibm.power_hmc.powervm_client_network_adapter:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: '{{ system_name }}'
    vios_name: '{{ vios_name }}'
    virtual_ethernet_adapter_id: '{{ virtual_ethernet_adapter_id }}'
    state: absent
'''

RETURN = '''
client_network_adapter_info:
    description: Information about Client Network Adapters on the logical partition or VIOS.
    type: dict
    returned: on success of C(facts), C(present), C(updated), and C(detach_virtual_network) states
    contains:
        client_network_adapters:
            description: List of Client Network Adapters found on the logical partition or VIOS.
            type: list
            elements: dict
            contains:
                adapter_uuid:
                    description: Unique identifier of the Client Network Adapter.
                    type: str
                mac_address:
                    description: MAC address of the adapter (no colons, uppercase hex).
                    type: str
                virtual_ethernet_adapter_id:
                    description: Virtual slot number of the adapter.
                    type: str
                port_vlan_id:
                    description: Port VLAN ID of the adapter.
                    type: str
                virtual_switch_name:
                    description: Name of the virtual switch the adapter is attached to.
                    type: str
                virtual_switch_id:
                    description: ID of the virtual switch the adapter is attached to.
                    type: str
                virtual_network_uuid:
                    description: UUID of the virtual network the adapter is connected to.
                    type: str
                virtual_network_uuids:
                    description: List of all virtual network UUIDs attached to the adapter.
                    type: list
                    elements: str
                virtual_network_name:
                    description: Name of the virtual network the adapter is connected to.
                    type: str
                location_code:
                    description: Location code of the adapter.
                    type: str
                drc_name:
                    description: Dynamic reconfiguration connector name of the adapter.
                    type: str
                local_partition_id:
                    description: ID of the logical partition or VIOS that owns the adapter.
                    type: str
                varied_on:
                    description: Whether the adapter is varied on.
                    type: str
                required_adapter:
                    description: Whether the adapter is required.
                    type: str
                tagged_vlan_supported:
                    description: Whether tagged VLAN is supported on the adapter.
                    type: str
                tagged_vlan_ids:
                    description: Comma-separated list of tagged VLAN IDs configured on the adapter.
                    type: str
                allowed_os_mac_addresses:
                    description: OS MAC address restriction setting (ALL, NONE, or a list of addresses).
                    type: str
                qos_priority_enabled:
                    description: Whether QoS priority is enabled on the adapter.
                    type: str
                qos_priority:
                    description: QoS priority value for the adapter (0-7). Null when QoS is disabled.
                    type: str
                vsi_type_id:
                    description: VSI Type ID of the adapter. Null when not configured.
                    type: str
                vsi_manager_id:
                    description: VSI Manager ID of the adapter. Null when not configured.
                    type: str
                vsi_type_version:
                    description: VSI Type Version of the adapter. Null when not configured.
                    type: str
                hcn_id:
                    description: Host Channel Name ID of the adapter.
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
    '''Check that the input parameters satisfy the mutual exclusiveness of HMC'''
    state = params.get('state')

    if not params.get('hmc_auth', {}).get('password'):
        raise ParameterError("mandatory parameter 'password' is missing in 'hmc_auth'")

    # vm_name and vios_name are mutually exclusive across all states
    if params.get('vm_name') and params.get('vios_name'):
        raise ParameterError("parameters 'vm_name' and 'vios_name' are mutually exclusive")

    # Whichever of vm_name / vios_name is set serves as the partition identifier
    _has_partition = params.get('vm_name') or params.get('vios_name')

    _update_only = ['mac_address', 'os_mac_address_restrictions', 'allowed_os_mac_addresses',
                    'qos_priority_enabled', 'qos_priority',
                    'vsi_type_id', 'vsi_manager_id', 'vsi_type_version']

    if state == 'present':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'virtual_network_name']
        unsupportedList = _update_only
    elif state == 'updated':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'virtual_ethernet_adapter_id']
        unsupportedList = ['virtual_network_name']
    elif state == 'absent':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'virtual_ethernet_adapter_id']
        unsupportedList = ['virtual_network_name'] + _update_only
    elif state == 'detach_virtual_network':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name',
                         'virtual_ethernet_adapter_id', 'virtual_network_name']
        unsupportedList = _update_only
    elif state == 'facts':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name']
        unsupportedList = _update_only
        if params.get('virtual_network_name') and params.get('virtual_ethernet_adapter_id') is not None:
            raise ParameterError(
                "'virtual_network_name' and 'virtual_ethernet_adapter_id' are mutually exclusive "
                "when state=facts")
    else:
        mandatoryList = []
        unsupportedList = []

    collate = []
    for eachMandatory in mandatoryList:
        if not params.get(eachMandatory):
            collate.append(eachMandatory)
    # Require exactly one of vm_name / vios_name for states that operate on a partition
    if state in ('present', 'updated', 'absent', 'detach_virtual_network', 'facts') and not _has_partition:
        collate.append('vm_name or vios_name')
    if collate:
        if len(collate) == 1:
            raise ParameterError("mandatory parameter '%s' is missing" % (collate[0]))
        else:
            raise ParameterError("mandatory parameters '%s' are missing" % (','.join(collate)))

    collate = []
    for eachUnsupported in unsupportedList:
        if params.get(eachUnsupported) is not None:
            collate.append(eachUnsupported)
    if collate:
        if len(collate) == 1:
            raise ParameterError("unsupported parameter: %s" % (collate[0]))
        else:
            raise ParameterError("unsupported parameters: %s" % (', '.join(collate)))


def _vn_uuid_from_adapter(adapter_dom):
    """Extract the virtual-network UUID from the VirtualNetworks href in a CNA DOM element.

    The real API encodes the network as a link href whose last path segment is the UUID:
      <VirtualNetworks><link href=".../VirtualNetwork/<uuid>" rel="related"/></VirtualNetworks>
    Returns the UUID string, or None if not present.
    """
    links = adapter_dom.xpath(".//VirtualNetworks/link[@rel='related']")
    if links:
        href = links[0].get('href', '')
        return href.rstrip('/').split('/')[-1]
    return None


def _extract_cna_info(adapter_dom):
    """Return a flat dict of all fields from a single ClientNetworkAdapter DOM element."""
    def _text(xpath_expr):
        nodes = adapter_dom.xpath(xpath_expr)
        return nodes[0].text if nodes else None

    adapter_uuid_nodes = adapter_dom.xpath(".//Metadata/Atom/AtomID")
    adapter_uuid = adapter_uuid_nodes[0].text if adapter_uuid_nodes else None

    vn_links = adapter_dom.xpath(".//VirtualNetworks/link[@rel='related']")
    # Collect all VirtualNetwork UUIDs — a slot may have multiple networks attached
    vn_uuids = [link.get('href', '').rstrip('/').split('/')[-1] for link in vn_links]
    # Keep first UUID in the legacy scalar key for internal callers that only need one
    vn_uuid = vn_uuids[0] if vn_uuids else None

    return {
        'adapter_uuid': adapter_uuid,
        'mac_address': _text('.//MACAddress'),
        'virtual_ethernet_adapter_id': _text('.//VirtualSlotNumber'),
        'port_vlan_id': _text('.//PortVLANID'),
        'virtual_switch_name': _text('.//VirtualSwitchName'),
        'virtual_switch_id': _text('.//VirtualSwitchID'),
        'virtual_network_uuid': vn_uuid,
        'virtual_network_uuids': vn_uuids,
        'location_code': _text('.//LocationCode'),
        'drc_name': _text('.//DynamicReconfigurationConnectorName'),
        'local_partition_id': _text('.//LocalPartitionID'),
        'varied_on': _text('.//VariedOn'),
        'required_adapter': _text('.//RequiredAdapter'),
        'tagged_vlan_supported': _text('.//TaggedVLANSupported'),
        'tagged_vlan_ids': _text('.//TaggedVLANIDs'),
        'allowed_os_mac_addresses': _text('.//AllowedOperatingSystemMACAddresses'),
        'qos_priority_enabled': _text('.//QualityOfServicePriorityEnabled'),
        'qos_priority': _text('.//QualityOfServicePriority'),
        'vsi_type_id': _text('.//VirtualStationInterfaceTypeID'),
        'vsi_manager_id': _text('.//VirtualStationInterfaceManagerID'),
        'vsi_type_version': _text('.//VirtualStationInterfaceTypeVersion'),
        'hcn_id': _text('.//HCNID'),
    }


def _build_cna_result(rest_conn, lpar_uuid, adapter_uuid, system_uuid, status):
    """Re-fetch a CNA by UUID after create/update and return the full adapter_info dict.

    Calls getClientNetworkAdapters to get a fresh DOM, locates the adapter by AtomID,
    runs _extract_cna_info to populate all fields, then resolves the virtual network name
    from a getVirtualNetworks lookup — matching what the facts path returns.
    Falls back to a minimal dict if the re-fetch fails (e.g. empty body after 201).
    """
    try:
        adapters = rest_conn.getClientNetworkAdapters(lpar_uuid)
        adapter_dom = None
        for adp in (adapters or []):
            uuid_nodes = adp.xpath(".//Metadata/Atom/AtomID")
            if uuid_nodes and uuid_nodes[0].text == adapter_uuid:
                adapter_dom = adp
                break

        if adapter_dom is None:
            return {'client_network_adapters': [{'adapter_uuid': adapter_uuid, 'status': status}]}

        info = _extract_cna_info(adapter_dom)
        info['status'] = status

        # Resolve all attached virtual network UUIDs → names, joined as CSV
        vn_uuid_to_name = {}
        vn_dom = rest_conn.getVirtualNetworks(system_uuid)
        if vn_dom:
            for network in vn_dom.xpath("//VirtualNetwork"):
                name_nodes = network.xpath(".//NetworkName")
                uuid_nodes = network.xpath(".//Metadata/Atom/AtomID")
                if name_nodes and uuid_nodes:
                    vn_uuid_to_name[uuid_nodes[0].text] = name_nodes[0].text
        resolved_names = [
            vn_uuid_to_name[uuid]
            for uuid in info.get('virtual_network_uuids', [])
            if uuid in vn_uuid_to_name
        ]
        info['virtual_network_name'] = ', '.join(resolved_names) if resolved_names else None

        return {'client_network_adapters': [info]}
    except Exception:
        return {'client_network_adapters': [{'adapter_uuid': adapter_uuid, 'status': status}]}


def _resolve_system_name(module, params, hmc_host, hmc_user, password, system_name):
    '''If system_name is in MTMS format, resolve it to the logical name via the CLI.'''
    if re.match(HmcConstants.MTMS_pattern, system_name):
        hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
        hmc = Hmc(hmc_conn)
        try:
            return hmc.getSystemNameFromMTMS(system_name)
        except HmcError as error:
            error_msg = parse_error_response(error)
            module.fail_json(msg=error_msg)
    return system_name


def _get_vios_uuid(module, rest_conn, system_uuid, vios_name, require_shutdown=False):
    """Resolve a VIOS name to its UUID using the quick/All endpoint.

    Returns the UUID string, or calls module.fail_json if not found.
    When *require_shutdown* is True, also verifies that PartitionState is
    'not activated'; fails if the VIOS is in any other state.
    """
    import json as _json
    vios_response = rest_conn.getVirtualIOServersQuick(system_uuid)
    if not vios_response:
        module.fail_json(msg="No Virtual I/O Servers found on managed system")
    vios_list = _json.loads(vios_response) if isinstance(vios_response, (str, bytes)) else vios_response
    for vios in vios_list:
        if vios.get('PartitionName') == vios_name:
            if require_shutdown:
                state = vios.get('PartitionState', '')
                if state != 'not activated':
                    module.fail_json(
                        msg="VIOS '{0}' must be shut down (state: 'not activated') before "
                            "modifying, deleting, or detaching a Client Network Adapter. "
                            "Current state: '{1}'.".format(vios_name, state))
            return vios.get('UUID')
    module.fail_json(msg="Virtual I/O Server not found: {0}".format(vios_name))


def create_client_network_adapter(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    vm_name = params.get('vm_name')
    vios_name = params.get('vios_name')
    virtual_network_name = params['virtual_network_name']
    virtual_ethernet_adapter_id = params.get('virtual_ethernet_adapter_id')
    changed = False

    validate_parameters(params)
    system_name = _resolve_system_name(module, params, hmc_host, hmc_user, password, system_name)

    try:
        with HmcRestClient(hmc_host, hmc_user, password) as rest_conn:
            system_uuid, server_dom = rest_conn.getManagedSystem(system_name)
            if not system_uuid:
                module.fail_json(msg="Managed system not found: {0}".format(system_name))

            if vios_name:
                lpar_uuid = _get_vios_uuid(module, rest_conn, system_uuid, vios_name)
                partition_type = 'VirtualIOServer'
                adapters_getter = rest_conn.getViosClientNetworkAdapters
            else:
                lpar_uuid, partition_dom = rest_conn.getLogicalPartition(system_uuid, partition_name=vm_name)
                if not lpar_uuid:
                    module.fail_json(msg="Logical partition not found: {0}".format(vm_name))
                partition_type = 'LogicalPartition'
                adapters_getter = rest_conn.getClientNetworkAdapters

            # Resolve virtual network UUID
            virtual_networks_dom = rest_conn.getVirtualNetworks(system_uuid)
            if not virtual_networks_dom:
                module.fail_json(msg="No virtual networks found on system '{0}'".format(system_name))

            network_uuid = None
            vlan_id = None
            switch_href = None
            networks = virtual_networks_dom.xpath("//VirtualNetwork")
            for network in networks:
                name_nodes = network.xpath(".//NetworkName")
                if name_nodes and name_nodes[0].text == virtual_network_name:
                    uuid_nodes = network.xpath(".//Metadata/Atom/AtomID")
                    if uuid_nodes:
                        network_uuid = uuid_nodes[0].text
                    vlan_nodes = network.xpath(".//NetworkVLANID")
                    if vlan_nodes:
                        vlan_id = vlan_nodes[0].text
                    # AssociatedSwitch link href — needed for CNA creation
                    sw_links = network.xpath(".//AssociatedSwitch[@rel='related']/@href")
                    if not sw_links:
                        sw_links = network.xpath(".//AssociatedSwitch/link[@rel='related']/@href")
                    if sw_links:
                        switch_href = sw_links[0]
                    break

            if not network_uuid:
                module.fail_json(msg="Virtual network '{0}' not found on system '{1}'".format(
                    virtual_network_name, system_name))

            if vlan_id is None:
                module.fail_json(msg="Could not determine VLAN ID for virtual network '{0}'".format(
                    virtual_network_name))

            # Idempotency: exit cleanly if CNA already exists for this virtual network
            existing_adapters = adapters_getter(lpar_uuid)
            existing_slot_adapter_uuid = None
            for adapter in (existing_adapters or []):
                adapter_info = _extract_cna_info(adapter)
                # Use all attached UUIDs for the match — the target network may not be first
                network_already_on_slot = network_uuid in adapter_info.get('virtual_network_uuids', [])
                if network_already_on_slot and \
                        adapter_info.get('virtual_ethernet_adapter_id') == str(virtual_ethernet_adapter_id):
                    idempotent_uuid = adapter_info.get('adapter_uuid')
                    idempotent_info = _build_cna_result(
                        rest_conn, lpar_uuid, idempotent_uuid, system_uuid, 'already exists')
                    return False, idempotent_info, None
                if virtual_ethernet_adapter_id is not None and \
                        adapter_info.get('virtual_ethernet_adapter_id') == str(virtual_ethernet_adapter_id):
                    existing_slot_adapter_uuid = adapter_info.get('adapter_uuid')

            if existing_slot_adapter_uuid is not None:
                virtual_network_href = "https://{0}:443/rest/api/uom/ManagedSystem/{1}/VirtualNetwork/{2}".format(
                    hmc_host, system_uuid, network_uuid)
                result = rest_conn.updateClientNetworkAdapter(
                    lpar_uuid, existing_slot_adapter_uuid,
                    virtual_network_href=virtual_network_href,
                    tagged_vlan_id=vlan_id,
                    partition_type=partition_type)
                if result is not None:
                    changed = True
                    adapter_info = _build_cna_result(
                        rest_conn, lpar_uuid, existing_slot_adapter_uuid,
                        system_uuid, 'updated')
                    return changed, adapter_info, None
                module.fail_json(msg="Failed to update Client Network Adapter")

            result = rest_conn.createClientNetworkAdapter(lpar_uuid, system_uuid, network_uuid,
                                                          vlan_id, switch_href or '', virtual_ethernet_adapter_id,
                                                          partition_type=partition_type)
            if result is not None:
                changed = True
                # Re-fetch to get the adapter UUID assigned by the HMC, then build full result
                new_adapters = adapters_getter(lpar_uuid)
                new_adapter_uuid = None
                for adp in (new_adapters or []):
                    adp_info = _extract_cna_info(adp)
                    if network_uuid in adp_info.get('virtual_network_uuids', []):
                        new_adapter_uuid = adp_info.get('adapter_uuid')
                        break
                adapter_info = _build_cna_result(
                    rest_conn, lpar_uuid, new_adapter_uuid,
                    system_uuid, 'created')
            else:
                module.fail_json(msg="Failed to create Client Network Adapter")

    except (Exception, HmcError) as error:
        error_msg = parse_error_response(error)
        logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(error))
        module.fail_json(msg=error_msg)

    return changed, adapter_info, None


def get_client_network_adapters(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    vm_name = params.get('vm_name')
    vios_name = params.get('vios_name')
    virtual_network_name_filter = params.get('virtual_network_name')
    virtual_ethernet_adapter_id_filter = params.get('virtual_ethernet_adapter_id')
    changed = False

    validate_parameters(params)
    system_name = _resolve_system_name(module, params, hmc_host, hmc_user, password, system_name)

    try:
        with HmcRestClient(hmc_host, hmc_user, password) as rest_conn:
            system_uuid, server_dom = rest_conn.getManagedSystem(system_name)
            if not system_uuid:
                module.fail_json(msg="Managed system not found: {0}".format(system_name))

            if vios_name:
                lpar_uuid = _get_vios_uuid(module, rest_conn, system_uuid, vios_name)
                adapters_dom_list = rest_conn.getViosClientNetworkAdapters(lpar_uuid)
            else:
                lpar_uuid, partition_dom = rest_conn.getLogicalPartition(system_uuid, partition_name=vm_name)
                if not lpar_uuid:
                    module.fail_json(msg="Logical partition not found: {0}".format(vm_name))
                adapters_dom_list = rest_conn.getClientNetworkAdapters(lpar_uuid)
            adapters_info = []

            # Build a UUID→name map for virtual networks so facts can show network name
            vn_uuid_to_name = {}
            virtual_networks_dom = rest_conn.getVirtualNetworks(system_uuid)
            if virtual_networks_dom:
                for network in virtual_networks_dom.xpath("//VirtualNetwork"):
                    name_nodes = network.xpath(".//NetworkName")
                    uuid_nodes = network.xpath(".//Metadata/Atom/AtomID")
                    if name_nodes and uuid_nodes:
                        vn_uuid_to_name[uuid_nodes[0].text] = name_nodes[0].text

            if adapters_dom_list:
                for adapter_dom in adapters_dom_list:
                    info = _extract_cna_info(adapter_dom)
                    # Resolve all attached virtual network UUIDs → names, joined as CSV
                    resolved_names = [
                        vn_uuid_to_name[uuid]
                        for uuid in info['virtual_network_uuids']
                        if uuid in vn_uuid_to_name
                    ]
                    info['virtual_network_name'] = ', '.join(resolved_names) if resolved_names else None

                    if virtual_network_name_filter and \
                            virtual_network_name_filter not in resolved_names:
                        continue

                    if virtual_ethernet_adapter_id_filter is not None and \
                            info.get('virtual_ethernet_adapter_id') != str(virtual_ethernet_adapter_id_filter):
                        continue

                    adapters_info.append(info)

            adapter_info = {'client_network_adapters': adapters_info}

    except (Exception, HmcError) as error:
        error_msg = parse_error_response(error)
        logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(error))
        module.fail_json(msg=error_msg)

    return changed, adapter_info, None


def update_client_network_adapter(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    vm_name = params.get('vm_name')
    vios_name = params.get('vios_name')
    virtual_ethernet_adapter_id = params['virtual_ethernet_adapter_id']
    mac_address = params.get('mac_address')
    os_mac_restrictions = params.get('os_mac_address_restrictions')
    allowed_os_macs = params.get('allowed_os_mac_addresses')
    qos_priority_enabled = params.get('qos_priority_enabled')
    qos_priority = params.get('qos_priority')
    vsi_type_id = params.get('vsi_type_id')
    vsi_manager_id = params.get('vsi_manager_id')
    vsi_type_version = params.get('vsi_type_version')
    changed = False

    validate_parameters(params)

    # Validate allow_specified requires at least one MAC address
    if os_mac_restrictions == 'allow_specified' and not allowed_os_macs:
        module.fail_json(
            msg="'allowed_os_mac_addresses' is required when "
                "'os_mac_address_restrictions' is 'allow_specified'")

    if os_mac_restrictions in ['allow_all', 'deny_all'] and allowed_os_macs:
        module.fail_json(
            msg="'allowed_os_mac_addresses' is supported only when "
                "'os_mac_address_restrictions' is 'allow_specified'")

    # Map friendly choice names to the API values
    _mac_restriction_map = {
        'allow_all': 'ALL',
        'deny_all': 'NONE',
        'allow_specified': ' '.join(allowed_os_macs) if allowed_os_macs else None,
    }
    allowed_os_mac_api_value = _mac_restriction_map.get(os_mac_restrictions) if os_mac_restrictions else None

    system_name = _resolve_system_name(module, params, hmc_host, hmc_user, password, system_name)

    try:
        with HmcRestClient(hmc_host, hmc_user, password) as rest_conn:
            system_uuid, server_dom = rest_conn.getManagedSystem(system_name)
            if not system_uuid:
                module.fail_json(msg="Managed system not found: {0}".format(system_name))

            if vios_name:
                lpar_uuid = _get_vios_uuid(module, rest_conn, system_uuid, vios_name,
                                           require_shutdown=True)
                partition_label = vios_name
                partition_type = 'VirtualIOServer'
                adapters_dom_list = rest_conn.getViosClientNetworkAdapters(lpar_uuid)
            else:
                lpar_uuid, partition_dom = rest_conn.getLogicalPartition(system_uuid, partition_name=vm_name)
                if not lpar_uuid:
                    module.fail_json(msg="Logical partition not found: {0}".format(vm_name))
                partition_label = vm_name
                partition_type = 'LogicalPartition'
                adapters_dom_list = rest_conn.getClientNetworkAdapters(lpar_uuid)

            # Locate the existing CNA by virtual slot number
            adapter_uuid = None
            current_adapter = None
            for adapter_dom in (adapters_dom_list or []):
                info = _extract_cna_info(adapter_dom)
                if info.get('virtual_ethernet_adapter_id') == str(virtual_ethernet_adapter_id):
                    current_adapter = info
                    adapter_uuid = info.get('adapter_uuid')
                    break

            if not adapter_uuid:
                module.fail_json(
                    msg="Client Network Adapter on slot '{0}' not found "
                        "on partition '{1}'".format(virtual_ethernet_adapter_id, partition_label))

            # TC3 guard: setting qos_priority requires QoS to be enabled — either
            # currently enabled on the adapter, or explicitly enabled in this call.
            if qos_priority is not None:
                qos_will_be_enabled = (
                    qos_priority_enabled is True
                    or (qos_priority_enabled is None
                        and current_adapter.get('qos_priority_enabled') == 'true')
                )
                if not qos_will_be_enabled:
                    module.fail_json(
                        msg="qos_priority cannot be set when QoS priority is not enabled. "
                            "Set qos_priority_enabled: true together with qos_priority.")

            requested_updates = {
                'mac_address': mac_address.replace(':', '').upper() if mac_address is not None else None,
                'allowed_os_mac_addresses': allowed_os_mac_api_value,
                'qos_priority_enabled': 'true' if qos_priority_enabled else 'false' if qos_priority_enabled is not None else None,
                'qos_priority': str(qos_priority) if qos_priority is not None else None,
                'vsi_type_id': str(vsi_type_id) if vsi_type_id is not None else None,
                'vsi_manager_id': str(vsi_manager_id) if vsi_manager_id is not None else None,
                'vsi_type_version': str(vsi_type_version) if vsi_type_version is not None else None,
            }

            if all(
                    value is None or current_adapter.get(key) == value
                    for key, value in requested_updates.items()):
                idempotent_info = _build_cna_result(
                    rest_conn, lpar_uuid, adapter_uuid, system_uuid, 'already updated')
                return False, idempotent_info, None

            result = rest_conn.updateClientNetworkAdapter(
                lpar_uuid, adapter_uuid,
                mac_address=mac_address,
                allowed_os_mac_addresses=allowed_os_mac_api_value,
                qos_priority_enabled=qos_priority_enabled,
                qos_priority=qos_priority,
                vsi_type_id=vsi_type_id,
                vsi_manager_id=vsi_manager_id,
                vsi_type_version=vsi_type_version,
                partition_type=partition_type)

            if result is not None:
                changed = True
                adapter_info = _build_cna_result(
                    rest_conn, lpar_uuid, adapter_uuid,
                    system_uuid, 'updated')
            else:
                module.fail_json(msg="Failed to update Client Network Adapter")

    except (Exception, HmcError) as error:
        error_msg = parse_error_response(error)
        logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(error))
        module.fail_json(msg=error_msg)

    return changed, adapter_info, None


def delete_client_network_adapter(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    vm_name = params.get('vm_name')
    vios_name = params.get('vios_name')
    virtual_ethernet_adapter_id = params['virtual_ethernet_adapter_id']
    changed = False

    validate_parameters(params)
    system_name = _resolve_system_name(module, params, hmc_host, hmc_user, password, system_name)

    try:
        with HmcRestClient(hmc_host, hmc_user, password) as rest_conn:
            system_uuid, server_dom = rest_conn.getManagedSystem(system_name)
            if not system_uuid:
                module.fail_json(msg="Managed system not found: {0}".format(system_name))

            if vios_name:
                lpar_uuid = _get_vios_uuid(module, rest_conn, system_uuid, vios_name,
                                           require_shutdown=True)
                partition_label = vios_name
                partition_type = 'VirtualIOServer'
                adapters_dom_list = rest_conn.getViosClientNetworkAdapters(lpar_uuid)
            else:
                lpar_uuid, partition_dom = rest_conn.getLogicalPartition(system_uuid, partition_name=vm_name)
                if not lpar_uuid:
                    module.fail_json(msg="Logical partition not found: {0}".format(vm_name))
                partition_label = vm_name
                partition_type = 'LogicalPartition'
                adapters_dom_list = rest_conn.getClientNetworkAdapters(lpar_uuid)

            adapter_uuid = None

            for adapter_dom in (adapters_dom_list or []):
                adapter_info = _extract_cna_info(adapter_dom)
                if adapter_info.get('virtual_ethernet_adapter_id') == str(virtual_ethernet_adapter_id):
                    adapter_uuid = adapter_info.get('adapter_uuid')
                    break

            if not adapter_uuid:
                module.exit_json(
                    changed=False,
                    msg="Client Network Adapter on slot '{0}' not found "
                        "on partition '{1}'".format(virtual_ethernet_adapter_id, partition_label))

            rest_conn.deleteClientNetworkAdapter(lpar_uuid, adapter_uuid,
                                                 partition_type=partition_type)
            changed = True
            adapter_info = {
                'virtual_ethernet_adapter_id': virtual_ethernet_adapter_id,
                'partition_name': partition_label,
                'status': 'deleted'
            }

    except (Exception, HmcError) as error:
        error_msg = parse_error_response(error)
        logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(error))
        module.fail_json(msg=error_msg)

    return changed, adapter_info, None


def detach_virtual_network(module, params):
    """Detach a named virtual network from the CNA on the specified virtual slot.

    Decision tree:
      - Adapter not found on slot      → idempotent exit (changed=False)
      - Network not attached to slot   → idempotent exit (changed=False)
      - Adapter has exactly 1 network  → delete the whole adapter (absent path)
      - Adapter has 2+ networks        → GET→modify (remove link + strip VLAN)→POST
    """
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    vm_name = params.get('vm_name')
    vios_name = params.get('vios_name')
    virtual_ethernet_adapter_id = params['virtual_ethernet_adapter_id']
    virtual_network_name = params['virtual_network_name']
    changed = False

    validate_parameters(params)
    system_name = _resolve_system_name(module, params, hmc_host, hmc_user, password, system_name)

    try:
        with HmcRestClient(hmc_host, hmc_user, password) as rest_conn:
            system_uuid, _server_dom = rest_conn.getManagedSystem(system_name)
            if not system_uuid:
                module.fail_json(msg="Managed system not found: {0}".format(system_name))

            if vios_name:
                lpar_uuid = _get_vios_uuid(module, rest_conn, system_uuid, vios_name,
                                           require_shutdown=True)
                partition_label = vios_name
                partition_type = 'VirtualIOServer'
                adapters_dom_list = rest_conn.getViosClientNetworkAdapters(lpar_uuid)
            else:
                lpar_uuid, _partition_dom = rest_conn.getLogicalPartition(system_uuid, partition_name=vm_name)
                if not lpar_uuid:
                    module.fail_json(msg="Logical partition not found: {0}".format(vm_name))
                partition_label = vm_name
                partition_type = 'LogicalPartition'
                adapters_dom_list = rest_conn.getClientNetworkAdapters(lpar_uuid)

            # Resolve the target virtual network UUID and VLAN ID
            virtual_networks_dom = rest_conn.getVirtualNetworks(system_uuid)
            if not virtual_networks_dom:
                module.fail_json(msg="No virtual networks found on system '{0}'".format(system_name))

            network_uuid = None
            vlan_id = None
            for network in virtual_networks_dom.xpath("//VirtualNetwork"):
                name_nodes = network.xpath(".//NetworkName")
                if name_nodes and name_nodes[0].text == virtual_network_name:
                    uuid_nodes = network.xpath(".//Metadata/Atom/AtomID")
                    if uuid_nodes:
                        network_uuid = uuid_nodes[0].text
                    vlan_nodes = network.xpath(".//NetworkVLANID")
                    if vlan_nodes:
                        vlan_id = vlan_nodes[0].text
                    break

            if not network_uuid:
                module.fail_json(msg="Virtual network '{0}' not found on system '{1}'".format(
                    virtual_network_name, system_name))

            # Find the CNA on the requested slot
            adapter_uuid = None
            adapter_info = None
            for adapter_dom in (adapters_dom_list or []):
                info = _extract_cna_info(adapter_dom)
                if info.get('virtual_ethernet_adapter_id') == str(virtual_ethernet_adapter_id):
                    adapter_uuid = info.get('adapter_uuid')
                    adapter_info = info
                    break

            # Idempotency: no CNA on this slot at all
            if not adapter_uuid:
                return False, {
                    'client_network_adapters': [],
                    'msg': "No Client Network Adapter found on slot '{0}' of partition '{1}'".format(
                        virtual_ethernet_adapter_id, partition_label)
                }, None

            attached_uuids = adapter_info.get('virtual_network_uuids', [])

            # Idempotency: network is not attached to this slot
            if network_uuid not in attached_uuids:
                return False, {
                    'client_network_adapters': [],
                    'msg': "Virtual network '{0}' is not attached to slot '{1}' on partition '{2}'".format(
                        virtual_network_name, virtual_ethernet_adapter_id, partition_label)
                }, None

            # Single network attached → delete the whole adapter
            if len(attached_uuids) == 1:
                rest_conn.deleteClientNetworkAdapter(lpar_uuid, adapter_uuid,
                                                     partition_type=partition_type)
                changed = True
                result_info = {
                    'virtual_ethernet_adapter_id': virtual_ethernet_adapter_id,
                    'virtual_network_name': virtual_network_name,
                    'partition_name': partition_label,
                    'status': 'deleted'
                }
                return changed, result_info, None

            # Multiple networks → remove only the target link and its VLAN ID
            vn_href = "https://{0}:443/rest/api/uom/ManagedSystem/{1}/VirtualNetwork/{2}".format(
                hmc_host, system_uuid, network_uuid)
            rest_conn.updateClientNetworkAdapter(
                lpar_uuid, adapter_uuid,
                detach_vn_href=vn_href,
                detach_tagged_vlan_id=vlan_id,
                partition_type=partition_type)
            changed = True
            result_info = _build_cna_result(rest_conn, lpar_uuid, adapter_uuid, system_uuid, 'updated')
            return changed, result_info, None

    except (Exception, HmcError) as error:
        error_msg = parse_error_response(error)
        logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(error))
        module.fail_json(msg=error_msg)


def perform_task(module):
    params = module.params
    actions = {
        "present": create_client_network_adapter,
        "updated": update_client_network_adapter,
        "absent": delete_client_network_adapter,
        "detach_virtual_network": detach_virtual_network,
        "facts": get_client_network_adapters,
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
                          password=dict(required=True, type='str', no_log=True),
                      )
                      ),
        system_name=dict(type='str', required=True),
        vm_name=dict(type='str'),
        vios_name=dict(type='str'),
        virtual_network_name=dict(type='str'),
        mac_address=dict(type='str'),
        virtual_ethernet_adapter_id=dict(type='int'),
        os_mac_address_restrictions=dict(type='str',
                                         choices=['allow_all', 'deny_all', 'allow_specified']),
        allowed_os_mac_addresses=dict(type='list', elements='str'),
        qos_priority_enabled=dict(type='bool'),
        qos_priority=dict(type='int'),
        vsi_type_id=dict(type='int'),
        vsi_manager_id=dict(type='int'),
        vsi_type_version=dict(type='int'),
        state=dict(type='str', choices=['present', 'updated', 'absent', 'detach_virtual_network', 'facts'], required=True),
    )
    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=[
            ['vm_name', 'vios_name'],
        ],
        required_one_of=[
            ['vm_name', 'vios_name'],
        ],
        required_if=[
            ['state', 'present', ['virtual_network_name']],
            ['state', 'updated', ['virtual_ethernet_adapter_id']],
            ['state', 'absent', ['virtual_ethernet_adapter_id']],
            ['state', 'detach_virtual_network', ['virtual_ethernet_adapter_id', 'virtual_network_name']],
        ]
    )
    init_logger()
    changed, info, warning = perform_task(module)
    if isinstance(info, str):
        module.fail_json(msg=info)
    result = {}
    result['changed'] = changed
    if info:
        result['client_network_adapter_info'] = info
    if warning:
        result['warning'] = warning
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
