# Chatlang: Role-Play Chat for Language Learning

Use Chatlang at [chatlang.net](https://chatlang.net)

## Web App Usage

Chatlang is a language learning tool that allows you to role-play different characters in a target language of your choosing.
Unlike a traditional chatbot which offers a single window for conversation, this tool offers two side-by-side windows with different purposes.
The window on the left is for role-playing: talking with the AI Chatbot in the target language only and without breaking character.
The window on the right is for study: ask questions in your native language about vocabulary, grammar, etc.
This allows you to study, ask questions, and get help without interrupting the flow of the roleplay dialog.
Below is a detailed description on how to use this tool.  Let's get started!

To begin with, you will need to provide inputs in the configuration section at the top of the webpage:

![info_form_empty](static/images/readme/info_form_empty.png)

The **Notes for AI** field is optional.
You can fill the **Notes for AI** with information like "Today is your birthday", to provide the AI chatbot with extra context it can use to make the conversation more realistic.
Once you've filled out the form, click the **New Conversation** button to start the chat.

![chat_start](static/images/readme/chat_start.png)

The window on the left is for you to have the conversation in your target language, the one you are learning (e.g., Chinese).
The window on the right is for you to ask questions about the conversation, clarify vocabulary/grammar, or change some context about the conversation as needed.
The **Reset Chat** button clears the current chat history and starts a new chat under the same settings.
The **Export Chat Log** button exports the current chat history to a zip file.

Recall that you can ask questions in your native language on the right side of the chat window.
See the example below:
![chat_1](static/images/readme/chat_1.png)

## Running Locally

Set up your local API keys by copying ```.env.example``` to ```.env``` and filling in the values.

```sh
cp .env.example .env
```

Install the requirements:

```sh
pip install -r requirements.txt
```

Or, with docker-compose:

```bash
docker compose up
```
