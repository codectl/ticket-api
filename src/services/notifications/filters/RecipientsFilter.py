import itertools

from flask import current_app

from src.services.notifications.filters.OutlookMessageFilter import OutlookMessageFilter
from src.services.ticket import TicketSvc


class RecipientsFilter(OutlookMessageFilter):
    """Filter for message validating its recipients"""

    def __init__(self, email, sent_folder):
        self.email = email
        self.sent_folder = sent_folder

    def apply(self, message):
        if not message:
            return None

        # exclude case where recipient is both present in the 'from' recipient field
        # and in any of the other recipient fields. This case will cause a duplicate
        # notification. Therefore, exclude the event where the message is sent because
        # the event will be triggered upon message delivery.
        other_recipients = itertools.chain(
            (e.address for e in message.cc),
            (e.address for e in message.bcc),
            (e.address for e in message.to),
        )
        if (
            self.email == message.sender.address
            and self.email in other_recipients
            and self.sent_folder.folder_id == message.folder_id
        ):
            msg = "Message filtered as the notification is a duplicate."
            current_app.logger.info(msg)
            return None

        # check for existing ticket
        cid = message.conversation_id
        existing_ticket = TicketSvc.find_one(outlook_conversation_id=cid, _model=True)

        if not existing_ticket:
            # exclude if new message initiated by the recipient
            if self.email == message.sender.address:
                current_app.logger.info(
                    f"Message filtered as the recipient '{self.email}' "
                    "is the sender of a new conversation."
                )
                return None

            # exclude if new message did not come from the recipient
            # and is not directly sent 'to' recipient (must be in cc or bcc)
            elif self.email not in (e.address for e in message.to):
                current_app.logger.info(
                    f"Message filtered as the recipient '{self.email}' "
                    "is not in the senders list of a new conversation."
                )
                return None

        return message
