from marshmallow import Schema, fields

from src.schemas.serializers.jira.Attachment import AttachmentSchema
from src.schemas.serializers.jira.Comment import CommentSchema
from src.schemas.serializers.jira.IssueType import IssueTypeSchema
from src.schemas.serializers.jira.Project import ProjectSchema
from src.schemas.serializers.jira.Rendered import RenderedSchema
from src.schemas.serializers.jira.Status import StatusSchema
from src.schemas.serializers.jira.User import UserSchema


class IssueSchema(Schema):
    id = fields.Integer()
    key = fields.String()
    title = fields.String(attribute="summary")
    body = fields.String(attribute="description")
    created = fields.String()
    assignee = fields.Nested(UserSchema)
    reporter = fields.Nested(UserSchema)
    status = fields.Nested(StatusSchema)
    labels = fields.List(fields.String())
    url = fields.Url()
    type = fields.Nested(IssueTypeSchema, attribute="issuetype")
    project = fields.Nested(ProjectSchema)
    comments = fields.List(fields.Nested(CommentSchema), attribute="comment.comments")
    attachments = fields.List(fields.Nested(AttachmentSchema), attribute="attachment")
    watchers = fields.List(fields.Nested(UserSchema))
    rendered = fields.Nested(RenderedSchema)
