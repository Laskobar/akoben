"""
Akoben Nightly Retraining System - Système de réentraînement nocturne pour Akoben.
Ce script coordonne le processus d'entraînement quotidien du modèle d'imitation
en utilisant à la fois les données collectées depuis MT5 et les captures d'écran TradingView.
"""

import os
import sys
import json
import glob
import datetime
import logging
import time
import shutil
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import traceback

# Ajoute le répertoire parent au chemin d'import pour accéder aux modules Akoben
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Tente d'importer les modules Akoben
try:
    from src.learning.imitation_learning_manager import ImitationLearningManager
except ImportError:
    print("Erreur: Impossible d'importer les modules Akoben. Vérifiez votre PYTHONPATH.")
    sys.exit(1)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("nightly_retraining.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("NightlyRetraining")

class NightlyRetrainingSystem:
    """Système de réentraînement nocturne pour le modèle d'imitation Akoben."""
    
    def __init__(self, 
                 tradingview_base_dir=None,
                 mt5_data_dir=None,
                 models_dir=None,
                 backup_dir=None):
        """
        Initialise le système de réentraînement nocturne.
        
        Args:
            tradingview_base_dir (str): Répertoire contenant les captures TradingView.
            mt5_data_dir (str): Répertoire contenant les données MT5.
            models_dir (str): Répertoire pour stocker les modèles entraînés.
            backup_dir (str): Répertoire pour les sauvegardes des modèles.
        """
        # Configuration des répertoires
        home_dir = os.path.expanduser("~")
        akoben_dir = os.path.join(home_dir, "akoben")
        
        self.tradingview_base_dir = tradingview_base_dir or os.path.join(akoben_dir, "tradingview_captures")
        self.mt5_data_dir = mt5_data_dir or os.path.join(akoben_dir, "mt5_data")
        self.models_dir = models_dir or os.path.join(akoben_dir, "models")
        self.backup_dir = backup_dir or os.path.join(akoben_dir, "models_backup")
        
        # Assure que les répertoires existent
        for directory in [self.tradingview_base_dir, self.mt5_data_dir, 
                          self.models_dir, self.backup_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Initialise le gestionnaire d'apprentissage par imitation
        self.learning_manager = ImitationLearningManager()
        
        # Définit le chemin du modèle actuel
        self.current_model_path = os.path.join(self.models_dir, "current_model.joblib")
        self.model_info_path = os.path.join(self.models_dir, "model_info.json")
        
        # État d'avancement
        self.training_records = []
        self.validation_records = []
        
        logger.info("Système de réentraînement nocturne initialisé")
    
    def collect_tradingview_data(self) -> List[Dict[str, Any]]:
        """
        Collecte les données standardisées des captures TradingView.
        
        Returns:
            List[Dict[str, Any]]: Liste des données standardisées.
        """
        standardized_files = []
        
        # Parcours tous les dossiers de date
        for date_dir in glob.glob(os.path.join(self.tradingview_base_dir, "????-??-??")):
            if os.path.isdir(date_dir):
                # Parcours tous les dossiers de setup
                setup_dirs = glob.glob(os.path.join(date_dir, "setup_*"))
                for setup_dir in setup_dirs:
                    standard_file = os.path.join(setup_dir, "standardized.json")
                    if os.path.exists(standard_file):
                        standardized_files.append(standard_file)
        
        # Charge les données standardisées
        standardized_data = []
        for file_path in standardized_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Vérifie que les données contiennent les champs nécessaires
                    if all(key in data for key in ["instrument", "timeframe", "direction", "features"]):
                        standardized_data.append(data)
            except Exception as e:
                logger.error(f"Erreur lors de la lecture de {file_path}: {str(e)}")
        
        logger.info(f"Collecté {len(standardized_data)} exemples depuis TradingView")
        return standardized_data
    
    def collect_mt5_data(self) -> List[Dict[str, Any]]:
        """
        Collecte les données standardisées des sessions MT5.
        
        Returns:
            List[Dict[str, Any]]: Liste des données standardisées.
        """
        # Cherche les fichiers de données MT5
        mt5_files = glob.glob(os.path.join(self.mt5_data_dir, "**", "standardized_*.json"), recursive=True)
        
        # Charge les données standardisées
        standardized_data = []
        for file_path in mt5_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Vérifie que les données contiennent les champs nécessaires
                    if all(key in data for key in ["instrument", "timeframe", "direction", "features"]):
                        # Vérifie si les résultats de trade sont disponibles
                        result_file = file_path.replace("standardized_", "result_")
                        if os.path.exists(result_file):
                            # Si le résultat est disponible, on l'ajoute aux données
                            with open(result_file, 'r') as rf:
                                result_data = json.load(rf)
                                data["trade_result"] = result_data
                        
                        standardized_data.append(data)
            except Exception as e:
                logger.error(f"Erreur lors de la lecture de {file_path}: {str(e)}")
        
        logger.info(f"Collecté {len(standardized_data)} exemples depuis MT5")
        return standardized_data
    
    def prepare_training_data(self, 
                             tv_data: List[Dict[str, Any]], 
                             mt5_data: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prépare les données d'entraînement à partir des sources TradingView et MT5.
        
        Args:
            tv_data (List[Dict[str, Any]]): Données TradingView.
            mt5_data (List[Dict[str, Any]]): Données MT5.
            
        Returns:
            Tuple[pd.DataFrame, pd.Series]: Features X et labels y pour l'entraînement.
        """
        # Combine les données
        all_data = tv_data + mt5_data
        
        if not all_data:
            logger.error("Aucune donnée disponible pour l'entraînement")
            return pd.DataFrame(), pd.Series()
        
        # Extraction des caractéristiques
        features = []
        labels = []
        
        for item in all_data:
            # Extraction des caractéristiques de base
            feature_dict = {
                "instrument": item["instrument"],
                "timeframe": item["timeframe"],
                "setup_type": item["setup_type"],
                "confidence": item["confidence"]
            }
            
            # Extraction des caractéristiques avancées
            for category, values in item["features"].items():
                if isinstance(values, dict):
                    for key, value in values.items():
                        feature_name = f"{category}_{key}"
                        feature_dict[feature_name] = value
            
            # Convertit les caractéristiques textuelles en valeurs numériques
            processed_features = self._process_features(feature_dict)
            features.append(processed_features)
            
            # Extraction du label (direction)
            label = 1 if item["direction"] == "BUY" else 0
            labels.append(label)
        
        # Conversion en DataFrame et Series
        X = pd.DataFrame(features)
        y = pd.Series(labels)
        
        logger.info(f"Données préparées: {X.shape[0]} exemples avec {X.shape[1]} caractéristiques")
        return X, y
    
    def _process_features(self, feature_dict: Dict[str, Any]) -> Dict[str, float]:
        """
        Traite les caractéristiques pour les rendre utilisables par le modèle.
        
        Args:
            feature_dict (Dict[str, Any]): Dictionnaire des caractéristiques brutes.
            
        Returns:
            Dict[str, float]: Dictionnaire des caractéristiques numériques.
        """
        processed = {}
        
        # Mapping pour conversion texte -> numérique
        timeframe_map = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}
        trend_map = {"up": 1, "down": -1, "neutral": 0}
        volatility_map = {"low": 0.5, "medium": 1.0, "high": 1.5}
        volume_map = {"decreasing": -1, "stable": 0, "increasing": 1}
        indicator_map = {"positive": 1, "negative": -1, "neutral": 0}
        
        # Traitement des caractéristiques
        for key, value in feature_dict.items():
            if key == "instrument":
                # One-hot encoding pour l'instrument
                if value == "US30":
                    processed["is_US30"] = 1
                else:
                    processed["is_US30"] = 0
            elif key == "timeframe":
                # Conversion de timeframe en minutes
                processed["timeframe_minutes"] = timeframe_map.get(value, 0)
            elif key == "setup_type":
                # One-hot encoding pour les types de setup
                setup_types = ["Breakout", "Pullback", "Reversal", "Range", "Trend Continuation"]
                for st in setup_types:
                    processed[f"setup_{st}"] = 1 if value == st else 0
            elif key == "confidence":
                # Normalisation de la confiance (0-10 -> 0-1)
                processed["confidence"] = float(value) / 10.0
            elif key.startswith("price_action_"):
                # Traitement des caractéristiques de price action
                subkey = key.replace("price_action_", "")
                if subkey == "trend":
                    processed[key] = trend_map.get(value, 0)
                elif subkey == "volatility":
                    processed[key] = volatility_map.get(value, 1.0)
                elif subkey == "volume":
                    processed[key] = volume_map.get(value, 0)
                else:
                    processed[key] = float(value) if isinstance(value, (int, float)) else 0
            elif key.startswith("technical_indicators_"):
                # Traitement des indicateurs techniques
                processed[key] = indicator_map.get(value, 0)
            else:
                # Autres caractéristiques numériques
                processed[key] = float(value) if isinstance(value, (int, float)) else 0
        
        return processed
    
    def train_model(self, X: pd.DataFrame, y: pd.Series) -> Tuple[Any, Dict[str, Any]]:
        """
        Entraîne un nouveau modèle d'imitation.
        
        Args:
            X (pd.DataFrame): Caractéristiques d'entraînement.
            y (pd.Series): Labels (directions).
            
        Returns:
            Tuple[Any, Dict[str, Any]]: Modèle entraîné et métriques.
        """
        if X.empty or y.empty:
            logger.error("Données d'entraînement vides, impossible d'entraîner le modèle")
            return None, {}
        
        try:
            # Divise les données en ensembles d'entraînement et de validation
            from sklearn.model_selection import train_test_split
            X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Enregistre les données d'entraînement pour analyse future
            self.training_records = [(X_train.iloc[i].to_dict(), int(y_train.iloc[i])) for i in range(len(y_train))]
            self.validation_records = [(X_val.iloc[i].to_dict(), int(y_val.iloc[i])) for i in range(len(y_val))]
            
            # Entraîne le modèle RandomForest
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
            model.fit(X_train, y_train)
            
            # Évalue sur l'ensemble de validation
            y_pred = model.predict(X_val)
            accuracy = accuracy_score(y_val, y_pred)
            precision, recall, f1, _ = precision_recall_fscore_support(y_val, y_pred, average='binary')
            
            # Caractéristiques importantes
            importances = model.feature_importances_
            feature_importance = {}
            for i, feature in enumerate(X.columns):
                feature_importance[feature] = float(importances[i])
            
            # Prépare les métriques du modèle
            metrics = {
                "accuracy": float(accuracy),
                "precision": float(precision),
                "recall": float(recall),
                "f1": float(f1),
                "training_size": len(X_train),
                "validation_size": len(X_val),
                "feature_importance": feature_importance,
                "training_date": datetime.datetime.now().isoformat()
            }
            
            logger.info(f"Modèle entraîné avec succès. Accuracy: {accuracy:.4f}, F1: {f1:.4f}")
            return model, metrics
            
        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement du modèle: {str(e)}")
            logger.error(traceback.format_exc())
            return None, {}
    
    def evaluate_model_improvement(self, 
                                  new_metrics: Dict[str, Any], 
                                  current_metrics: Optional[Dict[str, Any]] = None) -> bool:
        """
        Évalue si le nouveau modèle est meilleur que le modèle actuel.
        
        Args:
            new_metrics (Dict[str, Any]): Métriques du nouveau modèle.
            current_metrics (Dict[str, Any], optional): Métriques du modèle actuel.
            
        Returns:
            bool: True si le nouveau modèle est meilleur, False sinon.
        """
        # Si aucun modèle actuel, le nouveau est forcément meilleur
        if current_metrics is None:
            return True
        
        # Vérifie si le nouveau modèle a une meilleure précision
        accuracy_threshold = 0.02  # 2% d'amélioration minimale
        current_accuracy = current_metrics.get("accuracy", 0)
        new_accuracy = new_metrics.get("accuracy", 0)
        
        # Vérifie si le nouveau modèle a un meilleur F1-score
        f1_threshold = 0.01  # 1% d'amélioration minimale
        current_f1 = current_metrics.get("f1", 0)
        new_f1 = new_metrics.get("f1", 0)
        
        # Le nouveau modèle est meilleur si l'une des métriques est significativement améliorée
        is_better = (new_accuracy >= current_accuracy + accuracy_threshold) or \
                    (new_f1 >= current_f1 + f1_threshold)
        
        # Même si les métriques ne sont pas significativement meilleures,
        # on peut quand même accepter le nouveau modèle s'il a plus de données d'entraînement
        if not is_better:
            current_size = current_metrics.get("training_size", 0)
            new_size = new_metrics.get("training_size", 0)
            size_improvement = 0.20  # 20% plus de données
            
            if new_size >= current_size * (1 + size_improvement) and new_accuracy >= current_accuracy - 0.01:
                # Si beaucoup plus de données et pas de régression significative
                is_better = True
                logger.info(f"Nouveau modèle accepté: +{(new_size-current_size)/current_size:.1%} données, " +
                           f"accuracy: {new_accuracy:.4f} vs {current_accuracy:.4f}")
        else:
            logger.info(f"Nouveau modèle accepté: Accuracy +{new_accuracy-current_accuracy:.4f}, " +
                       f"F1 +{new_f1-current_f1:.4f}")
        
        return is_better
    
    def save_model(self, model: Any, metrics: Dict[str, Any], is_better: bool) -> bool:
        """
        Sauvegarde le modèle entraîné et ses métriques.
        
        Args:
            model (Any): Modèle entraîné.
            metrics (Dict[str, Any]): Métriques du modèle.
            is_better (bool): Indique si ce modèle est meilleur que le précédent.
            
        Returns:
            bool: True si la sauvegarde a réussi, False sinon.
        """
        try:
            # Génère un identifiant unique pour ce modèle
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            model_id = f"model_{timestamp}"
            
            # Si le modèle est meilleur, fait une sauvegarde du modèle actuel
            if is_better and os.path.exists(self.current_model_path):
                # Crée un backup du modèle actuel
                backup_filename = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.joblib"
                backup_path = os.path.join(self.backup_dir, backup_filename)
                shutil.copy2(self.current_model_path, backup_path)
                
                # Copie également les infos du modèle
                if os.path.exists(self.model_info_path):
                    info_backup = backup_path.replace(".joblib", "_info.json")
                    shutil.copy2(self.model_info_path, info_backup)
                
                logger.info(f"Backup du modèle actuel créé: {backup_path}")
            
            # Sauvegarde le nouveau modèle
            model_path = os.path.join(self.models_dir, f"{model_id}.joblib")
            joblib.dump(model, model_path)
            
            # Sauvegarde les métriques
            metrics_path = os.path.join(self.models_dir, f"{model_id}_metrics.json")
            with open(metrics_path, 'w') as f:
                json.dump(metrics, f, indent=2)
            
            # Si le modèle est meilleur, met à jour le modèle actuel
            if is_better:
                if os.path.exists(self.current_model_path):
                    os.remove(self.current_model_path)
                shutil.copy2(model_path, self.current_model_path)
                
                # Met à jour les informations du modèle
                model_info = {
                    "model_id": model_id,
                    "metrics": metrics,
                    "update_date": datetime.datetime.now().isoformat(),
                    "training_records_count": len(self.training_records),
                    "validation_records_count": len(self.validation_records)
                }
                
                with open(self.model_info_path, 'w') as f:
                    json.dump(model_info, f, indent=2)
                
                logger.info(f"Modèle actuel mis à jour: {self.current_model_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du modèle: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def load_current_model_info(self) -> Optional[Dict[str, Any]]:
        """
        Charge les informations du modèle actuel.
        
        Returns:
            Optional[Dict[str, Any]]: Informations du modèle actuel, ou None si pas disponible.
        """
        if not os.path.exists(self.model_info_path):
            logger.info("Aucun modèle actuel trouvé")
            return None
        
        try:
            with open(self.model_info_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur lors du chargement des informations du modèle: {str(e)}")
            return None
    
    def deploy_model(self) -> bool:
        """
        Déploie le modèle entraîné dans le système Akoben.
        
        Returns:
            bool: True si le déploiement a réussi, False sinon.
        """
        if not os.path.exists(self.current_model_path):
            logger.error("Aucun modèle actuel à déployer")
            return False
        
        try:
            # Déploie le modèle dans le système Akoben
            # Dans une implémentation réelle, cela pourrait impliquer de redémarrer
            # certains services, de mettre à jour des configurations, etc.
            
            # Ici, nous simulons simplement un déploiement réussi
            logger.info("Modèle déployé avec succès")
            
            # Création d'un fichier indiquant que le modèle a été mis à jour
            update_marker = os.path.join(self.models_dir, "model_updated.flag")
            with open(update_marker, 'w') as f:
                f.write(datetime.datetime.now().isoformat())
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du déploiement du modèle: {str(e)}")
            return False
    
    def run(self) -> bool:
        """
        Exécute le processus complet de réentraînement nocturne.
        
        Returns:
            bool: True si le réentraînement a réussi, False sinon.
        """
        try:
            logger.info("Démarrage du processus de réentraînement nocturne")
            
            # 1. Collecte des données
            logger.info("Collecte des données...")
            tv_data = self.collect_tradingview_data()
            mt5_data = self.collect_mt5_data()
            
            total_examples = len(tv_data) + len(mt5_data)
            if total_examples == 0:
                logger.warning("Aucune donnée disponible pour l'entraînement")
                return False
            
            logger.info(f"Total: {total_examples} exemples ({len(tv_data)} TradingView, {len(mt5_data)} MT5)")
            
            # 2. Préparation des données
            logger.info("Préparation des données d'entraînement...")
            X, y = self.prepare_training_data(tv_data, mt5_data)
            
            if X.empty or y.empty:
                logger.warning("Échec de la préparation des données")
                return False
            
            # 3. Entraînement du modèle
            logger.info("Entraînement du nouveau modèle...")
            model, metrics = self.train_model(X, y)
            
            if model is None:
                logger.warning("Échec de l'entraînement du modèle")
                return False
            
            # 4. Évaluation de l'amélioration
            logger.info("Évaluation de l'amélioration du modèle...")
            current_info = self.load_current_model_info()
            current_metrics = current_info.get("metrics") if current_info else None
            
            is_better = self.evaluate_model_improvement(metrics, current_metrics)
            
            # 5. Sauvegarde du modèle
            logger.info(f"Sauvegarde du modèle (meilleur: {is_better})...")
            save_success = self.save_model(model, metrics, is_better)
            
            if not save_success:
                logger.warning("Échec de la sauvegarde du modèle")
                return False
            
            # 6. Déploiement si le modèle est meilleur
            if is_better:
                logger.info("Déploiement du nouveau modèle...")
                deploy_success = self.deploy_model()
                
                if not deploy_success:
                    logger.warning("Échec du déploiement du modèle")
                    return False
            else:
                logger.info("Le nouveau modèle n'est pas significativement meilleur, pas de déploiement")
            
            logger.info("Processus de réentraînement nocturne terminé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du processus de réentraînement: {str(e)}")
            logger.error(traceback.format_exc())
            return False

def main():
    """Point d'entrée principal."""
    retraining_system = NightlyRetrainingSystem()
    success = retraining_system.run()
    
    # Code de retour pour les scripts de déploiement
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()