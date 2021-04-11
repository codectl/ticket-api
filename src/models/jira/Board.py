from flask import current_app


class Board:
    def __init__(self,
                 key=None,
                 board_id=None,
                 name=None,
                 board_type=None,
                 project=None,
                 **kwargs):
        self.key = key
        self.board_id = board_id or kwargs.get('id')
        self.name = name
        self.board_type = board_type or kwargs.get('board_type')
        self.project = project or kwargs.get('location')

    @property
    def filter(self):
        # prevent import loop
        from src.services.jira import JiraService

        jira = JiraService()
        return jira.get_board_filter(self.board_id)

    @classmethod
    def default(cls):
        # prevent import loop
        from src.services.jira import JiraService

        jira = JiraService()
        return jira.find_board(key=current_app.config['JIRA_DEFAULT_BOARD']['key'])

