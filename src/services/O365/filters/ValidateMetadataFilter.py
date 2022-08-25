from flask import current_app

from src.services.O365.filters.base import OutlookMessageFilter
from src.services.O365.handlers.jira import JiraNotificationHandler
from src.services.ticket import TicketSvc


class ValidateMetadataFilter(OutlookMessageFilter):
    """Filter message based on metadata present in the message"""

    def apply(self, message):
        if not message:
            return None

        soup = message.get_body_soup()

        if soup is None or soup.head is None:
            return message
        else:

            # append message to history if jira metadata is present
            opts = {"outlook_conversation_id": message.conversation_id, "_model": True}
            model = TicketSvc.find_one(**opts)

            # ignore the notification email sent to user after the creation of a ticket
            if soup.head.find("meta", attrs={"content": "jira ticket notification"}):
                JiraNotificationHandler.add_message_to_history(message, model=model)
                current_app.logger.info(
                    "Message filtered as this is a message notification to the user "
                    "about created ticket."
                )
                return None

            # ignore the message sent when a new comment is added to the ticket
            elif soup.head.find("meta", attrs={"content": "relay jira comment"}):
                JiraNotificationHandler.add_message_to_history(message, model=model)
                current_app.logger.info(
                    "Message filtered as this is a relay message from a Jira comment."
                )
                return None
            else:
                return message
