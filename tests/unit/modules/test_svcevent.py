from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
import importlib

IMPORT_SVCEVENT = "ansible_collections.ibm.power_hmc.plugins.modules.create_service_event"

from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError

hmc_auth = {'username': 'hscroot', 'password': 'password_value'}
test_data = [
    # title is missed
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'data',
      'description': 'test', 'types': 'vios', 'attributes':
     {'title': None, 'severity': '2', 'contact_name': 'Test',
      'contact_phone': 'data', 'contact_email': 'data', 'service_file': ['pedbgq4'],
      'target_lpar_name': None, 'target_mtms': None, 'lpar_name': 'data'},
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: title is mandatory in 'attributes' parameter"),

    # severity is missed
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'data',
      'description': 'test', 'types': 'vios', 'attributes':
     {'title': 'data', 'severity': None, 'contact_name': 'Test',
      'contact_phone': 'data', 'contact_email': 'data', 'service_file': ['pedbgq4'],
      'target_lpar_name': None, 'target_mtms': None, 'lpar_name': 'data'},
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: severity is mandatory in 'attributes' parameter"),

    # contact_name is missed
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'data',
      'description': 'test', 'types': 'vios', 'attributes':
     {'title': 'data', 'severity': '2', 'contact_name': None,
      'contact_phone': 'data', 'contact_email': 'data', 'service_file': ['pedbgq4'],
      'target_lpar_name': None, 'target_mtms': None, 'lpar_name': 'data'},
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: contact_name is mandatory in 'attributes' parameter"),

    # contact_phone is missed
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'data',
      'description': 'test', 'types': 'vios', 'attributes':
     {'title': 'data', 'severity': '2', 'contact_name': 'data',
      'contact_phone': None, 'contact_email': 'data', 'service_file': ['pedbgq4'],
      'target_lpar_name': None, 'target_mtms': None, 'lpar_name': 'data'},
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: contact_phone is mandatory in 'attributes' parameter"),

    # contact_email is missed
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'data',
      'description': 'test', 'types': 'vios', 'attributes':
     {'title': 'data', 'severity': '2', 'contact_name': 'data',
      'contact_phone': 'data', 'contact_email': None, 'service_file': ['pedbgq4'],
      'target_lpar_name': None, 'target_mtms': None, 'lpar_name': 'data'},
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: contact_email is mandatory in 'attributes' parameter"),

    # service_file is missed
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'data',
      'description': 'test', 'types': 'vios', 'attributes':
     {'title': 'data', 'severity': '2', 'contact_name': 'data',
      'contact_phone': 'data', 'contact_email': 'data', 'service_file': None,
      'target_lpar_name': None, 'target_mtms': None, 'lpar_name': 'data'},
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: 'service_file' is mandatory for types: vios"),

    # lpar_name is missed for vios type
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'data',
      'description': 'test', 'types': 'vios', 'attributes':
     {'title': 'data', 'severity': '2', 'contact_name': 'data',
      'contact_phone': 'data', 'contact_email': 'data', 'service_file': None,
      'target_lpar_name': None, 'target_mtms': None, 'lpar_name': None},
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: 'lpar_name' is mandatory for types: aix, lpm, vios"),

    # lpar_name is missed for lpm type
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'data',
      'description': 'test', 'types': 'lpm', 'attributes':
     {'title': 'data', 'severity': '2', 'contact_name': 'data',
      'contact_phone': 'data', 'contact_email': 'data', 'service_file': None,
      'target_lpar_name': None, 'target_mtms': None, 'lpar_name': None},
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: 'lpar_name' is mandatory for types: aix, lpm, vios"),

    # target_lpar_name is missed for lpm type
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'data',
      'description': 'test', 'types': 'lpm', 'attributes':
     {'title': 'data', 'severity': '2', 'contact_name': 'data',
      'contact_phone': 'data', 'contact_email': 'data', 'service_file': None,
      'target_lpar_name': None, 'target_mtms': 'data', 'lpar_name': 'data'},
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: 'target_lpar_name' is mandatory for types: lpm"),

    # target_mtms is missed for lpm type
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'data',
      'description': 'test', 'types': 'lpm', 'attributes':
     {'title': 'data', 'severity': '2', 'contact_name': 'data',
      'contact_phone': 'data', 'contact_email': 'data', 'service_file': None,
      'target_lpar_name': 'data', 'target_mtms': None, 'lpar_name': 'data'},
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: 'target_mtms' is mandatory for types: lpm"),

    # lpar_name is missed for aix type
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'sys1',
      'description': 'test', 'types': 'aix', 'attributes':
     {'title': 'data', 'severity': '2', 'contact_name': 'data',
      'contact_phone': 'data', 'contact_email': 'data', 'service_file': ['pedbgq4'],
      'target_lpar_name': None, 'target_mtms': None, 'lpar_name': None,
      'hostname': None, 'user': None},
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: 'lpar_name' is mandatory for types: aix, lpm, vios"),

    # service_file is missed for aix type
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'sys1',
      'description': 'test', 'types': 'aix', 'attributes':
     {'title': 'data', 'severity': '2', 'contact_name': 'data',
      'contact_phone': 'data', 'contact_email': 'data', 'service_file': None,
      'target_lpar_name': None, 'target_mtms': None, 'lpar_name': 'lp1',
      'hostname': None, 'user': None},
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: 'service_file' is mandatory for types: aix"),

    # invalid service_file for aix type
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'sys1',
      'description': 'test', 'types': 'aix', 'attributes':
     {'title': 'data', 'severity': '2', 'contact_name': 'data',
      'contact_phone': 'data', 'contact_email': 'data', 'service_file': ['badfile'],
      'target_lpar_name': None, 'target_mtms': None, 'lpar_name': 'lp1',
      'hostname': None, 'user': None},
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: Invalid service_file(s): badfile for types 'aix'. Valid values are: aixffdc, aixsnap, pedbgq4"),

    # hostname is missed for novalink type
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'sys1',
      'description': 'test', 'types': 'novalink', 'attributes':
     {'title': 'data', 'severity': '2', 'contact_name': 'data',
      'contact_phone': 'data', 'contact_email': 'data', 'service_file': ['novalinkffdc'],
      'target_lpar_name': None, 'target_mtms': None, 'lpar_name': None,
      'hostname': None, 'user': 'admin'},
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: 'hostname' is mandatory for types: novalink"),

    # user is missed for novalink type
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'sys1',
      'description': 'test', 'types': 'novalink', 'attributes':
     {'title': 'data', 'severity': '2', 'contact_name': 'data',
      'contact_phone': 'data', 'contact_email': 'data', 'service_file': ['novalinkffdc'],
      'target_lpar_name': None, 'target_mtms': None, 'lpar_name': None,
      'hostname': 'host1', 'user': None},
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: 'user' is mandatory for types: novalink"),

    # password is missed for novalink type
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'sys1',
      'description': 'test', 'types': 'novalink', 'attributes':
     {'title': 'data', 'severity': '2', 'contact_name': 'data',
      'contact_phone': 'data', 'contact_email': 'data', 'service_file': ['novalinkffdc'],
      'target_lpar_name': None, 'target_mtms': None, 'lpar_name': None,
      'hostname': 'host1', 'user': 'admin', 'password': None},
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: 'password' is mandatory for types: novalink"),

    # service_file is missed for novalink type
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'sys1',
      'description': 'test', 'types': 'novalink', 'attributes':
     {'title': 'data', 'severity': '2', 'contact_name': 'data',
      'contact_phone': 'data', 'contact_email': 'data', 'service_file': None,
      'target_lpar_name': None, 'target_mtms': None, 'lpar_name': None,
      'hostname': 'host1', 'user': 'admin', 'password': 'passw0rd'},
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: 'service_file' is mandatory for types: novalink"),

    # service_file is missed for sys type
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'sys1',
      'description': 'test', 'types': 'sys', 'attributes':
     {'title': 'data', 'severity': '2', 'contact_name': 'data',
      'contact_phone': 'data', 'contact_email': 'data', 'service_file': None,
      'target_lpar_name': None, 'target_mtms': None, 'lpar_name': None,
      'hostname': None, 'user': None},
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: 'service_file' is mandatory for types: sys"),

    # invalid service_file for sys type
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'sys1',
      'description': 'test', 'types': 'sys', 'attributes':
     {'title': 'data', 'severity': '2', 'contact_name': 'data',
      'contact_phone': 'data', 'contact_email': 'data', 'service_file': ['badfile'],
      'target_lpar_name': None, 'target_mtms': None, 'lpar_name': None,
      'hostname': None, 'user': None},
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: Invalid service_file(s): badfile for types 'sys'. Valid values are: pedbgq4, rscdump, spdump"),

    # service_file is missed for cloudconn type
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'sys1',
      'description': 'test', 'types': 'cloudconn', 'attributes':
     {'title': 'data', 'severity': '2', 'contact_name': 'data',
      'contact_phone': 'data', 'contact_email': 'data', 'service_file': None,
      'target_lpar_name': None, 'target_mtms': None, 'lpar_name': None,
      'hostname': None, 'user': None},
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: 'service_file' is mandatory for types: cloudconn"),

    # invalid service_file for cloudconn type
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'sys1',
      'description': 'test', 'types': 'cloudconn', 'attributes':
     {'title': 'data', 'severity': '2', 'contact_name': 'data',
      'contact_phone': 'data', 'contact_email': 'data', 'service_file': ['pedbgq4'],
      'target_lpar_name': None, 'target_mtms': None, 'lpar_name': None,
      'hostname': None, 'user': None},
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: Invalid service_file(s): pedbgq4 for types 'cloudconn'. Valid values are: pedbgq8"),

    # attributes is missed for hmc type
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'sys1',
      'description': 'test', 'types': 'hmc', 'attributes': None,
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: attributes is mandatory for types: hmc"),

    # system_name is not supported for hmctest type
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'sys1',
      'description': 'test', 'types': 'hmctest', 'attributes': None,
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: system_name is not supported for types: hmctest"),
]

created_extra_data = [
    # description is missing
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'data',
      'description': None, 'types': 'vios', 'attributes': None,
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: description is mandatory when state is 'created'"),

    # types is missing
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'data',
      'description': 'test', 'types': None, 'attributes': None,
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: types is mandatory when state is 'created'"),

    # system_name is mandatory for non-hmctest types
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': None,
      'description': 'test', 'types': 'sys', 'attributes': None,
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: system_name is mandatory for types: sys"),

    # attributes is mandatory for vios
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'data',
      'description': 'test', 'types': 'vios', 'attributes': None,
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: attributes is mandatory for types: vios"),

    # attributes not supported for 'test' type
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'data',
      'description': 'test', 'types': 'test', 'attributes':
     {'title': 'data', 'severity': '2', 'contact_name': 'data',
      'contact_phone': 'data', 'contact_email': 'data', 'service_file': None,
      'target_lpar_name': None, 'target_mtms': None, 'lpar_name': None},
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: attributes is not supported for types 'test'"),

    # event_type not supported for 'created' state
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'data',
      'description': 'test', 'types': 'vios', 'attributes': None,
      'event_type': 'hardware', 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: event_type is not supported when state is 'created'"),

    # days not supported for 'created' state
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'data',
      'description': 'test', 'types': 'vios', 'attributes': None,
      'event_type': None, 'days': 7, 'minutes': None, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: days is not supported when state is 'created'"),

    # minutes not supported for 'created' state
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'data',
      'description': 'test', 'types': 'vios', 'attributes': None,
      'event_type': None, 'days': None, 'minutes': 30, 'number_of_events': None, 'display_attributes': None},
     "ParameterError: minutes is not supported when state is 'created'"),

    # number_of_events not supported for 'created' state
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'data',
      'description': 'test', 'types': 'vios', 'attributes': None,
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': 10, 'display_attributes': None},
     "ParameterError: number_of_events is not supported when state is 'created'"),

    # display_attributes not supported for 'created' state
    ({'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'created', 'system_name': 'data',
      'description': 'test', 'types': 'vios', 'attributes': None,
      'event_type': None, 'days': None, 'minutes': None, 'number_of_events': None, 'display_attributes': ['col1']},
     "ParameterError: display_attributes is not supported when state is 'created'"),
]

facts_base = {
    'hmc_host': 'data', 'hmc_auth': hmc_auth, 'state': 'facts',
    'system_name': None, 'description': None, 'types': None, 'attributes': None,
    'event_type': None, 'days': None, 'minutes': None,
    'number_of_events': None, 'display_attributes': None,
}

facts_data = [
    # event_type is mandatory for 'facts'
    ({**facts_base},
     "ParameterError: event_type is mandatory when state is 'facts'"),

    # description not supported for 'facts' state
    ({**facts_base, 'event_type': 'hardware', 'description': 'oops'},
     "ParameterError: description is not supported when state is 'facts'"),

    # types not supported for 'facts' state
    ({**facts_base, 'event_type': 'hardware', 'types': 'vios'},
     "ParameterError: types is not supported when state is 'facts'"),

    # attributes not supported for 'facts' state
    ({**facts_base, 'event_type': 'hardware',
      'attributes': {'title': 'x', 'severity': '2', 'contact_name': 'x',
                     'contact_phone': 'x', 'contact_email': 'x', 'service_file': None,
                     'target_lpar_name': None, 'target_mtms': None, 'lpar_name': None}},
     "ParameterError: attributes is not supported when state is 'facts'"),

    # days and minutes are mutually exclusive
    ({**facts_base, 'event_type': 'hardware', 'days': 3, 'minutes': 60},
     "ParameterError: days and minutes are mutually exclusive"),

    # console: system_name not supported
    ({**facts_base, 'event_type': 'console', 'system_name': 'sys1'},
     "ParameterError: system_name is not supported when event_type is 'console'"),

    # console: number_of_events not supported
    ({**facts_base, 'event_type': 'console', 'number_of_events': 5},
     "ParameterError: number_of_events is not supported when event_type is 'console'"),

    # console: display_attributes not supported
    ({**facts_base, 'event_type': 'console', 'display_attributes': ['attr1']},
     "ParameterError: display_attributes is not supported when event_type is 'console'"),
]


def common_mock_setup(mocker):
    svcevent = importlib.import_module(IMPORT_SVCEVENT)
    mocker.patch.object(svcevent, 'HmcCliConnection')
    hmc_mock = mocker.patch.object(svcevent, 'Hmc', autospec=True)
    hmc_mock.return_value.list_all_managed_system_details.return_value = [{'name': 'data'}, {'name': 'sys1'}]
    hmc_mock.return_value.get_managed_system_gen.return_value = None
    return svcevent


@pytest.mark.parametrize("test_input, expectedError", test_data)
def test_update_vios(mocker, test_input, expectedError):
    svcevent_created = common_mock_setup(mocker)
    svcevent_created.Hmc.checkIfHMCFullyBootedUp.return_value = (True, {})
    if 'ParameterError' in expectedError:
        with pytest.raises(ParameterError) as e:
            svcevent_created.create_svc_events(svcevent_created, test_input)
        assert expectedError == repr(e.value)
    else:
        svcevent_created.create_svc_events(svcevent_created, test_input)


@pytest.mark.parametrize("test_input, expectedError", created_extra_data)
def test_created_parameter_errors(mocker, test_input, expectedError):
    svcevent = common_mock_setup(mocker)
    with pytest.raises(ParameterError) as e:
        svcevent.create_svc_events(svcevent, test_input)
    assert expectedError == repr(e.value)


@pytest.mark.parametrize("test_input, expectedError", facts_data)
def test_facts_parameter_errors(mocker, test_input, expectedError):
    svcevent = common_mock_setup(mocker)
    with pytest.raises(ParameterError) as e:
        svcevent.list_svc_events(svcevent, test_input)
    assert expectedError == repr(e.value)
