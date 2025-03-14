from src.agents.execution.mt5_connector import MT5FileConnector

# Réinitialiser le fichier de réponse
import os
import codecs
mt5_path = os.path.expanduser("~/.wine/drive_c/Program Files/MetaTrader 5/MQL5/Files")
response_file = os.path.join(mt5_path, "responses.txt")
with codecs.open(response_file, 'w', encoding='latin-1') as f:
    f.write("READY")

# Créer le connecteur
mt5 = MT5FileConnector()
if mt5.connect():
    print("Connecté à MT5 avec succès")
    
    # Placer un ordre d'achat
    result = mt5.place_order(
        symbol="US30",
        order_type="BUY",
        volume=0.1,
        price=0,  # 0 signifie au prix du marché
        sl=0,     # pas de stop loss
        tp=0,     # pas de take profit
        comment="Test Order Akoben"
    )
    
    print(f"Résultat de l'ordre: {result}")
    
    # Vérifier les positions
    positions = mt5.get_positions()
    print(f"Positions après ordre: {positions}")
else:
    print("Échec de connexion à MT5")