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

# initialize swagger
swagger = Swagger()
