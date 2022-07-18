from flask import current_app
from marshmallow import Schema, fields, validate

from src.services.jira import JiraSvc


class CreateTicketSchema(Schema):
    title = fields.String(
        required=True,
        metadata={"description": "an intuitive title for the ticket", "example": ""},
        validate=validate.Length(min=5),
    )
    body = fields.String(
        required=True,
        metadata={"description": "the content of the ticket", "example": ""},
        validate=validate.Length(min=5),
    )
    reporter = fields.Email(
        required=True, metadata={"description": "ticket reporter email", "example": ""}
    )
    board = fields.String(
        required=True,
        metadata={
            "description": "boards to fetch tickets from",
            "default": JiraSvc.default_board(),
        },
        validate=validate.OneOf(b.key for b in JiraSvc().boards()),
    )
    category = fields.String(
        required=True,
        metadata={
            "description": "category the ticket belongs to",
            "default": current_app.config["JIRA_TICKET_LABEL_DEFAULT_CATEGORY"],
        },
        validate=validate.OneOf(JiraSvc.supported_categories()),
    )
    watchers = fields.List(
        fields.Email(),
        allow_none=False,
        load_default=[],
        metadata={"description": "users to be watching the ticket", "example": []},
    )
    priority = fields.String(
        validate=validate.OneOf(["low", "high"]),
        allow_none=True,
        load_default=None,
        metadata={"description": "define a higher or lower ticket priority"},
    )
