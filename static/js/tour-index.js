
// Tour function.
function startTour() {
    introJs().setOptions({
       keyboardNavigation: false,
       steps: [
          {
             intro: "Welcome!<br><br>This is a language learning tool that allows you to role-play different characters in a target language of your choosing.<br><br>Let's get started!"
          },
          {
             element: document.querySelector('#settings-form'),
             intro: "This is the configuration section. Here, you can set information about the role-playing scenario."
          },
          {
             element: document.querySelector('#scenario'),
             intro: "Pick the role-play scenario, e.g., Restaurant."
          },
          {
             element: document.querySelector('#ai_role'),
             intro: "Pick chatbot's role, e.g., Waiter."
          },
          {
             element: document.querySelector('#your_role'),
             intro: "Pick your role, e.g., Customer."
          }, {
             element: document.querySelector('#language'),
             intro: "Pick the language you want to learn. <br><br>Please refer to: <a class='custom-link' href='https://acutrans.com/languages-supported-by-chatgpt/' target='_blank'>supported languages</a>."
          },
          {
             element: document.querySelector('#difficulty'),
             intro: "Easy level: replies from the chatbot are usually short and simple.<br><br>Moderate level: replies are short but with intermediate level grammars and vocabularies." +
                "<br><br>Expert level: replies are more lengthy and creative.",
          },
          {
             element: document.querySelector('#api_model'),
             intro: "Choose the chat model.<br><br>Note: some API keys do not support GPT-4."
          },
          {
             element: document.querySelector('#notes_for_ai'),
             intro: "You can give the chatbot an optional command to behave in a certain way, e.g. Today is a rainy day."
          },
          {
             element: document.querySelector('#btn-new-conversation'),
             intro: "Click here begin! <br><br>You will see two chat windows pop up below."
          },
       ]
    }).start();
 }