"""
Agent Assegai - Agent de décision de trading pour l'équipe Chaka
"""

import os
import time
import json
import uuid
from typing import Dict, Any, List, Optional, Tuple

from src.anansi.agent_framework.autonomous_agent import AutonomousAgent

class Assegai(AutonomousAgent):
    """
    Agent Assegai - Spécialisé dans la prise de décision finale de trading.
    
    Cet agent combine les analyses des autres agents (technique, sentiment,
    imitation, risque) pour prendre la décision finale d'exécuter ou non
    un ordre de trading.
    
    Fait partie de l'équipe Chaka (Trading).
    """
    
    def __init__(self, name="assegai", config=None, anansi_core=None):
        """
        Initialise l'agent Assegai.
        
        Args:
            name: Nom de l'agent
            config: Configuration de l'agent
            anansi_core: Référence au cerveau central Anansi
        """
        super().__init__(name, config, anansi_core)
        
        # Configuration 
        self.config = config or {}
        
        # Poids des différentes sources d'analyse (doivent totaliser 1.0)
        self.weights = self.config.get("analysis_weights", {
            "technical": 0.35,  # Analyse technique
            "imitation": 0.25,  # Agent d'imitation (Oba)
            "risk": 0.20,       # Gestion des risques (Iklwa)
            "fundamental": 0.10, # Analyse fondamentale 
            "sentiment": 0.10    # Analyse de sentiment
        })
        
        # Seuil de confiance minimum pour exécuter un ordre
        self.confidence_threshold = self.config.get("confidence_threshold", 0.7)
        
        # Paramètres de confirmation
        self.require_risk_approval = self.config.get("require_risk_approval", True)
        self.require_multiple_confirmations = self.config.get("require_multiple_confirmations", True)
        
        # État interne
        self.state.update({
            "decision_history": [],
            "execution_history": [],
            "performance_metrics": {
                "decisions_count": 0,
                "executed_count": 0,
                "successful_trades": 0,
                "failed_trades": 0
            }
        })
        
        self.logger.info(f"Agent Assegai initialisé. Seuil de confiance: {self.confidence_threshold}")
    
    def perceive(self, inputs):
        """
        Perçoit les analyses des différents agents et les données de marché.
        
        Args:
            inputs: Dict contenant les analyses et données
                - technical_analysis: Analyse technique
                - imitation_analysis: Analyse de l'agent d'imitation (Oba)
                - risk_assessment: Évaluation des risques (Iklwa)
                - fundamental_analysis: Analyse fondamentale (optionnel)
                - sentiment_analysis: Analyse du sentiment (optionnel)
                - market_data: Données actuelles du marché
                - symbol: Symbole de l'instrument
                
        Returns:
            Dict contenant les perceptions
        """
        perceptions = {
            "timestamp": time.time(),
            "analyses_received": {},
            "market_data": {},
            "symbol": inputs.get("symbol", "US30"),
            "timeframe": inputs.get("timeframe", "M1"),
            "analyses_count": 0,
            "analyses_summary": {}
        }
        
        # Collecter les analyses disponibles
        analysis_types = ["technical", "imitation", "risk", "fundamental", "sentiment"]
        for analysis_type in analysis_types:
            key = f"{analysis_type}_analysis"
            if analysis_type == "risk":
                key = "risk_assessment"  # Exception pour le nom de la clé de risque
                
            if key in inputs:
                perceptions["analyses_received"][analysis_type] = inputs[key]
                perceptions["analyses_count"] += 1
                
                # Extraire et standardiser l'action recommandée
                action, confidence = self._extract_action_from_analysis(inputs[key], analysis_type)
                
                if action:
                    if "actions" not in perceptions["analyses_summary"]:
                        perceptions["analyses_summary"]["actions"] = {}
                    
                    if action not in perceptions["analyses_summary"]["actions"]:
                        perceptions["analyses_summary"]["actions"][action] = []
                    
                    perceptions["analyses_summary"]["actions"][action].append({
                        "type": analysis_type,
                        "confidence": confidence
                    })
        
        # Collecter les données de marché
        market_data = inputs.get("market_data", {})
        if market_data:
            perceptions["market_data"] = market_data
        
        # Résumer les analyses
        if perceptions["analyses_count"] > 0:
            # Calculer la distribution des actions recommandées
            action_counts = {}
            if "actions" in perceptions["analyses_summary"]:
                for action, recommendations in perceptions["analyses_summary"]["actions"].items():
                    action_counts[action] = len(recommendations)
            
            perceptions["analyses_summary"]["action_counts"] = action_counts
            
            # Déterminer si nous avons un consensus
            if action_counts:
                max_action = max(action_counts, key=action_counts.get)
                max_count = action_counts[max_action]
                
                if max_count >= 2 and max_count > perceptions["analyses_count"] / 2:
                    perceptions["analyses_summary"]["consensus"] = {
                        "action": max_action,
                        "count": max_count,
                        "ratio": max_count / perceptions["analyses_count"]
                    }
        
        self.logger.info(f"Perception complétée. {perceptions['analyses_count']} analyses reçues pour {perceptions['symbol']}.")
        return perceptions
    
    def think(self, perceptions, context=None):
        """
        Analyse les perceptions et détermine la décision de trading.
        
        Args:
            perceptions: Dict des perceptions issues de perceive()
            context: Dict de contexte supplémentaire
                
        Returns:
            Dict des décisions à prendre
        """
        context = context or {}
        
        decisions = {
            "timestamp": time.time(),
            "trade_id": str(uuid.uuid4()),
            "action": "WAIT",  # Par défaut, attendre
            "confidence": 0.0,
            "symbol": perceptions.get("symbol", "US30"),
            "entry_type": "MARKET",  # MARKET ou LIMIT
            "entry_price": None,
            "stop_loss": None,
            "take_profit": None,
            "position_size": None,
            "reasoning": [],
            "analysis_contributions": {},
            "warnings": []
        }
        
        # Vérifier si nous avons suffisamment d'analyses
        min_analyses = 2
        if perceptions["analyses_count"] < min_analyses:
            decisions["reasoning"].append(f"Analyses insuffisantes: {perceptions['analyses_count']}/{min_analyses} requises.")
            decisions["warnings"].append("INSUFFICIENT_ANALYSES")
            return decisions
        
        # Récupérer l'évaluation des risques si disponible
        risk_approval = True  # Par défaut, considérer comme approuvé
        position_size = None
        stop_loss = None
        
        if "risk" in perceptions["analyses_received"]:
            risk_assessment = perceptions["analyses_received"]["risk"]
            
            # Vérifier si le gestionnaire de risques approuve la position
            if self.require_risk_approval:
                risk_approval = risk_assessment.get("position_approved", False)
                
                if not risk_approval:
                    decisions["reasoning"].append("Position rejetée par le gestionnaire de risques.")
                    decisions["warnings"].append("RISK_REJECTION")
                
                # Récupérer la taille de position recommandée
                position_size = risk_assessment.get("position_size")
                if position_size is not None:
                    decisions["position_size"] = position_size
                
                # Récupérer le stop loss recommandé
                recommended_stop = risk_assessment.get("recommended_stop_loss")
                if recommended_stop is not None:
                    decisions["stop_loss"] = recommended_stop
                    stop_loss = recommended_stop
        
        # Si le risque est rejeté et que cette validation est obligatoire, attendre
        if self.require_risk_approval and not risk_approval:
            decisions["reasoning"].append("Décision: WAIT - Rejet du gestionnaire de risques.")
            return decisions
        
        # Évaluer les actions recommandées
        action_scores = self._calculate_action_scores(perceptions["analyses_received"])
        
        # Trouver l'action avec le score le plus élevé
        if action_scores:
            best_action, best_score = max(action_scores.items(), key=lambda x: x[1]["weighted_score"])
            
            # Définir l'action et la confiance
            decisions["action"] = best_action
            decisions["confidence"] = best_score["weighted_score"]
            decisions["analysis_contributions"] = best_score["contributions"]
            
            # Ajouter le raisonnement
            decisions["reasoning"].append(f"Action recommandée: {best_action} avec {decisions['confidence']:.2%} de confiance.")
            for analysis_type, contribution in best_score["contributions"].items():
                if contribution > 0:
                    decisions["reasoning"].append(f"- {analysis_type.capitalize()}: contribution de {contribution:.2%}")
        
        # Vérifier si nous avons un consensus
        if "consensus" in perceptions["analyses_summary"]:
            consensus = perceptions["analyses_summary"]["consensus"]
            decisions["reasoning"].append(f"Consensus: {consensus['action']} recommandé par {consensus['count']}/{perceptions['analyses_count']} analyses.")
            
            # Bonus de confiance si l'action choisie correspond au consensus
            if decisions["action"] == consensus["action"]:
                consensus_bonus = 0.1 * consensus["ratio"]
                old_confidence = decisions["confidence"]
                decisions["confidence"] = min(1.0, decisions["confidence"] + consensus_bonus)
                decisions["reasoning"].append(f"Bonus de consensus: +{(decisions['confidence']-old_confidence):.2%} de confiance.")
        elif self.require_multiple_confirmations:
            # Si nous exigeons des confirmations multiples et qu'il n'y a pas de consensus
            decisions["reasoning"].append("Pas de consensus entre les analyses.")
            decisions["warnings"].append("NO_CONSENSUS")
            
            # Réduire la confiance
            decisions["confidence"] *= 0.8
            decisions["reasoning"].append(f"Pénalité pour absence de consensus: confiance réduite à {decisions['confidence']:.2%}.")
        
        # Vérifier le seuil de confiance
        if decisions["confidence"] < self.confidence_threshold:
            old_action = decisions["action"]
            decisions["action"] = "WAIT"
            decisions["reasoning"].append(f"Confiance insuffisante ({decisions['confidence']:.2%} < {self.confidence_threshold:.2%}) pour {old_action}.")
            decisions["warnings"].append("CONFIDENCE_TOO_LOW")
        
        # Déterminer les niveaux de prix
        entry_price, take_profit = self._determine_price_levels(perceptions, decisions["action"], stop_loss)
        
        if entry_price is not None:
            decisions["entry_price"] = entry_price
        
        if take_profit is not None:
            decisions["take_profit"] = take_profit
        
        # Déterminer la taille de la position si non définie par la gestion des risques
        if decisions["position_size"] is None and decisions["action"] in ["BUY", "SELL"]:
            # Utiliser une taille par défaut ou demander au gestionnaire de risques
            decisions["position_size"] = self.config.get("default_position_size", 0.01)
            decisions["reasoning"].append(f"Aucune taille de position recommandée par le gestionnaire de risques. Utilisation de la valeur par défaut: {decisions['position_size']}.")
        
        # Mémoriser la décision
        self.state["decision_history"].append({
            "timestamp": decisions["timestamp"],
            "trade_id": decisions["trade_id"],
            "symbol": decisions["symbol"],
            "action": decisions["action"],
            "confidence": decisions["confidence"],
            "position_size": decisions["position_size"]
        })
        
        # Limiter la taille de l'historique
        if len(self.state["decision_history"]) > 100:
            self.state["decision_history"] = self.state["decision_history"][-100:]
        
        # Mettre à jour les métriques
        self.state["performance_metrics"]["decisions_count"] += 1
        
        self.logger.info(f"Décision: {decisions['action']} {decisions['symbol']} avec {decisions['confidence']:.2%} de confiance.")
        return decisions
    
    def act(self, decisions):
        """
        Exécute la décision de trading.
        
        Args:
            decisions: Dict des décisions issues de think()
            
        Returns:
            Dict des résultats des actions entreprises
        """
        results = {
            "timestamp": time.time(),
            "trade_id": decisions["trade_id"],
            "action_taken": decisions["action"],
            "execution_status": "waiting",
            "order_details": None,
            "message": ""
        }
        
        # Si l'action est d'attendre, rien à exécuter
        if decisions["action"] == "WAIT":
            results["execution_status"] = "skipped"
            results["message"] = "Aucune action de trading nécessaire."
            return results
        
        # Vérifier que nous avons les informations nécessaires pour exécuter l'ordre
        required_fields = ["symbol", "action"]
        missing_fields = [field for field in required_fields if decisions.get(field) is None]
        
        if missing_fields:
            results["execution_status"] = "error"
            results["message"] = f"Informations manquantes pour l'exécution: {', '.join(missing_fields)}."
            return results
        
        # Si nous avons accès à l'agent d'exécution, exécuter l'ordre
        if self.anansi_core and "mt5_connector" in self.anansi_core.agents:
            executor = self.anansi_core.agents["mt5_connector"]
            
            try:
                # Préparer les paramètres de l'ordre
                order_params = {
                    "symbol": decisions["symbol"],
                    "order_type": decisions["action"],
                    "volume": decisions.get("position_size", 0.01),
                    "price": decisions.get("entry_price", 0),  # 0 = prix du marché
                    "sl": decisions.get("stop_loss", 0),
                    "tp": decisions.get("take_profit", 0),
                    "comment": f"Akoben-Assegai {decisions['trade_id']}"
                }
                
                # Exécuter l'ordre
                order_result = executor.place_order(**order_params)
                
                if order_result:
                    results["execution_status"] = "success"
                    results["order_details"] = order_result
                    results["message"] = f"Ordre {decisions['action']} exécuté avec succès."
                    
                    # Mettre à jour les métriques
                    self.state["performance_metrics"]["executed_count"] += 1
                else:
                    results["execution_status"] = "failed"
                    results["message"] = "Échec de l'exécution de l'ordre. Aucun résultat retourné."
            
            except Exception as e:
                results["execution_status"] = "error"
                results["message"] = f"Erreur lors de l'exécution de l'ordre: {str(e)}"
                self.logger.error(f"Erreur d'exécution: {str(e)}")
        else:
            # Mode simulation - Pas d'exécution réelle
            results["execution_status"] = "simulated"
            results["message"] = f"Mode simulation: {decisions['action']} {decisions['symbol']} à {decisions.get('entry_price', 'prix du marché')}."
            results["order_details"] = {
                "simulated": True,
                "symbol": decisions["symbol"],
                "action": decisions["action"],
                "volume": decisions.get("position_size", 0.01),
                "entry": decisions.get("entry_price"),
                "stop_loss": decisions.get("stop_loss"),
                "take_profit": decisions.get("take_profit"),
                "timestamp": results["timestamp"]
            }
            
            # En mode simulation, considérer comme exécuté
            self.state["performance_metrics"]["executed_count"] += 1
        
        # Enregistrer l'exécution dans l'historique
        self.state["execution_history"].append({
            "timestamp": results["timestamp"],
            "trade_id": results["trade_id"],
            "action": decisions["action"],
            "symbol": decisions["symbol"],
            "status": results["execution_status"],
            "details": results.get("order_details")
        })
        
        # Limiter la taille de l'historique
        if len(self.state["execution_history"]) > 100:
            self.state["execution_history"] = self.state["execution_history"][-100:]
        
        self.logger.info(f"Exécution: {results['execution_status']} - {results['message']}")
        return results
    
    def _extract_action_from_analysis(self, analysis, analysis_type):
        """
        Extrait l'action recommandée et la confiance d'une analyse.
        
        Args:
            analysis: Analyse d'un agent
            analysis_type: Type d'analyse
            
        Returns:
            Tuple (action, confidence)
        """
        action = None
        confidence = 0.0
        
        if analysis_type == "technical":
            # Extraire de l'analyse technique
            if "recommendation" in analysis:
                action = analysis["recommendation"].get("action")
                confidence = analysis["recommendation"].get("confidence", 0.5)
            elif "action" in analysis:
                action = analysis["action"]
                confidence = analysis.get("confidence", 0.5)
        
        elif analysis_type == "imitation":
            # Extraire de l'agent d'imitation
            if "action" in analysis:
                action = analysis["action"]
                confidence = analysis.get("confidence", 0.5)
        
        elif analysis_type == "risk":
            # Extraire de l'évaluation des risques
            if "position_approved" in analysis and analysis["position_approved"]:
                # Si la position est approuvée, utiliser l'action de l'opportunité
                if "trade_opportunity" in analysis:
                    action = analysis["trade_opportunity"].get("action")
                    confidence = 0.8  # Confiance élevée puisque approuvée par la gestion des risques
                else:
                    action = None  # Pas d'action spécifique recommandée
            else:
                action = "WAIT"  # Si la position n'est pas approuvée, recommander d'attendre
                confidence = 0.7
        
        elif analysis_type == "fundamental":
            # Extraire de l'analyse fondamentale
            if "recommendation" in analysis:
                action = analysis["recommendation"].get("action")
                confidence = analysis["recommendation"].get("confidence", 0.5)
            elif "bias" in analysis:
                # Convertir le biais en action
                bias = analysis["bias"].upper()
                if bias == "BULLISH":
                    action = "BUY"
                elif bias == "BEARISH":
                    action = "SELL"
                elif bias == "NEUTRAL":
                    action = "WAIT"
                confidence = analysis.get("confidence", 0.5)
        
        elif analysis_type == "sentiment":
            # Extraire de l'analyse de sentiment
            if "sentiment" in analysis:
                sentiment = analysis["sentiment"]
                if sentiment > 0.2:  # Sentiment positif
                    action = "BUY"
                    confidence = min(0.8, 0.5 + sentiment)
                elif sentiment < -0.2:  # Sentiment négatif
                    action = "SELL"
                    confidence = min(0.8, 0.5 + abs(sentiment))
                else:
                    action = "WAIT"
                    confidence = 0.5
        
        # Normaliser l'action
        if action:
            action = action.upper()
            # S'assurer que l'action est l'une des valeurs attendues
            if action not in ["BUY", "SELL", "WAIT"]:
                if action in ["LONG"]:
                    action = "BUY"
                elif action in ["SHORT"]:
                    action = "SELL"
                else:
                    action = "WAIT"
        
        return action, confidence
    
    def _calculate_action_scores(self, analyses):
        """
        Calcule un score pondéré pour chaque action recommandée.
        
        Args:
            analyses: Dict des analyses des différents agents
            
        Returns:
            Dict des scores par action
        """
        action_scores = {}
        
        for analysis_type, analysis in analyses.items():
            action, confidence = self._extract_action_from_analysis(analysis, analysis_type)
            
            if action:
                weight = self.weights.get(analysis_type, 0.1)
                contribution = weight * confidence
                
                if action not in action_scores:
                    action_scores[action] = {
                        "weighted_score": 0.0,
                        "contributions": {}
                    }
                
                action_scores[action]["weighted_score"] += contribution
                action_scores[action]["contributions"][analysis_type] = contribution
        
        return action_scores
    
    def _determine_price_levels(self, perceptions, action, stop_loss=None):
        """
        Détermine les niveaux de prix pour l'entrée et les objectifs.
        
        Args:
            perceptions: Dict des perceptions
            action: Action de trading (BUY/SELL)
            stop_loss: Niveau de stop loss (optionnel)
            
        Returns:
            Tuple (entry_price, take_profit)
        """
        entry_price = None
        take_profit = None
        
        # Vérifier si des niveaux sont déjà disponibles dans les analyses
        for analysis_type, analysis in perceptions["analyses_received"].items():
            # Chercher des niveaux d'entrée
            if "entry_price" in analysis:
                entry_price = analysis["entry_price"]
            elif analysis_type == "risk" and "trade_opportunity" in analysis:
                opportunity = analysis["trade_opportunity"]
                if "entry" in opportunity:
                    entry_price = opportunity["entry"]
            
            # Chercher des niveaux de prise de profit
            if "take_profit" in analysis:
                take_profit = analysis["take_profit"]
            elif analysis_type == "risk" and "trade_opportunity" in analysis:
                opportunity = analysis["trade_opportunity"]
                if "take_profit" in opportunity:
                    take_profit = opportunity["take_profit"]
        
        # Si pas de niveau d'entrée défini, utiliser le prix actuel du marché
        if entry_price is None and "market_data" in perceptions:
            market_data = perceptions["market_data"]
            if "bid" in market_data and "ask" in market_data:
                if action == "BUY":
                    entry_price = market_data["ask"]
                elif action == "SELL":
                    entry_price = market_data["bid"]
        
        # Calculer le take profit si non défini mais que nous avons un stop loss
        if take_profit is None and entry_price is not None and stop_loss is not None:
            risk = abs(entry_price - stop_loss)
            target_rr = 2.0  # Ratio risque/récompense cible
            
            if action == "BUY":
                take_profit = entry_price + (risk * target_rr)
            elif action == "SELL":
                take_profit = entry_price - (risk * target_rr)
        
        return entry_price, take_profit
    
    def record_trade_result(self, trade_id, success, profit=None, trade_data=None):
        """
        Enregistre le résultat d'un trade pour l'analyse des performances.
        
        Args:
            trade_id: ID du trade
            success: True si le trade est un succès, False sinon
            profit: Montant du profit/perte (optionnel)
            trade_data: Données supplémentaires sur le trade (optionnel)
            
        Returns:
            True si l'enregistrement a réussi, False sinon
        """
        # Trouver le trade dans l'historique
        trade_found = False
        for trade in self.state["execution_history"]:
            if trade.get("trade_id") == trade_id:
                trade_found = True
                
                # Mettre à jour le trade avec le résultat
                trade["result"] = {
                    "success": success,
                    "profit": profit,
                    "recorded_at": time.time()
                }
                
                if trade_data:
                    trade["result"].update(trade_data)
                
                break
        
        if not trade_found:
            self.logger.warning(f"Trade {trade_id} non trouvé dans l'historique.")
            return False
        
        # Mettre à jour les métriques
        if success:
            self.state["performance_metrics"]["successful_trades"] += 1
        else:
            self.state["performance_metrics"]["failed_trades"] += 1
        
        self.logger.info(f"Résultat du trade {trade_id} enregistré: {'succès' if success else 'échec'}, profit: {profit}")
        return True
    
    def get_performance_metrics(self):
        """
        Récupère les métriques de performance.
        
        Returns:
            Dict des métriques
        """
        metrics = self.state["performance_metrics"].copy()
        
        # Calculer des métriques dérivées
        if metrics["executed_count"] > 0:
            metrics["success_rate"] = metrics["successful_trades"] / metrics["executed_count"]
        else:
            metrics["success_rate"] = 0.0
        
        if metrics["decisions_count"] > 0:
            metrics["execution_rate"] = metrics["executed_count"] / metrics["decisions_count"]
        else:
            metrics["execution_rate"] = 0.0
        
        return metrics
    
    def update_configuration(self, new_config):
        """
        Met à jour la configuration de l'agent.
        
        Args:
            new_config: Dict de la nouvelle configuration
            
        Returns:
            Dict de la configuration mise à jour
        """
        # Mettre à jour les poids (tout en s'assurant qu'ils totalisent 1.0)
        if "analysis_weights" in new_config:
            weights = new_config["analysis_weights"]
            total = sum(weights.values())
            
            if abs(total - 1.0) > 0.01:  # Si le total n'est pas proche de 1.0
                # Normaliser les poids
                normalized_weights = {k: v/total for k, v in weights.items()}
                self.weights = normalized_weights
                self.logger.info(f"Poids normalisés pour totaliser 1.0: {self.weights}")
            else:
                self.weights = weights
        
        # Mettre à jour les autres paramètres
        if "confidence_threshold" in new_config:
            self.confidence_threshold = new_config["confidence_threshold"]
        
        if "require_risk_approval" in new_config:
            self.require_risk_approval = new_config["require_risk_approval"]
        
        if "require_multiple_confirmations" in new_config:
            self.require_multiple_confirmations = new_config["require_multiple_confirmations"]
        
        # Mettre à jour la configuration complète
        self.config.update({
            "analysis_weights": self.weights,
            "confidence_threshold": self.confidence_threshold,
            "require_risk_approval": self.require_risk_approval,
            "require_multiple_confirmations": self.require_multiple_confirmations
        })
        
        self.logger.info(f"Configuration mise à jour: threshold={self.confidence_threshold}, require_risk={self.require_risk_approval}")
        
        return self.config
    
    def get_decision_history(self, limit=10):
        """
        Récupère l'historique des décisions.
        
        Args:
            limit: Nombre maximum d'entrées à récupérer
            
        Returns:
            Liste des décisions récentes
        """
        decisions = self.state.get("decision_history", [])
        return decisions[-limit:] if decisions else []
    
    def get_execution_history(self, limit=10):
        """
        Récupère l'historique des exécutions.
        
        Args:
            limit: Nombre maximum d'entrées à récupérer
            
        Returns:
            Liste des exécutions récentes
        """
        executions = self.state.get("execution_history", [])
        return executions[-limit:] if executions else []