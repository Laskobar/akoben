import os
import time
import codecs
import uuid

# Chemins des fichiers
mt5_path = os.path.expanduser("~/.wine/drive_c/Program Files/MetaTrader 5/MQL5/Files")
request_file = os.path.join(mt5_path, "requests.txt")
response_file = os.path.join(mt5_path, "responses.txt")
encoding = 'latin-1'

# Nettoyer le fichier de réponse
with codecs.open(response_file, 'w', encoding=encoding) as f:
    f.write("READY")

# Attendre que l'EA soit prêt
time.sleep(2)

# Envoyer une commande avec ID
command_id = str(uuid.uuid4())[:8]
print(f"ID de commande généré: {command_id}")
command = f"ID:{command_id}|PING"

with codecs.open(request_file, 'w', encoding=encoding) as f:
    f.write(command)
print(f"Commande envoyée: '{command}'")

# Attendre et lire la réponse
print("Attente de la réponse...")
start_time = time.time()
while time.time() - start_time < 10:
    if os.path.exists(response_file):
        with codecs.open(response_file, 'r', encoding=encoding, errors='ignore') as f:
            response = f.read().strip()
            if response and response != "READY":
                print(f"Réponse complète reçue: '{response}'")
                
                # Vérifier si la réponse contient l'ID
                if response.startswith("ID:") and "|" in response:
                    parts = response.split("|", 1)
                    response_id = parts[0][3:]
                    content = parts[1]
                    print(f"ID reçu: {response_id}, Contenu: {content}")
                    
                    if response_id == command_id:
                        print("✅ L'ID correspond: l'EA avec ID fonctionne correctement!")
                    else:
                        print("❌ L'ID ne correspond pas: l'EA avec ID n'est pas correctement chargé.")
                else:
                    print("❌ Format de réponse incorrect: l'EA avec ID n'est pas correctement chargé.")
                break
    time.sleep(0.5)
else:
    print("❌ Timeout: aucune réponse reçue.")