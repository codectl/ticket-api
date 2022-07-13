from flask import current_app

from src.services.notifications.filters.OutlookMessageFilter import OutlookMessageFilter


class SenderEmailDomainWhitelistedFilter(OutlookMessageFilter):
    """Filter for message whose sender email domain is whitelisted"""

    def __init__(self, whitelisted_domains):
        self.whitelisted_domains = whitelisted_domains

    def apply(self, message):
        if not message:
            return None

        sender_email = message.sender.address
        if sender_email.split("@")[1] not in self.whitelisted_domains:
            current_app.logger.info(
                f"Message skipped as the sender's email '{sender_email}' is not whitelisted."
            )
            return None
        return message
