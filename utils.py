from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd

def get_week_ranges(df: pd.DataFrame) -> List[str]:
    """Get list of week ranges from DataFrame"""
    if df.empty:
        return []
    weeks = df['week'].unique()
    weeks.sort()
    return weeks.tolist()

def get_project_names(projects: List[Dict]) -> Dict[int, str]:
    """Convert project list to id->name mapping"""
    return {project['id']: project['name'] for project in projects}

def filter_tasks(df: pd.DataFrame, selected_week: str = None, 
                selected_project: int = None) -> pd.DataFrame:
    """Filter tasks based on week and project"""
    if df.empty:
        return df

    filtered_df = df.copy()
    
    if selected_week:
        filtered_df = filtered_df[filtered_df['week'] == selected_week]
    
    if selected_project:
        filtered_df = filtered_df[filtered_df['project_id'] == selected_project]
    
    return filtered_df
