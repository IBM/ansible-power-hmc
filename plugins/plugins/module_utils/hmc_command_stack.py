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
               'LSSYSCFG': 'lssyscfg'}

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
                                '-F': ' -F '}
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
                if "too many values to unpack" in errMsg:
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
