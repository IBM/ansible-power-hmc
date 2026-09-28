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
module: vios_alt_root_vg
author:
    - Sreenidhi S(@SreenidhiS1)
short_description: Create/Cleanup an alternate rootvg disk on a VIOS
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
    - Copy the rootvg to an alternate disk
    - Cleanup an existing alternate disk copy.
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
    vios_name:
        description:
            - The name of the VirtualIOServer.
        type: str
    targets:
        description:
            - Provided with C(copy), an alternate rootvg will be created on these targets.
            - Provided with C(clean), it removes the owning volume manager from the target disk(s).
        type: list
        elements: str
    disk_size_policy:
        description:
            - When I(state=copy), specifies how to choose the alternate disk if I(targets) is not specified.
            - C(minimize) smallest disk that can be selected.
            - C(upper) first disk found bigger than the rootvg disk.
            - C(lower) disk size less than rootvg disk size but big enough to contain the used physical partitions.
            - C(nearest) disk size closest to the rootvg disk.
        type: str
        choices: [ minimize, upper, lower, nearest ]
    force:
        description:
            - Forces removal of any existing alternate disk copy on target disks.
            - Valid only for C(copy) state.
        type: bool
        default: False
    state:
        description:
            - C(copy) to create alternate rootvg disk.
            - C(clean) to cleanup an existing alternate disk copy.
        type: str
        choices: ['copy', 'clean']
'''

EXAMPLES = '''
- name: Copy the rootvg to an alternate disk hdisk1
  ibm.power_hmc.vios_alt_root_vg:
    hmc_host: '{{ inventory_hostname }}'
    hmc_auth: "{{ curr_hmc_auth }}"
    system_name: <system-name>
    vios_name: <vios-name>
    targets:
      - hdisk1
    state: copy

- name: Copy the rootvg to multiple disks hdisk1 and hdisk2
  ibm.power_hmc.vios_alt_root_vg:
    hmc_host: '{{ inventory_hostname }}'
    hmc_auth: "{{ curr_hmc_auth }}"
    system_name: <system-name>
    vios_name: <vios-name>
    targets:
      - hdisk1
      - hdisk2
    state: copy

- name: Copy the rootvg using minimize disk_size_policy
  ibm.power_hmc.vios_alt_root_vg:
    hmc_host: '{{ inventory_hostname }}'
    hmc_auth: "{{ curr_hmc_auth }}"
    system_name: <system-name>
    vios_name: <vios-name>
    disk_size_policy: minimize
    state: copy

- name: Cleanup an existing alternate disk
  ibm.power_hmc.vios_alt_root_vg:
    hmc_host: '{{ inventory_hostname }}'
    hmc_auth: "{{ curr_hmc_auth }}"
    system_name: <system-name>
    vios_name: <vios-name>
    state: clean
'''
RETURN = '''
alt_rootvg_info:
    description: Alternate rootvg information.
    type: dict
    returned: on success for copy rootvg
'''
import logging
import os
LOG_FILENAME = "/tmp/ansible_power_hmc_{0}.log".format(os.getpid())
logger = logging.getLogger(__name__)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_resource import Hmc
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import parse_error_response
import re
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

    if opr == 'copy':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'vios_name']
        if params['disk_size_policy'] is None and params['targets'] is None:
            raise ParameterError("Either disk_size_policy or targets should be propvided.")
        if params['disk_size_policy'] and params['targets']:
            raise ParameterError("disk_size_policy and targets are mutually exclusive.")
    if opr == 'clean':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'vios_name']
        unsupportedList = ['force', 'disk_size_policy']

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


def get_pvs(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    system_name = params['system_name']
    vios_name = params['vios_name']
    cmd = "lspv"

    try:
        result = hmc.runCommandOnVIOS(system_name, vios_name, cmd, False)
    except Exception as e:
        return False, repr(e), None

    pvs = {}
    if result is not None:
        for line in result.split('\n'):
            line = line.rstrip()
            match_key = re.match(r"^(hdisk\S+)\s+(\S+)\s+(\S+)\s*(\S*)", line)
            if match_key:
                pvs[match_key.group(1)] = {}
                pvs[match_key.group(1)]['pvid'] = match_key.group(2)
                pvs[match_key.group(1)]['vg'] = match_key.group(3)
                pvs[match_key.group(1)]['status'] = match_key.group(4)
    return pvs


def get_free_pvs(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    system_name = params['system_name']
    vios_name = params['vios_name']
    cmd = "lspv -free"

    try:
        result = hmc.runCommandOnVIOS(system_name, vios_name, cmd, False)
    except Exception as e:
        return False, repr(e), None

    free_pvs = {}
    if result is not None:
        for line in result.split('\n'):
            line = line.rstrip()
            match_key = re.match(r"^(hdisk\S+)\s+(\S+)\s+(\S+)\s*(\S*)", line)
            if match_key:
                free_pvs[match_key.group(1)] = {}
                free_pvs[match_key.group(1)]['pvid'] = match_key.group(2)
                free_pvs[match_key.group(1)]['size'] = int(match_key.group(3))
    return free_pvs


def check_size_rootvg(module, params):
    vg_info = {}
    vg_info["status"] = 1
    vg_info["rootvg_size"] = 0
    vg_info["used_size"] = 0
    total_size = 0
    used_size = 0

    total_pps = used_pps = pp_size = -1
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    system_name = params['system_name']
    vios_name = params['vios_name']
    cmd = "lsvg rootvg -field TOTALPPS USEDPPs PPSIZE -fmt ','"

    try:
        result = hmc.runCommandOnVIOS(system_name, vios_name, cmd, False).split('\n')[0]
    except Exception as e:
        return False, repr(e), None

    if result is not None:
        values = [int(part.split(' ')[0]) for part in result.split(',')]
        total_pps, used_pps, pp_size = values[:3]
        total_size = total_pps * pp_size
        used_size = used_pps * pp_size

    vg_info["status"] = 0
    vg_info["rootvg_size"] = total_size
    vg_info["used_size"] = used_size
    return vg_info


def find_valid_altdisk(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    system_name = params['system_name']
    vios_name = params['vios_name']

    if params['rootvg_info']['status'] != 0:
        error_msg = 'Wrong rootvg state'
        module.fail_json(msg=error_msg)

    try:
        pvs = get_pvs(module, params)
    except Exception as error:
        error_msg = parse_error_response(error)
        module.fail_json(msg=error_msg)

    found_altdisk = []
    for pv in pvs:
        if pvs[pv]['vg'] == 'altinst_rootvg':
            found_altdisk.append(pv)
    if found_altdisk:
        if not params['force']:
            error_msg = f'An alternate disk already exists on disk {found_altdisk}'
            module.fail_json(msg=error_msg)
        elif params['targets'] is not None and set(params['targets']) == set(found_altdisk):
            return False

        cmd = "alt_rootvg_op -X altinst_rootvg"
        try:
            hmc.runCommandOnVIOS(system_name, vios_name, cmd, True)
        except Exception as e:
            return False, repr(e), None

        if pvs is not None:
            for pv in pvs:
                if pvs[pv]['vg'] == 'altinst_rootvg':
                    cmd = "chpv -C {}".format(pv)
                    try:
                        hmc.runCommandOnVIOS(system_name, vios_name, cmd, True)
                    except Exception as e:
                        return False, repr(e), None

    pvs = get_free_pvs(module, params)
    if pvs is None:
        error_msg = 'No free disk available'
        module.fail_json(msg=error_msg)

    used_size = params['rootvg_info']["used_size"]
    rootvg_size = params['rootvg_info']["rootvg_size"]

    if not params['targets']:
        selected_disk = ""
        prev_disk = ""
        diffsize = 0
        prev_diffsize = 0

        for key in sorted(pvs, key=lambda k: pvs[k]['size']):
            hdisk = key
            if pvs[hdisk]['size'] < used_size:
                continue
            if params['disk_size_policy'] == 'minimize':
                selected_disk = hdisk
                break
            diffsize = pvs[hdisk]['size'] - rootvg_size
            if diffsize == 0:
                selected_disk = hdisk
                break
            if diffsize > 0:
                if params['disk_size_policy'] == 'upper':
                    selected_disk = hdisk
                elif params['disk_size_policy'] == 'lower':
                    if not prev_disk:
                        selected_disk = hdisk
                    else:
                        selected_disk = prev_disk
                else:
                    if prev_disk == "":
                        selected_disk = hdisk
                    elif abs(prev_diffsize) > diffsize:
                        selected_disk = hdisk
                    else:
                        selected_disk = prev_disk
                break
            prev_disk = hdisk
            prev_diffsize = diffsize
        if not selected_disk:
            if prev_disk:
                selected_disk = prev_disk
            else:
                error_msg = f'No available alternate disk with size greater than {rootvg_size} MB found'
                module.fail_json(msg=error_msg)
        params['targets'].append(selected_disk)

    else:
        tot_size = 0
        for hdisk in params['targets']:
            if hdisk not in pvs:
                error_msg = f'Alternate disk {hdisk} is either not found or not available'
                module.fail_json(msg=error_msg)
            tot_size += pvs[hdisk]['size']
        if tot_size < rootvg_size:
            if tot_size >= used_size:
                module.log('[WARNING] Alternate disks smaller than the current rootvg.')
            else:
                error_msg = f'Alternate disks too small ({tot_size} < {rootvg_size}).'
                module.fail_json(msg=error_msg)


def alt_disk_copy(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    validate_parameters(params)
    system_name = params['system_name']
    vios_name = params['vios_name']
    changed = False
    sys_list = (
        hmc_conn.execute("lssyscfg -r sys -F name").splitlines()
    )
    if system_name not in sys_list:
        module.fail_json(msg="The managed system is not available in HMC")
    else:
        if params['vios_name'] is not None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F name".format(system_name)).splitlines())
        if vios_name not in vios_list:
            module.fail_json(msg="The vios is not available in the managed system")

    try:
        params['rootvg_info'] = check_size_rootvg(module, params)
    except Exception as error:
        error_msg = parse_error_response(error)
        module.fail_json(msg=error_msg)

    if params['targets'] is None:
        params['targets'] = []
    result = find_valid_altdisk(module, params)

    if result is not False:
        target_list = ' '.join(str(x) for x in params['targets'])
        cmd = "alt_root_vg -target {}".format(target_list)
        try:
            hmc.runCommandOnVIOS(system_name, vios_name, cmd, False)
        except Exception as e:
            return False, repr(e), None

        changed = True
    return changed, None, None


def alt_disk_clean(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    validate_parameters(params)
    system_name = params['system_name']
    vios_name = params['vios_name']
    changed = False
    sys_list = (
        hmc_conn.execute("lssyscfg -r sys -F name").splitlines()
    )
    if system_name not in sys_list:
        module.fail_json(msg="The managed system is not available in HMC")
    else:
        if params['vios_name'] is not None:
            vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F name".format(system_name)).splitlines())
        if vios_name not in vios_list:
            module.fail_json(msg="The vios is not available in the managed system")

    pvs = get_pvs(module, params)
    if pvs is None:
        error_msg = 'No free disk available'
        module.fail_json(msg=error_msg)

    hdisks = []
    if params['targets']:
        for hdisk in params['targets']:
            if (hdisk not in pvs) or (pvs[hdisk]['vg'] != 'altinst_rootvg'):
                error_msg = f'Specified disk {hdisk} is not an alternate install rootvg'
                module.fail_json(msg=error_msg)
    else:
        for pv in pvs.items():
            if pv[1]['vg'] == 'altinst_rootvg':
                hdisks.append(pv[0])
        params['targets'] = hdisks

    if params['targets'] is not None or hdisks != []:
        cmd = "alt_rootvg_op -X altinst_rootvg"
        try:
            hmc.runCommandOnVIOS(system_name, vios_name, cmd, True)
        except Exception as e:
            return False, repr(e), None

        for hdisk in params['targets']:
            cmd = "chpv -C {}".format(hdisk)
            try:
                hmc.runCommandOnVIOS(system_name, vios_name, cmd, True)
            except Exception as e:
                return False, repr(e), None
    else:
        error_msg = 'altinst_rootvg volume group not exist'
        module.fail_json(msg=error_msg)

    changed = True
    return changed, None, None


def perform_task(module):
    params = module.params
    actions = {
        "copy": alt_disk_copy,
        "clean": alt_disk_clean
    }
    oper = 'state'
    try:
        return actions[params[oper]](module, params)
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
        system_name=dict(type='str'),
        vios_name=dict(type='str'),
        force=dict(type='bool', default=False),
        targets=dict(type='list', elements='str'),
        disk_size_policy=dict(type='str', choices=['minimize', 'upper', 'lower', 'nearest']),
        state=dict(type='str', choices=['copy', 'clean'])
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_if=[['state', 'copy', ['hmc_host', 'hmc_auth', 'system_name', 'vios_name']],
                     ['state', 'clean', ['hmc_host', 'hmc_auth', 'system_name', 'vios_name']],
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
        result['alt_rootvg_info'] = info

    if warning:
        result['warning'] = warning

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
