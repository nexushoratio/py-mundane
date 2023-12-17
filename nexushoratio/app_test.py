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
        os.environ['COLUMNS'] = '60'
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


class ArgparseAppRegisterCommandsTest(unittest.TestCase):

    def setUp(self):
        os.environ['COLUMNS'] = '60'
        os.environ['ROWS'] = '24'

        self.my_app = app.ArgparseApp()
        self.stdout = io.StringIO()

        self.my_app.register_shared_flags([flags_one, flags_two])
        self.my_app.register_commands([flags_one, flags_two])

    def test_dash_h_commands(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout):
            self.my_app.parser.parse_args(['-h'])

        expected = inspect.cleandoc(
            r"""usage:.*\[-h\] <command> ...

            Global flags:
              -h, --help

            Commands:
              For more details: python -m unittest <command> --help

              <command>            <command description>
                generate-report
                put-on-hat
                remove-shoes       Shoes have custom help.
                ingest-new-material
                                   Take in new material.
                process            Process random data.
                dance              Like no one is watching.

            """)

        self.assertRegex(self.stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

    def test_generate_report_dash_h(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout):
            self.my_app.parser.parse_args(['generate-report', '-h'])

        expected = inspect.cleandoc(
            r"""usage: .* generate-report \[-h\]

            options:
              -h, --help  show this help message and exit
            """)

        self.assertRegex(self.stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

    def test_put_on_hat_dash_h(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout):
            self.my_app.parser.parse_args(['put-on-hat', '-h'])

        expected = inspect.cleandoc(
            r"""usage: .* put-on-hat \[-h\] -x XYZZY
            [ ]* \[-k \| --keep \| --no-keep\]

            options:
              -h, --help            show this help message and exit
              -x XYZZY, --xyzzy XYZZY
                                    The xyzzy input.
              -k, --keep, --no-keep
                                    Keep intermediates.
            """)

        self.assertRegex(self.stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

    def test_remove_shoes_dash_h(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout):
            self.my_app.parser.parse_args(['remove-shoes', '-h'])

        # Oops, implementer forgot to run through textwrap or equiv
        expected = inspect.cleandoc(
            r"""usage: .* remove-shoes \[-h\]

            This is also a custom description.

                Built by hand.

            options:
              -h, --help  show this help message and exit
            """)
        self.assertRegex(self.stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

    def test_ingest_dash_h(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout):
            self.my_app.parser.parse_args(['ingest-new-material', '-h'])

        expected = inspect.cleandoc(
            r"""usage: .* ingest-new-material
            [ ]* \[-h\] -f FILENAME

            Take in new material.

            Read the material and do something useful with it.

            This is a second paragraph that has more details on what is
            going on in this command.  Including long sentences that
            wrap.

            options:
              -h, --help            show this help message and exit
              -f FILENAME, --filename FILENAME
                                    Filename to ingest.
            """)
        self.assertRegex(self.stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

    def test_process_dash_h(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout):
            self.my_app.parser.parse_args(['process', '-h'])

        expected = inspect.cleandoc(
            r"""usage: .* process \[-h\]

            Process random data.

            options:
              -h, --help  show this help message and exit
            """)
        self.assertRegex(self.stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

    def test_dance_dash_h(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout):
            self.my_app.parser.parse_args(['dance', '-h'])

        expected = inspect.cleandoc(
            r"""usage: .* dance \[-h\]
            [ ]* \[-n \| --now \| --no-now\]

            Like no one is watching.

            Second line here.

            Rest of the content.

            options:
              -h, --help           show this help message and exit
              -n, --now, --no-now  Now or later. \(default: False\)
            """)
        self.assertRegex(self.stdout.getvalue(), expected)
        self.assertEqual(result.exception.code, 0)

    def test_put_on_hat_foo(self):
        args = self.my_app.parser.parse_args(['put-on-hat', '--xyzzy', 'foo'])

        self.assertEqual(
            vars(args), {
                'name': 'put-on-hat',
                'func': flags_one.put_on_hat,
                'xyzzy': 'foo',
                'keep': None,
            })

    def test_put_on_hat_bar(self):
        args = self.my_app.parser.parse_args(
            ['put-on-hat', '--xyzzy', 'bar', '-k'])

        self.assertEqual(
            vars(args), {
                'name': 'put-on-hat',
                'func': flags_one.put_on_hat,
                'xyzzy': 'bar',
                'keep': True,
            })

    def test_put_on_hat_bar_no_keep(self):
        args = self.my_app.parser.parse_args(
            ['put-on-hat', '--xyzzy', 'bar', '--no-keep'])

        self.assertEqual(
            vars(args), {
                'name': 'put-on-hat',
                'func': flags_one.put_on_hat,
                'xyzzy': 'bar',
                'keep': False,
            })

    def test_dance(self):
        args = self.my_app.parser.parse_args(['dance'])

        self.assertEqual(
            vars(args), {
                'name': 'dance',
                'func': flags_two.dance,
                'now': False
            })


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
