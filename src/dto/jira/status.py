from flask_restplus import fields

from src.dto.jira.user import user


status = {
    'name': fields.String(user, attribute=lambda x: x['statusCategory']['name']),
    'key': fields.String(user, attribute=lambda x: x['statusCategory']['key']),
    'color-name': fields.String(user, attribute=lambda x: x['statusCategory']['colorName'])
}
