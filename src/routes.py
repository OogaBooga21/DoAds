from flask import Blueprint, render_template, send_file, jsonify, abort, request
from flask import Blueprint, render_template, send_file, jsonify, abort
from flask_login import login_required, current_user
from .models import Task, Lead
from . import db
import io
import json

main_bp = Blueprint('main', __name__)

from .services.leads_from_gmaps import leads_from_gmaps_service
from .services.leads_from_mail import leads_from_mail_service
from .services.auto_offer import auto_offer_service
from .utils.mailing_service import send_email


@main_bp.route('/')
@login_required
def index():
    return render_template('index.html')


@main_bp.route('/tasks')
@login_required
def tasks():
    user_tasks = db.session.execute(
        db.select(Task).filter_by(user_id=current_user.id).order_by(
            Task.created_at.desc())
    ).scalars().all()
    return render_template('tasks.html', tasks=user_tasks)


@main_bp.route('/download_task_output/<int:task_id>')
@login_required
def download_task_output(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        abort(404)

    if task.user_id != current_user.id:
        abort(403)  # Forbidden

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


@main_bp.route('/auto_mail/<int:task_id>', methods=['POST'])
@login_required
def auto_mail(task_id):
    task = db.session.get(Task, task_id)
    if not task or task.user_id != current_user.id:
        abort(404)

    leads = task.leads.all()
    if not leads:
        return jsonify({"success": False, "message": "No leads found for this task."})

    email_subject = "A new opportunity for your business"
    email_body = "Hello, we are a digital marketing agency and we would like to offer you our services."

    for lead in leads:
        if lead.contact_email:
            try:
                send_email(lead.contact_email, email_subject, email_body)
            except Exception as e:
                return jsonify({"success": False, "message": f"Failed to send email: {e}"})

    return jsonify({"success": True, "message": f"Auto-mailing for task {task_id} completed."})


@main_bp.route('/send_generated_email', methods=['POST'])
@login_required
def send_generated_email():
    data = request.get_json()
    subject = data.get('subject')
    body = data.get('body')

    if not all([subject, body]):
        return jsonify({"success": False, "message": "Missing subject or body."}), 400

    # Hardcode the recipient email address
    recipient_email = "moga.olimpiu.biz@gmail.com"

    try:
        send_email(recipient_email, subject, body)
        return jsonify({"success": True, "message": f"Email sent to {recipient_email} successfully."})
    except Exception as e:
        # It's good practice to log the exception
        print(f"Failed to send email: {e}")
        return jsonify({"success": False, "message": "Failed to send email."}), 500





