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
module: hmc_update_upgrade
author:
    - Anil Vijayan (@AnilVijayan)
    - Navinakumar Kandakur (@nkandak1)
short_description: Manages the update and upgrade of the HMC
notes:
    - Upgrade with I(location_type=disk) will not support for V8 R870 and V9 R1 M910 release of the HMC
    - Update with I(location_type=disk) and I(build_file) in the HMC local path won't remove the file after update.
    - Module will not satisfy the idempotency requirement of Ansible, even though it partially confirms it.
      For instance, if the module is tasked to update/upgrade the HMC to the same level, it will still
      go ahead with the operation and finally the changed state will be reported as false.
    - All Operations support passwordless authentication.
    - By default, the HMC update/upgrade completion status is verified using Ping. To check the status via SSH,
      playbook must be executed in passwordless authentication mode.
description:
    - Updates the HMC by installing a corrective service package located on an FTP/SFTP/NFS server/Ansible Controller Node/HMC hard disk.
    - Upgrades the HMC by obtaining  the required  files  from a remote server or from the HMC hard disk. The files are transferred
      onto a special partition on the HMC hard disk. After the files have been transferred, HMC will boot from this partition
      and perform the upgrade.
    - Update/Upgrade the HMC from IBM Fix Central website
version_added: 1.0.0
requirements:
- Python >= 3.9
options:
    hmc_host:
        description:
            - The IP address or hostname of the HMC.
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
    build_config:
        description:
            - Configuration parameters required for the HMC update/upgrade.
        type: dict
        suboptions:
            location_type:
                description:
                    - The type of location that contains the corrective service ISO image. Valid values are
                    - C(disk) for the HMC hard disk
                    - C(ftp) for an FTP site
                    - C(sftp) for a secure FTP (SFTP) site
                    - C(nfs) for an NFS file system and
                    - C(ibmwebsite) for an IBM fixcentral website
                    - When the location type is set to C(disk), first it looks for the C(build_file) in HMC hard disk
                      if it doesn't exist then it looks for C(build_file) in the Ansible Controller node.
                    - C(ibmwebsite) location type supports update operation from V10 R2 M1030 release onwards and upgrade
                      operation from V10 R3 M1060 release onwards.
                type: str
                required: true
                choices: ['disk', 'ftp', 'sftp', 'nfs', 'ibmwebsite']
            hostname:
                description:
                    - The hostname or IPaddress of the remote server where the corrective
                      service ISO image is located.
                type: str
            userid:
                description:
                    - The user ID to use to log in to the remote FTP or SFTP server.
                      This option is required when the ISO image is located on a remote FTP or SFTP server.
                      Otherwise, this option is not valid.
                type: str
            passwd:
                description:
                    - The password to use to log in to the remote FTP or SFTP server.
                    - The I(passwd) and I(sshkey) options are mutually exclusive in case if I(location_type=sftp).
                    - This option is only valid when the ISO image is located on a remote FTP or SFTP server.
                type: str
            sshkey_file:
                description:
                    - The name of the file that contains the SSH private key.
                    - This option is only valid if I(location_type=sftp).
                type: str
            mount_location:
                description:
                    - The mount location defined on the NFS server where the corrective service
                      ISO image is located. This option is valid only if I(location_type=nfs).
                type: str
            build_file:
                description:
                    - The name of the corrective service ISO image file.
                    - This  option  is required when the ISO image is located on any of the following locations HMC hard disk,
                    - Ansible controller node filesystem, remote FTP, SFTP, or NFS server.
                    - During upgrade of the HMC, this option represents the host path where the network install
                      image is kept.
                    - During update of the HMC if I(location_type=disk) and ISO image is kept in Ansible controller node or HMC hard disk,
                      this option should be provided with the ansible control node path in which ISO file or network install image is kept.
                    - If the path specified contains the ISO file name then that specified ISO file will be considered for the update.
                    - If the path specified does not contain the ISO file name then the specified folder will be searched for ISO files,
                      sorted in alphabetical order and the 1st ISO will be considered for the update.
                type: str
            ptf:
                description:
                    - The name of the PTF to install.
                    - This option is required when the ISO image is located on the IBM Fix Central website. Otherwise, this option is not valid.
                    - This option is required only when the location_type is 'ibmwebsite'.
                    - This option is available for HMC versions from V10 R2 M1030 onwards for update and V10 R3 M1060 onwards for upgrade.
                type: str
    state:
        description:
            - The desired build state of the target HMC.
            - C(facts) does not change anything on the HMC and returns current driver/build level of HMC.
            - C(updated) ensures the target HMC is updated with given corrective service ISO image.
            - C(upgraded) ensures the target HMC is upgraded with given upgrade files.
        type: str
        choices: ['facts', 'updated', 'upgraded']
    action:
        description:
            - C(listptf) lists available Hardware Management Console (HMC) updates from the IBM Fix Central website.
            - This option is available for HMC versions from V10 R2 M1030 onwards
            - C(listupg) lists available Hardware Management Console (HMC) upgrades from the IBM Fix Central website.
            - This option is available for HMC versions from V10 R3 M1060 onwards
        type: str
        choices: ['listptf', 'listupg']
'''

EXAMPLES = '''
- name: List the Power HMC current build level
  hmc_update_upgrade:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth:
          username: '{{ ansible_user }}'
          password: '{{ hmc_password }}'
      state: facts

- name: Update the Power HMC to the V10R2M1040 build level from nfs location
  hmc_update_upgrade:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth:
          username: '{{ ansible_user }}'
          password: '{{ hmc_password }}'
      build_config:
          location_type: nfs
          hostname: <NFS_Server_IP/Hostname>
          build_file: /Images/MF70893-10.2.1040.0-2304262325-x86_64.iso
          mount_location: /HMCImages
      state: updated

- name: Update the Power HMC to the V10R2M1041 build level from sftp location
  hmc_update_upgrade:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth:
          username: '{{ ansible_user }}'
          password: '{{ hmc_password }}'
      build_config:
          location_type: sftp
          hostname: <SFTP_Server_IP/Hostname>
          userid: <SFTP_Server_Username>
          passwd: <SFTP_Server_Password>
          build_file: /Images/MF71190-10.2.1041.0-2308160028-x86_64.iso
      state: updated

- name: List all the available ptfs for update
  hmc_update_upgrade:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth:
          username: '{{ ansible_user }}'
          password: '{{ hmc_password }}'
      action: listptf

- name: Update the Power HMC to the V10R2M1041(ifix) build level from ibmwebsite
  hmc_update_upgrade:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth:
          username: '{{ ansible_user }}'
          password: '{{ hmc_password }}'
      build_config:
          location_type: ibmwebsite
          ptf: vMF71409
      state: updated

- name: Upgrade Power HMC to the mentioned PTF level using the image obtained from ibmwebsite
  ibm.power_hmc.hmc_update_upgrade:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth: '{{ curr_hmc_auth }}'
      build_config:
          location_type: ibmwebsite
          ptf: <ptf>
      state: upgraded

- name: Upgrade the Power HMC using NFS server
  ibm.power_hmc.hmc_update_upgrade:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth: '{{ curr_hmc_auth }}'
      build_config:
          location_type: nfs
          hostname: <hostname>
          mount_location: /HMCImages
          build_file: <build_file_path>
      state: upgraded

- name: Upgrade the Power HMC using SFTP server
  ibm.power_hmc.hmc_update_upgrade:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth: '{{ curr_hmc_auth }}'
      build_config:
          location_type: sftp
          hostname: <SFTP_Server_IP/Hostname>
          userid: <SFTP_Server_Username>
          passwd: <SFTP_Server_Password>
          build_file: <build_file>
      state: upgraded

- name: Provide a list of all available image files in ibmwebsite for upgrading Power HMC
  hmc_update_upgrade:
      hmc_host: '{{ inventory_hostname }}'
      hmc_auth:
          username: '{{ ansible_user }}'
          password: '{{ hmc_password }}'
      action: listupg
'''

RETURN = '''
build_info:
    description: Respective build information
    type: dict
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_resource import Hmc
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import Error
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import VersionError
import sys
import logging
import os
LOG_FILENAME = "/tmp/ansible_power_hmc_{0}.log".format(os.getpid())
logger = logging.getLogger(__name__)

HMC_REBOOT_TIMEOUT = 60


def init_logger():
    old_umask = os.umask(0o177)
    try:
        logging.basicConfig(
            filename=LOG_FILENAME,
            format='[%(asctime)s] %(levelname)s: [%(funcName)s] %(message)s',
            level=logging.DEBUG)
    finally:
        os.umask(old_umask)


def compare_version(initial_version_details, version_details):
    if initial_version_details == version_details:
        return False
    else:
        return True


def command_option_checker(config):
    """
    Checks that the input parameters satisfy the mutual exclusiveness of HMC
    """
    if config['location_type'] in ['ftp', 'sftp']:
        mandatoryList = ['hostname', 'build_file', 'userid', 'passwd']
        unsupportedList = ['mount_location', 'ptf']

        if config['location_type'] == 'sftp':
            if not (config['sshkey_file'] or config['passwd']):
                raise ParameterError("mandatory parameter 'passwd' or 'sshkey_file' is missing")
            elif config['sshkey_file'] and config['passwd']:
                raise ParameterError("conflicting parameters 'passwd' and 'sshkey_file'. Provide any one")

            if config['sshkey_file']:
                mandatoryList.remove('passwd')
        else:
            unsupportedList.append('sshkey_file')

    elif config['location_type'] == 'nfs':
        mandatoryList = ['hostname', 'build_file', 'mount_location']
        unsupportedList = ['userid', 'passwd', 'sshkey_file', 'ptf']
    elif config['location_type'] == 'disk':
        mandatoryList = ['build_file']
        unsupportedList = ['userid', 'passwd', 'sshkey_file', 'hostname', 'mount_location', 'ptf']
    elif config['location_type'] in ['usb', 'dvd']:
        raise ParameterError("not supporting the option '%s'" % (config['location_type']))
    elif config['location_type'] == 'ibmwebsite':
        mandatoryList = ['ptf']
        unsupportedList = ['userid', 'passwd', 'sshkey_file', 'hostname', 'mount_location', 'build_file']
    else:
        raise ParameterError("not supporting the location_type option: '%s'" % (config['location_type']))

    collate = []
    for eachMandatory in mandatoryList:
        if not config[eachMandatory]:
            collate.append(eachMandatory)
    if collate:
        if len(collate) == 1:
            raise ParameterError("mandatory parameter '%s' is missing" % (collate[0]))
        else:
            raise ParameterError("mandatory parameters '%s' are missing" % (','.join(collate)))

    collate = []
    for eachUnsupported in unsupportedList:
        if config[eachUnsupported]:
            collate.append(eachUnsupported)

    if collate:
        if len(collate) == 1:
            raise ParameterError("unsupported parameter: %s" % (collate[0]))
        else:
            raise ParameterError("unsupported parameters: %s" % (', '.join(collate)))


def remove_image_from_hmc(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    list_on_hmc = 'sshpass -p {0} ssh {1}@{2} ls network_install'.format(password, hmc_user, hmc_host)
    rc, out, err = module.run_command(list_on_hmc)
    if rc == 0:
        rm_install_path = 'sshpass -p {0} ssh {1}@{2} rm -rf network_install'.format(password, hmc_user, hmc_host)
        rc1, out1, err1 = module.run_command(rm_install_path)
        if rc1 != 0:
            logger.debug("Removal of 'network_install' directory failed")


def check_image_in_hmc(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    local_path = params['build_config']['build_file']

    # Check file exist on HMC
    list_on_hmc = 'sshpass -p {0} ssh {1}@{2} ls {3}'.format(password, hmc_user, hmc_host, local_path)
    logger.debug(list_on_hmc)
    rc, out, err = module.run_command(list_on_hmc)
    logger.debug(rc)
    if rc == 0:
        return True
    else:
        return False


def image_copy_from_local_to_hmc(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    local_path = params['build_config']['build_file']
    iso_name = ""
    iso_count = 0

    if '.iso' in local_path:
        local_path = local_path[:local_path.rfind("/")]
        iso_name = params['build_config']['build_file'].split("/")[-1]

    if params['state'] == 'upgraded':
        imageFilesUpg = ['base.img', 'disk1.img', 'hmcnetworkfiles.sum', 'img2a', 'img3a']
        list_cmd = "ls " + local_path
        rc, out, err = module.run_command(list_cmd)
        if rc == 0:
            logger.debug(out)
            if not all(True if each in out else False for each in imageFilesUpg):
                raise ParameterError("local path mentioned does not contain valid network files")
        else:
            logger.debug(err)
            raise ParameterError("not able to list files on mentioned local path")

    if params['state'] == 'updated':
        list_cmd = "ls " + local_path
        rc, out, err = module.run_command(list_cmd)
        if rc == 0:
            files = out.split()
            if params['state'] == 'updated' and iso_name == "":
                iso_count = sum(file.endswith(".iso") for file in files)
            if iso_count > 1:
                raise Error("There are multiple iso files in specified folder. Please specify the iso file also in build_file")
        else:
            logger.debug(err)
            raise ParameterError("not able to list files on mentioned local path")

    mkdir_cmd = 'sshpass -p {0} ssh {1}@{2} mkdir -p network_install'.format(password, hmc_user, hmc_host)
    rc1, out1, err1 = module.run_command(mkdir_cmd)
    if rc1 == 1:
        logger.debug(err1)
        raise Error("creation of temporary install directory inside HMC failed")

    scp_cmd = 'sshpass -p {0} scp -r {1}/* {2}@{3}:/home/{2}/network_install'.format(password, local_path, hmc_user, hmc_host)
    if params['state'] == 'updated' and iso_name != "":
        scp_cmd = 'sshpass -p {0} scp  {1}/{2} {3}@{4}:/home/{3}/network_install'.format(password, local_path, iso_name, hmc_user, hmc_host)
    rc2, out2, err2 = module.run_command(scp_cmd, use_unsafe_shell=True)
    if rc2 == 1:
        logger.debug(err2)
        remove_image_from_hmc(module, params)
        raise Error("copy of image to hmc failed")

    list_on_hmc = 'sshpass -p {0} ssh {1}@{2} ls network_install/'.format(password, hmc_user, hmc_host)
    rc3, out3, err3 = module.run_command(list_on_hmc)
    if rc3 == 0:
        if params['state'] == 'upgraded':
            if not all(True if each in out3 else False for each in imageFilesUpg):
                remove_image_from_hmc(module, params)
                raise Error("copy of image to hmc is incomplete. Necessary files are missing")
        elif params['state'] == 'updated':
            return out3
        else:
            iso_file = None
            for fl in files:
                if '.iso' in fl:
                    iso_file = fl
                    return iso_file
            if not iso_file:
                remove_image_from_hmc(module, params)
                raise Error("copy of image to hmc is incomplete. Necessary files are missing")
    else:
        logger.debug(err3)
        module.warn("could not confirm the copy of necessary image files")


def facts(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    changed = False
    hmc_conn = None

    if params['build_config']:
        raise ParameterError("not supporting build_config option")

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    version_details = hmc.listHMCVersion()
    return changed, version_details, None


def list_ptf(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    changed = False
    hmc_conn = None
    ptf_details = None

    if params['build_config']:
        raise ParameterError("not supporting build_config option")

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    initial_version_details = hmc.listHMCVersion()

    if int(initial_version_details["SERVICEPACK"]) < 1030:
        raise VersionError("List ptf is supported from V10 R2 M1030 version onwards.")
    else:
        ptf_details = hmc.listHMCPTF('ibmwebsite')
    if 'No PTFs are available' in ptf_details:
        return False, {"info": ptf_details}, None
    return changed, ptf_details, None


def list_upgrade_files(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    changed = False
    hmc_conn = None
    ptf_details = None

    if params['build_config']:
        raise ParameterError("not supporting build_config option")

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    initial_version_details = hmc.listHMCVersion()

    if int(initial_version_details["SERVICEPACK"]) < 1060:
        raise VersionError("List upgrade ptf is supported from V10 R3 M1060 version onwards.")
    else:
        ptf_details = hmc.listUpgradeFiles('ibmwebsite')
    if 'No upgrade files available' in ptf_details:
        return False, {"info": ptf_details}, None
    return changed, ptf_details, None


def upgrade_hmc(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    changed = False
    hmc_conn = None
    warning_msg = None
    isBootedUp = False
    is_img_in_hmc = False

    if not params['build_config']:
        raise ParameterError("missing options on build_config")

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    command_option_checker(params['build_config'])

    locationType = params['build_config']['location_type']

    if locationType == 'disk':
        is_img_in_hmc = check_image_in_hmc(module, params)
        if not is_img_in_hmc:
            image_copy_from_local_to_hmc(module, params)

    otherConfig = {}
    if params['build_config']['userid']:
        otherConfig['-U'] = params['build_config']['userid']
    if params['build_config']['passwd']:
        otherConfig['--PASSWD'] = params['build_config']['passwd']
    if params['build_config']['sshkey_file']:
        otherConfig['-K'] = params['build_config']['sshkey_file']
    if params['build_config']['mount_location']:
        otherConfig['-L'] = params['build_config']['mount_location']
    if params['build_config']['hostname']:
        otherConfig['-H'] = params['build_config']['hostname']
    if params['build_config']['build_file']:
        if locationType == 'disk' and not is_img_in_hmc:
            otherConfig['-D'] = '/home/{0}/network_install'.format(hmc_user)
        elif locationType == 'disk' and is_img_in_hmc:
            otherConfig['-D'] = params['build_config']['build_file']
            imageFilesUpg = ['base.img', 'disk1.img', 'hmcnetworkfiles.sum', 'img2a', 'img3a']
            list_cmd = "sshpass -p {0} ssh {1}@{2} ls {3}".format(password, hmc_user, hmc_host, params['build_config']['build_file'])
            logger.debug(list_cmd)
            rc, out, err = module.run_command(list_cmd)
            if rc == 0:
                logger.debug(out)
                if not all(True if each in out else False for each in imageFilesUpg):
                    raise ParameterError("local path mentioned does not contain valid network files")
            else:
                logger.debug(err)
                raise ParameterError("not able to list files on mentioned local path")
        else:
            otherConfig['-D'] = params['build_config']['build_file']

    initial_version_details = hmc.listHMCVersion()

    if locationType == 'ibmwebsite':
        if int(initial_version_details["SERVICEPACK"]) >= 1060:
            otherConfig['--PTF'] = params['build_config']['ptf']
        else:
            raise VersionError("Upgrade through ibmwebsite supported from V10 R3 M1060 version onwards.")

    hmc.getHMCUpgradeFiles(locationType, configDict=otherConfig)

    hmc.saveUpgrade('disk')

    hmc.configAltDisk(True, 'upgrade')

    hmc.hmcShutdown(reboot=True)

    version_details = {}
    if hmc.checkHmcUpandRunning(timeoutInMin=HMC_REBOOT_TIMEOUT):
        isBootedUp, version_details = Hmc.checkIfHMCFullyBootedUp(module, hmc_host, hmc_user, password)
        if not isBootedUp:
            version_details = "FAILED: HMC not booted up"
        else:
            changed = compare_version(initial_version_details, version_details)
    else:
        version_details = "FAILED: Hmc not responding after reboot"

    if not changed and locationType == 'disk':
        if not is_img_in_hmc:
            remove_image_from_hmc(module, params)

    if isBootedUp and not changed:
        warning_msg = "WARNING: HMC upgrade completed, but the version remains same. "\
                      "Check if any MPTF missing or the HMC was at same level already."

    return changed, version_details, warning_msg


def update_hmc(module, params):
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    changed = False
    warning_msg = None
    isBootedUp = False
    is_img_in_hmc = False
    iso_file = None
    if not params['build_config']:
        raise ParameterError("missing options on build_config")

    hmc_conn = None
    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    command_option_checker(params['build_config'])

    locationType = params['build_config']['location_type']

    if locationType == 'disk':
        if '.iso' in params['build_config']['build_file']:
            iso_file = params['build_config']['build_file'].split("/")[-1]
            is_img_in_hmc = check_image_in_hmc(module, params)
            if not is_img_in_hmc:
                iso_file = image_copy_from_local_to_hmc(module, params)
        else:
            is_img_in_hmc = check_image_in_hmc(module, params)
            if not is_img_in_hmc:
                iso_file = image_copy_from_local_to_hmc(module, params)
            else:
                hmc_ls_cmd = "sshpass -p {0} ssh {1}@{2} ls {3}".format(password, hmc_user, hmc_host, params['build_config']['build_file'])
                rc, out, err = module.run_command(hmc_ls_cmd)
                if rc == 0:
                    files = out.split()
                    iso_count = sum(file.endswith(".iso") for file in files)
                    if iso_count > 1:
                        raise Error("There are multiple iso files in specified folder. Please specify the iso file also in build_file")
                    else:
                        for fl in files:
                            if '.iso' in fl:
                                iso_file = fl
                                break
                        if not iso_file:
                            raise Error("Necessary files are missing in hmc")
                else:
                    logger.debug(err)
                    raise Error("could not confirm the necessary image files in hmc")

    otherConfig = {}
    if params['build_config']['hostname']:
        otherConfig['-H'] = params['build_config']['hostname']
    if params['build_config']['userid']:
        otherConfig['-U'] = params['build_config']['userid']
    if params['build_config']['passwd']:
        otherConfig['--PASSWD'] = params['build_config']['passwd']
    if params['build_config']['sshkey_file']:
        otherConfig['-K'] = params['build_config']['sshkey_file']
    if params['build_config']['mount_location']:
        otherConfig['-L'] = params['build_config']['mount_location']
    if params['build_config']['build_file']:
        otherConfig['-F'] = params['build_config']['build_file']

    # In case user opt for disk install, then image will be cleared from
    # local location once installed
    if locationType == 'disk':
        if not is_img_in_hmc:
            otherConfig['-C'] = ""
            otherConfig['-F'] = '/home/{0}/network_install/{1}'.format(hmc_user, iso_file).strip()
        elif '.iso' in params['build_config']['build_file']:
            otherConfig['-F'] = '/{0}'.format(params['build_config']['build_file']).strip()
        else:
            otherConfig['-F'] = '/{0}/{1}'.format(params['build_config']['build_file'], iso_file).strip()

    initial_version_details = hmc.listHMCVersion()

    # In case of ibmwebsite, provide the ptf number
    if locationType == 'ibmwebsite':
        if int(initial_version_details["SERVICEPACK"]) >= 1030:
            otherConfig['--PTF'] = params['build_config']['ptf']
        else:
            raise VersionError("Update through ibmwebsite supported from V10 R2 M1030 version onwards.")

    # this option to restart hmc after configuration
    otherConfig['-R'] = " "

    hmc.updateHMC(locationType, configDict=otherConfig)
    version_details = {}

    if not is_img_in_hmc:
        remove_image_from_hmc(module, params)

    if hmc.checkHmcUpandRunning(timeoutInMin=HMC_REBOOT_TIMEOUT):
        isBootedUp, version_details = Hmc.checkIfHMCFullyBootedUp(module, hmc_host, hmc_user, password)
        if not isBootedUp:
            version_details = "FAILED: HMC not booted up"
    else:
        version_details = "FAILED: Hmc not responding after reboot"

    if isBootedUp:
        changed = compare_version(initial_version_details, version_details)
        if not changed:
            warning_msg = "WARNING: HMC update completed, but the version "\
                          "remains same. Check if any MPTF missing or the HMC was at same level already."

    return changed, version_details, warning_msg


def perform_task(module):

    params = module.params
    actions = {
        "updated": update_hmc,
        "facts": facts,
        "upgraded": upgrade_hmc,
        "listptf": list_ptf,
        "listupg": list_upgrade_files
    }

    oper = 'state'
    if params['state'] is None:
        oper = 'action'
    try:
        return actions[params[oper]](module, params)
    except (ParameterError, HmcError, Error) as error:
        return False, repr(error), None

    if not params['hmc_auth']:
        return False, "missing credential info", None

    try:
        return actions[params['state']](module, params)
    except HmcError as error:
        if params['state'] != 'facts' and params['build_config']['location_type'] == 'disk':
            remove_image_from_hmc(module, params)
        return False, repr(error), None
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
        build_config=dict(type='dict',
                          options=dict(
                              location_type=dict(required=True, type='str', choices=['disk', 'ftp', 'sftp', 'nfs', 'ibmwebsite']),
                              hostname=dict(type='str'),
                              userid=dict(type='str'),
                              passwd=dict(type='str', no_log=True),
                              sshkey_file=dict(type='str'),
                              mount_location=dict(type='str'),
                              build_file=dict(type='str'),
                              ptf=dict(type='str')
                          )
                          ),
        state=dict(type='str', choices=['updated', 'upgraded', 'facts']),
        action=dict(type='str', choices=['listptf', 'listupg'])
    )

    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=[('state', 'action')],
        required_one_of=[('state', 'action')],
        required_if=[['state', 'facts', ['hmc_host', 'hmc_auth']],
                     ['state', 'updated', ['hmc_host', 'hmc_auth', 'build_config']],
                     ['state', 'upgraded', ['hmc_host', 'hmc_auth', 'build_config']],
                     ['action', 'listptf', ['hmc_host', 'hmc_auth']],
                     ['action', 'listupg', ['hmc_host', 'hmc_auth']],
                     ]
    )

    if module._verbosity >= 5:
        init_logger()

    if sys.version_info < (3, 0):
        py_ver = sys.version_info[0]
        module.fail_json(msg="Unsupported Python version {0}, supported python version is 3 and above".format(py_ver))

    changed, build_info, warning = perform_task(module)

    if isinstance(build_info, str):
        module.fail_json(msg=build_info)

    result = {}
    result['changed'] = changed
    result['build_info'] = build_info
    if warning:
        result['warning'] = warning

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
