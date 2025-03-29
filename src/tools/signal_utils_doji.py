# ----- START OF FILE src/tools/signal_utils.py (Version Complète et Révisée) -----
import pandas as pd
import numpy as np
import pandas_ta as ta # Assurez-vous que pandas-ta est installé
import math
import traceback # Pour le débogage des erreurs

# === Fonction 1: Calcul Pivots ZigZag ===
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
        return []

    df = df_ohlc.sort_index(ascending=True).copy()
    df['rolling_max'] = df['High'].rolling(length).max().shift(1)
    df['rolling_min'] = df['Low'].rolling(length).min().shift(1)
    df['potential_up_turn'] = df['Low'] <= df['rolling_min']
    df['potential_down_turn'] = df['High'] >= df['rolling_max']

    trend = np.zeros(len(df), dtype=int)
    initial_trend_determined = False
    for i in range(length, len(df)):
        if not initial_trend_determined and i > 0:
            if df['Close'].iloc[i-1] > df['Close'].iloc[i-length if i-length >= 0 else 0]:
                trend[i-1] = 1
            else:
                trend[i-1] = -1
            initial_trend_determined = True
            trend[:i-1] = trend[i-1]

        if i > 0:
            prev_trend = trend[i-1]
            current_trend = prev_trend
            if prev_trend == 1 and df['potential_up_turn'].iloc[i]:
                current_trend = -1
            elif prev_trend == -1 and df['potential_down_turn'].iloc[i]:
                current_trend = 1
            trend[i] = current_trend

    df['trend'] = trend
    df['trend_change'] = df['trend'].diff().fillna(0)

    pivots = []
    last_confirmed_low_idx = df.index[0]
    last_confirmed_high_idx = df.index[0]
    low_pivots_prices = []
    high_pivots_prices = []

    for i in range(1, len(df)):
        current_idx = df.index[i]
        change = df['trend_change'].iloc[i]

        if change == -2: # High Pivot Confirmation
            lookback_start_loc = df.index.get_loc(last_confirmed_low_idx)
            lookback_window = df.iloc[lookback_start_loc : i]
            if lookback_window.empty: continue
            pivot_high_price = lookback_window['High'].max()
            pivot_high_idx = lookback_window['High'].idxmax()
            if pivots and pivots[-1]['index'] == pivot_high_idx: continue
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

        elif change == 2: # Low Pivot Confirmation
            lookback_start_loc = df.index.get_loc(last_confirmed_high_idx)
            lookback_window = df.iloc[lookback_start_loc : i]
            if lookback_window.empty: continue
            pivot_low_price = lookback_window['Low'].min()
            pivot_low_idx = lookback_window['Low'].idxmin()
            if pivots and pivots[-1]['index'] == pivot_low_idx: continue
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

    pivots.sort(key=lambda x: df.index.get_loc(x['index']))
    return pivots

# === Fonction 2: Trouver Zone d'Intérêt ===
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
    if new_pivot['type'] == prev_pivot['type']: return None

    # --- Cas Achat (après HH) ---
    if new_pivot['type'] == 'high':
        preceding_low_pivot = prev_pivot
        if preceding_low_pivot['type'] != 'low': return None
        try:
            search_start_loc = df_ohlc_sma.index.get_loc(preceding_low_pivot['index']) + 1
            search_end_loc = df_ohlc_sma.index.get_loc(new_pivot['index'])
            if search_start_loc > search_end_loc: return None
        except KeyError: return None
        search_df = df_ohlc_sma.iloc[search_start_loc : search_end_loc + 1]
        if search_df.empty: return None
        breakout_candle_index = None
        for idx, row in search_df.iterrows():
            # Vérifier si SMA20 est valide avant comparaison
            if not pd.isna(row['SMA20']) and row['Close'] > row['SMA20']:
                breakout_candle_index = idx
                break
        if breakout_candle_index is None: return None
        zone_start_price = df_ohlc_sma.loc[breakout_candle_index, 'High']
        zone_end_price = preceding_low_pivot['price']
        return {'start_price': zone_start_price, 'end_price': zone_end_price,
                'direction': 'bullish', 'breakout_candle_index': breakout_candle_index,
                'preceding_pivot_index': preceding_low_pivot['index']}

    # --- Cas Vente (après LL) ---
    elif new_pivot['type'] == 'low':
        preceding_high_pivot = prev_pivot
        if preceding_high_pivot['type'] != 'high': return None
        try:
            search_start_loc = df_ohlc_sma.index.get_loc(preceding_high_pivot['index']) + 1
            search_end_loc = df_ohlc_sma.index.get_loc(new_pivot['index'])
            if search_start_loc > search_end_loc: return None
        except KeyError: return None
        search_df = df_ohlc_sma.iloc[search_start_loc : search_end_loc + 1]
        if search_df.empty: return None
        breakout_candle_index = None
        for idx, row in search_df.iterrows():
             # Vérifier si SMA20 est valide avant comparaison
            if not pd.isna(row['SMA20']) and row['Close'] < row['SMA20']:
                breakout_candle_index = idx
                break
        if breakout_candle_index is None: return None
        zone_start_price = df_ohlc_sma.loc[breakout_candle_index, 'Low']
        zone_end_price = preceding_high_pivot['price']
        return {'start_price': zone_start_price, 'end_price': zone_end_price,
                'direction': 'bearish', 'breakout_candle_index': breakout_candle_index,
                'preceding_pivot_index': preceding_high_pivot['index']}
    return None

# === Fonction 3: Vérifier Divergence dans Zone ===
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
    zone_start = zone_info['start_price']; zone_end = zone_info['end_price']
    direction = zone_info['direction']; pivot_price = last_relevant_pivot['price']
    zone_upper = max(zone_start, zone_end); zone_lower = min(zone_start, zone_end)
    zone_size = zone_upper - zone_lower
    # Utiliser une tolérance relative (ex: 0.1% du prix) et absolue minimale pour la comparaison des prix
    price_tolerance_relative = pivot_price * 0.0005 # 0.05%
    price_tolerance_absolute = 0.1 # Ex: 0.1 point minimum
    price_tolerance = max(price_tolerance_relative, price_tolerance_absolute)
    # Utiliser une tolérance pour le RSI (ex: 1 point RSI)
    rsi_tolerance = 1.0

    if direction == 'bullish':
        if last_relevant_pivot['type'] != 'low': return None
        if not (zone_lower <= current_low <= zone_upper): return None
        # Regular: Lower Low Price + Higher Low RSI
        if current_low < pivot_price - price_tolerance and current_rsi > rsi_at_last_pivot + rsi_tolerance:
            return "BULL_REGULAR"
        # Hidden (Continuation): Higher Low Price + Lower Low RSI
        if current_low > pivot_price + price_tolerance and current_rsi < rsi_at_last_pivot - rsi_tolerance:
            return "BULL_CONTINUATION"

    elif direction == 'bearish':
        if last_relevant_pivot['type'] != 'high': return None
        if not (zone_lower <= current_high <= zone_upper): return None
        # Regular: Higher High Price + Lower High RSI
        if current_high > pivot_price + price_tolerance and current_rsi < rsi_at_last_pivot - rsi_tolerance:
            return "BEAR_REGULAR"
        # Hidden (Continuation): Lower High Price + Higher High RSI
        if current_high < pivot_price - price_tolerance and current_rsi > rsi_at_last_pivot + rsi_tolerance:
            return "BEAR_CONTINUATION"
    return None

# === Fonction 4: Détecter Pattern Englobant ===
def detect_engulfing_pattern(df_ohlc: pd.DataFrame, current_candle_index: pd.Timestamp, direction: str) -> bool:
    """
    Détecte un pattern d'englobante (Bullish ou Bearish) à l'index spécifié.
    N'englobe pas les dojis (bougies avec corps nul).

    Args:
        df_ohlc: DataFrame pandas avec 'Open', 'Close'. Index DatetimeIndex trié.
        current_candle_index: L'index (Timestamp) de la bougie de confirmation (celle qui englobe).
        direction: 'bullish' ou 'bearish'.

    Returns:
        True si le pattern est détecté, False sinon.
    """
    try:
        current_loc = df_ohlc.index.get_loc(current_candle_index)
        if current_loc < 1: return False # Besoin de la bougie précédente

        current_candle = df_ohlc.iloc[current_loc]
        prev_candle = df_ohlc.iloc[current_loc - 1]

        required_cols = ['Open', 'Close']
        if current_candle[required_cols].isnull().any() or prev_candle[required_cols].isnull().any():
            return False

        prev_body = abs(prev_candle['Close'] - prev_candle['Open'])
        # Ignorer si la bougie précédente est un doji (ou a un corps très petit)
        # Utiliser une petite tolérance pour le corps nul
        body_tolerance = (df_ohlc['High'].mean() - df_ohlc['Low'].mean()) * 0.01 if len(df_ohlc)>0 else 0.01 # 1% de l'ATR moyen comme tolérance
        if prev_body < body_tolerance: return False

        if direction == 'bullish':
            is_current_bullish = current_candle['Close'] > current_candle['Open']
            is_previous_bearish = prev_candle['Close'] < prev_candle['Open']
            does_current_engulf_previous = (current_candle['Open'] < prev_candle['Close']) and \
                                           (current_candle['Close'] > prev_candle['Open'])
            if is_current_bullish and is_previous_bearish and does_current_engulf_previous:
                return True

        elif direction == 'bearish':
            is_current_bearish = current_candle['Close'] < current_candle['Open']
            is_previous_bullish = prev_candle['Close'] > prev_candle['Open']
            does_current_engulf_previous = (current_candle['Open'] > prev_candle['Close']) and \
                                           (current_candle['Close'] < prev_candle['Open'])
            if is_current_bearish and is_previous_bullish and does_current_engulf_previous:
                return True

    except KeyError: return False
    except Exception as e:
        print(f"ERREUR inattendue dans detect_engulfing_pattern pour {current_candle_index}: {e}")
        # traceback.print_exc() # Décommenter pour debug
        return False
    return False

# === Fonction 5: Calculer Stop Loss ===
def calculate_stop_loss(df_ohlc: pd.DataFrame,
                        confirmation_candle_index: pd.Timestamp,
                        direction: str,
                        buffer_points: float = 5.0,
                        max_lookback_candles: int = 10) -> float | None:
    """
    Calcule le niveau de Stop Loss basé sur la structure de prix menant
    à la bougie de confirmation (range entre dernière bougie opposée et confirmation).

    Args:
        df_ohlc: DataFrame pandas avec 'Open', 'High', 'Low', 'Close'. Index DatetimeIndex trié.
        confirmation_candle_index: L'index (Timestamp) de la bougie de confirmation finale.
        direction: 'bullish' (pour un achat) ou 'bearish' (pour une vente).
        buffer_points: Le nombre de points à ajouter/soustraire (ex: 5.0 pour US30).
                       Devrait être adapté au spread live + marge dans l'agent principal.
        max_lookback_candles: Nombre maximum de bougies à regarder en arrière pour
                              trouver la bougie opposée de départ de la structure.

    Returns:
        Le niveau de prix du Stop Loss calculé (arrondi à 2 décimales), ou None si impossible.
    """
    try:
        confirmation_loc = df_ohlc.index.get_loc(confirmation_candle_index)
        if confirmation_loc < 1: return None

        start_range_loc = -1
        search_start_loc = confirmation_loc - 1
        lookback_limit = max(search_start_loc - max_lookback_candles + 1, 0)

        for i in range(search_start_loc, lookback_limit -1, -1):
            candle = df_ohlc.iloc[i]
            if pd.isna(candle['Open']) or pd.isna(candle['Close']): continue
            is_bullish = candle['Close'] > candle['Open']
            is_bearish = candle['Close'] < candle['Open']
            if direction == 'bullish' and is_bearish:
                start_range_loc = i; break
            elif direction == 'bearish' and is_bullish:
                start_range_loc = i; break

        if start_range_loc == -1:
            start_range_loc = confirmation_loc - 1 # Fallback aux 2 dernières bougies

        sl_range_df = df_ohlc.iloc[start_range_loc : confirmation_loc + 1]
        if sl_range_df.empty or sl_range_df[['Low', 'High']].isnull().values.any():
            return None

        stop_loss_level = None
        if direction == 'bullish':
            low_point = sl_range_df['Low'].min()
            stop_loss_level = low_point - buffer_points
        elif direction == 'bearish':
            high_point = sl_range_df['High'].max()
            stop_loss_level = high_point + buffer_points

        return round(stop_loss_level, 2) if stop_loss_level is not None else None

    except KeyError: return None
    except Exception as e:
        print(f"ERREUR inattendue dans calculate_stop_loss pour {confirmation_candle_index}: {e}")
        traceback.print_exc()
        return None

# === Fonction 6: Calculer Take Profit V1 ===
def calculate_take_profit_v1(pivots: list,
                           confirmation_candle_index: pd.Timestamp,
                           direction: str,
                           divergence_type: str | None,
                           zone_info: dict | None,
                           df_ohlc: pd.DataFrame = None) -> float | None: # df_ohlc optionnel
    """
    Calcule le niveau de Take Profit v1 basé sur le type de divergence détectée.
    - Continuation: Vise le prix du dernier pivot ZigZag opposé pertinent avant l'entrée.
    - Régulière (Contre-Tendance): Vise le niveau de la bougie de cassure SMA20
      qui a défini le début de la zone d'intérêt (`zone_info['start_price']`).

    Args:
        pivots: La liste complète des pivots ZigZag détectés.
        confirmation_candle_index: L'index de la bougie de confirmation.
        direction: 'bullish' ou 'bearish'.
        divergence_type: Le type de divergence détecté (e.g., "BULL_REGULAR", etc.).
        zone_info: Le dictionnaire de la zone d'intérêt active. Requis pour TP régulier.
        df_ohlc: DataFrame avec OHLC. Principalement utile si zone_info n'est pas complet.

    Returns:
        Le niveau de prix du Take Profit calculé (arrondi à 2 décimales), ou None si impossible.
    """
    if not divergence_type: return None

    take_profit_level = None

    if "CONTINUATION" in divergence_type:
        target_pivot = None
        target_pivot_type = 'high' if direction == 'bullish' else 'low'
        for pivot in reversed(pivots):
            pivot_index = pivot.get('index')
            if pivot_index is None or pivot.get('type') is None or pivot.get('price') is None or pivot_index >= confirmation_candle_index:
                continue
            if pivot['type'] == target_pivot_type:
                target_pivot = pivot
                break
        if target_pivot:
            take_profit_level = target_pivot['price']
        else: return None # TP Continuation non trouvé

    elif "REGULAR" in divergence_type:
        if not zone_info: return None
        take_profit_level = zone_info.get('start_price')
        if take_profit_level is None: return None # TP Régulier non trouvé

    else: return None # Type divergence inconnu

    return round(take_profit_level, 2) if take_profit_level is not None else None

# === Fonction 7: Calculer Taille Position ===
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
                     !! VALEURS CRITIQUES À OBTENIR DE MT5 !!

    Returns:
        Le volume calculé et ajusté (arrondi selon volume_step), ou None si impossible.
    """
    try:
        if account_balance <= 0 or risk_percentage <= 0 or sl_level == entry_price:
            return None
        try:
            point = symbol_info['point']
            tick_value = symbol_info['trade_tick_value']
            tick_size = symbol_info['trade_tick_size']
            volume_min = symbol_info['volume_min']
            volume_max = symbol_info['volume_max']
            volume_step = symbol_info['volume_step']
        except KeyError as ke:
            print(f"DEBUG Size: Information symbole manquante: {ke}.")
            return None
        if None in [point, tick_value, tick_size, volume_min, volume_max, volume_step] or \
           tick_size <= 0 or point <= 0 or volume_step <= 0:
             print(f"DEBUG Size: Informations symbole numériques invalides.")
             return None

        risk_amount = account_balance * (risk_percentage / 100.0)
        sl_distance_price = abs(entry_price - sl_level)
        if sl_distance_price <= 0: return None
        sl_distance_points = sl_distance_price / point
        if sl_distance_points <= 0: return None

        point_value_per_lot = (tick_value / tick_size) * point
        if point_value_per_lot <= 0: return None

        volume_ideal = risk_amount / (sl_distance_points * point_value_per_lot)
        epsilon = 1e-9
        volume_adjusted = math.floor(volume_ideal / volume_step + epsilon) * volume_step
        volume_final = max(volume_min, volume_adjusted)
        volume_final = min(volume_max, volume_final)

        min_volume_risk = (sl_distance_points * point_value_per_lot) * volume_min
        if min_volume_risk > risk_amount + epsilon:
             print(f"ATTENTION Size: Vol min ({volume_min}) risque ({min_volume_risk:.2f}) > Risque autorisé ({risk_amount:.2f}).")
             # return None # Option plus sûre
             pass

        decimals = 0
        if '.' in str(volume_step):
             try:
                decimals = abs(math.log10(volume_step))
                decimals = int(decimals) if decimals == math.floor(decimals) else len(str(volume_step).split('.')[-1])
             except ValueError: # Log10(0) ou autre
                 print(f"DEBUG Size: Impossible de déterminer les décimales pour volume_step={volume_step}")
                 return None


        volume_final = round(volume_final, decimals)
        if volume_final < volume_min:
            volume_final = volume_min

        if volume_final <= 0: return None
        return volume_final

    except Exception as e:
        print(f"ERREUR inattendue dans calculate_position_size: {e}")
        traceback.print_exc()
        return None

# --- EXEMPLE: Simulation infos symbole (GARDER POUR TESTS OFFLINE) ---
# Rappel: Ces valeurs DOIVENT être mises à jour Lundi avec celles de MT5.
SYMBOL_INFO_US30_EUR_SIMULATED = {
    "name": "US30.cash",
    "currency_account": "EUR",
    "trade_contract_size": 1.0,    # Probablement 1
    "trade_tick_value": 0.09,      # !!! À VÉRIFIER !!! (Ex: 0.09 EUR pour 0.1 pt sur 1 lot ?)
    "trade_tick_size": 0.1,        # !!! À VÉRIFIER !!!
    "point": 1.0,                  # Probablement 1.0
    "volume_min": 0.01,            # !!! À VÉRIFIER !!!
    "volume_max": 100.0,           # !!! À VÉRIFIER !!!
    "volume_step": 0.01            # !!! À VÉRIFIER !!!
}
# --- FIN EXEMPLE SIMULATION ---

# ----- END OF FILE src/tools/signal_utils.py -----