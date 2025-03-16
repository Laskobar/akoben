"""
Agent Iklwa - Gestionnaire de risques pour l'équipe Chaka
"""

import os
import time
import json
import math
from typing import Dict, Any, List, Optional, Tuple

from src.anansi.agent_framework.autonomous_agent import AutonomousAgent

class Iklwa(AutonomousAgent):
    """
    Agent Iklwa - Spécialisé dans la gestion des risques pour le trading.
    
    Cet agent analyse les risques des opportunités de trading, détermine
    les tailles de position optimales et valide les niveaux de stop-loss
    en fonction de la volatilité et de paramètres de risque définis.
    
    Fait partie de l'équipe Chaka (Trading).
    """
    
    def __init__(self, name="iklwa", config=None, anansi_core=None):
        """
        Initialise l'agent Iklwa.
        
        Args:
            name: Nom de l'agent
            config: Configuration de l'agent
            anansi_core: Référence au cerveau central Anansi
        """
        super().__init__(name, config, anansi_core)
        
        # Configuration des paramètres de risque par défaut
        self.config = config or {}
        self.max_risk_per_trade = self.config.get("max_risk_per_trade", 0.02)  # 2% du capital par trade
        self.max_portfolio_risk = self.config.get("max_portfolio_risk", 0.06)  # 6% du capital max en risque
        self.max_open_positions = self.config.get("max_open_positions", 3)  # Max 3 positions ouvertes
        self.min_risk_reward = self.config.get("min_risk_reward", 1.5)  # Min 1.5:1 R:R
        self.optimal_risk_reward = self.config.get("optimal_risk_reward", 2.0)  # 2:1 R:R optimal
        
        # État interne
        self.state.update({
            "current_portfolio_risk": 0.0,
            "open_positions_count": 0,
            "risk_assessments": []  # Historique des évaluations de risque
        })
        
        self.logger.info(f"Agent Iklwa initialisé. Max. risque par trade: {self.max_risk_per_trade*100}%, Min. ratio R:R: {self.min_risk_reward}")
        
    def perceive(self, inputs):
        """
        Perçoit l'état actuel du compte et les opportunités de trading.
        
        Args:
            inputs: Dict contenant les paramètres d'entrée
                - account_info: Informations du compte
                - open_positions: Positions actuellement ouvertes
                - trade_opportunity: Opportunité de trading à évaluer
                - market_volatility: Niveau de volatilité du marché (optionnel)
                
        Returns:
            Dict contenant les perceptions
        """
        perceptions = {
            "timestamp": time.time(),
            "account_analyzed": False,
            "positions_analyzed": False,
            "opportunity_analyzed": False,
            "capital_at_risk": 0.0,
            "available_risk_budget": 0.0,
            "open_positions": []
        }
        
        # Analyser les informations du compte
        account_info = inputs.get("account_info", {})
        if account_info:
            perceptions["account_analyzed"] = True
            perceptions["account_balance"] = account_info.get("balance", 0)
            perceptions["account_equity"] = account_info.get("equity", 0)
            perceptions["account_margin"] = account_info.get("margin", 0)
            perceptions["account_free_margin"] = account_info.get("free_margin", 0)
            perceptions["account_currency"] = account_info.get("currency", "USD")
            
            # Utiliser l'équité pour les calculs de risque (plus conservateur)
            perceptions["risk_capital"] = perceptions["account_equity"]
        
        # Analyser les positions ouvertes
        open_positions = inputs.get("open_positions", [])
        if open_positions:
            perceptions["positions_analyzed"] = True
            perceptions["open_positions"] = open_positions
            perceptions["open_positions_count"] = len(open_positions)
            
            # Calculer le capital actuellement en risque
            total_risk = 0.0
            for position in open_positions:
                # Si la position a un stop loss, calculer le risque
                if position.get("stop_loss", 0) > 0:
                    entry_price = position.get("open_price", 0)
                    stop_loss = position.get("stop_loss", 0)
                    volume = position.get("volume", 0)
                    
                    # Calculer la distance en points jusqu'au stop loss
                    if position.get("type", "").upper() == "BUY":
                        distance = entry_price - stop_loss
                    else:  # SELL
                        distance = stop_loss - entry_price
                    
                    # Calculer le risque en devise
                    risk_amount = abs(distance) * volume * 10  # Pour les indices comme US30
                    total_risk += risk_amount
                else:
                    # Si pas de stop loss, estimation conservatrice basée sur la taille de position
                    total_risk += position.get("volume", 0) * 100  # Estimation arbitraire
            
            perceptions["capital_at_risk"] = total_risk
            
            # Convertir en pourcentage du capital
            if perceptions.get("risk_capital", 0) > 0:
                perceptions["portfolio_risk_percentage"] = total_risk / perceptions["risk_capital"]
            else:
                perceptions["portfolio_risk_percentage"] = 0.0
            
            # Mettre à jour l'état interne
            self.state["current_portfolio_risk"] = perceptions["portfolio_risk_percentage"]
            self.state["open_positions_count"] = perceptions["open_positions_count"]
        
        # Calculer le budget de risque disponible
        if perceptions.get("risk_capital", 0) > 0:
            max_risk_amount = perceptions["risk_capital"] * self.max_portfolio_risk
            current_risk_amount = perceptions.get("capital_at_risk", 0)
            perceptions["available_risk_budget"] = max(0, max_risk_amount - current_risk_amount)
            perceptions["available_risk_percentage"] = perceptions["available_risk_budget"] / perceptions["risk_capital"]
        
        # Analyser l'opportunité de trading
        trade_opportunity = inputs.get("trade_opportunity", {})
        if trade_opportunity:
            perceptions["opportunity_analyzed"] = True
            perceptions["trade_opportunity"] = trade_opportunity
            
            # Extraire des informations clés
            entry = trade_opportunity.get("entry", 0)
            stop_loss = trade_opportunity.get("stop_loss", 0)
            take_profit = trade_opportunity.get("take_profit", 0)
            
            if entry > 0 and stop_loss > 0:
                # Calculer le ratio risque-récompense si tous les niveaux sont disponibles
                if take_profit > 0:
                    if trade_opportunity.get("action", "").upper() == "BUY":
                        risk = entry - stop_loss
                        reward = take_profit - entry
                    else:  # SELL
                        risk = stop_loss - entry
                        reward = entry - take_profit
                    
                    if risk > 0:
                        perceptions["risk_reward_ratio"] = reward / risk
                
                # Calculer la distance au stop loss en points
                perceptions["stop_loss_distance"] = abs(entry - stop_loss)
        
        # Volatilité du marché (si fournie)
        market_volatility = inputs.get("market_volatility")
        if market_volatility is not None:
            perceptions["market_volatility"] = market_volatility
        
        self.logger.info(f"Perception complétée. Positions ouvertes: {perceptions.get('open_positions_count', 0)}, Capital en risque: {perceptions.get('portfolio_risk_percentage', 0)*100:.2f}%")
        return perceptions
    
    def think(self, perceptions, context=None):
        """
        Analyse les perceptions et détermine les recommandations de gestion des risques.
        
        Args:
            perceptions: Dict des perceptions issues de perceive()
            context: Dict de contexte supplémentaire
                
        Returns:
            Dict des décisions à prendre
        """
        context = context or {}
        decisions = {
            "timestamp": time.time(),
            "risk_evaluation": "HIGH",  # Par défaut, conservateur
            "position_approved": False,
            "position_size": 0.0,
            "recommended_stop_loss": None,
            "risk_amount": 0.0,
            "risk_percentage": 0.0,
            "risk_reward_adequate": False,
            "reasoning": [],
            "warnings": []
        }
        
        # Vérifier si l'opportunité est présente
        if not perceptions.get("opportunity_analyzed", False):
            decisions["reasoning"].append("Aucune opportunité de trading à évaluer.")
            return decisions
        
        opportunity = perceptions.get("trade_opportunity", {})
        action = opportunity.get("action", "").upper()
        
        # 1. Vérifier si le nombre de positions ouvertes est déjà au maximum
        positions_count = perceptions.get("open_positions_count", 0)
        if positions_count >= self.max_open_positions:
            decisions["reasoning"].append(f"Nombre maximum de positions atteint ({positions_count}/{self.max_open_positions}).")
            decisions["warnings"].append("MAX_POSITIONS_REACHED")
            return decisions
        
        # 2. Vérifier si le budget de risque est disponible
        risk_budget = perceptions.get("available_risk_percentage", 0.0)
        if risk_budget <= 0:
            decisions["reasoning"].append("Budget de risque épuisé. Aucune position supplémentaire recommandée.")
            decisions["warnings"].append("RISK_BUDGET_DEPLETED")
            return decisions
        
        # 3. Vérifier le ratio risque/récompense
        risk_reward = perceptions.get("risk_reward_ratio", 0.0)
        if risk_reward > 0:
            decisions["risk_reward_ratio"] = risk_reward
            
            if risk_reward >= self.optimal_risk_reward:
                decisions["risk_reward_adequate"] = True
                decisions["reasoning"].append(f"Ratio risque/récompense excellent: {risk_reward:.2f} ≥ {self.optimal_risk_reward} (optimal).")
            elif risk_reward >= self.min_risk_reward:
                decisions["risk_reward_adequate"] = True
                decisions["reasoning"].append(f"Ratio risque/récompense acceptable: {risk_reward:.2f} ≥ {self.min_risk_reward} (minimum).")
            else:
                decisions["reasoning"].append(f"Ratio risque/récompense insuffisant: {risk_reward:.2f} < {self.min_risk_reward} (minimum).")
                decisions["warnings"].append("INADEQUATE_RISK_REWARD")
        else:
            decisions["reasoning"].append("Impossible de calculer le ratio risque/récompense. Stop-loss ou take-profit manquant.")
            decisions["warnings"].append("MISSING_LEVELS")
        
        # 4. Évaluer le niveau de risque global
        # Facteurs: volatilité du marché, ratio R:R, nombre de positions ouvertes
        risk_score = 0  # 0-100, où 100 est le risque maximum
        
        # Ajouter le score de volatilité
        volatility = perceptions.get("market_volatility", 50)  # Valeur par défaut moyenne
        risk_score += volatility * 0.4  # Pondération de 40% pour la volatilité
        
        # Ajouter le score basé sur le ratio R:R
        if risk_reward > 0:
            rr_score = max(0, 100 - (risk_reward / self.optimal_risk_reward) * 100)
            risk_score += rr_score * 0.3  # Pondération de 30% pour le R:R
        else:
            risk_score += 80 * 0.3  # Score élevé si R:R non calculable
        
        # Ajouter le score basé sur le nombre de positions ouvertes
        position_ratio = positions_count / self.max_open_positions
        risk_score += position_ratio * 100 * 0.3  # Pondération de 30% pour les positions
        
        # Déterminer le niveau de risque
        if risk_score < 30:
            decisions["risk_evaluation"] = "LOW"
        elif risk_score < 60:
            decisions["risk_evaluation"] = "MEDIUM"
        else:
            decisions["risk_evaluation"] = "HIGH"
        
        decisions["risk_score"] = risk_score
        decisions["reasoning"].append(f"Évaluation du risque: {decisions['risk_evaluation']} (score: {risk_score:.1f}/100).")
        
        # 5. Calculer la taille de position recommandée
        entry_price = opportunity.get("entry", 0)
        stop_loss = opportunity.get("stop_loss", 0)
        
        if entry_price > 0 and stop_loss > 0 and perceptions.get("risk_capital", 0) > 0:
            # Calculer la distance au stop en points
            if action == "BUY":
                stop_distance = entry_price - stop_loss
            else:  # SELL
                stop_distance = stop_loss - entry_price
            
            stop_distance = abs(stop_distance)
            
            # Déterminer le pourcentage de risque à utiliser
            risk_percentage = min(self.max_risk_per_trade, risk_budget)
            
            # Ajuster le risque en fonction de l'évaluation du risque
            if decisions["risk_evaluation"] == "HIGH":
                risk_percentage *= 0.5  # Réduire de 50% pour le risque élevé
            elif decisions["risk_evaluation"] == "MEDIUM":
                risk_percentage *= 0.75  # Réduire de 25% pour le risque moyen
            
            # Calculer le montant à risquer
            risk_amount = perceptions["risk_capital"] * risk_percentage
            
            # Calculer la taille de position
            # Pour les indices comme US30: point_value = 1 USD par point, multiplié par 10 pour le volume
            point_value = 10
            position_size = risk_amount / (stop_distance * point_value)
            
            # Arrondir à 2 décimales (standard pour les lots)
            position_size = round(position_size, 2)
            
            # Stocker les calculs dans la décision
            decisions["position_size"] = position_size
            decisions["risk_amount"] = risk_amount
            decisions["risk_percentage"] = risk_percentage
            decisions["stop_distance"] = stop_distance
            
            decisions["reasoning"].append(f"Taille de position recommandée: {position_size} lots (risque: {risk_percentage*100:.2f}% du capital).")
            
            # Approuver la position si elle respecte les critères
            position_approval = True
            
            # Vérifier si le ratio R:R est suffisant
            if not decisions["risk_reward_adequate"]:
                position_approval = False
            
            # Vérifier si la distance au stop est adéquate
            min_stop_distance = 10  # Par exemple, minimum 10 points pour US30
            if stop_distance < min_stop_distance:
                decisions["reasoning"].append(f"Distance au stop trop faible: {stop_distance} < {min_stop_distance} points.")
                decisions["warnings"].append("STOP_TOO_CLOSE")
                position_approval = False
            
            decisions["position_approved"] = position_approval
            
            if position_approval:
                decisions["reasoning"].append("Position approuvée selon les critères de gestion des risques.")
            else:
                decisions["reasoning"].append("Position rejetée. Ne respecte pas tous les critères de gestion des risques.")
        else:
            decisions["reasoning"].append("Impossible de calculer la taille de position. Prix d'entrée ou stop-loss manquant.")
            decisions["warnings"].append("MISSING_PRICE_LEVELS")
        
        # Recommander un stop loss si nécessaire
        original_stop = stop_loss
        if entry_price > 0 and perceptions.get("market_volatility") is not None:
            # Ajuster le stop loss en fonction de la volatilité
            volatility = perceptions["market_volatility"]
            
            # Plus la volatilité est élevée, plus le stop doit être large
            volatility_factor = 1.0 + (volatility / 100.0)
            
            # Calculer l'ATR ou une mesure similaire de la volatilité en points
            volatility_in_points = 20 * volatility_factor  # Valeur fictive, à remplacer par calcul réel
            
            # Définir le stop loss recommandé
            if action == "BUY":
                recommended_stop = entry_price - volatility_in_points
            else:  # SELL
                recommended_stop = entry_price + volatility_in_points
            
            # Arrondir le stop loss
            recommended_stop = round(recommended_stop, 1)
            
            # Si le stop loss original est trop proche, recommander le nouveau
            if original_stop > 0:
                current_distance = abs(entry_price - original_stop)
                if current_distance < volatility_in_points * 0.8:  # Si le stop est < 80% de la volatilité
                    decisions["recommended_stop_loss"] = recommended_stop
                    decisions["reasoning"].append(f"Stop loss trop proche compte tenu de la volatilité. Recommandation: {recommended_stop}.")
                    decisions["warnings"].append("ADJUST_STOP_LOSS")
            else:
                # Si pas de stop loss défini, recommander un
                decisions["recommended_stop_loss"] = recommended_stop
                decisions["reasoning"].append(f"Stop loss non défini. Recommandation: {recommended_stop}.")
                decisions["warnings"].append("MISSING_STOP_LOSS")
        
        # Stocker l'évaluation dans l'historique
        self.state["risk_assessments"].append({
            "timestamp": decisions["timestamp"],
            "opportunity": opportunity,
            "evaluation": decisions["risk_evaluation"],
            "position_approved": decisions["position_approved"],
            "position_size": decisions["position_size"],
            "risk_percentage": decisions["risk_percentage"]
        })
        
        # Limiter la taille de l'historique
        if len(self.state["risk_assessments"]) > 100:
            self.state["risk_assessments"] = self.state["risk_assessments"][-100:]
        
        self.logger.info(f"Analyse complétée. Évaluation: {decisions['risk_evaluation']}, Position approuvée: {decisions['position_approved']}, Taille: {decisions['position_size']}")
        return decisions
    
    def act(self, decisions):
        """
        Exécute les recommandations de gestion des risques.
        
        Args:
            decisions: Dict des décisions issues de think()
            
        Returns:
            Dict des résultats des actions entreprises
        """
        results = {
            "timestamp": time.time(),
            "action_taken": "RISK_ASSESSMENT",
            "execution_status": "completed",
            "risk_report": {},
            "message": "Évaluation des risques complétée."
        }
        
        # Préparer le rapport de risque
        risk_report = {
            "risk_evaluation": decisions.get("risk_evaluation", "HIGH"),
            "position_approved": decisions.get("position_approved", False),
            "position_size": decisions.get("position_size", 0.0),
            "risk_percentage": decisions.get("risk_percentage", 0.0),
            "risk_amount": decisions.get("risk_amount", 0.0),
            "risk_reward_ratio": decisions.get("risk_reward_ratio", 0.0),
            "recommended_stop_loss": decisions.get("recommended_stop_loss"),
            "warnings": decisions.get("warnings", []),
            "reasoning": decisions.get("reasoning", [])
        }
        
        results["risk_report"] = risk_report
        
        # Fournir un message récapitulatif
        approved_status = "APPROUVÉE" if risk_report["position_approved"] else "REJETÉE"
        results["message"] = f"Évaluation des risques: {risk_report['risk_evaluation']}. Position {approved_status}."
        
        if risk_report["position_approved"]:
            results["message"] += f" Taille recommandée: {risk_report['position_size']} lots."
        
        if risk_report["recommended_stop_loss"]:
            results["message"] += f" Stop loss recommandé: {risk_report['recommended_stop_loss']}."
        
        # Communiquer le rapport à qui en a besoin
        if self.anansi_core:
            # Informer Anansi de l'évaluation des risques
            self.communicate({
                "action": "risk_assessment_completed",
                "risk_report": risk_report
            })
        
        self.logger.info(f"Action complétée: {results['message']}")
        return results
    
    def calculate_position_size(self, entry_price, stop_loss, risk_percentage=None, account_balance=None):
        """
        Utilitaire pour calculer la taille d'une position en fonction du risque.
        
        Args:
            entry_price: Prix d'entrée
            stop_loss: Niveau de stop loss
            risk_percentage: Pourcentage du capital à risquer (None = utiliser max_risk_per_trade)
            account_balance: Solde du compte (None = interroger MT5)
            
        Returns:
            Taille de position recommandée
        """
        if risk_percentage is None:
            risk_percentage = self.max_risk_per_trade
        
        # Obtenir le solde du compte
        if account_balance is None:
            # Tenter de récupérer via MT5
            if self.anansi_core and "mt5_connector" in self.anansi_core.agents:
                try:
                    account_info = self.anansi_core.agents["mt5_connector"].get_account_info()
                    if account_info:
                        account_balance = account_info.get("equity", 0)
                except Exception as e:
                    self.logger.error(f"Erreur lors de la récupération du solde: {str(e)}")
                    account_balance = 10000  # Valeur par défaut
            else:
                account_balance = 10000  # Valeur par défaut
        
        # Calculer la distance au stop en points
        stop_distance = abs(entry_price - stop_loss)
        
        if stop_distance <= 0:
            return 0.0  # Éviter la division par zéro
        
        # Calculer le montant à risquer
        risk_amount = account_balance * risk_percentage
        
        # Calculer la taille de position
        point_value = 10  # Pour US30
        position_size = risk_amount / (stop_distance * point_value)
        
        # Arrondir à 2 décimales (standard pour les lots)
        position_size = round(position_size, 2)
        
        return position_size
    
    def get_risk_assessment_history(self, limit=10):
        """
        Récupère l'historique des évaluations de risque.
        
        Args:
            limit: Nombre maximum d'entrées à récupérer
            
        Returns:
            Liste des évaluations récentes
        """
        assessments = self.state.get("risk_assessments", [])
        return assessments[-limit:] if assessments else []
    
    def update_risk_parameters(self, new_parameters):
        """
        Met à jour les paramètres de gestion des risques.
        
        Args:
            new_parameters: Dict des nouveaux paramètres
                - max_risk_per_trade: Risque maximum par trade
                - max_portfolio_risk: Risque maximum du portefeuille
                - max_open_positions: Nombre maximum de positions ouvertes
                - min_risk_reward: Ratio R:R minimum
                - optimal_risk_reward: Ratio R:R optimal
                
        Returns:
            Dict des paramètres mis à jour
        """
        # Mettre à jour uniquement les paramètres fournis
        if "max_risk_per_trade" in new_parameters:
            self.max_risk_per_trade = new_parameters["max_risk_per_trade"]
        
        if "max_portfolio_risk" in new_parameters:
            self.max_portfolio_risk = new_parameters["max_portfolio_risk"]
        
        if "max_open_positions" in new_parameters:
            self.max_open_positions = new_parameters["max_open_positions"]
        
        if "min_risk_reward" in new_parameters:
            self.min_risk_reward = new_parameters["min_risk_reward"]
        
        if "optimal_risk_reward" in new_parameters:
            self.optimal_risk_reward = new_parameters["optimal_risk_reward"]
        
        # Mettre à jour la configuration
        self.config.update({
            "max_risk_per_trade": self.max_risk_per_trade,
            "max_portfolio_risk": self.max_portfolio_risk,
            "max_open_positions": self.max_open_positions,
            "min_risk_reward": self.min_risk_reward,
            "optimal_risk_reward": self.optimal_risk_reward
        })
        
        self.logger.info(f"Paramètres de risque mis à jour: max_risk_per_trade={self.max_risk_per_trade}, max_open_positions={self.max_open_positions}")
        
        return self.config