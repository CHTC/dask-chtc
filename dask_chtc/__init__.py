from .cluster import CHTCCluster
from .config import _ensure_user_config_file, _set_base_config
from .version import __version__

_ensure_user_config_file()
_set_base_config()
