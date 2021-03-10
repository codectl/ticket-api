import os


class Config:

    # The application providing info about the ticket
    TICKET_APP_HOST = os.getenv('TICKET_APP_HOST', 'localhost')

    # The mailbox to manage
    MAILBOX = os.getenv('MAILBOX')

    # Office365 related configurations #
    O365_URL = os.getenv('O365_URL', 'https://login.microsoftonline.com')

    # Office365 registered tenant (ASML)
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
    JIRA_DEFAULT_REPORTER = os.getenv('JIRA_DEFAULT_REPORTER')

    # Filter settings
    EMAIL_WHITELISTED_DOMAINS = os.getenv('EMAIL_WHITELISTED_DOMAINS', []).split(',')
    EMAIL_BLACKLIST = os.getenv('EMAIL_BLACKLIST', []).split(',')
