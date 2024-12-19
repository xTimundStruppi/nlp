from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import sqlite3
import pandas as pd
from .utils import averagePercents, extract_entities, get_stat_index, check_duration_synonym, extract_season
from rasa_sdk.events import SlotSet
from rasa_sdk.events import FollowupAction

def send_stat_message(stat_index: int, dispatcher: CollectingDispatcher, player_name: str, stat: str, total_stat: float, duration_key: str, games: int, season: str = None, average: bool = False, stat_percent: float = None, attempts: int = None, ):

    if stat_index ==10:
        dispatcher.utter_message(text=f"{player_name} hat ein durchschnittliches {stat} von {total_stat:.2f} auf {games} Spiele.")
        return

    if stat_percent is None and attempts == 0:
                    dispatcher.utter_message(text=f"{player_name} hat keine {stat}.")
                    return
    elif stat_percent is not None and attempts != 0:
                    dispatcher.utter_message(text=f"{player_name} hat eine {stat} von {stat_percent:.2f}% auf {attempts} Versuche.")
                    return
    if duration_key == "alltime" and average != None:
        dispatcher.utter_message(text=f"{player_name} hat durchschnittlich {total_stat:.2f} {stat} in {games} Spielen .")
    elif duration_key == "alltime" and average is None:
        dispatcher.utter_message(text=f"{player_name} hat insgesamt {total_stat} {stat} in {games} Spielen.")
    elif duration_key == "season" and average != None:
        dispatcher.utter_message(text=f"{player_name} hat durchschnittlich {total_stat:.2f} {stat} in der Saison {season}. Er hat dabei {games} Spiele absolviert.")
    elif duration_key == "season" and average is None:
        dispatcher.utter_message(text=f"{player_name} hat insgesamt {total_stat} {stat} in der Saison {season}. Er hat dabei {games} Spiele absolviert.")
    
    else:
        dispatcher.utter_message(text=f"Keine Statistiken für {player_name} in diesem Zeitraum gefunden.")

def fetch_and_process_stats(dispatcher: CollectingDispatcher, player_name: str, stat: str, duration: str, average: bool):
    connection = sqlite3.connect("nba_player_games.db")
    cursor = connection.cursor()
    try:
        # Überprüfen der Dauer-Synonyme
        duration_key = check_duration_synonym(duration)
        if duration_key == "alltime":
            query = f"SELECT * FROM {player_name.replace(' ', '_')}"
            season = None
        elif duration_key == "season":
            season = extract_season(duration)
            if not season:
                dispatcher.utter_message(text=f"Keine gültige Eingabe einer Saison: {duration}. Bitte gib die Saison im Format 'Saison 20XX-XX' an. Zum Beispiel 'Saison 2020-21'.")
                return []
            query = f"SELECT * FROM {player_name.replace(' ', '_')} WHERE season = '{season}'"
        else:
            dispatcher.utter_message(text=f"Unknown duration: {duration}")
            return []

        cursor.execute(query)
        result = cursor.fetchall()
        games = len(result)

        if result:
            stat_index = get_stat_index(stat)
            if stat_index == -1:
                dispatcher.utter_message(text=f"Die Statistik {stat} gibt es nicht. Bitte wähle eine gültige Statistik, wie z.B. Punkte oder Rebounds.")
                return []
            
            if average or stat_index ==10:
                total_stat = sum(row[stat_index] for row in result) / len(result)
            else:
                total_stat = sum(row[stat_index] for row in result)
            
            if stat_index == 13 or stat_index == 16 or stat_index == 19:
                stat_percent, attempts = averagePercents(stat_index, result)
            else:
                stat_percent, attempts = None, None
            return stat_index,stat_percent, attempts, total_stat, duration_key, season, games
                
        else:
            dispatcher.utter_message(text=f"Keine Statistiken für {player_name} gefunden.")

    except Exception as e:
        dispatcher.utter_message(text=f"Fehler beim Abrufen der Daten. Bist du sicher, dass du den Spieler richtig geschrieben hast?")
    
    finally:
        connection.close()
    return []
    
def compare_players_stats(dispatcher: CollectingDispatcher, player_names: List[str], stat: str, duration: str):
    comparison = get_stat_index(stat)
    if comparison == 23:
        #punkte
        player1_points = fetch_and_process_stats(dispatcher, player_names[0], "pts", duration, average=True)
        player2_points = fetch_and_process_stats(dispatcher, player_names[1], "pts", duration, average=True)
        #assists
        player1_assists = fetch_and_process_stats(dispatcher, player_names[0], "ast", duration, average=True)
        player2_assists = fetch_and_process_stats(dispatcher, player_names[1], "ast", duration, average=True)
        #rebounds
        player1_rebounds = fetch_and_process_stats(dispatcher, player_names[0], "oreb", duration, average=True)
        player2_rebounds = fetch_and_process_stats(dispatcher, player_names[1], "oreb", duration, average=True)

        dispatcher.utter_message(text=f"{player_names[0]} hat eine durchschnittliche Punktzahl von {player1_points[3]:.2f} pro Spiel, "
                                      f"während {player_names[1]} {player2_points[3]:.2f} Punkte pro Spiel aufweist. "
                                      f"Bezüglich der Assists liefert {player_names[0]} eine durchschnittliche Anzahl "
                                      f"von {player1_assists[3]:.2f}, während {player_names[1]} {player2_assists[3]:.2f} Assists pro Spiel aulegt. "
                                      f"{player_names[0]} hat eine durchschnittliche Anzahl von {player1_rebounds[3]:.2f} offensive Rebounds "
                                      f"pro Spiel, während {player_names[1]} {player2_rebounds[3]:.2f} Boards am gegnerischen Brett pro Spiel.")    

    elif comparison == 24:
        #steals
        player1_steals = fetch_and_process_stats(dispatcher, player_names[0], "stl", duration, average=True)
        player2_steals = fetch_and_process_stats(dispatcher, player_names[1], "stl", duration, average=True)
        #dreb
        player1_dreb = fetch_and_process_stats(dispatcher, player_names[0], "dreb", duration, average=True)
        player2_dreb = fetch_and_process_stats(dispatcher, player_names[1], "dreb", duration, average=True)
        #blocks
        player1_blocks = fetch_and_process_stats(dispatcher, player_names[0], "blk", duration, average=True)
        player2_blocks = fetch_and_process_stats(dispatcher, player_names[1], "blk", duration, average=True)

        dispatcher.utter_message(text=f"{player_names[0]} hat jedes Spiel durchschnittlich {player1_steals[3]:.2f} Steals, "
                                      f"während {player_names[1]} {player2_steals[3]:.2f} Steals pro Spiel auflegt. "
                                      f"In Bezug auf die Blocks hat {player_names[0]} eine durchschnittliche Anzahl "
                                      f"von {player1_blocks[3]:.2f}, während {player_names[1]} {player2_blocks[3]:.2f} Blocks pro Spiel vorweist. "
                                      f"Bei den Rebounds hat {player_names[0]} eine durchschnittliche Anzahl von {player1_dreb[3]:.2f} defensiven Rebounds "
                                      f"pro Spiel und {player_names[1]} {player2_dreb[3]:.2f} Boards am eigenen Brett.")  
                                           
    else:
        player1_stats = fetch_and_process_stats(dispatcher, player_names[0], stat, duration, average=True)
        player2_stats = fetch_and_process_stats(dispatcher, player_names[1], stat, duration, average=True)

        if comparison == 13 or comparison == 16 or comparison == 19:
            if player1_stats and player2_stats:
                if duration == "season":
                    if player1_stats[1] > player2_stats[1]:
                        dispatcher.utter_message(text=f"{player_names[0]} hat eine bessere {stat} als {player_names[1]} in der Saison {duration}. {player_names[0]} trifft mit {player1_stats[1]:.2f}% auf {player1_stats[2]} Versuche, während {player_names[1]} nur {player2_stats[1]:.2f}% auf {player2_stats[2]} Versuche hat.")
                    elif player1_stats[1] < player2_stats[1]:
                        dispatcher.utter_message(text=f"{player_names[1]} hat eine bessere {stat} als {player_names[0]} in der Saison {duration}. {player_names[1]} trifft mit {player2_stats[1]:.2f}% auf {player2_stats[2]} Versuche, während {player_names[0]} nur {player1_stats[1]:.2f}% auf {player1_stats[2]} Versuche hat.")
                    else:
                        dispatcher.utter_message(text=f"{player_names[0]} und {player_names[1]} haben die gleiche {stat}.")

                else:
                    if player1_stats[1] > player2_stats[1]:
                        dispatcher.utter_message(text=f"{player_names[0]} hat eine bessere {stat} als {player_names[1]}. {player_names[0]} trifft mit {player1_stats[1]:.2f}% auf {player1_stats[2]} Versuche, während {player_names[1]} nur {player2_stats[1]:.2f}% auf {player2_stats[2]} Versuche hat.")
                    elif player1_stats[1] < player2_stats[1]:
                        dispatcher.utter_message(text=f"{player_names[1]} hat eine bessere {stat} als {player_names[0]}. {player_names[1]} trifft mit {player2_stats[1]:.2f}% auf {player2_stats[2]} Versuche, während {player_names[0]} nur {player1_stats[1]:.2f}% auf {player1_stats[2]} Versuche hat.")
                    else:
                        dispatcher.utter_message(text=f"{player_names[0]} und {player_names[1]} haben die gleiche {stat}.")
                   
        else:
            if player1_stats and player2_stats:
                if duration == "season":
                    if player1_stats[3] > player2_stats[3]:
                        dispatcher.utter_message(text=f"{player_names[0]} hat mehr {stat} pro Spiel als {player_names[1]} in der Saison {duration}. {player_names[0]} hat durchschnittlich {player1_stats[3]:.2f} {stat} pro Spiel, während {player_names[1]} nur {player2_stats[3]:.2f} {stat} pro Spiel aufweist.")
                    elif player1_stats[3] < player2_stats[3]:
                        dispatcher.utter_message(text=f"{player_names[1]} hat mehr {stat} pro Spiel als {player_names[0]} in der Saison {duration}. {player_names[1]} hat durchschnittlich {player2_stats[3]:.2f} {stat} pro Spiel, während {player_names[0]} nur {player1_stats[3]:.2f} {stat} pro Spiel aufweist.")
                    else:
                        dispatcher.utter_message(text=f"{player_names[0]} und {player_names[1]} haben die gleiche Anzahl an {stat}.")
                
                else:   
                    if player1_stats[3] > player2_stats[3]:
                        dispatcher.utter_message(text=f"{player_names[0]} hat mehr {stat} pro Spiel als {player_names[1]}. {player_names[0]} hat durchschnittlich {player1_stats[3]:.2f} {stat} pro Spiel, während {player_names[1]} nur {player2_stats[3]:.2f} {stat} pro Spiel aufweist.")
                    elif player1_stats[3] < player2_stats[3]:
                        dispatcher.utter_message(text=f"{player_names[1]} hat mehr {stat} pro Spiel als {player_names[0]}. {player_names[1]} hat durchschnittlich {player2_stats[3]:.2f} {stat} pro Spiel, während {player_names[0]} nur {player1_stats[3]:.2f} {stat} pro Spiel aufweist.")
                    else:
                        dispatcher.utter_message(text=f"{player_names[0]} und {player_names[1]} haben die gleiche Anzahl an {stat}.")
                   

class GetPlayerStats(Action):

    def name(self) -> Text:
        return "get_player_stats"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        entities = extract_entities(tracker)
        player_name = entities["player_name"]
        player_name = player_name[0]
        stat = entities["stat"]
        duration = entities["duration"]
        average = entities["average"]

        if not player_name:
            dispatcher.utter_message(text="No player name found.")
            return []
    
        else:
            try:
                stat_index,stat_percent, attempts, total_stat, duration_key, season, games = fetch_and_process_stats(dispatcher, player_name, stat, duration, average)
            except Exception as e:
                return []
            
            send_stat_message(stat_index,dispatcher, player_name, stat, total_stat, duration_key, games, season, average,stat_percent, attempts)
            
            

    
class ComparePlayers(Action):

    def name(self) -> Text:
        return "compare_player_stats"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
           
        entities = extract_entities(tracker)
        player_names = entities["player_name"]
        stat = entities["stat"]
        duration = entities["duration"]

        compare_players_stats(dispatcher, player_names, stat, duration)

class GetPlayerStatsSlots(Action):

    def name(self) -> Text:
        return "get_player_stats_slots"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        

        player_name = tracker.get_slot("player_name")
        stat = tracker.get_slot("stat")
        duration = tracker.get_slot("stat_type")
        #dispatcher.utter_message(text=f"Player name:{duration}")
        average = tracker.get_slot("average")
        if average == "absolut" or average == "Absolut":
            average = None

        if not player_name:
            dispatcher.utter_message(text="No player name found.")
            return []
        
        else:
            try:
                stat_index, stat_percent, attempts, total_stat, duration_key, season, games = fetch_and_process_stats(dispatcher, player_name, stat, duration, average)
            except Exception as e:
                return []
            
            send_stat_message(stat_index, dispatcher, player_name, stat, total_stat, duration_key, games, season, average,stat_percent, attempts)
            

class ComparePlayers(Action):

    def name(self) -> Text:
        return "compare_player_stats_slots"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        player_names = tracker.get_slot("player_names")
        stat = tracker.get_slot("stat")
        duration = tracker.get_slot("stat_type")
        comparison = get_stat_index(stat)
        compare_players_stats(dispatcher, player_names, stat, duration)



class SetPlayerSlots(Action):

    def name(self) -> Text:
        return "set_player_names_slots"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        entities = extract_entities(tracker)
        player_names = entities["player_name"]
        return [SlotSet("player_names", player_names),]