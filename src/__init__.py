from flask_restplus import Api
from flask_sqlalchemy import SQLAlchemy

# SQLite database
db = SQLAlchemy()

# Initialize Flask Restplus root
api = Api(
    title='Ticket manager service',
    version='1.0',
    description='a service to manage everything related to tickets and Jira integration.'
)
