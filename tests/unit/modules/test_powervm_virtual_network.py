from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
import importlib

IMPORT_VIRTUAL_NETWORK = "ansible_collections.ibm.power_hmc.plugins.modules.powervm_virtual_network"

from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError

hmc_auth = {'username': 'hscroot', 'password': 'password_value'}


class DummyModule:
    def exit_json(self, **kwargs):
        raise ModuleExit(kwargs)

    def fail_json(self, **kwargs):
        raise ModuleFail(kwargs)


class ModuleExit(Exception):
    def __init__(self, kwargs):
        self.kwargs = kwargs
        super().__init__(str(kwargs))


class ModuleFail(Exception):
    def __init__(self, kwargs):
        self.kwargs = kwargs
        super().__init__(str(kwargs))


test_data_present = [
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'state': 'present',
      'system_name': 'system1', 'network_name': 'nw1', 'network_vlan_id': 100,
      'switch_name': 'ETHERNET0', 'switch_id': None, 'tagged_network': False, 'new_network_name': None},
     "ParameterError: mandatory parameter 'hmc_host' is missing"),
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'present',
      'system_name': 'system1', 'network_name': None, 'network_vlan_id': 100,
      'switch_name': 'ETHERNET0', 'switch_id': None, 'tagged_network': False, 'new_network_name': None},
     "ParameterError: mandatory parameter 'network_name' is missing"),
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'present',
      'system_name': 'system1', 'network_name': 'nw1', 'network_vlan_id': 100,
      'switch_name': None, 'switch_id': None, 'tagged_network': False, 'new_network_name': None},
     "ParameterError: Either 'switch_name' or 'switch_id' is required for present state"),
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'present',
      'system_name': 'system1', 'network_name': 'nw1', 'network_vlan_id': 100,
      'switch_name': 'ETHERNET0', 'switch_id': 1, 'tagged_network': False, 'new_network_name': None},
     "ParameterError: Parameters 'switch_name' and 'switch_id' are mutually exclusive"),
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'present',
      'system_name': 'system1', 'network_name': 'nw1', 'network_vlan_id': 0,
      'switch_name': 'ETHERNET0', 'switch_id': None, 'tagged_network': False, 'new_network_name': None},
     "ParameterError: network_vlan_id must be between 1 and 4094 (inclusive), got: 0"),
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'present',
      'system_name': 'system1', 'network_name': 'nw1', 'network_vlan_id': 100,
      'switch_name': 'ETHERNET0', 'switch_id': None, 'tagged_network': False, 'new_network_name': 'nw2'},
     "ParameterError: unsupported parameter: new_network_name"),
]

test_data_absent = [
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'state': 'absent',
      'system_name': 'system1', 'network_name': 'nw1', 'network_vlan_id': None,
      'switch_name': None, 'switch_id': None, 'tagged_network': False, 'new_network_name': None},
     "ParameterError: mandatory parameter 'hmc_host' is missing"),
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'absent',
      'system_name': 'system1', 'network_name': None, 'network_vlan_id': None,
      'switch_name': None, 'switch_id': None, 'tagged_network': False, 'new_network_name': None},
     "ParameterError: mandatory parameter 'network_name' is missing"),
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'absent',
      'system_name': 'system1', 'network_name': 'nw1', 'network_vlan_id': 100,
      'switch_name': None, 'switch_id': None, 'tagged_network': False, 'new_network_name': None},
     "ParameterError: unsupported parameter: network_vlan_id"),
]

test_data_updated = [
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'state': 'updated',
      'system_name': 'system1', 'network_name': 'nw1', 'new_network_name': 'nw2',
      'network_vlan_id': None, 'switch_name': None, 'switch_id': None, 'tagged_network': False},
     "ParameterError: mandatory parameter 'hmc_host' is missing"),
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'updated',
      'system_name': 'system1', 'network_name': None, 'new_network_name': 'nw2',
      'network_vlan_id': None, 'switch_name': None, 'switch_id': None, 'tagged_network': False},
     "ParameterError: mandatory parameter 'network_name' is missing"),
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'updated',
      'system_name': 'system1', 'network_name': 'nw1', 'new_network_name': None,
      'network_vlan_id': None, 'switch_name': None, 'switch_id': None, 'tagged_network': False},
     "ParameterError: mandatory parameter 'new_network_name' is missing"),
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'updated',
      'system_name': 'system1', 'network_name': 'nw1', 'new_network_name': 'nw2',
      'network_vlan_id': 100, 'switch_name': None, 'switch_id': None, 'tagged_network': False},
     "ParameterError: unsupported parameter: network_vlan_id"),
]

test_data_facts = [
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'state': 'facts',
      'system_name': 'system1', 'network_name': None, 'network_vlan_id': None,
      'switch_name': None, 'switch_id': None, 'tagged_network': False, 'new_network_name': None},
     "ParameterError: mandatory parameter 'hmc_host' is missing"),
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'facts',
      'system_name': None, 'network_name': None, 'network_vlan_id': None,
      'switch_name': None, 'switch_id': None, 'tagged_network': False, 'new_network_name': None},
     "ParameterError: mandatory parameter 'system_name' is missing"),
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'facts',
      'system_name': 'system1', 'network_name': None, 'network_vlan_id': 100,
      'switch_name': None, 'switch_id': None, 'tagged_network': False, 'new_network_name': None},
     "ParameterError: unsupported parameter: network_vlan_id"),
]


def common_mock_setup(mocker):
    powervm_virtual_network = importlib.import_module(IMPORT_VIRTUAL_NETWORK)
    mocker.patch.object(powervm_virtual_network, 'HmcCliConnection')
    mocker.patch.object(powervm_virtual_network, 'Hmc', autospec=True)
    return powervm_virtual_network


class FakeElementList(list):
    def xpath(self, expression):
        if expression == ".//link[@rel='SELF']":
            return []
        return []


class FakeElement:
    def __init__(self, text=None, children=None):
        self.text = text
        self.children = children or {}

    def xpath(self, expression):
        return self.children.get(expression, FakeElementList())


class FakeDom:
    def __init__(self, names):
        self.names = names

    def xpath(self, expression):
        if expression == "//VirtualNetwork":
            networks = FakeElementList()
            for index, name in enumerate(self.names, start=1):
                networks.append(
                    FakeElement(children={
                        ".//NetworkName": FakeElementList([FakeElement(text=name)]),
                        ".//Metadata/Atom/AtomID": FakeElementList([FakeElement(text="uuid-{0}".format(index))]),
                        ".//Metadata/Atom": FakeElementList([FakeElement()])
                    })
                )
            return networks
        return FakeElementList()


def build_virtual_networks_dom(names):
    return FakeDom(names)


@pytest.mark.parametrize("test_input, expected_error", test_data_present)
def test_create_virtual_network_parameter_validation(mocker, test_input, expected_error):
    powervm_virtual_network = common_mock_setup(mocker)
    with pytest.raises(ParameterError) as e:
        powervm_virtual_network.validate_parameters(test_input)
    assert expected_error == repr(e.value)


@pytest.mark.parametrize("test_input, expected_error", test_data_absent)
def test_delete_virtual_network_parameter_validation(mocker, test_input, expected_error):
    powervm_virtual_network = common_mock_setup(mocker)
    with pytest.raises(ParameterError) as e:
        powervm_virtual_network.validate_parameters(test_input)
    assert expected_error == repr(e.value)


@pytest.mark.parametrize("test_input, expected_error", test_data_updated)
def test_update_virtual_network_parameter_validation(mocker, test_input, expected_error):
    powervm_virtual_network = common_mock_setup(mocker)
    with pytest.raises(ParameterError) as e:
        powervm_virtual_network.validate_parameters(test_input)
    assert expected_error == repr(e.value)


@pytest.mark.parametrize("test_input, expected_error", test_data_facts)
def test_get_virtual_networks_parameter_validation(mocker, test_input, expected_error):
    powervm_virtual_network = common_mock_setup(mocker)
    with pytest.raises(ParameterError) as e:
        powervm_virtual_network.validate_parameters(test_input)
    assert expected_error == repr(e.value)


def test_update_virtual_network_idempotent_when_new_name_exists(mocker):
    powervm_virtual_network = common_mock_setup(mocker)
    rest_client = mocker.patch.object(powervm_virtual_network, 'HmcRestClient', autospec=True)
    rest_conn = rest_client.return_value.__enter__.return_value
    rest_conn.getManagedSystem.return_value = ('sys-uuid', object())
    rest_conn.getVirtualNetworks.return_value = build_virtual_networks_dom(['target-network'])

    module = DummyModule()
    params = {
        'hmc_host': '0.0.0.0',
        'hmc_auth': hmc_auth,
        'system_name': 'system1',
        'network_name': 'source-network',
        'new_network_name': 'target-network',
        'network_vlan_id': None,
        'switch_name': None,
        'switch_id': None,
        'tagged_network': False,
        'state': 'updated'
    }

    with pytest.raises(ModuleFail) as exc:
        powervm_virtual_network.update_virtual_network(module, params)

    assert exc.value.kwargs['msg'] == 'ModuleExit(\'{\\\'changed\\\': False, \\\'msg\\\': "Virtual network \\\'target-network\\\' already exists"}\')'
    rest_conn.updateVirtualNetwork.assert_not_called()


def test_update_virtual_network_fails_when_both_names_do_not_exist(mocker):
    powervm_virtual_network = common_mock_setup(mocker)
    rest_client = mocker.patch.object(powervm_virtual_network, 'HmcRestClient', autospec=True)
    rest_conn = rest_client.return_value.__enter__.return_value
    rest_conn.getManagedSystem.return_value = ('sys-uuid', object())
    rest_conn.getVirtualNetworks.return_value = build_virtual_networks_dom(['another-network'])

    module = DummyModule()
    params = {
        'hmc_host': '0.0.0.0',
        'hmc_auth': hmc_auth,
        'system_name': 'system1',
        'network_name': 'source-network',
        'new_network_name': 'target-network',
        'network_vlan_id': None,
        'switch_name': None,
        'switch_id': None,
        'tagged_network': False,
        'state': 'updated'
    }

    with pytest.raises(ModuleFail) as exc:
        powervm_virtual_network.update_virtual_network(module, params)

    assert exc.value.kwargs['msg'] == 'ModuleFail(\'{\\\'msg\\\': "Virtual network \\\'source-network\\\' does not exist"}\')'
    rest_conn.updateVirtualNetwork.assert_not_called()

# Made with Bob
