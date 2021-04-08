from flask_restplus import fields

from src import api
from src.dto.jira.issue import issue


ticket = api.model('ticket', {
    'category': fields.String(description='category'),
    'created-at': fields.String(attribute='created_at', description='created at'),
    'updated-at': fields.String(attribute='updated_at', description='updated at'),
    'reporter': fields.String(description='user reporter'),
    'jira': fields.Nested(issue)
})
