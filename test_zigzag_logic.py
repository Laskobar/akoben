# ----- START OF FILE test_zigzag_logic.py (Updated) -----
import pandas as pd
import numpy as np
# import json # Plus utilisé ici directement
import time
import os
from datetime import datetime, timedelta, timezone
# import uuid # Plus nécessaire pour ce mode
import pandas_ta as ta
import math # Importé car utilisé par calculate_position_size

# --- Importer les fonctions ---
try:
    from src.tools.signal_utils import (
        calculate_zigzag_pivots,
        find_interest_zone,
        check_divergence_in_zone,
        detect_engulfing_pattern, # <== NOUVEAU
        calculate_stop_loss,      # <== NOUVEAU
        calculate_take_profit_v1, # <== NOUVEAU
        calculate_position_size,  # <== NOUVEAU
        SYMBOL_INFO_US30_EUR_SIMULATED # <== NOUVEAU (Récupère les infos simulées)
    )
    print("Fonctions de signal_utils importées (incluant exécution).")
except ImportError as e:
    print(f"ERREUR: Import fonctions signal_utils: {e}")
    exit()

# --- Configuration ---
CSV_DATA_PATH = os.path.join(os.path.dirname(__file__), "US30.cash_M1_202503281400_202503281800.csv") # <<< Vérifie que c'est ton nom de fichier
print(f"Utilisation du fichier CSV local: {CSV_DATA_PATH}")

# --- Paramètres Stratégie ---
SYMBOL = "US30.cash"
TIMEFRAME_STR = "M1"
ZIGZAG_LENGTH = 9
SMA_PERIOD = 20
RSI_PERIOD = 14
SL_BUFFER_POINTS = 5.0  # Buffer pour le Stop Loss (ex: 5 points pour US30)
RISK_PERCENTAGE = 1.0   # Risque par trade en %
SIMULATED_BALANCE = 10000.0 # Solde de compte simulé pour le test

# --- Variables Globales ---
rates_df = pd.DataFrame()
actual_start_time = None
actual_end_time = None
zigzag_pivots = []
interest_zones = {}
data_loaded_successfully = False

# --- Chargement et Traitement des Données depuis CSV ---
print("\n--- Chargement et Traitement des Données depuis CSV ---")
try:
    if not os.path.exists(CSV_DATA_PATH):
        raise FileNotFoundError(f"Le fichier CSV spécifié n'a pas été trouvé: {CSV_DATA_PATH}")

    print(f"Chargement depuis {CSV_DATA_PATH}...")
    rates_df = pd.read_csv(
        CSV_DATA_PATH, sep='\t',
        parse_dates={'time': ['<DATE>', '<TIME>']}, index_col='time',
        usecols=['<DATE>', '<TIME>', '<OPEN>', '<HIGH>', '<LOW>', '<CLOSE>']
    )
    rates_df.rename(columns={'<OPEN>': 'Open', '<HIGH>': 'High', '<LOW>': 'Low', '<CLOSE>': 'Close'}, inplace=True)

    try:
        # Tentative de localisation en UTC+1 (Europe/Brussels ou similaire, ajuster si besoin) puis conversion UTC
        rates_df.index = rates_df.index.tz_localize('Etc/GMT-1').tz_convert('UTC')
        print("Index Datetime localisé (supposé UTC+1) puis converti en UTC.")
    except Exception as tz_ex:
        print(f"Avertissement localisation/conversion Timezone: {tz_ex}. Tentative avec UTC directement.")
        try:
            rates_df.index = rates_df.index.tz_localize('UTC')
        except TypeError: # Si déjà tz-aware
             if rates_df.index.tz is not None: rates_df.index = rates_df.index.tz_convert('UTC')

    print(f"{len(rates_df)} barres chargées.")
    print("Calcul indicateurs (SMA, RSI)...")
    rates_df.sort_index(ascending=True, inplace=True)
    rates_df['SMA20'] = rates_df['Close'].rolling(window=SMA_PERIOD).mean()
    rates_df.ta.rsi(length=RSI_PERIOD, append=True)
    # Renommer explicitement la colonne RSI pour éviter les problèmes si le nom par défaut change
    rsi_col_name = f'RSI_{RSI_PERIOD}'
    if rsi_col_name not in rates_df.columns and 'RSI_14' in rates_df.columns: # Fallback si pandas-ta utilise un nom légèrement différent
        rsi_col_name = 'RSI_14'
    if rsi_col_name not in rates_df.columns:
        raise ValueError(f"Colonne RSI (attendu {f'RSI_{RSI_PERIOD}'} ou 'RSI_14') non trouvée après calcul.")

    rates_df.dropna(subset=['SMA20', rsi_col_name], inplace=True)
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
        # for p in zigzag_pivots: print(p) # Décommenter pour voir tous les pivots

        print("\nAnalyse pivots pour Zones d'Intérêt (HH/LL):")
        if not zigzag_pivots: print("Aucun pivot.")
        else:
            # --- MODIFIÉ: Recalculer les zones à chaque fois pour le test ---
            # Dans un système live, on mettrait à jour les zones actives seulement
            all_zones_found = [] # Pour garder une trace de toutes les zones détectées
            for i in range(1, len(zigzag_pivots)): # Commencer à 1 car on a besoin du pivot précédent
                pivot = zigzag_pivots[i]
                # On s'intéresse aux HH et LL pour définir les zones selon la strat V1
                if 'status' in pivot and (pivot['status'] == 'HH' or pivot['status'] == 'LL'):
                    print(f"- Pivot {i}: {pivot['index']}, P={pivot['price']:.2f}, T={pivot['type']}, S={pivot['status']}")
                    if pivot['index'] in rates_df.index:
                        try:
                            zone_info = find_interest_zone(rates_df, zigzag_pivots, i)
                            if zone_info:
                                zone_lower = min(zone_info['start_price'], zone_info['end_price'])
                                zone_upper = max(zone_info['start_price'], zone_info['end_price'])
                                print(f"    >>> ZONE TROUVEE ({zone_info['direction']}): [{zone_lower:.2f} - {zone_upper:.2f}] (Bougie Cassure: {zone_info['breakout_candle_index']}, Pivot Préc: {zone_info['preceding_pivot_index']})")
                                all_zones_found.append(zone_info)
                                # Pour la simulation, on garde la DERNIERE zone de chaque type
                                interest_zones[zone_info['direction']] = zone_info
                        except Exception as zie: print(f"    ERREUR find_interest_zone: {zie}")
                    else: print(f"    (Pivot {pivot['index']} hors DF post-indicateurs)")
                # else: # Afficher aussi les autres pivots si besoin de débugger
                #     print(f"- Pivot {i}: {pivot['index']}, P={pivot['price']:.2f}, T={pivot['type']}, S={pivot['status']}")

    except Exception as e: print(f"ERREUR calcul ZigZag/Zone: {e}"); import traceback; traceback.print_exc()

    # <<< ================= SECTIONS MODIFIÉES / NOUVELLES ================= >>>
    print("\n--- Simulation Détection Complète (Divergence + Trigger + Ordre) ---")
    potential_trades = [] # Pour stocker les trades simulés
    # Utiliser une fenêtre de vérification raisonnable (ex: les 100 dernières bougies)
    check_window = len(rates_df) # Tester TOUTES les bougies disponibles
    if check_window > 0 and zigzag_pivots:
        print(f"Vérification des {check_window} dernières bougies disponibles...")
        check_df = rates_df.iloc[-check_window:]

        # Récupérer les dernières zones actives (bullish/bearish) calculées juste avant
        active_bull_zone = interest_zones.get('bullish')
        active_bear_zone = interest_zones.get('bearish')

        # Afficher les zones actives pour la simulation
        if active_bull_zone:
             zone_lower = min(active_bull_zone['start_price'], active_bull_zone['end_price'])
             zone_upper = max(active_bull_zone['start_price'], active_bull_zone['end_price'])
             print(f"Zone Bullish Active pour Simu: [{zone_lower:.2f} - {zone_upper:.2f}] (Basée sur pivot: {active_bull_zone['preceding_pivot_index']})")
        else: print("Pas de Zone Bullish active pour la simulation.")

        if active_bear_zone:
             zone_lower = min(active_bear_zone['start_price'], active_bear_zone['end_price'])
             zone_upper = max(active_bear_zone['start_price'], active_bear_zone['end_price'])
             print(f"Zone Bearish Active pour Simu: [{zone_lower:.2f} - {zone_upper:.2f}] (Basée sur pivot: {active_bear_zone['preceding_pivot_index']})")
        else: print("Pas de Zone Bearish active pour la simulation.")

        # Préparer les infos des pivots pour la vérification de divergence
        last_bull_pivot = None; rsi_at_bull_pivot = np.nan
        if active_bull_zone:
            pivot_idx = active_bull_zone['preceding_pivot_index']
            last_bull_pivot = next((p for p in reversed(zigzag_pivots) if p['index'] == pivot_idx), None)
            if last_bull_pivot and pivot_idx in rates_df.index: rsi_at_bull_pivot = rates_df.loc[pivot_idx, rsi_col_name]

        last_bear_pivot = None; rsi_at_bear_pivot = np.nan
        if active_bear_zone:
            pivot_idx = active_bear_zone['preceding_pivot_index']
            last_bear_pivot = next((p for p in reversed(zigzag_pivots) if p['index'] == pivot_idx), None)
            if last_bear_pivot and pivot_idx in rates_df.index: rsi_at_bear_pivot = rates_df.loc[pivot_idx, rsi_col_name]

        # --- Boucle de simulation sur les dernières bougies ---
        for idx, row in check_df.iterrows():
            current_low = row['Low']; current_high = row['High']; current_close = row['Close']
            current_rsi = row[rsi_col_name]
            if pd.isna(current_rsi): continue # Ignorer si RSI non calculable

            # print(f"\nBougie {idx}: L={current_low:.2f}, H={current_high:.2f}, C={current_close:.2f}, RSI={current_rsi:.2f}") # Debug verbeux

            # 1. Vérifier Divergence dans Zone Bullish
            divergence_bull_type = None
            if active_bull_zone and last_bull_pivot and not pd.isna(rsi_at_bull_pivot):
                divergence_bull_type = check_divergence_in_zone(current_low, current_high, current_rsi, active_bull_zone, last_bull_pivot, rsi_at_bull_pivot)
                if divergence_bull_type:
                    # print(f"  -> Div Bullish Potentielle: {divergence_bull_type} à {idx}") # Debug
                    # 2. Vérifier Trigger Englobant Haussier
                    is_engulfing = detect_engulfing_pattern(rates_df, idx, 'bullish')
                    if is_engulfing:
                        print(f"\n!!! ===> SETUP ACHAT DETECTE à {idx} <=== !!!")
                        print(f"      Type: {divergence_bull_type}, Trigger: Englobante Haussière")
                        # 3. Calculer SL, TP, Taille
                        entry_price = current_close # Entrée à la clôture de la bougie d'englobante
                        print(f"      Entrée Estimée: {entry_price:.2f}")

                        sl = calculate_stop_loss(rates_df, idx, 'bullish', buffer_points=SL_BUFFER_POINTS)
                        if sl: print(f"      Stop Loss: {sl:.2f}")
                        else: print("      Stop Loss: ERREUR CALCUL")

                        tp = calculate_take_profit_v1(zigzag_pivots, idx, 'bullish', divergence_bull_type, active_bull_zone, rates_df)
                        if tp: print(f"      Take Profit: {tp:.2f}")
                        else: print("      Take Profit: ERREUR CALCUL")

                        if sl and tp and sl != entry_price:
                            # Utiliser les infos SYMBOLE SIMULÉES
                            size = calculate_position_size(SIMULATED_BALANCE, RISK_PERCENTAGE, sl, entry_price, SYMBOL_INFO_US30_EUR_SIMULATED)
                            if size: print(f"      Taille Position: {size:.2f} lots (pour {SIMULATED_BALANCE} EUR @ {RISK_PERCENTAGE}%)")
                            else: print("      Taille Position: ERREUR CALCUL / Risque trop élevé")
                        else:
                            print("      Taille Position: Non calculée (Erreur SL/TP ou SL=Entry)")

                        potential_trades.append({'time': idx, 'direction': 'BUY', 'type': divergence_bull_type, 'entry': entry_price, 'sl': sl, 'tp': tp, 'size': size if sl and tp else None})
                        # Pour éviter de trader plusieurs fois sur la même zone, on pourrait la désactiver ici pour le test
                        # active_bull_zone = None

            # 1. Vérifier Divergence dans Zone Bearish
            divergence_bear_type = None
            if active_bear_zone and last_bear_pivot and not pd.isna(rsi_at_bear_pivot):
                 divergence_bear_type = check_divergence_in_zone(current_low, current_high, current_rsi, active_bear_zone, last_bear_pivot, rsi_at_bear_pivot)
                 if divergence_bear_type:
                    # print(f"  -> Div Bearish Potentielle: {divergence_bear_type} à {idx}") # Debug
                    # 2. Vérifier Trigger Englobant Baissier
                    is_engulfing = detect_engulfing_pattern(rates_df, idx, 'bearish')
                    if is_engulfing:
                        print(f"\n!!! ===> SETUP VENTE DETECTE à {idx} <=== !!!")
                        print(f"      Type: {divergence_bear_type}, Trigger: Englobante Baissière")
                        # 3. Calculer SL, TP, Taille
                        entry_price = current_close
                        print(f"      Entrée Estimée: {entry_price:.2f}")

                        sl = calculate_stop_loss(rates_df, idx, 'bearish', buffer_points=SL_BUFFER_POINTS)
                        if sl: print(f"      Stop Loss: {sl:.2f}")
                        else: print("      Stop Loss: ERREUR CALCUL")

                        tp = calculate_take_profit_v1(zigzag_pivots, idx, 'bearish', divergence_bear_type, active_bear_zone, rates_df)
                        if tp: print(f"      Take Profit: {tp:.2f}")
                        else: print("      Take Profit: ERREUR CALCUL")

                        if sl and tp and sl != entry_price:
                             # Utiliser les infos SYMBOLE SIMULÉES
                            size = calculate_position_size(SIMULATED_BALANCE, RISK_PERCENTAGE, sl, entry_price, SYMBOL_INFO_US30_EUR_SIMULATED)
                            if size: print(f"      Taille Position: {size:.2f} lots (pour {SIMULATED_BALANCE} EUR @ {RISK_PERCENTAGE}%)")
                            else: print("      Taille Position: ERREUR CALCUL / Risque trop élevé")
                        else:
                             print("      Taille Position: Non calculée (Erreur SL/TP ou SL=Entry)")

                        potential_trades.append({'time': idx, 'direction': 'SELL', 'type': divergence_bear_type, 'entry': entry_price, 'sl': sl, 'tp': tp, 'size': size if sl and tp else None})
                        # Désactiver la zone pour éviter répétition dans le test
                        # active_bear_zone = None

    else: print("Pas assez de données/pivots ou zones pour la simulation détaillée.")
    # <<< ================= FIN SECTIONS MODIFIÉES / NOUVELLES ================= >>>

else: # Si échec chargement CSV
    print("\nImpossible de charger les données depuis le fichier CSV.")

# --- Instructions Finales ---
print("\n--- FIN DU TEST OFFLINE COMPLET ---")
print(f"1. Analysez la sortie ci-dessus pour les 'SETUP ACHAT/VENTE DETECTE'.")
print(f"2. Vérifiez si les calculs SL/TP/Taille semblent logiques pour ces setups.")
print(f"3. Rappel : La Taille Position est basée sur les infos symbole SIMULÉES : {SYMBOL_INFO_US30_EUR_SIMULATED}")
print(f"   -> Lundi: Récupérer les vraies valeurs de MT5 et mettre à jour.")
print(f"4. Ce test utilise les données du fichier: {CSV_DATA_PATH}")
print(f"   Période UTC: {actual_start_time.strftime('%Y-%m-%d %H:%M:%S') if actual_start_time else 'N/A'} à {actual_end_time.strftime('%Y-%m-%d %H:%M:%S') if actual_end_time else 'N/A'}")
print("-----------------------------")

# ----- END OF FILE test_zigzag_logic.py (Updated) -----