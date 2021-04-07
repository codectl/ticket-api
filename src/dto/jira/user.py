from flask_restplus import fields


user = {
    'id': fields.String(attribute='accountId'),
    'avatar': fields.String(attribute=lambda x: x['avatarUrls']['16x16']),
    'display-name': fields.String(attribute='displayName'),
    'email': fields.String(attribute='emailAddress'),
}
