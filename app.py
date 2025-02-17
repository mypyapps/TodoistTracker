import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# initialize the db with the app
db.init_app(app)

with app.app_context():
    import models  # noqa: F401
    db.create_all()

# import and register the dashboard
from dashboard import init_dashboard
app = init_dashboard(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)