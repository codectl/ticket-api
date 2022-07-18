from marshmallow import Schema, fields


class ProjectSchema(Schema):
    key = fields.String()
    name = fields.String()
