import json
import logging
import os
import secrets
import traceback
from typing import Dict, List, Tuple, Optional
from flask import redirect, render_template, request, jsonify, session, url_for
from flask_wtf import FlaskForm
import openai
from wtforms import StringField, SelectField, TextAreaField
from wtforms.validators import Optional as OptionalValidator
import markdown
import pathlib
from redis import Redis
import sys

from flask_limiter import Limiter, RateLimitExceeded

from app_base import app, bp
from app_oauth import get_app_metadata

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.environ["OPENAI_ORG_ID"]
PREFIX = os.getenv("PREFIX")
OUR_KEY_ALLOWED_MODELS = os.getenv("OUR_KEY_ALLOWED_MODELS", "gpt-3.5-turbo").split(",")
SECRET_KEY = os.getenv("SECRET_KEY")
FLASK_ENV = os.getenv("FLASK_ENV")

if not SECRET_KEY and FLASK_ENV != "production":
    SECRET_KEY = secrets.token_urlsafe(16)

app.config['SECRET_KEY'] = SECRET_KEY

thisdir = pathlib.Path(__file__).parent.absolute()

REDIS_URL = os.getenv("REDIS_URL")
if REDIS_URL is None:
    print("REDIS_URL is required for rate limiting.", file=sys.stderr)
    sys.exit(1)

redis_conn = Redis.from_url(REDIS_URL)

global_api_key_limiter = Limiter(app=app, key_func=lambda: 'global', storage_uri=REDIS_URL)
api_key_limiter = Limiter(app=app, key_func=lambda: session.get('profile', {}).get('sub', '__anonymous__'), storage_uri=REDIS_URL)

# exempt users where get_api_key() != OPENAI_API_KEY
@api_key_limiter.request_filter
def api_key_limiter_filter():
    api_key, _ = get_api_key()
    return api_key != OPENAI_API_KEY

@global_api_key_limiter.request_filter
def global_api_key_limiter_filter():
    api_key, _ = get_api_key()
    return api_key != OPENAI_API_KEY

@app.errorhandler(RateLimitExceeded)
def ratelimit_error(e: RateLimitExceeded):
    response = jsonify(
        error="ratelimit exceeded", 
        message=(
            f"When using the default API key, your messages are limited to: {e.description}. "
            "Add your own OpenAI API key in your Account Settings to remove these limits."
        )
    )
    response.status_code = 429
    return response

class APIException(Exception):
    """Raised when the API returns an error.
    """
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code

# error handler for APIException
@bp.errorhandler(APIException)
def handle_api_exception(error):
    response = jsonify({'message': error.message})
    response.status_code = error.status_code
    return response

class ChatSettingsForm(FlaskForm):
    scenario = StringField('Scenario', validators=[OptionalValidator()])
    ai_role = StringField('AI Role', validators=[OptionalValidator()])
    your_role = StringField('Your Role', validators=[OptionalValidator()])
    language = StringField('Language', validators=[OptionalValidator()])
    difficulty = SelectField('Difficulty', choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')])
    api_model = SelectField('API Model', choices=[('gpt-3.5-turbo', 'gpt-3.5-turbo'), ('gpt-4', 'gpt-4')])
    notes_for_ai = TextAreaField('Notes for AI', validators=[OptionalValidator()])
    api_key = StringField('API Key', validators=[OptionalValidator()])
    tutor_language = StringField('Tutor Language', validators=[OptionalValidator()])

def get_model() -> str:
    model = (request.json or {}).get('api_model')
    if model not in OUR_KEY_ALLOWED_MODELS:
        raise APIException(f"Model {model} is not allowed unless you use your own API key. Check your Account Settings.", status_code=403)
    return model

def get_api_key() -> Tuple[str, Optional[str]]:
    api_key = get_app_metadata().get('api_key') or OPENAI_API_KEY
    if not api_key:
        raise APIException("OPENAI API key is required.", status_code=403)
    org_id = None
    if api_key == OPENAI_API_KEY:
        org_id = OPENAI_ORG_ID
    else:
        logging.info("Using custom API key")
    return api_key, org_id

def get_tutor_language() -> str:
    return get_app_metadata().get('tutor_language') or 'English'

messages_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "role": {"type": "string", "enum": ["system", "user", "assistant"]},
            "content": {"type": "string"}
        },
        "required": ["role", "content"]
    }
}

@bp.route('/', methods=['GET', 'POST'])
def index():
    form = ChatSettingsForm()
    if form.validate_on_submit():
        query = {
            'api_model': form.api_model.data,
            'scenario': form.scenario.data,
            'ai_role': form.ai_role.data,
            'your_role': form.your_role.data,
            'language': form.language.data,
            'difficulty': form.difficulty.data,
            'notes_for_ai': form.notes_for_ai.data,
        }
        return redirect(url_for('chatlang.chat_page', **query))
    return render_template('index.html', form=form)

# use default limiter for this route
@bp.route('/api/chat', methods=['POST'])
@global_api_key_limiter.limit("500 per day")
@api_key_limiter.limit("20 per day")
def chat():
    bot_type = request.args.get('bot')

    if request.json is None:
        raise APIException("Request must be JSON.", status_code=400)
    request_json: Dict = request.json

    model = get_model()
    api_key, org_id = get_api_key()
    tutor_language: str = get_tutor_language()
    openai.api_key = api_key
    if org_id:
        openai.organization = OPENAI_ORG_ID
    try:
        rp_history: List[Dict[str, str]] = request_json['rp_history']
        tutor_history: List[Dict[str, str]] = request_json['tutor_history']
        scenario: str = request_json['scenario']
        ai_role: str = request_json['ai_role']
        your_role: str = request_json['your_role']
        language: str = request_json['language']
        difficulty: str = request_json['difficulty']
        notes_for_ai: str = request_json['notes_for_ai']
    except KeyError as e:
        raise APIException(f"Missing required key: {e.args[0]}", status_code=400)
    
    try:
        if bot_type == 'rp':
            # Proactive error correction
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
                    # "content": "You are a tutor monitoring a language learner's conversation with an AI assistant. Correct the learner's mistakes and provide advice (in English) on how to improve."
                    "content": (
                        f"The user is role-playing with an AI chatbot to practice their {language} language skills. "
                        f"The user is playing the role of {your_role} and the AI chatbot is playing the role of {ai_role}."
                        f"The scenario is {scenario}. "
                        f"You are a tutor that is monitoring the AI chatbot and the user. "
                        f"Correct the learner's mistakes and provide advice (in {tutor_language}) on how to improve."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        "Tutor/User conversation history:\n"
                        f"{tutor_history}\n\n"
                        "User conversation with AI assistant:\n"
                        f"{rp_history}"
                    )
                }
            ]

            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                functions=functions,
                function_call={"name": "get_tutor_response"}
            )
            response_message = response["choices"][0]["message"]
            function_args = json.loads(response_message["function_call"]["arguments"])
            tutor_response = ''
            if function_args['advice'].strip():
                tutor_response = f"[{function_args['correction']}] {function_args['advice']}"

            # Role-play response
            messages = [
                {
                    'role': 'system', 
                    'content': (
                        "You are an AI chatbot that will role-play with the user for them to practice their language skills. "
                        f"Your role is {ai_role} and the user's role is {your_role}. "
                        f"The scenario is {scenario}. "
                        f"The target language is {language}. Do not use any other languages and do not break character. "
                        f"Use {difficulty} level language. "
                        "" if not notes_for_ai else f"Notes: {notes_for_ai}"
                    )
                },
                *[{'role': m['role'], 'content': m['content']} for m in rp_history],
            ]

            response = openai.ChatCompletion.create(model=model, messages=messages)
            response_message = response.choices[0]['message']['content']
            return jsonify({'rp_response': response_message, 'tutor_response': tutor_response})
        else:
            # rp_convo = "\n".join([f"{ai_role if m['role'] == 'assistant' else your_role}: {m['content']}" for m in rp_history])
            # tutor_convo = "\n".join([f"{ai_role if m['role'] == 'assistant' else your_role}: {m['content']}" for m in tutor_history])
            
            # for each user message in tutor_history, get all rp_history messages that came before it

            messages = [
                {
                    'role': 'system',
                    'content': (
                        f"The user is role-playing with an AI chatbot to practice their {language} language skills. "
                        f"The user is playing the role of {your_role} and the AI chatbot is playing the role of {ai_role}."
                        f"The scenario is {scenario}. "
                        f"You are a tutor that is monitoring the AI chatbot and the user. "
                        f"When the user asks you a question, you should answer it in their native language {tutor_language}. "
                        f"The user may ask you questions about the conversation (i.e. what words/settings mean), how to say something in the target language, etc. "
                    )
                }
            ]
            tutor_user_messages = [m for m in tutor_history if m['role'] == 'user']
            tutor_assistant_messages = [m for m in tutor_history if m['role'] == 'assistant']
            for tutor_user_message in tutor_user_messages:
                rp_convo = "\n".join([f"{ai_role if m['role'] == 'assistant' else your_role}: {m['content']}" for m in rp_history if m['timestamp'] <= tutor_user_message['timestamp']])
                
                messages.append({
                    'role': 'user',
                    'content': (
                        f"User conversation with AI assistant:\n"
                        f"{rp_convo}\n\n"
                        f"{tutor_user_message['content']}"
                    )
                })
                
                tutor_response = None
                for tutor_assistant_message in tutor_assistant_messages:
                    if tutor_assistant_message['timestamp'] > tutor_user_message['timestamp']:
                        tutor_response = tutor_assistant_message['content']
                        break
                if tutor_response is not None:
                    messages.append({
                        'role': 'assistant',
                        'content': tutor_response
                    })
                
            openai.api_key = api_key
            response = openai.ChatCompletion.create(model=model, messages=messages)
            response_message = response.choices[0]['message']['content']
            return jsonify({'tutor_response': response_message})
    except openai.error.AuthenticationError as e:
        raise APIException("Invalid API key. Check your account settings.", status_code=401)
    except Exception as e:
        traceback.print_exc()
        raise APIException("Unknown error. Please submit feedback.", status_code=400)

@bp.route('/chat', methods=['GET'])
def chat_page():
    return render_template('chat.html')

@bp.route('/about', methods=['GET'])
def about_page():
    markdown_path = thisdir.joinpath('README.md')
    with open(markdown_path, 'r') as f:
        content = f.read()
    html_content = markdown.markdown(content)
    return render_template('about.html', html_content=html_content)

app.register_blueprint(bp)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
