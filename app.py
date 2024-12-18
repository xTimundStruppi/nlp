from flask import Flask, render_template, request, jsonify
import requests
import logging

app = Flask(__name__)

# Logging konfigurieren
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")
    try:
        # Anfrage an den Rasa-Server
        response = requests.post(
            "http://localhost:5005/webhooks/rest/webhook",
            json={"sender": "flask_user", "message": user_message},
        )
        bot_responses = response.json()

        # Alle Nachrichten sammeln und formatieren
        bot_messages = []
        for msg in bot_responses:
            if "text" in msg:  # Prüfe, ob die Nachricht Text enthält
                # Ersetze Zeilenumbrüche für HTML
                formatted_message = msg["text"].replace("\n", "<br><br>")
                bot_messages.append(formatted_message)

        # Sende alle Nachrichten als Liste zurück
        return jsonify({"bot_messages": bot_messages})
    except Exception as e:
        return jsonify({"bot_messages": ["Fehler beim Verbinden mit dem Bot."]})


if __name__ == '__main__':
    app.run(debug=True)
