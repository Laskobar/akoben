import pandas as pd
import numpy as np
import json
import time
import os
from datetime import datetime, timedelta, timezone
import uuid # Pour générer des ID de requêtes uniques

# --- Importer les fonctions depuis signal_utils ---
try:
    # Assurez-vous que signal_utils.py est dans le bon dossier (src/tools/)
    from src.tools.signal_utils import calculate_zigzag_pivots, find_interest_zone
    print("Fonctions calculate_zigzag_pivots et find_interest_zone importées.")
except ImportError:
    print("ERREUR: Impossible d'importer les fonctions depuis src.tools.signal_utils.")
    print("Vérifiez le chemin et l'emplacement du fichier signal_utils.py")
    exit()

# --- Configuration ---
WINE_PREFIX = os.path.expanduser("~/.wine64")
MT5_FILES_PATH_UNDER_WINE = "drive_c/Program Files/MetaTrader 5/MQL5/Files"
REQUEST_FILE_PATH = os.path.join(WINE_PREFIX, MT5_FILES_PATH_UNDER_WINE, "requests.txt")
RESPONSE_FILE_PATH = os.path.join(WINE_PREFIX, MT5_FILES_PATH_UNDER_WINE, "responses.txt")

print(f"Utilisation des chemins de fichiers:")
print(f"  Requêtes : {REQUEST_FILE_PATH}")
print(f"  Réponses : {RESPONSE_FILE_PATH}")

files_dir = os.path.dirname(REQUEST_FILE_PATH)
if not os.path.isdir(files_dir):
    print(f"\nERREUR: Le répertoire des fichiers ({files_dir}) ne semble pas exister.")
    exit()
else:
    print(f"Le répertoire des fichiers ({files_dir}) existe.")

SYMBOL = "US30.cash"
TIMEFRAME_STR = "M1"
ZIGZAG_LENGTH = 9
SMA_PERIOD = 20
RESPONSE_TIMEOUT_SECONDS = 10
RESPONSE_POLL_INTERVAL = 0.1
data_count_request = 300 + SMA_PERIOD # Demander assez pour calculer SMA + Zigzag
print(f"\nDemande des {data_count_request} dernières bougies M1 pour {SYMBOL}")

# --- Fonctions de Communication Fichiers ---
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
        if not os.path.exists(RESPONSE_FILE_PATH): return None
        with open(RESPONSE_FILE_PATH, 'r', encoding='utf-8') as f:
            response_content = f.read().strip()
        if not response_content: return None
        if response_content.startswith(f"ID:{expected_request_id}|"):
            response_data = response_content.split('|', 1)[1]
            # print(f"  Réponse reçue ({expected_request_id}): {response_data[:100]}...") # Décommenter pour debug
            return response_data
    except Exception as e:
        print(f"ERREUR lors de la lecture de {RESPONSE_FILE_PATH}: {e}")
    return None

def send_command_and_wait(command: str) -> str | None:
    request_id = str(uuid.uuid4())[:8]
    try:
        if os.path.exists(RESPONSE_FILE_PATH): os.remove(RESPONSE_FILE_PATH)
    except Exception as e:
        print(f"Avertissement: Impossible d'effacer l'ancien fichier réponse: {e}")
    if not write_request(command, request_id): return None
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

# --- Initialisation des variables pour les données ---
rates_df = pd.DataFrame()
actual_start_time = None
actual_end_time = None

# --- Récupération et Traitement des Données ---
print("\n--- Récupération et Traitement des Données ---")
try:
    print("Envoi de la commande DATA à l'EA...")
    data_command = f"DATA {SYMBOL} {TIMEFRAME_STR} {data_count_request}"
    response_data_str = send_command_and_wait(data_command)

    if response_data_str is None or response_data_str.startswith("ERROR"):
        raise RuntimeError(f"L'EA n'a pas pu fournir les données. Réponse: {response_data_str}")

    print("Parsing de la réponse JSON...")
    json_part = response_data_str.split('[', 1)[1].rsplit(']', 1)[0]
    json_data_str = '[' + json_part + ']'
    data_list = json.loads(json_data_str)
    if not data_list:
        raise ValueError("La liste de données JSON est vide.")
    print(f"{len(data_list)} barres reçues et parsées depuis l'EA.")

    rates_df = pd.DataFrame(data_list)
    rates_df['time'] = pd.to_datetime(rates_df['time'], unit='s', utc=True)
    rates_df.set_index('time', inplace=True)
    rates_df.rename(columns={'high': 'High', 'low': 'Low', 'close': 'Close', 'open': 'Open'}, inplace=True)
    required_cols = ['Open', 'High', 'Low', 'Close']
    if not all(col in rates_df.columns for col in required_cols):
        raise ValueError(f"Colonnes manquantes. Reçu: {rates_df.columns.tolist()}")
    rates_df = rates_df[required_cols]

    print("Calcul de la SMA(20)...")
    rates_df.sort_index(ascending=True, inplace=True) # Trier avant indicateurs
    rates_df['SMA20'] = rates_df['Close'].rolling(window=SMA_PERIOD).mean()
    rates_df.dropna(subset=['SMA20'], inplace=True) # Supprimer NaN SMA
    print(f"{len(rates_df)} barres après calcul SMA.")

    if rates_df.empty:
        raise ValueError("DataFrame vide après calcul SMA.")

    actual_start_time = rates_df.index.min()
    actual_end_time = rates_df.index.max()
    print(f"Données prêtes pour la période UTC: {actual_start_time} à {actual_end_time}")
    # print("Aperçu des dernières données:") # Décommenter pour debug
    # print(rates_df.tail())

except Exception as e:
    print(f"ERREUR lors de la récupération ou du traitement des données: {e}")
    if 'response_data_str' in locals() and response_data_str:
         print("Réponse brute reçue (début):", response_data_str[:500])
    import traceback
    traceback.print_exc()
    exit() # Quitter si les données ne sont pas chargées/préparées correctement

# --- Calcul et Affichage ZigZag / Zones d'Intérêt ---
print("\n--- Calcul et Affichage ZigZag / Zones d'Intérêt ---")
zigzag_pivots = [] # Initialiser en cas d'erreur plus bas
try:
    print(f"Calcul des pivots ZigZag (length={ZIGZAG_LENGTH}) sur {len(rates_df)} barres...")
    zigzag_pivots = calculate_zigzag_pivots(rates_df, length=ZIGZAG_LENGTH)
    print("Calcul ZigZag terminé.")

    print("\nPivots ZigZag détectés et Zones d'Intérêt potentielles:")
    if not zigzag_pivots:
        print("Aucun pivot ZigZag détecté.")
    else:
        interest_zones = []
        for i in range(len(zigzag_pivots)):
            pivot = zigzag_pivots[i]
            pivot_time_utc = pivot['index']
            print(f"- Pivot: {pivot_time_utc}, Price: {pivot['price']:.5f}, Type: {pivot['type']}, Status: {pivot['status']}")

            # Appel de find_interest_zone
            if pivot['index'] in rates_df.index:
                 # Appeler seulement si HH ou LL (selon la logique définie)
                 if 'status' in pivot and (pivot['status'] == 'HH' or pivot['status'] == 'LL'):
                     try:
                         zone_info = find_interest_zone(rates_df, zigzag_pivots, i)
                         if zone_info:
                             print(f"    ZONE D'INTÉRÊT DÉFINIE ({zone_info['direction']}):")
                             print(f"      Début : {zone_info['start_price']:.5f} (High/Low de bougie {zone_info['breakout_candle_index']})")
                             print(f"      Fin   : {zone_info['end_price']:.5f} (Prix pivot précédent {zone_info['preceding_pivot_index']})")
                             interest_zones.append(zone_info)
                     except Exception as zie: # Erreur spécifique à find_interest_zone
                          print(f"    ERREUR pendant find_interest_zone pour pivot {pivot_time_utc}: {zie}")
            else:
                print(f"    (Pivot {pivot_time_utc} non trouvé dans DF post-SMA)")

except Exception as e:
    print(f"ERREUR pendant le calcul ZigZag ou Zone Intérêt: {e}")
    import traceback
    traceback.print_exc()

# --- Instructions Finales ---
print("\n--- ACTION REQUISE ---")
# ... (instructions inchangées) ...
print(f"1. L'EA doit être actif.")
print(f"2. Ouvrez TradingView ({SYMBOL} M1).")
print(f"3. Comparez les Pivots ET les Zones d'Intérêt affichées ci-dessus avec votre analyse manuelle.")
print(f"   Période UTC approx: {actual_start_time.strftime('%Y-%m-%d %H:%M:%S') if actual_start_time else 'N/A'} à {actual_end_time.strftime('%Y-%m-%d %H:%M:%S') if actual_end_time else 'N/A'}")
print(f"4. Vérifiez si la bougie de cassure et les limites (Début/Fin) de la zone correspondent à votre stratégie.")
print(f"5. Faites-moi part des résultats.")
print("----------------------")