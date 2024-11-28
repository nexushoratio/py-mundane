"""No global flag, no shared flags, yes commands (with sub)."""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:  # pragma: no cover
    import argparse

    from mundane import app


def mundane_commands(an_app: app.ArgparseApp):
    """Register all module commands."""
    parser = an_app.register_command(sub)
    subparser = an_app.new_subparser(parser)

    parser.set_defaults(func=lambda x, y=parser: _hero(x, y))

    an_app.register_command(atomic, subparser=subparser)
    an_app.register_command(class_, subparser=subparser, name='class')
    parser = an_app.register_command(marine, subparser=subparser)
    an_app.register_command(routine, subparser=subparser)

    subparser = an_app.new_subparser(parser)
    parser = an_app.register_command(change_depth, subparser=subparser)
    parser.add_argument(
        '--rate',
        action='store',
        required=True,
        type=int,
        help='The rate of change in meters/second.')
    parser.add_argument(
        '--depth',
        action='store',
        default=0,
        type=int,
        help='Cruising depth in meters. (default: %(default)d)')
    an_app.register_command(fire, subparser=subparser)


def _hero(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    """A wrapper so sub can be handed a parser.

    Using set_defaults() to set `.parser` does not work because it will set it
    for all nested parsers.
    """
    args.parser = parser
    return sub(args)


def sub(args: argparse.Namespace) -> int:
    """A subcommand for wrapping other subcommands."""
    args.parser.print_help()

    return 1


def atomic(args: argparse.Namespace) -> int:
    """A small feature."""
    print('I am a particle that makes up elements.')

    del args
    return 0


def marine(args: argparse.Namespace) -> int:
    """A boat that can do interesting things."""

    print('This boat can go underwater and fire weapons.')

    del args
    return 0


def change_depth(args: argparse.Namespace) -> int:
    """Move to a new depth."""

    print(
        f'The boat will go to a depth of {args.depth} meters'
        f' at {args.rate} m/s.')

    return 0


def fire(args: argparse.Namespace) -> int:
    """Fire a weapon."""

    print(f'Torpedoes away!  Also, {args.foo=}.')

    return 0


def routine(args: argparse.Namespace) -> int:
    """A procedure to call."""
    del args

    print('A sub routine was called.')

    return 0


def class_(args: argparse.Namespace) -> int:
    """Deriving from a super."""
    del args

    print('Derivation achieved.')

    return 0
