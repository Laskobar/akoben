import pandas as pd
import numpy as np

def calculate_zigzag_pivots(df_ohlc: pd.DataFrame, length: int = 9):
    """
    Réplique la logique d'un indicateur ZigZag basé sur les plus hauts/bas
    sur une période donnée, similaire au script PineScript fourni.

    Args:
        df_ohlc: DataFrame pandas avec au moins les colonnes 'High', 'Low'.
                 L'index doit être temporel ou numérique séquentiel.
        length: La période de recherche pour le ZigZag (équivalent zigzag_len).

    Returns:
        Une liste de dictionnaires, chaque dictionnaire représentant un pivot
        confirmé avec les clés: 'index', 'price', 'type' ('high' ou 'low'),
        et 'status' ('H', 'L', 'HH', 'HL', 'LH', 'LL', 'EH', 'EL').
        Retourne une liste vide si pas assez de données.
    """
    if len(df_ohlc) < length:
        return [] # Pas assez de données pour calculer

    df = df_ohlc.copy()

    # --- Étape 1: Calculer les conditions de retournement potentiel ---
    # Note: .shift(1) est crucial pour comparer avec les N barres *précédentes*
    df['rolling_max'] = df['High'].rolling(length).max().shift(1)
    df['rolling_min'] = df['Low'].rolling(length).min().shift(1)

    # La bougie actuelle est-elle un plus haut/bas potentiel sur la période ?
    df['potential_up_turn'] = df['Low'] <= df['rolling_min']
    df['potential_down_turn'] = df['High'] >= df['rolling_max']

    # --- Étape 2: Déterminer la tendance (state machine) ---
    trend = np.zeros(len(df), dtype=int)
    # Initialisation : on peut supposer 1 ou essayer de deviner
    # Ici, on initialise à 0 et on détermine sur la première fenêtre valide
    initial_trend_determined = False
    for i in range(length, len(df)): # On commence après la première fenêtre complète
         if not initial_trend_determined:
             # Simple guess: if price rose more than fell in the first window
             if df['Close'].iloc[i] > df['Close'].iloc[i-length]:
                 trend[i-1] = 1 # Initial guess: Up
             else:
                 trend[i-1] = -1 # Initial guess: Down
             initial_trend_determined = True
             # Backfill trend pour les premiers points (nécessaire pour la suite)
             trend[:i-1] = trend[i-1]


         prev_trend = trend[i-1]
         current_trend = prev_trend

         if prev_trend == 1 and df['potential_up_turn'].iloc[i]:
             current_trend = -1
         elif prev_trend == -1 and df['potential_down_turn'].iloc[i]:
             current_trend = 1
         # else: garde le même trend

         trend[i] = current_trend

    df['trend'] = trend
    # Détecter quand le trend change effectivement
    # diff() = 0 (pas de changement), 2 (1 -> -1, high pivot), -2 (-1 -> 1, low pivot)
    df['trend_change'] = df['trend'].diff().fillna(0)

    # --- Étape 3: Identifier et stocker les pivots confirmés ---
    pivots = []
    last_low_idx = df.index[0]
    last_high_idx = df.index[0]
    low_pivots_prices = [] # Stocke juste les prix pour comparaison HH/LL
    high_pivots_prices = []

    for i in range(1, len(df)): # On itère pour trouver les changements
        current_idx = df.index[i]

        # Trend est passé de -1 à 1 => Confirmation d'un PIVOT BAS
        if df['trend_change'].iloc[i] == 2: # Correction: Si trend passe à 1, diff est 2 (-1 - (-1)) -> Non, c'est -2 (-1 -> 1)
            # Correction :  diff() = current - previous.  -1 - (1) = -2.  1 - (-1) = 2.
            pass # Erreur dans le commentaire, on continue avec la logique de diff()

        # Trend est passé de 1 à -1 => Confirmation d'un PIVOT HAUT
        if df['trend_change'].iloc[i] == -2: # 1 -> -1
            # Le VRAI pivot HAUT est le MAX(High) entre le dernier pivot BAS et maintenant
            lookback_start_idx = df.index.get_loc(last_low_idx)
            # Fenêtre incluant la bougie *précédente* celle du changement de trend
            lookback_window = df.iloc[lookback_start_idx : i] # Exclut la bougie i
            if lookback_window.empty: continue

            pivot_high_price = lookback_window['High'].max()
            # Trouver l'index (timestamp) de ce max dans le DataFrame original
            # Utilise idxmax() sur la fenêtre, puis récupère l'index original
            pivot_high_idx = lookback_window['High'].idxmax()


            # Déterminer le statut HH/LH
            status = 'H'
            if high_pivots_prices: # Si on a déjà eu des pivots hauts
                prev_high_price = high_pivots_prices[-1]
                if pivot_high_price > prev_high_price:
                    status = 'HH'
                elif pivot_high_price < prev_high_price:
                    status = 'LH'
                else:
                    status = 'EH' # Equal High

            pivot_info = {'index': pivot_high_idx, 'price': pivot_high_price, 'type': 'high', 'status': status}
            pivots.append(pivot_info)
            high_pivots_prices.append(pivot_high_price)
            last_high_idx = pivot_high_idx # Mémorise ce pivot haut pour la prochaine recherche de bas


        # Trend est passé de -1 à 1 => Confirmation d'un PIVOT BAS
        elif df['trend_change'].iloc[i] == 2: # -1 -> 1
             # Le VRAI pivot BAS est le MIN(Low) entre le dernier pivot HAUT et maintenant
            lookback_start_idx = df.index.get_loc(last_high_idx)
            lookback_window = df.iloc[lookback_start_idx : i] # Exclut la bougie i
            if lookback_window.empty: continue

            pivot_low_price = lookback_window['Low'].min()
            pivot_low_idx = lookback_window['Low'].idxmin()

            # Déterminer le statut LL/HL
            status = 'L'
            if low_pivots_prices:
                prev_low_price = low_pivots_prices[-1]
                if pivot_low_price < prev_low_price:
                    status = 'LL'
                elif pivot_low_price > prev_low_price:
                    status = 'HL'
                else:
                    status = 'EL' # Equal Low

            pivot_info = {'index': pivot_low_idx, 'price': pivot_low_price, 'type': 'low', 'status': status}
            pivots.append(pivot_info)
            low_pivots_prices.append(pivot_low_price)
            last_low_idx = pivot_low_idx # Mémorise ce pivot bas pour la prochaine recherche de haut

    # Tri final par index (normalement déjà trié, mais par sécurité)
    pivots.sort(key=lambda x: df.index.get_loc(x['index']))

    return pivots

# --- Exemple d'utilisation (à adapter avec vos données MT5) ---
# Supposons que 'mt5_data' est un DataFrame avec 'High', 'Low', 'Close'
# provenant de MT5, avec un index DatetimeIndex.

# zigzag_pivots = calculate_zigzag_pivots(mt5_data, length=9)
# print(zigzag_pivots)

# Afficher les derniers pivots pour vérification:
# if zigzag_pivots:
#     print("Dernier pivot:", zigzag_pivots[-1])
#     if len(zigzag_pivots) > 1:
#         print("Avant-dernier pivot:", zigzag_pivots[-2])