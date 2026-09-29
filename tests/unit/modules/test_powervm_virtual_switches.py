from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
import importlib

IMPORT_VIRTUAL_SWITCHES = "ansible_collections.ibm.power_hmc.plugins.modules.powervm_virtual_switches"

from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError

hmc_auth = {'username': 'hscroot', 'password': 'password_value'}

# Test data for state='present' (create virtual switch)
test_data_present = [
    # hmc_host is missing
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'state': 'present',
      'system_name': 'system1', 'virtual_switch_name': 'ETHERNET1', 'virtual_switch_mode': 'Veb'},
     "ParameterError: mandatory parameter 'hmc_host' is missing"),

    # system_name is missing
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'present',
      'system_name': None, 'virtual_switch_name': 'ETHERNET1', 'virtual_switch_mode': 'Veb'},
     "ParameterError: mandatory parameter 'system_name' is missing"),

    # virtual_switch_name is missing
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'present',
      'system_name': 'system1', 'virtual_switch_name': None, 'virtual_switch_mode': 'Veb'},
     "ParameterError: mandatory parameter 'virtual_switch_name' is missing"),

    # unsupported parameter new_switch_name for present state
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'present',
      'system_name': 'system1', 'virtual_switch_name': 'ETHERNET1',
      'virtual_switch_mode': 'Veb', 'new_switch_name': 'ETHERNET2'},
     "ParameterError: unsupported parameter: new_switch_name"),
]

# Test data for state='modify' (modify virtual switch)
test_data_modify = [
    # hmc_host is missing
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'state': 'modify',
      'system_name': 'system1', 'virtual_switch_name': 'ETHERNET1',
      'virtual_switch_mode': 'Vepa'},
     "ParameterError: mandatory parameter 'hmc_host' is missing"),

    # system_name is missing
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'modify',
      'system_name': None, 'virtual_switch_name': 'ETHERNET1',
      'virtual_switch_mode': 'Vepa'},
     "ParameterError: mandatory parameter 'system_name' is missing"),

    # virtual_switch_name is missing
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'modify',
      'system_name': 'system1', 'virtual_switch_name': None,
      'virtual_switch_mode': 'Vepa'},
     "ParameterError: mandatory parameter 'virtual_switch_name' is missing"),

    # neither virtual_switch_mode nor new_switch_name provided
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'modify',
      'system_name': 'system1', 'virtual_switch_name': 'ETHERNET1',
      'virtual_switch_mode': None, 'new_switch_name': None},
     "ParameterError: For modify state, at least one of 'virtual_switch_mode' or 'new_switch_name' must be provided"),

    # multiple mandatory parameters missing
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'state': 'modify',
      'system_name': None, 'virtual_switch_name': 'ETHERNET1',
      'virtual_switch_mode': 'Vepa'},
     "ParameterError: mandatory parameters 'hmc_host,system_name' are missing"),
]

# Test data for state='absent' (delete virtual switch)
test_data_absent = [
    # hmc_host is missing
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'state': 'absent',
      'system_name': 'system1', 'virtual_switch_name': 'ETHERNET1'},
     "ParameterError: mandatory parameter 'hmc_host' is missing"),

    # system_name is missing
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'absent',
      'system_name': None, 'virtual_switch_name': 'ETHERNET1'},
     "ParameterError: mandatory parameter 'system_name' is missing"),

    # virtual_switch_name is missing
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'absent',
      'system_name': 'system1', 'virtual_switch_name': None},
     "ParameterError: mandatory parameter 'virtual_switch_name' is missing"),

    # multiple unsupported parameters for absent state
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'absent',
      'system_name': 'system1', 'virtual_switch_name': 'ETHERNET1',
      'virtual_switch_mode': 'Veb', 'new_switch_name': 'ETHERNET2'},
     "ParameterError: unsupported parameters: virtual_switch_mode, new_switch_name"),
]

# Test data for state='facts' (get virtual switch information)
test_data_facts = [
    # hmc_host is missing
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'state': 'facts',
      'system_name': 'system1', 'virtual_switch_name': None},
     "ParameterError: mandatory parameter 'hmc_host' is missing"),

    # system_name is missing
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'facts',
      'system_name': None, 'virtual_switch_name': None},
     "ParameterError: mandatory parameter 'system_name' is missing"),

    # multiple unsupported parameters for facts state
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'state': 'facts',
      'system_name': 'system1', 'virtual_switch_name': None,
      'virtual_switch_mode': 'Veb', 'new_switch_name': 'ETHERNET2'},
     "ParameterError: unsupported parameters: virtual_switch_mode, new_switch_name"),
]


def common_mock_setup(mocker):
    """Common mock setup for all tests"""
    powervm_virtual_switches = importlib.import_module(IMPORT_VIRTUAL_SWITCHES)
    mocker.patch.object(powervm_virtual_switches, 'HmcCliConnection')
    mocker.patch.object(powervm_virtual_switches, 'HmcRestClient', autospec=True)
    mocker.patch.object(powervm_virtual_switches, 'Hmc', autospec=True)
    return powervm_virtual_switches


@pytest.mark.parametrize("test_input, expected_error", test_data_present)
def test_create_virtual_switch_parameter_validation(mocker, test_input, expected_error):
    """Test parameter validation for create virtual switch (state=present)"""
    powervm_virtual_switches = common_mock_setup(mocker)
    if 'ParameterError' in expected_error:
        with pytest.raises(ParameterError) as e:
            powervm_virtual_switches.create_virtual_switch(powervm_virtual_switches, test_input)
        assert expected_error == repr(e.value)
    else:
        powervm_virtual_switches.create_virtual_switch(powervm_virtual_switches, test_input)


@pytest.mark.parametrize("test_input, expected_error", test_data_modify)
def test_modify_virtual_switch_parameter_validation(mocker, test_input, expected_error):
    """Test parameter validation for modify virtual switch (state=modify)"""
    powervm_virtual_switches = common_mock_setup(mocker)
    if 'ParameterError' in expected_error:
        with pytest.raises(ParameterError) as e:
            powervm_virtual_switches.modify_virtual_switch(powervm_virtual_switches, test_input)
        assert expected_error == repr(e.value)
    else:
        powervm_virtual_switches.modify_virtual_switch(powervm_virtual_switches, test_input)


@pytest.mark.parametrize("test_input, expected_error", test_data_absent)
def test_delete_virtual_switch_parameter_validation(mocker, test_input, expected_error):
    """Test parameter validation for delete virtual switch (state=absent)"""
    powervm_virtual_switches = common_mock_setup(mocker)
    if 'ParameterError' in expected_error:
        with pytest.raises(ParameterError) as e:
            powervm_virtual_switches.delete_virtual_switch(powervm_virtual_switches, test_input)
        assert expected_error == repr(e.value)
    else:
        powervm_virtual_switches.delete_virtual_switch(powervm_virtual_switches, test_input)


@pytest.mark.parametrize("test_input, expected_error", test_data_facts)
def test_get_virtual_switches_parameter_validation(mocker, test_input, expected_error):
    """Test parameter validation for get virtual switches (state=facts)"""
    powervm_virtual_switches = common_mock_setup(mocker)
    if 'ParameterError' in expected_error:
        with pytest.raises(ParameterError) as e:
            powervm_virtual_switches.get_virtual_switches(powervm_virtual_switches, test_input)
        assert expected_error == repr(e.value)
    else:
        powervm_virtual_switches.get_virtual_switches(powervm_virtual_switches, test_input)

# Made with Bob
