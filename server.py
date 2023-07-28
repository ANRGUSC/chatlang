# ## This is the backend server that connects with ChatGPT API
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import openai
import requests

# ------------------------------------------------------------------------------------------------------------------
# local api key file:
API_KEY_FILE = "OPENAI_API_KEY.txt" # you can name your api key file however you like, but make sure to update it in here

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

# This is the read me page:
@app.route('/readme')
def read_me_page():
    return app.send_static_file('readme.html')

# Get response for user's prompt:
@app.route('/chatlanguagelearning/chat', methods=['GET', 'POST'])
def get_meta_response():
    # get the user message (a dict of messages):
    user_message = request.get_json()['messages']
    user_api_key = request.get_json()['api']
    user_input_model = request.get_json()['model']

    # Set up API key:
    api_key = ""
    if (user_api_key == ""):
        try:
            api_key = open(API_KEY_FILE, "r").read().strip()    
        except FileNotFoundError:
            return jsonify({'message': 'Uh-oh! No local API key detected. Please check your local API key is correctly configured or insert your API key above.'}) # did not input API key in frontend, also did not include API key in local file
    else:
        api_key = user_api_key.strip()

    # init requests parameters:
    search_url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization':  'Bearer ' + api_key,
        'Content-Type': 'application/json'
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

# Run it:
if __name__ == '__main__':
    app.run(debug=True)