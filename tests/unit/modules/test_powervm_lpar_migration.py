from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
import importlib

IMPORT_HMC_LPM = "ansible_collections.ibm.power_hmc.plugins.modules.powervm_lpar_migration"

from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError

hmc_auth = {'username': 'hscroot', 'password': 'password_value'}
test_data = [
    # ALL vios partition testdata
    # src_system is missing in validate
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'action': 'validate',
      'src_system': None, 'dest_system': 'dstsys', 'all_vms': False,
      'vm_names': 'name', 'vm_ids': None},
     "ParameterError: mandatory parameter 'src_system' is missing"),
    # dest_system is missing in validate
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'action': 'validate',
      'src_system': 'srcsys', 'dest_system': None, 'all_vms': False,
      'vm_names': 'name', 'vm_ids': None},
     "ParameterError: mandatory parameter 'dest_system' is missing"),
    # host is missing in validate
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'action': 'validate',
      'src_system': 'srcsys', 'dest_system': 'destsys', 'all_vms': False,
      'vm_names': 'name', 'vm_ids': None},
     "ParameterError: mandatory parameter 'hmc_host' is missing"),
    # unsupported parameter all_vms in validate
    ({'hmc_host': '1.1.1.1', 'hmc_auth': hmc_auth, 'action': 'validate',
      'src_system': 'srcsys', 'dest_system': 'destsys', 'all_vms': True,
      'vm_names': 'name', 'vm_ids': None},
     "ParameterError: unsupported parameter: all_vms"),
    # src_system is missing in migrate
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'action': 'migrate',
      'src_system': None, 'dest_system': 'dstsys', 'all_vms': False,
      'vm_names': 'name', 'vm_ids': None},
     "ParameterError: mandatory parameter 'src_system' is missing"),
    # dest_system is missing in migrate
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'action': 'migrate',
      'src_system': 'srcsys', 'dest_system': None, 'all_vms': False,
      'vm_names': 'name', 'vm_ids': None},
     "ParameterError: mandatory parameter 'dest_system' is missing"),
    # host is missing in migrate
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'action': 'migrate',
      'src_system': 'srcsys', 'dest_system': 'destsys', 'all_vms': False,
      'vm_names': 'name', 'vm_ids': None},
     "ParameterError: mandatory parameter 'hmc_host' is missing"),
    # src_system is missing in recover
    ({'hmc_host': "0.0.0.0", 'hmc_auth': hmc_auth, 'action': 'recover',
      'src_system': None, 'dest_system': None, 'all_vms': False,
      'vm_names': 'name', 'vm_ids': None},
     "ParameterError: mandatory parameter 'src_system' is missing"),
    # host is missing in recover
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'action': 'recover',
      'src_system': 'srcsys', 'dest_system': None, 'all_vms': False,
      'vm_names': 'name', 'vm_ids': None},
     "ParameterError: mandatory parameter 'hmc_host' is missing"),
    # unsupported parameter all_vms in validate
    ({'hmc_host': '1.1.1.1', 'hmc_auth': hmc_auth, 'action': 'recover',
      'src_system': 'srcsys', 'dest_system': None, 'all_vms': True,
      'vm_names': 'name', 'vm_ids': None},
     "ParameterError: unsupported parameter: all_vms"),
    # unsupported parameter all_vms in validate
    ({'hmc_host': '1.1.1.1', 'hmc_auth': hmc_auth, 'action': 'recover',
      'src_system': 'srcsys', 'dest_system': 'dest_sys', 'all_vms': False,
      'vm_names': 'name', 'vm_ids': None},
     "ParameterError: unsupported parameter: dest_system")]


def common_mock_setup(mocker):
    hmc_lpm = importlib.import_module(IMPORT_HMC_LPM)
    mocker.patch.object(hmc_lpm, 'HmcCliConnection')
    mocker.patch.object(hmc_lpm, 'Hmc', autospec=True)
    return hmc_lpm


@pytest.mark.parametrize("lpm_test_input, expectedError", test_data)
def test_call_inside_logical_partition_migration(mocker, lpm_test_input, expectedError):
    hmc_lpm = common_mock_setup(mocker)
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            hmc_lpm.logical_partition_migration(hmc_lpm, lpm_test_input)
        assert expectedError == repr(e.value)
    else:
        hmc_lpm.logical_partition_migration(hmc_lpm, lpm_test_input)
