from flask_restplus import fields

from src.dto.jira.project import project
from src.dto.jira.issueType import issue_type
from src.dto.jira.user import user
from src.dto.jira.status import status


issue = {
    'id': fields.Integer,
    'title': fields.String(attribute=lambda x: x.raw['fields']['summary']),
    'description': fields.String(attribute=lambda x: x.raw['fields']['description']),
    'assignee': fields.Nested(user, attribute=lambda x: x.raw['fields']['assignee'], allow_null=True),
    'reporter': fields.Nested(user, attribute=lambda x: x.raw['fields']['reporter'], allow_null=True),
    'status': fields.Nested(status, attribute=lambda x: x.raw['fields']['status']),
    'type': fields.Nested(issue_type, attribute=lambda x: x.raw['fields']['issueType']),
    'project': fields.Nested(project, attribute=lambda x: x.raw['fields']['project'])
}
