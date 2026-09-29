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
module: vios
author:
    - Anil Vijayan (@AnilVijayan)
    - Navinakumar Kandakur (@nkandak1)
short_description: Creation and management of Virtual I/O Server partition
notes:
    - Only state=present, action=install and action=accept_license operations support passwordless authentication.
    - I(install) action parameters C(nim_gateway) and C(nim_subnetmask) are deprecated now and will be removed from future versions
      and as a replacement C(vios_gateway) and C(vios_subnetmask) can be used from now onwards.
description:
    - "Creates VIOS partition"
    - "Installs VIOS"
    - "Displays VIOS information"
    - "Accepts VIOS License"
    - "List all VIOS Images available in HMC"
    - "Copy VIOS Images from SFTP/NFS server"
    - "Delete VIOS Images from HMC"
version_added: 1.0.0
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
                type: str
    system_name:
        description:
            - The name or MTMS (machine type model serial) of the managed system.
        type: str
    name:
        description:
            - The name of the VirtualIOServer for installation through nim server or image available on HMC local disk.
        type: str
    settings:
        description:
            - To configure various supported attributes of VIOS partition.
            - Supports all the attributes available for creation of VIOS
              on the mksyscfg command except 'lpar_env'.
            - valid only for C(state) = I(present)
        type: dict
    nim_IP:
        description:
            - This parameter determines whether to use Network Installation Manager (NIM) rather than relying on the HMC based image for VIOS installation.
            - IP Address of the NIM Server.
            - valid only for C(action) = I(install)
        type: str
    location_code:
        description:
            - Network adapter location code to be used while installing VIOS through nim server.
            - If user doesn't provide, it automatically picks the first pingable adapter attached to the partition.
            - valid only for C(action) = I(install)
        type: str
    nim_vlan_id:
        description:
            - Specifies the VLANID(0 to 4094) to use for tagging Ethernet frames during network install for virtual network communication.
            - Default value is 0
            - valid only for C(action) = I(install)
        type: str
    nim_vlan_priority:
        description:
            - Specifies the VLAN priority (0 to 7) to use for tagging Ethernet frames during network install for virtual network communication.
            - Default value is 0
            - valid only for C(action) = I(install)
        type: str
    nim_gateway:
        description:
            - VIOS gateway IP Address.
            - valid only for C(action) = I(install)
            - supports installation through nim server.
            - This parameter is deprecated now and will be removed from future versions and as a replacement C(vios_gateway) can be used now onwards.
        type: str
    nim_subnetmask:
        description:
            - Subnetmask IP Address to be configured to VIOS.
            - valid only for C(action) = I(install)
            - supports installation through nim server.
            - This parameter is deprecated now and will be removed from future versions and as a replacement C(vios_subnetmask) can be used now onwards.
        type: str
    vios_gateway:
        description:
            - VIOS gateway IP Address.
            - valid only for C(action) = I(install)
            - supports installation through nim server and image available on the HMC local disk.
        type: str
    vios_subnetmask:
        description:
            - Subnetmask IP Address to be configured to VIOS.
            - valid only for C(action) = I(install)
            - supports installation through nim server and image available on the HMC local disk.
        type: str
    vios_IP:
        description:
            - IP Address to be configured to VIOS.
            - valid only for C(action) = I(install)
        type: str
    prof_name:
        description:
            - Profile Name to be used for VIOS install.
            - Default profile name 'default_profile'.
            - valid only for C(action) = I(install)
        type: str
    timeout:
        description:
            - Max waiting time in mins for VIOS to bootup fully.
            - Min timeout should be more than 10 mins.
            - Default value is 60 min.
            - valid only for C(action) = I(install)
        type: int
    image_dir:
        description:
            - This parameter determines whether to use the HMC based image for VIOS installation, rather than relying on the Network Installation Manager (NIM).
            - Name of the directory on which VIOS image is available on HMC.
            - This represent the same parameter C(directory_name) that is used during the copy action.
            - valid only for C(action) = I(install)
        type: str
    label:
        description:
            - Specifies a label name for installed vios to use instead of creating a default label name.
            - supports only installation through image available on the HMC local disk.
            - valid only for C(action) = I(install)
        type: str
    network_macaddr:
        description:
            - Specifies the client MAC address through which the network installation of the Virtual I/O Server will take place.
            - If user doesn't provide, it automatically picks the first pingable adapter attached to the partition.
            - valid only for C(action) = I(install)
        type: str
    vios_iso:
        description:
            - The vios iso file to be installed.
            - supports only installation through image available on the HMC local disk.
            - valid only for C(action) = I(install)
        type: str
    virtual_optical_media:
        description:
            - Provides the virtual optical media details.
            - Default value is False.
            - Valid only for C(state) = I(facts)
        type: bool
    free_pvs:
        description:
            - Provides the Unassigned Physical Volume details.
            - Default value is False.
            - Valid only for C(state) = I(facts)
        type: bool
    directory_name:
        description:
            - The name to give the VIOS installation image on the HMC.
        type: str
    files:
        description:
            - Specify one or two comma-separated VIOS ISO files.
            - Required for remote imports ['sftp', 'nfs']; not valid for USB.
        type: list
        elements: str
    directory_list:
        description:
            - The name of one or more VIOS installation images to remove.
        type: list
        elements: str
    media:
        description:
            - Media type for the VIOS installation (e.g., nfs, sftp).
        type: str
        choices: ['nfs', 'sftp']
    remote_server:
        description:
            - The host name or IP address of the remote server ['sftp', 'nfs'].
        type: str
    ssh_key_file:
        description:
            - Specify the SSH private key file name.
            - If not fully qualified, it must be in the user's home directory on the HMC.
            - This option is only valid for sftp and is mutually exclusive with password.
        type: str
    mount_location:
        description:
            - Required for VIOS image imports from NFS; specify the NFS server mount location.
        type: str
    remote_directory:
        description:
            - Specify the directory on the remote server for the VIOS installation image.
            - If not provided for SFTP, the user's home directory is used; for NFS, the mount location is used.
        type: str
    options:
        description:
            - Specify options for the NFS mount command in double quotes.
            - Default is version 3; use vers=4 for version 4. Valid only for VIOS image imports from NFS.
        type: str
        choices: ['3', '4']
    sftp_auth:
        description:
            - Username and Password credential of the SFTP Server.
        type: dict
        suboptions:
            sftp_username:
                description:
                    - Username of the SFTP server to login.
                type: str
            sftp_password:
                description:
                    - Password of the SFTP server.
                type: str
    state:
        description:
            - C(facts) fetch details of specified I(VIOS).
            - C(present) creates VIOS with specified I(settings).
            - C(listimages) list the VIOS images present in HMC
        type: str
        choices: ['facts', 'present', 'listimages']
    action:
        description:
            - C(install) install VIOS through NIM Server or disk.
            - C(accept_license) Accept license after fresh installation of VIOS.
            - C(copy) copies VIOS images from NFS/SFTP server to the HMC.
            - C(delete) deletes VIOS images present in the HMC.
        type: str
        choices: ['install', 'accept_license', 'copy', 'delete']
'''

EXAMPLES = '''
- name: Create VIOS with default configuration.
  ibm.power_hmc.vios:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: <managed_system_name/mtms>
    name: <vios_partition_name>
    state: present

- name: Create VIOS with user defined settings.
  ibm.power_hmc.vios:
    hmc_host: '{{ inventory_hostname }}'
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: <managed_system_name/mtms>
    name: <vios_partition_name>
    settings:
      profile_name: <profileName>
      io_slots: <ioslot1>,<ioslot2>
    state: present

- name: Install VIOS using NIM Server.
  ibm.power_hmc.vios:
    hmc_host: '{{ inventory_hostname }}'
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: <managed_system_name/mtms>
    name: <vios name>
    nim_IP: <NIM Server IP>
    nim_gateway: <vios gateway ip>
    vios_IP: <vios ip>
    nim_subnetmask: <subnetmask>
    action: install

- name: Install VIOS using the image available on the HMC local disk
  ibm.power_hmc.vios:
    hmc_host: '{{ inventory_hostname }}'
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: <managed_system_name/mtms>
    image_dir: <image directory name>
    vios_iso: <vios iso>
    vios_IP: <vios ip>
    vios_gateway: <vios gateway ip>
    vios_subnetmask: <subnetmask>
    network_macaddr: <mac address>
    name: <vios name>
    prof_name: <profile name>
    timeout: <timeout>
    label: <label>
    action: install

- name: Accept License after VIOS Installation.
  ibm.power_hmc.vios:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: <managed_system_name/mtms>
    name: <vios_partition_name>
    action: accept_license

- name: Show VIOS details with Free PVs and Virtual Optical Media.
  ibm.power_hmc.vios:
    hmc_host: "{{ inventory_hostname }}"
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    system_name: <managed_system_name/mtms>
    name: <vios_partition_name>
    free_pvs: true
    virtual_optical_media: true
    state: facts

- name: List all VIOS Images
  ibm.power_hmc.vios:
    hmc_host: '{{ inventory_hostname }}'
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    state: listimages
    register: images_info

- name: Stdout the VIOS Images Info
  debug:
    msg: '{{ images_info }}'

- name: Copy Vios Image via SFTP Server
  ibm.power_hmc.vios:
    hmc_host: '{{ inventory_hostname }}'
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    media: sftp
    directory_name: dir_name
    remote_server: remote_server_IP
    sftp_auth:
      sftp_username: username
      sftp_password: password
    remote_directory: <directory_path>
    files:
      - file1
      - file2
    action: copy
    register: testout

- name: Copy Vios Image via NFS
  ibm.power_hmc.vios:
    hmc_host: '{{ inventory_hostname }}'
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    media: nfs
    directory_name: dir_name
    remote_server: remote_server_IP
    remote_directory: <directory_path>
    mount_location: <mount_location>
    files:
      - file1
      - file2
    options: <NFS_version>
    action: copy
    register: testout

- name: Delete Vios Image
  ibm.power_hmc.vios:
    hmc_host: '{{ inventory_hostname }}'
    hmc_auth:
      username: '{{ ansible_user }}'
      password: '{{ hmc_password }}'
    directory_list:
      - dir_name1
      - dir_name2
    action: delete
'''

RETURN = '''
vios_info:
    description: Respective VIOS information
    type: dict
    returned: on success for action install
'''

import logging
import os
LOG_FILENAME = "/tmp/ansible_power_hmc_{0}.log".format(os.getpid())
logger = logging.getLogger(__name__)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_resource import Hmc
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import parse_error_response
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import HmcRestClient
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_constants import HmcConstants
import re
import sys
import json


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
    '''Check that the input parameters satisfy the mutual exclusiveness of HMC'''
    opr = None
    if params['state'] is not None:
        opr = params['state']
    else:
        opr = params['action']

    if opr == 'install':
        if params['nim_IP'] and params['image_dir']:
            raise ParameterError("nim_IP and image_dir are mutually exclusive.")
        elif params['nim_IP'] and not params['image_dir']:
            if params['nim_gateway'] and params['nim_subnetmask']:
                mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'nim_IP', 'vios_IP', 'nim_subnetmask', 'nim_gateway', 'name']
                unsupportedList = ['settings', 'virtual_optical_media', 'free_pvs', 'vios_iso', 'image_dir', 'network_macaddr', 'label',
                                   'vios_gateway', 'vios_subnetmask', 'sftp_auth', 'remote_server', 'files', 'mount_location',
                                   'ssh_key_file', 'remote_directory', 'options', 'directory_list', 'media', 'directory_name']
            elif params['nim_gateway'] and params['vios_subnetmask']:
                mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'nim_IP', 'vios_IP', 'vios_subnetmask', 'nim_gateway', 'name']
                unsupportedList = ['settings', 'virtual_optical_media', 'free_pvs', 'vios_iso', 'image_dir', 'network_macaddr', 'label',
                                   'vios_gateway', 'nim_subnetmask', 'sftp_auth', 'remote_server', 'files', 'mount_location',
                                   'ssh_key_file', 'remote_directory', 'options', 'directory_list', 'media', 'directory_name']
            elif params['vios_gateway'] and params['nim_subnetmask']:
                mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'nim_IP', 'vios_IP', 'nim_subnetmask', 'vios_gateway', 'name']
                unsupportedList = ['settings', 'virtual_optical_media', 'free_pvs', 'vios_iso', 'image_dir', 'network_macaddr', 'label',
                                   'nim_gateway', 'vios_subnetmask', 'sftp_auth', 'remote_server', 'files', 'mount_location',
                                   'ssh_key_file', 'remote_directory', 'options', 'directory_list', 'media', 'directory_name']
            elif params['vios_gateway'] and params['vios_subnetmask']:
                mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'nim_IP', 'vios_IP', 'vios_subnetmask', 'vios_gateway', 'name']
                unsupportedList = ['settings', 'virtual_optical_media', 'free_pvs', 'vios_iso', 'image_dir', 'network_macaddr', 'label',
                                   'nim_gateway', 'nim_subnetmask', 'sftp_auth', 'remote_server', 'files', 'mount_location',
                                   'ssh_key_file', 'remote_directory', 'options', 'directory_list', 'media', 'directory_name']
            else:
                raise ParameterError("Provide gateway and subnetmask details")
        elif params['image_dir'] and not params['nim_IP']:
            mandatoryList = ['hmc_host', 'hmc_auth', 'vios_iso', 'image_dir', 'vios_IP', 'vios_gateway', 'vios_subnetmask', 'system_name', 'name']
            unsupportedList = ['nim_IP', 'nim_gateway', 'nim_subnetmask', 'directory_name', 'sftp_auth', 'remote_server', 'files', 'mount_location',
                               'ssh_key_file', 'remote_directory', 'options', 'directory_list', 'media', 'settings', 'virtual_optical_media',
                               'free_pvs', 'location_code', 'nim_vlan_id', 'nim_vlan_priority']
        else:
            raise ParameterError("Provide either nim_IP or image_dir for vios installation")

    elif opr == 'present':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'name']
        unsupportedList = ['nim_IP', 'nim_gateway', 'vios_IP', 'nim_subnetmask', 'prof_name',
                           'location_code', 'nim_vlan_id', 'nim_vlan_priority', 'timeout', 'virtual_optical_media', 'free_pvs', 'directory_name',
                           'directory_list', 'sftp_auth', 'remote_server', 'files', 'mount_location', 'ssh_key_file', 'remote_directory', 'options', 'media',
                           'vios_iso', 'image_dir', 'vios_gateway', 'vios_subnetmask']
    elif opr == 'accept_license':
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'name']
        unsupportedList = ['nim_IP', 'nim_gateway', 'vios_IP', 'nim_subnetmask', 'prof_name', 'location_code', 'nim_vlan_id', 'nim_vlan_priority',
                           'timeout', 'settings', 'virtual_optical_media', 'free_pvs', 'directory_name', 'directory_list', 'sftp_auth', 'remote_server',
                           'files', 'mount_location', 'ssh_key_file', 'remote_directory', 'options', 'media',
                           'vios_iso', 'image_dir', 'vios_gateway', 'vios_subnetmask']
    elif opr == 'copy':
        if not params['media']:
            raise ParameterError("mandatory parameter 'media' is missing")
        else:
            media = params['media'].lower()
        if media == 'sftp':
            sftp_auth = params.get('sftp_auth')
            if sftp_auth is None:
                raise ParameterError("mandatory parameter 'sftp_auth' is missing")
            if sftp_auth.get('sftp_username') is None:
                raise ParameterError("mandatory parameter 'sftp_username' is missing")
            sftp_password = sftp_auth.get('sftp_password')
            ssh_key_file = params.get('ssh_key_file')
            if sftp_password and ssh_key_file:
                raise ParameterError("Parameters 'sftp_password' and 'ssh_key_file' are mutually exclusive")
            elif not sftp_password and not ssh_key_file:
                raise ParameterError("Please provide either 'sftp_password' or 'ssh_key_file' for authentication.")
            mandatoryList = ['hmc_host', 'hmc_auth', 'directory_name', 'remote_server', 'files']
            unsupportedList = ['system_name', 'directory_list', 'name', 'mount_location', 'options', 'nim_IP', 'nim_gateway', 'vios_IP',
                               'nim_subnetmask', 'prof_name', 'location_code', 'nim_vlan_id', 'nim_vlan_priority', 'timeout', 'settings',
                               'virtual_optical_media', 'free_pvs', 'image_dir', 'vios_iso', 'vios_gateway', 'vios_subnetmask']
        elif media == 'nfs':
            mandatoryList = ['hmc_host', 'hmc_auth', 'directory_name', 'remote_server', 'files', 'mount_location']
            unsupportedList = ['sftp_auth', 'directory_list', 'ssh_key_file', 'system_name', 'name', 'nim_IP', 'nim_gateway', 'vios_IP',
                               'nim_subnetmask', 'prof_name', 'location_code', 'nim_vlan_id', 'nim_vlan_priority', 'timeout', 'settings',
                               'virtual_optical_media', 'free_pvs', 'image_dir', 'vios_iso', 'vios_gateway', 'vios_subnetmask']

    elif opr == 'listimages':
        mandatoryList = ['hmc_host', 'hmc_auth']
        unsupportedList = ['ssh_key_file', 'remote_directory', 'directory_name', 'directory_list', 'sftp_auth', 'remote_server', 'files',
                           'system_name', 'name', 'mount_location', 'options', 'nim_IP', 'nim_gateway', 'vios_IP', 'nim_subnetmask', 'prof_name',
                           'location_code', 'nim_vlan_id', 'nim_vlan_priority', 'timeout', 'settings', 'virtual_optical_media', 'free_pvs',
                           'media', 'image_dir', 'vios_iso', 'vios_gateway', 'vios_subnetmask']
    elif opr == 'delete':
        mandatoryList = ['hmc_host', 'hmc_auth', 'directory_list']
        unsupportedList = ['ssh_key_file', 'remote_directory', 'sftp_auth', 'directory_name', 'remote_server', 'files', 'system_name', 'name',
                           'mount_location', 'options', 'nim_IP', 'nim_gateway', 'vios_IP', 'nim_subnetmask', 'prof_name', 'location_code',
                           'nim_vlan_id', 'nim_vlan_priority', 'timeout', 'settings', 'virtual_optical_media', 'free_pvs', 'media',
                           'image_dir', 'vios_iso', 'vios_gateway', 'vios_subnetmask']
    else:
        mandatoryList = ['hmc_host', 'hmc_auth', 'system_name', 'name']
        unsupportedList = ['nim_IP', 'nim_gateway', 'vios_IP', 'nim_subnetmask', 'prof_name', 'location_code', 'nim_vlan_id', 'nim_vlan_priority',
                           'timeout', 'settings', 'directory_name', 'directory_list', 'sftp_auth', 'remote_server', 'files', 'mount_location',
                           'ssh_key_file', 'remote_directory', 'options', 'media', 'image_dir', 'vios_iso', 'vios_gateway', 'vios_subnetmask']

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


def fetchViosInfo(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    name = params['name']
    virtual_optical_media = params['virtual_optical_media']
    free_pvs = params['free_pvs']
    validate_parameters(params)
    lpar_config = {}
    changed = False

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    if re.match(HmcConstants.MTMS_pattern, system_name):
        try:
            system_name = hmc.getSystemNameFromMTMS(system_name)
        except HmcError as on_system_error:
            return changed, repr(on_system_error), None

    try:
        with HmcRestClient(hmc_host, hmc_user, password) as rest_conn:
            try:
                system_uuid, server_dom = rest_conn.getManagedSystem(system_name)
            except Exception as error:
                error_msg = parse_error_response(error)
                module.fail_json(msg=error_msg)
            if not system_uuid:
                module.fail_json(msg="Given system is not present")
            ms_state = server_dom.xpath("//DetailedState")[0].text
            if ms_state != 'None':
                module.fail_json(msg="Given system is in " + ms_state + " state")
            vios_quick_response = rest_conn.getVirtualIOServersQuick(system_uuid)
            vios_list = []
            vios_dom = None
            vios_UUID = None
            if vios_quick_response is not None:
                vios_list = json.loads(vios_quick_response)
            if vios_list:
                for vios in vios_list:
                    if vios['PartitionName'] == name:
                        lpar_config = vios
                        vios_UUID = vios['UUID']
                        vios_dom = rest_conn.getVirtualIOServer(vios_UUID)
                        break
                else:
                    module.fail_json("VIOS: {0} not found in the Managed System: {1}".format(name, system_name))
                lpar_config['MaximumMemory'] = vios_dom.xpath(
                    '//PartitionMemoryConfiguration//MaximumMemory')[0].text
                lpar_config['MinimumMemory'] = vios_dom.xpath(
                    '//PartitionMemoryConfiguration//MinimumMemory')[0].text
                lpar_config['CurrentHasDedicatedProcessors'] = vios_dom.xpath(
                    '//PartitionProcessorConfiguration//CurrentHasDedicatedProcessors')[0].text

                if lpar_config['CurrentHasDedicatedProcessors'] == 'false':
                    lpar_config['MaximumProcessingUnits'] = vios_dom.xpath(
                        '//PartitionProcessorConfiguration//MaximumProcessingUnits')[0].text
                    lpar_config['MaximumVirtualProcessors'] = vios_dom.xpath(
                        '//PartitionProcessorConfiguration//MaximumVirtualProcessors')[0].text
                    lpar_config['MinimumProcessingUnits'] = vios_dom.xpath(
                        '//PartitionProcessorConfiguration//MinimumProcessingUnits')[0].text
                    lpar_config['MinimumVirtualProcessors'] = vios_dom.xpath(
                        '//PartitionProcessorConfiguration//MinimumVirtualProcessors')[0].text
                else:
                    lpar_config['MaximumProcessors'] = vios_dom.xpath(
                        '//PartitionProcessorConfiguration//MaximumProcessors')[0].text
                    lpar_config['MinimumProcessors'] = vios_dom.xpath(
                        '//PartitionProcessorConfiguration//MinimumProcessors')[0].text

                if virtual_optical_media:
                    vom_dict = rest_conn.getVIOSVirtualOpticalMediaDetails(vios_dom)
                    lpar_config['VirtualOpticalMedia'] = vom_dict
                if free_pvs:
                    pv_list = []
                    # Initialize with empty list
                    lpar_config['FreePhysicalVolumes'] = []
                    try:
                        pv_xml_list = rest_conn.getFreePhyVolume(vios_UUID)
                        for each in pv_xml_list:
                            pv_dict = {}
                            pv_dict['VolumeName'] = each.xpath("VolumeName")[0].text
                            pv_dict['VolumeCapacity'] = each.xpath("VolumeCapacity")[0].text
                            pv_dict['VolumeState'] = each.xpath("VolumeState")[0].text
                            pv_dict['VolumeUniqueID'] = each.xpath("VolumeUniqueID")[0].text
                            pv_dict['ReservePolicy'] = each.xpath("ReservePolicy")[0].text
                            pv_dict['ReservePolicyAlgorithm'] = each.xpath("ReservePolicyAlgorithm")[0].text
                            pv_list.append(pv_dict)
                        lpar_config['FreePhysicalVolumes'] = pv_list
                    except Exception as error:
                        logger.debug(error)
    except Exception as error:
        error_msg = parse_error_response(error)
        module.fail_json(msg=error_msg)

    if lpar_config:
        return False, lpar_config, None
    else:
        return False, None, None


# Collection of attributes not supported by vios partition
not_support_settings = ['lpar_env', 'os400_restricted_io_mode', 'console_slot', 'alt_restart_device_slot',
                        'alt_console_slot', 'op_console_slot', 'load_source_slot', 'hsl_pool_id',
                        'virtual_opti_pool_id', 'vnic_adapters', 'electronic_err_reporting', 'suspend_capable',
                        'simplified_remote_restart_capable', 'remote_restart_capable', 'migration_disabled',
                        'virtual_serial_num', 'min_num_huge_pages', 'desired_num_huge_pages', 'max_num_huge_pages',
                        'name', 'lpar_name', 'rs_device_name', 'powervm_mgmt_capable', 'primary_paging_vios_name',
                        'primary_paging_vios_id', 'secondary_paging_vios_name', 'secondary_paging_vios_id',
                        'primary_rs_vios_name', 'primary_rs_vios_id', 'secondary_rs_vios_name', 'secondary_rs_vios_id']


def validate_settings_param(settings):
    if settings:
        anyPresent = [each for each in settings if each in not_support_settings]
        if anyPresent:
            raise ParameterError("Invalid parameters: %s" % (', '.join(anyPresent)))


def createVios(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    name = params['name']
    validate_parameters(params)
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    prof_name = None

    validate_settings_param(params['settings'])

    try:
        lpar_config = hmc.getPartitionConfig(system_name, name)
        if lpar_config:
            logger.debug(lpar_config)
            return False, lpar_config, None
    except HmcError as list_error:
        if 'HSCL8012' not in repr(list_error):
            raise

    try:
        hmc.createVirtualIOServer(system_name, name, params['settings'])

        if params.get('settings'):
            # Settings default profile name to 'default_profile' in case user didnt provide
            prof_name = params.get('settings').get('profile_name', 'default_profile')

        lpar_config = hmc.getPartitionConfig(system_name, name, prof_name)
    except HmcError as vios_error:
        return False, repr(vios_error), None

    return True, lpar_config, None


def installViosUsingNim(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    name = params['name']
    nim_IP = params['nim_IP']
    nim_gateway = params['nim_gateway'] or params['vios_gateway']
    vios_IP = params['vios_IP']
    prof_name = params['prof_name'] or 'default_profile'
    location_code = params['location_code']
    nim_subnetmask = params['nim_subnetmask'] or params['vios_subnetmask']
    nim_vlan_id = params['nim_vlan_id'] or '0'
    nim_vlan_priority = params['nim_vlan_priority'] or '0'
    timeout = params['timeout'] or 60
    validate_parameters(params)
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    changed = False
    vios_property = None
    warn_msg = None

    if timeout < 10:
        module.fail_json(msg="timeout should be more than 10mins")
    try:
        if location_code:
            hmc.installOSFromNIM(location_code, nim_IP, nim_gateway, vios_IP, nim_vlan_id, nim_vlan_priority, nim_subnetmask, name, prof_name, system_name)
        else:
            dvcdictlt = hmc.fetchIODetailsForNetboot(nim_IP, nim_gateway, vios_IP, name, prof_name, system_name, nim_subnetmask)
            for dvcdict in dvcdictlt:
                if dvcdict['Ping Result'] == 'successful':
                    location_code = dvcdict['Location Code']
                    break
            if location_code:
                hmc.installOSFromNIM(location_code, nim_IP, nim_gateway, vios_IP, nim_vlan_id, nim_vlan_priority, nim_subnetmask,
                                     name, prof_name, system_name)
            else:
                module.fail_json(msg="None of adapters part of the profile is reachable through network. Please attach correct network adapter")

        rmc_state, vios_property, ref_code = hmc.checkForOSToBootUpFully(system_name, name, timeout)
        if rmc_state:
            changed = True
        elif ref_code in ['', '00']:
            changed = True
            warn_msg = "VIOS installation has been successfull but RMC didnt come up, please check the HMC firewall and security"
        else:
            module.fail_json(msg="VIOS Installation failed even after waiting for " + str(timeout) + " mins and the reference code is " + ref_code)
    except HmcError as install_error:
        return False, repr(install_error), None

    return changed, vios_property, warn_msg


def installViosUsingDisk(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    vios_iso = params['vios_iso']
    image_dir = params['image_dir']
    vios_IP = params['vios_IP']
    vios_gateway = params['vios_gateway']
    vios_subnetmask = params['vios_subnetmask']
    network_macaddr = params['network_macaddr']
    system_name = params['system_name']
    name = params['name']
    prof_name = params['prof_name'] or 'default_profile'
    label = params['label']
    timeout = params['timeout'] or 60
    validate_parameters(params)
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    changed = False
    vios_property = None
    warn_msg = None

    if timeout < 10:
        module.fail_json(msg="timeout should be more than 10mins")
    try:
        image = hmc.listViosImages()
        logger.debug(image)
        if image is None:
            module.exit_json(changed=False, msg="There are no viosimages in the HMC")
        elif not any(entry['NAME'] == image_dir for entry in image):
            module.exit_json(changed=False, msg="The VIOS directory with name '{}' doesn't exist.".format(image_dir))
        else:
            if not any(vios_iso in entry['IMAGE_FILES'].split(',') for entry in image):
                module.exit_json(changed=False, msg=f"The '{vios_iso}' is not available in image_dir location.")
            elif vios_iso == 'flash.iso':
                module.exit_json(changed=False, msg="flash.iso cannot be copied.Please check if your iso file has been copied completely to the HMC.")
        if network_macaddr:
            hmc.installOSFromDisk(vios_iso, image_dir, vios_IP, vios_gateway, vios_subnetmask, network_macaddr, system_name, name, prof_name, label)
        else:
            dvcdictlt = hmc.fetchIODetailsForNetboot(hmc_host, vios_gateway, vios_IP, name, prof_name, system_name, vios_subnetmask)
            for dvcdict in dvcdictlt:
                if dvcdict['Ping Result'] == 'successful':
                    network_macaddr = dvcdict['MAC Address']
                    break
            if network_macaddr:
                hmc.installOSFromDisk(vios_iso, image_dir, vios_IP, vios_gateway, vios_subnetmask, network_macaddr, system_name, name, prof_name, label)
            else:
                module.fail_json(msg="Mac address not retrievable.")

        rmc_state, vios_property, ref_code = hmc.checkForOSToBootUpFully(system_name, name, timeout)
        if rmc_state:
            changed = True
            warn_msg = "VIOS installation has been successfull"
        elif ref_code in ['', '00']:
            changed = True
            warn_msg = "VIOS installation has been successfull but RMC didnt come up, please check the HMC firewall and security"
        else:
            module.fail_json(msg="VIOS Installation failed even after waiting for " + str(timeout) + " mins and the reference code is " + ref_code)

    except HmcError as install_error:
        return False, repr(install_error), None

    return changed, vios_property, warn_msg


def install(module, params):
    nim_IP = params['nim_IP']
    image_dir = params['image_dir']
    changed = False
    vios_property = None
    warn_msg = None

    if image_dir:
        changed, vios_property, warn_msg = installViosUsingDisk(module, params)

    elif nim_IP:
        changed, vios_property, warn_msg = installViosUsingNim(module, params)

    else:
        raise ParameterError("Provide either nim_IP or image_dir to perform vios installation")

    return changed, vios_property, warn_msg


def viosLicenseAccept(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    name = params['name']
    validate_parameters(params)
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    changed = False
    try:
        vios_config = hmc.getPartitionConfig(system_name, name)
        if vios_config['rmc_state'] == 'active':
            hmc.runCommandOnVIOS(system_name, name, 'license -accept')
            changed = True
        else:
            module.fail_json(msg="Cannot accept the license since the RMC state is " + vios_config['rmc_state'])
    except HmcError as error:
        return False, repr(error), None

    return changed, None, None


def list_all_vios_image(module, params, changed=False):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    validate_parameters(params)
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    try:
        vios_image_details = hmc.listViosImages()
        if vios_image_details is None:
            vios_image_details = "No directory names were found."
        module.exit_json(changed=changed, msg=vios_image_details)
    except Exception as e:
        module.fail_json(msg=str(e))


def copy_vios_image(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    validate_parameters(params)
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    try:
        directory_name = params['directory_name']
        image = hmc.listViosImages(directory_name=directory_name)
        if image:
            module.exit_json(changed=False, msg=f"The VIOS directory with name '{directory_name}' already exists.")
        else:
            if len(params['files']) > 2:
                raise ParameterError("Maximum 2 files can be copied to HMC")
            for item in params['files']:
                if not item.lower().endswith('.iso'):
                    raise ParameterError("Only ISO files can be copied to HMC")
            hmc.copyViosImage(params)
            image = hmc.listViosImages(directory_name=directory_name)
            if image:
                module.exit_json(changed=True, msg=f"The VIOS directory with name '{directory_name}' has been copied successfully.")
            else:
                module.exit_json(changed=False, msg=f"The VIOS directory with name '{directory_name}' has Not been copied successfully.")
    except Exception as e:
        module.fail_json(msg=str(e))


def delete_vios_image(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    directory_list = params['directory_list']
    validate_parameters(params)
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    try:
        changed_status = hmc.deleteViosImage(directory_list)
        list_all_vios_image(module, params, changed=changed_status)
    except Exception as e:
        logger.debug('entered the exception block')
        return False, repr(e), None


def perform_task(module):
    params = module.params
    actions = {
        "facts": fetchViosInfo,
        "present": createVios,
        "install": install,
        "accept_license": viosLicenseAccept,
        "listimages": list_all_vios_image,
        "copy": copy_vios_image,
        "delete": delete_vios_image
    }
    oper = 'action'
    if params['action'] is None:
        oper = 'state'
    try:
        return actions[params[oper]](module, params)
    except Exception as error:
        return False, repr(error), None


def run_module():

    # define available arguments/parameters a user can pass to the module
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
        sftp_auth=dict(type='dict',
                       no_log=True,
                       options=dict(
                           sftp_username=dict(type='str'),
                           sftp_password=dict(type='str', no_log=True),
                       )
                       ),
        remote_server=dict(type='str'),
        directory_name=dict(type='str'),
        directory_list=dict(type='list', elements='str'),
        system_name=dict(type='str'),
        name=dict(type='str'),
        media=dict(type='str', choices=['nfs', 'sftp']),
        remote_directory=dict(type='str'),
        mount_location=dict(type='str'),
        ssh_key_file=dict(type='str'),
        options=dict(type='str', choices=['3', '4']),
        files=dict(type='list', elements='str'),
        settings=dict(type='dict'),
        nim_IP=dict(type='str'),
        vios_gateway=dict(type='str'),
        nim_gateway=dict(type='str'),
        vios_IP=dict(type='str'),
        prof_name=dict(type='str'),
        location_code=dict(type='str'),
        vios_subnetmask=dict(type='str'),
        nim_subnetmask=dict(type='str'),
        nim_vlan_id=dict(type='str'),
        nim_vlan_priority=dict(type='str'),
        timeout=dict(type='int'),
        virtual_optical_media=dict(type='bool'),
        free_pvs=dict(type='bool'),
        vios_iso=dict(type='str'),
        image_dir=dict(type='str'),
        network_macaddr=dict(type='str'),
        label=dict(type='str'),
        state=dict(type='str', choices=['facts', 'present', 'listimages']),
        action=dict(type='str', choices=['install', 'accept_license', 'copy', 'delete']),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=[('state', 'action')],
        required_one_of=[('state', 'action')],
        required_if=[['state', 'facts', ['hmc_host', 'hmc_auth', 'system_name', 'name']],
                     ['state', 'present', ['hmc_host', 'hmc_auth', 'system_name', 'name']],
                     ['action', 'accept_license', ['hmc_host', 'hmc_auth', 'system_name', 'name']],
                     ['action', 'install', ['hmc_host', 'hmc_auth', 'vios_IP', 'system_name', 'name']],
                     ['state', 'listimages', ['hmc_host', 'hmc_auth']],
                     ['action', 'copy', ['hmc_host', 'hmc_auth', 'remote_server', 'directory_name']],
                     ['action', 'delete', ['hmc_host', 'hmc_auth', 'directory_list']],
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
        result['vios_info'] = info

    if warning:
        result['warning'] = warning

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
