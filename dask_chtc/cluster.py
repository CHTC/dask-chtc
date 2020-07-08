import collections
import datetime
import logging
import math
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

from dask_jobqueue import HTCondorCluster

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


PACKAGE_DIR = Path(__file__).parent
ENTRYPOINT_SCRIPT_PATH = (PACKAGE_DIR / "entrypoint.sh").absolute()

PORT_INSIDE_CONTAINER = 8787
DEFAULT_SCHEDULER_PORT = 3500
DEFAULT_DASHBOARD_PORT = 3501


class CHTCCluster(HTCondorCluster):
    def __init__(
        self,
        *,
        cores: int = 1,
        memory: str = "1 GB",
        disk: str = "10 GB",
        worker_image: Optional[str] = None,
        input_files: Optional[Iterable[os.PathLike]] = None,
        gpu_lab: bool = False,
        gpus: Optional[int] = None,
        scheduler_port: int = DEFAULT_SCHEDULER_PORT,
        dashboard_port: int = DEFAULT_DASHBOARD_PORT,
        python: str = "./entrypoint.sh python3",
        **kwargs: Any,
    ):
        kwargs = self._modify_kwargs(
            kwargs,
            worker_image=worker_image,
            input_files=input_files,
            gpu_lab=gpu_lab,
            gpus=gpus,
            scheduler_port=scheduler_port,
            dashboard_port=dashboard_port,
        )

        super().__init__(cores=cores, memory=memory, disk=disk, python=python, **kwargs)

    @staticmethod
    def _modify_kwargs(
        kwargs: Dict[str, Any],
        *,
        worker_image: Optional[str] = None,
        input_files: Optional[Iterable[os.PathLike]] = None,
        gpu_lab: bool = False,
        gpus: Optional[int] = None,
        scheduler_port: int = DEFAULT_SCHEDULER_PORT,
        dashboard_port: int = DEFAULT_DASHBOARD_PORT,
    ) -> Dict[str, Any]:
        modified = kwargs.copy()

        # These get forwarded to the Dask scheduler.
        modified["scheduler_options"] = merge(
            {"port": scheduler_port, "dashboard_address": str(dashboard_port)},
            # Capture anything the user passed in.
            kwargs.get("scheduler_options"),
        )

        input_files = list(input_files or [])
        input_files.insert(0, ENTRYPOINT_SCRIPT_PATH)
        tif = ", ".join(Path(path).absolute().as_posix() for path in input_files)

        # These get put in the HTCondor job submit description.
        modified["job_extra"] = merge(
            # Run workers in Docker universe.
            {"universe": "docker", "docker_image": worker_image or "daskdev/dask:latest"},
            # Set up container port forwarding.
            # We won't know the port outside the container (the "host port")
            # until the job starts; see entrypoint.sh for details.
            # See --listen-address below for telling Dask to actually listen to this port.
            {"container_service_names": "dask", "dask_container_port": PORT_INSIDE_CONTAINER},
            # Transfer our internals and whatever else the user requested.
            {"transfer_input_files": tif},
            # Do not transfer any output files, ever.
            {"transfer_output_files": '""'},
            # GPULab and general GPU setup.
            {"My.WantGPULab": "true", "My.GPUJobLength": '"short"'} if gpu_lab else None,
            # Request however many GPUs they want,
            # or 1 if they selected GPULab but didn't say how many they want.
            {"request_gpus": str(gpus) if gpus is not None else "1"}
            if gpus is not None or gpu_lab
            else None,
            # Workers can only run on certain execute nodes.
            {"requirements": "(Target.HasCHTCStaging)"},
            # Support attributes to gather usage data.
            {"My.IsDaskWorker": "true"},
            # Capture anything the user passed in.
            kwargs.get("job_extra"),
            # Overrideable utility/convenience attributes.
            {
                # This will cause the workers to be grouped in condor_q, with a reasonable name.
                "JobBatchName": "dask-worker",
                # Keep worker claims idle briefly for fast reconnects.
                "keep_claim_idle": seconds(minutes=10),
                # Higher-than-default job priority.
                "priority": "1",
            },
        )

        # These get tacked on to the command that starts the worker as arguments.
        modified["extra"] = [
            *kwargs.get("extra", []),
            # Bind to port inside the container, per dask_container_port above.
            "--listen-address",
            f"tcp://0.0.0.0:{PORT_INSIDE_CONTAINER}",
        ]

        return modified


def merge(*mappings: Optional[Mapping[Any, Any]]) -> Mapping[Any, Any]:
    """
    Merge the given mappings into a single mapping.
    Mappings given earlier in the args have precedence over those given later.
    """
    return dict(collections.ChainMap(*filter(None, mappings)))


def seconds(**kwargs: int) -> int:
    """
    Produce an integer number of seconds from keyword arguments,
    like ``minutes = 5``.

    Parameters
    ----------
    kwargs
        Any keyword argument that could be passed to :class:`datetime.timedelta`.

    Returns
    -------
    seconds : int
        The **integer** number of seconds,
        rounded up,
        represented by the ``kwargs``.
    """
    return math.ceil(datetime.timedelta(**kwargs).total_seconds())
