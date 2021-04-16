from flask_restplus import fields

from src import api
from src.dto.jira.comment import comment
from src.dto.jira.project import project
from src.dto.jira.issueType import issue_type
from src.dto.jira.user import user
from src.dto.jira.status import status


issue = api.model('jira-issue', {
    'id': fields.Integer,
    'key': fields.String,
    'title': fields.String(attribute='summary'),
    'body': fields.String(attribute='description'),
    'url': fields.Url,
    'assignee': fields.Nested(user, attribute='assignee', allow_null=True),
    'reporter': fields.Nested(user, attribute='reporter', allow_null=True),
    'status': fields.Nested(status, attribute='status'),
    'labels': fields.List(fields.String, attribute='labels'),
    'comments': fields.List(fields.Nested(comment), attribute=lambda x: x['comment']['comments'], allow_null=True),
    'watchers': fields.List(fields.Nested(user, attribute='watchers', allow_null=True)),
    'type': fields.Nested(issue_type, attribute='issuetype'),
    'project': fields.Nested(project, attribute='project')
})
