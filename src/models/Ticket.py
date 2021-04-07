import datetime

from flask_restplus import fields

from src import api, db


class Ticket(db.Model):
    __tablename__ = 'tickets'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String, nullable=False)
    jira_ticket_key = db.Column(db.String, unique=True, nullable=False, index=True)
    jira_ticket_url = db.Column(db.String, unique=True, nullable=False)
    outlook_message_id = db.Column(db.String, unique=True, nullable=False)
    outlook_message_url = db.Column(db.String, unique=True, nullable=False)
    outlook_conversation_id = db.Column(db.String, unique=True, nullable=False)
    outlook_messages_id = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    reporter = db.Column(db.String, nullable=False)


class TicketDTO:
    ticket = api.model('ticket', {
        'jira-key': fields.String(attribute='jira_ticket_key', description='Jira ticket key'),
        'jira-url': fields.String(attribute='jira_ticket_url', description='Jira ticket url'),
        'category': fields.String(description='category'),
        'created-at': fields.String(attribute='created_at', description='created at'),
        'updated-at': fields.String(attribute='updated_at', description='updated at'),
        'reporter': fields.String(description='user reporter')
    })
