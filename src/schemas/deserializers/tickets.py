from flask import current_app
from marshmallow import Schema, fields, pre_load, validate, validates_schema

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
        required=True, metadata={"description": "boards to fetch tickets from"}
    )
    category = fields.String(
        required=True,
        metadata={"description": "category the ticket belongs to"},
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

    @validates_schema
    def lazy_validator(self, data, **_):
        svc = JiraSvc()
        validate.OneOf(choices=[b.key for b in svc.boards()])(data["board"])
        validate.OneOf(choices=svc.allowed_categories())(data["category"])
        return True

    @pre_load
    def lazy_loader(self, data, **_):
        default_board = JiraSvc.default_board()
        default_category = current_app.config["JIRA_TICKET_LABEL_DEFAULT_CATEGORY"]
        data["board"] = data.get("board", default_board)
        data["category"] = data.get("category", default_category)
        return data


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
        fields.String(),
        metadata={"description": "boards to fetch tickets from"},
    )
    categories = fields.List(
        fields.String(),
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
        fields.String(),
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

    @validates_schema
    def lazy_validator(self, data):
        validate.OneOf(choices=(b.key for b in JiraSvc.boards()))(data["boards"])
        validate.OneOf(choices=JiraSvc.allowed_fields())(data["fields"])
        validate.OneOf(choices=JiraSvc.allowed_categories())(data["category"])
        return True
