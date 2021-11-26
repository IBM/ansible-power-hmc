from __future__ import absolute_import, division, print_function
__metaclass__ = type
import logging
from collections import OrderedDict
from ansible_collections.ibm.power_hmc.plugins.module_utils.hmc_exceptions import HmcError
logger = logging.getLogger(__name__)


def resolve_return_code(rc):
    if rc == 1:
        return "Invalid command line argument"
    elif rc == 2:
        return "Conflicting arguments given"
    elif rc == 3:
        return "General runtime error"
    elif rc == 4:
        return "Unrecognized response from ssh (parse error)"
    elif rc == 5:
        return "Invalid/incorrect password"
    elif rc == 6:
        return "Host public key is unknown. sshpass exits without confirming the new key."
    else:
        return "Unknown issue"


class HmcCliConnection:

    ##
    # Constructor for HmcCliConnection
    #
    def __init__(self, module, ip, username, password):
        self.ip = ip
        self.pwd = password
        self.user = username
        self.module = module

    def execute(self, cmd):
        stderr = None
        stdout = None

        logger.debug("COMMAND: %s", cmd)
        if self.pwd:
            ssh_hmc_cmd = "sshpass -p  {0} ssh {1}@{2} '{3}'".format(self.pwd, self.user, self.ip, cmd)
        else:
            ssh_hmc_cmd = "ssh {0}@{1} '{2}'".format(self.user, self.ip, cmd)

        status_code, stdout, stderr = self.module.run_command(ssh_hmc_cmd, use_unsafe_shell=True)

        if status_code != 0:
            stderr = stderr.replace("\n", "").replace("\r", "").replace("\\", "")
            stdout = stdout.replace("\r", "").replace("..|", "\n").replace("../", "\n").replace("..-", "\n").replace("\\", "\n").replace("...", "")
            stdout = "".join(list(OrderedDict.fromkeys(stdout.split("\n"))))
            errMsg = None
            if stdout not in (None, '') and stderr:
                errMsg = stdout + " ERROR MSG => " + stderr
            elif stdout not in (None, ''):
                errMsg = stdout
            else:
                errMsg = stderr
            if not errMsg:
                raise HmcError(resolve_return_code(status_code))
            else:
                raise HmcError(errMsg)

        logger.debug("COMMAND RESULT: %s", stdout)
        return stdout
