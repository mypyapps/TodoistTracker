
from app import app

# Make the application object available for gunicorn
application = app.server

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
