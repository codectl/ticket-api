from flask import current_app

from src.services.notifications.filters.OutlookMessageFilter import OutlookMessageFilter


class SenderEmailBlacklistFilter(OutlookMessageFilter):
    """Filter for message whose sender email is not blacklisted"""

    def __init__(self, blacklist):
        self.blacklist = blacklist

    def apply(self, message):
        if not message:
            return None

        sender = message.sender.address
        if sender in self.blacklist:
            msg = f"Message skipped as the sender's email '{sender}' is blacklisted."
            current_app.logger.info(msg)
            return None
        return message
