#
#    @author  Anil Vijayan
#
##

from __future__ import absolute_import, division, print_function
__metaclass__ = type
import time
import re
import subprocess
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_command_stack import HmcCommandStack
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_cli_client import HmcCliConnection
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError

import logging
logger = logging.getLogger(__name__)


class Hmc():

    def __init__(self, hmcconn):
        self.hmcconn = hmcconn
        self.cmdClass = HmcCommandStack()
        self.CMD = self.cmdClass.HMC_CMD
        self.OPT = self.cmdClass.HMC_CMD_OPT

    def listHMCVersion(self):
        versionDict = {}
        lshmcCmd = self.CMD['LSHMC'] + self.OPT['LSHMC']['-V']
        result = self.hmcconn.execute(lshmcCmd)

        fixPacks = []
        for each in result.split('\n'):
            if 'Version' in each:
                versionDict['VERSION'] = each.split(':')[1].strip()
            elif 'Release:' in each:
                versionDict['RELEASE'] = each.split(':')[1].strip()
            elif 'Service Pack:' in each:
                versionDict['SERVICEPACK'] = each.split(':')[1].strip()
            elif 'HMC Build level' in each:
                versionDict['HMCBUILDLEVEL'] = each.split('l ')[1].strip()
            elif '-' in each:
                fixPacks.append(each)
                versionDict['FIXPACKS'] = fixPacks
            elif 'base_version' in each:
                versionDict['BASEVERSION'] = each.split('=')[1].strip()

        return versionDict

    def pingTest(self, i_host):
        pattern = re.compile(r"(\d) received")
        report = ("No response", "Partial Response", "Alive")
        cmd = "ping -c 2 " + i_host.strip()

        result = 'No response'
        with subprocess.Popen(cmd, shell=True, executable="/bin/bash",
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE) as proc:

            stdout_value, stderr_value = proc.communicate()
            if isinstance(stdout_value, bytes):
                stdout_value = stdout_value.decode('ascii')

            igot = re.findall(pattern, stdout_value)
            if igot:
                result = report[int(igot[0])]

        return result

    def checkHmcUpandRunning(self, rebootStarted=False, timeoutInMin=12):
        POLL_INTERVAL_IN_SEC = 30
        WAIT_UNTIL_IN_SEC = timeoutInMin * 60

        # Polling logic to make sure hmc pinging after reboot
        waited = 0
        pingSuccess = False
        while waited < WAIT_UNTIL_IN_SEC:
            ping_state = self.pingTest(self.hmcconn.ip)

            if "Alive" in ping_state and rebootStarted:
                logger.debug("Alive")
                pingSuccess = True
                break
            if "No response" in ping_state:
                logger.debug("No response")
                rebootStarted = True
                waited += POLL_INTERVAL_IN_SEC
            else:
                logger.debug("Wait")
                waited += POLL_INTERVAL_IN_SEC

            # waiting for 30 seconds
            time.sleep(POLL_INTERVAL_IN_SEC)

        return pingSuccess

    @staticmethod
    def checkIfHMCFullyBootedUp(module, hmc_ip, user, password):
        POLL_INTERVAL_IN_SEC = 30
        WAIT_UNTIL_IN_SEC = 20 * 60
        waited = 0
        bootedUp = False
        hmc_obj = None
        versionDict = {}

        time.sleep(3 * 60)
        while waited < WAIT_UNTIL_IN_SEC:
            try:
                conn = HmcCliConnection(module, hmc_ip, user, password)
                hmc_obj = Hmc(conn)
                break
            except HmcError:
                waited += POLL_INTERVAL_IN_SEC
                # waiting for 30 seconds
                time.sleep(POLL_INTERVAL_IN_SEC)

        waited = 0
        if hmc_obj:

            while waited < WAIT_UNTIL_IN_SEC:
                try:
                    versionDict = hmc_obj.listHMCVersion()
                    if 'RELEASE' in versionDict.keys():
                        bootedUp = True
                        break
                except HmcError:
                    waited += POLL_INTERVAL_IN_SEC

                    # waiting for 30 seconds
                    time.sleep(POLL_INTERVAL_IN_SEC)

        return bootedUp, versionDict

    def hmcShutdown(self, numOfMin='now', reboot=False):
        hmcShutdownCmd = self.CMD['HMCSHUTDOWN']

        hmcShutdownCmd += self.OPT['HMCSHUTDOWN']['-T'] + numOfMin

        if reboot:
            hmcShutdownCmd += self.OPT['HMCSHUTDOWN']['-R']

        self.hmcconn.execute(hmcShutdownCmd)

        if numOfMin != 'now':
            time.sleep(int(numOfMin) * 60)

    def getHMCUpgradeFiles(self, serverType, configDict=None):
        hmcCmd = self.CMD['GETUPGFILES'] + \
            self.OPT['GETUPGFILES']['-R'][serverType.upper()] + \
            self.cmdClass.configBuilder('GETUPGFILES', configDict)

        result = self.hmcconn.execute(hmcCmd)
        return result

    def saveUpgrade(self, drive, configDict=None):
        hmcCmd = self.CMD['SAVEUPGDATA'] + \
            self.OPT['SAVEUPGDATA']['-R'][drive.upper()]

        if configDict:
            hmcCmd += self.cmdClass.configBuilder('SAVEUPGDATA', configDict)

        self.hmcconn.execute(hmcCmd)

    def updateHMC(self, locationType, configDict=None):
        hmcCmd = self.CMD['UPDHMC'] + \
            self.OPT['UPDHMC']['-T'][locationType.upper()] + \
            self.cmdClass.configBuilder('UPDHMC', configDict)

        result = self.hmcconn.execute(hmcCmd)
        return result

    def configAltDisk(self, enable, mode):
        chhhmcCmd = self.CMD['CHHMC'] + \
            self.OPT['CHHMC']['-C']['ALTDISKBOOT'] +  \
            self.OPT['CHHMC']['--MODE'][mode.upper()]

        if enable:
            chhhmcCmd += self.OPT['CHHMC']['-S']['ENABLE']
        else:
            chhhmcCmd += self.OPT['CHHMC']['-S']['DISABLE']
        self.hmcconn.execute(chhhmcCmd)

    def listPwdPolicy(self, policy_type):
        lsPwdPolicy = self.CMD['LSPWDPOLICY']

        if policy_type == 'status':
            lsPwdPolicy += self.OPT['LSPWDPOLICY']['-T']['S']
            result = self.hmcconn.execute(lsPwdPolicy)
            return self.cmdClass.parseCSV(result)
        elif policy_type == 'policies':
            lsPwdPolicy += self.OPT['LSPWDPOLICY']['-T']['P']
            result = self.hmcconn.execute(lsPwdPolicy)
            return self.cmdClass.parseMultiLineCSV(result)

    def createPwdPolicy(self, policy_config):
        mkPwdPolicy = self.CMD['MKPWDPOLICY']
        policy_config = self.cmdClass.convertKeysToUpper(policy_config)
        mkPwdPolicy += self.cmdClass.i_a_ConfigBuilder('MKPWDPOLICY', '-I', policy_config)
        self.hmcconn.execute(mkPwdPolicy)

    def modifyPwdPolicy(self, name=None, activate=False, policy_config=None):
        chPwdPolicy = self.CMD['CHPWDPOLICY']
        if policy_config:
            policy_config = self.cmdClass.convertKeysToUpper(policy_config)
        if policy_config:
            chPwdPolicy += self.OPT['CHPWDPOLICY']['-O']['M']
            chPwdPolicy += self.cmdClass.i_a_ConfigBuilder('CHPWDPOLICY', '-I', policy_config)
        else:
            if activate:
                chPwdPolicy += self.OPT['CHPWDPOLICY']['-O']['A'] + self.OPT['CHPWDPOLICY']['-N'] + name
            else:
                chPwdPolicy += self.OPT['CHPWDPOLICY']['-O']['D']
        self.hmcconn.execute(chPwdPolicy)

    def removePwdPolicy(self, name):
        rmPwdPolicy = self.CMD['RMPWDPOLICY']
        rmPwdPolicy += self.OPT['RMPWDPOLICY']['-N'] + name
        self.hmcconn.execute(rmPwdPolicy)

    def getNextPartitionID(self, cecName, max_supp_lpars):
        lssyscfgCmd = self.CMD['LSSYSCFG'] + \
            self.OPT['LSSYSCFG']['-R']['LPAR'] + \
            self.OPT['LSSYSCFG']['-M'] + cecName + \
            self.OPT['LSSYSCFG']['-F'] + 'lpar_id'

        result = self.hmcconn.execute(lssyscfgCmd).strip()
        if 'No results were found' in result:
            return 1
        existing_lpar_list = list(map(int, result.split('\n')))
        supp_id_list = list(range(1, int(max_supp_lpars)))
        avail_list = list(set(supp_id_list) - set(existing_lpar_list))
        result_list = sorted(avail_list)
        return result_list[0]

    def deletePartition(self, cecName, lparName, deleteAssociatedViosCfg=True, deleteVdisks=False):
        rmsyscfgCmd = self.CMD['RMSYSCFG'] + \
            self.OPT['RMSYSCFG']['-R']['LPAR'] + \
            self.OPT['RMSYSCFG']['-M'] + cecName + \
            self.OPT['RMSYSCFG']['-N'] + lparName
        if deleteAssociatedViosCfg:
            rmsyscfgCmd += self.OPT['RMSYSCFG']['VIOSCFG']
        if deleteVdisks:
            rmsyscfgCmd += self.OPT['RMSYSCFG']['VDISKS']
        self.hmcconn.execute(rmsyscfgCmd)

    def createPartitionWithAllResources(self, cecName, lparName, osType):
        lpar_config = {}
        profile_name = 'default_profile'
        if osType in ['aix', 'linux', 'aix_linux']:
            lpar_config = {'name': lparName, 'lpar_env': 'aixlinux', 'all_resources': '1', 'profile_name': profile_name}
        elif osType == 'ibmi':
            lpar_config = {'name': lparName, 'lpar_env': 'os400', 'all_resources': '1', 'profile_name': profile_name, 'console_slot': '1'}
        lpar_config = self.cmdClass.convertKeysToUpper(lpar_config)
        mksyscfgCmd = self.CMD['MKSYSCFG'] + \
            self.OPT['MKSYSCFG']['-R']['LPAR'] + \
            self.OPT['MKSYSCFG']['-M'] + cecName
        mksyscfgCmd += self.cmdClass.i_a_ConfigBuilder('MKSYSCFG', '-I', lpar_config)
        logger.debug("mksyscfgCmd: " + mksyscfgCmd)
        self.hmcconn.execute(mksyscfgCmd)

    def applyProfileToPartition(self, cecName, lparName, profile_name):
        chsyscfgCmd = self.CMD['CHSYSCFG'] + \
            self.OPT['CHSYSCFG']['-R']['LPAR'] + \
            self.OPT['CHSYSCFG']['-M'] + cecName + \
            self.OPT['CHSYSCFG']['-N'] + profile_name + \
            self.OPT['CHSYSCFG']['-P'] + lparName + \
            self.OPT['CHSYSCFG']['-O']['APPLY']
        logger.debug("chsyscfgCmd: " + chsyscfgCmd)
        self.hmcconn.execute(chsyscfgCmd)
