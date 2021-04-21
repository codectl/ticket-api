import logging
import os

import flasgger.utils
from dotenv import load_dotenv
from flask import Flask, Blueprint

from src import api, cache, db, swagger
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

    # link api to app
    api.init_app(app)

    # link cache to app
    cache.init_app(app)

    with app.app_context():

        # create tables if they do not exist already
        db.create_all()

        # use app context to load namespaces and blueprints
        from src.resources.tickets import Tickets
        from src.schemas.jira.issue import Issue

    # initialize root blueprint
    bp = Blueprint('api', __name__, url_prefix=app.config['APPLICATION_CONTEXT'])

    # link api to blueprint
    api.init_app(bp)

    # # register namespaces
    # api.add_namespace(tickets)
    api.add_resource(Tickets, '/tickets', endpoint='tickets')

    # register blueprints
    app.register_blueprint(bp)

    # link swagger to app
    swagger.init_app(app)
    swagger.template = {
        'basePath': app.config['APPLICATION_CONTEXT'],
        'components': {
            'schemas': [Issue]
        }
    }

    # register cli commands
    app.cli.add_command(o365_cli)
