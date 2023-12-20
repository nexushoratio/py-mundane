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
        os.environ['COLUMNS'] = '80'
        os.environ['ROWS'] = '24'

    def test_dash_h(self):
        my_app = app.ArgparseApp()
        my_app.register_global_flags([log_mgr])
        stdout = io.StringIO()

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(stdout):
            my_app.parser.parse_args(['--help'])

        levels = '{debug,info,warning,error}'
        expected = inspect.cleandoc(
            fr"""usage:.*\[-h\] \[-L {levels}\]

        Global flags:
          -h, --help
          -L {levels}, --log-level {levels}
        """)
        self.assertRegex(stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)
