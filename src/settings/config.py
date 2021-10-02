import os

import environs
import flasgger
import yaml


def create_env():
    """Create an env from local .env."""
    dotenv = environs.Env()
    dotenv.read_env()
    return dotenv


# load environment from .env
env = create_env()


class BaseConfig:
    """Base configurations."""

    DEBUG = False
    TESTING = False

    # Define host & port
    HOST = env('FLASK_RUN_HOST', '0.0.0.0')
    PORT = env.int('FLASK_RUN_PORT', 5000)

    # Application root context
    APPLICATION_CONTEXT = env('APPLICATION_CONTEXT', '/')

    # Swagger properties
    OPENAPI = env('OPENAPI', '3.0.3')
    SWAGGER = {
        'openapi': OPENAPI,
        'specs': [
            {
                'endpoint': 'swagger',
                'route': APPLICATION_CONTEXT + '/swagger.json',
                'rule_filter': lambda rule: True,
                'model_filter': lambda tag: True
            }
        ],

        # where to find the docs (ensure trailing slash)
        'specs_route': APPLICATION_CONTEXT + '/',

        # swagger static files
        'static_url_path': APPLICATION_CONTEXT + '/flasgger_static',

        # hide the Swagger top bar
        'hide_top_bar': True
    }

    # OpenAPI 3 initial specs
    OPENAPI_SPEC = yaml.safe_load(flasgger.utils.load_from_file(
        os.path.join('src', 'settings', 'oas3.yaml')
    ).format(**{
        'OPENAPI': OPENAPI,
        'APPLICATION_CONTEXT': APPLICATION_CONTEXT
    }))

    # Database settings
    SQLALCHEMY_DATABASE_URI = env('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_CONNECT_OPTIONS = {}

    # Cache settings
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT: 300

    # Application threads. A common general assumption is
    # using 2 per available processor cores - to handle
    # incoming requests using one and performing background
    # operations using the other.
    THREADS_PER_PAGE = 2

    # The application providing info about the ticket
    TICKET_CLIENT_APP = env('TICKET_CLIENT_APP', 'localhost')

    # The mailbox to manage
    MAILBOX = env('MAILBOX')

    # Office365 related configurations #
    O365_URL = env('O365_URL', 'https://login.microsoftonline.com')

    # Office365 registered tenant
    O365_TENANT_ID = env('O365_TENANT_ID')

    # O365 client Id according to OAuth2 standards
    O365_CLIENT_ID = env('O365_CLIENT_ID')

    # O365 client secret according to OAuth2 standards
    O365_CLIENT_SECRET = env('O365_CLIENT_SECRET')

    # O365 scopes according to OAuth2 standards
    O365_SCOPES = env.list('O365_SCOPES')

    # Streaming connection settings
    # See https://bit.ly/3eqDsGs for details
    CONNECTION_TIMEOUT_IN_MINUTES = env.int('CONNECTION_TIMEOUT_IN_MINUTES', 120)  # 2h
    KEEP_ALIVE_NOTIFICATION_INTERVAL_IN_SECONDS = env.int('KEEP_ALIVE_NOTIFICATION_INTERVAL_IN_SECONDS', 300)  # 5m

    # Atlassian credentials
    ATLASSIAN_URL = env('ATLASSIAN_URL')
    ATLASSIAN_USER = env('ATLASSIAN_USER')
    ATLASSIAN_API_TOKEN = env('ATLASSIAN_API_TOKEN')

    # Jira settings
    JIRA_TICKET_TYPE = env('JIRA_TICKET_TYPE', None)
    JIRA_TICKET_LABELS = env.list('JIRA_TICKET_LABELS', [])
    JIRA_TICKET_LABEL_CATEGORIES = env.list('JIRA_TICKET_LABEL_CATEGORIES', [])
    JIRA_TICKET_LABEL_DEFAULT_CATEGORY = env('JIRA_TICKET_LABEL_DEFAULT_CATEGORY', None)

    # Jira boards to fetch tickets from
    JIRA_BOARDS = (lambda env=env: [{
        'key': board.lower().replace('jira_', '').replace('_board', ''),
        'jira_name': env(board)
    } for board in env.list('JIRA_BOARDS', []) if env(board, None)])()
    JIRA_DEFAULT_BOARD = (
        lambda env=env, boards=tuple(JIRA_BOARDS):
        next(board for board in boards if board['jira_name'] == env(env('JIRA_DEFAULT_BOARD')))
    )()

    # Filter settings
    EMAIL_WHITELISTED_DOMAINS = env.list('EMAIL_WHITELISTED_DOMAINS', [])
    EMAIL_BLACKLIST = env.list('EMAIL_BLACKLIST', [])


class ProductionConfig(BaseConfig):
    ENV = 'production'
    LOG_LEVEL = 'INFO'


class DevelopmentConfig(BaseConfig):
    ENV = 'development'
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class TestingConfig(BaseConfig):
    ENV = 'test'
    TESTING = True
    LOG_LEVEL = 'DEBUG'


config_by_name = dict(
    production=ProductionConfig,
    development=DevelopmentConfig,
    testing=TestingConfig
)
