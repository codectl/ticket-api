from marshmallow import Schema, fields


class StatusSchema(Schema):
    name = fields.String(attribute="statusCategory.name")
    key = fields.String(attribute="statusCategory.key")
    color_name = fields.String(
        attribute="statusCategory.colorName", data_key="color-name"
    )
