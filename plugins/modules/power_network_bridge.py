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
module: power_network_bridge
author:
    - Navinakumar Kandakur (@nkandak1)
short_description: Manages a Virtual Network Bridge on an IBM Power HMC managed system

description:
    - Retrieves information about all Virtual Network Bridges on the managed system.
    - Creates a Virtual Network Bridge backed by one or two Shared Ethernet Adapters.
    - Updates an existing Virtual Network Bridge identified by I(virtual_network_name).
    - Deletes a Virtual Network Bridge identified by I(virtual_network_name).
version_added: "1.0.0"
requirements:
    - Python >= 3
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
    system_name:
        description:
            - Name of the managed system (e.g. C(hmc-zz1)).
            - Accepts an MTMS string (C(9009-42A*XXXXXXX)) as well.
        required: true
        type: str
    virtual_network_name:
        description:
            - Name of an existing untagged Virtual Network on the managed system.
            - Required when I(state=present), I(state=update), or I(state=absent).
            - The network must have C(TaggedNetwork=false) on the HMC.
            - Its VLAN ID is used as the bridge Port VLAN ID (PVID).
        type: str
    shared_ethernet_adapter:
        description:
            - Configuration block for the Virtual Network Bridge.
            - Required when I(state=present) or I(state=update).
        type: dict
        suboptions:
            load_balancing:
                description:
                    - Enable load-balancing across VIOSes.
                    - Requires I(secondary_vios) to be configured.
                type: bool
            addition_pvid:
                description:
                    - The Port VLAN ID for the secondary load group, used when
                      I(load_balancing=true).
                    - When I(load_balancing) is enabled the HMC creates a second
                      C(LoadGroup) element; this parameter sets its
                      C(PortVLANID).
                    - Must be between 1 and 4094 inclusive and must differ from
                      the primary PVID derived from I(virtual_network_name).
                    - Ignored when I(load_balancing=false).
                type: int
            jumbo_frames:
                description:
                    - Enable 9000-byte jumbo frames on the Shared Ethernet Adapter.
                    - Valid only when I(state=present)
                type: bool
            large_send:
                description:
                    - Enable TCP large-send offload on the Shared Ethernet Adapter.
                    - Valid only when I(state=present) or I(state=update).
                type: bool
            qos_mode:
                description:
                    - Quality-of-service mode on the Shared Ethernet Adapter.
                    - C(disabled) turns off QoS.
                    - C(loose) applies best-effort QoS prioritisation.
                    - C(strict) enforces strict priority queuing.
                type: str
                choices: ['disabled', 'loose', 'strict']
            primary_vios:
                description:
                    - Primary VIOS that hosts the Shared Ethernet Adapter.
                    - Required when I(state=present). Validated in code.
                type: dict
                suboptions:
                    name:
                        description:
                            - Name of the primary VIOS partition (e.g. C(VIOS-test-02)).
                            - Required when I(state=present).
                            - Not allowed when I(state=update) — the primary VIOS cannot
                              be changed after bridge creation.
                        type: str
                    backing_device:
                        description:
                            - Physical Ethernet adapter on the VIOS used as the SEA backing device
                              (e.g. C(ent2)).
                            - Required by the HMC — the SEA cannot be created without a backing device.
                            - Required when I(state=present). Can be changed via I(state=update).
                        type: str
                    high_availability_mode:
                        description:
                            - High-availability mode for the primary SEA.
                            - C(disabled) turns off HA mode.
                            - C(auto) lets the HMC choose the active SEA automatically.
                            - C(standby) keeps this SEA in standby until the active fails.
                            - Only valid when I(state=update) and the live bridge has two VIOSes
                              (C(FailoverEnabled=true)).
                        type: str
                        choices: ['disabled', 'auto', 'standby']
            secondary_vios:
                description:
                    - Secondary VIOS for SEA failover.
                    - When present on I(state=present), failover is automatically enabled.
                    - When omitted on I(state=present), the bridge is created without failover.
                    - On I(state=update), can be used to add a second VIOS to a single-VIOS bridge.
                type: dict
                suboptions:
                    name:
                        description:
                            - Name of the secondary VIOS partition (e.g. C(VIOS-test-01)).
                            - Required when I(secondary_vios) is configured for I(state=present).
                            - Required when I(state=update) while enabling load balancing or
                              adding a new secondary VIOS to an existing single-VIOS bridge.
                        type: str
                    backing_device:
                        description:
                            - Physical Ethernet adapter on the VIOS used as the secondary SEA
                              backing device (e.g. C(ent3)).
                            - Required by the HMC when I(secondary_vios) is configured.
                            - Can be changed via I(state=update).
                        type: str
                    high_availability_mode:
                        description:
                            - High-availability mode for the secondary SEA.
                            - C(disabled) turns off HA mode.
                            - C(auto) lets the HMC choose the active SEA automatically.
                            - C(standby) keeps this SEA in standby until the active fails.
                            - Only valid when I(state=update) and the live bridge has two VIOSes
                              (C(FailoverEnabled=true)).
                        type: str
                        choices: ['disabled', 'auto', 'standby']
            tagged_virtual_networks:
                description:
                    - List of load-group assignments, each mapping a LoadGroup PVID
                      to the Virtual Network names that should be linked to it.
                    - Only valid when I(state=update).
                    - "Each list entry is a single-key dict where the key is the
                      LoadGroup Port VLAN ID (integer) and the value is a list of
                      existing tagged Virtual Network names, e.g.
                      C([{72: ['vn1', 'vn2']}, {75: ['vn3']}])."
                    - Networks already linked to the target LoadGroup are silently
                      skipped (idempotent).
                    - Each Virtual Network must already exist on the managed system
                      and must have C(TaggedNetwork=true).
                type: list
                elements: dict
    state:
        description:
            - C(facts) retrieves information about all Virtual Network Bridges.
            - C(present) creates the Virtual Network Bridge if it does not already exist.
            - C(update) modifies an existing Virtual Network Bridge identified by
              I(virtual_network_name). Updatable fields are I(failover_enabled),
              I(load_balancing), I(jumbo_frames), I(large_send), I(qos_mode),
              I(addition_pvid) (when enabling load-sharing), per-VIOS
              I(high_availability_mode), and I(tagged_virtual_networks) (per
              LoadGroup, keyed by PVID).
            - C(absent) deletes the Virtual Network Bridge identified by I(virtual_network_name).
        required: true
        type: str
        choices: ['facts', 'present', 'update', 'absent']
'''

EXAMPLES = '''
- name: Get all Virtual Network Bridge facts
  ibm.power_hmc.power_network_bridge:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: <username>
      password: <password>
    system_name: <managed_system_name>
    state: facts

- name: Create a Virtual Network Bridge with failover (two VIOSes)
  ibm.power_hmc.power_network_bridge:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: <username>
      password: <password>
    system_name: <managed_system_name>
    virtual_network_name: <virtual_network_name>
    shared_ethernet_adapter:
      load_balancing: false
      jumbo_frames: false
      large_send: false
      qos_mode: loose
      primary_vios:
        name: <primary_vios_name>
        backing_device: <primary_backing_device>
      secondary_vios:
        name: <secondary_vios_name>
        backing_device: <secondary_backing_device>
    state: present

- name: Create a Virtual Network Bridge without failover (single VIOS)
  ibm.power_hmc.power_network_bridge:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: <username>
      password: <password>
    system_name: <managed_system_name>
    virtual_network_name: <virtual_network_name>
    shared_ethernet_adapter:
      primary_vios:
        name: <primary_vios_name>
        backing_device: <primary_backing_device>
    state: present

- name: Update a Virtual Network Bridge (enable load-sharing, change QoS, set HA mode)
  ibm.power_hmc.power_network_bridge:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: <username>
      password: <password>
    system_name: <managed_system_name>
    virtual_network_name: <virtual_network_name>
    shared_ethernet_adapter:
      load_balancing: true
      addition_pvid: <addition_pvid>
      jumbo_frames: false
      large_send: true
      qos_mode: loose
      primary_vios:
        high_availability_mode: auto
      secondary_vios:
        high_availability_mode: standby
    state: update

- name: Add tagged Virtual Networks to specific LoadGroups of an existing bridge
  ibm.power_hmc.power_network_bridge:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: <username>
      password: <password>
    system_name: <managed_system_name>
    virtual_network_name: <virtual_network_name>
    shared_ethernet_adapter:
      tagged_virtual_networks:
        - 72: [<tagged_vn_name_1>, <tagged_vn_name_2>]
        - 75: [<tagged_vn_name_3>]
    state: update

- name: Delete a Virtual Network Bridge
  ibm.power_hmc.power_network_bridge:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: <username>
      password: <password>
    system_name: <managed_system_name>
    virtual_network_name: <virtual_network_name>
    state: absent
'''

RETURN = '''
network_bridge_info:
    description: Information about Virtual Network Bridges on the managed system.
    type: dict
    returned: on success of C(facts), C(present), and C(update) states; not returned on C(absent)
    contains:
        network_bridges:
            description: List of Virtual Network Bridges on the managed system. Returned only on C(facts).
            type: list
            elements: dict
            contains:
                bridge_uuid:
                    description: Unique identifier of the Virtual Network Bridge.
                    type: str
                port_vlan_id:
                    description: Port VLAN ID of the primary LoadGroup (identifies the bridge).
                    type: str
                failover_enabled:
                    description: Whether SEA failover is enabled on the bridge.
                    type: str
                load_balancing_enabled:
                    description: Whether load balancing across LoadGroups is enabled.
                    type: str
                shared_ethernet_adapters:
                    description: List of Shared Ethernet Adapters backing the bridge.
                    type: list
                    elements: dict
                    contains:
                        device_name:
                            description: Device name of the Shared Ethernet Adapter on the VIOS.
                            type: str
                        backing_device_name:
                            description: Physical or virtual backing device used by the SEA.
                            type: str
                        is_primary:
                            description: Whether this SEA is the primary adapter.
                            type: str
                        jumbo_frames_enabled:
                            description: Whether jumbo frames are enabled on the SEA.
                            type: str
                        large_send:
                            description: Whether large send offload is enabled on the SEA.
                            type: str
                        qos_mode:
                            description: Quality of service mode of the SEA (disabled, loose, or strict).
                            type: str
                        high_availability_mode:
                            description: High availability mode of the SEA (disabled, auto, or standby).
                            type: str
                        port_vlan_id:
                            description: Port VLAN ID associated with the SEA.
                            type: str
                        unique_device_id:
                            description: Unique device identifier of the SEA.
                            type: str
                        assigned_vios_href:
                            description: REST href of the VIOS that owns this SEA.
                            type: str
                        location_code:
                            description: Location code of the SEA.
                            type: str
                        thread_mode_enabled:
                            description: Whether thread mode is enabled on the SEA.
                            type: str
                        trunk_adapters:
                            description: Trunk adapters belonging to this SEA.
                            type: list
                            elements: dict
                            contains:
                                device_name:
                                    description: Device name of the trunk adapter.
                                    type: str
                                virtual_slot_number:
                                    description: Virtual slot number of the trunk adapter.
                                    type: str
                                mac_address:
                                    description: MAC address of the trunk adapter (uppercase hex, no colons).
                                    type: str
                                trunk_priority:
                                    description: Trunk priority of the adapter.
                                    type: str
                                port_vlan_id:
                                    description: Port VLAN ID of the trunk adapter.
                                    type: str
                                location_code:
                                    description: Location code of the trunk adapter.
                                    type: str
                                virtual_switch_id:
                                    description: ID of the virtual switch the trunk adapter is connected to.
                                    type: str
                load_groups:
                    description: LoadGroups associated with the bridge.
                    type: list
                    elements: dict
                    contains:
                        port_vlan_id:
                            description: Port VLAN ID of the LoadGroup.
                            type: str
                        virtual_network_hrefs:
                            description: REST hrefs of the Virtual Networks linked to this LoadGroup.
                            type: list
                            elements: str
                        trunk_adapters:
                            description: Trunk adapters belonging to this LoadGroup.
                            type: list
                            elements: dict
                            contains:
                                device_name:
                                    description: Device name of the trunk adapter.
                                    type: str
                                virtual_slot_number:
                                    description: Virtual slot number of the trunk adapter.
                                    type: str
                                mac_address:
                                    description: MAC address of the trunk adapter (uppercase hex, no colons).
                                    type: str
                                trunk_priority:
                                    description: Trunk priority of the adapter.
                                    type: str
                                port_vlan_id:
                                    description: Port VLAN ID of the trunk adapter.
                                    type: str
                                location_code:
                                    description: Location code of the trunk adapter.
                                    type: str
                                virtual_switch_id:
                                    description: ID of the virtual switch the trunk adapter is connected to.
                                    type: str
        port_vlan_id:
            description: Port VLAN ID of the bridge acted on. Returned on C(present) and C(update).
            type: int
        status:
            description: Result of the operation (C(created), C(updated), or C(unchanged)).
            type: str
        failover_enabled:
            description: Whether SEA failover is enabled. Returned on C(present).
            type: bool
        load_balancing_enabled:
            description: Whether load balancing is enabled. Returned on C(present) and C(update).
            type: bool
        jumbo_frames:
            description: Whether jumbo frames are enabled on the SEA. Returned on C(present) and C(update).
            type: bool
        large_send:
            description: Whether large send offload is enabled on the SEA. Returned on C(present) and C(update).
            type: bool
        qos_mode:
            description: Quality of service mode set on the SEA. Returned on C(present) and C(update).
            type: str
        tagged_virtual_networks_added:
            description: >
                Dict mapping each LoadGroup PVID (as string) to the list of
                Virtual Network names newly linked to that LoadGroup during the
                update. Returned on C(update).
            type: dict
'''

import logging
import os
LOG_FILENAME = "/tmp/ansible_power_hmc_{0}.log".format(os.getpid())
logger = logging.getLogger(__name__)
import sys

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import parse_error_response
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import HmcRestClient
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_resource import Hmc
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_constants import HmcConstants
import re


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
    '''Validate parameters for the requested state.'''
    state = params.get('state')

    if state == 'present':
        mandatory = ['hmc_host', 'hmc_auth', 'system_name',
                     'virtual_network_name', 'shared_ethernet_adapter']
        unsupported = []

    elif state == 'update':
        mandatory = ['hmc_host', 'hmc_auth', 'system_name',
                     'virtual_network_name', 'shared_ethernet_adapter']
        unsupported = []

    elif state == 'absent':
        mandatory = ['hmc_host', 'hmc_auth', 'system_name', 'virtual_network_name']
        unsupported = ['shared_ethernet_adapter']

    elif state == 'facts':
        mandatory = ['hmc_host', 'hmc_auth', 'system_name']
        unsupported = ['virtual_network_name', 'shared_ethernet_adapter']

    else:
        mandatory = []
        unsupported = []

    collate = [k for k in mandatory if not params.get(k)]
    if collate:
        if len(collate) == 1:
            raise ParameterError("mandatory parameter '%s' is missing" % collate[0])
        raise ParameterError("mandatory parameters '%s' are missing" % ', '.join(collate))

    # shared_ethernet_adapter sub-field validation
    if state in ('present', 'update'):
        nb = params.get('shared_ethernet_adapter') or {}

        # present-only: primary_vios.name and backing_device are mandatory
        if state == 'present':
            p_vios = nb.get('primary_vios') or {}
            if not p_vios.get('name'):
                raise ParameterError(
                    "shared_ethernet_adapter.primary_vios.name is required when state=present")
            if not p_vios.get('backing_device'):
                raise ParameterError(
                    "shared_ethernet_adapter.primary_vios.backing_device is required when state=present")
            s_vios = nb.get('secondary_vios') or None
            if s_vios and not s_vios.get('name'):
                raise ParameterError(
                    "shared_ethernet_adapter.secondary_vios.name is required when secondary_vios is configured")
            if s_vios and not s_vios.get('backing_device'):
                raise ParameterError(
                    "shared_ethernet_adapter.secondary_vios.backing_device is required when secondary_vios is configured")

        # shared: qos_mode choices
        qos = nb.get('qos_mode')
        if qos is not None and qos not in ('disabled', 'loose', 'strict'):
            raise ParameterError(
                "shared_ethernet_adapter.qos_mode must be one of disabled, loose, strict; got: %s" % qos)

        # shared: addition_pvid constraints
        addition_pvid = nb.get('addition_pvid')
        if nb.get('load_balancing') and state == 'present':
            # For state=present the bridge does not exist yet so there is no
            # pre-existing failover/secondary VIOS — both fields are always required.
            if addition_pvid is None:
                raise ParameterError(
                    "shared_ethernet_adapter.addition_pvid is required when shared_ethernet_adapter.load_balancing=true")
            s_vios = nb.get('secondary_vios')
            if not s_vios or not s_vios.get('name') or not s_vios.get('backing_device'):
                raise ParameterError(
                    "shared_ethernet_adapter.secondary_vios (name and backing_device) is required when shared_ethernet_adapter.load_balancing=true")
        # For state=update these are checked at runtime in ensure_update after
        # reading the live bridge state — a bridge with failover already enabled
        # does not need secondary_vios or addition_pvid to re-enable load_balancing.
        if addition_pvid is not None and not nb.get('load_balancing', False):
            raise ParameterError(
                "shared_ethernet_adapter.addition_pvid is only valid when shared_ethernet_adapter.load_balancing=true")
        if addition_pvid is not None and not (1 <= addition_pvid <= 4094):
            raise ParameterError(
                "shared_ethernet_adapter.addition_pvid must be between 1 and 4094; got: %s" % addition_pvid)

        # high_availability_mode is unsupported for state=present
        if state == 'present':
            for vios_key in ('primary_vios', 'secondary_vios'):
                vios_cfg = nb.get(vios_key) or {}
                if vios_cfg.get('high_availability_mode') is not None:
                    raise ParameterError(
                        "unsupported parameter: shared_ethernet_adapter.%s.high_availability_mode" % vios_key)

        # update-only sub-field checks
        if state == 'update':
            # jumbo_frames cannot be changed after bridge creation
            if nb.get('jumbo_frames') is not None:
                raise ParameterError(
                    "shared_ethernet_adapter.jumbo_frames cannot be updated after bridge creation")

            # primary_vios.name is fixed at creation and cannot be changed
            primary_cfg_upd = nb.get('primary_vios') or {}
            if primary_cfg_upd.get('name') is not None:
                raise ParameterError(
                    "shared_ethernet_adapter.primary_vios.name cannot be changed after bridge creation")
            # secondary_vios.name is allowed — it is required when adding a new
            # secondary VIOS to an existing single-VIOS bridge

            # high_availability_mode choices + single-VIOS static guard
            ha_choices = ('disabled', 'auto', 'standby')
            has_secondary_vios = bool(nb.get('secondary_vios'))
            for vios_key in ('primary_vios', 'secondary_vios'):
                vios_cfg = nb.get(vios_key) or {}
                ha = vios_cfg.get('high_availability_mode')
                if ha is not None and not has_secondary_vios:
                    raise ParameterError(
                        "shared_ethernet_adapter.%s.high_availability_mode is only valid "
                        "when secondary_vios is configured (two-VIOS bridge)" % vios_key)
                if ha is not None and ha not in ha_choices:
                    raise ParameterError(
                        "shared_ethernet_adapter.%s.high_availability_mode must be one of %s; got: %s"
                        % (vios_key, ', '.join(ha_choices), ha))

        # update-only: tagged_virtual_networks
        tagged_vns = nb.get('tagged_virtual_networks')
        if tagged_vns is not None and state != 'update':
            raise ParameterError(
                "shared_ethernet_adapter.tagged_virtual_networks is only valid when state=update")
        if tagged_vns is not None:
            if not isinstance(tagged_vns, list) or len(tagged_vns) == 0:
                raise ParameterError(
                    "shared_ethernet_adapter.tagged_virtual_networks must be a non-empty list of "
                    "single-key dicts, e.g. [{72: ['vn1', 'vn2']}, {75: ['vn3']}]")
            for entry in tagged_vns:
                if not isinstance(entry, dict) or len(entry) != 1:
                    raise ParameterError(
                        "shared_ethernet_adapter.tagged_virtual_networks entries must each be a "
                        "single-key dict mapping a LoadGroup PVID to a list of VN names, "
                        "e.g. {72: ['vn1', 'vn2']}")
                pvid_key, vn_names = next(iter(entry.items()))
                # Ansible passes YAML integer keys as strings — coerce before validating
                try:
                    pvid_int = int(pvid_key)
                except (ValueError, TypeError):
                    pvid_int = None
                if pvid_int is None or not (1 <= pvid_int <= 4094):
                    raise ParameterError(
                        "shared_ethernet_adapter.tagged_virtual_networks LoadGroup PVID must be "
                        "an integer between 1 and 4094; got: %s" % pvid_key)
                if not isinstance(vn_names, list) or len(vn_names) == 0 or not all(
                        isinstance(n, str) and n.strip() for n in vn_names):
                    raise ParameterError(
                        "shared_ethernet_adapter.tagged_virtual_networks[%s] must be a "
                        "non-empty list of VN name strings" % pvid_int)

    collate = []
    for k in unsupported:
        v = params.get(k)
        if v is not None and v is not False:
            collate.append(k)
    if collate:
        if len(collate) == 1:
            raise ParameterError("unsupported parameter: %s" % collate[0])
        raise ParameterError("unsupported parameters: %s" % ', '.join(collate))


def _resolve_system_name(module, params, hmc_host, hmc_user, password):
    system_name = params['system_name']
    if re.match(HmcConstants.MTMS_pattern, system_name):
        hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
        hmc = Hmc(hmc_conn)
        try:
            system_name = hmc.getSystemNameFromMTMS(system_name)
        except HmcError as error:
            module.fail_json(msg=parse_error_response(error))
    return system_name


def _resolve_vios_uuid(module, rest_conn, system_uuid, vios_name):
    '''Resolve a VIOS partition name to its UUID.'''
    import json as _json
    response = rest_conn.getVirtualIOServersQuick(system_uuid)
    if not response:
        module.fail_json(msg="No Virtual I/O Servers found on managed system")
    vios_list = _json.loads(response) if isinstance(response, (str, bytes)) else response
    for vios in vios_list:
        if vios.get('PartitionName') == vios_name:
            return vios.get('UUID')
    module.fail_json(msg="Virtual I/O Server not found: {0}".format(vios_name))


def _extract_trunk_adapters(element):
    '''Extract TrunkAdapter list from a SharedEthernetAdapter or LoadGroup element.'''
    trunk_list = []
    for ta in element.xpath(".//TrunkAdapters/TrunkAdapter"):
        ta_data = {}
        for tag, key in [('DeviceName', 'device_name'),
                         ('VirtualSlotNumber', 'virtual_slot_number'),
                         ('MACAddress', 'mac_address'),
                         ('PortVLANID', 'port_vlan_id'),
                         ('TrunkPriority', 'trunk_priority'),
                         ('LocationCode', 'location_code'),
                         ('VirtualSwitchID', 'virtual_switch_id')]:
            elem = ta.xpath(".//" + tag)
            if elem:
                ta_data[key] = elem[0].text
        trunk_list.append(ta_data)
    return trunk_list


def _extract_bridge_data(bridge):
    '''Parse a single namespace-stripped NetworkBridge element into a dict.'''
    bridge_data = {}

    for tag, key in [('FailoverEnabled', 'failover_enabled'),
                     ('LoadBalancingEnabled', 'load_balancing_enabled'),
                     ('UniqueDeviceID', 'unique_device_id')]:
        elem = bridge.xpath(tag)
        if elem:
            bridge_data[key] = elem[0].text

    pvlan = bridge.xpath('PortVLANID')
    if pvlan:
        bridge_data['port_vlan_id'] = pvlan[0].text

    atom_id = bridge.xpath('Metadata/Atom/AtomID')
    if atom_id:
        bridge_data['bridge_uuid'] = atom_id[0].text

    seas = []
    for sea in bridge.xpath('SharedEthernetAdapters/SharedEthernetAdapter'):
        sea_data = {}
        for tag, key in [('DeviceName', 'device_name'),
                         ('PortVLANID', 'port_vlan_id'),
                         ('IsPrimary', 'is_primary'),
                         ('HighAvailabilityMode', 'high_availability_mode'),
                         ('JumboFramesEnabled', 'jumbo_frames_enabled'),
                         ('LargeSend', 'large_send'),
                         ('QualityOfServiceMode', 'qos_mode'),
                         ('ThreadModeEnabled', 'thread_mode_enabled'),
                         ('UniqueDeviceID', 'unique_device_id')]:
            elem = sea.xpath(tag)
            if elem:
                sea_data[key] = elem[0].text
        dev_name = sea.xpath('BackingDeviceChoice/EthernetBackingDevice/DeviceName')
        if dev_name:
            sea_data['backing_device_name'] = dev_name[0].text
        vios_elem = sea.xpath('AssignedVirtualIOServer')
        if vios_elem:
            sea_data['assigned_vios_href'] = vios_elem[0].get('href')
        sea_data['trunk_adapters'] = _extract_trunk_adapters(sea)
        seas.append(sea_data)
    bridge_data['shared_ethernet_adapters'] = seas

    load_groups = []
    for lg in bridge.xpath('LoadGroups/LoadGroup'):
        lg_data = {}
        pvlan_lg = lg.xpath('PortVLANID')
        if pvlan_lg:
            lg_data['port_vlan_id'] = pvlan_lg[0].text
        vn_links = [link.get('href') for link in lg.xpath('VirtualNetworks/link')]
        if vn_links:
            lg_data['virtual_network_hrefs'] = vn_links
        lg_data['trunk_adapters'] = _extract_trunk_adapters(lg)
        load_groups.append(lg_data)
    bridge_data['load_groups'] = load_groups

    return bridge_data


def facts(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']

    validate_parameters(params)
    system_name = _resolve_system_name(module, params, hmc_host, hmc_user, password)

    try:
        with HmcRestClient(hmc_host, hmc_user, password) as rest_conn:
            system_uuid, server_dom = rest_conn.getManagedSystem(system_name)
            if not system_uuid:
                module.fail_json(msg="Managed system not found: {0}".format(system_name))
            bridges_dom = rest_conn.getNetworkBridges(system_uuid)
            bridges_info = []
            if bridges_dom is not None:
                for bridge in bridges_dom.xpath("//NetworkBridge"):
                    bridges_info.append(_extract_bridge_data(bridge))
    except (Exception, HmcError) as error:
        logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(error))
        module.fail_json(msg=parse_error_response(error))

    return False, {'network_bridges': bridges_info}, None


def ensure_present(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    virtual_network_name = params['virtual_network_name']
    nb = params.get('shared_ethernet_adapter') or {}
    primary_cfg = nb.get('primary_vios') or {}
    secondary_cfg = nb.get('secondary_vios') or None
    primary_vios_name = primary_cfg.get('name')
    secondary_vios_name = secondary_cfg.get('name') if secondary_cfg else None
    load_balancing = nb.get('load_balancing') or False
    addition_pvid = nb.get('addition_pvid') if load_balancing else None
    jumbo_frames = nb.get('jumbo_frames') or False
    large_send = nb.get('large_send') if nb.get('large_send') is not None else False
    qos_mode = nb.get('qos_mode')
    failover_enabled = secondary_vios_name is not None
    p_backing = primary_cfg.get('backing_device')
    s_backing = secondary_cfg.get('backing_device') if secondary_cfg else None

    validate_parameters(params)
    system_name = _resolve_system_name(module, params, hmc_host, hmc_user, password)

    try:
        with HmcRestClient(hmc_host, hmc_user, password) as rest_conn:
            system_uuid, server_dom = rest_conn.getManagedSystem(system_name)
            if not system_uuid:
                module.fail_json(msg="Managed system not found: {0}".format(system_name))

            # Resolve VIOS names to UUIDs
            vios1_uuid = _resolve_vios_uuid(module, rest_conn, system_uuid, primary_vios_name)
            vios2_uuid = (_resolve_vios_uuid(module, rest_conn, system_uuid, secondary_vios_name)
                          if secondary_vios_name else None)
            vios1_cfg = {'backing_device': p_backing}
            vios2_cfg = ({'backing_device': s_backing}
                         if vios2_uuid else None)

            # Resolve virtual network name to UUID, validate it is untagged,
            # and derive the bridge PVID from its VLAN ID.
            virtual_network_id = None
            port_vlan_id = None
            vn_dom = rest_conn.getVirtualNetworks(system_uuid)
            if vn_dom is not None:
                for vn in vn_dom.xpath("//VirtualNetwork"):
                    name_elem = vn.xpath(".//NetworkName")
                    if not (name_elem and name_elem[0].text == virtual_network_name):
                        continue
                    vlan_elem = vn.xpath(".//NetworkVLANID")
                    if vlan_elem:
                        port_vlan_id = int(vlan_elem[0].text)
                    atom_elem = vn.xpath(".//Metadata/Atom/AtomID")
                    if atom_elem:
                        virtual_network_id = atom_elem[0].text
                    break

            if virtual_network_id is None:
                module.fail_json(msg="Virtual network '{0}' not found on system '{1}'".format(
                    virtual_network_name, system_name))

            # Idempotency: if a bridge already exists on the derived PVID, still
            # apply large_send (only post-create field) before exiting unchanged.
            bridge_uuid = None
            bridges_dom = rest_conn.getNetworkBridges(system_uuid)
            if bridges_dom is not None:
                for bridge in bridges_dom.xpath("//NetworkBridge"):
                    pvlan = bridge.xpath('PortVLANID')
                    if pvlan and pvlan[0].text == str(port_vlan_id):
                        atom_id_elem = bridge.xpath('Metadata/Atom/AtomID')
                        if atom_id_elem:
                            bridge_uuid = atom_id_elem[0].text
                        sea_update_needed = large_send is not None
                        if sea_update_needed and bridge_uuid:
                            single_bridge_dom = rest_conn.getNetworkBridge(system_uuid, bridge_uuid)
                            if single_bridge_dom is not None:
                                rest_conn.updateNetworkBridge(
                                    system_uuid, bridge_uuid, single_bridge_dom,
                                    large_send=large_send)
                        module.exit_json(
                            changed=False,
                            msg="Network bridge with port_vlan_id '{0}' already exists".format(port_vlan_id))

            # Step 1: create the bridge — jumbo_frames and qos_mode are embedded
            # directly in the CREATE payload at the correct XSD sequence positions.
            bridge_dom = rest_conn.createNetworkBridge(
                system_uuid, port_vlan_id, virtual_network_id,
                vios1_uuid, vios2_uuid, failover_enabled, load_balancing,
                vios1_cfg, vios2_cfg, addition_pvid=addition_pvid,
                jumbo_frames=jumbo_frames, qos_mode=qos_mode)
            if not bridge_dom:
                module.fail_json(msg="Failed to create network bridge")

            # Retrieve bridge UUID for the follow-up SEA update
            bridge_uuid_elem = bridge_dom.xpath("//NetworkBridge/Metadata/Atom/AtomID")
            if not bridge_uuid_elem:
                bridge_uuid_elem = bridge_dom.xpath("//AtomID")
            bridge_uuid = bridge_uuid_elem[0].text if bridge_uuid_elem else None

            # Step 2: apply large_send via follow-up POST (cannot be set at create time).
            # high_availability_mode is only settable via state=update.
            if large_send is not None and bridge_uuid:
                single_bridge_dom = rest_conn.getNetworkBridge(system_uuid, bridge_uuid)
                if single_bridge_dom is not None:
                    rest_conn.updateNetworkBridge(
                        system_uuid, bridge_uuid, single_bridge_dom,
                        large_send=large_send)

            network_bridge_info = {
                'port_vlan_id': port_vlan_id,
                'failover_enabled': failover_enabled,
                'load_balancing_enabled': load_balancing,
                'jumbo_frames': jumbo_frames,
                'large_send': large_send,
                'qos_mode': qos_mode,
                'status': 'created'
            }

    except (Exception, HmcError) as error:
        logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(error))
        module.fail_json(msg=parse_error_response(error))

    return True, network_bridge_info, None


def ensure_update(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    virtual_network_name = params['virtual_network_name']

    nb = params.get('shared_ethernet_adapter') or {}
    primary_cfg = nb.get('primary_vios') or {}
    secondary_cfg = nb.get('secondary_vios') or None
    load_balancing = nb.get('load_balancing')   # None = not specified
    addition_pvid = nb.get('addition_pvid') if load_balancing else None
    jumbo_frames = nb.get('jumbo_frames')       # None = not specified
    large_send = nb.get('large_send')           # None = not specified
    qos_mode = nb.get('qos_mode')
    # Auto-enable failover when secondary_vios name+backing_device are supplied,
    # mirroring state=present behaviour.  No user input needed or accepted.
    failover_enabled = (True if (secondary_cfg and secondary_cfg.get('name')
                                 and secondary_cfg.get('backing_device')) else None)
    tagged_virtual_networks = nb.get('tagged_virtual_networks') or []
    # Normalise: [{pvid: [names]}] → dict {int(pvid): [names]}
    # Keys may arrive as strings from YAML — coerce to int here so all
    # downstream code (DOM lookup, result dict keys) works uniformly.
    tagged_vns_by_pvid = {}
    for entry in tagged_virtual_networks:
        pvid_key, vn_names = next(iter(entry.items()))
        tagged_vns_by_pvid[int(pvid_key)] = list(vn_names)

    # high_availability_mode cannot be changed while enabling load_balancing
    if load_balancing:
        p_ha = primary_cfg.get('high_availability_mode') if primary_cfg else None
        s_ha = (secondary_cfg.get('high_availability_mode')
                if secondary_cfg else None)
        if p_ha is not None or s_ha is not None:
            module.fail_json(
                msg="high_availability_mode cannot be set when load_balancing is being enabled")

    validate_parameters(params)
    system_name = _resolve_system_name(module, params, hmc_host, hmc_user, password)

    try:
        with HmcRestClient(hmc_host, hmc_user, password) as rest_conn:
            system_uuid, server_dom = rest_conn.getManagedSystem(system_name)
            if not system_uuid:
                module.fail_json(msg="Managed system not found: {0}".format(system_name))

            # Resolve virtual_network_name → UUID + VLAN ID, then find the bridge.
            # Strategy: first try matching by bridge PortVLANID (works when an
            # untagged VN is supplied).  If that finds nothing, fall back to
            # scanning each bridge's VirtualNetworks link list for the VN UUID
            # (works when a tagged VN already assigned to a bridge is supplied).
            vn_dom = rest_conn.getVirtualNetworks(system_uuid)
            vn_uuid = None
            port_vlan_id = None
            if vn_dom is not None:
                for vn in vn_dom.xpath("//VirtualNetwork"):
                    name_elem = vn.xpath(".//NetworkName")
                    if name_elem and name_elem[0].text == virtual_network_name:
                        vlan_elem = vn.xpath(".//NetworkVLANID")
                        if vlan_elem:
                            port_vlan_id = int(vlan_elem[0].text)
                        atom_elem = vn.xpath(".//Metadata/Atom/AtomID")
                        if atom_elem:
                            vn_uuid = atom_elem[0].text
                        break
            if vn_uuid is None:
                module.fail_json(msg="Virtual network '{0}' not found on system '{1}'".format(
                    virtual_network_name, system_name))

            bridge_uuid = None
            bridges_dom = rest_conn.getNetworkBridges(system_uuid)
            if bridges_dom is not None:
                # Pass 1: match by primary PortVLANID (untagged VN case)
                for bridge in bridges_dom.xpath("//NetworkBridge"):
                    pvlan = bridge.xpath('PortVLANID')
                    if pvlan and port_vlan_id is not None and pvlan[0].text == str(port_vlan_id):
                        atom_id_elem = bridge.xpath('Metadata/Atom/AtomID')
                        if atom_id_elem:
                            bridge_uuid = atom_id_elem[0].text
                        break
                # Pass 2: match by VN UUID in any bridge's VirtualNetworks links
                # (tagged VN case — the VN is already assigned to a LoadGroup)
                if bridge_uuid is None:
                    for bridge in bridges_dom.xpath("//NetworkBridge"):
                        vn_links = bridge.xpath('.//VirtualNetworks/link')
                        if any(vn_uuid in lnk.get('href', '') for lnk in vn_links):
                            atom_id_elem = bridge.xpath('Metadata/Atom/AtomID')
                            if atom_id_elem:
                                bridge_uuid = atom_id_elem[0].text
                            break

            if not bridge_uuid:
                module.fail_json(
                    msg="Network bridge for virtual_network '{0}' not found".format(virtual_network_name))

            # Fetch the full single-bridge DOM for mutation
            bridge_dom = rest_conn.getNetworkBridge(system_uuid, bridge_uuid)
            if bridge_dom is None:
                module.fail_json(msg="Failed to retrieve bridge for update")

            # Runtime guard: check whether the bridge is a two-VIOS bridge (FailoverEnabled=true)
            nb_elem = bridge_dom.xpath("//NetworkBridge")
            live_nb = nb_elem[0] if nb_elem else None
            live_failover_elem = live_nb.xpath('FailoverEnabled') if live_nb is not None else []
            live_failover = (live_failover_elem[0].text.lower() == 'true') if live_failover_elem else False

            has_valid_secondary_vios = bool(secondary_cfg and secondary_cfg.get('name') and secondary_cfg.get('backing_device'))

            # Check if a secondary LoadGroup already exists in the live bridge DOM
            live_load_groups = live_nb.xpath('LoadGroups/LoadGroup/PortVLANID') if live_nb is not None else []
            live_has_secondary_lg = len(live_load_groups) > 1

            # If load_balancing is being enabled:
            # - On a single-VIOS bridge: secondary_vios and addition_pvid are required
            # - On a bridge that already has failover (two VIOSes): neither is needed
            if load_balancing and not live_failover and not has_valid_secondary_vios:
                module.fail_json(
                    msg="shared_ethernet_adapter.secondary_vios (name and backing_device) is required when "
                        "enabling load_balancing on a single-VIOS bridge '{0}'".format(virtual_network_name))
            if load_balancing and not live_has_secondary_lg and addition_pvid is None:
                module.fail_json(
                    msg="shared_ethernet_adapter.addition_pvid is required when enabling load_balancing "
                        "on bridge '{0}' (no secondary LoadGroup exists yet)".format(virtual_network_name))

            if not live_failover and not has_valid_secondary_vios:
                # Cannot set HA mode on a single-VIOS bridge
                for vios_key in ('primary_vios', 'secondary_vios'):
                    if (nb.get(vios_key) or {}).get('high_availability_mode') is not None:
                        module.fail_json(
                            msg="high_availability_mode cannot be set: bridge '{0}' has only one "
                                "VIOS/SEA configured (FailoverEnabled=false)".format(virtual_network_name))

            vios2_uuid = None
            if secondary_cfg and secondary_cfg.get('name') and secondary_cfg.get('backing_device'):
                vios2_uuid = _resolve_vios_uuid(module, rest_conn, system_uuid, secondary_cfg['name'])
            has_non_vn_update = any([
                load_balancing is not None,
                addition_pvid is not None,
                failover_enabled is not None,
                jumbo_frames is not None,
                large_send is not None,
                qos_mode is not None,
                bool(primary_cfg),
                bool(secondary_cfg),
            ])

            tagged_vn_ids_by_pvid = {}
            if tagged_vns_by_pvid:
                vn_dom = rest_conn.getVirtualNetworks(system_uuid)

                nb_elem_list = bridge_dom.xpath("//NetworkBridge")
                nb_el = nb_elem_list[0] if nb_elem_list else None
                existing_hrefs_by_pvid = {}
                if nb_el is not None:
                    for lg in nb_el.xpath('LoadGroups/LoadGroup'):
                        pvid_el = lg.xpath('PortVLANID')
                        lg_pvid = int(pvid_el[0].text) if pvid_el else None
                        if lg_pvid is None:
                            continue
                        vn_container = (lg.xpath('VirtualNetworks')
                                        or lg.xpath('AssociatedInternalNetwork'))
                        if vn_container:
                            existing_hrefs_by_pvid[lg_pvid] = {
                                link.get('href', '')
                                for link in vn_container[0].xpath('link')
                            }
                        else:
                            existing_hrefs_by_pvid[lg_pvid] = set()

                # Build a global VN-name → UUID lookup from the single VN DOM fetch
                vn_name_to_uuid = {}
                if vn_dom is not None:
                    for vn in vn_dom.xpath("//VirtualNetwork"):
                        name_elem = vn.xpath(".//NetworkName")
                        atom_elem = vn.xpath(".//Metadata/Atom/AtomID")
                        if name_elem and atom_elem:
                            vn_name_to_uuid[name_elem[0].text] = atom_elem[0].text

                for lg_pvid, vn_names in tagged_vns_by_pvid.items():
                    existing_hrefs = existing_hrefs_by_pvid.get(lg_pvid, set())
                    pairs = []
                    for vn_name in vn_names:
                        vn_uuid = vn_name_to_uuid.get(vn_name)
                        if vn_uuid is None:
                            module.fail_json(
                                msg="Tagged virtual network '{0}' not found on system '{1}'".format(
                                    vn_name, system_name))
                        if not any(vn_uuid in h for h in existing_hrefs):
                            pairs.append((vn_name, vn_uuid))
                    if pairs:
                        tagged_vn_ids_by_pvid[lg_pvid] = pairs

            # If nothing at all has changed, skip the POST and report unchanged.
            if not has_non_vn_update and tagged_vns_by_pvid and not tagged_vn_ids_by_pvid:
                return False, {
                    'virtual_network_name': virtual_network_name,
                    'tagged_virtual_networks_added': {},
                    'status': 'unchanged'
                }, None

            _resp, newly_added_by_pvid = rest_conn.updateNetworkBridge(
                system_uuid, bridge_uuid, bridge_dom,
                load_balancing=load_balancing,
                addition_pvid=addition_pvid,
                failover_enabled=failover_enabled,
                jumbo_frames=jumbo_frames,
                large_send=large_send,
                qos_mode=qos_mode,
                primary_vios_cfg=primary_cfg,
                secondary_vios_cfg=secondary_cfg,
                secondary_vios_uuid=vios2_uuid,
                tagged_vn_ids_by_pvid=tagged_vn_ids_by_pvid)

            network_bridge_info = {
                'virtual_network_name': virtual_network_name,
                'load_balancing_enabled': load_balancing,
                'jumbo_frames': jumbo_frames,
                'large_send': large_send,
                'qos_mode': qos_mode,
                'primary_vios': primary_cfg,
                'secondary_vios': secondary_cfg,
                'tagged_virtual_networks_added': newly_added_by_pvid,
                'status': 'updated'
            }

    except (Exception, HmcError) as error:
        logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(error))
        module.fail_json(msg=parse_error_response(error))

    return True, network_bridge_info, None


def ensure_absent(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    virtual_network_name = params['virtual_network_name']

    validate_parameters(params)
    system_name = _resolve_system_name(module, params, hmc_host, hmc_user, password)

    try:
        with HmcRestClient(hmc_host, hmc_user, password) as rest_conn:
            system_uuid, server_dom = rest_conn.getManagedSystem(system_name)
            if not system_uuid:
                module.fail_json(msg="Managed system not found: {0}".format(system_name))

            # Resolve virtual_network_name to PVID to locate the bridge.
            # Only untagged networks (TaggedNetwork=false) are valid — a tagged
            # network is not a bridge PVID and cannot be used to identify or
            # delete a NetworkBridge.
            port_vlan_id = None
            vn_dom = rest_conn.getVirtualNetworks(system_uuid)
            if vn_dom is not None:
                for vn in vn_dom.xpath("//VirtualNetwork"):
                    name_elem = vn.xpath(".//NetworkName")
                    if name_elem and name_elem[0].text == virtual_network_name:
                        tagged_elem = vn.xpath(".//TaggedNetwork")
                        if tagged_elem and tagged_elem[0].text.lower() == 'true':
                            module.fail_json(
                                msg="Virtual network '{0}' is a tagged network and cannot be used "
                                    "to identify a Network Bridge. Only untagged networks are "
                                    "valid for state=absent.".format(virtual_network_name))
                        vlan_elem = vn.xpath(".//NetworkVLANID")
                        if vlan_elem:
                            port_vlan_id = int(vlan_elem[0].text)
                        break
            if port_vlan_id is None:
                module.fail_json(msg="Virtual network '{0}' not found on system '{1}'".format(
                    virtual_network_name, system_name))

            bridge_uuid = None
            bridges_dom = rest_conn.getNetworkBridges(system_uuid)
            if bridges_dom is not None:
                for bridge in bridges_dom.xpath("//NetworkBridge"):
                    pvlan = bridge.xpath('PortVLANID')
                    if pvlan and pvlan[0].text == str(port_vlan_id):
                        atom_id_elem = bridge.xpath('Metadata/Atom/AtomID')
                        if atom_id_elem:
                            bridge_uuid = atom_id_elem[0].text
                            break

            if not bridge_uuid:
                module.exit_json(
                    changed=False,
                    msg="Network bridge for virtual_network '{0}' not found".format(virtual_network_name))

            rest_conn.deleteNetworkBridge(system_uuid, bridge_uuid)

    except (Exception, HmcError) as error:
        logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(error))
        module.fail_json(msg=parse_error_response(error))

    return True, None, None


def perform_task(module):
    params = module.params
    actions = {
        'facts': facts,
        'present': ensure_present,
        'update': ensure_update,
        'absent': ensure_absent,
    }

    if not params['hmc_auth']:
        return False, "missing credential info", None

    try:
        return actions[params['state']](module, params)
    except Exception as error:
        return False, repr(error), None


def run_module():
    vios_spec = dict(
        name=dict(type='str'),
        backing_device=dict(type='str'),
        high_availability_mode=dict(type='str', choices=['disabled', 'auto', 'standby']),
    )

    module_args = dict(
        hmc_host=dict(type='str', required=True),
        hmc_auth=dict(type='dict',
                      required=True,
                      no_log=True,
                      options=dict(
                          username=dict(required=True, type='str'),
                          password=dict(type='str', no_log=True),
                      )),
        system_name=dict(type='str', required=True),
        virtual_network_name=dict(type='str'),
        shared_ethernet_adapter=dict(
            type='dict',
            options=dict(
                load_balancing=dict(type='bool', default=None),
                addition_pvid=dict(type='int'),
                jumbo_frames=dict(type='bool', default=None),
                large_send=dict(type='bool', default=None),
                qos_mode=dict(type='str', choices=['disabled', 'loose', 'strict']),
                primary_vios=dict(type='dict', options=vios_spec),
                secondary_vios=dict(type='dict', options=vios_spec),
                tagged_virtual_networks=dict(type='list', elements='dict'),
            ),
        ),
        state=dict(type='str', required=True, choices=['facts', 'present', 'update', 'absent']),
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

    result = {'changed': changed}
    if info:
        result['network_bridge_info'] = info
    if warning:
        result['warning'] = warning

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
