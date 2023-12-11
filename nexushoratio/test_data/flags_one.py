"""Registers a global flag."""


def nh_global_flags(an_app):
    an_app.global_flags.add_argument(
        '--foo', action='store_true', help='Enable foo-ing.')
