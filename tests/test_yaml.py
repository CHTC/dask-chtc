from dask_chtc.config import PACKAGE_CONFIG_FILE


def test_config_file_in_package():
    assert PACKAGE_CONFIG_FILE.exists()
