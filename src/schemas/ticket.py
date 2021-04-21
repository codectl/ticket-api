from flask import current_app
from flask_restplus import fields

from src import api
from src.schemas.fields.Email import Email
from src.models.jira.Board import Board
from src.services.jira import JiraService


ticket = api.model('ticket', {
    'title': fields.String(required=True, example='example'),
    'body': fields.String(required=True, example='...'),
    'reporter': Email(description='user reporter', required=True),
    'board': fields.String(
        enum=JiraService.supported_board_keys(),
        example=Board.default().key,
        default=Board.default().key,
    ),
    'category': fields.String(
        description='category that the ticket belongs to',
        enum=JiraService.supported_categories(),
        example=current_app.config['JIRA_TICKET_LABEL_DEFAULT_CATEGORY'],
        default=current_app.config['JIRA_TICKET_LABEL_DEFAULT_CATEGORY']
    ),
    'watchers': fields.List(Email, example='None'),
    'priority': fields.String(enum=['low', 'high'], example='None')
})
