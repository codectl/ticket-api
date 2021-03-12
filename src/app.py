import os

from dotenv import load_dotenv
from flask import Flask, Blueprint

from src import api, db
from src.namespaces.service.index import service
from src.settings.config import config_by_name


def create_app(config_name=None):
    """
    Create a new app.
    """

    # Define the WSGI application object
    app = Flask(__name__)

    # Load .env and variables
    load_dotenv()

    # Load object-based default configuration
    env = os.getenv('FLASK_ENV', config_name)
    app.config.from_object(config_by_name[env])

    setup_app(app)

    return app


def setup_app(app):
    """
    Setup the app
    """

    # Link db to app
    db.init_app(app)

    # Create tables if they do not exist already
    with app.app_context():
        db.create_all()

    # Initialize root blueprint
    root = Blueprint('api', __name__, url_prefix=app.config['APPLICATION_CONTEXT'])

    # Link api to blueprint
    api.init_app(root)

    # Register blueprints
    app.register_blueprint(root)

    # Register namespaces
    api.add_namespace(service)
