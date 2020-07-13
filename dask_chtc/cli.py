import getpass
import logging
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from pprint import pformat
from typing import List, Mapping, Optional

import classad
import click
import dask
import htcondor
import humanize
from click_didyoumean import DYMGroup
from watchdog import events
from watchdog.observers import Observer

from . import CHTCCluster, __version__
from .config import CONFIG_FILE_NAME, _ensure_user_config_file, _user_config_file_path

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS, cls=DYMGroup)
@click.option(
    "--verbose", "-v", is_flag=True, default=False, help="Show log messages as the CLI runs.",
)
@click.version_option(
    version=__version__, prog_name="Dask-CHTC", message="%(prog)s version %(version)s",
)
def cli(verbose):
    """
    Command line tools for Dask-CHTC.
    """
    if verbose:
        _start_logger()
    logger.debug(f'CLI called with arguments "{" ".join(sys.argv[1:])}"')


def _start_logger():
    package_logger = logging.getLogger("dask_chtc")
    package_logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter("%(asctime)s ~ %(levelname)s ~ %(name)s:%(lineno)d ~ %(message)s")
    )

    package_logger.addHandler(handler)

    return handler


@cli.group()
def config():
    """
    Inspect and edit Dask-CHTC's configuration.

    Dask-CHTC provides a Dask/Dask-Jobqueue configuration file which provides
    default values for the arguments of CHTCCluster.
    You can use the subcommands in this group to
    show, edit, or reset
    the contents of this configuration file.

    See https://docs.dask.org/en/latest/configuration.html#yaml-files
    for more information on Dask configuration files.
    """
    pass


@config.command()
def path():
    """
    Echo the path to the configuration file.
    """
    click.echo(_user_config_file_path())


@config.command()
@click.option(
    "--parsed",
    is_flag=True,
    default=False,
    help="Show the parsed Dask config instead of the contents of the configuration file.",
)
def show(parsed):
    """
    Show the contents of the configuration file.

    To show what Dask actually parsed from the configuration file,
    add the --parsed option.
    """

    if parsed:
        user_config_text = pformat(dask.config.get(f"jobqueue.{CHTCCluster.config_name}"), indent=2)
    else:
        user_config_text = _user_config_file_path().read_text()

    click.echo_via_pager(user_config_text)


@config.command()
def edit():
    """
    Opens your preferred editor on the configuration file.

    Set the EDITOR environment variable to change your preferred editor.
    """
    click.edit(filename=_user_config_file_path())


@config.command()
@click.confirmation_option(
    prompt="\n".join(
        [
            "Are you sure you want to reset your Dask-CHTC configuration file?",
            "It will be overwritten by the current base configuration provided by the Dask-CHTC package.",
            click.style("Any changes you have made will be lost!", fg="red"),
        ]
    ),
)
def reset():
    """
    Reset the configuration file's contents.
    """
    (Path(dask.config.PATH) / CONFIG_FILE_NAME).unlink()
    _ensure_user_config_file()


@cli.group()
def jupyter():
    """
    Run a Jupyter notebook server as an HTCondor job.

    Do not run Jupyter notebook servers on CHTC submit nodes except by
    using these commands!

    Only one Jupyter notebook server can be created by this tool at a time.
    The subcommands let you create and interact with that server
    in various ways.

    The "run" subcommand runs the notebook server as if you had started it
    yourself. If your terminal session ends, the notebook server will also stop.

    The "started" subcommand runs the notebook server as a persistent HTCondor
    job: it will not be removed if your terminal session ends.
    The "status" subcommand can then be used to get information about your
    notebook server (like its contact address, to put into your web browser).
    The "stop" subcommand can be used to stop your started notebook server.
    """


JUPYTER_ARGS = click.argument("jupyter_args", nargs=-1, type=click.UNPROCESSED,)


@jupyter.command(context_settings=dict(ignore_unknown_options=True))
@JUPYTER_ARGS
def run(jupyter_args):
    """
    Run a Jupyter notebook server as an HTCondor job.

    The Jupyter notebook server will be connected to your terminal session:
    if you press Ctrl-c or disconnect from the server, your notebook server
    will end.

    To start a notebook server that is not connected to your terminal session,
    use the "start" subcommand.

    Extra arguments will be forwarded to Jupyter.
    For example, to start Jupyter Lab on some known port, you could run:

        dask-chtc jupyter run lab --port 3456
    """
    with JupyterJobManager().start(jupyter_args) as manager:
        try:
            manager.watch_events()
        except KeyboardInterrupt:
            pass


@jupyter.command(context_settings=dict(ignore_unknown_options=True))
@JUPYTER_ARGS
def start(jupyter_args):
    """
    Start a Jupyter notebook server as a persistent HTCondor job.

    Just like the "run" subcommand, this will start a Jupyter notebook server
    and show you any output from it.
    Unlike the "run" subcommand,
    the Jupyter notebook server will not be connected to your terminal session:
    if you press Ctrl-c or disconnect from the server, your notebook server
    will continue running (though you will stop seeing output from it).

    You can see the status of a persistent notebook server started by this
    command by using the "status" subcommand.

    To start a notebook server that is connected to your terminal session,
    use the "run" subcommand.

    Extra arguments will be forwarded to Jupyter.
    For example, to start Jupyter Lab on some known port, you could run

        dask-chtc jupyter run lab --port 3456
    """

    manager = JupyterJobManager().start(jupyter_args)
    manager.start_echoing()
    try:
        manager.watch_events()
    except KeyboardInterrupt:
        pass


@jupyter.command()
def stop():
    """
    Stop a Jupyter notebook server that was started via "start".
    """
    JupyterJobManager().connect().stop()


@jupyter.command()
@click.option(
    "--raw",
    is_flag=True,
    default=False,
    help="Print the raw HTCondor job ad instead of the formatted output.",
)
def status(raw):
    """
    Get information about your running Jupyter notebook server.

    If you have started a Jupyter notebook server in the past and need to
    find it's address again, use this command.
    """
    now = datetime.utcnow().replace(tzinfo=timezone.utc)

    manager = JupyterJobManager()
    job = manager.discover()

    if raw:
        click.echo(job)
        return

    status_msg = click.style(f"█ {job.status}".ljust(10), fg=JOB_STATUS_TO_COLOR.get(job.status))

    lines = [f"{status_msg} {job.get('JobBatchName', 'ID: ' + str(job.cluster_id))}"]
    lines.extend(
        [
            f"Hold Reason: {job.hold_reason}" if job.is_held else None,
            f"Contact Address: {manager.contact_address}",
            f"Python Executable: {job.executable}",
            f"Working Directory:  {job.iwd}",
            f"Job ID: {job.cluster_id}.{job.proc_id}",
            f"Last status change at:  {job.status_last_changed_at} UTC ({humanize.naturaldelta(now - job.status_last_changed_at)} ago)",
            f"Originally started at: {job.submitted_at} UTC ({humanize.naturaldelta(now - job.submitted_at)} ago)",
            f"Output: {job.stdout}",
            f"Error:  {job.stderr}",
            f"Events: {job.log}",
        ]
    )

    # format the output
    lines = list(filter(None, lines))
    rows = [lines[0]]
    for line in lines[1:-1]:
        rows.append("├─ " + line)
    rows.append("└─ " + lines[-1])
    rows.append("")
    click.echo("\n".join(rows))


JOB_STATUS_MAPPING = {1: "IDLE", 2: "RUNNING", 3: "REMOVED", 4: "COMPLETED", 5: "HELD"}
JOB_STATUS_TO_COLOR = {"IDLE": "yellow", "RUNNING": "green", "HELD": "red", "REMOVED": "magenta"}


class Job(Mapping):
    def __init__(self, ad: classad.ClassAd):
        self._ad = ad

    def __iter__(self):
        yield from self.keys()

    def __len__(self) -> int:
        return len(self._ad)

    def __getitem__(self, item):
        return self._ad[item]

    def items(self):
        yield from self._ad.items()

    def keys(self):
        yield from self._ad.keys()

    def values(self):
        yield from self._ad.values()

    def __str__(self):
        return str(self._ad)

    @property
    def cluster_id(self) -> int:
        return self._ad["ClusterId"]

    @property
    def proc_id(self) -> int:
        return self._ad["ProcId"]

    @property
    def executable(self) -> str:
        return self._ad["Cmd"]

    @property
    def iwd(self) -> Path:
        return Path(self._ad["Iwd"]).absolute()

    @property
    def submitted_at(self) -> datetime:
        return datetime.fromtimestamp(self._ad["QDate"]).astimezone(timezone.utc)

    @property
    def status_last_changed_at(self) -> datetime:
        return datetime.fromtimestamp(self._ad["EnteredCurrentStatus"]).astimezone(timezone.utc)

    @property
    def status(self) -> str:
        return JOB_STATUS_MAPPING[self._ad["JobStatus"]]

    @property
    def is_held(self) -> bool:
        return self.status == "HELD"

    @property
    def hold_reason(self) -> str:
        return self._ad["HoldReason"]

    @property
    def stdout(self) -> Path:
        p = Path(self._ad["Out"])
        if not p.is_absolute():
            return (self.iwd / self._ad["Out"]).absolute()
        return p

    @property
    def stderr(self) -> Path:
        p = Path(self._ad["Err"])
        if not p.is_absolute():
            return (self.iwd / self._ad["Err"]).absolute()
        return p

    @property
    def log(self) -> Path:
        return Path(self._ad["UserLog"]).absolute()


class EchoingEventHandler(events.FileSystemEventHandler):
    def __init__(self, path: Path, color: Optional[str] = None):
        self.file = path.open(mode="r")
        self.color = color

    def on_modified(self, event: events.FileSystemEvent):
        for line in self.file:
            click.secho(line.rstrip(), fg=self.color, err=True)


class JupyterJobManager:
    def __init__(self, logs_dir: Optional[Path] = None):
        self.logs_dir = logs_dir or Path.home() / ".dask-chtc" / "jupyter-logs"

        self.out = self.logs_dir / f"current.out"
        self.err = self.logs_dir / f"current.err"
        self.event_log = self.logs_dir / f"current.events"

        self.cluster_id: Optional[int] = None
        self.events: Optional[htcondor.JobEventLog] = None
        self.observer: Optional[Observer] = None

    @classmethod
    def discover(cls) -> Job:
        schedd = htcondor.Schedd()

        query = schedd.query(constraint=f"Owner == {classad.quote(getpass.getuser())}",)
        if len(query) == 0:
            raise click.ClickException(
                "Was not able to find a running Jupyter notebook server job!"
            )

        return Job(query[0])

    @classmethod
    def has_running_job(cls) -> bool:
        try:
            cls.discover()
            return True
        except click.ClickException:
            return False

    def connect(self) -> "JupyterJobManager":
        job_ad = self.discover()

        self.cluster_id = job_ad["ClusterId"]

        return self

    @property
    def contact_address(self) -> str:
        jupyter_logs = self.err.read_text().splitlines()
        contact_addresses = set()
        for line in jupyter_logs:
            match = re.search(r"https?://.+/?token=.+$", line)
            if match:
                contact_addresses.add(match.group(0))

        if len(contact_addresses) == 0:
            raise Exception("Could not find contact address for Jupyter notebook server from logs")

        # TODO: this choice is extremely arbitrary...
        return sorted(contact_addresses)[0]

    def start(self, jupyter_args: List[str]) -> "JupyterJobManager":
        if self.has_running_job():
            raise click.ClickException(
                'You already have a running Jupyter notebook server; try the "status" subcommand to see it.'
            )

        self.prep_log_files()

        arguments = " ".join(["-m", "jupyter", *jupyter_args, "--no-browser", "-y"])
        sub = htcondor.Submit(
            {
                "universe": "local",
                "JobBatchName": " ".join(("jupyter", *jupyter_args)),
                "executable": sys.executable,
                "arguments": arguments,
                "initialdir": Path.cwd(),
                "output": self.out.as_posix(),
                "error": self.err.as_posix(),
                "log": self.event_log.as_posix(),
                "stream_output": "true",
                "stream_error": "true",
                "getenv": "true",
                "transfer_executable": "false",
                "transfer_output_files": '""',
                "My.IsDaskCHTCJupyterNotebookServer": "true",
            }
        )

        logger.debug(f"HTCondor job submit description:\n{sub}")

        schedd = htcondor.Schedd()
        with schedd.transaction() as txn:
            self.cluster_id = sub.queue(txn)

        logger.debug(f"Submitted job with cluster ID {self.cluster_id}")

        return self

    def watch_events(self) -> None:
        if self.events is None:
            self.events = htcondor.JobEventLog(self.event_log.as_posix())

        for event in self.events:
            text = str(event).rstrip()
            if event.type in (htcondor.JobEventType.JOB_HELD, htcondor.JobEventType.JOB_TERMINATED):
                click.secho(text, err=True, fg="red")
            elif event.type is htcondor.JobEventType.JOB_ABORTED:
                click.secho(text, err=True, fg="white")
                break
            else:
                click.secho(text, err=True, fg="white")

    def remove_job(self) -> None:
        try:
            schedd = htcondor.Schedd()
            schedd.act(
                htcondor.JobAction.Remove,
                [f"{self.cluster_id}.0"],
                "Shut down Jupyter notebook server",
            )
        except Exception:
            logger.exception(f"Failed to remove Jupyter notebook server job!")

    def start_echoing(self) -> None:
        if self.observer is not None:
            return

        self.observer = Observer()
        self.observer.schedule(EchoingEventHandler(self.out), path=str(self.out))
        self.observer.schedule(EchoingEventHandler(self.err), path=str(self.err))
        self.observer.start()

        logger.debug("Started echoing job log files")

    def stop_echoing(self) -> None:
        if self.observer is None:
            return

        self.observer.stop()
        self.observer = None

        logger.debug("Stopped echoing job log files")

    def prep_log_files(self) -> None:
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        for p in (self.out, self.err, self.event_log):
            # Path.unlink(missing_ok=True) wasn't added until Python 3.8
            if p.exists():
                p.unlink()
            p.touch(exist_ok=True)

    def rotate_files(self) -> int:
        stamp = int(time.time())

        self.out.rename(self.logs_dir / f"previous-{stamp}.out")
        self.err.rename(self.logs_dir / f"previous-{stamp}.err")
        self.event_log.rename(self.logs_dir / f"previous-{stamp}.events")

        return stamp

    def stop(self) -> None:
        self.start_echoing()
        self.remove_job()
        self.watch_events()
        self.stop_echoing()
        self.rotate_files()

    def __enter__(self) -> "JupyterJobManager":
        self.start_echoing()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
