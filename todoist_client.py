import requests
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List
import logging

class TodoistClient:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.todoist.com/sync/v9"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}"
        }

    def get_completed_tasks(self) -> List[Dict]:
        """Fetch all completed tasks from Todoist"""
        try:
            response = requests.get(
                f"{self.base_url}/completed/get_all",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json().get('items', [])
        except requests.RequestException as e:
            logging.error(f"Error fetching completed tasks: {str(e)}")
            return []

    def get_projects(self) -> List[Dict]:
        """Fetch all projects from Todoist"""
        try:
            response = requests.post(
                f"{self.base_url}/sync",
                headers=self.headers,
                json={"sync_token": "*", "resource_types": ["projects"]}
            )
            response.raise_for_status()
            return response.json().get('projects', [])
        except requests.RequestException as e:
            logging.error(f"Error fetching projects: {str(e)}")
            return []

    def process_completed_tasks(self, tasks: List[Dict]) -> pd.DataFrame:
        """Process completed tasks into a pandas DataFrame"""
        if not tasks:
            return pd.DataFrame()

        df = pd.DataFrame(tasks)
        df['completed_date'] = pd.to_datetime(df['completed_date'])
        df['week'] = df['completed_date'].dt.strftime('%Y-W%W')
        return df
