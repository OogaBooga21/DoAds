release: FLASK_APP=app.py flask db upgrade
web: gunicorn --bind 0.0.0.0:$PORT --timeout 240 app:app