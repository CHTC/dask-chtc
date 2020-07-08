import logging
import sys
from pathlib import Path
from pprint import pformat

import click
import dask
from click_didyoumean import DYMGroup

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
def show(parsed):
    """
    Show the contents of the configuration file.

    Can also be used to show what Dask actually parsed
    from the configuration file by adding the --parse option.
    """

    if parsed:
        text = pformat(dask.config.get(f"jobqueue.{CHTCCluster.config_name}"), indent=2)
    else:
        text = _user_config_file_path().read_text()

    click.echo_via_pager(text)


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
