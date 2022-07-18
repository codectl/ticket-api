from marshmallow import Schema, fields, validate

from src.services.jira import JiraSvc


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
