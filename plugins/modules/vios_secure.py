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
module: vios_secure
author:
    - Sreenidhi S (@SreenidhiS1)
short_description: Configures firewall settings and applies security hardening rules.
notes:
    - This module requires the HMC login user to have specific permissions.
      To achieve this, the user should create a task role based on hmcsuperadmin with additional permissions,
      including ViosAdminOp, VirtualIOServerCommand and other permissions for managing lpar and cec resources.
      The following example demonstrates the same
    - Create a task role with above mentioned additional permissions using following command
      V(mkaccfg -t taskrole -i name=new_task_role,parent=hmcsuperadmin,
      resources=lpar:ActivateLPAR+CapturePartitionTemplate+ChangeLPARProperty+
      ChangeNPortLogin+ChangeProfileProperty+CloseVTerm+Connect5250VTerm+
      CreateProfile+Delete5250VTerm+DeleteLPAR+DeleteProfile+DisableEnableVirtualEthernet+
      DlparOperation+HibernateLPAR+ListLPARProperty+ListProfileProperty+ManageLPARDebugData+
      ManageLPARServEvents+ManageLicenseKeys+ManageProfile+MigrateLPAR+
      Open5250VTerm+OpenVTerm+PartProfileCopy+RRStartLPAR+RebootLPAR+RemoteRestartLPAR+
      ShutdownLPAR+VirtualIOServerCommand+ViosAdminOp,
      cec:ActivateSystemProfile+BackupProfileData+CECPowerOff+CECPowerOn+
      CaptureSystemTemplate+ChangeCECPassword+ChangeCECProperty+ChangeCoD+ChangePowerManagement+
      ChangeSnmpAlerts+ChangeSystemConnectionProperty+ChangeSystemProfileProperty+
      ChangeTrustedSystemKey+ChangeVETCode+CoDPoolManagement+CollectCECVPDInfo+
      ConfigProcessorRecovery+CreateLPAR+CreatePassThruCommand+CreateSystemProfile+
      DLPARRestoreHWResources+DeleteSystemProfile+DeployPartitionTemplate+DeploySystemPlan+
      DeploySystemTemplate+DeviceMaintenance+DisconnectOtherHmc+EditCECMTMS+
      InitializeProfileData+InitializeSPFailover+LSProfileSpace+LaunchAsm+
      ListCECProperty+ListCoDInformation+ListCoDNotifications+ListNPortLogin+
      ListPCIeTopology+ListRioTopology+ListSSP+ListSnmpAlerts+ListSystemProfileProperty+
      ListTrustedSystemKey+ListUtilizationData+ListVETInfo+MakeSystemPlan+
      ManageCECServEvents+ManageCoDNotifications+ManageDumps+
      ManageSPP+ManageSSP+ManageSriovAdapter+ManageSysProfile+ManageUtilizationData+
      ManageVirtualNetwork+ManageVirtualStorage+MoveSriovAdapter+PartitionConfigurationImage+
      RebuildCEC+RecoverPartitionData+RemoveCECConnection+RemoveCEConnection+RemoveProfileData+
      RestoreProfileData+SetCECKeylockPosition+SysProfileCopy+UpdateLIC+ValidateSystemProfile+
      ViewDumps+ViewPowerManagement+ViewSPP)
    - Create a user with the above created task role.
description:
    - Applies security hardening rules.
    - Configures and removes the firewall settings of the network.
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
        type: str
        required: true
    vios_name:
        description:
            - The name of the VirtualIOServer.
        type: str
        required: true
    file:
        description:
            - Specifies the security rules file to be applied.
            - Mutually exclusive with I(level).
            - This option is only valid for C(setting_security) state.
        type: str
    rule:
        description:
            - Specifies the name of the rule to be applied.
            - This option is only valid for C(setting_security) state.
        type: str
    level:
        description:
            - Specifies the security level settings to choose.
            - Specifying C(high) security level might cause stability or serviceability issues especially in a cluster environment.
            - Mutually exclusive with I(file).
            - This option is only valid for C(setting_security) state.
        type: str
        choices: ['low', 'medium', 'high', 'default']
    ip_version:
        description:
            - Specifies the version for firewall state and rules.
            - This option is only valid for C(setting_firewall) and C(firewall_facts) state.
        type: str
        choices: ['ipv4', 'ipv6', 'IPV4', 'IPV6']
    active:
        description:
            - Specifies the state of the firewall.
            - This option is only valid for C(setting_firewall) state.
        type: bool
    reload:
        description:
            - Specifies this option for deleting ODM rules and the default values are loaded from the /home/ios/security/viosecure.ctl file
            - For enabling the firewall rules for first time this option is required along with C(active) option.
            - This option is only valid for C(setting_firewall) state.
        type: bool
    firewall_config:
        description:
            - Specifies the firewall state and rules.
            - This option is only valid for C(setting_firewall) state.
        type: list
        elements: dict
        suboptions:
            port:
                description:
                    - Specifies the port number or a service name from the C(/etc/services) file.
                    - All the IP activity to and from that local port is allowed.
                required: true
                type: int
            interface:
                description:
                    - Specifies the network interface name.
                type: str
            remote:
                description:
                    - Specifies whether the port is a remote port.
                    - All the IP activity to and from that remote port is allowed.
                type: bool
            address:
                description:
                    - Specifies the IP address.
                type: str
            timeout:
                description:
                    - Specifies the timeout period.
                    - The timeout period can be specified as a number (in seconds), or with a number followed by C(m) (minutes), C(h) (hours), or C(d) (days).
                    - The maximum timeout period is 30 days.
                type: str
            present:
                description:
                    - Specify whether to activate or deactivate a port.
                type: str
                required: true
                choices: ['allow', 'deny', 'ALLOW', 'DENY']
    state:
        description:
            - C(setting_security) ensures the new security hardening rules are applied.
            - C(firewall_facts) does not change anything on the HMC and returns the firewall settings information.
            - C(setting_firewall) ensures the firewall settings are configured.
        type: str
        choices: ['setting_security', 'firewall_facts', 'setting_firewall']
'''
EXAMPLES = '''
- name: Apply the security rule lls_maxage to VIOS
  ibm.power_hmc.vios_secure:
    hmc_host: '{{ hmc_ip }}'
    hmc_auth: '{{ hmc_auth }}'
    system_name: <sys>
    vios_name: <vios>
    rule: lls_maxage
    level: low
    state: setting_security

- name: Get firewall information for ipv6 of VIOS
  ibm.power_hmc.vios_secure:
    hmc_host: '{{ hmc_ip }}'
    hmc_auth: '{{ curr_hmc_auth }}'
    system_name: <sys>
    vios_name: <vios>
    ip_version: IPV6
    state: firewall_facts

- name: Configure firewall rule for port 2000 with interface en0 on VIOS
  ibm.power_hmc.vios_secure:
    hmc_host: '{{ hmc_ip }}'
    hmc_auth: '{{ curr_hmc_auth }}'
    system_name: <sys>
    vios_name: <vios>
    ip_version: IPV6
    firewall_config:
      - port: 2000
        present: allow
        interface: en0
    state: setting_firewall
'''

RETURN = '''
security_facts:
    description: Respective security information
    type: dict
    returned: on success for setting vios security
'''
import logging
import os
LOG_FILENAME = "/tmp/ansible_power_hmc_{0}.log".format(os.getpid())
logger = logging.getLogger(__name__)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_resource import Hmc
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError
import sys


def init_logger():
    old_umask = os.umask(0o177)
    try:
        logging.basicConfig(
            filename=LOG_FILENAME,
            format='[%(asctime)s] %(levelname)s: [%(funcName)s] %(message)s',
            level=logging.DEBUG)
    finally:
        os.umask(old_umask)


def validate_parameters(params):
    unsupportedList = []
    opr = None
    if params['state'] is not None:
        opr = params['state']
    else:
        opr = params['action']
    mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'vios_name']
    if opr == 'setting_security':
        unsupportedList = ['ip_version', 'firewall_config', 'active', 'reload']
        if params['level'] is None and params['file'] is None:
            raise ParameterError("Either level or file parameter should be propvided.")
        if params['level'] and params['file']:
            raise ParameterError("level and file parameter are mutually exclusive.")
    if opr == 'setting_firewall':
        unsupportedList = ['level', 'rule', 'file']
        if str(params['ip_version']).lower() != 'ipv6':
            params['ip_version'] = 'ipv4'
        if params['firewall_config'] is not None:
            for each in params['firewall_config']:
                if each['timeout'] is not None:
                    timeout = str(each['timeout']).strip().lower()
                    if timeout.endswith(('h', 'm', 'd')) or timeout.isdigit():
                        if timeout.isdigit() and int(timeout) > 2592000:
                            raise ParameterError("timeout should be less than 30 days(2592000 sec)")
                        elif not timeout.isdigit():
                            limits = {'h': 720, 'm': 43200, 'd': 30}
                            for unit in limits:
                                if timeout.endswith(unit):
                                    value_str = timeout[:-1]
                                    if int(value_str) > limits[unit]:
                                        raise ParameterError("timeout should be less than 30 days")
                    else:
                        raise ParameterError("timeout can be specified as a number, or with a number followed by m/h/d.")
        if (str(params['reload']).lower() == 'true' and str(params['active']).lower() != 'true'):
            raise ParameterError("Reload option can be applied only with active option.")
    if opr == 'firewall_facts':
        unsupportedList = ['level', 'rule', 'file', 'firewall_config', 'active', 'reload']
        if str(params['ip_version']).lower() != 'ipv6':
            params['ip_version'] = 'ipv4'
    collate = []
    for eachMandatory in mandatoryList:
        if not params[eachMandatory]:
            collate.append(eachMandatory)
    if collate:
        if len(collate) == 1:
            raise ParameterError("mandatory parameter '%s' is missing" % (collate[0]))
        else:
            raise ParameterError("mandatory parameters '%s' are missing" % (','.join(collate)))

    collate = []
    for eachUnsupported in unsupportedList:
        if params[eachUnsupported]:
            collate.append(eachUnsupported)

    if collate:
        if len(collate) == 1:
            raise ParameterError("unsupported parameter: %s" % (collate[0]))
        else:
            raise ParameterError("unsupported parameters: %s" % (', '.join(collate)))


def apply_security_setting(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    changed = False
    system_name = params['system_name']
    vios_name = params['vios_name']
    validate_parameters(params)
    sys_list = (
        hmc_conn.execute("lssyscfg -r sys -F name").splitlines() + hmc_conn.execute("lssyscfg -r sys -F type_model*serial_num").splitlines()
    )
    if system_name not in sys_list:
        module.fail_json(msg="The managed system is not available in HMC")
    else:
        if params['vios_name'] is not None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F name".format(system_name)).splitlines())
        if vios_name not in vios_list:
            module.fail_json(msg="The vios is not available in the managed system")
    cmd = hmc.create_viosecure_command(params, None)
    try:
        result = hmc.runCommandOnVIOS(system_name, vios_name, cmd, False)
        changed = True
    except Exception as e:
        return False, repr(e), None

    return changed, result.splitlines(), None


def firewall_setting(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    system_name = params['system_name']
    vios_name = params['vios_name']
    validate_parameters(params)
    changed = False
    failed_ports = []
    sys_list = (
        hmc_conn.execute("lssyscfg -r sys -F name").splitlines() + hmc_conn.execute("lssyscfg -r sys -F type_model*serial_num").splitlines()
    )
    if system_name not in sys_list:
        module.fail_json(msg="The managed system is not available in HMC")
    if vios_name is not None:
        vios_list = hmc_conn.execute(
            f"lssyscfg -r lpar -m {system_name} -F name"
        ).splitlines()
    if vios_name not in vios_list:
        module.fail_json(msg="The vios is not available in the managed system")
    if params['active'] is not None:
        if str(params['active']).lower() == 'true':
            active_cmd = "viosecure -firewall on"
            if str(params['ip_version']).lower() == 'ipv6':
                active_cmd += ' -ip6'
            if str(params['reload']).lower() == 'true':
                active_cmd += ' -reload '
        elif str(params['active']).lower() == 'false':
            active_cmd = "viosecure -firewall off"
            if str(params['ip_version']).lower() == 'ipv6':
                active_cmd += ' -ip6'
        try:
            hmc.runCommandOnVIOS(system_name, vios_name, active_cmd, False)
            changed = True
        except Exception as e:
            return False, repr(e), None
    params['firewall'] = True
    if params['firewall_config'] is not None:
        for each in params['firewall_config']:
            cmd = hmc.create_viosecure_command(params, each)
            try:
                hmc.runCommandOnVIOS(system_name, vios_name, cmd, False)
                changed = True
            except Exception as e:
                port = each.get('port', 'unknown')
                reason = str(e)
                if 'the port for the allow rule was not found in the database' not in reason.lower():
                    failed_ports.append({'port': port, 'reason': reason})
    security_info = display_firewall_setting(module, params)
    if params['firewall_config'] is not None:
        if len(failed_ports) == len(params['firewall_config']):
            return False, str(failed_ports), None
    return changed, security_info, failed_ports


def display_firewall_setting(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    system_name = params['system_name']
    vios_name = params['vios_name']
    validate_parameters(params)
    sys_list = (
        hmc_conn.execute("lssyscfg -r sys -F name").splitlines() + hmc_conn.execute("lssyscfg -r sys -F type_model*serial_num").splitlines()
    )
    if system_name not in sys_list:
        module.fail_json(msg="The managed system is not available in HMC")
    cmd = "viosecure -firewall view  -fmt , "
    if str(params['ip_version']).lower() == 'ipv6':
        cmd += "-ip6"
    try:
        result = hmc.runCommandOnVIOS(system_name, vios_name, cmd, False)
    except Exception as e:
        return False, repr(e), None

    firewall = {}
    firewall[params['ip_version']] = {}
    rules = []
    lines = result.split('\n')
    status = lines.pop(0)
    if status == 'ON':
        firewall[params['ip_version']]['active'] = True
    else:
        firewall[params['ip_version']]['active'] = False
    for line in lines:
        fields = line.split(',', 6)
        if len(fields) == 6:
            rule = {}
            if fields[0] != 'all':
                rule['interface'] = fields[0]
            if fields[1] != 'any':
                rule['port'] = int(fields[1])
            else:
                rule['port'] = int(fields[2])
                rule['remote'] = True
            if (params['ip_version'] == 'ipv6' and fields[4] != '::') or (params['ip_version'] == 'ipv4' and fields[4] != '0.0.0.0'):
                rule['address'] = fields[4]
            if fields[5] != '0':
                rule['timeout'] = fields[5]
            rules += [rule]
    firewall[params['ip_version']]['rules'] = rules

    return False, firewall, None


def perform_task(module):
    params = module.params
    actions = {
        "setting_security": apply_security_setting,
        "firewall_facts": display_firewall_setting,
        "setting_firewall": firewall_setting
    }
    oper = 'state'
    try:
        return actions[params[oper]](module, params)
    except Exception as error:
        return False, repr(error), None


def run_module():

    firewall_args = dict(port=dict(type='int', required=True),
                         interface=dict(type='str'),
                         remote=dict(type='bool'),
                         address=dict(type='str'),
                         timeout=dict(type='str'),
                         present=dict(type='str', choices=['allow', 'deny', 'ALLOW', 'DENY'], required=True),
                         )
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
        system_name=dict(type='str', required=True),
        vios_name=dict(type='str', required=True),
        level=dict(type='str', choices=['low', 'medium', 'high', 'default']),
        rule=dict(type='str'),
        file=dict(type='str'),
        ip_version=dict(type='str', choices=['ipv4', 'ipv6', 'IPV4', 'IPV6']),
        firewall_config=dict(type='list',
                             elements='dict',
                             options=firewall_args
                             ),
        active=dict(type='bool'),
        reload=dict(type='bool'),
        state=dict(type='str', choices=['setting_security', 'firewall_facts', 'setting_firewall']),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_if=[['state', 'setting_security', ['hmc_host', 'hmc_auth', 'system_name', 'vios_name']],
                     ['state', 'firewall_facts', ['hmc_host', 'hmc_auth', 'system_name', 'vios_name']],
                     ['state', 'setting_firewall', ['hmc_host', 'hmc_auth', 'system_name', 'vios_name']],
                     ],
    )

    if module._verbosity >= 5:
        init_logger()

    if sys.version_info < (3, 0):
        py_ver = sys.version_info[0]
        module.fail_json(msg="Unsupported Python version {0}, supported python version is 3 and above".format(py_ver))

    changed, info, warning = perform_task(module)

    if isinstance(info, str):
        module.fail_json(msg=info)

    result = {}
    result['changed'] = changed
    if info:
        result['security_facts'] = info
    if warning:
        result['warning'] = warning

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
