"""Yes global flag, no shared flags, yes commands."""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:  # pragma: no cover
    import argparse

    from mundane import app


def mundane_global_flags(an_app: app.ArgparseApp):
    """Register global flags for the application."""
    an_app.global_flags.add_argument(
        '--foo', action='store_true', help='Enable foo-ing.'
    )
    an_app.register_after_parse_hook(check_foo)


def mundane_commands(an_app: app.ArgparseApp):
    """Register all module commands."""
    an_app.register_command(generate_report)

    foo_flags = an_app.get_shared_parser('foo')
    an_app.register_command(put_on_hat, parents=[foo_flags])

    shoes_description = """This is also a custom description.

    Built by hand."""
    an_app.register_command(
        remove_shoes,
        help='Shoes have custom help.',
        description=shoes_description
    )


def check_foo(args: argparse.Namespace) -> None:
    """See what args is up to."""
    args.checker = f'Foo was {args.foo}'


# Purposefully no docstring for testing.
# And ignoring return because that is also being tested.
def generate_report(args: argparse.Namespace) -> int:  # type: ignore[return]
    print('generating report using', args.name)


# Purposefully no docstring for testing.
# pylint: disable=missing-function-docstring
def put_on_hat(args: argparse.Namespace) -> int:  # pragma: no cover
    del args
    return 99


def remove_shoes(args: argparse.Namespace) -> int:
    """This will remove the shoes from the brakes."""
    print('removing shoes because', args.name)
    print('Also:', args.checker)
    return 3
