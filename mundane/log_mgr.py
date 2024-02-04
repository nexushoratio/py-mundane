"""Provide a reasonable set of defaults for logging.

To use the global flag, register using:
   ArgparseApp().register_global_flags(log_mgr)

To turn on the global log file, execute the following early in your program:
  log_mgr.activate()
"""
from __future__ import annotations

import argparse
import datetime
import logging
import os
import pathlib
import platform
import pwd
import socket
import sys
import tempfile
import typing

import psutil

if typing.TYPE_CHECKING:  # pragma: no cover
    from mundane import app

LOG_FORMAT = (
    '%(levelname).1s%(asctime)s: %(filename)s:%(lineno)d'
    '(%(funcName)s)] {%(name)s} %(message)s')


class LogHandler(logging.FileHandler):
    """Logging handler that writes to a directory.

    Features:
    * It always defers opening the logs until the first write.
    * It uses a filename that should be unique across clusters.
    * It provides a convenience symlink when possible.
    * The output directory can be set before the first log is written.

    File names use the pattern below.  They should be as unique as hostnames
    across a cluster.  With the pattern, they should be easy to identify for
    asynchronous processing and to use the names as unique keys.

    A convenience symlink is also created that typically ends up pointing to
    the most recent invocation.  This makes it easy to use TAB-key expansion
    to find the current/most-recent log file from the shell.  Obviously user
    permissions could prevent the symlink if files are logged to a directory
    shared by users with a sticky-bit set (e.g., /tmp).

    argv[0].log -> argv[0].log.$HOST.$USER.$DATETIME.$PID
    """

    def __init__(self):
        process = psutil.Process()

        # The following handles 'python foo.py' better than process.name()
        progname = pathlib.Path(sys.argv[0]).name
        now = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')

        self.short_filename = f'{progname}.log'
        self.long_filename = (
            f'{self.short_filename}.{platform.node()}'
            f'.{process.username()}.{now}.{process.pid}')
        self.output_dir = tempfile.gettempdir()

        super().__init__(self._base_path, delay=True)

    @property
    def output_dir(self):
        """Where log files are written."""
        return self._output_dir

    @output_dir.setter
    def output_dir(self, value):
        self._output_dir = value
        self.symlink_path = pathlib.Path(
            self._output_dir, self.short_filename).absolute()

        self._base_path = pathlib.Path(self._output_dir,
                                       self.long_filename).absolute()
        self.baseFilename = str(self._base_path)

    def _open(self):
        handle = super()._open()

        # best effort on symlink
        try:
            self.symlink_path.unlink(missing_ok=True)
            self.symlink_path.symlink_to(self.baseFilename)
        except OSError:
            pass

        return handle


HANDLER = LogHandler()


class LogLevel(argparse.Action):  # pylint: disable=too-few-public-methods
    """Callback action to tweak log settings during flag parsing."""

    def __init__(self, *args, log_level: str | None = None, **kwargs):
        """Thin Action wrapper.

        For this action, the default is set via 'log_level' so that the caller
        can use 'argparse.SUPPRESS' to not pass it along via parse_args().

        Args:
          args: Passed directly to argparse.Action.
          log_level: Default logging level for the root logger.
          kwargs: Passed directly to argparse.Action.
        """
        self.log_level = log_level
        if self.log_level is None:
            root_logger = logging.getLogger()
            self.log_level = logging.getLevelName(
                root_logger.getEffectiveLevel())

        if 'help' in kwargs:
            kwargs['help'] += ' (Default: %(_log_level)s)'

        super().__init__(*args, **kwargs)

    # The following ignore is for the 'values' paramter.
    def __call__(  # type: ignore[override]
            self,
            parser: argparse.ArgumentParser,
            namespace: argparse.Namespace,
            values: str,
            option_string: str | None = None):
        set_root_log_level(values)

    @property
    def log_level(self):
        """The default root logging level."""
        return self._log_level

    @log_level.setter
    def log_level(self, value):
        self._log_level = value
        set_root_log_level(self._log_level)


def set_root_log_level(level: str | None):
    """Convenience function for setting the root logger level by name."""
    if level is not None:
        logging.getLogger().setLevel(level)


def mundane_global_flags(argp_app: app.ArgparseApp):
    """Register global flags."""

    # TODO: switch to getLevelNamesMapping() once minver = 3.11
    choices = tuple(
        name for level, name in sorted(logging._levelToName.items())  # pylint: disable=protected-access
        if level)

    argp_app.global_flags.add_argument(
        '-L',
        '--log-level',
        action=LogLevel,
        help='Minimal log level',
        default=argparse.SUPPRESS,
        choices=choices)


def activate():
    """Activate this logfile setup."""
    # argv[0] -> argv[0].$HOST.$USER.$DATETIME.$PID

    progname = os.path.basename(sys.argv[0])
    now = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')

    short_filename = f'{progname}.log'
    long_filename = (
        f'{short_filename}.{socket.gethostname()}'
        f'.{pwd.getpwuid(os.getuid())[0]}.{now}.{os.getpid()}')

    long_pathname = os.path.join(tempfile.gettempdir(), long_filename)
    short_pathname = os.path.join(tempfile.gettempdir(), short_filename)

    logging.basicConfig(format=LOG_FORMAT, filename=long_pathname, force=True)

    # best effort on symlink
    try:
        os.unlink(short_pathname)
    except OSError:
        pass
    os.symlink(long_pathname, short_pathname)
