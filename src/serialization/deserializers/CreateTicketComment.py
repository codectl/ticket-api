from marshmallow import Schema, fields, validate


class CreateTicketCommentSchema(Schema):
    body = fields.String(
        required=True,
        metadata={"description": "the content of the ticket", "example": ""},
        validate=validate.Length(min=5),
    )
    author = fields.Email(
        required=True, metadata={"description": "ticket author email", "example": ""}
    )
