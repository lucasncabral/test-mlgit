"""
© Copyright 2022 HP Development Company, L.P.
SPDX-License-Identifier: GPL-2.0-only
"""

import click

from ml_git.commands.prompt_msg import EMPTY_FOR_NONE
from ml_git.config import merged_config_load

WIZARD_ENABLE_KEY = 'wizard_enable'


def check_empty_for_none(value):
    return value if value != EMPTY_FOR_NONE else None


def is_field_present(field):
    return True if field else False


def request_new_value(input_message):
    field_value = click.prompt(input_message, default=EMPTY_FOR_NONE, show_default=False)
    return field_value


def request_user_confirmation(confimation_message):
    should_continue = click.confirm(confimation_message, default=False, abort=True)
    return should_continue


def abort_click_execution(context):
    context.exit()


def wizard_for_field(context, field, input_message):
    config_file = merged_config_load()
    if is_field_present(field) or (WIZARD_ENABLE_KEY in config_file and not config_file[WIZARD_ENABLE_KEY]):
        return field
    else:
        try:
            new_field = check_empty_for_none(request_new_value(input_message))
            return new_field
        except Exception:
            abort_click_execution(context)
