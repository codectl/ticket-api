import datetime

from flask_restplus import fields

from src import api, db


class Ticket(db.Model):
    __tablename__ = 'tickets'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String, nullable=False)
    jira_ticket_key = db.Column(db.String, unique=True, nullable=False)
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
        'jira_key': fields.String(attribute='jira_ticket_key', description='Jira ticket key'),
        'jira_url': fields.String(attribute='jira_ticket_url', description='Jira ticket url'),
        'created_at': fields.String(description='created at'),
        'updated_at': fields.String(description='updated at'),
        'reporter': fields.String(description='user reporter')
    })
