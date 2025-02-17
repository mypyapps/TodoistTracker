import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
from datetime import datetime
import logging

from todoist_client import TodoistClient
from utils import get_week_ranges, get_project_names, filter_tasks
from config import TODOIST_API_TOKEN, CACHE_TIMEOUT
from models import Task, Project
from app import db

def init_dashboard(server):
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

    def sync_todoist_data():
        """Sync data from Todoist to database"""
        try:
            # Fetch and store projects
            todoist_projects = todoist_client.get_projects()
            for proj_data in todoist_projects:
                project = Project.query.filter_by(todoist_id=proj_data['id']).first()
                if not project:
                    project = Project(
                        todoist_id=proj_data['id'],
                        name=proj_data['name']
                    )
                    db.session.add(project)
            db.session.commit()

            # Fetch and store tasks
            tasks = todoist_client.get_completed_tasks()
            for task_data in tasks:
                task = Task.query.filter_by(todoist_id=task_data['id']).first()
                if not task:
                    project = Project.query.filter_by(todoist_id=task_data['project_id']).first()
                    task = Task.create_from_todoist(task_data, project.id if project else None)
                    db.session.add(task)
            db.session.commit()
        except Exception as e:
            logging.error(f"Error syncing data: {str(e)}")

    # Layout
    app.layout = dbc.Container([
        dcc.Interval(
            id='sync-interval',
            interval=CACHE_TIMEOUT * 1000,  # Convert to milliseconds
            n_intervals=0
        ),

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
        Output('sync-interval', 'disabled'),
        Input('sync-interval', 'n_intervals')
    )
    def sync_data(n):
        if n is not None:
            sync_todoist_data()
        return False

    @app.callback(
        [Output('week-dropdown', 'options'),
         Output('week-dropdown', 'value'),
         Output('project-dropdown', 'options'),
         Output('project-dropdown', 'value')],
        [Input('sync-interval', 'n_intervals')]
    )
    def update_dropdowns(n):
        weeks = db.session.query(Task.week).distinct().order_by(Task.week).all()
        week_options = [{'label': week[0], 'value': week[0]} for week in weeks]

        projects = Project.query.all()
        project_options = [{'label': p.name, 'value': p.id} for p in projects]

        return week_options, weeks[-1][0] if weeks else None, project_options, None

    @app.callback(
        [Output('tasks-graph', 'figure'),
         Output('tasks-table', 'children')],
        [Input('week-dropdown', 'value'),
         Input('project-dropdown', 'value')]
    )
    def update_dashboard(selected_week, selected_project):
        query = Task.query

        if selected_week:
            query = query.filter(Task.week == selected_week)
        if selected_project:
            query = query.filter(Task.project_id == selected_project)

        tasks = query.all()

        # Create DataFrame for visualization
        df = pd.DataFrame([{
            'week': task.week,
            'content': task.content,
            'completed_date': task.completed_date,
            'project_name': task.project.name if task.project else 'No Project'
        } for task in tasks])

        # Create graph
        if not df.empty:
            fig = px.bar(
                df.groupby('week').size().reset_index(),
                x='week',
                y=0,
                title='Completed Tasks by Week',
                labels={'week': 'Week', '0': 'Number of Tasks'}
            )
        else:
            fig = px.bar(
                pd.DataFrame({'week': [], 'count': []}),
                x='week',
                y='count',
                title='No Tasks Found'
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
                        html.Td(row['project_name'])
                    ]) for _, row in df.iterrows()
                ])
            ],
            bordered=True,
            hover=True,
            responsive=True,
            striped=True,
            className="mt-4"
        )

        return fig, table

    return app