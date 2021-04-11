class Board:
    def __init__(self,
                 board_id=None,
                 name=None,
                 board_type=None,
                 project=None,
                 **kwargs):
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
