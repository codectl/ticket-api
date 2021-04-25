import os

import flasgger
import yaml


class BaseConfig:
    DEBUG = False
    TESTING = False

    # Name of the host
    HOST = os.getenv('FLASK_RUN_HOST', '0.0.0.0')

    # Application root context
    APPLICATION_CONTEXT = os.getenv('APPLICATION_CONTEXT', '/')

    # Swagger properties
    OPENAPI = os.getenv('OPENAPI', '3.0.3')
    SWAGGER = {
        'openapi': OPENAPI,
        'specs': [
            {
                'endpoint': 'swagger',
                'route': '/swagger.json',
                'rule_filter': lambda rule: True,
                'model_filter': lambda tag: True
            }
        ],

        # where to find the docs (ensure trailing slash)
        'specs_route': APPLICATION_CONTEXT + ('' if APPLICATION_CONTEXT.endswith('/') else '/'),

        # hide the Swagger top bar
        'hide_top_bar': True,
    }

    # OpenAPI 3 initial specs
    OPENAPI_SPEC = yaml.safe_load(flasgger.utils.load_from_file(
        os.path.join('src', 'settings', 'oas3.yaml')
    ).format(**{
        'OPENAPI': OPENAPI,
        'APPLICATION_CONTEXT': APPLICATION_CONTEXT
    }))

    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
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
    TICKET_CLIENT_APP = os.getenv('TICKET_CLIENT_APP', 'localhost')

    # The mailbox to manage
    MAILBOX = os.getenv('MAILBOX')

    # Office365 related configurations #
    O365_URL = os.getenv('O365_URL', 'https://login.microsoftonline.com')

    # Office365 registered tenant
    O365_TENANT_ID = os.getenv('O365_TENANT_ID')

    # O365 client Id according to OAuth2 standards
    O365_CLIENT_ID = os.getenv('O365_CLIENT_ID')

    # O365 client secret according to OAuth2 standards
    O365_CLIENT_SECRET = os.getenv('O365_CLIENT_SECRET')

    # O365 scopes according to OAuth2 standards
    O365_SCOPES = os.getenv('O365_SCOPES', []).split(',')

    # Streaming connection settings
    # See https://bit.ly/3eqDsGs for details
    CONNECTION_TIMEOUT_IN_MINUTES = os.getenv('CONNECTION_TIMEOUT_IN_MINUTES', 120)  # 2h
    KEEP_ALIVE_NOTIFICATION_INTERVAL_IN_SECONDS = os.getenv('KEEP_ALIVE_NOTIFICATION_INTERVAL_IN_SECONDS', 300)  # 5m

    # Atlassian credentials
    ATLASSIAN_URL = os.getenv('ATLASSIAN_URL')
    ATLASSIAN_USER = os.getenv('ATLASSIAN_USER')
    ATLASSIAN_API_TOKEN = os.getenv('ATLASSIAN_API_TOKEN')

    # Jira settings
    JIRA_TICKET_BOARD_ID = os.getenv('JIRA_TICKET_BOARD_ID')
    JIRA_TICKET_BOARD_KEY = os.getenv('JIRA_TICKET_BOARD_KEY')
    JIRA_TICKET_TYPE = os.getenv('JIRA_TICKET_TYPE')
    JIRA_TICKET_LABELS = os.getenv('JIRA_TICKET_LABELS', []).split(',')
    JIRA_TICKET_LABEL_CATEGORIES = os.getenv('JIRA_TICKET_LABEL_CATEGORIES', []).split(',')
    JIRA_TICKET_LABEL_DEFAULT_CATEGORY = os.getenv('JIRA_TICKET_LABEL_DEFAULT_CATEGORY')
    JIRA_DEFAULT_REPORTER = os.getenv('JIRA_DEFAULT_REPORTER')

    # Jira boards to fetch tickets from
    JIRA_BOARDS = [{
        'key': board.lower().replace('jira_', '').replace('_board', ''),
        'jira_name': os.getenv(board)
    } for board in os.getenv('JIRA_BOARDS').split(',')]
    JIRA_DEFAULT_BOARD = next(
        board for board in JIRA_BOARDS if board['jira_name'] == os.getenv(os.getenv('JIRA_DEFAULT_BOARD'))
    )

    # Filter settings
    EMAIL_WHITELISTED_DOMAINS = os.getenv('EMAIL_WHITELISTED_DOMAINS', []).split(',')
    EMAIL_BLACKLIST = os.getenv('EMAIL_BLACKLIST', []).split(',')


class ProductionConfig(BaseConfig):
    ENV = 'production'
    PORT = os.getenv('FLASK_RUN_PORT', 5000)
    LOG_LEVEL = 'INFO'


class DevelopmentConfig(BaseConfig):
    ENV = 'development'
    PORT = os.getenv('FLASK_RUN_PORT', 5001)
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class TestingConfig(BaseConfig):
    ENV = 'test'
    PORT = os.getenv('FLASK_RUN_PORT', 5002)
    TESTING = True
    LOG_LEVEL = 'DEBUG'


config_by_name = dict(
    production=ProductionConfig,
    development=DevelopmentConfig,
    testing=TestingConfig
)
