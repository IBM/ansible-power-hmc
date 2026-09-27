from __future__ import absolute_import, division, print_function
__metaclass__ = type
import time
import json
from ansible.module_utils.urls import open_url
import ansible.module_utils.six.moves.urllib.error as urllib_error
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import Error
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError
import re
import xml.etree.ElementTree as ET
NEED_LXML = False
try:
    from lxml import etree, objectify
except ImportError:
    NEED_LXML = True

import logging
LOG_FILENAME = "/tmp/ansible_power_hmc.log"
logger = logging.getLogger(__name__)

PCM_TEMPLATE_NS = 'ManagedSystemPcmPreference xmlns:ManagedSystemPcmPreference="http://www.ibm.com/xmlns/systems/power/\
firmware/pcm/mc/2012_10/" xmlns="http://www.ibm.com/xmlns/systems/power/firmware/pcm/\
mc/2012_10/" xmlns:ns2="http://www.w3.org/XML/1998/namespace/k2"'
LPAR_TEMPLATE_NS = 'PartitionTemplate xmlns="http://www.ibm.com/xmlns/systems/power/\
firmware/templates/mc/2012_10/" xmlns:ns2="http://www.w3.org/XML/1998/namespace/k2"'
LPAR_NS = 'LogicalPartition xmlns:LogicalPartition="http://www.ibm.com/xmlns/\
systems/power/firmware/uom/mc/2012_10/" xmlns="http://www.ibm.com/xmlns/systems/power\
/firmware/uom/mc/2012_10/" xmlns:ns2="http://www.w3.org/XML/1998/namespace/k2"'
VIOS_NS = 'VirtualIOServer xmlns:VirtualIOServer="http://www.ibm.com/xmlns/\
systems/power/firmware/uom/mc/2012_10/" xmlns="http://www.ibm.com/xmlns/systems/power\
/firmware/uom/mc/2012_10/" xmlns:ns2="http://www.w3.org/XML/1998/namespace/k2"'
VSWITCH_NS = 'VirtualSwitch xmlns:VirtualSwitch="http://www.ibm.com/xmlns/\
systems/power/firmware/uom/mc/2012_10/" xmlns="http://www.ibm.com/xmlns/systems/power\
/firmware/uom/mc/2012_10/" xmlns:ns2="http://www.w3.org/XML/1998/namespace/k2"'
VNETWORK_NS = 'VirtualNetwork xmlns:VirtualNetwork="http://www.ibm.com/xmlns/\
systems/power/firmware/uom/mc/2012_10/" xmlns="http://www.ibm.com/xmlns/systems/power\
/firmware/uom/mc/2012_10/" xmlns:ns2="http://www.w3.org/XML/1998/namespace/k2"'
CNA_NS = 'ClientNetworkAdapter xmlns:ClientNetworkAdapter="http://www.ibm.com/xmlns/\
systems/power/firmware/uom/mc/2012_10/" xmlns="http://www.ibm.com/xmlns/systems/power\
/firmware/uom/mc/2012_10/" xmlns:ns2="http://www.w3.org/XML/1998/namespace/k2"'
NBRIDGE_NS = 'NetworkBridge xmlns:NetworkBridge="http://www.ibm.com/xmlns/\
systems/power/firmware/uom/mc/2012_10/" xmlns="http://www.ibm.com/xmlns/systems/power\
/firmware/uom/mc/2012_10/" xmlns:ns2="http://www.w3.org/XML/1998/namespace/k2"'


def xml_strip_namespace(xml_str):
    parser = etree.XMLParser(recover=True, encoding='utf-8')
    root = etree.fromstring(xml_str, parser)
    for elem in root.getiterator():
        if not hasattr(elem.tag, 'find'):
            continue
        i = elem.tag.find('}')
        if i >= 0:
            elem.tag = elem.tag[i + 1:]

    objectify.deannotate(root, cleanup_namespaces=True)
    return root


def parse_error_response(error):
    if isinstance(error, urllib_error.HTTPError):
        xml_str = error.read().decode()
        if not xml_str:
            logger.debug(error.url)
            error_msg = "HTTP Error {0}: {1}".format(error.code, error.reason)
        else:
            dom = xml_strip_namespace(xml_str)
            error_msg_l = dom.xpath("//Message")
            if error_msg_l:
                error_msg = error_msg_l[0].text
            else:
                error_msg = "Unknown http error"
    else:
        error_msg = repr(error)
    logger.debug(error_msg)
    return error_msg


def _logonPayload(user, password):
    root = ET.Element("LogonRequest")
    root.attrib = {"schemaVersion": "V1_0",
                   "xmlns": "http://www.ibm.com/xmlns/systems/power/firmware/web/mc/2012_10/",
                   "xmlns:mc": "http://www.ibm.com/xmlns/systems/power/firmware/web/mc/2012_10/"}

    ET.SubElement(root, "UserID").text = user
    ET.SubElement(root, "Password").text = password
    return ET.tostring(root)


def _jobHeader(session):

    header = {'Content-Type': 'application/vnd.ibm.powervm.web+xml; type=JobRequest',
              'Accept': 'application/atom+xml',
              'Authorization': 'Basic Og=='}
    header['X-API-Session'] = session

    return header


def _kxe_kb_schema(kxe=None, kb=None, schema=None):
    attrib = {}
    if kxe:
        attrib.update({"kxe": kxe})
    if kb:
        attrib.update({"kb": kb})
    if schema:
        attrib.update({"schemaVersion": schema})

    return attrib


def _job_parameter(parameter, parameterVal, schemaVersion="V1_0"):

    metaData = ET.Element("Metadata")
    metaData.insert(1, ET.Element("Atom"))

    jobParameter = ET.Element("JobParameter")
    jobParameter.attrib = _kxe_kb_schema(schema=schemaVersion)
    jobParameter.insert(1, metaData)
    parameterName = ET.Element("ParameterName")
    parameterName.attrib = _kxe_kb_schema("false", "ROR")
    parameterName.text = parameter
    parameterValue = ET.Element("ParameterValue")
    parameterValue.attrib = _kxe_kb_schema("false", "CUR")
    parameterValue.text = parameterVal
    jobParameter.insert(2, parameterName)
    jobParameter.insert(3, parameterValue)

    return jobParameter


def _job_RequestPayload(reqdOperation, jobParams, schemaVersion="V1_0"):
    root = ET.Element("JobRequest")
    root.attrib = {"xmlns:JobRequest": "http://www.ibm.com/xmlns/systems/power/firmware/web/mc/2012_10/",
                   "xmlns": "http://www.ibm.com/xmlns/systems/power/firmware/web/mc/2012_10/",
                   "xmlns:ns2": "http://www.w3.org/XML/1998/namespace/k2",
                   "schemaVersion": schemaVersion
                   }

    metaData = ET.Element("Metadata")
    metaData.insert(1, ET.Element("Atom"))
    root.insert(1, metaData)

    requestedOperation = ET.Element("RequestedOperation")
    requestedOperation.attrib = _kxe_kb_schema("false", "CUR", schemaVersion)
    requestedOperation.insert(1, metaData)

    index = 2
    requestedOperationTags = ['OperationName', 'GroupName', 'ProgressType']
    for each in requestedOperationTags:
        operationName = ET.Element(each)
        operationName.attrib = _kxe_kb_schema("false", "ROR")
        operationName.text = reqdOperation[each]
        requestedOperation.insert(index, operationName)
        index = index + 1

    jobParameters = ET.Element("JobParameters")
    jobParameters.attrib = _kxe_kb_schema("false", "CUR", schemaVersion)
    jobParameters.insert(1, metaData)

    index = 2
    for each in jobParams:
        jobParameters.insert(index, _job_parameter(each, jobParams[each]))
        index = index + 1

    root.insert(2, requestedOperation)
    root.insert(3, jobParameters)

    return ET.tostring(root)


def add_taggedIO_details(lpar_template_dom):
    taggedIO_payload = '''<iBMiPartitionTaggedIO kxe="false" kb="CUD" schemaVersion="V1_0">
                <Metadata>
                    <Atom/>
                </Metadata>
                <console kxe="false" kb="CUD">HMC</console>
                <operationsConsole kxe="false" kb="CUD">NONE</operationsConsole>
                <loadSource kb="CUD" kxe="false">NONE</loadSource>
                <alternateLoadSource kxe="false" kb="CUD">NONE</alternateLoadSource>
                <alternateConsole kxe="false" kb="CUD">NONE</alternateConsole>
            </iBMiPartitionTaggedIO>'''

    ioConfigurationTag = lpar_template_dom.xpath("//ioConfiguration/isUseCapturedPhysicalIOInformationEnabled")[0]
    ioConfigurationTag.addnext(etree.XML(taggedIO_payload))


def lookup_physical_io(rest_conn, server_dom, drcname):
    physical_io_list = server_dom.xpath("//AssociatedSystemIOConfiguration/IOSlots/IOSlot")
    drcname_occurences = server_dom.xpath("//AssociatedSystemIOConfiguration/IOSlots/"
                                          + "IOSlot/RelatedIOAdapter/IOAdapter/"
                                          + "DynamicReconfigurationConnectorName[contains(text(),'" + drcname + "')]")
    if len(drcname_occurences) > 1:
        occurence = 0
        for each in drcname_occurences:
            # End Charater matching, handles the case where P1-C1 and P1-C12 should not be considered same
            if each.text.endswith(drcname):
                logger.debug("End Charaters matching")
                occurence += 1
                drcname = each.text

        if occurence > 1:
            raise Error("Given location code matching with adapters from multiple drawer")
        elif occurence == 0:
            return None
    elif len(drcname_occurences) == 1:
        drcname = drcname_occurences[0].text

    for each in physical_io_list:
        each_eletree = etree.ElementTree(each)
        if drcname == each_eletree.xpath("//RelatedIOAdapter/IOAdapter/DynamicReconfigurationConnectorName")[0].text:
            return each_eletree

    return None


def add_physical_io(rest_conn, server_dom, lpar_template_dom, drcnames):
    profileioslot_payload = ''
    for drcname in drcnames:
        # find the physical io adpater details from managed system dom
        io_adapter_dom = lookup_physical_io(rest_conn, server_dom, drcname)
        if not io_adapter_dom:
            raise Error("Not able to find the matching IO Adapter on the Server")

        drc_index = io_adapter_dom.xpath("//IOAdapter/AdapterID")[0].text
        location_code = io_adapter_dom.xpath("//IOAdapter/DynamicReconfigurationConnectorName")[0].text
        logger.debug("Location_code %s", location_code)

        profileioslot_payload += '''<ProfileIOSlot schemaVersion="V1_0">
                        <Metadata>
                            <Atom/>
                        </Metadata>
                        <isAssigned kxe="false" kb="CUD">true</isAssigned>
                        <drcIndex kxe="false" kb="CUD">{0}</drcIndex>
                        <locationCode kb="CUD" kxe="false">{1}</locationCode>
                    </ProfileIOSlot>'''.format(drc_index, location_code)

    profileioslots_payload = '''<profileIOSlots kxe="false" kb="CUD" schemaVersion="V1_0">
                    <Metadata>
                        <Atom/>
                    </Metadata>
                    {0}
                  </profileIOSlots>'''.format(profileioslot_payload)
    ioConfigurationTag = lpar_template_dom.xpath("//ioConfiguration/Metadata")[0]
    ioConfigurationTag.addnext(etree.XML(profileioslots_payload))


class HmcRestClient:

    def __init__(self, hmc_ip, username, password):
        if NEED_LXML:
            raise Error("Missing prerequisite lxml package. Hint pip install lxml")
        self.hmc_ip = hmc_ip
        self.username = username
        self.password = password

        self.session = self.logon()
        logger.debug(self.session)

    def logon(self):
        header = {'Content-Type': 'application/vnd.ibm.powervm.web+xml; type=LogonRequest'}

        url = "https://{0}/rest/api/web/Logon".format(self.hmc_ip)

        resp = open_url(url,
                        headers=header,
                        method='PUT',
                        data=_logonPayload(self.username, self.password),
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=300)
        logger.debug(resp.code)

        response = resp.read()
        doc = xml_strip_namespace(response)
        session = doc.xpath('X-API-Session')[0].text
        return session

    def logoff(self):
        header = {'Content-Type': 'application/vnd.ibm.powervm.web+xml; type=LogonRequest',
                  'Authorization': 'Basic Og==',
                  'X-API-Session': self.session}
        url = "https://{0}/rest/api/web/Logon".format(self.hmc_ip)

        open_url(url,
                 headers=header,
                 method='DELETE',
                 validate_certs=False,
                 force_basic_auth=True,
                 timeout=300)

    def __enter__(self):
        """Context manager entry point - returns the connection object."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point - calls the existing logoff() method."""
        logger.debug("__exit__ called - cleaning up HMC session")
        try:
            self.logoff()
            logger.debug("HMC session successfully logged off in __exit__")
        except Exception as e:
            logger.debug("Error during logoff in __exit__: %s", repr(e))
        return False

    def fetchJobStatus(self, jobId, template=False, timeout_in_min=30):

        if template:
            url = "https://{0}/rest/api/templates/jobs/{1}".format(self.hmc_ip, jobId)
        else:
            url = "https://{0}/rest/api/uom/jobs/{1}".format(self.hmc_ip, jobId)

        header = {'X-API-Session': self.session, 'Accept': "application/atom+xml"}
        result = None

        jobStatus = ''
        timeout_counter = 0
        while True:
            time.sleep(30)
            timeout_counter += 1
            resp = open_url(url,
                            headers=header,
                            method='GET',
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=300).read()
            doc = xml_strip_namespace(resp)

            jobStatus = doc.xpath('//Status')[0].text
            logger.debug("jobStatus: %s", jobStatus)

            if jobStatus == 'COMPLETED_OK':
                logger.debug(resp)
                result = doc
                break

            if jobStatus == 'COMPLETED_WITH_ERROR':
                logger.debug("jobStatus: %s", jobStatus)
                resp_msg = None
                resp_msg = doc.xpath("//ParameterName[text()='result']/following-sibling::ParameterValue")
                if resp_msg:
                    logger.debug("debugger: %s", resp_msg[0].text)
                    raise HmcError(resp_msg[0].text.strip('\n'))
                else:
                    err_msg = "Failed: Job completed with error"
                    raise HmcError(err_msg)

            if jobStatus != 'RUNNING':
                logger.debug("jobStatus: %s", jobStatus)
                err_msg_l = doc.xpath("//ResponseException//Message")
                err_msg_l = doc.xpath("//ParameterName[text()='ExceptionText']/following-sibling::ParameterValue") if not err_msg_l else err_msg_l
                if not err_msg_l:
                    err_msg = 'Job failed.'
                else:
                    err_msg = err_msg_l[0].text
                raise HmcError(err_msg)

            if timeout_counter == timeout_in_min * 2:
                job_name = doc.xpath("//OperationName")[0].text.strip()
                logger.debug("%s job stuck in %s state. Timed out!!", job_name, jobStatus)
                raise HmcError("Job: {0} timed out!!".format(job_name))

        return result

    def getManagedSystem(self, system_name):
        url = "https://{0}/rest/api/uom/ManagedSystem/search/(SystemName=='{1}')".format(self.hmc_ip, system_name)
        header = {'X-API-Session': self.session,
                  'Accept': 'application/vnd.ibm.powervm.uom+xml; type=ManagedSystem'}
        response = open_url(url,
                            headers=header,
                            method='GET',
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=300)
        if response.code == 204:
            return None, None

        managedsystem_root = xml_strip_namespace(response.read())

        uuid = managedsystem_root.xpath("//AtomID")[0].text
        return uuid, managedsystem_root.xpath("//ManagedSystem")[0]

    def getManagementConsole(self):
        url = "https://{}/rest/api/uom/ManagementConsole".format(self.hmc_ip)
        header = {'X-API-Session': self.session,
                  'Accept': 'application/json'}
        try:
            resp = open_url(url,
                            headers=header,
                            method='GET',
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=300)
            if resp.code == 204:
                logger.error("Request failed. Response code: %d", resp.code)
                return None
            response = json.loads(resp.read())
            managementConsoleLink = response['feed']['ManagementConsoleLink']
            managementConsole_uuid = managementConsoleLink.split('/')[-1]
            return managementConsole_uuid
        except Exception as e:
            logger.error("ManagementConsole request failed: %s", str(e))
            return None

    def getManagedSystems(self):
        url = "https://{0}/rest/api/uom/ManagedSystem".format(self.hmc_ip)
        header = {'X-API-Session': self.session,
                  'Accept': 'application/vnd.ibm.powervm.uom+xml; type=ManagedSystem'}

        response = open_url(url,
                            headers=header,
                            method='GET',
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=3600)

        if response.code == 204:
            return None, None

        managedsystems_root = xml_strip_namespace(response.read())
        return managedsystems_root

    def getManagedSystemsQuick(self):
        url = "https://{0}/rest/api/uom/ManagedSystem/quick/All".format(self.hmc_ip)
        header = {'X-API-Session': self.session,
                  'Accept': '*/*'}
        resp = open_url(url,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=300)
        if resp.code != 200:
            logger.debug("Get of Managed Systems failed. Respsonse code: %d", resp.code)
            return None
        response = resp.read()
        return response

    def getManagedSystemQuick(self, system_uuid):
        url = "https://{0}/rest/api/uom/ManagedSystem/{1}/quick".format(self.hmc_ip, system_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': '*/*'}
        resp = open_url(url,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=300)
        if resp.code != 200:
            logger.debug("Get of Logical Partition failed. Respsonse code: %d", resp.code)
            return None
        response = resp.read()
        return response

    def getLogicalPartition(self, system_uuid, partition_name=None, partition_uuid=None):
        lpar_uuid = None
        if partition_uuid is None:
            lpar_quick_list = []
            lpar_response = self.getLogicalPartitionsQuick(system_uuid)
            if lpar_response:
                lpar_quick_list = json.loads(lpar_response)

            if lpar_quick_list:
                for eachLpar in lpar_quick_list:
                    if eachLpar['PartitionName'] == partition_name:
                        lpar_uuid = eachLpar['UUID']
                        break

            if not lpar_uuid:
                return None, None
        else:
            lpar_uuid = partition_uuid

        url = "https://{0}/rest/api/uom/LogicalPartition/{1}".format(self.hmc_ip, lpar_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': 'application/vnd.ibm.powervm.uom+xml; type=LogicalPartition'}

        resp = open_url(url,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=300)
        if resp.code != 200:
            logger.debug("Get of Logical Partition failed. Respsonse code: %d", resp.code)
            return None, None

        response = resp.read()
        partition_dom = xml_strip_namespace(response)
        if partition_dom:
            return lpar_uuid, partition_dom

        return None, None

    def getLogicalPartitions(self, system_uuid):
        url = "https://{0}/rest/api/uom/ManagedSystem/{1}/LogicalPartition?group=Advanced".format(self.hmc_ip, system_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': 'application/vnd.ibm.powervm.uom+xml; type=LogicalPartition'}
        resp = open_url(url,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=3600)
        if resp.code != 200:
            logger.debug("Get of Logical Partitions failed. Respsonse code: %d", resp.code)
            return None
        response = resp.read()
        return response

    def getLogicalPartitionsQuick(self, system_uuid):
        url = "https://{0}/rest/api/uom/ManagedSystem/{1}/LogicalPartition/quick/All".format(self.hmc_ip, system_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': '*/*'}
        resp = open_url(url,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=300)
        if resp.code != 200:
            logger.debug("Get of Logical Partitions failed. Respsonse code: %d", resp.code)
            return None
        response = resp.read()
        return response

    def getLogicalPartitionQuick(self, partition_uuid):
        url = "https://{0}/rest/api/uom/LogicalPartition/{1}/quick".format(self.hmc_ip, partition_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': '*/*'}
        resp = open_url(url,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=300)
        if resp.code != 200:
            logger.debug("Get of Logical Partition failed. Respsonse code: %d", resp.code)
            return None
        response = resp.read()
        return response

    def get_request(self, url):
        try:
            header = {
                'X-API-Session': self.session,
                'Accept': '*/*'
            }
            resp = open_url(url,
                            headers=header,
                            method='GET',
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=300)
            if resp.code != 200:
                logger.debug("Request failed with response code: %s", resp.code)
                return None
            response = resp.read()
            dom = xml_strip_namespace(response)
            return dom
        except Exception as e:
            logger.debug("Error making GET request to %s: %s", url, str(e))
            return None

    def partition_fetch_virtualnetwrok_info(self, system_uuid, partition_name=None, partition_uuid=None):
        network_info_list = []
        lpar_uuid, partition_dom = self.getLogicalPartition(system_uuid, partition_uuid=partition_uuid)
        client_adapter_links = partition_dom.findall('.//ClientNetworkAdapters/link')
        if client_adapter_links:
            for link in client_adapter_links:
                try:
                    adapter_href = link.get('href')
                    adapter_dom = self.get_request(adapter_href)
                    if not adapter_dom:
                        continue
                    mac_addr_nodes = adapter_dom.xpath(".//MACAddress")
                    slot_number_nodes = adapter_dom.xpath(".//VirtualSlotNumber")
                    port_vlanid_nodes = adapter_dom.xpath(".//PortVLANID")
                    switch_name_nodes = adapter_dom.xpath(".//VirtualSwitchName")
                    if not mac_addr_nodes or not slot_number_nodes or not port_vlanid_nodes or not switch_name_nodes:
                        continue
                    mac_addr = mac_addr_nodes[0].text
                    slot_number = slot_number_nodes[0].text
                    port_vlanid = port_vlanid_nodes[0].text
                    virtual_swtich_name = switch_name_nodes[0].text
                    adapter_links = adapter_dom.findall('.//VirtualNetworks/link')
                    if not adapter_links:
                        continue
                    url = adapter_links[0].get('href')
                    network_dom = self.get_request(url)
                    if not network_dom:
                        continue
                    network_name_nodes = network_dom.xpath(".//NetworkName")
                    if not network_name_nodes:
                        continue
                    network_name = network_name_nodes[0].text
                    network_info_list.append({
                        'virtual_network_name': network_name,
                        'mac_address': mac_addr,
                        'slot_number': slot_number,
                        'port_vlan_id': port_vlanid,
                        'switch_name': virtual_swtich_name
                    })
                except Exception as e:
                    logger.debug("Error processing adapter: %s", str(e))
                    continue
        return {"VirtualNetworkAdapters": network_info_list}

    def getSystemPCMpreferences(self, system_uuid):
        url = "https://{0}/rest/api/pcm/ManagedSystem/{1}/preferences".format(self.hmc_ip, system_uuid)
        header = {'X-API-Session': self.session,
                  'Content-Type': 'application/xml'}
        resp = open_url(url,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=3600)
        if resp.code != 200:
            logger.debug("Get of preferences failed. Respsonse code: %d", resp.code)
            return None
        response = resp.read()
        return response

    def getPCM(self, system_uuid, action):
        preference_map = {'LTM': 'LongTermMonitorEnabled', 'STM': 'ShortTermMonitorEnabled',
                          'AM': 'AggregationEnabled', 'CLTM': 'ComputeLTMEnabled', 'EM': 'EnergyMonitorEnabled'}
        url = "https://{0}/rest/api/pcm/ManagedSystem/{1}/preferences".format(self.hmc_ip, system_uuid)
        header = {'X-API-Session': self.session,
                  'Content-Type': 'application/xml'}
        resp = open_url(url,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=3600)
        if resp.code != 200:
            logger.debug("Get of preferences failed. Respsonse code: %d", resp.code)
            return None
        response = resp.read()
        if action is not None:
            doc = xml_strip_namespace(response)
            path = doc.xpath("//ManagedSystemPcmPreference")[0]
            output = dict()
            for item in preference_map:
                if (path.xpath(preference_map[item])[0].text == "true"):
                    value = "Enabled"
                else:
                    value = "Disabled"
                output[preference_map[item]] = value
            return output
        return response

    def updatePCM(self, system_uuid, metrics, disable):
        url = "https://{0}/rest/api/pcm/ManagedSystem/{1}/preferences".format(self.hmc_ip, system_uuid)
        header = {'Content-Type': 'application/xml',
                  'X-API-Session': self.session}
        sys_details = self.getPCM(system_uuid, None)
        doc = xml_strip_namespace(sys_details)
        preference_map = {'LTM': 'LongTermMonitorEnabled', 'STM': 'ShortTermMonitorEnabled',
                          'AM': 'AggregationEnabled', 'CLTM': 'ComputeLTMEnabled', 'EM': 'EnergyMonitorEnabled'}
        existing_enabled = []
        existing_disabled = []
        flag = False
        path = doc.xpath("//ManagedSystemPcmPreference")[0]
        for item in preference_map:
            if path.xpath(preference_map[item])[0].text == "true":
                existing_enabled.append(item)
            elif path.xpath(preference_map[item])[0].text == "false":
                existing_disabled.append(item)
        if disable == 'true':
            # LTM and CM is dependent on AM"
            if ("LTM" in metrics or "EM" in metrics) and "AM" not in metrics:
                metrics.append("AM")
            preference = list(set(metrics) | set(existing_disabled))
            if (set(existing_disabled) != set(preference) and (set(preference).issubset(set(existing_disabled)) is False)):
                flag = True
                for item in preference:
                    path.xpath(preference_map[item])[0].text = "false"
        else:
            if "AM" in metrics and ("LTM" not in metrics or "EM" not in metrics):
                metrics.append("LTM")
                metrics.append("EM")
            preference = list(set(metrics) | set(existing_enabled))
            if (set(existing_enabled) != set(preference) and (set(preference).issubset(set(existing_enabled)) is False)):
                flag = True
                for item in preference:
                    path.xpath(preference_map[item])[0].text = "true"
        if flag is True:
            payload_content = etree.tostring(path)
            payload_content = payload_content.decode("utf-8").replace("ManagedSystemPcmPreference", PCM_TEMPLATE_NS, 1)
            payload_content = payload_content.replace('\n', ' ').replace('\"', '\'')
            payload_content = etree.fromstring(payload_content)
            payload_content = etree.tostring(payload_content, encoding='unicode')
            resp = open_url(url,
                            headers=header,
                            method='POST',
                            data=payload_content,
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=3600)
            if resp.code != 200:
                logger.debug("Get of preferences failed. Respsonse code: %d", resp.code)
                return None
            else:
                # response = resp.read()
                output = dict()
                for item in preference_map:
                    if (path.xpath(preference_map[item])[0].text == "true"):
                        value = "Enabled"
                    else:
                        value = "Disabled"
                    output[preference_map[item]] = value
                return output

    def getVirtualIOServers(self, system_uuid, group='Advanced'):
        url = "https://{0}/rest/api/uom/ManagedSystem/{1}/VirtualIOServer?group={2}".format(self.hmc_ip, system_uuid, group)
        header = {'X-API-Session': self.session,
                  'Accept': 'application/vnd.ibm.powervm.uom+xml; type=VirtualIOServer'}
        resp = open_url(url,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=3600)
        if resp.code != 200:
            logger.debug("Get of Virtual IO Servers failed. Respsonse code: %d", resp.code)
            return None
        response = resp.read()
        return response

    def getVirtualIOServersQuick(self, system_uuid):
        url = "https://{0}/rest/api/uom/ManagedSystem/{1}/VirtualIOServer/quick/All".format(self.hmc_ip, system_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': '*/*'}
        resp = open_url(url,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=300)
        if resp.code != 200:
            logger.debug("Get of Virtual IO Servers failed. Respsonse code: %d", resp.code)
            return None
        response = resp.read()
        return response

    def getVirtualIOServer(self, vios_uuid, group=None):
        header = {'X-API-Session': self.session,
                  'Accept': 'application/vnd.ibm.powervm.uom+xml; type=VirtualIOServer'}

        if group:
            url = "https://{0}/rest/api/uom/VirtualIOServer/{1}?group={2}".format(self.hmc_ip, vios_uuid, group)
        else:
            url = "https://{0}/rest/api/uom/VirtualIOServer/{1}".format(self.hmc_ip, vios_uuid)

        resp = open_url(url,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=3600)

        if resp.code != 200:
            logger.debug("Get of Virtual IO Server failed. Respsonse code: %d", resp.code)
            return None
        response = xml_strip_namespace(resp.read())
        return response

    def deleteLogicalPartition(self, partition_uuid):
        url = "https://{0}/rest/api/uom/LogicalPartition/{1}".format(self.hmc_ip, partition_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': 'application/vnd.ibm.powervm.uom+xml; type=LogicalPartition'}

        open_url(url,
                 headers=header,
                 method='DELETE',
                 validate_certs=False,
                 force_basic_auth=True,
                 timeout=300)

    def updateLparNameAndIDToDom(self, template_xml, config_dict):
        if 'lpar_id' in config_dict:
            template_xml.xpath("//partitionId")[0].text = config_dict['lpar_id']
        else:
            lpar_id_tag = template_xml.xpath("//partitionId")[0]
            lpar_id_tag.getparent().remove(lpar_id_tag)
        template_xml.xpath("//currMaxVirtualIOSlots")[0].text = config_dict['max_virtual_slots']
        template_xml.xpath("//partitionName")[0].text = config_dict['vm_name']

    def updateProcMemSettingsToDom(self, template_xml, config_dict):
        shared_config_tag = None
        # shared processor configuration
        if config_dict['proc_unit']:
            shared_payload = '''<sharedProcessorConfiguration kxe="false" kb="CUD" schemaVersion="V1_0">
                <Metadata>
                    <Atom/>
                </Metadata>
                <sharedProcessorPoolId kxe="false" kb="CUD">{7}</sharedProcessorPoolId>
                <uncappedWeight kxe="false" kb="CUD">{0}</uncappedWeight>
                <minProcessingUnits kb="CUD" kxe="false">{1}</minProcessingUnits>
                <desiredProcessingUnits kxe="false" kb="CUD">{2}</desiredProcessingUnits>
                <maxProcessingUnits kb="CUD" kxe="false">{3}</maxProcessingUnits>
                <minVirtualProcessors kb="CUD" kxe="false">{4}</minVirtualProcessors>
                <desiredVirtualProcessors kxe="false" kb="CUD">{5}</desiredVirtualProcessors>
                <maxVirtualProcessors kxe="false" kb="CUD">{6}</maxVirtualProcessors>
                </sharedProcessorConfiguration>'''.format(config_dict['weight'], config_dict['min_proc_unit'],
                                                          config_dict['proc_unit'], config_dict['max_proc_unit'],
                                                          config_dict['min_proc'], config_dict['proc'],
                                                          config_dict['max_proc'], config_dict['shared_proc_pool'])

            shared_config_tag = template_xml.xpath("//sharedProcessorConfiguration")[0]
            if shared_config_tag:
                shared_config_tag.getparent().remove(shared_config_tag)
            sharingMode_tag = template_xml.xpath("//sharingMode")[0]
            sharingMode_tag.addnext(etree.XML(shared_payload))

            dedi_tag = template_xml.xpath("//dedicatedProcessorConfiguration")[0]
            if dedi_tag:
                dedi_tag.getparent().remove(dedi_tag)

            template_xml.xpath("//currHasDedicatedProcessors")[0].text = 'false'
            template_xml.xpath("//currSharingMode")[0].text = config_dict['proc_mode']
        else:
            template_xml.xpath("//minProcessors")[0].text = config_dict['min_proc']
            template_xml.xpath("//desiredProcessors")[0].text = config_dict['proc']
            template_xml.xpath("//maxProcessors")[0].text = config_dict['max_proc']

        template_xml.xpath("//currMinMemory")[0].text = config_dict['min_mem']
        template_xml.xpath("//currMemory")[0].text = config_dict['mem']
        template_xml.xpath("//currMaxMemory")[0].text = config_dict['max_mem']
        if config_dict['proc_comp_mode']:
            template_xml.xpath("//currProcessorCompatibilityMode")[0].text = config_dict['proc_comp_mode']

    def updatePartitionTemplate(self, uuid, template_xml):
        templateUrl = "https://{0}/rest/api/templates/PartitionTemplate/{1}".format(self.hmc_ip, uuid)
        header = {'X-API-Session': self.session,
                  'Content-Type': 'application/vnd.ibm.powervm.templates+xml;type=PartitionTemplate'}

        partiton_template_xmlstr = etree.tostring(template_xml)
        partiton_template_xmlstr = partiton_template_xmlstr.decode("utf-8").replace("PartitionTemplate", LPAR_TEMPLATE_NS, 1)
        logger.debug(partiton_template_xmlstr)

        resp = open_url(templateUrl,
                        headers=header,
                        data=partiton_template_xmlstr,
                        method='POST',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=300).read()
        logger.debug(resp.decode("utf-8"))

    def quickGetPartition(self, lpar_uuid):
        header = {'X-API-Session': self.session}
        url = "https://{0}/rest/api/uom/LogicalPartition/{1}/quick".format(self.hmc_ip, lpar_uuid)
        resp = open_url(url,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=300)

        lpar_quick_dom = resp.read()
        lpar_dict = json.loads(lpar_quick_dom)
        return lpar_dict

    def getPartitionTemplateUUID(self, name):
        header = {'X-API-Session': self.session}
        url = "https://{0}/rest/api/templates/PartitionTemplate?draft=false&detail=table".format(self.hmc_ip)

        resp = open_url(url,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=300)
        if resp.code == 200:
            response = resp.read()
        else:
            return None

        root = xml_strip_namespace(response)
        element = root.xpath("//partitionTemplateName[text()='{0}']/preceding-sibling::Metadata//AtomID".format(name))
        uuid = element[0].text if element else None
        return uuid

    def getPartitionTemplate(self, uuid=None, name=None):
        logger.debug("Get partition template...")
        header = {'X-API-Session': self.session}

        if name:
            uuid = self.getPartitionTemplateUUID(name)

        if not uuid:
            return None

        templateUrl = "https://{0}/rest/api/templates/PartitionTemplate/{1}".format(self.hmc_ip, uuid)
        logger.debug(templateUrl)
        resp = open_url(templateUrl,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=300)
        if resp.code == 200:
            response = resp.read()
        else:
            return None

        partiton_template_root = xml_strip_namespace(response)
        return partiton_template_root.xpath("//PartitionTemplate")[0]

    def copyPartitionTemplate(self, from_name, to_name):
        header = {'X-API-Session': self.session,
                  'Content-Type': 'application/vnd.ibm.powervm.templates+xml;type=PartitionTemplate'}

        partiton_template_doc = self.getPartitionTemplate(name=from_name)
        if not partiton_template_doc:
            raise HmcError("Not able to fetch the template")
        partiton_template_doc.xpath("//partitionTemplateName")[0].text = to_name
        templateNamespace = 'PartitionTemplate xmlns="http://www.ibm.com/xmlns/systems/power/firmware/templates/mc/2012_10/" \
                             xmlns:ns2="http://www.w3.org/XML/1998/namespace/k2"'
        partiton_template_xmlstr = etree.tostring(partiton_template_doc)
        partiton_template_xmlstr = partiton_template_xmlstr.decode("utf-8").replace("PartitionTemplate", templateNamespace, 1)

        templateUrl = "https://{0}/rest/api/templates/PartitionTemplate".format(self.hmc_ip)
        resp = open_url(templateUrl,
                        headers=header,
                        data=partiton_template_xmlstr,
                        method='PUT',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=300)
        # This is to handle the case of unauthorized access, instead of getting error http code seems to be 200
        response = resp.read()
        response_dom = xml_strip_namespace(response)
        error_msg_l = response_dom.xpath("//Message")
        if error_msg_l:
            error_msg = error_msg_l[0].text
            raise HmcError(error_msg)

    def deletePartitionTemplate(self, template_name):
        logger.debug("Delete partition template...")
        header = {'X-API-Session': self.session,
                  'Accept': 'application/vnd.ibm.powervm.web+xml'}

        partiton_template_doc = self.getPartitionTemplate(name=template_name)
        if not partiton_template_doc:
            raise HmcError("Not able to fetch the partition template")
        template_uuid = partiton_template_doc.xpath("//AtomID")[0].text

        templateUrl = "https://{0}/rest/api/templates/PartitionTemplate/{1}".format(self.hmc_ip, template_uuid)
        logger.debug(templateUrl)
        open_url(templateUrl,
                 headers=header,
                 method='DELETE',
                 validate_certs=False,
                 force_basic_auth=True,
                 timeout=300)

    def checkPartitionTemplate(self, template_name, cec_uuid):
        header = _jobHeader(self.session)

        partiton_template_doc = self.getPartitionTemplate(name=template_name)
        if not partiton_template_doc:
            raise HmcError("Not able to fetch the partition template")
        template_uuid = partiton_template_doc.xpath("//AtomID")[0].text
        check_url = "https://{0}/rest/api/templates/PartitionTemplate/{1}/do/check".format(self.hmc_ip, template_uuid)

        reqdOperation = {'OperationName': 'Check',
                         'GroupName': 'PartitionTemplate',
                         'ProgressType': 'DISCRETE'}

        jobParams = {'K_X_API_SESSION_MEMENTO': self.session,
                     'TargetUuid': cec_uuid}

        payload = _job_RequestPayload(reqdOperation, jobParams)
        resp = open_url(check_url,
                        headers=header,
                        data=payload,
                        method='PUT',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=300).read()

        checkjob_resp = xml_strip_namespace(resp)

        jobID = checkjob_resp.xpath('//JobID')[0].text

        return self.fetchJobStatus(jobID, template=True)

    def deployPartitionTemplate(self, draft_uuid, cec_uuid):

        url = "https://{0}/rest/api/templates/PartitionTemplate/{1}/do/deploy".format(self.hmc_ip, draft_uuid)

        header = _jobHeader(self.session)

        reqdOperation = {'OperationName': 'Deploy',
                         'GroupName': 'PartitionTemplate',
                         'ProgressType': 'DISCRETE'}

        jobParams = {'K_X_API_SESSION_MEMENTO': self.session,
                     'TargetUuid': cec_uuid}

        payload = _job_RequestPayload(reqdOperation, jobParams)
        resp = open_url(url,
                        headers=header,
                        data=payload,
                        method='PUT',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=300).read()

        deploy_resp = xml_strip_namespace(resp)
        jobID = deploy_resp.xpath('//JobID')[0].text
        return self.fetchJobStatus(jobID, template=True)

    def transformPartitionTemplate(self, draft_uuid, cec_uuid):

        url = "https://{0}/rest/api/templates/PartitionTemplate/{1}/do/transform".format(self.hmc_ip, draft_uuid)
        header = _jobHeader(self.session)

        reqdOperation = {'OperationName': 'Transform',
                         'GroupName': 'PartitionTemplate',
                         'ProgressType': 'DISCRETE'}

        jobParams = {'K_X_API_SESSION_MEMENTO': self.session,
                     'TargetUuid': cec_uuid}

        payload = _job_RequestPayload(reqdOperation, jobParams)

        resp = open_url(url,
                        headers=header,
                        data=payload,
                        method='PUT',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=300).read()

        transform_resp = xml_strip_namespace(resp)
        jobID = transform_resp.xpath('//JobID')[0].text
        return self.fetchJobStatus(jobID, template=True)

    def poweroffPartition(self, vm_uuid, restart, shutdown_option):
        url = "https://{0}/rest/api/uom/LogicalPartition/{1}/do/PowerOff".format(self.hmc_ip, vm_uuid)
        header = _jobHeader(self.session)

        reqdOperation = {'OperationName': 'PowerOff',
                         'GroupName': 'LogicalPartition',
                         'ProgressType': 'DISCRETE'}
        immediate = 'false'
        operation = 'shutdown'

        if shutdown_option == 'Delayed':
            immediate = 'false'
            operation = 'shutdown'
        elif shutdown_option == 'Immediate':
            immediate = 'true'
            operation = 'shutdown'
        elif shutdown_option == 'OperatingSystem':
            immediate = 'false'
            operation = 'osshutdown'
        elif shutdown_option == 'OSImmediate':
            immediate = 'true'
            operation = 'osshutdown'
        elif shutdown_option == 'Dump':
            immediate = 'false'
            operation = 'dumprestart'
            restart = 'false'
        elif shutdown_option == 'DumpRetry':
            immediate = 'false'
            operation = 'retrydump'
            restart = 'false'

        jobParams = {'immediate': immediate,
                     'restart': restart,
                     'operation': operation}

        payload = _job_RequestPayload(reqdOperation, jobParams)

        resp = open_url(url,
                        headers=header,
                        data=payload,
                        method='PUT',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=300).read()

        shutdown_resp = xml_strip_namespace(resp)
        jobID = shutdown_resp.xpath('//JobID')[0].text
        return self.fetchJobStatus(jobID, timeout_in_min=10)

    def poweronPartition(self, vm_uuid, prof_uuid, keylock, iIPLsource, os_type):
        url = "https://{0}/rest/api/uom/LogicalPartition/{1}/do/PowerOn".format(self.hmc_ip, vm_uuid)
        header = _jobHeader(self.session)

        reqdOperation = {'OperationName': 'PowerOn',
                         'GroupName': 'LogicalPartition',
                         'ProgressType': 'DISCRETE'}

        jobParams = {'force': 'false',
                     'novsi': 'true',
                     'bootmode': 'norm'}

        if prof_uuid:
            jobParams.update({'LogicalPartitionProfile': prof_uuid})

        if keylock:
            if keylock == 'normal':
                keylock = 'norm'
            jobParams.update({'keylock': keylock})

        if os_type == 'OS400' and iIPLsource:
            jobParams.update({'iIPLsource': iIPLsource})

        payload = _job_RequestPayload(reqdOperation, jobParams)

        resp = open_url(url,
                        headers=header,
                        data=payload,
                        method='PUT',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=300).read()

        activate_resp = xml_strip_namespace(resp)
        jobID = activate_resp.xpath('//JobID')[0].text
        return self.fetchJobStatus(jobID, timeout_in_min=10)

    def getPartitionProfiles(self, vm_uuid):
        url = "https://{0}/rest/api/uom/LogicalPartition/{1}/LogicalPartitionProfile".format(self.hmc_ip, vm_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': 'application/vnd.ibm.powervm.uom+xml; type=LogicalPartitionProfile'}

        response = open_url(url,
                            headers=header,
                            method='GET',
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=300)

        if response.code == 204:
            return None

        lparProfiles_root = xml_strip_namespace(response.read())
        lparProfiles = lparProfiles_root.xpath('//LogicalPartitionProfile')
        return lparProfiles

    def add_vscsi_payload(self, pv_tup, vtd_name=''):
        payload = ''
        pv_tup_list_slice = pv_tup[:2]
        for pv_name, vios_name, pv_obj in pv_tup_list_slice:
            payload += '''
            <VirtualSCSIClientAdapter schemaVersion="V1_0">
                    <Metadata>
                            <Atom/>
                    </Metadata>
                    <PhyscalVolumeVTDName kb="CUD" kxe="false">{2}</PhyscalVolumeVTDName>
                    <associatedLogicalUnits kb="CUD" kxe="false" schemaVersion="V1_0">
                            <Metadata>
                                    <Atom/>
                            </Metadata>
                    </associatedLogicalUnits>
                    <associatedPhysicalVolume kb="CUD" kxe="false" schemaVersion="V1_0">
                            <Metadata>
                                    <Atom/>
                            </Metadata>
                            <PhysicalVolume schemaVersion="V1_0">
                                    <Metadata>
                                            <Atom/>
                                    </Metadata>
                                    <name kb="CUD" kxe="false">{0}</name>
                            </PhysicalVolume>
                    </associatedPhysicalVolume>
                    <connectingPartitionName kxe="false" kb="CUD">{1}</connectingPartitionName>
                    <AssociatedTargetDevices kb="CUD" kxe="false" schemaVersion="V1_0">
                            <Metadata>
                                    <Atom/>
                            </Metadata>
                    </AssociatedTargetDevices>
                    <associatedVirtualOpticalMedia kb="CUD" kxe="false" schemaVersion="V1_0">
                            <Metadata>
                                    <Atom/>
                            </Metadata>
                    </associatedVirtualOpticalMedia>
            </VirtualSCSIClientAdapter>'''.format(pv_name, vios_name, vtd_name)
        return payload

    def add_vscsi(self, lpar_template_dom, vscsi_clients):
        vscsi_client_payload = '''
        <virtualSCSIClientAdapters kxe="false" kb="CUD" schemaVersion="V1_0">
        <Metadata>
                <Atom/>
        </Metadata>
        {0}
        </virtualSCSIClientAdapters>'''.format(vscsi_clients)
        suspendEnableTag = lpar_template_dom.xpath("//suspendEnable")[0]
        suspendEnableTag.addprevious(etree.XML(vscsi_client_payload))

    def getFreePhyVolume(self, vios_uuid):
        logger.debug(vios_uuid)
        url = "https://{0}/rest/api/uom/VirtualIOServer/{1}/do/GetFreePhysicalVolumes".format(self.hmc_ip, vios_uuid)
        header = _jobHeader(self.session)

        reqdOperation = {'OperationName': 'GetFreePhysicalVolumes',
                         'GroupName': 'VirtualIOServer',
                         'ProgressType': 'DISCRETE'}
        jobParams = {}

        payload = _job_RequestPayload(reqdOperation, jobParams, "V1_3_0")

        resp = open_url(url,
                        headers=header,
                        data=payload,
                        method='PUT',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=300).read()

        resp = xml_strip_namespace(resp)
        jobID = resp.xpath('//JobID')[0].text

        pv_resp = self.fetchJobStatus(jobID)
        logger.debug("Free Physical Volume job response")
        logger.debug(pv_resp)
        pv_xml = pv_resp.xpath("//Results//ParameterName[text()='result']//following-sibling::ParameterValue")[0].text
        pv_xml = pv_xml.encode()
        resp = xml_strip_namespace(pv_xml)
        list_pv_elem = resp.xpath("//PhysicalVolume")
        return list_pv_elem

    def getVirtualNetworksQuick(self, system_uuid):
        url = "https://{0}/rest/api/uom/ManagedSystem/{1}/VirtualNetwork/quick/All".format(self.hmc_ip, system_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': '*/*'}
        resp = open_url(url,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=300)
        if resp.code != 200:
            logger.debug("Get of Logical Partitions failed. Respsonse code: %d", resp.code)
            return None
        response = resp.read()
        vnw_quick_list = json.loads(response)
        return vnw_quick_list

    def updateVirtualNWSettingsToDom(self, template_xml, config_dict_list):
        vn_payload = ''
        for each_vn in config_dict_list:
            vsn_payload = ''
            if each_vn['virtual_slot_number'] is not None:
                vsn_payload = '''
                <VirtualSlotNumber kb="CUD" kxe="false">{0}</VirtualSlotNumber>'''.format(each_vn['virtual_slot_number'])
            vn_payload += '''
            <ClientNetworkAdapter schemaVersion="V1_0">
                <Metadata>
                    <Atom/>
                </Metadata>
                {2}
                <clientVirtualNetworks kb="CUD" kxe="false" schemaVersion="V1_0">
                    <Metadata>
                        <Atom/>
                    </Metadata>
                    <ClientVirtualNetwork schemaVersion="V1_0">
                        <Metadata>
                            <Atom/>
                        </Metadata>
                        <name kxe="false" kb="CUD">{0}</name>
                        <uuid kb="CUD" kxe="false">{1}</uuid>
                    </ClientVirtualNetwork>
                </clientVirtualNetworks>
            </ClientNetworkAdapter>'''.format(each_vn['nw_name'], each_vn['nw_uuid'], vsn_payload)

        vnw_payload = '''
        <clientNetworkAdapters kb="CUD" kxe="false" schemaVersion="V1_0">
            <Metadata>
                <Atom/>
            </Metadata>
            {0}
        </clientNetworkAdapters>'''.format(vn_payload)

        vnw_payload_xml = etree.XML(vnw_payload)
        client_nw_adapter_tag = template_xml.xpath("//ioConfiguration")[0]
        client_nw_adapter_tag.addnext(vnw_payload_xml)

    def vios_fetch_fcports_info(self, viosuuid):
        vios_dom = self.getVirtualIOServer(viosuuid)
        phys_fc_ports = vios_dom.xpath("//PhysicalFibreChannelPort")
        fc_ports = []
        available_ports = None
        for each in phys_fc_ports:
            # check if <AvailablePorts> is present for respective fc adapter
            available_ports = each.xpath("AvailablePorts")
            if not available_ports:
                logger.debug("Skipping since not NPIV capable")
                continue
            fcport = {}
            fcport['LocationCode'] = each.xpath("LocationCode")[0].text
            fcport['PortName'] = each.xpath("PortName")[0].text
            fc_ports.append(fcport)
        return fc_ports

    def updateFCSettingsToDom(self, lpar_template_dom, config_list):
        fc_client_adapter = None
        fc_clients = ''
        for fc in config_list:
            fc_client_adapter = '''<VirtualFibreChannelClientAdapter schemaVersion="V1_0">
                <Metadata>
                    <Atom/>
                </Metadata>
                <locationCode kb="CUD" kxe="false">{0}</locationCode>
                <connectingPartitionName kb="CUD" kxe="false">{1}</connectingPartitionName>
                <portName kb="CUD" kxe="false">{2}</portName>
            </VirtualFibreChannelClientAdapter>'''.format(fc['LocationCode'], fc['viosname'], fc['PortName'])

            fc_client_adpt_dom = etree.XML(fc_client_adapter)
            if 'wwpn_pair' in fc:
                wwpn_str = ' '.join(fc['wwpn_pair'].split(';'))
                wwpn_xml = '<wwpns kb="CUD" kxe="false">{0}</wwpns>'.format(wwpn_str)
                fc_client_adpt_dom.xpath("//locationCode")[0].addnext(etree.XML(wwpn_xml))
            if 'client_adapter_id' in fc:
                caid_str = fc['client_adapter_id']
                caid_xml = '<VirtualSlotNumber kb="CUD" kxe="false">{0}</VirtualSlotNumber>'.format(caid_str)
                fc_client_adpt_dom.xpath("//locationCode")[0].addprevious(etree.XML(caid_xml))
            if 'server_adapter_id' in fc:
                said_str = fc['server_adapter_id']
                said_xml = '<remoteAdapterID kb="CUD" kxe="false">{0}</remoteAdapterID>'.format(said_str)
                fc_client_adpt_dom.xpath("//connectingPartitionName")[0].addnext(etree.XML(said_xml))

            fc_clients += ET.tostring(fc_client_adpt_dom).decode("utf-8")

        virtualFibreChannelClientAdapters = '''<virtualFibreChannelClientAdapters kb="CUD" kxe="false" schemaVersion="V1_0">
            <Metadata>
                <Atom/>
            </Metadata>
            {0}
            </virtualFibreChannelClientAdapters>'''.format(fc_clients)

        suspendEnableTag = lpar_template_dom.xpath("//suspendEnable")[0]
        suspendEnableTag.addprevious(etree.XML(virtualFibreChannelClientAdapters))

    def fetchFCDetailsFromVIOS(self, system_uuid, lpar_id, vios_list):
        vfcs = []
        if not vios_list:
            return vfcs
        vios_dict = {vios['PartitionID']: vios['PartitionName'] for vios in vios_list}

        try:
            vios_fc_xml = xml_strip_namespace(
                self.getVirtualIOServers(system_uuid, 'ViosFCMapping')
            )
            vios_fcs = vios_fc_xml.xpath('//VirtualFibreChannelMapping')
            for vios_fc in vios_fcs:
                vfc_dict = {}
                if not vios_fc.xpath('./ClientAdapter'):
                    continue
                part_id_nodes = vios_fc.xpath('./ClientAdapter/LocalPartitionID')
                if not part_id_nodes:
                    continue
                part_id = part_id_nodes[0].text
                if str(lpar_id) == str(part_id):
                    vios_id_nodes = vios_fc.xpath('./ClientAdapter/ConnectingPartitionID')
                    if not vios_id_nodes:
                        continue
                    vios_id = int(vios_id_nodes[0].text)
                    vfc_dict['vios'] = vios_dict.get(vios_id)
                    port_nodes = vios_fc.xpath('./ServerAdapter/PhysicalPort/PortName')
                    if port_nodes:
                        vfc_dict['PortName'] = port_nodes[0].text
                    loc_nodes = vios_fc.xpath('./ServerAdapter/PhysicalPort/LocationCode')
                    if loc_nodes:
                        vfc_dict['LocationCode'] = loc_nodes[0].text
                    wwpn_nodes = vios_fc.xpath('./ClientAdapter/WWPNs')
                    if wwpn_nodes:
                        vfc_dict['WWPNs'] = wwpn_nodes[0].text
                    client_slot_nodes = vios_fc.xpath('./ClientAdapter/VirtualSlotNumber')
                    if client_slot_nodes:
                        vfc_dict['ClientVirtualSlotNumber'] = client_slot_nodes[0].text
                    server_slot_nodes = vios_fc.xpath('./ClientAdapter/ConnectingVirtualSlotNumber')
                    if server_slot_nodes:
                        vfc_dict['ServerVirtualSlotNumber'] = server_slot_nodes[0].text
                    vfcs.append(vfc_dict)
        except Exception:
            pass

        return vfcs

    def fetchSCSIDetailsFromVIOS(self, system_uuid, lpar_id, vios_list):
        vscsis = []
        if not vios_list:
            return vscsis
        vios_dict = {vios['PartitionID']: vios['PartitionName'] for vios in vios_list}

        try:
            vios_scsi_xml = xml_strip_namespace(self.getVirtualIOServers(system_uuid, 'ViosSCSIMapping'))
            vios_scsis = vios_scsi_xml.xpath('//VirtualSCSIMapping')
            for vios_scsi_raw in vios_scsis:
                vscsi_dict = {}
                vios_scsi = etree.ElementTree(vios_scsi_raw)
                # This code is to handle stale adapters
                if len(vios_scsi.xpath('//ClientAdapter')) < 1:
                    continue
                part_id = vios_scsi.xpath('//ClientAdapter/LocalPartitionID')[0].text
                if str(lpar_id) == str(part_id):
                    # Adds the PVs
                    if len(vios_scsi.xpath('//Storage/PhysicalVolume/VolumeUniqueID')) >= 1:
                        volumeUniqueID = vios_scsi.xpath('//Storage/PhysicalVolume/VolumeUniqueID')[0].text
                        vscsi_dict['VolumeUniqueID'] = volumeUniqueID
                        vios_id = int(vios_scsi.xpath('//ClientAdapter/RemoteLogicalPartitionID')[0].text)
                        client_slot = vios_scsi.xpath('//ClientAdapter/VirtualSlotNumber')[0].text
                        server_slot = vios_scsi.xpath('//ClientAdapter/RemoteSlotNumber')[0].text
                        target_device = vios_scsi.xpath('//TargetDevice//TargetName')[0].text
                        vol_dict = {
                            "vios": vios_dict[vios_id],
                            'name': vios_scsi.xpath('//Storage/PhysicalVolume/VolumeName')[0].text,
                            'ClientVirtualSlotNumber': client_slot,
                            'ServerVirtualSlotNumber': server_slot,
                            'TargetDeviceName': target_device
                        }
                        flag = False
                        for vscsi in vscsis:
                            if 'VolumeUniqueID' in vscsi and vscsi['VolumeUniqueID'] == volumeUniqueID:
                                vscsi['Volume'].append(vol_dict)
                                flag = True
                                break
                        if not flag:
                            vscsi_dict['VolumeCapacity'] = vios_scsi.xpath('//Storage/PhysicalVolume/VolumeCapacity')[0].text
                            vscsi_dict['Volume'] = [vol_dict]
                            vscsis.append(vscsi_dict)
                    elif len(vios_scsi.xpath('//TargetDevice/VirtualOpticalTargetDevice')) >= 1:
                        vscsi_dict['ClientVirtualSlotNumber'] = vios_scsi.xpath('//ClientAdapter/VirtualSlotNumber')[0].text
                        vscsi_dict['ServerVirtualSlotNumber'] = vios_scsi.xpath('//ClientAdapter/RemoteSlotNumber')[0].text
                        vscsi_dict['TargetName'] = vios_scsi.xpath('//TargetDevice/VirtualOpticalTargetDevice/TargetName')[0].text
                        if len(vios_scsi.xpath('//Storage')) >= 1:
                            vscsi_dict['MediaName'] = vios_scsi.xpath('//Storage//MediaName')[0].text
                            vscsi_dict['MountType'] = vios_scsi.xpath('//Storage//MountType')[0].text
                            vscsi_dict['Size'] = vios_scsi.xpath('//Storage//Size')[0].text
                        vscsis.append(vscsi_dict)
        except Exception:
            pass
        return vscsis

    def getSharedProcessorPools(self, system_uuid):
        url = "https://{0}/rest/api/uom/ManagedSystem/{1}/SharedProcessorPool".format(self.hmc_ip, system_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': '*/*'}
        resp = open_url(url,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=300)
        if resp.code != 200:
            logger.debug("Get of Shared Processor Pool failed. Respsonse code: %d", resp.code)
            return None
        sharedProcPool_root = xml_strip_namespace(resp.read())
        sharedProcPool = sharedProcPool_root.xpath('//entry')
        return sharedProcPool

    def validateSharedProcessorPoolNameAndID(self, system_uuid, user_spp):
        spps = self.getSharedProcessorPools(system_uuid)
        spp_dict = {}
        spp_id = None
        for spp_raw in spps:
            spp = etree.ElementTree(spp_raw)
            v = spp.xpath('//PoolName')[0].text
            k = spp.xpath('//PoolID')[0].text
            spp_dict[k] = v
        if user_spp.isdigit():
            if user_spp in spp_dict:
                spp_id = user_spp
        else:
            logger.debug(spp_dict)
            for key, value in spp_dict.items():
                if value == user_spp:
                    spp_id = key
        return spp_id

    def check_vnic_condition(self, params):
        msg = ""
        for each in params['vnic_config']:
            if each['port_vlan_id'] is not None and (each['port_vlan_id'] < 2 or each['port_vlan_id'] > 4094) and each['port_vlan_id'] == 1:
                msg = "The valid values for port_vlan_id are 0 and 2 to 4094."
                return msg
            elif each['port_vlan_id'] is None:
                each['port_vlan_id'] = 0
            if each['port_vlan_priority'] is not None and each['port_vlan_priority'] > 7:
                msg = "The valid values for port_vlan_priority is 0 to 7."
                return msg
            elif each['port_vlan_priority'] is None:
                each['port_vlan_priority'] = 0
            if each['allowed_vlanids'] is not None:
                vlanids = each['allowed_vlanids'].strip().lower()
                if vlanids in ['all', 'none']:
                    pass
                elif re.fullmatch(r'(\d+)(,\d+)*', each['allowed_vlanids'].strip()):
                    vlan_list = each['allowed_vlanids'].strip().split(',')
                    if len(vlan_list) > 20:
                        msg = "The maximum number of allowed vlan id is 20."
                        return msg
                    if [vlan for vlan in vlan_list if not (vlan.isdigit() and 2 <= int(vlan) <= 4094)]:
                        msg = "The allowed vlan values can be only between 2 and 4094."
                        return msg
                else:
                    msg = "The valid values for allowed_vlanids are 'All', 'None', 'Comma-separated vlan ids'."
                    return msg
            else:
                each['allowed_vlanids'] = 'all'
            if each['allowed_macaddr'] is not None:
                if each['allowed_macaddr'].strip().lower() in ['all', 'none']:
                    pass
                elif re.fullmatch(r'(([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2}))(,\s*(([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})))*', each['allowed_macaddr'].strip()):
                    mac_list = each['allowed_macaddr'].strip().split(',')
                    if len(mac_list) > 4:
                        msg = "The maximum number of allowed vlan id is 4."
                        return msg
                else:
                    msg = "The valid values for allowed_macaddr are 'All', 'None', 'Comma-separated mac address'."
                    return msg
            else:
                each['allowed_macaddr'] = 'all'
            if (each['allowed_vlanids'].lower() == 'all') != (each['allowed_macaddr'].lower() == 'all'):
                msg = "If allowed VLAN IDs is set to allow all, then allowed OS MAC addresses must also be set to allow all and vice versa."
                return msg
        return msg

    def add_vnic_payload(self, lpar_template_dom, vnic_tup, sriov_dvc_col, vios_name_list):
        payload = ''
        default_vnic_no = 65535
        count = 0
        for vnic in vnic_tup:
            vnic_id = vnic['vnic_adapter_id'] if vnic['vnic_adapter_id'] else str(default_vnic_no - count)
            use_nxt_slot = "false" if vnic['vnic_adapter_id'] else "true"
            backing_devices = vnic['backing_devices']
            vlan_port_id = vnic['port_vlan_id']
            vlan_port_priority = vnic['port_vlan_priority']
            allowed_vlan_ids = 'ALL'
            allowed_mac_addr = 'ALL'
            if vnic['allowed_vlanids'] is not None:
                vlanids = vnic['allowed_vlanids'].strip().lower()
                if vlanids == 'all':
                    allowed_vlan_ids = 'ALL'
                elif vlanids == 'none':
                    allowed_vlan_ids = 'NONE'
                elif re.fullmatch(r'(\d+)(,\d+)*', vlanids):
                    allowed_vlan_ids = vlanids.replace(',', ' ')
            if vnic['allowed_macaddr'] is not None:
                mac = vnic['allowed_macaddr'].strip().lower()
                if mac == 'all':
                    allowed_mac_addr = 'ALL'
                elif mac == 'none':
                    allowed_mac_addr = 'NONE'
                elif re.fullmatch(r'(([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2}))(,\s*(([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})))*', mac):
                    allowed_mac_addr = mac.replace(',', ' ')
            backing_devices_payload = self.get_vnic_backing_devices_payload(backing_devices, sriov_dvc_col, vios_name_list)
            payload += '''
            <VirtualNICDedicated schemaVersion="V1_0">
                    <Metadata>
                           <Atom/>
                    </Metadata>
                    <VirtualSlotNumber kb="CUD" kxe="false">{0}</VirtualSlotNumber>
                    <drcName kb="CUD" kxe="false">CUSTOM_1653548478255-{1}9747</drcName>
                    <UseNextAvailableSlotID kxe="false" kb="CUD">{2}</UseNextAvailableSlotID>
                    <Details kxe="false" kb="CUR" schemaVersion="V1_0">
                            <Metadata>
                                    <Atom/>
                            </Metadata>
                            <PortVLANID kxe="false" kb="CUD">{4}</PortVLANID>
                            <PortVLANIDPriority kxe="false" kb="CUD">{5}</PortVLANIDPriority>
                            <AllowedVLANIDs kxe="false" kb="CUD">{6}</AllowedVLANIDs>
                            <MACAddress kxe="false" kb="COD">HMC-ASSIGNED</MACAddress>
                            <AllowedOperatingSystemMACAddresses kxe="false" kb="CUD">{7}</AllowedOperatingSystemMACAddresses>
                            <DesiredMode kxe="false" kb="CUD">DEDICATED</DesiredMode>
                            <AutoPriorityFailover kxe="false" kb="CUD">true</AutoPriorityFailover>
                    </Details>
                    <AssociatedBackingDevices kb="CUR" kxe="false" schemaVersion="V1_0">
                            <Metadata>
                                    <Atom/>
                            </Metadata>
                                    {3}
                    </AssociatedBackingDevices>
            </VirtualNICDedicated>'''.format(vnic_id, str(default_vnic_no - count), use_nxt_slot, backing_devices_payload,
                                             str(vlan_port_id), str(vlan_port_priority), str(allowed_vlan_ids), str(allowed_mac_addr))
            count += 1

        vnic_payload = '''
        <DedicatedVirtualNICs kxe="false" kb="CUD" schemaVersion="V1_0">
        <Metadata>
                <Atom/>
        </Metadata>
                {0}
        </DedicatedVirtualNICs>'''.format(payload)
        dedicatedvnicstag = lpar_template_dom.xpath('//DedicatedVirtualNICs')[0]
        dedicatedvnicstag.getparent().replace(dedicatedvnicstag, etree.XML(vnic_payload))

    def get_vnic_backing_devices_payload(self, backing_devices, sriov_dvc_col, vios_name_list):
        eval_backing_devices = []
        if backing_devices is None:
            for sriov_dvc in sriov_dvc_col:
                if sriov_dvc["LinkStatus"] == "true":
                    eval_dvc_dict = {}
                    eval_dvc_dict['partitionName'] = vios_name_list[0]
                    eval_dvc_dict['RelatedSRIOVAdapterID'] = sriov_dvc['RelatedSRIOVAdapterID']
                    if round((100.0 - float(sriov_dvc['AllocatedCapacity'])), 1) >= 2.0:
                        eval_dvc_dict['DesiredCapacityPercentage'] = "2.0"
                    else:
                        continue
                    eval_dvc_dict['RelatedSRIOVPhysicalPortID'] = sriov_dvc['RelatedSRIOVPhysicalPortID']
                    eval_backing_devices.append(eval_dvc_dict)
                    break
            else:
                for sriov_dvc in sriov_dvc_col:
                    if round((100.0 - float(sriov_dvc['AllocatedCapacity'])), 1) >= 2.0:
                        eval_dvc_dict = {}
                        eval_dvc_dict['partitionName'] = vios_name_list[0]
                        eval_dvc_dict['RelatedSRIOVAdapterID'] = sriov_dvc['RelatedSRIOVAdapterID']
                        eval_dvc_dict['DesiredCapacityPercentage'] = "2.0"
                        eval_dvc_dict['RelatedSRIOVPhysicalPortID'] = sriov_dvc['RelatedSRIOVPhysicalPortID']
                        eval_backing_devices.append(eval_dvc_dict)
                        break
                else:
                    raise Error('Their are no backing device with link status up or available capacity more than 2.0 in the managed system')
        else:
            for backing_device in backing_devices:
                for sriov_dvc in sriov_dvc_col:
                    if (backing_device['location_code'] is None) or (re.search(r'[a-zA-Z]\d{1,2}-[a-zA-Z]\d{1,2}$', backing_device['location_code']) is None):
                        msg = ('mandatory parameter backing device location_code is missing '
                               'or location_code is not in C1-T1 or XXXXX.XXXXX.XXX-P1-C1-T1 format')
                        raise ParameterError(msg)
                    if sriov_dvc['LocationCode'] == backing_device['location_code'] or (sriov_dvc['LocationCode']).endswith(backing_device['location_code']):
                        eval_dvc_dict = {}
                        if backing_device['hosting_partition'] is None:
                            eval_dvc_dict['partitionName'] = vios_name_list[0]
                        elif backing_device['hosting_partition'] in vios_name_list:
                            eval_dvc_dict['partitionName'] = backing_device['hosting_partition']
                        else:
                            msg = ("Given backing device hosting partition name: {0} not found in the managed system "
                                   "or RMC of state is not active")
                            raise Error(msg.format(backing_device['hosting_partition']))
                        eval_dvc_dict['RelatedSRIOVAdapterID'] = sriov_dvc['RelatedSRIOVAdapterID']
                        if backing_device['capacity']:
                            if round(backing_device['capacity'], 1) <= round(100.0 - float(sriov_dvc['AllocatedCapacity']), 1):
                                eval_dvc_dict['DesiredCapacityPercentage'] = str(backing_device['capacity'])
                            else:
                                msg = 'Available Capacity of the backing device:{0} is {1} but desired capacity is: {2}'
                                raise Error(msg.format(sriov_dvc['LocationCode'], round(100.0 - float(sriov_dvc['AllocatedCapacity']), 1),
                                            backing_device['capacity']))
                        else:
                            if round(100.0 - float(sriov_dvc['AllocatedCapacity']), 1) >= 2.0:
                                eval_dvc_dict['DesiredCapacityPercentage'] = "2.0"
                            else:
                                msg = 'Available Capacity of the backing device:{0} is {1} but desired capacity is: 2.0'
                                raise Error(msg.format(sriov_dvc['LocationCode'], round(100.0 - float(sriov_dvc['AllocatedCapacity']), 1)))
                        eval_dvc_dict['RelatedSRIOVPhysicalPortID'] = sriov_dvc['RelatedSRIOVPhysicalPortID']
                        eval_backing_devices.append(eval_dvc_dict)
                        break
                else:
                    msg = "Given VNIC SRIOV backing device location code: {0} not found in the managed system or exhausted with Ethernet LogicalPort limit"
                    raise Error(msg.format(backing_device['location_code']))
        payload = ''
        for ev_bck_dvc in eval_backing_devices:
            payload += '''
            <VirtualNICBackingDeviceChoice>
            <VirtualNICSRIOVBackingDevice schemaVersion="V1_0">
                    <Metadata>
                            <Atom/>
                    </Metadata>
                    <DeviceType kb="COR" kxe="false">SRIOV</DeviceType>
                    <AssociatedVirtualIOServer kxe="false" kb="COR" schemaVersion="V1_0">
                            <Metadata>
                                    <Atom/>
                            </Metadata>
                            <partitionName kb="CUD" kxe="false">{0}</partitionName>
                    </AssociatedVirtualIOServer>
                    <FailOverPriority kb="CUD" kxe="false">50</FailOverPriority>
                    <RelatedSRIOVAdapterID kxe="false" kb="COR">{1}</RelatedSRIOVAdapterID>
                    <DesiredCapacityPercentage kxe="false" kb="ROR">{2}%</DesiredCapacityPercentage>
                    <RelatedSRIOVPhysicalPortID kb="COR" kxe="false">{3}</RelatedSRIOVPhysicalPortID>
            </VirtualNICSRIOVBackingDevice>
            </VirtualNICBackingDeviceChoice>
            '''.format(ev_bck_dvc['partitionName'], ev_bck_dvc['RelatedSRIOVAdapterID'],
                       ev_bck_dvc['DesiredCapacityPercentage'], ev_bck_dvc['RelatedSRIOVPhysicalPortID'])
        return payload

    def create_sriov_collection(self, sriov_adapters_dom):
        sriov_col_li = []
        for sriov_adapter_dom_raw in sriov_adapters_dom:
            sriov_adapter_dom = etree.ElementTree(sriov_adapter_dom_raw)
            try:
                sriov_adapter_id = sriov_adapter_dom.xpath('//SRIOVAdapterID')[0].text
                sriov_ce_pps = sriov_adapter_dom.xpath('//ConvergedEthernetPhysicalPorts//SRIOVConvergedNetworkAdapterPhysicalPort')
                sriov_et_pps = sriov_adapter_dom.xpath('//EthernetPhysicalPorts//SRIOVEthernetPhysicalPort')
                sriov_rc_pps = sriov_adapter_dom.xpath('//SRIOVRoCEPhysicalPorts//SRIOVRoCEPhysicalPort')
                sriov_pps = sriov_ce_pps + sriov_et_pps + sriov_rc_pps
                for sriov_pp_raw in sriov_pps:
                    sriov_pp = etree.ElementTree(sriov_pp_raw)
                    sriov_dict = {}
                    maxELP = int(sriov_pp.xpath("//ConfiguredMaxEthernetLogicalPorts")[0].text)
                    cELP = int(sriov_pp.xpath("//ConfiguredEthernetLogicalPorts")[0].text)
                    if maxELP - cELP == 0:
                        continue
                    sriov_dict['RelatedSRIOVAdapterID'] = sriov_adapter_id
                    sriov_dict['LocationCode'] = sriov_pp.xpath("//LocationCode")[0].text
                    sriov_dict['RelatedSRIOVPhysicalPortID'] = sriov_pp.xpath("//PhysicalPortID")[0].text
                    sriov_dict['LinkStatus'] = sriov_pp.xpath("//LinkStatus")[0].text
                    sriov_dict['AllocatedCapacity'] = sriov_pp.xpath("//AllocatedCapacity")[0].text.strip('%')
                    sriov_col_li.append(sriov_dict)
            except Exception:
                continue
        return sriov_col_li

    def generic_get(self, url):
        header = {'X-API-Session': self.session,
                  'Accept': '*/*'}
        resp = open_url(url,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=3600)
        if resp.code != 200:
            logger.debug("Get operation failed. Respsonse code: %d", resp.code)
            return None
        response = resp.read()
        gen_response = xml_strip_namespace(response)
        return gen_response

    def isDedicatedProcConfig(self, partition_dom):
        return True if partition_dom.xpath('//HasDedicatedProcessors')[0].text == 'true' else False

    def updateProc(self, partition_dom, isDedicated, proc=None, proc_unit=None):
        if isDedicated:
            partition_dom.xpath('//DedicatedProcessorConfiguration/DesiredProcessors')[0].text = proc
        else:
            if proc:
                partition_dom.xpath('//SharedProcessorConfiguration/DesiredVirtualProcessors')[0].text = proc
            if proc_unit:
                partition_dom.xpath('//SharedProcessorConfiguration/DesiredProcessingUnits')[0].text = proc_unit
        return partition_dom

    def updateProcSharingMode(self, partition_dom, sharingMode):
        modeMapping = {'keep_idle_procs': 'keep idle procs',
                       'share_idle_procs': 'sre idle proces',
                       'share_idle_procs_active': 'sre idle procs active',
                       'share_idle_procs_always': 'sre idle procs always',
                       'uncapped': 'uncapped',
                       'capped': 'capped'
                       }
        partition_dom.xpath('//SharingMode')[0].text = modeMapping[sharingMode]
        return partition_dom

    def getProcSharingMode(self, partition_dom):
        return partition_dom.xpath('//CurrentSharingMode')[0].text

    def updateProcUncappedWeight(self, partition_dom, weight):
        sharedProcElement = partition_dom.xpath('//UncappedWeight')
        if isinstance(sharedProcElement, list) and len(sharedProcElement) > 0:
            partition_dom.xpath('//UncappedWeight')[0].text = weight
        else:
            weightXml = '<UncappedWeight kxe="false" kb="CUD">{0}</UncappedWeight>'.format(weight)
            sharedProcessorPoolIDElement = partition_dom.xpath('//SharedProcessorPoolID')[0]
            sharedProcessorPoolIDElement.addnext(etree.XML(weightXml))
        return partition_dom

    def getProcUncappedWeight(self, partition_dom):
        element = partition_dom.xpath('//UncappedWeight')
        if isinstance(element, list) and len(element) > 0:
            return element[0].text
        else:
            return None

    def getProcPool(self, partition_dom):
        return partition_dom.xpath('//CurrentSharedProcessorPoolID')[0].text

    def updateProcPool(self, partition_dom, poolId):
        partition_dom.xpath('//SharedProcessorPoolID')[0].text = poolId
        return partition_dom

    def getProcs(self, isDedicated, partition_dom):
        if isDedicated:
            procs = partition_dom.xpath('//CurrentDedicatedProcessorConfiguration/CurrentProcessors')[0].text
        else:
            procs = partition_dom.xpath('//CurrentSharedProcessorConfiguration/AllocatedVirtualProcessors')[0].text
        return procs

    def getProcUnits(self, partition_dom):
        return partition_dom.xpath('//CurrentSharedProcessorConfiguration/CurrentProcessingUnits')[0].text

    def getMem(self, partition_dom):
        return partition_dom.xpath('//CurrentMemory')[0].text

    def updateMem(self, partition_dom, mem):
        partition_dom.xpath('//DesiredMemory')[0].text = mem
        return partition_dom

    def updateLogicalPartition(self, partition_dom, timeout=None):
        header = {'X-API-Session': self.session,
                  'Accept': '*/*',
                  'Content-Type': 'application/vnd.ibm.powervm.uom+xml; type=LogicalPartition'}

        partition_uuid = partition_dom.xpath('//AtomID')[0].text
        timeout_in_sec = 3600
        if timeout:
            if timeout > 60:
                timeout_in_sec = timeout * 60

            url = "https://{0}/rest/api/uom/LogicalPartition/{1}?timeout={2}".format(
                  self.hmc_ip, partition_uuid, timeout)
        else:
            url = "https://{0}/rest/api/uom/LogicalPartition/{1}".format(
                  self.hmc_ip, partition_uuid)

        partition_dom = partition_dom.xpath("//LogicalPartition")[0]

        partiton_xmlstr = etree.tostring(partition_dom)
        partiton_xmlstr = partiton_xmlstr.decode("utf-8").replace("LogicalPartition", LPAR_NS, 1)
        logger.debug("INPUT PAYLOAD: \n %s", partiton_xmlstr)
        resp = open_url(url,
                        headers=header,
                        method='POST',
                        data=partiton_xmlstr,
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=timeout_in_sec)
        if resp.code != 200:
            logger.debug("Post operation failed. Respsonse code: %d", resp.code)
            return None
        response = resp.read()
        logger.debug("POST RESPONSE: \n %s", response)
        post_response = xml_strip_namespace(response)
        return post_response

    def fetchDedicatedVirtualNICs(self, system_uuid, lpar_uuid, vm_name, vios_list):
        lpar_uuid, partition_dom = self.getLogicalPartition(system_uuid,
                                                            partition_name=vm_name, partition_uuid=lpar_uuid)
        vios_dict = {}
        if vios_list:
            vios_dict = {vios['UUID']: vios['PartitionName'] for vios in vios_list}
        vnics_list = []
        vnic_links = partition_dom.xpath('//DedicatedVirtualNICs//link')
        if vnic_links:
            for vnic_link_raw in vnic_links:
                vnic_dict = {}
                vnic_link = etree.ElementTree(vnic_link_raw)
                href = vnic_link.xpath('./@href')[0]
                vnic_dom = self.generic_get(href)
                vnic_dict['vnic_adapter_id'] = vnic_dom.xpath('//VirtualSlotNumber')[0].text
                vnic_backing_devices = vnic_dom.xpath('//VirtualNICBackingDeviceChoice')
                bck_dvcs = []
                for vnic_bck_dvc_raw in vnic_backing_devices:
                    bck_dvc_dict = {}
                    vnic_bck_dvc = etree.ElementTree(vnic_bck_dvc_raw)
                    bck_dvc_dict['Capacity'] = vnic_bck_dvc.xpath('//CurrentCapacityPercentage')[0].text
                    bck_dvc_dict['DeviceType'] = vnic_bck_dvc.xpath('//DeviceType')[0].text
                    bck_dvc_dict['Status'] = vnic_bck_dvc.xpath('//Status')[0].text
                    bck_dvc_dict['RelatedSRIOVAdapterID'] = vnic_bck_dvc.xpath('//RelatedSRIOVAdapterID')[0].text
                    vios_href = vnic_bck_dvc.xpath('//AssociatedVirtualIOServer')[0].attrib['href']
                    bck_dvc_dict['AssociatedVirtualIOServer'] = vios_dict[(vios_href.split('/'))[-1]]
                    sriov_href = vnic_bck_dvc.xpath('//RelatedSRIOVLogicalPort')[0].attrib['href']
                    bck_dvc_dict['RelatedSRIOVLocationCode'] = self.generic_get(sriov_href).xpath('//LocationCode')[0].text
                    bck_dvcs.append(bck_dvc_dict)
                vnic_dict['backing_devices'] = bck_dvcs
                vnics_list.append(vnic_dict)
        return vnics_list

    def fetchTaggedGroupItems(self):
        url = "https://{0}/rest/api/uom/Group".format(self.hmc_ip)
        resp_dom = self.generic_get(url)
        resp_dict = {}
        if resp_dom is not None:
            group_dom_list = resp_dom.xpath("//Group")
            for group_dom_raw in group_dom_list:
                uuid_list = []
                group_dom = etree.ElementTree(group_dom_raw)
                group_name = group_dom.xpath("//GroupName")[0].text
                assc_lpar_links = group_dom.xpath("//AssociatedLogicalPartitions//link")
                assc_ms_links = group_dom.xpath("//AssociatedManagedSystems//link")
                assc_vios_links = group_dom.xpath("//AssociatedVirtualIOServers//link")
                for assc_raw_lpar in assc_lpar_links:
                    assc_lpar = etree.ElementTree(assc_raw_lpar)
                    lpar_uuid = (assc_lpar.xpath('./@href')[0]).split('/')[-1]
                    uuid_list.append(lpar_uuid)
                for assc_raw_ms in assc_ms_links:
                    assc_ms = etree.ElementTree(assc_raw_ms)
                    ms_uuid = (assc_ms.xpath('./@href')[0]).split('/')[-1]
                    uuid_list.append(ms_uuid)
                for assc_raw_vios in assc_vios_links:
                    assc_vios = etree.ElementTree(assc_raw_vios)
                    vios_uuid = (assc_vios.xpath('./@href')[0]).split('/')[-1]
                    uuid_list.append(vios_uuid)
                resp_dict[group_name] = uuid_list
        return resp_dict

    def fetchPVsFromVIOSDOM(self, vios_dom, vios_name):
        # Generate the list of PhysicalVolumes available in the VIOS DOM
        pvs_raw = []
        pvs = []
        fc_ports_dom = vios_dom.xpath("//PhysicalFibreChannelPorts/PhysicalFibreChannelPort")
        for fc_port_raw in fc_ports_dom:
            fc_port_dom = etree.ElementTree(fc_port_raw)
            pvs_raw = pvs_raw + fc_port_dom.xpath("//PhysicalVolumes/PhysicalVolume")
        if pvs_raw:
            pvs = [etree.ElementTree(pv_raw) for pv_raw in pvs_raw]
        else:
            raise HmcError("There are no Physical Volumes Available in VIOS: {0}".format(vios_name))
        return pvs

    def build_SCSI_MappingPayload(self, pv_dom_list, pv_setting, lpar_UUID, lpar_id, vios_id):
        payload = ""
        target_name_payload = ""
        server_adapter_id_payload = ""
        client_adapter_id_payload = ""
        pv_payload = ""

        for pv_dom in pv_dom_list:
            disk_name = pv_dom.xpath("//VolumeName")[0].text
            if disk_name == pv_setting['disk_name']:
                pv_payload = pv_dom
                break
        else:
            raise HmcError("Disk_Name provided: {0} not found in the vios {1}".format(pv_setting['disk_name'], pv_setting['vios_name']))

        # build a payload for target name, if user provides
        if pv_setting['target_name']:
            target_name_payload = '''
            <TargetDevice kb="CUR" kxe="false">
                <PhysicalVolumeVirtualTargetDevice schemaVersion="V1_0">
                    <Metadata>
                        <Atom/>
                    </Metadata>
                <TargetName kb="CUR" kxe="false">{0}</TargetName>
                </PhysicalVolumeVirtualTargetDevice>
            </TargetDevice>
            '''.format(pv_setting['target_name'])

        # build a payload for client adapter id, if user provides
        if pv_setting['server_adapter_id']:
            server_adapter_id_payload = '''
            <ServerAdapter kb="CUR" kxe="false" schemaVersion="V1_0">
                <Metadata>
                    <Atom/>
                </Metadata>
                <VirtualSlotNumber kb="COD" kxe="false">{0}</VirtualSlotNumber>
            </ServerAdapter>
            '''.format(str(pv_setting['server_adapter_id']))

        # build a payload for server adapter id, if user provides
        if pv_setting['client_adapter_id']:
            client_adapter_id_payload = '''
            <ClientAdapter kb="CUR" kxe="false" schemaVersion="V1_0">
                <Metadata>
                    <Atom/>
                </Metadata>
                <VirtualSlotNumber kb="COD" kxe="false">{0}</VirtualSlotNumber>
            </ClientAdapter>
            '''.format(str(pv_setting['client_adapter_id']))

        payload = '''
        <VirtualSCSIMapping schemaVersion="V1_0">
            <Metadata>
                <Atom/>
            </Metadata>
            <AssociatedLogicalPartition kxe="false" kb="CUR" href="https://localhost:443/rest/api/uom/LogicalPartition/{0}" rel="related"/>
            {1}
            {2}
            <Storage kb="CUR" kxe="false">
            {3}
            </Storage>
            {4}
        </VirtualSCSIMapping>
        '''.format(lpar_UUID, client_adapter_id_payload, server_adapter_id_payload, (etree.tostring(pv_payload)).decode("utf-8"), target_name_payload)

        return payload.replace('\n\n', '').replace('\n', '')

    def getVIOSSCSCIMappings_dictionary(self, vios_uuid):
        vscsis_pv = []
        vscsis_vod = []
        try:
            vios_scsi_xml = self.getVirtualIOServer(vios_uuid, 'ViosSCSIMapping')
            vios_scsis = vios_scsi_xml.xpath('//VirtualSCSIMapping')
            for vios_scsi_raw in vios_scsis:
                vscsi_dict = {}
                vios_scsi = etree.ElementTree(vios_scsi_raw)
                try:
                    # Fills the vscsi_pv dictionary
                    vscsi_dict['BackingDeviceName'] = vios_scsi.xpath('//ServerAdapter/BackingDeviceName')[0].text
                    vscsi_dict['RemoteLogicalPartitionID'] = vios_scsi.xpath('//ServerAdapter/RemoteLogicalPartitionID')[0].text
                    vscsis_pv.append(vscsi_dict)
                except Exception:
                    pass
                try:
                    # Fills the vscsi_vod dictionary
                    vscsi_dict['TargetName'] = vios_scsi.xpath('//TargetDevice/VirtualOpticalTargetDevice/TargetName')[0].text
                    vscsis_vod.append(vscsi_dict)
                except Exception:
                    pass
        except Exception:
            pass
        return vscsis_pv, vscsis_vod

    def updateVIOSwithSCSIMappings(self, vios_UUID, pv_settings_list, lpar_UUID, vios_name, partition_dom, timeout):
        payload = ""
        flag = False
        vios_dom = self.getVirtualIOServer(vios_UUID)
        vios_vscsi_dict = self.getVIOSSCSCIMappings_dictionary(vios_UUID)
        mapped_dvc_names = [item['BackingDeviceName'] for item in vios_vscsi_dict[0]]
        pv_dom_list = self.fetchPVsFromVIOSDOM(vios_dom, vios_name)
        lpar_id = partition_dom.xpath("//PartitionID")[0].text
        vios_id = vios_dom.xpath("//PartitionID")[0].text
        for pv_settings in pv_settings_list:
            if pv_settings['disk_name'] not in mapped_dvc_names:
                payload = self.build_SCSI_MappingPayload(pv_dom_list, pv_settings, lpar_UUID, lpar_id, vios_id)
                vSCSIMappingsTag = vios_dom.xpath("//VirtualSCSIMappings")[0]
                vSCSIMappingsTag.append(etree.XML(payload))
                flag = True
        if flag:
            self.updateVirtualIOServer(vios_dom, timeout)
        return flag

    def fetchVIOSFcDetails(self, vios_dom):
        fc_ports_list = []
        fc_ports = vios_dom.xpath("//PhysicalFibreChannelAdapter/PhysicalFibreChannelPorts/PhysicalFibreChannelPort")
        for fc_port_raw in fc_ports:
            fc_dict = {}
            fc_dict['AvailablePorts'] = "0"
            fc_dict['TotalPorts'] = "0"
            fc_port = etree.ElementTree(fc_port_raw)
            try:
                fc_dict['PortName'] = fc_port.xpath("//PortName")[0].text
                fc_dict['AvailablePorts'] = fc_port.xpath("//AvailablePorts")[0].text
                fc_dict['TotalPorts'] = fc_port.xpath("//TotalPorts")[0].text
                fc_dict['LocationCode'] = fc_port.xpath("//LocationCode")[0].text
            except Exception:
                pass
            finally:
                fc_ports_list.append(fc_dict)

        return fc_ports_list

    def build_FC_MappingPayload(self, location_code, npiv_setting, lpar_UUID, lpar_id, vios_id):
        payload = ""
        server_adapter_id_payload = ""
        client_adapter_id_payload = ""
        wwpn_pair_payload = ""
        client_adapter_payload = ""
        # build client adapter_id payload
        if npiv_setting['wwpn_pair']:
            if ';' in npiv_setting['wwpn_pair']:
                wwpn_pair = npiv_setting['wwpn_pair'].replace(";", " ")
                wwpn_pair_payload = '''
                <WWPNs kb="CUR" kxe="false">{0}</WWPNs>'''.format(wwpn_pair)
            else:
                raise ParameterError("Invalid WWPN pair format: {0}, Correct format is <wwpn1;wwpn2>".format(npiv_setting['wwpn_pair']))
        if npiv_setting['client_adapter_id']:
            client_adapter_payload = '''
            <VirtualSlotNumber kb="COD" kxe="false">{0}</VirtualSlotNumber>
            <ConnectingPartitionID kxe="false" kb="CUR">{1}</ConnectingPartitionID>'''.format(str(npiv_setting['client_adapter_id']), vios_id)
        if wwpn_pair_payload or client_adapter_payload:
            client_adapter_id_payload = '''
            <ClientAdapter kxe="false" kb="CUR" schemaVersion="V1_0">
                <Metadata>
                    <Atom/>
                </Metadata>
                <LocalPartitionID kxe="false" kb="CUR">{0}</LocalPartitionID>
                {1}
                {2}
            </ClientAdapter>
            '''.format(lpar_id, client_adapter_payload, wwpn_pair_payload)
        # build server adapter id payload
        if npiv_setting['server_adapter_id']:
            server_adapter_id_payload = '''
            <ServerAdapter kxe="false" kb="CUR" schemaVersion="V1_0">
                <Metadata>
                    <Atom/>
                </Metadata>
                <VirtualSlotNumber kb="COD" kxe="false">{0}</VirtualSlotNumber>
                <ConnectingPartitionID kxe="false" kb="CUR">{1}</ConnectingPartitionID>
            </ServerAdapter>
            '''.format(str(npiv_setting['server_adapter_id']), lpar_id)
        # build Virtual Fibre Channel Mapping payload
        payload = '''
        <VirtualFibreChannelMapping schemaVersion="V1_0">
            <Metadata>
                <Atom/>
            </Metadata>
            <AssociatedLogicalPartition kxe="false" kb="CUR" href="https://localhost:443/rest/api/uom/LogicalPartition/{0}" rel="related"/>
            {1}
            <Port kxe="false" kb="CUR" schemaVersion="V1_0">
                <Metadata>
                    <Atom/>
                </Metadata>
                <LocationCode kb="ROR" kxe="false">{2}</LocationCode>
                <PortName kxe="false" kb="CUR">{3}</PortName>
            </Port>
            {4}
        </VirtualFibreChannelMapping>
        '''.format(lpar_UUID, client_adapter_id_payload, location_code, npiv_setting['fc_port_name'], server_adapter_id_payload)
        return payload

    def updateVIOSwithNPIVMappings(self, vios_UUID, npiv_settings_list, lpar_UUID, vios_name, partition_dom, timeout):
        payload = ""
        flag = False
        vios_dom = self.getVirtualIOServer(vios_UUID)
        vios_npiv_dict_list = self.fetchVIOSFcDetails(vios_dom)
        lpar_id = partition_dom.xpath("//PartitionID")[0].text
        vios_id = vios_dom.xpath("//PartitionID")[0].text
        vfc_dom = vios_dom.xpath(".//VirtualFibreChannelMapping")
        mappings_list = []
        for mapping in vfc_dom:
            server_virtual_slot = mapping.xpath(".//ServerAdapter/VirtualSlotNumber/text()")
            client_virtual_slot = mapping.xpath(".//ClientAdapter/VirtualSlotNumber/text()")
            mapping_dict = {
                "server_virtual_slot": server_virtual_slot[0] if server_virtual_slot else None,
                "client_virtual_slot": client_virtual_slot[0] if client_virtual_slot else None,
            }
            mappings_list.append(mapping_dict)
        for npiv_settings in npiv_settings_list:
            exists = any(
                (
                    str(mapping["server_virtual_slot"]) == str(npiv_settings['server_adapter_id'])
                    and str(mapping["client_virtual_slot"]) == str(npiv_settings['client_adapter_id'])
                )
                for mapping in mappings_list
            )
            if not exists:
                for vios_npiv_dict in vios_npiv_dict_list:
                    if (npiv_settings['fc_port_name'] == vios_npiv_dict['PortName']):
                        if int(vios_npiv_dict['AvailablePorts']) > 0:
                            payload = self.build_FC_MappingPayload(vios_npiv_dict['LocationCode'], npiv_settings, lpar_UUID, lpar_id, vios_id)
                            FCMappingsTag = vios_dom.xpath("//VirtualFibreChannelMappings")[0]
                            FCMappingsTag.append(etree.XML(payload))
                            flag = True
                            break
                        raise HmcError(
                            "There are only {0} available ports in the fc_port_name: {1}".format(
                                vios_npiv_dict['AvailablePorts'], npiv_settings['fc_port_name']
                            )
                        )
                else:
                    raise HmcError("fc_port_name: {0} provided is not found in the vios: {1}".format(npiv_settings['fc_port_name'], vios_name, ))
        if flag:
            self.updateVirtualIOServer(vios_dom, timeout)
        return flag

    def build_SCSI_VOD_MappingPayload(self, vod_setting, lpar_UUID, lpar_id, vios_id, vom_dict):
        payload = ""
        server_adapter_id_payload = ""
        client_adapter_id_payload = ""
        media_name_payload = ""

        # build a payload for client adapter id, if user provides
        if vod_setting['server_adapter_id']:
            server_adapter_id_payload = '''
            <ClientAdapter kb="CUR" kxe="false" schemaVersion="V1_0">
                <Metadata>
                    <Atom/>
                </Metadata>
                <LocalPartitionID kxe="false" kb="CUR">{0}</LocalPartitionID>
                <VirtualSlotNumber kb="COD" kxe="false">{1}</VirtualSlotNumber>
                <RemoteLogicalPartitionID kxe="false" kb="CUR">{2}</RemoteLogicalPartitionID>
            </ClientAdapter>
            '''.format(lpar_id, str(vod_setting['server_adapter_id']), vios_id)

        # build a payload for server adapter id, if user provides
        if vod_setting['client_adapter_id']:
            client_adapter_id_payload = '''
            <ServerAdapter kb="CUR" kxe="false" schemaVersion="V1_0">
                <Metadata>
                    <Atom/>
                </Metadata>
                <LocalPartitionID kxe="false" kb="CUR">{0}</LocalPartitionID>
                <VirtualSlotNumber kb="COD" kxe="false">{1}</VirtualSlotNumber>
                <RemoteLogicalPartitionID kxe="false" kb="CUR">{2}</RemoteLogicalPartitionID>
            </ServerAdapter>
            '''.format(vios_id, str(vod_setting['client_adapter_id']), lpar_id)

        # build payload for loading media
        if vod_setting['media_name']:
            if vod_setting['media_name'] in vom_dict:
                media_name_payload = '''
                <Storage kb="CUR" kxe="false">
                    <VirtualOpticalMedia schemaVersion="V1_0">
                        <Metadata>
                            <Atom/>
                        </Metadata>
                        <MediaName kxe="false" kb="CUR">{0}</MediaName>
                    </VirtualOpticalMedia>
                </Storage>
                '''.format(vod_setting['media_name'])
            else:
                raise HmcError("MediaName: {0} not found in the VIOS".format(vod_setting['media_name']))

        payload = '''
        <VirtualSCSIMapping schemaVersion="V1_0">
            <Metadata>
                <Atom/>
            </Metadata>
            <AssociatedLogicalPartition kxe="false" kb="CUR" href="https://localhost:443/rest/api/uom/LogicalPartition/{0}" rel="related"/>
            {1}
            {2}
            {3}
            <TargetDevice kb="CUR" kxe="false">
                <VirtualOpticalTargetDevice schemaVersion="V1_0">
                    <Metadata>
                        <Atom/>
                    </Metadata>
                    <TargetName kb="CUR" kxe="false">{4}</TargetName>
                </VirtualOpticalTargetDevice>
            </TargetDevice>
        </VirtualSCSIMapping>
        '''.format(lpar_UUID, server_adapter_id_payload, client_adapter_id_payload, media_name_payload, vod_setting['device_name'])

        return payload.replace('\n\n', '').replace('\n', '')

    def getVIOSVirtualOpticalMediaDetails(self, vios_dom):
        voms_dict = {}
        if len(vios_dom.xpath("//MediaRepositories/VirtualMediaRepository/OpticalMedia/VirtualOpticalMedia")) >= 1:
            voms = vios_dom.xpath("//MediaRepositories/VirtualMediaRepository/OpticalMedia/VirtualOpticalMedia")
            for vom_raw in voms:
                vom_dict = {}
                vom = etree.ElementTree(vom_raw)
                media_name = vom.xpath('//MediaName')[0].text
                vom_dict['MediaUDID'] = vom.xpath('//MediaUDID')[0].text
                vom_dict['MountType'] = vom.xpath('//MountType')[0].text
                vom_dict['Size'] = vom.xpath('//Size')[0].text
                voms_dict[media_name] = vom_dict
        return voms_dict

    def updateVIOSwithVODMappings(self, vios_UUID, vod_settings_list, lpar_UUID, partition_dom, timeout):
        payload = ""
        flag = False
        vios_dom = self.getVirtualIOServer(vios_UUID)
        vios_vscsi_dict = self.getVIOSSCSCIMappings_dictionary(vios_UUID)
        mapped_dvc_names = [item['TargetName'] for item in vios_vscsi_dict[1]]
        lpar_id = partition_dom.xpath("//PartitionID")[0].text
        vios_id = vios_dom.xpath("//PartitionID")[0].text
        vom_dict = self.getVIOSVirtualOpticalMediaDetails(vios_dom)
        for vod_settings in vod_settings_list:
            if vod_settings['device_name'] not in mapped_dvc_names:
                payload = self.build_SCSI_VOD_MappingPayload(vod_settings, lpar_UUID, lpar_id, vios_id, vom_dict)
                vSCSIMappingsTag = vios_dom.xpath("//VirtualSCSIMappings")[0]
                vSCSIMappingsTag.append(etree.XML(payload))
                flag = True
        if flag:
            self.updateVirtualIOServer(vios_dom, timeout)
        return flag

    def updateVirtualIOServer(self, vios_dom, timeout=None):
        header = {'X-API-Session': self.session,
                  'Accept': '*/*',
                  'Content-Type': 'application/vnd.ibm.powervm.uom+xml; type=VirtualIOServer'}

        vios_uuid = vios_dom.xpath('//AtomID')[0].text
        timeout_in_sec = 3600
        if timeout:
            if timeout > 60:
                timeout_in_sec = timeout * 60

            url = "https://{0}/rest/api/uom/VirtualIOServer/{1}?timeout={2}".format(
                  self.hmc_ip, vios_uuid, timeout)
        else:
            url = "https://{0}/rest/api/uom/VirtualIOServer/{1}".format(
                  self.hmc_ip, vios_uuid)

        vios_dom = vios_dom.xpath("//VirtualIOServer")[0]
        vios_xmlstr = etree.tostring(vios_dom)
        vios_xmlstr = vios_xmlstr.decode("utf-8").replace("VirtualIOServer", VIOS_NS, 1)
        logger.debug("INPUT PAYLOAD: \n %s", vios_xmlstr)
        resp = open_url(url,
                        headers=header,
                        method='POST',
                        data=vios_xmlstr,
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=timeout_in_sec)
        if resp.code != 200:
            logger.debug("Post operation failed. Respsonse code: %d", resp.code)
            return None
        response = resp.read()
        logger.debug("POST RESPONSE: \n %s", response)
        post_response = xml_strip_namespace(response)
        return post_response

    def LicReadinessCheck(self, system_uuid, system_name):
        url = f"https://{self.hmc_ip}/rest/api/uom/ManagedSystem/{system_uuid}/do/LICReadiness"
        logger.info("In LICReadiness check")

        header = {
            "X-API-Session": self.session,
            "Accept": "application/json",
            "Content-Type": "application/vnd.ibm.powervm.web+json; type=JobRequest"
        }

        payload = {
            "JobRequest": {
                "Metadata": {
                    "Atom": ""
                },
                "RequestedOperation": {
                    "Metadata": {
                        "Atom": ""
                    },
                    "OperationName": "LICReadiness",
                    "GroupName": "ManagedSystem"
                },
                "JobParameters": {
                    "Metadata": {
                        "Atom": ""
                    },
                    "JobParameter": [
                        {
                            "Metadata": {
                                "Atom": ""
                            },
                            "ParameterName": "managedSystem",
                            "ParameterValue": f"{system_name}"
                        },
                        {
                            "Metadata": {
                                "Atom": ""
                            },
                            "ParameterName": "operation",
                            "ParameterValue": "k"
                        }
                    ]
                }
            }
        }

        timeout_in_sec = 3600

        try:
            resp = open_url(
                url,
                headers=header,
                method='PUT',
                data=json.dumps(payload),
                validate_certs=False,
                timeout=timeout_in_sec
            )

            if resp.code != 200:
                logger.debug("LICReadiness failed. Response code: %d", resp.code)
                return None

            response = json.loads(resp.read())
            job_url = response['entry']['selfLink']
            response = self.fetchJobStatusJSON(job_url)
            status = response['entry']['content']['JobResponse']['Status']
            result = response['entry']['content']['JobResponse']['Result']
            if status == 'FAILED_BEFORE_COMPLETION':
                response = response['entry']['content']['JobResponse']
                if response.get('ResponseException'):
                    return None, response
            return status, result

        except Exception as e:
            logger.error("LICReadiness request failed: %s", str(e))
            return None

    def LicQueryLevel(self, system_uuid, system_name, type):
        url = f"https://{self.hmc_ip}/rest/api/uom/ManagedSystem/{system_uuid}/do/LICQueryLevel"

        header = {
            "X-API-Session": self.session,
            "Accept": "application/json",
            "Content-Type": "application/vnd.ibm.powervm.web+json; type=JobRequest"
        }

        timeout_in_sec = 3600
        job_result_dict = {}

        try:
            job_params = [
                {
                    "Metadata": {"Atom": ""},
                    "ParameterName": "managedSystem",
                    "ParameterValue": system_name
                },
                {
                    "Metadata": {"Atom": ""},
                    "ParameterName": "type",
                    "ParameterValue": type
                }
            ]

            if type == "io":
                job_params += [
                    {
                        "Metadata": {"Atom": ""},
                        "ParameterName": "attributes",
                        "ParameterValue": "partition,logical_device,mtms,location_code,current_level,device"
                    },
                    {
                        "Metadata": {"Atom": ""},
                        "ParameterName": "filter",
                        "ParameterValue": "os=vios"
                    }
                ]

            payload = {
                "JobRequest": {
                    "Metadata": {"Atom": ""},
                    "RequestedOperation": {
                        "Metadata": {"Atom": ""},
                        "OperationName": "LICQueryLevel",
                        "GroupName": "ManagedSystem"
                    },
                    "JobParameters": {
                        "Metadata": {"Atom": ""},
                        "JobParameter": job_params
                    }
                }
            }

            resp = open_url(
                url,
                headers=header,
                method='PUT',
                data=json.dumps(payload),
                validate_certs=False,
                timeout=timeout_in_sec
            )

            if resp.code != 200:
                logger.debug("LICQueryLevel failed for type %s. Response code: %s", type, resp.code)
                return {}

            response = json.loads(resp.read())
            job_url = response['entry']['selfLink']
            response = self.fetchJobStatusJSON(job_url)
            result = response['entry']['content']['JobResponse']['Result']
            status = response['entry']['content']['JobResponse']['Status']
            if status == 'FAILED_BEFORE_COMPLETION':
                response = response['entry']['content']['JobResponse']
                if response.get('ResponseException'):
                    return response

            value = ''
            for output in result:
                if status == 'COMPLETED_WITH_ERROR':
                    if output.get('ParameterName') == 'JOBRESULT_KEY_ERRORMSG':
                        value = output
                        return value
                if output.get('ParameterName') == 'JOBRESULT_KEY_OUTPUT':
                    value = output.get('ParameterValue')

            if type == 'sriov':
                if 'No results' in value:
                    adapter_id = value
                else:
                    adapter_id = [int(dict(item.split("=", 1) for item in line.split(","))["adapter_id"])
                                  for line in value.strip().split("\n")]
                job_result_dict["SRIOVAdapterUpdate"] = {"AdapterID": adapter_id}
            elif type == 'io':
                if 'No results' in value:
                    IOAdapterUpdate = value
                else:
                    IOAdapterUpdate = {}
                    for line in value.splitlines():
                        parts = line.split(",")
                        if len(parts) >= 2:
                            partition_id = parts[0].strip()
                            device = parts[1].strip()
                            IOAdapterUpdate.setdefault(partition_id, []).append(device)
                job_result_dict["IOAdapterUpdate"] = IOAdapterUpdate

            return job_result_dict

        except Exception as e:
            logger.error("LICQueryLevel request failed for type %s: %s", type, e)
            return {}

    def listViosUpdates(self, console_uuid, system_name, vios_name, source_file):
        url = f'https://{self.hmc_ip}/rest/api/uom/ManagementConsole/{console_uuid}/do/ListVIOSUpdates'
        header = {
            "X-API-Session": self.session,
            "Accept": "application/json",
            "Content-Type": "application/vnd.ibm.powervm.web+json; type=JobRequest"
        }
        payload = {
            "JobRequest": {
                "Metadata": {
                    "Atom": ""
                },
                "RequestedOperation": {
                    "Metadata": {
                        "Atom": ""
                    },
                    "OperationName": "ListVIOSUpdates",
                    "GroupName": "ManagementConsole"
                },
                "JobParameters": {
                    "Metadata": {
                        "Atom": ""
                    },
                    "JobParameter": [
                        {
                            "Metadata": {
                                "Atom": ""
                            },
                            "ParameterName": "Source",
                            "ParameterValue": source_file
                        },
                        {
                            "Metadata": {
                                "Atom": ""
                            },
                            "ParameterName": "SystemName",
                            "ParameterValue": system_name
                        },
                        {
                            "Metadata": {
                                "Atom": ""
                            },
                            "ParameterName": "VIOSName",
                            "ParameterValue": vios_name
                        }
                    ]
                }
            }
        }
        timeout_in_sec = 3600

        try:
            resp = open_url(
                url,
                headers=header,
                method='PUT',
                data=json.dumps(payload),
                validate_certs=False,
                timeout=timeout_in_sec
            )

            if resp.code != 200:
                logger.debug("listViosUpdates failed. Response code: %d", resp.code)
                return None

            response = json.loads(resp.read())
            job_url = response['entry']['selfLink']
            response = self.fetchJobStatusJSON(job_url)
            result = response['entry']['content']['JobResponse']['Result']
            status = response['entry']['content']['JobResponse']['Status']
            if status == 'FAILED_BEFORE_COMPLETION':
                response = response['entry']['content']['JobResponse']
                if response.get('ResponseException'):
                    return response
            value = ''
            for output in result:
                if output.get('ParameterName') == 'Updates':
                    value = output.get('ParameterValue')
            return value
        except Exception as e:
            logger.error("listViosUpdates request failed: %s", str(e))
            return None

    def LICQueryRepository(self, system_uuid, system_name, source_file, type="io", level=None,
                           hostname=None, username=None, password=None, directory=None, keyfile=None):
        url = f"https://{self.hmc_ip}/rest/api/uom/ManagedSystem/{system_uuid}/do/LICQueryRepository"
        header = {
            "X-API-Session": self.session,
            "Accept": "application/json",
            "Content-Type": "application/vnd.ibm.powervm.web+json; type=JobRequest"
        }

        job_parameters = [
            {
                "Metadata": {"Atom": ""},
                "ParameterName": "managedSystem",
                "ParameterValue": system_name
            },
            {
                "Metadata": {"Atom": ""},
                "ParameterName": "type",
                "ParameterValue": type
            },
            {
                "Metadata": {"Atom": ""},
                "ParameterName": "repository",
                "ParameterValue": source_file
            }
        ]

        if type == "sys":
            if level:
                job_parameters.append({
                    "Metadata": {"Atom": ""},
                    "ParameterName": "level",
                    "ParameterValue": level
                })
            job_parameters.append({
                "Metadata": {"Atom": ""},
                "ParameterName": "attributes",
                "ParameterValue": "lic_type,ecnumber,level,spname,concurrency,is_concurrent"
            })
        elif type == "io":
            job_parameters.append({
                "Metadata": {"Atom": ""},
                "ParameterName": "filter",
                "ParameterValue": "os=vios"
            })

        # Optional SFTP connection parameters
        for param_name, param_value in [
            ("hostname", hostname),
            ("username", username),
            ("password", password),
            ("directory", directory),
            ("keyfile", keyfile),
        ]:
            if param_value:
                job_parameters.append({
                    "Metadata": {"Atom": ""},
                    "ParameterName": param_name,
                    "ParameterValue": param_value
                })

        payload = {
            "JobRequest": {
                "Metadata": {"Atom": ""},
                "RequestedOperation": {
                    "Metadata": {"Atom": ""},
                    "OperationName": "LICQueryRepository",
                    "GroupName": "ManagedSystem"
                },
                "JobParameters": {
                    "Metadata": {"Atom": ""},
                    "JobParameter": job_parameters
                }
            }
        }
        timeout_in_sec = 3600
        try:
            resp = open_url(
                url,
                headers=header,
                method='PUT',
                data=json.dumps(payload),
                validate_certs=False,
                timeout=timeout_in_sec
            )

            if resp.code != 200:
                logger.debug("LICQueryRepository failed. Response code: %d", resp.code)
                return None

            response = json.loads(resp.read())
            job_url = response['entry']['selfLink']
            response = self.fetchJobStatusJSON(job_url)
            result = response['entry']['content']['JobResponse']['Result']
            status = response['entry']['content']['JobResponse']['Status']
            if status == 'FAILED_BEFORE_COMPLETION':
                response = response['entry']['content']['JobResponse']
                if response.get('ResponseException'):
                    return response
            value = {}
            for output in result:
                if status == 'COMPLETED_WITH_ERROR':
                    if output.get('ParameterName') == 'JOBRESULT_KEY_ERRORMSG':
                        value = output
                        break
                if output.get('ParameterName') == 'JOBRESULT_KEY_OUTPUT':
                    value = output
            return value
        except Exception as e:
            logger.error("LICQueryRepository request failed: %s", str(e))
            return None

    def PlatformUpdate(self, system_uuid, param):
        url = f"https://{self.hmc_ip}/rest/api/uom/ManagedSystem/{system_uuid}/do/PlatformUpdate"
        header = {
            "X-API-Session": self.session,
            "Accept": "application/json",
            "Content-Type": "application/vnd.ibm.powervm.web+json; type=JobRequest"
        }
        payload = {
            "JobRequest": {
                "Metadata": {
                    "Atom": ""
                },
                "RequestedOperation": {
                    "Metadata": {
                        "Atom": ""
                    },
                    "OperationName": "PlatformUpdate",
                    "GroupName": "ManagedSystem"
                },
                "JobParameters": {
                    "Metadata": {
                        "Atom": ""
                    },
                    "JobParameter": [
                        {
                            "Metadata": {
                                "Atom": ""
                            },
                            "ParameterName": "PlatformUpdateParameter",
                            "ParameterValue": param
                        }
                    ]
                }
            }
        }
        try:
            resp = open_url(
                url,
                headers=header,
                method='PUT',
                data=json.dumps(payload),
                validate_certs=False,
                timeout=3600
            )

            if resp.code != 200:
                logger.debug("Platform request failed. Response code: %d", resp.code)
                return None
            response = json.loads(resp.read())
            job_url = response['entry']['selfLink']
            response = self.fetchJobStatusJSON(job_url)
            status = response['entry']['content']['JobResponse']['Status']
            result = response['entry']['content']['JobResponse']['Result']
            if status == 'FAILED_BEFORE_COMPLETION':
                response = response['entry']['content']['JobResponse']
                if response.get('ResponseException'):
                    return response
            for output in result:
                if output.get("ParameterName") == "result":
                    steps_json = json.loads(output["ParameterValue"])
                    steps = steps_json.get("Steps", [])
                    return steps
        except Exception as e:
            logger.error("Platform request failed: %s", str(e))
            raise

    def fetchJobStatusJSON(self, job_url):
        header = {
            "X-API-Session": self.session,
            "Accept": "application/json",
            "Content-Type": "application/vnd.ibm.powervm.web+json; type=JobRequest"
        }

        try:
            resp = open_url(
                job_url,
                headers=header,
                method='GET',
                validate_certs=False,
                timeout=60
            )
            if resp.code != 200:
                logger.debug("Request failed. Response code: %d", resp.code)
                return None
            result = json.loads(resp.read())
            status = result['entry']['content']['JobResponse']['Status']
            if status == "RUNNING":
                time.sleep(10)
                return self.fetchJobStatusJSON(job_url)
            if status in ["COMPLETED_OK", "COMPLETED_WITH_ERROR", "FAILED_BEFORE_COMPLETION"]:
                return result

            raise HmcError(f"Unexpected job status: {status}")
        except Exception as e:
            logger.error("Failed to check job status: %s", e)
            raise

    def getAllPartitionProfiles(self, lpar_uuid, profile_name=None):
        url = "https://{0}/rest/api/uom/LogicalPartition/{1}/LogicalPartitionProfile".format(self.hmc_ip, lpar_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': '*/*'}
        resp = open_url(url,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=300)
        if resp.code != 200:
            logger.debug("Get of partition profile failed. Respsonse code: %d", resp.code)
            return None
        response = resp.read()
        if profile_name is None:
            return response
        elif profile_name is not None:
            post_response = xml_strip_namespace(response)
            entries = post_response.xpath("//entry")
            for entry in entries:
                profile_name_elem = entry.xpath(".//ProfileName")
                if profile_name_elem and profile_name_elem[0].text == profile_name:
                    atom_id_elem = entry.xpath(".//AtomID")
                    if atom_id_elem:
                        return atom_id_elem[0].text
            return None

    def getCurrentPartitionProfiles(self, lpar_uuid, profile_uuid):
        url = "https://{0}/rest/api/uom/LogicalPartition/{1}/LogicalPartitionProfile/{2}".format(self.hmc_ip, lpar_uuid, profile_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': '*/*'}
        resp = open_url(url,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=300)
        if resp.code != 200:
            logger.debug("Get of partition profile failed. Respsonse code: %d", resp.code)
            return None
        response = resp.read()
        return response

    def copyPartitionProfile(self, lpar_uuid, params):
        payload = {
            "JobRequest": {
                "Metadata": {
                    "Atom": ""
                },
                "RequestedOperation": {
                    "Metadata": {
                        "Atom": ""
                    },
                    "OperationName": "CopyProfile",
                    "GroupName": "LogicalPartition"
                },
                "JobParameters": {
                    "Metadata": {
                        "Atom": ""
                    },
                    "JobParameter": [
                        {
                            "Metadata": {
                                "Atom": ""
                            },
                            "ParameterName": "existingPartitionProfileName",
                            "ParameterValue": params['name']
                        },
                        {
                            "Metadata": {
                                "Atom": ""
                            },
                            "ParameterName": "newPartitionProfileName",
                            "ParameterValue": params['duplicate_prof_name']
                        }
                    ]
                }
            }
        }
        url = "https://{0}/rest/api/uom/LogicalPartition/{1}/do/CopyProfile".format(self.hmc_ip, lpar_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': 'application/json',
                  'Content-Type': 'application/vnd.ibm.powervm.web+json; type=JobRequest'}
        try:
            resp = open_url(url,
                            headers=header,
                            data=json.dumps(payload),
                            method='PUT',
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=300)
            resp = json.loads(resp.read())
            self_link = resp['entry']['selfLink']
            response = self.fetchJobStatusJSON(self_link)
            status = response['entry']['content']['JobResponse']['Status']
            if status == 'FAILED_BEFORE_COMPLETION':
                response = response['entry']['content']['JobResponse']
                if response.get('ResponseException'):
                    return response
            elif status == 'COMPLETED_OK':
                return 200
        except Exception as e:
            logger.debug("Error in copyPartitionProfile: %s", str(e))
            return f"Error: {str(e)}"

    def dedicatedProcessorAttributesXML(self, params):
        return '''
            <ProcessorAttributes kxe="false" kb="CUR" schemaVersion="V1_0">
                <Metadata>
                    <Atom/>
                </Metadata>
                <DedicatedProcessorConfiguration kxe="false" kb="CUD" schemaVersion="V1_0">
                    <Metadata>
                        <Atom/>
                    </Metadata>
                    <DesiredProcessors kb="CUD" kxe="false">{0}</DesiredProcessors>
                    <MaximumProcessors kb="CUD" kxe="false">{1}</MaximumProcessors>
                    <MinimumProcessors kxe="false" kb="CUD">{2}</MinimumProcessors>
                </DedicatedProcessorConfiguration>
                <HasDedicatedProcessors kxe="false" kb="CUD">{3}</HasDedicatedProcessors>
                <SharingMode kxe="false" kb="CUD">{4}</SharingMode>
            </ProcessorAttributes>
            '''.format(params['desired_processors'], params['maximum_processors'], params['minimum_processors'],
                       params['processor_mode'], params['allow_processor_sharing'])

    def dedicatedProcessorPayload(self, params):
        processor_attributes = self.dedicatedProcessorAttributesXML(params)
        if params['operating_system'] == 'IBM i':
            payload = '''
            <AssignAllResources kxe="false" kb="COD">false</AssignAllResources>
            <IOConfigurationInstance kb="CUD" kxe="false" schemaVersion="V1_0">
                <Metadata>
                    <Atom/>
                </Metadata>
                <MaximumVirtualIOSlots kb="CUD" kxe="false">10</MaximumVirtualIOSlots>
                <TaggedIO kb="CUD" kxe="false" schemaVersion="V1_0">
                    <Metadata>
                        <Atom/>
                    </Metadata>
                    <AlternateLoadSource kb="CUD" kxe="false">NONE</AlternateLoadSource>
                    <Console kxe="false" kb="CUR">HMC</Console>
                    <LoadSource kb="CUR" kxe="false">NONE</LoadSource>
                </TaggedIO>
                <VirtualOpticonnectPool kb="CUD" kxe="false">false</VirtualOpticonnectPool>
            </IOConfigurationInstance>
            {0}
            '''.format(processor_attributes)
        else:
            payload = '''
            <AssignAllResources kxe="false" kb="COD">false</AssignAllResources>
            {0}
            '''.format(processor_attributes)
        return payload

    def sharedProcessorAttributesXML(self, params):
        return '''
        <ProcessorAttributes kxe="false" kb="CUR" schemaVersion="V1_0">
            <Metadata>
                <Atom/>
            </Metadata>
            <HasDedicatedProcessors kxe="false" kb="CUD">{0}</HasDedicatedProcessors>
            <SharedProcessorConfiguration kxe="false" kb="CUD" schemaVersion="V1_0">
                <Metadata>
                    <Atom/>
                </Metadata>
                <DesiredProcessingUnits kb="CUD" kxe="false">{1}</DesiredProcessingUnits>
                <DesiredVirtualProcessors kxe="false" kb="CUD">{2}</DesiredVirtualProcessors>
                <MaximumProcessingUnits kb="CUD" kxe="false">{3}</MaximumProcessingUnits>
                <MaximumVirtualProcessors kxe="false" kb="CUD">{4}</MaximumVirtualProcessors>
                <MinimumProcessingUnits kxe="false" kb="CUD">{5}</MinimumProcessingUnits>
                <MinimumVirtualProcessors kb="CUD" kxe="false">{6}</MinimumVirtualProcessors>
                <SharedProcessorPoolID kb="CUD" kxe="false">{7}</SharedProcessorPoolID>
                <UncappedWeight kb="CUD" kxe="false">{8}</UncappedWeight>
            </SharedProcessorConfiguration>
            <SharingMode kb="CUD" kxe="false">{9}</SharingMode>
        </ProcessorAttributes>
        '''.format(params['processor_mode'], params['desired_processing_units'], params['desired_processors'],
                   params['maximum_processing_units'], params['maximum_processors'], params['minimum_processing_units'],
                   params['minimum_processors'], params['shared_processor_pool'], params['uncapped_weight'], params['sharing_mode'])

    def sharedProcessorPayload(self, params):
        processor_attributes = self.sharedProcessorAttributesXML(params)
        if params['operating_system'] == 'IBM i':
            payload = '''
            <AssignAllResources kb="COD" kxe="false">false</AssignAllResources>
            <IOConfigurationInstance kb="CUD" kxe="false" schemaVersion="V1_0">
                <Metadata>
                    <Atom/>
                </Metadata>
                <MaximumVirtualIOSlots kb="CUD" kxe="false">10</MaximumVirtualIOSlots>
                <TaggedIO kb="CUD" kxe="false" schemaVersion="V1_0">
                    <Metadata>
                        <Atom/>
                    </Metadata>
                    <AlternateLoadSource kb="CUD" kxe="false">NONE</AlternateLoadSource>
                    <Console kxe="false" kb="CUR">HMC</Console>
                    <LoadSource kb="CUR" kxe="false">NONE</LoadSource>
                </TaggedIO>
                <VirtualOpticonnectPool kb="CUD" kxe="false">false</VirtualOpticonnectPool>
            </IOConfigurationInstance>
            {0}
            '''.format(processor_attributes)
        else:
            payload = '''
            <AssignAllResources kb="COD" kxe="false">false</AssignAllResources>
            {0}
            '''.format(processor_attributes)
        return payload

    def buildMemoryPayloadXML(self, params):
        memory_payload = '''<ProfileMemory kb="CUR" kxe="false" schemaVersion="V1_0">
            <Metadata>
                <Atom/>
            </Metadata>
            <ActiveMemoryExpansionEnabled kb="CUD" kxe="false">{0}</ActiveMemoryExpansionEnabled>
            <ActiveMemorySharingEnabled kb="CUD" kxe="false">false</ActiveMemorySharingEnabled>
            <DesiredHugePageCount kb="CUD" kxe="false">{1}</DesiredHugePageCount>
            <DesiredMemory kxe="false" kb="CUD">{2}</DesiredMemory>
            <ExpansionFactor kb="CUD" kxe="false">{3}</ExpansionFactor>
            <HardwarePageTableRatio kb="CUD" kxe="false">{4}</HardwarePageTableRatio>
            <MaximumHugePageCount kb="CUD" kxe="false">{5}</MaximumHugePageCount>
            <MaximumMemory kb="CUD" kxe="false">{6}</MaximumMemory>
            <MinimumHugePageCount kb="CUD" kxe="false">{7}</MinimumHugePageCount>
            <MinimumMemory kxe="false" kb="CUD">{8}</MinimumMemory>
            <DesiredPhysicalPageTableRatio ksv="V1_6_0" kb="CUD" kxe="false">{9}</DesiredPhysicalPageTableRatio>
            </ProfileMemory>
            <ProfileName kb="CUR" kxe="false">{10}</ProfileName>
            </LogicalPartitionProfile:LogicalPartitionProfile>
            '''.format(str(params['active_memory_expansion']).lower(),
                       params['desired_huge_pagecount'], params['desired_memory'], params['expansion_factor'],
                       params['hardware_page_tableratio'], params['maximum_huge_pagecount'], params['maximum_memory'],
                       params['minimum_huge_pagecount'], params['minimum_memory'],
                       params['desired_physical_page_tableratio'], params['name'])
        return memory_payload

    def createPartitionProfile(self, lpar_uuid, params):
        partiton_profile_xmlstr = ''
        template_partition_profile = '''<LogicalPartitionProfile:LogicalPartitionProfile
                                    xmlns:LogicalPartitionProfile="http://www.ibm.com/xmlns/systems/power/firmware/uom/mc/2012_10/"
                                    xmlns="http://www.ibm.com/xmlns/systems/power/firmware/uom/mc/2012_10/"
                                    xmlns:ns2="http://www.w3.org/XML/1998/namespace/k2" schemaVersion="V1_0">'''
        partiton_profile_xmlstr += template_partition_profile
        if params['processor_mode'].lower() == 'false':
            partiton_profile_xmlstr += self.sharedProcessorPayload(params)
        else:
            partiton_profile_xmlstr += self.dedicatedProcessorPayload(params)
        partiton_profile_xmlstr += self.buildMemoryPayloadXML(params)
        if 'sharing_mode' in params:
            if params['sharing_mode'] == 'capped':
                xml_tree = etree.fromstring(partiton_profile_xmlstr.encode())
                for elem in xml_tree.xpath('.//*[local-name()="UncappedWeight"]'):
                    elem.getparent().remove(elem)
                    partiton_profile_xmlstr = etree.tostring(xml_tree, encoding='unicode')
        url = "https://{0}/rest/api/uom/LogicalPartition/{1}/LogicalPartitionProfile".format(self.hmc_ip, lpar_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': '*/*',
                  'Content-Type': 'application/vnd.ibm.powervm.uom+xml; type=LogicalPartitionProfile'}
        try:
            resp = open_url(url,
                            headers=header,
                            data=partiton_profile_xmlstr,
                            method='PUT',
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=300)
            response = resp.read()
        except Exception as e:
            if hasattr(e, 'read'):
                response = e.read()
                post_response = xml_strip_namespace(response)
                error_message_elements = post_response.xpath("//Message")
                logger.debug(response)
                return e.code, error_message_elements[0].text.strip()
            else:
                return f"Error: {str(e)}"
        post_response = xml_strip_namespace(response)
        profile_name_elements = post_response.xpath("//ProfileName")
        if profile_name_elements:
            return 200, profile_name_elements[0].text
        return "Error: Profile creation failed with unknown error"

    def updatePartitionProfile(self, lpar_uuid, partition_uuid, patched_xml, force=False):
        url = "https://{0}/rest/api/uom/LogicalPartition/{1}/LogicalPartitionProfile/{2}".format(self.hmc_ip, lpar_uuid, partition_uuid)
        if force:
            url += "?force=true"
        header = {'X-API-Session': self.session,
                  'Accept': '*/*',
                  'Content-Type': 'application/vnd.ibm.powervm.uom+xml; type=LogicalPartitionProfile'}
        try:
            resp = open_url(url,
                            headers=header,
                            data=patched_xml,
                            method='POST',
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=300)
            response = resp.read()
        except Exception as e:
            if hasattr(e, 'read'):
                response = e.read()
                post_response = xml_strip_namespace(response)
                error_message_elements = post_response.xpath("//Message")
                logger.debug(response)
                return e.code, error_message_elements[0].text.strip()
            else:
                return f"Error: {str(e)}"
        post_response = xml_strip_namespace(response)
        profile_name_elements = post_response.xpath("//ProfileName")
        if profile_name_elements:
            return 200, profile_name_elements[0].text
        return "Error: Profile Updation failed with unknown error"

    def getVirtualSwitches(self, system_uuid):
        url = "https://{0}/rest/api/uom/ManagedSystem/{1}/VirtualSwitch".format(self.hmc_ip, system_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': 'application/vnd.ibm.powervm.uom+xml; type=VirtualSwitch'}

        try:
            resp = open_url(url,
                            headers=header,
                            method='GET',
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=300)

            if resp.code == 204:
                return None

            response = resp.read()
            if not response:
                return None

            virtual_switches_root = xml_strip_namespace(response)
            return virtual_switches_root
        except Exception as error:
            logger.debug("Get of Virtual Switches failed: %s", repr(error))
            raise

    def createVirtualSwitch(self, system_uuid, switch_name, switch_mode):
        url = "https://{0}/rest/api/uom/ManagedSystem/{1}/VirtualSwitch".format(self.hmc_ip, system_uuid)
        header = {'X-API-Session': self.session,
                  'Content-Type': 'application/vnd.ibm.powervm.uom+xml; type=VirtualSwitch',
                  'Accept': 'application/atom+xml'}

        payload = '''<VirtualSwitch schemaVersion="V1_0">
            <SwitchMode kb="CUD" kxe="false">{0}</SwitchMode>
            <SwitchName kxe="false" kb="CUD">{1}</SwitchName>
            <VirtualNetworks kb="CUD" kxe="false"/>
        </VirtualSwitch>'''.format(switch_mode, switch_name)
        payload = payload.replace("VirtualSwitch", VSWITCH_NS, 1)
        try:
            resp = open_url(url,
                            headers=header,
                            data=payload,
                            method='PUT',
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=300)

            response = resp.read()
            if not response:
                return None
            virtual_switch_dom = xml_strip_namespace(response)
            if virtual_switch_dom is None:
                return None
            return virtual_switch_dom
        except Exception:
            raise

    def updateVirtualSwitch(self, system_uuid, switch_uuid, switch_name, switch_mode, switch_id):
        url = "https://{0}/rest/api/uom/ManagedSystem/{1}/VirtualSwitch/{2}".format(self.hmc_ip, system_uuid, switch_uuid)
        header = {'X-API-Session': self.session,
                  'Content-Type': 'application/vnd.ibm.powervm.uom+xml; type=VirtualSwitch',
                  'Accept': 'application/atom+xml'}

        payload = '''<VirtualSwitch schemaVersion="V1_0">
            <SwitchMode kb="CUD" kxe="false">{0}</SwitchMode>
            <SwitchName kxe="false" kb="CUD">{1}</SwitchName>
            <VirtualNetworks kb="CUD" kxe="false"/>
        </VirtualSwitch>'''.format(switch_mode, switch_name)
        payload = payload.replace("VirtualSwitch", VSWITCH_NS, 1)
        try:
            resp = open_url(url,
                            headers=header,
                            data=payload,
                            method='POST',
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=300)
            response = resp.read()
            if not response:
                return None
            virtual_switch_dom = xml_strip_namespace(response)
            return virtual_switch_dom
        except Exception:
            raise

    def getVirtualSwitchByName(self, system_uuid, switch_name):
        try:
            virtual_switches_dom = self.getVirtualSwitches(system_uuid)
            if not virtual_switches_dom:
                return None, None, None

            switches = virtual_switches_dom.xpath("//VirtualSwitch")
            for switch in switches:
                name_elem = switch.xpath(".//SwitchName")
                if name_elem and name_elem[0].text == switch_name:
                    uuid_elem = switch.xpath(".//Metadata/Atom/AtomID")
                    switch_uuid = uuid_elem[0].text if uuid_elem else None
                    id_elem = switch.xpath(".//SwitchID")
                    switch_id = id_elem[0].text if id_elem else None
                    mode_elem = switch.xpath(".//SwitchMode")
                    switch_mode = mode_elem[0].text if mode_elem else None
                    return switch_uuid, switch_id, switch_mode

            return None, None, None
        except Exception as error:
            logger.debug("Get Virtual Switch by name failed: %s", repr(error))
            raise

    def deleteVirtualSwitch(self, system_uuid, switch_uuid):
        url = "https://{0}/rest/api/uom/ManagedSystem/{1}/VirtualSwitch/{2}".format(self.hmc_ip, system_uuid, switch_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': 'application/atom+xml'}
        try:
            open_url(url,
                     headers=header,
                     method='DELETE',
                     validate_certs=False,
                     force_basic_auth=True,
                     timeout=300)

            return True
        except Exception:
            raise

    def getVirtualNetworks(self, system_uuid):
        url = "https://{0}/rest/api/uom/ManagedSystem/{1}/VirtualNetwork".format(self.hmc_ip, system_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': 'application/vnd.ibm.powervm.uom+xml; type=VirtualNetwork'}

        try:
            resp = open_url(url,
                            headers=header,
                            method='GET',
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=300)

            if resp.code == 204:
                return None

            response = resp.read()
            if not response:
                return None

            virtual_networks_root = xml_strip_namespace(response)
            return virtual_networks_root
        except Exception as error:
            logger.debug("Get of Virtual Networks failed: %s", repr(error))
            raise

    def createVirtualNetwork(self, system_uuid, network_name, network_vlan_id, switch_href, switch_id, switch_name, tagged_network):
        url = "https://{0}/rest/api/uom/ManagedSystem/{1}/VirtualNetwork".format(self.hmc_ip, system_uuid)
        header = {'X-API-Session': self.session,
                  'Content-Type': 'application/vnd.ibm.powervm.uom+xml; type=VirtualNetwork',
                  'Accept': 'application/atom+xml'}

        tagged_str = 'true' if tagged_network else 'false'
        payload = '''<VirtualNetwork schemaVersion="V1_0">
                <AssociatedSwitch kxe="false" kb="COD" href="{0}" rel="related"/>
                <NetworkName kxe="false" kb="CUR">{1}</NetworkName>
                <NetworkVLANID kxe="false" kb="COD">{2}</NetworkVLANID>
                <VswitchID kb="ROR" kxe="false">{3}</VswitchID>
                <VirtualSwitchName ksv="V1_12_0" kb="ROR" kxe="false">{4}</VirtualSwitchName>
                <TaggedNetwork kxe="false" kb="COD">{5}</TaggedNetwork>
            </VirtualNetwork>'''.format(switch_href, network_name, network_vlan_id, switch_id, switch_name, tagged_str)
        payload = payload.replace("VirtualNetwork", VNETWORK_NS, 1)
        try:
            resp = open_url(url,
                            headers=header,
                            data=payload,
                            method='PUT',
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=300)

            response = resp.read()
            if not response:
                return None
            virtual_network_dom = xml_strip_namespace(response)
            if virtual_network_dom is None:
                return None
            return virtual_network_dom
        except Exception:
            raise

    def updateVirtualNetwork(self, system_uuid, network_uuid, new_network_name):
        url = "https://{0}/rest/api/uom/ManagedSystem/{1}/VirtualNetwork/{2}".format(self.hmc_ip, system_uuid, network_uuid)
        header = {'X-API-Session': self.session,
                  'Content-Type': 'application/vnd.ibm.powervm.uom+xml; type=VirtualNetwork',
                  'Accept': 'application/atom+xml'}
        payload = '''<VirtualNetwork schemaVersion="V1_0">
            <NetworkName kxe="false" kb="CUR">{0}</NetworkName>
        </VirtualNetwork>'''.format(new_network_name)
        payload = payload.replace("VirtualNetwork", VNETWORK_NS, 1)
        try:
            resp = open_url(url,
                            headers=header,
                            data=payload,
                            method='POST',
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=300)

            response = resp.read()
            if not response:
                return None
            virtual_network_dom = xml_strip_namespace(response)
            if virtual_network_dom is None:
                return None
            return virtual_network_dom
        except Exception:
            raise

    def deleteVirtualNetwork(self, system_uuid, network_uuid):
        url = "https://{0}/rest/api/uom/ManagedSystem/{1}/VirtualNetwork/{2}".format(self.hmc_ip, system_uuid, network_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': 'application/atom+xml'}
        try:
            open_url(url,
                     headers=header,
                     method='DELETE',
                     validate_certs=False,
                     force_basic_auth=True,
                     timeout=300)

            return True
        except Exception:
            raise

    def getViosClientNetworkAdapters(self, vios_uuid):
        """Return a list of parsed CNA DOM elements for *vios_uuid* (VirtualIOServer), or an empty list."""
        url = "https://{0}/rest/api/uom/VirtualIOServer/{1}/ClientNetworkAdapter".format(
            self.hmc_ip, vios_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': 'application/vnd.ibm.powervm.uom+xml; type=ClientNetworkAdapter'}

        try:
            resp = open_url(url,
                            headers=header,
                            method='GET',
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=300)

            if resp.code == 204:
                return []

            response = resp.read()
            if not response:
                return []

            root = xml_strip_namespace(response)
            if root is None:
                logger.debug("getViosClientNetworkAdapters: xml_strip_namespace returned None")
                return []
            return root.xpath("//ClientNetworkAdapter")
        except Exception as error:
            logger.debug("Get of VIOS Client Network Adapters failed: %s", repr(error))
            raise

    def getClientNetworkAdapters(self, lpar_uuid):
        """Return a list of parsed CNA DOM elements for *lpar_uuid*, or an empty list."""
        url = "https://{0}/rest/api/uom/LogicalPartition/{1}/ClientNetworkAdapter".format(
            self.hmc_ip, lpar_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': 'application/vnd.ibm.powervm.uom+xml; type=ClientNetworkAdapter'}

        try:
            resp = open_url(url,
                            headers=header,
                            method='GET',
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=300)

            if resp.code == 204:
                return []

            response = resp.read()
            if not response:
                return []

            root = xml_strip_namespace(response)
            if root is None:
                logger.debug("getClientNetworkAdapters: xml_strip_namespace returned None")
                return []
            return root.xpath("//ClientNetworkAdapter")
        except Exception as error:
            logger.debug("Get of Client Network Adapters failed: %s", repr(error))
            raise

    def createClientNetworkAdapter(self, lpar_uuid, system_uuid, network_uuid,
                                   vlan_id, switch_href, virtual_ethernet_adapter_id=None,
                                   mac_address=None, allowed_os_mac_addresses=None,
                                   tagged_vlan_ids=None, partition_type='LogicalPartition'):
        """Create a Client Network Adapter on *lpar_uuid* connected to *network_uuid*.

        PUTs a minimal ClientNetworkAdapter XML to the sub-resource collection URL.
        vlan_id and switch_href are sourced from the target VirtualNetwork.
        allowed_os_mac_addresses: string value for AllowedOperatingSystemMACAddresses
            (e.g. 'ALL', 'NONE', or space-separated MACs). Defaults to 'ALL'.
        tagged_vlan_ids: space-separated VLAN IDs string for TaggedVLANIDs when the
            new adapter should have tagged VLAN support enabled from creation.
        partition_type: 'LogicalPartition' (default) or 'VirtualIOServer'.
        """
        url = "https://{0}/rest/api/uom/{1}/{2}/ClientNetworkAdapter".format(
            self.hmc_ip, partition_type, lpar_uuid)

        # Build the virtual network href exactly as the HMC returns it on GET.
        vn_href = "https://{0}:443/rest/api/uom/ManagedSystem/{1}/VirtualNetwork/{2}".format(
            self.hmc_ip, system_uuid, network_uuid)

        vsn_payload = ''
        if virtual_ethernet_adapter_id is not None:
            vsn_payload = '\n    <VirtualSlotNumber kb="COD" kxe="false">{0}</VirtualSlotNumber>'.format(
                virtual_ethernet_adapter_id)

        mac_payload = ''
        if mac_address is not None:
            mac_payload = '\n    <MACAddress kxe="false" kb="CUR">{0}</MACAddress>'.format(
                mac_address.replace(':', '').upper())

        _allowed_os_mac = allowed_os_mac_addresses if allowed_os_mac_addresses is not None else 'ALL'
        allowed_os_mac_payload = '\n    <AllowedOperatingSystemMACAddresses kb="CUD" kxe="false">{0}</AllowedOperatingSystemMACAddresses>'.format(
            _allowed_os_mac)

        if tagged_vlan_ids:
            tvlan_payload = (
                '\n    <TaggedVLANIDs kxe="false" kb="CUA">{0}</TaggedVLANIDs>'
                '\n    <TaggedVLANSupported kb="CUA" kxe="false">true</TaggedVLANSupported>'
            ).format(tagged_vlan_ids)
        else:
            tvlan_payload = '\n    <TaggedVLANSupported kb="CUA" kxe="false">false</TaggedVLANSupported>'

        payload = '''<ClientNetworkAdapter schemaVersion="V1_0">
    <Metadata><Atom/></Metadata>{0}{1}{2}
    <PortVLANID kxe="false" kb="CUR">{3}</PortVLANID>
    <QualityOfServicePriorityEnabled kxe="false" kb="CUD">false</QualityOfServicePriorityEnabled>{4}
    <AssociatedVirtualSwitch kb="CUD" kxe="false">
        <link href="{5}" rel="related"/>
    </AssociatedVirtualSwitch>
    <VirtualNetworks kb="CUR" kxe="false">
        <link href="{6}" rel="related"/>
    </VirtualNetworks>
</ClientNetworkAdapter>'''.format(vsn_payload, mac_payload, allowed_os_mac_payload,
                                  vlan_id, tvlan_payload, switch_href, vn_href)
        payload = payload.replace("ClientNetworkAdapter", CNA_NS, 1)

        header = {'X-API-Session': self.session,
                  'Content-Type': 'application/vnd.ibm.powervm.uom+xml; type=ClientNetworkAdapter',
                  'Accept': 'application/atom+xml'}

        logger.debug("createClientNetworkAdapter URL: %s", url)
        logger.debug("createClientNetworkAdapter PAYLOAD:\n%s", payload)

        resp = open_url(url,
                        headers=header,
                        data=payload,
                        method='POST' if mac_address is not None else 'PUT',
                        validate_certs=False,
                        force_basic_auth=True,
                        timeout=300)

        logger.debug("createClientNetworkAdapter response code: %s", resp.code)
        response = resp.read()
        if not response:
            return True
        try:
            return xml_strip_namespace(response)
        except Exception:
            # A non-XML or empty body just means success (e.g. 201 Created with no body)
            return True

    def updateClientNetworkAdapter(self, lpar_uuid, adapter_uuid,
                                   mac_address=None, allowed_os_mac_addresses=None,
                                   qos_priority_enabled=None, qos_priority=None,
                                   vsi_type_id=None, vsi_manager_id=None, vsi_type_version=None,
                                   virtual_network_href=None, tagged_vlan_id=None,
                                   detach_vn_href=None, detach_tagged_vlan_id=None,
                                   partition_type='LogicalPartition'):
        """Update a Client Network Adapter's settings (MAC, QoS, OS MAC restrictions, 802.1Qbg).

        The HMC requires VirtualSlotNumber and PortVLANID in every POST, so both are
        fetched via GET first. Only the fields the caller wants to change are included
        beyond that. MAC addresses in mac_address and allowed_os_mac_addresses are
        normalised to no-colon uppercase format as expected by the HMC API.
        tagged_vlan_id: when adding a new VirtualNetwork to an existing slot, pass the
        VLAN ID of the new network so it is merged into the TaggedVLANIDs field.
        detach_vn_href: href of a VirtualNetwork link to *remove* from VirtualNetworks.
        detach_tagged_vlan_id: VLAN ID string to *remove* from TaggedVLANIDs after detach.
        partition_type: 'LogicalPartition' (default) or 'VirtualIOServer'.
        """
        url = "https://{0}/rest/api/uom/{1}/{2}/ClientNetworkAdapter/{3}".format(
            self.hmc_ip, partition_type, lpar_uuid, adapter_uuid)

        # HMC API expects MAC addresses without colons (e.g. B608907CA607)
        def _strip_colons(mac):
            return mac.replace(':', '').upper()

        # Fetch the current CNA XML — needed to replay as POST with changes applied
        get_header = {'X-API-Session': self.session, 'Accept': 'application/atom+xml'}
        get_resp = open_url(url, headers=get_header, method='GET',
                            validate_certs=False, force_basic_auth=True, timeout=300)
        raw_get = get_resp.read()

        # Parse preserving namespaces so we can re-serialise faithfully
        from lxml import etree as _et
        ns_parser = _et.XMLParser(recover=True, encoding='utf-8')
        ns_root = _et.fromstring(raw_get if isinstance(raw_get, bytes) else raw_get.encode('utf-8'),
                                 ns_parser)

        # Locate the ClientNetworkAdapter element inside the Atom <content> wrapper
        _UOM_NS = 'http://www.ibm.com/xmlns/systems/power/firmware/uom/mc/2012_10/'
        _cna_tag = '{{{0}}}ClientNetworkAdapter'.format(_UOM_NS)
        cna_el = ns_root.find('.//' + _cna_tag)
        if cna_el is None:
            # Fallback: root may already be the CNA
            cna_el = ns_root

        def _set_ns_field(el, local_name, value):
            """Update or insert a UOM namespace child element by local name.

            For existing elements the kb attribute is left exactly as the HMC
            returned it on GET — the HMC schema dictates which value is valid
            per field and changing it (e.g. CUR→CUD) causes REST0001.
            Only newly inserted elements get kb="CUD".
            """
            qname = '{{{0}}}{1}'.format(_UOM_NS, local_name)
            nodes = el.findall('.//' + qname)
            if nodes:
                nodes[0].text = value
            else:
                new_el = _et.SubElement(el, qname)
                new_el.set('kb', 'CUD')
                new_el.set('kxe', 'false')
                new_el.text = value

        if mac_address is not None:
            _set_ns_field(cna_el, 'MACAddress', _strip_colons(mac_address))
        if virtual_network_href is not None:
            qname = '{{{0}}}VirtualNetworks'.format(_UOM_NS)
            virtual_networks_el = cna_el.find('.//' + qname)
            if virtual_networks_el is None:
                virtual_networks_el = _et.SubElement(cna_el, qname)
                virtual_networks_el.set('kb', 'CUR')
                virtual_networks_el.set('kxe', 'false')
            _LINK_TAG = '{{{0}}}link'.format(_UOM_NS)
            existing_links = virtual_networks_el.findall('.//' + _LINK_TAG)
            if not any(link.get('href') == virtual_network_href for link in existing_links):
                new_link = _et.SubElement(virtual_networks_el, _LINK_TAG)
                new_link.set('href', virtual_network_href)
                new_link.set('rel', 'related')
        _needs_tvlan_fixup = False
        if tagged_vlan_id is not None:
            # Merge the new VLAN ID into the space-separated TaggedVLANIDs list and
            # ensure TaggedVLANSupported is true, as required by the HMC when multiple
            # virtual networks share a slot.
            _tvlan_qname = '{{{0}}}TaggedVLANIDs'.format(_UOM_NS)
            _tvsup_qname = '{{{0}}}TaggedVLANSupported'.format(_UOM_NS)
            tvlan_nodes = cna_el.findall('.//' + _tvlan_qname)
            _vlan_str = str(tagged_vlan_id)
            if tvlan_nodes:
                existing_ids = tvlan_nodes[0].text.split() if tvlan_nodes[0].text else []
                if _vlan_str not in existing_ids:
                    existing_ids.append(_vlan_str)
                tvlan_nodes[0].text = ' '.join(existing_ids)
            else:
                # lxml always serialises a new element with the registered prefix
                # for the UOM namespace (ClientNetworkAdapter:) rather than the
                # default namespace, which the HMC rejects. Work around this by
                # inserting using makeelement (inherits nsmap) and fixing up the
                # serialised string afterwards.
                tvsup_nodes = cna_el.findall('.//' + _tvsup_qname)
                if tvsup_nodes:
                    new_tvlan = tvsup_nodes[0].makeelement(_tvlan_qname,
                                                           {'kb': 'CUA', 'kxe': 'false'})
                    new_tvlan.text = _vlan_str
                    cna_el.insert(list(cna_el).index(tvsup_nodes[0]), new_tvlan)
                else:
                    new_tvlan = cna_el.makeelement(_tvlan_qname,
                                                   {'kb': 'CUA', 'kxe': 'false'})
                    new_tvlan.text = _vlan_str
                    cna_el.append(new_tvlan)
                _needs_tvlan_fixup = True
            # Ensure TaggedVLANSupported is set to true
            tvsup_nodes = cna_el.findall('.//' + _tvsup_qname)
            if tvsup_nodes:
                tvsup_nodes[0].text = 'true'
            else:
                _set_ns_field(cna_el, 'TaggedVLANSupported', 'true')
                _needs_tvlan_fixup = True
        if detach_vn_href is not None:
            # Remove the specified VirtualNetwork link from the VirtualNetworks element
            _vn_qname = '{{{0}}}VirtualNetworks'.format(_UOM_NS)
            _LINK_TAG = '{{{0}}}link'.format(_UOM_NS)
            vn_el = cna_el.find('.//' + _vn_qname)
            if vn_el is not None:
                for link in vn_el.findall('.//' + _LINK_TAG):
                    if link.get('href') == detach_vn_href:
                        vn_el.remove(link)
                        break
        if detach_tagged_vlan_id is not None:
            # Remove the specified VLAN ID from the space-separated TaggedVLANIDs list.
            # If the list becomes empty afterwards, set TaggedVLANSupported to false and
            # clear the TaggedVLANIDs text rather than leaving an empty element.
            _tvlan_qname = '{{{0}}}TaggedVLANIDs'.format(_UOM_NS)
            _tvsup_qname = '{{{0}}}TaggedVLANSupported'.format(_UOM_NS)
            tvlan_nodes = cna_el.findall('.//' + _tvlan_qname)
            if tvlan_nodes:
                existing_ids = tvlan_nodes[0].text.split() if tvlan_nodes[0].text else []
                updated_ids = [v for v in existing_ids if v != str(detach_tagged_vlan_id)]
                if updated_ids:
                    tvlan_nodes[0].text = ' '.join(updated_ids)
                else:
                    tvlan_nodes[0].text = ''
                    # No tagged VLANs remain — disable TaggedVLANSupported
                    tvsup_nodes = cna_el.findall('.//' + _tvsup_qname)
                    if tvsup_nodes:
                        tvsup_nodes[0].text = 'false'
        if allowed_os_mac_addresses is not None:
            if allowed_os_mac_addresses in ('ALL', 'NONE'):
                _oa = allowed_os_mac_addresses
            else:
                _oa = ' '.join(_strip_colons(m) for m in allowed_os_mac_addresses.split())
            _set_ns_field(cna_el, 'AllowedOperatingSystemMACAddresses', _oa)
        if qos_priority_enabled is not None:
            _set_ns_field(cna_el, 'QualityOfServicePriorityEnabled',
                          'true' if qos_priority_enabled else 'false')
        _needs_qp_fixup = False
        _qp_qname = '{{{0}}}QualityOfServicePriority'.format(_UOM_NS)
        _qpe_qname = '{{{0}}}QualityOfServicePriorityEnabled'.format(_UOM_NS)
        if qos_priority is not None:
            _qp_nodes = cna_el.findall('.//' + _qp_qname)
            if _qp_nodes:
                _qp_nodes[0].text = str(qos_priority)
            else:
                # Insert immediately BEFORE QualityOfServicePriorityEnabled —
                # the HMC schema places QualityOfServicePriority before the
                # Enabled flag. Use makeelement so the new node inherits the
                # nsmap and lxml doesn't serialise it with a prefixed tag name.
                _qpe_nodes = cna_el.findall('.//' + _qpe_qname)
                new_qp = (_qpe_nodes[0] if _qpe_nodes else cna_el).makeelement(
                    _qp_qname, {'kb': 'CUD', 'kxe': 'false'})
                new_qp.text = str(qos_priority)
                if _qpe_nodes:
                    cna_el.insert(list(cna_el).index(_qpe_nodes[0]), new_qp)
                else:
                    cna_el.append(new_qp)
                _needs_qp_fixup = True
        elif qos_priority_enabled:
            # HMC REST0149: enabling QoS requires QualityOfServicePriority in the
            # same payload. If the caller did not supply a value, read the current
            # element value from the GET response and write it back unchanged.
            # Fall back to '0' if the element was absent (adapter never had QoS).
            _qp_nodes = cna_el.findall('.//' + _qp_qname)
            if _qp_nodes:
                # Element already in GET response — text is fine as-is, nothing to do.
                pass
            else:
                # Element absent — insert BEFORE QualityOfServicePriorityEnabled.
                _qpe_nodes = cna_el.findall('.//' + _qpe_qname)
                new_qp = (_qpe_nodes[0] if _qpe_nodes else cna_el).makeelement(
                    _qp_qname, {'kb': 'CUD', 'kxe': 'false'})
                new_qp.text = '0'
                if _qpe_nodes:
                    cna_el.insert(list(cna_el).index(_qpe_nodes[0]), new_qp)
                else:
                    cna_el.append(new_qp)
                _needs_qp_fixup = True
        if vsi_type_id is not None:
            _set_ns_field(cna_el, 'VirtualStationInterfaceTypeID', str(vsi_type_id))
        if vsi_manager_id is not None:
            _set_ns_field(cna_el, 'VirtualStationInterfaceManagerID', str(vsi_manager_id))
        if vsi_type_version is not None:
            _set_ns_field(cna_el, 'VirtualStationInterfaceTypeVersion', str(vsi_type_version))

        # Re-serialise the modified CNA element preserving its original namespaces
        payload = _et.tostring(cna_el, encoding='unicode')

        # lxml serialises newly inserted UOM elements with the ClientNetworkAdapter:
        # prefix instead of the default namespace. Strip that prefix from all
        # affected leaf elements so the HMC receives well-formed XML.
        if _needs_tvlan_fixup or _needs_qp_fixup:
            _uom_prefix = next(
                (p for p, ns in cna_el.nsmap.items() if ns == _UOM_NS and p is not None),
                None)
            if _uom_prefix:
                _fixup_locals = []
                if _needs_tvlan_fixup:
                    _fixup_locals += ['TaggedVLANIDs', 'TaggedVLANSupported']
                if _needs_qp_fixup:
                    _fixup_locals += ['QualityOfServicePriority']
                for _local in _fixup_locals:
                    payload = payload.replace(
                        '<%s:%s ' % (_uom_prefix, _local), '<%s ' % _local)
                    payload = payload.replace(
                        '</%s:%s>' % (_uom_prefix, _local), '</%s>' % _local)

        logger.debug("updateClientNetworkAdapter POST payload:\n%s", payload)

        post_header = {'X-API-Session': self.session,
                       'Content-Type': 'application/vnd.ibm.powervm.uom+xml; type=ClientNetworkAdapter',
                       'Accept': 'application/atom+xml'}

        try:
            resp = open_url(url,
                            headers=post_header,
                            data=payload,
                            method='POST',
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=300)

            response = resp.read()
            logger.debug(url)
            logger.debug(response)
            if not response:
                return True

            adapter_dom = xml_strip_namespace(response)
            return adapter_dom
        except Exception:
            raise

    def deleteClientNetworkAdapter(self, lpar_uuid, adapter_uuid,
                                   partition_type='LogicalPartition'):
        """Delete the Client Network Adapter identified by *adapter_uuid* from *lpar_uuid*.

        partition_type: 'LogicalPartition' (default) or 'VirtualIOServer'.
        """
        url = "https://{0}/rest/api/uom/{1}/{2}/ClientNetworkAdapter/{3}".format(
            self.hmc_ip, partition_type, lpar_uuid, adapter_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': 'application/atom+xml'}
        try:
            open_url(url,
                     headers=header,
                     method='DELETE',
                     validate_certs=False,
                     force_basic_auth=True,
                     timeout=300)

            return True
        except Exception:
            raise

    def getNetworkBridges(self, system_uuid):
        url = "https://{0}/rest/api/uom/ManagedSystem/{1}/NetworkBridge".format(self.hmc_ip, system_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': 'application/vnd.ibm.powervm.uom+xml; type=NetworkBridge'}
        try:
            resp = open_url(url,
                            headers=header,
                            method='GET',
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=300)
            if resp.code == 204:
                return None
            response = resp.read()
            if not response:
                return None
            return xml_strip_namespace(response)
        except Exception as error:
            logger.debug("Get of Network Bridges failed: %s", repr(error))
            raise

    @staticmethod
    def _sea_xml(vios_href, is_primary, cfg, jumbo_frames=None, qos_mode=None, large_send=None):
        """Return the XML fragment list for one SharedEthernetAdapter block.

        Used in the bridge CREATE (PUT) payload and when appending a new secondary
        SEA during a state=update load-balancing enable.

        Element order matches the HMC GET response XSD sequence:
          Metadata → AssignedVirtualIOServer → BackingDeviceChoice →
          JumboFramesEnabled → LargeSend → QualityOfServiceMode →
          TrunkAdapters (empty) → IsPrimary

        DeviceName inside EthernetBackingDevice must use kb="ROR" per HMC schema.

        cfg is a dict with optional key: backing_device.
        large_send: when not None, emits a <LargeSend> element — pass the inherited
          value from the primary SEA to prevent the HMC defaulting to true.
        (ip_address, netmask, address_to_ping, and high_availability_mode are not
        accepted by the HMC PUT schema at create time.)
        """
        primary_str = 'true' if is_primary else 'false'
        parts = ['<SharedEthernetAdapter schemaVersion="V1_0">',
                 '<Metadata><Atom/></Metadata>',
                 '<AssignedVirtualIOServer kb="CUD" kxe="false"'
                 ' href="{0}" rel="related"/>'.format(vios_href)]
        # BackingDeviceChoice — immediately after AssignedVirtualIOServer.
        # DeviceName uses kb="ROR" as required by the HMC XSD.
        backing = cfg.get('backing_device') if cfg else None
        if backing:
            parts += ['<BackingDeviceChoice kb="CUD" kxe="false">',
                      '<EthernetBackingDevice schemaVersion="V1_0">',
                      '<Metadata><Atom/></Metadata>',
                      '<DeviceName kb="ROR" kxe="false">{0}</DeviceName>'.format(backing),
                      '</EthernetBackingDevice>',
                      '</BackingDeviceChoice>']
        # JumboFramesEnabled — must come after BackingDeviceChoice, before TrunkAdapters
        if jumbo_frames is not None:
            jf_str = 'true' if jumbo_frames else 'false'
            parts.append('<JumboFramesEnabled kb="UOD" kxe="false">{0}</JumboFramesEnabled>'.format(jf_str))
        # QualityOfServiceMode — must come after JumboFramesEnabled, before TrunkAdapters
        if qos_mode is not None:
            parts.append('<QualityOfServiceMode kb="CUD" kxe="false">{0}</QualityOfServiceMode>'.format(qos_mode))
        # Empty TrunkAdapters — HMC auto-assigns the slot
        parts += ['<TrunkAdapters kb="CUD" kxe="false" schemaVersion="V1_0">',
                  '<Metadata><Atom/></Metadata>',
                  '</TrunkAdapters>']
        parts.append('<IsPrimary kxe="false" kb="CUD">{0}</IsPrimary>'.format(primary_str))
        # LargeSend — must come after IsPrimary (HMC XSD sequence for POST update)
        if large_send is not None:
            ls_str = 'true' if large_send else 'false'
            parts.append('<LargeSend kb="CUD" kxe="false">{0}</LargeSend>'.format(ls_str))
        parts.append('</SharedEthernetAdapter>')
        return parts

    def createNetworkBridge(self, system_uuid, port_vlan_id, virtual_network_id,
                            vios_id, vios2_id, failover_enabled, load_balancing_enabled,
                            vios1_cfg=None, vios2_cfg=None, addition_pvid=None,
                            jumbo_frames=None, qos_mode=None):
        """Create a NetworkBridge.

        vios2_id / vios2_cfg may be None for a single-VIOS bridge.
        vios1_cfg / vios2_cfg are dicts with optional key: backing_device.
        addition_pvid: when load_balancing_enabled is True the caller may supply
          an integer PVID for the secondary LoadGroup.  When None the secondary
          LoadGroup is omitted from the payload.
        jumbo_frames / qos_mode: SEA-level settings embedded directly in the
          CREATE payload at the correct XSD sequence positions.
          (large_send cannot be set at create time — applied via follow-up POST.)
        """
        url = "https://{0}/rest/api/uom/ManagedSystem/{1}/NetworkBridge".format(self.hmc_ip, system_uuid)
        header = {'X-API-Session': self.session,
                  'Content-Type': 'application/vnd.ibm.powervm.uom+xml; type=NetworkBridge',
                  'Accept': 'application/atom+xml'}
        failover_str = 'true' if failover_enabled else 'false'
        lb_str = 'true' if load_balancing_enabled else 'false'
        vn_href = "https://{0}/rest/api/uom/ManagedSystem/{1}/VirtualNetwork/{2}".format(
            self.hmc_ip, system_uuid, virtual_network_id)
        vios_href = "https://{0}/rest/api/uom/ManagedSystem/{1}/VirtualIOServer/{2}".format(
            self.hmc_ip, system_uuid, vios_id)
        vios1_cfg = vios1_cfg or {}
        payload_parts = ['<NetworkBridge schemaVersion="V1_0">',
                         '<FailoverEnabled kxe="false" kb="CUD">{0}</FailoverEnabled>'.format(failover_str),
                         '<LoadBalancingEnabled kb="CUD" kxe="false">{0}</LoadBalancingEnabled>'.format(lb_str),
                         '<LoadGroups kb="CUD" kxe="false" schemaVersion="V1_0">',
                         '<Metadata><Atom/></Metadata>',
                         '<LoadGroup schemaVersion="V1_0">',
                         '<Metadata><Atom/></Metadata>',
                         '<PortVLANID kxe="false" kb="CUR">{0}</PortVLANID>'.format(port_vlan_id),
                         '<TrunkAdapters kb="CUD" kxe="false" schemaVersion="V1_0">',
                         '<Metadata><Atom/></Metadata>',
                         '</TrunkAdapters>',
                         '<VirtualNetworks kb="CUD" kxe="false">',
                         '<link href="{0}" rel="related"/>'.format(vn_href),
                         '</VirtualNetworks>',
                         '</LoadGroup>']
        # Secondary LoadGroup — only emitted when load-balancing is on and an
        # addition PVID has been supplied by the caller.
        if load_balancing_enabled and addition_pvid is not None:
            payload_parts += ['<LoadGroup schemaVersion="V1_0">',
                              '<Metadata><Atom/></Metadata>',
                              '<PortVLANID kxe="false" kb="CUR">{0}</PortVLANID>'.format(addition_pvid),
                              '<TrunkAdapters kb="CUD" kxe="false" schemaVersion="V1_0">',
                              '<Metadata><Atom/></Metadata>',
                              '</TrunkAdapters>',
                              '</LoadGroup>']
        payload_parts += ['</LoadGroups>',
                          '<PortVLANID kb="COR" kxe="false">{0}</PortVLANID>'.format(port_vlan_id),
                          '<SharedEthernetAdapters kxe="false" kb="CUD" schemaVersion="V1_0">',
                          '<Metadata><Atom/></Metadata>']
        payload_parts += self._sea_xml(vios_href, is_primary=True, cfg=vios1_cfg,
                                       jumbo_frames=jumbo_frames, qos_mode=qos_mode)
        if vios2_id:
            vios2_href = "https://{0}/rest/api/uom/ManagedSystem/{1}/VirtualIOServer/{2}".format(
                self.hmc_ip, system_uuid, vios2_id)
            payload_parts += self._sea_xml(vios2_href, is_primary=False, cfg=vios2_cfg or {},
                                           jumbo_frames=jumbo_frames, qos_mode=qos_mode)
        payload_parts += ['</SharedEthernetAdapters>',
                          '</NetworkBridge>']
        payload = ''.join(payload_parts)
        payload = payload.replace("NetworkBridge", NBRIDGE_NS, 1)
        try:
            resp = open_url(url,
                            headers=header,
                            data=payload,
                            method='PUT',
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=300)
            response = resp.read()
            if not response:
                return None
            bridge_dom = xml_strip_namespace(response)
            return bridge_dom
        except Exception:
            raise

    def getNetworkBridge(self, system_uuid, bridge_uuid):
        """Fetch a single NetworkBridge by UUID and return its namespace-stripped DOM."""
        url = "https://{0}/rest/api/uom/ManagedSystem/{1}/NetworkBridge/{2}".format(
            self.hmc_ip, system_uuid, bridge_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': 'application/vnd.ibm.powervm.uom+xml; type=NetworkBridge'}
        try:
            resp = open_url(url,
                            headers=header,
                            method='GET',
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=300)
            response = resp.read()
            if not response:
                return None
            return xml_strip_namespace(response)
        except Exception:
            raise

    def updateNetworkBridgeSEAs(self, system_uuid, bridge_uuid, bridge_dom,
                                large_send, vios1_ha_mode=None, vios2_ha_mode=None):
        """POST a full NetworkBridge DOM back after patching per-SEA fields.

        Called only from ensure_present (create). LargeSend and HighAvailabilityMode
        cannot be set in the CREATE PUT payload:
          - LargeSend requires IIDPService/ConfigurationState (HMC-generated, absent
            at create time).
          - HighAvailabilityMode is accepted by the HMC only on an already-created
            bridge via a follow-up POST.
        jumbo_frames and qos_mode are handled directly in the CREATE PUT.

        vios1_ha_mode / vios2_ha_mode map to the primary (IsPrimary=true) and
        secondary (IsPrimary=false) SEAs respectively.  The element is upserted —
        created if absent, updated if already present.
        """
        url = "https://{0}/rest/api/uom/ManagedSystem/{1}/NetworkBridge/{2}".format(
            self.hmc_ip, system_uuid, bridge_uuid)
        header = {'X-API-Session': self.session,
                  'Content-Type': 'application/vnd.ibm.powervm.uom+xml; type=NetworkBridge',
                  'Accept': 'application/atom+xml'}
        NS = "http://www.ibm.com/xmlns/systems/power/firmware/uom/mc/2012_10/"
        for sea in bridge_dom.xpath("//SharedEthernetAdapter"):
            # --- LargeSend ---
            if large_send is not None:
                large_send_str = 'true' if large_send else 'false'
                elem = sea.find("{%s}LargeSend" % NS)
                if elem is None:
                    elem = sea.xpath('LargeSend')
                    if elem:
                        elem[0].text = large_send_str
                else:
                    elem.text = large_send_str

            # --- HighAvailabilityMode (upsert) ---
            is_primary_elem = sea.xpath('IsPrimary')
            is_primary = (is_primary_elem[0].text.lower() == 'true') if is_primary_elem else True
            ha_mode = vios1_ha_mode if is_primary else vios2_ha_mode
            if ha_mode is not None:
                ha_elems = sea.xpath('HighAvailabilityMode')
                if ha_elems:
                    ha_elems[0].text = ha_mode
                else:
                    ha_el = etree.SubElement(sea, 'HighAvailabilityMode')
                    ha_el.set('kb', 'CUD')
                    ha_el.set('kxe', 'false')
                    ha_el.text = ha_mode
        nb_elem = bridge_dom.xpath("//NetworkBridge")
        if not nb_elem:
            return None
        nb_xmlstr = etree.tostring(nb_elem[0]).decode("utf-8")
        nb_xmlstr = nb_xmlstr.replace("NetworkBridge", NBRIDGE_NS, 1)
        try:
            resp = open_url(url,
                            headers=header,
                            data=nb_xmlstr,
                            method='POST',
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=300)
            response = resp.read()
            if not response:
                return None
            return xml_strip_namespace(response)
        except Exception:
            raise

    @staticmethod
    def _set_text(element, xpath, value):
        """Set the text of the first matching child element; no-op if not found."""
        nodes = element.xpath(xpath)
        if nodes:
            nodes[0].text = value

    def updateNetworkBridge(self, system_uuid, bridge_uuid, bridge_dom,
                            load_balancing=None, addition_pvid=None,
                            failover_enabled=None,
                            jumbo_frames=None, large_send=None, qos_mode=None,
                            primary_vios_cfg=None, secondary_vios_cfg=None,
                            secondary_vios_uuid=None,
                            tagged_vn_ids_by_pvid=None):
        """Patch a live NetworkBridge DOM and POST it back to apply a full update.

        All parameters are optional.  Only non-None values are applied to the
        live DOM; anything left as None keeps whatever the HMC already has.

        primary_vios_cfg / secondary_vios_cfg are dicts with optional keys:
          backing_device, high_availability_mode.
        secondary_vios_uuid: when provided, a new secondary SharedEthernetAdapter
          block is appended to the DOM for the new VIOS (failover/load-balancing).
        addition_pvid is the Port VLAN ID for the secondary LoadGroup (only
          relevant when load_balancing is being enabled).
        tagged_vn_ids_by_pvid is a dict mapping LoadGroup PVID (int) to a list
          of (vn_name, vn_uuid) tuples to add to that LoadGroup's VirtualNetworks
          block.  Networks whose href is already present are silently skipped.
        """
        url = "https://{0}/rest/api/uom/ManagedSystem/{1}/NetworkBridge/{2}".format(
            self.hmc_ip, system_uuid, bridge_uuid)
        header = {'X-API-Session': self.session,
                  'Content-Type': 'application/vnd.ibm.powervm.uom+xml; type=NetworkBridge',
                  'Accept': 'application/atom+xml'}
        nb_elem_list = bridge_dom.xpath("//NetworkBridge")
        if not nb_elem_list:
            raise ValueError("NetworkBridge element not found in DOM")
        nb = nb_elem_list[0]

        # --- Bridge-level boolean flags ---
        if load_balancing is not None:
            self._set_text(nb, 'LoadBalancingEnabled', 'true' if load_balancing else 'false')
        if failover_enabled is not None:
            self._set_text(nb, 'FailoverEnabled', 'true' if failover_enabled else 'false')

        # --- Secondary LoadGroup PVID ---
        # When load-sharing is being enabled the caller supplies an addition_pvid.
        # The HMC requires a new LoadGroup entry with that PVID to be present in the
        # POST body.  If a LoadGroup with that PVID already exists we leave it alone;
        # if it does not exist we append a minimal one.
        if load_balancing and addition_pvid is not None:
            existing_pvids = [
                e.text for e in nb.xpath('.//LoadGroup/PortVLANID')
            ]
            if str(addition_pvid) not in existing_pvids:
                lg_container = nb.xpath('LoadGroups')
                if lg_container:
                    new_lg_xml = (
                        '<LoadGroup schemaVersion="V1_0">'
                        '<Metadata><Atom/></Metadata>'
                        '<PortVLANID kxe="false" kb="CUR">{0}</PortVLANID>'
                        '<TrunkAdapters kb="CUD" kxe="false" schemaVersion="V1_0">'
                        '<Metadata><Atom/></Metadata>'
                        '</TrunkAdapters>'
                        '</LoadGroup>'
                    ).format(addition_pvid)
                    new_lg_elem = etree.fromstring(new_lg_xml)
                    lg_container[0].append(new_lg_elem)

        # --- Tagged Virtual Networks → per-LoadGroup injection ---
        # Same pattern as the original single-LoadGroup implementation that was
        # already working: use nb.xpath('LoadGroups/LoadGroup') then relative
        # child xpaths — no deep searches needed.  The only change is we match
        # each LoadGroup by its PVID instead of always using load_groups[0].
        newly_added_by_pvid = {}
        if tagged_vn_ids_by_pvid:
            load_groups = nb.xpath('LoadGroups/LoadGroup')
            logger.debug("[updateNetworkBridge] LoadGroups/LoadGroup count=%d", len(load_groups))

            for lg_pvid, vn_pairs in tagged_vn_ids_by_pvid.items():
                logger.debug("[updateNetworkBridge] Looking for LoadGroup PVID=%s in %d groups",
                             lg_pvid, len(load_groups))
                # Find the LoadGroup whose direct PortVLANID child matches lg_pvid
                target_lg = None
                for lg in load_groups:
                    pvid_el = lg.xpath('PortVLANID')
                    if pvid_el and int(pvid_el[0].text) == lg_pvid:
                        target_lg = lg
                        break
                if target_lg is None:
                    raise ValueError(
                        "LoadGroup with PVID {0} not found in bridge DOM".format(lg_pvid))

                # Accept either element name the HMC may use
                vn_container = (target_lg.xpath('VirtualNetworks')
                                or target_lg.xpath('AssociatedInternalNetwork'))
                if not vn_container:
                    # LoadGroup has no VirtualNetworks block yet — create one
                    logger.debug("[updateNetworkBridge] LoadGroup PVID=%s: creating VirtualNetworks block", lg_pvid)
                    vn_el = etree.SubElement(target_lg, 'VirtualNetworks')
                    vn_el.set('kb', 'CUD')
                    vn_el.set('kxe', 'false')
                    existing_hrefs = set()
                else:
                    vn_read_el = vn_container[0]
                    existing_hrefs = {
                        link.get('href', '') for link in vn_read_el.xpath('link')
                    }
                    existing_links = list(vn_read_el.xpath('link'))

                    # Normalise tag name to <VirtualNetworks> if the HMC returned
                    # <AssociatedInternalNetwork> — POST requires <VirtualNetworks>.
                    if vn_read_el.tag != 'VirtualNetworks':
                        new_vn_el = etree.Element('VirtualNetworks')
                        new_vn_el.set('kb', 'CUD')
                        new_vn_el.set('kxe', 'false')
                        for lnk in existing_links:
                            new_vn_el.append(lnk)
                        vn_read_el.getparent().replace(vn_read_el, new_vn_el)
                        vn_el = new_vn_el
                    else:
                        vn_el = vn_read_el

                added_names = []
                for vn_name, vn_uuid in vn_pairs:
                    new_href = "https://{0}:443/rest/api/uom/ManagedSystem/{1}/VirtualNetwork/{2}".format(
                        self.hmc_ip, system_uuid, vn_uuid)
                    alt_href = "https://{0}/rest/api/uom/ManagedSystem/{1}/VirtualNetwork/{2}".format(
                        self.hmc_ip, system_uuid, vn_uuid)
                    if new_href not in existing_hrefs and alt_href not in existing_hrefs:
                        link_elem = etree.SubElement(vn_el, 'link')
                        link_elem.set('href', new_href)
                        link_elem.set('rel', 'related')
                        existing_hrefs.add(new_href)
                        added_names.append(vn_name)
                    else:
                        logger.debug("[updateNetworkBridge] VN '%s' already linked to LoadGroup PVID=%s — skipping",
                                     vn_name, lg_pvid)
                if added_names:
                    newly_added_by_pvid[str(lg_pvid)] = added_names

        # --- Append new secondary SEA when adding a second VIOS ---
        # Only append if the secondary VIOS is not already present in the DOM.
        # If it is already there the SEA-level loop below handles attribute
        # updates without duplicating the SEA block.
        if secondary_vios_uuid and secondary_vios_cfg:
            vios2_href = "https://{0}/rest/api/uom/ManagedSystem/{1}/VirtualIOServer/{2}".format(
                self.hmc_ip, system_uuid, secondary_vios_uuid)
            already_present = any(
                vios2_href in (sea.xpath('AssignedVirtualIOServer/@href') or [])
                for sea in nb.xpath('SharedEthernetAdapters/SharedEthernetAdapter')
            )
            if not already_present:
                # Inherit the primary SEA's current LargeSend value so the HMC
                # does not default the new SEA to LargeSend=true.
                primary_large_send = None
                for _sea in nb.xpath('SharedEthernetAdapters/SharedEthernetAdapter'):
                    _is_p = _sea.xpath('IsPrimary')
                    if _is_p and _is_p[0].text.lower() == 'true':
                        _ls = _sea.xpath('LargeSend')
                        if _ls:
                            primary_large_send = _ls[0].text.lower() == 'true'
                        break
                sea_parts = self._sea_xml(vios2_href, is_primary=False, cfg=secondary_vios_cfg,
                                          large_send=primary_large_send)
                new_sea_elem = etree.fromstring(''.join(sea_parts))
                sea_container = nb.xpath('SharedEthernetAdapters')
                if sea_container:
                    sea_container[0].append(new_sea_elem)
            else:
                pass

        # --- SEA-level attributes (applied to every SharedEthernetAdapter) ---
        for sea in nb.xpath('SharedEthernetAdapters/SharedEthernetAdapter'):
            if jumbo_frames is not None:
                self._set_text(sea, 'JumboFramesEnabled', 'true' if jumbo_frames else 'false')
            if large_send is not None:
                large_send_str = 'true' if large_send else 'false'
                ls_elems = sea.xpath('LargeSend')
                if ls_elems:
                    ls_elems[0].text = large_send_str
                else:
                    ls_el = etree.SubElement(sea, 'LargeSend')
                    ls_el.set('kb', 'CUD')
                    ls_el.set('kxe', 'false')
                    ls_el.text = large_send_str
            if qos_mode is not None:
                self._set_text(sea, 'QualityOfServiceMode', qos_mode)

            # Determine whether this SEA is primary or secondary by its IsPrimary flag
            is_primary_elem = sea.xpath('IsPrimary')
            is_primary = (is_primary_elem[0].text.lower() == 'true') if is_primary_elem else True
            vios_cfg = primary_vios_cfg if is_primary else secondary_vios_cfg
            if not vios_cfg:
                continue

            # Update backing device if specified
            backing_dev = vios_cfg.get('backing_device')
            if backing_dev:
                dev_elems = sea.xpath('BackingDeviceChoice/EthernetBackingDevice/DeviceName')
                if dev_elems:
                    dev_elems[0].text = backing_dev

            # Per-VIOS mutable fields — high_availability_mode is blocked when
            # load_balancing is being changed (caller must validate before here).
            ha_mode = vios_cfg.get('high_availability_mode')
            if ha_mode is not None and not load_balancing:
                self._set_text(sea, 'HighAvailabilityMode', ha_mode)

        nb_xmlstr = etree.tostring(nb).decode("utf-8")
        nb_xmlstr = nb_xmlstr.replace("NetworkBridge", NBRIDGE_NS, 1)
        try:
            resp = open_url(url,
                            headers=header,
                            data=nb_xmlstr,
                            method='POST',
                            validate_certs=False,
                            force_basic_auth=True,
                            timeout=300)
            response = resp.read()
            if not response:
                return None, newly_added_by_pvid
            return xml_strip_namespace(response), newly_added_by_pvid
        except Exception:
            raise

    def deleteNetworkBridge(self, system_uuid, bridge_uuid):
        url = "https://{0}/rest/api/uom/ManagedSystem/{1}/NetworkBridge/{2}".format(
            self.hmc_ip, system_uuid, bridge_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': 'application/atom+xml'}
        try:
            open_url(url,
                     headers=header,
                     method='DELETE',
                     validate_certs=False,
                     force_basic_auth=True,
                     timeout=300)
            return True
        except Exception:
            raise
