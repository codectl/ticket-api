class Board:
    def __init__(self, key: str = None, raw: dict = None, is_default: bool = False):
        self.key = key
        self.raw = raw
        self.is_default = is_default
        self.id = raw["id"]
        self.name = raw["name"]

    @property
    def filter(self):
        from src.services.jira import JiraSvc

        svc = JiraSvc()
        config = svc.board_configuration(board_id=self.id)
        return svc.filter(id=config["permission"]["id"])
