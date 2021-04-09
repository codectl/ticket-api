from flask_restplus import fields

from src import api
from src.dto.jira.issue import issue

ro_fields = api.model('ticket-ro', {
    'category': fields.String(description='category'),
    'created-at': fields.String(attribute='created_at', description='created at', readonly=True),
    'updated-at': fields.String(attribute='updated_at', description='updated at', readonly=True),
    'reporter': fields.String(description='user reporter'),
    'jira': fields.Nested(issue, readonly=True)
})

rw_fields = api.inherit('ticket-rw', ro_fields, {
    'title': fields.String(description='ticket title'),
    'description': fields.String(description='ticket description'),
})
