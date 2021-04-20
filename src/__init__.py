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
    # 'openapi': '3.0.2',
    'info': {
        'title': "Ticket manager service",
        'description': "Service to manage tickets and Jira integration.",
        'version': '1.0.0'
    },
    'specs': [
        {
            'endpoint': 'apispec',
            'route': '/mysite.com/api.json',
            'rule_filter': lambda rule: True,
            'model_filter': lambda tag: True
        }
    ],
    'specs_route': '/api/tickets/',
    "host": "mysite.com"
}, merge=True, template={
    "basePath": "/api/tickets"
})
