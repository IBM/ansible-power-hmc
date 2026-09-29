#
#    @author  Anil Vijayan
#
##

from __future__ import absolute_import, division, print_function
__metaclass__ = type
import time
import re
import multiprocessing
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
        pattern = re.compile(r"(\d) (packets\s)?received")
        report = ("No response", "Partial Response", "Alive")
        cmd = "ping -c 2 " + i_host.strip()

        result = 'No response'
        rc, stdout_value, stderr_value = self.hmcconn.module.run_command(cmd, use_unsafe_shell=True)

        if isinstance(stdout_value, bytes):
            stdout_value = stdout_value.decode('ascii')

        igot = re.findall(pattern, stdout_value)
        if igot:
            result = report[int(igot[0][0])]

        return result

    def sshTest(self, i_host, u_host):
        pattern = re.compile(r"Alive")
        report = ("No response", "Alive")
        cmd = "ssh -o ConnectTimeout=5 -o Batchmode=yes " + u_host.strip() + "@" + i_host.strip() + " echo 'Alive'"

        result = report[0]
        rc, stdout_value, stderr_value = self.hmcconn.module.run_command(cmd, use_unsafe_shell=True)

        if isinstance(stdout_value, bytes):
            stdout_value = stdout_value.decode('ascii')

        igot = re.findall(pattern, stdout_value)
        if igot:
            result = report[1]

        return result

    def checkHmcUpandRunning(self, rebootStarted=False, timeoutInMin=12):
        POLL_INTERVAL_IN_SEC = 30
        WAIT_UNTIL_IN_SEC = timeoutInMin * 60

        # Polling logic to make sure hmc pinging after reboot
        waited = 0
        pingSuccess = False
        while waited < WAIT_UNTIL_IN_SEC:
            # This section of code is used when the ICMP is disabled HMC and this confirms
            # HMC active status by SSHing to it and this routine works only in case of password less authentication
            if waited % 150 == 0 and None is self.hmcconn.pwd and rebootStarted:
                ssh_state = self.sshTest(self.hmcconn.ip, self.hmcconn.user)
                logger.debug(ssh_state)
                if "Alive" in ssh_state:
                    logger.debug("SSH Alive")
                    pingSuccess = True
                    break

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

    def listUpgradeFiles(self, locationType, configDict=None):
        hmcCmd = self.CMD['LSUPGFILES'] + \
            self.OPT['LSUPGFILES']['-R'][locationType.upper()]

        result = self.hmcconn.execute(hmcCmd)
        if 'No results were found.' in result:
            return 'No upgrade files available'
        return self.cmdClass.parseMultiLineCSV(result)

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

    def listHMCPTF(self, locationType, configDict=None):
        hmcCmd = self.CMD['LSUPDHMC'] + \
            self.OPT['LSUPDHMC']['-T'][locationType.upper()]

        result = self.hmcconn.execute(hmcCmd)
        if 'No results were found.' in result:
            return 'No PTFs are available'
        return self.cmdClass.parseMultiLineCSV(result)

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

    def updateProfileName(self, system_name, lparName, prof_name, next_profile_name):
        chsyscfgCmd = self.CMD['CHSYSCFG'] + \
            self.OPT['CHSYSCFG']['-R']['PROF'] + \
            self.OPT['CHSYSCFG']['-M'] + system_name + \
            self.OPT['CHSYSCFG']['--FORCE'] + \
            "-i '" + self.OPT['CHSYSCFG']['-I']['NAME'] + f"={next_profile_name}," + \
            self.OPT['CHSYSCFG']['-I']['LPAR_NAME'] + "=" + lparName + "," + \
            self.OPT['CHSYSCFG']['-I']['NEW_NAME'] + "=" + prof_name + "'"

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

    def getManagedSystemDetails(self, cecName, config_F=None):
        lssyscfgCmd = self.CMD['LSSYSCFG'] + \
            self.OPT['LSSYSCFG']['-R']['SYS'] + \
            self.OPT['LSSYSCFG']['-M'] + cecName
        if config_F is not None:
            lssyscfgCmd += self.OPT['LSSYSCFG']['-F'] + config_F
            return self.hmcconn.execute(lssyscfgCmd)
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

    def migratePartitions(self, opr, srcCEC, dstCEC=None, lparNames=None, lparIDs=None, aLL=False, ip=None, wait=None, pool=None):
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
        if ip:
            migrlparCmd += self.OPT['MIGRLPAR']['--IP'] + ip
        if wait:
            migrlparCmd += self.OPT['MIGRLPAR']['-W'] + str(wait)
        if pool and opr == 'M':
            if '/' not in str(pool):
                if pool.isdigit():
                    migrlparCmd += " " + self.OPT['MIGRLPAR']['-I'] + '"shared_proc_pool_id=' + str(pool) + '"'
                else:
                    migrlparCmd += " " + self.OPT['MIGRLPAR']['-I'] + '"shared_proc_pool_name=' + str(pool) + '"'
            else:
                if '//' in str(pool):
                    migrlparCmd += " " + self.OPT['MIGRLPAR']['-I'] + '\\' + '"multiple_shared_proc_pool_names=' + str(pool) + '\\' + '"'
                else:
                    migrlparCmd += " " + self.OPT['MIGRLPAR']['-I'] + '\\' + '"multiple_shared_proc_pool_ids=' + str(pool) + '\\' + '"'
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

    def fetchIODetailsForNetboot(self, nimIP, gateway, lparIP, viosName, profName, systemName, submask):
        lpar_netboot = self.CMD['LPAR_NETBOOT'] +\
            self.OPT['LPAR_NETBOOT']['-A'] +\
            self.OPT['LPAR_NETBOOT']['-M'] +\
            self.OPT['LPAR_NETBOOT']['-D'] +\
            self.OPT['LPAR_NETBOOT']['-N'] +\
            self.OPT['LPAR_NETBOOT']['-T'] + "ent" +\
            self.OPT['LPAR_NETBOOT']['-S'] + nimIP +\
            self.OPT['LPAR_NETBOOT']['-G'] + gateway +\
            self.OPT['LPAR_NETBOOT']['-C'] + lparIP +\
            self.OPT['LPAR_NETBOOT']['-K'] + submask +\
            " " + viosName + " " + profName + " " + systemName

        result = self.hmcconn.execute(lpar_netboot)
        return self._parseIODetailsFromNetboot(result)

    def installOSFromNIM(self, loc_code, nimIP, gateway, lparIP, vlanID, vlanPrio, submask, viosName, profName, systemName, lparMac=None):
        if loc_code:
            os_command = self.OPT['LPAR_NETBOOT']['-L'] + loc_code +\
                self.OPT['LPAR_NETBOOT']['-V'] + vlanID +\
                self.OPT['LPAR_NETBOOT']['-Y'] + vlanPrio
        elif lparMac:
            os_command = self.OPT['LPAR_NETBOOT']['-x'] +\
                self.OPT['LPAR_NETBOOT']['-v'] +\
                self.OPT['LPAR_NETBOOT']['-i'] +\
                self.OPT['LPAR_NETBOOT']['-s'] + "auto" +\
                self.OPT['LPAR_NETBOOT']['-d'] + "auto" +\
                self.OPT['LPAR_NETBOOT']['-m'] + lparMac
        else:
            pass

        lpar_netboot = self.CMD['LPAR_NETBOOT'] + self.OPT['LPAR_NETBOOT']['-F'] +\
            self.OPT['LPAR_NETBOOT']['-D'] +\
            self.OPT['LPAR_NETBOOT']['-T'] + "ent" +\
            self.OPT['LPAR_NETBOOT']['-S'] + nimIP +\
            self.OPT['LPAR_NETBOOT']['-G'] + gateway +\
            self.OPT['LPAR_NETBOOT']['-C'] + lparIP +\
            self.OPT['LPAR_NETBOOT']['-K'] + submask +\
            os_command +\
            " " + viosName + " " + profName + " " + systemName
        self.hmcconn.execute(lpar_netboot)

    def installOSFromDisk(self, vios_iso, image_dir, vios_IP, vios_gateway, vios_subnetmask, network_macaddr, system_name, name, prof_name, label=None):
        default_path = "/extra/viosimages/"
        installiosCmd = ''
        installiosCmd = self.CMD['INSTALLIOS'] +\
            self.OPT['INSTALLIOS']['-D'] + default_path + image_dir + "/" + vios_iso +\
            self.OPT['INSTALLIOS']['-I'] + vios_IP +\
            self.OPT['INSTALLIOS']['-G'] + vios_gateway +\
            self.OPT['INSTALLIOS']['-S'] + vios_subnetmask +\
            self.OPT['INSTALLIOS']['-M'] + network_macaddr +\
            self.OPT['INSTALLIOS']['-s'] + system_name +\
            self.OPT['INSTALLIOS']['-P'] + name +\
            self.OPT['INSTALLIOS']['-r'] + prof_name
        if label is not None:
            installiosCmd += self.OPT['INSTALLIOS']['-R'] + label
        logger.debug(installiosCmd)
        self.hmcconn.execute(installiosCmd)

    def getconsolelog(self, module, lpar_hmc, userid, hmc_password, systemName, lparName):
        conn = HmcCliConnection(module, lpar_hmc, userid, hmc_password)
        cmd = 'rmvterm -m ' + systemName + ' -p ' + lparName
        conn.execute(cmd)
        cmd = 'mkvterm -m ' + systemName + ' -p ' + lparName
        stdout = conn.execute(cmd)
        try:
            for line in stdout:
                logger.debug(line.strip())
                logger.debug("\n")
        except UnicodeDecodeError:
            pass

    def checkconsolelog(self, module, lpar_ip, lpar_hmc, userid, hmc_password, systemName, lparName):
        logger.info("Installation will take approximatly 10-12 mins to complete.")
        process = multiprocessing.Process(target=self.getconsolelog, args=(module, lpar_hmc, userid, hmc_password, systemName, lparName))
        process.start()
        time.sleep(360)
        process.terminate()
        process.join()

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

    def runCommandOnVIOS(self, system_name, name, cmd, flag=None):
        viosvrcmd = self.CMD['VIOSVRCMD'] +\
            self.OPT['VIOSVRCMD']['-M'] + system_name +\
            self.OPT['VIOSVRCMD']['-P'] + name
        if flag is True:
            viosvrcmd += self.OPT['VIOSVRCMD']['--ADMIN']
        viosvrcmd += self.OPT['VIOSVRCMD']['-C'] + '"' + cmd + '"'
        if flag is not None:
            return self.hmcconn.execute(viosvrcmd)
        self.hmcconn.execute(viosvrcmd)

    def authenticateHMCs(self, remote_hmc, username=None, passwd=None, test=False):
        mkauthcmd = self.CMD['MKAUTHKEYS'] +\
            self.OPT['MKAUTHKEYS']['--IP'] + remote_hmc
        if test:
            mkauthcmd += self.OPT['MKAUTHKEYS']['--TEST']
        else:
            mkauthcmd += self.OPT['MKAUTHKEYS']['-G'] +\
                self.OPT['MKAUTHKEYS']['-U'] + username +\
                self.OPT['MKAUTHKEYS']['--PASSWD'] + passwd
        self.hmcconn.execute(mkauthcmd)

    def listUsr(self, user_type=None, filt=None):
        listHmcUsr = self.CMD['LSHMCUSR']
        if user_type:
            listHmcUsr += self.OPT['LSHMCUSR']['-T'][user_type.upper()]
        if filt:
            listHmcUsr += self.cmdClass.filterBuilder('LSHMCUSR', filt)
        result = self.hmcconn.execute(listHmcUsr)
        if 'No results were found' in result:
            return []
        return self.cmdClass.parseMultiLineCSV(result)

    def createUsr(self, configDict):
        config = {each.upper(): str(configDict[each]) for each in configDict if configDict[each] is not None}
        mkhmcusrCmd = self.CMD['MKHMCUSR'] +\
            self.cmdClass.i_a_ConfigBuilder('MKHMCUSR', '-I', config)
        self.hmcconn.execute(mkhmcusrCmd)

    def modifyUsr(self, configDict=None, enable=False, modify_type=None):
        chhmcusrCmd = self.CMD['CHHMCUSR']
        config = {each.upper(): str(configDict[each]) for each in configDict if configDict[each] is not None}
        if enable:
            chhmcusrCmd += self.OPT['CHHMCUSR']['-O']['E'] +\
                self.OPT['CHHMCUSR']['-U'] + config['NAME']
        elif modify_type == 'default' and config:
            chhmcusrCmd += self.OPT['CHHMCUSR']['-T']['DEFAULT'] +\
                self.cmdClass.i_a_ConfigBuilder('CHHMCUSR', '-I', config)
        elif config:
            chhmcusrCmd += self.cmdClass.i_a_ConfigBuilder('CHHMCUSR', '-I', config)
        self.hmcconn.execute(chhmcusrCmd)

    def removeUsr(self, usr=None, rm_type=None):
        rmhmcusrCmd = self.CMD['RMHMCUSR']
        if usr:
            rmhmcusrCmd += self.OPT['RMHMCUSR']['-U'] + usr
        elif rm_type:
            rmhmcusrCmd += self.OPT['RMHMCUSR']['-T'][rm_type.upper()]
        self.hmcconn.execute(rmhmcusrCmd)

    def listViosbk(self, filt=None):
        listViosBk = self.CMD['LSVIOSBK']
        if filt:
            listViosBk += self.cmdClass.filterBuilder('LSVIOSBK', filt)
        result = self.hmcconn.execute(listViosBk)
        if 'No results were found' in result:
            return []
        return self.cmdClass.parseMultiLineCSV(result)

    def createViosBk(self, configDict=None, enable=False, modify_type=None):
        optional = ['nimol_resource', 'media_repository', 'volume_group_structure']
        opt = []
        output = ""
        for each in optional:
            if configDict.get(each) is not None:
                opt.append("{}={}".format(each, configDict[each]))
        output = ','.join(opt)
        viosbk_cmd = self.CMD['MKVIOSBK'] + \
            self.OPT['MKVIOSBK']['-T'] + configDict['types'] + \
            self.OPT['MKVIOSBK']['-M'] + configDict['system'] + \
            self.OPT['MKVIOSBK']['-F'] + configDict['backup_name'] + " "
        if configDict['vios_name'] is not None:
            viosbk_cmd += self.OPT['MKVIOSBK']['-P'] + configDict['vios_name'] + " "
        elif configDict['vios_id'] is not None:
            viosbk_cmd += self.OPT['MKVIOSBK']['--ID'] + configDict['vios_id'] + " "
        elif configDict['vios_uuid'] is not None:
            viosbk_cmd += self.OPT['MKVIOSBK']['--UUID'] + configDict['vios_uuid'] + " "
        if output != "":
            viosbk_cmd += self.OPT['MKVIOSBK']['-A'] + '"' + output + '"'
        return self.hmcconn.execute(viosbk_cmd)

    def restoreViosBk(self, configDict=None, enable=False, modify_type=None):
        restore_cmd = self.CMD['RSTVIOSBK'] + \
            self.OPT['RSTVIOSBK']['-T'] + configDict['types'] + \
            self.OPT['RSTVIOSBK']['-M'] + configDict['system'] + \
            self.OPT['RSTVIOSBK']['-F'] + configDict['backup_name'] + " "
        if configDict['vios_name'] is not None:
            restore_cmd += self.OPT['RSTVIOSBK']['-P'] + configDict['vios_name'] + " "
        elif configDict['vios_id'] is not None:
            restore_cmd += self.OPT['RSTVIOSBK']['--ID'] + configDict['vios_id'] + " "
        elif configDict['vios_uuid'] is not None:
            restore_cmd += self.OPT['RSTVIOSBK']['--UUID'] + configDict['vios_uuid'] + " "
        if configDict['restart'] is not None:
            restore_cmd += self.OPT['RSTVIOSBK']['-R']
        self.hmcconn.execute(restore_cmd)

    def removeViosBk(self, configDict=None, enable=False, modify_type=None):
        rmviosbk_cmd = self.CMD['RMVIOSBK'] + \
            self.OPT['RMVIOSBK']['-T'] + configDict['types'] + \
            self.OPT['RMVIOSBK']['-M'] + configDict['system'] + \
            self.OPT['RMVIOSBK']['-F'] + configDict['backup_name'] + " "
        if configDict['vios_name'] is not None:
            rmviosbk_cmd += self.OPT['MKVIOSBK']['-P'] + configDict['vios_name']
        elif configDict['vios_id'] is not None:
            rmviosbk_cmd += self.OPT['MKVIOSBK']['--ID'] + configDict['vios_id']
        elif configDict['vios_uuid'] is not None:
            rmviosbk_cmd += self.OPT['MKVIOSBK']['--UUID'] + configDict['vios_uuid']
        return self.hmcconn.execute(rmviosbk_cmd)

    def modifyViosBk(self, configDict=None, enable=False, modify_type=None):
        modviosbk_cmd = self.CMD['CHVIOSBK'] + \
            self.OPT['CHVIOSBK']['-T'] + configDict['types'] + \
            self.OPT['CHVIOSBK']['-M'] + configDict['system'] + \
            self.OPT['CHVIOSBK']['-F'] + configDict['backup_name'] + " "
        modviosbk_cmd += self.OPT['CHVIOSBK']['-O'] + "s "
        if configDict['vios_name'] is not None:
            modviosbk_cmd += self.OPT['CHVIOSBK']['-P'] + configDict['vios_name']
        elif configDict['vios_id'] is not None:
            modviosbk_cmd += self.OPT['CHVIOSBK']['--ID'] + configDict['vios_id']
        elif configDict['vios_uuid'] is not None:
            modviosbk_cmd += self.OPT['CHVIOSBK']['--UUID'] + configDict['vios_uuid']
        modviosbk_cmd += " " + self.OPT['CHVIOSBK']['-A'] + "'new_name=" + configDict['new_name'] + "'"
        return self.hmcconn.execute(modviosbk_cmd)

    def checkForOSToBootUpFully(self, system_name, name, timeoutInMin=60):
        POLL_INTERVAL_IN_SEC = 30
        WAIT_UNTIL_IN_SEC = timeoutInMin * 60 - 600
        waited = 0
        rmcActive = False
        ref_code = None
        # wait for 10 mins before polling
        time.sleep(600)
        while waited < WAIT_UNTIL_IN_SEC:
            conf_dict = self.getPartitionConfig(system_name, name)
            if conf_dict['rmc_state'] == 'active':
                rmcActive = True
                break
            waited += POLL_INTERVAL_IN_SEC
            time.sleep(POLL_INTERVAL_IN_SEC)
        if not rmcActive:
            res = self.getPartitionRefcode(system_name, name)
            ref_code = res['REFCODE']
        return rmcActive, conf_dict, ref_code

    def accept_level(self, system_name):
        updlic_cmd = self.CMD['UPDLIC'] +\
            self.OPT['UPDLIC']['-M'] + system_name +\
            self.OPT['UPDLIC']['-O']['ACCEPT']

        return self.hmcconn.execute(updlic_cmd)

    def get_latest_firmware_level(self, system_name, upgrade=False, repo='ibmwebsite', level='latest', remote_repo=None):
        if upgrade:
            update_upgrade_flags = 'upgrade'
        else:
            update_upgrade_flags = 'update'

        lslic_cmd = self.CMD['LSLIC'] +\
            self.OPT['LSLIC']['-M'] + system_name +\
            self.OPT['LSLIC']['-T']['SYS'] +\
            self.OPT['LSLIC']['-R'] + repo +\
            self.OPT['LSLIC']['-L'] + update_upgrade_flags +\
            self.OPT["LSLIC"]['-F']['AVAILABLE_LEVEL_FIELDS']
        if remote_repo:
            lslic_cmd += self.OPT['LSLIC']['-H'] + remote_repo['hostname']
            lslic_cmd += self.OPT['LSLIC']['-U'] + remote_repo['userid']
            lslic_cmd += self.OPT['LSLIC']['-D'] + remote_repo['directory']
            passwd = remote_repo['passwd']
            if passwd:
                lslic_cmd += self.OPT['LSLIC']['--PASSWD'] + passwd
            ssh_key = remote_repo['sshkey_file']
            if ssh_key:
                lslic_cmd += self.OPT['LSLIC']['-K'] + ssh_key

        raw_result = self.hmcconn.execute(lslic_cmd)
        if 'No results were found.' in raw_result:
            return f"No {update_upgrade_flags} files available in '{repo}' repository"
        headers = "level,spname,concurrency"
        res_dict = self.cmdClass.parseMultiLineCSV(raw_result, userConfig={'-F': headers})
        filtered = res_dict
        if level == 'latestconcurrent':
            filtered = [r for r in res_dict if r['concurrency'].lower() == 'concurrent']
            if not filtered:
                return f"No Concurrent {update_upgrade_flags} files available for '{repo}' repository"
        latest_level = max(filtered, key=lambda x: int(x['level']))
        return latest_level

    def update_managed_system(self, system_name, upgrade=False, repo='ibmwebsite', level='latest', remote_repo=None):
        if upgrade:
            update_upgrade_flags = self.OPT['UPDLIC']['-O']['UPGRADE']
        else:
            update_upgrade_flags = self.OPT['UPDLIC']['-O']['RETINSTACT']
        # build command
        updlic_cmd = self.CMD['UPDLIC'] +\
            self.OPT['UPDLIC']['-M'] + system_name +\
            update_upgrade_flags +\
            self.OPT['UPDLIC']['-T']['SYS'] +\
            self.OPT['UPDLIC']['-R'] + repo +\
            self.OPT['UPDLIC']['-L'] + level
        if remote_repo:
            updlic_cmd += self.OPT['UPDLIC']['-H'] + remote_repo['hostname']
            updlic_cmd += self.OPT['UPDLIC']['-U'] + remote_repo['userid']
            updlic_cmd += self.OPT['UPDLIC']['-D'] + remote_repo['directory']
            passwd = remote_repo['passwd']
            if passwd:
                updlic_cmd += self.OPT['UPDLIC']['--PASSWD'] + passwd
            ssh_key = remote_repo['sshkey_file']
            if ssh_key:
                updlic_cmd += self.OPT['UPDLIC']['-K'] + ssh_key

        self.hmcconn.execute(updlic_cmd)

    def get_firmware_level(self, system_name):
        lslic_cmd = self.CMD['LSLIC'] +\
            self.OPT['LSLIC']['-M'] + system_name +\
            self.OPT['LSLIC']['-F']['SPNAMELEVEL']
        raw_result = self.hmcconn.execute(lslic_cmd)
        headers = "service_pack,level,ecnumber"
        res_dict = self.cmdClass.parseAttributes(headers, raw_result)
        parsed_res = dict((k.lower(), v) for k, v in res_dict.items())
        return parsed_res

    def get_managed_system_gen(self, system_name):
        lslic_cmd = self.CMD['LSLIC'] + \
            self.OPT['LSLIC']['-T']['SYS'] + \
            self.OPT['LSLIC']['-M'] + system_name + \
            self.OPT['LSLIC']['-F']['SPNAMELEVEL']
        raw_result = self.hmcconn.execute(lslic_cmd)
        headers = "service_pack,level,ecnumber"
        res_dict = self.cmdClass.parseAttributes(headers, raw_result)
        service_pack = res_dict.get('service_pack', '').strip().lower()
        match = re.match(r'^fw(\d+)', service_pack)
        if not match:
            return None
        digits = match.group(1)
        if digits.startswith('9'):
            version = '9'
        else:
            version = digits[:2]
        return f'power{version}'

    def get_io_sriov_level(self, system_name, lic_type):

        if lic_type == 'sriov':
            field_key = 'SRIOVLEVEL'
            headers = "adapter_id,active_adapter_driver_level,active_adapter_level"
        elif lic_type == 'io':
            field_key = 'IOLEVEL'
            headers = "logical_device,current_level"
        else:
            raise ValueError("Unsupported lic_type. Must be 'sriov' or 'io'.")

        lslic_cmd = self.CMD['LSLIC'] + \
            self.OPT['LSLIC']['-T'] + ' ' + lic_type + \
            self.OPT['LSLIC']['-M'] + system_name + \
            self.OPT['LSLIC']['-F'][field_key]

        raw_result = self.hmcconn.execute(lslic_cmd)
        return self.cmdClass.parseMultiLineCSV(raw_result, userConfig={'-F': headers})

    def list_all_managed_systems(self):
        lssysconn_cmd = self.CMD['LSSYSCONN'] +\
            self.OPT['LSSYSCONN']['-R']['ALL'] +\
            self.OPT['LSSYSCONN']['-F']['MTMS']

        raw_result = self.hmcconn.execute(lssysconn_cmd)
        lines = raw_result.split()
        return lines

    def list_HMC_LDAP(self, resource, filt=None):
        lshmcldap_cmd = self.CMD['LSHMCLDAP'] +\
            self.OPT['LSHMCLDAP']['-R'][resource.upper()]
        if filt:
            lshmcldap_cmd += self.cmdClass.filterBuilder('LSHMCLDAP', filt)
        result = self.hmcconn.execute(lshmcldap_cmd)
        if 'LDAP server is not configured' in result:
            return []
        return self.cmdClass.parseMultiLineCSV(result)

    def configure_LDAP_on_HMC(self, operation, configDict=None, resource=None):
        chhmcldap = self.CMD['CHHMCLDAP']
        if operation == 'set':
            chhmcldap += self.OPT['CHHMCLDAP']['-O']['S']
            config = {each.upper(): str(configDict[each]) for each in configDict if configDict[each] is not None}
            chhmcldap += self.cmdClass.configBuilder('CHHMCLDAP', config)
        elif operation == 'remove':
            resource = resource.upper()
            chhmcldap += self.OPT['CHHMCLDAP']['-O']['R'] +\
                self.OPT['CHHMCLDAP']['-R'][resource]
        self.hmcconn.execute(chhmcldap)

    def list_all_managed_system_details(self, config_F=None):
        lssyscfgCmd = self.CMD['LSSYSCFG'] +\
            self.OPT['LSSYSCFG']['-R']['SYS']
        if config_F:
            lssyscfgCmd += self.OPT['LSSYSCFG']['-F'] + config_F

        raw_result = self.hmcconn.execute(lssyscfgCmd)
        user_config = {"-F": config_F}
        res = self.cmdClass.parseMultiLineCSV(raw_result, user_config)
        return res

    def list_all_lpars_details(self, sys_name, filter=None):
        lines = []
        lssyscfgCmd = self.CMD['LSSYSCFG'] +\
            self.OPT['LSSYSCFG']['-R']['LPAR'] +\
            self.OPT['LSSYSCFG']['-M'] + sys_name
        if filter:
            lssyscfgCmd += self.OPT['LSSYSCFG']['-F'] + filter

        raw_result = self.hmcconn.execute(lssyscfgCmd)
        raw_result = raw_result.replace("Power Off", "Off")
        lines = raw_result.strip().split()

        return lines

    def getSystemNameFromMTMS(self, system_name):
        attr_dict = self.getManagedSystemDetails(system_name)
        return attr_dict.get('name')

    def copyViosImage(self, params):
        media = params['media'].lower()
        mount_location = params['mount_location']
        remote_server = params['remote_server']
        directory_name = params['directory_name']
        files = params['files']
        remote_directory = params['remote_directory']
        options = params['options']
        ssh_key_file = params['ssh_key_file']

        if files:
            files = ','.join(files)

        if options:
            options = '"ver={}"'.format(options)

        if media == 'sftp':
            sftp_user = params['sftp_auth']['sftp_username']
            sftp_password = params['sftp_auth']['sftp_password']
            cpviosimgCmd = self.CMD['CPVIOSIMG'] +\
                self.OPT['CPVIOSIMG']['-R']['SFTP'] +\
                self.OPT['CPVIOSIMG']['-N'] + directory_name +\
                self.OPT['CPVIOSIMG']['-H'] + remote_server +\
                self.OPT['CPVIOSIMG']['-U'] + sftp_user +\
                self.OPT['CPVIOSIMG']['-F'] + files
            if remote_directory:
                cpviosimgCmd += self.OPT['CPVIOSIMG']['-D'] + remote_directory
            if sftp_password:
                cpviosimgCmd += self.OPT['CPVIOSIMG']['--PASSWD'] + sftp_password
            elif ssh_key_file:
                cpviosimgCmd += self.OPT['CPVIOSIMG']['-K'] + ssh_key_file
        elif media == 'nfs':
            cpviosimgCmd = self.CMD['CPVIOSIMG'] +\
                self.OPT['CPVIOSIMG']['-R']['NFS'] +\
                self.OPT['CPVIOSIMG']['-N'] + directory_name +\
                self.OPT['CPVIOSIMG']['-H'] + remote_server +\
                self.OPT['CPVIOSIMG']['-L'] + mount_location +\
                self.OPT['CPVIOSIMG']['-F'] + files
            if remote_directory:
                cpviosimgCmd += self.OPT['CPVIOSIMG']['-D'] + remote_directory
            if options:
                cpviosimgCmd += self.OPT['CPVIOSIMG']['--OPTIONS'] + options

        self.hmcconn.execute(cpviosimgCmd)

    def listViosImages(self, directory_name=None):
        if directory_name:
            lsviosimgCmd = self.CMD['LSVIOSIMG'] +\
                '| grep -w ' + directory_name +\
                ' || echo No results were found'
        else:
            lsviosimgCmd = self.CMD['LSVIOSIMG']
        output = self.hmcconn.execute(lsviosimgCmd)
        if 'No results' in output:
            return None
        return self.cmdClass.parseMultiLineCSV(output)

    def deleteViosImage(self, directory_list):
        changed = False
        for directory in directory_list:
            rmviosimgCmd = self.CMD['RMVIOSIMG'] +\
                self.OPT['RMVIOSIMG']['-N'] + directory
            try:
                self.hmcconn.execute(rmviosimgCmd)
                changed = True
            except HmcError as list_error:
                if 'HSCLC464' in repr(list_error):
                    continue
                else:
                    raise Exception(f"Error deleting VIOS image: {repr(list_error)}") from list_error
            except Exception as e:
                raise Exception(f"Unexpected error occurred while deleting VIOS image: {repr(e)}") from e
        return changed

    def getviosversion(self, configDict=None):
        vios_version = ''
        vios_version += self.CMD['VIOSVRCMD'] + self.OPT['VIOSVRCMD']['-M'] + configDict['system_name'] + \
            self.OPT['VIOSVRCMD']['-C'] + 'ioslevel'
        if configDict['vios_name'] is not None:
            vios_version += self.OPT['VIOSVRCMD']['-P'] + configDict['vios_name']
        elif configDict['vios_id'] is not None:
            vios_version += self.OPT['VIOSVRCMD']['--ID'] + configDict['vios_id']
        return self.hmcconn.execute(vios_version)

    def updatevios(self, state, configDict=None):
        updviosbk_cmd = ''
        if state == 'updated':
            updviosbk_cmd += self.CMD['UPDVIOS']
        elif state == 'upgraded':
            updviosbk_cmd += self.CMD['UPGVIOS']
        updviosbk_cmd += self.OPT['UPDVIOS']['-R'] + configDict['repository'] + \
            self.OPT['UPDVIOS']['-M'] + configDict['system_name']
        option_map = {'vios_name': '-P', 'vios_id': '--ID', 'image_name': '-N', 'files': '-F',
                      'host_name': '-H', 'user_id': '-U', 'password': '--PASSWD', 'ssh_key_file': '-K',
                      'directory': '-D', 'mount_loc': '-L', 'option': '--OPTIONS'}
        for key in option_map:
            if configDict[key] is not None:
                updviosbk_cmd += self.OPT['UPDVIOS'][option_map[key]] + configDict[key]
        if configDict['restart'] is not None:
            updviosbk_cmd += self.OPT['UPDVIOS']['--RESTART']
        if configDict['save'] is not None:
            updviosbk_cmd += self.OPT['UPDVIOS']['--SAVE']
        if state == 'upgraded':
            updviosbk_cmd += self.OPT['UPDVIOS']['--DISK'] + str(configDict['disks'])
        return self.hmcconn.execute(updviosbk_cmd)

    def create_svc_events(self, params):
        svc_ticket_cmd = ''
        svc_ticket_cmd += (
            self.CMD['MKSVCEVENT']
            + self.OPT['MKSVCEVENT']['-D']
            + str(params['description'])
            + self.OPT['MKSVCEVENT']['-T']
            + str(params['types'])
        )
        if params['system_name'] is not None:
            svc_ticket_cmd += self.OPT['MKSVCEVENT']['-M'] + str(params['system_name'])

        attributes = params['attributes']
        if attributes is None:
            return self.hmcconn.execute(svc_ticket_cmd)

        if attributes['service_file'] is not None:
            csv_string = ",".join(attributes['service_file'])
            csv_string += '\\"'
            attributes['service_file'] = csv_string
        option_map = {'title': '-TITLE', 'severity': '-SEVERITY', 'contact_name': '-NAME', 'service_file': '-SERVICE_FILE',
                      'contact_phone': '-PHONE', 'contact_email': '-EMAIL', 'target_lpar_name': '-TARGET_LPAR_NAME', 'target_mtms': '-TARGET_MTMS',
                      'lpar_name': '-LPAR_NAME', 'hostname': '-HOSTNAME', 'user': '-USER', 'password': '-PASSWORD'}
        svc_ticket_cmd += self.OPT['MKSVCEVENT']['-A']
        for key in option_map:
            if attributes[key] is not None:
                svc_ticket_cmd += self.OPT['MKSVCEVENT'][option_map[key]] + str(attributes[key])
        svc_ticket_cmd += ",is_callhome=1"
        return self.hmcconn.execute(svc_ticket_cmd)

    def list_svc_events(self, params):
        svc_events_cmd = self.CMD['LSSVCEVENTS'] + self.OPT['LSSVCEVENTS']['-T'] + str(params['event_type'])
        if params['system_name'] is not None:
            svc_events_cmd += self.OPT['LSSVCEVENTS']['-M'] + str(params['system_name'])
        if params['days'] is not None:
            svc_events_cmd += self.OPT['LSSVCEVENTS']['-D'] + str(params['days'])
        if params['minutes'] is not None:
            svc_events_cmd += self.OPT['LSSVCEVENTS']['-I'] + str(params['minutes'])
        if params['number_of_events'] is not None:
            svc_events_cmd += self.OPT['LSSVCEVENTS']['-N'] + str(params['number_of_events'])
        if params['display_attributes'] is not None:
            svc_events_cmd += self.OPT['LSSVCEVENTS']['-F'] + ','.join(params['display_attributes'])
        return self.hmcconn.execute(svc_events_cmd)

    def create_viosecure_command(self, params, fields):
        option_map = {'port': '-PORT', 'interface': '-INTERFACE', 'remote': '-REMOTE', 'address': '-ADDRESS', 'timeout': '-TIMEOUT'}
        viosecure_cmd = 'viosecure'
        if params['level'] is not None:
            viosecure_cmd += self.OPT['VIOSECURE']['-LEVEL'] + str(params['level']) + self.OPT['VIOSECURE']['-APPLY']
            if params['rule'] is not None:
                viosecure_cmd += self.OPT['VIOSECURE']['-RULE'] + str(params['rule'])
        elif params['file'] is not None:
            viosecure_cmd += self.OPT['VIOSECURE']['-FILE'] + str(params['file'])
        elif params['firewall'] is True:
            viosecure_cmd += self.OPT['VIOSECURE']['-FIREWALL'] + str(fields['present'].lower())
            for key in option_map:
                if fields[key] is not None and key != 'remote':
                    viosecure_cmd += self.OPT['VIOSECURE'][option_map[key]] + str(fields[key])
                elif key == 'remote' and fields[key] is not None:
                    if str(fields[key]).lower() == 'true':
                        viosecure_cmd += self.OPT['VIOSECURE'][option_map[key]]
            if str(params['ip_version']).lower() == 'ipv6':
                viosecure_cmd += self.OPT['VIOSECURE']['-IPV6']
        return viosecure_cmd

    def update_lpar(self, cecName, lparConfig):
        chsyscfgCmd = self.CMD['CHSYSCFG'] + \
            self.OPT['CHSYSCFG']['-R']['LPAR'] + \
            self.OPT['CHSYSCFG']['-M'] + cecName
        chsyscfgCmd += self.cmdClass.i_a_ConfigBuilder('CHSYSCFG', '-I', lparConfig)
        self.hmcconn.execute(chsyscfgCmd)

    def get_mappings(self, params):
        cmd = self.CMD['LSMAP']
        component = params['component']
        component_options = {
            'npiv': '-NPIV',
            'net': '-NET',
            'vnic': '-VNIC',
            'ams': '-AMS',
            'suspend': '-SUSPEND'
        }
        if component in component_options:
            cmd += self.OPT['LSMAP'][component_options[component]]
        if component == 'ams':
            if params.get('vtd') is not None:
                cmd += self.OPT['LSMAP']['-VTD'] + params['vtd']
            else:
                cmd += self.OPT['LSMAP']['-ALL']
        elif component == 'suspend':
            if params.get('vadapter') is not None:
                cmd += self.OPT['LSMAP']['-VADAPTER'] + params['vadapter']
            else:
                cmd += self.OPT['LSMAP']['-ALL']
        else:
            if params.get('vadapter') is not None:
                cmd += self.OPT['LSMAP']['-VADAPTER'] + params['vadapter']
            elif params.get('physloc') is not None:
                cmd += self.OPT['LSMAP']['-PLC'] + params['physloc']
            else:
                cmd += self.OPT['LSMAP']['-ALL']
        if component in ['vscsi', 'npiv', 'vnic'] and params.get('cpid') is not None:
            cmd += self.OPT['LSMAP']['-CPID'] + str(params['cpid'])
        if component in ['vscsi', 'ams', 'suspend'] and params.get('types') is not None:
            cmd += self.OPT['LSMAP']['-TYPE'] + ' '.join(params['types'])
        cmd += ' -fmt' + ' , '
        return cmd

    def get_cluster_mappings(self, params):
        cmd = self.CMD['LSMAP'] + self.OPT['LSMAP']['-CLUSTERNAME']
        if params.get('hostname') is not None:
            cmd += self.OPT['LSMAP']['-HOSTNAME'] + params['physloc']
        else:
            cmd += self.OPT['LSMAP']['-ALL']
        cmd += ' -fmt' + ' , '
