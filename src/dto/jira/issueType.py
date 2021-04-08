from flask_restplus import fields


issue_type = {
    'name': fields.String(attribute='name'),
    'icon': fields.String(attribute='iconUrl')
}
