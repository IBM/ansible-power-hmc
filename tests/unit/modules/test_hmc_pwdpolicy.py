from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
import importlib

IMPORT_HMC_PWDPOLICY = "ansible_collections.ibm.power_hmc.plugins.modules.hmc_pwdpolicy"

from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError

hmc_auth = {'username': 'hscroot', 'password': 'password_value'}
policy_config = {'min_pwage': "int", 'pwage': "pwage", 'min_length': "min_value"}
test_data = [
    # policy_name is mentioned
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'facts', 'policy_type': 'policy_type', 'policy_name': 'policy_name',
      'policy_config': None}, "ParameterError: not supporting policy_name option"),
    # policy_config is mentioned
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'facts', 'policy_type': 'policy_type', 'policy_name': None,
      'policy_config': 'policy_config'}, "ParameterError: not supporting policy_config option"),
    # policy_type  is not mentioned
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'facts', 'policy_type': None, 'policy_name': None, 'policy_config': None},
     "state is facts but all of the following are missing: policy_type"),
    # hmc_host is not mentioned
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'state': 'facts', 'policy_type': 'policy_type', 'policy_name': None, 'policy_config': None},
     "missing required arguments: hmc_host"),
    # hmc_auth is not mentioned
    ({'hmc_host': "0.0.0.0", 'hmc_auth': {'username': None, 'password': None}, 'state': 'facts', 'policy_type': 'policy_type',
      'policy_name': None, 'policy_config': None}, "missing required arguments: hmc_auth")]
test_data1 = [
    # Ensure that password policy exists in hmc
    # policy_type is mentioned
    ({'hmc_host': "0.0.0.0", 'policy_type': 'policies', 'hmc_auth': hmc_auth, 'state': 'present', 'policy_name': 'policy_name',
      'policy_config': 'policy_config'}, "ParameterError: not supporting policy_type option"),
    # hmc_host is not mentioned
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'state': 'facts', 'policy_type': None, 'policy_name': None, 'policy_config': None},
     "missing required arguments: hmc_host"),
    # hmc_auth is not mentioned
    ({'hmc_host': "0.0.0.0", 'hmc_auth': {'username': None, 'password': None}, 'state': 'facts', 'policy_type': None, 'policy_name': None,
      'policy_config': None}, "missing required arguments: hmc_auth")]
test_data2 = [
    # Delete Password Policy
    # policy_config is  mentioned
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'absent', 'policy_type': None, 'policy_name': None,
      'policy_config': policy_config}, "ParameterError: not supporting policy_config option"),
    # policy_type is mentioned
    ({'hmc_host': "0.0.0.0", 'policy_type': None, 'hmc_auth': hmc_auth, 'state': 'absent', 'policy_name': None, 'policy_config': None},
     "Parameter Error: given policy does not exist"),
    # policy_type is mentioned
    ({'hmc_host': "0.0.0.0", 'policy_type': 'policies', 'hmc_auth': hmc_auth, 'state': 'absent', 'policy_name': 'policy_name'},
     "ParameterError: not supporting policy_type option")]

test_data3 = [
    # policy_type is mentioned
    ({'hmc_host': "0.0.0.0", 'policy_type': 'policies', 'hmc_auth': hmc_auth, 'state': 'activated', 'policy_name': 'policy_name'},
     "ParameterError: not supporting policy_type option"),
    # policy_config is  mentioned
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'activated', 'policy_type': None, 'policy_name': None,
      'policy_config': policy_config}, "ParameterError: not supporting policy_config option"),
    # policy_name is not mentioned
    ({'hmc_host': "0.0.0.0", 'policy_type': None, 'hmc_auth': hmc_auth, 'state': 'activated', 'policy_name': None, 'policy_config': None},
     "ParameterError: given policy does not exist")]

test_data4 = [
    # policy_type is mentioned
    ({'hmc_host': "0.0.0.0", 'policy_type': 'policies', 'hmc_auth': hmc_auth, 'state': 'deactivated', 'policy_name': 'policy_name'},
     "ParameterError: not supporting policy_type option"),
    # policy_config is  mentioned
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'deactivated', 'policy_type': None, 'policy_name': None,
      'policy_config': policy_config}, "ParameterError: not supporting policy_config option"),
    # policy_name is  mentioned
    ({'hmc_host': "0.0.0.0", 'policy_type': None, 'hmc_auth': hmc_auth, 'state': 'deactivated', 'policy_name': 'policy_name',
      'policy_config': None}, "ParameterError: not supporting policy_name option")]
test_data5 = [
    # policy_type is mentioned
    ({'hmc_host': "0.0.0.0", 'policy_type': 'policies', 'hmc_auth': hmc_auth, 'state': 'modified', 'policy_name': 'policy_name',
      'policy_config': policy_config}, "ParameterError: not supporting policy_type option"),
    # when policy_nam is not mentioned
    ({'hmc_host': "0.0.0.0", 'policy_type': None, 'hmc_auth': hmc_auth, 'state': 'modified', 'policy_name': None,
      'policy_config': policy_config}, "ParameterError: given policy does not exist"),
    # when policy_name is not mentioned
    ({'hmc_host': "0.0.0.0", 'policy_type': None, 'hmc_auth': hmc_auth, 'state': 'modified', 'policy_name': 'policy_name',
      'policy_config': {'min_pwage': None, 'pwage': None, 'min_length': None}}, "ParameterError: given policy does not exist")]


def common_mock_setup(mocker):
    hmc_pwdpolicy = importlib.import_module(IMPORT_HMC_PWDPOLICY)
    mocker.patch.object(hmc_pwdpolicy, 'HmcCliConnection')
    mocker.patch.object(hmc_pwdpolicy, 'Hmc', autospec=True)
    return hmc_pwdpolicy


@pytest.mark.parametrize("pwdpolicy_test_input, expectedError", test_data)
def test_call_inside_facts(mocker, pwdpolicy_test_input, expectedError):
    hmc_pwdpolicy = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            hmc_pwdpolicy.facts(hmc_pwdpolicy, pwdpolicy_test_input)
        assert expectedError == repr(e.value)
    else:
        hmc_pwdpolicy.facts(hmc_pwdpolicy, pwdpolicy_test_input)


@pytest.mark.parametrize("pwdpolicy_test_input, expectedError", test_data1)
def test_call_inside_ensure_present(mocker, pwdpolicy_test_input, expectedError):
    hmc_pwdpolicy = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            hmc_pwdpolicy.ensure_present(hmc_pwdpolicy, pwdpolicy_test_input)
        assert expectedError == repr(e.value)
    else:
        hmc_pwdpolicy.ensure_present(hmc_pwdpolicy, pwdpolicy_test_input)


@pytest.mark.parametrize("pwdpolicy_test_input, expectedError", test_data2)
def test_call_inside_ensure_absent(mocker, pwdpolicy_test_input, expectedError):
    hmc_pwdpolicy = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            hmc_pwdpolicy.ensure_absent(hmc_pwdpolicy, pwdpolicy_test_input)
        assert expectedError == repr(e.value)
    else:
        hmc_pwdpolicy.ensure_absent(hmc_pwdpolicy, pwdpolicy_test_input)


@pytest.mark.parametrize("pwdpolicy_test_input, expectedError", test_data3)
def test_call_inside_ensure_activate(mocker, pwdpolicy_test_input, expectedError):
    hmc_pwdpolicy = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            hmc_pwdpolicy.ensure_activate(hmc_pwdpolicy, pwdpolicy_test_input)
        assert expectedError == repr(e.value)
    else:
        hmc_pwdpolicy.ensure_activate(hmc_pwdpolicy, pwdpolicy_test_input)


@pytest.mark.parametrize("pwdpolicy_test_input, expectedError", test_data4)
def test_call_inside_ensure_deactivate(mocker, pwdpolicy_test_input, expectedError):
    hmc_pwdpolicy = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            hmc_pwdpolicy.ensure_deactivate(hmc_pwdpolicy, pwdpolicy_test_input)
        assert expectedError == repr(e.value)
    else:
        hmc_pwdpolicy.ensure_deactivate(hmc_pwdpolicy, pwdpolicy_test_input)


@pytest.mark.parametrize("pwdpolicy_test_input, expectedError", test_data5)
def test_call_inside_ensure_updation(mocker, pwdpolicy_test_input, expectedError):
    hmc_pwdpolicy = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            hmc_pwdpolicy.ensure_updation(hmc_pwdpolicy, pwdpolicy_test_input)
        assert expectedError == repr(e.value)
    else:
        hmc_pwdpolicy.ensure_updation(hmc_pwdpolicy, pwdpolicy_test_input)
