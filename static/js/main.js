// Record the last user and assistant message from left main window: (for context connection in the right chat window)
let prevLeftAssistantMessage = "";

// Keep a log history, array of JSON objects:
var leftChatLog = new Array();
var rightChatLog = new Array();

// Log for export, add timestamp and some filters, will be array of Strings:
var leftExportLog = new Array();
var rightExportLog = new Array();

// System role content:
let leftSystemConfig = "";
let levelSuffix = "";
let rightSystemConfig = "You're a language teacher. The user is your student and he/she will ask you various language-related questions based on the references possibly given. " +
                        "Please provide concise and informative responses, keeping each reply simple, direct and not lengthy. Always keep your role and that of the user in mind.";
let easySuffix = "Please provide short and simple replies, keeping each reply to only one sentence in entry level vocabulary and grammar."; 
let moderateSuffix = "Please provide short replies, keeping each reply to only one sentence in intermediate level vocabulary and grammar.";   
let expertSuffix = "Please provice concise and creative replies, keeping each reply to no more than three sentences in high-level vocabulary and grammar."; 

// Counter to remind the left assistant to stick with the current difficulty level:
let leftCounter = 3; // remind it per three rounds of conversation

// Record user role, environment, and assistant role:
let userRole = "";
let aiRole = "";
let chatContext = "";
let chatLanguage = "";
let chatLevel = "";  // "Easy", "Moderate", or "Expert"
let userSystemInput = "";
let userAPIKey = ""; // user insert API key
let userModel = "";  // user picked model
var configClicked = false; // we only want take the first user click to the Let's Go button effective
var updatedLeftMessage = false;  // false means: (1) did not get any assistant reply yet from the left window or (2) already updated this last left assistant reply in right window system message

// --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

// When user click the "Let's Go!" button:
function setupConfig() {
   // Get information from the form:
   userRole = normalizeString($("#user-role").val());
   aiRole = normalizeString($("#ai-role").val());
   chatContext = $("#chat-context").val();
   chatLanguage = normalizeString($("#chat-language").val());
   chatLevel = $("#chat-level").val();
   userSystemInput = $("#system-context").val();
   userAPIKey = $("#user-api-key").val();
   userModel = $("#chat-model").val();

   // Show chat windows:
   if (!configClicked && userRole.replace(/\s/g, "") != "" 
      && aiRole.replace(/\s/g, "") != "" && chatContext.replace(/\s/g, "") != "" && chatLanguage.replace(/\s/g, "") 
      && chatLevel.replace(/\s/g, "") != "" && userModel.replace(/\s/g, "") != "") {
      // disable all input box once "Let's Go!" is clicked:
      $("#user-role").prop("disabled", true);
      $("#ai-role").prop("disabled", true);
      $("#chat-context").prop("disabled", true);
      $("#chat-language").prop("disabled", true);
      $("#chat-level").prop("disabled", true);
      $("#system-context").prop("disabled", true);
      $("#chat-model").prop("disabled", true);
      $("#user-api-key").prop("disabled", true);

      // Set up environment and user prefix for chat:
      // Left window system config:
      leftSystemConfig = "You are the " + aiRole + " at this " + chatContext + ", " +
         "and the user is the " + userRole + " at this " + chatContext + ". " +
         "You and the user will have a conversation in " + chatLanguage + ". " +
         "Please make sure your replies are culturally appropriate, and always keep in mind your and the user's roles in the above scenario.";
      if (userSystemInput.replace(/\s/g, "") != "") {
         leftSystemConfig = leftSystemConfig + " " + userSystemInput;
      }

      // Set level suffix:
      if (chatLevel === "Easy") {
         levelSuffix = easySuffix;
      } else if (chatLevel === "Moderate") {
         levelSuffix = moderateSuffix;
      } else if (chatLevel === "Expert") {
         levelSuffix = expertSuffix;
      }

      // Add header to left main chat window based on user input information:
      $("#main-chat-window-header").html("Chat for " + userRole + " (user) & " + aiRole + " (AI)");

      // Add initial log message in the export log arrays:
      leftExportLog.push("This is the chat log history between " + userRole + " (user) and " + aiRole + " (AI) at the " + chatContext + " in " + chatLanguage + ".\n");
      rightExportLog.push("This is the chat log history between Student (user) and Teacher (AI).\n");
      
      // show chat windows:
      configClicked = true;
      $(".chat-box-container").css("visibility", "visible");
   }
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

// Add user input message to chatbox:
function addUserMessage(message, chatBoxNumber) {
   const chatBoxId = '#chatBox' + chatBoxNumber;
   if (chatBoxNumber == 1) {
      message = userRole + ": " + message;
   } else {
      message = "Student: " + message;
   }
   $(chatBoxId).append(`<div class="message">${message}</div>`);

   // Auto scroll to the bottom:
   $(chatBoxId).scrollTop($(chatBoxId)[0].scrollHeight);
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
   
   // Auto scroll to the bottom:
   $(chatBoxId).scrollTop($(chatBoxId)[0].scrollHeight);
}

// Add system message.
// caseNumber = 1 meaning its a system message, 2 meaning it should be centered as a notification:
function addSystemMessage(message, caseNumber) {
   const chatBoxId = '#chatBox2';
   if (caseNumber == 1) {
      $(chatBoxId).append(`<div class="system-message">${message}</div>`);
   } else {
      $(chatBoxId).append(`<div class="chat-box-header-message">${message}</div>`);
   }

   // Auto scroll to the bottom:
   $(chatBoxId).scrollTop($(chatBoxId)[0].scrollHeight);
}

// Enables the click/enter button function to input a message:
function enterMessage(event, chatBoxNumber) {
   if (event.keyCode === 13) {
      event.preventDefault();
      sendMessage(chatBoxNumber);
   }
}

// Maintain the log history:
function updateLog(chatBoxNumber, message) {
   if (chatBoxNumber == 1) {
      leftChatLog.push(message);
   } else if (chatBoxNumber == 2) {
      rightChatLog.push(message);
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

   // Check to see if on right window and message is a instruction message of "-help", "-level" or "system":
   if (chatBoxNumber == 2 && userInput.startsWith("/")) {
      // This should be considered as a system message, we append it in right export log:
      rightExportLog.push(getCurrentTime() + "USER: " + userInput);

      if (userInput.startsWith("/help")) {
         addSystemMessage("/level [level]:<br>&emsp;&emsp;&emsp;Change current level to [level]<br>&emsp;&emsp;&emsp;[level] must be Easy, Moderate, or Expert", 1);
         addSystemMessage("/system [message]:<br>&emsp;&emsp;&emsp;Add instruction to chat bot<br>&emsp;&emsp;&emsp;e.g. You are upset./Start sentence with...", 1);
         rightExportLog.push(getCurrentTime() + "SYSTEM: /level [level]: Change current level to [level], [level] must be Easy, Moderate, or Expert.\t" +
            "/system [message]: Add instruction to chat bot. e.g. You are upset./Start sentence with...");
      } else if (userInput.startsWith("/level")) {
         // Get level:
         var newLevel = userInput.substring(userInput.indexOf("/level ") + "/level ".length);
         newLevel = newLevel.replace(/\s/g, "");   // remove all spaces
         newLevel = normalizeString(newLevel);
         if (newLevel === "Easy" || newLevel === "Moderate" || newLevel === "Expert") {
            if (newLevel === chatLevel) {
               addSystemMessage("---Level unchanged---", 2);
               rightExportLog.push(getCurrentTime() + "SYSTEM: ---Level unchanged---");
            } else {
               // Update left reminder counter:
               leftCounter = 3;
               // Update select value to avoid confusion:
               $("#chat-level").prop("disabled", false);
               $("#chat-level").val(newLevel);
               $("#chat-level").prop("disabled", true);
               // Show message:
               addSystemMessage("---Level changed from " + chatLevel + " to " + newLevel + "---", 2);
               rightExportLog.push(getCurrentTime() + "SYSTEM: ---Level changed from " + chatLevel + " to " + newLevel + "---");
               // Update chat level:
               chatLevel = newLevel;
               // Add new system message to left log history to take effect:
               if (chatLevel === "Easy") {
                  levelSuffix = easySuffix;
               } else if (chatLevel === "Moderate") {
                  levelSuffix = moderateSuffix;
               } else {
                  levelSuffix = expertSuffix;
               }
               if (leftChatLog.length === 0) {
                  updateLog(1, {'role': 'system', 'content': leftSystemConfig +  " " + levelSuffix});
               } else {
                  updateLog(1, {'role': 'system', 'content': "From now on, in the following conversation, " + levelSuffix});
               }
            }
         } else {
            addSystemMessage("---Invalid level---", 2);
            rightExportLog.push(getCurrentTime() + "SYSTEM: ---Invalid level---");
         }
      } else if (userInput.startsWith("/system")) {
         // Get system message:
         var newSystemMessage = userInput.substring(userInput.indexOf("/system ") + "/system ".length);
         // Add new system message to left log history:
         updateLog(1, {'role': 'system', 'content': newSystemMessage});
         addSystemMessage("System message: \"" + newSystemMessage + "\" has been successfully configured.", 1);
         rightExportLog.push(getCurrentTime() + "SYSTEM: " + "System message: \"" + newSystemMessage + "\" has been successfully configured.");
      } else {
         addSystemMessage("---Invalid instruction---<br>---Type /help for more information---", 2);
         rightExportLog.push(getCurrentTime() + "SYSTEM: ---Invalid instruction---\t---Type /help for more information---");
      }
   } else {
      // add user message to log history for export:
      if (chatBoxNumber == 1) {
         const currUserMessage = getCurrentTime() + userRole + ": " + userInput;
         leftExportLog.push(currUserMessage);
      } else {
         const currUserMessage = getCurrentTime() + "Student: " + userInput;
         rightExportLog.push(currUserMessage);
      }

      // Add user message to chatbox:
      addUserMessage(userInput, chatBoxNumber);

      // Add loading icon:
      const chatBoxId = '#chatBox' + chatBoxNumber;
      // current_url + /static/images/loading.gif
      $(chatBoxId).append(`<div class="loading"><img id="loading-logo" src="static/images/loading.gif"></div>`);
      $(chatBoxId).scrollTop($(chatBoxId)[0].scrollHeight);

      // Build the message from history log:
      var messages = buildMessage(chatBoxNumber, userInput);   // get it from history log
      let payload = {'api': userAPIKey, 'model': userModel, 'messages': messages};  // payload include gpt model, api-key, and messages

      // Execute ajax call:
      $.ajax({
         type: 'POST',
         // url: '/chatlanguagelearning/chat',  // change to this one when deploy on server
         url: 'chatlanguagelearning/chat',  
         contentType: 'application/json',
         data: JSON.stringify(payload),
         success: function (response) {
            var assistantReply = response.message;

            // Remove loading icon and add assistant message to chat:
            $(".loading").remove();
            addAssistantMessage(assistantReply, chatBoxNumber);

            // Add this new assistant message in the log history:
            if (chatBoxNumber == 1) {
               updatedLeftMessage = true; // now we can get this assistant message add to the right window system message as a reference
               prevLeftAssistantMessage = assistantReply;   // update this value
            }
            updateLog(chatBoxNumber, {'role': 'assistant', 'content': assistantReply});

            // Add assistant reply to log history for export:
            if (chatBoxNumber == 1) {
               const currUserMessage = getCurrentTime() + aiRole + ": " + assistantReply;
               leftExportLog.push(currUserMessage);
            } else {
               const currUserMessage = getCurrentTime() + "Teacher: " + assistantReply;
               rightExportLog.push(currUserMessage);
            }

            // Update left counter for difficulty reminder:
            leftCounter--;
            if (leftCounter === 0) {
               leftCounter = 3;
               updateLog(1, {'role': 'system', 'content': levelSuffix});
            }
         },
         error: function (error) {
            console.error('Error:', error);
         }
      });
   }
}

// Build the payload messages from log history:
function buildMessage(chatBoxNumber, userInput) {
   var messages = new Array();
   
   // Add history log messages:
   if (chatBoxNumber === 1) {
      if (leftChatLog.length === 0) {
         updateLog(chatBoxNumber, {'role': 'system', 'content': leftSystemConfig + " " + levelSuffix});
      }
      // Add all history log into message:
      for (var i = 0; i < leftChatLog.length; i++) {
         messages.push(leftChatLog[i]);
      }
   } else {
      if (rightChatLog.length === 0) {
         updateLog(chatBoxNumber, {'role': 'system', 'content': rightSystemConfig});
      } 
      // Avoid repeat system message:
      if (prevLeftAssistantMessage.replace(/\s/g, "") != "" && updatedLeftMessage) {
         updatedLeftMessage = false;
         updateLog(chatBoxNumber, {'role': 'system', 'content': 'Answer student question based on this: ' + prevLeftAssistantMessage});
      }
      // Add all history log into message:
      for (var i = 0; i < rightChatLog.length; i++) {
         messages.push(rightChatLog[i]);
      }
   }

   // Add the new user input message, and update this into the correct log:
   messages.push({'role': 'user', 'content': userInput}); // add user input message
   updateLog(chatBoxNumber, {'role': 'user', 'content': userInput});
   return messages;
}

// Get current time for the time stamp to store in log:
function getCurrentTime() {
   const currentTime = new Date();

   // current date components:
   const year = currentTime.getFullYear();
   const month = currentTime.getMonth() + 1; // months are zero-based, add 1 to get the actual month
   const day = currentTime.getDate();

   // current time components:
   const hours = currentTime.getHours();
   const minutes = currentTime.getMinutes();
   const seconds = currentTime.getSeconds();

   // "year-month-day hour-minute-second: "
   const formattedDateTime = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}: `;
   return formattedDateTime;
}

// Generate UID for log file based on current time:
function getUID() {
   const currentTime = new Date();

   // current date components:
   const year = currentTime.getFullYear();
   const month = currentTime.getMonth() + 1; // months are zero-based, add 1 to get the actual month
   const day = currentTime.getDate();

   // current time components:
   const hours = currentTime.getHours();
   const minutes = currentTime.getMinutes();
   const seconds = currentTime.getSeconds();

   // Combine the extracted parts to form the UID
   const uid = `${year}${month}${day}${hours}${minutes}${seconds}`;
   return uid;
}

// Generate a txt file for export log history and auto-downloading:
function generateLogFile(chatBoxNumber) {
   // one line per chat history
   let chatLog = "";
   if (chatBoxNumber === 1) {
      chatLog = leftExportLog.join("\n"); 
   } else {
      chatLog = rightExportLog.join("\n"); 
   }

   const blob = new Blob([chatLog], { type: "text/plain" });
   const url = URL.createObjectURL(blob);
   const link = document.createElement("a");
   link.href = url;

   if (chatBoxNumber == 1) {
      link.download = getUID() + "_" + userRole + "_" + aiRole + "_log.txt";
   } else {
      link.download = getUID() + "_" + "Student_Teacher_log.txt";
   }

   // trigger the download:
   link.click();

   // after the download clean up the URL object:
   URL.revokeObjectURL(url);
}

// Tour function.
function startTour() {
   introJs().setOptions({
      keyboardNavigation: false,
      steps: [
         {
            intro: "Welcome!<br><br>This is a language learning tool that allows you to role-play different characters in a target language of your choosing.<br><br>Let's get started!"
         }, 
         {
            element: document.querySelector('#info-form'),
            intro: "This is the configuration section. Here, you can set information about the role-playing scenario."
         },
         {
            element: document.querySelector('#chat-context'),
            intro: "Pick the role-play scenario, e.g., Restaurant."
         },
         {
            element: document.querySelector('#ai-role'),
            intro: "Pick chatbot's role, e.g., Waiter."
         },
         {
            element: document.querySelector('#user-role'),
            intro: "Pick your role, e.g., Customer."
         },{
            element: document.querySelector('#chat-language'),
            intro: "Pick the language you want to learn. <br><br>Please refer to: <a class='custom-link' href='https://acutrans.com/languages-supported-by-chatgpt/' target='_blank'>supported languages</a>."
         },
         {
            element: document.querySelector('#chat-level'),
            intro: "Easy level: replies from the chatbot are usually short and simple.<br><br>Moderate level: replies are short but with intermediate level grammars and vocabularies." +
               "<br><br>Expert level: replies are more lengthy and creative.",
         },
         {
            element: document.querySelector('#chat-model'),
            intro: "Choose the chat model.<br><br>Note: some API keys do not support GPT-4."
         },
         {
            element: document.querySelector('#system-context'),
            intro: "You can give the chatbot an optional command to behave in a certain way, e.g. Today is a rainy day."
         },
         {
            element: document.querySelector('#user-api-key'),
            intro: "You can enter your API key for one time use.<br><br>We do NOT store or cache your API keys."
         },
         {
            element: document.querySelector('#start-button'),
            intro: "Click here begin! <br><br>You will see two chat windows pop up below."
         },
         {
            element: document.querySelector('#inputBox1'),
            intro: "You can start chat in the language and the role-playing scenario you've just configured.",
         },
         {
            element: document.querySelector('#chatBox1'),
            intro: "The chatbot will chat with you based on your inputs.",
         },
         {
            element: document.querySelector('#inputBox2'),
            intro: "You can ask questions regarding with the chatbot's replies in any language here.<br><br>Please make sure to indicate the related language in your questions, e.g. How to say xxx in French..." +
               "<br><br>You can also change language difficulty level and add additional notes for the chatbot. Type /help to find out more."
         },
         {
            element: document.querySelector('#chatBox2'),
            intro: "The chatbot will answer your questions like a language teacher. <br><br>All system messages will show in a different color.",
         },
         {
            element: document.querySelector('#export-button-1'),
            intro: "You can download your chat history anytime."
         },
         {
            element: document.querySelector('#restart-button'),
            intro: "When you're done with the current chat, click here to restart everything!"
         }
      ]
   }).start();
}