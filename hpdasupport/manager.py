import logging

from O365 import Account, MSOffice365Protocol

import hpdasupport.hpdasupport as hpdasupport
from hpdasupport import config, manager
from hpdasupport.subscription import MailBoxStreamingSubscription, Notification

logger = logging.getLogger(__name__)


class Manager:

    @staticmethod
    def default_account():
        credentials = (config['CLIENT_ID'], None)
        protocol = MSOffice365Protocol(api_version='beta')
        return Account(credentials,
                       protocol=protocol,
                       tenant_id=config['TENANT_ID'],
                       main_resource=config['MAILBOX_SUPPORT'],
                       request_retries=0)  # no retries when request fails (getting rid of 429 HTTP error)

    @staticmethod
    @manager.command
    def authenticate(account=None):
        """
        Set authorization code used for OAuth2 authentication.
        """
        if not account:
            account = Manager.default_account()

        if not account.is_authenticated:
            account.authenticate(tenant_id=config['TENANT_ID'],
                                 scopes=config['SCOPES'])
        logger.info('Authenticated successfully.')

    @staticmethod
    def _hpda_support_configuration():
        """
        Get default configuration for the HPDA support ticket system.
        """
        account = Manager.default_account()
        Manager.authenticate(account)
        mailbox = account.mailbox()

        mailbox_subscriber = MailBoxStreamingSubscription(parent=mailbox,
                                                          change_type=Notification.ChangeType.CREATED.value)

        # Change Id alias to the real id for the 'RecipientsFilter' object
        sent_folder = mailbox.sent_folder()
        sent_folder = sent_folder.get_folder(folder_id=sent_folder.folder_id)

        # Filling the HPDA Support object
        support = hpdasupport.HPDASupport(mailbox=mailbox) \
            .subscriber(mailbox_subscriber) \
            .jira(url=config['ATLASSIAN_URL'],
                  user=config['ATLASSIAN_USER'],
                  token=config['ATLASSIAN_API_TOKEN']) \
            .filters([
                hpdasupport.SenderEmailDomainWhitelistedFilter(whitelisted_domains=config['EMAIL_WHITELISTED_DOMAINS']),
                hpdasupport.SenderEmailBlacklistFilter(blacklist=config['EMAIL_BLACKLIST']),
                hpdasupport.RecipientsFilter(recipient_reference=config['MAILBOX_SUPPORT'], sent_folder=sent_folder),
                hpdasupport.ValidateMetadataFilter(),
                hpdasupport.JiraCommentNotificationFilter(mailbox=mailbox)
            ])

        return support

    @staticmethod
    @manager.command
    def listen_for_incoming_email():
        """
        Listen for incoming email to the HPC email inbox folder.
        """
        support = Manager._hpda_support_configuration()

        # Start listening for incoming notifications...
        support.listen_to_notifications(connection_timeout=config['CONNECTION_TIMEOUT_IN_MINUTES'],
                                        keep_alive_interval=config['KEEP_ALIVE_NOTIFICATION_INTERVAL_IN_SECONDS'],
                                        refresh_after_expire=True)

    @staticmethod
    @manager.arg('days', help='number of days to search back')
    @manager.command
    def check_for_missing_tickets(days=1):
        """
        Check for possible tickets that went missing in the last days.
        """
        support = Manager._hpda_support_configuration()

        # Start listening for incoming notifications...
        support.check_for_missing_tickets(days=days)

    @staticmethod
    def main():
        manager.main()
