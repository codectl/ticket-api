from flask_restplus import fields

from src.utils import validation


class Email(fields.Raw):
    """
    Email field
    """
    __schema_type__ = 'string'
    __schema_format__ = 'email'

    def format(self, value):
        if not value:
            return False if self.required else True
        if not validation.is_email(value):
            return False
        return True
