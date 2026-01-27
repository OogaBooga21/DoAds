import queue

# Queue for status updates
status_updates = queue.Queue()

def send_status_update(task_id, message):
    """Adds a status update to the queue."""
    status_updates.put({'task_id': task_id, 'message': message})
