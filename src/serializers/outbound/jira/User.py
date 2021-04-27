from marshmallow import Schema, fields


class UserSchema(Schema):
    account = fields.String(attribute='accountId')
    avatar = fields.String(attribute='avatarUrls.16x16')
    name = fields.String(attribute='displayName')
    email = fields.String(attribute='emailAddress')
    created = fields.String()
