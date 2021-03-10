import datetime
from sqlalchemy import Column, Integer, String, DateTime

from hpdasupport import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True)
    jira_ticket_key = Column(String, unique=True, nullable=False)
    jira_ticket_url = Column(String, unique=True, nullable=False)
    outlook_message_id = Column(String, unique=True, nullable=False)
    outlook_message_url = Column(String, unique=True, nullable=False)
    outlook_conversation_id = Column(String, unique=True, nullable=False)
    outlook_messages_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    owner_email = Column(String, nullable=False)
