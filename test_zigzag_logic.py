# ----- START OF FILE test_zigzag_logic.py -----
import pandas as pd
import numpy as np
import json
import time
import os
from datetime import datetime, timedelta, timezone
# import uuid # Plus nécessaire pour ce mode
import pandas_ta as ta

# --- Importer les fonctions ---
try:
    from src.tools.signal_utils import calculate_zigzag_pivots, find_interest_zone, check_divergence_in_zone
    print("Fonctions importées.")
except ImportError:
    print("ERREUR: Import fonctions signal_utils.")
    exit()

# --- Configuration ---
# <<< MODIFIÉ : Chemin vers VOTRE fichier CSV exporté >>>
CSV_DATA_PATH = os.path.join(os.path.dirname(__file__), "US30.cash_M1_202503281400_202503281800.csv")

print(f"Utilisation du fichier CSV local: {CSV_DATA_PATH}")

# --- Paramètres ---
SYMBOL = "US30.cash" # Gardé pour information
TIMEFRAME_STR = "M1" # Gardé pour information
ZIGZAG_LENGTH = 9
SMA_PERIOD = 20
RSI_PERIOD = 14

# --- Variables ---
rates_df = pd.DataFrame()
actual_start_time = None
actual_end_time = None
zigzag_pivots = []
interest_zones = {}
data_loaded_successfully = False # Important: sera mis à True si le chargement CSV réussit

# --- Chargement et Traitement des Données depuis CSV ---
print("\n--- Chargement et Traitement des Données depuis CSV ---")
try:
    if not os.path.exists(CSV_DATA_PATH):
        raise FileNotFoundError(f"Le fichier CSV spécifié n'a pas été trouvé: {CSV_DATA_PATH}")

    print(f"Chargement depuis {CSV_DATA_PATH}...")
    # Lecture du CSV exporté par MT5 (séparateur tabulation, noms de colonnes spécifiques)
    rates_df = pd.read_csv(
        CSV_DATA_PATH,
        sep='\t', # Séparateur tabulation
        parse_dates={'time': ['<DATE>', '<TIME>']}, # Combine DATE et TIME en une colonne 'time'
        index_col='time', # Utiliser la colonne 'time' comme index
        usecols=['<DATE>', '<TIME>', '<OPEN>', '<HIGH>', '<LOW>', '<CLOSE>'] # Ne lire que les colonnes utiles
    )

    # Renommer les colonnes MT5 standard en noms attendus (casse correcte)
    rates_df.rename(columns={
        '<OPEN>': 'Open',
        '<HIGH>': 'High',
        '<LOW>': 'Low',
        '<CLOSE>': 'Close'
    }, inplace=True)

    # Assurer que l'index est bien DatetimeIndex UTC
    # L'export MT5 est souvent dans le fuseau horaire du PC/serveur.
    # Supposons que c'était UTC+1 (Belgique) comme dans vos images?
    # Si oui, on localise puis on convertit en UTC. Sinon, ajustez la timezone initiale.
    try:
        # Exemple: si l'export était en Europe/Brussels (UTC+1 sans DST ou UTC+2 avec DST)
        # Mieux : si l'heure dans le fichier est déjà UTC+1 (comme indiqué en haut de vos images TV)
        # On localise en UTC+1 puis convertit en UTC pour être cohérent
        rates_df.index = rates_df.index.tz_localize('Etc/GMT-1').tz_convert('UTC')
        print("Index Datetime localisé en UTC+1 puis converti en UTC.")
    except TypeError: # Si déjà tz-aware (peu probable avec read_csv comme ça)
         if rates_df.index.tz is not None:
             print(f"Avertissement: L'index est déjà tz-aware ({rates_df.index.tz}), conversion en UTC.")
             rates_df.index = rates_df.index.tz_convert('UTC')
         else: # Si aucune timezone, on suppose UTC (moins précis)
             print("Avertissement: Impossible de déterminer le fuseau horaire original, en supposant UTC.")
             rates_df.index = rates_df.index.tz_localize('UTC')


    print(f"{len(rates_df)} barres chargées depuis CSV.")

    print("Calcul indicateurs (SMA, RSI)...")
    rates_df.sort_index(ascending=True, inplace=True) # Assurer le tri
    rates_df['SMA20'] = rates_df['Close'].rolling(window=SMA_PERIOD).mean()
    rates_df.ta.rsi(length=RSI_PERIOD, append=True)
    rates_df.dropna(subset=['SMA20', f'RSI_{RSI_PERIOD}'], inplace=True)
    print(f"{len(rates_df)} barres après calcul/dropna.")

    if rates_df.empty: raise ValueError("DataFrame vide post-indicateurs.")
    actual_start_time = rates_df.index.min()
    actual_end_time = rates_df.index.max()
    print(f"Données prêtes pour UTC: {actual_start_time} à {actual_end_time}")
    data_loaded_successfully = True

except Exception as e:
    print(f"ERREUR lors du chargement/traitement du CSV: {e}")
    import traceback
    traceback.print_exc()

# --- Calculs et Simulation (si les données sont chargées) ---
if data_loaded_successfully:
    print("\n--- Calcul ZigZag et Zones ---")
    try:
        print(f"Calcul pivots ZigZag (length={ZIGZAG_LENGTH})...")
        zigzag_pivots = calculate_zigzag_pivots(rates_df, length=ZIGZAG_LENGTH)
        print(f"Calcul ZigZag terminé. {len(zigzag_pivots)} pivots trouvés.")

        print("\nAnalyse pivots pour Zones d'Intérêt (HH/LL):")
        if not zigzag_pivots: print("Aucun pivot.")
        else:
            interest_zones = {}
            for i in range(len(zigzag_pivots)):
                pivot = zigzag_pivots[i]
                print(f"- Pivot {i}: {pivot['index']}, P={pivot['price']:.5f}, T={pivot['type']}, S={pivot['status']}")
                if pivot['index'] in rates_df.index:
                     if 'status' in pivot and (pivot['status'] == 'HH' or pivot['status'] == 'LL'):
                         try:
                             zone_info = find_interest_zone(rates_df, zigzag_pivots, i)
                             if zone_info:
                                 # Ajuster l'affichage de la zone pour être cohérent (min -> max)
                                 zone_lower = min(zone_info['start_price'], zone_info['end_price'])
                                 zone_upper = max(zone_info['start_price'], zone_info['end_price'])
                                 print(f"    >>> ZONE ({zone_info['direction']}): [{zone_lower:.5f} - {zone_upper:.5f}] (Bougie: {zone_info['breakout_candle_index']}, Pivot Préc: {zone_info['preceding_pivot_index']})")
                                 interest_zones[zone_info['direction']] = zone_info
                         except Exception as zie: print(f"    ERREUR find_interest_zone: {zie}")
                else: print(f"    (Pivot hors DF post-indi)")
    except Exception as e: print(f"ERREUR calcul ZigZag/Zone: {e}"); import traceback; traceback.print_exc()

    print("\n--- Simulation Divergence ---")
    last_n_candles_to_check = 60 # Vérifier plus de bougies pour ce test offline
    if len(rates_df) > last_n_candles_to_check and zigzag_pivots:
        print(f"Vérification dernières {last_n_candles_to_check} bougies...")
        check_df = rates_df.iloc[-last_n_candles_to_check:]
        active_bull_zone = interest_zones.get('bullish'); active_bear_zone = interest_zones.get('bearish')
        last_bull_pivot = None; rsi_at_bull_pivot = np.nan
        if active_bull_zone:
            pivot_idx = active_bull_zone['preceding_pivot_index']
            last_bull_pivot = next((p for p in reversed(zigzag_pivots) if p['index'] == pivot_idx), None)
            if last_bull_pivot and pivot_idx in rates_df.index: rsi_at_bull_pivot = rates_df.loc[pivot_idx, f'RSI_{RSI_PERIOD}']
            zone_lower = min(active_bull_zone['start_price'], active_bull_zone['end_price'])
            zone_upper = max(active_bull_zone['start_price'], active_bull_zone['end_price'])
            print(f"Zone Bullish active: [{zone_lower:.5f} - {zone_upper:.5f}] (vs Pivot {pivot_idx} / RSI {rsi_at_bull_pivot:.2f})")

        last_bear_pivot = None; rsi_at_bear_pivot = np.nan
        if active_bear_zone:
            pivot_idx = active_bear_zone['preceding_pivot_index']
            last_bear_pivot = next((p for p in reversed(zigzag_pivots) if p['index'] == pivot_idx), None)
            if last_bear_pivot and pivot_idx in rates_df.index: rsi_at_bear_pivot = rates_df.loc[pivot_idx, f'RSI_{RSI_PERIOD}']
            zone_lower = min(active_bear_zone['start_price'], active_bear_zone['end_price'])
            zone_upper = max(active_bear_zone['start_price'], active_bear_zone['end_price'])
            print(f"Zone Bearish active: [{zone_lower:.5f} - {zone_upper:.5f}] (vs Pivot {pivot_idx} / RSI {rsi_at_bear_pivot:.2f})")

        for idx, row in check_df.iterrows():
            current_low = row['Low']; current_high = row['High']; current_rsi = row[f'RSI_{RSI_PERIOD}']
            print(f"\nBougie {idx}: L={current_low:.5f}, H={current_high:.5f}, RSI={current_rsi:.2f}")
            # Vérif Bullish
            if active_bull_zone and last_bull_pivot:
                divergence_bull = check_divergence_in_zone(current_low, current_high, current_rsi, active_bull_zone, last_bull_pivot, rsi_at_bull_pivot)
                if divergence_bull: print(f"  >>> SIGNAL ACHAT POTENTIEL <<< Div: {divergence_bull}")
            # Vérif Bearish
            if active_bear_zone and last_bear_pivot:
                 divergence_bear = check_divergence_in_zone(current_low, current_high, current_rsi, active_bear_zone, last_bear_pivot, rsi_at_bear_pivot)
                 if divergence_bear: print(f"  >>> SIGNAL VENTE POTENTIEL <<< Div: {divergence_bear}")
    else: print("Pas assez données/pivots pour simulation.")

else: # Si échec chargement CSV
    print("\nImpossible de charger les données depuis le fichier CSV.")

# --- Instructions Finales ---
print("\n--- FIN DU TEST OFFLINE ---")
print(f"1. Analysez la sortie ci-dessus.")
print(f"2. Vérifiez les Pivots, Zones d'Intérêt et Signaux Potentiels détectés.")
print(f"3. Comparez avec votre analyse manuelle pour la période UTC:")
print(f"   {actual_start_time.strftime('%Y-%m-%d %H:%M:%S') if actual_start_time else 'N/A'} à {actual_end_time.strftime('%Y-%m-%d %H:%M:%S') if actual_end_time else 'N/A'}")
print(f"4. Ce test utilise les données du fichier: {CSV_DATA_PATH}")
print("-----------------------------")
# ----- END OF FILE test_zigzag_logic.py -----