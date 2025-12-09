from flask import Blueprint, render_template, send_file, jsonify, abort, request
from flask import Blueprint, render_template, send_file, jsonify, abort
from flask_login import login_required, current_user
from .models import Task, Lead, Email
from . import db
import io
import json

main_bp = Blueprint('main', __name__)

from .services.leads_from_gmaps import leads_from_gmaps_service
from .services.leads_from_mail import leads_from_mail_service
from .services.auto_offer import auto_offer_service
from .services.manual_lead import manual_lead_service
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


@main_bp.route('/emails')
@login_required
def emails():
    user_emails = db.session.execute(
        db.select(Email).join(Lead).join(Task).filter(Task.user_id == current_user.id).order_by(
            Email.sent_at.desc())
    ).scalars().all()
    return render_template('emails.html', emails=user_emails)


@main_bp.route('/related_emails/<email>')
@login_required
def related_emails(email):
    related_emails = db.session.execute(
        db.select(Email).join(Lead).join(Task).filter(Task.user_id == current_user.id, Email.recipient_email == email).order_by(
            Email.sent_at.desc())
    ).scalars().all()
    return render_template('related_emails.html', emails=related_emails, recipient=email)


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


@main_bp.route('/manual_lead', methods=['POST'])
@login_required
def manual_lead():
    return manual_lead_service()


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


@main_bp.route('/send_generated_email/<int:task_id>/<int:result_index>', methods=['POST'])
@login_required
def send_generated_email(task_id, result_index):
    task = db.session.get(Task, task_id)
    if not task or task.user_id != current_user.id:
        abort(404)

    lead = task.leads.first()
    if not lead:
        return jsonify({"success": False, "message": "No lead found for this task."}), 404

    data = request.get_json()
    subject = data.get('subject')
    body = data.get('body')

    if not all([subject, body]):
        return jsonify({"success": False, "message": "Missing subject or body."}), 400

    try:
        # Create and save the email object
        new_email = Email(
            lead_id=lead.id,
            subject_line=subject,
            content=body,
            recipient_email=lead.contact_email,
            status='GENERATED'
        )
        db.session.add(new_email)
        db.session.commit()

        html_body = body.replace('\n', '<br>')
        send_email(lead.contact_email, subject, html_body)

        new_email.status = 'SENT'
        db.session.commit()

        return jsonify({"success": True, "message": f"Email sent successfully."})
    except Exception as e:
        # It's good practice to log the exception
        print(f"Failed to send email: {e}")
        db.session.rollback()
        return jsonify({"success": False, "message": "Failed to send email."}), 500





