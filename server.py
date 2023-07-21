# ## This is the backend server that connects with ChatGPT API
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import openai
import requests

# Setup openai env:
API_KEY = open("OPENAI_API_KEY", "r").read().strip()
openai.api_key = API_KEY

# ------------------------------------------------------------------------------------------------------------------
app = Flask(__name__)
CORS(app, support_credentials=True)

# Enable CORS for testing:
@app.route("/login")
@cross_origin(supports_credentials=True)
def login():
  return jsonify({'success': 'ok'})

# This is the main page:
@app.route('/')
def main_page():
   return app.send_static_file('index.html')

# Get response for user's prompt:
@app.route('/chatlanguagelearning/chat', methods=['GET', 'POST'])
def get_meta_response():
    # get the user message (a dict of messages):
    user_message = request.get_json()['messages']

    # init requests parameters:
    search_url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization':  'Bearer ' + API_KEY,
        'Content-Type': 'application/json'
    }
    data = {
        'model': 'gpt-3.5-turbo',  # Can change this model later on
        'messages': user_message,
    }

    # call openai api to get response:
    response = requests.post(search_url, json=data, headers=headers).json()

    # extract the response and only returns chatGPT's reply:
    assistant_message = response["choices"][0]["message"]["content"]
    return jsonify({'message': assistant_message})

# Run it:
if __name__ == '__main__':
    app.run(debug=True)