from marshmallow import fields, Schema


class ErrorSchema(Schema):
    code = fields.String()
    message = fields.String()
