"""Tests for log_mgr.py"""

import contextlib
import io
import os
import pathlib
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

from mundane import app
from mundane import log_mgr


def setUpModule():
    """Set up a new temp directory due to lots of log files."""
    orig_dir = tempfile.tempdir

    def restore_tempdir():
        tempfile.tempdir = orig_dir

    unittest.addModuleCleanup(restore_tempdir)

    tempfile.tempdir = tempfile.mkdtemp()


def munge_expected(old_s: str) -> str:
    """Modify a multiple line string in a standard way.

    * Run through textwrap.dedent()
    * Strip leading newline
    """
    return textwrap.dedent(old_s).lstrip()


class BaseLogging(unittest.TestCase):
    """Handle cases common to mucking around with a singleton."""

    def setUp(self):
        self.mee = self.id().split('.')[-1]

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

        sys.argv[0] = self.mee

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


class LogHandlerPropertyTest(BaseLogging):

    def setUp(self):
        super().setUp()
        self.set_handler()

    def set_handler(self):
        self.handler = log_mgr.LogHandler(
            self.mee, str(pathlib.PurePath('default', 'path'))
        )

    def check_properties(self, expected_dir: str):
        """Shared checks."""
        out_dir = pathlib.Path(self.handler.output_dir)

        self.assertTrue(out_dir.match(expected_dir))
        self.assertEqual(self.handler.short_filename, f'{self.mee}.log')
        # app.log.host.user.date-time.pid
        host = log_mgr.platform.node()
        pattern = fr'{self.mee}\.log\.{host}\.\w+\.\d{{8}}-\d{{6}}\.\d+$'
        self.assertRegex(self.handler.long_filename, pattern)

        self.assertEqual(
            self.handler.symlink_path,
            out_dir.joinpath(self.handler.short_filename).absolute()
        )
        self.assertEqual(
            self.handler.baseFilename,
            str(out_dir.joinpath(self.handler.long_filename).absolute())
        )

    def test_default_properties(self):
        self.check_properties(str(pathlib.PurePath('default', 'path')))

    def test_set_output_dir(self):
        out = tempfile.mkdtemp()
        self.handler.output_dir = out

        self.check_properties(out)

    def test_unusual_hostname(self):
        node = self.enterContext(
            mock.patch.object(
                log_mgr.platform, 'node', spec_set=True, autospec=True
            )
        )
        node.return_value = 'host-name-12.uncle.bob'
        self.set_handler()

        self.check_properties(str(pathlib.PurePath('default', 'path')))


class LogHandlerTest(BaseLogging):

    def setUp(self):
        super().setUp()

        self.logger = log_mgr.logging.getLogger(self.id())
        self.logger.propagate = False
        self.logger.setLevel('INFO')

        self.handler = log_mgr.LogHandler(self.id(), tempfile.mkdtemp())
        self.handler.output_dir = tempfile.mkdtemp()
        self.logger.addHandler(self.handler)

    def test_output_deferred_until_first_write(self):
        symlink = self.handler.symlink_path
        full_path = pathlib.Path(self.handler.baseFilename)

        self.assertFalse(symlink.exists(), 'should not exist yet')
        self.assertFalse(full_path.exists(), 'should not exist yet')

        self.logger.info('Logged from %s', self.id())

        self.assertTrue(symlink.exists(), 'should now exist')
        self.assertTrue(full_path.exists(), 'should now exist')

    def test_symlink_dst_created(self):
        self.logger.info('Logged from %s', self.id())

        self.assertTrue(
            self.handler.symlink_path.is_symlink(), 'should now exist'
        )

    def test_symlink_dst_already_exists(self):
        self.handler.symlink_path.touch()
        self.assertTrue(
            self.handler.symlink_path.exists(), 'exists sanity check'
        )
        self.assertFalse(
            self.handler.symlink_path.is_symlink(), 'symlink sanity check'
        )

        self.logger.info('Logged from %s', self.id())

        self.assertTrue(self.handler.symlink_path.is_symlink())

    def test_symlink_dst_is_directory(self):
        self.handler.symlink_path.mkdir()
        self.assertTrue(
            self.handler.symlink_path.is_dir(), 'dir sanity check'
        )

        self.logger.info('Logged from %s', self.id())

        self.assertTrue(self.handler.symlink_path.is_dir(), 'still a dir')

    def test_output_dir_does_not_exist(self):
        out_dir = pathlib.Path(self.handler.output_dir)
        self.handler.output_dir = str(out_dir.joinpath('extra', self.id()))

        self.logger.info('Logged from %s', self.id())


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
                SystemExit) as result, contextlib.redirect_stdout(self.stdout
                                                                  ):
            self.parser.parse_args(['--help'])

        expected = munge_expected(
            """
            usage: test_action_only [-h] [-x X]

            options:
              -h, --help  show this help message and exit
              -x X
            """
        )
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

        self.parser.parse_args('-x WARNING'.split())
        self.assertEqual(logger.level, log_mgr.logging.WARNING)

    def test_with_help(self):
        logger = log_mgr.logging.getLogger()
        logger.setLevel(log_mgr.logging.INFO)

        self.parser.add_argument(
            '-x', action=log_mgr.LogLevel, help='My help'
        )
        self.assertEqual(logger.level, log_mgr.logging.INFO)

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(self.stdout
                                                                  ):
            self.parser.parse_args(['--help'])

        expected = munge_expected(
            """
            usage: test_with_help [-h] [-x X]

            options:
              -h, --help  show this help message and exit
              -x X        My help (Default: INFO)
            """
        )
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

        self.parser.parse_args('-x WARNING'.split())
        self.assertEqual(logger.level, log_mgr.logging.WARNING)

    def test_with_choices(self):
        logger = log_mgr.logging.getLogger()
        logger.setLevel(0)

        self.parser.add_argument(
            '-x', action=log_mgr.LogLevel, choices=('INFO', 'WARNING')
        )
        self.assertEqual(logger.level, 0)

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(self.stdout
                                                                  ):
            self.parser.parse_args(['--help'])

        expected = munge_expected(
            """
            usage: test_with_choices [-h] [-x {INFO,WARNING}]

            options:
              -h, --help         show this help message and exit
              -x {INFO,WARNING}
            """
        )
        self.assertEqual(self.stdout.getvalue(), expected)
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
            help='My other help'
        )
        self.assertEqual(logger.level, log_mgr.logging.INFO)

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(self.stdout
                                                                  ):
            self.parser.parse_args(['--help'])

        expected = munge_expected(
            """
            usage: test_with_choices_and_help [-h]
                                              [-x {INFO,WARNING,CRITICAL}]

            options:
              -h, --help            show this help message and exit
              -x {INFO,WARNING,CRITICAL}
                                    My other help (Default: INFO)
            """
        )
        self.assertEqual(self.stdout.getvalue(), expected)
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
            log_level='WARNING'
        )
        self.assertEqual(logger.level, log_mgr.logging.WARNING)

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(self.stdout
                                                                  ):
            self.parser.parse_args(['--help'])

        expected = munge_expected(
            """
            usage: test_with_default_and_help [-h] [-x X]

            options:
              -h, --help  show this help message and exit
              -x X        My unusual help (Default: WARNING)
            """
        )
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

        self.parser.parse_args('-x CRITICAL'.split())
        self.assertEqual(logger.level, log_mgr.logging.CRITICAL)


class LogDirTest(BaseLogging):

    def setUp(self):
        super().setUp()

        log_mgr.activate(self.id(), tempfile.mkdtemp())
        self.parser = log_mgr.argparse.ArgumentParser()
        self.stdout = io.StringIO()
        self.handler = log_mgr.logging.getLogger().handlers[0]
        self.handler.output_dir = tempfile.mkdtemp()

        # Different length of tempdir can cause wrapping issues in help output
        os.environ['COLUMNS'] = f'{40 + len(self.handler.output_dir)}'

    def test_action_only(self):
        orig_out_dir = self.handler.output_dir

        self.parser.add_argument('-d', action=log_mgr.LogDir)

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(self.stdout
                                                                  ):
            self.parser.parse_args(['--help'])

        expected = munge_expected(
            """
            usage: test_action_only [-h] [-d D]

            options:
              -h, --help  show this help message and exit
              -d D
            """
        )
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)
        self.assertEqual(self.handler.output_dir, orig_out_dir)

        self.parser.parse_args(f'-d path/to/{self.id()}'.split())

        self.assertEqual(self.handler.output_dir, f'path/to/{self.id()}')

    def test_with_help(self):
        orig_out_dir = self.handler.output_dir
        self.parser.add_argument(
            '-d', action=log_mgr.LogDir, help='My dir help'
        )

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(self.stdout
                                                                  ):
            self.parser.parse_args(['--help'])

        expected = munge_expected(
            f"""
            usage: test_with_help [-h] [-d D]

            options:
              -h, --help  show this help message and exit
              -d D        My dir help (Default: {orig_out_dir})
            """
        )
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

    def test_with_default_and_help(self):
        out_dir = f'/path/to/{self.id()}'
        help_msg = 'My usual dir help'
        os.environ['COLUMNS'] = f'{30 + len(help_msg) + len(out_dir)}'

        self.parser.add_argument(
            '-d',
            action=log_mgr.LogDir,
            help=help_msg,
            default=log_mgr.argparse.SUPPRESS,
            log_dir=out_dir
        )

        self.assertEqual(
            self.handler.output_dir, out_dir,
            'Registering the flag was enough to change the directory.'
        )

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(self.stdout
                                                                  ):
            self.parser.parse_args(['--help'])

        expected = munge_expected(
            f"""
            usage: test_with_default_and_help [-h] [-d D]

            options:
              -h, --help  show this help message and exit
              -d D        {help_msg} (Default: {out_dir})
            """
        )
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

        self.parser.parse_args('-d dir/xyzzy'.split())

        self.assertEqual(self.handler.output_dir, 'dir/xyzzy')


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

    def setUp(self):
        super().setUp()

        log_mgr.activate(
            self.id(), str(pathlib.PurePath('well', 'known', 'path'))
        )
        self.handler = log_mgr.logging.getLogger().handlers[0]
        self.handler.output_dir = str(
            pathlib.PurePath('well', 'known', 'path')
        )

    def test_default_dash_h(self):
        my_app = app.ArgparseApp()
        my_app.register_global_flags([log_mgr])
        stdout = io.StringIO()

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(stdout):
            my_app.parser.parse_args(['--help'])

        levels = '{DEBUG,INFO,WARNING,ERROR,CRITICAL}'
        expected = munge_expected(
            f"""
            usage: test_default_dash_h [-h]
                                       [-L {levels}]
                                       [--log-dir LOG_DIR]

            Global flags:
              -h, --help
              -L {levels}, --log-level {levels}
                                    Minimal log level (Default:
                                    WARNING)
              --log-dir LOG_DIR     Logging directory (Default:
                                    well/known/path)
            """
        )
        self.assertEqual(stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

    def test_custom_logging_level_dash_h(self):
        # between info and warning
        log_mgr.logging.addLevelName(
            (log_mgr.logging.INFO + log_mgr.logging.WARNING + 2) // 2,
            'Custom'
        )

        my_app = app.ArgparseApp()
        my_app.register_global_flags([log_mgr])
        stdout = io.StringIO()

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(stdout):
            my_app.parser.parse_args(['--help'])

        levels = '{DEBUG,INFO,Custom,WARNING,ERROR,CRITICAL}'
        expected = munge_expected(
            f"""
            usage: test_custom_logging_level_dash_h [-h]
                                                    [-L {levels}]
                                                    [--log-dir LOG_DIR]

            Global flags:
              -h, --help
              -L {levels}, --log-level {levels}
                                    Minimal log level (Default:
                                    WARNING)
              --log-dir LOG_DIR     Logging directory (Default:
                                    well/known/path)
            """
        )
        self.assertEqual(stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

    def test_default_changes_logging_level(self):
        root_logger = log_mgr.logging.getLogger()
        root_logger.setLevel(0)

        self.assertEqual(root_logger.getEffectiveLevel(), 0)

        my_app = app.ArgparseApp()
        my_app.register_global_flags([log_mgr])

        args = my_app.parser.parse_args('-L INFO'.split())

        self.assertEqual(
            root_logger.getEffectiveLevel(), log_mgr.logging.INFO
        )
        self.assertEqual(vars(args), {}, 'log level should not be here')

    def test_custom_changes_logging_level(self):
        # between info and warning
        log_mgr.logging.addLevelName(
            (log_mgr.logging.INFO + log_mgr.logging.WARNING) // 2, 'Xyzzy'
        )

        root_logger = log_mgr.logging.getLogger()
        root_logger.setLevel(0)

        self.assertEqual(root_logger.getEffectiveLevel(), 0)

        my_app = app.ArgparseApp()
        my_app.register_global_flags([log_mgr])

        my_app.parser.parse_args('-L Xyzzy'.split())

        self.assertGreater(
            root_logger.getEffectiveLevel(), log_mgr.logging.INFO
        )

    def test_log_dir_flag(self):
        my_app = app.ArgparseApp()
        my_app.register_global_flags([log_mgr])

        self.assertEqual(self.handler.output_dir, 'well/known/path')

        my_app.parser.parse_args('--log-dir road/to/nowhere'.split())

        self.assertEqual(self.handler.output_dir, 'road/to/nowhere')


class ActivateTest(BaseLogging):

    def setUp(self):
        super().setUp()

        log_mgr.activate(self.id(), tempfile.mkdtemp())
        root_logger = log_mgr.logging.getLogger()
        root_logger.setLevel('INFO')
        self.handler = root_logger.handlers[0]
        self.handler.output_dir = tempfile.mkdtemp()

    def test_output_deferred_until_first_write(self):
        dst = self.handler.symlink_path

        self.assertFalse(dst.exists(), 'sanity check')

        log_mgr.logging.info('Logged from %s', self.id())

        self.assertTrue(dst.exists())

    def test_symlink_dst_created(self):
        log_mgr.logging.info('Logged from %s', self.id())

        self.assertTrue(self.handler.symlink_path.is_symlink())

    def test_symlink_dst_already_exists(self):
        dst = self.handler.symlink_path

        dst.touch()
        self.assertTrue(dst.exists(), 'does exist')
        self.assertFalse(dst.is_symlink(), 'but not a symlink')

        log_mgr.logging.info('Logged from %s', self.id())

        self.assertTrue(dst.is_symlink())

    def test_symlink_dst_is_directory(self):
        dst = self.handler.symlink_path

        dst.mkdir()
        self.assertTrue(dst.is_dir(), 'sanity check')

        log_mgr.logging.info('Logged from %s', self.id())

        self.assertTrue(dst.is_dir())
