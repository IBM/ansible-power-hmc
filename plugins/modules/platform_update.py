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
module: platform_update
author:
    - Chiranthan M V (@chiranthanmv)
short_description: Applies consolidated system firmware (update/upgrade), VIOS, SR-IOV, and I/O adapter updates, including optional partition migration
notes:
  - Supports IBM Fix Central website (C(IBMWebsite)) and SFTP server (C(sftp)) as update/upgrade sources.
  - For SFTP-based updates, the firmware or VIOS image must already be present on the SFTP server.
    The HMC connects to the SFTP server directly; no pre-staging to the HMC is required.
  - Supports defining the order in which updates and upgrades are applied across components.
  - To perform configuration operations, you do not need to specify a separate state or action.
    Supplying values under C(platform_config) is sufficient to apply the changes directly to the HMC.
  - When performing an update or upgrade operation via C(IBMWebsite) with C(level='latest'),
    if the Ansible response status is C(ok) and C(changed) is C(False), and the result is C(COMPLETED_WITH_ERROR) with the reason C("update not available"),
    it indicates that no newer update images are available or the target is already up-to-date.
  - This module will not satisfy the idempotency requirement of Ansible, even though it partially confirms it.
    For instance, if the module is tasked to update/upgrade the HMC to the same level, it will still
    go ahead with the operation and finally the changed state will be reported as false.
  - Upgrade the Power server after successfully evacuating the partition to the destination system,
    and ensure the partition is not returned to the original server.
description:
    - This module performs update and upgrade for various system components as part of system maintenance or automation workflows.
    - Supports System Firmware update and upgrade.
    - Supports VIOS and I/O Adapters update.
    - Supports SR-IOV Adapters update based on supported system firmware levels.
    - Supports Logical Partition migration.
    - All updates and upgrades can be performed independently or combined in a single consolidated update operation.
    - Supports C(state=facts) to retrieve information about available adapters without making any changes.
version_added: 1.0.0
requirements:
- Python >= 3.9
options:
    hmc_host:
        description:
            - IP address or hostname of the target Hardware Management Console (HMC).
        required: true
        type: str
    hmc_auth:
        description:
            - Authentication credentials to connect to the HMC.
        required: true
        type: dict
        suboptions:
            username:
                description:
                    - Username for logging into the HMC.
                required: true
                type: str
            password:
                description:
                    - Password for the HMC user.
                type: str
    system_name:
        description:
            - The name or MTMS (machine type model serial) of the managed system on which the operations are to be performed.
        required: true
        type: str
    platform_config:
        description:
            - Defines the configuration for the operation to be performed, such as system firmware update/upgrade
              (including SR-IOV adapter updates) or VIOS updates (including I/O adapter updates).
            - Also supports performing partition migrations.
        type: dict
        suboptions:
            system_firmware_update:
                description:
                    - System firmware update/upgrade configuration.
                type: dict
                suboptions:
                    update_type:
                        description:
                            - Type of firmware update/upgrade operation.
                            - 'C(NoUpdate): System firmware update/upgrade is skipped, but SR-IOV adapter updates are still allowed.'
                            - 'C(Update): Applies an update.'
                            - 'C(Upgrade): Applies an upgrade.'
                            - When set to C(Update) or C(Upgrade), the C(sriov_adapter_update) will be implicit.
                            - When set to C(NoUpdate), the fields C(repository) and C(level) are not required.
                        type: str
                        choices: ['NoUpdate', 'Update', 'Upgrade']
                    update_order:
                        description:
                            - Priority order in which the update/upgrade should be applied.
                        type: int
                    repository:
                        description:
                            - Specifies the source repository for the update image.
                            - C(IBMWebsite) uses IBM Fix Central as the source.
                            - C(sftp) uses an SFTP server as the source; requires the C(sftp) block.
                            - If not specified, it defaults to C(IBMWebsite).
                        type: str
                        choices: ['IBMWebsite', 'sftp']
                        default: 'IBMWebsite'
                    level:
                        description:
                            - Specifies the firmware version level to apply.
                            - If not provided, the latest available version will be used by default.
                            - Not applicable when C(repository=sftp).
                        type: str
                        default: 'latest'
                    sftp:
                        description:
                            - SFTP connection and authentication details.
                            - Required when C(repository=sftp).
                        type: dict
                        suboptions:
                            hostname:
                                description:
                                    - Hostname or IP address of the SFTP server.
                                    - Required when C(repository=sftp).
                                type: str
                            directory:
                                description:
                                    - Directory on the SFTP server containing the firmware image.
                                    - Required when C(repository=sftp).
                                type: str
                            username:
                                description:
                                    - Username for SFTP authentication.
                                    - Required when C(repository=sftp).
                                type: str
                            password:
                                description:
                                    - Password for SFTP authentication.
                                    - Required unless C(keyfile) is provided.
                                type: str
                            keyfile:
                                description:
                                    - Path to an SSH private key file.
                                    - Mutually exclusive with C(password).
                                type: str
                    sriov_adapter_update:
                        description:
                            - List of SR-IOV adapter update configurations.
                            - This option must not be provided if C(update_type) is set to C(Update) or C(Upgrade) in C(system_firmware_update).
                        type: list
                        elements: dict
                        suboptions:
                            all:
                                description:
                                    - Indicates whether the update should be applied to all adapters.
                                    - If set to C(True), the C(adapter_id) field is not required.
                                type: bool
                            adapter_id:
                                description:
                                    - ID of the specific adapter to be updated.
                                    - Required only when C(all) is not specified.
                                type: int
                            subtype:
                                description:
                                    - Specifies the level of update to apply.
                                    - C(DriverOnly) performs only the driver update.
                                    - C(Adapter) performs both the adapter firmware and driver updates.
                                type: str
                                choices: ['DriverOnly', 'Adapter']
            partition_migration:
                description:
                    - Configuration for migrating logical partitions.
                    - This option cannot be used alone.
                    - Must be specified along with either C(vios_update) or C(system_firmware_update).
                type: dict
                suboptions:
                    is_quick_evac:
                        description:
                            - Indicates whether to perform a quick evacuation during partition migration.
                            - Must always be set to C(True) when performing partition migration.
                        type: bool
                    destination_managed_system:
                        description:
                            - Name of the target managed system to migrate partitions to.
                        type: str
                    leave_partition_in_target:
                        description:
                            - Whether to keep the partition in the target after platform update.
                            - If not specified, the default is C(False).
                        type: bool
                        default: False
            vios_update:
                description:
                    - Configuration for updating Virtual I/O Servers.
                type: list
                elements: dict
                suboptions:
                    update_type:
                        description:
                            - Specifies the type of VIOS update to be performed.
                            - 'C(NoUpdate): No update will be applied to VIOS, but I/O adapter updates are still allowed.'
                            - 'C(Update): Applies a VIOS update using the provided configuration. The I/O adapter update is performed implicitly.'
                            - When set to C(NoUpdate), the fields C(resource_type) and C(vios_image_name) are not required.
                        type: str
                        choices: ['NoUpdate', 'Update']
                    vios_name:
                        description:
                            - Name of the VIOS partition to be updated.
                        type: str
                    update_order:
                        description:
                            - Priority order in which the update should be applied relative to other components.
                        type: int
                    resource_type:
                        description:
                            - Specifies the source repository for the update image.
                            - C(IBMWebsite) uses IBM Fix Central as the source.
                            - C(sftp) uses an SFTP server as the source; requires the C(sftp) block.
                            - If not specified, it defaults to C(IBMWebsite).
                        type: str
                        choices: ['IBMWebsite', 'sftp']
                        default: 'IBMWebsite'
                    vios_image_name:
                        description:
                            - Specifies the VIOS image name to apply.
                            - Required when C(update_type=Update) for both C(IBMWebsite) and C(sftp).
                        type: str
                    sftp:
                        description:
                            - SFTP connection and authentication details.
                            - Required when C(resource_type=sftp).
                        type: dict
                        suboptions:
                            hostname:
                                description:
                                    - Hostname or IP address of the SFTP server.
                                    - Required when C(resource_type=sftp).
                                type: str
                            username:
                                description:
                                    - Username for SFTP authentication.
                                    - Required when C(resource_type=sftp).
                                type: str
                            password:
                                description:
                                    - Password for SFTP authentication.
                                    - Required unless C(ssh_key) is provided.
                                type: str
                            ssh_key:
                                description:
                                    - Path to an SSH private key file used for SFTP authentication.
                                    - Mutually exclusive with C(password).
                                type: str
                            remote_directory:
                                description:
                                    - Directory on the SFTP server containing the VIOS image.
                                type: str
                            file_names:
                                description:
                                    - Specific files to download from the SFTP server.
                                    - Specified as a list; internally converted to a comma-separated string.
                                type: list
                                elements: str
                    io_adapter_update:
                        description: List of I/O adapters to update during VIOS update.
                        type: list
                        elements: dict
                        suboptions:
                            all:
                                description:
                                    - Indicates whether all I/O adapters should be updated.
                                    - If set to C(True), the C(device) field is not required.
                                type: bool
                            device:
                                description:
                                    - List of I/O adapter device names to be updated.
                                    - Specify one or more device names as a list (e.g., C(['ent0', 'ent1'])).
                                    - Required only when C(all) is not specified.
                                type: list
                                elements: str
                            repository:
                                description:
                                    - Specifies the source repository for the update image.
                                    - C(IBMWebsite) uses IBM Fix Central as the source.
                                    - C(sftp) uses an SFTP server as the source; requires the C(sftp) block.
                                    - If not specified, it defaults to C(IBMWebsite).
                                type: str
                                choices: ['IBMWebsite', 'sftp']
                                default: 'IBMWebsite'
                            sftp:
                                description:
                                    - SFTP connection and authentication details.
                                    - Required when C(repository=sftp).
                                type: dict
                                suboptions:
                                    hostname:
                                        description:
                                            - Hostname or IP address of the SFTP server.
                                            - Required when C(repository=sftp).
                                        type: str
                                    directory:
                                        description:
                                            - Directory on the SFTP server containing the adapter firmware.
                                            - Required when C(repository=sftp).
                                        type: str
                                    username:
                                        description:
                                            - Username for SFTP authentication.
                                            - Required when C(repository=sftp).
                                        type: str
                                    password:
                                        description:
                                            - Password for SFTP authentication.
                                            - Required unless C(keyfile) is provided.
                                        type: str
                                    keyfile:
                                        description:
                                            - Path to an SSH private key file.
                                            - Mutually exclusive with C(password).
                                        type: str
    state:
        description:
            - C(facts) gathers and returns information about available SR-IOV adapters, Virtual I/O Servers (VIOS), and I/O adapters without making any changes.
        type: str
        choices: ['facts']
'''

EXAMPLES = '''
- name: Update a SR-IOV adapters (DriverOnly) using IBM Fix Central
  platform_update:
    hmc_host: <host>
    hmc_auth:
      username: <hscroot>
      password: <hmcpass>
    system_name: <system_name>
    platform_config:
      system_firmware_update:
        update_type: NoUpdate
        update_order: 1
        sriov_adapter_update:
          - adapter_id: 1
            subtype: DriverOnly

- name: Update all SR-IOV adapters (Adapter) using IBM Fix Central (No Firmware Update)
  platform_update:
    hmc_host: <host>
    hmc_auth:
      username: <hscroot>
      password: <hmcpass>
    system_name: <system_name>
    platform_config:
      system_firmware_update:
        update_type: NoUpdate
        update_order: 1
        sriov_adapter_update:
          - all: true
            subtype: Adapter

- name: Perform a System Firmware update using default level
  platform_update:
    hmc_host: <host>
    hmc_auth:
      username: <hscroot>
      password: <hmcpass>
    system_name: <system_name>
    platform_config:
      system_firmware_update:
        update_type: Update
        update_order: 1

- name: Perform a System Firmware update using specified level (level 12)
  platform_update:
    hmc_host: <host>
    hmc_auth:
      username: <hscroot>
      password: <hmcpass>
    system_name: <system_name>
    platform_config:
      system_firmware_update:
        update_type: Update
        update_order: 1
        level: 12

- name: Migrate a partition to a different managed system and perform a System Firmware update
  platform_update:
    hmc_host: <host>
    hmc_auth:
      username: <hscroot>
      password: <hmcpass>
    system_name: <system_name>
    platform_config:
      system_firmware_update:
        update_type: Update
        update_order: 1
        repository: IBMWebsite
      partition_migration:
        is_quick_evac: true
        destination_managed_system: "p920_system"
        leave_partition_in_target: true

- name: Update VIOS to latest available level from IBM Fix Central
  platform_update:
    hmc_host: <host>
    hmc_auth:
      username: <hscroot>
      password: <hmcpass>
    system_name: <system_name>
    platform_config:
      vios_update:
        - update_type: Update
          vios_name: "vios1"
          vios_image_name: "name"
          update_order: 1
          resource_type: IBMWebsite

- name: Update selected I/O adapters only (no VIOS update)
  platform_update:
    hmc_host: <host>
    hmc_auth:
      username: <hscroot>
      password: <hmcpass>
    system_name: <system_name>
    platform_config:
      vios_update:
        - update_type: NoUpdate
          vios_name: <vios1>
          update_order: 1
          io_adapter_update:
            - device:
                - "ent0"
                - "ent1"
              repository: IBMWebsite

- name: Update VIOS to specific image and all I/O adapters from IBM Fix Central
  platform_update:
    hmc_host: <host>
    hmc_auth:
      username: <hscroot>
      password: <hmcpass>
    system_name: <system_name>
    platform_config:
      vios_update:
        - update_type: NoUpdate
          vios_name: <vios1>
          update_order: 1
          resource_type: IBMWebsite
          io_adapter_update:
            - all: true
              repository: IBMWebsite

- name: Update multiple VIOS instances from IBM Fix Central with ordered execution
  platform_update:
    hmc_host: <host>
    hmc_auth:
      username: <hscroot>
      password: <hmcpass>
    system_name: <system_name>
    platform_config:
      vios_update:
        - update_type: Update
          vios_name: <vios1>
          update_order: 1
          vios_image_name: "name"
          resource_type: IBMWebsite
        - update_type: Update
          vios_name: <vios2>
          update_order: 2
          vios_image_name: <name>
          resource_type: IBMWebsite

- name: Update System Firmware and VIOS with all I/O adapters from IBM Fix Central
  platform_update:
    hmc_host: <host>
    hmc_auth:
      username: <hscroot>
      password: <hmcpass>
    system_name: <system_name>
    platform_config:
      system_firmware_update:
        update_type: Update
        update_order: 1
        repository: IBMWebsite
      vios_update:
        - update_type: Update
          vios_name: <vios1>
          update_order: 1
          vios_image_name: "name"
          resource_type: IBMWebsite
          io_adapter_update:
            - all: true
              repository: IBMWebsite

- name: Perform a System Firmware update from an SFTP server using password authentication
  platform_update:
    hmc_host: <host>
    hmc_auth:
      username: <hscroot>
      password: <hmcpass>
    system_name: <system_name>
    platform_config:
      system_firmware_update:
        update_type: Update
        update_order: 1
        repository: sftp
        sftp:
          hostname: sftp.example.com
          directory: /firmware/images
          username: sftpuser
          password: sftppass

- name: Update VIOS from an SFTP server using SSH key authentication with specific files
  platform_update:
    hmc_host: <host>
    hmc_auth:
      username: <hscroot>
      password: <hmcpass>
    system_name: <system_name>
    platform_config:
      vios_update:
        - update_type: Update
          vios_name: vios1
          update_order: 1
          resource_type: sftp
          vios_image_name: vios_package_name
          sftp:
            hostname: sftp.example.com
            username: sftpuser
            ssh_key: /home/hscroot/.ssh/id_rsa
            remote_directory: /vios/images
            file_names:
              - vios_image.tar.gz

- name: Update I/O adapters from an SFTP server using SSH key authentication
  platform_update:
    hmc_host: <host>
    hmc_auth:
      username: <hscroot>
      password: <hmcpass>
    system_name: <system_name>
    platform_config:
      vios_update:
        - update_type: NoUpdate
          vios_name: vios1
          update_order: 1
          io_adapter_update:
            - all: true
              repository: sftp
              sftp:
                hostname: sftp.example.com
                directory: /io/firmware
                username: sftpuser
                keyfile: /home/hscroot/.ssh/id_rsa

- name: Gather SR-IOV, VIOS, and I/O adapter facts
  platform_update:
    hmc_host: <host>
    hmc_auth:
      username: <hscroot>
      password: <hmcpass>
    system_name: <system_name>
    state: facts
'''

RETURN = '''
result:
    description: >
        Dictionary containing the outcome of the operation.
        Always includes C(changed) indicating if the operation made any changes.
        The C(command_output) key contains a dictionary with operation-specific details.
        The keys and values in C(command_output) depend on the type of operation performed.
    type: dict
    returned: always
    sample: {
        "changed": true,
        "command_output": {
            "Key1": "Value1",
            "Key2": "Value2",
            "...": "..."
        }
    }
'''


import logging
import os
LOG_FILENAME = "/tmp/ansible_power_hmc_{0}.log".format(os.getpid())
logger = logging.getLogger(__name__)
import re
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_resource import Hmc
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_constants import HmcConstants
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import parse_error_response
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import HmcRestClient
import sys
import copy
import json


before_update_level = {}
after_update_level = {}


def init_logger():
    old_umask = os.umask(0o177)
    try:
        logging.basicConfig(
            filename=LOG_FILENAME,
            format='[%(asctime)s] %(levelname)s: [%(funcName)s] %(message)s',
            level=logging.DEBUG)
    finally:
        os.umask(old_umask)


def _validate_sftp_block(sftp_block, context, password_key='password', key_key='keyfile', required_fields=None):
    """Validate the nested sftp block: required fields present, exactly one auth method supplied."""
    if required_fields is None:
        required_fields = ['hostname', 'username']

    missing = [f for f in required_fields if not sftp_block.get(f)]
    if missing:
        raise ParameterError(
            f"mandatory parameter{'s' if len(missing) > 1 else ''} "
            f"[{', '.join(missing)}] {'are' if len(missing) > 1 else 'is'} missing "
            f"in sftp block for {context}"
        )

    has_password = bool(sftp_block.get(password_key))
    has_key = bool(sftp_block.get(key_key))
    if has_password and has_key:
        raise ParameterError(
            f"Parameters '{password_key}' and '{key_key}' are mutually exclusive in sftp block for {context}"
        )
    if not has_password and not has_key:
        raise ParameterError(
            f"Either '{password_key}' or '{key_key}' is required in sftp block for {context}"
        )


def validate_sub_params(params, value):
    mandatoryList = []
    unsupportedList = []
    if value == 'sriov_adapter_update':
        mandatoryList += ['subtype']
        unsupportedList += ['is_quick_evac', 'destination_managed_system', 'leave_partition_in_target', 'vios_name', 'resource_type',
                            'io_adapter_update', 'device', 'repository', 'hmc_host', 'hmc_auth', 'update_type',
                            'system_name', 'vios_update', 'vios_image_name', 'level']

        if params.get('all') and params.get('adapter_id'):
            raise ParameterError("Parameter all and adapter_id are mutually exculsive")

        if not (params.get('all') or params.get('adapter_id')):
            raise ParameterError("either all or adapter_id parameter is required")

    if value == 'io_adapter_update':
        unsupportedList += ['is_quick_evac', 'destination_managed_system', 'leave_partition_in_target', 'vios_name', 'resource_type',
                            'io_adapter_update', 'hmc_host', 'hmc_auth', 'update_type', 'system_name', 'vios_update', 'vios_image_name']

        if params.get('all'):
            if params.get('device'):
                raise ParameterError("'all' is mutually exclusive with 'device'.")
        if not (params.get('all') or params.get('device')):
            raise ParameterError("either 'all' or 'device' parameter is required")

        repo = (params.get('repository') or '').lower()
        if repo == 'sftp':
            sftp_block = params.get('sftp')
            if not sftp_block:
                raise ParameterError(f"'sftp' block is required for {value} when repository=sftp")
            _validate_sftp_block(
                sftp_block, context=value,
                required_fields=['hostname', 'directory', 'username']
            )

    collate = []
    for eachUnsupported in unsupportedList:
        if params.get(eachUnsupported):
            collate.append(eachUnsupported)

    if collate:
        if len(collate) == 1:
            raise ParameterError(f"unsupported parameter for {value}: {(collate[0])}")
        else:
            raise ParameterError(f"unsupported parameters for {value}: {(','.join(collate))}")

    collate = []
    for eachMandatory in mandatoryList:
        if not params.get(eachMandatory):
            collate.append(eachMandatory)

    if collate:
        if len(collate) == 1:
            raise ParameterError(f"mandatory parameter {(collate[0])} is missing for {value}")
        else:
            raise ParameterError(f"mandatory parameters {(','.join(collate))} are missing for {value}")


def validate_parameters(params):
    def check_params(param_dict, mandatory, unsupported, context=''):
        missing = [key for key in mandatory if not param_dict.get(key)]
        if missing:
            raise ParameterError(
                f"mandatory parameter{'s' if len(missing) > 1 else ''} "
                f"{'[' + ', '.join(missing) + ']'} {'are' if len(missing) > 1 else 'is'} missing"
                + (f" for {context}" if context else '')
            )

        invalid = [key for key in unsupported if param_dict.get(key)]
        if invalid:
            raise ParameterError(
                f"unsupported parameter{'s' if len(invalid) > 1 else ''} "
                f"{'[' + ', '.join(invalid) + ']'}"
                + (f" for {context}" if context else '')
            )

    def validate_sfw_update(sfw_update):
        mandatory = ['update_type', 'update_order']
        unsupported = [
            'is_quick_evac', 'destination_managed_system', 'leave_partition_in_target', 'vios_name',
            'io_adapter_update', 'id', 'device', 'resource_type', 'hmc_host', 'hmc_auth', 'adapter_id',
            'subtype', 'system_name', 'vios_update', 'vios_image_name'
        ]
        update_type = sfw_update.get('update_type', '')
        if update_type:
            update_type = update_type.lower()
        sriov_updates = sfw_update.get('sriov_adapter_update', [])
        repo = (sfw_update.get('repository') or '').lower()

        if update_type == 'noupdate':
            if not sriov_updates:
                raise ParameterError("Missing parameter sriov_adapter_update for system_firmware_update")
            if repo:
                sfw_update['repository'] = None
            if sfw_update.get('level') != 'latest':
                raise ParameterError("Parameter 'level' is not supported for system_firmware_update when update_type = 'NoUpdate'")
            sfw_update['level'] = None
        elif update_type in ['update', 'upgrade']:
            if sriov_updates:
                raise ParameterError(f"Invalid combination: sriov_adapter_update is not allowed with update_type = '{update_type}'")
            if repo == 'sftp':
                sftp_block = sfw_update.get('sftp')
                if not sftp_block:
                    raise ParameterError("'sftp' block is required for system_firmware_update when repository=sftp")
                _validate_sftp_block(
                    sftp_block, context='system_firmware_update',
                    required_fields=['hostname', 'directory', 'username']
                )

        if sriov_updates:
            for adapter in sriov_updates:
                validate_sub_params(adapter, 'sriov_adapter_update')

        check_params(sfw_update, mandatory, unsupported, 'system_firmware_update')

    def validate_vios_update(vios_updates):
        for vios in vios_updates:
            mandatory = ['update_type', 'vios_name', 'update_order']
            unsupported = [
                'is_quick_evac', 'destination_managed_system', 'leave_partition_in_target', 'device',
                'repository', 'sriov_adapter_update', 'hmc_host', 'hmc_auth', 'adapter_id', 'subtype',
                'system_name'
            ]
            vios_update_type = vios.get('update_type', '')
            resource_type = (vios.get('resource_type') or '').lower()

            if vios_update_type and vios_update_type.lower() != 'noupdate':
                mandatory.append('resource_type')
                mandatory.append('vios_image_name')
                if resource_type == 'sftp':
                    sftp_block = vios.get('sftp')
                    if not sftp_block:
                        raise ParameterError("'sftp' block is required for vios_update when resource_type=sftp")
                    _validate_sftp_block(
                        sftp_block, context='vios_update',
                        password_key='password', key_key='ssh_key',
                        required_fields=['hostname', 'username']
                    )
            else:
                if vios.get('resource_type'):
                    vios['resource_type'] = None
                if vios.get('vios_image_name'):
                    raise ParameterError("Parameter 'vios_image_name' is not supported for vios_update when update_type = 'NoUpdate'")

            io_adapters = vios.get('io_adapter_update', [])
            if io_adapters:
                for adapter in io_adapters:
                    validate_sub_params(adapter, 'io_adapter_update')

            check_params(vios, mandatory, unsupported, 'vios_update')

    def validate_partition_migration(partition_migs):
        mandatory = ['is_quick_evac', 'destination_managed_system']
        unsupported = [
            'update_type', 'update_order', 'vios_name', 'resource_type', 'io_adapter_update',
            'device', 'repository', 'sriov_adapter_update', 'hmc_host', 'hmc_auth', 'adapter_id',
            'subtype', 'system_name', 'level', 'vios_update', 'vios_image_name'
        ]
        check_params(partition_migs, mandatory, unsupported, 'partition_migration')

    def validate_update_order_uniqueness(platform_config):
        components = []

        sfw_update = platform_config.get('system_firmware_update')
        if sfw_update and 'update_order' in sfw_update:
            order = sfw_update['update_order']
            components.append(('system_firmware_update', order))

        vios_updates = platform_config.get('vios_update', [])
        if vios_updates:
            for vios in vios_updates:
                if 'update_order' in vios:
                    components.append((f"vios_update:{vios.get('vios_name', 'unknown')}", vios['update_order']))

        orders = [order for _unused, order in components]
        duplicates = {order for order in orders if orders.count(order) > 1}

        if duplicates:
            dup_details = [name for name, order in components if order in duplicates]
            raise ParameterError(f"'update_order' values must be unique across system_firmware_update and vios_update. Duplicate found in: {dup_details}")

    if params.get('state') and params.get('platform_config'):
        raise ParameterError("Invalid parameter combination: 'state' and 'platform_config' cannot be used together. Please provide only one of them.")
    elif not (params.get('state') or params.get('platform_config')):
        raise ParameterError("Missing required parameter: Please provide either 'state' or 'platform_config'.")
    if params.get('state'):
        mandatory = ['hmc_host', 'hmc_auth', 'system_name']
        unsupported = [
            'is_quick_evac', 'destination_managed_system', 'leave_partition_in_target', 'vios_name',
            'resource_type', 'io_adapter_update', 'id', 'device', 'repository', 'adapter_id',
            'subtype', 'update_type', 'all', 'platform_config', 'vios_update',
        ]
        check_params(params, mandatory, unsupported)
    else:
        mandatory = ['hmc_host', 'hmc_auth', 'system_name', 'platform_config']
        unsupported = [
            'is_quick_evac', 'destination_managed_system', 'leave_partition_in_target', 'vios_name',
            'resource_type', 'io_adapter_update', 'id', 'device', 'repository', 'adapter_id',
            'subtype', 'update_type', 'all', 'vios_update'
        ]
        check_params(params, mandatory, unsupported)

        platform_config = params.get('platform_config', {})
        if not platform_config:
            raise ParameterError("Missing parameter 'platform_config'")

        sfw_update = platform_config.get('system_firmware_update')
        if sfw_update:
            validate_sfw_update(sfw_update)

        vios_updates = platform_config.get('vios_update', [])
        if vios_updates:
            validate_vios_update(vios_updates)

        partition_migs = platform_config.get('partition_migration', {})
        if partition_migs:
            if not (sfw_update or vios_updates):
                raise ParameterError("Invalid usage: 'partition_migration' must be specified along with either 'vios_update' or 'system_firmware_update'")
            validate_partition_migration(partition_migs)
        validate_update_order_uniqueness(platform_config)


def cleanup_entries(data, sriov=None, io=None):
    Adapter_subtype_map = {
        'DriverOnly': 'adapterdriver',
        'Adapter': 'adapterdriver,adapter'
    }
    if sriov:
        sriov_adapters = data["system_firmware_update"].get("sriov_adapter_update", [])
        if sriov_adapters:
            subtype = sriov_adapters[0].get("subtype", "adapterdriver")
            data['system_firmware_update']['sriov_adapter_update'] = [
                {
                    "AdapterID": str(adapter_id),
                    "SubType": subtype
                } for adapter_id in sriov
            ]
    if io:
        viosUpdates = data['vios_update']
        if viosUpdates:
            for vios in viosUpdates:
                ioAdapters = vios.get("io_adapter_update")
                if ioAdapters and ioAdapters[0].get('all'):
                    repo = ioAdapters[0].get("repository", "")
                    sftp_fields = {k: v for k, v in ioAdapters[0].items()
                                   if k not in ('all', 'device', 'repository', 'sftp', 'Id', 'Device', 'Repository')}
                    vios["io_adapter_update"] = [
                        dict(
                            {"Id": adapter_id, "Device": ",".join(devices), "Repository": repo},
                            **sftp_fields
                        )
                        for adapter_id, devices in io['IOAdapterUpdate'].items()
                    ]
                elif ioAdapters:
                    vios["io_adapter_update"] = [
                        dict(
                            {
                                "Id": adapter.get("Id", ""),
                                "Device": ",".join(adapter.get("device", [])) if isinstance(adapter.get("device"), list) else adapter.get("device", ""),
                                "Repository": adapter.get("repository")
                            },
                            **{k: v for k, v in adapter.items()
                               if k not in ('id', 'Id', 'device', 'Device', 'repository', 'Repository', 'sftp', 'all')}
                        )
                        for adapter in ioAdapters
                    ]

    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            if value is not None:
                cleaned_value = cleanup_entries(value)

                if key in ["subtype", "SubType"] and isinstance(cleaned_value, str):
                    cleaned_value = Adapter_subtype_map.get(cleaned_value, cleaned_value)

                cleaned[key] = cleaned_value
        return cleaned

    elif isinstance(data, list):
        return [cleanup_entries(item) for item in data]

    else:
        return data


def _flatten_sftp_block(data):
    """
    Walk the config dict and inline any nested 'sftp' block one level up,
    converting its keys to the API-expected names in the process.

    The sftp block under system_firmware_update / io_adapter_update uses:
        hostname, directory, username, password, keyfile
    mapped to:
        HostName, Directory, UserName, Password, Keyfile

    The sftp block under vios_update uses:
        hostname, username, password, ssh_key, remote_directory, file_names
    mapped to:
        ServerHostOrIP, UserName, Password, SSHKey, RemoteDirectory, FileNames
    SaveFile is always injected as true for SFTP VIOS updates.
    """
    sfw_key_map = {
        'hostname': 'HostName',
        'directory': 'Directory',
        'username': 'UserName',
        'password': 'Password',
        'keyfile': 'Keyfile',
    }
    vios_key_map = {
        'hostname': 'ServerHostOrIP',
        'username': 'UserName',
        'password': 'Password',
        'ssh_key': 'SSHKey',
        'remote_directory': 'RemoteDirectory',
        'file_names': 'FileNames',
    }
    io_key_map = {
        'hostname': 'HostName',
        'directory': 'Directory',
        'username': 'UserName',
        'password': 'Password',
        'keyfile': 'Keyfile',
    }

    if not isinstance(data, dict):
        return data

    # system_firmware_update
    sfw = data.get('SystemFirmwareUpdate') or data.get('system_firmware_update')
    if isinstance(sfw, dict):
        sftp = sfw.pop('sftp', None)
        if sftp and isinstance(sftp, dict):
            for k, v in sftp.items():
                if v is not None:
                    sfw[sfw_key_map.get(k, k)] = v

    # vios_update entries
    vios_list = data.get('VIOSUpdate') or data.get('vios_update') or []
    for vios in vios_list:
        if not isinstance(vios, dict):
            continue
        sftp = vios.pop('sftp', None)
        if sftp and isinstance(sftp, dict):
            # convert file_names list -> comma-separated string
            file_names = sftp.get('file_names')
            if isinstance(file_names, list):
                sftp['file_names'] = ','.join(file_names)
            for k, v in sftp.items():
                if v is not None:
                    vios[vios_key_map.get(k, k)] = v
            # SaveFile is always true for SFTP VIOS updates
            vios['SaveFile'] = True

        # io_adapter_update entries inside each vios
        io_list = vios.get('IOAdapterUpdate') or vios.get('io_adapter_update') or []
        for io in io_list:
            if not isinstance(io, dict):
                continue
            sftp = io.pop('sftp', None)
            if sftp and isinstance(sftp, dict):
                for k, v in sftp.items():
                    if v is not None:
                        io[io_key_map.get(k, k)] = v

    return data


def map_entries(data):
    config_map = {
        "vios_update": "VIOSUpdate",
        "io_adapter_update": "IOAdapterUpdate",
        "device": "Device",
        "repository": "Repository",
        "update_order": "UpdateOrder",
        "vios_name": "VIOSName",
        "update_type": "UpdateType",
        "system_firmware_update": "SystemFirmwareUpdate",
        "sriov_adapter_update": "SRIOVAdapterUpdate",
        "adapter_id": "AdapterID",
        "subtype": "SubType",
        "partition_migration": "PartitionMigration",
        "is_quick_evac": "IsQuickEvac",
        "destination_managed_system": "DestinationManagedSystem",
        "leave_partition_in_target": "LeavePartitionInTarget",
        "resource_type": "ResourceType",
        "name": "Name",
        "level": "Level",
        "vios_image_name": "Name",
        "all": "ALL",
    }

    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            new_key = config_map.get(k, k)
            new_dict[new_key] = map_entries(v)
        return new_dict
    elif isinstance(data, list):
        return [map_entries(item) for item in data]
    else:
        return data


def _is_sftp(source):
    """Return True when the normalised source value indicates SFTP."""
    return (source or '').lower() == 'sftp'


def check_response_exception(output, module, request):
    if isinstance(output, dict) and output.get('ResponseException'):
        module.fail_json(msg=output['ResponseException'])
    if output is None:
        module.fail_json(msg=f"{request} request failed")


def check_current_level(hmc, data, system):
    result = {
        "firmware_level": None,
        "sriov_levels": [],
        "io_adapter_levels": [],
        "vios_versions": []
    }
    try:
        sysfw = data.get("SystemFirmwareUpdate")
        if sysfw:
            update_type = sysfw.get("UpdateType")
            if update_type and update_type not in ("NoUpdate", ""):
                try:
                    result["firmware_level"] = hmc.get_firmware_level(system)
                except Exception as e:
                    logger.error("Failed to get firmware level for %s: %s", system, e)

            sriov_updates = sysfw.get("SRIOVAdapterUpdate")
            if sriov_updates and isinstance(sriov_updates, list):
                try:
                    sriov_data = hmc.get_io_sriov_level(system, 'sriov')
                    result["sriov_levels"].append(sriov_data)
                except Exception as e:
                    logger.error("Failed to get SRIOV adapter level: %s", e)

    except Exception as e:
        logger.error("Error in SystemFirmwareUpdate parsing: %s", e)

    try:
        vios_updates = data.get("VIOSUpdate")
        if vios_updates and isinstance(vios_updates, list):
            for vios in vios_updates:
                try:
                    update_type = vios.get("UpdateType")
                    vios_name = vios.get("VIOSName")
                    if update_type and update_type not in ("NoUpdate", "") and vios_name:
                        try:
                            configDict = {
                                "system_name": system,
                                "vios_name": vios_name,
                            }

                            os_version = hmc.getviosversion(configDict).strip()
                            result["vios_versions"].append({
                                "vios_name": vios_name,
                                "os_version": os_version
                            })
                        except Exception as e:
                            logger.error("Failed to get OS version for VIOS %s: %s", vios_name, e)

                    io_updates = vios.get("IOAdapterUpdate")
                    if io_updates and isinstance(io_updates, list):
                        try:
                            io_data = hmc.get_io_sriov_level(system, 'io')
                            result["io_adapter_levels"].append(io_data)
                        except Exception as e:
                            logger.error("Failed to get IO adapter levels: %s", e)
                except Exception as e:
                    logger.error("Error while processing individual VIOS update entry: %s", e)
    except Exception as e:
        logger.error("Error in VIOSUpdate parsing: %s", e)

    return result


def platform_update(module):
    params = module.params
    try:
        validate_parameters(params)
    except Exception as e:
        module.fail_json(msg=str(e))
    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    attributes = params.get('platform_config')
    changed = False
    vios_updates = copy.deepcopy(attributes.get('vios_update'))
    all_io_updates = []
    available_adapter_id = []
    available_io_updates = {"IOAdapterUpdate": {}}
    global before_update_level, after_update_level
    if vios_updates:
        for entry in vios_updates:
            vios_name = entry.get("vios_name")
            io_adapters = entry.get("io_adapter_update")

            if isinstance(io_adapters, list):
                for adapter in entry["io_adapter_update"]:
                    adapter["vios_name"] = vios_name
                    all_io_updates.append(adapter)

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)

    sys_list = (
        hmc.list_all_managed_system_details(config_F="name") + hmc.list_all_managed_system_details(config_F="type_model*serial_num")
    )
    if not sys_list:
        module.fail_json(msg="No managed systems found in HMC")
    elif system_name not in [v for d in sys_list for v in d.values()]:
        module.fail_json(msg="The managed system is not available in HMC")
    else:
        vios_list = list(hmc_conn.execute("lssyscfg -r lpar -m {0} -F name,state,lpar_id,rmc_state".format(system_name)).splitlines())
        if vios_updates:
            vios_names = [entry["vios_name"] for entry in attributes.get("vios_update", [])]
            for vios in vios_names:
                vios_details = next((entry.split(',') for entry in vios_list if entry.split(',')[0] == vios), None)
                if vios_details:
                    if vios_details[3] == 'inactive':
                        module.fail_json(msg=f"The VIOS {vios} does not have an active RMC connection and cannot be updated at this time")
                    for io_update in all_io_updates:
                        if io_update.get("vios_name") == vios:
                            io_update["vios_id"] = vios_details[2].zfill(3)
                    if attributes.get('vios_update'):
                        for entry in attributes.get('vios_update'):
                            io_adapters = entry.get("io_adapter_update")
                            if io_adapters:
                                for adapter in io_adapters:
                                    adapter["Id"] = vios_details[2].zfill(3)
                                    adapter['repository'] = (adapter.get("repository") or '').lower()
                else:
                    module.fail_json(msg=f"The VIOS {vios} is not available in HMC")

    if re.match(HmcConstants.MTMS_pattern, system_name):
        try:
            system_name = hmc.getSystemNameFromMTMS(system_name)
        except HmcError as on_system_error:
            return changed, repr(on_system_error), None

    try:
        with HmcRestClient(hmc_host, hmc_user, password) as rest_conn:
            try:
                system_uuid, _unused = rest_conn.getManagedSystem(system_name)
            except Exception as error:
                error_msg = parse_error_response(error)
                module.fail_json(msg=error_msg)
            if not system_uuid:
                module.fail_json(msg="Given system is not present")

            # Partition Migration Checks
            if attributes.get('partition_migration'):
                partition_migration = attributes.get('partition_migration')
                destination_system = partition_migration.get('destination_managed_system')
                if destination_system not in [v for d in sys_list for v in d.values()]:
                    module.fail_json(msg=f"The managed system {destination_system} is not available in HMC")
                attributes['partition_migration'] = [partition_migration]

            # System Readiness Check
            sysfirm_update = attributes.get("system_firmware_update", {})
            if sysfirm_update:
                status, result = rest_conn.LicReadinessCheck(system_uuid, system_name)
                check_response_exception(result, module, 'LicReadinessCheck')
                if status == 'COMPLETED_OK':
                    logger.info("System readiness check Passed")
                else:
                    msg = "No message error provided"
                    for param in result:
                        if param.get("ParameterName") == 'JOBRESULT_KEY_ERRORMSG':
                            msg = param.get('ParameterValue')
                            break
                    error_msg = f'system {system_name} is not in ready state, therefore the system firmware cannot be updated, Msg: {msg}'
                    module.fail_json(msg=error_msg)

            # SRIOV Adapters Avaiability Check
            sysfirm_update = attributes.get("system_firmware_update", {})
            if sysfirm_update:
                output = rest_conn.LicQueryLevel(system_uuid, system_name, type='sriov')
                check_response_exception(output, module, 'LicQueryLevel')
                if output.get('ParameterName'):
                    error_msg = output.get('ParameterValue')
                    module.fail_json(msg=error_msg)
                sriov_update = sysfirm_update.get('sriov_adapter_update')
                if sriov_update:
                    if 'No results' in (output.get("SRIOVAdapterUpdate", {}).get("AdapterID") or ''):
                        error_msg = f'No SRIOV Adapters are available for {system_name}'
                        module.fail_json(msg=error_msg)

                    for adapter in sriov_update:
                        if adapter.get('all') is False:
                            adapter['all'] = None
                        if adapter.get('all'):
                            available_adapter_id = output.get("SRIOVAdapterUpdate", {}).get("AdapterID")
                        else:
                            adapter_id = adapter.get("adapter_id")
                            if adapter_id not in (output.get("SRIOVAdapterUpdate", {}).get("AdapterID") or []):
                                error_msg = f"SRIOVAdapter with ID {adapter_id} is not present for system {system_name}"
                                module.fail_json(msg=error_msg)
                            adapter['adapter_id'] = str(adapter_id)

            # IO Adapter Avaiabillty check
            if all_io_updates:
                output = rest_conn.LicQueryLevel(system_uuid, system_name, type='io')
                check_response_exception(output, module, 'LicQueryLevel')
                if output.get('ParameterName'):
                    error_msg = output.get('ParameterValue')
                    module.fail_json(msg=error_msg)

                for io_update in all_io_updates:
                    if 'No results' in (output.get("IOAdapterUpdate") or ''):
                        error_msg = f"No IO Adapters are available for VIOS '{io_update.get('vios_name')}'"
                        module.fail_json(msg=error_msg)
                    if io_update.get('all'):
                        vios_id = io_update.get('vios_id')
                        if output.get('IOAdapterUpdate', {}).get(vios_id, []):
                            available_io_updates = {'IOAdapterUpdate': {vios_id: output.get('IOAdapterUpdate', {}).get(vios_id, [])}}
                        else:
                            error_msg = f"No available I/O adapters found for VIOS {io_update.get('vios_name')}"
                            module.fail_json(msg=error_msg)
                    else:
                        io_id = str(io_update.get('vios_id')).zfill(3)
                        devices = io_update.get('device')
                        valid_devices = output.get('IOAdapterUpdate', {}).get(io_id, [])
                        if valid_devices:
                            for device in devices:
                                if device not in valid_devices:
                                    error_msg = (
                                        f"Device '{device}' is not found under IO Adapter with ID '{io_update.get('vios_id')}' "
                                        f"for VIOS '{io_update.get('vios_name')}'."
                                    )
                                    module.fail_json(msg=error_msg)
                        else:
                            error_msg = f"VIOS '{io_update.get('vios_name')}' does not contain IO Adapter with ID '{io_update.get('vios_id')}'."
                            module.fail_json(msg=error_msg)

            # Vios Update Check — skip listViosUpdates for SFTP (image resolved by HMC at update time)
            needs_update = None
            if vios_updates:
                needs_update = any('update' == vios.get('update_type', '').lower() for vios in attributes.get("vios_update", []))
            if needs_update:
                console_uuid = rest_conn.getManagementConsole()
                for vios_info in attributes.get("vios_update", []):
                    updateType = vios_info['update_type'].lower()
                    if updateType == 'update':
                        vios_name = vios_info['vios_name']
                        source_file = vios_info['resource_type']
                        if _is_sftp(source_file):
                            logger.info("Skipping listViosUpdates for VIOS %s: sftp repository", vios_name)
                            continue
                        vios_level = vios_info['vios_image_name']
                        output = rest_conn.listViosUpdates(console_uuid, system_name, vios_name, source_file)
                        check_response_exception(output, module, 'listViosUpdates')
                        if output.strip() in ("[]", "", "None"):
                            error_msg = f"Vios Image {vios_level} for {vios_name} not found at the specified source location: {source_file}."
                            module.fail_json(msg=error_msg)
                        elif vios_level not in output:
                            error_msg = (
                                f"Update file {vios_level} for vios {vios_name} "
                                f"is not found at the specified source location: {source_file}."
                            )
                            module.fail_json(msg=error_msg)

            # System Firmware Update Check — skip LICQueryRepository for SFTP
            sysfirm_update = attributes.get('system_firmware_update')
            if sysfirm_update:
                updateType = (sysfirm_update.get('update_type') or '').lower()
                if updateType in ['update', 'upgrade']:
                    firm_level = sysfirm_update.get('level')
                    source_file = (sysfirm_update.get('repository') or '').lower()
                    if source_file:
                        sysfirm_update['repository'] = source_file
                    sysfirm_update['Type'] = 'sys'
                    if _is_sftp(source_file):
                        sftp_block = sysfirm_update.get('sftp', {}) or {}
                        output = rest_conn.LICQueryRepository(
                            system_uuid, system_name, source_file,
                            type="sys", level=updateType,
                            hostname=sftp_block.get('hostname'),
                            username=sftp_block.get('username'),
                            password=sftp_block.get('password'),
                            directory=sftp_block.get('directory'),
                            keyfile=sftp_block.get('keyfile'),
                        )
                        check_response_exception(output, module, 'LICQueryRepository')
                        if output.get('ParameterName') == 'JOBRESULT_KEY_ERRORMSG':
                            error_msg = (
                                f"No {updateType.upper()} file found at the SFTP source: {sftp_block.get('hostname')} "
                                f"for the resource: {system_name} reason: {output.get('ParameterValue')}"
                            )
                            module.fail_json(msg=error_msg)
                        param_val = output.get('ParameterValue', '')
                        logger.debug("SFTP LICQueryRepository ParameterValue raw: %s", repr(param_val))
                        if not param_val or 'No results' in param_val:
                            module.fail_json(msg=(
                                f"No {updateType.upper()} firmware image found on SFTP server "
                                f"{sftp_block.get('hostname')}:{sftp_block.get('directory', '')} "
                                f"for the resource: {system_name}. "
                                f"Verify the directory path and that firmware images are present."
                            ))
                        available_levels = []
                        for line in param_val.splitlines():
                            parts = line.split(",")
                            if len(parts) >= 3:
                                available_levels.append(parts[2].strip())
                        if firm_level != 'latest' and firm_level not in available_levels:
                            error_msg = (
                                f"Update file {firm_level} for the resource {system_name} "
                                f"is not found at the specified SFTP source location: {sftp_block.get('hostname')}."
                            )
                            module.fail_json(msg=error_msg)
                        else:
                            lines = param_val.split("\n")
                            sysfirm_update['IsDestruptive'] = False
                            if firm_level != 'latest':
                                for line in lines:
                                    parts = line.split(",")
                                    if len(parts) > 4 and firm_level == parts[2]:
                                        sysfirm_update['IsDestruptive'] = parts[4].strip().lower() == "disruptive"
                                        break
                    else:
                        output = rest_conn.LICQueryRepository(system_uuid, system_name, source_file,
                                                              type="sys", level=updateType)
                        check_response_exception(output, module, 'LICQueryRepository')
                        if "No results" in (output.get('ParameterValue') or ''):
                            error_msg = f"No {updateType.upper()} file found at the specified source: {source_file} for the resource: {system_name}."
                            module.fail_json(msg=error_msg)
                        if output.get('ParameterName') == 'JOBRESULT_KEY_ERRORMSG':
                            error_msg = (
                                f"No {updateType.upper()} file found at the specified source: {source_file} "
                                f"for the resource: {system_name} reason: {output.get('ParameterValue')}"
                            )
                            module.fail_json(msg=error_msg)
                        param_val = output.get('ParameterValue', '')
                        available_levels = []
                        if param_val:
                            for line in param_val.splitlines():
                                parts = line.split(",")
                                if len(parts) >= 3:
                                    available_levels.append(parts[2].strip())
                        if firm_level != 'latest' and firm_level not in available_levels:
                            error_msg = (
                                f"Update file {firm_level} for the resource {system_name} "
                                f"is not found at the specified source location: {source_file}."
                            )
                            module.fail_json(msg=error_msg)
                        else:
                            if output.get('ParameterValue'):
                                output = output.get('ParameterValue')
                                lines = output.split("\n")
                                sysfirm_update['IsDestruptive'] = False
                                if firm_level != 'latest':
                                    for line in lines:
                                        parts = line.split(",")
                                        if firm_level == parts[2]:
                                            sysfirm_update['IsDestruptive'] = parts[4].strip().lower() == "disruptive"
                                            break
                                else:
                                    latest_line = max(
                                        (line for line in lines if line.strip()),
                                        key=lambda line_data: int(line_data.split(",")[2])
                                    )
                                    parts = latest_line.split(",")
                                    sysfirm_update['IsDestruptive'] = parts[4].strip().lower() == "disruptive"

                    # Normalise numeric level to 3-digit zero-padded string for HMC API
                    if sysfirm_update.get('level') != "latest":
                        firm_level = str(sysfirm_update.get('level'))
                        if firm_level.isdigit():
                            if len(firm_level) == 1:
                                firm_level = "00" + firm_level
                            elif len(firm_level) == 2:
                                firm_level = "0" + firm_level
                        sysfirm_update['level'] = firm_level

            # IO Adapter Update check — skip LICQueryRepository for SFTP
            if all_io_updates:
                for io_update in all_io_updates:
                    source_file = (io_update.get('repository') or '').lower()
                    vios_id = io_update.get('vios_id')
                    if _is_sftp(source_file):
                        logger.info("Skipping LICQueryRepository for IO adapter update: sftp repository")
                        continue
                    output = rest_conn.LICQueryRepository(system_uuid, system_name, source_file)
                    check_response_exception(output, module, 'LICQueryRepository')
                    if available_io_updates:
                        adp_ids = vios_id
                    else:
                        adp_ids = {io_update.get('id')}
                    if output.get('ParameterName') == 'JOBRESULT_KEY_ERRORMSG':
                        error_msg = (
                            f"Import operation failed for IO Adapter ID '{adp_ids}' "
                            f"on VIOS '{io_update.get('vios_name')}': {output.get('ParameterValue')}"
                        )
                        module.fail_json(msg=error_msg)

            # Flatten nested sftp blocks into parent dicts before cleanup/mapping
            _flatten_sftp_block(attributes)

            cleaned_data = cleanup_entries(attributes, sriov=available_adapter_id, io=available_io_updates)
            mapped_data = map_entries(cleaned_data)
            before_update_level = check_current_level(hmc, mapped_data, system_name)
            final_output = rest_conn.PlatformUpdate(system_uuid, mapped_data)
            check_response_exception(final_output, module, 'PlatformUpdate')
            after_update_level = check_current_level(hmc, mapped_data, system_name)
    except (Exception, HmcError) as error:
        error_msg = parse_error_response(error)
        logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(error))
        module.fail_json(msg=error_msg)

    return True, final_output, None


def facts(module):
    params = module.params

    try:
        validate_parameters(params)
    except Exception as e:
        module.fail_json(msg=str(e))

    hmc_host = params['hmc_host']
    hmc_user = params['hmc_auth']['username']
    password = params['hmc_auth']['password']
    system_name = params['system_name']
    changed = False
    hmc_conn = None

    hmc_conn = HmcCliConnection(module, hmc_host, hmc_user, password)
    hmc = Hmc(hmc_conn)
    sys_list = (
        hmc.list_all_managed_system_details(config_F="name") + hmc.list_all_managed_system_details(config_F="type_model*serial_num")
    )
    if not sys_list:
        module.fail_json(msg="No managed systems found in HMC")
    elif system_name not in [v for d in sys_list for v in d.values()]:
        module.fail_json(msg="The managed system is not available in HMC")
    else:
        cmd = f"lssyscfg -r lpar -m {system_name} -F name,rmc_state,lpar_id,lpar_env | grep vioserver | grep -w active"
        try:
            output = hmc_conn.execute(cmd)
        except Exception:
            output = None
        if output:
            output = output.splitlines()
            vios_list = [(line.split(',')[0], line.split(',')[2]) for line in output if line.strip()]
        else:
            vios_list = []
        if re.match(HmcConstants.MTMS_pattern, system_name):
            try:
                system_name = hmc.getSystemNameFromMTMS(system_name)
            except HmcError as on_system_error:
                return changed, repr(on_system_error), None

        try:
            with HmcRestClient(hmc_host, hmc_user, password) as rest_conn:
                try:
                    system_uuid, _unused = rest_conn.getManagedSystem(system_name)
                except Exception as error:
                    error_msg = parse_error_response(error)
                    module.fail_json(msg=error_msg)
                if not system_uuid:
                    module.fail_json(msg="Given system is not present")

                def extract_adapters(response, key):
                    if response.get('ParameterName'):
                        return None
                    value = response.get(key)
                    if not value or 'No results' in value:
                        return None
                    return value

                sriov_output = rest_conn.LicQueryLevel(system_uuid, system_name, type='sriov')
                check_response_exception(sriov_output, module, 'LicQueryLevel')
                sriov_adapters = extract_adapters(sriov_output, 'SRIOVAdapterUpdate')

                io_output = rest_conn.LicQueryLevel(system_uuid, system_name, type='io')
                check_response_exception(io_output, module, 'LicQueryLevel')
                io_adapters = extract_adapters(io_output, 'IOAdapterUpdate')

                vios_info = []

                for vios_name, vios_id in vios_list:
                    padded_id = vios_id.zfill(3)
                    adapter_info = io_adapters.get(padded_id) if io_adapters else None
                    vios_info.append({
                        'vios_name': vios_name,
                        'vios_id': vios_id,
                        'io_devices': adapter_info if adapter_info else 'No adapters available'
                    })

                adapter_info = {
                    system_name: {
                        'sriov_adapters': sriov_adapters if sriov_adapters else 'No sriov_adapters available',
                        'vios_info': vios_info
                    }
                }
        except (Exception, HmcError) as error:
            error_msg = parse_error_response(error)
            logger.debug("Line number: %d exception: %s", sys.exc_info()[2].tb_lineno, repr(error))
            module.fail_json(msg=error_msg)

    return changed, adapter_info, None


def compare_levels(before, after):
    if before is not None and after is not None:
        return json.dumps(before, sort_keys=True) == json.dumps(after, sort_keys=True)
    return False


def run_module():
    # Shared sftp sub-spec reused across all three update sections
    sftp_sfw_spec = dict(
        hostname=dict(type='str'),
        directory=dict(type='str'),
        username=dict(type='str'),
        password=dict(type='str', no_log=True),
        keyfile=dict(type='str', no_log=True),
    )
    sftp_vios_spec = dict(
        hostname=dict(type='str'),
        username=dict(type='str'),
        password=dict(type='str', no_log=True),
        ssh_key=dict(type='str', no_log=True),
        remote_directory=dict(type='str'),
        file_names=dict(type='list', elements='str'),
    )
    sftp_io_spec = dict(
        hostname=dict(type='str'),
        directory=dict(type='str'),
        username=dict(type='str'),
        password=dict(type='str', no_log=True),
        keyfile=dict(type='str', no_log=True),
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
        platform_config=dict(
            type='dict',
            options=dict(
                system_firmware_update=dict(
                    type='dict',
                    options=dict(
                        update_type=dict(type='str', choices=['NoUpdate', 'Update', 'Upgrade']),
                        update_order=dict(type='int'),
                        repository=dict(type='str', choices=['IBMWebsite', 'sftp'], default='IBMWebsite'),
                        level=dict(type='str', default="latest"),
                        sftp=dict(type='dict', options=sftp_sfw_spec),
                        sriov_adapter_update=dict(
                            type='list',
                            elements='dict',
                            options=dict(
                                all=dict(type="bool"),
                                adapter_id=dict(type='int'),
                                subtype=dict(type='str', choices=['DriverOnly', 'Adapter'])
                            )
                        )
                    )
                ),
                partition_migration=dict(
                    type='dict',
                    options=dict(
                        is_quick_evac=dict(type='bool'),
                        destination_managed_system=dict(type='str'),
                        leave_partition_in_target=dict(type='bool', default=False)
                    )
                ),
                vios_update=dict(
                    type='list',
                    elements='dict',
                    options=dict(
                        update_type=dict(type='str', choices=['NoUpdate', 'Update']),
                        vios_name=dict(type='str'),
                        update_order=dict(type='int'),
                        resource_type=dict(type='str', choices=['IBMWebsite', 'sftp'], default='IBMWebsite'),
                        vios_image_name=dict(type='str'),
                        sftp=dict(type='dict', options=sftp_vios_spec),
                        io_adapter_update=dict(
                            type='list',
                            elements='dict',
                            options=dict(
                                all=dict(type='bool'),
                                device=dict(type='list', elements='str'),
                                repository=dict(type='str', choices=['IBMWebsite', 'sftp'], default='IBMWebsite'),
                                sftp=dict(type='dict', options=sftp_io_spec),
                            )
                        )
                    )
                )
            )
        ),
        state=dict(type='str', choices=['facts'])
    )

    module = AnsibleModule(
        argument_spec=module_args,
    )

    if module._verbosity >= 5:
        init_logger()

    if sys.version_info < (3, 0):
        py_ver = sys.version_info[0]
        raise ParameterError("Unsupported Python version {0}, supported python version is 3 and above".format(py_ver))

    ok_count = 0
    failed_messages = []

    if module.params.get('state'):
        changed, info, warning = facts(module)
    else:
        changed, info, warning = platform_update(module)

        if info:
            for data in info:
                status = data.get('CurrentStatus')
                if status == "COMPLETED_OK":
                    ok_count += 1
                elif status == "COMPLETED_WITH_ERROR":
                    failureMsg = data.get('FailureMessage', '')
                    if failureMsg and "no updates" in failureMsg.lower():
                        ok_count += 1
                    else:
                        failed_messages.append(failureMsg or "Unknown error")

            if failed_messages and ok_count == 0:
                result = {'changed': changed, 'command_output': info}
                if warning:
                    result['warning'] = warning
                module.fail_json(msg='; '.join(failed_messages), **result)

        if compare_levels(before_update_level, after_update_level):
            changed = False

    result = {
        'changed': changed,
    }

    if info:
        result['command_output'] = info

    if warning:
        result['warning'] = warning

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
