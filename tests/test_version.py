import dask_chtc


def test_has_dunder_version():
    assert hasattr(dask_chtc, "__version__")
