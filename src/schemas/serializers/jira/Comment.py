from marshmallow import Schema, fields

from src.serialization.serializers.jira.User import UserSchema


class CommentSchema(Schema):
    author = fields.Nested(UserSchema)
    body = fields.String()
    created = fields.String()
    updated = fields.String()
