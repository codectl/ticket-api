from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_plugins.webframeworks.flask import FlaskPlugin
from apispec_ui.flask import Swagger
from flask import Flask, Blueprint

from src import __meta__, __version__, utils
from src.api.tickets import blueprint as tickets
from src.cli.O365.cli import cli as o365_cli
from src.settings import oas
from src.settings.ctx import ctx_settings, db
from src.settings.env import config_class, load_dotenv


def create_app(config_name="development", dotenv=True, configs=None):
    """Create a new app."""

    # define the WSGI application object
    app = Flask(__name__)

    # load object-based default configuration
    load_dotenv(dotenv)
    app.config.from_object(config_class(config_name))
    app.config.update(configs or {})

    # finalize app setups
    setup_app(app)

    return app


def setup_app(app):
    """Initial setups."""
    url_prefix = app.config["APPLICATION_ROOT"]
    openapi_version = app.config["OPENAPI"]

    # link db to app
    db.init_app(app)

    # initial blueprint wiring
    index = Blueprint("index", __name__)
    index.register_blueprint(tickets)
    app.register_blueprint(index, url_prefix=url_prefix)

    # base template for OpenAPI specs
    oas.converter = oas.create_spec_converter(openapi_version)

    spec_template = oas.base_template(
        openapi_version=openapi_version,
        info={
            "title": __meta__["name"],
            "version": __version__,
            "description": __meta__["summary"],
        },
        servers=[oas.Server(url=url_prefix, description=app.config["ENV"])],
        tags=[
            oas.Tag(
                name="tickets",
                description="All operations involving tickets",
            )
        ],
        responses=[
            utils.http_response(code=400, serialize=False),
            utils.http_response(code=404, serialize=False),
            utils.http_response(code=415, serialize=False),
        ],
    )

    spec = APISpec(
        title=__meta__["name"],
        version=__version__,
        openapi_version=openapi_version,
        plugins=(FlaskPlugin(), MarshmallowPlugin()),
        basePath=url_prefix,
        **spec_template
    )

    # create paths from app views
    for view in app.view_functions.values():
        spec.path(view=view, app=app, base_path=url_prefix)

    # create views for Swagger
    Swagger(app=app, apispec=spec, config=oas.swagger_configs(app_root=url_prefix))

    # settings within app ctx
    ctx_settings(app)

    # register cli commands
    app.cli.add_command(o365_cli)
