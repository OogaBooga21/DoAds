from flask import Blueprint, render_template, send_file, jsonify, abort
from flask_login import login_required, current_user
from .models import Task # Import the Task model
from . import db # Import the db instance
import io
import json

main_bp = Blueprint('main', __name__)

from .services.leads_from_gmaps import leads_from_gmaps_service
from .services.leads_from_mail import leads_from_mail_service
from .services.auto_offer import auto_offer_service


@main_bp.route('/')
@login_required 
def index():
    return render_template('index.html')

@main_bp.route('/tasks')
@login_required
def tasks():
    user_tasks = db.session.execute(
        db.select(Task).filter_by(user_id=current_user.id).order_by(Task.created_at.desc())
    ).scalars().all()
    return render_template('tasks.html', tasks=user_tasks)

@main_bp.route('/download_task_output/<int:task_id>')
@login_required
def download_task_output(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        abort(404)

    if task.user_id != current_user.id:
        abort(403) # Forbidden

    if not task.output:
        return jsonify({"error": "No output available for this task."}), 404

    # Assuming task.output is already a JSON object/dict
    # Convert it to a JSON string for the file
    json_string = json.dumps(task.output, indent=2, ensure_ascii=False)
    
    # Create a BytesIO object from the JSON string
    buffer = io.BytesIO(json_string.encode('utf-8'))
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype="application/json",
        as_attachment=True,
        download_name=f"task_{task_id}_output.json"
    )

@main_bp.route('/run_from_gmaps', methods=['POST'])
@login_required 
def run_from_gmaps():
    return leads_from_gmaps_service()
    
@main_bp.route('/run_from_mail', methods=['POST'])
@login_required 
def run_from_mail():
    return leads_from_mail_service()

@main_bp.route('/auto_offer', methods=['POST'])
@login_required 
def auto_offer():
    return auto_offer_service()