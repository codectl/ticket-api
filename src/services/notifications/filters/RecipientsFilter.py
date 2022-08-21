import itertools

from flask import current_app

from src.services.notifications.filters.OutlookMessageFilter import OutlookMessageFilter
from src.services.ticket import TicketService


class RecipientsFilter(OutlookMessageFilter):
    """ Filter for message validating its recipients """

    def __init__(self, recipient_reference, sent_folder):
        self.recipient_reference = recipient_reference
        self.sent_folder = sent_folder

    def apply(self, message):
        if not message:
            return None

        # exclude case where recipient is both present in the 'from' recipient field
        # and in any of the other recipient fields. This case will cause a duplicate
        # notification. Therefore exclude the event where the message is sent because
        # the event will be triggered upon message delivery.
        other_recipients = itertools.chain((e.address for e in message.cc),
                                           (e.address for e in message.bcc),
                                           (e.address for e in message.to))
        if self.recipient_reference == message.sender.address and \
                self.recipient_reference in other_recipients and \
                self.sent_folder.folder_id == message.folder_id:
            current_app.logger.info('Message filtered as the notification is a duplicate.'
                                    .format(self.recipient_reference))
            return None

        # check for existing ticket
        existing_ticket = TicketService.find_by(
            outlook_conversation_id=message.conversation_id,
            fetch_one=True
        )

        if not existing_ticket:
            # exclude if new message initiated by the recipient
            if self.recipient_reference == message.sender.address:
                current_app.logger.info('Message filtered as the recipient \'{0}\' '
                                        'is the sender of a new conversation.'
                                        .format(self.recipient_reference))
                return None

            # exclude if new message did not come from the recipient
            # and is not directly sent 'to' recipient (must be in cc or bcc)
            elif self.recipient_reference not in (e.address for e in message.to):
                current_app.logger.info('Message filtered as the recipient \'{0}\' '
                                        'is not in the senders list of a new conversation.'
                                        .format(self.recipient_reference))
                return None

        return message
