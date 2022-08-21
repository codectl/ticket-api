import datetime

from src import db


class Ticket(db.Model):
    __tablename__ = 'tickets'

    id = db.Column(db.Integer, primary_key=True)
    jira_ticket_key = db.Column(db.String, unique=True, nullable=False)
    jira_ticket_url = db.Column(db.String, unique=True, nullable=False)
    outlook_message_id = db.Column(db.String, unique=True, nullable=False)
    outlook_message_url = db.Column(db.String, unique=True, nullable=False)
    outlook_conversation_id = db.Column(db.String, unique=True, nullable=False)
    outlook_messages_id = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    owner_email = db.Column(db.String, nullable=False)
