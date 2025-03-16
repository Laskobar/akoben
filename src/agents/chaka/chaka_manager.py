"""
ChakaManager - Gestionnaire de l'équipe Chaka pour Akoben
"""

import os
import time
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

from src.anansi.agent_framework.autonomous_agent import AutonomousAgent
from src.agents.chaka.oba import Oba
from src.agents.chaka.iklwa import Iklwa
from src.agents.chaka.assegai import Assegai

class ChakaManager(AutonomousAgent):
    """
    ChakaManager - Gestionnaire de l'équipe Chaka.
    
    Coordonne les agents de trading (Oba, Iklwa, Assegai) et gère
    le workflow d'analyse et de prise de décision de trading.
    
    Agit comme le point d'entrée principal pour l'équipe Chaka.
    """
    
    def __init__(self, name="chaka_manager", config=None, anansi_core=None):
        """
        Initialise le gestionnaire de l'équipe Chaka.
        
        Args:
            name: Nom du gestionnaire
            config: Configuration du gestionnaire
            anansi_core: Référence au cerveau central Anansi
        """
        super().__init__(name, config, anansi_core)
        
        # Configuration
        self.config = config or {}
        
        # Initialiser les agents de l'équipe
        self.agents = {}
        self._initialize_agents()
        
        # État interne
        self.state.update({
            "workflow_history": [],
            "active_analyses": {}
        })
        
        self.logger.info(f"ChakaManager initialisé avec {len(self.agents)} agents.")
    
    def _initialize_agents(self):
        """
        Initialise les agents de l'équipe Chaka.
        """
        # Configurations des agents
        agent_configs = self.config.get("agent_configs", {})
        
        # Créer l'agent d'imitation (Oba)
        self.agents["oba"] = Oba(
            config=agent_configs.get("oba", {}),
            anansi_core=self.anansi_core
        )
        
        # Créer l'agent de gestion des risques (Iklwa)
        self.agents["iklwa"] = Iklwa(
            config=agent_configs.get("iklwa", {}),
            anansi_core=self.anansi_core
        )
        
        # Créer l'agent de décision (Assegai)
        self.agents["assegai"] = Assegai(
            config=agent_configs.get("assegai", {}),
            anansi_core=self.anansi_core
        )
    
    def perceive(self, inputs):
        """
        Perçoit les données du marché et les informations pertinentes.
        
        Args:
            inputs: Dict contenant les données
                - market_data: Données du marché
                - chart_image: Chemin vers l'image du graphique
                - technical_analysis: Analyse technique (optionnel)
                - symbol: Symbole de l'instrument
                - timeframe: Timeframe d'analyse
                
        Returns:
            Dict contenant les perceptions
        """
        perceptions = {
            "timestamp": time.time(),
            "analysis_id": inputs.get("analysis_id", str(int(time.time()))),
            "symbol": inputs.get("symbol", "US30"),
            "timeframe": inputs.get("timeframe", "M1"),
            "market_data": {},
            "analysis_inputs": {},
            "has_chart_image": False,
            "external_analyses": []
        }
        
        # Récupérer les données du marché
        market_data = inputs.get("market_data", {})
        if market_data:
            perceptions["market_data"] = market_data
        
        # Vérifier si une image de graphique est fournie
        chart_image = inputs.get("chart_image")
        if chart_image and os.path.exists(chart_image):
            perceptions["has_chart_image"] = True
            perceptions["chart_image"] = chart_image
        
        # Collecter les analyses externes déjà disponibles
        for analysis_type in ["technical_analysis", "fundamental_analysis", "sentiment_analysis"]:
            if analysis_type in inputs:
                perceptions["external_analyses"].append({
                    "type": analysis_type.replace("_analysis", ""),
                    "data": inputs[analysis_type]
                })
        
        # Préparer les entrées pour les agents
        perceptions["analysis_inputs"] = {
            "market_data": perceptions["market_data"],
            "symbol": perceptions["symbol"],
            "timeframe": perceptions["timeframe"],
            "chart_image": perceptions.get("chart_image")
        }
        
        # Si nous avons une description du trader, l'ajouter
        if "trader_description" in inputs:
            perceptions["analysis_inputs"]["description"] = inputs["trader_description"]
        
        self.logger.info(f"Perception complétée pour {perceptions['symbol']} {perceptions['timeframe']}. Analyses externes: {len(perceptions['external_analyses'])}.")
        return perceptions
    
    def think(self, perceptions, context=None):
        """
        Analyse les perceptions et détermine le workflow d'analyse à exécuter.
        
        Args:
            perceptions: Dict des perceptions issues de perceive()
            context: Dict de contexte supplémentaire
                
        Returns:
            Dict des décisions à prendre
        """
        context = context or {}
        decisions = {
            "timestamp": time.time(),
            "analysis_id": perceptions["analysis_id"],
            "workflow": "full_analysis",
            "agents_to_run": ["oba", "iklwa", "assegai"],
            "run_sequence": ["oba", "iklwa", "assegai"],
            "parameters": {
                "symbol": perceptions["symbol"],
                "timeframe": perceptions["timeframe"]
            },
            "reasoning": []
        }
        
        # Déterminer le workflow à exécuter
        workflow_type = context.get("workflow_type", "full_analysis")
        
        if workflow_type == "quick_check":
            # Workflow rapide: juste l'analyse rapide puis la décision
            decisions["workflow"] = "quick_check"
            decisions["agents_to_run"] = ["assegai"]
            decisions["run_sequence"] = ["assegai"]
            decisions["reasoning"].append("Workflow rapide sélectionné: uniquement la décision finale sans analyses détaillées.")
        
        elif workflow_type == "risk_check":
            # Workflow de vérification du risque: seulement l'évaluation des risques
            decisions["workflow"] = "risk_check"
            decisions["agents_to_run"] = ["iklwa"]
            decisions["run_sequence"] = ["iklwa"]
            decisions["reasoning"].append("Workflow de vérification des risques sélectionné.")
        
        elif workflow_type == "imitation_only":
            # Workflow d'imitation: seulement l'agent d'imitation
            decisions["workflow"] = "imitation_only"
            decisions["agents_to_run"] = ["oba"]
            decisions["run_sequence"] = ["oba"]
            decisions["reasoning"].append("Workflow d'imitation sélectionné: uniquement l'agent Oba.")
        
        else:  # full_analysis
            # Workflow complet: analyse par Oba, évaluation des risques, puis décision finale
            decisions["workflow"] = "full_analysis"
            decisions["agents_to_run"] = ["oba", "iklwa", "assegai"]
            decisions["run_sequence"] = ["oba", "iklwa", "assegai"]
            decisions["reasoning"].append("Workflow d'analyse complète sélectionné: imitation, risque et décision finale.")
        
        # Préparer les paramètres pour chaque agent
        agent_parameters = {}
        
        # Paramètres de base communs
        base_params = {
            "symbol": perceptions["symbol"],
            "timeframe": perceptions["timeframe"],
            "market_data": perceptions["market_data"]
        }
        
        # Paramètres spécifiques pour Oba (imitation)
        oba_params = base_params.copy()
        if perceptions.get("has_chart_image", False):
            oba_params["chart_image"] = perceptions["chart_image"]
        if "description" in perceptions.get("analysis_inputs", {}):
            oba_params["description"] = perceptions["analysis_inputs"]["description"]
        agent_parameters["oba"] = oba_params
        
        # Paramètres pour Iklwa (risque)
        iklwa_params = base_params.copy()
        # On ajoutera les informations de compte et la proposition de trade plus tard
        agent_parameters["iklwa"] = iklwa_params
        
        # Paramètres pour Assegai (décision)
        assegai_params = base_params.copy()
        # On ajoutera les analyses des autres agents plus tard
        agent_parameters["assegai"] = assegai_params
        
        # Stocker les paramètres des agents
        decisions["agent_parameters"] = agent_parameters
        
        # Enregistrer l'analyse en cours
        self.state["active_analyses"][decisions["analysis_id"]] = {
            "timestamp": decisions["timestamp"],
            "symbol": perceptions["symbol"],
            "timeframe": perceptions["timeframe"],
            "workflow": decisions["workflow"],
            "status": "pending",
            "results": {}
        }
        
        self.logger.info(f"Décision: workflow {decisions['workflow']} avec {len(decisions['agents_to_run'])} agents.")
        return decisions
    
    def act(self, decisions):
        """
        Exécute le workflow d'analyse et de trading.
        
        Args:
            decisions: Dict des décisions issues de think()
            
        Returns:
            Dict des résultats des actions entreprises
        """
        results = {
            "timestamp": time.time(),
            "analysis_id": decisions["analysis_id"],
            "workflow": decisions["workflow"],
            "status": "in_progress",
            "agent_results": {},
            "final_decision": None,
            "execution_result": None,
            "message": ""
        }
        
        # Récupérer les paramètres
        analysis_id = decisions["analysis_id"]
        run_sequence = decisions["run_sequence"]
        agent_parameters = decisions["agent_parameters"]
        
        # Exécuter les agents dans l'ordre spécifié
        for agent_name in run_sequence:
            if agent_name not in self.agents:
                self.logger.error(f"Agent {agent_name} non disponible dans l'équipe Chaka.")
                continue
            
            try:
                agent = self.agents[agent_name]
                agent_params = agent_parameters.get(agent_name, {})
                
                # Mise à jour des paramètres en fonction des résultats précédents
                self._update_agent_parameters(agent_name, agent_params, results["agent_results"])
                
                # Exécuter le cycle cognitif de l'agent
                self.logger.info(f"Exécution de l'agent {agent_name} pour {analysis_id}...")
                agent_result = agent.cognitive_cycle(agent_params)
                
                # Stocker les résultats
                results["agent_results"][agent_name] = agent_result
                
                # Mettre à jour l'état de l'analyse active
                if analysis_id in self.state["active_analyses"]:
                    self.state["active_analyses"][analysis_id]["results"][agent_name] = agent_result
                
                self.logger.info(f"Agent {agent_name} exécuté avec succès.")
                
            except Exception as e:
                self.logger.error(f"Erreur lors de l'exécution de l'agent {agent_name}: {str(e)}")
                results["agent_results"][agent_name] = {"error": str(e)}
        
        # Extraire la décision finale si Assegai a été exécuté
        if "assegai" in results["agent_results"]:
            assegai_result = results["agent_results"]["assegai"]
            
            # Vérifier si l'exécution est un succès
            if isinstance(assegai_result, dict) and "error" not in assegai_result:
                # Chercher la décision de trading
                if "action_taken" in assegai_result:
                    # Si c'est le résultat de l'action (act)
                    results["final_decision"] = assegai_result.get("action_taken")
                    results["execution_result"] = assegai_result
                elif "action" in assegai_result:
                    # Si c'est le résultat de la réflexion (think)
                    results["final_decision"] = assegai_result.get("action")
        
        # Finaliser les résultats
        results["status"] = "completed"
        results["message"] = f"Workflow {decisions['workflow']} exécuté avec succès."
        
        # Mettre à jour l'historique
        self.state["workflow_history"].append({
            "timestamp": results["timestamp"],
            "analysis_id": analysis_id,
            "workflow": decisions["workflow"],
            "final_decision": results["final_decision"]
        })
        
        # Limiter la taille de l'historique
        if len(self.state["workflow_history"]) > 100:
            self.state["workflow_history"] = self.state["workflow_history"][-100:]
        
        # Mettre à jour le statut de l'analyse active
        if analysis_id in self.state["active_analyses"]:
            self.state["active_analyses"][analysis_id]["status"] = "completed"
            self.state["active_analyses"][analysis_id]["final_decision"] = results["final_decision"]
        
        self.logger.info(f"Workflow {decisions['workflow']} terminé. Décision: {results['final_decision']}.")
        return results
    
    def _update_agent_parameters(self, agent_name, params, previous_results):
        """
        Met à jour les paramètres d'un agent en fonction des résultats précédents.
        
        Args:
            agent_name: Nom de l'agent à mettre à jour
            params: Paramètres actuels de l'agent
            previous_results: Résultats des agents précédents
            
        Returns:
            Aucun, modifie params directement
        """
        if agent_name == "iklwa":
            # Iklwa (risque) a besoin des informations du compte et de l'opportunité de trading
            
            # Récupérer les informations du compte via MT5 si disponible
            if self.anansi_core and "mt5_connector" in self.anansi_core.agents:
                try:
                    connector = self.anansi_core.agents["mt5_connector"]
                    # Récupérer les informations du compte
                    account_info = connector.get_account_info()
                    if account_info:
                        params["account_info"] = account_info
                    
                    # Récupérer les positions ouvertes
                    positions = connector.get_positions()
                    if positions is not None:
                        params["open_positions"] = positions
                except Exception as e:
                    self.logger.error(f"Erreur lors de la récupération des informations du compte: {str(e)}")
            
            # Si Oba a été exécuté, utiliser ses résultats comme opportunité de trading
            if "oba" in previous_results:
                oba_result = previous_results["oba"]
                
                # Créer une opportunité de trading à partir des résultats de Oba
                trade_opportunity = self._extract_trade_opportunity_from_oba(oba_result)
                if trade_opportunity:
                    params["trade_opportunity"] = trade_opportunity
        
        elif agent_name == "assegai":
            # Assegai (décision) a besoin des analyses de tous les autres agents
            
            # Ajouter les résultats d'Oba comme analyse d'imitation
            if "oba" in previous_results:
                params["imitation_analysis"] = previous_results["oba"]
            
            # Ajouter les résultats d'Iklwa comme évaluation des risques
            if "iklwa" in previous_results:
                params["risk_assessment"] = previous_results["iklwa"]
            
            # Si une analyse technique externe est disponible, l'ajouter aussi
            # (Cette partie serait à adapter selon votre structure de données)
    
    def _extract_trade_opportunity_from_oba(self, oba_result):
        """
        Extrait une opportunité de trading des résultats de l'agent Oba.
        
        Args:
            oba_result: Résultat de l'agent Oba
            
        Returns:
            Dict représentant l'opportunité de trading ou None
        """
        # Vérifier que le résultat est valide
        if not isinstance(oba_result, dict):
            return None
        
        trade_opportunity = {}
        
        # Chercher l'action recommandée
        if "action" in oba_result:
            trade_opportunity["action"] = oba_result["action"]
        elif "action_taken" in oba_result:
            trade_opportunity["action"] = oba_result["action_taken"]
        
        # Chercher les niveaux de prix
        if "entry_price" in oba_result:
            trade_opportunity["entry"] = oba_result["entry_price"]
        
        if "stop_loss" in oba_result:
            trade_opportunity["stop_loss"] = oba_result["stop_loss"]
        
        if "take_profit" in oba_result:
            trade_opportunity["take_profit"] = oba_result["take_profit"]
        
        # Autres informations utiles
        if "confidence" in oba_result:
            trade_opportunity["confidence"] = oba_result["confidence"]
        
        # Ne retourner l'opportunité que si elle contient au moins une action
        return trade_opportunity if "action" in trade_opportunity else None
    
    def run_analysis(self, symbol, timeframe, chart_image=None, workflow_type="full_analysis", trader_description=None):
        """
        Point d'entrée principal pour exécuter une analyse de trading complète.
        
        Args:
            symbol: Symbole de l'instrument
            timeframe: Timeframe d'analyse
            chart_image: Chemin vers l'image du graphique (optionnel)
            workflow_type: Type de workflow à exécuter
            trader_description: Description textuelle du trader (optionnel)
            
        Returns:
            Résultats de l'analyse
        """
        # Générer un ID unique pour cette analyse
        analysis_id = f"analysis_{int(time.time())}_{symbol}_{timeframe}"
        
        # Récupérer les données du marché
        market_data = {}
        if self.anansi_core and "mt5_connector" in self.anansi_core.agents:
            try:
                connector = self.anansi_core.agents["mt5_connector"]
                price_data = connector.get_current_price(symbol)
                if price_data:
                    market_data = price_data
            except Exception as e:
                self.logger.error(f"Erreur lors de la récupération des données de marché: {str(e)}")
        
        # Préparer les inputs pour la perception
        inputs = {
            "analysis_id": analysis_id,
            "symbol": symbol,
            "timeframe": timeframe,
            "market_data": market_data
        }
        
        if chart_image:
            inputs["chart_image"] = chart_image
        
        if trader_description:
            inputs["trader_description"] = trader_description
        
        # Exécuter le cycle cognitif complet
        perceptions = self.perceive(inputs)
        decisions = self.think(perceptions, {"workflow_type": workflow_type})
        results = self.act(decisions)
        
        return results
    
    def get_active_analyses(self):
        """
        Récupère la liste des analyses actives.
        
        Returns:
            Dict des analyses actives
        """
        return self.state["active_analyses"]
    
    def get_workflow_history(self, limit=10):
        """
        Récupère l'historique des workflows exécutés.
        
        Args:
            limit: Nombre maximum d'entrées à récupérer
            
        Returns:
            Liste des workflows récents
        """
        history = self.state.get("workflow_history", [])
        return history[-limit:] if history else []
    
    def get_agent(self, agent_name):
        """
        Récupère un agent spécifique de l'équipe.
        
        Args:
            agent_name: Nom de l'agent à récupérer
            
        Returns:
            Instance de l'agent ou None si non trouvé
        """
        return self.agents.get(agent_name)
    
    def train_imitation_model(self, setup_types=None):
        """
        Entraîne le modèle d'imitation de l'agent Oba.
        
        Args:
            setup_types: Types de setup à inclure dans l'entraînement
            
        Returns:
            Résultats de l'entraînement
        """
        if "oba" not in self.agents:
            return {"success": False, "message": "Agent Oba non disponible."}
        
        return self.agents["oba"].train_model(setup_types)