from flask_restplus import fields

from src import api


project = api.model('jira-project', {
    'key': fields.String,
    'name': fields.String
})
