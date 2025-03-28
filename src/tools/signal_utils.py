# ----- START OF FILE src/tools/signal_utils.py -----
import pandas as pd
import numpy as np
import pandas_ta as ta # Assurez-vous que pandas-ta est installé (pip install pandas-ta)

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
# ----- END OF FILE src/tools/signal_utils.py -----