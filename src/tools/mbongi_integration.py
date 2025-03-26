"""
MBONGI Integration - Module d'intégration pour synchroniser les descriptions MBONGI
générées automatiquement avec l'agent documentaliste MBONGI existant.
"""

import os
import sys
import json
import glob
import datetime
import logging
import time
import subprocess
import argparse
import shutil
from typing import Dict, List, Any, Optional
import git
import re

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mbongi_integration.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("MbongiIntegration")

class MbongiIntegration:
    """Module d'intégration pour synchroniser les descriptions MBONGI avec l'agent documentaliste."""
    
    def __init__(self, base_dir=None, docs_dir=None):
        """
        Initialise le module d'intégration MBONGI.
        
        Args:
            base_dir (str): Répertoire de base pour le système Akoben.
            docs_dir (str): Répertoire de documentation MBONGI.
        """
        # Configuration des répertoires
        if base_dir is None:
            self.base_dir = os.path.join(os.path.expanduser("~"), "akoben")
        else:
            self.base_dir = base_dir
        
        if docs_dir is None:
            self.docs_dir = os.path.join(self.base_dir, "docs")
        else:
            self.docs_dir = docs_dir
        
        # Structure des répertoires
        self.tradingview_dir = os.path.join(self.base_dir, "tradingview_captures")
        self.setups_doc_dir = os.path.join(self.docs_dir, "setups")
        self.models_doc_dir = os.path.join(self.docs_dir, "models")
        
        # S'assure que les répertoires existent
        for directory in [self.docs_dir, self.setups_doc_dir, self.models_doc_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Vérifie si le répertoire docs est un dépôt git
        self.git_repo = None
        try:
            if os.path.exists(os.path.join(self.docs_dir, ".git")):
                self.git_repo = git.Repo(self.docs_dir)
                logger.info(f"Dépôt Git trouvé: {self.docs_dir}")
        except Exception as e:
            logger.warning(f"Erreur lors de l'accès au dépôt Git: {str(e)}")
        
        logger.info(f"Module d'intégration MBONGI initialisé avec répertoire de base: {self.base_dir}")
    
    def find_new_mbongi_descriptions(self) -> List[Dict[str, str]]:
        """
        Trouve les nouvelles descriptions MBONGI générées automatiquement.
        
        Returns:
            List[Dict[str, str]]: Liste des chemins de fichiers et métadonnées associées.
        """
        # Liste tous les répertoires de setup
        new_descriptions = []
        
        for date_dir in glob.glob(os.path.join(self.tradingview_dir, "????-??-??")):
            if os.path.isdir(date_dir):
                # Parcours tous les dossiers de setup
                setup_dirs = glob.glob(os.path.join(date_dir, "setup_*"))
                for setup_dir in setup_dirs:
                    mbongi_file = os.path.join(setup_dir, "mbongi_standard.md")
                    metadata_file = os.path.join(setup_dir, "metadata.json")
                    
                    # Vérifie que les fichiers existent
                    if os.path.exists(mbongi_file) and os.path.exists(metadata_file):
                        # Vérifie si la description a déjà été intégrée
                        setup_id = os.path.basename(setup_dir)
                        doc_file = os.path.join(self.setups_doc_dir, f"{setup_id}.md")
                        
                        if not os.path.exists(doc_file):
                            # Charge les métadonnées
                            try:
                                with open(metadata_file, 'r') as f:
                                    metadata = json.load(f)
                                
                                new_descriptions.append({
                                    "setup_id": setup_id,
                                    "mbongi_file": mbongi_file,
                                    "metadata": metadata,
                                    "date_dir": os.path.basename(date_dir)
                                })
                            except Exception as e:
                                logger.error(f"Erreur lors de la lecture des métadonnées pour {setup_id}: {str(e)}")
        
        logger.info(f"Trouvé {len(new_descriptions)} nouvelles descriptions MBONGI")
        return new_descriptions
    
    def integrate_description(self, description_info: Dict[str, Any]) -> bool:
        """
        Intègre une description MBONGI dans le système de documentation.
        
        Args:
            description_info (Dict[str, Any]): Informations sur la description à intégrer.
            
        Returns:
            bool: True si l'intégration a réussi, False sinon.
        """
        try:
            setup_id = description_info["setup_id"]
            mbongi_file = description_info["mbongi_file"]
            metadata = description_info["metadata"]
            date_dir = description_info["date_dir"]
            
            # Lecture du fichier MBONGI
            with open(mbongi_file, 'r') as f:
                mbongi_content = f.read()
            
            # Création du fichier documentation
            doc_file = os.path.join(self.setups_doc_dir, f"{setup_id}.md")
            
            # Ajout d'informations supplémentaires
            doc_content = f"""---
setup_id: {setup_id}
date: {date_dir}
instrument: {metadata.get('instrument', 'Inconnu')}
timeframe: {metadata.get('timeframe', 'Inconnu')}
direction: {metadata.get('direction', 'Inconnu')}
confidence: {metadata.get('confidence', 0)}
import_date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
---

{mbongi_content}

## Métadonnées système
- **ID du setup**: `{setup_id}`
- **Date d'import**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Source**: Capture TradingView importée
"""
            
            # Sauvegarde du fichier
            with open(doc_file, 'w') as f:
                f.write(doc_content)
            
            logger.info(f"Description MBONGI intégrée avec succès: {setup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'intégration de la description: {str(e)}")
            return False
    
    def update_model_documentation(self) -> bool:
        """
        Met à jour la documentation des modèles d'imitation.
        
        Returns:
            bool: True si la mise à jour a réussi, False sinon.
        """
        try:
            # Vérifier si de nouveaux modèles ont été déployés
            models_dir = os.path.join(self.base_dir, "models")
            model_info_path = os.path.join(models_dir, "model_info.json")
            
            if not os.path.exists(model_info_path):
                logger.warning("Aucune information de modèle trouvée")
                return False
            
            # Charge les informations du modèle actuel
            with open(model_info_path, 'r') as f:
                model_info = json.load(f)
            
            # Crée ou met à jour le fichier de documentation du modèle
            model_id = model_info.get("model_id", "unknown")
            doc_file = os.path.join(self.models_doc_dir, f"{model_id}.md")
            update_date = model_info.get("update_date", datetime.datetime.now().isoformat())
            
            # Convertit ISO date en format lisible
            try:
                dt = datetime.datetime.fromisoformat(update_date)
                update_date_formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                update_date_formatted = update_date
            
            # Extraction et formatage des métriques
            metrics = model_info.get("metrics", {})
            accuracy = metrics.get("accuracy", 0) * 100
            precision = metrics.get("precision", 0) * 100
            recall = metrics.get("recall", 0) * 100
            f1 = metrics.get("f1", 0) * 100
            
            training_size = metrics.get("training_size", 0)
            validation_size = metrics.get("validation_size", 0)
            
            # Extraction des caractéristiques importantes
            feature_importance = metrics.get("feature_importance", {})
            sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
            
            # Création du contenu de documentation
            doc_content = f"""# Modèle d'imitation: {model_id}

## Informations générales
- **ID du modèle**: `{model_id}`
- **Date de déploiement**: {update_date_formatted}
- **Type de modèle**: RandomForest

## Performances
- **Précision (Accuracy)**: {accuracy:.2f}%
- **Précision (Precision)**: {precision:.2f}%
- **Rappel (Recall)**: {recall:.2f}%
- **Score F1**: {f1:.2f}%

## Données d'entraînement
- **Taille de l'ensemble d'entraînement**: {training_size} exemples
- **Taille de l'ensemble de validation**: {validation_size} exemples
- **Taille totale**: {training_size + validation_size} exemples

## Caractéristiques importantes
"""
            
            # Ajoute les 10 caractéristiques les plus importantes
            for i, (feature, importance) in enumerate(sorted_features[:10]):
                doc_content += f"{i+1}. **{feature}**: {importance:.4f}\n"
            
            # Ajoute des informations sur la version précédente
            doc_content += f"""
## Historique
- **Créé le**: {update_date_formatted}
- **Remplace**: Version précédente
"""
            
            # Sauvegarde du fichier
            with open(doc_file, 'w') as f:
                f.write(doc_content)
            
            # Met à jour l'index des modèles
            self.update_models_index()
            
            logger.info(f"Documentation du modèle mise à jour avec succès: {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la documentation du modèle: {str(e)}")
            return False
    
    def update_models_index(self) -> bool:
        """
        Met à jour l'index des modèles.
        
        Returns:
            bool: True si la mise à jour a réussi, False sinon.
        """
        try:
            # Liste tous les fichiers de documentation de modèles
            model_files = glob.glob(os.path.join(self.models_doc_dir, "*.md"))
            
            # Extrait les informations de base de chaque modèle
            models_info = []
            
            for model_file in model_files:
                model_id = os.path.basename(model_file).replace(".md", "")
                
                # Lit le fichier pour extraire les informations
                with open(model_file, 'r') as f:
                    content = f.read()
                
                # Extrait la date et les performances
                date_match = re.search(r"Date de déploiement\**: (.+)", content)
                accuracy_match = re.search(r"Précision \(Accuracy\)\**: ([0-9.]+)%", content)
                
                date = date_match.group(1) if date_match else "Inconnue"
                accuracy = accuracy_match.group(1) if accuracy_match else "0"
                
                models_info.append({
                    "model_id": model_id,
                    "file": os.path.basename(model_file),
                    "date": date,
                    "accuracy": accuracy
                })
            
            # Trie les modèles par date (du plus récent au plus ancien)
            models_info.sort(key=lambda x: x["date"], reverse=True)
            
            # Crée le fichier d'index
            index_file = os.path.join(self.models_doc_dir, "index.md")
            
            index_content = f"""# Index des modèles d'imitation

Ce document répertorie tous les modèles d'imitation entraînés dans le système Akoben.

## Modèles par date

| ID du modèle | Date de déploiement | Précision |
|-------------|---------------------|-----------|
"""
            
            for model in models_info:
                index_content += f"| [{model['model_id']}](./{model['file']}) | {model['date']} | {model['accuracy']}% |\n"
            
            # Ajoute une section pour le modèle actuel
            index_content += """
## Modèle actuel

Le modèle actuel utilisé par le système Akoben est le plus récent de la liste ci-dessus.
"""
            
            # Sauvegarde du fichier
            with open(index_file, 'w') as f:
                f.write(index_content)
            
            logger.info("Index des modèles mis à jour avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'index des modèles: {str(e)}")
            return False
    
    def update_setups_index(self) -> bool:
        """
        Met à jour l'index des setups.
        
        Returns:
            bool: True si la mise à jour a réussi, False sinon.
        """
        try:
            # Liste tous les fichiers de documentation de setups
            setup_files = glob.glob(os.path.join(self.setups_doc_dir, "*.md"))
            
            # Extrait les informations de base de chaque setup
            setups_info = []
            
            for setup_file in setup_files:
                setup_id = os.path.basename(setup_file).replace(".md", "")
                
                # Lit le fichier pour extraire les informations
                with open(setup_file, 'r') as f:
                    content = f.read()
                
                # Extrait les métadonnées du frontmatter
                instrument_match = re.search(r"instrument: (.+)", content)
                timeframe_match = re.search(r"timeframe: (.+)", content)
                direction_match = re.search(r"direction: (.+)", content)
                date_match = re.search(r"date: (.+)", content)
                
                instrument = instrument_match.group(1) if instrument_match else "Inconnu"
                timeframe = timeframe_match.group(1) if timeframe_match else "Inconnu"
                direction = direction_match.group(1) if direction_match else "Inconnu"
                date = date_match.group(1) if date_match else "Inconnue"
                
                setups_info.append({
                    "setup_id": setup_id,
                    "file": os.path.basename(setup_file),
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "direction": direction,
                    "date": date
                })
            
            # Trie les setups par date (du plus récent au plus ancien)
            setups_info.sort(key=lambda x: x["date"], reverse=True)
            
            # Crée le fichier d'index
            index_file = os.path.join(self.setups_doc_dir, "index.md")
            
            index_content = f"""# Index des setups de trading

Ce document répertorie tous les setups de trading documentés dans le système Akoben.

## Setups par date

| Date | Instrument | Timeframe | Direction | Setup ID |
|------|------------|-----------|-----------|----------|
"""
            
            for setup in setups_info:
                index_content += f"| {setup['date']} | {setup['instrument']} | {setup['timeframe']} | {setup['direction']} | [{setup['setup_id']}](./{setup['file']}) |\n"
            
            # Ajoute des statistiques
            buy_count = sum(1 for setup in setups_info if setup["direction"] == "BUY")
            sell_count = sum(1 for setup in setups_info if setup["direction"] == "SELL")
            
            index_content += f"""
## Statistiques

- **Nombre total de setups**: {len(setups_info)}
- **Setups BUY**: {buy_count} ({buy_count / len(setups_info) * 100:.1f}%)
- **Setups SELL**: {sell_count} ({sell_count / len(setups_info) * 100:.1f}%)
"""
            
            # Sauvegarde du fichier
            with open(index_file, 'w') as f:
                f.write(index_content)
            
            logger.info("Index des setups mis à jour avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'index des setups: {str(e)}")
            return False
    
    def commit_changes(self) -> bool:
        """
        Commit les changements dans le dépôt Git.
        
        Returns:
            bool: True si le commit a réussi, False sinon.
        """
        if self.git_repo is None:
            logger.warning("Aucun dépôt Git disponible, les changements ne seront pas commités")
            return False
        
        try:
            # Vérifie s'il y a des changements
            if not self.git_repo.is_dirty(untracked_files=True):
                logger.info("Aucun changement à commiter")
                return True
            
            # Ajoute tous les fichiers
            self.git_repo.git.add(all=True)
            
            # Crée un message de commit
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_message = f"Mise à jour automatique de la documentation ({timestamp})"
            
            # Commit les changements
            self.git_repo.git.commit(m=commit_message)
            
            # Push les changements si un remote est configuré
            if self.git_repo.remotes:
                self.git_repo.git.push()
                logger.info("Changements commités et poussés avec succès")
            else:
                logger.info("Changements commités avec succès (pas de remote configuré)")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du commit des changements: {str(e)}")
            return False
    
    def run(self) -> bool:
        """
        Exécute le processus complet d'intégration MBONGI.
        
        Returns:
            bool: True si l'intégration a réussi, False sinon.
        """
        try:
            logger.info("Démarrage du processus d'intégration MBONGI")
            
            # 1. Recherche des nouvelles descriptions
            new_descriptions = self.find_new_mbongi_descriptions()
            
            # 2. Intégration des descriptions
            success_count = 0
            for desc_info in new_descriptions:
                if self.integrate_description(desc_info):
                    success_count += 1
            
            logger.info(f"Intégration terminée: {success_count}/{len(new_descriptions)} descriptions intégrées")
            
            # 3. Mise à jour de la documentation des modèles
            model_success = self.update_model_documentation()
            
            # 4. Mise à jour des index
            if new_descriptions:
                self.update_setups_index()
            
            # 5. Commit des changements
            if success_count > 0 or model_success:
                self.commit_changes()
            
            logger.info("Processus d'intégration MBONGI terminé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du processus d'intégration: {str(e)}")
            return False

def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description="Module d'intégration MBONGI")
    parser.add_argument("--base-dir", help="Répertoire de base Akoben")
    parser.add_argument("--docs-dir", help="Répertoire de documentation MBONGI")
    
    args = parser.parse_args()
    
    integration = MbongiIntegration(base_dir=args.base_dir, docs_dir=args.docs_dir)
    success = integration.run()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()