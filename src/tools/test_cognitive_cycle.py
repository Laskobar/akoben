"""
Script pour tester le cycle cognitif complet d'Anansi
"""

import sys
import json
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CognitiveCycleTest")

# Ajout du chemin du projet au PYTHONPATH
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

try:
    from src.anansi.core import Anansi
except ImportError as e:
    logger.error(f"Erreur d'importation: {e}")
    logger.error("Vérifiez que vous exécutez ce script depuis le répertoire racine du projet.")
    sys.exit(1)

def test_cognitive_cycle():
    """
    Teste le cycle cognitif complet d'Anansi
    """
    logger.info("Initialisation d'Anansi...")
    anansi = Anansi()
    
    # Données de test pour simuler une situation de trading
    test_inputs = {
        "market_data": {
            "symbol": "US30",
            "current_price": 39500,
            "previous_close": 39350,
            "daily_range": {"high": 39650, "low": 39300},
            "condition": "trending_up"
        },
        "indicators": {
            "macd": {"value": 25.5, "signal": 15.2, "histogram": 10.3},
            "rsi": 62.5,
            "ema": {"ema20": 39250, "ema50": 38900, "ema200": 37500}
        },
        "price_action": {
            "trend": "up",
            "recent_pattern": "higher_highs",
            "support_levels": [39300, 39000, 38700],
            "resistance_levels": [39800, 40000, 40500]
        }
    }
    
    test_context = {
        "symbol": "US30",
        "timeframe": "H1",
        "capital": 100000,
        "max_risk_per_trade": 0.02
    }
    
    logger.info("Exécution du cycle cognitif complet...")
    
    try:
        results = anansi.process_cognitive_cycle(test_inputs, test_context)
        
        logger.info("\n" + "="*50)
        logger.info("RÉSULTATS DU CYCLE COGNITIF")
        logger.info("="*50)
        
        # Affichage des résultats du raisonnement
        if "reasoning" in results:
            logger.info("\nRÉSULTATS DU RAISONNEMENT:")
            reasoning = results["reasoning"]
            
            if "perception" in reasoning:
                logger.info(f"\nPERCEPTION:\n{reasoning['perception']}")
            
            if "reasoning" in reasoning:
                logger.info(f"\nRAISONNEMENT:\n{reasoning['reasoning']}")
        
        # Affichage de la décision
        if "decision" in results:
            decision = results["decision"]
            logger.info("\nDÉCISION FINALE:")
            logger.info(f"Action: {decision.get('action', 'non définie')}")
            logger.info(f"Point d'entrée: {decision.get('entry_price')}")
            logger.info(f"Stop-loss: {decision.get('stop_loss')}")
            logger.info(f"Take-profit: {decision.get('take_profit')}")
            logger.info(f"Taille de position: {decision.get('position_size')}")
            
            if "justification" in decision:
                logger.info(f"\nJUSTIFICATION:\n{decision['justification']}")
        
        logger.info("="*50)
        logger.info("Test du cycle cognitif terminé avec succès!")
        
    except Exception as e:
        logger.error(f"Erreur lors du test du cycle cognitif: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cognitive_cycle()
