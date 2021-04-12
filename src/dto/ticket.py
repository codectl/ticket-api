from flask_restplus import fields

from src import api
from src.dto.fields.Email import Email
from src.dto.jira.issue import issue
from src.models.jira.Board import Board
from src.services.jira import JiraService

ro_fields = api.model('ticket-ro', {
    'created-at': fields.String(attribute='created_at', description='creation date', readonly=True),
    'updated-at': fields.String(attribute='updated_at', description='last update', readonly=True),
    'reporter': Email(description='user reporter', required=True),
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
    'watchers': fields.List(Email),
    'priority': fields.String(enum=['low', 'high'])
})
