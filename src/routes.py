from flask import Blueprint, render_template, send_file, jsonify, abort, request, Response, current_app, redirect, url_for
from flask_login import login_required, current_user
from .models import Task, Lead, Email
from . import db
import io
import json
from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.orm.attributes import flag_modified
import queue
import threading
import time

main_bp = Blueprint('main', __name__)

from .utils.status_utils import status_updates, send_status_update
from .services.leads_from_gmaps import leads_from_gmaps_service
from .services.leads_from_gmaps_no_website import leads_from_gmaps_no_website_service
from .services.leads_from_mail import leads_from_mail_service
from .services.auto_offer import auto_offer_service
from .services.manual_lead import manual_lead_service
from .utils.mailing_service import send_email, process_inbound_email, process_transactional_event

def run_in_background(target, *args, **kwargs):
    """Runs a function in a background thread with app context."""
    app = current_app._get_current_object()
    def wrapper(*args, **kwargs):
        with app.app_context():
            target(*args, **kwargs)
    thread = threading.Thread(target=wrapper, args=args, kwargs=kwargs)
    thread.start()

@main_bp.route('/task_status/<int:task_id>')
def task_status(task_id):
    def generate():
        while True:
            try:
                update = status_updates.get(timeout=30) # Timeout to prevent hanging
                if update['task_id'] == task_id:
                    if update['message'] == "CLOSE":
                        yield f"data: {json.dumps({'message': 'CLOSE'})}\n\n"
                        break
                    yield f"data: {json.dumps(update)}\n\n"
            except queue.Empty:
                # Send a keep-alive comment every so often to prevent timeout
                yield ": keep-alive\n\n"
                
    return Response(generate(), mimetype='text/event-stream')


@main_bp.route('/brevo-webhook', methods=['POST'])
def brevo_webhook():
    data = request.get_json()

    # Differentiate between inbound replies and transactional events
    if 'items' in data and data.get('items'): # Inbound Reply Webhook
        for item in data['items']:
            process_inbound_email(item)
    elif 'event' in data: # Transactional Event Webhook
        process_transactional_event(data)
        
    return jsonify({"success": True}), 200


@main_bp.route('/')
@login_required
def index():
    return render_template('index.html')


@main_bp.route('/tasks')
@login_required
def tasks():
    page = request.args.get('page', 1, type=int)
    pagination = db.paginate(
        db.select(Task).filter_by(user_id=current_user.id).order_by(
            Task.created_at.desc()),
        page=page, 
        per_page=30
    )
    return render_template('tasks.html', pagination=pagination)


@main_bp.route('/emails')
@login_required
def emails():
    page = request.args.get('page', 1, type=int)
    tab = request.args.get('tab', 'sent') # Default to 'sent' tab

    if tab == 'sent':
        query = db.select(Email).join(Lead).join(Task).filter(
            Task.user_id == current_user.id,
            Email.direction == 'OUTBOUND'
        ).order_by(Email.sent_at.desc())
    elif tab == 'replied':
        query = db.select(Email).join(Lead).join(Task).filter(
            Task.user_id == current_user.id,
            Email.direction == 'OUTBOUND',
            Email.status == 'REPLIED'
        ).order_by(Email.sent_at.desc())
    else:
        # Optional: handle invalid tab parameter, e.g., redirect or show an error
        return "Invalid tab", 404

    pagination = db.paginate(query, page=page, per_page=30)
    
    return render_template('emails.html', pagination=pagination, current_tab=tab)


@main_bp.route('/delete_email/<int:email_id>', methods=['POST'])
@login_required
def delete_email(email_id):
    email = db.session.get(Email, email_id)
    if not email:
        abort(404)

    # Optional: Check if the email belongs to the current user to prevent unauthorized deletion
    if email.lead.task.user_id != current_user.id:
        abort(403)

    db.session.delete(email)
    db.session.commit()
    
    # Redirect back to the emails page, maintaining the current tab
    return redirect(url_for('main.emails', tab=request.args.get('tab', 'sent')))


@main_bp.route('/related_emails/<email>')
@login_required
def related_emails(email):
    related_emails = db.session.execute(
        db.select(Email).join(Lead).join(Task).filter(
            Task.user_id == current_user.id,
            or_(Email.recipient_email == email, Email.sender_email == email)
        ).order_by(Email.sent_at.asc())
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
    form = request.form
    queries = form["query"].strip().splitlines()
    task_ids = []

    for query in queries:
        if not query:
            continue

        new_task = Task(
            user_id=current_user.id, 
            status='RUNNING', 
            query=query,
            language=form["prompt_language"],
            offer=form.get("offer"),
            tone=form.get("tone"),
            additional_instructions=form.get("additional_instructions")
        )
        db.session.add(new_task)
        db.session.commit()

        task_args = {
            "task_id": new_task.id,
            "user_id": current_user.id,
            "api_key": current_app.config['OPENAI_API_KEY'],
            "form_data": {**form.to_dict(), "query": query} # Pass the single query
        }
        
        run_in_background(leads_from_gmaps_service, **task_args)
        task_ids.append(new_task.id)

    return jsonify({"task_ids": task_ids})


@main_bp.route('/run_from_gmaps_no_website', methods=['POST'])
@login_required
def run_from_gmaps_no_website():
    form = request.form
    queries = form["query"].strip().splitlines()
    task_ids = []

    for query in queries:
        if not query:
            continue

        new_task = Task(
            user_id=current_user.id, 
            status='RUNNING', 
            query=f"NO_WEBSITE: {query}",
            language="N/A",
            offer="N/A",
            tone="N/A",
            additional_instructions="N/A"
        )
        db.session.add(new_task)
        db.session.commit()

        task_args = {
            "task_id": new_task.id,
            "user_id": current_user.id,
            "api_key": current_app.config['OPENAI_API_KEY'],
            "form_data": {**form.to_dict(), "query": query}
        }
        
        run_in_background(leads_from_gmaps_no_website_service, **task_args)
        task_ids.append(new_task.id)

    return jsonify({"task_ids": task_ids})


@main_bp.route('/run_from_mail', methods=['POST'])
@login_required
def run_from_mail():
    form = request.form
    files = request.files.getlist('email_files')
    task_ids = []

    for file in files:
        if not file:
            continue

        new_task = Task(
            user_id=current_user.id, 
            status='RUNNING', 
            query="Mail to Lead",
            language=form["prompt_language"],
            offer=form.get("offer"),
            tone=form.get("tone"),
            additional_instructions=form.get("additional_instructions")
        )
        db.session.add(new_task)
        db.session.commit()

        task_args = {
            "task_id": new_task.id,
            "user_id": current_user.id,
            "api_key": current_app.config['OPENAI_API_KEY'],
            "form_data": form.to_dict(),
            "email_file": file.read().decode('utf-8')
        }
        
        run_in_background(leads_from_mail_service, **task_args)
        task_ids.append(new_task.id)

    return jsonify({"task_ids": task_ids})


@main_bp.route('/auto_offer', methods=['POST'])
@login_required
def auto_offer():
    form = request.form
    new_task = Task(
        user_id=current_user.id, 
        status='RUNNING', 
        query=f"Auto-Offer for {form['url']}",
        language='ro_prompt.txt', # Hardcoded as per service prompt
        offer=form.get("additional_info") # Using 'additional_info' as offer for this task type
    )
    db.session.add(new_task)
    db.session.commit()

    task_args = {
        "task_id": new_task.id,
        "user_id": current_user.id,
        "api_key": current_app.config['OPENAI_API_KEY'],
        "form_data": form.to_dict()
    }

    run_in_background(auto_offer_service, **task_args)
    return jsonify({"task_id": new_task.id})


@main_bp.route('/manual_lead', methods=['POST'])
@login_required
def manual_lead():
    form = request.form
    new_task = Task(
        user_id=current_user.id, 
        status='RUNNING', 
        query=f"Manual Lead: {form['company_name']}",
        language=form["prompt_language"],
        offer=form.get("offer"),
        tone=form.get("tone"),
        additional_instructions=form.get("additional_instructions")
    )
    db.session.add(new_task)
    db.session.commit()

    task_args = {
        "task_id": new_task.id,
        "user_id": current_user.id,
        "api_key": current_app.config['OPENAI_API_KEY'],
        "form_data": form.to_dict()
    }

    run_in_background(manual_lead_service, **task_args)
    return jsonify({"task_id": new_task.id})


@main_bp.route('/auto_mail/<int:task_id>', methods=['POST'])
@login_required
def auto_mail(task_id):
    task = db.session.get(Task, task_id)
    if not task or task.user_id != current_user.id:
        abort(404)

    leads = task.leads.all()
    if not leads:
        return jsonify({"success": False, "message": "No leads found for this task."}), 404

    email_subject = "A new opportunity for your business"
    email_body = "Hello, we are a digital marketing agency and we would like to offer you our services."

    for lead in leads:
        if lead.contact_email:
            try:
                send_email(lead.contact_email, email_subject, email_body)
            except Exception as e:
                return jsonify({"success": False, "message": f"Failed to send email: {e}"}), 500

    return jsonify({"success": True, "message": f"Auto-mailing for task {task_id} completed."})


@main_bp.route('/send_bulk_emails/<int:task_id>', methods=['POST'])
@login_required
def send_bulk_emails(task_id):
    task = db.session.get(Task, task_id)
    if not task or task.user_id != current_user.id:
        abort(404)

    data = request.get_json()
    emails_to_send = data.get('emails', [])

    if not emails_to_send:
        return jsonify({"success": False, "message": "No emails selected to send."}), 400

    lead = task.leads.first()
    if not lead:
        return jsonify({"success": False, "message": "No lead found for this task."}), 404

    sent_count = 0
    failed_count = 0

    for email_data in emails_to_send:
        subject = email_data.get('subject')
        body = email_data.get('body')
        recipient_email = email_data.get('email')

        if not all([subject, body, recipient_email]):
            failed_count += 1
            continue

        try:
            new_email = Email(
                lead_id=lead.id,
                subject_line=subject,
                content=body,
                recipient_email=recipient_email,
                sender_email=current_user.email,
                status='GENERATED'
            )
            db.session.add(new_email)
            db.session.commit()

            html_body = body.replace('\n', '<br>')
            message_id = send_email(recipient_email, subject, html_body)

            new_email.status = 'SENT'
            new_email.sent_at = datetime.utcnow()
            new_email.brevo_message_id = message_id
            db.session.commit()
            sent_count += 1
        except Exception as e:
            print(f"Failed to send email to {recipient_email}: {e}")
            db.session.rollback()
            failed_count += 1

    return jsonify({
        "success": True,
        "message": f"Sent {sent_count} emails. {failed_count} failed."
    })


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
    recipient_email = data.get('email')

    if not all([subject, body, recipient_email]):
        return jsonify({"success": False, "message": "Missing subject, body, or email."}), 400

    try:
        # Create and save the email object
        new_email = Email(
            lead_id=lead.id,
            subject_line=subject,
            content=body,
            recipient_email=recipient_email,
            sender_email=current_user.email,
            status='GENERATED'
        )
        db.session.add(new_email)
        db.session.commit()

        html_body = body.replace('\n', '<br>')
        message_id = send_email(recipient_email, subject, html_body)

        new_email.status = 'SENT'
        new_email.sent_at = datetime.utcnow()
        new_email.brevo_message_id = message_id
        db.session.commit()

        return jsonify({"success": True, "message": "Email sent successfully."})
    except Exception as e:
        # It's good practice to log the exception
        print(f"Failed to send email: {e}")
        db.session.rollback()
        return jsonify({"success": False, "message": "Failed to send email."}), 500


@main_bp.route('/update_email_body/<int:task_id>/<int:result_index>', methods=['POST'])
@login_required
def update_email_body(task_id, result_index):
    task = db.session.get(Task, task_id)
    if not task or task.user_id != current_user.id:
        abort(404)

    data = request.get_json()
    new_body = data.get('body')

    if new_body is None:
        return jsonify({"success": False, "message": "No new body provided."}), 400

    try:
        # Modify the JSON data in the output field
        task.output['results'][result_index]['email_body'] = new_body
        
        # Mark the 'output' field as modified so SQLAlchemy detects the change
        flag_modified(task, "output")
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify({"success": True, "message": "Email content updated successfully."})
    except (IndexError, KeyError) as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating email body due to invalid structure: {e}")
        return jsonify({"success": False, "message": "Invalid task data structure."}), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating email body: {e}")
        return jsonify({"success": False, "message": "An internal error occurred."}), 500

