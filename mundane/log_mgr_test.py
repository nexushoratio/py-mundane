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


class FlagsTest(unittest.TestCase):

    def setUp(self):
        os.environ['COLUMNS'] = '60'
        os.environ['ROWS'] = '24'

        orig_levels = log_mgr.logging._levelToName.copy()  # pylint: disable=protected-access

        def restore_orig_levels():
            log_mgr.logging._levelToName = orig_levels.copy()  # pylint: disable=protected-access

        self.addCleanup(restore_orig_levels)

    def test_default_dash_h(self):
        my_app = app.ArgparseApp()
        my_app.register_global_flags([log_mgr])
        stdout = io.StringIO()

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(stdout):
            my_app.parser.parse_args(['--help'])

        levels = '{debug,info,warning,error,critical}'
        expected = inspect.cleandoc(
            fr"""usage:.*\[-h\]
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
            (log_mgr.logging.INFO + log_mgr.logging.WARNING) // 2, 'CUSTOM')

        my_app = app.ArgparseApp()
        my_app.register_global_flags([log_mgr])
        stdout = io.StringIO()

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(stdout):
            my_app.parser.parse_args(['--help'])

        levels = '{.*,info,custom,warning,.*}'
        expected = inspect.cleandoc(
            fr"""usage:.*\[-h\]
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

        args = my_app.parser.parse_args('-L info'.split())

        self.assertEqual(
            root_logger.getEffectiveLevel(), log_mgr.logging.INFO)
        self.assertEqual(vars(args), {}, 'log level should not be here')

    def test_custom_changes_logging_level(self):
        # between info and warning
        log_mgr.logging.addLevelName(
            (log_mgr.logging.INFO + log_mgr.logging.WARNING) // 2, 'CUSTOM')

        root_logger = log_mgr.logging.getLogger()
        root_logger.setLevel(0)

        self.assertEqual(root_logger.getEffectiveLevel(), 0)

        my_app = app.ArgparseApp()
        my_app.register_global_flags([log_mgr])

        my_app.parser.parse_args('-L custom'.split())

        self.assertGreater(
            root_logger.getEffectiveLevel(), log_mgr.logging.INFO)


class ActivateTest(unittest.TestCase):

    def setUp(self):
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

        orig_sys_argv0 = sys.argv[0]

        def restore_sys_argv0():
            sys.argv[0] = orig_sys_argv0

        self.addCleanup(restore_sys_argv0)

        sys.argv[0] = self.id()

    def test_noop(self):
        # This triggers other paths in clean up so they do not bitrot.
        pass

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
