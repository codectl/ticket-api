import click
from flask import current_app
from flask.cli import AppGroup
from O365 import Account, MSOffice365Protocol
from O365_notifications.constants import O365EventType
from O365_notifications.streaming import O365StreamingSubscriber

from src.cli.O365.backend import DatabaseTokenBackend
from src.services.notifications.filters import (
    JiraCommentNotificationFilter,
    RecipientsFilter,
    SenderEmailBlacklistFilter,
    SenderEmailDomainWhitelistedFilter,
    ValidateMetadataFilter,
)
from src.services.notifications.managers.mailbox import O365SubscriberMgr

cli = AppGroup(
    "o365", short_help="Handle O365 operations, mostly to handle Outlook events"
)


def authorize_account(email=None, retries=0):
    """Authorize an O365 account."""
    config = current_app.config
    credentials = (config["O365_CLIENT_ID"], config["O365_CLIENT_SECRET"])
    protocol = MSOffice365Protocol(api_version="beta")

    # for authorization code flow:
    #   * set auth_flow_type="authorization"
    #   * add scopes (env "O365_SCOPES")
    account = Account(
        credentials=credentials,
        protocol=protocol,
        tenant_id=config["O365_TENANT_ID"],
        main_resource=email or config["MAILBOX"],
        auth_flow_type="credentials",
        request_retries=retries,
        token_backend=DatabaseTokenBackend(),
    )

    if account.is_authenticated:
        current_app.logger.info("Account already authorized.")
    else:
        current_app.logger.info("Authorizing account ...")
        account.authenticate(tenant_id=config["O365_TENANT_ID"])
        current_app.logger.info("Authorization done.")
    return account


def subscriber_mgr(email: str = None, **kwargs):
    email = email or current_app.config["MAILBOX"]
    account = authorize_account(email=email, **kwargs)
    mailbox = account.mailbox()

    # create a new streaming subscriber
    subscriber = O365StreamingSubscriber(parent=account)

    # subscribe to inbox and sent items folder events
    events = [O365EventType.CREATED]
    subscriber.subscribe(resource=mailbox.inbox_folder(), events=events)
    subscriber.subscribe(resource=mailbox.sent_folder(), events=events)

    # the O365 mailbox manager
    whitelist = current_app.config["EMAIL_WHITELISTED_DOMAINS"]
    blacklist = current_app.config["EMAIL_BLACKLIST"]
    filters = [
        JiraCommentNotificationFilter(mailbox=mailbox),
        RecipientsFilter(email=email, sent_folder=mailbox.sent_folder()),
        SenderEmailBlacklistFilter(blacklist=blacklist),
        SenderEmailDomainWhitelistedFilter(whitelisted_domains=whitelist),
        ValidateMetadataFilter(),
    ]
    return O365SubscriberMgr(subscriber=subscriber, filters=filters)


@cli.command()
@click.option("--mailbox", "-m", default=None, help="the mailbox to manage events")
@click.option("--retries", "-r", default=0, help="number of retries when request fails")
def authorize(mailbox=None, retries=0):
    """Grant service authorization to O365 resources."""
    return authorize_account(email=mailbox, retries=retries)


@cli.command()
@click.option("--mailbox", "-m", default=None, help="the mailbox to manage events")
@click.option("--retries", "-r", default=0, help="number of retries when request fails")
def handle_incoming_email(mailbox, retries):
    """Handle incoming email."""
    mgr = subscriber_mgr(email=mailbox, retries=retries)

    # Start listening for incoming notifications...
    config = current_app.config
    mgr.start_streaming(
        connection_timeout=config["CONNECTION_TIMEOUT_IN_MINUTES"],
        keep_alive_interval=config["KEEP_ALIVE_NOTIFICATION_INTERVAL_IN_SECONDS"],
        refresh_after_expire=True,
    )


@cli.command()
@click.option("--days", "-d", default=1, help="number of days to search back")
def check_for_missing_tickets(days):
    """Check for possible tickets that went missing in the last days."""
    mgr = subscriber_mgr()

    # Start listening for incoming notifications...
    mgr.check_for_missing_tickets(days=days)
