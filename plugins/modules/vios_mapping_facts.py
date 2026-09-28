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
module: vios_mapping_facts
author:
    - Sreenidhi S (@SreenidhiS1)
short_description: Returns the VIOS mapping of physical, logical, and virtual devices as facts.
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
    - Returns the VIOS mapping of physical, logical, and virtual devices as facts.
requirements:
- VIOS >= 2.2.5.0
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
                    - Username of the HMC to log in.
                required: true
                type: str
            password:
                description:
                    - Password of the HMC.
                required: true
                type: str
    system_name:
        description:
            - The name or MTMS (machine type model serial) of the managed system.
        type: str
    vios_name:
        description:
            - The name of the Virtual I/O Server.
        required: true
        type: str
    component:
        description:
            - Type of mapping to retrieve
            - C(vscsi) to list virtual SCSI devices.
            - C(npiv) to list NPIV devices.
            - C(net) to list shared Ethernet adapters.
            - C(vnic) to list server virtual NIC adapters.
            - C(ams) to list paging space devices that are used in active memory sharing.
            - C(suspend) to list suspended virtual adapters.
            - C(cluster) to list shared storage pool mappings.
            - C(all) to list all devices.
        type: str
        choices: ['vscsi', 'net', 'npiv', 'vnic', 'ams', 'suspend', 'cluster', 'all']
        default: 'all'
    vadapter:
        description:
            - Specifies the device name of a server virtual adapter.
            - Mutually exclusive with I(physloc)
        type: str
    physloc:
        description:
            - Specifies the device physical location code of a server virtual adapter.
            - Mutually exclusive with I(vadapter)
        type: str
    cpid:
        description:
            - Specifies the client partition ID, in decimal, for which to return device
              mapping information.
            - Use value 0 to display all mappings for the specified component.
            - Not applicable for C(net) and C(ams) components.
        type: int
    types:
        description:
            - Specifies the type of devices to display
            - C(disk) to list physical backing devices.
            - C(lv) to list logical volume backing devices.
            - C(optical) to list optical backing devices.
            - C(tape) to list tape backed devices.
            - C(file) to list file backed devices.
            - C(file_disk) to list file backed disk devices.
            - C(file_opt) to list file backed optical devices.
            - C(cl_disk) to list clustered backing devices.
            - C(usb_disk) to list USB disks.
            - Only applicable for C(vscsi) and C(ams) components
        type: list
        choices: ['disk', 'lv', 'optical', 'tape', 'file', 'file_disk', 'file_opt', 'cl_disk', 'usb_disk']
        elements: str
    vtd:
        description:
            - Specifies the active memory sharing (AMS) paging device to be displayed.
            - Only applicable for C(ams) component
        type: str
    hostname:
        description:
            - Specifies the host name or IP address of the VIOS partition.
            - Only applicable for C(cluster) component
        type: str
    state:
        description:
            - C(facts) gathers and returns information about mapping between physical, logical, and virtual devices
        type: str
        required: true
        choices: ['facts']
'''

EXAMPLES = '''
- name: Populate the mapping facts with the mapping information for VSCSI
  ibm.power_hmc.vios_mapping_facts:
    hmc_host: <hmc_host>
    hmc_auth:
      username: <hmc_username>
      password: <hmc_password>
    system_name: <system_name>
    vios_name: <vios_name>
    component: vscsi
    state: facts

- name: Populate the mapping facts with the mapping information for NPIV device vfchost0
  ibm.power_hmc.vios_mapping_facts:
    hmc_host: <hmc_host>
    hmc_auth:
      username: <hmc_username>
      password: <hmc_password>
    system_name: <system_name>
    vios_name: <vios_name>
    vadapter: vfchost0
    component: npiv
    state: facts

- name: Populate the mapping facts with the mapping information for all devices
  ibm.power_hmc.vios_mapping_facts:
    hmc_host: <hmc_host>
    hmc_auth:
      username: <hmc_username>
      password: <hmc_password>
    system_name: <system_name>
    vios_name: <vios_name>
    component: all
    state: facts

- name: Populate the mapping facts with the mapping information for optical backing devices
  ibm.power_hmc.vios_mapping_facts:
    hmc_host: <hmc_host>
    hmc_auth:
      username: <hmc_username>
      password: <hmc_password>
    system_name: <system_name>
    vios_name: <vios_name>
    types: optical
    state: facts
'''

RETURN = '''
mapping_facts:
    description: Respective configuration mapping information
    type: dict
    returned: on success for retrieving facts
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
mappings = {}


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
    opr = params['state']
    component = params['component']
    if opr == 'facts':
        mandatoryList = ['hmc_host', 'hmc_auth', 'vios_name']
        if component == 'vscsi':
            unsupportedList = ['vtd', 'hostname']
        elif component == 'npiv' or component == 'vnic':
            unsupportedList = ['vtd', 'types', 'hostname']
        elif component == 'net':
            unsupportedList = ['vtd', 'types', 'cpid', 'hostname']
        elif component == 'ams':
            unsupportedList = ['vadapter', 'physloc', 'cpid', 'hostname']
        elif component == 'suspend':
            unsupportedList = ['physloc', 'vtd', 'cpid', 'hostname']
        elif component == 'cluster':
            unsupportedList = ['physloc', 'vtd', 'cpid', 'types', 'vadapter']

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


def vscsi_mappings(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    system_name = params['system_name']
    vios_name = params['vios_name']
    cmd = hmc.get_mappings(params)
    try:
        result = hmc.runCommandOnVIOS(system_name, vios_name, cmd, False)
        mappings['vscsi'] = {}
        for line in result.splitlines():
            raw_fields = line.split(',')
            if len(raw_fields) < 9:
                continue
            fields = [field.strip() for field in raw_fields]

            svsa = fields[0]
            mapping = {}
            mapping['physloc'] = fields[1]
            mapping['clientid'] = int(fields[2], 16)
            mapping['vtds'] = {}
            for i in range(3, len(fields), 6):
                if not fields[i]:
                    break
                vtd = {}
                vtd['status'] = fields[i + 1]
                vtd['lun'] = fields[i + 2]
                if fields[i + 3]:
                    vtd['backing'] = fields[i + 3]
                if fields[i + 4]:
                    vtd['bdphysloc'] = fields[i + 4]
                if fields[i + 5] != 'N/A':
                    vtd['mirrored'] = fields[i + 5] != 'false'
                mapping['vtds'][fields[i]] = vtd
            mappings['vscsi'][svsa] = mapping
    except Exception as e:
        return False, repr(e), None


def npiv_mappings(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    system_name = params['system_name']
    vios_name = params['vios_name']
    cmd = hmc.get_mappings(params)
    try:
        result = hmc.runCommandOnVIOS(system_name, vios_name, cmd, False)
        mappings['npiv'] = {}
        for line in result.splitlines():
            raw_fields = line.split(',')
            if len(raw_fields) < 12:
                continue
            fields = [field.strip() for field in raw_fields]
            name = fields[0]
            mapping = {}
            mapping['physloc'] = fields[1]
            mapping['clntid'] = int(fields[2])
            if fields[3]:
                mapping['clntname'] = fields[3]
            if fields[4]:
                mapping['clntos'] = fields[4]
            mapping['status'] = fields[5]
            if fields[6]:
                mapping['fc'] = fields[6]
            if fields[7]:
                mapping['fcphysloc'] = fields[7]
            mapping['ports'] = int(fields[8])
            mapping['flags'] = int(fields[9], 16)
            if fields[10]:
                mapping['vfcclient'] = fields[10]
            if fields[11]:
                mapping['vfcclientdrc'] = fields[11]
            mappings['npiv'][name] = mapping
    except Exception as e:
        return False, repr(e), None


def net_mappings(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    system_name = params['system_name']
    vios_name = params['vios_name']
    cmd = hmc.get_mappings(params)
    try:
        result = hmc.runCommandOnVIOS(system_name, vios_name, cmd, False)
        mappings['net'] = {}
        for line in result.splitlines():
            raw_fields = line.split(',')
            if len(raw_fields) < 6:
                continue
            fields = [field.strip() for field in raw_fields]
            svea = fields[0]
            mapping = {}
            mapping['physloc'] = fields[1]
            if fields[2]:
                mapping['sea'] = fields[2]
            if fields[3]:
                mapping['backing'] = fields[3]
            if fields[4]:
                mapping['status'] = fields[4]
            if fields[5]:
                mapping['bdphysloc'] = fields[5]
            mappings['net'][svea] = mapping
    except Exception as e:
        return False, repr(e), None


def vnic_mappings(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    system_name = params['system_name']
    vios_name = params['vios_name']
    cmd = hmc.get_mappings(params)
    try:
        result = hmc.runCommandOnVIOS(system_name, vios_name, cmd, False)
        mappings['vnic'] = {}
        for line in result.splitlines():
            raw_fields = line.split(',')
            if len(raw_fields) < 10:
                continue
            fields = [field.strip() for field in raw_fields]
            name = fields[0]
            mapping = {}
            mapping['physloc'] = fields[1]
            if fields[2] != 'N/A':
                mapping['clntid'] = int(fields[2])
            if fields[3] != 'N/A':
                mapping['clntname'] = fields[3]
            if fields[4] != 'N/A':
                mapping['clntos'] = fields[4]
            if fields[5] != 'N/A':
                mapping['backing'] = fields[5]
            mapping['status'] = fields[6]
            mapping['bdphysloc'] = fields[7]
            if fields[8] != 'N/A':
                mapping['clntdev'] = fields[8]
            mapping['clntphysloc'] = fields[9]
            mappings['vnic'][name] = mapping
    except Exception as e:
        return False, repr(e), None


def ams_mappings(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    system_name = params['system_name']
    vios_name = params['vios_name']
    cmd = hmc.get_mappings(params)
    try:
        result = hmc.runCommandOnVIOS(system_name, vios_name, cmd, False)
        mappings['ams'] = {}
        for line in result.splitlines():
            raw_fields = line.split(',')
            if len(raw_fields) < 10:
                continue
            fields = [field.strip() for field in raw_fields]

            paging = fields[0]
            mapping = {}
            mapping['streamid'] = fields[1]
            mapping['clntid'] = int(fields[2], 16)
            mapping['status'] = fields[3]
            mapping['redundancy'] = fields[4] != 'no'
            mapping['backing'] = fields[5]
            mapping['poolid'] = fields[6]
            if fields[7]:
                mapping['vasi'] = fields[7]
            if fields[8]:
                mapping['pager'] = fields[8]
            if fields[9]:
                mapping['vbsd'] = fields[9]
            mappings['ams'][paging] = mapping
    except Exception as e:
        return False, repr(e), None


def suspend_mappings(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    system_name = params['system_name']
    vios_name = params['vios_name']
    cmd = hmc.get_mappings(params)
    try:
        result = hmc.runCommandOnVIOS(system_name, vios_name, cmd, False)
        mappings['suspend'] = {}
        for line in result.splitlines():
            raw_fields = line.split(',')
            if len(raw_fields) < 11:
                continue
            fields = [field.strip() for field in raw_fields]
            svsa = fields[0]
            mapping = {}
            mapping['state'] = fields[1]
            if fields[2]:
                mapping['clientname'] = fields[2]
            mapping['streamid'] = fields[3]
            mapping['clientid'] = int(fields[4], 16)
            mapping['vtds'] = {}
            for i in range(5, len(fields), 6):
                if not fields[i]:
                    break
                vtd = {}
                vtd['status'] = fields[i + 1]
                vtd['lun'] = fields[i + 2]
                if fields[i + 3]:
                    vtd['backing'] = fields[i + 3]
                if fields[i + 4]:
                    vtd['bdphysloc'] = fields[i + 4]
                if fields[i + 5] != 'N/A':
                    vtd['mirrored'] = fields[i + 5] != 'false'
                mapping['vtds'][fields[i]] = vtd
            mappings['suspend'][svsa] = mapping
    except Exception as e:
        return False, repr(e), None


def cluster_mappings(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    system_name = params['system_name']
    vios_name = params['vios_name']
    mappings['cluster'] = {}
    cmd = 'cluster -list -field cluster_name -fmt ,'
    try:
        result = hmc.runCommandOnVIOS(system_name, vios_name, cmd, False)
        clustername = result.splitlines()[0]
        mappings['cluster'][clustername] = {}
        cmd_new = hmc.get_cluster_mappings(params)
        result_new = hmc.runCommandOnVIOS(system_name, vios_name, cmd_new, False)
        physmap = {}
        for line in result_new.splitlines():
            raw_fields = line.split(',')
            if len(raw_fields) < 5:
                continue
            fields = [field.strip() for field in raw_fields]

            physloc = fields[0]
            if physloc not in physmap:
                physmap[physloc] = {}
                physmap[physloc]['vtds'] = {}
                if fields[1] != 'suspended':
                    physmap[physloc]['clientid'] = int(fields[1], 16)
            if fields[2]:
                vtd = fields[2]
                physmap[physloc]['vtds'][vtd] = {}
                physmap[physloc]['vtds'][vtd]['lun'] = fields[3]
                physmap[physloc]['vtds'][vtd]['backing'] = fields[4]
        mappings['cluster'][clustername] = physmap
    except Exception as e:
        return False, repr(e), None


def get_MS_names_by_lpar_name(hmc_obj, lpar_name):
    mss = hmc_obj.list_all_managed_system_details("name,state")
    ms_list = []
    for ms in mss:
        if ms["state"] == 'Operating':
            lpar_names = hmc_obj.list_all_lpars_details(ms["name"], "name")
            if lpar_name in lpar_names:
                ms_list.append(ms["name"])
    return ms_list


def identify_ManagedSystem_of_lpar(hmc, vm_name, module):
    system_name = None
    ms_name = get_MS_names_by_lpar_name(hmc, vm_name)
    if len(ms_name) == 1:
        system_name = ms_name[0]
    elif len(ms_name) > 1:
        err_msg = "Logical Partition Name:'{0}' found in more than one managed systems:'{1}'," \
                  " Please provide the system_name parameter to avoid the confusion".format(vm_name, ms_name)
        raise ParameterError(err_msg)
    else:
        err_msg = "Logical Partition Name:'{0}' not found in any of the managed systems".format(vm_name)
        module.warn(err_msg)
        return 1
    return system_name


def component_mapping(module, params):
    validate_parameters(params)
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    system_name = params['system_name']
    vios_name = params['vios_name']
    vios_list = []
    if params['vios_name'] is not None and system_name is None:
        system_name = identify_ManagedSystem_of_lpar(hmc, vios_name, module)
        params['system_name'] = system_name
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
    component = module.params['component']
    if component == 'all' or component == 'vscsi':
        vscsi_mappings(module, params)
    if component == 'all' or component == 'ams':
        ams_mappings(module, params)
    if component == 'all' or component == 'suspend':
        suspend_mappings(module, params)
    if not module.params['types']:
        if component == 'all' or component == 'npiv':
            npiv_mappings(module, params)
        if component == 'all' or component == 'net':
            net_mappings(module, params)
        if component == 'all' or component == 'vnic':
            vnic_mappings(module, params)
        if component == 'all' or component == 'cluster':
            cluster_mappings(module, params)
    if mappings == {}:
        msg = "No mappings found"
        return False, None, msg
    return False, mappings, None


def perform_task(module):
    params = module.params
    actions = {
        "facts": component_mapping
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
                          password=dict(required=True, type='str', no_log=True),
                      )
                      ),
        component=dict(type='str',
                       choices=['vscsi', 'net', 'npiv', 'vnic',
                                'ams', 'suspend', 'cluster', 'all'],
                       default='all'),
        system_name=dict(type='str'),
        vios_name=dict(type='str', required=True),
        vadapter=dict(type='str'),
        physloc=dict(type='str'),
        cpid=dict(type='int'),
        types=dict(type='list', elements='str',
                   choices=['disk', 'lv', 'optical', 'tape', 'usb_disk',
                            'file', 'file_disk', 'file_opt', 'cl_disk']),
        vtd=dict(type='str'),
        hostname=dict(type='str'),
        state=dict(type='str', choices=['facts'], required=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_if=[['state', 'facts', ['hmc_host', 'hmc_auth', 'vios_name']]],
        mutually_exclusive=[['vadapter', 'physloc']],
        supports_check_mode=True
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
        result['mapping_facts'] = info

    if warning:
        result['warning'] = warning

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
