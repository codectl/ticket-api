from flask_caching import Cache
from flask_restplus import Api
from flask_sqlalchemy import SQLAlchemy
from jsonschema import FormatChecker

# SQLite database
db = SQLAlchemy()

# Initialize Cache
cache = Cache()

# initialize Flask Restplus root
api = Api(
    title='Ticket manager service',
    version='1.0',
    description='a service to manage everything related to tickets and Jira integration.',
    format_checker=FormatChecker(formats=['email', 'date'])
)
