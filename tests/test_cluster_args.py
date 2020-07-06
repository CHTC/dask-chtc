from dask_chtc import CHTCCluster


def test_can_override_job_batch_name():
    kwargs = CHTCCluster._modify_kwargs(kwargs=dict(job_extra={"JobBatchName": "foobar"}))

    assert kwargs["job_extra"]["JobBatchName"] == "foobar"


def test_cannot_override_job_universe():
    kwargs = CHTCCluster._modify_kwargs(kwargs=dict(job_extra={"universe": "foobar"}))

    assert kwargs["job_extra"]["universe"] == "docker"
