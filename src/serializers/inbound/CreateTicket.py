from flask import current_app
from marshmallow import Schema, fields, validate

from src.models.jira.Board import Board
from src.services.jira import JiraService


class CreateTicketSchema(Schema):
    title = fields.String(
        required=True,
        metadata=dict(
            description='an intuitive title for the ticket',
            example=''
        ),
        validate=validate.Length(min=5)
    )
    body = fields.String(
        required=True,
        metadata=dict(
            description='the content of the ticket',
            example=''
        ),
        validate=validate.Length(min=5)
    )
    reporter = fields.Email(
        required=True,
        metadata=dict(
            description='ticket reporter email',
            example=''
        )
    )
    board = fields.String(
        validate=validate.OneOf(JiraService.supported_board_keys()),
        metadata=dict(
            description='boards to fetch tickets from',
            default=Board.default().key
        ),
        required=True
    )
    category = fields.String(
        validate=validate.OneOf(JiraService.supported_categories()),
        metadata=dict(
            description='category the ticket belongs to',
            default=current_app.config['JIRA_TICKET_LABEL_DEFAULT_CATEGORY']
        ),
        required=True
    )
    watchers = fields.List(
        fields.Email(),
        allow_none=True,
        missing=None,
        metadata=dict(
            description='tickets user has subscribed to',
            example=None
        )
    )
    priority = fields.String(
        validate=validate.OneOf(['low', 'high']),
        allow_none=True,
        missing=None,
        metadata=dict(
            description='define a higher or lower ticket priority',
            example=None
        )
    )
