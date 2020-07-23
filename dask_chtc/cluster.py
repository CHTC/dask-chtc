import collections
import datetime
import logging
import math
import random
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Set, Union

import dask
import psutil
from dask_jobqueue import HTCondorCluster
from dask_jobqueue.htcondor import HTCondorJob
from distributed.security import Security

from . import security

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

PACKAGE_DIR = Path(__file__).parent
ENTRYPOINT_SCRIPT_PATH = (PACKAGE_DIR / "entrypoint.sh").absolute()

PORT_INSIDE_CONTAINER = 8787
SCHEDULER_PORTS = set(range(3000, 4000))


class CHTCJob(HTCondorJob):
    config_name = "chtc"

    def __init__(self, *args, **kwargs):
        # Suppress automatic addition of TLS config options to the worker args
        # (so that we can add our own in entrypoint.sh).
        kwargs.pop("security")

        super().__init__(*args, **kwargs)


T_PORT_ARG = Union[int, Iterable[int]]


class CHTCCluster(HTCondorCluster):
    """
    A customized :class:`dask_jobqueue.HTCondorCluster` subclass for
    spawning Dask workers
    in the CHTC HTCondor pool.

    It provides a variety of custom arguments designed around the CHTC pool,
    and forwards any remaining arguments to
    :class:`dask_jobqueue.HTCondorCluster`.
    """

    config_name = "chtc"
    job_cls = CHTCJob

    def __init__(
        self,
        *,
        worker_image: Optional[str] = None,
        gpu_lab: bool = False,
        gpus: Optional[int] = None,
        batch_name: Optional[str] = None,
        python: str = "./entrypoint.sh python3",
        **kwargs: Any,
    ):
        """
        Parameters
        ----------
        worker_image
            The Docker image to run the Dask workers inside.
            Defaults to ``daskdev/dask:latest``
            (`Dockerfile <https://hub.docker.com/r/daskdev/dask/dockerfile>`_).
            See :ref:`this page <docker>`
            for advice on building Docker images for use with Dask-CHTC.
        gpu_lab
            If ``True``, workers will be allowed to run on GPULab nodes.
            If this is ``True``, the default value of ``gpus`` becomes ``1``.
            Defaults to ``False``.
        gpus
            The number of GPUs to request.
            Defaults to ``0`` unless ``gpu_lab = True``,
            in which case the default is ``1``.
        batch_name
            The HTCondor JobBatchName to assign to the worker jobs.
            This can be helpful for more sensible output for *condor_q*.
            Defaults to ``"dask-worker"``.
        python
            The command to execute to start Python inside the worker job.
            Only modify this if you know what you're doing!
        kwargs
            Additional keyword arguments,
            like ``cores`` or ``memory``,
            are passed to :class:`dask_jobqueue.HTCondorCluster`.
        """

        kwargs = self._modify_kwargs(
            kwargs, worker_image=worker_image, gpu_lab=gpu_lab, gpus=gpus, batch_name=batch_name,
        )

        super().__init__(python=python, **kwargs)

    @classmethod
    def _modify_kwargs(
        cls,
        kwargs: Dict[str, Any],
        *,
        worker_image: Optional[str] = None,
        gpu_lab: bool = False,
        gpus: Optional[int] = None,
        batch_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        This method implements the various special modifications we make to
        adapt dask-jobqueue to run on CHTC resources.

        See this class's __init__ method for details on the meanings of the
        arguments, and the comments in this method for everything else.
        """
        modified = kwargs.copy()

        # Security settings.
        # Worker security configuration is done in entrypoint.sh;
        # this mainly effects the client and scheduler.
        security.ensure_certs()
        modified["protocol"] = "tls://"
        modified["security"] = cls.security()

        # TODO: there are race conditions in port selection.
        # These get forwarded to the Dask scheduler.
        modified["scheduler_options"] = merge(
            {"port": random_open_port(SCHEDULER_PORTS)},
            # Capture anything the user passed in.
            kwargs.get(
                "scheduler_options",
                dask.config.get(f"jobqueue.{cls.config_name}.scheduler-options"),
            ),
        )

        # TODO: do we allow arbitrary input file transfer?
        encrypted_input_files = [security.CA_FILE, security.CERT_FILE]
        eif = ", ".join(Path(path).absolute().as_posix() for path in encrypted_input_files)

        input_files = [ENTRYPOINT_SCRIPT_PATH, *encrypted_input_files]
        tif = ", ".join(Path(path).absolute().as_posix() for path in input_files)

        # These get put in the HTCondor job submit description.
        gpus = gpus or dask.config.get(f"jobqueue.{cls.config_name}.gpus")
        gpu_lab = gpu_lab or dask.config.get(f"jobqueue.{cls.config_name}.gpu-lab")
        modified["job_extra"] = merge(
            # Run workers in Docker universe.
            {
                "universe": "docker",
                "docker_image": worker_image
                or dask.config.get(f"jobqueue.{cls.config_name}.worker-image"),
            },
            # Set up container port forwarding.
            # We won't know the port outside the container (the "host port")
            # until the job starts; see entrypoint.sh for details.
            # See --listen-address below for telling Dask to actually listen to this port.
            {"container_service_names": "dask", "dask_container_port": PORT_INSIDE_CONTAINER},
            # Transfer our internals and whatever else the user requested.
            {"transfer_input_files": tif, "encrypt_input_files": eif},
            # TODO: turn on encrypt_execute_directory ?
            # Do not transfer any output files, ever.
            {"transfer_output_files": '""'},
            # GPULab and general GPU setup.
            {"My.WantGPULab": "true", "My.GPUJobLength": '"short"'} if gpu_lab else None,
            # Request however many GPUs they want,
            # or 1 if they selected GPULab but didn't say how many they want.
            {"request_gpus": str(gpus) if gpus is not None else "1"}
            if gpus is not None or gpu_lab
            else None,
            # CHTC normally holds jobs after three days; vacate them instead.
            # There's no actual checkpointing: the worker job will just restart.
            {"My.is_resumable": "true"},
            # Workers can only run on certain execute nodes.
            {"requirements": "(Target.HasCHTCStaging)"},
            # Support attributes to gather usage data.
            {"My.IsDaskWorker": "true"},
            # Capture anything the user passed in.
            kwargs.get("job_extra", dask.config.get(f"jobqueue.{cls.config_name}.job-extra")),
            # Overrideable utility/convenience attributes.
            {
                # This will cause the workers to be grouped in condor_q, with a reasonable name.
                "JobBatchName": f'"{batch_name or dask.config.get(f"jobqueue.{cls.config_name}.batch-name")}"',
                # Keep worker claims idle briefly for fast restarts.
                "keep_claim_idle": seconds(minutes=10),
                # Higher-than-default job priority.
                "priority": "1",
            },
        )

        # These get tacked on to the command that starts the worker as arguments.
        modified["extra"] = [
            # Capture anything the user passed in.
            *kwargs.get("extra", dask.config.get(f"jobqueue.{cls.config_name}.extra")),
            # Bind to port inside the container, per dask_container_port above.
            "--listen-address",
            f"tcp://0.0.0.0:{PORT_INSIDE_CONTAINER}",
        ]

        return modified

    @classmethod
    def security(cls):
        """
        Return the Dask ``Security`` object used by Dask-CHTC.
        Can also be used to create a new Dask ``Client`` with the correct
        security settings for connecting to your workers, e.g. if you started
        your :class:`CHTCCluster` via the Dask JupyterLab extension.
        """
        ca_file = str(security.CA_FILE)
        cert_file = str(security.CERT_FILE)
        return Security(
            tls_ca_file=ca_file,
            tls_worker_cert=cert_file,
            tls_worker_key=cert_file,
            tls_client_cert=cert_file,
            tls_client_key=cert_file,
            tls_scheduler_cert=cert_file,
            tls_scheduler_key=cert_file,
            require_encryption=True,
        )


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


def random_open_port(ports: Iterable[int]) -> int:
    """
    Find a random available port among the given ports.
    """
    return random.sample(filter_ports(ports), k=1)[0]


def filter_ports(
    desired_ports: Iterable[int], bad_ports: Optional[Iterable[int]] = None
) -> Set[int]:
    """
    Filter the desired ports down to the ones that are not "bad".

    Parameters
    ----------
    desired_ports
        The ports we would like to use.
    bad_ports
        The ports that we shouldn't use.
        If not given, use :func:`used_ports`.

    Returns
    -------
    good_ports : Set[int]
        The ports from ``desired_ports`` that weren't in ``bad_ports``.
    """
    return set(desired_ports) - set(bad_ports or used_ports())


def used_ports() -> Set[int]:
    """
    Return a set containing the ports that are currently in use.
    """
    return {connection.laddr.port for connection in psutil.net_connections()}
