let isSending = false;


function handleKeyPress(event) {

    if (event.key === "Enter") {

        event.preventDefault();

        sendMessage();

    }

}


async function sendMessage() {

    // Prevent duplicate messages
    if (isSending) {
        return;
    }

    const input = document.getElementById("message");
    const chatBox = document.getElementById("chatBox");

    const message = input.value.trim();


    if (message === "") {
        return;
    }


    // Lock sending
    isSending = true;


    // Show user's message
    chatBox.innerHTML += `

        <div class="bot-message">

            <div class="message-avatar">
                👤
            </div>

            <div class="message-bubble">

                <b>You</b>

                <p>
                    ${message}
                </p>

            </div>

        </div>

    `;


    // Clear input
    input.value = "";


    // Scroll down
    chatBox.scrollTop = chatBox.scrollHeight;


    try {

        const response = await fetch("/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: message
            })

        });


        const data = await response.json();


        // Show AI response
        chatBox.innerHTML += `

            <div class="bot-message">

                <div class="message-avatar">
                    🤖
                </div>

                <div class="message-bubble">

                    <b>AI Assistant</b>

                    <p>
                        ${data.response}
                    </p>

                </div>

            </div>

        `;


        // Scroll to latest message
        chatBox.scrollTop = chatBox.scrollHeight;


    } catch (error) {

        console.log("Error:", error);


        chatBox.innerHTML += `

            <div class="bot-message">

                <div class="message-avatar">
                    🤖
                </div>

                <div class="message-bubble">

                    <b>AI Assistant</b>

                    <p>
                        ❌ Sorry, something went wrong. Please try again.
                    </p>

                </div>

            </div>

        `;

    }


    // Unlock sending
    isSending = false;

}


function showMessage(type) {

    const input = document.getElementById("message");


    if (type === "courses") {

        input.value = "Show me available courses";

    }


    else if (type === "eligibility") {

        input.value = "Check my eligibility";

    }


    else if (type === "registration") {

        input.value = "I want to register";

    }


    else if (type === "assistant") {

        input.value = "I need help";

    }


    sendMessage();

}