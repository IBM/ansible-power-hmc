from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
import importlib

IMPORT_HMC_POWER_SYSTEM = "ansible_collections.ibm.power_hmc.plugins.modules.power_system"

from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError

hmc_auth = {'username': 'hscroot', 'password': 'password_value'}
test_data1 = [
    # All PowerOff Managed System Testdata
    # when hostname is missing
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'action': 'poweroff', 'state': None, 'system_name': "system_name"},
     "ParameterError: mandatory parameter 'hmc_host' is missing"),
    # when system_name is missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'action': 'poweroff', 'system_name': None, 'state': None},
     "ParameterError: mandatory parameter 'system_name' is missing")]

test_data2 = [
    # All PowerOn Power system Testdata
    # when hostname is missing
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'action': 'poweron', 'state': None, 'system_name': "system_name"},
     "ParameterError: mandatory parameter 'hmc_host' is missing"),
    # when system_name is missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'action': 'poweron', 'system_name': None, 'state': None},
     "ParameterError: mandatory parameter 'system_name' is missing")]

test_data3 = [
    # All modify system_config data
    # when hostname is missing
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'action': 'modify_syscfg', 'state': None, 'system_name': "system_name"},
     "ParameterError: mandatory parameter 'hmc_host' is missing"),
    # when system_name is missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'action': 'modify_syscfg', 'system_name': None, 'state': None},
     "ParameterError: mandatory parameter 'system_name' is missing"),
    # when requested_num_sys_huge_pages, mem_mirroring_mode, pend_mem_region_size mentioned
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'action': 'modify_syscfg', 'system_name': "system_name",
      'requested_num_sys_huge_pages': 'requested_num_sys_huge_pages', 'state': None, 'pend_mem_region_size': '256',
      'mem_mirroring_mode': 'sys_firmware_only'},
     "ParameterError: unsupported parameters: requested_num_sys_huge_pages, mem_mirroring_mode, pend_mem_region_size")]

test_data4 = [
    # All modify_hwres data
    # when hostname is missing
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'action': 'modify_hwres', 'state': None, 'system_name': "system_name"},
     "ParameterError: mandatory parameter 'hmc_host' is missing"),
    # when system_name is missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'action': 'modify_hwres', 'system_name': None, 'state': None},
     "ParameterError: mandatory parameter 'system_name' is missing"),
    # when new_name', 'power_off_policy', 'power_on_lpar_start_policy mentiones
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'action': 'modify_hwres', 'system_name': "system_name", 'new_name': 'new_name', 'power_off_policy': 0,
      'power_on_lpar_start_policy': 'power_on_lpar_start_policy', 'state': None, 'pend_mem_region_size': '256', 'mem_mirroring_mode': 'sys_firmware_only'},
     "ParameterError: unsupported parameters: new_name, power_on_lpar_start_policy")]

test_data5 = [
    # All Facts Partition Testdata
    # when hostname is missing
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'action': None, 'state': 'facts', 'system_name': "system_name"},
     "ParameterError: mandatory parameter 'hmc_host' is missing"),
    # when system_name is missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'action': None, 'system_name': None, 'state': 'facts'},
     "ParameterError: mandatory parameter 'system_name' is missing"),
    # when new_name', 'power_off_policy', 'power_on_lpar_start_policy,requested_num_sys_huge_pages, mem_mirroring_mode, pend_mem_region_size are mentioned
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'action': None, 'system_name': "system_name", 'new_name': 'new_name', 'power_off_policy': 0,
      'power_on_lpar_start_policy': 'power_on_lpar_start_policy', 'state': 'facts', 'pend_mem_region_size': '256',
      'requested_num_sys_huge_pages': 'requested_num_sys_huge_pages', 'mem_mirroring_mode': 'sys_firmware_only'},
     "ParameterError: unsupported parameters: new_name, power_on_lpar_start_policy, requested_num_sys_huge_pages, mem_mirroring_mode, pend_mem_region_size")]


def common_mock_setup(mocker):
    hmc_power_system = importlib.import_module(IMPORT_HMC_POWER_SYSTEM)
    mocker.patch.object(hmc_power_system, 'HmcCliConnection')
    mocker.patch.object(hmc_power_system, 'HmcRestClient', autospec=True)
    return hmc_power_system


@pytest.mark.parametrize("power_system_test_input, expectedError", test_data1)
def test_call_inside_powerOffManagedSys(mocker, power_system_test_input, expectedError):
    hmc_power_system = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            hmc_power_system.powerOffManagedSys(hmc_power_system, power_system_test_input)
        assert expectedError == repr(e.value)
    else:
        hmc_power_system.powerOffManagedSys(hmc_power_system, power_system_test_input)


@pytest.mark.parametrize("power_system_test_input, expectedError", test_data2)
def test_call_inside_powerOnManagedSys(mocker, power_system_test_input, expectedError):
    hmc_power_system = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            hmc_power_system.powerOnManagedSys(hmc_power_system, power_system_test_input)
        assert expectedError == repr(e.value)
    else:
        hmc_power_system.powerOnManagedSys(hmc_power_system, power_system_test_input)


@pytest.mark.parametrize("power_system_test_input, expectedError", test_data3)
def test_call_inside_modifySystemConfiguration(mocker, power_system_test_input, expectedError):
    hmc_power_system = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            hmc_power_system.modifySystemConfiguration(hmc_power_system, power_system_test_input)
        assert expectedError == repr(e.value)
    else:
        hmc_power_system.modifySystemConfiguration(hmc_power_system, power_system_test_input)


@pytest.mark.parametrize("power_system_test_input, expectedError", test_data4)
def test_call_inside_modifySystemHardwareResources(mocker, power_system_test_input, expectedError):
    hmc_power_system = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            hmc_power_system.modifySystemHardwareResources(hmc_power_system, power_system_test_input)
        assert expectedError == repr(e.value)
    else:
        hmc_power_system.modifySystemHardwareResources(hmc_power_system, power_system_test_input)


@pytest.mark.parametrize("power_system_test_input, expectedError", test_data5)
def test_call_inside_fetchManagedSysDetails(mocker, power_system_test_input, expectedError):
    hmc_power_system = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            hmc_power_system.fetchManagedSysDetails(hmc_power_system, power_system_test_input)
        assert expectedError == repr(e.value)
    else:
        hmc_power_system.fetchManagedSysDetails(hmc_power_system, power_system_test_input)
