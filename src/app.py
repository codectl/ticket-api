import logging
import os

import flasgger
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from dotenv import load_dotenv
from flask import Flask, Blueprint

from src import api, cache, db, swagger
from src.cli.o365 import o365_cli
from src.misc.converters import openapi3_converters
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

        # make use of OAS3 schema converters
        openapi3_converters()

        # use app context to load namespaces, blueprints and schemas
        from src.resources.tickets import Ticket, Tickets
        from src.serializers.outbound.HttpError import HttpErrorSchema
        from src.serializers.outbound.jira.Issue import IssueSchema

    # initialize root blueprint
    bp = Blueprint('api', __name__, url_prefix=app.config['APPLICATION_CONTEXT'])

    # link api to blueprint
    api.init_app(bp)

    # # register namespaces
    api.add_resource(Tickets, '/tickets', endpoint='tickets')
    api.add_resource(Ticket, '/tickets/<key>', endpoint='ticket')

    # register blueprints
    app.register_blueprint(bp)

    # link swagger to app
    swagger.init_app(app)

    # define OAS3 base template
    swagger.template = flasgger.apispec_to_template(
        app=app,
        spec=APISpec(
            title=app.config['OPENAPI_SPEC']['info']['title'],
            version=app.config['OPENAPI_SPEC']['info']['version'],
            openapi_version=app.config['OPENAPI_SPEC']['openapi'],
            plugins=(MarshmallowPlugin(),),
            basePath=app.config['APPLICATION_CONTEXT'],
            **app.config['OPENAPI_SPEC']
        ),
        definitions=[
            HttpErrorSchema,
            IssueSchema
        ]
    )

    # register cli commands
    app.cli.add_command(o365_cli)
