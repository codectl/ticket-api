from marshmallow import fields, Schema


class TokenSchema(Schema):
    token_type = fields.String()
    access_token = fields.String()
    refresh_token = fields.String()
    expires_in = fields.Integer()
    ext_expires_in = fields.Integer()
    expires_at = fields.Float()
    active = fields.Boolean()
