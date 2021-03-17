from flask import current_app
from o365_notifications.base import (
    O365Notification,
    O365NotificationsHandler
)


class JiraNotificationHandler(O365NotificationsHandler):
    """ Handler for Jira """

    def __init__(self, manager):
        self.manager = manager
        super().__init__()

    def process(self, notification):
        """
        Process an incoming notification.
        If notification is of type Message, create a new Jira ticket.
        This handler deals with notifications from emails arriving
        to the inbox and sent folder.

        :param notification: the incoming notification
        :type notification: O365Notification
        """

        # when a notification is received...
        if notification.type == O365Notification.Type.NOTIFICATION.value:

            # log 'Missed' notifications
            if notification.change_type == O365Notification.ChangeType.MISSED.value:
                current_app.logger.warning("Notification missed: {0}".format(vars(notification)))

            # create Jira ticket for 'Message' notifications
            elif notification.resource_data.get('@odata.type') == O365Notification.ResourceType.MESSAGE.value:

                # folder represents any folder from subscriptions list (inbox)
                self.manager.process_message(message_id=notification.resource_data.get('Id'))
