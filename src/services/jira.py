from jira import JIRA
from jira.resources import User


class ProxyJIRA(JIRA):
    """
    Proxy class for Jira
    """

    def __init__(self, **kwargs):
        url = kwargs.pop('url')
        user = kwargs.pop('user')
        token = kwargs.pop('token')
        super().__init__(server=url,
                         basic_auth=(user, token),
                         **kwargs)

    def has_permissions(self, permissions, **kwargs):
        """
        Check whether the signed user has the given permissions.
        """
        jira_permissions = self.my_permissions(permissions=','.join(permissions), **kwargs)
        return all(jira_permissions['permissions'][permission]['havePermission'] for permission in permissions)

    def my_permissions(self, projectKey=None, projectId=None, issueKey=None, issueId=None, permissions=None):
        """
        Override method.
        Introduced param permissions:
        :param permissions: limit returned permissions to the specified permissions.
            Change introduce by Jira as per early 2020.
        """
        params = {}
        if projectKey is not None:
            params['projectKey'] = projectKey
        if projectId is not None:
            params['projectId'] = projectId
        if issueKey is not None:
            params['issueKey'] = issueKey
        if issueId is not None:
            params['issueId'] = issueId
        if permissions is not None:
            params['permissions'] = permissions
        return self._get_json('mypermissions', params=params)

    def search_users(self, user, startAt=0, maxResults=50, includeActive=True, includeInactive=False):
        """
        Override method.
        Change from 'username' to 'query' after some Jira API update:
            "The query parameter 'username' is not supported in GDPR strict mode."
        """
        params = {
            'query': user,
            'includeActive': includeActive,
            'includeInactive': includeInactive
        }
        return self._fetch_pages(User, None, 'user/search', startAt, maxResults, params)
