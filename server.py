import os
from flask import Flask, Blueprint, request, jsonify
import flask
from flask_cors import CORS, cross_origin
import openai
import requests
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.environ["OPENAI_ORG_ID"]
PREFIX = os.getenv("PREFIX")

app = Flask(__name__, static_folder='static')
CORS(app, support_credentials=True)

print('prefix: ', PREFIX)
bp = Blueprint('chatlang', __name__, url_prefix=PREFIX, static_folder='static', static_url_path='/static')

# This is the main page:
@bp.route('/')
def main_page():
   return flask.render_template('index.html')

# This is the read me page:
@bp.route('/readme')
def read_me_page():
    return flask.render_template('readme.html')

# Get response for user's prompt:
@bp.route('/chatlanguagelearning/chat', methods=['GET', 'POST'])
def get_meta_response():
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
