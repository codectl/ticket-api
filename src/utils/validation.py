# Utility methods for validations

import re


def is_email(value):
    """
    Check if given value is an email.

    @returns True: if is an email.
             False: otherwise.
    """
    regex = r'[^@]+@[^@]+\.[^@]+'
    return re.match(regex, value)
