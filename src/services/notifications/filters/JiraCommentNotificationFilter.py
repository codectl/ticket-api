import requests
from flask import current_app
import O365.mailbox

from src.services.ticket import TicketService
from src.services.notifications.filters.OutlookMessageFilter import OutlookMessageFilter
from src.services.notifications.managers.o365_mailbox import O365MailboxManager


class JiraCommentNotificationFilter(OutlookMessageFilter):
    """ Filter for messages that represent comments added to tickets.
    The email recipient get notified that a new comment was added to the ticket. """

    def __init__(self, mailbox: O365.mailbox):
        self.mailbox = mailbox

    def apply(self, message):
        if not message:
            return None

        if message.sender.address.split('@')[1] == 'automationforjira.com':

            # extract the info from the Jira notification message
            data = O365MailboxManager.extract_ticket_data(message)

            ticket = TicketService.find_by(
                jira_ticket_key=data['ticket'],
                fetch_one=True
            )

            # skip if ticket not defined
            if not ticket:
                current_app.logger.warning('Commented on ticket that was not found.')
                return None

            # locate last lent message
            last_message_id = ticket.outlook_messages_id.split(',')[-1]
            try:
                last_message = self.mailbox.get_message(object_id=last_message_id)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == requests.codes.not_found:
                    current_app.logger.warning('Message to reply to was not found. No email was sent.')
            else:

                # send out the comment message has a reply to the last sent message
                reply = O365MailboxManager.create_reply(message=last_message,
                                                        data=data,
                                                        metadata=[dict(name='message', content='relay jira comment')])
                reply.send()

            # delete Jira message since it serves no further purpose
            message.delete()

            return None

        return message
