class TestJiraSvc:
    def test_content(self, svc):
        assert svc.content("version") == b"data"
