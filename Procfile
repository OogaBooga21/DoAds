release: FLASK_APP=app.py flask db upgrade
web: sh -c 'gunicorn --bind 0.0.0.0:$PORT --timeout 240 app:app'