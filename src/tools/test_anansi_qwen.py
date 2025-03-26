"""
Script pour tester l'intégration d'Anansi avec Qwen
"""

import sys
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AnansiQwenTest")

# Ajout du chemin du projet au PYTHONPATH
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

try:
    from src.anansi.core import Anansi
except ImportError as e:
    logger.error(f"Erreur d'importation: {e}")
    logger.error("Vérifiez que vous exécutez ce script depuis le répertoire racine du projet.")
    sys.exit(1)

def test_anansi_qwen():
    """
    Teste l'intégration d'Anansi avec Qwen
    """
    logger.info("Initialisation d'Anansi avec Qwen...")
    anansi = Anansi()
    
    # Vérifier le modèle par défaut
    logger.info(f"Modèle général par défaut: {anansi.general_model}")
    
    # Test simple pour vérifier la communication avec Qwen
    test_prompt = "Quelles sont les 3 principales stratégies de trading sur le marché US30?"
    logger.info(f"Envoi d'un prompt test à Qwen via Anansi: {test_prompt}")
    
    response = anansi.call_llm(test_prompt)
    logger.info(f"Réponse reçue (premiers 500 caractères): {response[:500]}...")
    
    logger.info("Test réussi!")

if __name__ == "__main__":
    test_anansi_qwen()
