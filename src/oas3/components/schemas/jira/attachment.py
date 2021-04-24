from flask_restplus import fields

from src import api
from src.oas3.components import user

attachment = api.model('jira-attachment', {
    'filename': fields.String,
    'content': fields.String,
    'mimetype': fields.String(attribute='mimeType'),
    'size': fields.Integer,
    'author': fields.Nested(user),
    'created': fields.DateTime,
    'thumbnail': fields.String,
})
