from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
import importlib

IMPORT_HMC_POWERVM = "ansible_collections.ibm.power_hmc.plugins.modules.powervm_lpar_instance"

from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError

hmc_auth = {'username': 'hscroot', 'password': 'password_value'}
volume_config = {'volume_size': 2048}
virt_network_config = {'network_name': 'test'}
test_data = [
    # ALL Create partition testdata
    # system name is missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'present',
      'system_name': None, 'vm_name': "vmname", 'proc': '4', 'mem': '2048',
      'os_type': 'aix_linux'}, "ParameterError: mandatory parameter 'system_name' is missing"),
    # vmname is missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'present',
      'system_name': "systemname", 'vm_name': None, 'proc': '4', 'mem':
      '2048', 'os_type': 'aix_linux'}, "ParameterError: mandatory parameter 'vm_name' is missing"),
    # os type is missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'present',
      'system_name': "systemname", 'vm_name': "vmname", 'proc': '4', 'mem':
      '2048', 'os_type': None}, "ParameterError: mandatory parameter 'os_type' is missing"),
    # hmc_host is missing
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'state': 'present',
      'system_name': "systemname", 'vm_name': "vmname", 'proc': '4', 'mem':
      '2048', 'os_type': 'aix'}, "ParameterError: mandatory parameter 'hmc_host' is missing"),
    # hmc_auth is missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': None, 'state': 'present',
      'system_name': "systemname", 'vm_name': "vmname", 'proc': '4', 'mem':
      '2048', 'os_type': 'aix'}, "ParameterError: mandatory parameter 'hmc_auth' is missing"),
    # vmname, proc and mem are missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'present', 'volume_config': volume_config,
      'system_name': "systemname", 'vm_name': None, 'proc': None, 'mem': None,
      'os_type': 'aix'}, "ParameterError: mandatory parameter 'vm_name' is missing"),
    # sys_name and vmname are missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'present', 'volume_config': volume_config,
      'system_name': None, 'vm_name': None, 'proc': '4', 'mem': '2048',
      'os_type': 'ibmi'}, "ParameterError: mandatory parameters 'system_name,vm_name' are missing")]
test_data1 = [
    # ALL Delete partition testdata
    # system name is missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'absent',
      'system_name': None, 'vm_name': "vmname"}, "ParameterError: mandatory parameter 'system_name' is missing"),
    # vmname is missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'absent',
      'system_name': "systemname", 'vm_name': None}, "ParameterError: mandatory parameter 'vm_name' is missing"),
    # hmc_host is missing
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'state': 'absent',
      'system_name': "systemname", 'vm_name': "vm_name"}, "ParameterError: mandatory parameter 'hmc_host' is missing"),
    # hmc_auth is missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': None, 'state': 'absent',
      'system_name': "systemname", 'vm_name': "vmname"}, "ParameterError: mandatory parameter 'hmc_auth' is missing"),
    # unsupported parameter os_type,proc,mem
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'absent',
      'system_name': "systemname", 'vm_name': 'vmname', 'proc': '4', 'mem':
      '1024', 'os_type': 'aix_linux', 'proc_unit': '4', 'prof_name': 'default', 'keylock': 'manual', 'iIPLsource': 'a',
      'volume_config': volume_config, 'virt_network_config': virt_network_config, 'all_resources': True, 'max_virtual_slots': 25, 'advanced_info': True},
     "ParameterError: unsupported parameters: proc, mem, os_type, proc_unit, prof_name, keylock, iIPLsource, volume_config, virt_network_config,"
     " all_resources, max_virtual_slots, advanced_info")]
test_data2 = [
    # ALL Shutdown partition testdata
    # system_name value is missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'action': 'shutdown', 'state': None,
      'system_name': None, 'vm_name': "vmname"}, "ParameterError: mandatory parameter 'system_name' is missing"),
    # vmname value is missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'action': 'shutdown', 'state': None,
      'system_name': "systemname", 'vm_name': None}, "ParameterError: mandatory parameter 'vm_name' is missing"),
    # hmc_host value is missing
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'action': 'shutdown', 'state': None,
      'system_name': "systemname", 'vm_name': "vm_name"}, "ParameterError: mandatory parameter 'hmc_host' is missing"),
    # hmc_auth value is missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': None, 'action': 'shutdown', 'state': None,
      'system_name': "systemname", 'vm_name': "vmname"}, "ParameterError: mandatory parameter 'hmc_auth' is missing"),
    # unsupported parameter os_type,proc,mem,prof_name,keylock,iIPLsource
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'action': 'shutdown', 'state': None,
      'system_name': "systemname", 'vm_name': 'vmname', 'proc': '4', 'mem':
      '1024', 'os_type': 'aix_linux', 'proc_unit': '4', 'prof_name': 'default', 'keylock': 'manual', 'iIPLsource': 'a',
      'volume_config': volume_config, 'virt_network_config': virt_network_config, 'retain_vios_cfg': True, 'delete_vdisks': True,
      'all_resources': True, 'max_virtual_slots': 25, 'advanced_info': True},
     "ParameterError: unsupported parameters: proc, mem, os_type, proc_unit, prof_name, keylock, iIPLsource, volume_config,"
     " virt_network_config, retain_vios_cfg, delete_vdisks, all_resources, max_virtual_slots, advanced_info")]
test_data3 = [
    # ALL Activate partition testdata
    # system name is missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': None, 'action': 'poweron',
      'system_name': None, 'vm_name': "vm_name"}, "ParameterError: mandatory parameter 'system_name' is missing"),
    # vmname is missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': None, 'action': 'poweron',
      'system_name': "systemname", 'vm_name': None}, "ParameterError: mandatory parameter 'vm_name' is missing"),
    # hmc_host is missing
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'state': None, 'action': 'poweron',
      'system_name': "systemname", 'vm_name': "vm_name"}, "ParameterError: mandatory parameter 'hmc_host' is missing"),
    # hmc_auth is missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': None, 'state': None, 'action': 'poweron',
      'system_name': "systemname", 'vm_name': "vmname"}, "ParameterError: mandatory parameter 'hmc_auth' is missing"),
    # unsupported parameter os_type,proc,mem
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': None, 'action': 'poweron',
      'system_name': "systemname", 'vm_name': 'vmname', 'proc': '4', 'mem':
      '1024', 'os_type': 'aix_linux', 'proc_unit': '4', 'volume_config': volume_config, 'virt_network_config': 'test_vn_name',
      'retain_vios_cfg': True, 'delete_vdisks': True, 'all_resources': True, 'max_virtual_slots': 25, 'advanced_info': True},
     "ParameterError: unsupported parameters: proc, mem, os_type, proc_unit, volume_config, virt_network_config, retain_vios_cfg, delete_vdisks,"
     " all_resources, max_virtual_slots, advanced_info")]


def common_mock_setup(mocker):
    hmc_powervm = importlib.import_module(IMPORT_HMC_POWERVM)
    mocker.patch.object(hmc_powervm, 'HmcCliConnection')
    mocker.patch.object(hmc_powervm, 'HmcRestClient', autospec=True)
    return hmc_powervm


@pytest.mark.parametrize("powervm_test_input, expectedError", test_data)
def test_call_inside_powervm_create_partition(mocker, powervm_test_input, expectedError):
    hmc_powervm = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            hmc_powervm.create_partition(hmc_powervm, powervm_test_input)
        assert expectedError == repr(e.value)
    else:
        hmc_powervm.create_partition(hmc_powervm, powervm_test_input)


@pytest.mark.parametrize("powervm_test_input, expectedError", test_data1)
def test_call_inside_powervm_delete_partition(mocker, powervm_test_input, expectedError):
    hmc_powervm = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            hmc_powervm.remove_partition(hmc_powervm, powervm_test_input)
        assert expectedError == repr(e.value)
    else:
        hmc_powervm.remove_partition(hmc_powervm, powervm_test_input)


@pytest.mark.parametrize("powervm_test_input, expectedError", test_data2)
def test_call_inside_powervm_poweroff_partition(mocker, powervm_test_input, expectedError):
    hmc_powervm = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            hmc_powervm.poweroff_partition(hmc_powervm, powervm_test_input)
        assert expectedError == repr(e.value)
    else:
        hmc_powervm.poweroff_partition(hmc_powervm, powervm_test_input)


@pytest.mark.parametrize("powervm_test_input, expectedError", test_data3)
def test_call_inside_powervm_poweron_partition(mocker, powervm_test_input, expectedError):
    hmc_powervm = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            hmc_powervm.poweron_partition(hmc_powervm, powervm_test_input)
        assert expectedError == repr(e.value)
    else:
        hmc_powervm.poweron_partition(hmc_powervm, powervm_test_input)
