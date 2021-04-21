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
    'openapi': '3.0.2',
    'info': {
        'title': "Ticket manager service",
        'description': "Service to manage tickets and Jira integration.",
        'version': '1.0.0'
    },
}, merge=True, template={
    'basePath': '/api/tickets'
})
