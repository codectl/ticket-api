import click
from flask import current_app
from flask.cli import AppGroup
from O365 import Account, MSOffice365Protocol
from o365_notifications.base import O365Notification
from o365_notifications.streaming.mailbox import O365MailBoxStreamingNotifications

from src.services.notifications.managers.o365_mailbox import O365MailboxManager
from src.services.notifications.filters import (
    JiraCommentNotificationFilter,
    RecipientsFilter,
    SenderEmailBlacklistFilter,
    SenderEmailDomainWhitelistedFilter,
    ValidateMetadataFilter
)

o365_cli = AppGroup(
    'o365',
    short_help='Handle O365 operations, mostly to handle Outlook events'
)


def authenticate_account(mailbox=None, retries=0):
    """
    Authenticate an O365 account.
    """

    credentials = (current_app.config['O365_CLIENT_ID'], None)
    protocol = MSOffice365Protocol(api_version='beta')
    account = Account(credentials,
                      protocol=protocol,
                      tenant_id=current_app.config['O365_TENANT_ID'],
                      main_resource=mailbox or current_app.config['MAILBOX'],
                      request_retries=retries)

    if account.is_authenticated:
        current_app.logger.info('Account already authenticated.')
    else:
        current_app.logger.info('Account not yet authenticated.')
        account.authenticate(tenant_id=current_app.config['O365_TENANT_ID'],
                             scopes=current_app.config['O365_SCOPES'])
        current_app.logger.info('Authenticated successfully.')
    return account


def create_mailbox_manager(**kwargs):
    """
    Create the mailbox manager.
    """

    account = authenticate_account(**kwargs)
    o365_mailbox = account.mailbox()

    mailbox_notifications = O365MailBoxStreamingNotifications(
        parent=o365_mailbox,
        change_type=O365Notification.ChangeType.CREATED.value
    )

    # Change Id alias to the real id for the 'RecipientsFilter' object
    sent_folder = o365_mailbox.sent_folder()
    sent_folder = sent_folder.get_folder(folder_id=sent_folder.folder_id)

    # the O365 mailbox manager
    manager = O365MailboxManager(mailbox=o365_mailbox) \
        .subscriber(mailbox_notifications) \
        .jira(url=current_app.config['ATLASSIAN_URL'],
              user=current_app.config['ATLASSIAN_USER'],
              token=current_app.config['ATLASSIAN_API_TOKEN']) \
        .filters(
        [
            JiraCommentNotificationFilter(mailbox=o365_mailbox),
            RecipientsFilter(recipient_reference=current_app.config['MAILBOX'], sent_folder=sent_folder),
            SenderEmailBlacklistFilter(blacklist=current_app.config['EMAIL_BLACKLIST']),
            SenderEmailDomainWhitelistedFilter(whitelisted_domains=current_app.config['EMAIL_WHITELISTED_DOMAINS']),
            ValidateMetadataFilter()
        ]
    )

    return manager


@o365_cli.command()
@click.option('--mailbox', '-m', type=str, help='the mailbox to manage events')
@click.option('--retries', '-r', type=int, help='number of retries when request fails')
def authenticate(mailbox=None, retries=0):
    """
    Set code used for OAuth2 authentication.
    """

    return authenticate_account(mailbox=mailbox, retries=retries)


@o365_cli.command()
@click.option('--mailbox', '-m', type=str, help='the mailbox to manage events')
@click.option('--retries', '-r', type=int, help='number of retries when request fails')
def handle_incoming_email(mailbox=None, retries=0):
    """
    Handle incoming email.
    """

    manager = create_mailbox_manager(mailbox=mailbox, retries=retries)

    # Start listening for incoming notifications...
    manager.notification_manager(connection_timeout=current_app.config['CONNECTION_TIMEOUT_IN_MINUTES'],
                                 keep_alive_interval=current_app.config['KEEP_ALIVE_NOTIFICATION_INTERVAL_IN_SECONDS'],
                                 refresh_after_expire=True)


@o365_cli.command()
@click.option('--days', '-d', type=str, help='number of days to search back')
def check_for_missing_tickets(days=1):
    """
    Check for possible tickets that went missing in the last days.
    """

    manager = create_mailbox_manager()

    # Start listening for incoming notifications...
    manager.check_for_missing_tickets(days=days)
