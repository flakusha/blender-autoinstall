import platform
from enum import Enum, unique


# Exit codes
@unique
class EC(Enum):
    """This enum describes enum variants of errors in the script."""

    OK = 0
    INSTALLATION_FAILED = 1
    ADDON_NOT_INSTALLED = 2
    PIP_NOT_INSTALLED = 3
    PIP_MODULES_NOT_INSTALLED = 4
    PLATFORM_NOT_SUPPORTED = 5
    ADDON_ACTIVATION_FAILED = 6
    CONFIG_NOT_PROVIDED = 7
    CUSTOM_SCRIPT_FAILED = 10
    UNKNOWN_ERROR = 42


PLATFORM = platform.system()
