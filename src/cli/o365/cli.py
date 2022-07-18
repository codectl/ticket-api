import click
from flask import current_app
from flask.cli import AppGroup
from O365 import Account, MSOffice365Protocol
from o365_notifications.base import O365Notification
from o365_notifications.streaming.mailbox import O365MailBoxStreamingNotifications

from src.cli.o365.backend import DatabaseTokenBackend
from src.services.notifications.filters import (
    JiraCommentNotificationFilter,
    RecipientsFilter,
    SenderEmailBlacklistFilter,
    SenderEmailDomainWhitelistedFilter,
    ValidateMetadataFilter,
)
from src.services.notifications.managers.mailbox import O365MailboxManager

cli = AppGroup(
    "o365", short_help="Handle O365 operations, mostly to handle Outlook events"
)


def authenticate_account(email=None, retries=0):
    """Authenticate an O365 account."""
    credentials = (current_app.config["O365_CLIENT_ID"], None)
    protocol = MSOffice365Protocol(api_version="beta")
    account = Account(
        credentials,
        protocol=protocol,
        tenant_id=current_app.config["O365_TENANT_ID"],
        main_resource=email or current_app.config["MAILBOX"],
        request_retries=retries,
        token_backend=DatabaseTokenBackend(),
    )

    if account.is_authenticated:
        current_app.logger.info("Account already authenticated.")
    else:
        current_app.logger.info("Account not yet authenticated.")
        account.authenticate(
            tenant_id=current_app.config["O365_TENANT_ID"],
            scopes=current_app.config["O365_SCOPES"],
        )
        current_app.logger.info("Authenticated successfully.")
    return account


def create_mailbox_manager(email: str = None, **kwargs):
    """Create the mailbox manager."""
    email = email or current_app.config["MAILBOX"]
    account = authenticate_account(email=email, **kwargs)
    mailbox = account.mailbox()

    ct = O365Notification.ChangeType.CREATED.value
    notif = O365MailBoxStreamingNotifications(parent=mailbox, change_type=ct)

    # Change id alias to the real id for the 'RecipientsFilter' object
    sent_folder = mailbox.sent_folder()
    sent_folder = sent_folder.get_folder(folder_id=sent_folder.folder_id)

    # the O365 mailbox manager
    whitelist = current_app.config["EMAIL_WHITELISTED_DOMAINS"]
    blacklist = current_app.config["EMAIL_BLACKLIST"]
    manager = (
        O365MailboxManager(mailbox=mailbox)
        .subscriber(notif)
        .filters(
            [
                JiraCommentNotificationFilter(mailbox=mailbox),
                RecipientsFilter(recipient_reference=mailbox, sent_folder=sent_folder),
                SenderEmailBlacklistFilter(blacklist=blacklist),
                SenderEmailDomainWhitelistedFilter(whitelisted_domains=whitelist),
                ValidateMetadataFilter(),
            ]
        )
    )

    return manager


@cli.command()
@click.option("--mailbox", "-m", default=None, help="the mailbox to manage events")
@click.option("--retries", "-r", default=0, help="number of retries when request fails")
def authenticate(mailbox=None, retries=0):
    """Set code used for OAuth2 authentication."""
    return authenticate_account(email=mailbox, retries=retries)


@cli.command()
@click.option("--mailbox", "-m", default=None, help="the mailbox to manage events")
@click.option("--retries", "-r", default=0, help="number of retries when request fails")
def handle_incoming_email(mailbox, retries):
    """Handle incoming email."""
    manager = create_mailbox_manager(email=mailbox, retries=retries)

    # Start listening for incoming notifications...
    config = current_app.config
    manager.start_streaming(
        connection_timeout=config["CONNECTION_TIMEOUT_IN_MINUTES"],
        keep_alive_interval=config["KEEP_ALIVE_NOTIFICATION_INTERVAL_IN_SECONDS"],
        refresh_after_expire=True,
    )


@cli.command()
@click.option("--days", "-d", default=1, help="number of days to search back")
def check_for_missing_tickets(days):
    """Check for possible tickets that went missing in the last days."""
    manager = create_mailbox_manager()

    # Start listening for incoming notifications...
    manager.check_for_missing_tickets(days=days)
