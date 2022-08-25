import re
import functools

import requests
import O365.mailbox
from flask import current_app

from src import utils
from src.services.jira import JiraSvc
from src.services.notifications.filters.base import OutlookMessageFilter
from src.services.notifications.handlers.jira import JiraNotificationHandler
from src.services.ticket import TicketSvc


class JiraCommentNotificationFilter(OutlookMessageFilter):
    """Filter for messages that represent comments added to tickets. The email
    recipient gets notified whenever a new comment has been added to the ticket.
    """

    def __init__(self, folder: O365.mailbox.Folder):
        self.folder = folder

    def apply(self, message):
        if not message:
            return None

        if message.sender.address.split("@")[1] == "automation.atlassian.com":
            svc = JiraSvc()

            # load message json payload
            payload = utils.message_json(message)

            model = TicketSvc.find_one(key=payload["ticket"], _model=True)
            if not model:
                current_app.logger.warning("Commented on ticket that was not found.")
                return None

            # locate last lent message to reply on
            last_message_id = model.outlook_messages_id.split(",")[-1]
            try:
                last_message = self.folder.get_message(object_id=last_message_id)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == requests.codes.not_found:
                    msg = "Message to reply to was not found. No email was sent."
                    current_app.logger.warning(msg)
            else:

                # locate the specific comment given the
                comment = svc.comment(
                    issue=payload["ticket"],
                    comment=payload["id"],
                    expand="renderedBody",
                )

                # embed base64 images under RFC2397
                scheme = "data:image/jpeg;base64"
                encode = utils.encode_content
                data = functools.partial(svc.content, base="{server}{path}")
                body = re.sub(
                    pattern=r'src="(.*?)"',
                    repl=lambda m: f"src='{scheme},{encode(data(path=m.group(1)))}'",
                    string=comment.renderedBody,
                )

                # send out the comment message has a reply to the last sent message
                metadata = {"name": "message", "content": "relay jira comment"}
                reply = JiraNotificationHandler.create_reply(
                    message=last_message,
                    values={
                        "body": body,
                        "author": payload["author"]["name"],
                        "metadata": [metadata],
                    },
                )
                reply.send()

            # delete message since it serves no further purpose
            message.delete()

            return None

        return message
