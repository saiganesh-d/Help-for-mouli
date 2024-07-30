import requests
import json

class JiraAPI:
    def __init__(self, base_url, email, api_token):
        self.base_url = base_url
        self.auth = (email, api_token)
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.api_endpoint = '/rest/api/3/issue'

    def create_issue(self, project_key, summary, description, issue_type):
        """
        Create a new issue in JIRA.
        :param project_key: Project key in which the issue will be created.
        :param summary: Summary of the issue.
        :param description: Description of the issue.
        :param issue_type: Type of the issue (e.g., 'Task', 'Bug').
        :return: The created issue's key and ID.
        """
        url = self.base_url + self.api_endpoint
        payload = {
            'fields': {
                'project': {
                    'key': project_key
                },
                'summary': summary,
                'description': description,
                'issuetype': {
                    'name': issue_type
                }
            }
        }
        response = requests.post(url, headers=self.headers, auth=self.auth, data=json.dumps(payload))
        if response.status_code == 201:
            issue = response.json()
            return issue['key'], issue['id']
        else:
            print(f"Failed to create issue: {response.status_code} {response.text}")
            return None

    def get_issue(self, issue_key):
        """
        Get the details of an issue in JIRA.
        :param issue_key: Key of the issue to fetch.
        :return: The issue details.
        """
        url = self.base_url + self.api_endpoint + '/' + issue_key
        response = requests.get(url, headers=self.headers, auth=self.auth)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get issue: {response.status_code} {response.text}")
            return None

    def update_issue(self, issue_key, fields):
        """
        Update an existing issue in JIRA.
        :param issue_key: Key of the issue to update.
        :param fields: Fields to update (dictionary).
        :return: None
        """
        url = self.base_url + self.api_endpoint + '/' + issue_key
        payload = {
            'fields': fields
        }
        response = requests.put(url, headers=self.headers, auth=self.auth, data=json.dumps(payload))
        if response.status_code == 204:
            print(f"Issue {issue_key} updated successfully.")
        else:
            print(f"Failed to update issue: {response.status_code} {response.text}")

# Example usage
if __name__ == "__main__":
    # Replace with your JIRA instance details, email, and API token
    jira_url = 'https://your-domain.atlassian.net'
    email = 'your-email@example.com'
    api_token = 'your-api-token'

    # Create an instance of the JiraAPI class
    jira = JiraAPI(jira_url, email, api_token)

    # Replace with your project key, summary, description, and issue type
    project_key = 'PROJECT_KEY'
    summary = 'Example Issue'
    description = 'This is an example issue created via JIRA API'
    issue_type = 'Task'

    # Create a new issue
    created_issue_key, created_issue_id = jira.create_issue(project_key, summary, description, issue_type)
    if created_issue_key:
        print(f"Issue created: {created_issue_key}")

    # Get the created issue details
    if created_issue_key:
        issue = jira.get_issue(created_issue_key)
        if issue:
            print(f"Issue details: {json.dumps(issue, indent=2)}")

    # Update the created issue
    if created_issue_key:
        update_fields = {
            'summary': 'Updated Issue Summary',
            'description': 'Updated description of the issue.'
        }
        jira.update_issue(created_issue_key, update_fields)








import requests
import json

class JiraAPI:
    def __init__(self, base_url, email, api_token):
        self.base_url = base_url
        self.auth = (email, api_token)
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.api_endpoint = '/rest/api/3/issue'

    def create_issue(self, project_key, summary, description, issue_type):
        url = self.base_url + self.api_endpoint
        payload = {
            'fields': {
                'project': {
                    'key': project_key
                },
                'summary': summary,
                'description': description,
                'issuetype': {
                    'name': issue_type
                }
            }
        }
        response = requests.post(url, headers=self.headers, auth=self.auth, data=json.dumps(payload))
        if response.status_code == 201:
            issue = response.json()
            return issue['key'], issue['id']
        else:
            print(f"Failed to create issue: {response.status_code} {response.text}")
            return None

    def get_issue(self, issue_key):
        url = self.base_url + self.api_endpoint + '/' + issue_key
        response = requests.get(url, headers=self.headers, auth=self.auth)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get issue: {response.status_code} {response.text}")
            return None

    def update_issue(self, issue_key, fields):
        url = self.base_url + self.api_endpoint + '/' + issue_key
        payload = {
            'fields': fields
        }
        response = requests.put(url, headers=self.headers, auth=self.auth, data=json.dumps(payload))
        if response.status_code == 204:
            print(f"Issue {issue_key} updated successfully.")
        else:
            print(f"Failed to update issue: {response.status_code} {response.text}")

class JiraBulkAPI:
    def __init__(self, jira_api):
        self.jira_api = jira_api

    def bulk_create_issues(self, issues):
        """
        Create multiple issues in JIRA.
        :param issues: List of dictionaries containing project_key, summary, description, and issue_type.
        :return: List of created issue keys and IDs.
        """
        created_issues = []
        for issue in issues:
            project_key = issue.get('project_key')
            summary = issue.get('summary')
            description = issue.get('description')
            issue_type = issue.get('issue_type')
            result = self.jira_api.create_issue(project_key, summary, description, issue_type)
            if result:
                created_issues.append(result)
        return created_issues

    def bulk_get_issues(self, issue_keys):
        """
        Get details of multiple issues in JIRA.
        :param issue_keys: List of issue keys to fetch.
        :return: List of issue details.
        """
        issues = []
        for issue_key in issue_keys:
            issue = self.jira_api.get_issue(issue_key)
            if issue:
                issues.append(issue)
        return issues

    def bulk_update_issues(self, updates):
        """
        Update multiple issues in JIRA.
        :param updates: List of dictionaries containing issue_key and fields to update.
        :return: None
        """
        for update in updates:
            issue_key = update.get('issue_key')
            fields = update.get('fields')
            self.jira_api.update_issue(issue_key, fields)

# Example usage
if __name__ == "__main__":
    jira_url = 'https://your-domain.atlassian.net'
    email = 'your-email@example.com'
    api_token = 'your-api-token'

    jira = JiraAPI(jira_url, email, api_token)
    jira_bulk = JiraBulkAPI(jira)

    # Bulk create issues
    issues_to_create = [
        {'project_key': 'PROJECT_KEY', 'summary': 'Bulk Issue 1', 'description': 'Bulk description 1', 'issue_type': 'Task'},
        {'project_key': 'PROJECT_KEY', 'summary': 'Bulk Issue 2', 'description': 'Bulk description 2', 'issue_type': 'Bug'}
    ]
    created_issues = jira_bulk.bulk_create_issues(issues_to_create)
    print(f"Created issues: {created_issues}")

    # Bulk get issues
    issue_keys_to_get = [issue[0] for issue in created_issues]  # Extract issue keys from created issues
    fetched_issues = jira_bulk.bulk_get_issues(issue_keys_to_get)
    print(f"Issue details: {json.dumps(fetched_issues, indent=2)}")

    # Bulk update issues
    updates_to_perform = [
        {'issue_key': created_issues[0][0], 'fields': {'summary': 'Updated Bulk Issue 1', 'description': 'Updated bulk description 1'}},
        {'issue_key': created_issues[1][0], 'fields': {'summary': 'Updated Bulk Issue 2', 'description': 'Updated bulk description 2'}}
    ]
    jira_bulk.bulk_update_issues(updates_to_perform)
