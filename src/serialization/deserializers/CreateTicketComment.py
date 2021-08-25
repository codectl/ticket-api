from marshmallow import Schema, fields, validate


class CreateTicketCommentSchema(Schema):
    body = fields.String(
        required=True,
        metadata=dict(
            description='the content of the ticket',
            example=''
        ),
        validate=validate.Length(min=5)
    )
    author = fields.Email(
        required=True,
        metadata=dict(
            description='ticket author email',
            example=''
        )
    )
