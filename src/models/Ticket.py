import datetime

from src import db


class Ticket(db.Model):
    __tablename__ = 'tickets'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String, unique=True, nullable=False, index=True)
    outlook_message_id = db.Column(db.String, unique=True)
    outlook_message_url = db.Column(db.String, unique=True)
    outlook_conversation_id = db.Column(db.String, unique=True)
    outlook_messages_id = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    reporter = db.Column(db.String, nullable=False)
