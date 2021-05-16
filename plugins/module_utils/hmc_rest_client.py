from __future__ import absolute_import, division, print_function
__metaclass__ = type
import time
import json
from ansible.module_utils.urls import open_url
import ansible.module_utils.six.moves.urllib.error as urllib_error
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import Error
import xml.etree.ElementTree as ET
NEED_LXML = False
try:
    from lxml import etree, objectify
except ImportError:
    NEED_LXML = True

import logging
LOG_FILENAME = "/tmp/ansible_power_hmc.log"
logger = logging.getLogger(__name__)


LPAR_TEMPLATE_NS = 'PartitionTemplate xmlns="http://www.ibm.com/xmlns/systems/power/\
firmware/templates/mc/2012_10/" xmlns:ns2="http://www.w3.org/XML/1998/namespace/k2"'


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
                if "Failed to unmarshal input payload" in error_msg:
                    error_msg = "Current HMC version might not support some of input settings"
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
    physical_io_list = server_dom.xpath("//AssociatedSystemIOConfiguration/IOAdapters/IOAdapterChoice")
    drcname_occurence = server_dom.xpath("//AssociatedSystemIOConfiguration/IOAdapters//DeviceName[contains(text(),'"+drcname+"')]")
    if len(drcname_occurence) > 1:
        ignore_occurence = False
        for each in drcname_occurence:
            #End Charater matching, handles the case where P1-C1 and P1-C12 should not be considered same
            if each.text[-1] == drcname[-1] and len(each.text.split('-')[-1]) == len(drcname.split('-')[-1]):
                logger.debug("End Charater matching")
                ignore_occurence = True
                break

        if not ignore_occurence:
            raise Error("Given location code matching with adapters from multiple drawer")

    for each in physical_io_list:
        if drcname in each.xpath("IOAdapter/DeviceName")[0].text:
            return etree.ElementTree(each)

    return None


def add_physical_io(rest_conn, server_dom, lpar_template_dom, drcnames):
    profileioslot_payload = ''
    for drcname in drcnames:
        # find the physical io adpater details from managed system dom
        io_adapter_dom = lookup_physical_io(rest_conn, server_dom, drcname)
        if not io_adapter_dom:
            raise Error("Not able to find the matching IO Adapter on the Server")

        drc_index = io_adapter_dom.xpath("//AdapterID")[0].text
        location_code = io_adapter_dom.xpath("//DynamicReconfigurationConnectorName")[0].text
        logger.debug("Location_code %s"%location_code)

        profileioslot_payload += '''<ProfileIOSlot schemaVersion="V1_0">
                        <Metadata>
                            <Atom/>
                        </Metadata>
                        <isAssigned kb="CUD" kxe="false">true</isAssigned>
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

    def fetchJobStatus(self, jobId, template=False, timeout_counter=0):

        if template:
            url = "https://{0}/rest/api/templates/jobs/{1}".format(self.hmc_ip, jobId)
        else:
            url = "https://{0}/rest/api/uom/jobs/{1}".format(self.hmc_ip, jobId)

        header = {'X-API-Session': self.session, 'Accept': "application/atom+xml"}
        result = None

        jobStatus = ''
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
                    raise HmcError(resp_msg[0].text)
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

            if timeout_counter == 60:
                job_name = doc.xpath("//OperationName")[0].text.strip()
                logger.debug("%s job stuck in %s state. Timed out!!", job_name, jobStatus)
                raise HmcError("Job: {0} timed out!!".format(job_name))

        return result

    def getManagedSystem(self, system_name):
        url = "https://{0}/rest/api/uom/ManagedSystem/search/(SystemName=={1})".format(self.hmc_ip, system_name)
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

    def getLogicalPartition(self, system_uuid, partition_name):
        lpar_uuid = None
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

    def getVirtualIOServers(self, system_uuid):
        url = "https://{0}/rest/api/uom/ManagedSystem/{1}/VirtualIOServer?group=Advanced".format(self.hmc_ip, system_uuid)
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

    def updateProcMemSettingsToDom(self, template_xml, config_dict):
        shared_config_tag = None
        template_xml.xpath("//partitionId")[0].text = config_dict['lpar_id']
        template_xml.xpath("//partitionName")[0].text = config_dict['vm_name']

        # shared processor configuration
        if config_dict['proc_unit']:
            shared_payload = '''<sharedProcessorConfiguration kxe="false" kb="CUD" schemaVersion="V1_0">
                <Metadata>
                    <Atom/>
                </Metadata>
                <sharedProcessorPoolId kxe="false" kb="CUD">0</sharedProcessorPoolId>
                <uncappedWeight kxe="false" kb="CUD">128</uncappedWeight>
                <minProcessingUnits kb="CUD" kxe="false">0.1</minProcessingUnits>
                <desiredProcessingUnits kxe="false" kb="CUD">{0}</desiredProcessingUnits>
                <maxProcessingUnits kb="CUD" kxe="false">{0}</maxProcessingUnits>
                <minVirtualProcessors kb="CUD" kxe="false">1</minVirtualProcessors>
                <desiredVirtualProcessors kxe="false" kb="CUD">{1}</desiredVirtualProcessors>
                <maxVirtualProcessors kxe="false" kb="CUD">{1}</maxVirtualProcessors>
                </sharedProcessorConfiguration>'''.format(config_dict['proc_unit'], config_dict['proc'])

            shared_config_tag = template_xml.xpath("//sharedProcessorConfiguration")[0]
            if shared_config_tag:
                shared_config_tag.getparent().remove(shared_config_tag)
            sharingMode_tag = template_xml.xpath("//sharingMode")[0]
            sharingMode_tag.addnext(etree.XML(shared_payload))

            dedi_tag = template_xml.xpath("//dedicatedProcessorConfiguration")[0]
            if dedi_tag:
                dedi_tag.getparent().remove(dedi_tag)

            template_xml.xpath("//currHasDedicatedProcessors")[0].text = 'false'
            template_xml.xpath("//currSharingMode")[0].text = 'uncapped'
        else:
            template_xml.xpath("//minProcessors")[0].text = '1'
            template_xml.xpath("//desiredProcessors")[0].text = config_dict['proc']
            template_xml.xpath("//maxProcessors")[0].text = config_dict['proc']

        template_xml.xpath("//currMinMemory")[0].text = config_dict['mem']
        template_xml.xpath("//currMemory")[0].text = config_dict['mem']
        template_xml.xpath("//currMaxMemory")[0].text = config_dict['mem']

    def updatePartitionTemplate(self, uuid, template_xml):
        templateUrl = "https://{0}/rest/api/templates/PartitionTemplate/{1}".format(self.hmc_ip, uuid)
        header = {'X-API-Session': self.session,
                  'Content-Type': 'application/vnd.ibm.powervm.templates+xml;type=PartitionTemplate'}

        partiton_template_xmlstr = etree.tostring(template_xml)
        partiton_template_xmlstr = partiton_template_xmlstr.decode("utf-8").replace("PartitionTemplate", LPAR_TEMPLATE_NS, 1)

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

    def poweroffPartition(self, vm_uuid, operation, immediate='false'):
        url = "https://{0}/rest/api/uom/LogicalPartition/{1}/do/PowerOff".format(self.hmc_ip, vm_uuid)
        header = _jobHeader(self.session)

        reqdOperation = {'OperationName': 'PowerOff',
                         'GroupName': 'LogicalPartition',
                         'ProgressType': 'DISCRETE'}

        jobParams = {'immediate': immediate,
                     'restart': 'false',
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
        return self.fetchJobStatus(jobID, timeout_counter=40)

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
        return self.fetchJobStatus(jobID, timeout_counter=40)

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

    def add_vscsi_payload(self, lpar_template_dom, pv_tup):

        payload = ''
        pv_tup_list_slice = pv_tup[:2]
        for pv_name, vios_name, pv_obj in pv_tup_list_slice:
            payload += '''
            <VirtualSCSIClientAdapter schemaVersion="V1_0">
                    <Metadata>
                            <Atom/>
                    </Metadata>
                    <name kb="CUD" kxe="false"></name>
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
            </VirtualSCSIClientAdapter>'''.format(pv_name, vios_name)

        vscsi_client_payload = '''
        <virtualSCSIClientAdapters kxe="false" kb="CUD" schemaVersion="V1_0">
        <Metadata>
                <Atom/>
        </Metadata>
        {0}
        </virtualSCSIClientAdapters>'''.format(payload)
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

        disk_dict = {}
        for each in list_pv_elem:
            disk_dict.update({each.xpath("VolumeUniqueID")[0].text: each})
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

    def updateVirtualNWSettingsToDom(self, template_xml, config_dict):
        vnw_payload = '''
        <clientNetworkAdapters kb="CUD" kxe="false" schemaVersion="V1_0">
            <Metadata>
                <Atom/>
            </Metadata>
            <ClientNetworkAdapter schemaVersion="V1_0">
                <Metadata>
                    <Atom/>
                </Metadata>
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
            </ClientNetworkAdapter>
        </clientNetworkAdapters>'''.format(config_dict['nw_name'], config_dict['nw_uuid'])

        client_nw_adapter_tag = template_xml.xpath("//ioConfiguration")[0]
        client_nw_adapter_tag.addnext(etree.XML(vnw_payload))
