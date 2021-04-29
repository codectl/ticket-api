from flask import current_app
from marshmallow import Schema, fields, validate

from src.models.jira.Board import Board
from src.services.jira import JiraService


class CreateTicketSchema(Schema):
    title = fields.String(
        required=True,
        metadata=dict(example=''),
        validate=validate.Length(min=5)
    )
    body = fields.String(
        required=True,
        metadata=dict(example=''),
        validate=validate.Length(min=5)
    )
    reporter = fields.Email(required=True, metadata=dict(example=''))
    board = fields.String(
        validate=validate.OneOf(JiraService.supported_board_keys()),
        metadata=dict(default=Board.default().key),
        required=True
    )
    category = fields.String(
        validate=validate.OneOf(JiraService.supported_categories()),
        metadata=dict(default=current_app.config['JIRA_TICKET_LABEL_DEFAULT_CATEGORY']),
        required=True
    )
    watchers = fields.List(
        fields.Email(),
        allow_none=True,
        missing=None,
        metadata=dict(example=None)
    )
    priority = fields.String(
        validate=validate.OneOf(['low', 'high']),
        allow_none=True,
        missing=None,
        metadata=dict(example=None)
    )
