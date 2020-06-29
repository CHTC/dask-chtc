import shutil
import sys

from dask_jobqueue import HTCondorCluster


def CHTCCluster(
    worker_image=None, gpus=False, scheduler_port=3500, dashboard_port=3400
):
    shutil.rmtree("logs", ignore_errors=True)

    if worker_image is None:
        worker_image = sys.argv[1]

    job_extra = {
        "universe": "docker",
        "docker_image": worker_image,
        "container_service_names": "dask",
        "dask_container_port": "8787",
        "requirements": "(Target.HasCHTCStaging)",
        "transfer_input_files": "entrypoint.sh",
        "keep_claim_idle": "600",
        "My.IsDaskWorker": "true",
        "JobBatchName": "dask-worker",
    }

    request_memory = "1 GB"

    if gpus:
        job_extra.update(
            {
                "request_gpus": "1",
                "My.WantGPULab": "true",
                "My.GPUJobLength": '"short"',
                "JobBatchName": "dask-worker-gpu",
            }
        )

        request_memory = "4 GB"

    cluster = HTCondorCluster(
        cores=1,
        memory=request_memory,
        disk="10 GB",
        log_directory="logs",
        python="./entrypoint.sh python3",
        scheduler_options={
            "dashboard_address": str(dashboard_port),
            "port": scheduler_port,
        },
        job_extra=job_extra,
        extra=["--listen-address", "tcp://0.0.0.0:8787"],
    )

    return cluster
