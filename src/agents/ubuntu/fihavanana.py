"""
Agent Fihavanana - Agent d'exécution pour l'équipe Ubuntu
"""

import os
import time
import json
from src.anansi.agent_framework.autonomous_agent import AutonomousAgent
from src.agents.execution.mt5_connector import MT5FileConnector

class Fihavanana(AutonomousAgent):
    """
    Agent Fihavanana - Responsable de l'exécution des ordres de trading
    et de la communication avec MetaTrader 5.
    
    Fait partie de l'équipe Ubuntu (Support).
    """
    
    def __init__(self, name="fihavanana", config=None, anansi_core=None):
        super().__init__(name, config, anansi_core)
        
        # Initialiser le connecteur MT5
        self.mt5_connector = MT5FileConnector(
            config=config.get("mt5_config", {}),
            llm_caller=lambda prompt: self.anansi_core.call_llm(prompt) if self.anansi_core else None
        )
        
        # État interne spécifique à Fihavanana
        self.state.update({
            "last_execution_time": None,
            "last_execution_status": None,
            "execution_history": []
        })
    
    def perceive(self, inputs):
        """
        Perçoit l'état actuel du marché et du compte MT5.
        
        Args:
            inputs: Dict contenant les paramètres de perception
                - update_market_data: Bool indiquant s'il faut mettre à jour les données de marché
                - symbols: Liste de symboles à surveiller
                
        Returns:
            Dict contenant les perceptions
        """
        perceptions = {
            "timestamp": time.time(),
            "connection_status": False,
            "account_info": None,
            "market_data": {},
            "open_positions": []
        }
        
        # Vérifier la connexion
        if self.mt5_connector.connect():
            perceptions["connection_status"] = True
            
            # Récupérer les informations de compte
            perceptions["account_info"] = self.mt5_connector.get_account_info()
            
            # Récupérer les positions ouvertes
            perceptions["open_positions"] = self.mt5_connector.get_positions()
            
            # Récupérer les données de marché si demandé
            if inputs.get("update_market_data", True):
                symbols = inputs.get("symbols", ["US30"])
                for symbol in symbols:
                    price_data = self.mt5_connector.get_current_price(symbol)
                    if price_data:
                        perceptions["market_data"][symbol] = price_data
        
        self.logger.info(f"Perception complétée - {len(perceptions['open_positions'])} positions ouvertes")
        return perceptions
    
    def think(self, perceptions, context=None):
        """
        Analyse les perceptions et détermine les actions à entreprendre.
        
        Args:
            perceptions: Dict des perceptions issues de perceive()
            context: Dict de contexte supplémentaire
                - action: Action demandée (buy, sell, close, etc.)
                - parameters: Paramètres spécifiques à l'action
                
        Returns:
            Dict des décisions à prendre
        """
        context = context or {}
        decisions = {
            "timestamp": time.time(),
            "action_type": None,
            "parameters": {},
            "reasoning": "Aucune action à entreprendre"
        }
        
        # Vérifier si une connexion est établie
        if not perceptions["connection_status"]:
            decisions["action_type"] = "reconnect"
            decisions["reasoning"] = "Connexion MT5 perdue, tentative de reconnexion"
            return decisions
        
        # Traiter l'action demandée dans le contexte
        if "action" in context:
            action = context["action"].lower()
            parameters = context.get("parameters", {})
            
            # Valider les paramètres selon l'action
            if action in ["buy", "sell"]:
                # Vérifier que les paramètres essentiels sont présents
                required_params = ["symbol", "volume"]
                if all(param in parameters for param in required_params):
                    decisions["action_type"] = action
                    decisions["parameters"] = parameters
                    decisions["reasoning"] = f"Exécution de l'ordre {action} sur {parameters.get('symbol')}"
                else:
                    decisions["action_type"] = "error"
                    decisions["reasoning"] = f"Paramètres manquants pour l'action {action}"
                    
            elif action == "close":
                symbol = parameters.get("symbol", "all")
                decisions["action_type"] = "close"
                decisions["parameters"] = {"symbol": symbol}
                decisions["reasoning"] = f"Fermeture des positions pour {symbol}"
                
            elif action == "status":
                decisions["action_type"] = "status"
                decisions["reasoning"] = "Récupération du statut du compte et des positions"
                
            else:
                decisions["action_type"] = "unknown"
                decisions["reasoning"] = f"Action non reconnue: {action}"
        
        # Si aucune action spécifique n'est demandée, planifier une surveillance régulière
        else:
            decisions["action_type"] = "monitor"
            decisions["reasoning"] = "Surveillance régulière du compte et des positions"
        
        self.logger.info(f"Décision: {decisions['action_type']} - {decisions['reasoning']}")
        return decisions
    
    def act(self, decisions):
        """
        Exécute les actions déterminées par le processus de réflexion.
        
        Args:
            decisions: Dict des décisions issues de think()
            
        Returns:
            Dict des résultats des actions entreprises
        """
        action_type = decisions.get("action_type")
        parameters = decisions.get("parameters", {})
        
        results = {
            "timestamp": time.time(),
            "action_type": action_type,
            "success": False,
            "message": "",
            "data": None
        }
        
        # Exécuter l'action appropriée
        if action_type == "reconnect":
            success = self.mt5_connector.connect()
            results["success"] = success
            results["message"] = "Reconnexion réussie" if success else "Échec de la reconnexion"
            
        elif action_type == "buy":
            symbol = parameters.get("symbol", "US30")
            volume = parameters.get("volume", 0.01)
            price = parameters.get("price", 0)  # 0 = prix du marché
            sl = parameters.get("sl", 0)
            tp = parameters.get("tp", 0)
            
            result = self.mt5_connector.place_order(
                symbol=symbol,
                order_type="BUY",
                volume=volume,
                price=price,
                sl=sl,
                tp=tp,
                comment="Akoben Trading System"
            )
            
            if result:
                results["success"] = True
                results["message"] = f"Ordre d'achat exécuté sur {symbol}"
                results["data"] = result
            else:
                results["message"] = f"Échec de l'ordre d'achat sur {symbol}"
                
        elif action_type == "sell":
            symbol = parameters.get("symbol", "US30")
            volume = parameters.get("volume", 0.01)
            price = parameters.get("price", 0)  # 0 = prix du marché
            sl = parameters.get("sl", 0)
            tp = parameters.get("tp", 0)
            
            result = self.mt5_connector.place_order(
                symbol=symbol,
                order_type="SELL",
                volume=volume,
                price=price,
                sl=sl,
                tp=tp,
                comment="Akoben Trading System"
            )
            
            if result:
                results["success"] = True
                results["message"] = f"Ordre de vente exécuté sur {symbol}"
                results["data"] = result
            else:
                results["message"] = f"Échec de l'ordre de vente sur {symbol}"
                
        elif action_type == "close":
            symbol = parameters.get("symbol", "all")
            
            if symbol.lower() == "all":
                success = self.mt5_connector.close_all_positions()
                results["success"] = success
                results["message"] = "Toutes les positions fermées" if success else "Échec de fermeture des positions"
            else:
                success = self.mt5_connector.close_position(symbol=symbol)
                results["success"] = success
                results["message"] = f"Position {symbol} fermée" if success else f"Échec de fermeture de {symbol}"
                
        elif action_type == "status":
            account_info = self.mt5_connector.get_account_info()
            positions = self.mt5_connector.get_positions()
            
            results["success"] = account_info is not None
            results["message"] = "Statut récupéré avec succès" if results["success"] else "Échec de récupération du statut"
            results["data"] = {
                "account_info": account_info,
                "positions": positions
            }
            
        elif action_type == "monitor":
            # Simple surveillance, aucune action spécifique
            results["success"] = True
            results["message"] = "Surveillance effectuée"
            
        else:
            results["message"] = f"Action non prise en charge: {action_type}"
        
        # Mettre à jour l'historique des exécutions
        self.state["last_execution_time"] = results["timestamp"]
        self.state["last_execution_status"] = results["success"]
        self.state["execution_history"].append({
            "timestamp": results["timestamp"],
            "action_type": action_type,
            "success": results["success"]
        })
        
        # Limiter la taille de l'historique pour éviter une croissance excessive
        if len(self.state["execution_history"]) > 100:
            self.state["execution_history"] = self.state["execution_history"][-100:]
        
        self.logger.info(f"Action {action_type} - Résultat: {'Succès' if results['success'] else 'Échec'}")
        return results