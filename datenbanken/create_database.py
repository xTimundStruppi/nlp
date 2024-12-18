import sqlite3
import re
import time
import os
import numpy as np
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelogs, commonplayerinfo
import unicodedata


all_players = players.get_players()

# SQL-Datenbank erstellen/verbinden
db_name = "team_nba_player_games_test.db"
conn = sqlite3.connect(db_name)
cursor = conn.cursor()

# Funktion: Spieler-ID anhand des Namens finden
def get_player_id(player_name):
    player = players.find_players_by_full_name(player_name)
    if player:
        return player[0]['id']  # ID zurückgeben
    return None

# Funktion: Alle Saisons ab 2000 für einen Spieler abrufen
def get_all_seasons(player_id):
    retry_count = 0
    while retry_count < 5:
        player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_data_frames()[0]
        from_year = player_info['FROM_YEAR'].values[0]
        to_year = player_info['TO_YEAR'].values[0]
        
        if from_year is None or to_year is None:
            print(f"Ungültige Daten für Spieler-ID {player_id}, Anfrage wird wiederholt...")
            time.sleep(1)  # Wartezeit von 1 Sekunde vor der erneuten Anfrage
            retry_count += 1
            continue
        
        from_year = max(from_year, 2000)  # Nur Saisons ab 2000
        return [f"{year}-{str(year+1)[-2:]}" for year in range(from_year, to_year + 1)]
    
    print(f"Maximale Anzahl von Wiederholungen erreicht für Spieler-ID {player_id}. Weiter mit nächstem Spieler.")
    return []

# Funktion: Tabelle für einen Spieler erstellen
def create_player_table(player_name):
    table_name = re.sub(r'\W+', '_', player_name)  # Ersetze nicht alphanumerische Zeichen durch Unterstriche
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {table_name} (
        game_id TEXT,
        game_date TEXT,
        team_abbreviation TEXT,
        season TEXT,
        pts INTEGER,
        reb INTEGER,
        ast INTEGER,
        stl INTEGER,
        tov INTEGER,
        blk INTEGER,
        plus_minus INTEGER,
        fga INTEGER,
        fgm INTEGER,
        fg_pct REAL,
        fg3a INTEGER,
        fg3m INTEGER,
        fg3_pct REAL,
        fta INTEGER,
        ftm INTEGER,
        ft_pct REAL,
        oreb INTEGER,
        dreb INTEGER,
        pf INTEGER,
        opponent_team_abbreviation TEXT
    )
    ''')
    conn.commit()
    return table_name

# Funktion: Datenbankgröße überprüfen und Skript beenden, wenn sie 6 GB überschreitet
def check_db_size_and_exit(db_name):
    db_size = os.path.getsize(db_name)
    if db_size >= 6 * 1024 * 1024 * 1024:  # 6 GB in Bytes
        print("Datenbankgröße hat 6 GB überschritten. Skript wird beendet.")
        conn.close()
        exit()

# Funktion: Spiele abrufen und speichern
def fetch_and_store_games(player_name):
    player_id = get_player_id(player_name)
    if not player_id:
        print(f"Spieler-ID für {player_name} nicht gefunden.")
        return

    table_name = create_player_table(player_name)

    seasons = get_all_seasons(player_id)
    if not seasons:
        print(f"Keine gültigen Saisons für {player_name} gefunden.")
        return

    for season in seasons:
        try:
            # Spiele abrufen
            game_logs = playergamelogs.PlayerGameLogs(season_nullable=season, player_id_nullable=player_id, timeout=60)
            games = game_logs.get_data_frames()[0]

            if games.empty:
                print(f"Keine Spieldaten für {player_name} in Saison {season} gefunden.")
                continue

            for _, row in games.iterrows():
                data_to_insert = (
                    row.get('GAME_ID', None),
                    row.get('GAME_DATE', None),
                    row.get('TEAM_ABBREVIATION', None),
                    season,
                    row.get('PTS', None),
                    row.get('REB', None),
                    row.get('AST', None),
                    row.get('STL', None),
                    row.get('TOV', None),
                    row.get('BLK', None),
                    row.get('PLUS_MINUS', None),
                    row.get('FGA', None),
                    row.get('FGM', None),
                    row.get('FG_PCT', None),
                    row.get('FG3A', None),
                    row.get('FG3M', None),
                    row.get('FG3_PCT', None),
                    row.get('FTA', None),
                    row.get('FTM', None),
                    row.get('FT_PCT', None),
                    row.get('OREB', None),
                    row.get('DREB', None),
                    row.get('PF', None),
                    row.get('MATCHUP', '').split(' ')[2] if 'MATCHUP' in row else None  # Gegnerteam aus Matchup extrahieren
                )

                # Ersetze nan-Werte durch None
                data_to_insert = [None if isinstance(x, float) and np.isnan(x) else x for x in data_to_insert]
                
                cursor.execute(f'''
                INSERT INTO {table_name} (game_id, game_date, team_abbreviation,  season, pts, reb, ast, stl, tov, blk, plus_minus, fga, fgm, fg_pct, fg3a, fg3m, fg3_pct, fta, ftm, ft_pct, oreb, dreb, pf, opponent_team_abbreviation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', data_to_insert)
                
                # Überprüfe die Datenbankgröße nach jedem Einfügen
                check_db_size_and_exit(db_name)

            conn.commit()
            print(f"Daten für {player_name} in Saison {season} gespeichert.")
        except Exception as e:
            print(f"Fehler beim Abrufen der Daten für {player_name} in Saison {season}: {e}")

        # Verzögerung von 1 Sekunde zwischen den Anfragen
        time.sleep(0.25)

# Hauptlogik
for player in all_players:
    fetch_and_store_games(player['full_name'])

# Verbindung schließen
conn.close()