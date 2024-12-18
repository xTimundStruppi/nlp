import re
from typing import Any, Text, Dict, List, Tuple
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import sqlite3
# Dictionary mit Synonymen für "alltime" und "season"
DURATION_SYNONYMS = {
    "alltime": ["alltime", "aller zeiten", "gesamt", "total", "insgesamt", "in seiner karriere"],
    "season": ["saison", "in der saison"]
}

# Dictionary mit Synonymen für Statistiken
STAT_SYNONYMS = {
    "punkte": ["punkte", "points", "pts"],
    "assists": ["assists", "ast"],
    "rebounds": ["rebounds", "reb"],
    "steals": ["steals", "stl"],
    "turnovers": ["turnovers", "tov", "turnover"],
    "blocks": ["blocks", "blk"],
    "plus_minus": ["plus_minus", "plusminus","plus/minus" ],
    "fgm": ["fgm", "field goals made","treffer", "körbe"],
    "fga": ["fga", "field goals attempted", "fg versuche", "wurfversuche"],
    "fg_pct": ["fg_pct", "field goal percentage", "wurfquote"],
    "fg3m": ["fg3m", "three point field goals made", "dreier"],
    "fg3a": ["fg3a", "three point field goals attempted", "dreierversuche", "dreier versuche"],
    "fg3_pct": ["fg3_pct", "three point field goal percentage", "dreierquote"],
    "ftm": ["ftm", "free throws made", "freiwürfe"],
    "fta": ["fta", "free throws attempted", "freiwurfversuche"],
    "ft_pct": ["ft_pct", "free throw percentage","freiwurfquote"],
    "oreb": ["oreb", "offensive rebounds", "offensiven rebounds"],
    "dreb": ["dreb", "defensive rebounds", "defensiven rebounds"],
    "pf": ["pf", "personal fouls", "fouls"],
    "ol":["offensiven leistung", "offensivleistungen", "offensiv"],
    "dl":["defensiven leistung", "defensivleistungen", "defensiv"]
}

def extract_entities(tracker: Tracker) -> Dict[str, Any]:
    player_name = list(tracker.get_latest_entity_values("player_name")) 

    if not player_name:
        player_name = None
    stat = next(tracker.get_latest_entity_values("stat"), None)  # Standardmäßig "points"
    duration = next(tracker.get_latest_entity_values("stat_type"), "alltime")  # Standardmäßig "alltime"
    average = next(tracker.get_latest_entity_values("average"), None)
    team = next(tracker.get_latest_entity_values("team"), None)
    return {"player_name": player_name, "stat": stat, "duration": duration, "average": average, "team": team}

def get_stat_index(stat: str) -> int:
    for key, synonyms in STAT_SYNONYMS.items():
        if stat.lower() in synonyms:
            if key == "punkte":
                return 4  # 'PTS' ist die 4. Spalte
            elif key == "assists":
                return 6  # 'AST' ist die 6. Spalte
            elif key == "rebounds":
                return 5  # 'REB' ist die 5. Spalte
            elif key == "steals":
                return 7
            elif key == "turnovers":
                return 8
            elif key == "blocks":
                return 9
            elif key == "plus_minus":
                return 10
            elif key == "fgm":
                return 12
            elif key == "fga":
                return 11
            elif key == "fg_pct":
                return 13
            elif key == "fg3m":
                return 15
            elif key == "fg3a":
                return 14
            elif key == "fg3_pct":
                return 16
            elif key == "ftm":
                return 18
            elif key == "fta":
                return 17
            elif key == "ft_pct":
                return 19
            elif key == "oreb":
                return 20
            elif key == "dreb":
                return 21
            elif key == "pf":
                return 22
            elif key == "ol":
                return 23
            elif key == "dl":
                return 24
    return -1  # Unbekannte Statistik

def check_duration_synonym(duration: str) -> str:
    for key, synonyms in DURATION_SYNONYMS.items():
        if any(synonym in duration.lower() for synonym in synonyms):
            return key
    # Überprüfen, ob die Dauer eine Saison im Format YYYY-YY enthält
    if re.search(r'\b\d{4}-\d{2}\b', duration):
        return "season"
    return "unknown"

def extract_season(duration: str) -> str:
    # Muster für die Saison im Format YYYY-YY
    pattern = r'\b(\d{4}-\d{2})\b'
    match = re.search(pattern, duration)
    if match:
        return match.group(1)
    return None

def averagePercents(stat_index: int, result: List[Tuple]) -> float:

    # FG%, FT%, 3P%
    if stat_index == 13:
        total_attempts = sum(row[11] for row in result)
        total_makes = sum(row[12] for row in result)
        if total_attempts == 0:
            return None, 0
        else:
            fg_percentage = total_makes / total_attempts * 100
            return fg_percentage, total_attempts

    if stat_index == 16:
        total_attempts = sum(row[14] for row in result)
        total_makes = sum(row[15] for row in result)
        if total_attempts == 0:
            return None, 0
        else:
            fg_percentage = total_makes / total_attempts * 100
            return fg_percentage, total_attempts
            
    if stat_index == 19: 
        total_attempts = sum(row[17] for row in result)
        total_makes = sum(row[18] for row in result)
        if total_attempts == 0:
            return None, 0
        else:
            fg_percentage = total_makes / total_attempts * 100
            return fg_percentage, total_attempts

    total_stat = sum(row[stat_index] for row in result)
    total_attempts = sum(row[stat_index + 1] for row in result)
    if total_attempts == 0:
        return 0.0
    return total_stat / total_attempts * 100