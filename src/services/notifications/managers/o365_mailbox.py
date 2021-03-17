import base64
import datetime
import itertools
import json
import re

import jira
import mistune
import O365.mailbox
import requests
from flask import current_app

from src.models.Ticket import Ticket
from src.services.jira import ProxyJIRA as Jira
from src.services.notifications.handlers.JiraNotificationHandler import JiraNotificationHandler
from src.services.ticket import TicketService


class O365MailboxManager:
    """
    Manager for O365 events.
    """

    def __init__(self, mailbox):
        self._mailbox = mailbox
        self._subscriber = None
        self._filters = None
        self._jira = None

    def subscriber(self, subscriber_):
        self._subscriber = subscriber_
        return self

    def filters(self, filters_):
        self._filters = filters_
        return self

    def jira(self, url, user, token):
        self._jira = Jira(url=url,
                          user=user,
                          token=token)
        return self

    def check_for_missing_tickets(self, days):
        """
        Sweep the messages received in the last days to create tickets out of
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

        current_app.logger.info('Found {0} messages to process.'.format(str(len(messages))))

        # process each individual message
        for message in messages:
            self.process_message(message_id=message.object_id)

    def notification_manager(self, **kwargs):
        handler = JiraNotificationHandler(manager=self)

        # set inbox/sent folder
        inbox_folder = self._mailbox.inbox_folder()
        sent_folder = self._mailbox.sent_folder()

        # define subscriptions
        inbox_subscription_id = self._subscriber.subscribe(resource=inbox_folder)
        sent_subscription_id = self._subscriber.subscribe(resource=sent_folder)
        subscriptions = [inbox_subscription_id, sent_subscription_id]

        self._subscriber.create_event_channel(subscriptions=subscriptions,
                                              notification_handler=handler,
                                              **kwargs)

    def process_message(self, message_id):
        """
        Process a message (given its Id) for the creation of a ticket.
        """

        # reading message from the corresponding folder
        # and create Jira ticket for it.
        message = self._get_message(message_id=message_id)
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

        owner_email = message.sender.address

        # check for existing ticket
        existing_ticket = TicketService.find_by(
            outlook_conversation_id=message.conversation_id,
            fetch_one=True
        )

        # add new comment if ticket already exists.
        # create new ticket otherwise.
        if existing_ticket:

            # check whether the ticket exists in Jira
            # if so, the ticket has been deleted
            try:
                self._jira.find('issue/{0}', ids=existing_ticket.jira_ticket_key)
            except jira.exceptions.JIRAError as e:
                if e.status_code == requests.codes.not_found:
                    TicketService.delete(ticket_id=existing_ticket.id)
                    return
                else:
                    raise e

            # only add comment if not added yet.
            # happens in case checking for missing tickets.
            if message.object_id not in existing_ticket.outlook_messages_id:
                self._jira.add_comment(issue=existing_ticket.jira_ticket_key,
                                       body=self._create_comment(message),
                                       is_internal=True)

                # append message to history
                self.add_message_to_history(message, existing_ticket)

                current_app.logger.info("New comment added to Jira ticket '{0}'."
                                        .format(existing_ticket.jira_ticket_key))
            else:
                current_app.logger.info("Skip comment to Jira ticket '{0}' since it has already been added."
                                        .format(existing_ticket.jira_ticket_key))
        else:
            # creation of new ticket:
            # 1. Adding ticket to Jira
            # 2. Create ticket entry in local database
            users = self._jira.search_users(user=owner_email)

            # set reporter. If user is invalid, reporter
            # is set to 'Anonymous'.
            reporter_id = getattr(next(iter(users), None), 'accountId', None)

            # set priority between 'high' and 'low', if requested.
            # otherwise unset it.
            priority = message.importance.value.capitalize() \
                if message.importance.value in ['high', 'low'] else 'None'

            issue = self._jira.create_issue(summary=message.subject,
                                            description=self._create_comment(message),
                                            reporter=dict(id=reporter_id),
                                            project=dict(key=current_app.config['JIRA_TICKET_BOARD_KEY']),
                                            issuetype=dict(name=current_app.config['JIRA_TICKET_TYPE']),
                                            labels=current_app.config['JIRA_TICKET_LABELS'],
                                            priority=dict(name=priority))

            # adding attachments
            for attachment in message.attachments:
                if attachment.content is not None:
                    self._jira.add_attachment(issue=issue.key,
                                              attachment=base64.b64decode(attachment.content),
                                              filename=attachment.name)
                    current_app.logger.debug('Added attachment \'{0}\' to ticket \'{1}\'.'
                                             .format(attachment.name, issue.key))

            # adding watchers
            emails = itertools.chain((e.address for e in message.cc),
                                     (e.address for e in message.bcc),
                                     (e.address for e in message.to))

            # add watchers iff has permission
            if self._jira.has_permissions(permissions=['MANAGE_WATCHERS'],
                                          issueKey=issue.key):
                for email in emails:
                    user = next(iter(self._jira.search_users(user=email)), None)
                    if user is not None:

                        # check whether watcher has permissions to watch the issue
                        try:
                            self._jira.add_watcher(issue=issue.key,
                                                   watcher=user.accountId)
                        except jira.exceptions.JIRAError as e:
                            if e.status_code == requests.codes.unauthorized:
                                current_app.logger.warning('Watcher \'{0}\' has no permission to watch issue \'{1}\'.'
                                                           .format(user.displayName, issue.key))
                            else:
                                raise e

            ticket = TicketService.create(
                jira_ticket_key=issue.key,
                jira_ticket_url='{0}/browse/{1}'.format(current_app.config['ATLASSIAN_URL'], issue.key),
                outlook_message_id=message.object_id,
                outlook_message_url=message.resource_namespace,
                outlook_conversation_id=message.conversation_id,
                outlook_messages_id=message.object_id,
                owner_email=owner_email
            )

            # send email to ticket owner about created ticket
            notification = self._notify_ticket_owner(received_message=message,
                                                     ticket=ticket)

            # append message to history
            self.add_message_to_history(notification, ticket)

            current_app.logger.info("New ticket created with Jira key '{0}'. (internal id: '{1}')."
                                    .format(issue.key, ticket.id))

    def _get_message(self, message_id):
        """
        Custom implementation for getting message from id.
        Headers must be included in the request and original implementation
        does not allow. Remove this if future implementation of Folder.get_message
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
        message_object = folder.message_constructor(parent=folder,
                                                    is_draft=False,
                                                    download_attachments=True,
                                                    **{folder._cloud_data_key: message})

        message_object.folder = folder
        message_object.resource_namespace = message['@odata.id']
        return message_object

    def _create_comment(self, message):
        """
        Create comment for the Jira ticket

        :param message: the message to build description from
        :return: the comment
        """

        raw_description = O365.message.bs(message.unique_body, 'html.parser').body.text

        def resolve_username(email):
            """
            Resolve email into a Jira mention, if user exists.
            Otherwise return link to the email.

            :param email: the email
            :return: the resolved email
            """

            users = self._jira.search_users(user=email)
            account_id = getattr(next(iter(users), None), 'accountId', None)
            if account_id is not None:
                return '[~accountid:{0}]'.format(account_id)
            return ''.join(('[', email, ';|', 'mailto:', email, ']'))

        comment_from = 'From  {0}'.format(resolve_username(message.sender.address))
        comment_cc = 'Cc  {0}'.format(
            ' '.join(resolve_username(e.address) for e in message.cc)) if message.cc else ''
        comment = '\n'.join((comment_from, comment_cc, raw_description))
        return comment

    @classmethod
    def _notify_ticket_owner(cls, *, received_message, ticket):
        """
        Notify ticket owner about ticket creation.

        :param Message received_message: the reported issue message
        :param Ticket ticket: the created ticket
        """

        def email_template():
            client_app_ticket = "{0}/jira/tickets?board=mailbox-tickets&q={1}".format(
                current_app.config['TICKET_CLIENT_APP'],
                ticket.jira_ticket_key)
            return \
                'Dear HPDA user,\n' \
                '\n' \
                'In regards to the reported issue __{0}__, the ticket [{1}]({2}) was created.<br/>' \
                'Please track the progress of the issue in our [HPDA Portal]({3}).\n' \
                '\n' \
                'Best regards,<br/>' \
                'HPDA Support Team'.format(
                    received_message.subject,
                    ticket.jira_ticket_key,
                    client_app_ticket,
                    client_app_ticket)

        # creating notification message to be sent to all recipients
        body = mistune.markdown(email_template(), escape=False).strip()
        reply = cls.create_reply(received_message,
                                 data=dict(body=body),
                                 metadata=[dict(name='message', content='jira ticket notification')])
        reply.send()
        return reply

    @staticmethod
    def add_message_to_history(message, ticket):
        """ Add a message to the ticket history """

        messages_id = ticket.outlook_messages_id.split(',')
        if message.object_id not in messages_id:
            ticket.outlook_messages_id = ','.join(messages_id + [message.object_id])
            ticket.update_at = datetime.datetime.utcnow

    @staticmethod
    def create_reply(message, data=None, metadata=None):
        """ Create a reply message to a given message with a given body. """

        reply = message.reply(to_all=True)

        # process email body with bs
        bs = O365.message.bs
        body = bs(data['body'], 'html.parser')

        # process body of the reply with bs
        sep = bs().new_tag('div', style="border-top:solid #E1E1E1 1.0pt; "
                                        "padding:3.0pt 0in 0in 0in;")
        if reply.body_type.lower() == 'html':
            soup = bs(reply.body, 'html.parser')
            soup.find('hr').decompose()
            soup.find('div', id='divRplyFwdMsg').wrap(sep)
        else:
            content = '\n'.join(reply.body.splitlines()[2:])
            soup = bs('<html>'
                      '<head><meta name="reply"></head>'
                      '<body><div>{0}</div></body>'
                      '</html>'.format(content))
            soup.find('div').wrap(sep)

        # wrap the body in a div
        wrapper = soup.new_tag('div')
        wrapper.append(body)
        soup.body.div.insert_before(wrapper)

        if data.get('author'):
            author_tag = soup.new_tag('div', style='margin-top: 10px;')
            author_tag.string = data['author']['name']
            author_tag.append(bs('<div>&nbsp;</div>', 'html.parser'))
            soup.body.div.insert_after(author_tag)

        # add metadata
        for meta in metadata or []:
            soup.head('meta')[-1].insert_after(soup.new_tag('meta', attrs=meta))

        # replace body of the reply with the processed body
        reply.body = None  # reset body
        reply.body_type = 'html'
        reply.body = str(soup)

        return reply

    @staticmethod
    def extract_ticket_data(message):
        """ Get information about a ticket from an email Jira notification """

        soup = O365.message.bs(message.unique_body, 'html.parser')

        # remove the external message warning
        soup.find('div', id='x_extban1').decompose()
        body = str(soup)
        body = body.replace('\n', '').replace('\r', '').replace('\\', '')

        # get the json data
        data = re.search(r'{.*}', body).group()
        data = json.loads(data)

        return data
