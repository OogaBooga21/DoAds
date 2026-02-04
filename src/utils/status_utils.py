import json
from flask import current_app

def send_status_update(task_id, message):
    """Publishes a status update to a Redis channel."""
    try:
        redis_conn = current_app.redis_conn
        channel = f'task_status:{task_id}'
        payload = json.dumps({'task_id': task_id, 'message': message})
        redis_conn.publish(channel, payload)
    except RuntimeError:
        # This can happen if the status update is called from a place
        # where there is no app context.
        # In a real-world scenario, you would want to handle this more gracefully.
        print(f"Could not send status update for task {task_id}: No application context.")