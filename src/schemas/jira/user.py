from flask_restplus import fields

from src import api


user = api.model('jira-user', {
    'account': fields.String(attribute='accountId'),
    'avatar': fields.String(attribute=lambda x: x.get('avatarUrls', {}).get('16x16')),
    'name': fields.String(attribute='displayName'),
    'email': fields.String(attribute='emailAddress'),
})
