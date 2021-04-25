from marshmallow import fields, Schema


class HttpErrorSchema(Schema):
    code = fields.Int()
    message = fields.String()
