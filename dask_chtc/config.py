from pathlib import Path

import dask
import yaml

PACKAGE_DIR = Path(__file__).parent
CONFIG_FILE_NAME = "jobqueue-chtc.yaml"
BASE_CONFIG_FILE = PACKAGE_DIR / CONFIG_FILE_NAME


def _ensure_user_config_file():
    dask.config.ensure_file(source=BASE_CONFIG_FILE)


def _set_base_config(priority: str = "old"):
    with open(BASE_CONFIG_FILE) as f:
        defaults = yaml.safe_load(f)

    dask.config.update(dask.config.config, defaults, priority=priority)


def _user_config_file_path() -> Path:
    return Path(dask.config.PATH) / CONFIG_FILE_NAME
