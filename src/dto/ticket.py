from flask_restplus import fields

from src import api
from src.dto.jira.issue import issue
from src.models.jira.Board import Board
from src.services.jira import JiraService

ro_fields = api.model('ticket-ro', {
    'category': fields.String,
    'created-at': fields.String(attribute='created_at', description='creation date', readonly=True),
    'updated-at': fields.String(attribute='updated_at', description='last update', readonly=True),
    'reporter': fields.String(description='user reporter', required=True),
    'jira': fields.Nested(issue, description='additional Jira data', readonly=True)
})

rw_fields = api.inherit('ticket-rw', ro_fields, {
    'title': fields.String(required=True),
    'description': fields.String(required=True),
    'board': fields.String(
        enum=JiraService.supported_board_keys(),
        example=Board.default().key,
        default=Board.default().key,
        required=True
    ),
    'priority': fields.String(enum=['low', 'high']),
})
