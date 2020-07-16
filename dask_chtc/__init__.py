import logging as _logging

# Set up null log handler
_logger = _logging.getLogger(__name__)
_logger.setLevel(_logging.DEBUG)
_logger.addHandler(_logging.NullHandler())

from .cluster import CHTCCluster
from .config import _ensure_user_config_file, _set_base_config
from .version import __version__

_ensure_user_config_file()
_set_base_config()
