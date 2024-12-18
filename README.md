# Nba Chatbot von Tim Weiß

Um den Bot zu starten, das Repo klonen. Die benötigten Requirements sind in der requirements.txt und können mit 
````
pip install -r requirements.txt
````
installiert werden.
Danach das Model trainieren mit: 
````
rasa train 
````
In verschiedenen Konsolen folgende Befehle starten:

````
rasa run actions
````
````
rasa run --enable-api --cors "*" --debug
````
````
python app.py
````

Auf http://127.0.0.1:5000 kann dann der Chatbot benutzt werden
