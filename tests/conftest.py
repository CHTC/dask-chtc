import dask
import pytest

from dask_chtc.config import _set_base_config


@pytest.fixture(scope="function", autouse=True)
def reset_dask_config():
    # reset the dask config to scratch
    dask.config.refresh()

    # overwrite any user config that leaked in with the package copy of the config file
    _set_base_config(priority="new")
