"""
MT5 Connector (Agent Fihavanana)
Équipe: Ubuntu (Support)
Rôle: Exécution des ordres de trading et connexion avec MetaTrader 5 via échange de fichiers
"""

import os
import time
import json
import codecs
import uuid
import pandas as pd
from datetime import datetime

class MT5FileConnector:
    """
    Agent Fihavanana - Connecteur pour MetaTrader 5 via fichiers
    Responsable de l'exécution des ordres et de la récupération des données de marché
    via des fichiers partagés entre Python et MT5
    """
    def __init__(self, config=None, llm_caller=None):
        self.config = config or {}
        self.llm_caller = llm_caller
        self.connected = False
        
        # Chemins des fichiers de communication (utilise le dossier Files de MT5)
        mt5_path = os.path.expanduser("~/.wine64/drive_c/Program Files/MetaTrader 5/MQL5/Files")
        self.request_file = os.path.join(mt5_path, "requests.txt")
        self.response_file = os.path.join(mt5_path, "responses.txt")
        
        # Configuration
        self.encoding = 'latin-1'  # Encoding compatible avec MT5/Windows
        self.timeout = self.config.get("timeout", 10)  # Timeout en secondes
        
        print("Agent Fihavanana (MT5 File Connector) initialisé")
        print(f"Fichier de requête: {self.request_file}")
        print(f"Fichier de réponse: {self.response_file}")
    
    def connect(self):
        """
        Établit une connexion avec le terminal MetaTrader 5 via des fichiers partagés
        
        Returns:
            bool: True si la connexion est réussie, False sinon
        """
        if self.connected:
            print("Déjà connecté à MetaTrader 5")
            return True
        
        try:
            # Vérifier si le fichier de réponse existe
            if os.path.exists(self.response_file):
                # Lire le fichier pour voir s'il contient "READY"
                with codecs.open(self.response_file, 'r', encoding=self.encoding, errors='ignore') as f:
                    content = f.read().strip()
                    print(f"Contenu du fichier de réponse: '{content}'")
                    if content == "READY":
                        print("MT5 est prêt (READY trouvé)")
                        self.connected = True
                        return True
            else:
                print("Fichier de réponse non trouvé - MT5 n'est peut-être pas en cours d'exécution")
                return False
        except Exception as e:
            print(f"Erreur lors de la connexion à MetaTrader 5: {e}")
            return False
    
    def send_command(self, command, timeout=None):
        """
        Envoie une commande à MT5 via des fichiers et attend une réponse
        
        Args:
            command: Commande à envoyer
            timeout: Délai d'attente en secondes (utilise la valeur par défaut si None)
            
        Returns:
            str: Réponse du serveur ou message d'erreur
        """
        if not self.connected and not self.connect():
            return "ERROR: NOT CONNECTED"
        
        timeout = timeout or self.timeout
        
        try:
            # Générer un ID unique pour cette commande
            command_id = str(uuid.uuid4())[:8]
            tagged_command = f"ID:{command_id}|{command}"
            print(f"Envoi de la commande: '{tagged_command}'")
            
            # S'assurer que le fichier de réponse est prêt pour une nouvelle commande
            with codecs.open(self.response_file, 'w', encoding=self.encoding) as f:
                f.write("READY")
            
            # Attendre un court instant pour que l'EA puisse lire "READY"
            time.sleep(0.5)
            
            # Écrire la commande avec son ID dans le fichier de requête
            with codecs.open(self.request_file, 'w', encoding=self.encoding) as f:
                f.write(tagged_command)
            print(f"Commande écrite dans {self.request_file}")
            
            # Attendre la réponse avec un timeout
            start_time = time.time()
            while time.time() - start_time < timeout:
                if os.path.exists(self.response_file):
                    with codecs.open(self.response_file, 'r', encoding=self.encoding, errors='ignore') as f:
                        response = f.read().strip()
                        
                        # Vérifier si la réponse contient l'ID et n'est pas READY
                        if response and response != "READY":
                            # Extraire l'ID et le contenu de la réponse
                            if response.startswith("ID:") and "|" in response:
                                parts = response.split("|", 1)
                                response_id = parts[0][3:]  # Ignorer "ID:" au début
                                content = parts[1]
                                
                                # Vérifier que l'ID correspond
                                if response_id == command_id:
                                    print(f"Réponse reçue avec ID correspondant: '{content}'")
                                    return content
                                else:
                                    print(f"ID de réponse non correspondant: attendu {command_id}, reçu {response_id}")
                            else:
                                # Compatibilité avec l'ancien format sans ID
                                print(f"Réponse reçue (ancien format): '{response}'")
                                return response
                time.sleep(0.1)
            
            print(f"Timeout atteint ({timeout}s) sans réponse")
            return "ERROR: TIMEOUT"
        except Exception as e:
            print(f"Erreur lors de l'envoi de la commande à MT5: {e}")
            return f"ERROR: {str(e)}"
    
    def get_account_info(self):
        """
        Récupère les informations du compte actuel
        
        Returns:
            dict: Informations du compte ou None en cas d'échec
        """
        response = self.send_command("ACCOUNT_INFO")
        
        # Analyse de la réponse
        if response.startswith("ACCOUNT_INFO"):
            info = {}
            parts = response.split()
            
            for part in parts[1:]:
                if "=" in part:
                    key, value = part.split("=")
                    try:
                        # Convertir en nombre si possible
                        if "." in value:
                            info[key] = float(value)
                        else:
                            info[key] = int(value)
                    except ValueError:
                        info[key] = value
            
            return info
        else:
            print(f"Erreur lors de la récupération des informations du compte: {response}")
            return None
    
    def get_current_price(self, symbol):
        """
        Récupère le prix actuel d'un instrument
        
        Args:
            symbol: Instrument financier (ex: "EURUSD")
            
        Returns:
            dict: Prix bid et ask ou None en cas d'échec
        """
        # Ajustement pour US30
        if symbol.lower() == "us30":
            symbol = "US30.cash"
        
        response = self.send_command(f"PRICE {symbol}")
        
        # Analyse de la réponse
        if response.startswith("PRICE"):
            parts = response.split()
            price_data = {}
            
            for part in parts:
                if part.startswith("BID="):
                    price_data["bid"] = float(part.split("=")[1])
                elif part.startswith("ASK="):
                    price_data["ask"] = float(part.split("=")[1])
            
            # Ajouter les champs supplémentaires
            price_data["symbol"] = symbol
            price_data["time"] = datetime.now()
            if "bid" in price_data and "ask" in price_data:
                price_data["spread"] = price_data["ask"] - price_data["bid"]
            
            return price_data
        else:
            print(f"Erreur lors de la récupération du prix pour {symbol}: {response}")
            return None
    
    def get_data(self, symbol, timeframe, count=500):
        """
        Récupère les données historiques de MT5
        
        Args:
            symbol: Instrument financier (ex: "EURUSD")
            timeframe: Temporalité (ex: "M1", "H1", "D1")
            count: Nombre de barres à récupérer
            
        Returns:
            pandas.DataFrame: Données historiques ou None en cas d'échec
        """
        # Ajustement pour US30
        if symbol.lower() == "us30":
            symbol = "US30.cash"
            
        response = self.send_command(f"DATA {symbol} {timeframe} {count}")
        
        if response.startswith("DATA"):
            try:
                # Extraire les données JSON
                json_start = response.find("[")
                if json_start != -1:
                    json_data = response[json_start:]
                    data = json.loads(json_data)
                    
                    # Convertir en DataFrame
                    df = pd.DataFrame(data)
                    
                    # Convertir la colonne time en datetime
                    if 'time' in df.columns:
                        df['time'] = pd.to_datetime(df['time'], unit='s')
                        df.set_index('time', inplace=True)
                    
                    return df
                else:
                    print("Données JSON non trouvées dans la réponse")
                    return None
            except Exception as e:
                print(f"Erreur lors du traitement des données: {e}")
                return None
        else:
            print(f"Erreur lors de la récupération des données pour {symbol} sur {timeframe}: {response}")
            return None
    
    def place_order(self, symbol, order_type, volume, price=0.0, sl=0.0, tp=0.0, comment="", magic=0):
        """
        Place un ordre de trading
        
        Args:
            symbol: Instrument financier (ex: "EURUSD")
            order_type: Type d'ordre ("BUY", "SELL")
            volume: Volume de l'ordre
            price: Prix d'entrée (0 pour ordre au marché)
            sl: Stop Loss (0 pour désactiver)
            tp: Take Profit (0 pour désactiver)
            comment: Commentaire sur l'ordre
            magic: Numéro magique pour identifier les ordres automatiques
            
        Returns:
            dict: Résultat de l'exécution de l'ordre ou None en cas d'échec
        """
        # Ajustement pour US30
        if symbol.lower() == "us30":
            symbol = "US30.cash"
            
        command = f"ORDER {symbol} {order_type} {volume} {price} {sl} {tp} {magic} {comment}"
        response = self.send_command(command)
        
        if response.startswith("ORDER_RESULT"):
            # Analyser la réponse
            result = {}
            parts = response.split()
            
            for part in parts[1:]:  # Skip "ORDER_RESULT"
                if "=" in part:
                    key, value = part.split("=")
                    try:
                        # Convertir en nombre si possible
                        if "." in value:
                            result[key] = float(value)
                        else:
                            result[key] = int(value)
                    except ValueError:
                        result[key] = value
            
            return result
        else:
            print(f"Erreur lors du placement de l'ordre: {response}")
            return None
    
    def close_position(self, position_id=None, symbol=None):
        """
        Ferme une position ouverte
        
        Args:
            position_id: ID de la position à fermer (facultatif)
            symbol: Symbole de la position à fermer (facultatif)
            
        Returns:
            bool: True si la fermeture est réussie, False sinon
        """
        # Ajustement pour US30
        if symbol and symbol.lower() == "us30":
            symbol = "US30.cash"
            
        if position_id is not None:
            command = f"CLOSE_POSITION ID={position_id}"
        elif symbol is not None:
            command = f"CLOSE_POSITION SYMBOL={symbol}"
        else:
            print("Veuillez spécifier soit l'ID de la position, soit le symbole")
            return False
        
        response = self.send_command(command)
        
        if response == "POSITION_CLOSED":
            return True
        else:
            print(f"Erreur lors de la fermeture de la position: {response}")
            return False
    
    def close_all_positions(self):
        """
        Ferme toutes les positions ouvertes
        
        Returns:
            bool: True si toutes les fermetures sont réussies, False sinon
        """
        response = self.send_command("CLOSE_ALL_POSITIONS")
        
        if response.startswith("POSITIONS_CLOSED"):
            try:
                # Extraire le nombre de positions fermées
                count = int(response.split("=")[1])
                return True
            except:
                return True
        else:
            print(f"Erreur lors de la fermeture des positions: {response}")
            return False
    
    def get_positions(self, symbol=None):
        """
        Récupère les positions ouvertes
        
        Args:
            symbol: Filtrer par symbole (facultatif)
            
        Returns:
            list: Liste des positions ouvertes ou None en cas d'échec
        """
        # Ajustement pour US30
        if symbol and symbol.lower() == "us30":
            symbol = "US30.cash"
            
        command = "POSITIONS"
        if symbol:
            command += f" {symbol}"
            
        response = self.send_command(command)
        
        if response.startswith("POSITIONS"):
            try:
                # Extraire les données JSON
                json_start = response.find("[")
                if json_start != -1:
                    json_data = response[json_start:]
                    positions = json.loads(json_data)
                    return positions
                else:
                    # Pas de positions ou format différent
                    if "EMPTY" in response:
                        return []
                    print("Données JSON non trouvées dans la réponse")
                    return None
            except Exception as e:
                print(f"Erreur lors du traitement des positions: {e}")
                return None
        else:
            print(f"Erreur lors de la récupération des positions: {response}")
            return None
    
    def calculate_position_size(self, symbol, stop_loss_pips, risk_percent):
        """
        Calcule la taille de position optimale basée sur le risque
        
        Args:
            symbol: Instrument financier
            stop_loss_pips: Distance du stop loss en pips
            risk_percent: Pourcentage du compte à risquer (1 = 1%)
            
        Returns:
            float: Taille de position recommandée ou None en cas d'échec
        """
        # Ajustement pour US30
        if symbol.lower() == "us30":
            symbol = "US30.cash"
            
        command = f"POSITION_SIZE {symbol} {stop_loss_pips} {risk_percent}"
        response = self.send_command(command)
        
        if response.startswith("POSITION_SIZE"):
            try:
                size = float(response.split("=")[1])
                return size
            except:
                print(f"Erreur lors de l'analyse de la réponse: {response}")
                return None
        else:
            print(f"Erreur lors du calcul de la taille de position: {response}")
            return None
    
    def get_history_orders(self, days=7, symbol=None):
        """
        Récupère l'historique des ordres
        
        Args:
            days: Nombre de jours à récupérer
            symbol: Filtrer par symbole (facultatif)
            
        Returns:
            list: Liste des ordres historiques ou None en cas d'échec
        """
        # Ajustement pour US30
        if symbol and symbol.lower() == "us30":
            symbol = "US30.cash"
            
        command = f"HISTORY_ORDERS {days}"
        if symbol:
            command += f" {symbol}"
            
        response = self.send_command(command)
        
        if response.startswith("HISTORY_ORDERS"):
            try:
                # Extraire les données JSON
                json_start = response.find("[")
                if json_start != -1:
                    json_data = response[json_start:]
                    orders = json.loads(json_data)
                    return orders
                else:
                    # Pas d'ordres ou format différent
                    if "EMPTY" in response:
                        return []
                    print("Données JSON non trouvées dans la réponse")
                    return None
            except Exception as e:
                print(f"Erreur lors du traitement de l'historique des ordres: {e}")
                return None
        else:
            print(f"Erreur lors de la récupération de l'historique des ordres: {response}")
            return None
    
    def calculate_performance_metrics(self, days=30, symbol=None):
        """
        Calcule les métriques de performance du trading
        
        Args:
            days: Nombre de jours à analyser
            symbol: Filtrer par symbole (facultatif)
            
        Returns:
            dict: Métriques de performance ou None en cas d'échec
        """
        # Ajustement pour US30
        if symbol and symbol.lower() == "us30":
            symbol = "US30.cash"
            
        command = f"PERFORMANCE {days}"
        if symbol:
            command += f" {symbol}"
            
        response = self.send_command(command)
        
        if response.startswith("PERFORMANCE"):
            try:
                # Extraire les données JSON
                json_start = response.find("{")
                if json_start != -1:
                    json_data = response[json_start:]
                    metrics = json.loads(json_data)
                    return metrics
                else:
                    print("Données JSON non trouvées dans la réponse")
                    return None
            except Exception as e:
                print(f"Erreur lors du traitement des métriques de performance: {e}")
                return None
        else:
            print(f"Erreur lors du calcul des métriques de performance: {response}")
            return None
    
    def disconnect(self):
        """
        Déconnecte du terminal MT5
        """
        if self.connected:
            self.connected = False
            print("Déconnecté de MetaTrader 5")
        
    def __del__(self):
        """
        Destructeur pour assurer la déconnexion
        """
        self.disconnect()