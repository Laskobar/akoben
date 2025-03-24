#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test pour l'infrastructure d'apprentissage par imitation d'Akoben.
Ce script permet de tester le chargement des données d'exemple, l'extraction des caractéristiques,
et l'entraînement de modèles d'imitation simples.
"""

import os
import sys
import logging
import pandas as pd
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("ImitationTest")

# Ajout du répertoire parent au path pour l'import des modules
current_dir = Path(__file__).resolve().parent
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

try:
    from learning.imitation_learning_manager import ImitationLearningManager
    from tools.setup_database_manager import SetupDatabaseManager
    from tools.setup_text_processor import SetupTextProcessor
    logger.info("Modules importés avec succès")
except ImportError as e:
    logger.error(f"Erreur lors de l'importation des modules: {e}")
    sys.exit(1)

def test_setup_database():
    """Teste le chargement et l'accès à la base de données des setups."""
    logger.info("Test de la base de données des setups...")
    
    try:
        # Chemin vers le dossier de données
        data_dir = current_dir / "data" / "setups"
        
        # Vérification de l'existence du dossier
        if not data_dir.exists():
            logger.warning(f"Le dossier {data_dir} n'existe pas. Création du dossier...")
            data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialisation du gestionnaire de base de données
        db_manager = SetupDatabaseManager(str(data_dir))
        
        # Liste des setups disponibles
        setups = db_manager.list_all_setups()
        logger.info(f"Nombre de setups trouvés: {len(setups)}")
        
        # Afficher les premiers setups (si disponibles)
        if setups:
            logger.info(f"Exemples de setups: {setups[:5]}")
            
            # Tester le chargement d'un setup
            setup_data = db_manager.load_setup(setups[0])
            logger.info(f"Setup chargé avec succès: {setups[0]}")
            logger.info(f"Clés disponibles: {setup_data.keys()}")
        else:
            logger.warning("Aucun setup trouvé dans la base de données")
        
        return db_manager, setups
    
    except Exception as e:
        logger.error(f"Erreur lors du test de la base de données: {e}")
        return None, []

def test_text_processor(db_manager, setups):
    """Teste le traitement des descriptions textuelles des setups."""
    logger.info("Test du processeur de texte...")
    
    if not db_manager or not setups:
        logger.error("Impossible de tester le processeur de texte sans base de données fonctionnelle")
        return None
    
    try:
        # Initialisation du processeur de texte
        text_processor = SetupTextProcessor()
        
        processed_setups = []
        for setup_id in setups[:5]:  # Traiter les 5 premiers setups
            setup_data = db_manager.load_setup(setup_id)
            
            if 'description' in setup_data:
                # Traitement de la description
                processed_text = text_processor.process_setup_description(setup_data['description'])
                logger.info(f"Setup {setup_id} traité avec succès")
                logger.info(f"Extrait du traitement: {str(processed_text)[:100]}...")
                
                processed_setups.append({
                    'id': setup_id,
                    'original': setup_data['description'],
                    'processed': processed_text
                })
            else:
                logger.warning(f"Le setup {setup_id} ne contient pas de description")
        
        return text_processor, processed_setups
    
    except Exception as e:
        logger.error(f"Erreur lors du test du processeur de texte: {e}")
        return None, []

def test_imitation_learning(db_manager, text_processor, setups):
    """Teste le gestionnaire d'apprentissage par imitation."""
    logger.info("Test du gestionnaire d'apprentissage par imitation...")
    
    if not db_manager or not text_processor:
        logger.error("Impossible de tester l'apprentissage par imitation sans les composants nécessaires")
        return
    
    try:
        # Initialisation du gestionnaire d'apprentissage par imitation
        imitation_manager = ImitationLearningManager(
            db_manager=db_manager,
            text_processor=text_processor
        )
        
        # Préparation des données d'entraînement à partir des setups disponibles
        logger.info("Préparation des données d'entraînement...")
        training_data = imitation_manager.prepare_training_data(setups)
        
        if training_data and len(training_data) > 0:
            logger.info(f"Données d'entraînement préparées avec succès: {len(training_data)} exemples")
            
            # Visualisation des premières données
            for i, (X, y) in enumerate(training_data[:2]):
                logger.info(f"Exemple {i+1}:")
                logger.info(f"Features: {X}")
                logger.info(f"Target: {y}")
            
            # Entraînement d'un modèle simple
            logger.info("Entraînement d'un modèle de base...")
            model = imitation_manager.train_model(training_data, model_type="decision_tree")
            
            # Test du modèle sur un exemple
            if model and training_data:
                X_test, _ = training_data[0]
                prediction = imitation_manager.predict(model, X_test)
                logger.info(f"Prédiction sur l'exemple de test: {prediction}")
                
                # Sauvegarde du modèle pour référence
                model_dir = current_dir / "data" / "models"
                model_dir.mkdir(parents=True, exist_ok=True)
                model_path = model_dir / "test_imitation_model.pkl"
                imitation_manager.save_model(model, str(model_path))
                logger.info(f"Modèle sauvegardé: {model_path}")
        else:
            logger.warning("Aucune donnée d'entraînement n'a pu être préparée")
    
    except Exception as e:
        logger.error(f"Erreur lors du test d'apprentissage par imitation: {e}")

def main():
    """Fonction principale exécutant tous les tests."""
    logger.info("Démarrage des tests de l'infrastructure d'apprentissage par imitation...")
    
    # Test de la base de données
    db_manager, setups = test_setup_database()
    
    # Test du processeur de texte
    text_processor, processed_setups = test_text_processor(db_manager, setups)
    
    # Test de l'apprentissage par imitation
    test_imitation_learning(db_manager, text_processor, setups)
    
    logger.info("Tests terminés")

if __name__ == "__main__":
    main()