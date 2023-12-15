"""Tests for app.py"""
import contextlib
import inspect
import io
import os
import unittest

from nexushoratio import app

from nexushoratio.test_data import flags_one
from nexushoratio.test_data import flags_two


class ArgparseAppParsingTest(unittest.TestCase):

    def setUp(self):
        os.environ['COLUMNS'] = '80'
        os.environ['ROWS'] = '24'

    def test_no_args(self):
        my_app = app.ArgparseApp()
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            my_app.parser.parse_args([])

        self.assertEqual(stdout.getvalue(), '')

    def test_dash_h(self):
        my_app = app.ArgparseApp()
        stdout = io.StringIO()

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(stdout):
            my_app.parser.parse_args(['-h'])

        expected = inspect.cleandoc(
            r"""usage:.*\[-h\]

        Global flags:
          -h, --help
        """)
        self.assertRegex(stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

    def test_dash_dash_help(self):
        my_app = app.ArgparseApp()
        stdout = io.StringIO()

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(stdout):
            my_app.parser.parse_args(['--help'])

        expected = inspect.cleandoc(
            r"""usage:.*\[-h\]

        Global flags:
          -h, --help
        """)
        self.assertRegex(stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

    def test_unknown_arg(self):
        my_app = app.ArgparseApp()
        stderr = io.StringIO()

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stderr(stderr):
            my_app.parser.parse_args(['-k'])

        expected = inspect.cleandoc(
            r"""usage:.*\[-h\]
            .*error: unrecognized arguments: -k
            """)
        self.assertRegex(stderr.getvalue(), expected)
        self.assertEqual(result.exception.code, 2)


class ArgparseAppRegisterFlagsTest(unittest.TestCase):

    def setUp(self):
        os.environ['COLUMNS'] = '80'
        os.environ['ROWS'] = '24'

    def test_global_flags(self):
        my_app = app.ArgparseApp()
        stdout = io.StringIO()

        my_app.register_global_flags([flags_one, flags_two])

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(stdout):
            my_app.parser.parse_args(['-h'])

        expected = inspect.cleandoc(
            r"""usage:.*\[-h\] \[--foo\]

        Global flags:
          -h, --help
          --foo *Enable foo-ing.
        """)
        self.assertRegex(stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

    def test_shared_flags(self):
        my_app = app.ArgparseApp()
        stdout = io.StringIO()

        my_app.register_shared_flags([flags_one, flags_two])

        self.assertIn('foo', my_app._shared_parsers)  # pylint: disable=protected-access

        self.assertRaisesRegex(
            Exception, 'called again', my_app.register_shared_flags,
            [flags_one, flags_two])


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
