from flask import current_app

from src.services.notifications.filters.OutlookMessageFilter import OutlookMessageFilter
from src.services.notifications.managers.o365_mailbox import MessageManager
from src.services.ticket import TicketService


class ValidateMetadataFilter(OutlookMessageFilter):
    """ Filter message based on metadata present in the message"""

    def apply(self, message):
        if not message:
            return None

        soup = message.get_body_soup()

        if soup is None or soup.head is None:
            return message
        else:

            # append message to history if jira metadata is present
            ticket = TicketService.find_by(
                outlook_conversation_id=message.conversation_id,
                fetch_one=True
            )

            # ignore the notification email sent to user after the creation of a new ticket
            if soup.head.find('meta', attrs={'name': 'message', 'content': 'jira ticket notification'}):
                MessageManager.add_message_to_history(message, ticket)
                current_app.logger.info('Message filtered as this is a message notification to the user about created ticket.')
                return None

            # ignore the message sent when a new comment is added to the ticket
            elif soup.head.find('meta', attrs={'name': 'message', 'content': 'relay jira comment'}):
                MessageManager.add_message_to_history(message, ticket)
                current_app.logger.info('Message filtered as this is a relay message from a Jira comment.')
                return None
            else:
                return message
