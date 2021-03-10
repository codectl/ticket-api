import json
import logging
import requests
from abc import abstractmethod
from enum import Enum

from O365.utils import ApiComponent
from O365.mailbox import MailBox, Folder

logger = logging.getLogger(__name__)


class Notification(ApiComponent):
    """ Notification representation """

    class Type(Enum):
        NOTIFICATION = '#Microsoft.OutlookServices.Notification'
        STREAMING_SUBSCRIPTION = '#Microsoft.OutlookServices.StreamingSubscription'
        KEEP_ALIVE_NOTIFICATION = '#Microsoft.OutlookServices.KeepAliveNotification'

    class ResourceType(Enum):
        MESSAGE = '#Microsoft.OutlookServices.Message'
        EVENT = '#Microsoft.OutlookServices.Event'

    class ChangeType(Enum):
        ACKNOWLEDGEMENT = 'Acknowledgment'
        CREATED = 'Created'
        DELETED = 'Deleted'
        MISSED = 'Missed'
        UPDATED = 'Updated'

    def __init__(self, parent=None, **kwargs):
        self.parent = parent
        protocol = parent.protocol

        super().__init__(protocol=protocol, **kwargs)

        self.type = kwargs.get('@odata.type')
        self.subscription_id = kwargs.get(self._cc('id'))
        self.resource = kwargs.get(self._cc('resource'))
        self.change_type = kwargs.get(self._cc('changeType'))
        if kwargs.get(self._cc('resourceData')):
            self.resource_data = dict(**kwargs.get(self._cc('resourceData')))


class StreamingNotification(Notification):
    """ Streaming implementation for Notification """

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)


class NotificationHandler:
    """ Handler meant to deal with incoming notifications """

    @abstractmethod
    def process(self, notification):
        """
        Process a notification.
        Override as this function simply prints the given notification.
        """
        logger.debug(vars(notification))


class Subscription(ApiComponent):
    """ Subscription representation for Push Notification Service """

    def __init__(self, *, parent=None, con=None, **kwargs):
        # connection is only needed if you want to communicate with the api provider
        self.con = getattr(parent, 'con', con)
        self.parent = parent if issubclass(type(parent), Subscription) else None

        protocol = kwargs.get('protocol') or getattr(parent, 'protocol', None)
        main_resource = kwargs.get('main_resource') or getattr(parent, 'main_resource', None)

        super().__init__(protocol=protocol, main_resource=main_resource)

        self.name = kwargs.get('name', getattr(parent, 'name', None))
        self.change_type = kwargs.get('change_type', getattr(parent, 'change_type', None))
        self.subscribed_resources = []

    @property
    def request_type(self):
        raise NotImplementedError('Subclasses must implement this method.')

    def subscribe(self, *, resource):
        raise NotImplementedError('Subclasses must implement this method.')

    def renew_subscriptions(self):
        """ Renew subscriptions """
        logger.info("Renew subscription for {0}".format(str(self.subscribed_resources)))
        subscriptions = [self.subscribe(resource=resource) for resource in self.subscribed_resources]
        logger.info("Renewed subscriptions are {0}".format(str(subscriptions)))
        return subscriptions


class StreamingSubscription(Subscription):
    """ Streaming implementation for Subscription """

    _endpoints = {
        'subscriptions': '/subscriptions',
        'notifications': '/GetNotifications'
    }
    _request_type = '#Microsoft.OutlookServices.StreamingSubscription'
    streaming_notification_constructor = StreamingNotification

    # Streaming connection settings
    _default_connection_timeout_in_minutes = 120  # Equivalent to 2 hours
    _default_keep_alive_notification_interval_in_seconds = 5

    def __init__(self, *, parent=None, con=None, **kwargs):
        super().__init__(parent=parent, con=con, **kwargs)

    @property
    def request_type(self):
        return self._request_type

    @abstractmethod
    def resource_namespace(self, resource):
        """
        Get the full resource namespace for
        a given resource.

        :param resource: the subscribable resource
        :return the resource namespace
        """
        return resource

    def subscribe(self, *, resource):
        """
        Subscribing to a given resource.

        :param: resource: the resource to subscribe to
        :return: the subscription id
        """
        url = self.build_url(self._endpoints.get('subscriptions'))

        if resource not in self.subscribed_resources:
            self.subscribed_resources.append(resource)
        resource_namespace = self.resource_namespace(resource)

        data = dict()
        data['@odata.type'] = self.request_type
        data[self._cc('resource')] = resource_namespace
        data[self._cc('changeType')] = self.change_type

        try:
            response = self.con.post(url, data)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == requests.codes.too_many_requests:
                logger.warning('Too many requests...')
                logger.info(str(e.response.headers))
                logger.warning('Raising exception...')
                raise e
        else:
            if not response:
                return None

            notification = response.json()

            logger.debug("Subscribed to resource {0}: Response: {1}".format(resource, notification))
            return notification['Id']

    def listen_to_notifications(self, *, subscriptions, notification_handler=None,
                                connection_timeout=_default_connection_timeout_in_minutes,
                                keep_alive_interval=_default_keep_alive_notification_interval_in_seconds,
                                refresh_after_expire=False):
        """
        Listen to new notifications.

        :param subscriptions: subscription id's to listen to
        :param notification_handler: the notifications handler
        :param int connection_timeout: time in minutes in which connection closes
        :param int keep_alive_interval: time interval in seconds in which a message is sent
        :param bool refresh_after_expire: refresh when http connection expires
        """
        if not subscriptions:
            raise ValueError('Can\'t start streaming connection without subscription.')
        elif not isinstance(subscriptions, list):
            subscriptions = [subscriptions]

        notification_handler = notification_handler or NotificationHandler
        url = self.build_url(self._endpoints.get('notifications'))

        data = dict()
        data[self._cc('connectionTimeoutInMinutes')] = connection_timeout
        data[self._cc('keepAliveNotificationIntervalInSeconds')] = keep_alive_interval
        data[self._cc('subscriptionIds')] = subscriptions

        logger.info('Start listening for events ...')
        while True:
            try:
                response = self.con.post(url, data, stream=True)
                logger.debug('Start streaming cycle ...')

            # Renew subscriptions if 404 is raised
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == requests.codes.not_found:
                    logger.info('Expired subscription. Renewing subscriptions...')
                    data[self._cc('subscriptionIds')] = self.renew_subscriptions()
                    logger.info('Renewed subscriptions: {0}'.format(data[self._cc('subscriptionIds')]))
                    continue
                else:
                    raise e
            else:
                if not response:
                    return

            # Use 'with' clause to prevent requests.exceptions.ChunkedEncodingError.
            # Exception occurs when connection is closed by the server causing
            # partially reading the request body.
            with response:
                stream_data = b''
                bracket_control = []
                for starting_chunk in response.iter_content(chunk_size=1):
                    # Reading json group values...
                    if starting_chunk == b'[':
                        bracket_control.append(starting_chunk)
                        try:
                            for chunk in response.iter_content(chunk_size=1):
                                # Grouping json objects
                                if chunk == b'{':
                                    bracket_control.append(chunk)
                                elif chunk == b'}':
                                    bracket_control.remove(b'{')
                                elif chunk == b']':
                                    bracket_control.remove(b'[')

                                # Control to see if json object is complete
                                if b'{' in bracket_control:
                                    stream_data += chunk
                                elif b'[' in bracket_control:
                                    if stream_data:
                                        stream_data += b'}'
                                        notification = self.streaming_notification_constructor(
                                            parent=self, **json.loads(stream_data.decode('utf-8')))
                                        notification_handler.process(notification)
                                        stream_data = b''
                                else:
                                    # Break outer loop
                                    bracket_control.append(True)
                                    break  # Connection timed out

                        except Exception as e:
                            if isinstance(e, requests.exceptions.ChunkedEncodingError):
                                # Seem like empty values through the connection causing
                                # the communication to be corrupted. When that happens,
                                # the loop is interrupted and the streaming is restarted.
                                logger.warning("Exception suppressed: {0}".format(e))
                                break
                            else:
                                raise e
                    if bracket_control:
                        # Break loop since all data is read
                        break

            # Automatically refresh HTTP connection after it expires
            if refresh_after_expire:
                logger.debug('Refreshing connection ...')
            else:
                break

        logger.info('Stopped listening for events: connection closed.')


class MailBoxStreamingSubscription(StreamingSubscription):
    """ Streaming implementation for MailBox Subscription """

    subscription_constructor = StreamingSubscription

    def __init__(self, *, parent, **kwargs):
        """ Mailbox Streaming Subscription

        :param parent: parent mailbox for this subscription
        :type parent: Mailbox
        :param kwargs: any extra args to be passed to the StreamingSubscription instance
        :raises ValueError: if parent is not instance of Mailbox
        """
        if not isinstance(parent, MailBox):
            raise ValueError("'parent' must be instance of Mailbox")

        super().__init__(parent=parent, **kwargs)

    def resource_namespace(self, resource):
        """
        Get the full resource namespace for
        the folder resource.

        :param Folder resource: the resource
        :return: the full resource namespace
        """
        if not isinstance(resource, Folder):
            raise ValueError("'resource' must be instance of Folder")

        return resource.build_url(resource._endpoints.get('folder_messages').format(
            id=resource.folder_id) if resource else resource._endpoints.get('root_messages'))
