import logging
import os
from flask import Flask, Blueprint, request, jsonify
import flask
from flask_cors import CORS, cross_origin
import openai
import requests
from dotenv import load_dotenv
from flask_dance.contrib.github import make_github_blueprint, github
import secrets
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.environ["OPENAI_ORG_ID"]
PREFIX = os.getenv("PREFIX")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
ENABLE_GITHUB_LOGIN = os.getenv("ENABLE_GITHUB_LOGIN")

SECRET_KEY = secrets.token_urlsafe(16)

logging.basicConfig(level=logging.INFO)

app = Flask(__name__, static_folder='static')
CORS(app, support_credentials=True)
app.secret_key = SECRET_KEY
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

bp = Blueprint('chatlang', __name__, url_prefix=PREFIX, static_folder='static', static_url_path='/static')

if ENABLE_GITHUB_LOGIN == "true":
    bp_github = make_github_blueprint(
        client_id=GITHUB_CLIENT_ID, 
        client_secret=GITHUB_CLIENT_SECRET,
        redirect_to='chatlang.main_page',
        scope="read:org"
    )
    bp.register_blueprint(bp_github, url_prefix='/login')

# This is the main page:
@bp.route('/', methods=['GET', 'POST'])
def main_page():
    if ENABLE_GITHUB_LOGIN == "true":
        if not github.authorized:
            if request.method == 'POST':
                logging.info("Logging in with Github.")
                return flask.redirect(flask.url_for("github.login"))
            else:
                logging.info("Not logged in - showing login page.")
                return flask.render_template('login.html')
        else:
            resp = github.get("/user/orgs")
            if resp.ok:
                orgs = resp.json()
                if not any(org['login'] == 'ANRGUSC' for org in orgs):
                    logging.error("User is not a member of the ANRGUSC Github organization.")
                    return flask.render_template('login.html', error="Access Denied. You are not a member of the ANRGUSC Github organization.")
                else:
                    logging.info("Github login successful.")
            else:
                logging.error(f"Github login failed. {resp.status_code} {resp.text}")
                return flask.render_template('login.html', error="Access Denied. Github login failed.")
    return flask.render_template('index.html')

@bp.route('/logout')
def logout():
    flask.session.clear()
    return flask.redirect(flask.url_for("chatlang.main_page"))

# This is the read me page:
@bp.route('/readme')
def read_me_page():
    return flask.render_template('readme.html')

# Get response for user's prompt:
@bp.route('/chatlanguagelearning/chat', methods=['GET', 'POST'])
def get_meta_response():
    if ENABLE_GITHUB_LOGIN == "true":
        if not github.authorized:
            return jsonify({'message': 'Uh-oh! You are not logged in. Please log in to continue.'})
    # get the user message (a dict of messages):
    user_message = request.get_json()['messages']
    user_api_key = request.get_json()['api']
    user_input_model = request.get_json()['model']

    # Set up API key:
    api_key = ""
    if (user_api_key == ""):
        try:
            api_key = OPENAI_API_KEY
        except FileNotFoundError:
            return jsonify({'message': 'Uh-oh! No local API key detected. Please check your local API key is correctly configured or insert your API key above.'}) # did not input API key in frontend, also did not include API key in local file
    else:
        api_key = user_api_key.strip()

    # init requests parameters:
    search_url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization':  'Bearer ' + api_key,
        'Content-Type': 'application/json',
        'OpenAI-Organization': OPENAI_ORG_ID
    }
    data = {
        'model': user_input_model,
        'messages': user_message,
    }
    # call openai api to get response:
    response = requests.post(search_url, json=data, headers=headers)

    # handles error:
    if response.status_code == 200:
        # extract the response and only returns chatGPT's reply:
        assistant_message = response.json()["choices"][0]["message"]["content"]
        return jsonify({'message': assistant_message}) 
    else:
        return jsonify({'message': 'Uh-oh! API call failed. Possible causes: invalid API key; your API key does not support the current model; API server is busy. Please resend message or restart.'}) 
    
app.register_blueprint(bp)

# Run it:
if __name__ == '__main__':
    # host at 0.0.0.0 
    app.run(host='0.0.0.0', port=5000, debug=True)
