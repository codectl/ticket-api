from marshmallow import Schema, fields

from src.serializers.outbound.jira.Status import StatusSchema
from src.serializers.outbound.jira.User import UserSchema
# from src.dto.jira.comment import comment, rendered_comment
# from src.dto.jira.project import project
# from src.dto.jira.issueType import issue_type
# from src.dto.jira.user import user
# from src.dto.jira.status import status


class IssueSchema(Schema):
    id = fields.Integer()
    key = fields.String()
    title = fields.String(attribute='summary')
    body = fields.String(attribute='description')
    created = fields.String()
    assignee = fields.Nested(UserSchema)
    reporter = fields.Nested(UserSchema)
    status = fields.Nested(StatusSchema)
    labels = fields.List(fields.String())

    # updated = fields.DateTime()


# issue = api.model('jira-issue', {
#     'id': fields.Integer,
#     'key': fields.String,
#     'title': fields.String(attribute='summary'),
#     'body': fields.String(attribute='description'),
#     'created': fields.DateTime,
#     'updated': fields.DateTime,
    # 'assignee': fields.Nested(user, attribute='assignee', allow_null=True),
    # 'reporter': fields.Nested(user, attribute='reporter'),
    # 'status': fields.Nested(status, attribute='status'),
    # 'labels': fields.List(fields.String, attribute='labels'),
    # 'url': fields.String,
    # 'type': fields.Nested(issue_type, attribute='issuetype'),
    # 'project': fields.Nested(project, attribute='project'),
    # 'comments': fields.List(
    #     fields.Nested(comment),
    #     attribute=lambda x: x.get('comment', {}).get('comments'),
    #     allow_null=True
    # ),
    # 'attachments': fields.List(fields.Nested(attachment), attribute='attachment'),
    # 'watchers': fields.List(fields.Nested(user)),
    # 'rendered': fields.Nested(api.model('jira-rendered', {
    #     'body': fields.String(attribute='description'),
    #     'comments': fields.List(
    #         fields.Nested(rendered_comment),
    #         attribute=lambda x: x.get('comment', {}).get('comments'),
    #         allow_null=True
    #     )
    # }), allow_null=True)
# })
