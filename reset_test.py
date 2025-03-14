from src.agents.execution.mt5_connector import MT5FileConnector
import time

print("Initialisation du connecteur MT5...")
connector = MT5FileConnector()

print("Forçage de la réinitialisation des communications...")
connector.force_reset_communication()
time.sleep(3)  # Attendre que l'EA détecte les changements

print("Tentative de connexion...")
if connector.connect():
    print("Connexion réussie!")
    
    # Récupérer le prix actuel
    print("Récupération du prix US30...")
    price_info = connector.get_current_price("US30")
    if price_info:
        print(f"Prix récupéré avec succès: {price_info}")
    else:
        print("Échec de récupération du prix")
else:
    print("Échec de connexion à MT5")