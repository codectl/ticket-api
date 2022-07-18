class Board:
    def __init__(self, key: str = None, raw: dict = None):
        self.key = key
        self.id = raw["id"]
        self.name = raw["name"]
        self.raw = raw

    @property
    def filter(self):
        # prevent import loop
        from src.services.jira import JiraSvc

        return JiraSvc().get_board_filter(board_id=self.id)
