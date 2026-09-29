from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
import importlib

IMPORT_MODULE = "ansible_collections.ibm.power_hmc.plugins.modules.powervm_client_network_adapter"

from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError

hmc_auth = {'username': 'hscroot', 'password': 'password_value'}


# ---------------------------------------------------------------------------
# Test data — each entry is (params_dict, expected_error_repr_string)
# ---------------------------------------------------------------------------

hmc_auth_no_pw = {'username': 'hscroot', 'password': None}

# Shared None values for all new update-only params
_update_only_none = {
    'mac_address': None,
    'os_mac_address_restrictions': None,
    'allowed_os_mac_addresses': None,
    'qos_priority_enabled': None,
    'qos_priority': None,
    'vsi_type_id': None,
    'vsi_manager_id': None,
    'vsi_type_version': None,
}

# Added to every params dict so validate_parameters sees the field
_vios_none = {'vios_name': None}

test_data_present = [
    # Missing password
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth_no_pw, 'state': 'present',
      'system_name': 'system1', 'vm_name': 'lpar1',
      'virtual_network_name': 'vnw-lp02', 'new_virtual_network_name': None,
      'virtual_ethernet_adapter_id': None, **_update_only_none, **_vios_none},
     "ParameterError: mandatory parameter 'password' is missing in 'hmc_auth'"),
    # Missing hmc_host
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'state': 'present',
      'system_name': 'system1', 'vm_name': 'lpar1',
      'virtual_network_name': 'vnw-lp02', 'new_virtual_network_name': None,
      'virtual_ethernet_adapter_id': None, **_update_only_none, **_vios_none},
     "ParameterError: mandatory parameter 'hmc_host' is missing"),
    # Missing both vm_name and vios_name
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'present',
      'system_name': 'system1', 'vm_name': None,
      'virtual_network_name': 'vnw-lp02', 'new_virtual_network_name': None,
      'virtual_ethernet_adapter_id': None, **_update_only_none, **_vios_none},
     "ParameterError: mandatory parameter 'vm_name or vios_name' is missing"),
    # Missing virtual_network_name
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'present',
      'system_name': 'system1', 'vm_name': 'lpar1',
      'virtual_network_name': None, 'new_virtual_network_name': None,
      'virtual_ethernet_adapter_id': None, **_update_only_none, **_vios_none},
     "ParameterError: mandatory parameter 'virtual_network_name' is missing"),
]

test_data_updated = [
    # Missing password
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth_no_pw, 'state': 'updated',
      'system_name': 'system1', 'vm_name': 'lpar1',
      'virtual_network_name': 'vnw-lp02', 'virtual_ethernet_adapter_id': None,
      **_update_only_none, **_vios_none},
     "ParameterError: mandatory parameter 'password' is missing in 'hmc_auth'"),
    # Missing hmc_host (also missing virtual_ethernet_adapter_id → plural error)
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'state': 'updated',
      'system_name': 'system1', 'vm_name': 'lpar1',
      'virtual_network_name': 'vnw-lp02', 'virtual_ethernet_adapter_id': None,
      **_update_only_none, **_vios_none},
     "ParameterError: mandatory parameters 'hmc_host,virtual_ethernet_adapter_id' are missing"),
    # Missing virtual_network_name (now virtual_ethernet_adapter_id is the mandatory param)
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'updated',
      'system_name': 'system1', 'vm_name': 'lpar1',
      'virtual_network_name': None, 'virtual_ethernet_adapter_id': None,
      **_update_only_none, **_vios_none},
     "ParameterError: mandatory parameter 'virtual_ethernet_adapter_id' is missing"),
    # Unsupported virtual_network_name for updated
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'updated',
      'system_name': 'system1', 'vm_name': 'lpar1',
      'virtual_network_name': 'vnw-lp02', 'virtual_ethernet_adapter_id': 3,
      **_update_only_none, **_vios_none},
     "ParameterError: unsupported parameter: virtual_network_name"),
]

test_data_absent = [
    # Missing password
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth_no_pw, 'state': 'absent',
      'system_name': 'system1', 'vm_name': 'lpar1',
      'virtual_network_name': None, 'virtual_ethernet_adapter_id': None,
      **_update_only_none, **_vios_none},
     "ParameterError: mandatory parameter 'password' is missing in 'hmc_auth'"),
    # Missing hmc_host (also missing virtual_ethernet_adapter_id → plural error)
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'state': 'absent',
      'system_name': 'system1', 'vm_name': 'lpar1',
      'virtual_network_name': None, 'virtual_ethernet_adapter_id': None,
      **_update_only_none, **_vios_none},
     "ParameterError: mandatory parameters 'hmc_host,virtual_ethernet_adapter_id' are missing"),
    # Missing virtual_ethernet_adapter_id for absent
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'absent',
      'system_name': 'system1', 'vm_name': 'lpar1',
      'virtual_network_name': None, 'virtual_ethernet_adapter_id': None,
      **_update_only_none, **_vios_none},
     "ParameterError: mandatory parameter 'virtual_ethernet_adapter_id' is missing"),
    # Unsupported virtual_network_name for absent
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'absent',
      'system_name': 'system1', 'vm_name': 'lpar1',
      'virtual_network_name': 'vnw-lp02', 'virtual_ethernet_adapter_id': 3,
      **_update_only_none, **_vios_none},
     "ParameterError: unsupported parameter: virtual_network_name"),
    # Unsupported qos_priority for absent
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'absent',
      'system_name': 'system1', 'vm_name': 'lpar1',
      'virtual_network_name': None, 'virtual_ethernet_adapter_id': 3,
      'os_mac_address_restrictions': None,
      'allowed_os_mac_addresses': None, 'qos_priority_enabled': None,
      'qos_priority': 3, 'vsi_type_id': None, 'vsi_manager_id': None,
      'vsi_type_version': None, **_vios_none},
     "ParameterError: unsupported parameter: qos_priority"),
]

test_data_facts = [
    # Missing password
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth_no_pw, 'state': 'facts',
      'system_name': 'system1', 'vm_name': 'lpar1',
      'virtual_network_name': None, 'virtual_ethernet_adapter_id': None,
      **_update_only_none, **_vios_none},
     "ParameterError: mandatory parameter 'password' is missing in 'hmc_auth'"),
    # Missing hmc_host
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'state': 'facts',
      'system_name': 'system1', 'vm_name': 'lpar1',
      'virtual_network_name': None, 'virtual_ethernet_adapter_id': None,
      **_update_only_none, **_vios_none},
     "ParameterError: mandatory parameter 'hmc_host' is missing"),
    # Missing system_name
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'facts',
      'system_name': None, 'vm_name': 'lpar1',
      'virtual_network_name': None, 'virtual_ethernet_adapter_id': None,
      **_update_only_none, **_vios_none},
     "ParameterError: mandatory parameter 'system_name' is missing"),
    # Missing both vm_name and vios_name
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'facts',
      'system_name': 'system1', 'vm_name': None,
      'virtual_network_name': None, 'virtual_ethernet_adapter_id': None,
      **_update_only_none, **_vios_none},
     "ParameterError: mandatory parameter 'vm_name or vios_name' is missing"),
    # Unsupported vsi_type_id for facts
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'facts',
      'system_name': 'system1', 'vm_name': 'lpar1',
      'virtual_network_name': None, 'virtual_ethernet_adapter_id': None,
      'os_mac_address_restrictions': None,
      'allowed_os_mac_addresses': None, 'qos_priority_enabled': None,
      'qos_priority': None, 'vsi_type_id': 10, 'vsi_manager_id': None,
      'vsi_type_version': None, **_vios_none},
     "ParameterError: unsupported parameter: vsi_type_id"),
]

test_data_mutually_exclusive = [
    # vm_name and vios_name both provided → mutual exclusion error
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'facts',
      'system_name': 'system1', 'vm_name': 'lpar1', 'vios_name': 'vios1',
      'virtual_network_name': None, 'virtual_ethernet_adapter_id': None,
      **_update_only_none},
     "ParameterError: parameters 'vm_name' and 'vios_name' are mutually exclusive"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def common_mock_setup(mocker):
    mod = importlib.import_module(IMPORT_MODULE)
    mocker.patch.object(mod, 'HmcCliConnection')
    mocker.patch.object(mod, 'Hmc', autospec=True)
    return mod


class FakeElement:
    def __init__(self, text=None, attribs=None, children=None):
        self.text = text
        self._attribs = attribs or {}
        self._children = children or {}

    def get(self, key, default=None):
        return self._attribs.get(key, default)

    def xpath(self, expr):
        return self._children.get(expr, [])


class FakeAdapterDom:
    """Simulates a ClientNetworkAdapter DOM element matching the real API XML structure.

    The real response encodes the virtual network as:
      <VirtualNetworks><link href=".../VirtualNetwork/<uuid>" rel="related"/></VirtualNetworks>
    and uses Metadata/Atom/AtomID for the adapter UUID.
    """
    def __init__(self, vn_uuid, adapter_uuid,
                 mac='4AA9B56A0E02', slot='2', pvlan='1',
                 switch_name='ETHERNET0', switch_id='0',
                 location_code='U9009.22A-V3-C2', drc_name='U9009.22A-V3-C2',
                 local_partition_id='3', allowed_os_mac_addresses=None,
                 qos_priority_enabled=None, qos_priority=None,
                 vsi_type_id=None, vsi_manager_id=None, vsi_type_version=None):
        self._vn_uuid = vn_uuid
        self._uuid = adapter_uuid
        self._mac = mac
        self._slot = slot
        self._pvlan = pvlan
        self._switch_name = switch_name
        self._switch_id = switch_id
        self._location_code = location_code
        self._drc_name = drc_name
        self._local_partition_id = local_partition_id
        self._allowed_os_mac_addresses = allowed_os_mac_addresses
        self._qos_priority_enabled = qos_priority_enabled
        self._qos_priority = qos_priority
        self._vsi_type_id = vsi_type_id
        self._vsi_manager_id = vsi_manager_id
        self._vsi_type_version = vsi_type_version

    def xpath(self, expr):
        if expr == './/Metadata/Atom/AtomID':
            return [FakeElement(text=self._uuid)]
        if expr == './/VirtualNetworks/link[@rel=\'related\']':
            href = 'https://hmc/rest/api/uom/ManagedSystem/sys/VirtualNetwork/{0}'.format(
                self._vn_uuid)
            return [FakeElement(attribs={'href': href})]
        if expr == './/MACAddress':
            return [FakeElement(text=self._mac)]
        if expr == './/VirtualSlotNumber':
            return [FakeElement(text=self._slot)]
        if expr == './/PortVLANID':
            return [FakeElement(text=self._pvlan)]
        if expr == './/VirtualSwitchName':
            return [FakeElement(text=self._switch_name)]
        if expr == './/VirtualSwitchID':
            return [FakeElement(text=self._switch_id)]
        if expr == './/LocationCode':
            return [FakeElement(text=self._location_code)]
        if expr == './/DynamicReconfigurationConnectorName':
            return [FakeElement(text=self._drc_name)]
        if expr == './/LocalPartitionID':
            return [FakeElement(text=self._local_partition_id)]
        if expr == './/AllowedOperatingSystemMACAddresses':
            return [FakeElement(text=self._allowed_os_mac_addresses)] if self._allowed_os_mac_addresses is not None else []
        if expr == './/QualityOfServicePriorityEnabled':
            return [FakeElement(text=self._qos_priority_enabled)] if self._qos_priority_enabled is not None else []
        if expr == './/QualityOfServicePriority':
            return [FakeElement(text=self._qos_priority)] if self._qos_priority is not None else []
        if expr == './/VirtualStationInterfaceTypeID':
            return [FakeElement(text=self._vsi_type_id)] if self._vsi_type_id is not None else []
        if expr == './/VirtualStationInterfaceManagerID':
            return [FakeElement(text=self._vsi_manager_id)] if self._vsi_manager_id is not None else []
        if expr == './/VirtualStationInterfaceTypeVersion':
            return [FakeElement(text=self._vsi_type_version)] if self._vsi_type_version is not None else []
        if expr in ('.//VariedOn', './/RequiredAdapter', './/TaggedVLANSupported', './/HCNID'):
            return []
        return []


class FakeVnetworkDom:
    """Simulates the virtual-networks root DOM returned by getVirtualNetworks."""
    def __init__(self, networks):
        # networks: list of {'name': str, 'uuid': str, 'vlan_id': str (optional)}
        self._networks = networks

    def xpath(self, expr):
        if expr == '//VirtualNetwork':
            elems = []
            for nw in self._networks:
                vlan_nodes = [FakeElement(text=nw['vlan_id'])] if nw.get('vlan_id') else []
                elems.append(FakeElement(children={
                    './/NetworkName': [FakeElement(text=nw['name'])],
                    './/Metadata/Atom/AtomID': [FakeElement(text=nw['uuid'])],
                    './/NetworkVLANID': vlan_nodes,
                    './/AssociatedSwitch[@rel=\'related\']/@href': [],
                    './/AssociatedSwitch/link[@rel=\'related\']/@href': [],
                }))
            return elems
        return []


class DummyModule:
    def exit_json(self, **kwargs):
        raise ModuleExit(kwargs)

    def fail_json(self, **kwargs):
        raise ModuleFail(kwargs)


class ModuleExit(BaseException):
    """Mimics AnsibleModule.exit_json which calls sys.exit() — not catchable by 'except Exception'."""
    def __init__(self, kwargs):
        self.kwargs = kwargs
        super().__init__(str(kwargs))


class ModuleFail(Exception):
    def __init__(self, kwargs):
        self.kwargs = kwargs
        super().__init__(str(kwargs))


# ---------------------------------------------------------------------------
# Parametrized parameter-validation tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("test_input, expected_error", test_data_present)
def test_present_parameter_validation(mocker, test_input, expected_error):
    mod = common_mock_setup(mocker)
    with pytest.raises(ParameterError) as exc:
        mod.validate_parameters(test_input)
    assert expected_error == repr(exc.value)


@pytest.mark.parametrize("test_input, expected_error", test_data_updated)
def test_updated_parameter_validation(mocker, test_input, expected_error):
    mod = common_mock_setup(mocker)
    with pytest.raises(ParameterError) as exc:
        mod.validate_parameters(test_input)
    assert expected_error == repr(exc.value)


@pytest.mark.parametrize("test_input, expected_error", test_data_absent)
def test_absent_parameter_validation(mocker, test_input, expected_error):
    mod = common_mock_setup(mocker)
    with pytest.raises(ParameterError) as exc:
        mod.validate_parameters(test_input)
    assert expected_error == repr(exc.value)


@pytest.mark.parametrize("test_input, expected_error", test_data_facts)
def test_facts_parameter_validation(mocker, test_input, expected_error):
    mod = common_mock_setup(mocker)
    with pytest.raises(ParameterError) as exc:
        mod.validate_parameters(test_input)
    assert expected_error == repr(exc.value)


@pytest.mark.parametrize("test_input, expected_error", test_data_mutually_exclusive)
def test_mutually_exclusive_vm_vios(mocker, test_input, expected_error):
    mod = common_mock_setup(mocker)
    with pytest.raises(ParameterError) as exc:
        mod.validate_parameters(test_input)
    assert expected_error == repr(exc.value)


# ---------------------------------------------------------------------------
# Functional tests for get_client_network_adapters
# ---------------------------------------------------------------------------

def _facts_params(vn_name=None):
    return {
        'hmc_host': '0.0.0.0',
        'hmc_auth': hmc_auth,
        'state': 'facts',
        'system_name': 'system1',
        'vm_name': 'lpar1',
        'vios_name': None,
        'virtual_network_name': vn_name,
        'virtual_ethernet_adapter_id': None,
        **_update_only_none,
    }


def _fake_vnets(pairs):
    """Build a FakeVnetworkDom from a list of (name, uuid) or (name, uuid, vlan_id) tuples."""
    networks = []
    for item in pairs:
        d = {'name': item[0], 'uuid': item[1]}
        if len(item) > 2:
            d['vlan_id'] = item[2]
        else:
            d['vlan_id'] = '1'
        networks.append(d)
    return FakeVnetworkDom(networks)


def test_facts_returns_all_adapters(mocker):
    mod = common_mock_setup(mocker)
    rest_client = mocker.patch.object(mod, 'HmcRestClient', autospec=True)
    rest_conn = rest_client.return_value.__enter__.return_value
    rest_conn.getManagedSystem.return_value = ('sys-uuid', object())
    rest_conn.getLogicalPartition.return_value = ('lpar-uuid', object())
    rest_conn.getVirtualNetworks.return_value = _fake_vnets([
        ('vnw-lp02', 'net-uuid-1'),
        ('vnw-lp03', 'net-uuid-2'),
    ])
    rest_conn.getClientNetworkAdapters.return_value = [
        FakeAdapterDom(vn_uuid='net-uuid-1', adapter_uuid='cna-uuid-1'),
        FakeAdapterDom(vn_uuid='net-uuid-2', adapter_uuid='cna-uuid-2'),
    ]

    module = DummyModule()
    changed, info, warning = mod.get_client_network_adapters(module, _facts_params())

    assert changed is False
    assert warning is None
    adapters = info['client_network_adapters']
    assert len(adapters) == 2
    assert adapters[0]['virtual_network_name'] == 'vnw-lp02'
    assert adapters[0]['mac_address'] == '4AA9B56A0E02'
    assert adapters[0]['adapter_uuid'] == 'cna-uuid-1'
    assert adapters[0]['virtual_network_uuid'] == 'net-uuid-1'
    assert adapters[0]['virtual_switch_name'] == 'ETHERNET0'
    assert adapters[1]['virtual_network_name'] == 'vnw-lp03'


def test_facts_filters_by_virtual_network_name(mocker):
    mod = common_mock_setup(mocker)
    rest_client = mocker.patch.object(mod, 'HmcRestClient', autospec=True)
    rest_conn = rest_client.return_value.__enter__.return_value
    rest_conn.getManagedSystem.return_value = ('sys-uuid', object())
    rest_conn.getLogicalPartition.return_value = ('lpar-uuid', object())
    rest_conn.getVirtualNetworks.return_value = _fake_vnets([
        ('vnw-lp02', 'net-uuid-1'),
        ('vnw-lp03', 'net-uuid-2'),
    ])
    rest_conn.getClientNetworkAdapters.return_value = [
        FakeAdapterDom(vn_uuid='net-uuid-1', adapter_uuid='cna-uuid-1'),
        FakeAdapterDom(vn_uuid='net-uuid-2', adapter_uuid='cna-uuid-2'),
    ]

    module = DummyModule()
    changed, info, warning = mod.get_client_network_adapters(module, _facts_params('vnw-lp02'))

    adapters = info['client_network_adapters']
    assert len(adapters) == 1
    assert adapters[0]['virtual_network_name'] == 'vnw-lp02'
    assert adapters[0]['adapter_uuid'] == 'cna-uuid-1'


def test_facts_returns_empty_when_no_adapters(mocker):
    mod = common_mock_setup(mocker)
    rest_client = mocker.patch.object(mod, 'HmcRestClient', autospec=True)
    rest_conn = rest_client.return_value.__enter__.return_value
    rest_conn.getManagedSystem.return_value = ('sys-uuid', object())
    rest_conn.getLogicalPartition.return_value = ('lpar-uuid', object())
    rest_conn.getVirtualNetworks.return_value = _fake_vnets([])
    rest_conn.getClientNetworkAdapters.return_value = []

    module = DummyModule()
    changed, info, _warning = mod.get_client_network_adapters(module, _facts_params())
    assert info == {'client_network_adapters': []}


# ---------------------------------------------------------------------------
# Functional tests for create_client_network_adapter
# ---------------------------------------------------------------------------


def _present_params(vn_name='vnw-lp02', slot=None):
    return {
        'hmc_host': '0.0.0.0',
        'hmc_auth': hmc_auth,
        'state': 'present',
        'system_name': 'system1',
        'vm_name': 'lpar1',
        'vios_name': None,
        'virtual_network_name': vn_name,
        'virtual_ethernet_adapter_id': slot,
        **_update_only_none,
    }


def test_create_is_idempotent_when_network_already_exists(mocker):
    mod = common_mock_setup(mocker)
    rest_client = mocker.patch.object(mod, 'HmcRestClient', autospec=True)
    rest_conn = rest_client.return_value.__enter__.return_value
    rest_conn.getManagedSystem.return_value = ('sys-uuid', object())
    rest_conn.getLogicalPartition.return_value = ('lpar-uuid', object())
    rest_conn.getVirtualNetworks.return_value = _fake_vnets([('vnw-lp02', 'net-uuid-1')])
    rest_conn.getClientNetworkAdapters.return_value = [
        FakeAdapterDom(vn_uuid='net-uuid-1', adapter_uuid='cna-uuid-1', slot='7'),
    ]

    module = DummyModule()
    changed, info, warning = mod.create_client_network_adapter(module, _present_params(slot=7))

    assert changed is False
    assert warning is None
    assert info['client_network_adapters'][0]['status'] == 'already exists'
    rest_conn.createClientNetworkAdapter.assert_not_called()
    rest_conn.updateClientNetworkAdapter.assert_not_called()


def test_create_updates_existing_slot_with_new_virtual_network(mocker):
    mod = common_mock_setup(mocker)
    rest_client = mocker.patch.object(mod, 'HmcRestClient', autospec=True)
    rest_conn = rest_client.return_value.__enter__.return_value
    rest_conn.getManagedSystem.return_value = ('sys-uuid', object())
    rest_conn.getLogicalPartition.return_value = ('lpar-uuid', object())
    rest_conn.getVirtualNetworks.return_value = _fake_vnets([('vnw-lp03', 'net-uuid-2')])
    rest_conn.getClientNetworkAdapters.return_value = [
        FakeAdapterDom(vn_uuid='net-uuid-1', adapter_uuid='cna-uuid-1', slot='7'),
    ]
    rest_conn.updateClientNetworkAdapter.return_value = object()

    module = DummyModule()
    changed, info, warning = mod.create_client_network_adapter(module, _present_params('vnw-lp03', 7))

    assert changed is True
    assert warning is None
    assert info['client_network_adapters'][0]['status'] == 'updated'
    rest_conn.createClientNetworkAdapter.assert_not_called()
    rest_conn.updateClientNetworkAdapter.assert_called_once_with(
        'lpar-uuid', 'cna-uuid-1',
        virtual_network_href='https://0.0.0.0:443/rest/api/uom/ManagedSystem/sys-uuid/VirtualNetwork/net-uuid-2',
        tagged_vlan_id='1',
        partition_type='LogicalPartition')


def test_create_creates_new_adapter_when_slot_not_in_use(mocker):
    mod = common_mock_setup(mocker)
    rest_client = mocker.patch.object(mod, 'HmcRestClient', autospec=True)
    rest_conn = rest_client.return_value.__enter__.return_value
    rest_conn.getManagedSystem.return_value = ('sys-uuid', object())
    rest_conn.getLogicalPartition.return_value = ('lpar-uuid', object())
    rest_conn.getVirtualNetworks.return_value = _fake_vnets([('vnw-lp03', 'net-uuid-2')])
    rest_conn.getClientNetworkAdapters.return_value = [
        FakeAdapterDom(vn_uuid='net-uuid-1', adapter_uuid='cna-uuid-1', slot='8'),
    ]
    rest_conn.createClientNetworkAdapter.return_value = object()

    module = DummyModule()
    changed, info, warning = mod.create_client_network_adapter(module, _present_params('vnw-lp03', 7))

    assert changed is True
    assert warning is None
    assert info['client_network_adapters'][0]['status'] == 'created'
    rest_conn.updateClientNetworkAdapter.assert_not_called()
    rest_conn.createClientNetworkAdapter.assert_called_once_with(
        'lpar-uuid', 'sys-uuid', 'net-uuid-2', '1', '', 7,
        partition_type='LogicalPartition')


# ---------------------------------------------------------------------------
# Functional tests for delete_client_network_adapter
# ---------------------------------------------------------------------------

def _absent_params():
    return {
        'hmc_host': '0.0.0.0',
        'hmc_auth': hmc_auth,
        'state': 'absent',
        'system_name': 'system1',
        'vm_name': 'lpar1',
        'vios_name': None,
        'virtual_network_name': None,
        'virtual_ethernet_adapter_id': 2,
        **_update_only_none,
    }


def test_delete_exits_gracefully_when_adapter_not_found(mocker):
    mod = common_mock_setup(mocker)
    rest_client = mocker.patch.object(mod, 'HmcRestClient', autospec=True)
    rest_conn = rest_client.return_value.__enter__.return_value
    rest_conn.getManagedSystem.return_value = ('sys-uuid', object())
    rest_conn.getLogicalPartition.return_value = ('lpar-uuid', object())
    rest_conn.getClientNetworkAdapters.return_value = []

    module = DummyModule()
    with pytest.raises(ModuleExit) as exc:
        mod.delete_client_network_adapter(module, _absent_params())

    assert exc.value.kwargs.get('changed') is False
    assert 'lpar1' in exc.value.kwargs.get('msg', '')
    rest_conn.deleteClientNetworkAdapter.assert_not_called()


def test_delete_succeeds_when_adapter_found(mocker):
    mod = common_mock_setup(mocker)
    rest_client = mocker.patch.object(mod, 'HmcRestClient', autospec=True)
    rest_conn = rest_client.return_value.__enter__.return_value
    rest_conn.getManagedSystem.return_value = ('sys-uuid', object())
    rest_conn.getLogicalPartition.return_value = ('lpar-uuid', object())
    rest_conn.getClientNetworkAdapters.return_value = [
        FakeAdapterDom(vn_uuid='net-uuid-1', adapter_uuid='cna-uuid-1', slot='2'),
    ]
    rest_conn.deleteClientNetworkAdapter.return_value = True

    module = DummyModule()
    changed, info, warning = mod.delete_client_network_adapter(module, _absent_params())

    assert changed is True
    assert info['status'] == 'deleted'
    assert info['partition_name'] == 'lpar1'
    rest_conn.deleteClientNetworkAdapter.assert_called_once_with(
        'lpar-uuid', 'cna-uuid-1', partition_type='LogicalPartition')


# ---------------------------------------------------------------------------
# Functional tests for update_client_network_adapter
# ---------------------------------------------------------------------------

def _updated_params(vn_name=None, **kwargs):
    params = {
        'hmc_host': '0.0.0.0',
        'hmc_auth': hmc_auth,
        'state': 'updated',
        'system_name': 'system1',
        'vm_name': 'lpar1',
        'vios_name': None,
        'virtual_network_name': vn_name,
        'virtual_ethernet_adapter_id': 2,
        **_update_only_none,
    }
    params.update(kwargs)
    return params


def test_update_fails_when_adapter_not_found(mocker):
    mod = common_mock_setup(mocker)
    rest_client = mocker.patch.object(mod, 'HmcRestClient', autospec=True)
    rest_conn = rest_client.return_value.__enter__.return_value
    rest_conn.getManagedSystem.return_value = ('sys-uuid', object())
    rest_conn.getLogicalPartition.return_value = ('lpar-uuid', object())
    rest_conn.getClientNetworkAdapters.return_value = []

    module = DummyModule()
    with pytest.raises(ModuleFail) as exc:
        mod.update_client_network_adapter(module, _updated_params())

    assert 'lpar1' in exc.value.kwargs['msg']
    rest_conn.updateClientNetworkAdapter.assert_not_called()


def test_update_is_idempotent_when_no_values_requested(mocker):
    mod = common_mock_setup(mocker)
    rest_client = mocker.patch.object(mod, 'HmcRestClient', autospec=True)
    rest_conn = rest_client.return_value.__enter__.return_value
    rest_conn.getManagedSystem.return_value = ('sys-uuid', object())
    rest_conn.getLogicalPartition.return_value = ('lpar-uuid', object())
    rest_conn.getVirtualNetworks.return_value = _fake_vnets([('vnw-lp02', 'net-uuid-1')])
    rest_conn.getClientNetworkAdapters.return_value = [
        FakeAdapterDom(vn_uuid='net-uuid-1', adapter_uuid='cna-uuid-1', slot='2'),
    ]

    module = DummyModule()
    changed, info, warning = mod.update_client_network_adapter(module, _updated_params())

    assert changed is False
    assert warning is None
    adapters = info['client_network_adapters']
    assert adapters[0]['status'] == 'already updated'
    rest_conn.updateClientNetworkAdapter.assert_not_called()


def test_update_succeeds_when_values_change(mocker):
    """Updated state passes MAC, QoS, and 802.1Qbg values to the REST client."""
    mod = common_mock_setup(mocker)
    rest_client = mocker.patch.object(mod, 'HmcRestClient', autospec=True)
    rest_conn = rest_client.return_value.__enter__.return_value
    rest_conn.getManagedSystem.return_value = ('sys-uuid', object())
    rest_conn.getLogicalPartition.return_value = ('lpar-uuid', object())
    rest_conn.getVirtualNetworks.return_value = _fake_vnets([('vnw-lp02', 'net-uuid-1')])
    rest_conn.getClientNetworkAdapters.return_value = [
        FakeAdapterDom(
            vn_uuid='net-uuid-1',
            adapter_uuid='cna-uuid-1',
            slot='2',
            mac='4AA9B56A0E02',
            allowed_os_mac_addresses='ALL',
            qos_priority_enabled='false',
            qos_priority='1',
            vsi_type_id='99',
            vsi_manager_id='199',
            vsi_type_version='0'),
    ]
    rest_conn.updateClientNetworkAdapter.return_value = object()

    module = DummyModule()
    params = _updated_params(
        mac_address='B6:08:90:7C:A6:07',
        os_mac_address_restrictions='allow_specified',
        allowed_os_mac_addresses=['B6:08:90:7C:A6:08', 'B6:08:90:7C:A6:09'],
        qos_priority_enabled=True,
        qos_priority=2,
        vsi_type_id=100,
        vsi_manager_id=200,
        vsi_type_version=1,
    )
    changed, info, _warning = mod.update_client_network_adapter(module, params)

    assert changed is True
    assert info['client_network_adapters'][0]['status'] == 'updated'
    rest_conn.updateClientNetworkAdapter.assert_called_once_with(
        'lpar-uuid', 'cna-uuid-1',
        mac_address='B6:08:90:7C:A6:07',
        allowed_os_mac_addresses='B6:08:90:7C:A6:08 B6:08:90:7C:A6:09',
        qos_priority_enabled=True,
        qos_priority=2,
        vsi_type_id=100,
        vsi_manager_id=200,
        vsi_type_version=1,
        partition_type='LogicalPartition')


def test_update_allow_all_mac_restriction(mocker):
    """allow_all maps to API value 'ALL'."""
    mod = common_mock_setup(mocker)
    rest_client = mocker.patch.object(mod, 'HmcRestClient', autospec=True)
    rest_conn = rest_client.return_value.__enter__.return_value
    rest_conn.getManagedSystem.return_value = ('sys-uuid', object())
    rest_conn.getLogicalPartition.return_value = ('lpar-uuid', object())
    rest_conn.getVirtualNetworks.return_value = _fake_vnets([('vnw-lp02', 'net-uuid-1')])
    rest_conn.getClientNetworkAdapters.return_value = [
        FakeAdapterDom(vn_uuid='net-uuid-1', adapter_uuid='cna-uuid-1', slot='2', allowed_os_mac_addresses='NONE'),
    ]
    rest_conn.updateClientNetworkAdapter.return_value = object()

    module = DummyModule()
    params = _updated_params(os_mac_address_restrictions='allow_all')
    mod.update_client_network_adapter(module, params)

    call_kwargs = rest_conn.updateClientNetworkAdapter.call_args
    assert call_kwargs.kwargs['allowed_os_mac_addresses'] == 'ALL'


def test_update_deny_all_mac_restriction(mocker):
    """deny_all maps to API value 'NONE'."""
    mod = common_mock_setup(mocker)
    rest_client = mocker.patch.object(mod, 'HmcRestClient', autospec=True)
    rest_conn = rest_client.return_value.__enter__.return_value
    rest_conn.getManagedSystem.return_value = ('sys-uuid', object())
    rest_conn.getLogicalPartition.return_value = ('lpar-uuid', object())
    rest_conn.getVirtualNetworks.return_value = _fake_vnets([('vnw-lp02', 'net-uuid-1')])
    rest_conn.getClientNetworkAdapters.return_value = [
        FakeAdapterDom(vn_uuid='net-uuid-1', adapter_uuid='cna-uuid-1', slot='2', allowed_os_mac_addresses='ALL'),
    ]
    rest_conn.updateClientNetworkAdapter.return_value = object()

    module = DummyModule()
    params = _updated_params(os_mac_address_restrictions='deny_all')
    mod.update_client_network_adapter(module, params)

    call_kwargs = rest_conn.updateClientNetworkAdapter.call_args
    assert call_kwargs.kwargs['allowed_os_mac_addresses'] == 'NONE'


def test_update_allow_specified_without_addresses_fails(mocker):
    """allow_specified with no allowed_os_mac_addresses should fail_json."""
    mod = common_mock_setup(mocker)
    module = DummyModule()
    params = _updated_params(
        os_mac_address_restrictions='allow_specified',
        allowed_os_mac_addresses=None,
    )
    with pytest.raises(ModuleFail) as exc:
        mod.update_client_network_adapter(module, params)
    assert 'allowed_os_mac_addresses' in exc.value.kwargs['msg']


def test_update_allow_all_with_addresses_fails(mocker):
    mod = common_mock_setup(mocker)
    module = DummyModule()
    params = _updated_params(
        os_mac_address_restrictions='allow_all',
        allowed_os_mac_addresses=['B6:08:90:7C:A6:08'],
    )
    with pytest.raises(ModuleFail) as exc:
        mod.update_client_network_adapter(module, params)
    assert "supported only when" in exc.value.kwargs['msg']


def test_update_is_idempotent_when_requested_values_match_current_state(mocker):
    mod = common_mock_setup(mocker)
    rest_client = mocker.patch.object(mod, 'HmcRestClient', autospec=True)
    rest_conn = rest_client.return_value.__enter__.return_value
    rest_conn.getManagedSystem.return_value = ('sys-uuid', object())
    rest_conn.getLogicalPartition.return_value = ('lpar-uuid', object())
    rest_conn.getVirtualNetworks.return_value = _fake_vnets([('vnw-lp02', 'net-uuid-1')])
    rest_conn.getClientNetworkAdapters.return_value = [
        FakeAdapterDom(
            vn_uuid='net-uuid-1',
            adapter_uuid='cna-uuid-1',
            slot='2',
            mac='B608907CA607',
            allowed_os_mac_addresses='B6:08:90:7C:A6:08 B6:08:90:7C:A6:09',
            qos_priority_enabled='true',
            qos_priority='2',
            vsi_type_id='100',
            vsi_manager_id='200',
            vsi_type_version='1'),
    ]

    module = DummyModule()
    params = _updated_params(
        mac_address='B6:08:90:7C:A6:07',
        os_mac_address_restrictions='allow_specified',
        allowed_os_mac_addresses=['B6:08:90:7C:A6:08', 'B6:08:90:7C:A6:09'],
        qos_priority_enabled=True,
        qos_priority=2,
        vsi_type_id=100,
        vsi_manager_id=200,
        vsi_type_version=1,
    )
    changed, info, warning = mod.update_client_network_adapter(module, params)

    assert changed is False
    assert warning is None
    assert info['client_network_adapters'][0]['status'] == 'already updated'
    rest_conn.updateClientNetworkAdapter.assert_not_called()


def test_update_deny_all_with_addresses_fails(mocker):
    mod = common_mock_setup(mocker)
    module = DummyModule()
    params = _updated_params(
        os_mac_address_restrictions='deny_all',
        allowed_os_mac_addresses=['B6:08:90:7C:A6:08'],
    )
    with pytest.raises(ModuleFail) as exc:
        mod.update_client_network_adapter(module, params)
    assert "supported only when" in exc.value.kwargs['msg']


# ---------------------------------------------------------------------------
# VIOS shutdown-state guard tests (updated, absent, detach_virtual_network)
# ---------------------------------------------------------------------------

def _vios_quick_response(vios_name, partition_state):
    """Return a JSON bytes object simulating getVirtualIOServersQuick output."""
    import json
    return json.dumps([
        {'PartitionName': vios_name, 'UUID': 'vios-uuid-1', 'PartitionState': partition_state,
         'RMCState': 'inactive'},
    ]).encode()


def test_update_vios_fails_when_running(mocker):
    """updated state with vios_name must fail if VIOS is not 'not activated'."""
    mod = common_mock_setup(mocker)
    rest_client = mocker.patch.object(mod, 'HmcRestClient', autospec=True)
    rest_conn = rest_client.return_value.__enter__.return_value
    rest_conn.getManagedSystem.return_value = ('sys-uuid', object())
    rest_conn.getVirtualIOServersQuick.return_value = _vios_quick_response('vios1', 'running')

    module = DummyModule()
    params = {
        'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'updated',
        'system_name': 'system1', 'vm_name': None, 'vios_name': 'vios1',
        'virtual_network_name': None, 'virtual_ethernet_adapter_id': 2,
        **_update_only_none,
    }
    with pytest.raises(ModuleFail) as exc:
        mod.update_client_network_adapter(module, params)
    assert 'not activated' in exc.value.kwargs['msg']
    assert 'running' in exc.value.kwargs['msg']


def test_delete_vios_fails_when_running(mocker):
    """absent state with vios_name must fail if VIOS is not 'not activated'."""
    mod = common_mock_setup(mocker)
    rest_client = mocker.patch.object(mod, 'HmcRestClient', autospec=True)
    rest_conn = rest_client.return_value.__enter__.return_value
    rest_conn.getManagedSystem.return_value = ('sys-uuid', object())
    rest_conn.getVirtualIOServersQuick.return_value = _vios_quick_response('vios1', 'running')

    module = DummyModule()
    params = {
        'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'absent',
        'system_name': 'system1', 'vm_name': None, 'vios_name': 'vios1',
        'virtual_network_name': None, 'virtual_ethernet_adapter_id': 2,
        **_update_only_none,
    }
    with pytest.raises(ModuleFail) as exc:
        mod.delete_client_network_adapter(module, params)
    assert 'not activated' in exc.value.kwargs['msg']
    assert 'running' in exc.value.kwargs['msg']


def test_detach_vios_fails_when_running(mocker):
    """detach_virtual_network state with vios_name must fail if VIOS is not 'not activated'."""
    mod = common_mock_setup(mocker)
    rest_client = mocker.patch.object(mod, 'HmcRestClient', autospec=True)
    rest_conn = rest_client.return_value.__enter__.return_value
    rest_conn.getManagedSystem.return_value = ('sys-uuid', object())
    rest_conn.getVirtualIOServersQuick.return_value = _vios_quick_response('vios1', 'running')

    module = DummyModule()
    params = {
        'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'detach_virtual_network',
        'system_name': 'system1', 'vm_name': None, 'vios_name': 'vios1',
        'virtual_network_name': 'vnw1', 'virtual_ethernet_adapter_id': 2,
        **_update_only_none,
    }
    with pytest.raises(ModuleFail) as exc:
        mod.detach_virtual_network(module, params)
    assert 'not activated' in exc.value.kwargs['msg']
    assert 'running' in exc.value.kwargs['msg']


def test_update_vios_succeeds_when_shutdown(mocker):
    """updated state with vios_name must proceed when VIOS is 'not activated'."""
    mod = common_mock_setup(mocker)
    rest_client = mocker.patch.object(mod, 'HmcRestClient', autospec=True)
    rest_conn = rest_client.return_value.__enter__.return_value
    rest_conn.getManagedSystem.return_value = ('sys-uuid', object())
    rest_conn.getVirtualIOServersQuick.return_value = _vios_quick_response('vios1', 'not activated')
    rest_conn.getVirtualNetworks.return_value = _fake_vnets([('vnw1', 'net-uuid-1')])
    rest_conn.getViosClientNetworkAdapters.return_value = [
        FakeAdapterDom(vn_uuid='net-uuid-1', adapter_uuid='cna-uuid-1', slot='2',
                       allowed_os_mac_addresses='NONE'),
    ]
    rest_conn.updateClientNetworkAdapter.return_value = object()

    module = DummyModule()
    params = {
        'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'updated',
        'system_name': 'system1', 'vm_name': None, 'vios_name': 'vios1',
        'virtual_network_name': None, 'virtual_ethernet_adapter_id': 2,
        'mac_address': None, 'os_mac_address_restrictions': 'allow_all',
        'allowed_os_mac_addresses': None, 'qos_priority_enabled': None,
        'qos_priority': None, 'vsi_type_id': None, 'vsi_manager_id': None,
        'vsi_type_version': None,
    }
    changed, info, _warning = mod.update_client_network_adapter(module, params)
    assert changed is True
