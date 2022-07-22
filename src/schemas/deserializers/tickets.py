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
        validate=validate.OneOf(("low", "high")),
        allow_none=True,
        load_default=None,
        metadata={"description": "define a higher or lower ticket priority"},
    )


class CreateTicketSchemaAttachments(CreateTicketSchema):
    attachments = fields.List(
        fields.Raw(metadata={"type": "file"}),
        allow_none=False,
        load_default=[],
        metadata={"description": "files to attach"},
    )


class CreateTicketCommentSchema(Schema):
    body = fields.String(
        required=True,
        metadata={"description": "the content of the ticket", "example": ""},
        validate=validate.Length(min=5),
    )
    author = fields.Email(
        required=True, metadata={"description": "ticket author email", "example": ""}
    )


class CreateTicketCommentAttachmentsSchema(CreateTicketCommentSchema):
    attachments = fields.List(
        fields.Raw(metadata={"type": "file"}),
        allow_none=False,
        load_default=[],
        metadata={"description": "files to attach"},
    )


class TicketSearchCriteriaSchema(Schema):
    boards = fields.List(
        fields.String(validate=validate.OneOf(JiraSvc.supported_board_keys())),
        metadata={"description": "boards to fetch tickets from"},
    )
    categories = fields.List(
        fields.String(validate=validate.OneOf(JiraSvc.supported_categories())),
        metadata={"description": "categories the tickets belongs to"},
    )
    reporter = fields.Email(metadata={"description": "ticket reporter email"})
    assignee = fields.Email(
        metadata={"description": "user whose ticket is assigned to"}
    )
    status = fields.String(
        metadata={"description": "name of the current ticket status"}
    )
    watcher = fields.Email(metadata={"description": "tickets user has subscribed to"})
    q = fields.String(metadata={"description": "search for text occurrences"})
    fields_ = fields.List(
        fields.String(validate=validate.OneOf(JiraSvc.supported_fields())),
        data_key="fields",
        metadata={"description": "additional fields to include in the results"},
    )
    limit = fields.Integer(
        load_default=20, metadata={"description": "tickets user has subscribed to"}
    )
    sort = fields.String(
        validate=validate.OneOf(["created"]),
        load_default="created",
        metadata={"description": "sort tickets by"},
    )
