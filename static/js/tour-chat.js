
// Tour function.
function startTour() {
    introJs().setOptions({
        keyboardNavigation: false,
        steps: [
            {
                element: document.querySelector('#tab-content'),
                intro: "This is chat area with two chat windows."
            },
            {
                element: document.querySelector('#rp-card'),
                intro: "This is the role-playing scenario you've just configured. In this chat, stay in character and only use the target language."
            },
            {
                element: document.querySelector('#tutor-card'),
                intro: "This is the tutor chat. The can help you with understand the chatbot's replies, correct your mistakes, and answer your questions. Feel free to talk to the tutor in your native language."
            },
            {
                element: document.querySelector('#button-addon-export'),
                intro: "Click here to export the chat history."
            },
            {
                element: document.querySelector('#button-addon-reset'),
                intro: "Click here to reset the chat history."
            }
       ]
    }).start();
}