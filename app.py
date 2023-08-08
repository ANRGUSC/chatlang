import json
import os
import secrets
from typing import Dict, List
from dotenv import load_dotenv
from flask import Blueprint, Flask, redirect, render_template, request, jsonify, url_for
from flask_wtf import FlaskForm
import openai
from wtforms import StringField, SelectField, TextAreaField
from wtforms.validators import Optional
import jsonschema
import markdown
import pathlib

app = Flask(__name__)
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.environ["OPENAI_ORG_ID"]
PREFIX = os.getenv("PREFIX")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
ENABLE_GITHUB_LOGIN = os.getenv("ENABLE_GITHUB_LOGIN")
OUR_KEY_ALLOWED_MODELS = os.getenv("OUR_KEY_ALLOWED_MODELS", "gpt-3.5-turbo").split(",")
SECRET_KEY = os.getenv("SECRET_KEY")
FLASK_ENV = os.getenv("FLASK_ENV")

if not SECRET_KEY and FLASK_ENV != "production":
    SECRET_KEY = secrets.token_urlsafe(16)

app.config['SECRET_KEY'] = SECRET_KEY

bp = Blueprint('chatlang', __name__, url_prefix=PREFIX, static_folder='static', static_url_path='/static')
thisdir = pathlib.Path(__file__).parent.absolute()

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
    scenario = StringField('Scenario', validators=[Optional()])
    ai_role = StringField('AI Role', validators=[Optional()])
    your_role = StringField('Your Role', validators=[Optional()])
    language = StringField('Language', validators=[Optional()])
    difficulty = SelectField('Difficulty', choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')])
    api_model = SelectField('API Model', choices=[('gpt-3.5-turbo', 'gpt-3.5-turbo'), ('gpt-4', 'gpt-4')])
    notes_for_ai = TextAreaField('Notes for AI', validators=[Optional()])
    api_key = StringField('API Key', validators=[Optional()])
    tutor_language = StringField('Tutor Language', validators=[Optional()])

def get_model() -> str:
    print(request.json)
    model = (request.json or {}).get('api_model')
    if model not in OUR_KEY_ALLOWED_MODELS:
        raise APIException(f"Model {model} is not allowed.", status_code=403)
    return model

def get_api_key() -> str:
    api_key = (request.json or {}).get('api_key') or OPENAI_API_KEY
    if not api_key:
        raise APIException("OPENAI API key is required.", status_code=403)
    return api_key

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
            'tutor_language': form.tutor_language.data,
            'api_key': form.api_key.data
        }
        return redirect(url_for('chatlang.chat_page', **query))
    return render_template('main.html', form=form)

@bp.route('/api/chat', methods=['POST'])
def chat():
    bot_type = request.args.get('bot')

    if request.json is None:
        raise APIException("Request must be JSON.", status_code=400)
    request_json: Dict = request.json

    model = get_model()
    api_key = get_api_key()
    try:
        rp_history: List[Dict[str, str]] = request_json['rp_history']
        tutor_history: List[Dict[str, str]] = request_json['tutor_history']
        scenario: str = request_json['scenario']
        ai_role: str = request_json['ai_role']
        your_role: str = request_json['your_role']
        language: str = request_json['language']
        difficulty: str = request_json['difficulty']
        notes_for_ai: str = request_json['notes_for_ai']
        tutor_language: str = request_json['tutor_language']
        api_key: str = request_json['api_key']
    except KeyError as e:
        raise APIException(f"Missing required key: {e.args[0]}", status_code=400)
    
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

        response = openai.ChatCompletion.create(model=model, messages=messages, api_key=api_key)
        response_message = response.choices[0]['message']['content']
        return jsonify({'rp_response': response_message, 'tutor_response': tutor_response})
    else:
        rp_convo = "\n".join([f"{ai_role if m['role'] == 'assistant' else your_role}: {m['content']}" for m in rp_history])
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
                    f""
                    f"This is the conversation history so far:\n" + rp_convo
                )
            },
            *[{'role': m['role'], 'content': m['content']} for m in tutor_history],
        ]

        response = openai.ChatCompletion.create(model=model, messages=messages, api_key=api_key)
        response_message = response.choices[0]['message']['content']
        return jsonify({'tutor_response': response_message})

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
    app.run(debug=True)
