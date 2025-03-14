connector = MT5FileConnector()
if connector.connect():
    response = connector.send_command("PING")
    print(f"Réponse reçue : {response}")
else:
    print("Échec de la connexion à MT5.")