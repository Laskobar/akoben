# ----- START OF FILE test_zigzag_logic.py -----
import pandas as pd
import numpy as np
import json
import time
import os
from datetime import datetime, timedelta, timezone
import uuid # Pour générer des ID de requêtes uniques
import pandas_ta as ta # Import pour le RSI

# --- Importer les fonctions depuis signal_utils ---
try:
    # Assurez-vous que signal_utils.py est dans le bon dossier (src/tools/)
    from src.tools.signal_utils import calculate_zigzag_pivots, find_interest_zone, check_divergence_in_zone
    print("Fonctions calculate_zigzag_pivots, find_interest_zone, et check_divergence_in_zone importées.")
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

# Paramètres
SYMBOL = "US30.cash"
TIMEFRAME_STR = "M1"
ZIGZAG_LENGTH = 9
SMA_PERIOD = 20
RSI_PERIOD = 14
RESPONSE_TIMEOUT_SECONDS = 10
RESPONSE_POLL_INTERVAL = 0.1
# Demander assez de données pour SMA, RSI, et Zigzag
data_count_request = 300 + max(SMA_PERIOD, RSI_PERIOD, ZIGZAG_LENGTH)
print(f"\nDemande des {data_count_request} dernières bougies M1 pour {SYMBOL}")

# --- Fonctions de Communication Fichiers ---
# (Les fonctions write_request, clear_request_file, read_response, send_command_and_wait
#  restent les mêmes)
def write_request(command: str, request_id: str) -> bool:
    request_content = f"ID:{request_id}|{command}"
    try:
        with open(REQUEST_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(request_content)
        # print(f"  Requête écrite ({request_id}): {command}") # Décommenter pour debug détaillé
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

# --- Initialisation ---
rates_df = pd.DataFrame()
actual_start_time = None
actual_end_time = None
zigzag_pivots = []
interest_zones = {} # Stocker les zones actives par direction

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
    if not data_list: raise ValueError("Liste de données JSON vide.")
    print(f"{len(data_list)} barres reçues.")

    rates_df = pd.DataFrame(data_list)
    rates_df['time'] = pd.to_datetime(rates_df['time'], unit='s', utc=True)
    rates_df.set_index('time', inplace=True)
    rates_df.rename(columns={'high': 'High', 'low': 'Low', 'close': 'Close', 'open': 'Open'}, inplace=True)
    required_cols = ['Open', 'High', 'Low', 'Close']
    if not all(col in rates_df.columns for col in required_cols):
        raise ValueError(f"Colonnes manquantes. Reçu: {rates_df.columns.tolist()}")
    rates_df = rates_df[required_cols]

    print("Calcul des indicateurs (SMA, RSI)...")
    rates_df.sort_index(ascending=True, inplace=True)
    rates_df['SMA20'] = rates_df['Close'].rolling(window=SMA_PERIOD).mean()
    rates_df.ta.rsi(length=RSI_PERIOD, append=True) # Ajoute colonne 'RSI_14'
    rates_df.dropna(subset=['SMA20', f'RSI_{RSI_PERIOD}'], inplace=True)
    print(f"{len(rates_df)} barres après calcul indicateurs et dropna.")

    if rates_df.empty: raise ValueError("DataFrame vide après calcul indicateurs.")
    actual_start_time = rates_df.index.min()
    actual_end_time = rates_df.index.max()
    print(f"Données prêtes pour UTC: {actual_start_time} à {actual_end_time}")

except Exception as e:
    print(f"ERREUR lors de la récupération/traitement des données: {e}")
    if 'response_data_str' in locals() and response_data_str:
         print("Réponse brute reçue (début):", response_data_str[:500])
    import traceback
    traceback.print_exc()
    exit()

# --- Calcul ZigZag et Zones ---
print("\n--- Calcul ZigZag et Zones ---")
try:
    print(f"Calcul pivots ZigZag (length={ZIGZAG_LENGTH})...")
    zigzag_pivots = calculate_zigzag_pivots(rates_df, length=ZIGZAG_LENGTH)
    print(f"Calcul ZigZag terminé. {len(zigzag_pivots)} pivots trouvés.")

    print("\nAnalyse des pivots pour définir les Zones d'Intérêt:")
    if not zigzag_pivots:
        print("Aucun pivot ZigZag détecté.")
    else:
        # Afficher les pivots et chercher les zones associées
        for i in range(len(zigzag_pivots)):
            pivot = zigzag_pivots[i]
            print(f"- Pivot {i}: {pivot['index']}, Price: {pivot['price']:.5f}, Type: {pivot['type']}, Status: {pivot['status']}")

            if pivot['index'] in rates_df.index:
                 if 'status' in pivot and (pivot['status'] == 'HH' or pivot['status'] == 'LL'):
                     try:
                         zone_info = find_interest_zone(rates_df, zigzag_pivots, i)
                         if zone_info:
                             print(f"    ZONE D'INTÉRÊT DÉFINIE ({zone_info['direction']}):")
                             print(f"      Début: {zone_info['start_price']:.5f} (Bougie {zone_info['breakout_candle_index']})")
                             print(f"      Fin  : {zone_info['end_price']:.5f} (Pivot {zone_info['preceding_pivot_index']})")
                             # Stocker la dernière zone trouvée pour chaque direction
                             interest_zones[zone_info['direction']] = zone_info
                     except Exception as zie:
                          print(f"    ERREUR find_interest_zone pour pivot {i}: {zie}")
            else:
                print(f"    (Pivot {pivot['index']} hors DF post-indicateurs)")

except Exception as e:
    print(f"ERREUR calcul ZigZag/Zone: {e}")
    import traceback
    traceback.print_exc()

# --- Simulation : Vérification Divergence dans Zone (sur les dernières bougies) ---
print("\n--- Simulation : Vérification Divergence dans Zone ---")
last_n_candles_to_check = 30 # Nombre de dernières bougies à vérifier
if not rates_df.empty and len(rates_df) > last_n_candles_to_check and zigzag_pivots:
    print(f"Vérification des {last_n_candles_to_check} dernières bougies pour signaux...")
    check_df = rates_df.iloc[-last_n_candles_to_check:] # Sélectionne les N dernières lignes

    # Récupérer la dernière zone bullish et bearish active (si elles existent)
    active_bull_zone = interest_zones.get('bullish')
    active_bear_zone = interest_zones.get('bearish')

    # Trouver le pivot correspondant à la fin de chaque zone active
    last_bull_pivot = None
    rsi_at_bull_pivot = np.nan
    if active_bull_zone:
        pivot_idx = active_bull_zone['preceding_pivot_index']
        # Trouver le dict pivot correspondant dans la liste zigzag_pivots
        last_bull_pivot = next((p for p in reversed(zigzag_pivots) if p['index'] == pivot_idx), None)
        if last_bull_pivot and pivot_idx in rates_df.index:
             rsi_at_bull_pivot = rates_df.loc[pivot_idx, f'RSI_{RSI_PERIOD}']

    last_bear_pivot = None
    rsi_at_bear_pivot = np.nan
    if active_bear_zone:
        pivot_idx = active_bear_zone['preceding_pivot_index']
        last_bear_pivot = next((p for p in reversed(zigzag_pivots) if p['index'] == pivot_idx), None)
        if last_bear_pivot and pivot_idx in rates_df.index:
            rsi_at_bear_pivot = rates_df.loc[pivot_idx, f'RSI_{RSI_PERIOD}']

    if active_bull_zone: print(f"Zone Bullish active: [{active_bull_zone['end_price']:.5f} - {active_bull_zone['start_price']:.5f}] (compare avec pivot {active_bull_zone['preceding_pivot_index']} / RSI {rsi_at_bull_pivot:.2f})")
    if active_bear_zone: print(f"Zone Bearish active: [{active_bear_zone['start_price']:.5f} - {active_bear_zone['end_price']:.5f}] (compare avec pivot {active_bear_zone['preceding_pivot_index']} / RSI {rsi_at_bear_pivot:.2f})")


    # Itérer sur les N dernières bougies
    for idx, row in check_df.iterrows():
        current_low = row['Low']
        current_high = row['High']
        current_rsi = row[f'RSI_{RSI_PERIOD}']

        print(f"\nBougie {idx}: L={current_low:.5f}, H={current_high:.5f}, RSI={current_rsi:.2f}")

        # Vérifier divergence dans zone Bullish
        if active_bull_zone and last_bull_pivot:
            divergence_bull = check_divergence_in_zone(
                current_low, current_high, current_rsi,
                active_bull_zone, last_bull_pivot, rsi_at_bull_pivot
            )
            if divergence_bull:
                print(f"  >>> SIGNAL POTENTIEL ACHAT <<< Divergence détectée: {divergence_bull}")
                # Ici, on ajouterait la vérification du trigger (Englobante)

        # Vérifier divergence dans zone Bearish
        if active_bear_zone and last_bear_pivot:
             divergence_bear = check_divergence_in_zone(
                current_low, current_high, current_rsi,
                active_bear_zone, last_bear_pivot, rsi_at_bear_pivot
             )
             if divergence_bear:
                 print(f"  >>> SIGNAL POTENTIEL VENTE <<< Divergence détectée: {divergence_bear}")
                 # Ici, on ajouterait la vérification du trigger (Englobante)

else:
    print("Pas assez de données ou de pivots pour la simulation de divergence.")


# --- Instructions Finales ---
print("\n--- ACTION REQUISE ---")
print(f"1. L'EA doit être actif.")
print(f"2. Ouvrez TradingView ({SYMBOL} M1).")
print(f"3. Analysez la sortie ci-dessus:")
print(f"   - Les Zones d'Intérêt semblent-elles correctes ?")
print(f"   - La simulation sur les dernières bougies détecte-t-elle des divergences ")
print(f"     aux moments où vous vous y attendriez (quand le prix revient dans la zone) ?")
print(f"   Période UTC approx des données: {actual_start_time.strftime('%Y-%m-%d %H:%M:%S') if actual_start_time else 'N/A'} à {actual_end_time.strftime('%Y-%m-%d %H:%M:%S') if actual_end_time else 'N/A'}")
print(f"4. Faites-moi part de vos observations.")
print("----------------------")
# ----- END OF FILE test_zigzag_logic.py -----