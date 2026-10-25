from flask import Blueprint, render_template

social_bp = Blueprint('social', __name__, url_prefix='/social')

@social_bp.route('/linkedin')
def linkedin():
    return render_template('social/linkedin.html')

@social_bp.route('/facebook')
def facebook():
    return render_template('social/facebook.html')

@social_bp.route('/instagram')
def instagram():
    return render_template('social/instagram.html')

@social_bp.route('/youtube')
def youtube():
    return render_template('social/youtube.html')

@social_bp.route('/github')
def github():
    return render_template('social/github.html')
