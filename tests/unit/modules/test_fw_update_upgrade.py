from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
import importlib

IMPORT_CECFW = "ansible_collections.ibm.power_hmc.plugins.modules.firmware_update"

from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError

hmc_auth = {'username': 'hscroot', 'password': 'password_value'}
test_data1 = [
    # All Update Firmware Testdata
    # when hostname is missing
    ({'hmc_host': None, 'level': None, 'hmc_auth': hmc_auth, 'remote_repo': {'hostname': None, 'userid': None, 'directory': None, 'passwd': None}, 'state': 'updated', 'system_name': "system_name", 'repository': "ibmiwebsite"},
      "missing required arguments: hmc_host"),
    # when  hmc_auth is missing
    ({'hmc_host': 'hmc_host', 'level': None, 'hmc_auth': {'username': None, 'password': None}
, 'remote_repo': {'hostname': None, 'userid': None, 'directory': None, 'passwd': None}, 'state': 'updated', 'system_name': "system_name", 'repository': "ibmiwebsite"},
      "missing required arguments: hmc_auth"),
    # when system_name is missing
    ({'hmc_host': None, 'level': None, 'hmc_auth': hmc_auth, 'remote_repo': {'hostname': None, 'userid': None, 'directory': None, 'passwd': None}, 'state': 'updated', 'system_name': None, 'repository': "ibmiwebsite"},
      "missing required arguments: system_name"),
    # when remote_repo mentioned with ibmwebsite repository
    ({'hmc_host': 'hmc_host', 'level': None, 'hmc_auth': hmc_auth, 'remote_repo': {'hostname': 'hostname', 'userid': 'username', 'directory': 'directory', 'passwd': 'passwd'}, 'state': 'updated', 'system_name': None, 'repository': 'ibmiwebsite'},
      "Value 'ibmwebsite' is incompatible with any 'remote_repo' arguments"),
    # when both sshkey_file & password are mentioned for sftp website
    ({'hmc_host': 'hmc_host', 'level': None, 'hmc_auth': hmc_auth, 'remote_repo': {'hostname': 'hostname', 'userid': 'username', 'directory': 'directory', 'passwd': 'passwd', 'sshkey_file': 'sshkey_file'}, 'state': 'updated', 'system_name': 'system_name', 'repository': "sftp"},
      "'passwd' and 'sshkey_file' are  mutually exclusive"),
    # when sshkey_file mentioned with ftp type
    ({'hmc_host': 'hmc_host', 'level': None, 'hmc_auth': hmc_auth, 'remote_repo': {'hostname': 'hostname', 'userid': 'username', 'directory': 'directory', 'passwd': 'passwd', 'sshkey_file': None}, 'state': 'updated', 'system_name': 'system_name', 'repository': "ftp"},
      "'repository:ftp' and 'sshkey_file' are  incompatible"),
    # when hostname is missing in remote_repo
    ({'hmc_host': None, 'level': None, 'hmc_auth': hmc_auth, 'remote_repo': {'hostname': None, 'userid': 'userid', 'directory': 'directory', 'passwd': 'passwd'}, 'state': 'updated', 'system_name': "system_name", 'repository': "sftp"},
      "missing required arguments: hostname found in remote_repo"),
    # when userid is missing in remote_repo
    ({'hmc_host': None, 'level': None, 'hmc_auth': hmc_auth, 'remote_repo': {'hostname': 'hostname', 'userid': None, 'directory': 'directory', 'passwd': 'passwd'}, 'state': 'updated', 'system_name': "system_name", 'repository': "sftp"},
      "missing required arguments: hostname found in remote_repo"),
    # when directory is missing in remote_repo
    ({'hmc_host': None, 'level': None, 'hmc_auth': hmc_auth, 'remote_repo': {'hostname': 'hostname', 'userid': 'userid', 'directory': None, 'passwd': 'passwd'}, 'state': 'updated', 'system_name': "system_name", 'repository': "sftp"},
      "missing required arguments: directory found in remote_repo")
]

test_data2 = [
    # All Upgrade Firmware Testdata
    # when hostname is missing
    ({'hmc_host': None, 'level': None, 'hmc_auth': hmc_auth, 'remote_repo': {'hostname': None, 'userid': None, 'directory': None, 'passwd': None}, 'state': 'upgraded', 'system_name': "system_name", 'repository': "ibmiwebsite"},
      "missing required arguments: hmc_host"),
    # when  hmc_auth is missing
    ({'hmc_host': 'hmc_host', 'level': None, 'hmc_auth': {'username': None, 'password': None}
, 'remote_repo': {'hostname': None, 'userid': None, 'directory': None, 'passwd': None}, 'state': 'upgraded', 'system_name': "system_name", 'repository': "ibmiwebsite"},
      "missing required arguments: hmc_auth"),
    # when system_name is missing
    ({'hmc_host': None, 'level': None, 'hmc_auth': hmc_auth, 'remote_repo': {'hostname': None, 'userid': None, 'directory': None, 'passwd': None}, 'state': 'upgraded', 'system_name': None, 'repository': "ibmiwebsite"},
      "missing required arguments: system_name"),
    # when remote_repo mentioned with ibmwebsite repository
    ({'hmc_host': 'hmc_host', 'level': None, 'hmc_auth': hmc_auth, 'remote_repo': {'hostname': 'hostname', 'userid': 'username', 'directory': 'directory', 'passwd': 'passwd'}, 'state': 'upgraded', 'system_name': None, 'repository': 'ibmiwebsite'},
      "Value 'ibmwebsite' is incompatible with any 'remote_repo' arguments"),
    # when both sshkey_file & password are mentioned for sftp website
    ({'hmc_host': 'hmc_host', 'level': None, 'hmc_auth': hmc_auth, 'remote_repo': {'hostname': 'hostname', 'userid': 'username', 'directory': 'directory', 'passwd': 'passwd', 'sshkey_file': 'sshkey_file'}, 'state': 'upgraded', 'system_name': 'system_name', 'repository': "sftp"},
      "'passwd' and 'sshkey_file' are  mutually exclusive"),
    # when sshkey_file mentioned with ftp type
    ({'hmc_host': 'hmc_host', 'level': None, 'hmc_auth': hmc_auth, 'remote_repo': {'hostname': 'hostname', 'userid': 'username', 'directory': 'directory', 'passwd': 'passwd', 'sshkey_file': None}, 'state': 'upgraded', 'system_name': 'system_name', 'repository': "ftp"},
      "'repository:ftp' and 'sshkey_file' are  incompatible"),
    # when hostname is missing in remote_repo
    ({'hmc_host': None, 'level': None, 'hmc_auth': hmc_auth, 'remote_repo': {'hostname': None, 'userid': 'userid', 'directory': 'directory', 'passwd': 'passwd'}, 'state': 'upgraded', 'system_name': "system_name", 'repository': "sftp"},
      "missing required arguments: hostname found in remote_repo"),
    # when userid is missing in remote_repo
    ({'hmc_host': None, 'level': None, 'hmc_auth': hmc_auth, 'remote_repo': {'hostname': 'hostname', 'userid': None, 'directory': 'directory', 'passwd': 'passwd'}, 'state': 'upgraded', 'system_name': "system_name", 'repository': "sftp"},
      "missing required arguments: hostname found in remote_repo"),
     # when directory is missing in remote_repo
    ({'hmc_host': None, 'level': None, 'hmc_auth': hmc_auth, 'remote_repo': {'hostname': 'hostname', 'userid': 'userid', 'directory': None, 'passwd': 'passwd'}, 'state': 'upgraded', 'system_name': "system_name", 'repository': "sftp"},
      "missing required arguments: directory found in remote_repo")
]

test_data3 = [
    # All Accept Licence Firmware Testdata
    # when action & repository are mentioned
    ({'hmc_host': 'hmc_host', 'level': None, 'hmc_auth': hmc_auth, 'remote_repo': {'hostname': None, 'userid': None, 'directory': None, 'passwd': None}, 'state': None, 'action': 'accept', 'system_name': "system_name", 'repository': "ibmiwebsite"},
      "parameters are mutually exclusive: action|repository"),
    # when action & remote_repo are mentioned
    ({'hmc_host': 'hmc_host', 'level': None, 'hmc_auth': hmc_auth, 'remote_repo': {'hostname': 'hostname', 'userid': 'userid', 'directory': 'directory', 'passwd': 'passwd'}, 'state': None, 'action': 'accept', 'system_name': "system_name", 'repository': None},
      "parameters are mutually exclusive: action|repository"),
    # when action & level are mentioned
    ({'hmc_host': 'hmc_host', 'level': 'level', 'hmc_auth': hmc_auth, 'remote_repo': {'hostname': None, 'userid': None, 'directory': None, 'passwd': None}, 'state': None, 'action': 'accept', 'system_name': "system_name", 'repository': None},
      "parameters are mutually exclusive: action|level"),
    # when system_name is not mentioned
    ({'hmc_host': 'hmc_host', 'level': None, 'hmc_auth': hmc_auth, 'remote_repo': {'hostname': None, 'userid': None, 'directory': None, 'passwd': None}, 'state': None, 'action': 'accept', 'system_name': None, 'repository': None},
      "missing required arguments: system_name"),
    # when hmc_auth is not mentioned
    ({'hmc_host': 'hmc_host', 'level': None, 'hmc_auth': {'username': None, 'password': None}, 'remote_repo': {'hostname': None, 'userid': None, 'directory': None, 'passwd': None}, 'state': None, 'action': 'accept', 'system_name': 'system_name', 'repository': None},
      "missing required arguments: hmc_auth"),
    # when hmc_host is not mentioned
    ({'hmc_host': None, 'level': None, 'hmc_auth': hmc_auth, 'remote_repo': {'hostname': None, 'userid': None, 'directory': None, 'passwd': None}, 'state': None, 'action': 'accept', 'system_name': 'system_name', 'repository': None},
      "missing required arguments: hmc_host"),
    # when action & state is not mentioned
    ({'hmc_host': 'hmc_host', 'level': None, 'hmc_auth': hmc_auth, 'remote_repo': {'hostname': None, 'userid': None, 'directory': None, 'passwd': None}, 'state': 'state', 'action': 'accept', 'system_name': 'system_name', 'repository': None},
      "parameters are mutually exclusive: state|action")]
    

def common_mock_setup(mocker):
    cecfw_update_upgrade = importlib.import_module(IMPORT_CECFW)
    mocker.patch.object(cecfw_update_upgrade, 'HmcCliConnection')
    mocker.patch.object(cecfw_update_upgrade, 'Hmc', autospec=True)
#    mocker.patch.object(cecfw_update_upgrade, 'HmcRestClient', autospec=True)
    return cecfw_update_upgrade


@pytest.mark.parametrize("cecfw_test_input, expectedError", test_data1)
def test_call_inside_update_system(mocker, cecfw_test_input, expectedError):
    cecfw_update_upgrade = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            cecfw_update_upgrade.update_system(cecfw_update_upgrade, cecfw_test_input)
        assert expectedError == repr(e.value)
    else:
        cecfw_update_upgrade.update_system(cecfw_update_upgrade, cecfw_test_input)

@pytest.mark.parametrize("cecfw_test_input, expectedError", test_data2)
def test_call_inside_upgrade_system(mocker, cecfw_test_input, expectedError):
    cecfw_update_upgrade = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            cecfw_update_upgrade.upgrade_system(cecfw_update_upgrade, cecfw_test_input)
        assert expectedError == repr(e.value)
    else:
        cecfw_update_upgrade.upgrade_system(cecfw_update_upgrade, cecfw_test_input)

@pytest.mark.parametrize("cecfw_test_input, expectedError", test_data3)
def test_call_inside_accept_level(mocker, cecfw_test_input, expectedError):
    cecfw_update_upgrade = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            cecfw_update_upgrade.accept_level(cecfw_update_upgrade, cecfw_test_input)
        assert expectedError == repr(e.value)
    else:
        cecfw_update_upgrade.accept_level(cecfw_update_upgrade, cecfw_test_input)

