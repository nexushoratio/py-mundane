"""Tests for log_mgr.py"""

import contextlib
import inspect
import io
import os
import pathlib
import sys
import tempfile
import unittest

from mundane import app
from mundane import log_mgr


def setUpModule():
    """Set up a new temp directory due to lots of log files."""
    orig_dir = tempfile.tempdir

    def restore_tempdir():
        tempfile.tempdir = orig_dir

    unittest.addModuleCleanup(restore_tempdir)

    tempfile.tempdir = tempfile.mkdtemp()


class BaseLogging(unittest.TestCase):
    """Handle cases common to mucking around with a singleton."""

    def setUp(self):
        self.prep_tty_vars()
        self.prep_level_names()
        self.prep_logger_handlers()
        self.prep_sys_argv()
        self.prep_root_logging_level()

    def prep_tty_vars(self):
        """Explicitly control line wrapping of help.

        By keeping columns fairly narrow, it makes writing tests fit < 80
        chars.
        """
        os.environ['COLUMNS'] = '60'
        os.environ['ROWS'] = '24'

    def prep_level_names(self):
        """Restore level names after each test."""
        orig_levels = log_mgr.logging._levelToName.copy()  # pylint: disable=protected-access

        def restore_orig_levels():
            log_mgr.logging._levelToName = orig_levels.copy()  # pylint: disable=protected-access

        self.addCleanup(restore_orig_levels)

    def prep_logger_handlers(self):
        """Restore known logging handlers after each test."""
        logger = log_mgr.logging.getLogger()
        orig_handlers = logger.handlers.copy()

        def restore_orig_handlers():
            for hdlr in logger.handlers:
                if hdlr not in orig_handlers:
                    logger.removeHandler(hdlr)
                    hdlr.close()
            for hdlr in orig_handlers:
                if hdlr not in logger.handlers:
                    logger.addHandler(hdlr)

        self.addCleanup(restore_orig_handlers)

    def prep_sys_argv(self):
        """Set sys_argv[0] to something knowable to assist testing."""
        orig_sys_argv0 = sys.argv[0]

        def restore_sys_argv0():
            sys.argv[0] = orig_sys_argv0

        self.addCleanup(restore_sys_argv0)

        # Keep argv well known so tests can control line wrapping.
        sys.argv[0] = 'my_app'

    def prep_root_logging_level(self):
        """Restore root logging level after each test."""
        logger = log_mgr.logging.getLogger()
        orig_level = logger.level

        def restore_logger_level():
            logger.level = orig_level

        self.addCleanup(restore_logger_level)

    def test_noop(self):
        # This triggers certain code paths in clean up so they do not bitrot.
        pass


class LogLevelTest(BaseLogging):

    def setUp(self):
        super().setUp()
        self.parser = log_mgr.argparse.ArgumentParser()
        self.stdout = io.StringIO()

    def test_action_only(self):
        logger = log_mgr.logging.getLogger()
        logger.setLevel(0)

        self.parser.add_argument('-x', action=log_mgr.LogLevel)
        self.assertEqual(logger.level, 0)

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout):
            self.parser.parse_args(['--help'])

        expected = inspect.cleandoc(
            r"""usage: my_app \[-h\] \[-x X\]

        options:
          -h, --help  show this help message and exit
          -x X

        """)
        self.assertRegex(self.stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

        self.parser.parse_args('-x WARNING'.split())
        self.assertEqual(logger.level, log_mgr.logging.WARNING)

    def test_with_help(self):
        logger = log_mgr.logging.getLogger()
        logger.setLevel(log_mgr.logging.INFO)

        self.parser.add_argument(
            '-x', action=log_mgr.LogLevel, help='My help')
        self.assertEqual(logger.level, log_mgr.logging.INFO)

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout):
            self.parser.parse_args(['--help'])

        expected = inspect.cleandoc(
            r"""usage: my_app \[-h\] \[-x X\]

        options:
          -h, --help  show this help message and exit
          -x X        My help \(Default: INFO\)

        """)
        self.assertRegex(self.stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

        self.parser.parse_args('-x WARNING'.split())
        self.assertEqual(logger.level, log_mgr.logging.WARNING)

    def test_with_choices(self):
        logger = log_mgr.logging.getLogger()
        logger.setLevel(0)

        self.parser.add_argument(
            '-x', action=log_mgr.LogLevel, choices=('INFO', 'WARNING'))
        self.assertEqual(logger.level, 0)

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout):
            self.parser.parse_args(['--help'])

        expected = inspect.cleandoc(
            r"""usage: my_app \[-h\] \[-x {INFO,WARNING}\]

        options:
          -h, --help         show this help message and exit
          -x {INFO,WARNING}

        """)
        self.assertRegex(self.stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

        self.parser.parse_args('-x WARNING'.split())
        self.assertEqual(logger.level, log_mgr.logging.WARNING)

    def test_with_choices_and_help(self):
        logger = log_mgr.logging.getLogger()
        logger.setLevel(log_mgr.logging.INFO)

        self.parser.add_argument(
            '-x',
            action=log_mgr.LogLevel,
            choices=('INFO', 'WARNING', 'CRITICAL'),
            help='My other help')
        self.assertEqual(logger.level, log_mgr.logging.INFO)

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout):
            self.parser.parse_args(['--help'])

        expected = inspect.cleandoc(
            r"""usage: my_app \[-h\] \[-x {INFO,WARNING,CRITICAL}\]

        options:
          -h, --help            show this help message and exit
          -x {INFO,WARNING,CRITICAL}
                                My other help \(Default: INFO\)

        """)
        self.assertRegex(self.stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

        self.parser.parse_args('-x CRITICAL'.split())
        self.assertEqual(logger.level, log_mgr.logging.CRITICAL)

    def test_with_default_and_help(self):
        logger = log_mgr.logging.getLogger()
        logger.setLevel(log_mgr.logging.WARNING)

        self.parser.add_argument(
            '-x',
            action=log_mgr.LogLevel,
            help='My unusual help',
            default=log_mgr.argparse.SUPPRESS,
            log_level='WARNING')
        self.assertEqual(logger.level, log_mgr.logging.WARNING)

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout):
            self.parser.parse_args(['--help'])

        expected = inspect.cleandoc(
            r"""usage: my_app \[-h\] \[-x X\]

        options:
          -h, --help  show this help message and exit
          -x X        My unusual help \(Default: WARNING\)

        """)
        self.assertRegex(self.stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

        self.parser.parse_args('-x CRITICAL'.split())
        self.assertEqual(logger.level, log_mgr.logging.CRITICAL)


class SetRootLoggingLevelTest(BaseLogging):

    def test_with_string(self):
        logger = log_mgr.logging.getLogger()
        logger.setLevel(log_mgr.logging.WARNING)

        log_mgr.set_root_log_level('INFO')

        self.assertEqual(logger.level, log_mgr.logging.INFO)

    def test_with_none(self):
        logger = log_mgr.logging.getLogger()
        logger.setLevel(log_mgr.logging.WARNING)

        log_mgr.set_root_log_level(None)

        self.assertEqual(logger.level, log_mgr.logging.WARNING)


class FlagsTest(BaseLogging):

    def test_default_dash_h(self):
        my_app = app.ArgparseApp()
        my_app.register_global_flags([log_mgr])
        stdout = io.StringIO()

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(stdout):
            my_app.parser.parse_args(['--help'])

        levels = '{DEBUG,INFO,WARNING,ERROR,CRITICAL}'
        expected = inspect.cleandoc(
            fr"""usage: my_app \[-h\]
         *\[-L {levels}\]

        Global flags:
          -h, --help
          -L {levels}, --log-level {levels}
         *Minimal log level

        """)
        self.assertRegex(stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

    def test_custom_logging_level_dash_h(self):
        # between info and warning
        log_mgr.logging.addLevelName(
            (log_mgr.logging.INFO + log_mgr.logging.WARNING + 2) // 2,
            'Custom')

        my_app = app.ArgparseApp()
        my_app.register_global_flags([log_mgr])
        stdout = io.StringIO()

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(stdout):
            my_app.parser.parse_args(['--help'])

        levels = '{.*,INFO,Custom,WARNING,.*}'
        expected = inspect.cleandoc(
            fr"""usage: my_app \[-h\]
         *\[-L {levels}\]

        Global flags:
          -h, --help
          -L {levels}, --log-level {levels}
         *Minimal log level

        """)
        self.assertRegex(stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

    def test_default_changes_logging_level(self):
        root_logger = log_mgr.logging.getLogger()
        root_logger.setLevel(0)

        self.assertEqual(root_logger.getEffectiveLevel(), 0)

        my_app = app.ArgparseApp()
        my_app.register_global_flags([log_mgr])

        args = my_app.parser.parse_args('-L INFO'.split())

        self.assertEqual(
            root_logger.getEffectiveLevel(), log_mgr.logging.INFO)
        self.assertEqual(vars(args), {}, 'log level should not be here')

    def test_custom_changes_logging_level(self):
        # between info and warning
        log_mgr.logging.addLevelName(
            (log_mgr.logging.INFO + log_mgr.logging.WARNING) // 2, 'Xyzzy')

        root_logger = log_mgr.logging.getLogger()
        root_logger.setLevel(0)

        self.assertEqual(root_logger.getEffectiveLevel(), 0)

        my_app = app.ArgparseApp()
        my_app.register_global_flags([log_mgr])

        my_app.parser.parse_args('-L Xyzzy'.split())

        self.assertGreater(
            root_logger.getEffectiveLevel(), log_mgr.logging.INFO)


class ActivateTest(BaseLogging):

    def setUp(self):
        super().setUp()

        # In these tests, symlinks are created based upon argv0, so they do
        # should be unique.
        sys.argv[0] = self.id()

    def test_correct_filename(self):
        root_logger = log_mgr.logging.getLogger()

        log_mgr.activate()

        handler = root_logger.handlers[0]

        # app.log.host.user.date-time.pid
        pattern = '*/*.log.*.*.*-*.*'
        self.assertTrue(pathlib.PurePath(handler.baseFilename).match(pattern))

    def test_symlink_dst_created(self):
        dst = pathlib.Path(tempfile.gettempdir(), f'{self.id()}.log')

        log_mgr.activate()

        self.assertTrue(dst.is_symlink())

    def test_symlink_dst_already_exists(self):
        dst = pathlib.Path(tempfile.gettempdir(), f'{self.id()}.log')

        dst.touch()
        self.assertFalse(dst.is_symlink(), 'sanity check')

        log_mgr.activate()

        self.assertTrue(dst.is_symlink())

    def test_symlink_dst_is_directory(self):
        dst = pathlib.Path(
            tempfile.gettempdir(),
            pathlib.PurePath(self.id()).with_suffix('.log'))

        dst.mkdir()
        self.assertTrue(dst.is_dir(), 'sanity check')

        log_mgr.activate()

        self.assertTrue(dst.is_dir())

    def test_flag_changes_logging_level(self):
        root_logger = log_mgr.logging.getLogger()
        root_logger.setLevel(0)

        self.assertEqual(root_logger.getEffectiveLevel(), 0)

        my_app = app.ArgparseApp()
        my_app.register_global_flags([log_mgr])

        my_app.parser.parse_args('-L WARNING'.split())

        log_mgr.activate()

        self.assertEqual(
            root_logger.getEffectiveLevel(), log_mgr.logging.WARNING)

    def test_no_flag_leaves_logging_level_alone(self):
        magic_level = 17

        root_logger = log_mgr.logging.getLogger()
        root_logger.setLevel(magic_level)
        # A shame the level name is not add automatically
        log_mgr.logging.addLevelName(
            magic_level, log_mgr.logging.getLevelName(magic_level))

        self.assertEqual(root_logger.getEffectiveLevel(), magic_level)

        my_app = app.ArgparseApp()
        my_app.register_global_flags([log_mgr])

        log_mgr.activate()

        self.assertEqual(root_logger.getEffectiveLevel(), magic_level)
