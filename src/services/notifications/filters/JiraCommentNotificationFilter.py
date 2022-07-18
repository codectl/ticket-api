import re

import requests
import O365.mailbox
from flask import current_app

from src.utils import converters
from src.services.jira import JiraSvc
from src.services.ticket import TicketSvc
from src.services.notifications.filters.OutlookMessageFilter import OutlookMessageFilter
from src.services.notifications.managers.o365_mailbox import O365MailboxManager


class JiraCommentNotificationFilter(OutlookMessageFilter):
    """Filter for messages that represent comments added to tickets.
    The email recipient get notified that a new comment was added to
    the ticket.
    """

    def __init__(self, mailbox: O365.mailbox):
        self.mailbox = mailbox
        self._jira = JiraSvc()

    def apply(self, message):
        if not message:
            return None

        if message.sender.address.split("@")[1] == "automation.atlassian.com":

            # get json content from message
            data = O365MailboxManager.get_message_json(message)

            model = TicketSvc.find_one(key=data["ticket"], _model=True)

            # skip if ticket not defined
            if not model:
                current_app.logger.warning("Commented on ticket that was not found.")
                return None

            # locate last lent message
            last_message_id = model.outlook_messages_id.split(",")[-1]

            try:
                last_message = self.mailbox.get_message(object_id=last_message_id)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == requests.codes.not_found:
                    current_app.logger.warning(
                        "Message to reply to was not found. No email was sent."
                    )
            else:

                # get the specific comment
                comment = self._jira.comment(
                    issue=data["ticket"], comment=data["id"], expand="renderedBody"
                )

                # embed base64 images in message body
                body = re.sub(
                    pattern=r'src="(.*?)"',
                    repl=lambda x: r'src="data:image/jpeg;base64,{}"'.format(
                        converters.encode_content(
                            self._jira.get_content(
                                path=x.group(1), base="{server}{path}"
                            )
                        )
                    ),
                    string=comment.renderedBody,
                )

                # send out the comment message has a reply to the last sent message
                reply = O365MailboxManager.create_reply(
                    message=last_message,
                    values={
                        "body": body,
                        "author": data["author"]["name"],
                        "metadata": [
                            dict(name="message", content="relay jira comment")
                        ],
                    },
                )
                reply.send()

            # delete Jira message since it serves no further purpose
            message.delete()

            return None

        return message
