import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz # Nécessaire pour gérer les fuseaux horaires

# --- Importer la fonction ZigZag depuis son emplacement ---
# Ajustez le chemin si nécessaire selon votre structure
try:
    from src.tools.signal_utils import calculate_zigzag_pivots
    print("Fonction calculate_zigzag_pivots importée avec succès.")
except ImportError:
    print("ERREUR: Impossible d'importer calculate_zigzag_pivots.")
    print("Vérifiez le chemin et l'emplacement du fichier signal_utils.py")
    exit()

# --- Configuration du Test ---
MT5_LOGIN = 1510385169         # <<< REMPLACEZ par votre login MT5
MT5_PASSWORD = "?9E15!PHbAe" # <<< REMPLACEZ par votre mot de passe MT5
MT5_SERVER = "FTMO-Demo" # <<< REMPLACEZ par le nom de votre serveur MT5
MT5_PATH = "C:/Program Files/MetaTrader 5/terminal64.exe" # <<< REMPLACEZ si MT5 n'est pas à l'emplacement par défaut

SYMBOL = "US30.cash"        # Instrument à tester
TIMEFRAME = mt5.TIMEFRAME_M1 # Timeframe M1
ZIGZAG_LENGTH = 9      # Longueur du ZigZag à tester

# --- Définir la période de test ---
# !!! IMPORTANT: Choisissez une période où vous voyez clairement
# plusieurs pivots ZigZag sur TradingView pour comparer !!!
# Utilisez le fuseau horaire UTC pour la requête MT5
timezone = pytz.utc
# Exemple: Tester sur une journée spécifique (ajustez les dates/heures)
# Attention aux heures d'ouverture/fermeture du marché US30
start_time_utc = datetime(2025, 3, 28, 5, 0, 0, tzinfo=timezone) # UTC ~ Heure de début pour l'image fournie?
end_time_utc = datetime(2025, 3, 28, 10, 0, 0, tzinfo=timezone) # UTC ~ Heure de fin pour l'image fournie?

print(f"Configuration du test:")
print(f"Symbol: {SYMBOL}, Timeframe: M1, ZigZag Length: {ZIGZAG_LENGTH}")
print(f"Période UTC: de {start_time_utc} à {end_time_utc}")

# --- Connexion à MetaTrader 5 ---
print("\nInitialisation de MetaTrader 5...")
if not mt5.initialize(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER, path=MT5_PATH):
    print(f"initialize() a échoué, code d'erreur = {mt5.last_error()}")
    mt5.shutdown()
    exit()
print("Connecté à MetaTrader 5 avec succès.")

# --- Récupération des données historiques ---
print(f"Récupération des données pour {SYMBOL}...")
rates = mt5.copy_rates_range(SYMBOL, TIMEFRAME, start_time_utc, end_time_utc)

# --- Arrêt de MT5 (important) ---
mt5.shutdown()
print("Connexion à MetaTrader 5 terminée.")

if rates is None:
    print("Aucune donnée récupérée pour la période spécifiée.")
    exit()
if len(rates) == 0:
    print("Aucune donnée récupérée (longueur 0). Vérifiez la période et le symbole.")
    exit()

print(f"{len(rates)} barres M1 récupérées.")

# --- Conversion en DataFrame Pandas ---
rates_df = pd.DataFrame(rates)
# Convertir le temps en DatetimeIndex (MT5 donne des timestamps Unix)
rates_df['time'] = pd.to_datetime(rates_df['time'], unit='s', utc=True)
rates_df.set_index('time', inplace=True)

# Renommer les colonnes pour correspondre à ce que la fonction attend (si nécessaire)
# MT5 utilise 'open', 'high', 'low', 'close'. Notre fonction utilise 'High', 'Low'.
# Assurons la bonne casse :
rates_df.rename(columns={'high': 'High', 'low': 'Low', 'close': 'Close', 'open': 'Open'}, inplace=True)

print("DataFrame créé avec les colonnes:", rates_df.columns.tolist())
print("Index du DataFrame:", rates_df.index.name, "Type:", type(rates_df.index))
print("Premières lignes du DataFrame:")
print(rates_df.head())
print("Dernières lignes du DataFrame:")
print(rates_df.tail())


# --- Exécution de la fonction ZigZag ---
print(f"\nCalcul des pivots ZigZag (length={ZIGZAG_LENGTH})...")
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
    for pivot in zigzag_pivots:
        # Formatter le timestamp pour lisibilité (optionnel: convertir en heure locale si besoin)
        # pivot_time_local = pivot['index'].tz_convert('Europe/Paris') # Exemple
        pivot_time_utc = pivot['index']
        print(f"- Time (UTC): {pivot_time_utc}, Price: {pivot['price']:.5f}, Type: {pivot['type']}, Status: {pivot['status']}")

print("\n--- ACTION REQUISE ---")
print("1. Ouvrez TradingView pour le symbole", SYMBOL, "en M1.")
print("2. Affichez votre indicateur ZigZag (length=", ZIGZAG_LENGTH, ").")
print("3. Comparez MANUELLEMENT les pivots affichés ci-dessus avec ceux visibles sur TradingView pour la période UTC:", start_time_utc, "à", end_time_utc)
print("4. Vérifiez :")
print("   - Le nombre de pivots correspond-il ?")
print("   - Les timestamps (Date/Heure UTC) des pivots correspondent-ils ? (Attention aux fuseaux horaires !)")
print("   - Les prix des pivots correspondent-ils ? (De petites différences dues aux flux de données sont possibles)")
print("   - Le type (high/low) et le statut (HH/LL/...) correspondent-ils ?")
print("5. Faites-moi part des résultats de votre comparaison (succès, échec, différences observées).")
print("----------------------")