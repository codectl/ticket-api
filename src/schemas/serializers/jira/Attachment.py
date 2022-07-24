from marshmallow import Schema, fields

from src.schemas.serializers.jira.User import UserSchema


class AttachmentSchema(Schema):
    filename = fields.String()
    content = fields.String()
    mimetype = fields.String(attribute="mimeType")
    size = fields.Integer()
    author = fields.Nested(UserSchema)
    created = fields.String()
    thumbnail = fields.String()
