from src import create_app

def execute_job_with_context(func, *args, **kwargs):
    """
    Creates a Flask app context and executes the given function 
    within that context.
    """
    app = create_app()
    with app.app_context():
        return func(*args, **kwargs)
