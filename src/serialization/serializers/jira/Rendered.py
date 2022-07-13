from marshmallow import Schema, fields

from src.serialization.serializers.jira.Comment import CommentSchema


class RenderedSchema(Schema):
    body = (fields.String(attribute="description"),)
    comments = fields.List(fields.Nested(CommentSchema), attribute="comment.comments")
