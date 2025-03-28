import pandas as pd
import numpy as np
import json
import time
import os
from datetime import datetime, timedelta, timezone
import uuid # Pour générer des ID de requêtes uniques

# --- Importer la fonction ZigZag ---
try:
    from src.tools.signal_utils import calculate_zigzag_pivots
    print("Fonction calculate_zigzag_pivots importée avec succès.")
except ImportError:
    print("ERREUR: Impossible d'importer calculate_zigzag_pivots.")
    print("Vérifiez le chemin et l'emplacement du fichier signal_utils.py")
    exit()

# --- Configuration ---
# Chemins des fichiers de communication (adaptés pour Wine/Linux)
WINE_PREFIX = os.path.expanduser("~/.wine64") # << Adapté à .wine64
MT5_FILES_PATH_UNDER_WINE = "drive_c/Program Files/MetaTrader 5/MQL5/Files"
REQUEST_FILE_PATH = os.path.join(WINE_PREFIX, MT5_FILES_PATH_UNDER_WINE, "requests.txt")
RESPONSE_FILE_PATH = os.path.join(WINE_PREFIX, MT5_FILES_PATH_UNDER_WINE, "responses.txt")

print(f"Utilisation des chemins de fichiers:")
print(f"  Requêtes : {REQUEST_FILE_PATH}")
print(f"  Réponses : {RESPONSE_FILE_PATH}")

# Vérifier l'existence du répertoire MQL5/Files
files_dir = os.path.dirname(REQUEST_FILE_PATH)
if not os.path.isdir(files_dir):
    print(f"\nERREUR: Le répertoire des fichiers ({files_dir}) ne semble pas exister.")
    exit()
else:
    print(f"Le répertoire des fichiers ({files_dir}) existe.")

# Paramètres du test
SYMBOL = "US30.cash"
TIMEFRAME_STR = "M1"
ZIGZAG_LENGTH = 9
RESPONSE_TIMEOUT_SECONDS = 10
RESPONSE_POLL_INTERVAL = 0.1

# --- Définir le NOMBRE de bougies à demander ---
# On demande un peu plus pour les calculs initiaux
data_count_request = 300 # Demandons 300 bougies (ajustez si besoin)
print(f"\nDemande des {data_count_request} dernières bougies M1 pour {SYMBOL}")


# --- Fonctions de Communication Fichiers ---
# (Les fonctions write_request, clear_request_file, read_response, send_command_and_wait
#  restent les mêmes que dans la version précédente)
def write_request(command: str, request_id: str) -> bool:
    request_content = f"ID:{request_id}|{command}"
    try:
        with open(REQUEST_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(request_content)
        print(f"  Requête écrite ({request_id}): {command}")
        return True
    except Exception as e:
        print(f"ERREUR lors de l'écriture dans {REQUEST_FILE_PATH}: {e}")
        return False

def clear_request_file():
     try:
         with open(REQUEST_FILE_PATH, 'w', encoding='utf-8') as f:
             f.write("")
     except Exception as e:
         print(f"ERREUR lors de l'effacement de {REQUEST_FILE_PATH}: {e}")

def read_response(expected_request_id: str) -> str | None:
    try:
        if not os.path.exists(RESPONSE_FILE_PATH):
            return None
        with open(RESPONSE_FILE_PATH, 'r', encoding='utf-8') as f:
            response_content = f.read().strip()
        if not response_content:
            return None
        if response_content.startswith(f"ID:{expected_request_id}|"):
            response_data = response_content.split('|', 1)[1]
            print(f"  Réponse reçue ({expected_request_id}): {response_data[:100]}...")
            return response_data
    except Exception as e:
        print(f"ERREUR lors de la lecture de {RESPONSE_FILE_PATH}: {e}")
    return None

def send_command_and_wait(command: str) -> str | None:
    request_id = str(uuid.uuid4())[:8]
    try:
        if os.path.exists(RESPONSE_FILE_PATH):
            os.remove(RESPONSE_FILE_PATH)
    except Exception as e:
        print(f"Avertissement: Impossible d'effacer l'ancien fichier réponse: {e}")
    if not write_request(command, request_id):
        return None
    start_wait_time = time.time()
    while time.time() - start_wait_time < RESPONSE_TIMEOUT_SECONDS:
        response = read_response(request_id)
        if response is not None:
            clear_request_file()
            return response
        time.sleep(RESPONSE_POLL_INTERVAL)
    print(f"ERREUR: Timeout - Requête {request_id}")
    clear_request_file()
    return None
# --- Fin Fonctions Communication ---


# --- Récupération des données via l'EA ---
print("\nEnvoi de la commande DATA à l'EA...")
data_command = f"DATA {SYMBOL} {TIMEFRAME_STR} {data_count_request}"
response_data_str = send_command_and_wait(data_command)

if response_data_str is None or response_data_str.startswith("ERROR"):
    print(f"ERREUR: L'EA n'a pas pu fournir les données. Réponse: {response_data_str}")
    exit()

# --- Parsing de la réponse JSON de l'EA ---
print("Parsing de la réponse JSON...")
try:
    json_part = response_data_str.split('[', 1)[1].rsplit(']', 1)[0]
    json_data_str = '[' + json_part + ']'
    data_list = json.loads(json_data_str)
    if not data_list:
        print("ERREUR: La liste de données JSON est vide.")
        exit()
    print(f"{len(data_list)} barres reçues et parsées depuis l'EA.")

    rates_df = pd.DataFrame(data_list)
    rates_df['time'] = pd.to_datetime(rates_df['time'], unit='s', utc=True)
    rates_df.set_index('time', inplace=True)
    rates_df.rename(columns={'high': 'High', 'low': 'Low', 'close': 'Close', 'open': 'Open'}, inplace=True)
    required_cols = ['Open', 'High', 'Low', 'Close']
    if not all(col in rates_df.columns for col in required_cols):
        print(f"ERREUR: Colonnes manquantes. Reçu: {rates_df.columns.tolist()}")
        exit()
    rates_df = rates_df[required_cols]

    # !!!! LIGNE DE FILTRAGE SUPPRIMÉE !!!!
    # rates_df = rates_df.loc[start_datetime_utc : end_datetime_utc]

    # Afficher la période réelle des données reçues
    if not rates_df.empty:
        actual_start_time = rates_df.index.min()
        actual_end_time = rates_df.index.max()
        print(f"\nDonnées traitées pour la période UTC réelle: {actual_start_time} à {actual_end_time}")
    else:
        print("\nERREUR: DataFrame vide après parsing, impossible de continuer.")
        exit()

    print("Premières lignes du DataFrame (données réelles):")
    print(rates_df.head())
    print("Dernières lignes du DataFrame (données réelles):")
    print(rates_df.tail())

except Exception as e:
    print(f"ERREUR lors du parsing JSON ou création DataFrame: {e}")
    print("Réponse brute reçue (début):", response_data_str[:500])
    import traceback
    traceback.print_exc()
    exit()

# --- Exécution de la fonction ZigZag ---
print(f"\nCalcul des pivots ZigZag (length={ZIGZAG_LENGTH}) sur {len(rates_df)} barres...")
try:
    zigzag_pivots = calculate_zigzag_pivots(rates_df, length=ZIGZAG_LENGTH)
    print("Calcul terminé.")
except Exception as e:
    print(f"ERREUR pendant l'exécution de calculate_zigzag_pivots: {e}")
    import traceback
    traceback.print_exc()
    exit()

# --- Affichage des résultats ---
print("\nPivots ZigZag détectés par la fonction Python:")
if not zigzag_pivots:
    print("Aucun pivot détecté.")
else:
    # Afficher les 15-20 derniers pivots pour comparaison facile
    start_index = max(0, len(zigzag_pivots) - 20)
    print(f"(Affichage des {len(zigzag_pivots) - start_index} derniers pivots sur {len(zigzag_pivots)} détectés)")
    for i in range(start_index, len(zigzag_pivots)):
        pivot = zigzag_pivots[i]
        pivot_time_utc = pivot['index']
        print(f"- Time (UTC): {pivot_time_utc}, Price: {pivot['price']:.5f}, Type: {pivot['type']}, Status: {pivot['status']}")

print("\n--- ACTION REQUISE ---")
print(f"1. L'EA EA_AkobenConnector doit être actif sur un graphique MT5 (sous Wine).")
print(f"2. Ouvrez TradingView pour {SYMBOL} en M1.")
print(f"3. Affichez votre indicateur ZigZag (length={ZIGZAG_LENGTH}).")
print(f"4. Comparez MANUELLEMENT les pivots affichés ci-dessus avec ceux visibles sur TradingView")
print(f"   pour la période récente correspondant approximativement à :")
if 'actual_start_time' in locals() and 'actual_end_time' in locals():
      print(f"   {actual_start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC à {actual_end_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
else:
      print("   (Période non déterminée)")
print(f"5. Concentrez-vous sur les 15-20 derniers pivots pour la comparaison.")
print(f"6. Vérifiez la correspondance (Time UTC, Prix, Type, Statut HH/LL...).")
print(f"7. Faites-moi part des résultats.")
print("----------------------")