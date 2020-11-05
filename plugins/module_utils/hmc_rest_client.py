from __future__ import absolute_import, division, print_function
__metaclass__ = type
from ansible.module_utils.urls import open_url
import time
import xml.etree.ElementTree as ET
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError
from ansible.module_utils.six.moves import cStringIO
from lxml import etree, objectify
import xml.etree.ElementTree as ET

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


def parse_error_response(xml_str):
    dom = xml_strip_namespace(xml_str)
    logger.debug(dom.xpath("//Message")[0].text)
    return dom.xpath("//Message")[0].text


def logonPayload(user, password):
    root = ET.Element("LogonRequest")
    root.attrib = {"schemaVersion": "V1_0",
                   "xmlns": "http://www.ibm.com/xmlns/systems/power/firmware/web/mc/2012_10/",
                   "xmlns:mc": "http://www.ibm.com/xmlns/systems/power/firmware/web/mc/2012_10/"}
    tree = ET.ElementTree(root)

    ET.SubElement(root, "UserID").text = user
    ET.SubElement(root, "Password").text = password
    return ET.tostring(root)


def logon(hmc_ip, username, password):
    header = {'Content-Type': 'application/vnd.ibm.powervm.web+xml; type=LogonRequest'}

    url = "https://{0}/rest/api/web/Logon".format(hmc_ip)

    resp = open_url(url,
                    headers=header,
                    method='PUT',
                    data=logonPayload(username, password),
                    validate_certs=False,
                    force_basic_auth=True).read()

    doc = xml_strip_namespace(resp)
    xapi_session = doc.xpath('X-API-Session')[0].text
    return xapi_session


def logoff(hmc_ip, xpi_session):
    header = {'Content-Type': 'application/vnd.ibm.powervm.web+xml; type=LogonRequest',
              'Authorization': 'Basic Og==',
              'X-API-Session': xpi_session}
    url = "https://{0}/rest/api/web/Logon".format(hmc_ip)

    open_url(url,
             headers=header,
             method='DELETE',
             validate_certs=False,
             force_basic_auth=True)


def fetchJobStatus(hmc_ip, jobId, session, template=False, ignoreSearch=False):

    if template:
        url = "https://{0}/rest/api/templates/jobs/{1}".format(hmc_ip, jobId)
    else:
        url = "https://{0}/rest/api/uom/jobs/{1}".format(hmc_ip, jobId)

    header = {'X-API-Session': session}
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

        logger.debug("fetchJobStatus: %s", resp.decode("utf-8"))

        jobStatus = doc.xpath('//Status')[0].text

        if jobStatus == 'COMPLETED_OK' or jobStatus == 'COMPLETED_WITH_ERROR':
            if ignoreSearch:
                result = doc
            else:
                result = doc.xpath("//ParameterValue")[3].text
            break

        if jobStatus != 'RUNNING':
            logger.debug("jobStatus: %s", jobStatus)
            err_msg = doc.xpath("//ResponseException//Message")[0].text
            raise HmcError(err_msg)

    return result


def getManagedSystems(hmc_ip, session):

    url = "https://{0}/rest/api/uom/ManagedSystem".format(hmc_ip)
    header = {'X-API-Session': session,
              'Accept': 'application/vnd.ibm.powervm.uom+xml; type=ManagedSystem'}
    response = open_url(url,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True).read()

    logger.debug("GET MANAGEDSYSTEMS")
    logger.debug(response.decode("utf-8"))
    managedsystem_root = xml_strip_namespace(response)
    return managedsystem_root.xpath("//ManagedSystem")


def getManagedSystem(hmc_ip, session, system_name):
    url = "https://{0}/rest/api/uom/ManagedSystem/search/(SystemName=={1})".format(hmc_ip, system_name)
    header = {'X-API-Session': session,
              'Accept': 'application/vnd.ibm.powervm.uom+xml; type=ManagedSystem'}

    response = open_url(url,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True).read()

    managedsystem_root = xml_strip_namespace(response)
    uuid = managedsystem_root.xpath("//AtomID")[0].text
    logger.debug(etree.tostring(managedsystem_root.xpath("//ManagedSystem")[0]).decode("utf-8"))
    return uuid, managedsystem_root.xpath("//ManagedSystem")[0]


def updatePartitionTemplate(hmc_ip, session, uuid, template_xml, config_dict):

    template_xml.xpath("//partitionId")[0].text = config_dict['lpar_id']
    template_xml.xpath("//partitionName")[0].text = config_dict['vm_name']

    template_xml.xpath("//minProcessors")[0].text = '1'
    template_xml.xpath("//desiredProcessors")[0].text = config_dict['proc']
    template_xml.xpath("//maxProcessors")[0].text = config_dict['proc']

    template_xml.xpath("//currMinMemory")[0].text = '1024'
    template_xml.xpath("//currMemory")[0].text = config_dict['mem']
    template_xml.xpath("//currMaxMemory")[0].text = config_dict['mem']

    templateUrl = "https://{0}/rest/api/templates/PartitionTemplate/{1}".format(hmc_ip, uuid)
    header = {'X-API-Session': session,
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


def getPartitionTemplateUUID(hmc_ip, session, name):
    header = {'X-API-Session': session}
    url = "https://{0}/rest/api/templates/PartitionTemplate?draft=false&detail=table".format(hmc_ip)

    response = open_url(url,
                        headers=header,
                        method='GET',
                        validate_certs=False,
                        force_basic_auth=True).read()

    root = xml_strip_namespace(response)
    element = root.xpath("//partitionTemplateName[text()='{0}']/preceding-sibling::Metadata//AtomID".format(name))
    uuid = element[0].text
    return uuid


def getPartitionTemplate(hmc_ip, session, uuid=None, name=None):
    logger.debug("Get partition template...")
    header = {'X-API-Session': session}

    if name:
        uuid = getPartitionTemplateUUID(hmc_ip, session, name)

    templateUrl = "https://{0}/rest/api/templates/PartitionTemplate/{1}".format(hmc_ip, uuid)
    logger.debug(templateUrl)
    resp = open_url(templateUrl,
                    headers=header,
                    method='GET',
                    validate_certs=False,
                    force_basic_auth=True)
    response = resp.read()

    partiton_template_root = xml_strip_namespace(response)
    return partiton_template_root.xpath("//PartitionTemplate")[0]


def copyPartitionTemplate(hmc_ip, session, from_name, to_name):
    header = {'X-API-Session': session,
              'Content-Type': 'application/vnd.ibm.powervm.templates+xml;type=PartitionTemplate'}

    partiton_template_doc = getPartitionTemplate(hmc_ip, session, name=from_name)
    partiton_template_doc.xpath("//partitionTemplateName")[0].text = to_name
    templateNamespace = 'PartitionTemplate xmlns="http://www.ibm.com/xmlns/systems/power/firmware/templates/mc/2012_10/" \
                         xmlns:ns2="http://www.w3.org/XML/1998/namespace/k2"'
    partiton_template_xmlstr = etree.tostring(partiton_template_doc)
    partiton_template_xmlstr = partiton_template_xmlstr.decode("utf-8").replace("PartitionTemplate", templateNamespace, 1)
    logger.debug(partiton_template_xmlstr)

    templateUrl = "https://{0}/rest/api/templates/PartitionTemplate".format(hmc_ip)

    resp = open_url(templateUrl,
                    headers=header,
                    data=partiton_template_xmlstr,
                    method='PUT',
                    validate_certs=False,
                    force_basic_auth=True)


def deletePartitionTemplate(hmc_ip, session, template_name):
    logger.debug("Delete partition template...")
    header = {'X-API-Session': session,
              'Accept': 'application/vnd.ibm.powervm.web+xml'}

    partiton_template_doc = getPartitionTemplate(hmc_ip, session, name=template_name)
    template_uuid = partiton_template_doc.xpath("//AtomID")[0].text

    templateUrl = "https://{0}/rest/api/templates/PartitionTemplate/{1}".format(hmc_ip, template_uuid)
    logger.debug(templateUrl)
    resp = open_url(templateUrl,
                    headers=header,
                    method='DELETE',
                    validate_certs=False,
                    force_basic_auth=True)


def _jobHeader(session):

    header = {'Content-Type': 'application/vnd.ibm.powervm.web+xml; type=JobRequest',
              'Authorization': 'Basic Og=='}
    header['X-API-Session'] = session

    return header


def checkPartitionTemplate(hmc_ip, session, template_name, cec_uuid):
    header = _jobHeader(session)

    partiton_template_doc = getPartitionTemplate(hmc_ip, session, name=template_name)
    template_uuid = partiton_template_doc.xpath("//AtomID")[0].text
    check_url = "https://{0}/rest/api/templates/PartitionTemplate/{1}/do/check".format(hmc_ip, template_uuid)

    reqdOperation = {'OperationName': 'Check',
                     'GroupName': 'PartitionTemplate',
                     'ProgressType': 'DISCRETE'}

    jobParams = {'K_X_API_SESSION_MEMENTO': session,
                 'TargetUuid': cec_uuid}

    payload = job_RequestPayload(reqdOperation, jobParams)
    resp = open_url(check_url,
                    headers=header,
                    data=payload,
                    method='PUT',
                    validate_certs=False,
                    force_basic_auth=True).read()

    checkjob_resp = xml_strip_namespace(resp)

    jobID = checkjob_resp.xpath('//JobID')[0].text

    return fetchJobStatus(hmc_ip, jobID, header['X-API-Session'], template=True, ignoreSearch=True)


def deployPartitionTemplate(hmc_ip, session, draft_uuid, cec_uuid):

    url = "https://{0}/rest/api/templates/PartitionTemplate/{1}/do/deploy".format(hmc_ip, draft_uuid)

    header = _jobHeader(session)

    reqdOperation = {'OperationName': 'Deploy',
                     'GroupName': 'PartitionTemplate',
                     'ProgressType': 'DISCRETE'}

    jobParams = {'K_X_API_SESSION_MEMENTO': session,
                 'TargetUuid': cec_uuid}

    payload = job_RequestPayload(reqdOperation, jobParams)
    resp = open_url(url,
                    headers=header,
                    data=payload,
                    method='PUT',
                    validate_certs=False,
                    force_basic_auth=True).read()

    deploy_resp = xml_strip_namespace(resp)
    jobID = deploy_resp.xpath('//JobID')[0].text
    return fetchJobStatus(hmc_ip, jobID, header['X-API-Session'], template=True, ignoreSearch=True)


def transformPartitionTemplate(hmc_ip, session, draft_uuid, cec_uuid):

    url = "https://{0}/rest/api/templates/PartitionTemplate/{1}/do/transform".format(hmc_ip, draft_uuid)
    header = _jobHeader(session)

    reqdOperation = {'OperationName': 'Transform',
                     'GroupName': 'PartitionTemplate',
                     'ProgressType': 'DISCRETE'}

    jobParams = {'K_X_API_SESSION_MEMENTO': session,
                 'TargetUuid': cec_uuid}

    payload = job_RequestPayload(reqdOperation, jobParams)

    resp = open_url(url,
                    headers=header,
                    data=payload,
                    method='PUT',
                    validate_certs=False,
                    force_basic_auth=True).read()

    transform_resp = xml_strip_namespace(resp)
    jobID = transform_resp.xpath('//JobID')[0].text
    return fetchJobStatus(hmc_ip, jobID, header['X-API-Session'], template=True, ignoreSearch=True)


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


def job_RequestPayload(reqdOperation, jobParams):
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
