from marshmallow import fields, Schema


class HttpResponseSchema(Schema):
    code = fields.Int()
    reason = fields.String()
    message = fields.String()
