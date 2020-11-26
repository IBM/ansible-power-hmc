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
except Exception:
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


def _job_parameter(parameter, parameterVal):

    metaData = ET.Element("Metadata")
    metaData.insert(1, ET.Element("Atom"))

    jobParameter = ET.Element("JobParameter")
    jobParameter.attrib = _kxe_kb_schema(schema="V1_0")
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


def _job_RequestPayload(reqdOperation, jobParams):
    root = ET.Element("JobRequest")
    root.attrib = {"xmlns:JobRequest": "http://www.ibm.com/xmlns/systems/power/firmware/web/mc/2012_10/",
                   "xmlns": "http://www.ibm.com/xmlns/systems/power/firmware/web/mc/2012_10/",
                   "xmlns:ns2": "http://www.w3.org/XML/1998/namespace/k2",
                   "schemaVersion": "V1_0"
                   }

    metaData = ET.Element("Metadata")
    metaData.insert(1, ET.Element("Atom"))
    root.insert(1, metaData)

    requestedOperation = ET.Element("RequestedOperation")
    requestedOperation.attrib = _kxe_kb_schema("false", "CUR", "V1_0")
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
    jobParameters.attrib = _kxe_kb_schema("false", "CUR", "V1_0")
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
                        force_basic_auth=True)
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
                 force_basic_auth=True)

    def fetchJobStatus(self, jobId, template=False, ignoreSearch=False):

        if template:
            url = "https://{0}/rest/api/templates/jobs/{1}".format(self.hmc_ip, jobId)
        else:
            url = "https://{0}/rest/api/uom/jobs/{1}".format(self.hmc_ip, jobId)

        header = {'X-API-Session': self.session}
        result = None

        jobStatus = ''
        while True:
            time.sleep(20)
            resp = open_url(url,
                            headers=header,
                            method='GET',
                            validate_certs=False,
                            force_basic_auth=True).read()
            doc = xml_strip_namespace(resp)

            jobStatus = doc.xpath('//Status')[0].text

            if jobStatus == 'COMPLETED_OK' or jobStatus == 'COMPLETED_WITH_ERROR':
                if ignoreSearch:
                    result = doc
                else:
                    result = doc.xpath("//ParameterValue")[3].text
                break

            if jobStatus != 'RUNNING':
                logger.debug("jobStatus: %s", jobStatus)
                err_msg_l = doc.xpath("//ResponseException//Message")
                err_msg_l = doc.xpath("//ParameterName[text()='ExceptionText']/following-sibling::ParameterValue") if not err_msg_l else err_msg_l
                if not err_msg_l:
                    err_msg = 'Job failed.'
                else:
                    err_msg = err_msg_l[0].text
                raise HmcError(err_msg)

        return result

    def getManagedSystem(self, system_name):
        url = "https://{0}/rest/api/uom/ManagedSystem/search/(SystemName=={1})".format(self.hmc_ip, system_name)
        header = {'X-API-Session': self.session,
                  'Accept': 'application/vnd.ibm.powervm.uom+xml; type=ManagedSystem'}

        response = open_url(url,
                            headers=header,
                            method='GET',
                            validate_certs=False,
                            force_basic_auth=True)

        if response.code == 204:
            return None, None

        managedsystem_root = xml_strip_namespace(response.read())
        uuid = managedsystem_root.xpath("//AtomID")[0].text
        return uuid, managedsystem_root.xpath("//ManagedSystem")[0]

    def getLogicalPartition(self, system_uuid, partition_name):
        url = "https://{0}/rest/api/uom/ManagedSystem/{1}/LogicalPartition".format(self.hmc_ip, system_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': 'application/vnd.ibm.powervm.uom+xml; type=LogicalPartition'}

        resp = open_url(url,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True)
        if resp.code != 200:
            logger.debug("Get of Logical Partition failed. Respsonse code: %d", resp.code)
            return None, None
        response = resp.read()

        lpar_root = xml_strip_namespace(response)
        if lpar_root:
            partitions_dom = lpar_root.xpath("//PartitionName[text()='{0}']/..".format(partition_name))
            if partitions_dom:
                partition_dom = partitions_dom[0]
                xml_str = etree.tostring(partition_dom)
                partition_dom = etree.fromstring(xml_str)
                uuid = partition_dom.xpath("//PartitionUUID")[0].text
                logger.debug("PartitionUUID: %s", uuid)
                return uuid, partition_dom

        return None, None

    def deleteLogicalPartition(self, partition_uuid):
        url = "https://{0}/rest/api/uom/LogicalPartition/{1}".format(self.hmc_ip, partition_uuid)
        header = {'X-API-Session': self.session,
                  'Accept': 'application/vnd.ibm.powervm.uom+xml; type=LogicalPartition'}

        open_url(url,
                 headers=header,
                 method='DELETE',
                 validate_certs=False,
                 force_basic_auth=True)

    def updatePartitionTemplate(self, uuid, template_xml, config_dict):
        template_xml.xpath("//partitionId")[0].text = config_dict['lpar_id']
        template_xml.xpath("//partitionName")[0].text = config_dict['vm_name']

        template_xml.xpath("//minProcessors")[0].text = '1'
        template_xml.xpath("//desiredProcessors")[0].text = config_dict['proc']
        template_xml.xpath("//maxProcessors")[0].text = config_dict['proc']

        template_xml.xpath("//currMinMemory")[0].text = config_dict['mem']
        template_xml.xpath("//currMemory")[0].text = config_dict['mem']
        template_xml.xpath("//currMaxMemory")[0].text = config_dict['mem']

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
                        force_basic_auth=True).read()
        logger.debug(resp.decode("utf-8"))

    def quickGetPartition(self, lpar_uuid):
        header = {'X-API-Session': self.session}
        url = "https://{0}/rest/api/uom/LogicalPartition/{1}/quick".format(self.hmc_ip, lpar_uuid)
        resp = open_url(url,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True)

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
                        force_basic_auth=True)
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
                        force_basic_auth=True)
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
                        force_basic_auth=True)
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
                 force_basic_auth=True)

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
                        force_basic_auth=True).read()

        checkjob_resp = xml_strip_namespace(resp)

        jobID = checkjob_resp.xpath('//JobID')[0].text

        return self.fetchJobStatus(jobID, template=True, ignoreSearch=True)

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
                        force_basic_auth=True).read()

        deploy_resp = xml_strip_namespace(resp)
        jobID = deploy_resp.xpath('//JobID')[0].text
        return self.fetchJobStatus(jobID, template=True, ignoreSearch=True)

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
                        force_basic_auth=True).read()

        transform_resp = xml_strip_namespace(resp)
        jobID = transform_resp.xpath('//JobID')[0].text
        return self.fetchJobStatus(jobID, template=True, ignoreSearch=True)
