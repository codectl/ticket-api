from flask import current_app

from src.services.notifications.filters.base import OutlookMessageFilter


class SenderEmailDomainWhitelistedFilter(OutlookMessageFilter):
    """Filter for message whose sender email domain is whitelisted"""

    def __init__(self, whitelisted_domains):
        self.whitelisted_domains = whitelisted_domains

    def apply(self, message):
        if not message:
            return None

        sender = message.sender.address
        if sender.split("@")[1] not in self.whitelisted_domains:
            current_app.logger.info(
                f"Message skipped as the sender's email '{sender}' is not whitelisted."
            )
            return None
        return message
