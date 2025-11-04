from flask import Blueprint, render_template
from flask_login import login_required

main_bp = Blueprint('main', __name__)

from .services.leads_from_gmaps import leads_from_gmaps_service
from .services.leads_from_mail import leads_from_mail_service
from .services.auto_offer import auto_offer_service


@main_bp.route('/')
@login_required 
def index():
    return render_template('index.html')

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