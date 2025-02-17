from datetime import datetime
from app import db

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    todoist_id = db.Column(db.BigInteger, unique=True, nullable=False)
    tasks = db.relationship('Task', backref='project', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    todoist_id = db.Column(db.BigInteger, unique=True, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    completed_date = db.Column(db.DateTime, nullable=False)
    week = db.Column(db.String(10), nullable=False)  # Format: YYYY-WW

    @classmethod
    def create_from_todoist(cls, task_data, project_id=None):
        completed_date = datetime.fromisoformat(task_data['completed_date'])
        week = completed_date.strftime('%Y-W%W')

        return cls(
            content=task_data['content'],
            todoist_id=task_data['id'],
            project_id=project_id,
            completed_date=completed_date,
            week=week
        )