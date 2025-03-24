#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test pour l'agent Oba d'imitation amélioré avec données standardisées.
Ce script teste l'intégration des données standardisées avec l'agent d'imitation.
"""

import os
import sys
import logging
import json
import time
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("ObaImitationTest")

# Ajout du répertoire parent au path pour l'import des modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

def main():
    """Fonction principale du test."""
    logger.info("=== Test de l'agent Oba avec données standardisées ===")
    
    try:
        # Import des modules (à l'intérieur de la fonction pour attraper les erreurs d'import)
        from src.agents.chaka.oba import Oba
        from src.anansi.agent_framework.autonomous_agent import AutonomousAgent
        
        # Configuration de l'agent Oba
        config = {
            "standardized_data_path": "data/setups/standardized",
            "model_type": "random_forest",
            "confidence_threshold": 0.6,
        }
        
        # Initialisation de l'agent
        logger.info("Initialisation de l'agent Oba...")
        oba_agent = Oba(name="oba_test", config=config)
        
        # Vérification des setups standardisés disponibles
        logger.info("Récupération des statistiques sur les setups standardisés...")
        stats = oba_agent.get_standardized_setups_stats()
        
        logger.info(f"Statistiques des setups standardisés:")
        logger.info(f"- Total des setups: {stats.get('total_setups', 0)}")
        logger.info(f"- Setups d'achat (BUY): {stats.get('buy_setups', 0)}")
        logger.info(f"- Setups de vente (SELL): {stats.get('sell_setups', 0)}")
        logger.info(f"- Setups avec patterns: {stats.get('setups_with_patterns', 0)}")
        logger.info(f"- Setups avec indicateurs: {stats.get('setups_with_indicators', 0)}")
        logger.info(f"- Setups avec niveaux de prix: {stats.get('setups_with_price_levels', 0)}")
        
        # Afficher les patterns et indicateurs les plus fréquents
        patterns = stats.get('patterns_counts', {})
        if patterns:
            logger.info("Patterns les plus fréquents:")
            for pattern, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:5]:
                logger.info(f"- {pattern}: {count}")
        
        indicators = stats.get('indicators_counts', {})
        if indicators:
            logger.info("Indicateurs les plus fréquents:")
            for indicator, count in sorted(indicators.items(), key=lambda x: x[1], reverse=True)[:5]:
                logger.info(f"- {indicator}: {count}")
        
        # Si pas assez de setups ou déséquilibre entre BUY et SELL
        if stats.get('total_setups', 0) < 10:
            logger.warning("Nombre insuffisant de setups standardisés pour l'entraînement.")
            return
        
        if min(stats.get('buy_setups', 0), stats.get('sell_setups', 0)) < 3:
            logger.warning("Déséquilibre important entre les setups BUY et SELL. L'entraînement peut être biaisé.")
        
        # Menu d'options
        while True:
            print("\nOptions:")
            print("1. Entraîner un modèle sur les données standardisées")
            print("2. Tester le modèle sur les données standardisées")
            print("3. Tester une prédiction spécifique")
            print("4. Voir les informations du modèle actuel")
            print("5. Quitter")
            
            choice = input("\nChoisissez une option (1-5): ")
            
            if choice == "1":
                train_model(oba_agent)
            elif choice == "2":
                test_model(oba_agent)
            elif choice == "3":
                test_specific_prediction(oba_agent)
            elif choice == "4":
                show_model_info(oba_agent)
            elif choice == "5":
                print("Au revoir!")
                break
            else:
                print("Option non valide. Veuillez réessayer.")
    
    except ImportError as e:
        logger.error(f"Erreur d'importation: {e}")
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution du test: {e}")

def train_model(oba_agent):
    """Entraîne un modèle sur les données standardisées."""
    print("\n=== Entraînement du modèle ===")
    
    # Demander confirmation
    confirmation = input("Confirmer l'entraînement du modèle? (o/n): ").lower()
    if confirmation != 'o':
        print("Entraînement annulé.")
        return
    
    # Entraîner le modèle
    start_time = time.time()
    result = oba_agent.train_model(use_standardized=True)
    elapsed_time = time.time() - start_time
    
    if result.get("success", False):
        print(f"Modèle entraîné avec succès en {elapsed_time:.2f} secondes!")
        print(f"- ID du modèle: {result.get('model_id', 'Non disponible')}")
        print(f"- Précision: {result.get('accuracy', 0)*100:.2f}%")
        print(f"- Nombre d'échantillons: {result.get('sample_count', 0)}")
    else:
        print(f"Échec de l'entraînement: {result.get('message', 'Erreur inconnue')}")

def test_model(oba_agent):
    """Teste le modèle sur les données standardisées."""
    print("\n=== Test du modèle ===")
    
    # Vérifier si un modèle est chargé
    model_info = oba_agent.get_model_info()
    if model_info.get("status") != "loaded":
        print("Aucun modèle chargé. Veuillez d'abord entraîner un modèle.")
        return
    
    # Demander le pourcentage de données à utiliser pour le test
    test_size = input("Pourcentage de données à utiliser pour le test (10-50, défaut 30): ")
    try:
        test_size = float(test_size) / 100 if test_size else 0.3
        test_size = max(0.1, min(0.5, test_size))  # Limiter entre 0.1 et 0.5
    except ValueError:
        test_size = 0.3
        print("Valeur non valide. Utilisation de la valeur par défaut: 30%")
    
    # Tester le modèle
    start_time = time.time()
    results = oba_agent.test_model_on_standardized_setups(test_size=test_size)
    elapsed_time = time.time() - start_time
    
    print(f"Test terminé en {elapsed_time:.2f} secondes!")
    print(f"Précision: {results.get('accuracy', 0)*100:.2f}%")
    print(f"Prédictions correctes: {results.get('correct_predictions', 0)}/{results.get('total_tests', 0)}")
    
    # Afficher le détail des erreurs
    incorrect_results = [r for r in results.get("details", []) if not r.get("correct", False)]
    if incorrect_results:
        print("\nDétail des prédictions incorrectes:")
        for i, result in enumerate(incorrect_results[:5], 1):  # Limiter à 5 erreurs
            print(f"{i}. Setup: {result.get('setup_id')}")
            print(f"   Attendu: {result.get('expected_action')}, Prédit: {result.get('predicted_action')}")
            print(f"   Confiance: {result.get('confidence', 0)*100:.2f}%")
        
        if len(incorrect_results) > 5:
            print(f"... et {len(incorrect_results) - 5} autres prédictions incorrectes.")

def test_specific_prediction(oba_agent):
    """Teste une prédiction sur un setup spécifique."""
    print("\n=== Test d'une prédiction spécifique ===")
    
    # Vérifier si un modèle est chargé
    model_info = oba_agent.get_model_info()
    if model_info.get("status") != "loaded":
        print("Aucun modèle chargé. Veuillez d'abord entraîner un modèle.")
        return
    
    # Récupérer les setups disponibles
    stats = oba_agent.get_standardized_setups_stats()
    if stats.get('total_setups', 0) == 0:
        print("Aucun setup standardisé disponible.")
        return
    
    # Récupérer les IDs des setups
    setups = oba_agent.state.get("available_standardized_setups", [])
    if not setups:
        print("Aucun setup disponible dans l'état de l'agent.")
        return
    
    # Afficher les premiers setups
    print("Premiers setups disponibles:")
    for i, setup in enumerate(setups[:10], 1):
        setup_id = setup.get("id", "")
        action = setup.get("standardized_info", {}).get("action", "UNKNOWN")
        print(f"{i}. {setup_id} - Action: {action}")
    
    # Demander l'ID du setup
    setup_id = input("\nEntrez l'ID du setup à tester (ou le numéro dans la liste): ")
    
    # Si l'utilisateur entre un nombre, utiliser l'ID correspondant dans la liste
    try:
        setup_index = int(setup_id) - 1
        if 0 <= setup_index < len(setups):
            setup_id = setups[setup_index].get("id", "")
            print(f"Setup sélectionné: {setup_id}")
        else:
            print("Numéro de setup invalide.")
            return
    except ValueError:
        # C'est probablement un ID de setup, continuer normalement
        pass
    
    # Effectuer la prédiction
    perceptions = oba_agent.perceive({"standardized_setup_id": setup_id})
    
    if not perceptions.get("standardized_data_used", False):
        print(f"Setup {setup_id} non trouvé ou impossible à charger.")
        return
    
    # Afficher les informations du setup
    print("\nInformations du setup:")
    std_info = perceptions.get("standardized_data", {}).get("standardized_info", {})
    
    print(f"Patterns: {', '.join(std_info.get('patterns', []))}")
    print(f"Indicateurs: {', '.join(std_info.get('indicators', []))}")
    print(f"Niveaux de prix:")
    print(f"- Entrée: {std_info.get('entry_price', 'Non spécifié')}")
    print(f"- Stop Loss: {std_info.get('stop_loss', 'Non spécifié')}")
    print(f"- Take Profit: {std_info.get('take_profit', 'Non spécifié')}")
    
    # Faire la prédiction
    decisions = oba_agent.think(perceptions)
    
    print("\nPrédiction:")
    print(f"Action: {decisions.get('action')}")
    print(f"Confiance: {decisions.get('confidence', 0)*100:.2f}%")
    print(f"Raisonnement: {decisions.get('reasoning')}")
    
    # Comparer avec l'action attendue
    expected_action = std_info.get("action")
    if expected_action:
        print(f"\nAction attendue: {expected_action}")
        correct = expected_action == decisions.get('action')
        print(f"Prédiction correcte: {'Oui' if correct else 'Non'}")

def show_model_info(oba_agent):
    """Affiche les informations sur le modèle actuel."""
    print("\n=== Informations sur le modèle actuel ===")
    
    model_info = oba_agent.get_model_info()
    
    if model_info.get("status") == "loaded":
        print(f"ID du modèle: {model_info.get('model_id', 'Non disponible')}")
        print(f"Type de modèle: {model_info.get('model_type', 'Non disponible')}")
        print(f"Date d'entraînement: {model_info.get('training_date', 'Non disponible')}")
        
        # Afficher les métriques
        metrics = model_info.get("metrics", {})
        print("\nMétriques:")
        print(f"- Précision: {metrics.get('accuracy', 0)*100:.2f}%")
        print(f"- Nombre d'échantillons: {metrics.get('sample_count', 0)}")
        
        # Afficher le nombre de caractéristiques et de labels
        print(f"\nNombre de caractéristiques: {model_info.get('feature_count', 0)}")
        print(f"Nombre de classes: {model_info.get('label_count', 0)}")
    else:
        print(f"Statut du modèle: {model_info.get('status', 'inconnu')}")
        print(f"Message: {model_info.get('message', 'Aucune information disponible')}")

if __name__ == "__main__":
    main()