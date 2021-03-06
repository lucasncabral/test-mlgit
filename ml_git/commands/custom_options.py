"""
© Copyright 2020-2021 HP Development Company, L.P.
SPDX-License-Identifier: GPL-2.0-only
"""

from click import Option, UsageError, MissingParameter, Command

from ml_git import log
from ml_git.ml_git_message import output_messages


class MutuallyExclusiveOption(Option):
    def __init__(self, *args, **kwargs):
        self.mutually_exclusive = set(kwargs.pop('mutually_exclusive', []))
        help = kwargs.get('help', '')
        if self.mutually_exclusive:
            ex_str = ', '.join(self.mutually_exclusive)
            kwargs['help'] = help + (
                    ' NOTE: Mutually exclusive with'
                    ' argument: ' + ex_str + '.'
            )
        super(MutuallyExclusiveOption, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise UsageError(
                'The argument `{}` is mutually exclusive with '
                'argument `{}`.'.format(
                    self.name,
                    ', '.join(self.mutually_exclusive)
                )
            )

        return super(MutuallyExclusiveOption, self).handle_parse_result(
            ctx,
            opts,
            args
        )


class OptionRequiredIf(Option):
    def __init__(self, *args, **kwargs):
        self.required_option = set(kwargs.pop('required_option', []))
        help = kwargs.get('help', '')
        if self.required_option:
            ex_str = ', '.join(self.required_option)
            kwargs['help'] = help + (' NOTE: This option is required if --' + ex_str + ' is used.')
        super(OptionRequiredIf, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        using_required_option = self.name in opts
        using_dependent_options = all(opt.replace('-', '_') in opts for opt in self.required_option)
        if not using_required_option and using_dependent_options:
            msg = output_messages['ERROR_REQUIRED_OPTION_MISSING'].format(self.name, ', '.join(self.required_option))
            raise MissingParameter(ctx=ctx, param=self, message=msg)
        elif using_required_option and not using_dependent_options:
            option_name = self.name.replace('_', '-')
            log.warn(output_messages['WARN_USELESS_OPTION'].format(option_name, ', '.join(self.required_option)))
        return super(OptionRequiredIf, self).handle_parse_result(ctx, opts, args)


class DeprecatedOption(Option):
    def __init__(self, *args, **kwargs):
        self.deprecated = kwargs.pop('deprecated', ())
        self.preferred = kwargs.pop('preferred', args[0][-1])
        help = kwargs.get('help', '')
        if self.deprecated:
            kwargs['help'] = help + (' [DEPRECATED:' + self.deprecated[0] + ']')
        super(DeprecatedOption, self).__init__(*args, **kwargs)


class DeprecatedOptionsCommand(Command):
    def make_parser(self, ctx):
        parser = super(DeprecatedOptionsCommand, self).make_parser(ctx)
        # get the parser options
        options = set(parser._short_opt.values())
        options |= set(parser._long_opt.values())

        for option in options:
            if not isinstance(option.obj, DeprecatedOption):
                continue

            def make_process(an_option):
                orig_process = an_option.process
                deprecated = getattr(an_option.obj, 'deprecated', None)
                preferred = getattr(an_option.obj, 'preferred', None)
                msg = "Expected `deprecated` value for `{}`"
                assert deprecated is not None, msg.format(an_option.obj.name)

                def process(value, state):
                    import inspect
                    frame = inspect.currentframe()
                    try:
                        opt = frame.f_back.f_locals.get('opt')
                    finally:
                        del frame
                    if opt in deprecated:
                        msg = "'{}' has been deprecated, use '{}' instead;"
                        log.warn(msg.format(opt, preferred))
                    return orig_process(value, state)
                return process
            option.process = make_process(option)
        return parser
