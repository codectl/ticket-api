from marshmallow import Schema, fields

from src.serializers.outbound.jira.User import UserSchema


class CommentSchema(Schema):
    author = fields.Nested(UserSchema)
    body = fields.String()
    created = fields.String()
    updated = fields.String()
