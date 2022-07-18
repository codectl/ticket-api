class Board:
    def __init__(self, key: str = None, raw: dict = None, is_default: bool = False):
        self.key = key
        self.raw = raw
        self.is_default = is_default
        self.id = raw["id"]
        self.name = raw["name"]

    @property
    def filter(self):
        # prevent import loop
        from src.services.jira import JiraSvc

        return JiraSvc().board_filter(board_id=self.id)
