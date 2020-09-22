from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
import importlib

IMPORT_HMC_BUILD_MANAGER = "ansible_collections.ibm.power_hmc.plugins.modules.hmc_build_manager"

from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError

hmc_auth = {'username': 'hscroot', 'password': 'password_value'}
test_data = [

    # All SFTP related testdata
    # host name is missed
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'sftp', 'build_file': 'path', 'hostname': None, 'mount_location': 'data',\
      'userid': 'data', 'passwd': 'data', 'sshkey_file': None, 'restart': None}},\
     "ParameterError: mandatory parameter 'hostname' is missing"),

    # userid is missed
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'sftp', 'build_file': 'path', 'hostname': '0.0.0.0',\
      'mount_location': 'data', 'userid': None, 'passwd': 'data', 'sshkey_file': None, 'restart': None}},\
     "ParameterError: mandatory parameter 'userid' is missing"),

    # passwd and sshkey_file is missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'sftp', 'build_file': 'path', 'hostname': '0.0.0.0',\
      'mount_location': 'data', 'userid': None, 'passwd': None, 'sshkey_file': None, 'restart': None}},\
     "ParameterError: mandatory parameter 'passwd' or 'sshkey_file' is missing"),

    # passwd and sskjey information passed
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'sftp', 'build_file': 'path', 'hostname': '0.0.0.0',\
      'mount_location': 'data', 'passwd': "abcd1234", 'sshkey_file': "None", 'restart': None}},\
     "ParameterError: conflicting parameters 'passwd' and 'sshkey_file'. Provide any one"),

    # mount_location are mentioned in sftp
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'sftp', 'build_file': 'path', 'hostname': '0.0.0.0',\
      'mount_location': 'data', 'userid': 'test', 'passwd': 'data', 'sshkey_file': None, 'restart': None}},\
     "ParameterError: unsupported parameter: mount_location"),

    # build_file is not mentioned in sftp
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'sftp', 'build_file': None, 'hostname': '0.0.0.0',\
      'mount_location': 'data', 'userid': 'test', 'passwd': 'data', 'sshkey_file': None, 'restart': None}},\
     "ParameterError: mandatory parameter 'build_file' is missing"),

    # All FTP related testdata
    # host name is missed
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'ftp', 'build_file': 'path', 'hostname': None, 'mount_location': 'data',\
      'userid': 'data', 'passwd': 'data', 'sshkey_file': None, 'restart': None}},\
     "ParameterError: mandatory parameter 'hostname' is missing"),

    # userid is missed
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'ftp', 'build_file': 'path', 'hostname': '0.0.0.0',\
      'mount_location': 'data', 'userid': None, 'passwd': 'data', 'sshkey_file': None, 'restart': None}},\
     "ParameterError: mandatory parameter 'userid' is missing"),

    # passwd is missing
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'ftp', 'build_file': 'path', 'hostname': '0.0.0.0',\
      'mount_location': 'data', 'userid': 'data', 'passwd': None, 'sshkey_file': None, 'restart': None}},\
     "ParameterError: mandatory parameter 'passwd' is missing"),

    # mount_location are mentioned in ftp
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'ftp', 'build_file': 'path', 'hostname': '0.0.0.0',\
      'mount_location': 'data', 'userid': 'test', 'passwd': 'data', 'sshkey_file': None, 'restart': None}},\
     "ParameterError: unsupported parameter: mount_location"),

    # hostname is not mentioned in ftp
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'ftp', 'build_file': 'path', 'hostname': None, 'mount_location': 'data',\
      'userid': 'test', 'passwd': 'data', 'sshkey_file': None, 'restart': None}},\
     "ParameterError: mandatory parameter 'hostname' is missing"),

    # build_file is not mentioned in ftp
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'ftp', 'build_file': None, 'hostname': '0.0.0.0', \
      'mount_location': 'data', 'userid': 'test', 'passwd': 'data', 'sshkey_file': None, 'restart': None}},\
     "ParameterError: mandatory parameter 'build_file' is missing"),

    # All NFS related testdata
    # host name is missed
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'nfs', 'build_file': 'path', 'hostname': None, 'mount_location': 'data',\
      'userid': 'data', 'passwd': 'data', 'sshkey_file': None, 'restart': None}},\
     "ParameterError: mandatory parameter 'hostname' is missing"),

    # userid is mentioned in nfs
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'nfs', 'build_file': 'path', 'hostname': '0.0.0.0', \
      'mount_location': 'data', 'userid': 'data', 'passwd': None, 'sshkey_file': None, 'restart': None}}, "ParameterError: unsupported parameter: userid"),

    # password is mentioned in nfs
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'nfs', 'build_file': 'path', 'hostname': '0.0.0.0', \
      'mount_location': 'data', 'userid': None, 'passwd': 'data', 'sshkey_file': None, 'restart': None}}, "ParameterError: unsupported parameter: passwd"),

    # sshkey_file is mentioned in nfs
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'nfs', 'build_file': 'path', 'hostname': '0.0.0.0',\
      'mount_location': 'data', 'userid': None, 'passwd': None, 'sshkey_file': 'data', 'restart': None}},\
     "ParameterError: unsupported parameter: sshkey_file"),

    # mount location is missing in nfs
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'nfs', 'build_file': 'path', 'hostname': '0.0.0.0', \
      'mount_location': None, 'userid': None, 'passwd': None, 'sshkey_file': None, 'restart': None}},\
     "ParameterError: mandatory parameter 'mount_location' is missing"),

    # hostname is not mentioned in nfs
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'nfs', 'build_file': 'path', 'hostname': None, 'mount_location': 'data',\
      'userid': 'test', 'passwd': 'data', 'sshkey_file': None, 'restart': None}},\
     "ParameterError: mandatory parameter 'hostname' is missing"),

    # build_file is not mentioned in nfs
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'nfs', 'build_file': None, 'hostname': '0.0.0.0', \
      'mount_location': 'data', 'userid': 'test', 'passwd': 'data', 'sshkey_file': None, 'restart': None}},\
     "ParameterError: mandatory parameter 'build_file' is missing"),

    # All disk related testdata
    # host name is mentioned in disk
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'disk', 'build_file': 'path', 'hostname': '0.0.0.0', \
      'mount_location': None, 'userid': None, 'passwd': None, 'sshkey_file': None, 'restart': None}}, "ParameterError: unsupported parameter: hostname"),

    # userid is mentioned in nfs
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'disk', 'build_file': 'path', 'hostname': None, 'mount_location': None,\
      'userid': 'data', 'passwd': None, 'sshkey_file': None, 'restart': None}}, "ParameterError: unsupported parameter: userid"),

    # password is mentioned in disk
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'disk', 'build_file': 'path', 'hostname': None, 'mount_location': None,\
      'userid': None, 'passwd': 'data', 'sshkey_file': None, 'restart': None}}, "ParameterError: unsupported parameter: passwd"),

    # sshkey_file is mentioned in disk
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'disk', 'build_file': 'path', 'hostname': None, 'mount_location': None,\
      'userid': None, 'passwd': None, 'sshkey_file': 'data', 'restart': None}}, "ParameterError: unsupported parameter: sshkey_file"),

    # mount location is mentioned in disk
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'disk', 'build_file': 'path', 'hostname': None, 'mount_location': 'data',\
      'userid': None, 'passwd': None, 'sshkey_file': None, 'restart': None}}, "ParameterError: unsupported parameter: mount_location"),

    # build_file is not mentioned in disk
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'disk', 'build_file': None, 'hostname': None, 'mount_location': None,\
      'userid': None, 'passwd': None, 'sshkey_file': None, 'restart': None}},\
     "ParameterError: mandatory parameter 'build_file' is missing"),

    # unsupported location_type
    ({'hmc_host': "0.0.0.10", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'nfssed', 'build_file': 'path', 'hostname': '0.0.0.0',\
      'mount_location': 'data', 'userid': None, 'passwd': None, 'sshkey_file': None, 'restart': None}},\
     "ParameterError: not supporting the location_type option: 'nfssed'"),

    ({'hmc_host': "0.0.0.10", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'usb', 'build_file': 'path', 'hostname': '0.0.0.0', \
      'mount_location': 'data', 'userid': None, 'passwd': None, 'sshkey_file': None, 'restart': None}}, "ParameterError: not supporting the option 'usb'"),

    ({'hmc_host': "0.0.0.10", 'hmc_auth': hmc_auth, 'build_config': {'location_type': 'dvd', 'build_file': 'path', 'hostname': '0.0.0.0',\
      'mount_location': 'data', 'userid': None, 'passwd': None, 'sshkey_file': None, 'restart': None}},\
     "ParameterError: not supporting the option 'dvd'")]

facts_test_data = [({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'build_config': None}, ""),
                   ({'hmc_auth': {'username': 'hscroot', 'password': '123456'}}, "'hmc_host'"),
                   ({'hmc_host': "0.0.0.0"}, "'hmc_auth'"),
                   ({'hmc_host': "0.0.0.0", 'hmc_auth': {'password': '123456'}}, "'username'"),
                   ({'hmc_host': "0.0.0.0", 'hmc_auth': {'username': 'hscroot'}}, "'password'"),
                   ]


def common_mock_setup(mocker):
    hmc_build_manager = importlib.import_module(IMPORT_HMC_BUILD_MANAGER)
    mocker.patch.object(hmc_build_manager, 'HmcCliConnection')
    mocker.patch.object(hmc_build_manager, 'Hmc', autospec=True)
    return hmc_build_manager


@pytest.mark.parametrize("upgrade_teset_input, expectedError", test_data)
def test_call_inside_upgrade_hmc(mocker, upgrade_teset_input, expectedError):
    hmc_build_manager = common_mock_setup(mocker)
    hmc_build_manager.Hmc.checkIfHMCFullyBootedUp.return_value = (True, {})
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            hmc_build_manager.upgrade_hmc(hmc_build_manager, upgrade_teset_input)
        assert expectedError == repr(e.value)
    else:
        hmc_build_manager.upgrade_hmc(hmc_build_manager, upgrade_teset_input)


@pytest.mark.parametrize("update_test_input, expectedError", test_data)
def test_call_inside_update_hmc(mocker, update_test_input, expectedError):
    hmc_build_manager = common_mock_setup(mocker)
    hmc_build_manager.Hmc.checkIfHMCFullyBootedUp.return_value = (True, {})
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            hmc_build_manager.update_hmc(hmc_build_manager, update_test_input)
        assert expectedError == repr(e.value)
    else:
        hmc_build_manager.update_hmc(update_test_input)


@pytest.mark.parametrize("facts_test_data, expectedError", facts_test_data)
def test_call_inside_facts_hmc(mocker, facts_test_data, expectedError):
    hmc_build_manager = common_mock_setup(mocker)
    hmc_build_manager.Hmc.checkIfHMCFullyBootedUp.return_value = (True, {})
    if expectedError != "":
        with pytest.raises(KeyError) as e:
            hmc_build_manager.facts(hmc_build_manager, facts_test_data)
        assert expectedError == str(e.value)
    else:
        hmc_build_manager.facts(hmc_build_manager, facts_test_data)
    #   hmc_build_manager.HmcCliConnection.assert_called_with(params['hmc_host'], params['hmc_auth']['userid'], '123456' )
