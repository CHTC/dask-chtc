from dask_chtc.cluster import ENTRYPOINT_SCRIPT_PATH


def test_entrypoint_script_in_right_place():
    assert ENTRYPOINT_SCRIPT_PATH.exists()
