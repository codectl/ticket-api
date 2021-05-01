import jira.client
import collections.abc


class CaseInsensitiveDict(dict):

    def __init__(self, *args, **kw):
        super(CaseInsensitiveDict, self).__init__(*args, **kw)

        for key, value in self.copy().items():
            if key != key.lower():
                self[key.lower()] = value
                self.pop(key, None)


# monkey-patching for Jira package
jira.client.CaseInsensitiveDict = CaseInsensitiveDict
jira.client.collections = collections.abc
