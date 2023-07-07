// Record the last assistant message from the two chat windows:
let prevLeftReply = "";
let prevRightReply = "";
let systemConfig = "";

// Add user input message to chatbox:
function addUserMessage(message, chatBoxNumber) {
   const chatBoxId = '#chatBox' + chatBoxNumber;
   message = "User: " + message;
   $(chatBoxId).append(`<div class="message">${message}</div>`);
}

// Add chatGPT's response to chatbox:
function addAssistantMessage(message, chatBoxNumber) {
   if (chatBoxNumber == 1) {
      prevLeftReply = message;
   } else {
      prevRightReply = message;
   }
   const chatBoxId = '#chatBox' + chatBoxNumber;
   message = "Assistant: " + message;
   $(chatBoxId).append(`<div class="message">${message}</div>`);
}

// If chatBoxNumber == 1, it's the right main chat; otherwise it's the left meta chat.
// chatBoxNumber in here must be 1 or 2.
function sendMessage(chatBoxNumber) {
   // Get the user input:
   const inputBoxId = "#inputBox" + chatBoxNumber;
   let userInput = $(inputBoxId).val();

   // Clear input field:
   $(inputBoxId).val('');

   // If input only includes space or empty strings, do nothing:
   if (userInput.replace(/\s/g, "") == "") {
      return;
   }

   // Add user message to chatbox:
   addUserMessage(userInput, chatBoxNumber);

   // Depending on which chatbox current is on, modify the sent message:
   let payload = {};
   if (chatBoxNumber == 2) {
      if (prevRightReply == "") {
         // initialize the chat bot in such context.
         // it is guaranteed to enter here since we start from right window.
         systemConfig = userInput;
         payload = {
            'messages': [
               {'role': 'system', 'content': systemConfig}
            ]
         }; 
      } else {
         // for random response in the meta-conversation window, it doesn't need a specific context:
         payload = {
            'messages': [
               // {'role': 'assistant', 'content': prevLeftReply},   // this might cause confusion
               {'role': 'user', 'content': userInput}
            ]
         };
      }
   } else if (chatBoxNumber == 1) {
      // for the left main window, we always want chat to be in the context defined:
      payload = {
         'messages': [
            {'role': 'system', 'content': systemConfig},
            {'role': 'assistant', 'content': prevLeftReply},   // it's ok if prevLeftReply is empty
            {'role': 'user', 'content': userInput}
         ]
      };
   } else {
      return;
   }

   console.log(JSON.stringify(payload));

   // Execute ajax call:
   $.ajax({
      type: 'POST',
      // url: '/chatlanguagelearning/chat',  // change to this one when deploy on server
      url: 'http://localhost:5000/chatlanguagelearning/chat',  // for testing only
      contentType: 'application/json',
      data: JSON.stringify(payload),
      success: function (response) {
         var assistantReply = response.message;
         addAssistantMessage(assistantReply, chatBoxNumber);
      },
      error: function (error) {
         console.error('Error:', error);
      }
   });
}

// Enables the click/enter button function to input a message:
function checkSubmit(event, chatBoxNumber) {
   if (event.keyCode === 13) {
      event.preventDefault();
      sendMessage(chatBoxNumber);
   }
}