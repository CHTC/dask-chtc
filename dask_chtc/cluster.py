import collections
import datetime
import logging
import os
from pathlib import Path
from typing import Iterable, Mapping, Optional

from dask_jobqueue import HTCondorCluster

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

TEN_MINUTES = datetime.timedelta(minutes=10).total_seconds()

PACKAGE_DIR = Path(__file__).parent
ENTRYPOINT_SCRIPT_PATH = (PACKAGE_DIR / "entrypoint.sh").absolute()


class CHTCCluster(HTCondorCluster):
    def __init__(
        self,
        *,
        worker_image: Optional[str] = None,
        transfer_input_files: Optional[Iterable[os.PathLike]] = None,
        use_gpus: bool = False,
        python: str = "./entrypoint.sh python3",
        **kwargs,
    ):
        kwargs = self._modify_kwargs(kwargs, worker_image, transfer_input_files, use_gpus)

        super().__init__(python=python, **kwargs)

    @staticmethod
    def _modify_kwargs(
        kwargs,
        worker_image: Optional[str] = None,
        transfer_input_files: Optional[Iterable[os.PathLike]] = None,
        use_gpus: bool = False,
    ):
        modified = kwargs.copy()

        # These get forward to the Dask scheduler
        modified["scheduler_options"] = merge(
            # Capture anything the user passed in.
            {"port": 3500, "dashboard_address": str(3400)},
            kwargs.get("scheduler_options"),
        )

        transfer_input_files = [ENTRYPOINT_SCRIPT_PATH] + list(transfer_input_files or [])
        # These get put in the HTCondor job submit description
        modified["job_extra"] = merge(
            # Run workers in Docker universe
            {"universe": "docker", "docker_image": worker_image or "daskdev/dask:latest"},
            # Workers can only run on certain execute nodes
            {"requirements": "(Target.HasCHTCStaging)"},
            # Set up port forwarding from the container
            # 8787 will be the port inside the container
            # We won't know the port outside the container (the "host port")
            # until the job starts
            {"container_service_names": "dask", "dask_container_port": "8787"},
            # Transfer the custom entrypoint script
            {"transfer_input_files": ", ".join(path.as_posix() for path in transfer_input_files)},
            # Support attributes for CHTC to gather usage data
            {"My.IsDaskWorker": "true"},
            # GPU setup
            {"request_gpus": "1", "My.WantGPULab": "true", "My.GPUJobLength": '"short"'}
            if use_gpus
            else {},
            # Capture anything the user passed in.
            kwargs.get("job_extra"),
            # Overrideable utility/convenience attributes
            {
                "JobBatchName": "dask-worker" if not use_gpus else "dask-worker-gpus",
                "keep_claim_idle": TEN_MINUTES,
            },
        )

        # These get tacked on to the command that starts the worker as arguments
        modified["extra"] = kwargs.get("extra", []) + [
            "--listen-address",
            "tcp://0.0.0.0:8787",
        ]

        return modified


def merge(*mappings: Mapping) -> Mapping:
    """
    Merge the given mappings into a single mapping.
    Mappings given earlier in the list have precedence over those given later.
    """
    return dict(collections.ChainMap(*filter(None, mappings)))
