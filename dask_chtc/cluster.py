import collections
import datetime
import logging
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

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
        input_files: Optional[Iterable[os.PathLike]] = None,
        gpu_lab: bool = False,
        gpus: Optional[int] = None,
        python: str = "./entrypoint.sh python3",
        **kwargs: Any,
    ):
        kwargs = self._modify_kwargs(
            kwargs, worker_image=worker_image, input_files=input_files, gpu_lab=gpu_lab, gpus=gpus,
        )

        super().__init__(python=python, **kwargs)

    @staticmethod
    def _modify_kwargs(
        kwargs: Dict[str, Any],
        *,
        worker_image: Optional[str] = None,
        input_files: Optional[Iterable[os.PathLike]] = None,
        gpu_lab: bool = False,
        gpus: Optional[int] = None,
    ) -> Dict[str, Any]:
        modified = kwargs.copy()

        # These get forward to the Dask scheduler
        modified["scheduler_options"] = merge(
            # Capture anything the user passed in.
            {"port": 3500, "dashboard_address": str(3400)},
            kwargs.get("scheduler_options"),
        )

        input_files = list(input_files or [])
        input_files.insert(0, ENTRYPOINT_SCRIPT_PATH)
        tif = ", ".join(Path(path).absolute().as_posix() for path in input_files)

        # These get put in the HTCondor job submit description
        modified["job_extra"] = merge(
            # Run workers in Docker universe
            {"universe": "docker", "docker_image": worker_image or "daskdev/dask:latest"},
            # Set up port forwarding from the container
            # 8787 will be the port inside the container
            # We won't know the port outside the container (the "host port")
            # until the job starts; see entrypoint.sh for details
            {"container_service_names": "dask", "dask_container_port": "8787"},
            # Transfer our internals and whatever else the user requested
            {"transfer_input_files": tif},
            # GPULab and general GPU setup
            {"My.WantGPULab": "true", "My.GPUJobLength": '"short"'} if gpu_lab else None,
            # Request however many GPUs they want,
            # or 1 if they selected GPULab but didn't say how many they want
            {"request_gpus": str(gpus) if gpus is not None else "1"}
            if gpus is not None or gpu_lab
            else None,
            # Workers can only run on certain execute nodes
            {"requirements": "(Target.HasCHTCStaging)"},
            # Support attributes to gather usage data
            {"My.IsDaskWorker": "true"},
            # Capture anything the user passed in.
            kwargs.get("job_extra"),
            # Overrideable utility/convenience attributes
            {"JobBatchName": "dask-worker", "keep_claim_idle": str(TEN_MINUTES)},
        )

        # These get tacked on to the command that starts the worker as arguments
        modified["extra"] = [
            *kwargs.get("extra", []),
            "--listen-address",
            "tcp://0.0.0.0:8787",
        ]

        return modified


def merge(*mappings: Optional[Mapping[Any, Any]]) -> Mapping[Any, Any]:
    """
    Merge the given mappings into a single mapping.
    Mappings given earlier in the list have precedence over those given later.
    """
    return dict(collections.ChainMap(*filter(None, mappings)))
