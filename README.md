# Role-Play Chat for Language Learning

## Welcome!

Chatlang is a language learning tool that allows you to role-play different characters in a target language of your choosing.
Unlike a traditional chatbot which offers a single window for conversation, this tool offers two side-by-side windows with different purposes.
The window on the left is for role-playing: talking with the AI Chatbot in the target language only and without breaking character.
The window on the right is for study: ask questions in your native language about vocabulary, grammar, etc.
This allows you to study, ask questions, and get help without interrupting the flow of the roleplay dialog.
Below is a detailed description on how to use this tool.  Let's get started!

To begin with, you will need to provide inputs in the configuration section at the top of the webpage:

![info_form_empty](static/images/readme/info_form_empty.png)

The **Notes for AI** and **API Key** fields are optional.

You can fill the **Notes for AI** like "Today is your birthday", then when you start the chat, the AI knows that today is its birthday.

**API Key** is required only if you don't have your local API set up. If you just want to test this out, you will need to insert your API key in here every time you restart the chat. To set-up your local API key, please refer to **Running Locally** at the bottom of the page for more instructions.

Let's continue! This is just a sample.

- Please use proper and rational scenario settings e.g. customer & waiter in a restaurant. Otherwise, the AI may behave strangely.

![info_form_filled](static/images/readme/info_form_filled.png)

Once that's done. You can find these two buttons:

![header_button](static/images/readme/header_button.png)

**Refresh Chat** clears the current chat history and starts a new chat under the same settings. **Start Over** allows you reset everything.

Click the **Let's Go!** button, you will see the two chat windows appear. The headers show your (user) role and the AI's role in each chat window.

![chat_start](static/images/readme/chat_start.png)

The window on the left is for you to have the conversation in your target language, the one you are learning (e.g., Chinese).

The window on the right is for you to ask questions about the conversation, clarify vocabulary/grammar, or change some context about the conversation as needed. This can be in the language you already know (e.g., English).

![chat_1](static/images/readme/chat_1.png)

As you can see above, you can chat with the AI in the setting given on the left chat window. You can stop any time if you have a question and ask it on the right window. Let's continue:

![chat_2](static/images/readme/chat_2.png)

![chat_3](static/images/readme/chat_3.png)

As you can see above, you can change your level anytime if you feel it's too hard or too easy. There are three different levels: **Easy**, **Moderate**, and **Expert**. You can change your level with **/level [desired level]** command.

You can also add notes to the chatbot on the left window as extra information. To do that, use the **/system [notes]** handle. This is an example:

![chat_4](static/images/readme/chat_4.png)

You can use the **/help** handle in case you forget how to use those instructions.

![chat_5](static/images/readme/chat_5.png)

Last but not least, you can export your chat log history any time you want by clicking the Export Chat Log button. Your log history will be converted into a .txt file with an UID prefix:

The left chat log only contains the role play chat. The right chat log will contain all system instructions between the user and the system.

![left_log_sample](static/images/readme/left_log_sample.png)

![right_log_sample](static/images/readme/right_log_sample.png)


## Running Locally
Install the requirements:

```sh
pip install -r requirements.txt
```

Set up your local API keys by copying ```.env.example``` to ```.env``` and filling in the values.

```sh
cp .env.example .env
```

## There you have it! We hope you like it!
