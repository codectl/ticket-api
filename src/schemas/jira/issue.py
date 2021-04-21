from marshmallow import Schema, fields
# from flask_restful import fields
from flasgger import Schema

from src import swagger
# from src.dto.jira.attachment import attachment
# from src.dto.jira.comment import comment, rendered_comment
# from src.dto.jira.project import project
# from src.dto.jira.issueType import issue_type
# from src.dto.jira.user import user
# from src.dto.jira.status import status


class Issue(Schema):
    id = fields.Int()


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
