function sendMessage() {
    const userInput = document.getElementById("user-input");
    const chatBox = document.getElementById("chat-box");

    const userMessage = userInput.value.trim();
    if (userMessage) {
        // Zeige die Nachricht des Benutzers
        chatBox.innerHTML += `
            <div class="message user-message">
                <div class="text">${userMessage}</div>
                <img class="icon" src="https://cdn-icons-png.flaticon.com/512/456/456212.png">
            </div>
        `;
        userInput.value = "";

        // Anfrage an den Flask-Server
        fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: userMessage }),
        })
        .then(response => response.json())
        .then(data => {
            const botMessages = data.bot_messages; // Liste von Bot-Nachrichten
            botMessages.forEach(botMessage => {
                chatBox.innerHTML += `
                    <div class="message bot-message">
                        <img class="icon" src="https://upload.wikimedia.org/wikipedia/en/0/03/National_Basketball_Association_logo.svg">
                        <div class="text">${botMessage}</div>
                    </div>
                `;
            });
            chatBox.scrollTop = chatBox.scrollHeight; // Scroll nach unten
        })
        .catch(error => {
            console.error("Fehler beim Senden der Nachricht:", error);
            chatBox.innerHTML += `
                <div class="message bot-message">
                    <div class="text">Fehler beim Verbinden mit dem Server.</div>
                </div>
            `;
        });
    }
}

document.addEventListener("DOMContentLoaded", function () {
    // Begrüßungsnachricht des Bots
    const chatBox = document.getElementById("chat-box");
    const botMessage = "Heyy:) Willkommen beim NBA Chatbot! Stelle mir Fragen über einzelne Spieler oder vergleiche sie miteinander. Wenn du Hilfe benötigst, gib einfach 'Hilfe' ein.";
    chatBox.innerHTML += `
        <div class="message bot-message">
            <img class="icon" src="https://upload.wikimedia.org/wikipedia/en/0/03/National_Basketball_Association_logo.svg">
            <div class="text">${botMessage}</div>
        </div>
    `;
});

function checkEnter(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
}
