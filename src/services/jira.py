from flask import current_app
from jira import JIRA
from jira.resources import Dashboard, User

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

    def search_boards(self, name=None, limit=5):
        """
        Search for dashboards.
        """
        params = {
            'dashboardName': 'HPC',
        }
        return self._fetch_pages(Dashboard, 'values', 'dashboard/search', startAt=0, maxResults=limit, params=params)

    def get_board_configuration(self, board_id) -> dict:
        """
        Get the configuration from a given board

        :param board_id: the id of the board
        :return: the board configuration
        """
        url = self._get_url("board/{0}/configuration".format(board_id), base=self.AGILE_BASE_URL)
        return self._session.get(url).json()

    def get_board_filter(self, board_id):
        """
        Get the filter from a board's configuration

        :param board_id: the id of the board
        :return: the board filter
        """
        configuration = self.get_board_configuration(board_id=board_id)
        return self.filter(configuration.get('filter', {}).get('id'))

    @staticmethod
    def create_jql_query(boards=None, q=None, key=None, assignee=None,
                         status=None, watcher=None, expand=None,
                         sort=None):
        """
            Build jql query based on a provided searching parameters.

        :param boards: the boards to get tickets from.
        :param q: the text search.
        :param key: the Jira ticket key
        :param assignee: the key assignee.
        :param status: the status key.
        :param watcher: the watcher key.
        :param expand: the expand field.
        :param sort: the sort criteria. Could have the value 'created'.
        """
        jql = ''

        if boards:
            jql += '&filter in ({0})'.format(boards)
        if q:
            jql += '&summary ~ \'' + q + '\''
        if key:
            jql += '&key = ' + q
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
