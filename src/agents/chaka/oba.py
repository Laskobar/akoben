"""
Agent Oba - Agent d'imitation de trading pour l'équipe Chaka
"""

import os
import time
import json
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

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
        
        # Chemin vers les données standardisées
        self.standardized_data_path = self.config.get(
            "standardized_data_path", 
            str(Path.cwd() / "data" / "setups" / "standardized")
        )
        
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
            "prediction_history": [],
            "available_standardized_setups": self._get_available_standardized_setups()
        })
        
        self.logger.info(f"Agent Oba initialisé. Modèle chargé: {self.model_loaded}")
        self.logger.info(f"Nombre de setups standardisés disponibles: {len(self.state['available_standardized_setups'])}")
    
    def _get_available_standardized_setups(self) -> List[Dict[str, Any]]:
        """
        Découvre et indexe tous les setups standardisés disponibles.
        
        Returns:
            Liste des métadonnées des setups standardisés
        """
        setups = []
        standardized_path = Path(self.standardized_data_path)
        
        if not standardized_path.exists():
            self.logger.warning(f"Répertoire de données standardisées non trouvé: {standardized_path}")
            return []
        
        # Parcourir tous les dossiers de setup
        for setup_dir in standardized_path.iterdir():
            if not setup_dir.is_dir():
                continue
                
            metadata_file = setup_dir / "metadata.json"
            
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    # Ajouter le chemin du dossier à la métadonnée
                    metadata["directory"] = str(setup_dir)
                    
                    # Extraire l'action (BUY/SELL) du setup_id ou des métadonnées
                    if "action" not in metadata.get("standardized_info", {}):
                        setup_id = metadata.get("id", "").lower()
                        if "achat" in setup_id or "buy" in setup_id or "long" in setup_id:
                            metadata["standardized_info"]["action"] = "BUY"
                        elif "vente" in setup_id or "sell" in setup_id or "short" in setup_id:
                            metadata["standardized_info"]["action"] = "SELL"
                    
                    setups.append(metadata)
                    
                except Exception as e:
                    self.logger.error(f"Erreur lors de la lecture des métadonnées {metadata_file}: {str(e)}")
        
        self.logger.info(f"Découverte de {len(setups)} setups standardisés")
        return setups
    
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
                - standardized_setup_id: ID d'un setup standardisé à utiliser (optionnel)
                
        Returns:
            Dict contenant les perceptions
        """
        perceptions = {
            "timestamp": time.time(),
            "chart_analyzed": False,
            "market_context": {},
            "detected_patterns": [],
            "price_levels": {},
            "standardized_data_used": False
        }
        
        # Vérifier si un setup standardisé spécifique est demandé
        standardized_setup_id = inputs.get("standardized_setup_id")
        if standardized_setup_id:
            standardized_setup = self._get_standardized_setup(standardized_setup_id)
            if standardized_setup:
                perceptions["standardized_data"] = standardized_setup
                perceptions["standardized_data_used"] = True
                
                # Extraire les informations importantes
                std_info = standardized_setup.get("standardized_info", {})
                
                # Extraire les patterns
                if "patterns" in std_info and std_info["patterns"]:
                    perceptions["detected_patterns"] = [
                        {"name": pattern, "confidence": 0.9} 
                        for pattern in std_info["patterns"]
                    ]
                
                # Extraire les niveaux de prix
                price_levels = {}
                if "entry_price" in std_info and std_info["entry_price"]:
                    price_levels["entry"] = std_info["entry_price"]
                if "stop_loss" in std_info and std_info["stop_loss"]:
                    price_levels["stop_loss"] = std_info["stop_loss"]
                if "take_profit" in std_info and std_info["take_profit"]:
                    price_levels["take_profit"] = std_info["take_profit"]
                
                perceptions["price_levels"] = price_levels
                
                # Extraire le contexte de marché
                if "market_context" in std_info and std_info["market_context"]:
                    perceptions["market_context"]["description"] = std_info["market_context"]
                
                # Extraire les indicateurs
                if "indicators" in std_info and std_info["indicators"]:
                    perceptions["indicators"] = std_info["indicators"]
                
                # Extraire l'action attendue (pour l'entraînement)
                if "action" in std_info:
                    perceptions["expected_action"] = std_info["action"]
                
                self.logger.info(f"Perception basée sur le setup standardisé: {standardized_setup_id}")
                
                # Récupérer les images associées pour l'analyse visuelle
                if "directory" in standardized_setup:
                    image_files = self._get_setup_images(standardized_setup["directory"])
                    if image_files:
                        perceptions["chart_image"] = image_files[0]  # Utiliser la première image
                        perceptions["chart_analyzed"] = True
                        perceptions["all_images"] = image_files
        
        # Si aucun setup standardisé n'est fourni, utiliser l'approche traditionnelle
        if not perceptions["standardized_data_used"]:
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
    
    def _get_standardized_setup(self, setup_id: str) -> Dict[str, Any]:
        """
        Récupère les données d'un setup standardisé par son ID.
        
        Args:
            setup_id: ID du setup standardisé
            
        Returns:
            Données du setup ou None si non trouvé
        """
        for setup in self.state["available_standardized_setups"]:
            if setup.get("id") == setup_id:
                return setup
        
        # Si non trouvé dans l'index, chercher directement dans le répertoire
        setup_dir = Path(self.standardized_data_path) / setup_id
        if setup_dir.exists():
            metadata_file = setup_dir / "metadata.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    metadata["directory"] = str(setup_dir)
                    return metadata
                except Exception as e:
                    self.logger.error(f"Erreur lors de la lecture des métadonnées {metadata_file}: {str(e)}")
        
        return None
    
    def _get_setup_images(self, setup_dir: str) -> List[str]:
        """
        Récupère les chemins des images d'un setup.
        
        Args:
            setup_dir: Chemin du répertoire du setup
            
        Returns:
            Liste des chemins d'images
        """
        image_paths = []
        try:
            dir_path = Path(setup_dir)
            image_files = list(dir_path.glob("*.png")) + list(dir_path.glob("*.jpg"))
            image_paths = [str(img) for img in image_files]
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des images du setup: {str(e)}")
        
        return image_paths
    
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
        
        # Stratégie 0: Utiliser directement l'action attendue si disponible (mode entraînement/évaluation)
        if "expected_action" in perceptions:
            decisions["action"] = perceptions["expected_action"]
            decisions["confidence"] = 1.0
            decisions["reasoning"] = "Action basée sur le setup standardisé (mode entraînement/évaluation)."
        
        # Stratégie 1: Utiliser les données standardisées si disponibles
        elif perceptions.get("standardized_data_used", False) and "standardized_data" in perceptions:
            std_data = perceptions["standardized_data"]
            std_info = std_data.get("standardized_info", {})
            
            # Créer une représentation structurée des données standardisées
            features = self._extract_features_from_standardized_data(std_info)
            
            # Faire une prédiction basée sur les caractéristiques extraites
            prediction = self.imitation_manager.predict(features)
            
            if prediction:
                decisions["action"] = prediction["action"]
                if "confidences" in prediction:
                    decisions["confidence"] = max(prediction["confidences"].values()) if prediction["confidences"] else 0.0
                decisions["reasoning"] = prediction.get("explanation", "Décision basée sur les données standardisées.")
                decisions["features_used"] = prediction.get("features_used", [])
                
                # Récupérer les niveaux de prix des données standardisées
                if "entry_price" in std_info:
                    decisions["entry_price"] = std_info["entry_price"]
                if "stop_loss" in std_info:
                    decisions["stop_loss"] = std_info["stop_loss"]
                if "take_profit" in std_info:
                    decisions["take_profit"] = std_info["take_profit"]
        
        # Stratégie 2: Utiliser le modèle d'imitation si on a une description textuelle
        elif "text_analysis" in perceptions and "features" in perceptions:
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
        
        # Stratégie 3: Utiliser l'analyse de graphique si disponible
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
        
        # Récupérer les niveaux de prix s'ils n'ont pas déjà été définis
        if not all([decisions["entry_price"], decisions["stop_loss"], decisions["take_profit"]]):
            price_levels = perceptions.get("price_levels", {})
            if "entry" in price_levels and not decisions["entry_price"]:
                decisions["entry_price"] = price_levels["entry"]
            if "stop_loss" in price_levels and not decisions["stop_loss"]:
                decisions["stop_loss"] = price_levels["stop_loss"]
            if "take_profit" in price_levels and not decisions["take_profit"]:
                decisions["take_profit"] = price_levels["take_profit"]
        
        # Si le marché est trop volatil ou incertain, suggérer d'attendre
        market_context = perceptions.get("market_context", {})
        if market_context.get("volatility", 0) > 80 or market_context.get("uncertainty", 0) > 70:
            # Réduire la confiance si on a décidé d'agir
            if decisions["action"] in ["BUY", "SELL"]:
                decisions["confidence"] *= 0.7
                decisions["reasoning"] += "\nAttention: Conditions de marché volatiles détectées."
        
        # Enregistrer la prédiction dans l'historique
        self.state["prediction_history"].append({
            "timestamp": decisions["timestamp"],
            "action": decisions["action"],
            "confidence": decisions["confidence"]
        })
        self.state["last_prediction_time"] = decisions["timestamp"]
        self.state["last_prediction_result"] = decisions["action"]
        
        self.logger.info(f"Décision: {decisions['action']} avec {decisions['confidence']:.2%} de confiance")
        return decisions
    
    def _extract_features_from_standardized_data(self, std_info):
        """
        Extrait les caractéristiques d'un setup standardisé pour la prédiction.
    
        Args:
            std_info: Informations standardisées du setup
        
        Returns:
            Dictionnaire des caractéristiques
        """
        features = {}
    
        # Extraire les caractéristiques pertinentes
        if "patterns" in std_info and std_info["patterns"]:
            for pattern in std_info["patterns"]:
                if pattern:  # Vérifier que le pattern n'est pas None
                    features[f"pattern_{pattern.lower().replace(' ', '_')}"] = 1
    
        if "indicators" in std_info and std_info["indicators"]:
            for indicator in std_info["indicators"]:
                if indicator:  # Vérifier que l'indicateur n'est pas None
                    features[f"indicator_{indicator.lower().replace(' ', '_')}"] = 1
    
        # Calculer le ratio risque/récompense si possible
        if all(key in std_info and std_info[key] is not None for key in ["stop_loss", "take_profit", "entry_price"]):
            try:
                entry = float(std_info["entry_price"])
                sl = float(std_info["stop_loss"])
                tp = float(std_info["take_profit"])
            
                risk = abs(entry - sl)
                reward = abs(tp - entry)
            
                if risk > 0:
                    rr_ratio = reward / risk
                    features["risk_reward_ratio"] = rr_ratio
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Erreur de conversion lors du calcul du ratio R/R: {e}")
    
        # Ajouter d'autres caractéristiques si disponibles
        if "confidence" in std_info and std_info["confidence"] is not None:
            try:
                features["confidence"] = float(std_info["confidence"])
            except (ValueError, TypeError):
                pass
    
        if "timeframe" in std_info and std_info["timeframe"]:
            features[f"timeframe_{std_info['timeframe'].lower()}"] = 1
    
        if "instrument" in std_info and std_info["instrument"]:
            features[f"instrument_{std_info['instrument'].lower()}"] = 1
    
        return features
    
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
    
    def _prepare_training_data_from_standardized(self):
        """
        Prépare les données d'entraînement à partir des setups standardisés.
        
        Returns:
            Dict contenant les features et labels pour l'entraînement
        """
        self.logger.info("Préparation des données d'entraînement à partir des setups standardisés...")
        
        # Rafraîchir la liste des setups disponibles
        self.state["available_standardized_setups"] = self._get_available_standardized_setups()
        
        features_list = []
        labels = []
        
        for setup in self.state["available_standardized_setups"]:
            std_info = setup.get("standardized_info", {})
            
            # Vérifier que l'action est définie (BUY ou SELL)
            action = std_info.get("action")
            if not action:
                # Essayer de déduire l'action du nom du setup
                setup_id = setup.get("id", "").lower()
                if "achat" in setup_id or "buy" in setup_id or "long" in setup_id:
                    action = "BUY"
                elif "vente" in setup_id or "sell" in setup_id or "short" in setup_id:
                    action = "SELL"
                else:
                    self.logger.warning(f"Action non définie pour le setup {setup.get('id')}, ignoré.")
                    continue
            
            # Extraire les caractéristiques
            features = self._extract_features_from_standardized_data(std_info)
            
            if features:
                features_list.append(features)
                labels.append(action)
        
        if not features_list:
            self.logger.warning("Aucune donnée d'entraînement extraite des setups standardisés.")
            return None
        
        self.logger.info(f"Données d'entraînement préparées: {len(features_list)} exemples")
        
        return {
            "features": features_list,
            "labels": labels
        }
    
    def train_model(self, setup_types=None, use_standardized=True):
        """
        Entraîne ou met à jour le modèle d'imitation.
        
        Args:
            setup_types: Liste des types de setup à inclure dans l'entraînement
            use_standardized: Utiliser les données standardisées pour l'entraînement
            
        Returns:
            Résultats de l'entraînement
        """
        self.logger.info("Début de l'entraînement du modèle d'imitation...")
        
        try:
            # Utiliser les données standardisées si demandé
            if use_standardized:
                training_data = self._prepare_training_data_from_standardized()
            else:
                # Préparer les données avec la méthode traditionnelle
                training_data = self.imitation_manager.prepare_training_data(setup_types)
            
            if not training_data or len(training_data.get("labels", [])) < 10:
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
    
    def get_standardized_setups_stats(self):
        """
        Récupère des statistiques sur les setups standardisés disponibles.
        
        Returns:
            Statistiques sur les setups standardisés
        """
        # Rafraîchir la liste des setups disponibles
        self.state["available_standardized_setups"] = self._get_available_standardized_setups()
        
        # Initialiser les compteurs
        total_setups = len(self.state["available_standardized_setups"])
        buy_setups = 0
        sell_setups = 0
        undefined_action = 0
        setups_with_patterns = 0
        setups_with_indicators = 0
        setups_with_price_levels = 0
        patterns_counts = {}
        indicators_counts = {}
        
        # Analyser chaque setup
        for setup in self.state["available_standardized_setups"]:
            std_info = setup.get("standardized_info", {})
            
            # Compter par action
            action = std_info.get("action")
            if action:
                if action == "BUY":
                    buy_setups += 1
                elif action == "SELL":
                    sell_setups += 1
            else:
                undefined_action += 1
            
            # Compter les setups avec patterns
            if "patterns" in std_info and std_info["patterns"]:
                setups_with_patterns += 1
                for pattern in std_info["patterns"]:
                    patterns_counts[pattern] = patterns_counts.get(pattern, 0) + 1
            
            # Compter les setups avec indicateurs
            if "indicators" in std_info and std_info["indicators"]:
                setups_with_indicators += 1
                for indicator in std_info["indicators"]:
                    indicators_counts[indicator] = indicators_counts.get(indicator, 0) + 1
            
            # Compter les setups avec niveaux de prix
            if any([key in std_info for key in ["entry_price", "stop_loss", "take_profit"]]):
                setups_with_price_levels += 1
        
        # Compiler les statistiques
        return {
            "total_setups": total_setups,
            "buy_setups": buy_setups,
            "sell_setups": sell_setups,
            "undefined_action": undefined_action,
            "setups_with_patterns": setups_with_patterns,
            "setups_with_indicators": setups_with_indicators,
            "setups_with_price_levels": setups_with_price_levels,
            "patterns_counts": patterns_counts,
            "indicators_counts": indicators_counts,
            "directory": self.standardized_data_path
        }
    
    def test_model_on_standardized_setups(self, test_size=0.3, random_seed=42):
        """
        Teste le modèle sur un sous-ensemble des setups standardisés.
        
        Args:
            test_size: Proportion des données à utiliser pour le test (0.0 à 1.0)
            random_seed: Graine pour la reproductibilité des résultats
            
        Returns:
            Résultats des tests
        """
        # Vérifier que le modèle est chargé
        if not self.model_loaded and not self._load_model():
            return {"success": False, "message": "Aucun modèle d'imitation disponible."}
        
        # Rafraîchir la liste des setups disponibles
        self.state["available_standardized_setups"] = self._get_available_standardized_setups()
        
        # Préparer les données pour le test
        import random
        random.seed(random_seed)
        
        # Mélanger les setups disponibles
        setups = self.state["available_standardized_setups"].copy()
        random.shuffle(setups)
        
        # Calculer le nombre de setups pour le test
        test_count = max(1, int(len(setups) * test_size))
        test_setups = setups[:test_count]
        
        self.logger.info(f"Test du modèle sur {test_count} setups standardisés...")
        
        # Initialiser les résultats
        results = {
            "total_tests": test_count,
            "correct_predictions": 0,
            "incorrect_predictions": 0,
            "accuracy": 0.0,
            "details": []
        }
        
        # Tester chaque setup
        for setup in test_setups:
            std_info = setup.get("standardized_info", {})
            expected_action = std_info.get("action")
            
            # Ignorer les setups sans action définie
            if not expected_action:
                results["total_tests"] -= 1
                continue
            
            # Extraire les caractéristiques
            features = self._extract_features_from_standardized_data(std_info)
            
            # Faire une prédiction
            prediction = self.imitation_manager.predict(features)
            
            if not prediction:
                results["total_tests"] -= 1
                continue
            
            predicted_action = prediction.get("action")
            confidence = max(prediction.get("confidences", {}).values()) if prediction.get("confidences") else 0.0
            
            # Enregistrer les détails du test
            test_result = {
                "setup_id": setup.get("id"),
                "expected_action": expected_action,
                "predicted_action": predicted_action,
                "confidence": confidence,
                "correct": expected_action == predicted_action
            }
            
            results["details"].append(test_result)
            
            # Mettre à jour les compteurs
            if expected_action == predicted_action:
                results["correct_predictions"] += 1
            else:
                results["incorrect_predictions"] += 1
        
        # Calculer la précision
        if results["total_tests"] > 0:
            results["accuracy"] = results["correct_predictions"] / results["total_tests"]
        
        self.logger.info(f"Test terminé. Précision: {results['accuracy']:.2%}")
        return results        