"""Tests for app.py"""

import contextlib
import inspect
import io
import logging
import os
import sys
import unittest

from mundane import app

from mundane.test_data import flags_one
from mundane.test_data import flags_two


class DocstringTest(unittest.TestCase):

    def test_summary_only(self):
        """This is a simple method."""

        doc = app.Docstring(self.test_summary_only, 80)

        self.assertEqual(doc.summary, 'This is a simple method.')
        self.assertEqual(doc.description, 'This is a simple method.')

    def test_no_docstring(self):
        doc = app.Docstring(self.test_no_docstring, 80)

        self.assertEqual(doc.summary, '')
        self.assertEqual(doc.description, '')

    def test_docstring(self):
        """Lorem ipsum dolor sit amet, consectetur adipiscing elit.

        Nam non ornare ex, sit amet aliquet urna.  Mauris a fringilla
        justo.  Mauris eget mi arcu.  Mauris pretium faucibus purus eget
        consequat.

        Quisque et luctus lacus.  Mauris volutpat lacinia dignissim.  Cras
        cursus aliquam lacus a ultrices.  Proin nec nisi tristique, rutrum
        erat ac, rhoncus sapien.  Morbi vel eros ac est commodo
        malesuada.  Phasellus cursus porta ligula quis suscipit.  Maecenas
        at turpis neque.  Ut ipsum neque, eleifend hendrerit massa fringilla,
        tincidunt rutrum nisi.

        Integer tristique tortor et eros dictum pellentesque.
        """

    def test_long_normal_width(self):
        doc = app.Docstring(self.test_docstring, 80)

        expected_description = (
            'Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
            '',
            'Nam non ornare ex, sit amet aliquet urna.  Mauris a fringilla'
            ' justo.  Mauris',
            'eget mi arcu.  Mauris pretium faucibus purus eget consequat.',
            '',
            'Quisque et luctus lacus.  Mauris volutpat lacinia'
            ' dignissim.  Cras cursus',
            'aliquam lacus a ultrices.  Proin nec nisi tristique, rutrum'
            ' erat ac, rhoncus',
            'sapien.  Morbi vel eros ac est commodo malesuada.  Phasellus'
            ' cursus porta ligula',
            'quis suscipit.  Maecenas at turpis neque.  Ut ipsum neque,'
            ' eleifend hendrerit',
            'massa fringilla, tincidunt rutrum nisi.',
            '',
            'Integer tristique tortor et eros dictum pellentesque.',
        )
        self.assertEqual(
            doc.summary,
            'Lorem ipsum dolor sit amet, consectetur adipiscing elit.')
        self.assertEqual(doc.description, '\n'.join(expected_description))

    def test_full_wide_width(self):
        doc = app.Docstring(self.test_docstring, 150)

        expected_description = (
            'Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
            '',
            'Nam non ornare ex, sit amet aliquet urna.  Mauris a fringilla'
            ' justo.  Mauris eget mi arcu.  Mauris pretium faucibus purus'
            ' eget consequat.',
            '',
            'Quisque et luctus lacus.  Mauris volutpat lacinia'
            ' dignissim.  Cras cursus aliquam lacus a ultrices.  Proin nec'
            ' nisi tristique, rutrum erat ac, rhoncus',
            'sapien.  Morbi vel eros ac est commodo malesuada.  Phasellus'
            ' cursus porta ligula quis suscipit.  Maecenas at turpis'
            ' neque.  Ut ipsum neque, eleifend',
            'hendrerit massa fringilla, tincidunt rutrum nisi.',
            '',
            'Integer tristique tortor et eros dictum pellentesque.',
        )
        self.assertEqual(
            doc.summary,
            'Lorem ipsum dolor sit amet, consectetur adipiscing elit.')
        self.assertEqual(doc.description, '\n'.join(expected_description))

    def test_full_narrow_width(self):
        doc = app.Docstring(self.test_docstring, 40)

        expected_description = (
            'Lorem ipsum dolor sit amet, consectetur',
            'adipiscing elit.',
            '',
            'Nam non ornare ex, sit amet aliquet',
            'urna.  Mauris a fringilla justo.  Mauris',
            'eget mi arcu.  Mauris pretium faucibus',
            'purus eget consequat.',
            '',
            'Quisque et luctus lacus.  Mauris',
            'volutpat lacinia dignissim.  Cras cursus',
            'aliquam lacus a ultrices.  Proin nec',
            'nisi tristique, rutrum erat ac, rhoncus',
            'sapien.  Morbi vel eros ac est commodo',
            'malesuada.  Phasellus cursus porta',
            'ligula quis suscipit.  Maecenas at',
            'turpis neque.  Ut ipsum neque, eleifend',
            'hendrerit massa fringilla, tincidunt',
            'rutrum nisi.',
            '',
            'Integer tristique tortor et eros dictum',
            'pellentesque.',
        )
        self.assertEqual(doc.description, '\n'.join(expected_description))
        self.assertEqual(
            doc.summary,
            'Lorem ipsum dolor sit amet, consectetur\nadipiscing elit.')

    def test_missing_blank_line_after_summary(self):
        """This is my summary.
        This is the next line.

        Then the final content.
        """
        doc = app.Docstring(self.test_missing_blank_line_after_summary, 80)

        expected_description = (
            'This is my summary.',
            '',
            'This is the next line.',
            '',
            'Then the final content.',
        )

        self.assertEqual(doc.summary, 'This is my summary.')
        self.assertEqual(doc.description, '\n'.join(expected_description))

    def test_extra_blank_line_after_summary(self):
        """This is the blank line summary.

        """
        doc = app.Docstring(self.test_extra_blank_line_after_summary, 80)

        self.assertEqual(doc.summary, 'This is the blank line summary.')
        self.assertEqual(doc.description, 'This is the blank line summary.')

    def test_extra_blank_lines_in_docstring(self):
        """This is the first line.


        Then after two blank lines.



        And more blank lines.

        """
        doc = app.Docstring(self.test_extra_blank_lines_in_docstring, 80)

        expected_description = (
            'This is the first line.',
            '',
            'Then after two blank lines.',
            '',
            'And more blank lines.',
        )
        self.assertEqual(doc.summary, 'This is the first line.')
        self.assertEqual(doc.description, '\n'.join(expected_description))

    def test_first_line_is_blank(self):
        """

        This is really the first line.

        Then the last.


        """
        doc = app.Docstring(self.test_first_line_is_blank, 80)

        expected_description = (
            'This is really the first line.',
            '',
            'Then the last.',
        )
        self.assertEqual(doc.summary, 'This is really the first line.')
        self.assertEqual(doc.description, '\n'.join(expected_description))


class ArgparseAppParsingTest(unittest.TestCase):

    def setUp(self):
        os.environ['COLUMNS'] = '80'
        os.environ['ROWS'] = '24'

        self.my_app = app.ArgparseApp()
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()

    def test_no_args(self):

        with contextlib.redirect_stdout(
                self.stdout), contextlib.redirect_stderr(self.stderr):
            args = self.my_app.parser.parse_args([])

        self.assertEqual(self.stdout.getvalue(), '')
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(vars(args), {})

    def test_dash_h(self):

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            self.my_app.parser.parse_args(['-h'])

        expected = inspect.cleandoc(
            r"""usage:.*\[-h\]

        Global flags:
          -h, --help

        """)
        self.assertRegex(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_dash_dash_help(self):

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            self.my_app.parser.parse_args(['--help'])

        expected = inspect.cleandoc(
            r"""usage:.*\[-h\]

        Global flags:
          -h, --help

        """)
        self.assertRegex(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_unknown_arg(self):

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            self.my_app.parser.parse_args(['-k'])

        expected = inspect.cleandoc(
            r"""usage:.*\[-h\]
            .*error: unrecognized arguments: -k

            """)
        self.assertEqual(self.stdout.getvalue(), '')
        self.assertRegex(self.stderr.getvalue(), expected)
        self.assertEqual(result.exception.code, 2)


class ArgparseAppCustomizationsTest(unittest.TestCase):

    def setUp(self):
        os.environ['COLUMNS'] = '80'
        os.environ['ROWS'] = '24'

        self.stdout = io.StringIO()
        self.stderr = io.StringIO()

    def test_with_extras(self):
        description = 'This app does this thing.'
        epilog = 'This is an epilog.'
        my_app = app.ArgparseApp(description=description, epilog=epilog)

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            my_app.parser.parse_args(['-h'])

        expected = inspect.cleandoc(
            r"""usage:.*\[-h\]

        This app does this thing.

        Global flags:
          -h, --help

        This is an epilog.

        """)
        self.assertRegex(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)


class ArgparseAppParsingWithLogMgrTest(unittest.TestCase):

    def setUp(self):
        # Ensure a handler exists
        logging.debug(self.id)

        os.environ['COLUMNS'] = '80'
        os.environ['ROWS'] = '24'

        self.stdout = io.StringIO()
        self.stderr = io.StringIO()

        logger = logging.getLogger()
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

    def test_noop(self):
        # This triggers other paths in clean up so they do not bitrot.
        pass

    def test_dash_h(self):
        my_app = app.ArgparseApp(use_log_mgr=True)

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            my_app.parser.parse_args(['-h'])

        expected = inspect.cleandoc(
            r"""usage:.*\[-h\] \[-L {.*}\]

        Global flags:
          -h, --help
          -L {.*}, --log-level {.*}

        """)
        self.assertRegex(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_activated(self):
        app.ArgparseApp(use_log_mgr=True)

        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]

        self.assertIsInstance(handler, logging.FileHandler)


class ArgparseAppRegisterFlagsTest(unittest.TestCase):

    def setUp(self):
        os.environ['COLUMNS'] = '60'
        os.environ['ROWS'] = '24'

        self.my_app = app.ArgparseApp()
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()

    def test_global_flags(self):

        self.my_app.register_global_flags([flags_one, flags_two])

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            self.my_app.parser.parse_args(['-h'])

        expected = inspect.cleandoc(
            r"""usage:.*\[-h\] \[--foo\]

        Global flags:
          -h, --help
          --foo *Enable foo-ing.

        """)
        self.assertRegex(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_shared_flags(self):

        self.my_app.register_shared_flags([flags_one, flags_two])

        self.assertIn('foo', self.my_app._shared_parsers)  # pylint: disable=protected-access

        self.assertRaisesRegex(
            Exception, 'called again', self.my_app.register_shared_flags,
            [flags_one, flags_two])


class ArgparseAppRegisterCommandsTest(unittest.TestCase):

    def setUp(self):
        os.environ['COLUMNS'] = '60'
        os.environ['ROWS'] = '24'

        self.my_app = app.ArgparseApp()
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()

        self.my_app.register_shared_flags([flags_one, flags_two])
        self.my_app.register_commands([flags_one, flags_two])

    def test_dash_h_commands(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
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
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_generate_report_dash_h(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            self.my_app.parser.parse_args(['generate-report', '-h'])

        expected = inspect.cleandoc(
            r"""usage: .* generate-report \[-h\]

            options:
              -h, --help  show this help message and exit

            """)

        self.assertRegex(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_put_on_hat_dash_h(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
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
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_remove_shoes_dash_h(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
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
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_ingest_dash_h(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
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
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_process_dash_h(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            self.my_app.parser.parse_args(['process', '-h'])

        expected = inspect.cleandoc(
            r"""usage: .* process \[-h\]

            Process random data.

            options:
              -h, --help  show this help message and exit

            """)
        self.assertRegex(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_dance_dash_h(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
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
        self.assertEqual(self.stderr.getvalue(), '')
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


class ArgparseAppRunCommandTest(unittest.TestCase):

    def setUp(self):
        os.environ['COLUMNS'] = '60'
        os.environ['ROWS'] = '24'

        self.my_app = app.ArgparseApp()
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()

        self.my_app.register_shared_flags([flags_one, flags_two])
        self.my_app.register_commands([flags_one, flags_two])

    def test_no_command_with_defaults(self):
        with contextlib.redirect_stdout(
                self.stdout), contextlib.redirect_stderr(self.stderr):
            retcode = self.my_app.run([])

        expected = inspect.cleandoc(
            r"""usage:.*\[-h\] <command> ...

            Global flags:
              -h, --help

            Commands:
              For more details: .* <command> --help

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
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(retcode, os.EX_USAGE)

    def test_no_command_with_fallback(self):

        def fallback(args):
            print('fallback was called')
            return 42

        self.my_app.parser.set_defaults(func=fallback)

        with contextlib.redirect_stdout(
                self.stdout), contextlib.redirect_stderr(self.stderr):
            retcode = self.my_app.run([])

        self.assertEqual(self.stdout.getvalue(), 'fallback was called\n')
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(retcode, 42)

    def test_fallback_with_dash_h(self):

        def fallback(args):  # pragma: no cover
            print('fallback was called')
            return 42

        self.my_app.parser.set_defaults(func=fallback)

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            self.my_app.run(['-h'])

        expected = inspect.cleandoc(
            r"""usage:.*\[-h\] <command> ...

            Global flags:
              -h, --help

            Commands:
              For more details: .* <command> --help

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
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_bogus_command_with_defaults(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            sys.exit(self.my_app.run(['bogus-command']))

        expected = inspect.cleandoc(
            r"""usage:.*\[-h\] <command> ...
            .*: argument <command>: invalid choice: 'bogus-command'

            """)
        self.assertEqual(self.stdout.getvalue(), '')
        self.assertRegex(self.stderr.getvalue(), expected)
        self.assertEqual(result.exception.code, 2)

    def test_bogus_command_with_fallback(self):

        def fallback(args):  # pragma: no cover
            print('fallback was called')
            return 42

        self.my_app.parser.set_defaults(func=fallback)

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            sys.exit(self.my_app.run(['bogosity']))

        expected = inspect.cleandoc(
            r"""usage:.*\[-h\] <command> ...
            .*: error: argument <command>: invalid choice: 'bogosity' \(choo.*

            """)
        self.assertEqual(self.stdout.getvalue(), '')
        self.assertRegex(self.stderr.getvalue(), expected)
        self.assertEqual(result.exception.code, 2)

    def test_generate_report(self):

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            sys.exit(self.my_app.run(['generate-report']))

        expected = 'generating report using generate-report\n'
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, None)

    def test_remove_shoes(self):

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            sys.exit(self.my_app.run(['remove-shoes']))

        expected = 'removing shoes because remove-shoes\n'
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 3)

    def test_ingest_new_material(self):

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            sys.exit(self.my_app.run(['ingest-new-material', '-f', 'blah']))

        expected = 'ingesting material from blah\n'
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 5)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
