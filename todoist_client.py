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

        processed_tasks = []
        for task in tasks:
            try:
                # Ensure completed_date exists and is in the correct format
                if 'completed_date' not in task:
                    logging.warning(f"Task {task.get('content', 'Unknown')} missing completed_date")
                    continue

                if isinstance(task.get('completed_date'), str):
                    completed_date = pd.to_datetime(task['completed_date'])
                    task['completed_date'] = completed_date
                else:
                    logging.warning(f"Task {task.get('content', 'Unknown')} has invalid completed_date format")
                    continue
                task['week'] = completed_date.strftime('%Y-W%W')
                processed_tasks.append(task)
            except Exception as e:
                logging.error(f"Error processing task {task.get('content', 'Unknown')}: {str(e)}")
                continue

        if not processed_tasks:
            return pd.DataFrame()

        return pd.DataFrame(processed_tasks)