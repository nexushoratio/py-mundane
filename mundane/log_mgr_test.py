"""Tests for log_mgr.py"""

import contextlib
import inspect
import io
import os
import unittest

from mundane import app
from mundane import log_mgr


class LogMgrFlagsTest(unittest.TestCase):

    def setUp(self):
        os.environ['COLUMNS'] = '60'
        os.environ['ROWS'] = '24'

        orig_levels = log_mgr.logging._levelToName.copy()  # pylint: disable=protected-access

        def restore_orig_levels():
            log_mgr.logging._levelToName = orig_levels.copy()  # pylint: disable=protected-access

        self.addCleanup(restore_orig_levels)

    def test_dash_h(self):
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
