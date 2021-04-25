from marshmallow import fields, Schema

from src import swagger


class TestSchema(Schema):
    code = fields.Int()
    message = fields.String()
