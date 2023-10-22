
from functools import wraps
import os
import traceback
from urllib.parse import urlencode
from app_base import bp

from auth0.authentication import Users, GetToken
from flask import session, url_for, flash, g
from flask_oauthlib.client import OAuth
from flask import Blueprint, render_template, redirect, request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired
from auth0.management.auth0 import Auth0

auth0_bp = Blueprint('auth0', __name__)

# AUTH0_CALLBACK_URL = os.getenv('AUTH0_CALLBACK_URL')
AUTH0_CLIENT_ID = os.getenv('AUTH0_CLIENT_ID')
AUTH0_CLIENT_SECRET = os.getenv('AUTH0_CLIENT_SECRET')
AUTH0_DOMAIN = os.getenv('AUTH0_DOMAIN')

oauth = OAuth(bp)
auth0 = oauth.remote_app(
    'auth0',
    consumer_key=AUTH0_CLIENT_ID,
    consumer_secret=AUTH0_CLIENT_SECRET,
    request_token_params={
        'scope': 'openid profile',
        'audience': f'https://{AUTH0_DOMAIN}/userinfo'
    },
    base_url=f'https://{AUTH0_DOMAIN}/',
    access_token_method='POST',
    access_token_url=f'/oauth/token',
    authorize_url=f'/authorize',
)

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'profile' not in session:
            return redirect('/auth0/login')
        return f(*args, **kwargs)
    return decorated

# set global current_user variable
@bp.before_request
def before_request():
    g.current_user = session.get('profile', None)

@auth0_bp.route('/login')
def login():
    callback_url = url_for('chatlang.auth0.callback_handling', _external=True)
    callback_url = callback_url.replace('127.0.0.1', 'localhost') # hack for auth0
    print(f"URL: ", url_for('chatlang.auth0.callback_handling', _external=True), flush=True)
    return auth0.authorize(callback=callback_url)

@auth0_bp.route('/callback')
def callback_handling():
    resp = auth0.authorized_response()
    if resp is None or resp.get('access_token') is None:
        return 'Access denied: reason={} error={}'.format(
            request.args['error_reason'],
            request.args['error_description']
        )
    
    # Store user info and tokens
    session['access_token'] = resp['access_token']
    user_info = Users(AUTH0_DOMAIN).userinfo(session['access_token'])
    session['profile'] = user_info
    return redirect(url_for('chatlang.index'))

@auth0_bp.route('/logout')
def logout():
    session.clear()
    # logout from auth0.com too
    params = {'returnTo': url_for('chatlang.index', _external=True), 'client_id': AUTH0_CLIENT_ID}
    return redirect(auth0.base_url + 'v2/logout?' + urlencode(params))

class UserProfileForm(FlaskForm):
    default_tutor_language = StringField('Default Tutor Language', validators=[DataRequired()], default='English')
    api_key = StringField('API Key', validators=[DataRequired()])

@bp.route('/user', methods=['GET', 'POST'])
@requires_auth
def user():
    error_message, success_message = None, None
    form = UserProfileForm()
    if request.method == 'GET':
        app_metadata = get_app_metadata()
        form.default_tutor_language.data = app_metadata.get('default_tutor_language', 'English')
        form.api_key.data = app_metadata.get('api_key', '')
    try:
        if form.validate_on_submit():
            update_app_metadata(
                default_tutor_language=form.default_tutor_language.data,
                api_key=form.api_key.data
            )
            success_message = 'Profile updated successfully!'

        return render_template(
            'user.html', form=form, user=session['profile'], 
            error_message=error_message, success_message=success_message
        )
    except Exception as e:
        error_message = str(e)
        traceback.print_exc()
        return render_template(
            'user.html', form=form, user=session['profile'], 
            error_message=error_message, success_message=success_message
        )
    
def get_management_api_token():
    get_token = GetToken(AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET)
    token = get_token.client_credentials(audience=f'https://{AUTH0_DOMAIN}/api/v2/')
    return token['access_token']

def update_app_metadata(default_tutor_language, api_key):
    auth0_mgmt_api = Auth0(AUTH0_DOMAIN, get_management_api_token())
    metadata = {
        'default_tutor_language': default_tutor_language,
        'api_key': api_key
    }
    sub = session['profile']['sub']
    auth0_mgmt_api.users.update(session['profile']['sub'], {'app_metadata': metadata})
    session['profile']['app_metadata'] = metadata

def get_app_metadata():
    # if user is not logged in, return empty dict
    if 'profile' not in session:
        return {}
    if 'app_metadata' in session['profile']:
        return session['profile']['app_metadata']
    auth0_mgmt_api = Auth0(AUTH0_DOMAIN, get_management_api_token())
    app_metadata = auth0_mgmt_api.users.get(session['profile']['sub']).get('app_metadata', {})
    session['profile']['app_metadata'] = app_metadata
    return app_metadata

@auth0_bp.route('/delete_account', methods=['POST'])
def delete_account():
    auth0_mgmt_api = Auth0(AUTH0_DOMAIN, get_management_api_token())
    auth0_mgmt_api.users.delete(session['profile']['sub'])
    session.clear()
    flash('Account deleted successfully!', 'success')
    return redirect('/')


bp.register_blueprint(auth0_bp, url_prefix='/auth0')
