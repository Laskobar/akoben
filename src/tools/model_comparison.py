"""
Script de comparaison entre Llama3 et Qwen pour évaluer les performances
"""

import sys
import time
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ModelComparison")

# Ajout du chemin du projet au PYTHONPATH
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

try:
    from src.connectors.llama_connector import LlamaConnector
    from src.connectors.qwen_connector import QwenConnector
except ImportError as e:
    logger.error(f"Erreur d'importation: {e}")
    logger.error("Vérifiez que vous avez bien créé les connecteurs Llama et Qwen, et que vous exécutez ce script depuis le répertoire racine du projet.")
    sys.exit(1)

# Questions de test pour comparer les modèles
TEST_QUESTIONS = [
    # Questions générales
    "Quelles sont les principales différences entre l'analyse technique et l'analyse fondamentale en trading?",
    "Explique la stratégie de trading 'price action' et comment elle peut être appliquée sur le US30.",
    
    # Questions liées au raisonnement
    "Si un trader observe une divergence entre le MACD et le prix sur un graphique M5, quelles pourraient être les implications pour un trade sur le US30?",
    "Comment pourrait-on combiner une stratégie de suivi de tendance avec une approche de retour à la moyenne pour créer un système de trading robuste?",
    
    # Questions liées à la génération de code
    "Écris une fonction Python simple qui calcule le RSI (Relative Strength Index) à partir d'une série de prix.",
    "Comment implémenterais-tu un système de gestion des risques qui limite l'exposition à 2% du capital par trade?"
]

def run_comparison():
    """
    Exécute une comparaison entre Llama3 et Qwen sur différentes questions
    """
    # Initialisation des connecteurs
    try:
        llama = LlamaConnector()
        qwen = QwenConnector()
        
        # Vérification de la disponibilité des modèles
        llama_available = llama.check_availability()
        qwen_available = qwen.check_availability()
        
        if not llama_available:
            logger.error("Modèle Llama3 non disponible. Vérifiez qu'Ollama est en cours d'exécution et que le modèle est installé.")
            return
            
        if not qwen_available:
            logger.error("Modèle Qwen non disponible. Vérifiez qu'Ollama est en cours d'exécution et que le modèle est installé.")
            return
            
        logger.info("Début de la comparaison des modèles...")
        
        results = []
        
        # Exécution des tests pour chaque question
        for i, question in enumerate(TEST_QUESTIONS):
            logger.info(f"Test {i+1}/{len(TEST_QUESTIONS)}: {question[:50]}...")
            
            # Test avec Llama3
            start_time = time.time()
            llama_response = llama.get_completion(question)
            llama_time = time.time() - start_time
            
            # Test avec Qwen
            start_time = time.time()
            qwen_response = qwen.get_completion(question)
            qwen_time = time.time() - start_time
            
            # Enregistrement des résultats
            results.append({
                "question": question,
                "llama": {
                    "response": llama_response,
                    "time": llama_time,
                    "length": len(llama_response)
                },
                "qwen": {
                    "response": qwen_response,
                    "time": qwen_time,
                    "length": len(qwen_response)
                }
            })
            
            # Affichage des résultats pour cette question
            print("\n" + "="*80)
            print(f"QUESTION {i+1}: {question}")
            print("-"*80)
            print(f"LLAMA3 ({llama_time:.2f}s):")
            print(llama_response[:500] + "..." if len(llama_response) > 500 else llama_response)
            print("-"*80)
            print(f"QWEN ({qwen_time:.2f}s):")
            print(qwen_response[:500] + "..." if len(qwen_response) > 500 else qwen_response)
            print("="*80 + "\n")
        
        # Calcul et affichage des statistiques globales
        llama_avg_time = sum(r["llama"]["time"] for r in results) / len(results)
        qwen_avg_time = sum(r["qwen"]["time"] for r in results) / len(results)
        
        llama_avg_length = sum(r["llama"]["length"] for r in results) / len(results)
        qwen_avg_length = sum(r["qwen"]["length"] for r in results) / len(results)
        
        print("\nRÉSULTATS COMPARATIFS:")
        print(f"Llama3 - Temps moyen: {llama_avg_time:.2f}s, Longueur moyenne: {llama_avg_length:.0f} caractères")
        print(f"Qwen - Temps moyen: {qwen_avg_time:.2f}s, Longueur moyenne: {qwen_avg_length:.0f} caractères")
        
        if qwen_avg_time < llama_avg_time:
            print(f"Qwen est {(llama_avg_time/qwen_avg_time):.2f}x plus rapide que Llama3")
        else:
            print(f"Llama3 est {(qwen_avg_time/llama_avg_time):.2f}x plus rapide que Qwen")
            
        logger.info("Comparaison terminée.")
        
    except Exception as e:
        logger.error(f"Erreur lors de la comparaison: {str(e)}")

if __name__ == "__main__":
    run_comparison()
