import datetime
import itertools
import json
import re

import mistune
import O365.mailbox
from flask import current_app

from src.models.ticket import Ticket
from src.services.notifications.filters.OutlookMessageFilter import OutlookMessageFilter
from src.services.notifications.handlers.jira import JiraNotificationHandler
from src.services.ticket import TicketSvc


class O365MailboxManager:
    """Manager for O365 mailbox events."""

    def __init__(self, mailbox: O365.mailbox.MailBox):
        self._mailbox = mailbox
        self._subscriber = None
        self._filters = None

    def subscriber(self, subs):
        self._subscriber = subs
        return self

    def filters(self, fltr: list[OutlookMessageFilter]):
        self._filters = fltr
        return self

    def check_for_missing_tickets(self, days):
        """Sweep the messages received in the last days to create tickets out of
        of the possible messages that were missed.
        """

        # set inbox/sent folder
        inbox_folder = self._mailbox.inbox_folder()
        sent_folder = self._mailbox.sent_folder()

        # build query for O365
        daytime = datetime.datetime.now() - datetime.timedelta(days=days)
        query = (
            self._mailbox.new_query()
            .on_attribute("receivedDateTime")
            .greater_equal(daytime)
        )
        inbox_msgs = inbox_folder.get_messages(limit=None, query=query)
        sent_msgs = sent_folder.get_messages(limit=None, query=query)
        messages = list(itertools.chain(inbox_msgs, sent_msgs))

        # sort messages by age (older first)
        messages.sort(key=lambda e: e.received)

        current_app.logger.info(f"Found {str(len(messages))} messages to process.")

        # process each individual message
        for message in messages:
            self.process_message(message_id=message.object_id)

    def start_streaming(self, **kwargs):
        handler = JiraNotificationHandler(manager=self)

        # create subscriptions from inbox & sent folders
        inbox_folder = self._mailbox.inbox_folder()
        sent_folder = self._mailbox.sent_folder()
        inbox_subscription_id = self._subscriber.subscribe(resource=inbox_folder)
        sent_subscription_id = self._subscriber.subscribe(resource=sent_folder)
        subscriptions = [inbox_subscription_id, sent_subscription_id]

        msg = f"Start streaming connection for '{self._mailbox.main_resource}' ..."
        current_app.logger.info(msg)

        self._subscriber.create_event_channel(
            subscriptions=subscriptions, notification_handler=handler, **kwargs
        )

    def process_message(self, message_id):
        """Process a message and create/update ticket."""
        svc = TicketSvc()

        # reading message from the corresponding folder
        # and create Jira ticket for it.
        message = self._get_message(message_id=message_id)

        # watchers list
        ccs = (e.address for e in message.cc)
        bccs = (e.address for e in message.bcc)
        emails = list(itertools.chain(ccs, bccs))

        current_app.logger.info("\n*** Processing new message ***")
        current_app.logger.info(
            json.dumps(
                {
                    "outlook id": message.object_id,
                    "created": message.created.strftime("%d/%m/%Y %H:%M:%S"),
                    "subject": message.subject,
                    "from": message.sender.address,
                },
                indent=4,
            )
        )

        # skip message processing if message is filtered
        if any(not e for e in list(map(lambda f: f.apply(message), self._filters))):
            current_app.logger.info(f"Message '{message.subject}' filtered.")
            return

        # check for local existing ticket
        existing_ticket = svc.find_one(
            outlook_conversation_id=message.conversation_id, _model=True
        )

        # add new comment if ticket already exists.
        # create new ticket otherwise.
        if existing_ticket:

            # delete local reference if ticket no longer exists in Jira
            exists = next(iter(svc.find_by(key=existing_ticket.key, limit=1)), None)
            if not exists:
                svc.delete(ticket_id=existing_ticket.id)

            # only add comment if not added yet
            if message.object_id not in existing_ticket.outlook_messages_id:
                svc.create_comment(
                    issue=existing_ticket,
                    author=message.sender.address,
                    body=O365.message.bs(message.unique_body, "html.parser").body.text,
                    watchers=emails,
                    attachments=message.attachments,
                )

                # append message to history
                self.add_message_to_history(message, existing_ticket)

                msg = f"New comment added to Jira ticket '{existing_ticket.key}'."
            else:
                key = existing_ticket.key
                msg = f"Comment on ticket '{key}' has already been added."
            current_app.logger.info(msg)
        else:

            # create ticket in Jira and keep local reference
            issue = svc.create(
                # Jira fields
                title=message.subject,
                body=O365.message.bs(message.unique_body, "html.parser").body.text,
                reporter=message.sender.address,
                board="support",
                category="general",
                priority=message.importance.value,
                watchers=emails,
                attachments=message.attachments,
                # local fields
                outlook_message_id=message.object_id,
                outlook_message_url=message.resource_namespace,
                outlook_conversation_id=message.conversation_id,
                outlook_messages_id=message.object_id,
            )

            # get local ticket reference
            model = svc.find_one(key=issue["key"], _model=True)

            # notify ticket reporter about created ticket
            notification = self._notify_reporter(message=message, key=model.key)

            # append message to history
            self.add_message_to_history(message=notification, model=model)

            current_app.logger.info(f"New ticket created with Jira key '{model.key}'.")

    def _get_message(self, message_id):
        """Custom implementation for getting message from id.

        Headers must be included in the request and original implementation
        does not allow.

        Remove this if future implementation of Folder.get_message
        allow kwargs to be passed on to connection.get method.
        """

        # fields to retrieve
        params = {
            "$select": "CreatedDateTime,Subject,"
            "Body,UniqueBody,"
            "From,ToRecipients,"
            "BccRecipients,CcRecipients,"
            "Flag,Importance,"
            "HasAttachments,Id,ParentFolderId,"
            "ConversationId,ConversationIndex"
        }

        # create a dummy folder to get message
        folder = O365.mailbox.Folder(parent=self._mailbox)

        url = folder.build_url(folder._endpoints.get("message").format(id=message_id))
        message = folder.con.get(url, params=params).json()
        message_object = folder.message_constructor(
            parent=folder,
            is_draft=False,
            download_attachments=True,
            **{folder._cloud_data_key: message},
        )

        message_object.folder = folder
        message_object.resource_namespace = message["@odata.id"]
        return message_object

    @classmethod
    def _notify_reporter(cls, *, message: O365.Message, key: str):
        """Notify ticket reporter.

        :param message: the reported issue message
        :param key: the ticket key
        """

        # creating notification message to be sent to all recipients
        markdown = mistune.create_markdown(escape=False)
        body = markdown(
            TicketSvc.create_message_body(
                template="notification.j2",
                values={
                    "summary": message.subject,
                    "key": key,
                    "url": current_app.config["TICKET_CLIENT_APP"],
                },
            )
        )

        reply = cls.create_reply(
            message,
            values={
                "body": body,
                "metadata": [dict(name="message", content="jira ticket notification")],
            },
        )
        reply.send()
        return reply

    @staticmethod
    def add_message_to_history(message: O365.Message, model: Ticket):
        """Add a message to the ticket history."""
        messages_id = model.outlook_messages_id.split(",")
        if message.object_id not in messages_id:
            TicketSvc.update(
                ticket_id=model.id,
                outlook_messages_id=",".join(messages_id + [message.object_id]),
                updated_at=datetime.datetime.utcnow(),
            )

    @staticmethod
    def create_reply(message: O365.Message, values: dict = None):
        """Create a reply message from template."""
        reply = message.reply(to_all=True)

        # process email body with bs
        bs = O365.message.bs

        if reply.body_type.lower() == "html":
            soup = bs(reply.body, "html.parser")
            soup.find("hr").decompose()  # remove horizontal lines
            reply_body = soup.find("body").decode_contents()
            style_bs = soup.find("style")
            style = style_bs.decode_contents() if style_bs else ""
        else:
            reply_body = "\n".join(reply.body.splitlines()[2:])
            style = ""

        body = TicketSvc.create_message_body(
            template="reply.j2", values={"reply": reply_body, "style": style, **values}
        )

        # replace body of the reply with the processed body
        reply.body = None  # reset body
        reply.body_type = "html"
        reply.body = body

        return reply

    @staticmethod
    def message_json(message: O365.Message):
        """Get json information from message."""
        soup = O365.message.bs(message.unique_body, "html.parser")

        body = str(soup)

        # get the json data
        data = re.search(r"{.*\s.*}", body).group()
        data = json.loads(data)

        return data
