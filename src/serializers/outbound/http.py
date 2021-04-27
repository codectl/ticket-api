from marshmallow import fields, Schema


class HttpErrorSchema(Schema):
    status = fields.Int()
    message = fields.String()
