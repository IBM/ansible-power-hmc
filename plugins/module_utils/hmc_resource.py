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
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import ParameterError

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
        self.hmcconn.execute(mksyscfgCmd)

    def applyProfileToPartition(self, cecName, lparName, profile_name):
        chsyscfgCmd = self.CMD['CHSYSCFG'] + \
            self.OPT['CHSYSCFG']['-R']['LPAR'] + \
            self.OPT['CHSYSCFG']['-M'] + cecName + \
            self.OPT['CHSYSCFG']['-N'] + profile_name + \
            self.OPT['CHSYSCFG']['-P'] + lparName + \
            self.OPT['CHSYSCFG']['-O']['APPLY']
        self.hmcconn.execute(chsyscfgCmd)

    def managedSystemShutdown(self, cecName):
        chsysstateCmd = self.CMD['CHSYSSTATE'] + \
            self.OPT['CHSYSSTATE']['-R']['SYS'] + \
            self.OPT['CHSYSSTATE']['-M'] + cecName +\
            self.OPT['CHSYSSTATE']['-O']['OFF']
        self.hmcconn.execute(chsysstateCmd)

    def managedSystemPowerON(self, cecName):
        chsysstateCmd = self.CMD['CHSYSSTATE'] + \
            self.OPT['CHSYSSTATE']['-R']['SYS'] + \
            self.OPT['CHSYSSTATE']['-M'] + cecName +\
            self.OPT['CHSYSSTATE']['-O']['ON']
        self.hmcconn.execute(chsysstateCmd)

    def getManagedSystemDetails(self, cecName):
        lssyscfgCmd = self.CMD['LSSYSCFG'] + \
            self.OPT['LSSYSCFG']['-R']['SYS'] + \
            self.OPT['LSSYSCFG']['-M'] + cecName
        result = self.hmcconn.execute(lssyscfgCmd)
        res_dict = self.cmdClass.parseCSV(result)
        res = dict((k.lower(), v) for k, v in res_dict.items())
        return res

    def getManagedSystemHwres(self, system_name, resource, level):
        lshwresCmd = self.CMD['LSHWRES'] + \
            self.OPT['LSHWRES']['-R'] + resource + \
            self.OPT['LSHWRES']['-M'] + system_name + \
            self.OPT['LSHWRES']['--LEVEL'] + level
        result = self.hmcconn.execute(lshwresCmd)
        res_dict = self.cmdClass.parseCSV(result)
        res = dict((k.lower(), v) for k, v in res_dict.items())
        return res

    def checkManagedSysState(self, cecName, expectedStates, timeoutInMin=12):
        POLL_INTERVAL_IN_SEC = 30
        WAIT_UNTIL_IN_SEC = timeoutInMin * 60

        # Polling logic to make sure CEC state changed as expectedState
        waited = 0
        stateSuccess = False
        while waited < WAIT_UNTIL_IN_SEC:
            res = self.getManagedSystemDetails(cecName)
            cec_state = res.get('state')
            if cec_state in expectedStates:
                logger.debug(cec_state)
                stateSuccess = True
                break
            else:
                logger.debug(cec_state)
                waited += POLL_INTERVAL_IN_SEC

            # waiting for 30 seconds
            time.sleep(POLL_INTERVAL_IN_SEC)

        return stateSuccess

    def confSysGenSettings(self, cecName, sysConfig):
        sysConfig = self.cmdClass.convertKeysToUpper(sysConfig)
        chsyscfgCmd = self.CMD['CHSYSCFG'] + \
            self.OPT['CHSYSCFG']['-R']['SYS'] + \
            self.OPT['CHSYSCFG']['-M'] + cecName
        chsyscfgCmd += self.cmdClass.i_a_ConfigBuilder('CHSYSCFG', '-I', sysConfig)
        logger.debug(chsyscfgCmd)
        self.hmcconn.execute(chsyscfgCmd)

    def confSysMem(self, cecName, sysConfig, oper):
        oper = oper.upper()
        sysConfig = self.cmdClass.convertKeysToUpper(sysConfig)
        chhwresCmd = self.CMD['CHHWRES'] + \
            self.OPT['CHHWRES']['-R']['MEM'] + \
            self.OPT['CHHWRES']['-M'] + cecName + \
            self.OPT['CHHWRES']['-O'][oper]
        chhwresCmd += self.cmdClass.i_a_ConfigBuilder('CHHWRES', '-A', sysConfig)
        logger.debug(chhwresCmd)
        self.hmcconn.execute(chhwresCmd)

    def migratePartitions(self, opr, srcCEC, dstCEC=None, lparNames=None, lparIDs=None, aLL=False):
        opr = opr.upper()
        migrlparCmd = self.CMD['MIGRLPAR'] + \
            self.OPT['MIGRLPAR']['-O'][opr] +\
            self.OPT['MIGRLPAR']['-M'] + srcCEC
        if opr != 'R':
            migrlparCmd += self.OPT['MIGRLPAR']['-T'] + dstCEC
        if lparNames:
            migrlparCmd += self.OPT['MIGRLPAR']['-P'] + lparNames
        elif lparIDs:
            migrlparCmd += self.OPT['MIGRLPAR']['--ID'] + lparIDs
        elif aLL:
            migrlparCmd += self.OPT['MIGRLPAR']['--ALL']
        self.hmcconn.execute(migrlparCmd)

    def _configMandatoryLparSettings(self, delta_config=None):
        lparMandatConfig = {'PROFILE_NAME': 'default_profile',
                            'MIN_MEM': '2048',
                            'DESIRED_MEM': '2048',
                            'MAX_MEM': '4096',
                            'MIN_PROCS': '2',
                            'DESIRED_PROCS': '2',
                            'MAX_PROCS': '4',
                            'BOOT_MODE': 'norm',
                            'PROC_MODE': 'ded',
                            'SHARING_MODE': 'keep_idle_procs',
                            'MAX_VIRTUAL_SLOTS': '20'}

        if delta_config:

            if delta_config.get('all_resources'):
                lparMandatConfig = {'PROFILE_NAME': delta_config.get('profile_name') or 'default'}
                for eachKey in delta_config:
                    lparMandatConfig[eachKey.upper()] = str(delta_config[eachKey])
                return lparMandatConfig

            lparMandatConfig['MAX_MEM'] = str(delta_config.get('desired_mem') or lparMandatConfig['MAX_MEM'])
            lparMandatConfig['MAX_PROCS'] = str(delta_config.get('desired_procs') or lparMandatConfig['MAX_PROCS'])

            for eachKey in delta_config:
                if 'proc_mode' == eachKey and delta_config['proc_mode'] == 'shared':
                    if 'max_proc_units' not in delta_config:
                        lparMandatConfig['MAX_PROC_UNITS'] = str(delta_config.get('desired_proc_units') or '1.0')
                    if 'min_proc_units' not in delta_config:
                        lparMandatConfig['MIN_PROC_UNITS'] = '0.1'
                    if 'desired_proc_units' not in delta_config:
                        lparMandatConfig['DESIRED_PROC_UNITS'] = '0.5'
                    if 'sharing_mode' not in delta_config:
                        lparMandatConfig['SHARING_MODE'] = 'cap'

                lparMandatConfig[eachKey.upper()] = str(delta_config[eachKey])

        return lparMandatConfig

    def createVirtualIOServer(self, system_name, name, vios_config=None):

        viosconfig = {'LPAR_ENV': 'vioserver'}
        viosconfig['NAME'] = name
        viosconfig.update(self._configMandatoryLparSettings(vios_config))

        invalid_settings_keys = [key for key in viosconfig.keys() if key not in self.OPT['MKSYSCFG']['-I']]
        if invalid_settings_keys:
            raise ParameterError("Invalid attributes: {0}".format(','.join(invalid_settings_keys)))

        mksyscfg = self.CMD['MKSYSCFG'] +\
            self.OPT['MKSYSCFG']['-R']['LPAR'] +\
            self.OPT['MKSYSCFG']['-M'] + system_name + \
            self.cmdClass.i_a_ConfigBuilder('MKSYSCFG', '-I', viosconfig)

        self.hmcconn.execute(mksyscfg)

    def getPartitionConfig(self, system_name, name, prof=None):
        filter_config = dict(LPAR_NAMES=name)
        lssyscfg = self.CMD['LSSYSCFG'] +\
            self.OPT['LSSYSCFG']['-R']['LPAR'] +\
            self.OPT['LSSYSCFG']['-M'] + system_name +\
            self.cmdClass.filterBuilder("LSSYSCFG", filter_config)

        result = self.hmcconn.execute(lssyscfg)
        res_dict = self.cmdClass.parseCSV(result)
        res = dict((k.lower(), v) for k, v in res_dict.items())

        if prof:
            filter_config['PROFILE_NAMES'] = prof
            logger.debug(filter_config)
            lssyscfg_prof = self.CMD['LSSYSCFG'] +\
                self.OPT['LSSYSCFG']['-R']['PROF'] +\
                self.OPT['LSSYSCFG']['-M'] + system_name +\
                self.cmdClass.filterBuilder("LSSYSCFG", filter_config)

            result_prof = self.hmcconn.execute(lssyscfg_prof)
            res_dict_prof = self.cmdClass.parseCSV(result_prof)
            res_prof = dict((k.lower(), v) for k, v in res_dict_prof.items())
            res.update({'profile_config': res_prof})

        return res

    def _parseIODetailsFromNetboot(self, result):
        lns = result.strip('\n').split('\n')
        res = []
        for ln in lns:
            di = {}
            if not ln.lstrip().startswith('#'):
                x = ln.split()
                di['Type'] = x[0]
                di['Location Code'] = x[1]
                di['MAC Address'] = x[2]
                di['Full Path Name'] = x[3]
                di['Ping Result'] = x[4]
                di['Device Type'] = x[5]
                res.append(di)
        return res

    def fetchIODetailsForNetboot(self, nimIP, gateway, lparIP, viosName, profName, systemName):
        lpar_netboot = self.CMD['LPAR_NETBOOT'] +\
            self.OPT['LPAR_NETBOOT']['-A'] +\
            self.OPT['LPAR_NETBOOT']['-M'] +\
            self.OPT['LPAR_NETBOOT']['-D'] +\
            self.OPT['LPAR_NETBOOT']['-N'] +\
            self.OPT['LPAR_NETBOOT']['-T'] + "ent" +\
            self.OPT['LPAR_NETBOOT']['-S'] + nimIP +\
            self.OPT['LPAR_NETBOOT']['-G'] + gateway +\
            self.OPT['LPAR_NETBOOT']['-C'] + lparIP +\
            " " + viosName + " " + profName + " " + systemName
        result = self.hmcconn.execute(lpar_netboot)
        return self._parseIODetailsFromNetboot(result)

    def installVIOSFromNIM(self, loc_code, nimIP, gateway, lparIP, vlanID, vlanPrio, submask, viosName, profName, systemName):
        lpar_netboot = self.CMD['LPAR_NETBOOT'] +\
            self.OPT['LPAR_NETBOOT']['-F'] +\
            self.OPT['LPAR_NETBOOT']['-D'] +\
            self.OPT['LPAR_NETBOOT']['-T'] + "ent" +\
            self.OPT['LPAR_NETBOOT']['-L'] + loc_code +\
            self.OPT['LPAR_NETBOOT']['-S'] + nimIP +\
            self.OPT['LPAR_NETBOOT']['-G'] + gateway +\
            self.OPT['LPAR_NETBOOT']['-C'] + lparIP +\
            self.OPT['LPAR_NETBOOT']['-V'] + vlanID +\
            self.OPT['LPAR_NETBOOT']['-Y'] + vlanPrio +\
            self.OPT['LPAR_NETBOOT']['-K'] + submask +\
            " " + viosName + " " + profName + " " + systemName
        self.hmcconn.execute(lpar_netboot)

    def getPartitionRefcode(self, system_name, name):
        filter_config = dict(LPAR_NAMES=name)
        lsrefcode = self.CMD['LSREFCODE'] +\
            self.OPT['LSREFCODE']['-R']['LPAR'] +\
            self.OPT['LSREFCODE']['-M'] + system_name +\
            self.cmdClass.filterBuilder("LSREFCODE", filter_config)
        result = self.hmcconn.execute(lsrefcode)
        res_dict = self.cmdClass.parseCSV(result)
        res = dict((k, v) for k, v in res_dict.items())

        return res

    def runCommandOnVIOS(self, system_name, name, cmd):
        viosvrcmd = self.CMD['VIOSVRCMD'] +\
            self.OPT['VIOSVRCMD']['-M'] + system_name +\
            self.OPT['VIOSVRCMD']['-P'] + name +\
            self.OPT['VIOSVRCMD']['-C'] + '"' + cmd + '"'
        self.hmcconn.execute(viosvrcmd)
