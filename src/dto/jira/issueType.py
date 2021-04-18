from flask_restplus import fields

from src import api


issue_type = api.model('jira-issue-type', {
    'name': fields.String(attribute='name'),
    'icon': fields.String(attribute='iconUrl')
})
