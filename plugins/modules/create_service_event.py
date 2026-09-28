#!/usr/bin/python

# Copyright: (c) 2018- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: create_service_event
author:
    - Sreenidhi S(@SreenidhiS1)
short_description: Creates or lists serviceable events on the Hardware Management Console (HMC)
notes:
    - This module requires the HMC which has systems licensed for advanced automation and monitoring.
    - The types C(aix), C(cloudconn), C(lpm), C(novalink), C(sys), and C(vios) are supported for POWER11 systems only.
    - The types C(power), C(processor), C(lan), C(software), C(io), and C(other) are supported for POWER10 and POWER9 systems only.
    - The types C(hmc), C(test), and C(hmctest) are supported for all systems.
description:
    - Creates a serviceable event on the Hardware Management Console (HMC) to report a problem that occurred
      on either the managed system or the HMC itself, and initiates a service request for repair.
    - Lists serviceable events available on the HMC.
version_added: 1.0.0
requirements:
- Python >= 3.9
options:
    hmc_host:
        description:
            - The IP Address or hostname of the HMC.
        required: true
        type: str
    hmc_auth:
        description:
            - Username and Password credential of the HMC.
        required: true
        type: dict
        suboptions:
            username:
                description:
                    - Username of the HMC to login.
                required: true
                type: str
            password:
                description:
                    - Password of the HMC.
                type: str
    system_name:
        description:
            - The name or MTMS (machine type model serial) of the managed system.
            - Required for I(state=created) except with C(hmctest).
            - Optional for I(state=facts).
        type: str
    description:
        description:
            - The problem description.
            - Required when I(state=created).
        type: str
    types:
        description:
            - The type of event to create.
            - C(power) to report a problem with the power subsystem of managed-system.
            - C(processor) to report a problem with hardware in the processor subsystem of managed-system.
            - C(lan) to report a problem with the local area network (LAN) to which managed-system is attached.
            - C(software) to report a problem with an operating system or other software loaded on managed-system.
            - C(io) to report a problem with hardware in the I/O configuration of managed-system.
            - C(other) to report a problem with managed-system that is not adequately described by any other event type.
            - C(hmc) to report a problem with this HMC.
            - C(test) to test whether problems can be reported for managed-system.
            - C(hmctest) to test whether problems can be reported for this HMC.
            - C(sys) to report a problem with managed-system.
            - C(vios) to report a problem with a Virtual I/O Server on managed-system.
            - C(lpm) to report a partition migration problem where managed-system is the source system for the partition migration operation.
            - C(cloudconn) to report a problem with the cloud connector on this HMC.
            - C(aix) to report a problem with an AIX partition on managed-system.
            - C(novalink) to report a problem with PowerVM NovaLink.
        type: str
        choices: ['power', 'processor', 'lan', 'software', 'io', 'other', 'hmc', 'test', 'hmctest',
                  'sys', 'vios', 'lpm', 'cloudconn', 'aix', 'novalink']
    attributes:
        description:
            - The serviceable event attributes to set.
            - The attribute data consists of name/value pairs.
            - Required with C(aix), C(cloudconn), C(lpm), C(novalink), C(sys), and C(vios).
            - Also required with C(hmc) on POWER11 systems.
            - Otherwise this option is not valid.
        type: dict
        suboptions:
            title:
                description:
                    - Title for the serviceable event.
                type: str
                required: true
            severity:
                description:
                    - The priority for the serviceable event.
                    - Valid values are 1 - 4.
                type: int
                required: true
                choices: [1, 2, 3, 4]
            contact_name:
                description:
                    - The contact name for the serviceable event.
                required: true
                type: str
            contact_email:
                description:
                    - The contact email for the serviceable event.
                required: true
                type: str
            contact_phone:
                description:
                    - The contact phone number for the serviceable event.
                required: true
                type: int
            target_lpar_name:
                description:
                    - The target logical partition name for the serviceable event.
                    - Required with C(lpm).
                type: str
            target_mtms:
                description:
                    - The target managed system MTMS for the serviceable event.
                    - Required with C(lpm).
                    - Format is C(tttt-mmm*sssssss).
                type: str
            lpar_name:
                description:
                    - The logical partition name for the serviceable event.
                    - Required with C(aix), C(lpm), and C(vios).
                type: str
            associated_entitled_mtms:
                description:
                    - The managed system MTMS used to register this virtual HMC for call home.
                    - Required with C(hmc) when this HMC is a virtual HMC.
                    - Format is C(tttt-mmm*sssssss).
                type: str
            hostname:
                description:
                    - NovaLink hostname.
                    - Required with C(novalink).
                type: str
            user:
                description:
                    - NovaLink user.
                    - Required with C(novalink).
                type: str
            password:
                description:
                    - NovaLink password.
                    - Required with C(novalink).
                type: str
            service_file:
                description:
                    - The name of the log file attached to the serviceable event.
                    - Multiple service files must be comma-separated.
                    - Required with C(aix), C(cloudconn), C(lpm), C(novalink), C(sys), and C(vios).
                    - Also required with C(hmc) on POWER11 systems.
                    - C(aixffdc) AIX system logs. Valid with C(aix).
                    - C(aixsnap) AIX snap data. Valid with C(aix).
                    - C(lpmffdc) Partition migration debug data. Valid with C(lpm).
                    - C(novalinkffdc) NovaLink pedbg data. Valid with C(novalink).
                    - C(pedbgq4) HMC pedbg data. Valid with C(aix), C(hmc), C(lpm), C(sys), and C(vios).
                    - C(pedbgq8) Cloud connector pedbg data. Valid with C(cloudconn).
                    - C(rscdump) Non-disruptive system dump. Valid with C(sys).
                    - C(spdump) Service processor dump. Valid with C(sys).
                    - C(vios) VIOS snap data. Valid with C(vios).
                type: list
                elements: str
                choices: ['aixffdc', 'aixsnap', 'lpmffdc', 'novalinkffdc', 'pedbgq4', 'pedbgq8', 'rscdump', 'spdump', 'vios']
    event_type:
        description:
            - The type of events to list when I(state=facts).
            - C(hardware) lists serviceable events.
            - C(console) lists console events.
        type: str
        choices: ['console', 'hardware']
    days:
        description:
            - The number of days to go back and search for events when I(state=facts).
        type: int
    minutes:
        description:
            - The number of minutes to go back and search for events when I(state=facts).
        type: int
    number_of_events:
        description:
            - The number of events to display when I(state=facts).
        type: int
    display_attributes:
        description:
            - List of hardware event attributes to display when I(state=facts).
            - Maps to C(lssvcevents -F).
        type: list
        elements: str
    state:
        description:
            - C(created) to create a serviceable event.
            - C(facts) to list serviceable events.
        type: str
        choices: ['created', 'facts']
        required: true
'''

EXAMPLES = '''
- name: Create a serviceable event for collection of vios logs
  create_service_event:
    hmc_host: '{{ inventory_hostname }}'
    hmc_auth: "{{ curr_hmc_auth }}"
    system_name: <system name>
    description: Test Description
    types: vios
    attributes:
      title: test
      severity: 4
      contact_name: Test
      contact_phone: < phone-num >
      contact_email: test@abc.com
      lpar_name: < partition >
      service_file:
        - pedbgq4
        - vios
    state: created

- name: Create a serviceable event for collection of lpm logs
  create_service_event:
    hmc_host: '{{ inventory_hostname }}'
    hmc_auth: "{{ curr_hmc_auth }}"
    system_name: <system name>
    description: Test Description
    types: lpm
    attributes:
      title: test
      severity: 4
      contact_name: Test
      contact_phone: < phone-num >
      contact_email: test@abc.com
      lpar_name: < partition1 >
      target_lpar_name: <partition2 >
      target_mtms: < target-sys >
      service_file:
        - pedbgq4
        - lpmffdc
    state: created

- name: List serviceable events
  create_service_event:
    hmc_host: '{{ inventory_hostname }}'
    hmc_auth: "{{ curr_hmc_auth }}"
    state: facts
    event_type: hardware

- name: List console events
  create_service_event:
    hmc_host: '{{ inventory_hostname }}'
    hmc_auth: "{{ curr_hmc_auth }}"
    state: facts
    event_type: console
    days: 7
    number_of_events: 10
'''

RETURN = '''
changed:
    description: Indicates whether the serviceable event was created.
    type: bool
    returned: always
info:
    description: Output of the serviceable event creation or list operation.
    type: raw
    returned: always
warning:
    description: Warning message, if any.
    type: str
    returned: when a warning is raised
'''

import logging
import os
LOG_FILENAME = "/tmp/ansible_power_hmc_{0}.log".format(os.getpid())
logger = logging.getLogger(__name__)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_resource import Hmc
import sys

USER_AUTHORITY_ERR = "HSCL350B The user does not have the appropriate authority"


def init_logger():
    old_umask = os.umask(0o177)
    try:
        logging.basicConfig(
            filename=LOG_FILENAME,
            format='[%(asctime)s] %(levelname)s: [%(funcName)s] %(message)s',
            level=logging.DEBUG)
    finally:
        os.umask(old_umask)


# Types supported on Power11 systems only
POWER11_ONLY_TYPES = frozenset(['sys', 'vios', 'lpm', 'cloudconn', 'aix', 'novalink'])

# Types supported on POWER9 and Power10 systems only
POWER9_POWER10_ONLY_TYPES = frozenset(['power', 'processor', 'lan', 'software', 'io', 'other'])

# Types supported on all systems
ALL_SYSTEM_TYPES = frozenset(['hmc', 'test', 'hmctest'])


def get_hmc_resource(module, params):
    hmc_conn = HmcCliConnection(module, params['hmc_host'], params['hmc_auth']['username'], params['hmc_auth']['password'])
    return Hmc(hmc_conn)


def validate_parameters(params, system_gen):
    '''Check that the input parameters satisfy the mutual exclusiveness of HMC'''
    unsupported_params = {
        'facts': ['description', 'types', 'attributes'],
        'created': ['event_type', 'days', 'minutes', 'number_of_events', 'display_attributes']
    }
    for param in unsupported_params[params['state']]:
        if params[param] is not None:
            raise ParameterError("{} is not supported when state is '{}'".format(param, params['state']))

    if params['state'] == 'facts':
        if params['event_type'] is None:
            raise ParameterError("event_type is mandatory when state is 'facts'")
        if params['event_type'] == 'console':
            if params['system_name'] is not None:
                raise ParameterError("system_name is not supported when event_type is 'console'")
            if params['number_of_events'] is not None:
                raise ParameterError("number_of_events is not supported when event_type is 'console'")
            if params['display_attributes'] is not None:
                raise ParameterError("display_attributes is not supported when event_type is 'console'")
        if params['days'] is not None and params['minutes'] is not None:
            raise ParameterError("days and minutes are mutually exclusive")
        return

    attributes = params['attributes']
    if params['description'] is None:
        raise ParameterError("description is mandatory when state is 'created'")
    if params['types'] is None:
        raise ParameterError("types is mandatory when state is 'created'")

    selected_type = params['types']
    if system_gen == 'power11' and selected_type in POWER9_POWER10_ONLY_TYPES:
        raise ParameterError(
            "type '{}' is not supported on current system type '{}'".format(
                selected_type, system_gen
            )
        )
    if system_gen in ['power9', 'power10'] and selected_type in POWER11_ONLY_TYPES:
        raise ParameterError(
            "type '{}' is not supported on current system type '{}'".format(
                selected_type, system_gen
            )
        )

    if selected_type == 'hmctest':
        if params['system_name'] is not None:
            raise ParameterError("system_name is not supported for types: hmctest")
    elif params['system_name'] is None:
        raise ParameterError("system_name is mandatory for types: {}".format(selected_type))

    valid_attribute_types = {'aix', 'cloudconn', 'lpm', 'novalink', 'sys', 'vios', 'hmc'}

    if selected_type in valid_attribute_types:
        if attributes is None:
            raise ParameterError(
                "attributes is mandatory for types: {}".format(selected_type)
            )
    elif attributes is not None:
        raise ParameterError(
            "attributes is not supported for types '{}'".format(selected_type)
        )
    else:
        return

    mandatory_attributes = ['title', 'severity', 'contact_name', 'contact_phone', 'contact_email']
    for each in mandatory_attributes:
        if attributes[each] is None:
            raise ParameterError("{} is mandatory in 'attributes' parameter".format(each))

    if selected_type in ['aix', 'lpm', 'vios'] and attributes['lpar_name'] is None:
        raise ParameterError("'lpar_name' is mandatory for types: aix, lpm, vios")
    if selected_type == 'lpm':
        if attributes['target_mtms'] is None:
            raise ParameterError("'target_mtms' is mandatory for types: lpm")
        if attributes['target_lpar_name'] is None:
            raise ParameterError("'target_lpar_name' is mandatory for types: lpm")
    if selected_type == 'novalink':
        if attributes['hostname'] is None:
            raise ParameterError("'hostname' is mandatory for types: novalink")
        if attributes['user'] is None:
            raise ParameterError("'user' is mandatory for types: novalink")
        if attributes['password'] is None:
            raise ParameterError("'password' is mandatory for types: novalink")

    valid_service_files = {
        'aix': {'aixffdc', 'aixsnap', 'pedbgq4'},
        'cloudconn': {'pedbgq8'},
        'hmc': {'pedbgq4'},
        'lpm': {'lpmffdc', 'pedbgq4'},
        'novalink': {'novalinkffdc'},
        'sys': {'pedbgq4', 'rscdump', 'spdump'},
        'vios': {'pedbgq4', 'vios'},
    }
    mandatory_service_file_types = {'aix', 'cloudconn', 'lpm', 'novalink', 'sys', 'vios'}
    if system_gen == 'power11' and selected_type == 'hmc':
        mandatory_service_file_types.add('hmc')

    if selected_type in mandatory_service_file_types:
        if attributes['service_file'] is None:
            raise ParameterError(
                "'service_file' is mandatory for types: {}".format(selected_type)
            )
    elif attributes['service_file'] is not None and selected_type not in valid_service_files:
        raise ParameterError(
            "'service_file' is not supported for types '{}'.".format(selected_type)
        )

    if attributes['service_file'] is not None:
        invalid_files = [
            f for f in attributes['service_file']
            if f not in valid_service_files.get(selected_type, set())
        ]
        if invalid_files:
            valid = sorted(valid_service_files.get(selected_type, set()))
            raise ParameterError(
                "Invalid service_file(s): {} for types '{}'. Valid values are: {}".format(
                    ', '.join(invalid_files), selected_type, ', '.join(valid)
                )
            )


def create_svc_events(module, params):
    hmc = get_hmc_resource(module, params)
    m_system = params['system_name']
    sys_list = hmc.list_all_managed_system_details("name") + hmc.list_all_managed_system_details("type_model*serial_num")
    sys_list = [list(d.values())[0] for d in sys_list]
    system_gen = None
    if params['types'] != 'hmctest' and m_system is not None:
        if m_system not in sys_list:
            module.fail_json(msg="The managed system is not available in HMC")
        system_gen = hmc.get_managed_system_gen(m_system)
        logger.debug("Testing")
        logger.debug(system_gen)
        if system_gen == 'power11' and hmc.getManagedSystemDetails(m_system, "advanced_hmc_automation_and_monitoring_capable").strip() != '1':
            module.fail_json(msg="This module is supported only for systems where advanced hmc automation and monitoring capability is enabled")
    validate_parameters(params, system_gen)
    attributes = params['attributes']
    if params['types'] != 'hmctest' and attributes is not None:
        lpar_list = hmc.list_all_lpars_details(m_system, "name")
        if attributes['lpar_name'] is not None:
            if attributes['lpar_name'] not in lpar_list:
                module.fail_json(msg="The partition is not available in HMC")
        if attributes['target_mtms'] is not None:
            target_system = attributes['target_mtms']
            if target_system not in sys_list:
                module.fail_json(msg="The target managed system is not available in HMC")
            target_lpar_name = attributes['target_lpar_name']
            target_lpar_list = hmc.list_all_lpars_details(target_system, "name")
            if target_lpar_name not in target_lpar_list:
                module.fail_json(msg="The target partition is not available in HMC")
    try:
        output = hmc.create_svc_events(params)
        changed = True
        return changed, output.strip(), None
    except Exception as e:
        return False, repr(e), None


def format_svc_event_output(output, event_type, display_attributes):
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if lines == ['No results were found.']:
        return 'No results were found.'

    if event_type == 'console':
        return lines

    rows = []
    for line in lines:
        values = [value.strip() for value in line.split(',')]
        event = {}
        if display_attributes is not None:
            for key, value in zip(display_attributes, values):
                event[key] = value
        else:
            for value in values:
                if '=' in value:
                    key, field_value = value.split('=', 1)
                    event[key.strip()] = field_value.strip()
            if not event:
                for index, value in enumerate(values, start=1):
                    event['value_{0}'.format(index)] = value
        rows.append(event)
    return rows


def list_svc_events(module, params):
    validate_parameters(params, None)
    hmc = get_hmc_resource(module, params)

    try:
        output = hmc.list_svc_events(params)
        return False, format_svc_event_output(output, params['event_type'], params['display_attributes']), None
    except Exception as e:
        return False, repr(e), None


def perform_task(module):
    params = module.params
    actions = {
        "created": create_svc_events,
        "facts": list_svc_events
    }

    if not params['hmc_auth']:
        return False, "missing credential info", None
    try:
        return actions[params['state']](module, params)
    except Exception as error:
        return False, repr(error), None


def run_module():
    module_args = dict(
        hmc_host=dict(type='str', required=True),
        hmc_auth=dict(type='dict',
                      required=True,
                      no_log=True,
                      options=dict(
                          username=dict(required=True, type='str'),
                          password=dict(type='str', no_log=True),
                      )
                      ),
        state=dict(type='str', choices=['created', 'facts'], required=True),
        system_name=dict(type='str'),
        event_type=dict(type='str', choices=['console', 'hardware']),
        days=dict(type='int'),
        minutes=dict(type='int'),
        number_of_events=dict(type='int'),
        display_attributes=dict(type='list', elements='str'),
        description=dict(type='str'),
        types=dict(type='str', choices=[
            'power', 'processor', 'lan', 'software', 'io', 'other', 'hmc', 'test', 'hmctest',
            'sys', 'vios', 'lpm', 'cloudconn', 'aix', 'novalink'
        ]),
        attributes=dict(type='dict',
                        options=dict(
                            title=dict(type='str', required=True),
                            severity=dict(type='int', choices=[1, 2, 3, 4], required=True),
                            contact_name=dict(type='str', required=True),
                            contact_phone=dict(type='int', required=True),
                            contact_email=dict(type='str', required=True),
                            service_file=dict(type='list',
                                              choices=['aixffdc', 'aixsnap', 'lpmffdc', 'novalinkffdc', 'pedbgq4', 'pedbgq8', 'rscdump', 'spdump', 'vios'],
                                              elements='str'),
                            target_lpar_name=dict(type='str'),
                            target_mtms=dict(type='str'),
                            lpar_name=dict(type='str'),
                            associated_entitled_mtms=dict(type='str'),
                            hostname=dict(type='str'),
                            user=dict(type='str'),
                            password=dict(type='str', no_log=True)
                        )
                        ),
    )

    module = AnsibleModule(
        argument_spec=module_args,
    )

    if module._verbosity >= 5:
        init_logger()

    if sys.version_info < (3, 0):
        py_ver = sys.version_info[0]
        module.fail_json(msg="Unsupported Python version {0}, supported python version is 3 and above".format(py_ver))

    changed, info, warning = perform_task(module)
    if not changed and isinstance(info, str):
        module.fail_json(msg=info)

    result = {}
    result['changed'] = changed
    result['info'] = info
    if warning:
        result['warning'] = warning

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
