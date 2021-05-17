import datetime
import itertools
import json
import re

import mistune
import O365.mailbox
from flask import current_app

from src.models.Ticket import Ticket
from src.services.notifications.handlers.JiraNotificationHandler import JiraNotificationHandler
from src.services.ticket import TicketService


class O365MailboxManager:
    """Manager for O365 mailbox events."""

    def __init__(self, mailbox: O365.mailbox.MailBox):
        self._mailbox = mailbox
        self._subscriber = None
        self._filters = None

    def subscriber(self, subscriber_):
        self._subscriber = subscriber_
        return self

    def filters(self, filters_):
        self._filters = filters_
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
        query = self._mailbox.new_query().on_attribute('receivedDateTime').greater_equal(daytime)
        messages = list(itertools.chain(inbox_folder.get_messages(limit=None, query=query),
                                        sent_folder.get_messages(limit=None, query=query)))

        # sort messages by age (older first)
        messages.sort(key=lambda e: e.received)

        current_app.logger.info("Found {0} messages to process.".format(str(len(messages))))

        # process each individual message
        for message in messages:
            self.process_message(message_id=message.object_id)

    def start_streaming(self, **kwargs):
        handler = JiraNotificationHandler(manager=self)

        # set inbox/sent folder
        inbox_folder = self._mailbox.inbox_folder()
        sent_folder = self._mailbox.sent_folder()

        # define subscriptions
        inbox_subscription_id = self._subscriber.subscribe(resource=inbox_folder)
        sent_subscription_id = self._subscriber.subscribe(resource=sent_folder)
        subscriptions = [inbox_subscription_id, sent_subscription_id]

        current_app.logger.info("Start streaming connection for '{0}' ...".format(self._mailbox.main_resource))
        self._subscriber.create_event_channel(
            subscriptions=subscriptions,
            notification_handler=handler,
            **kwargs
        )

    def process_message(self, message_id):
        """Process a message (given its Id) for the creation of a ticket."""

        # reading message from the corresponding folder
        # and create Jira ticket for it.
        message = self._get_message(message_id=message_id)

        # watchers list
        emails = list(itertools.chain((e.address for e in message.cc),
                                      (e.address for e in message.bcc)))

        current_app.logger.info('*** Processing new message ***')
        current_app.logger.info(json.dumps({
            'outlook id': message.object_id,
            'created': message.created.strftime('%d/%m/%Y %H:%M:%S'),
            'subject': message.subject,
            'from': message.sender.address
        }, indent=4))

        # skip message processing if message is filtered
        if any(not e for e in list(map(lambda filter_: filter_.apply(message), self._filters))):
            current_app.logger.info('Message \'{0}\' filtered.'.format(message.subject))
            return

        # check for local existing ticket
        existing_ticket = TicketService.find_one(
            outlook_conversation_id=message.conversation_id,
            _model=True
        )

        # add new comment if ticket already exists.
        # create new ticket otherwise.
        if existing_ticket:

            # check whether the ticket exists in Jira
            result = next(iter(TicketService.find_by(
                key=existing_ticket.key,
                limit=1
            )), None)

            # delete local reference
            if not result:
                TicketService.delete(ticket_id=existing_ticket.id)

            # only add comment if not added yet
            if message.object_id not in existing_ticket.outlook_messages_id:
                TicketService.create_comment(
                    issue=existing_ticket,
                    author=message.sender.address,
                    body=O365.message.bs(message.unique_body, 'html.parser').body.text,
                    watchers=emails,
                    attachments=message.attachments
                )

                # append message to history
                self.add_message_to_history(message, existing_ticket)

                current_app.logger.info("New comment added to Jira ticket '{0}'.".format(existing_ticket.key))
            else:
                current_app.logger.info("Skip comment to Jira ticket '{0}' since it has already been added."
                                        .format(existing_ticket.key))
        else:

            # create ticket in Jira and keep local reference
            issue = TicketService.create(

                # Jira fields
                title=message.subject,
                body=O365.message.bs(message.unique_body, 'html.parser').body.text,
                reporter=message.sender.address,
                board='support',
                category='general',
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
            model = TicketService.find_one(key=issue['key'], _model=True)

            # notify ticket reporter about created ticket
            notification = self._notify_reporter(
                message=message,
                key=model.key
            )

            # append message to history
            self.add_message_to_history(
                message=notification,
                model=model
            )

            current_app.logger.info("New ticket created with Jira key '{0}'.".format(model.key, model.id))

    def _get_message(self, message_id):
        """Custom implementation for getting message from id.

        Headers must be included in the request and original implementation
        does not allow.

        Remove this if future implementation of Folder.get_message
        allow kwargs to be passed on to connection.get method.
        """

        # fields to retrieve
        params = {'$select': 'CreatedDateTime,Subject,'
                             'Body,UniqueBody,'
                             'From,ToRecipients,'
                             'BccRecipients,CcRecipients,'
                             'Flag,Importance,'
                             'HasAttachments,Id,ParentFolderId,'
                             'ConversationId,ConversationIndex'}

        # create a dummy folder to get message
        folder = O365.mailbox.Folder(parent=self._mailbox)

        url = folder.build_url(folder._endpoints.get('message').format(id=message_id))
        message = folder.con.get(url, params=params).json()
        message_object = folder.message_constructor(
            parent=folder,
            is_draft=False,
            download_attachments=True,
            **{folder._cloud_data_key: message}
        )

        message_object.folder = folder
        message_object.resource_namespace = message['@odata.id']
        return message_object

    @classmethod
    def _notify_reporter(
            cls, *,
            message: O365.Message,
            key: str
    ):
        """Notify ticket reporter.

        :param message: the reported issue message
        :param key: the ticket key
        """

        # creating notification message to be sent to all recipients
        body = mistune.markdown(TicketService.create_message_body(
            template='notification.j2',
            values={
                'summary': message.subject,
                'key': key,
                'url': current_app.config['TICKET_CLIENT_APP']
            }
        ), hard_wrap=True)

        reply = cls.create_reply(
            message,
            values={
                'body': body,
                'metadata': [dict(
                    name='message',
                    content='jira ticket notification'
                )]
            }
        )
        reply.send()
        return reply

    @staticmethod
    def add_message_to_history(
            message: O365.Message,
            model: Ticket
    ):
        """Add a message to the ticket history."""
        messages_id = model.outlook_messages_id.split(',')
        if message.object_id not in messages_id:
            model.outlook_messages_id = ','.join(messages_id + [message.object_id])
            model.update_at = datetime.datetime.utcnow

    @staticmethod
    def create_reply(
            message: O365.Message,
            values: dict = None
    ):
        """Create a reply message from template."""
        reply = message.reply(to_all=True)

        # process email body with bs
        bs = O365.message.bs

        if reply.body_type.lower() == 'html':
            soup = bs(reply.body, 'html.parser')
            reply_fwd = str(soup.find('div', id='divRplyFwdMsg'))
        else:
            reply_fwd = '\n'.join(reply.body.splitlines()[2:])

        body = TicketService.create_message_body(
            template='reply.j2',
            values={
                'reply': reply_fwd,
                **values
            }
        )

        # replace body of the reply with the processed body
        reply.body = None  # reset body
        reply.body_type = 'html'
        reply.body = body

        return reply

    @staticmethod
    def get_message_json(message: O365.Message):
        """Get json information from message."""
        soup = O365.message.bs(message.unique_body, 'html.parser')

        body = str(soup)

        # get the json data
        data = re.search(r'{.*}', body).group()
        data = json.loads(data)

        return data
