import datetime
import itertools

import click
from flask import current_app
from flask.cli import AppGroup
from O365 import Account, MSOffice365Protocol
from O365_notifications.constants import O365EventType
from O365_notifications.streaming import O365StreamingSubscriber

from src.cli.O365.backend import DatabaseTokenBackend
from src.services.O365.filters import (
    JiraCommentNotificationFilter,
    RecipientControlFilter,
    SenderEmailBlacklistFilter,
    SenderEmailDomainWhitelistedFilter,
    ValidateMetadataFilter,
)
from src.services.O365.handlers.jira import JiraNotificationHandler

cli = AppGroup("O365", short_help="Handle O365 events")


def authorize_account(email=None, retries=0):
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


def create_subscriber(email: str = None, **kwargs):
    email = email or current_app.config["MAILBOX"]
    account = authorize_account(email=email, **kwargs)
    mailbox = account.mailbox()

    # create a new streaming subscriber
    subscriber = O365StreamingSubscriber(parent=account)

    # subscribe to inbox and sent items folder events
    events = [O365EventType.CREATED]
    subscriber.subscribe(resource=mailbox.inbox_folder(), events=events)
    subscriber.subscribe(resource=mailbox.sent_folder(), events=events)
    return subscriber


def create_handler(subscriber):

    # the O365 mailbox manager
    whitelist = current_app.config["EMAIL_WHITELISTED_DOMAINS"]
    blacklist = current_app.config["EMAIL_BLACKLIST"]
    resources = [sub.resource for sub in subscriber.subscriptions]
    main_resource = subscriber.main_resource
    filters = [
        JiraCommentNotificationFilter(folder=resources[0]),
        RecipientControlFilter(email=main_resource, ignore=[resources[1]]),
        SenderEmailBlacklistFilter(blacklist=blacklist),
        SenderEmailDomainWhitelistedFilter(whitelisted_domains=whitelist),
        ValidateMetadataFilter(),
    ]
    return JiraNotificationHandler(
        parent=subscriber, namespace=subscriber.namespace, filters=filters
    )


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
    subscriber = create_subscriber(email=mailbox)
    handler = create_handler(subscriber)

    # start listening for incoming notifications ...
    subscriber.start_streaming(
        notification_handler=handler,
        connection_timeout=current_app.config["CONNECTION_TIMEOUT_IN_MINUTES"],
        keep_alive_interval=current_app.config["KEEP_ALIVE_INTERVAL_IN_SECONDS"],
        refresh_after_expire=True,
    )


@cli.command()
@click.option("--mailbox", "-m", default=None, help="the mailbox to verify")
@click.option("--days", "-d", default=1, help="number of days to search back")
def check_for_missing_tickets(mailbox, days):
    """Check for possible tickets that went missing in the last days."""
    subscriber = create_subscriber(email=mailbox)
    handler = create_handler(subscriber)

    daytime = datetime.datetime.now() - datetime.timedelta(days=days)
    query = (
        subscriber.new_query().on_attribute("receivedDateTime").greater_equal(daytime)
    )

    folders = [sub.resource for sub in subscriber.subscriptions]
    data = [folder.get_messages(limit=None, query=query) for folder in folders]
    messages = list(itertools.chain(data))
    messages.sort(key=lambda msg: msg.received)  # sort by date

    # process each individual message
    current_app.logger.info(f"Found {str(len(messages))} messages to process.")
    for message in messages:
        handler.process_message(message.object_id)
