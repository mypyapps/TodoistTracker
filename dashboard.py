import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
from flask import Flask
import logging
from datetime import datetime

from todoist_client import TodoistClient
from utils import get_week_ranges, get_project_names, filter_tasks
from config import TODOIST_API_TOKEN, CACHE_TIMEOUT

# Initialize Flask and Dash
server = Flask(__name__)
app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[
        "https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css"
    ],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

# Initialize Todoist client
todoist_client = TodoistClient(TODOIST_API_TOKEN)

# Cache for data
cache = {
    'last_update': None,
    'tasks_df': None,
    'projects': None
}

def get_cached_data():
    """Get cached data or fetch new data if cache expired"""
    now = datetime.now()
    if (not cache['last_update'] or 
        (now - cache['last_update']).total_seconds() > CACHE_TIMEOUT):
        
        tasks = todoist_client.get_completed_tasks()
        cache['tasks_df'] = todoist_client.process_completed_tasks(tasks)
        cache['projects'] = todoist_client.get_projects()
        cache['last_update'] = now

    return cache['tasks_df'], cache['projects']

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Todoist Completed Tasks Dashboard", 
                   className="text-center mb-4 mt-3")
        ])
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Select Week"),
                            dcc.Dropdown(
                                id='week-dropdown',
                                placeholder="Select a week"
                            )
                        ], md=6),
                        dbc.Col([
                            html.Label("Select Project"),
                            dcc.Dropdown(
                                id='project-dropdown',
                                placeholder="Select a project"
                            )
                        ], md=6)
                    ])
                ])
            ], className="mb-4")
        ])
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Spinner(
                dcc.Graph(id='tasks-graph'),
                color="primary",
                type="border"
            )
        ])
    ]),

    dbc.Row([
        dbc.Col([
            html.Div(id='tasks-table', className="mt-4")
        ])
    ])
], fluid=True)

@app.callback(
    [Output('week-dropdown', 'options'),
     Output('week-dropdown', 'value'),
     Output('project-dropdown', 'options'),
     Output('project-dropdown', 'value')],
    [Input('interval-component', 'n_intervals')]
)
def update_dropdowns(n):
    tasks_df, projects = get_cached_data()
    
    weeks = get_week_ranges(tasks_df)
    week_options = [{'label': week, 'value': week} for week in weeks]
    
    project_dict = get_project_names(projects)
    project_options = [
        {'label': name, 'value': pid} 
        for pid, name in project_dict.items()
    ]
    
    return week_options, weeks[-1] if weeks else None, project_options, None

@app.callback(
    [Output('tasks-graph', 'figure'),
     Output('tasks-table', 'children')],
    [Input('week-dropdown', 'value'),
     Input('project-dropdown', 'value')]
)
def update_dashboard(selected_week, selected_project):
    tasks_df, projects = get_cached_data()
    
    filtered_df = filter_tasks(tasks_df, selected_week, selected_project)
    
    # Create graph
    fig = px.bar(
        filtered_df.groupby('week').size().reset_index(),
        x='week',
        y=0,
        title='Completed Tasks by Week',
        labels={'week': 'Week', '0': 'Number of Tasks'}
    )
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    # Create table
    table = dbc.Table(
        [
            html.Thead([
                html.Tr([
                    html.Th("Task"),
                    html.Th("Completed Date"),
                    html.Th("Project")
                ])
            ]),
            html.Tbody([
                html.Tr([
                    html.Td(row['content']),
                    html.Td(row['completed_date'].strftime('%Y-%m-%d')),
                    html.Td(get_project_names(projects).get(row['project_id'], ''))
                ]) for _, row in filtered_df.iterrows()
            ])
        ],
        bordered=True,
        hover=True,
        responsive=True,
        striped=True,
        className="mt-4"
    )
    
    return fig, table
