from flasgger import Swagger
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy

# monkey patching to handle Flask upgrade
# to remove once flask-restful gets updated
import flask.scaffold
flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func
from flask_restful import Api


# SQLite database
db = SQLAlchemy()

# Initialize Cache
cache = Cache()

# initialize Flask Restful
api = Api()

# initialize swagger
swagger = Swagger()
