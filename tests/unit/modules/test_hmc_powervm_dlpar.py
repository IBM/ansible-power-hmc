import pytest
import importlib

IMPORT_DLPAR = "ansible_collections.ibm.power_hmc.plugins.modules.powervm_dlpar"

from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError

hmc_auth = {'username': 'hscroot', 'password': 'password_value'}

pv_settings = ['1', '2']
npiv_settings = ['1', '2']
vod_settings = ['1', '2']
proc_settings = {'proc': 3, 'proc_unit': 2.5, 'sharing_mode': 'uncapped', 'uncapped_weight': 131, 'pool_id': 2}
mem_settings = {'mem': 3072}

test_data = [
    # All update_proc_mem related Testdata
    # when hmc_host key is not mentioned for update_proc_mem action
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'action': 'update_proc_mem', 'system_name': 'system_name',
      'vm_name': 'vm_name', 'proc_settings': proc_settings, 'mem_settings': mem_settings,
      'timeout': 123, 'pv_settings': None, 'npiv_settings': None, 'vod_settings': None},
     "ParameterError: mandatory parameter 'hmc_host' is missing"),
    # when system_name key is not mentioned for update_proc_mem action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_proc_mem', 'system_name': None,
      'vm_name': 'vm_name', 'proc_settings': proc_settings, 'mem_settings': mem_settings,
      'timeout': 123, 'pv_settings': None, 'npiv_settings': None, 'vod_settings': None},
     "ParameterError: mandatory parameter 'system_name' is missing"),
    # when vm_name key is not mentioned for update_proc_mem action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_proc_mem', 'system_name': 'system_name',
      'vm_name': None, 'proc_settings': proc_settings, 'mem_settings': mem_settings,
      'timeout': 123, 'pv_settings': None, 'npiv_settings': None, 'vod_settings': None},
     "ParameterError: mandatory parameter 'vm_name' is missing"),
    # when pv_settings key is not mentioned for update_proc_mem action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_proc_mem', 'system_name': 'system_name',
      'vm_name': 'vm_name', 'proc_settings': None, 'mem_settings': None,
      'timeout': 123, 'pv_settings': pv_settings, 'npiv_settings': None, 'vod_settings': None},
     "ParameterError: unsupported parameter: pv_settings"),
    # when npiv_settings key mentioned for update_proc_mem action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_proc_mem', 'system_name': 'system_name',
      'vm_name': 'vm_name', 'proc_settings': None, 'mem_settings': None,
      'timeout': 123, 'pv_settings': None, 'npiv_settings': npiv_settings, 'vod_settings': None},
     "ParameterError: unsupported parameter: npiv_settings"),
    # when vod_settings key mentioned for update_proc_mem action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_proc_mem', 'system_name': 'system_name',
      'vm_name': 'vm_name', 'proc_settings': None, 'mem_settings': None,
      'timeout': 123, 'pv_settings': None, 'npiv_settings': None, 'vod_settings': vod_settings},
     "ParameterError: unsupported parameter: vod_settings"),
]

test_data1 = [
    # All update_pv related Testdata
    # when hmc_host key is not mentioned for update_pv action
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'action': 'update_pv', 'system_name': 'system_name',
      'vm_name': 'vm_name', 'proc_settings': proc_settings, 'mem_settings': mem_settings,
      'timeout': 123, 'pv_settings': pv_settings, 'npiv_settings': None, 'vod_settings': None},
     "ParameterError: mandatory parameter 'hmc_host' is missing"),
    # when system_name key is not mentioned for update_pv action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_pv', 'system_name': None,
      'vm_name': 'vm_name', 'proc_settings': proc_settings, 'mem_settings': mem_settings,
      'timeout': 123, 'pv_settings': pv_settings, 'npiv_settings': None, 'vod_settings': None},
     "ParameterError: mandatory parameter 'system_name' is missing"),
    # when vm_name key is not mentioned for update_pv action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_pv', 'system_name': 'system_name',
      'vm_name': None, 'proc_settings': proc_settings, 'mem_settings': mem_settings,
      'timeout': 123, 'pv_settings': pv_settings, 'npiv_settings': None, 'vod_settings': None},
     "ParameterError: mandatory parameter 'vm_name' is missing"),
    # when pv_settings key is not mentioned for update_pv action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_pv', 'system_name': 'system_name',
      'vm_name': 'vm_name', 'proc_settings': None, 'mem_settings': mem_settings,
      'timeout': 123, 'pv_settings': None, 'npiv_settings': None, 'vod_settings': None},
     "ParameterError: mandatory parameter 'pv_settings' is missing"),
    # when proc_settings key is mentioned for update_pv action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_pv', 'system_name': 'system_name',
      'vm_name': 'vm_name', 'proc_settings': proc_settings, 'mem_settings': None,
      'timeout': 123, 'pv_settings': pv_settings, 'npiv_settings': None, 'vod_settings': None},
     "ParameterError: unsupported parameter: proc_settings"),
    # when npiv_settings key mentioned for update_pv action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_pv', 'system_name': 'system_name',
      'vm_name': 'vm_name', 'proc_settings': None, 'mem_settings': None,
      'timeout': 123, 'pv_settings': pv_settings, 'npiv_settings': npiv_settings, 'vod_settings': None},
     "ParameterError: unsupported parameter: npiv_settings"),
    # when vod_settings key mentioned for update_pv action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_pv', 'system_name': 'system_name',
      'vm_name': 'vm_name', 'proc_settings': None, 'mem_settings': None,
      'timeout': 123, 'pv_settings': pv_settings, 'npiv_settings': None, 'vod_settings': vod_settings},
     "ParameterError: unsupported parameter: vod_settings"),
    # when mem_settings key mentioned for update_pv action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_pv', 'system_name': 'system_name',
      'vm_name': 'vm_name', 'proc_settings': None, 'mem_settings': mem_settings,
      'timeout': 123, 'pv_settings': pv_settings, 'npiv_settings': None, 'vod_settings': None},
     "ParameterError: unsupported parameter: mem_settings"),
]

test_data2 = [
    # All update_npiv related Testdata
    # when hmc_host key is not mentioned for update_npiv action
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'action': 'update_npiv', 'system_name': 'system_name',
      'vm_name': 'vm_name', 'proc_settings': proc_settings, 'mem_settings': mem_settings,
      'timeout': 123, 'pv_settings': None, 'npiv_settings': npiv_settings, 'vod_settings': None},
     "ParameterError: mandatory parameter 'hmc_host' is missing"),
    # when system_name key is not mentioned for update_npiv action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_npiv', 'system_name': None,
      'vm_name': 'vm_name', 'proc_settings': proc_settings, 'mem_settings': mem_settings,
      'timeout': 123, 'pv_settings': None, 'npiv_settings': npiv_settings, 'vod_settings': None},
     "ParameterError: mandatory parameter 'system_name' is missing"),
    # when vm_name key is not mentioned for update_npiv action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_npiv', 'system_name': 'system_name',
      'vm_name': None, 'proc_settings': proc_settings, 'mem_settings': mem_settings,
      'timeout': 123, 'pv_settings': None, 'npiv_settings': npiv_settings, 'vod_settings': None},
     "ParameterError: mandatory parameter 'vm_name' is missing"),
    # when npiv_settings key is not mentioned for update_npiv action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_npiv', 'system_name': 'system_name',
      'vm_name': 'vm_name', 'proc_settings': None, 'mem_settings': mem_settings,
      'timeout': 123, 'pv_settings': None, 'npiv_settings': None, 'vod_settings': None},
     "ParameterError: mandatory parameter 'npiv_settings' is missing"),
    # when proc_settings key is mentioned for update_npiv action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_npiv', 'system_name': 'system_name',
      'vm_name': 'vm_name', 'proc_settings': proc_settings, 'mem_settings': None,
      'timeout': 123, 'pv_settings': None, 'npiv_settings': npiv_settings, 'vod_settings': None},
     "ParameterError: unsupported parameter: proc_settings"),
    # when pv_settings key mentioned for update_npiv action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_npiv', 'system_name': 'system_name',
      'vm_name': 'vm_name', 'proc_settings': None, 'mem_settings': None,
      'timeout': 123, 'pv_settings': pv_settings, 'npiv_settings': npiv_settings, 'vod_settings': None},
     "ParameterError: unsupported parameter: pv_settings"),
    # when vod_settings key mentioned for update_npiv action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_npiv', 'system_name': 'system_name',
      'vm_name': 'vm_name', 'proc_settings': None, 'mem_settings': None,
      'timeout': 123, 'pv_settings': None, 'npiv_settings': npiv_settings, 'vod_settings': vod_settings},
     "ParameterError: unsupported parameter: vod_settings"),
    # when mem_settings key mentioned for update_npiv action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_npiv', 'system_name': 'system_name',
      'vm_name': 'vm_name', 'proc_settings': None, 'mem_settings': mem_settings,
      'timeout': 123, 'pv_settings': None, 'npiv_settings': npiv_settings, 'vod_settings': None},
     "ParameterError: unsupported parameter: mem_settings"),
]

test_data3 = [
    # All update_vod related Testdata
    # when hmc_host key is not mentioned for update_vod action
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'action': 'update_vod', 'system_name': 'system_name',
      'vm_name': 'vm_name', 'proc_settings': proc_settings, 'mem_settings': mem_settings,
      'timeout': 123, 'pv_settings': None, 'npiv_settings': None, 'vod_settings': vod_settings},
     "ParameterError: mandatory parameter 'hmc_host' is missing"),
    # when system_name key is not mentioned for update_vod action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_vod', 'system_name': None,
      'vm_name': 'vm_name', 'proc_settings': proc_settings, 'mem_settings': mem_settings,
      'timeout': 123, 'pv_settings': None, 'npiv_settings': None, 'vod_settings': vod_settings},
     "ParameterError: mandatory parameter 'system_name' is missing"),
    # when vm_name key is not mentioned for update_vod action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_vod', 'system_name': 'system_name',
      'vm_name': None, 'proc_settings': proc_settings, 'mem_settings': mem_settings,
      'timeout': 123, 'pv_settings': None, 'npiv_settings': None, 'vod_settings': vod_settings},
     "ParameterError: mandatory parameter 'vm_name' is missing"),
    # when vod_settings key is not mentioned for update_vod action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_vod', 'system_name': 'system_name',
      'vm_name': 'vm_name', 'proc_settings': None, 'mem_settings': mem_settings,
      'timeout': 123, 'pv_settings': None, 'npiv_settings': None, 'vod_settings': None},
     "ParameterError: mandatory parameter 'vod_settings' is missing"),
    # when proc_settings key is mentioned for update_vod action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_vod', 'system_name': 'system_name',
      'vm_name': 'vm_name', 'proc_settings': proc_settings, 'mem_settings': None,
      'timeout': 123, 'pv_settings': None, 'npiv_settings': None, 'vod_settings': vod_settings},
     "ParameterError: unsupported parameter: proc_settings"),
    # when npiv_settings key mentioned for update_vod action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_vod', 'system_name': 'system_name',
      'vm_name': 'vm_name', 'proc_settings': None, 'mem_settings': None,
      'timeout': 123, 'pv_settings': None, 'npiv_settings': npiv_settings, 'vod_settings': vod_settings},
     "ParameterError: unsupported parameter: npiv_settings"),
    # when pv_settings key mentioned for update_vod action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_vod', 'system_name': 'system_name',
      'vm_name': 'vm_name', 'proc_settings': None, 'mem_settings': None,
      'timeout': 123, 'pv_settings': pv_settings, 'npiv_settings': None, 'vod_settings': vod_settings},
     "ParameterError: unsupported parameter: pv_settings"),
    # when mem_settings key mentioned for update_vod action
    ({'hmc_host': '0.0.0.0', 'hmc_auth': hmc_auth, 'action': 'update_vod', 'system_name': 'system_name',
      'vm_name': 'vm_name', 'proc_settings': None, 'mem_settings': mem_settings,
      'timeout': 123, 'pv_settings': None, 'npiv_settings': None, 'vod_settings': vod_settings},
     "ParameterError: unsupported parameter: mem_settings"),
]


def common_mock_setup(mocker):
    powervm_dlpar = importlib.import_module(IMPORT_DLPAR)
    mocker.patch.object(powervm_dlpar, 'HmcRestClient')
    return powervm_dlpar


@pytest.mark.parametrize("user_test_input, expectedError", test_data)
def test_call_inside_update_proc_mem(mocker, user_test_input, expectedError):
    powervm_dlpar = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            powervm_dlpar.update_proc_mem(powervm_dlpar, user_test_input)
        assert expectedError == repr(e.value)
    else:
        powervm_dlpar.update_proc_mem(powervm_dlpar, user_test_input)


@pytest.mark.parametrize("user_test_input, expectedError", test_data1)
def test_call_inside_update_pv(mocker, user_test_input, expectedError):
    powervm_dlpar = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            powervm_dlpar.update_pv(powervm_dlpar, user_test_input)
        assert expectedError == repr(e.value)
    else:
        powervm_dlpar.update_pv(powervm_dlpar, user_test_input)


@pytest.mark.parametrize("user_test_input, expectedError", test_data2)
def test_call_inside_update_npiv(mocker, user_test_input, expectedError):
    powervm_dlpar = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            powervm_dlpar.update_npiv(powervm_dlpar, user_test_input)
        assert expectedError == repr(e.value)
    else:
        powervm_dlpar.update_npiv(powervm_dlpar, user_test_input)


@pytest.mark.parametrize("user_test_input, expectedError", test_data3)
def test_call_inside_update_vod(mocker, user_test_input, expectedError):
    powervm_dlpar = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            powervm_dlpar.update_vod(powervm_dlpar, user_test_input)
        assert expectedError == repr(e.value)
    else:
        powervm_dlpar.update_vod(powervm_dlpar, user_test_input)
