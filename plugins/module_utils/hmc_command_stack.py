# !/usr/bin/python
#     @author  Anil Vijayan
#
#  @par Class description:
#  This class contains related HMC command constants
#
#  @param None
# #

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class HmcCommandStack():

    #  hmc commands
    HMC_CMD = {'LSHMC': 'lshmc',
               'CHHMC': 'chhmc',
               'HMCSHUTDOWN': 'hmcshutdown',
               'GETUPGFILES': 'getupgfiles',
               'UPDHMC': 'updhmc',
               'SAVEUPGDATA': 'saveupgdata',
               'LSPWDPOLICY': 'lspwdpolicy',
               'CHPWDPOLICY': 'chpwdpolicy',
               'RMPWDPOLICY': 'rmpwdpolicy',
               'MKPWDPOLICY': 'mkpwdpolicy',
               'LSSYSCFG': 'lssyscfg',
               'RMSYSCFG': 'rmsyscfg',
               'MKSYSCFG': 'mksyscfg',
               'CHSYSCFG': 'chsyscfg',
               'CHSYSSTATE': 'chsysstate',
               'CHHWRES': 'chhwres',
               'LSHWRES': 'lshwres',
               'MIGRLPAR': 'migrlpar',
               'LPAR_NETBOOT': 'lpar_netboot',
               'LSREFCODE': 'lsrefcode',
               'VIOSVRCMD': 'viosvrcmd'}

    HMC_CMD_OPT = {'LSHMC': {'-N': ' -n ',
                             '-v': ' -v ',
                             '-V': ' -V ',
                             '-B': ' -b ',
                             '-l': ' -l ',
                             '-L': ' -L ',
                             '-H': ' -h ',
                             '-I': ' -i ',
                             '-E': ' -e ',
                             '-R': ' -r ',
                             '--NETROUTE': ' --netroute ',
                             '--FIREWALL': ' --firewall ',
                             '-F': {'POSITION': ' -F position ', 'DESTINATION': ' -F destination ',
                                    'GATEWAY': ' -F gateway ', 'NETWORKMASK': ' -F networkmask ',
                                    'INTERFACE': ' -F interface ', 'XNTP': ' -F xntp ',
                                    'XNTPSERVER': ' -F  xntpserver ', 'XNTPSTATUS': ' -F xntpstatus '},
                             '--HELP': ' --help ',
                             '--SYSLOG': ' --syslog ',
                             '--NTPSERVER': ' --ntpserver '},
                   'CHHMC': {'-C': {'NETROUTE': ' -c netroute ', 'SSH': ' -c ssh ',
                                    'XNTP': ' -c xntp ', 'SYSLOG': ' -c syslog ',
                                    'NETWORK': ' -c network ', 'DATE': ' -c date ',
                                    'KERBEROS': ' -c kerberos ', 'ALTDISKBOOT': ' -c altdiskboot '},
                             '-NM': ' -nm ',
                             '-S': {'ADD': ' -s add ', 'REMOVE': ' -s remove ',
                                    'MODIFY': ' -s modify ',
                                    'ENABLE': ' -s enable ', 'DISABLE': ' -s disable '},
                             '--ROUTETYPE': {'HOST': ' --routetype host ', 'NET': ' --routetype net '},
                             '-G': ' -g ',
                             '-A': ' -a ',
                             '-I': ' -i ',
                             '-D': ' -d ',
                             '-T': {'TCP': ' -t tcp ',
                                    'TLS': ' -t tls ',
                                    'UDP': ' -t udp '},
                             '--POSITION': ' --position ',
                             '-DS': ' -ds ',
                             '--HELP': ' --help ',
                             '-H': ' -h ',
                             '--REALM': ' --realm ',
                             '--DEFAULTREALM': ' --defaultrealm ',
                             '--CLOCKSKEW': ' --clockskew ',
                             '--TICKETLIFETIME': ' --ticketlifetime ',
                             '--KPASSWDADMIN': ' --kpasswdadmin ',
                             '--TRACE': ' --trace ',
                             '--WEAKCRYPTO': ' --weakcrypto ',
                             '--FORCE': ' --force ',
                             '--MODE': {'INSTALL': ' --mode install ',
                                        'UPGRADE': ' --mode upgrade '},
                             '--IPV6AUTO': {'ON': ' --ipv6auto on ',
                                            'OFF': ' --ipv6auto off '},
                             '--IPV6PRIVACY': {'ON': ' --ipv6privacy on ',
                                               'OFF': ' --ipv6privacy off '},
                             '--IPV6DHCP': {'ON': ' --ipv6dhcp on ',
                                            'OFF': ' --ipv6dhcp off '},
                             '--IPV4DHCP': {'ON': ' --ipv4dhcp on ',
                                            'OFF': ' --ipv4dhcp off '},
                             '--LPARCOMM': {'ON': ' --lparcomm on ',
                                            'OFF': ' --lparcomm off '},
                             '--TSO': {'ON': ' --tso on ',
                                       'OFF': ' --tso off '},
                             '--SPEED': {'AUTO': ' --speed auto ',
                                         '10': ' --speed 10 ',
                                         '100': ' --speed 100 ',
                                         '1000': ' --speed 1000 '}},
                   'HMCSHUTDOWN': {'-T': ' -t ', '-R': ' -r '},
                   'GETUPGFILES': {'-R': {'FTP': ' -r ftp ',
                                          'SFTP': ' -r sftp ',
                                          'NFS': ' -r nfs ',
                                          'DISK': ' -r disk '},
                                   '-H': ' -h ',
                                   '-D': ' -d ',
                                   '-U': ' -u ',
                                   '--PASSWD': ' --passwd ',
                                   '-K': ' -k ',
                                   '-L': ' -l ',
                                   '-O': ' -o '},
                   'UPDHMC': {'-T': {'DISK': ' -t disk ',
                                     'DVD': ' -t dvd ',
                                     'FTP': ' -t ftp ',
                                     'SFTP': ' -t sftp ',
                                     'NFS': ' -t nfs ',
                                     'USB': ' -t usb '},
                              '-F': ' -f ',
                              '-R': ' -r ',
                              '-C': ' -c ',
                              '-N': ' -n ',
                              '-H': ' -h ',
                              '-D': ' -d ',
                              '-U': ' -u ',
                              '--PASSWD': ' --passwd ',
                              '-K': ' -k ',
                              '-L': ' -l ',
                              '-O': ' -o '},
                   'SAVEUPGDATA': {'-R': {'DISK': ' -r disk ', 'DISKUSB': ' -r diskusb ', 'DISKFTP': ' -r diskftp ', 'DISKSFTP': ' -r disksftp '},
                                   '-H': ' -h ',
                                   '-U': ' -u ',
                                   '-K': ' -k ',
                                   '-D': ' -d ',
                                   '-I': ' -i ',
                                   '--PASSWD': ' --passwd ',
                                   '--MIGRATE': ' --migrate ',
                                   '--FORCE': ' --force '},
                   'LSPWDPOLICY': {'-T': {'P': ' -t p ', 'S': ' -t s '}},
                   'MKPWDPOLICY': {'-I': {'NAME': 'name', 'DESCRIPTION': 'description', 'MIN_PWAGE': 'min_pwage', 'PWAGE': 'pwage',
                                          'WARN_PWAGE': 'warn_pwage', 'MIN_LENGTH': 'min_length', 'HIST_SIZE': 'hist_size', 'MIN_DIGITS': 'min_digits',
                                          'MIN_UPPERCASE_CHARS': 'min_uppercase_chars', 'MIN_LOWERCASE_CHARS': 'min_lowercase_chars',
                                          'MIN_SPECIAL_CHARS': 'min_special_chars'}},
                   'CHPWDPOLICY': {'-O': {'A': ' -o a ', 'D': ' -o d ', 'M': ' -o m '},
                                   '-N': ' -n ',
                                   '-I': {'NAME': 'name', 'DESCRIPTION': 'description', 'MIN_PWAGE': 'min_pwage', 'PWAGE': 'pwage',
                                          'WARN_PWAGE': 'warn_pwage', 'MIN_LENGTH': 'min_length', 'HIST_SIZE': 'hist_size', 'MIN_DIGITS': 'min_digits',
                                          'MIN_UPPERCASE_CHARS': 'min_uppercase_chars', 'MIN_LOWERCASE_CHARS': 'min_lowercase_chars',
                                          'MIN_SPECIAL_CHARS': 'min_special_chars', 'NEW_NAME': 'new_name'}
                                   },
                   'RMPWDPOLICY': {'-N': ' -n '},
                   'LSSYSCFG': {'-R': {'LPAR': ' -r lpar', 'SYS': ' -r sys', 'PROF': ' -r prof', 'SYSPROF': ' -r sysprof'},
                                '-M': ' -m ',
                                '-F': ' -F ',
                                '--FILTER': {'LPAR_NAMES': 'lpar_names', 'LPAR_IDS': 'lpar_ids', 'WORK_GROUPS': 'work_groups',
                                             'PROFILE_NAMES': 'profile_names'}},
                   'LSHWRES': {'-R': ' -r ',
                               '-M': ' -m ',
                               '--LEVEL': ' --level ',
                               '-F': ' -F '},
                   'RMSYSCFG': {'-R': {'LPAR': ' -r lpar'},
                                '-M': ' -m ',
                                '-N': ' -n ',
                                '--ID': ' --id ',
                                'VIOSCFG': ' --vioscfg',
                                'VDISKS': ' --vdisk'},
                   'MKSYSCFG': {'-R': {'LPAR': ' -r lpar', 'PROF': ' -r prof', 'SYSPROF': ' -r sysprof'},
                                '-M': ' -m ',
                                '--ID': ' --id ',
                                '-I': {'NAME': 'name', 'PROFILE_NAME': 'profile_name', 'LPAR_ENV': 'lpar_env',
                                       'MIN_MEM': 'min_mem', 'DESIRED_MEM': 'desired_mem', 'MAX_MEM': 'max_mem',
                                       'MIN_PROCS': 'min_procs', 'MAX_PROCS': 'max_procs',
                                       'MIN_PROC_UNITS': 'min_proc_units', 'DESIRED_PROC_UNITS': 'desired_proc_units',
                                       'MAX_PROC_UNITS': 'max_proc_units',
                                       'DESIRED_PROCS': 'desired_procs', 'BOOT_MODE': 'boot_mode',
                                       'SHARING_MODE': 'sharing_mode', 'PROC_MODE': 'proc_mode',
                                       'MAX_VIRTUAL_SLOTS': 'max_virtual_slots',
                                       'VIRTUAL_SCSI_ADAPTERS': 'virtual_scsi_adapters', 'VIRTUAL_ETH_ADAPTERS': 'virtual_eth_adapters',
                                       'CONSOLE_SLOT': 'console_slot', 'LPAR_NAME': 'lpar_name', 'ALL_RESOURCES': 'all_resources',
                                       'LPAR_NAMES': 'lpar_names',
                                       'LPAR_IDS': 'lpar_ids', 'PROFILE_NAMES': 'profile_names',
                                       'HPT_RATIO': 'hpt_ratio', 'VTPM_ENABLED': 'vtpm_enabled',
                                       'REMOTE_RESTART_CAPABLE': 'remote_restart_capable',
                                       'MEM_EXPANSION': 'mem_expansion', 'SUSPEND_CAPABLE': 'suspend_capable',
                                       'OS400_RESTRICTED_IO_MODE': 'os400_restricted_io_mode', 'SHARED_PROC_POOL_ID': 'shared_proc_pool_id',
                                       'SIMPLIFIED_REMOTE_RESTART_CAPABLE': 'simplified_remote_restart_capable',
                                       'MEM_MODE': 'mem_mode', 'ALT_RESTART_DEVICE_SLOT': 'alt_restart_device_slot',
                                       'LPAR_PROC_COMPAT_MODE': 'lpar_proc_compat_mode', 'PPT_RATIO': 'ppt_ratio', 'SECURE_BOOT': 'secure_boot',
                                       'LPAR_ID': 'lpar_id', 'UNCAP_WEIGHT': 'uncap_weight',
                                       'TIME_REF': 'time_ref', 'PRIMARY_RS_VIOS_ID': 'primary_rs_vios_id',
                                       'PRIMARY_RS_VIOS_NAME': 'primary_rs_vios_name', 'SECONDARY_RS_VIOS_NAME': 'secondary_rs_vios_name',
                                       'SECONDARY_RS_VIOS_ID': 'secondary_rs_vios_id', 'ALLOW_PERF_COLLECTION': 'allow_perf_collection',
                                       'HARDWARE_MEM_EXPANSION': 'hardware_mem_expansion', 'HARDWARE_MEM_ENCRYPTION': 'hardware_mem_encryption',
                                       'SYNC_CURR_PROFILE': 'sync_curr_profile', 'LPAR_AVAIL_PRIORITY': 'lpar_avail_priority',
                                       'MIGRATION_DISABLED': 'migration_disabled', 'RS_DEVICE_NAME': 'rs_device_name', 'MSP': 'msp',
                                       'MIN_NUM_HUGE_PAGES': 'min_num_huge_pages', 'DESIRED_NUM_HUGE_PAGES': 'desired_num_huge_pages',
                                       'MAX_NUM_HUGE_PAGES': 'max_num_huge_pages', 'DESIRED_IO_ENTITLED_MEM': 'desired_io_entitled_mem',
                                       'PRIMARY_PAGING_VIOS_NAME': 'primary_paging_vios_name', 'PRIMARY_PAGING_VIOS_ID': 'primary_paging_vios_id',
                                       'SECONDARY_PAGING_VIOS_NAME': 'secondary_paging_vios_name', 'SECONDARY_PAGING_VIOS_ID': 'secondary_paging_vios_id',
                                       'BSR_ARRAYS': 'bsr_arrays', 'MEM_WEIGHT': 'mem_weight', 'AFFINITY_GROUP_ID': 'affinity_group_id',
                                       'IO_SLOTS': 'io_slots', 'AUTO_START': 'auto_start', 'POWER_CTRL_LPAR_IDS': 'power_ctrl_lpar_ids',
                                       'POWER_CTRL_LPAR_NAMES': 'power_ctrl_lpar_names', 'CONN_MONITORING': 'conn_monitoring',
                                       'LPAR_IO_POOL_IDS': 'lpar_io_pool_ids', 'VIRTUAL_ETH_VSI_PROFILES': 'virtual_eth_vsi_profiles',
                                       'VIRTUAL_FC_ADAPTERS': 'virtual_fc_adapters', 'VIRTUAL_SERIAL_ADAPTERS': 'virtual_serial_adapters',
                                       'VIRTUAL_OPTI_POOL_ID': 'virtual_opti_pool_id', 'HSL_POOL_ID': 'hsl_pool_id', 'ALT_CONSOLE_SLOT': 'alt_console_slot',
                                       'OP_CONSOLE_SLOT': 'op_console_slot', 'LOAD_SOURCE_SLOT': 'load_source_slot',
                                       'KEYSTORE_KBYTES': 'keystore_kbytes', 'SRIOV_ROCE_LOGICAL_PORTS': 'sriov_roce_logical_ports',
                                       'POWERVM_MGMT_CAPABLE': 'powervm_mgmt_capable', 'SRIOV_ETH_LOGICAL_PORTS': 'sriov_eth_logical_ports',
                                       'REDUNDANT_ERR_PATH_REPORTING': 'redundant_err_path_reporting', 'WORK_GROUP_ID': 'work_group_id',
                                       'VIRTUAL_SERIAL_NUM': 'virtual_serial_num', 'SHARED_PROC_POOL_NAME': 'shared_proc_pool_name',
                                       'VTPM_VERSION': 'vtpm_version',
                                       'VTPM_ENCRYPTION': 'vtpm_encryption'},
                                '-P': ' -p ',
                                '-N': ' -n ',
                                '-O': {'SAVE': ' -o save'},
                                '--FORCE': ' --force '},
                   'CHSYSCFG': {'-R': {'LPAR': ' -r lpar', 'PROF': ' -r prof', 'SYSPROF': ' -r sysprof', 'SYS': ' -r sys'},
                                '-M': ' -m ',
                                '-N': ' -n ',
                                '-P': ' -p ',
                                '-O': {'APPLY': ' -o apply'},
                                '--FORCE': ' --force ',
                                '-I': {'NAME': 'name', 'PROFILE_NAME': 'profile_name', 'LPAR_ENV': 'lpar_env',
                                       'MIN_MEM': 'min_mem', 'DESIRED_MEM': 'desired_mem', 'MAX_MEM': 'max_mem',
                                       'MIN_PROCS': 'min_procs', 'MAX_PROCS': 'max_procs',
                                       'MIN_PROC_UNITS': 'min_proc_units', 'DESIRED_PROC_UNITS': 'desired_proc_units',
                                       'MAX_PROC_UNITS': 'max_proc_units',
                                       'DESIRED_PROCS': 'desired_procs', 'BOOT_MODE': 'boot_mode',
                                       'SHARING_MODE': 'sharing_mode', 'PROC_MODE': 'proc_mode',
                                       'LPAR_NAME': 'lpar_name',
                                       'VIRTUAL_SCSI_ADAPTERS': 'virtual_scsi_adapters',
                                       'VIRTUAL_ETH_ADAPTERS': 'virtual_eth_adapters',
                                       'VIRTUAL_FC_ADAPTERS': 'virtual_fc_adapters',
                                       'MAX_VIRTUAL_SLOTS': 'max_virtual_slots', 'LPAR_NAMES': 'lpar_names',
                                       'AUTO_PRIORITY_FAILOVER': 'auto_priority_failover', 'PROFILE_NAMES': 'profile_names',
                                       'VTPM_ENABLED': 'vtpm_enabled', 'VTPM_STATE': 'vtpm_state',
                                       'LPAR_PROC_COMPAT_MODE': 'lpar_proc_compat_mode', 'HPT_RATIO': 'hpt_ratio',
                                       'SUSPEND_CAPABLE': 'suspend_capable',
                                       'REMOTE_RESTART_CAPABLE': 'remote_restart_capable',
                                       'SIMPLIFIED_REMOTE_RESTART_CAPABLE': 'simplified_remote_restart_capable',
                                       'SYNC_CURR_PROFILE': 'sync_curr_profile',
                                       'PPT_RATIO': 'ppt_ratio', 'CONSOLE_SLOT': 'console_slot', 'SECURE_BOOT': 'secure_boot',
                                       'KEYSTORE_KBYTES': 'keystore_kbytes',
                                       'LOAD_SOURCE_SLOT': 'load_source_slot', 'ALT_RESTART_DEVICE_SLOT': 'alt_restart_device_slot',
                                       'IPL_SOURCE': 'ipl_source', 'VIRTUAL_SERIAL_NUM': 'virtual_serial_num',
                                       'VTPM_VERSION': 'vtpm_version',
                                       'VTPM_ENCRYPTION': 'vtpm_encryption', 'NEW_NAME': 'new_name',
                                       'POWER_OFF_POLICY': 'power_off_policy', 'POWER_ON_LPAR_START_POLICY': 'power_on_lpar_start_policy'}
                                },
                   'CHSYSSTATE': {'-R': {'LPAR': ' -r lpar', 'SYS': ' -r sys', 'SYSPROF': ' -r sysprof'},
                                  '-M': ' -m ',
                                  '-O': {'ON': ' -o on ', 'ONSTANDBY': ' -o onstandby ', 'ONSTARTPOLICY': ' -o onstartpolicy ',
                                         'ONSYSPROF': ' -o onsysprof ', 'ONHWDISK': ' -o onhwdisc ', 'OFF': ' -o off ',
                                         'REBUILD': ' -o rebuild ', 'RECOVER': ' -o recover ', 'SPFAILOVER': ' -o spfailover ',
                                         'CHKEY': ' -o chkey ', 'SHUTDOWN': ' -o shutdown ', 'OSSHUTDOWN': ' -o osshutdown ',
                                         'DUMPRESTART': ' -o dumprestart ', 'RETRYDUMP': ' -o retrydump ', 'DSTON': ' -o dston ',
                                         'REMOTEDSTOFF': ' -o remotedstoff ', 'REMOTEDSTON': ' -o remotedston ',
                                         'CONSOLESERVICE': ' -o consoleservice ', 'IOPRESET': ' -o iopreset ', 'IOPDUMP': ' -o iopdump ',
                                         'UNOWNEDIOOFF': ' -o unownediooff '},
                                  '-F': ' -f ',
                                  '-K': {'MANUAL': ' -k manual ', 'NORM': ' -k norm '},
                                  '-B': {'NORM': ' -b norm ', 'DIAG_DEFAULT': ' -b dd ', 'DIAG_STORED': ' -b ds ', 'OK': ' -b of ', 'SMS': ' -b sms '},
                                  '--IMMED': ' --immed ',
                                  '-I': {'A': ' -i a ', 'B': ' -i b ', 'C': ' -i c ', 'D': ' -i d '},
                                  '--RESTART': ' --restart ',
                                  '-N': ' -n ',
                                  '--ID': ' --id ',
                                  '--IP': ' --ip ',
                                  '--GATEWAY': ' --gateway ',
                                  '--SERVERIP': ' --serverip ',
                                  '--SERVERDIR': ' --serverdir ',
                                  '--SPEED': {'AUTO': ' --speed auto ', '1': ' --speed 1 ', '10': ' --speed 10 ', '100': ' --speed 100 ',
                                              '1000': ' --speed 1000 '},
                                  '--DUPLEX': {'AUTO': ' --duplex auto ', 'HALF': ' --duplex half ', 'FULL': ' --duplex full '},
                                  '--MTU': {'1500': ' --mtu 1500 ', '9000': ' --mtu 9000'},
                                  '--VLAN': ' --vlan '
                                  },
                   'CHHWRES': {'-R': {'MEM': ' -r mem '},
                               '-M': ' -m ',
                               '-O': {'S': ' -o s '},
                               '-A': {'REQUESTED_NUM_SYS_HUGE_PAGES': 'requested_num_sys_huge_pages',
                                      'PEND_MEM_REGION_SIZE': 'pend_mem_region_size', 'MEM_MIRRORING_MODE': 'mem_mirroring_mode'},
                               },
                   'MIGRLPAR': {'-O': {'V': ' -o v', 'M': ' -o m', 'R': ' -o r'},
                                '-M': ' -m ',
                                '-T': ' -t ',
                                '-P': ' -p ',
                                '--IP': ' --ip ',
                                '--ALL': ' --all',
                                '--ID': ' --id '},
                   'LPAR_NETBOOT': {'-A': ' -A',
                                    '-M': ' -M',
                                    '-D': ' -D',
                                    '-N': ' -n',
                                    '-T': ' -t ',
                                    '-S': ' -S ',
                                    '-G': ' -G ',
                                    '-C': ' -C ',
                                    '-F': ' -f',
                                    '-L': ' -l ',
                                    '-V': ' -V ',
                                    '-Y': ' -Y ',
                                    '-K': ' -K '},
                   'LSREFCODE': {'-R': {'LPAR': ' -r lpar'},
                                 '-M': ' -m ',
                                 '-F': ' -F ',
                                 '--FILTER': {'LPAR_NAMES': 'lpar_names'}},
                   'VIOSVRCMD': {'-M': ' -m ',
                                 '-P': ' -p ',
                                 '-C': ' -c '},
                   }

    def filterBuilder(self, cmdKey, configOptionsDict):
        configStr = " --filter "
        configStr += '"'
        ATTRIBUTE = self.HMC_CMD_OPT[cmdKey]['--FILTER']

        for key in configOptionsDict.keys():
            if ',' in configOptionsDict[key]:
                configStr += '"'
                configStr += ATTRIBUTE[key] + '=' + configOptionsDict[key]
                configStr += '"'
            else:
                configStr += ATTRIBUTE[key] + '=' + configOptionsDict[key]
            configStr += ','

        configStr = configStr.rstrip(',')
        configStr += '"'
        return configStr

    def configBuilder(self, cmdKey, configOptionsDict):
        cmdStr = ''
        ATTRIBUTE = self.HMC_CMD_OPT[cmdKey]
        for eachKey in configOptionsDict:
            if '--FILTER' in eachKey:
                cmdStr += self.filterBuilder(cmdKey, configOptionsDict['--FILTER'])
            elif isinstance(ATTRIBUTE[eachKey], dict):
                cmdStr += ATTRIBUTE[eachKey][configOptionsDict[eachKey].upper()]
            elif isinstance(configOptionsDict[eachKey], list):
                subData = r''
                for eachData in configOptionsDict[eachKey]:
                    subData += r'\"' + eachData + r'\",'
                subData = subData.rstrip(',')
                cmdStr += ATTRIBUTE[eachKey] + " " + subData
            else:
                cmdStr += ATTRIBUTE[eachKey] + " " + configOptionsDict[eachKey]
        return cmdStr

    def parseColonSV(self, colonSVData):
        innerDict = {}
        for each in colonSVData.split(': '):
            each = each.strip('""')
            keyvalue = each.split('=')
            innerDict.update({keyvalue[0].upper(): keyvalue[1]})
        return innerDict

    def parseCSV(self, csvData, userConfig=None):
        if userConfig and '-F' in userConfig:
            return self.parseAttributes(userConfig['-F'], csvData)

        dict = {}
        key_bkup = ""
        value_bkup = ""
        valueHasColonDelim = False
        caseLshmccert = False
        csvList = csvData.split(',')
        csvIter = iter(csvList)
        next(csvIter)
        prevdata = ""
        for each in csvList:
            if csvIter.__length_hint__():
                nextdata = next(csvIter)
            else:
                nextdata = ""
            try:
                if valueHasColonDelim:
                    if '=' not in each:
                        value_bkup += ',' + each
                        continue
                    if ': ' in each and '=' not in each.split(': ')[0]:
                        value_bkup += ',' + each
                        if nextdata == "":
                            dict[key_bkup].append(self.parseColonSV(value_bkup))
                        continue
                    # To handle colon seperated data which starts with double quote
                    if ': ' in each and '""' in each[0: 2]:
                        if value_bkup:
                            dict[key_bkup].append(self.parseColonSV(value_bkup))

                        value_bkup = each.strip('""')
                        continue
                    # To handle simple colon seperated data
                    if ': ' in each:
                        if value_bkup:
                            dict[key_bkup].append(self.parseColonSV(value_bkup))

                        value_bkup = ""
                        # Identifying the end of colon data
                        if ': ' not in nextdata and '=' in nextdata:
                            dict[key_bkup].append(self.parseColonSV(each))
                            valueHasColonDelim = False
                            continue
                    # To confirm that the colon data finised, here handling
                    #  the next non colon data as well and going out of colon
                    #  parsing
                    else:
                        if value_bkup:
                            dict[key_bkup].append(self.parseColonSV(value_bkup))

                        key, value = each.split('=')
                        key = key.strip('"').strip('\r\n')
                        value = value.strip('\r\n')
                        dict.update({key.upper(): value})
                        valueHasColonDelim = False
                else:
                    if caseLshmccert:
                        key = key_bkup
                        value = dict[key_bkup] + ',' + each.strip('"')
                        if '"' in each[-1]:
                            caseLshmccert = False
                    elif '<' in each and ('>' in each or '>' in nextdata[-4]):
                        t = each.split('=')
                        if t[0][0] != '<':
                            key = t.pop(0)
                            value = '='.join(t)
                            value = value.strip('"')
                        else:
                            key = dict.keys()[0]
                            value = dict[key] + ',' + '='.join(t)
                    elif '<' in prevdata and '>' in each[-4]:
                        key = key_bkup
                        value = dict[key_bkup] + ',' + each.strip('"')
                    elif '"' in each[0]:
                        t = each.split('=')
                        if len(t) == 3:
                            key = t[0].strip('"')
                            value = t[1] + '=' + t[2]
                            caseLshmccert = True
                        else:
                            key, value = each.split('=')
                    else:
                        key, value = each.split('=')
                    key = key.strip('"').strip('\r\n')
                    value = value.strip('\r\n')
                    dict.update({key.upper(): value})

            except ValueError as errMsg:
                if "too many values to unpack" in repr(errMsg):
                    if ': ' in each:
                        temp = each.split('=')
                        valueHasColonDelim = True
                        key = temp[0].strip('"')
                        dict.update({key.upper(): []})
                        value = each.lstrip('"')
                        value = value.strip(key)
                        value = value.strip('=')
                        # if the next data is empty, then handle the parsing of
                        # colon data here itself
                        if nextdata == "":
                            dict[key.upper()].append(self.parseColonSV(value))
                else:
                    value = each.strip('"').strip('\r\n')
                    value = value_bkup + ',' + value.strip('\r\n')
                    dict.pop(key_bkup)
                    dict.update({key_bkup: value})
            key_bkup, value_bkup = key.upper(), value
            prevdata = each

        return dict

    def parseMultiLineCSV(self, csvData, userConfig=None):
        eachDict = {}
        listOfDict = []

        lines = csvData.split('\n')
        for line in lines:
            if not line:  # to remove empty lines
                continue
            eachDict = self.parseCSV(line, userConfig)
            listOfDict.append(eachDict)
        return listOfDict

    def parseAttributes(self, i_csvAttrStr, i_csvValueStr):
        l_attrs = i_csvAttrStr.split(',')
        l_values = i_csvValueStr.strip().split(',')
        if ',"' in i_csvValueStr or '"' in i_csvValueStr:
            csvValueList = []
            finalList = []
            startComma = False
            for each in l_values:
                if startComma and '"' in each[-1]:
                    csvValueList.append(each.strip('"'))
                    startComma = False
                    finalList.append(','.join(csvValueList))
                    csvValueList = []
                elif '"' in each[0]:
                    csvValueList.append(each.strip('"'))
                    startComma = True
                elif startComma:
                    csvValueList.append(each)
                else:
                    finalList.append(each)
            l_values = finalList

        if len(l_attrs) != len(l_values):
            raise Exception("#  of values returned (" + str(len(l_values)) + ") is not equal to #  of attributes specified (" + str(len(l_attrs)) + ")")

        l_attrDict = {}
        for i in range(len(l_attrs)):
            l_attrDict[l_attrs[i]] = l_values[i]
        return l_attrDict

    def convertKeysToUpper(self, dict_Data):
        return {k.upper(): v for k, v in dict_Data.items()}

    def i_a_ConfigBuilder(self, cmdKey, optionKey, configOptionsDict):
        configStr = " " + optionKey.lower() + " "
        configStr += '"'
        ATTRIBUTE = self.HMC_CMD_OPT[cmdKey][optionKey]
        for key in configOptionsDict.keys():
            if '-' == configOptionsDict[key][0].encode('utf8'):
                attr = ATTRIBUTE[key] + '-='
                addOrSubSign = '-'
            elif '+' == configOptionsDict[key][0].encode('utf8'):
                attr = ATTRIBUTE[key] + '+='
                addOrSubSign = '+'
            else:
                attr = ATTRIBUTE[key] + '='
                addOrSubSign = ''

            if ',' in configOptionsDict[key]:
                if r'\"\"' in configOptionsDict[key]:
                    configStr += attr + r'\"' + configOptionsDict[key].\
                        lstrip(addOrSubSign) + r'\"\"\"' + ','
                else:
                    configStr += attr + r'\"' + configOptionsDict[key].\
                        lstrip(addOrSubSign) + r'\"' + ','
            else:
                configStr += attr + configOptionsDict[key].lstrip(addOrSubSign) + ','

        configStr = configStr.rstrip(',')
        configStr += '"'
        return configStr
