from src.services.jira import JiraService


class Board:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.key = kwargs.get('key')
        self.display_key = kwargs.get('display_key')
        self.display_name = kwargs.get('display_name')
        self.description = kwargs.get('description')
        self.project_key = kwargs.get('project_key')

    @property
    def filter(self):
        jira = JiraService()
        return jira.get_board_filter(self.id)
