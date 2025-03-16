"""
ImitationLearningManager - Gestionnaire d'apprentissage par imitation pour Akoben
"""

import os
import json
import time
import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from src.tools.setup_database_manager import SetupDatabaseManager
from src.tools.setup_text_processor import SetupTextProcessor

class ImitationLearningManager:
    """
    Gestionnaire pour l'apprentissage par imitation dans Akoben.
    Utilise les données annotées de trading pour entraîner le système
    à reproduire le style de trading du trader humain.
    """
    
    def __init__(self, config=None):
        """
        Initialise le gestionnaire d'apprentissage par imitation.
        
        Args:
            config: Configuration pour l'apprentissage par imitation
        """
        self.config = config or {}
        
        # Configuration des chemins
        self.data_root = self.config.get("data_root", "data/training")
        self.models_dir = self.config.get("models_dir", "data/models/imitation")
        self.results_dir = self.config.get("results_dir", "data/results/imitation")
        
        # Créer les répertoires nécessaires
        os.makedirs(self.data_root, exist_ok=True)
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Configuration du logger
        self.logger = logging.getLogger("akoben.learning.imitation")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # Initialiser les composants
        self.setup_db = SetupDatabaseManager(data_root=self.data_root)
        self.text_processor = SetupTextProcessor()
        
        # État de l'apprentissage
        self.training_history = []
        self.current_model = None
        
        self.logger.info("ImitationLearningManager initialisé")
    
    def prepare_training_data(self, setup_types=None, min_samples=10):
        """
        Prépare les données d'entraînement à partir des setups annotés.
        
        Args:
            setup_types: Liste des types de setup à inclure (None = tous)
            min_samples: Nombre minimum d'échantillons requis
            
        Returns:
            Dictionnaire contenant les données d'entraînement formatées
        """
        # Récupérer tous les setups ou ceux du type spécifié
        if setup_types:
            all_setups = []
            for setup_type in setup_types:
                all_setups.extend(self.setup_db.get_setups_by_type(setup_type))
        else:
            # Obtenir tous les setup_types disponibles
            all_setup_types = self.setup_db.get_all_setup_types()
            all_setups = []
            for setup_type in all_setup_types:
                all_setups.extend(self.setup_db.get_setups_by_type(setup_type))
        
        if len(all_setups) < min_samples:
            self.logger.warning(f"Nombre insuffisant d'échantillons: {len(all_setups)} < {min_samples}")
            return None
        
        # Structures pour les données d'entraînement
        training_data = {
            "image_paths": [],
            "text_descriptions": [],
            "structured_data": [],
            "features": [],
            "labels": []
        }
        
        # Traiter chaque setup
        for setup in all_setups:
            try:
                # Vérifier que les fichiers existent
                if not os.path.exists(setup["image_path"]) or not os.path.exists(setup["text_path"]):
                    continue
                
                # Lire le fichier texte
                with open(setup["text_path"], 'r', encoding='utf-8') as f:
                    text_content = f.read()
                
                # Extraire les informations structurées
                structured_info = self.text_processor.extract_from_text(text_content)
                standardized_info = self.text_processor.standardize_setup_info(structured_info)
                
                # Extraire les caractéristiques pour l'apprentissage
                features = self.text_processor.extract_key_elements(standardized_info)
                
                # Déterminer l'étiquette (action de trading)
                label = None
                if 'action' in standardized_info:
                    action = standardized_info['action'].lower()
                    if action in ['buy', 'long']:
                        label = 'BUY'
                    elif action in ['sell', 'short']:
                        label = 'SELL'
                    elif action in ['wait', 'hold', 'neutral']:
                        label = 'WAIT'
                
                # Ne conserver que les setups ayant une étiquette
                if label:
                    training_data["image_paths"].append(setup["image_path"])
                    training_data["text_descriptions"].append(text_content)
                    training_data["structured_data"].append(standardized_info)
                    training_data["features"].append(features)
                    training_data["labels"].append(label)
            
            except Exception as e:
                self.logger.error(f"Erreur lors du traitement du setup {setup.get('id')}: {str(e)}")
        
        self.logger.info(f"Données d'entraînement préparées: {len(training_data['labels'])} échantillons")
        
        # Statistiques de base
        label_counts = {}
        for label in training_data["labels"]:
            label_counts[label] = label_counts.get(label, 0) + 1
        
        self.logger.info(f"Distribution des étiquettes: {label_counts}")
        
        return training_data
    
    def encode_features(self, features_list):
        """
        Encode les caractéristiques textuelles en vecteurs numériques.
        
        Args:
            features_list: Liste des listes de caractéristiques textuelles
            
        Returns:
            Matrice de caractéristiques encodées
        """
        # Collecter toutes les caractéristiques uniques
        unique_features = set()
        for features in features_list:
            unique_features.update(features)
        
        # Créer un dictionnaire de correspondance
        feature_map = {feature: i for i, feature in enumerate(sorted(unique_features))}
        
        # Encoder les caractéristiques en vecteurs one-hot
        encoded_features = np.zeros((len(features_list), len(feature_map)))
        
        for i, features in enumerate(features_list):
            for feature in features:
                if feature in feature_map:
                    encoded_features[i, feature_map[feature]] = 1
        
        return encoded_features, feature_map
    
    def encode_labels(self, labels):
        """
        Encode les étiquettes textuelles en valeurs numériques.
        
        Args:
            labels: Liste des étiquettes textuelles
            
        Returns:
            Vecteur d'étiquettes encodées
        """
        unique_labels = sorted(set(labels))
        label_map = {label: i for i, label in enumerate(unique_labels)}
        
        encoded_labels = np.array([label_map[label] for label in labels])
        
        return encoded_labels, label_map
    
    def train_imitation_model(self, model_type="baseline", training_data=None):
        """
        Entraîne un modèle d'imitation sur les données d'entraînement.
        
        Args:
            model_type: Type de modèle à entraîner (baseline, decision_tree, neural_network)
            training_data: Données d'entraînement préparées (None = les préparer)
            
        Returns:
            Dictionnaire contenant le modèle entraîné et les métriques
        """
        try:
            from sklearn.model_selection import train_test_split
            from sklearn.tree import DecisionTreeClassifier
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.linear_model import LogisticRegression
            from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
        except ImportError:
            self.logger.error("scikit-learn non installé. Impossible d'entraîner le modèle.")
            return None
        
        # Préparer les données si non fournies
        if training_data is None:
            training_data = self.prepare_training_data()
            
        if training_data is None or len(training_data["labels"]) < 10:
            self.logger.error("Données d'entraînement insuffisantes.")
            return None
        
        # Encoder les caractéristiques et les étiquettes
        X, feature_map = self.encode_features(training_data["features"])
        y, label_map = self.encode_labels(training_data["labels"])
        
        # Division entraînement/test
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Sélection du modèle
        if model_type == "baseline":
            model = LogisticRegression(max_iter=1000, C=1.0)
            model_name = "logistic_regression"
        elif model_type == "decision_tree":
            model = DecisionTreeClassifier(max_depth=10)
            model_name = "decision_tree"
        elif model_type == "random_forest":
            model = RandomForestClassifier(n_estimators=100, max_depth=10)
            model_name = "random_forest"
        else:
            # Modèle par défaut
            model = LogisticRegression(max_iter=1000)
            model_name = "default_logistic_regression"
        
        # Entraînement
        start_time = time.time()
        model.fit(X_train, y_train)
        training_time = time.time() - start_time
        
        # Évaluation
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        classification_rep = classification_report(y_test, y_pred, target_names=[label_map[i] for i in range(len(label_map))], output_dict=True)
        conf_matrix = confusion_matrix(y_test, y_pred).tolist()
        
        # Créer le résultat
        result = {
            "model": model,
            "model_type": model_type,
            "model_name": model_name,
            "feature_map": feature_map,
            "label_map": {v: k for k, v in label_map.items()},  # Inverser pour faciliter l'utilisation
            "metrics": {
                "accuracy": accuracy,
                "classification_report": classification_rep,
                "confusion_matrix": conf_matrix,
                "training_time": training_time,
                "sample_count": len(y),
                "feature_count": len(feature_map)
            },
            "training_date": datetime.now().isoformat()
        }
        
        self.logger.info(f"Modèle {model_name} entraîné avec une précision de {accuracy:.4f}")
        
        # Sauvegarder le modèle
        self._save_model(result)
        
        # Mettre à jour l'historique d'entraînement
        self.training_history.append({
            "date": result["training_date"],
            "model_type": model_type,
            "accuracy": accuracy,
            "sample_count": len(y)
        })
        
        # Définir comme modèle actuel
        self.current_model = result
        
        return result
    
    def _save_model(self, model_result):
        """
        Sauvegarde un modèle entraîné.
        
        Args:
            model_result: Résultat de l'entraînement du modèle
        """
        try:
            import joblib
        except ImportError:
            self.logger.error("joblib non installé. Impossible de sauvegarder le modèle.")
            return
        
        # Créer un identifiant pour le modèle
        model_id = f"{model_result['model_name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        model_path = os.path.join(self.models_dir, f"{model_id}.joblib")
        
        # Sauvegarder le modèle avec joblib
        joblib.dump(model_result, model_path)
        
        # Sauvegarder les métriques séparément en JSON pour faciliter l'accès
        metrics_path = os.path.join(self.results_dir, f"{model_id}_metrics.json")
        with open(metrics_path, 'w') as f:
            json.dump({
                "model_id": model_id,
                "model_type": model_result["model_type"],
                "metrics": model_result["metrics"],
                "training_date": model_result["training_date"]
            }, f, indent=2)
        
        self.logger.info(f"Modèle sauvegardé: {model_path}")
    
    def load_model(self, model_id=None):
        """
        Charge un modèle entraîné.
        
        Args:
            model_id: Identifiant du modèle à charger (None = le plus récent)
            
        Returns:
            Modèle chargé ou None en cas d'échec
        """
        try:
            import joblib
        except ImportError:
            self.logger.error("joblib non installé. Impossible de charger le modèle.")
            return None
        
        # Si aucun ID n'est spécifié, charger le modèle le plus récent
        if model_id is None:
            model_files = [f for f in os.listdir(self.models_dir) if f.endswith('.joblib')]
            if not model_files:
                self.logger.error("Aucun modèle trouvé.")
                return None
            
            # Trier par date de modification
            model_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.models_dir, x)), reverse=True)
            model_id = os.path.splitext(model_files[0])[0]
        
        # Construire le chemin complet
        if not model_id.endswith('.joblib'):
            model_path = os.path.join(self.models_dir, f"{model_id}.joblib")
        else:
            model_path = os.path.join(self.models_dir, model_id)
        
        # Vérifier si le fichier existe
        if not os.path.exists(model_path):
            self.logger.error(f"Modèle {model_id} non trouvé.")
            return None
        
        # Charger le modèle
        try:
            model_result = joblib.load(model_path)
            self.current_model = model_result
            self.logger.info(f"Modèle {model_id} chargé avec succès.")
            return model_result
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement du modèle {model_id}: {str(e)}")
            return None
    
    def predict_from_setup(self, setup_id=None, image_path=None, text_description=None):
        """
        Prédit l'action à prendre pour un setup donné.
        
        Args:
            setup_id: ID du setup dans la base de données
            image_path: Chemin vers l'image du setup (alternative à setup_id)
            text_description: Description textuelle du setup (alternative à setup_id)
            
        Returns:
            Prédiction avec confiance et explications
        """
        # Vérifier qu'un modèle est chargé
        if self.current_model is None:
            try:
                self.load_model()
                if self.current_model is None:
                    self.logger.error("Aucun modèle disponible pour la prédiction.")
                    return None
            except Exception as e:
                self.logger.error(f"Erreur lors du chargement du modèle: {str(e)}")
                return None
        
        # Obtenir les informations du setup
        setup_info = None
        if setup_id:
            # Récupérer le setup de la base de données
            setup = self.setup_db.get_setup_by_id(setup_id)
            if setup:
                with open(setup["text_path"], 'r', encoding='utf-8') as f:
                    text_description = f.read()
        
        # Si aucune description textuelle n'est disponible, impossible de faire une prédiction
        if not text_description:
            self.logger.error("Description textuelle requise pour la prédiction.")
            return None
        
        # Extraire les informations structurées
        structured_info = self.text_processor.extract_from_text(text_description)
        standardized_info = self.text_processor.standardize_setup_info(structured_info)
        
        # Extraire les caractéristiques
        features = self.text_processor.extract_key_elements(standardized_info)
        
        # Encoder les caractéristiques
        feature_map = self.current_model["feature_map"]
        encoded_features = np.zeros(len(feature_map))
        
        for feature in features:
            if feature in feature_map:
                encoded_features[feature_map[feature]] = 1
        
        # Faire la prédiction
        try:
            # Obtenir la prédiction
            y_pred = self.current_model["model"].predict([encoded_features])[0]
            action = self.current_model["label_map"][y_pred]
            
            # Obtenir les probabilités si disponibles
            confidences = {}
            if hasattr(self.current_model["model"], 'predict_proba'):
                proba = self.current_model["model"].predict_proba([encoded_features])[0]
                for i, p in enumerate(proba):
                    label = self.current_model["label_map"][i]
                    confidences[label] = float(p)
            
            # Préparer l'explication
            explanation = self._generate_prediction_explanation(
                features, action, standardized_info, confidences
            )
            
            result = {
                "action": action,
                "confidences": confidences,
                "explanation": explanation,
                "features_used": features
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la prédiction: {str(e)}")
            return None
    
    def _generate_prediction_explanation(self, features, action, setup_info, confidences):
        """
        Génère une explication pour la prédiction.
        
        Args:
            features: Caractéristiques utilisées pour la prédiction
            action: Action prédite
            setup_info: Informations du setup
            confidences: Confiances pour chaque classe
            
        Returns:
            Explication textuelle
        """
        # Introduction
        explanation = f"Prédiction: {action}\n\n"
        
        # Ajouter les confiances si disponibles
        if confidences:
            explanation += "Confiance:\n"
            for label, conf in sorted(confidences.items(), key=lambda x: x[1], reverse=True):
                explanation += f"- {label}: {conf:.2%}\n"
            explanation += "\n"
        
        # Caractéristiques importantes
        explanation += "Caractéristiques clés détectées:\n"
        for feature in features:
            explanation += f"- {feature.replace('_', ' ').title()}\n"
        
        # Contexte du setup
        if setup_info.get('setup'):
            explanation += f"\nType de setup: {setup_info['setup']}\n"
        
        if setup_info.get('timeframe'):
            explanation += f"Timeframe: {setup_info['timeframe']}\n"
        
        # Niveaux de prix si disponibles
        price_levels = []
        if setup_info.get('entry'):
            price_levels.append(f"Entrée: {setup_info['entry']}")
        if setup_info.get('stop_loss'):
            price_levels.append(f"Stop Loss: {setup_info['stop_loss']}")
        if setup_info.get('take_profit'):
            price_levels.append(f"Take Profit: {setup_info['take_profit']}")
        
        if price_levels:
            explanation += "\nNiveaux de prix:\n" + "\n".join([f"- {level}" for level in price_levels]) + "\n"
        
        # Risque/Récompense
        if setup_info.get('risk_reward') or setup_info.get('risk_reward_ratio'):
            rr = setup_info.get('risk_reward') or setup_info.get('risk_reward_ratio')
            explanation += f"\nRatio Risque/Récompense: {rr}\n"
        
        return explanation
    
    def get_training_history(self):
        """
        Récupère l'historique des entraînements.
        
        Returns:
            Liste des entraînements effectués
        """
        return self.training_history
    
    def get_available_models(self):
        """
        Récupère la liste des modèles disponibles.
        
        Returns:
            Liste des informations sur les modèles
        """
        model_files = [f for f in os.listdir(self.models_dir) if f.endswith('.joblib')]
        models = []
        
        for model_file in model_files:
            model_id = os.path.splitext(model_file)[0]
            metrics_file = os.path.join(self.results_dir, f"{model_id}_metrics.json")
            
            info = {
                "id": model_id,
                "path": os.path.join(self.models_dir, model_file),
                "created": datetime.fromtimestamp(os.path.getmtime(os.path.join(self.models_dir, model_file))).isoformat()
            }
            
            # Ajouter les métriques si disponibles
            if os.path.exists(metrics_file):
                try:
                    with open(metrics_file, 'r') as f:
                        metrics = json.load(f)
                    info.update({
                        "model_type": metrics.get("model_type"),
                        "accuracy": metrics.get("metrics", {}).get("accuracy"),
                        "sample_count": metrics.get("metrics", {}).get("sample_count")
                    })
                except:
                    pass
            
            models.append(info)
        
        # Trier par date de création (plus récent en premier)
        models.sort(key=lambda x: x["created"], reverse=True)
        
        return models
    
    def delete_model(self, model_id):
        """
        Supprime un modèle.
        
        Args:
            model_id: ID du modèle à supprimer
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        # Construire les chemins
        model_path = os.path.join(self.models_dir, f"{model_id}.joblib")
        metrics_path = os.path.join(self.results_dir, f"{model_id}_metrics.json")
        
        # Vérifier si le modèle existe
        if not os.path.exists(model_path):
            self.logger.error(f"Modèle {model_id} non trouvé.")
            return False
        
        # Supprimer les fichiers
        try:
            os.remove(model_path)
            if os.path.exists(metrics_path):
                os.remove(metrics_path)
            
            self.logger.info(f"Modèle {model_id} supprimé.")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la suppression du modèle {model_id}: {str(e)}")
            return False