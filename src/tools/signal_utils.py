# ----- START OF FILE src/tools/signal_utils.py (Version "Précédente" + Règle Anti-Doji) -----
import pandas as pd
import numpy as np
import pandas_ta as ta # Assurez-vous que pandas-ta est installé
import math
import traceback # Pour le débogage des erreurs

# === Fonctions d'Analyse (Versions initiales ou peu modifiées) ===
def calculate_zigzag_pivots(df_ohlc: pd.DataFrame, length: int = 9):
    # ... (Code de calculate_zigzag_pivots comme avant) ...
    if len(df_ohlc) < length: return []
    df = df_ohlc.sort_index(ascending=True).copy()
    df['rolling_max'] = df['High'].rolling(length).max().shift(1)
    df['rolling_min'] = df['Low'].rolling(length).min().shift(1)
    df['potential_up_turn'] = df['Low'] <= df['rolling_min']
    df['potential_down_turn'] = df['High'] >= df['rolling_max']
    trend = np.zeros(len(df), dtype=int)
    initial_trend_determined = False
    for i in range(length, len(df)):
        if not initial_trend_determined and i > 0:
            if df['Close'].iloc[i-1] > df['Close'].iloc[i-length if i-length >= 0 else 0]: trend[i-1] = 1
            else: trend[i-1] = -1
            initial_trend_determined = True; trend[:i-1] = trend[i-1]
        if i > 0:
            prev_trend = trend[i-1]; current_trend = prev_trend
            if prev_trend == 1 and df['potential_up_turn'].iloc[i]: current_trend = -1
            elif prev_trend == -1 and df['potential_down_turn'].iloc[i]: current_trend = 1
            trend[i] = current_trend
    df['trend'] = trend; df['trend_change'] = df['trend'].diff().fillna(0)
    pivots = []; last_confirmed_low_idx = df.index[0]; last_confirmed_high_idx = df.index[0]
    low_pivots_prices = []; high_pivots_prices = []
    for i in range(1, len(df)):
        change = df['trend_change'].iloc[i]
        if change == -2: # High Pivot
            lookback_start_loc = df.index.get_loc(last_confirmed_low_idx)
            lookback_window = df.iloc[lookback_start_loc : i]
            if lookback_window.empty: continue
            pivot_high_price = lookback_window['High'].max(); pivot_high_idx = lookback_window['High'].idxmax()
            if pivots and pivots[-1]['index'] == pivot_high_idx: continue
            if pivot_high_idx <= last_confirmed_low_idx: continue
            status = 'H'
            if high_pivots_prices:
                prev_high_price = high_pivots_prices[-1]
                if pivot_high_price > prev_high_price: status = 'HH'
                elif pivot_high_price < prev_high_price: status = 'LH'
                else: status = 'EH'
            pivot_info = {'index': pivot_high_idx, 'price': pivot_high_price, 'type': 'high', 'status': status}
            pivots.append(pivot_info); high_pivots_prices.append(pivot_high_price); last_confirmed_high_idx = pivot_high_idx
        elif change == 2: # Low Pivot
            lookback_start_loc = df.index.get_loc(last_confirmed_high_idx)
            lookback_window = df.iloc[lookback_start_loc : i]
            if lookback_window.empty: continue
            pivot_low_price = lookback_window['Low'].min(); pivot_low_idx = lookback_window['Low'].idxmin()
            if pivots and pivots[-1]['index'] == pivot_low_idx: continue
            if pivot_low_idx <= last_confirmed_high_idx: continue
            status = 'L'
            if low_pivots_prices:
                prev_low_price = low_pivots_prices[-1]
                if pivot_low_price < prev_low_price: status = 'LL'
                elif pivot_low_price > prev_low_price: status = 'HL'
                else: status = 'EL'
            pivot_info = {'index': pivot_low_idx, 'price': pivot_low_price, 'type': 'low', 'status': status}
            pivots.append(pivot_info); low_pivots_prices.append(pivot_low_price); last_confirmed_low_idx = pivot_low_idx
    pivots.sort(key=lambda x: df.index.get_loc(x['index']))
    return pivots

def find_interest_zone(df_ohlc_sma: pd.DataFrame, pivots: list, new_pivot_index_in_list: int) -> dict | None:
    # ... (Code de find_interest_zone comme avant) ...
     if new_pivot_index_in_list < 1 or new_pivot_index_in_list >= len(pivots): return None
     new_pivot = pivots[new_pivot_index_in_list]; prev_pivot = pivots[new_pivot_index_in_list - 1]
     if new_pivot['type'] == prev_pivot['type']: return None
     if new_pivot['type'] == 'high': # Cas Achat
         preceding_low_pivot = prev_pivot
         if preceding_low_pivot['type'] != 'low': return None
         try:
             search_start_loc = df_ohlc_sma.index.get_loc(preceding_low_pivot['index']) + 1
             search_end_loc = df_ohlc_sma.index.get_loc(new_pivot['index'])
             if search_start_loc > search_end_loc: return None
         except KeyError: return None
         search_df = df_ohlc_sma.iloc[search_start_loc : search_end_loc + 1]; breakout_candle_index = None
         if search_df.empty: return None
         for idx, row in search_df.iterrows():
             if not pd.isna(row['SMA20']) and row['Close'] > row['SMA20']: breakout_candle_index = idx; break
         if breakout_candle_index is None: return None
         zone_start_price = df_ohlc_sma.loc[breakout_candle_index, 'High']; zone_end_price = preceding_low_pivot['price']
         return {'start_price': zone_start_price, 'end_price': zone_end_price, 'direction': 'bullish', 'breakout_candle_index': breakout_candle_index, 'preceding_pivot_index': preceding_low_pivot['index']}
     elif new_pivot['type'] == 'low': # Cas Vente
         preceding_high_pivot = prev_pivot
         if preceding_high_pivot['type'] != 'high': return None
         try:
             search_start_loc = df_ohlc_sma.index.get_loc(preceding_high_pivot['index']) + 1
             search_end_loc = df_ohlc_sma.index.get_loc(new_pivot['index'])
             if search_start_loc > search_end_loc: return None
         except KeyError: return None
         search_df = df_ohlc_sma.iloc[search_start_loc : search_end_loc + 1]; breakout_candle_index = None
         if search_df.empty: return None
         for idx, row in search_df.iterrows():
              if not pd.isna(row['SMA20']) and row['Close'] < row['SMA20']: breakout_candle_index = idx; break
         if breakout_candle_index is None: return None
         zone_start_price = df_ohlc_sma.loc[breakout_candle_index, 'Low']; zone_end_price = preceding_high_pivot['price']
         return {'start_price': zone_start_price, 'end_price': zone_end_price, 'direction': 'bearish', 'breakout_candle_index': breakout_candle_index, 'preceding_pivot_index': preceding_high_pivot['index']}
     return None

# === Fonction 3: Vérifier Divergence dans Zone (Version originale AVANT revue) ===
def check_divergence_in_zone(current_low: float,
                              current_high: float,
                              current_rsi: float,
                              zone_info: dict,
                              last_relevant_pivot: dict,
                              rsi_at_last_pivot: float) -> str | None:
    """
    Vérifie si le prix actuel est dans la zone d'intérêt et s'il y a une
    divergence RSI pertinente par rapport au dernier pivot ZigZag.
    (Version SANS tolérances RSI/Prix explicites ajoutées lors de la revue)

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
    # Utiliser la tolérance de prix relative initiale
    tolerance = zone_size * 0.05 if zone_size > 0 else 0.00001

    # --- Setup ACHAT (zone bullish) ---
    if direction == 'bullish':
        if last_relevant_pivot['type'] != 'low': return None
        # Prix (Low) doit être dans la zone
        if not (zone_lower <= current_low <= zone_upper): return None

        # Div Bull Régulière: LL < L mais RSI(LL) > RSI(L) (Comparaison stricte)
        if current_low < pivot_price - tolerance and current_rsi > rsi_at_last_pivot:
             return "BULL_REGULAR"
        # Div Bull Continuation: HL > L mais RSI(HL) < RSI(L) (Comparaison stricte)
        if current_low > pivot_price + tolerance and current_rsi < rsi_at_last_pivot:
             return "BULL_CONTINUATION"

    # --- Setup VENTE (zone bearish) ---
    elif direction == 'bearish':
        if last_relevant_pivot['type'] != 'high': return None
        # Prix (High) doit être dans la zone
        if not (zone_lower <= current_high <= zone_upper): return None

        # Div Bear Régulière: HH > H mais RSI(HH) < RSI(H) (Comparaison stricte)
        if current_high > pivot_price + tolerance and current_rsi < rsi_at_last_pivot:
            return "BEAR_REGULAR"
        # Div Bear Continuation: LH < H mais RSI(LH) > RSI(H) (Comparaison stricte)
        if current_high < pivot_price - tolerance and current_rsi > rsi_at_last_pivot:
            return "BEAR_CONTINUATION"

    return None
# === Fin Fonction 3 (Version originale) ===

# === Fonctions d'Exécution (Versions "brutes" AVANT revue/nettoyage MAIS AVEC règle anti-doji réactivée) ===

# --- Version detect_engulfing_pattern AVEC règle anti-doji ---
def detect_engulfing_pattern(df_ohlc: pd.DataFrame, current_candle_index: pd.Timestamp, direction: str) -> bool:
    try:
        current_loc = df_ohlc.index.get_loc(current_candle_index)
        if current_loc < 1: return False
        prev_loc = current_loc - 1 # Correction ici, on utilise bien current_loc - 1
        current_candle = df_ohlc.iloc[current_loc]
        prev_candle = df_ohlc.iloc[prev_loc] # Utilisation de prev_loc
        if pd.isna(current_candle['Open']) or pd.isna(current_candle['Close']) or \
           pd.isna(prev_candle['Open']) or pd.isna(prev_candle['Close']):
            return False

        # --- MODIFICATION ICI : Règle Anti-Doji ---
        prev_body = abs(prev_candle['Close'] - prev_candle['Open'])
        # Utiliser une petite tolérance (ex: 0.01% du prix)
        body_tolerance = prev_candle['Close'] * 0.0001 if prev_candle['Close'] > 0 else 0.01
        if prev_body < body_tolerance: return False # Ne pas englober si corps précédent trop petit
        # --- FIN MODIFICATION ---

        if direction == 'bullish':
            is_current_bullish = current_candle['Close'] > current_candle['Open']
            is_previous_bearish = prev_candle['Close'] < prev_candle['Open']
            does_current_engulf_previous = (current_candle['Open'] < prev_candle['Close']) and \
                                           (current_candle['Close'] > prev_candle['Open'])
            if is_current_bullish and is_previous_bearish and does_current_engulf_previous: return True
        elif direction == 'bearish':
            is_current_bearish = current_candle['Close'] < current_candle['Open']
            is_previous_bullish = prev_candle['Close'] > prev_candle['Open']
            does_current_engulf_previous = (current_candle['Open'] > prev_candle['Close']) and \
                                           (current_candle['Close'] < prev_candle['Open'])
            if is_current_bearish and is_previous_bullish and does_current_engulf_previous: return True
    except KeyError: return False
    except IndexError: return False
    except Exception as e: print(f"ERREUR inattendue dans detect_engulfing_pattern pour {current_candle_index}: {e}"); return False
    return False

# --- Version corrigée (plage) calculate_stop_loss ---
def calculate_stop_loss(df_ohlc: pd.DataFrame, confirmation_candle_index: pd.Timestamp, direction: str, buffer_points: float = 5.0, max_lookback_candles: int = 10) -> float | None:
    # ... (Code inchangé par rapport à la version précédente "qui marche") ...
    try:
        confirmation_loc = df_ohlc.index.get_loc(confirmation_candle_index)
        if confirmation_loc < 1: return None
        start_range_loc = -1
        search_start_loc = confirmation_loc - 1
        for i in range(search_start_loc, max(search_start_loc - max_lookback_candles, -1), -1):
            candle = df_ohlc.iloc[i]
            if pd.isna(candle['Open']) or pd.isna(candle['Close']): continue
            is_bullish = candle['Close'] > candle['Open']
            is_bearish = candle['Close'] < candle['Open']
            if direction == 'bullish' and is_bearish: start_range_loc = i; break
            elif direction == 'bearish' and is_bullish: start_range_loc = i; break
        if start_range_loc == -1: start_range_loc = confirmation_loc - 1
        sl_range_df = df_ohlc.iloc[start_range_loc : confirmation_loc + 1]
        if sl_range_df.empty: return None
        if sl_range_df[['Low', 'High']].isnull().values.any(): return None
        stop_loss_level = None
        if direction == 'bullish':
            low_point = sl_range_df['Low'].min()
            stop_loss_level = low_point - buffer_points
        elif direction == 'bearish':
            high_point = sl_range_df['High'].max()
            stop_loss_level = high_point + buffer_points
        return round(stop_loss_level, 2) if stop_loss_level is not None else None
    except KeyError: return None
    except Exception as e: print(f"ERREUR inattendue dans calculate_stop_loss pour {confirmation_candle_index}: {e}"); traceback.print_exc(); return None


# --- Version corrigée (double logique) calculate_take_profit_v1 ---
def calculate_take_profit_v1(pivots: list, confirmation_candle_index: pd.Timestamp, direction: str, divergence_type: str | None, zone_info: dict | None, df_ohlc: pd.DataFrame) -> float | None:
     # ... (Code inchangé par rapport à la version précédente "qui marche") ...
    if divergence_type is None: print(f"DEBUG TP {direction}: Type de divergence non fourni."); return None
    take_profit_level = None
    if "CONTINUATION" in divergence_type:
        target_pivot = None; target_pivot_type = 'high' if direction == 'bullish' else 'low'
        for pivot in reversed(pivots):
            pivot_index = pivot.get('index'); pivot_type = pivot.get('type'); pivot_price = pivot.get('price')
            if pivot_index is None or pivot_type is None or pivot_price is None: continue
            if pivot_index >= confirmation_candle_index: continue
            if pivot_type == target_pivot_type: target_pivot = pivot; break
        if target_pivot: take_profit_level = target_pivot['price']
        else: print(f"DEBUG TP {direction} Continuation: Aucun pivot {target_pivot_type} trouvé avant {confirmation_candle_index}."); return None
    elif "REGULAR" in divergence_type:
        if zone_info is None: print(f"DEBUG TP {direction} Régulière: zone_info manquant."); return None
        if df_ohlc is None: print(f"DEBUG TP {direction} Régulière: df_ohlc manquant."); return None
        take_profit_level = zone_info.get('start_price')
        if take_profit_level is None: print(f"DEBUG TP {direction} Régulière: Impossible de récupérer 'start_price' depuis zone_info."); return None
    else: print(f"DEBUG TP {direction}: Type de divergence inconnu ou non géré: {divergence_type}"); return None
    return round(take_profit_level, 2) if take_profit_level is not None else None

# --- Version initiale calculate_position_size ---
def calculate_position_size(account_balance: float, risk_percentage: float, sl_level: float, entry_price: float, symbol_info: dict) -> float | None:
    # ... (Code inchangé par rapport à la version précédente "qui marche") ...
    try:
        if account_balance <= 0 or risk_percentage <= 0 or sl_level == entry_price: return None
        point = symbol_info.get('point'); tick_value = symbol_info.get('trade_tick_value'); tick_size = symbol_info.get('trade_tick_size')
        volume_min = symbol_info.get('volume_min'); volume_max = symbol_info.get('volume_max'); volume_step = symbol_info.get('volume_step')
        if None in [point, tick_value, tick_size, volume_min, volume_max, volume_step] or tick_size == 0 or point == 0: return None
        if volume_step <= 0: return None
        risk_amount = account_balance * (risk_percentage / 100.0)
        sl_distance_points = abs(entry_price - sl_level) / point
        if sl_distance_points <= 0: return None
        point_value_per_lot = (tick_value / tick_size) * point
        if point_value_per_lot <= 0: return None
        volume_ideal = risk_amount / (sl_distance_points * point_value_per_lot)
        volume_adjusted = math.floor(volume_ideal / volume_step) * volume_step
        volume_final = max(volume_min, volume_adjusted)
        volume_final = min(volume_max, volume_final)
        min_volume_risk = (sl_distance_points * point_value_per_lot) * volume_min
        if min_volume_risk > risk_amount and volume_final == volume_min: print(f"ATTENTION Size: Volume minimum ({volume_min}) dépasse le risque autorisé ({risk_amount:.2f} > {min_volume_risk:.2f}). Trade trop risqué."); pass
        decimals = 0
        if '.' in str(volume_step): decimals = len(str(volume_step).split('.')[-1])
        volume_final = round(volume_final, decimals)
        if volume_final < volume_min : return None
        return volume_final
    except Exception as e: print(f"ERREUR inattendue dans calculate_position_size: {e}"); traceback.print_exc(); return None


# --- EXEMPLE: Simulation infos symbole ---
SYMBOL_INFO_US30_EUR_SIMULATED = {
    "name": "US30.cash", "currency_account": "EUR", "trade_contract_size": 1.0,
    "trade_tick_value": 0.09,      # !!! À VÉRIFIER !!!
    "trade_tick_size": 0.1,        # !!! À VÉRIFIER !!!
    "point": 1.0,                  # Probablement 1.0
    "volume_min": 0.01,            # !!! À VÉRIFIER !!!
    "volume_max": 100.0,           # !!! À VÉRIFIER !!!
    "volume_step": 0.01            # !!! À VÉRIFIER !!!
}
# --- FIN EXEMPLE SIMULATION ---

# ----- END OF FILE src/tools/signal_utils.py -----