from __future__ import absolute_import, division, print_function
__metaclass__ = type


class Error(Exception):
    """
    Abstract base class that serves as a common exception superclass for the
    hmc ansible module.
    """
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __repr__(self):
        if self.message:
            return "Error: {0}".format(self.message)

    def __str__(self):
        if self.message:
            return self.message


class ParameterError(Error):
    """
    Indicates an error with the module input parameters.
    """
    def __repr__(self):
        if self.message:
            return "ParameterError: {0}".format(self.message)


class ProcMemValidationError(Error):
    """
    Raised when process memory validation fails
    """
    def __repr__(self):
        if self.message:
            return "ProcMemValidationError: {0}".format(self.message)


class HmcError(Error):
    """
    Indicates an error with the hmc execution
    """
    def __repr__(self):
        if self.message:
            # In case if the message is in unicode
            if isinstance(self.message, u''.__class__):
                return "HmcError: {0}".format(self.message.encode('utf-8'))
            else:
                return "HmcError: {0}".format(self.message)
