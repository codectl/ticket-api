from flask_restplus import fields

from src import api


status = api.model('jira-status', {
    'name': fields.String(attribute=lambda x: x['statusCategory']['name']),
    'key': fields.String(attribute=lambda x: x['statusCategory']['key']),
    'color-name': fields.String(attribute=lambda x: x['statusCategory']['colorName'])
})
