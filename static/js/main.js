// Record the last user and assistant message from left main window: (for context connection in the right chat window)
let prevLeftAssistantMessage = "";

// Keep a log history:
let leftLogSize = 6; // can change the size for cost consideration   (3 rounds of talk)
let rightLogSize = 2; // can change the size for cost consideration  (1 round of talk)
var leftChatLog = new Array();
var rightChatLog = new Array();

// System role content:
let leftSystemConfig = "";
let rightSystemConfig = "You are an assistant that acts like a language learning teacher.";

// Record user role, environment, and assistant role:
let userRole = "";
let aiRole = "";
let chatContext = "";
let chatLanguage = "";
var configClicked = false; // we only want take the first user click to the Let's Go button effective

// When user click the "Let's Go!" button:
function setupConfig() {
   // Get role information
   userRole = normalizeString($("#user-role").val());
   aiRole = normalizeString($("#ai-role").val());
   chatContext = $("#chat-context").val();
   chatLanguage = normalizeString($("#chat-language").val());

   // Set up environment and user prefix for chat:
   leftSystemConfig = "You are an assistant that acts like a/an " + aiRole + " in a/an " + chatLanguage + " " + chatContext + ".";

   // Send message to API and store the first two messages in left chat log:
   if (!configClicked && userRole.replace(/\s/g, "") != "" && aiRole.replace(/\s/g, "") != "" && chatContext.replace(/\s/g, "") != "" && chatLanguage.replace(/\s/g, "")) {
      configClicked = true;
      configChatLog();
   }
}

// Send first message to API to take the AI into context, user won't see this message.
function configChatLog() {
   var messages = new Array();
   messages.push({'role': 'system', 'content': leftSystemConfig});

   // I am your {user role} at this {context}. Hello!
   // After testing, this "Hello!" starter is the most stable input
   let psedoInput = 'I am the ' + userRole + ' in this ' + chatLanguage + " " + chatContext + '. Hello!';
   messages.push({'role': 'user', 'content': psedoInput});
   let payload = {'messages': messages};

   // Append this psedo input in the left chat log:
   updateLeftLog(psedoInput);

   // Send message to API, get response:
   $.ajax({
      beforeSend: function() {
         // Show loading:
         $(".config-loading").removeClass("hidden");
      },
      type: 'POST',
      // url: '/chatlanguagelearning/chat',  // change to this one when deploy on server
      url: 'http://localhost:5000/chatlanguagelearning/chat',  // for testing only
      contentType: 'application/json',
      data: JSON.stringify(payload),
      success: function (response) {
         var assistantReply = response.message;
         // Add this new assistant message in the log history:
         updateLeftLog(assistantReply);
         
         // Hide loading:
         $(".config-loading").addClass("hidden");
         
         // Show the two chat windows:
         $(".chat-box-container").css("visibility", "visible");
      },
      error: function (error) {
         console.error('Error:', error);
      }
   });
}

// Normalize user input to have first letter capitalized, and the rest all lower case:
function normalizeString(input) {
   input = input.toLowerCase();
   return input.charAt(0).toUpperCase() + input.slice(1);
}

// When user click the "Restart" button:
function resetConfig() {
   // Hide the two chat windows:
   $(".chat-box-container").css("visibility", "hidden");

   // Refresh page:
   window.location.reload();
}

// Update the left main conversation log history.
// Always in the order: "user", "assistant", "user", "assistant"...
function updateLeftLog(message) {
   // If the array is already full, we are sure there will be at least two messages:
   if (leftChatLog.length === leftLogSize) {
      leftChatLog.splice(2, 2);  // always keep the first user & assistant message on record to have the chat take into context
   }
   leftChatLog.push(message);
}

// Update the right meta conversation log history.
// Always in the order: "user", "assistant", "user", "assistant"...
function updateRightLog(message) {
   if (rightChatLog.length === rightLogSize) {
      rightChatLog.splice(0, 2);
   }
   rightChatLog.push(message);
}

// Add user input message to chatbox:
function addUserMessage(message, chatBoxNumber) {
   const chatBoxId = '#chatBox' + chatBoxNumber;
   if (chatBoxNumber == 1) {
      message = userRole + ": " + message;
   } else {
      message = "Student: " + message;
   }
   $(chatBoxId).append(`<div class="message">${message}</div>`);
}

// Add chatGPT's response to chatbox:
function addAssistantMessage(message, chatBoxNumber) {
   const chatBoxId = '#chatBox' + chatBoxNumber;
   if (chatBoxNumber == 1) {
      message = aiRole + ": " + message;
   } else {
      message = "Teacher: " + message;
   }
   $(chatBoxId).append(`<div class="message">${message}</div>`);
}

// Enables the click/enter button function to input a message:
function enterMessage(event, chatBoxNumber) {
   if (event.keyCode === 13) {
      event.preventDefault();
      sendMessage(chatBoxNumber);
   }
}

// If chatBoxNumber == 1, it's the left main chat; otherwise it's the right meta chat.
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

   // Build the message from history log:
   var messages = buildMessage(chatBoxNumber);   // get it from history log
   if (chatBoxNumber == 1) {
      messages.push({'role': 'user', 'content': userInput}); // add user input message
   } else {
      if (prevLeftAssistantMessage === "") {
         messages.push({'role': 'user', 'content': userInput}); // add user input message
      } else {
         messages.push({'role': 'user', 'content': 'Take this as a reference: "' + prevLeftAssistantMessage + '", ' + userInput}); // take last assistant reply from left window as reference
      }
   }
   let payload = {'messages': messages};

   // console.log(JSON.stringify(payload));

   // Add this new user input in the log history:
   if (chatBoxNumber == 1) {
      updateLeftLog(userInput);
   } else {
      updateRightLog(userInput);
   }

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
         // Add this new assistant message in the log history:
         if (chatBoxNumber == 1) {
            updateLeftLog(assistantReply);
            prevLeftAssistantMessage = assistantReply;   // update this value
         } else {
            updateRightLog(assistantReply);
         }
      },
      error: function (error) {
         console.error('Error:', error);
      }
   });
}

// Build the payload messages from log history:
function buildMessage(chatBoxNumber) {
   var messages = new Array();
   if (chatBoxNumber === 1) {
      messages.push({'role': 'system', 'content': leftSystemConfig});
      for (var i = 0; i < leftChatLog.length; i++) {
         if (i % 2 === 0) {
            // this is a user message:
            messages.push({'role': 'user', 'content': leftChatLog[i]});
         } else {
            // this is a assistant reply:
            messages.push({'role': 'assistant', 'content': leftChatLog[i]});
         }
      }
   } else {
      messages.push({'role': 'system', 'content': rightSystemConfig});
      for (var i = 0; i < rightChatLog.length; i++) {
         if (i % 2 === 0) {
            // this is a user message:
            messages.push({'role': 'user', 'content': rightChatLog[i]});
         } else {
            // this is a assistant reply:
            messages.push({'role': 'assistant', 'content': rightChatLog[i]});
         }
      }
   }
   return messages;
}