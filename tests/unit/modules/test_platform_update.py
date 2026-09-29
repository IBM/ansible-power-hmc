from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
import importlib

IMPORT_HMC_PLATFORM_UPDATE = "ansible_collections.ibm.power_hmc.plugins.modules.platform_update"


class FakeModule:
    def __init__(self, params):
        self.params = params
        self.fail_msg = None

    def fail_json(self, msg):
        raise Exception(f"ParameterError: {msg}")


hmc_auth = {'username': 'hscroot', 'password': 'password_value'}
facts_test_data = [
    # All Facts related test cases
    # Not providing hmc host
    ({'hmc_host': None, 'hmc_auth': hmc_auth, 'state': 'facts', 'system_name': 'sys'},
        "ParameterError: mandatory parameter [hmc_host] is missing"),

    # Not providing hmc_auth
    ({'hmc_host': 'hmc_host', 'hmc_auth': None, 'state': 'facts', 'system_name': 'sys'},
        "ParameterError: mandatory parameter [hmc_auth] is missing"),

    # Not providing system_name
    ({'hmc_host': 'hmc_host', 'hmc_auth': hmc_auth, 'state': 'facts', 'system_name': None},
        "ParameterError: mandatory parameter [system_name] is missing"),

    # providing both state and platform_config
    ({'hmc_host': 'hmc_host', 'hmc_auth': hmc_auth, 'state': 'facts', 'system_name': 'sys',
        'platform_config': {'vios_update': [{'update_type': 'NoUpdate', 'vios_name': 'vios_name', 'update_order': 1, 'resource_type': None}]}},
        "ParameterError: Invalid parameter combination: 'state' and 'platform_config' cannot be used together. Please provide only one of them."),

    # Not providing state and platform_config
    ({'hmc_host': 'hmc_host', 'hmc_auth': hmc_auth, 'system_name': None},
        "ParameterError: Missing required parameter: Please provide either 'state' or 'platform_config'."),
]

platform_config_test_data = [
    # All platform_config test cases

    # Missing hmc_host
    (
        {'hmc_host': None, 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'state': None, 'system_name': 'sys',
         'platform_config': {'vios_update': [{'update_type': 'NoUpdate', 'vios_name': 'vios1', 'update_order': 1}]}},
        "ParameterError: mandatory parameter [hmc_host] is missing"
    ),

    # Missing hmc_auth
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': None, 'state': None, 'system_name': 'sys',
         'platform_config': {'vios_update': [{'update_type': 'NoUpdate', 'vios_name': 'vios1', 'update_order': 1}]}},
        "ParameterError: mandatory parameter [hmc_auth] is missing"
    ),

    # Missing system_name
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'state': None, 'system_name': None,
         'platform_config': {'vios_update': [{'update_type': 'NoUpdate', 'vios_name': 'vios1', 'update_order': 1}]}},
        "ParameterError: mandatory parameter [system_name] is missing"
    ),

    # Both state and platform_config provided
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'state': 'facts', 'system_name': 'sys',
         'platform_config': {'vios_update': [{'update_type': 'Update', 'vios_name': 'vios1', 'update_order': 1}]}},
        "ParameterError: Invalid parameter combination: 'state' and 'platform_config' cannot be used together. Please provide only one of them."
    ),

    # Neither state nor platform_config provided
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'state': None, 'system_name': 'sys'},
        "ParameterError: Missing required parameter: Please provide either 'state' or 'platform_config'."
    ),

    # vios_update with NoUpdate and level not latest
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
         'platform_config': {'vios_update': [{'update_type': 'NoUpdate', 'vios_name': 'vios1', 'update_order': 1, 'vios_image_name': 'fixpack-3'}]}},
        "ParameterError: Parameter 'vios_image_name' is not supported for vios_update when update_type = 'NoUpdate'"
    ),

    # system_firmware_update with update_type=NoUpdate and no sriov_adapter_update
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
         'platform_config': {'system_firmware_update': {'update_type': 'NoUpdate', 'update_order': 1}}},
        "ParameterError: Missing parameter sriov_adapter_update for system_firmware_update"
    ),

    # sriov_adapter_update missing both 'all' and 'adapter_id'
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
            'platform_config': {'system_firmware_update': {'update_type': 'NoUpdate', 'update_order': 1, 'level': 'latest',
                                                           'sriov_adapter_update': [{'subtype': 'DriverOnly'}]}}},
        "ParameterError: either all or adapter_id parameter is required"
    ),

    # sriov_adapter_update has both 'all' and 'adapter_id'
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
            'platform_config': {'system_firmware_update': {'update_type': 'NoUpdate', 'update_order': 1, 'level': 'latest',
                                                           'sriov_adapter_update': [{'all': True, 'adapter_id': 'adapter1',
                                                                                      'subtype': 'Adapter'}]}}},
        "ParameterError: Parameter all and adapter_id are mutually exculsive"
    ),

    # partition_migration without vios_update or system_firmware_update
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
            'platform_config': {'partition_migration': {'is_quick_evac': True, 'destination_managed_system': 'ms1'}}},
        "ParameterError: Invalid usage: 'partition_migration' must be specified along with either 'vios_update' or 'system_firmware_update'"
    ),

    # system_firmware_update with update_type 'update' and sriov_adapter_update present (invalid combo)
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
         'platform_config': {
            'system_firmware_update': {
                'update_type': 'Update',
                'update_order': 1,
                'sriov_adapter_update': [{'all': True, 'subtype': 'Adapter'}]
            }
        }},
        "ParameterError: Invalid combination: sriov_adapter_update is not allowed with update_type = 'update'"
    ),

    # system_firmware_update with update_type 'NoUpdate' and level != 'latest'
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
         'platform_config': {
             'system_firmware_update': {
                 'update_type': 'NoUpdate',
                 'update_order': 1,
                 'level': 'fixpack-10',
                 'sriov_adapter_update': [{'all': True, 'subtype': 'Adapter'}]
             }
        }},
        "ParameterError: Parameter 'level' is not supported for system_firmware_update when update_type = 'NoUpdate'"
    ),

    # sriov_adapter_update missing subtype (mandatory)
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
         'platform_config': {
             'system_firmware_update': {
                 'update_type': 'NoUpdate',
                 'update_order': 1,
                 'level': 'latest',
                 'sriov_adapter_update': [{'all': True}]
             }
        }},
        "ParameterError: mandatory parameter subtype is missing for sriov_adapter_update"
    ),

    # io_adapter_update with 'all' and 'device' together (invalid combo)
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
         'platform_config': {
             'vios_update': [{
                 'update_type': 'Update',
                 'vios_name': 'vios1',
                 'update_order': 1,
                 'io_adapter_update': [{'all': True, 'device': 'dev1'}]
             }]
        }},
        "ParameterError: 'all' is mutually exclusive with 'device'."
    ),

    # io_adapter_update missing all or device
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
         'platform_config': {
             'vios_update': [{
                 'update_type': 'Update',
                 'vios_name': 'vios1',
                 'update_order': 1,
                 'io_adapter_update': [{}]
             }]
        }},
        "ParameterError: either 'all' or 'device' parameter is required"
    ),

    # partition_migration missing is_quick_evac (mandatory)
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
         'platform_config': {
             'system_firmware_update': {
                 'update_type': 'NoUpdate',
                 'update_order': 1,
                 'level': 'latest',
                 'sriov_adapter_update': [{'all': True, 'subtype': 'DriverOnly'}]
             },
             'partition_migration': {'destination_managed_system': 'sys2'}
        }},
        "ParameterError: mandatory parameter [is_quick_evac] is missing for partition_migration"
    ),

    # partition_migration with unsupported field 'vios_name'
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
         'platform_config': {
             'system_firmware_update': {
                 'update_type': 'NoUpdate',
                 'update_order': 1,
                 'level': 'latest',
                 'sriov_adapter_update': [{'all': True, 'subtype': 'DriverOnly'}]
             },
             'partition_migration': {'is_quick_evac': True, 'destination_managed_system': 'sys2', 'vios_name': 'v1'}
        }},
        "ParameterError: unsupported parameter [vios_name] for partition_migration"
    ),

    # --- SFTP: system_firmware_update ---

    # sftp repository but no sftp block at all
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
         'platform_config': {
             'system_firmware_update': {
                 'update_type': 'Update', 'update_order': 1,
                 'repository': 'sftp', 'level': 'latest', 'sftp': None
             }
        }},
        "ParameterError: 'sftp' block is required for system_firmware_update when repository=sftp"
    ),

    # sftp block present but hostname missing
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
         'platform_config': {
             'system_firmware_update': {
                 'update_type': 'Update', 'update_order': 1,
                 'repository': 'sftp', 'level': 'latest',
                 'sftp': {'hostname': None, 'directory': '/fw', 'username': 'user', 'password': 'pass', 'keyfile': None}
             }
        }},
        "ParameterError: mandatory parameter [hostname] is missing in sftp block for system_firmware_update"
    ),

    # sftp block present but directory missing
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
         'platform_config': {
             'system_firmware_update': {
                 'update_type': 'Update', 'update_order': 1,
                 'repository': 'sftp', 'level': 'latest',
                 'sftp': {'hostname': 'sftp.host', 'directory': None, 'username': 'user', 'password': 'pass', 'keyfile': None}
             }
        }},
        "ParameterError: mandatory parameter [directory] is missing in sftp block for system_firmware_update"
    ),

    # sftp block: neither password nor keyfile provided
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
         'platform_config': {
             'system_firmware_update': {
                 'update_type': 'Update', 'update_order': 1,
                 'repository': 'sftp', 'level': 'latest',
                 'sftp': {'hostname': 'sftp.host', 'directory': '/fw', 'username': 'user', 'password': None, 'keyfile': None}
             }
        }},
        "ParameterError: Either 'password' or 'keyfile' is required in sftp block for system_firmware_update"
    ),

    # sftp block: both password and keyfile provided (mutually exclusive)
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
         'platform_config': {
             'system_firmware_update': {
                 'update_type': 'Update', 'update_order': 1,
                 'repository': 'sftp', 'level': 'latest',
                 'sftp': {'hostname': 'sftp.host', 'directory': '/fw', 'username': 'user', 'password': 'pass', 'keyfile': '/id_rsa'}
             }
        }},
        "ParameterError: Parameters 'password' and 'keyfile' are mutually exclusive in sftp block for system_firmware_update"
    ),

    # --- SFTP: vios_update ---

    # sftp resource_type but no sftp block
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
         'platform_config': {
             'vios_update': [{
                 'update_type': 'Update', 'vios_name': 'vios1', 'update_order': 1,
                 'resource_type': 'sftp', 'vios_image_name': 'pkg', 'sftp': None
             }]
        }},
        "ParameterError: 'sftp' block is required for vios_update when resource_type=sftp"
    ),

    # sftp vios: vios_image_name missing
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
         'platform_config': {
             'vios_update': [{
                 'update_type': 'Update', 'vios_name': 'vios1', 'update_order': 1,
                 'resource_type': 'sftp', 'vios_image_name': None,
                 'sftp': {'hostname': 'sftp.host', 'username': 'user', 'password': 'pass', 'ssh_key': None}
             }]
        }},
        "ParameterError: mandatory parameter [vios_image_name] is missing for vios_update"
    ),

    # sftp vios: neither password nor ssh_key provided
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
         'platform_config': {
             'vios_update': [{
                 'update_type': 'Update', 'vios_name': 'vios1', 'update_order': 1,
                 'resource_type': 'sftp', 'vios_image_name': 'pkg',
                 'sftp': {'hostname': 'sftp.host', 'username': 'user', 'password': None, 'ssh_key': None}
             }]
        }},
        "ParameterError: Either 'password' or 'ssh_key' is required in sftp block for vios_update"
    ),

    # sftp vios: both password and ssh_key provided (mutually exclusive)
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
         'platform_config': {
             'vios_update': [{
                 'update_type': 'Update', 'vios_name': 'vios1', 'update_order': 1,
                 'resource_type': 'sftp', 'vios_image_name': 'pkg',
                 'sftp': {'hostname': 'sftp.host', 'username': 'user', 'password': 'pass', 'ssh_key': '/id_rsa'}
             }]
        }},
        "ParameterError: Parameters 'password' and 'ssh_key' are mutually exclusive in sftp block for vios_update"
    ),

    # --- SFTP: io_adapter_update ---

    # sftp repository but no sftp block in io_adapter_update
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
         'platform_config': {
             'vios_update': [{
                 'update_type': 'NoUpdate', 'vios_name': 'vios1', 'update_order': 1,
                 'io_adapter_update': [{'all': True, 'repository': 'sftp', 'sftp': None}]
             }]
        }},
        "ParameterError: 'sftp' block is required for io_adapter_update when repository=sftp"
    ),

    # sftp io_adapter: neither password nor keyfile provided
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
         'platform_config': {
             'vios_update': [{
                 'update_type': 'NoUpdate', 'vios_name': 'vios1', 'update_order': 1,
                 'io_adapter_update': [{
                     'all': True, 'repository': 'sftp',
                     'sftp': {'hostname': 'sftp.host', 'directory': '/io', 'username': 'user', 'password': None, 'keyfile': None}
                 }]
             }]
        }},
        "ParameterError: Either 'password' or 'keyfile' is required in sftp block for io_adapter_update"
    ),

    # sftp io_adapter: both password and keyfile provided (mutually exclusive)
    (
        {'hmc_host': '1.2.3.4', 'hmc_auth': {'username': 'user', 'password': 'pass'}, 'system_name': 'sys', 'state': None,
         'platform_config': {
             'vios_update': [{
                 'update_type': 'NoUpdate', 'vios_name': 'vios1', 'update_order': 1,
                 'io_adapter_update': [{
                     'all': True, 'repository': 'sftp',
                     'sftp': {'hostname': 'sftp.host', 'directory': '/io', 'username': 'user', 'password': 'pass', 'keyfile': '/id_rsa'}
                 }]
             }]
        }},
        "ParameterError: Parameters 'password' and 'keyfile' are mutually exclusive in sftp block for io_adapter_update"
    ),

]

platform_config_test_data1 = [

    # VIOS update with IO adapter update (list of devices)
    (
        {
            'platform_config': {
                'vios_update': [
                    {
                        'update_type': 'Update',
                        'vios_name': 'vios2',
                        'update_order': 2,
                        'vios_image_name': 'image_name',
                        'io_adapter_update': [
                            {
                                'all': None,
                                'device': 'ent0',
                                'repository': 'IBMWebsite'
                            },
                            {
                                'all': None,
                                'device': 'ent1',
                                'repository': 'IBMWebsite'
                            }
                        ]
                    }
                ]
            }
        },
        {
            'platform_config': {
                'VIOSUpdate': [
                    {
                        'UpdateType': 'Update',
                        'VIOSName': 'vios2',
                        'UpdateOrder': 2,
                        'Name': 'image_name',
                        'IOAdapterUpdate': [
                            {
                                'Device': 'ent0',
                                'Repository': 'IBMWebsite'
                            },
                            {
                                'Device': 'ent1',
                                'Repository': 'IBMWebsite'
                            }
                        ]
                    }
                ]
            }
        }
    ),

    # Multiple VIOS update
    (
        {
            'platform_config': {
                'vios_update': [
                    {
                        'update_type': 'Update',
                        'vios_name': 'vios2',
                        'update_order': 1,
                        'vios_image_name': 'image_name',
                        'io_adapter_update': [
                            {
                                'all': None,
                                'device': ['ent0', 'ent1'],
                                'repository': 'IBMWebsite'
                            }
                        ]
                    },
                    {
                        'update_type': 'Update',
                        'vios_name': 'vios1',
                        'update_order': 2,
                        'vios_image_name': 'image_name',
                        'io_adapter_update': None
                    }
                ]
            }
        },
        {
            'platform_config': {
                'VIOSUpdate': [
                    {
                        'UpdateType': 'Update',
                        'VIOSName': 'vios2',
                        'UpdateOrder': 1,
                        'Name': 'image_name',
                        'IOAdapterUpdate': [
                            {
                                'Device': ['ent0', 'ent1'],
                                'Repository': 'IBMWebsite'
                            }
                        ]
                    },
                    {
                        'UpdateType': 'Update',
                        'VIOSName': 'vios1',
                        'UpdateOrder': 2,
                        'Name': 'image_name',
                    }
                ]
            }
        }
    ),

    # System firmware update
    (
        {
            'platform_config': {
                'system_firmware_update': {
                    'update_type': 'Update',
                    'update_order': 1,
                    'repository': 'IBMWebsite',
                    'level': 'latest',
                    'sriov_adapter_update': None
                }
            }
        },
        {
            'platform_config': {
                'SystemFirmwareUpdate': {
                    'UpdateType': 'Update',
                    'UpdateOrder': 1,
                    'Repository': 'IBMWebsite',
                    'Level': 'latest',
                }
            }
        }
    ),

    # Sriov Adapter Update
    (
        {
            'platform_config': {
                'system_firmware_update': {
                    'update_type': 'NoUpdate',
                    'update_order': 1,
                    'repository': None,
                    'level': 'latest',
                    'sriov_adapter_update': [
                        {
                            'all': None,
                            'adapter_id': '1',
                            'subtype': 'Adapter'
                        }
                    ]
                }
            }
        },
        {
            'platform_config': {
                'SystemFirmwareUpdate': {
                    'UpdateType': 'NoUpdate',
                    'UpdateOrder': 1,
                    'Level': 'latest',
                    'SRIOVAdapterUpdate': [
                        {
                            'AdapterID': '1',
                            'SubType': 'adapterdriver,adapter'
                        }
                    ]
                }
            }
        }
    ),

    # Multiple Sriov Adapter Update
    (
        {
            'platform_config': {
                'system_firmware_update': {
                    'update_type': 'NoUpdate',
                    'update_order': 1,
                    'repository': None,
                    'level': 'latest',
                    'sriov_adapter_update': [
                        {
                            'all': None,
                            'adapter_id': '1',
                            'subtype': 'Adapter'
                        },
                        {
                            'all': None,
                            'adapter_id': '2',
                            'subtype': 'DriverOnly'
                        }
                    ]
                }
            }
        },
        {
            'platform_config': {
                'SystemFirmwareUpdate': {
                    'UpdateType': 'NoUpdate',
                    'UpdateOrder': 1,
                    'Level': 'latest',
                    'SRIOVAdapterUpdate': [
                        {
                            'AdapterID': '1',
                            'SubType': 'adapterdriver,adapter'
                        },
                        {
                            'AdapterID': '2',
                            'SubType': 'adapterdriver'
                        }
                    ]
                }
            }
        }
    ),

    # Partition migration with defaults
    (
        {
            'platform_config': {
                'partition_migration': {
                    'is_quick_evac': True,
                    'destination_managed_system': 'sysA',
                    'leave_partition_in_target': False
                }
            }
        },
        {
            'platform_config': {
                'PartitionMigration': {
                    'IsQuickEvac': True,
                    'DestinationManagedSystem': 'sysA',
                    'LeavePartitionInTarget': False
                }
            }
        }
    ),

    # Mixed config: system firmware + VIOS update + partition migration
    (
        {
            'platform_config': {
                'system_firmware_update': {
                    'update_type': 'Update',
                    'update_order': 1,
                    'repository': 'IBMWebsite',
                    'level': 'FW940',
                    'SRIOVAdapterUpdate': None
                },
                'vios_update': [
                    {
                        'update_type': 'Update',
                        'vios_name': 'vios3',
                        'update_order': 1
                    }
                ],
                'partition_migration': {
                    'is_quick_evac': True,
                    'destination_managed_system': 'sysB',
                    'LeavePartitionInTarget': False
                }
            }
        },
        {
            'platform_config': {
                'SystemFirmwareUpdate': {
                    'UpdateType': 'Update',
                    'UpdateOrder': 1,
                    'Repository': 'IBMWebsite',
                    'Level': 'FW940',
                },
                'VIOSUpdate': [
                    {
                        'UpdateType': 'Update',
                        'VIOSName': 'vios3',
                        'UpdateOrder': 1
                    }
                ],
                'PartitionMigration': {
                    'IsQuickEvac': True,
                    'DestinationManagedSystem': 'sysB',
                    'LeavePartitionInTarget': False
                }
            }
        }
    ),

    # --- SFTP payload: system_firmware_update with password auth ---
    (
        {
            'platform_config': {
                'system_firmware_update': {
                    'update_type': 'Update',
                    'update_order': 1,
                    'repository': 'sftp',
                    'level': 'latest',
                    'sriov_adapter_update': None,
                    'sftp': {
                        'hostname': 'sftp.host',
                        'directory': '/fw',
                        'username': 'sftpuser',
                        'password': 'sftppass',
                        'keyfile': None,
                    }
                }
            }
        },
        {
            'platform_config': {
                'SystemFirmwareUpdate': {
                    'UpdateType': 'Update',
                    'UpdateOrder': 1,
                    'Repository': 'sftp',
                    'Level': 'latest',
                    'HostName': 'sftp.host',
                    'Directory': '/fw',
                    'UserName': 'sftpuser',
                    'Password': 'sftppass',
                }
            }
        }
    ),

    # --- SFTP payload: system_firmware_update with keyfile auth ---
    (
        {
            'platform_config': {
                'system_firmware_update': {
                    'update_type': 'Update',
                    'update_order': 1,
                    'repository': 'sftp',
                    'level': 'latest',
                    'sriov_adapter_update': None,
                    'sftp': {
                        'hostname': 'sftp.host',
                        'directory': '/fw',
                        'username': 'sftpuser',
                        'password': None,
                        'keyfile': '/home/user/.ssh/id_rsa',
                    }
                }
            }
        },
        {
            'platform_config': {
                'SystemFirmwareUpdate': {
                    'UpdateType': 'Update',
                    'UpdateOrder': 1,
                    'Repository': 'sftp',
                    'Level': 'latest',
                    'HostName': 'sftp.host',
                    'Directory': '/fw',
                    'UserName': 'sftpuser',
                    'Keyfile': '/home/user/.ssh/id_rsa',
                }
            }
        }
    ),

    # --- SFTP payload: vios_update with password auth, SaveFile injected ---
    (
        {
            'platform_config': {
                'vios_update': [{
                    'update_type': 'Update',
                    'vios_name': 'vios1',
                    'update_order': 1,
                    'resource_type': 'sftp',
                    'vios_image_name': 'pkg_name',
                    'sftp': {
                        'hostname': 'sftp.host',
                        'username': 'sftpuser',
                        'password': 'sftppass',
                        'ssh_key': None,
                        'remote_directory': '/vios',
                        'file_names': None,
                    }
                }]
            }
        },
        {
            'platform_config': {
                'VIOSUpdate': [{
                    'UpdateType': 'Update',
                    'VIOSName': 'vios1',
                    'UpdateOrder': 1,
                    'ResourceType': 'sftp',
                    'Name': 'pkg_name',
                    'ServerHostOrIP': 'sftp.host',
                    'UserName': 'sftpuser',
                    'Password': 'sftppass',
                    'RemoteDirectory': '/vios',
                    'SaveFile': True,
                }]
            }
        }
    ),

    # --- SFTP payload: vios_update with ssh_key and file_names list ---
    (
        {
            'platform_config': {
                'vios_update': [{
                    'update_type': 'Update',
                    'vios_name': 'vios1',
                    'update_order': 1,
                    'resource_type': 'sftp',
                    'vios_image_name': 'pkg_name',
                    'sftp': {
                        'hostname': 'sftp.host',
                        'username': 'sftpuser',
                        'password': None,
                        'ssh_key': '/id_rsa',
                        'remote_directory': '/vios',
                        'file_names': ['img1.tar.gz', 'img2.tar.gz'],
                    }
                }]
            }
        },
        {
            'platform_config': {
                'VIOSUpdate': [{
                    'UpdateType': 'Update',
                    'VIOSName': 'vios1',
                    'UpdateOrder': 1,
                    'ResourceType': 'sftp',
                    'Name': 'pkg_name',
                    'ServerHostOrIP': 'sftp.host',
                    'UserName': 'sftpuser',
                    'SSHKey': '/id_rsa',
                    'RemoteDirectory': '/vios',
                    'FileNames': 'img1.tar.gz,img2.tar.gz',
                    'SaveFile': True,
                }]
            }
        }
    ),

    # --- SFTP payload: io_adapter_update with password auth ---
    (
        {
            'platform_config': {
                'vios_update': [{
                    'update_type': 'NoUpdate',
                    'vios_name': 'vios1',
                    'update_order': 1,
                    'resource_type': None,
                    'io_adapter_update': [{
                        'all': True,
                        'device': None,
                        'repository': 'sftp',
                        'sftp': {
                            'hostname': 'sftp.host',
                            'directory': '/io',
                            'username': 'sftpuser',
                            'password': 'sftppass',
                            'keyfile': None,
                        }
                    }]
                }]
            }
        },
        {
            'platform_config': {
                'VIOSUpdate': [{
                    'UpdateType': 'NoUpdate',
                    'VIOSName': 'vios1',
                    'UpdateOrder': 1,
                    'IOAdapterUpdate': [{
                        'ALL': True,
                        'Repository': 'sftp',
                        'HostName': 'sftp.host',
                        'Directory': '/io',
                        'UserName': 'sftpuser',
                        'Password': 'sftppass',
                    }]
                }]
            }
        }
    ),

]


def common_mock_setup(mocker):
    hmc_platform_update = importlib.import_module(IMPORT_HMC_PLATFORM_UPDATE)
    mocker.patch.object(hmc_platform_update, 'HmcCliConnection')
    mocker.patch.object(hmc_platform_update, 'Hmc', autospec=True)
    mocker.patch.object(hmc_platform_update, 'HmcRestClient', autospec=True)
    return hmc_platform_update


@pytest.mark.parametrize("fact_test_input, expectedError", facts_test_data)
def test_call_facts(mocker, fact_test_input, expectedError):
    module = FakeModule(fact_test_input)

    hmc_module = common_mock_setup(mocker)

    with pytest.raises(Exception) as excinfo:
        hmc_module.facts(module)

    assert "ParameterError:" in str(excinfo.value)
    assert expectedError in str(excinfo.value)


@pytest.mark.parametrize("platform_config_test_input, expectedError", platform_config_test_data)
def test_call_platform_config(mocker, platform_config_test_input, expectedError):
    module = FakeModule(platform_config_test_input)

    hmc_module = common_mock_setup(mocker)

    with pytest.raises(Exception) as excinfo:
        hmc_module.platform_update(module)

    assert "ParameterError:" in str(excinfo.value)
    assert expectedError in str(excinfo.value)


@pytest.mark.parametrize("platform_config_test_input, expected", platform_config_test_data1)
def test_call_platform_config_payload(mocker, platform_config_test_input, expected):
    hmc_module = common_mock_setup(mocker)

    # Mirror the exact call order in platform_update():
    # _flatten_sftp_block → cleanup_entries → map_entries
    hmc_module._flatten_sftp_block(platform_config_test_input.get('platform_config', {}))
    cleanup_data = hmc_module.cleanup_entries(platform_config_test_input)
    result = hmc_module.map_entries(cleanup_data)
    assert result == expected
