from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
import importlib

IMPORT_HMC_USER = "ansible_collections.ibm.power_hmc.plugins.modules.hmc_user"

from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError

hmc_auth = {'username': 'hscroot', 'password': 'password_value'}
policy_config = {'min_pwage': "int", 'pwage': "pwage", 'min_length': "min_value"}
test_data = [
    # All Facts related Testdata
    # when enable_user key is mentioned for facts state
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'facts', 'type': None, 'enable_user': None, 'attributes': None},
     "unsupported parameter: enable_user"),
    # when name and type: default is mentioned for facts state
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'facts', 'attributes': None, 'type': 'default', 'name': 'name',
      'enable_user': None}, "ParameterError: facts state will not support parameter: name with default type"),
    # when attributes key is mentioned for facts state
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'type': None, 'state': 'facts', 'attributes': None, 'enable_user': None},
     "unsupported parameter: attributes")]
test_data1 = [
    # All user creation TestData
    # when name is missing for present state
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'present', 'attributes': {'authentication_type': 'local'},
      'type': None, 'name': None}, "ParameterError: mandatory parameter 'name' is missing"),
    # when hmc_host is missing for present state
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'name': 'name', 'state': 'present', 'attributes': {'authentication_type': 'local'}, 'type': None},
     "ParameterError: mandatory parameter 'hmc_host' is missing"),
    # when atributes are missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'present', 'name': 'name', 'attributes': None},
     "ParameterError: mandatory parameter 'attributes' is missing"),
    # when hmc_auth is missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': {'username': None, 'password': None}, 'type': None, 'enable_user': None, 'state': 'present',
      'attributes': {'authentication_type': 'local', 'passwd': 'abcd1234', 'taskrole': 'hmcservicerep'}, 'name': 'name'},
     "missing required arguments: username found in hmc_auth"),
    # when enable_user is  mentioned
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'enable_user': True, 'state': 'present', 'type': None,
      'attributes': {'authentication_type': 'local', 'passwd': 'abcd1234', 'taskrole': 'hmcservicerep'}, 'name': 'name'},
     "ParameterError: unsupported parameter: enable_user"),
    # when passwd is missing in attributes for present state
    ({'hmc_host': "0.0.0.0", 'enable_user': None, 'hmc_auth': hmc_auth, 'name': 'name', 'state': 'present',
      'attributes': {'authentication_type': 'local'}, 'type': None}, "ParameterError: 'passwd' attribute is mandatory"),
    # when taskrole is missing in attributes for present state
    ({'hmc_host': "0.0.0.0", 'enable_user': None, 'hmc_auth': hmc_auth, 'name': 'name', 'state': 'present',
      'attributes': {'authentication_type': 'local', 'passwd': 'abc123'}, 'type': None}, "ParameterError: mandatory parameter taskrole is missing")]
test_data2 = [
    # All user deletion testdata
    # when name & type are  missing for absent state
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'absent', 'type': None, 'name': None, 'enable_user': None,
      'attributes': None}, "ParameterError: absent state need either name or type parameter"),
    # when enable_user is mentioned for absent state
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'absent', 'enable_user': True, 'type': None, 'name': 'name',
      'attributes': None}, "ParameterError: unsupported parameter: enable_user"),
    # when attributes dict added for absent state
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'absent', 'type': None, 'enable_user': None,
      'attributes': {'authentication_type': 'name'}}, "ParameterError: unsupported parameter: attributes")]
test_data3 = [
    # All user modification testdata
    # when name is missing for updated state
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'updated', 'attributes': {'authentication_type': 'name'},
      'enable_user': None, 'name': None, 'type': None}, "ParameterError: updated state need parameter: name with non default settings"),
    # when attributes dict is mentioned with name & attributes have max_webui_login_attempts , webui_login_suspend_time
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'updated', 'attributes': {'webui_login_suspend_time': 3,
      'max_webui_login_attempts': 4, 'session_timeout': None, 'idle_timeout': None}, 'enable_user': None, 'name': 'name', 'type': None},
     "ParameterError: updated state with parameter:name will not support attributes: webui_login_suspend_time,max_webui_login_attempts"),
    # when attributes dict is mentioned with name & attributes have max_webui_login_attempts , webui_login_suspend_time
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'updated', 'attributes': {'authentication_type': 'local', 'passwd': 'abcd1234',
      'max_webui_login_attempts': None, 'webui_login_suspend_time': None, 'session_timeout': None, 'idle_timeout': None}, 'enable_user': None,
      'name': 'name', 'type': 'default'},
     "ParameterError: updated state will support only attributes: webui_login_suspend_time,max_webui_login_attempts,session_timeout,"
     "idle_timeout for default type"),
    # when attributes dict and enable_user is not added for updated state
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'state': 'updated', 'attributes': None, 'enable_user': None, 'name': 'name', 'type': None},
     "ParameterError: updated state with parameter: name either need enable_user or attributes param")]


def common_mock_setup(mocker):
    hmc_user = importlib.import_module(IMPORT_HMC_USER)
    mocker.patch.object(hmc_user, 'HmcCliConnection')
    mocker.patch.object(hmc_user, 'Hmc', autospec=True)
    return hmc_user


@pytest.mark.parametrize("user_test_input, expectedError", test_data)
def test_call_inside_facts(mocker, user_test_input, expectedError):
    hmc_user = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            hmc_user.facts(hmc_user, user_test_input)
        assert expectedError == repr(e.value)
    else:
        hmc_user.facts(hmc_user, user_test_input)


@pytest.mark.parametrize("user_test_input, expectedError", test_data1)
def test_call_inside_ensure_present(mocker, user_test_input, expectedError):
    hmc_user = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            hmc_user.ensure_present(hmc_user, user_test_input)
        assert expectedError == repr(e.value)
    else:
        hmc_user.ensure_present(hmc_user, user_test_input)


@pytest.mark.parametrize("user_test_input, expectedError", test_data2)
def test_call_inside_ensure_absent(mocker, user_test_input, expectedError):
    hmc_user = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            hmc_user.ensure_absent(hmc_user, user_test_input)
        assert expectedError == repr(e.value)
    else:
        hmc_user.ensure_absent(hmc_user, user_test_input)


@pytest.mark.parametrize("user_test_input, expectedError", test_data3)
def test_call_inside_ensure_update(mocker, user_test_input, expectedError):
    hmc_user = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            hmc_user.ensure_update(hmc_user, user_test_input)
        assert expectedError == repr(e.value)
    else:
        hmc_user.ensure_update(hmc_user, user_test_input)
