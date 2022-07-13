from marshmallow import Schema, fields


class IssueTypeSchema(Schema):
    name = fields.String()
    icon = fields.String(attribute="iconUrl")
