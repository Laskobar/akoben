"""
Agent Oba - Agent d'imitation de trading pour l'équipe Chaka
"""

import os
import time
import json
from typing import Dict, Any, List, Optional

from src.anansi.agent_framework.autonomous_agent import AutonomousAgent
from src.learning.imitation_learning_manager import ImitationLearningManager
from src.tools.setup_text_processor import SetupTextProcessor

class Oba(AutonomousAgent):
    """
    Agent Oba - Spécialisé dans l'apprentissage par imitation du style de trading.
    
    Cet agent analyse les configurations de marché et reproduit les décisions
    d'un trader humain en se basant sur des exemples annotés.
    
    Fait partie de l'équipe Chaka (Trading).
    """
    
    def __init__(self, name="oba", config=None, anansi_core=None):
        """
        Initialise l'agent Oba.
        
        Args:
            name: Nom de l'agent
            config: Configuration de l'agent
            anansi_core: Référence au cerveau central Anansi
        """
        super().__init__(name, config, anansi_core)
        
        # Configuration spécifique
        self.config = config or {}
        
        # Initialiser les composants
        self.imitation_manager = ImitationLearningManager(self.config.get("imitation_config"))
        self.text_processor = SetupTextProcessor()
        
        # Chargement du modèle
        self.model_id = self.config.get("model_id")
        self.model_loaded = False
        self._load_model()
        
        # État interne spécifique à Oba
        self.state.update({
            "last_prediction_time": None,
            "last_prediction_result": None,
            "prediction_history": []
        })
        
        self.logger.info(f"Agent Oba initialisé. Modèle chargé: {self.model_loaded}")
    
    def _load_model(self):
        """
        Charge le modèle d'imitation.
        
        Returns:
            True si le chargement a réussi, False sinon
        """
        try:
            model_result = self.imitation_manager.load_model(self.model_id)
            self.model_loaded = model_result is not None
            
            if self.model_loaded:
                model_info = {
                    "type": model_result.get("model_type"),
                    "accuracy": model_result.get("metrics", {}).get("accuracy"),
                    "training_date": model_result.get("training_date")
                }
                self.logger.info(f"Modèle chargé: {model_info}")
            else:
                self.logger.warning("Aucun modèle d'imitation disponible. L'agent fonctionnera en mode limité.")
            
            return self.model_loaded
            
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement du modèle: {str(e)}")
            return False
    
    def perceive(self, inputs):
        """
        Perçoit les informations du marché et les configurations actuelles.
        
        Args:
            inputs: Dict contenant les paramètres d'entrée
                - chart_image: Chemin vers l'image du graphique (optionnel)
                - market_data: Données de marché structurées
                - description: Description textuelle (optionnel)
                
        Returns:
            Dict contenant les perceptions
        """
        perceptions = {
            "timestamp": time.time(),
            "chart_analyzed": False,
            "market_context": {},
            "detected_patterns": [],
            "price_levels": {}
        }
        
        # Extraire les informations de l'image du graphique
        chart_image = inputs.get("chart_image")
        if chart_image and os.path.exists(chart_image):
            perceptions["chart_analyzed"] = True
            perceptions["chart_image"] = chart_image
            
            # Si nous avons accès à l'agent de vision Kora, l'utiliser pour analyser le graphique
            if self.anansi_core and "vision_kora" in self.anansi_core.agents:
                kora_agent = self.anansi_core.agents["vision_kora"]
                vision_analysis = kora_agent.analyze_chart(image_path=chart_image)
                
                if "error" not in vision_analysis:
                    perceptions["chart_analysis"] = vision_analysis
                    perceptions["detected_patterns"] = vision_analysis.get("patterns", [])
                    
                    # Extraire les niveaux de prix détectés visuellement
                    if "detections" in vision_analysis:
                        if "support_levels" in vision_analysis["detections"]:
                            perceptions["price_levels"]["support"] = vision_analysis["detections"]["support_levels"]
                        if "resistance_levels" in vision_analysis["detections"]:
                            perceptions["price_levels"]["resistance"] = vision_analysis["detections"]["resistance_levels"]
        
        # Contexte de marché
        market_data = inputs.get("market_data", {})
        perceptions["market_context"] = market_data
        
        # Traiter la description textuelle si fournie
        description = inputs.get("description")
        if description:
            structured_info = self.text_processor.extract_from_text(description)
            standardized_info = self.text_processor.standardize_setup_info(structured_info)
            perceptions["text_analysis"] = standardized_info
            
            # Extraire les caractéristiques pour le modèle d'imitation
            features = self.text_processor.extract_key_elements(standardized_info)
            perceptions["features"] = features
            
            # Extraire les niveaux de prix de la description
            if "entry" in standardized_info:
                perceptions["price_levels"]["entry"] = standardized_info["entry"]
            if "stop_loss" in standardized_info:
                perceptions["price_levels"]["stop_loss"] = standardized_info["stop_loss"]
            if "take_profit" in standardized_info:
                perceptions["price_levels"]["take_profit"] = standardized_info["take_profit"]
        
        self.logger.info(f"Perception complétée. Graphique analysé: {perceptions['chart_analyzed']}, Patterns détectés: {len(perceptions['detected_patterns'])}")
        return perceptions
    
    def think(self, perceptions, context=None):
        """
        Analyse les perceptions et détermine les actions à entreprendre.
        
        Args:
            perceptions: Dict des perceptions issues de perceive()
            context: Dict de contexte supplémentaire
                
        Returns:
            Dict des décisions à prendre
        """
        context = context or {}
        decisions = {
            "timestamp": time.time(),
            "action": None,
            "confidence": 0.0,
            "entry_price": None,
            "stop_loss": None,
            "take_profit": None,
            "reasoning": "Analyse en cours...",
            "features_used": []
        }
        
        # Vérifier que le modèle est chargé
        if not self.model_loaded and not self._load_model():
            decisions["reasoning"] = "Aucun modèle d'imitation disponible. Impossible de prendre une décision."
            return decisions
        
        # Stratégie 1: Utiliser le modèle d'imitation si on a une description textuelle
        if "text_analysis" in perceptions and "features" in perceptions:
            # Créer une description structurée utilisable par le modèle
            description = self._generate_structured_description(perceptions)
            
            # Faire une prédiction
            prediction = self.imitation_manager.predict_from_setup(
                text_description=description
            )
            
            if prediction:
                decisions["action"] = prediction["action"]
                if "confidences" in prediction:
                    decisions["confidence"] = max(prediction["confidences"].values()) if prediction["confidences"] else 0.0
                decisions["reasoning"] = prediction.get("explanation", "Décision basée sur le modèle d'imitation.")
                decisions["features_used"] = prediction.get("features_used", [])
                
                # Enregistrer la prédiction dans l'historique
                self.state["prediction_history"].append({
                    "timestamp": decisions["timestamp"],
                    "action": decisions["action"],
                    "confidence": decisions["confidence"]
                })
                self.state["last_prediction_time"] = decisions["timestamp"]
                self.state["last_prediction_result"] = decisions["action"]
        
        # Stratégie 2: Utiliser l'analyse de graphique si disponible
        elif "chart_analysis" in perceptions:
            # Exploiter l'analyse du graphique
            chart_analysis = perceptions["chart_analysis"]
            chart_recommendation = chart_analysis.get("analysis", "").lower()
            
            # Déterminer l'action en fonction de l'analyse
            if "buy" in chart_recommendation or "long" in chart_recommendation:
                decisions["action"] = "BUY"
                decisions["confidence"] = 0.6  # Confiance réduite car basée uniquement sur l'analyse visuelle
            elif "sell" in chart_recommendation or "short" in chart_recommendation:
                decisions["action"] = "SELL"
                decisions["confidence"] = 0.6
            else:
                decisions["action"] = "WAIT"
                decisions["confidence"] = 0.5
            
            decisions["reasoning"] = f"Décision basée sur l'analyse visuelle du graphique: {chart_recommendation[:100]}..."
        
        # Si pas assez d'informations, attendre
        else:
            decisions["action"] = "WAIT"
            decisions["confidence"] = 0.3
            decisions["reasoning"] = "Informations insuffisantes pour prendre une décision éclairée."
        
        # Récupérer les niveaux de prix
        price_levels = perceptions.get("price_levels", {})
        if "entry" in price_levels:
            decisions["entry_price"] = price_levels["entry"]
        if "stop_loss" in price_levels:
            decisions["stop_loss"] = price_levels["stop_loss"]
        if "take_profit" in price_levels:
            decisions["take_profit"] = price_levels["take_profit"]
        
        # Si le marché est trop volatil ou incertain, suggérer d'attendre
        market_context = perceptions.get("market_context", {})
        if market_context.get("volatility", 0) > 80 or market_context.get("uncertainty", 0) > 70:
            # Réduire la confiance si on a décidé d'agir
            if decisions["action"] in ["BUY", "SELL"]:
                decisions["confidence"] *= 0.7
                decisions["reasoning"] += "\nAttention: Conditions de marché volatiles détectées."
        
        self.logger.info(f"Décision: {decisions['action']} avec {decisions['confidence']:.2%} de confiance")
        return decisions
    
    def act(self, decisions):
        """
        Exécute les actions déterminées par le processus de réflexion.
        
        Args:
            decisions: Dict des décisions issues de think()
            
        Returns:
            Dict des résultats des actions entreprises
        """
        results = {
            "timestamp": time.time(),
            "action_taken": decisions["action"],
            "execution_status": "completed",
            "message": "",
            "execution_details": {}
        }
        
        # Enregistrer l'action dans les logs
        self.logger.info(f"Exécution de l'action {decisions['action']} avec {decisions['confidence']:.2%} de confiance")
        
        # Vérifier si l'action doit être exécutée
        confidence_threshold = self.config.get("confidence_threshold", 0.7)
        if decisions["confidence"] < confidence_threshold and decisions["action"] in ["BUY", "SELL"]:
            results["action_taken"] = "WAIT"
            results["execution_status"] = "cancelled"
            results["message"] = f"Confiance insuffisante ({decisions['confidence']:.2%} < {confidence_threshold:.2%}) pour exécuter l'action {decisions['action']}."
            return results
        
        # Exécuter l'action
        if decisions["action"] in ["BUY", "SELL"]:
            # Si nous avons accès à l'agent d'exécution Fihavanana, l'utiliser pour l'ordre
            if self.anansi_core and "mt5_connector" in self.anansi_core.agents:
                executor = self.anansi_core.agents["mt5_connector"]
                
                # Préparer les paramètres de l'ordre
                order_params = {
                    "symbol": decisions.get("symbol", "US30"),
                    "order_type": decisions["action"],
                    "volume": self.config.get("default_volume", 0.01),
                    "price": 0,  # 0 = prix du marché
                    "sl": decisions.get("stop_loss", 0),
                    "tp": decisions.get("take_profit", 0),
                    "comment": "Akoben-Oba Imitation"
                }
                
                # Soumettre l'ordre
                try:
                    order_result = executor.place_order(**order_params)
                    
                    if order_result:
                        results["execution_status"] = "success"
                        results["message"] = f"Ordre {decisions['action']} exécuté avec succès."
                        results["execution_details"] = order_result
                    else:
                        results["execution_status"] = "failed"
                        results["message"] = f"Échec de l'exécution de l'ordre {decisions['action']}."
                        
                except Exception as e:
                    results["execution_status"] = "error"
                    results["message"] = f"Erreur lors de l'exécution de l'ordre: {str(e)}"
            else:
                # Mode simulation si l'exécuteur n'est pas disponible
                results["execution_status"] = "simulated"
                results["message"] = f"Mode simulation: Ordre {decisions['action']} à {decisions.get('entry_price', 'prix du marché')}."
                results["execution_details"] = {
                    "simulated": True,
                    "action": decisions["action"],
                    "entry": decisions.get("entry_price"),
                    "stop_loss": decisions.get("stop_loss"),
                    "take_profit": decisions.get("take_profit"),
                    "timestamp": results["timestamp"]
                }
        
        elif decisions["action"] == "WAIT":
            # Aucune action à exécuter
            results["message"] = "Décision d'attente. Aucun ordre exécuté."
        
        else:
            # Action non reconnue
            results["execution_status"] = "unknown"
            results["message"] = f"Action {decisions['action']} non reconnue."
        
        return results
    
    def _generate_structured_description(self, perceptions):
        """
        Génère une description textuelle structurée à partir des perceptions.
        
        Args:
            perceptions: Dict des perceptions
            
        Returns:
            Description textuelle structurée
        """
        # Commencer par les informations textuelles si disponibles
        if "text_analysis" in perceptions:
            text_analysis = perceptions["text_analysis"]
            return self.text_processor.text_to_structured_format(text_analysis).get("structured_text", "")
        
        # Sinon, créer une description à partir des perceptions disponibles
        description = "Setup: Market Analysis\n"
        
        # Contexte de marché
        market_context = perceptions.get("market_context", {})
        if market_context:
            description += f"Timeframe: {market_context.get('timeframe', 'unknown')}\n"
        
        # Patterns détectés
        patterns = perceptions.get("detected_patterns", [])
        if patterns:
            description += "\nPatterns:\n"
            for pattern in patterns:
                description += f"- {pattern.get('name', 'Unknown pattern')}\n"
        
        # Niveaux de prix
        price_levels = perceptions.get("price_levels", {})
        if price_levels:
            description += "\nPrice Levels:\n"
            for level_type, level_value in price_levels.items():
                description += f"- {level_type.capitalize()}: {level_value}\n"
        
        # Analyse du graphique
        if "chart_analysis" in perceptions:
            description += f"\nChart Analysis:\n{perceptions['chart_analysis'].get('analysis', '')}\n"
        
        return description
    
    def train_model(self, setup_types=None):
        """
        Entraîne ou met à jour le modèle d'imitation.
        
        Args:
            setup_types: Liste des types de setup à inclure dans l'entraînement
            
        Returns:
            Résultats de l'entraînement
        """
        self.logger.info("Début de l'entraînement du modèle d'imitation...")
        
        try:
            # Préparer les données
            training_data = self.imitation_manager.prepare_training_data(setup_types)
            
            if not training_data or len(training_data["labels"]) < 10:
                self.logger.error("Données d'entraînement insuffisantes.")
                return {"success": False, "message": "Données d'entraînement insuffisantes."}
            
            # Entraîner le modèle
            model_result = self.imitation_manager.train_imitation_model(
                model_type=self.config.get("model_type", "random_forest"),
                training_data=training_data
            )
            
            if model_result:
                self.model_loaded = True
                self.model_id = model_result.get("model_name") + "_" + model_result.get("training_date", "").replace(":", "-")
                
                return {
                    "success": True,
                    "message": "Modèle entraîné avec succès.",
                    "model_id": self.model_id,
                    "accuracy": model_result.get("metrics", {}).get("accuracy"),
                    "sample_count": model_result.get("metrics", {}).get("sample_count")
                }
            else:
                return {"success": False, "message": "Échec de l'entraînement du modèle."}
                
        except Exception as e:
            self.logger.error(f"Erreur lors de l'entraînement du modèle: {str(e)}")
            return {"success": False, "message": f"Erreur: {str(e)}"}
    
    def get_model_info(self):
        """
        Récupère les informations sur le modèle actuel.
        
        Returns:
            Informations sur le modèle
        """
        if not self.model_loaded:
            return {"status": "not_loaded", "message": "Aucun modèle chargé."}
        
        try:
            # Récupérer les informations du modèle
            current_model = self.imitation_manager.current_model
            
            if not current_model:
                return {"status": "error", "message": "Informations du modèle non disponibles."}
            
            return {
                "status": "loaded",
                "model_id": self.model_id,
                "model_type": current_model.get("model_type"),
                "training_date": current_model.get("training_date"),
                "metrics": current_model.get("metrics", {}),
                "feature_count": len(current_model.get("feature_map", {})),
                "label_count": len(current_model.get("label_map", {}))
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Erreur: {str(e)}"}
    
    def get_all_available_models(self):
        """
        Récupère la liste de tous les modèles disponibles.
        
        Returns:
            Liste des modèles disponibles
        """
        return self.imitation_manager.get_available_models()