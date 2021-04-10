import logging
import os

from dotenv import load_dotenv
from flask import Flask, Blueprint

from src import api, db
from src.cli.o365 import o365_cli
from src.settings.config import config_by_name


def create_app(config_name=None):
    """
    Create a new app.
    """

    # define the WSGI application object
    app = Flask(__name__)

    # load .env and variables
    load_dotenv()

    # load object-based default configuration
    env = os.getenv('FLASK_ENV', config_name)
    app.config.from_object(config_by_name[env])

    # finalize app setups
    setup_app(app)

    return app


def setup_app(app):
    """
    Setup the app
    """

    # set app default logging to INFO
    app.logger.setLevel(logging.INFO)

    # link db to app
    db.init_app(app)

    with app.app_context():

        # create tables if they do not exist already
        db.create_all()

        # use app context to load namespaces and blueprints
        from src.namespaces.tickets.index import tickets

    # initialize root blueprint
    root = Blueprint('api', __name__, url_prefix=app.config['APPLICATION_CONTEXT'])

    # link api to blueprint
    api.init_app(root)

    # register blueprints
    app.register_blueprint(root)

    # register namespaces
    api.add_namespace(tickets)

    # register cli commands
    app.cli.add_command(o365_cli)
