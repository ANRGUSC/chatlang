import json
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
OUR_KEY_ALLOWED_MODELS = os.getenv("OUR_KEY_ALLOWED_MODELS", "gpt-3.5-turbo").split(",")

SECRET_KEY = secrets.token_urlsafe(16)

logging.basicConfig(level=logging.INFO)

app = Flask(__name__, static_folder='static')
CORS(app, support_credentials=True)
app.secret_key = SECRET_KEY
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

bp = Blueprint('chatlang', __name__, url_prefix=PREFIX, static_folder='static', static_url_path='/static')

class APIException(Exception):
    """Raised when the API returns an error.
    """
    pass

# error handler for APIException
@bp.errorhandler(APIException)
def handle_api_exception(error):
    response = jsonify({'message': error.message})
    response.status_code = error.status_code
    return response

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


class NoAPIKeyException(APIException):
    """Raised when no API key is provided in the frontend, and no local file is found.
    """
    pass

def get_api_key() -> str:
    """Get the API key from the frontend, or from the local file if no API key is provided in the frontend.
    
    Args:
        api_key (str): The API key provided in the frontend.
        
    Returns:
        str: The API key.
        
    Raises:
        NoAPIKeyException: If no API key is provided in the frontend, and no local file is found.
    """
    user_api_key = request.get_json()['api']
    api_key = ""
    if (user_api_key == ""):
        try:
            api_key = OPENAI_API_KEY
        except FileNotFoundError:
            raise NoAPIKeyException("Uh-oh! No local API key detected. Please check your local API key is correctly configured or insert your API key above.")
    else:
        api_key = user_api_key.strip()
    return api_key

class InvalidModelException(APIException):
    """Raised when the model provided by the user is invalid.
    """
    pass

def get_model() -> str:
    """Get the model from the frontend, or from the local file if no model is provided in the frontend.

    Returns:
        str: The model.

    Raises:
        InvalidModelException: If the model provided by the user is invalid.
    """
    user_input_model = request.get_json()['model']
    if user_input_model not in OUR_KEY_ALLOWED_MODELS:
        return jsonify({'message': f'If you want to use {user_input_model}, you must provide your own key. We allow the following models without a key: {", ".join(OUR_KEY_ALLOWED_MODELS)}.'})
    return user_input_model

@bp.route('/api/tutor', methods=['POST'])
def get_tutor_response():
    """Get the tutor's advice for the user's last message in a conversation.
    
    Returns:
        str: The tutor's advice for the user's last message in a conversation.
    """
    if ENABLE_GITHUB_LOGIN == "true":
        if not github.authorized:
            return jsonify({'message': 'Uh-oh! You are not logged in. Please log in to continue.'})
    data = request.get_json()
    rp_messages = data['rp_messages']
    tutor_messages = data['tutor_messages']
    api_key = get_api_key()
    model = get_model()

    rp_message_string = "\n".join(
        f"{rp_message['role']}: {rp_message['content']}" 
        for rp_message in rp_messages
        if rp_message['role'] in ['user', 'assistant']
    )
    tutor_message_string = "\n".join(
        f"{tutor_message['role']}: {tutor_message['content']}" 
        for tutor_message in tutor_messages
        if tutor_message['role'] in ['user', 'assistant']
    )

    functions = [
        {
            "name": "get_tutor_response",
            "description": " ".join([
                "Get the tutor's advice for the user's last message in a conversation",
                "The tutor corrects spelling and grammar mistakes, and provides advice on how to improve.",
                "If the sentence is correct, the tutor will say so."
            ]),
            "parameters": {
                "type": "object",
                "properties": {
                    "correction": {
                        "type": "string",
                        "description": "The corrected version of the user's last message. If the user's message is correct, this is the same as the user's message."
                    },
                    "advice": {
                        "type": "string",
                        "description": "The tutor's advice for the user's last message. If the user's message is correct, this is an empty string."
                    }
                },
                "required": ["correction", "advice"],
            }
        }
    ]

    messages = [
        {
            "role": "system",
            "content": "You are a tutor monitoring a language learner's conversation with an AI assistant. Correct the learner's mistakes and provide advice (in English) on how to improve."
        },
        {
            "role": "user",
            "content": (
                "Tutor/User conversation history:\n"
                f"{tutor_message_string}\n\n"
                "User conversation with AI assistant:\n"
                f"{rp_message_string}\n\n"
            )
        }
    ]

    print(messages)

    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        functions=functions,
        function_call={"name": "get_tutor_response"}
    )
    response_message = response["choices"][0]["message"]
    function_args = json.loads(response_message["function_call"]["arguments"])
    print(function_args)
    return jsonify({'correction': function_args["correction"], 'advice': function_args["advice"]})


# Get response for user's prompt:
@bp.route('/api/chat', methods=['GET', 'POST'])
def get_meta_response():
    if ENABLE_GITHUB_LOGIN == "true":
        if not github.authorized:
            return jsonify({'message': 'Uh-oh! You are not logged in. Please log in to continue.'})
    # get the user message (a dict of messages):
    user_message = request.get_json()['messages']
    user_input_model = get_model()
    api_key = get_api_key()

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
