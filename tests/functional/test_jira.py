class TestJiraSvc:
    def test_content(self, svc, adapter):
        assert svc.content("test") == b"data"
