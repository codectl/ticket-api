from flask import current_app
from jira import JIRA
from jira.resources import User

__all__ = ['JiraService']


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

    def my_permissions(self, project_key=None, project_id=None, issue_key=None, issue_id=None, permissions=None):
        """
            Introduced param permissions.
            Overridden method.

        :param project_key: see overridden method
        :param project_id: see overridden method
        :param issue_key: see overridden method
        :param issue_id: see overridden method
        :param permissions: limit returned permissions to the specified permissions.
                            Change introduce by Jira as per early 2020.
        """
        params = {}
        if project_key is not None:
            params['projectKey'] = project_key
        if project_id is not None:
            params['projectId'] = project_id
        if issue_key is not None:
            params['issueKey'] = issue_key
        if issue_id is not None:
            params['issueId'] = issue_id
        if permissions is not None:
            params['permissions'] = permissions
        return self._get_json('mypermissions', params=params)

    def search_users(self, user, start_at=0, limit=50,
                     include_active=True, include_inactive=False):
        """
            Change from 'username' to 'query' after some Jira API update:
            "The query parameter 'username' is not supported in GDPR strict mode."
            Overridden method.
        """
        params = {
            'query': user,
            'includeActive': include_active,
            'includeInactive': include_inactive
        }
        return self._fetch_pages(User, None, 'user/search',
                                 startAt=start_at, maxResults=limit, params=params)

    @staticmethod
    def create_jql_query(q=None, key=None, filters=None, assignee=None,
                         status=None, watcher=None, expand=None,
                         sort=None):
        """
            Build jql query based on a provided searching parameters.

        :param q: the text search.
        :param key: the Jira ticket key
        :param filters: the query filters. Comma separated values.
        :param assignee: the key assignee.
        :param status: the status key.
        :param watcher: the watcher key.
        :param expand: the expand field.
        :param sort: the sort criteria. Could have the value 'created'.
        """
        jql = ''

        if q:
            jql += '&summary ~ \'' + q + '\''
        if key:
            jql += '&key = ' + q
        if filters:
            jql += '&filter in ({0})'.format(filters)
        if assignee:
            jql += '&assignee=' + assignee
        if status:
            jql += '&status=\'' + status + '\''
        if watcher:
            jql += '&watcher=' + watcher
        if expand:
            jql += '&expand=' + expand
        if sort:
            jql += ' ORDER BY ' + sort

        return jql.lstrip('&')


class JiraService(ProxyJIRA):
    """
        Service to handle Jira operations
    """

    def __init__(self, **kwargs):
        super().__init__(url=current_app.config['ATLASSIAN_URL'],
                         user=current_app.config['ATLASSIAN_USER'],
                         token=current_app.config['ATLASSIAN_API_TOKEN'],
                         **kwargs)
