"""Yes global flag, no shared flags, yes commands."""


def nh_global_flags(an_app):
    an_app.global_flags.add_argument(
        '--foo', action='store_true', help='Enable foo-ing.')


def nh_commands(an_app: 'mundane.ArgparserApp'):
    """Register all module commands."""
    parser = an_app.register_command(generate_report)

    foo_flags = an_app.get_shared_parser('foo')
    an_app.register_command(put_on_hat, parents=[foo_flags])

    shoes_description = """This is also a custom description.

    Built by hand."""
    an_app.register_command(
        remove_shoes,
        help='Shoes have custom help.',
        description=shoes_description)


# Purposefully no docstring for testing.
def generate_report(args: 'argparse.Namespace') -> int:
    print('generating report using', args)


# Purposefully no docstring for testing.
def put_on_hat(args: 'argparse.Namespace') -> int:
    print('putting on a hat with', args)


def remove_shoes(args: 'argparse.Namespace') -> int:
    """This will remove the shoes from the brakes."""
    print('removing shoes because', args)
