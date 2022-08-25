from dataclasses import dataclass

from src.settings.env import env


@dataclass
class BaseConfig:
    """Base configurations."""

    DEBUG = False
    TESTING = False

    # Application root context
    APPLICATION_CONTEXT = env("APPLICATION_CONTEXT", "/")

    # Database settings
    SQLALCHEMY_DATABASE_URI = env("SQLALCHEMY_DATABASE_URI", None)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_CONNECT_OPTIONS = {}

    # OpenAPI supported version
    OPENAPI = env("OPENAPI", "3.0.3")

    # The application providing info about the ticket
    TICKET_CLIENT_APP = env("TICKET_CLIENT_APP", "localhost")

    # The mailbox to manage
    MAILBOX = env("MAILBOX", None)

    # Office365 related configurations #
    O365_URL = env("O365_URL", "https://login.microsoftonline.com")

    # Office365 registered tenant
    O365_TENANT_ID = env("O365_TENANT_ID", None)

    # O365 client id according to OAuth2 standards
    O365_CLIENT_ID = env("O365_CLIENT_ID", None)

    # O365 client secret according to OAuth2 standards
    O365_CLIENT_SECRET = env("O365_CLIENT_SECRET", None)

    # O365 scopes according to OAuth2 standards
    O365_SCOPES = env.list("O365_SCOPES", [])

    # Streaming connection settings
    # See https://bit.ly/3eqDsGs for details
    CONNECTION_TIMEOUT_IN_MINUTES = env.int("CONNECTION_TIMEOUT_IN_MINUTES", 120)
    KEEP_ALIVE_INTERVAL_IN_SECONDS = env.int("KEEP_ALIVE_INTERVAL_IN_SECONDS", 300)

    # Atlassian credentials
    ATLASSIAN_URL = env("ATLASSIAN_URL", "https://atlassian.net")
    ATLASSIAN_USER = env("ATLASSIAN_USER", None)
    ATLASSIAN_API_TOKEN = env("ATLASSIAN_API_TOKEN", None)

    # Jira settings
    JIRA_TICKET_TYPE = env("JIRA_TICKET_TYPE", None)
    JIRA_TICKET_LABELS = env.list("JIRA_TICKET_LABELS", [])
    JIRA_TICKET_LABEL_CATEGORIES = env.list("JIRA_TICKET_LABEL_CATEGORIES", [])
    JIRA_TICKET_LABEL_DEFAULT_CATEGORY = env("JIRA_TICKET_LABEL_DEFAULT_CATEGORY", None)

    # Jira boards to fetch tickets from
    JIRA_BOARDS = env.list("JIRA_BOARDS", [])
    JIRA_DEFAULT_BOARD = env("JIRA_DEFAULT_BOARD", None)

    # Filter settings
    EMAIL_WHITELISTED_DOMAINS = env.list("EMAIL_WHITELISTED_DOMAINS", [])
    EMAIL_BLACKLIST = env.list("EMAIL_BLACKLIST", [])


@dataclass
class ProductionConfig(BaseConfig):
    ENV = "production"
    LOG_LEVEL = "INFO"


@dataclass
class DevelopmentConfig(BaseConfig):
    ENV = "development"
    DEBUG = True
    LOG_LEVEL = "DEBUG"


@dataclass
class TestingConfig(BaseConfig):
    ENV = "test"
    TESTING = True
    LOG_LEVEL = "DEBUG"
