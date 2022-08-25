import datetime
import itertools
import json

import mistune
import O365
import O365.mailbox
from flask import current_app

from O365_notifications.base import O365Notification, O365NotificationHandler
from O365_notifications.constants import O365EventType, O365Namespace

from src.models.ticket import Ticket
from src.services.notifications.filters.base import OutlookMessageFilter
from src.services.ticket import TicketSvc


class JiraNotificationHandler(O365NotificationHandler):
    def __init__(
        self,
        parent: O365.utils.ApiComponent,
        namespace: O365Namespace,
        filters: list[OutlookMessageFilter] = (),
    ):
        self.parent = parent
        self.namespace = namespace
        self.filters = filters

    def process(self, notification: O365Notification):
        """A handler that deals with email notifications.

        When the notification is of type Message, create a new Jira ticket. And this
        is currently the only type supported atm.
        """

        # when a notification is received...
        if notification.type == self.namespace.O365NotificationType.NOTIFICATION:

            # log 'Missed' notifications
            if notification.event == O365EventType.MISSED:
                current_app.logger.warning(f"Notification missed: {vars(notification)}")

            # create Jira ticket for 'Message' notifications
            elif (
                notification.resource.type
                == self.namespace.O365ResourceDataType.MESSAGE
            ):
                self.process_message(message_id=notification.resource.id)

    def process_message(self, message_id):
        """Process a message and create/update a ticket."""
        svc = TicketSvc()

        message = self.get_message(message_id, parent=self.parent)

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
        if any(not e for e in list(map(lambda f: f.apply(message), self.filters))):
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

                msg = f"New comment added on ticket '{existing_ticket.key}'."
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
                outlook_conversation_id=message.conversation_id,
                outlook_messages_id=message.object_id,
            )

            # get local ticket reference
            model = svc.find_one(key=issue["key"], _model=True)

            # notify ticket reporter about created ticket
            notification = self.notify_reporter(message=message, ticket_key=model.key)

            # append message to history
            self.add_message_to_history(message=notification, model=model)

            current_app.logger.info(f"New ticket created with Jira key '{model.key}'.")

    @staticmethod
    def get_message(message_id, parent: O365.utils.ApiComponent):
        """Create a complete message O365 component given its id."""

        # force certain properties from the message to be present
        select = (
            "CreatedDateTime",
            "Subject",
            "Body",
            "UniqueBody",
            "From",
            "ToRecipients",
            "BccRecipients",
            "CcRecipients",
            "Flag",
            "Importance",
            "HasAttachments",
            "Id",
            "ParentFolderId",
            "ConversationId",
            "ConversationIndex",
        )

        # dummy folder used to get messages
        folder = O365.mailbox.Folder(parent=parent)

        query = folder.new_query().select(*select)
        return folder.get_message(
            object_id=message_id, query=query, download_attachments=True
        )

    @classmethod
    def notify_reporter(cls, *, message: O365.Message, ticket_key: str):
        # creating notification message to be sent to all recipients
        markdown = mistune.create_markdown(escape=False)
        body = markdown(
            TicketSvc.create_message_body(
                template="notification.j2",
                values={
                    "summary": message.subject,
                    "key": ticket_key,
                    "url": current_app.config["TICKET_CLIENT_APP"],
                },
            )
        )

        metadata = {"name": "message", "content": "jira ticket notification"}
        reply = cls.create_reply(message, values={"body": body, "metadata": [metadata]})
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
