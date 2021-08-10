# Copyright: (c) 2018- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
import xml.etree.ElementTree as ET
import json
import sys
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable
from ansible.module_utils.six import string_types, viewitems, reraise
from ansible.errors import AnsibleParserError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import parse_error_response
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_rest_client import HmcRestClient
from ansible.config.manager import ensure_type
from ansible.template import Templar

from ansible.utils.display import Display
display = Display()

# Generic setting for log initializing and log rotation
import logging
LOG_FILENAME = "/tmp/ansible_power_hmc.log"
logger = logging.getLogger(__name__)


def init_logger():
    logging.basicConfig(
        filename=LOG_FILENAME,
        format='[%(asctime)s] %(levelname)s: [%(funcName)s] %(message)s',
        level=logging.DEBUG)


__metaclass__ = type

DOCUMENTATION = '''
    name: powervm_inventory
    author:
        - Torin Reilly (@torinreilly)
        - Michael Cohoon (@mtcohoon)
        - Ozzie Rodriguez
        - Anil Vijayan
        - Navinakumar Kandakur (@nkandak1)
    plugin_type: inventory
    version_added: "1.1.0"
    requirements:
        - Python >= 3
    short_description: HMC-based inventory source for Power Systems
    description:
        - This plugin utilizes HMC APIs to build a dynamic inventory
          of defined partitions (LPAR, VIOS). Inventory sources must be structured as *.power_hmc.yml
          or *.power_hmc.yaml.
        - To create a usable Ansible host for a given LPAR, the ip or hostname
          of the LPAR must be exposed through the HMC in some way.
          Currently there are only two such sources supported by this plugin,
          either an RMC ip address(not valid for IBMi partition) or the name of the LPAR must be also a valid hostname.
        - Valid LPAR/VIOS properties that can be used for groups, keyed groups, filters, unknown partition identification,
          and composite variables can be found in the HMC REST API documentation. By default, valid properties include those
          listed as "Quick Properties", but if `advanced_fields` are enabled you may be able to use more advanced properties of the
          partition. Further information about the APIs can be found in the
          L(Knowledge Center, https://www.ibm.com/support/knowledgecenter/9040-MR9/p9ehl/apis/LogicalPartition.htm).
        - If a property is used in the inventory source that is unique to a partition type,
          only partitions for which that property is defined may be included. Non-compatible partitions can be
          filtered out by `OperatingSystemVersion` or `PartitionType` as detailed in the second example.

    options:
        hmc_hosts:
          description: A dictionary of hosts and their associated usernames and passwords.
          required: true
          type: dict
          elements: dict
        filters:
            description:
                - A key value pair for filtering by various LPAR/VIOS attributes.
                  Only results matching the filter will be included in the inventory.
            default: {}
        compose:
            description: Create vars from Jinja2 expressions.
            default: {}
            type: dict
        groups:
            description: Add hosts to group based on Jinja2 conditionals.
            default: {}
            type: dict
        keyed_groups:
            description: Add hosts to group based on the values of a variable.
            type: list
            elements: str
            default: []
        exclude_ip:
            description: A list of IP addresses to exclude from the inventory.
              This will be compared to the RMC ip address specified in the HMC.
              Currently, no hostname lookup is performed, so only ip addresses
              that match the RMC ip address specified in the HMC will be exlcuded.
              This is not valid for IBMi LPARs
            type: list
            default: []
        exclude_lpar:
            description: A list of partitions (LPAR, VIOS) to exclude by partition name.
            type: list
            default: []
        exclude_system:
            description: A list of HMC managed systems whose partitions (LPAR, VIOS)
              will be excluded from the dynamic inventory.
            type: list
            default: []
        ansible_display_name:
            description: By default, partitions names will be used as the name displayed by
              Ansible in output. If you wish this to display the ip address instead you may
              set this to "ip".
            default: "lpar_name"
            choices: [lpar_name, ip]
            type: str
        ansible_host_type:
            description: Determines if the ip address or the LPAR name will be used as
              the "ansible_host" variable in playbooks.
              This is not valid for IBMi LPARs
            default: "ip"
            choices: [lpar_name, ip]
            type: str
        advanced_fields:
            description:
                - Allows for additional LPAR/VIOS properties to be used for
                  the purposes of grouping and filtering.
                - Retrieving these properties could increase dynamic inventory generation run time,
                  depending on the size of your environment and the properties to be fetched.
            default: false
            type: bool
        group_by_managed_system:
            description: Creates a grouping of partitions by managed system name. This is enabled by default.
            default: true
            type: bool
        identify_unknown_by:
            description:
                - Allows you to include partitions unable to be automatically detected
                  as a valid Ansible target.
                - By default, Aix/Linux partitions without ip's and IBMi partitions in not running state are ommited from the inventory.
                  This is not be the case in the event you have lpar_name set for ansible_host_type.
                  If not, omitted partitions will be added to a group called "unknown"
                  and will can be identified by any LPAR property of your choosing
                  (PartitionName or UUID are common identifiers).
                - If you do not omit unknown partitions, you may run into issues
                  targetting groups that include them. To avoid this, you can specify a host pattern
                  in a playbooks such as `targetgroup:!unknown`.
                  This will your playbook to run against all known hosts in your target group.
            default: omit
            type: str
'''

EXAMPLES = '''
# The most minimal example, targetting only a single HMC
plugin: ibm.power_hmc.powervm_inventory
hmc_hosts:
  "hmc_host_name":
    user: user
    password: password

# Create an inventory consisting of only Virtual IO Servers.
# This may be important if grouping by advanced_fields exclusive to VIOS.
plugin: ibm.power_hmc.powervm_inventory
hmc_hosts:
  "hmc_host_name":
    user: user
    password: password
filters:
    PartitionType: 'Virtual IO Server'

# Target multiple HMC hosts and only add running partitions to the inventory
plugin: ibm.power_hmc.powervm_inventory
hmc_hosts:
  "hmc_host_name":
    user: user
    password: password
  "hmc_host_name2":
    user: user
    password: password
filters:
    PartitionState: 'running'

# Generate an inventory including all running partitions and also create a group allowing us to target AIX 7.2 and IBMi specifically
plugin: ibm.power_hmc.powervm_inventory
hmc_hosts:
  "hmc_host_name":
    user: user
    password: password
  "hmc_host_name2":
    user: user
    password: password
filters:
    PartitionState: 'running'
groups:
    AIX_72: "'7.2' in OperatingSystemVersion"
    IBMi: "'IBM' in OperatingSystemVersion"

# Generate an inventory of running partitions and group them by PartitionType with a prefix of type_
# Groups will be created will resemble "type_Virtual_IO_Server", "type_AIX_Linux", "type_OS400", etc.
# Additionally, include the following variables as host_vars for a given target host: CurrentMemory, OperatingSystemVersion, PartitionName
plugin: ibm.power_hmc.powervm_inventory
hmc_hosts:
  "hmc_host_name":
    user: user
    password: password
  "hmc_host_name2":
    user: user
    password: password
filters:
    PartitionState: 'running'
keyed_groups:
  - prefix: type
    key: PartitionType
compose:
  current_memory: CurrentMemory
  os: OperatingSystemVersion
  name: PartitionName

## Generate an inventory that excludes partitions by ip, name, or the name of managed system on which they run
plugin: ibm.power_hmc.powervm_inventory
hmc_hosts:
  "hmc_host_name":
    user: user
    password: password
exclude_ip:
    - 10.0.0.44
    - 10.0.0.46
exclude_lpar:
    - aixlparnameX1
    - aixlparnameX2
    - vioslparnameX1
    - vioslparnameX2
exclude_system:
    - Frame1-XXX-WWWWWW
    - Frame2-XXX-WWWWWW
'''


class LparFieldNotFoundError(Exception):
    '''Raised when a field does not exist in the LPAR data.'''


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):

    NAME = 'ibm.power_hmc.powervm_inventory'

    def __init__(self):
        super().__init__()

        self.group_prefix = 'power_hmc_'
        self.template_handle = None

    def verify_file(self, path):
        """
        Verify inventory source is valid
        """
        if super().verify_file(path):
            logger.debug("Path: %s", path)
            if path.endswith(('.power_hmc.yml', '.power_hmc.yaml')):
                return True
            raise AnsibleParserError("Path is not valid. All HMC inventory sources must have a suffix of .power_hmc.yml or .power_hmc.yaml.")

    def parse(self, inventory, loader, path, cache=True):
        """
        Parse inventory source
        """
        super().parse(inventory, loader, path, cache)

        self.template_handle = Templar(loader=loader)
        self._configure(path)
        self._populate_from_systems(self.get_lpars_by_system())

    def _populate_from_systems(self, systems):
        invalid_identify_unknown_by = False
        # Ensure there is a system defined to an HMC
        if not systems:
            raise HmcError("There are no systems defined to any valid HMCs provided or no valid connections were established.")
        for system in systems:
            for lpar in systems[system]:
                if self.lpar_should_be_included(lpar):
                    try:
                        # Lookup the IP address for LPAR
                        ip = self.get_ip(lpar)
                        lpar_name = self.get_lpar_name(lpar)

                        if self.ansible_host_type == "lpar_name":
                            hostname = lpar_name
                        else:
                            hostname = ip

                        if self.ansible_display_name == "lpar_name":
                            entry_name = lpar_name
                        else:
                            entry_name = ip
                    except LparFieldNotFoundError:
                        # If the IP address was missing, this LPAR is 'unknown' and
                        # cannot be added as a valid Ansible host.
                        partition_type = self.get_lpar_os_type(lpar)

                        if partition_type == 'OS400' and lpar['PartitionState'] == 'running' and self.ansible_display_name == "lpar_name":
                            entry_name = self.get_lpar_name(lpar)
                            hostname = entry_name
                        elif self.identify_unknown_by.lower() != 'omit':
                            value_for_unknown = self.get_value_for_unknown_lpar(lpar)
                            if value_for_unknown:
                                self.inventory.add_group('unknowns')
                                self.inventory.add_host(value_for_unknown, 'unknowns')
                            else:
                                invalid_identify_unknown_by = True
                            continue
                        else:
                            continue

                    # A valid IP address was found for this LPAR
                    if self.group_by_managed_system:
                        self.inventory.add_group(system)
                        self.inventory.add_host(entry_name, system)
                    else:
                        self.inventory.add_host(entry_name)

                    # Only add an ansible_host variable if it differs from the displayname in the inventory
                    if hostname != entry_name:
                        self.inventory.set_variable(entry_name, "ansible_host", hostname)

                    self._set_composite_vars(self.compose, lpar, entry_name, strict=True)
                    self._add_host_to_composed_groups(self.groups, lpar, entry_name, strict=True)
                    self._add_host_to_keyed_groups(self.keyed_groups, lpar, entry_name, strict=True)

        # Warn the user if the property they are using to use to identify partitions is invalid in some circumstances
        if invalid_identify_unknown_by:
            msg = ("Could not find property %s for some or all unknown partitions, as a result they will not be included." % self.identify_unknown_by)
            display.warning(msg=msg)
            logger.warning(msg)

    def get_lpars_by_system(self):
        systems = {}

        if self.template_handle.is_template(self.get_option('hmc_hosts')):
            self.hmc_hosts = self.template_handle.template(variable=self.get_option('hmc_hosts'))

        for hmc_host in self.hmc_hosts:
            try:
                rest_conn = HmcRestClient(str(hmc_host), str(self.hmc_hosts[hmc_host]["user"]), str(self.hmc_hosts[hmc_host]["password"]))
                try:
                    managed_systems = json.loads(rest_conn.getManagedSystemsQuick())
                except Exception:
                    logger.debug("Could not retrieve systems from %s it may not have any defined", hmc_host)
                    continue
                for system in managed_systems:
                    lpars = []
                    if system.get("SystemName") not in self.exclude_system:
                        # Make calls to full XML APIs which have access to a few additional fields
                        # Note: This call takes nearly 10x as long because it must reach out to each system individually
                        if self.advanced_fields:
                            try:
                                lpar_xml = rest_conn.getLogicalPartitions(system.get("UUID"))
                                system_lpars = self.parse_lpars_xml(lpar_xml)
                                lpars.extend(system_lpars)
                            except Exception:
                                logger.debug("Could not retrieve LPARs from %s it may not have any defined", system.get("SystemName"))
                            try:
                                vios_xml = rest_conn.getVirtualIOServers(system.get("UUID"))
                                system_vios = self.parse_lpars_xml(vios_xml)
                                lpars.extend(system_vios)
                            except Exception:
                                logger.debug("Could not retrieve VIOS from %s it may not have any defined", system.get("SystemName"))
                        # Call the "quick" JSON API
                        else:
                            try:
                                system_lpars = json.loads(rest_conn.getLogicalPartitionsQuick(system.get("UUID")))
                                lpars.extend(system_lpars)
                            except Exception:
                                logger.debug("Could not retrieve LPARs from %s it may not have any defined", system.get("SystemName"))
                            try:
                                system_vios = json.loads(rest_conn.getVirtualIOServersQuick(system.get("UUID")))
                                lpars.extend(system_vios)
                            except Exception:
                                logger.debug("Could not retrieve VIOS from %s it may not have any defined", system.get("SystemName"))
                        systems[system.get("SystemName")] = lpars
                # Logoff HMC
                try:
                    rest_conn.logoff()
                except Exception as del_error:
                    error_msg = parse_error_response(del_error)
                    logger.debug(error_msg)
                    traceback = sys.exc_info()[2]
                    reraise(HmcError, "Error logging off HMC REST Service: %s" % error_msg, traceback)
            except Exception as error:
                error_msg = parse_error_response(error)
                msg = ("Unable to connect to HMC host %s: %s" % (hmc_host, error_msg))
                display.warning(msg=msg)
                logger.debug(msg)
                continue
        return systems

    def parse_lpars_xml(self, xml):
        root = ET.fromstring(xml)
        feed = next(root.iter())
        entries = feed.findall("{http://www.w3.org/2005/Atom}entry")
        lpars = []
        for entry in entries:
            lpar = self.get_tag_text(entry)
            lpars.append(lpar)
        return lpars

    def _configure(self, path):
        config = self._read_config_data(path)

        args = dict(
            hmc_hosts=dict(type='dict', value=config.get("hmc_hosts", None), required=True),
            filters=dict(type='dict', value=config.get("filters", {})),
            keyed_groups=dict(type='list', value=config.get("keyed_groups", [])),
            groups=dict(type='dict', value=config.get("groups", {})),
            compose=dict(type='dict', value=config.get("compose", {})),
            exclude_ip=dict(type='list', value=config.get("exclude_ip", [])),
            exclude_lpar=dict(type='list', value=config.get("exclude_lpar", [])),
            exclude_system=dict(type='list', value=config.get("exclude_system", [])),
            ansible_display_name=dict(type='str', choices=['lpar_name', 'ip'], value=config.get("ansible_display_name", "lpar_name")),
            ansible_host_type=dict(type='str', choices=['lpar_name', 'ip'], value=config.get("ansible_host_type", "ip")),
            advanced_fields=dict(type='bool', value=config.get("advanced_fields", False)),
            group_by_managed_system=dict(type='bool', value=config.get("group_by_managed_system", True)),
            identify_unknown_by=dict(type='str', value=config.get("identify_unknown_by", "omit")),
        )

        self.validate_and_set_args(args)

    def validate_and_set_args(self, args):
        for arg in args:
            if args[arg].get("required") and args[arg].get("value") is None:
                raise AnsibleParserError("%s is required value." % (arg))
            # check type
            if args[arg]["type"] == 'str':
                type_checked_arg = ensure_type(
                    args[arg].get("value"), 'string')
                if type_checked_arg is not None and not isinstance(type_checked_arg, string_types):
                    raise AnsibleParserError("%s is expected to be a string, but got %s instead" % (
                        arg, type(type_checked_arg)))
                # Check for choices
                if "choices" in args[arg]:
                    if type_checked_arg not in args[arg]["choices"]:
                        raise AnsibleParserError("%s is not a valid option for %s. The following are valid options: %s" % (
                            type_checked_arg, arg, str(args[arg]["choices"])))
                setattr(self, arg, type_checked_arg)
            elif args[arg]["type"] == 'bool':
                if isinstance(args[arg].get("value"), bool):
                    setattr(self, arg, args[arg].get("value"))
                else:
                    raise AnsibleParserError("%s must be a boolean value. Current value is: %s" % (arg, args[arg].get("value")))
            elif args[arg]["type"] == 'list':
                if not isinstance(args[arg].get("value"), list):
                    raise AnsibleParserError("%s is currently %s and needs to be defined as a %s." % (arg, args[arg].get("value"), 'list'))
                setattr(self, arg, args[arg].get("value"))
            elif args[arg]["type"] == 'dict':
                if not isinstance(args[arg].get("value"), dict):
                    raise AnsibleParserError("%s is currently %s and needs to be defined as a %s." % (arg, args[arg].get("value"), 'dict'))
                setattr(self, arg, args[arg].get("value"))
            else:
                raise AnsibleParserError("%s is an unhandled type! This shoulddn't happen." % (args[arg]["type"]))

            # Do not allow inventory generation to contine if an argument is set to None,
            # but also do not override a more type specific message that may have been raised.
            if args[arg].get("value") is None:
                raise AnsibleParserError("%s is an optional value, but cannot be None. Please specify a value or remove it from your inventory source." % (arg))

    def get_ip(self, lpar):
        if "ResourceMonitoringIPAddress" in lpar and lpar['ResourceMonitoringIPAddress'] is not None:
            return lpar['ResourceMonitoringIPAddress']
        else:
            raise LparFieldNotFoundError("LPAR has no value for 'ResourceMonitoringIPAddress'")

    def get_lpar_name(self, lpar):
        if "PartitionName" in lpar and lpar['PartitionName'] is not None:
            return lpar['PartitionName']
        else:
            raise LparFieldNotFoundError("LPAR has no value for 'PartitionName'")

    def get_value_for_unknown_lpar(self, lpar):
        if self.identify_unknown_by in lpar:
            return lpar[self.identify_unknown_by]

    def get_lpar_os_type(self, lpar):
        return lpar["PartitionType"]

    def get_tag_text(self, e):
        lpar_data = {}
        for child in e:
            if child.text is None or child.text.strip() == "":
                lpar_data.update(self.get_tag_text(child))
            else:
                tag = child.tag.split("}")[-1]
                lpar_data[tag] = child.text
        return lpar_data

    def is_lpar_excluded(self, lpar):
        if "ResourceMonitoringIPAddress" in lpar and lpar["ResourceMonitoringIPAddress"] in self.exclude_ip:
            # LPAR excluded due to IP address
            return True
        if "PartitionName" in lpar and lpar["PartitionName"] in self.exclude_lpar:
            # LPAR excluded due to partinion name
            return True
        return False

    def matches_filters(self, lpar):
        # Our filter should be a subset of our LPAR if the LPAR matches the filter items
        return viewitems(self.filters) <= viewitems(lpar)

    def lpar_should_be_included(self, lpar):
        if self.matches_filters(lpar) and not self.is_lpar_excluded(lpar):
            return True
        return False
