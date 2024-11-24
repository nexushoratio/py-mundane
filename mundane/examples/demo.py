"""This is a simple demo.

This docstring is ignored for this demo.
"""

# This allows the TYPE_CHECKING guarded argparse.Namespace to work.
from __future__ import annotations

import sys
import typing

from mundane import app

# This modules is only needed for static type checking in this demo.
if typing.TYPE_CHECKING:
    import argparse


def demo(args: argparse.Namespace) -> int:
    """This is a simple demo.

    This docstring provides some top-level information about the application.
    """
    print('demo was called')

    # Process the flags directly.
    print(f'{args.bee=}')
    print(f'{args.see=}')

    # Or as a dictionary.
    print(vars(args))

    # Success!
    return 0


def main() -> int:
    my_app = app.ArgparseApp(use_docstring_for_description=demo)

    # This is necessary since this application has no subcommands.
    my_app.parser.set_defaults(func=demo)

    # Works, but atypical for mundane apps.
    my_app.parser.add_argument('-b', '--bee', help='That which stings.')

    # The traditional way for mundane apps.
    my_app.global_flags.add_argument('-c', '--see', help='Open the eyes.')

    sys.exit(my_app.run())


if __name__ == '__main__':
    main()
