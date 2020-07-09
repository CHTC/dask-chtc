import logging
import sys
import time
from pathlib import Path
from pprint import pformat
from typing import Optional

import click
import dask
import htcondor
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
    version=__version__, prog_name="HTMap", message="%(prog)s version %(version)s",
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
    Subcommands for inspecting and editing Dask-CHTC's configuration.

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
def show(parsed, diff):
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


@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.argument("jupyter_args", nargs=-1, type=click.UNPROCESSED)
def jupyter(jupyter_args):
    logs_dir = Path.home() / ".dask-chtc" / "jupyter-logs"
    out = logs_dir / "current.out"
    err = logs_dir / "current.err"
    event_log = logs_dir / "currents.events"

    logs_dir.mkdir(parents=True, exist_ok=True)
    for p in (out, err, event_log):
        p.unlink(missing_ok=True)
        p.touch()

    arguments = " ".join(["-m", "jupyter", *jupyter_args, "--no-browser", "-y"])
    logger.debug(f"HTCondor job will run: {sys.executable} {arguments}")
    sub = htcondor.Submit(
        {
            "universe": "local",
            "JobBatchName": "dask-chtc jupyter",
            "executable": sys.executable,
            "arguments": arguments,
            "initialdir": Path.cwd(),
            "getenv": "true",
            "output": out.as_posix(),
            "error": err.as_posix(),
            "log": event_log.as_posix(),
            "stream_output": "true",
            "stream_error": "true",
            "transfer_executable": "false",
            "transfer_output_files": '""',
            "My.IsDaskCHTCJupyterNotebook": "true",
        }
    )

    with RunLocalUniverseJob(sub) as job:
        with out.open(mode="r") as out_file, err.open(mode="r") as err_file:
            observer = Observer()
            observer.schedule(EchoingEventHandler(out_file, color="bright_white"), path=str(out))
            observer.schedule(EchoingEventHandler(err_file, color="bright_white"), path=str(err))
            observer.start()

            jel = htcondor.JobEventLog(event_log.as_posix())
            events = jel.events(None)
            try:
                watch_job_events(events)
            except KeyboardInterrupt:
                job.rm()
                watch_job_events(events)

            observer.stop()

    stamp = int(time.time())
    out.rename(logs_dir / f"previous-{stamp}.out")
    err.rename(logs_dir / f"previous-{stamp}.err")
    event_log.rename(logs_dir / f"previous-{stamp}.events")


def watch_job_events(events):
    for event in events:
        text = str(event).rstrip()
        if event.type in (htcondor.JobEventType.JOB_HELD, htcondor.JobEventType.JOB_TERMINATED):
            click.secho(text, err=True, fg="red")
            break
        elif event.type is htcondor.JobEventType.JOB_ABORTED:
            click.secho(text, err=True, fg="white")
            break
        else:
            click.secho(text, err=True, fg="white")


class EchoingEventHandler(events.FileSystemEventHandler):
    def __init__(self, file, color: Optional[str] = None):
        self.file = file
        self.color = color

    def on_modified(self, event):
        for line in self.file:
            click.secho(line.rstrip(), fg=self.color, err=True)


class RunLocalUniverseJob:
    def __init__(self, submit_description: htcondor.Submit):
        self.submit_description = submit_description
        self.cluster_id: Optional[int] = None

    def __enter__(self):
        schedd = htcondor.Schedd()
        with schedd.transaction() as txn:
            self.cluster_id = self.submit_description.queue(txn)
        logger.debug(f"Submitted job with cluster ID {self.cluster_id}")

        return self

    def rm(self):
        try:
            schedd = htcondor.Schedd()
            schedd.act(htcondor.JobAction.Remove, [f"{self.cluster_id}.0"], "Shut down Jupyter")
        except:
            logger.exception(f"Failed to remove local universe job!")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rm()
