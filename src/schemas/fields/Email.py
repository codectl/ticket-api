from flask_restplus import fields


class Email(fields.Raw):
    """
    Email field
    """
    __schema_type__ = 'string'
    __schema_format__ = 'email'
