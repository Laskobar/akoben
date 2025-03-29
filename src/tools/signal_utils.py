# ----- START OF FILE src/tools/signal_utils.py -----
import pandas as pd
import numpy as np
import pandas_ta as ta # Assurez-vous que pandas-ta est installé (pip install pandas-ta)
import math

def calculate_zigzag_pivots(df_ohlc: pd.DataFrame, length: int = 9):
    """
    Réplique la logique d'un indicateur ZigZag basé sur les plus hauts/bas
    sur une période donnée, similaire au script PineScript fourni.

    Args:
        df_ohlc: DataFrame pandas avec au moins les colonnes 'High', 'Low', 'Close'.
                 L'index doit être DatetimeIndex, trié par ordre chronologique croissant.
        length: La période de recherche pour le ZigZag (équivalent zigzag_len).

    Returns:
        Une liste de dictionnaires, chaque dictionnaire représentant un pivot
        confirmé avec les clés: 'index', 'price', 'type' ('high' ou 'low'),
        et 'status' ('H', 'L', 'HH', 'HL', 'LH', 'LL', 'EH', 'EL').
        Retourne une liste vide si pas assez de données.
    """
    if len(df_ohlc) < length:
        return [] # Pas assez de données pour calculer

    # Assurer que le DataFrame est trié par date croissante
    df = df_ohlc.sort_index(ascending=True).copy()

    # --- Étape 1: Calculer les conditions de retournement potentiel ---
    # Note: .shift(1) pour comparer avec les N barres *précédentes*
    df['rolling_max'] = df['High'].rolling(length).max().shift(1)
    df['rolling_min'] = df['Low'].rolling(length).min().shift(1)

    df['potential_up_turn'] = df['Low'] <= df['rolling_min']
    df['potential_down_turn'] = df['High'] >= df['rolling_max']

    # --- Étape 2: Déterminer la tendance (state machine) ---
    trend = np.zeros(len(df), dtype=int)
    initial_trend_determined = False
    for i in range(length, len(df)):
         if not initial_trend_determined and i > 0:
             # Guess initial trend based on the first valid window
             if df['Close'].iloc[i-1] > df['Close'].iloc[i-length if i-length >= 0 else 0]:
                 trend[i-1] = 1 # Up
             else:
                 trend[i-1] = -1 # Down
             initial_trend_determined = True
             trend[:i-1] = trend[i-1] # Backfill

         if i > 0: # Ensure we have a previous trend value
            prev_trend = trend[i-1]
            current_trend = prev_trend

            if prev_trend == 1 and df['potential_up_turn'].iloc[i]:
                current_trend = -1
            elif prev_trend == -1 and df['potential_down_turn'].iloc[i]:
                current_trend = 1

            trend[i] = current_trend

    df['trend'] = trend
    # diff() = current - previous. 1-(-1) = 2 (low pivot). -1-(1) = -2 (high pivot).
    df['trend_change'] = df['trend'].diff().fillna(0)

    # --- Étape 3: Identifier et stocker les pivots confirmés ---
    pivots = []
    last_confirmed_low_idx = df.index[0]
    last_confirmed_high_idx = df.index[0]
    low_pivots_prices = []
    high_pivots_prices = []
    # Initialize first pivot based on initial trend? Or just let the loop find them?
    # Let the loop find them to be safer.

    for i in range(1, len(df)):
        current_idx = df.index[i]
        change = df['trend_change'].iloc[i]

        # --- Confirmation d'un PIVOT HAUT (trend 1 -> -1) ---
        if change == -2:
            # Lookback from the last confirmed LOW pivot up to (but not including) the current bar
            lookback_start_loc = df.index.get_loc(last_confirmed_low_idx)
            lookback_window = df.iloc[lookback_start_loc : i] # up to i (exclusive)
            if lookback_window.empty: continue

            pivot_high_price = lookback_window['High'].max()
            pivot_high_idx = lookback_window['High'].idxmax()

            # Avoid adding duplicate pivots if trend flips back and forth quickly
            if pivots and pivots[-1]['index'] == pivot_high_idx: continue
            # Ensure the new pivot is strictly after the last one of the opposite type
            if pivot_high_idx <= last_confirmed_low_idx: continue

            status = 'H'
            if high_pivots_prices:
                prev_high_price = high_pivots_prices[-1]
                if pivot_high_price > prev_high_price: status = 'HH'
                elif pivot_high_price < prev_high_price: status = 'LH'
                else: status = 'EH'

            pivot_info = {'index': pivot_high_idx, 'price': pivot_high_price, 'type': 'high', 'status': status}
            pivots.append(pivot_info)
            high_pivots_prices.append(pivot_high_price)
            last_confirmed_high_idx = pivot_high_idx

        # --- Confirmation d'un PIVOT BAS (trend -1 -> 1) ---
        elif change == 2:
            # Lookback from the last confirmed HIGH pivot up to (but not including) the current bar
            lookback_start_loc = df.index.get_loc(last_confirmed_high_idx)
            lookback_window = df.iloc[lookback_start_loc : i] # up to i (exclusive)
            if lookback_window.empty: continue

            pivot_low_price = lookback_window['Low'].min()
            pivot_low_idx = lookback_window['Low'].idxmin()

            # Avoid adding duplicate pivots
            if pivots and pivots[-1]['index'] == pivot_low_idx: continue
             # Ensure the new pivot is strictly after the last one of the opposite type
            if pivot_low_idx <= last_confirmed_high_idx: continue

            status = 'L'
            if low_pivots_prices:
                prev_low_price = low_pivots_prices[-1]
                if pivot_low_price < prev_low_price: status = 'LL'
                elif pivot_low_price > prev_low_price: status = 'HL'
                else: status = 'EL'

            pivot_info = {'index': pivot_low_idx, 'price': pivot_low_price, 'type': 'low', 'status': status}
            pivots.append(pivot_info)
            low_pivots_prices.append(pivot_low_price)
            last_confirmed_low_idx = pivot_low_idx

    # Final sort just in case (should be sorted already)
    pivots.sort(key=lambda x: df.index.get_loc(x['index']))

    return pivots


def find_interest_zone(df_ohlc_sma: pd.DataFrame,
                         pivots: list,
                         new_pivot_index_in_list: int) -> dict | None:
    """
    Identifie la zone d'intérêt basée sur une bougie de cassure de la SMA20
    suite à la confirmation d'un nouveau pivot HH ou LL.

    Args:
        df_ohlc_sma: DataFrame pandas avec 'High', 'Low', 'Close', 'SMA20'.
                     L'index doit être DatetimeIndex, trié chronologiquement.
        pivots: La liste complète des pivots ZigZag détectés.
        new_pivot_index_in_list: L'index du pivot HH/LL *nouvellement confirmé* dans la liste `pivots`.

    Returns:
        Un dictionnaire décrivant la zone {...} ou None.
    """
    if new_pivot_index_in_list < 1 or new_pivot_index_in_list >= len(pivots):
        return None

    new_pivot = pivots[new_pivot_index_in_list]
    prev_pivot = pivots[new_pivot_index_in_list - 1]

    if new_pivot['type'] == prev_pivot['type']: return None # Pivots doivent être opposés

    # --- Cas: Nouveau Pivot HAUT (HH/LH/H) -> Cherche zone Achat ---
    if new_pivot['type'] == 'high':
        preceding_low_pivot = prev_pivot
        if preceding_low_pivot['type'] != 'low': return None

        # Plage de recherche: après le pivot bas précédent jusqu'au nouveau pivot haut
        try:
            search_start_loc = df_ohlc_sma.index.get_loc(preceding_low_pivot['index']) + 1
            search_end_loc = df_ohlc_sma.index.get_loc(new_pivot['index'])
            if search_start_loc > search_end_loc: return None
        except KeyError:
             # print(f"Warning: Pivot index not found in DataFrame for zone search.") # Debug
             return None # Pivot index non trouvé dans le DF actuel (peut arriver avec dropna)


        search_df = df_ohlc_sma.iloc[search_start_loc : search_end_loc + 1]
        if search_df.empty: return None

        breakout_candle_index = None
        # Cherche PREMIERE clôture AU-DESSUS SMA20 dans la plage
        for idx, row in search_df.iterrows():
            if row['Close'] > row['SMA20']:
                breakout_candle_index = idx
                break

        if breakout_candle_index is None: return None

        # Zone Achat: Début=High bougie cassure, Fin=Low pivot bas précédent
        zone_start_price = df_ohlc_sma.loc[breakout_candle_index, 'High']
        zone_end_price = preceding_low_pivot['price']

        return {
            'start_price': zone_start_price, 'end_price': zone_end_price,
            'direction': 'bullish',
            'breakout_candle_index': breakout_candle_index,
            'preceding_pivot_index': preceding_low_pivot['index']
        }

    # --- Cas: Nouveau Pivot BAS (LL/HL/L) -> Cherche zone Vente ---
    elif new_pivot['type'] == 'low':
        preceding_high_pivot = prev_pivot
        if preceding_high_pivot['type'] != 'high': return None

        # Plage de recherche: après le pivot haut précédent jusqu'au nouveau pivot bas
        try:
            search_start_loc = df_ohlc_sma.index.get_loc(preceding_high_pivot['index']) + 1
            search_end_loc = df_ohlc_sma.index.get_loc(new_pivot['index'])
            if search_start_loc > search_end_loc: return None
        except KeyError:
            # print(f"Warning: Pivot index not found in DataFrame for zone search.") # Debug
            return None

        search_df = df_ohlc_sma.iloc[search_start_loc : search_end_loc + 1]
        if search_df.empty: return None

        breakout_candle_index = None
        # Cherche PREMIERE clôture EN DESSOUS SMA20 dans la plage
        for idx, row in search_df.iterrows():
            if row['Close'] < row['SMA20']:
                breakout_candle_index = idx
                break

        if breakout_candle_index is None: return None

        # Zone Vente: Début=Low bougie cassure, Fin=High pivot haut précédent
        zone_start_price = df_ohlc_sma.loc[breakout_candle_index, 'Low']
        zone_end_price = preceding_high_pivot['price']

        return {
            'start_price': zone_start_price, 'end_price': zone_end_price,
            'direction': 'bearish',
            'breakout_candle_index': breakout_candle_index,
            'preceding_pivot_index': preceding_high_pivot['index']
        }

    return None


def check_divergence_in_zone(current_low: float,
                              current_high: float,
                              current_rsi: float,
                              zone_info: dict,
                              last_relevant_pivot: dict,
                              rsi_at_last_pivot: float) -> str | None:
    """
    Vérifie si le prix actuel est dans la zone d'intérêt et s'il y a une
    divergence RSI pertinente par rapport au dernier pivot ZigZag.

    Args:
        current_low: Le prix bas de la bougie actuelle.
        current_high: Le prix haut de la bougie actuelle.
        current_rsi: La valeur RSI de la bougie actuelle.
        zone_info: Dictionnaire retourné par find_interest_zone.
        last_relevant_pivot: Le pivot ZigZag (bas ou haut) qui définit la fin de la zone.
        rsi_at_last_pivot: La valeur RSI au moment du last_relevant_pivot.

    Returns:
        Le type de divergence détectée ("BULL_REGULAR", "BULL_CONTINUATION",
        "BEAR_REGULAR", "BEAR_CONTINUATION") si les conditions sont remplies,
        sinon None.
    """
    if zone_info is None or last_relevant_pivot is None or pd.isna(current_rsi) or pd.isna(rsi_at_last_pivot):
        return None

    zone_start = zone_info['start_price']
    zone_end = zone_info['end_price']
    direction = zone_info['direction']
    pivot_price = last_relevant_pivot['price']

    # Définir zone_upper/lower pour comparaison
    zone_upper = max(zone_start, zone_end)
    zone_lower = min(zone_start, zone_end)
    zone_size = zone_upper - zone_lower
    tolerance = zone_size * 0.05 if zone_size > 0 else 0.00001 # Petite tolérance pour comparaison prix

    # --- Setup ACHAT (zone bullish) ---
    if direction == 'bullish':
        if last_relevant_pivot['type'] != 'low': return None # Doit comparer avec un pivot bas
        # Prix (Low) doit être dans la zone
        if not (zone_lower <= current_low <= zone_upper): return None

        # Div Bull Régulière: LL < L mais RSI(LL) > RSI(L)
        if current_low < pivot_price - tolerance and current_rsi > rsi_at_last_pivot:
             # print(f"Debug: Div Bull Regular détectée (Prix: {current_low:.5f} < {pivot_price:.5f}, RSI: {current_rsi:.2f} > {rsi_at_last_pivot:.2f})")
             return "BULL_REGULAR"
        # Div Bull Continuation: HL > L mais RSI(HL) < RSI(L)
        if current_low > pivot_price + tolerance and current_rsi < rsi_at_last_pivot:
             # print(f"Debug: Div Bull Cont détectée (Prix: {current_low:.5f} > {pivot_price:.5f}, RSI: {current_rsi:.2f} < {rsi_at_last_pivot:.2f})")
             return "BULL_CONTINUATION"

    # --- Setup VENTE (zone bearish) ---
    elif direction == 'bearish':
        if last_relevant_pivot['type'] != 'high': return None # Doit comparer avec un pivot haut
        # Prix (High) doit être dans la zone
        if not (zone_lower <= current_high <= zone_upper): return None

        # Div Bear Régulière: HH > H mais RSI(HH) < RSI(H)
        if current_high > pivot_price + tolerance and current_rsi < rsi_at_last_pivot:
            # print(f"Debug: Div Bear Regular détectée (Prix: {current_high:.5f} > {pivot_price:.5f}, RSI: {current_rsi:.2f} < {rsi_at_last_pivot:.2f})")
            return "BEAR_REGULAR"
        # Div Bear Continuation: LH < H mais RSI(LH) > RSI(H)
        if current_high < pivot_price - tolerance and current_rsi > rsi_at_last_pivot:
            # print(f"Debug: Div Bear Cont détectée (Prix: {current_high:.5f} < {pivot_price:.5f}, RSI: {current_rsi:.2f} > {rsi_at_last_pivot:.2f})")
            return "BEAR_CONTINUATION"

    return None

# ----- START: NOUVELLE FONCTION detect_engulfing_pattern -----
def detect_engulfing_pattern(df_ohlc: pd.DataFrame, current_candle_index: pd.Timestamp, direction: str) -> bool:
    """
    Détecte un pattern d'englobante (Bullish ou Bearish) à l'index spécifié.

    Args:
        df_ohlc: DataFrame pandas avec 'Open', 'High', 'Low', 'Close'.
                 L'index doit être DatetimeIndex, trié chronologiquement.
        current_candle_index: L'index (Timestamp) de la bougie de confirmation potentielle (celle qui englobe).
        direction: 'bullish' pour chercher une englobante haussière,
                   'bearish' pour chercher une englobante baissière.

    Returns:
        True si le pattern est détecté, False sinon.
    """
    try:
        current_loc = df_ohlc.index.get_loc(current_candle_index)
        if current_loc < 1: # Besoin d'au moins une bougie précédente
            return False

        prev_loc = current_loc - 1
        current_candle = df_ohlc.iloc[current_loc]
        prev_candle = df_ohlc.iloc[prev_loc]

        # Vérifier si les bougies sont valides (contiennent les données nécessaires)
        if pd.isna(current_candle['Open']) or pd.isna(current_candle['Close']) or \
           pd.isna(prev_candle['Open']) or pd.isna(prev_candle['Close']):
            return False

        # --- Englobante Haussière (Trigger Achat) ---
        if direction == 'bullish':
            # Bougie actuelle doit être haussière
            is_current_bullish = current_candle['Close'] > current_candle['Open']
            # Bougie précédente doit être baissière
            is_previous_bearish = prev_candle['Close'] < prev_candle['Open']
            # Corps actuel englobe corps précédent
            does_current_engulf_previous = (current_candle['Open'] < prev_candle['Close']) and \
                                           (current_candle['Close'] > prev_candle['Open'])

            if is_current_bullish and is_previous_bearish and does_current_engulf_previous:
                # print(f"DEBUG Engulfing: Bullish Engulfing detected at {current_candle_index}")
                return True

        # --- Englobante Baissière (Trigger Vente) ---
        elif direction == 'bearish':
            # Bougie actuelle doit être baissière
            is_current_bearish = current_candle['Close'] < current_candle['Open']
            # Bougie précédente doit être haussière
            is_previous_bullish = prev_candle['Close'] > prev_candle['Open']
            # Corps actuel englobe corps précédent
            does_current_engulf_previous = (current_candle['Open'] > prev_candle['Close']) and \
                                           (current_candle['Close'] < prev_candle['Open'])

            if is_current_bearish and is_previous_bullish and does_current_engulf_previous:
                # print(f"DEBUG Engulfing: Bearish Engulfing detected at {current_candle_index}")
                return True

    except KeyError:
        # L'index n'est pas trouvé dans le DataFrame
        # print(f"DEBUG Engulfing: Index {current_candle_index} not found in DataFrame.")
        return False
    except IndexError:
        # Problème d'accès par position (ne devrait pas arriver avec get_loc)
        # print(f"DEBUG Engulfing: Index location issue for {current_candle_index}.")
        return False
    except Exception as e:
        # Autre erreur inattendue
        print(f"ERREUR inattendue dans detect_engulfing_pattern pour {current_candle_index}: {e}")
        return False

    return False # Si aucune condition n'est remplie

# ----- START: NOUVELLE FONCTION calculate_stop_loss (Logique Corrigée) -----
def calculate_stop_loss(df_ohlc: pd.DataFrame,
                        confirmation_candle_index: pd.Timestamp,
                        direction: str,
                        buffer_points: float = 5.0,
                        max_lookback_candles: int = 10) -> float | None:
    """
    Calcule le niveau de Stop Loss basé sur la structure de prix menant
    à la bougie de confirmation.

    Args:
        df_ohlc: DataFrame pandas avec 'Open', 'High', 'Low', 'Close'. Index DatetimeIndex trié.
        confirmation_candle_index: L'index (Timestamp) de la bougie de confirmation finale.
        direction: 'bullish' (pour un achat) ou 'bearish' (pour une vente).
        buffer_points: Le nombre de points à ajouter/soustraire (ex: 5.0 pour US30).
        max_lookback_candles: Nombre maximum de bougies à regarder en arrière pour
                              trouver la bougie opposée de départ.

    Returns:
        Le niveau de prix du Stop Loss calculé, ou None si impossible.
    """
    try:
        confirmation_loc = df_ohlc.index.get_loc(confirmation_candle_index)
        if confirmation_loc < 1:
            # print(f"DEBUG SL: Confirmation candle {confirmation_candle_index} est la première bougie.")
            return None

        # --- Trouver le début de la plage de calcul SL ---
        start_range_loc = -1
        # Commencer la recherche à partir de la bougie juste AVANT la confirmation
        search_start_loc = confirmation_loc - 1

        for i in range(search_start_loc, max(search_start_loc - max_lookback_candles, -1), -1):
            candle = df_ohlc.iloc[i]
            if pd.isna(candle['Open']) or pd.isna(candle['Close']):
                continue # Ignorer bougie invalide

            is_bullish = candle['Close'] > candle['Open']
            is_bearish = candle['Close'] < candle['Open']

            # Pour un achat (bullish), on cherche la dernière bougie BAISSIERE
            if direction == 'bullish' and is_bearish:
                start_range_loc = i
                break
            # Pour une vente (bearish), on cherche la dernière bougie HAUSSIERE
            elif direction == 'bearish' and is_bullish:
                start_range_loc = i
                break

        # Si on n'a pas trouvé de bougie opposée dans la fenêtre de lookback,
        # utiliser une plage par défaut (ex: juste les 2 dernières bougies comme avant)
        # ou considérer que le setup n'est pas clair. Utilisons les 2 dernières pour l'instant.
        if start_range_loc == -1:
            start_range_loc = confirmation_loc - 1
            # print(f"DEBUG SL: Pas trouvé bougie opposée pour {confirmation_candle_index} dans les {max_lookback_candles} bougies. Utilisation plage réduite.")


        # --- Définir la plage et calculer le SL ---
        # La plage va de l'indice de la bougie opposée trouvée (ou N-1 par défaut)
        # jusqu'à l'indice de la bougie de confirmation (incluse).
        sl_range_df = df_ohlc.iloc[start_range_loc : confirmation_loc + 1]

        if sl_range_df.empty:
            print(f"DEBUG SL: Plage de calcul SL vide pour {confirmation_candle_index}.")
            return None
        if sl_range_df[['Low', 'High']].isnull().values.any():
            print(f"DEBUG SL: Données manquantes dans la plage SL pour {confirmation_candle_index}.")
            return None

        stop_loss_level = None

        # --- SL pour un Achat ---
        if direction == 'bullish':
            # Trouver le plus bas de TOUTES les bougies dans la plage définie
            low_point = sl_range_df['Low'].min()
            stop_loss_level = low_point - buffer_points
            # print(f"DEBUG SL Bullish: Plage [{df_ohlc.index[start_range_loc]}]-[{confirmation_candle_index}]. MinLow = {low_point:.5f}. SL = {stop_loss_level:.5f}")

        # --- SL pour une Vente ---
        elif direction == 'bearish':
            # Trouver le plus haut de TOUTES les bougies dans la plage définie
            high_point = sl_range_df['High'].max()
            stop_loss_level = high_point + buffer_points
            # print(f"DEBUG SL Bearish: Plage [{df_ohlc.index[start_range_loc]}]-[{confirmation_candle_index}]. MaxHigh = {high_point:.5f}. SL = {stop_loss_level:.5f}")


        # Retourner le niveau arrondi
        return round(stop_loss_level, 2) if stop_loss_level is not None else None

    except KeyError:
        # print(f"DEBUG SL: Index {confirmation_candle_index} non trouvé dans DataFrame pour SL.")
        return None
    except Exception as e:
        print(f"ERREUR inattendue dans calculate_stop_loss pour {confirmation_candle_index}: {e}")
        import traceback
        traceback.print_exc() # Afficher plus de détails pour le débogage
        return None

# ----- START: MODIFICATION calculate_take_profit_v1 (Gestion 2 Types TP) -----
def calculate_take_profit_v1(pivots: list,
                           confirmation_candle_index: pd.Timestamp,
                           direction: str,
                           divergence_type: str | None,
                           zone_info: dict | None,
                           df_ohlc: pd.DataFrame) -> float | None: # Ajout df_ohlc pour récupérer prix bougie cassure
    """
    Calcule le niveau de Take Profit v1 basé sur le type de divergence détectée.
    - Continuation: Vise le dernier pivot ZigZag opposé pertinent avant l'entrée.
    - Régulière (Contre-Tendance): Vise le niveau de la bougie de cassure SMA20
      qui a défini le début de la zone d'intérêt.

    Args:
        pivots: La liste complète des pivots ZigZag détectés.
        confirmation_candle_index: L'index de la bougie de confirmation.
        direction: 'bullish' ou 'bearish'.
        divergence_type: Le type de divergence détecté (e.g., "BULL_REGULAR",
                         "BULL_CONTINUATION", "BEAR_REGULAR", "BEAR_CONTINUATION").
        zone_info: Le dictionnaire de la zone d'intérêt active. Requis pour TP régulier.
        df_ohlc: DataFrame avec OHLC pour retrouver le prix de la bougie de cassure. Requis pour TP régulier.


    Returns:
        Le niveau de prix du Take Profit calculé, ou None si impossible.
    """
    if divergence_type is None:
        print(f"DEBUG TP {direction}: Type de divergence non fourni.")
        return None

    take_profit_level = None

    # --- Cas 1: Divergence de CONTINUATION (Cachée) ---
    if "CONTINUATION" in divergence_type:
        # print(f"DEBUG TP {direction}: Calcul TP pour Divergence Continuation...")
        target_pivot = None
        target_pivot_type = 'high' if direction == 'bullish' else 'low'

        for pivot in reversed(pivots):
            pivot_index = pivot.get('index')
            pivot_type = pivot.get('type')
            pivot_price = pivot.get('price')

            if pivot_index is None or pivot_type is None or pivot_price is None: continue
            if pivot_index >= confirmation_candle_index: continue

            if pivot_type == target_pivot_type:
                target_pivot = pivot
                break

        if target_pivot:
            take_profit_level = target_pivot['price']
            # print(f"DEBUG TP {direction} Continuation: Cible trouvée au pivot {target_pivot['type']} à {target_pivot['index']} (Prix: {take_profit_level:.5f})")
        else:
             print(f"DEBUG TP {direction} Continuation: Aucun pivot {target_pivot_type} trouvé avant {confirmation_candle_index}.")
             return None # Impossible de calculer le TP

    # --- Cas 2: Divergence REGULIERE (Contre Tendance) ---
    elif "REGULAR" in divergence_type:
        # print(f"DEBUG TP {direction}: Calcul TP pour Divergence Régulière...")
        if zone_info is None:
            print(f"DEBUG TP {direction} Régulière: zone_info manquant.")
            return None
        if df_ohlc is None:
             print(f"DEBUG TP {direction} Régulière: df_ohlc manquant.")
             return None

        # Le TP est le PRIX de la bougie de cassure qui a défini le début de la zone
        # Pour une zone Bullish (achat), la cassure était haussière, on vise son High.
        # Pour une zone Bearish (vente), la cassure était baissière, on vise son Low.
        # C'est le 'start_price' de zone_info qui contient déjà cette valeur.
        take_profit_level = zone_info.get('start_price')

        if take_profit_level is None:
            print(f"DEBUG TP {direction} Régulière: Impossible de récupérer 'start_price' depuis zone_info.")
            return None
        # else:
            # print(f"DEBUG TP {direction} Régulière: Cible basée sur zone_info['start_price'] = {take_profit_level:.5f} (Bougie: {zone_info.get('breakout_candle_index')})")

    # --- Cas Inconnu ---
    else:
        print(f"DEBUG TP {direction}: Type de divergence inconnu ou non géré: {divergence_type}")
        return None

    # Retourner le niveau arrondi
    return round(take_profit_level, 2) if take_profit_level is not None else None

# ----- START: NOUVELLE FONCTION calculate_position_size -----


def calculate_position_size(account_balance: float,
                            risk_percentage: float,
                            sl_level: float,
                            entry_price: float,
                            symbol_info: dict) -> float | None:
    """
    Calcule la taille de la position (volume en lots) basée sur le risque,
    la distance du SL et les spécifications de l'instrument.

    Args:
        account_balance: Solde actuel du compte dans la devise du compte.
        risk_percentage: Pourcentage du solde à risquer (ex: 1.0 pour 1%).
        sl_level: Niveau de prix du Stop Loss.
        entry_price: Prix d'entrée estimé.
        symbol_info: Dictionnaire contenant les spécifications du symbole:
                     'point', 'trade_tick_value', 'trade_tick_size',
                     'volume_min', 'volume_max', 'volume_step'.

    Returns:
        Le volume calculé et ajusté, ou None si impossible.
    """
    try:
        # --- Validation des entrées ---
        if account_balance <= 0 or risk_percentage <= 0 or sl_level == entry_price:
            print(f"DEBUG Size: Entrées invalides (balance={account_balance}, risk={risk_percentage}, SL={sl_level}, Entry={entry_price})")
            return None

        point = symbol_info.get('point')
        tick_value = symbol_info.get('trade_tick_value')
        tick_size = symbol_info.get('trade_tick_size')
        volume_min = symbol_info.get('volume_min')
        volume_max = symbol_info.get('volume_max')
        volume_step = symbol_info.get('volume_step')

        if None in [point, tick_value, tick_size, volume_min, volume_max, volume_step] or tick_size == 0 or point == 0:
             print(f"DEBUG Size: Informations symbole manquantes ou invalides: {symbol_info}")
             return None
        if volume_step <= 0:
            print(f"DEBUG Size: Volume step invalide: {volume_step}")
            return None


        # --- Calculs ---
        # 1. Montant du risque en devise du compte
        risk_amount = account_balance * (risk_percentage / 100.0)

        # 2. Distance SL en Pips/Points (unités définies par 'point')
        sl_distance_points = abs(entry_price - sl_level) / point
        if sl_distance_points <= 0:
             print(f"DEBUG Size: Distance SL nulle ou négative ({sl_distance_points})")
             return None

        # 3. Valeur d'un point pour 1 lot standard dans la devise du compte
        #    (Valeur d'un tick / Taille d'un tick) * Taille d'un point
        point_value_per_lot = (tick_value / tick_size) * point
        if point_value_per_lot <= 0:
            print(f"DEBUG Size: Valeur du point par lot nulle ou négative ({point_value_per_lot})")
            return None

        # 4. Volume idéal (théorique)
        volume_ideal = risk_amount / (sl_distance_points * point_value_per_lot)

        # --- Ajustements selon les contraintes du broker ---
        # 5. Arrondir au step inférieur (pour ne jamais dépasser le risque)
        #    volume = floor(volume_ideal / volume_step) * volume_step
        #    Utiliser math.floor après division donne le nombre de steps entiers
        volume_adjusted = math.floor(volume_ideal / volume_step) * volume_step

        # 6. Vérifier les limites min/max
        volume_final = max(volume_min, volume_adjusted) # Assurer au moins le min
        volume_final = min(volume_max, volume_final)   # Ne pas dépasser le max

        # Vérifier si le volume minimum dépasse déjà le risque autorisé
        # (arrive si SL très proche ou compte petit)
        min_volume_risk = (sl_distance_points * point_value_per_lot) * volume_min
        if min_volume_risk > risk_amount and volume_final == volume_min:
             print(f"ATTENTION Size: Volume minimum ({volume_min}) dépasse le risque autorisé ({risk_amount:.2f} > {min_volume_risk:.2f}). Trade trop risqué.")
             # Dans un vrai système, on pourrait décider de ne pas trader ici.
             # Pour le test, on retourne le volume min, mais avec l'alerte.
             # return None # Option plus sûre: ne pas trader
             pass # Pour le test, on continue mais on a l'alerte

        # Arrondir le résultat final à la précision du step pour éviter erreurs flottants
        # Ex: si step=0.01, arrondir à 2 décimales.
        decimals = 0
        if '.' in str(volume_step):
             decimals = len(str(volume_step).split('.')[-1])

        volume_final = round(volume_final, decimals)

        # print(f"DEBUG Size: Balance={account_balance:.2f}, Risk%={risk_percentage:.2f}, RiskAmt={risk_amount:.2f}")
        # print(f"DEBUG Size: SL={sl_level:.5f}, Entry={entry_price:.5f}, SLDistPts={sl_distance_points:.2f}")
        # print(f"DEBUG Size: TickVal={tick_value}, TickSize={tick_size}, Point={point}, PtValLot={point_value_per_lot:.5f}")
        # print(f"DEBUG Size: VolIdeal={volume_ideal:.6f}, VolAdjusted={volume_adjusted:.6f}, VolFinal={volume_final:.{decimals}f}")

        # Vérification finale: le volume doit être > 0 et >= min
        if volume_final < volume_min :
             print(f"DEBUG Size: Volume final ({volume_final}) inférieur au minimum requis ({volume_min}).")
             return None

        return volume_final

    except Exception as e:
        print(f"ERREUR inattendue dans calculate_position_size: {e}")
        import traceback
        traceback.print_exc()
        return None

# ----- END: NOUVELLE FONCTION calculate_position_size -----

# --- EXEMPLE: Simulation des infos pour US30.cash compte EUR (À METTRE À JOUR !) ---
# Ces valeurs DOIVENT être récupérées de MT5 pour être exactes.
# Mettez-les ici pour pouvoir tester la fonction sans MT5 connecté.
SYMBOL_INFO_US30_EUR_SIMULATED = {
    "name": "US30.cash",
    "currency_account": "EUR",
    "trade_contract_size": 1.0,    # Généralement 1 pour les CFD sur Indices
    "trade_tick_value": 0.09,      # !!! VALEUR CRUCIALE À VÉRIFIER SUR VOTRE MT5 !!! (valeur en EUR d'un mouvement de 0.1 pour 1 lot)
    "trade_tick_size": 0.1,        # !!! À VÉRIFIER SUR VOTRE MT5 !!! (plus petite variation affichée)
    "point": 1.0,                  # Pour US30, 1 point = 1.0 changement de prix (généralement correct)
    "volume_min": 0.01,            # Minimum lot size (souvent 0.01 ou 0.1)
    "volume_max": 100.0,           # Maximum lot size (varie beaucoup)
    "volume_step": 0.01            # Incrément de lot size (souvent 0.01)
}
# --- FIN EXEMPLE SIMULATION ---

