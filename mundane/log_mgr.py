"""Provide a reasonable set of defaults for logging.

To use the global flag, register using:
   ArgparseApp().register_global_flags(logmgr)

To turn on the global log file, execute the following early in your program:
  log_mgr.activate()
"""
from __future__ import annotations

import argparse
import datetime
import logging
import os
import pwd
import socket
import sys
import tempfile
import typing

if typing.TYPE_CHECKING:  # pragma: no cover
    from mundane import app

LOG_FORMAT = (
    '%(levelname).1s%(asctime)s: %(filename)s:%(lineno)d'
    '(%(funcName)s)] {%(name)s} %(message)s')


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
