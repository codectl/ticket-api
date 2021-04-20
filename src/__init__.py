from flasgger import Swagger
from flask_caching import Cache
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy

# SQLite database
db = SQLAlchemy()

# Initialize Cache
cache = Cache()

# initialize Flask Restful
api = Api()

# Swagger properties
swagger = Swagger(config={
    'openapi': '3.0.0',
    'info': {
        'title': "Ticket manager service",
        'description': "Service to manage tickets and Jira integration.",
        'version': '1.0.0'
    },
    'specs': [
        {
            'endpoint': 'swagger',
            'route': '/swagger.json',
            'rule_filter': lambda rule: True,
            'model_filter': lambda tag: True
        }
    ],

    # hide the Swagger top bar
    'hide_top_bar': True,

    # where to find the docs
    'specs_route': '/api/tickets/',

    # OAS3 fields
    'servers': [
        {
            'url': 'http://localhost:5000/api/tickets',
        }
    ]
}, merge=True, template={
    'basePath': '/api/tickets'
})
