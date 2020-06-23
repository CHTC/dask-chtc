import shutil
import sys

from dask_jobqueue import HTCondorCluster


def CHTCCluster(worker_image=None, gpus=False):
    shutil.rmtree("logs", ignore_errors=True)

    if worker_image is None:
        worker_image = sys.argv[1]

    job_extra = {
        "universe": "docker",
        "docker_image": worker_image,
        "container_service_names": "dask",
        "dask_container_port": "8787",
        "requirements": "(Target.HasCHTCStaging)",
        "keep_claim_idle": "600",
        "My.IsDaskWorker": "true",
        "My.wantFlocking": "true",
        "JobBatchName": "dask-worker",
    }

    if gpus:
        job_extra.update(
            {
                "request_gpus": "1",
                "My.WantGPULab": "true",
                "My.GPUJobLength": '"short"',
                "JobBatchName": "dask-worker-gpu",
            }
        )

    return HTCondorCluster(
        cores=1,
        memory="1 GB",
        disk="1 GB",
        log_directory="logs",
        python="python3",
        scheduler_options={"dashboard_address": "3400", "port": 3500},
        job_extra=job_extra,
    )
