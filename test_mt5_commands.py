import os
import codecs
import time
from src.agents.execution.mt5_connector import MT5FileConnector

# Réinitialiser le fichier de réponse avant de commencer
mt5_path = os.path.expanduser("~/.wine/drive_c/Program Files/MetaTrader 5/MQL5/Files")
response_file = os.path.join(mt5_path, "responses.txt")

# Écrire READY dans le fichier de réponse
with codecs.open(response_file, 'w', encoding='latin-1') as f:
    f.write("READY")
print("Fichier de réponse réinitialisé à 'READY'")

# Attendre un moment pour que l'EA détecte le changement
time.sleep(1)

# Créer une instance du connecteur
connector = MT5FileConnector()

# Test de connexion
if connector.connect():
    print("Connexion réussie!")

    # Test 1: Informations du compte
    print("\n--- Test: Informations du compte ---")
    account_info = connector.get_account_info()
    print(f"Informations du compte: {account_info}")

    # Test 2: Prix actuel
    print("\n--- Test: Prix actuel ---")
    price = connector.get_current_price("US30")
    print(f"Prix US30: {price}")

    # Test 3: Positions ouvertes
    print("\n--- Test: Positions ouvertes ---")
    positions = connector.get_positions()
    print(f"Positions: {positions}")

    # Test 4: Historique des ordres (7 derniers jours)
    print("\n--- Test: Historique des ordres ---")
    history = connector.get_history_orders(7)
    print(f"Historique des ordres: {history}")

    # Test 5: Métriques de performance
    print("\n--- Test: Métriques de performance ---")
    metrics = connector.calculate_performance_metrics(30)
    print(f"Métriques de performance: {metrics}")

    # Test 6: Calcul de taille de position
    print("\n--- Test: Calcul de taille de position ---")
    size = connector.calculate_position_size("US30", 100, 1) # 100 pips, 1% de risque
    print(f"Taille de position recommandée: {size}")

    connector.disconnect()
    print("\nTests terminés avec succès")
else:
    print("Échec de la connexion à MT5")