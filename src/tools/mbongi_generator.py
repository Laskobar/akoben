"""
MBONGI Generator - Générateur automatique de descriptions MBONGI pour le système Akoben.
Utilise les captures TradingView importées et leurs métadonnées pour générer des descriptions
standardisées au format MBONGI.
"""

import os
import json
import datetime
import glob
from PIL import Image
import numpy as np
import logging
import sys
from typing import Dict, List, Any, Optional, Tuple
import re

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mbongi_generator.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("MbongiGenerator")

class MbongiGenerator:
    """Générateur de descriptions MBONGI à partir de captures TradingView."""
    
    def __init__(self, base_dir=None):
        """
        Initialise le générateur de descriptions MBONGI.
        
        Args:
            base_dir (str): Répertoire de base contenant les captures TradingView.
        """
        if base_dir is None:
            self.base_dir = os.path.join(os.path.expanduser("~"), "akoben", "tradingview_captures")
        else:
            self.base_dir = base_dir
            
        self.template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
        os.makedirs(self.template_dir, exist_ok=True)
        
        # Charge les templates par défaut s'ils n'existent pas
        self._ensure_default_templates()
        
        logger.info(f"Générateur MBONGI initialisé avec répertoire de base: {self.base_dir}")
    
    def _ensure_default_templates(self):
        """Crée les templates par défaut s'ils n'existent pas."""
        template_buy = os.path.join(self.template_dir, "template_buy.md")
        template_sell = os.path.join(self.template_dir, "template_sell.md")
        
        if not os.path.exists(template_buy):
            with open(template_buy, 'w') as f:
                f.write("""# Setup BUY sur {instrument} ({timeframe})

## Description générale
Ce setup {setup_type} sur {instrument} présente une opportunité d'achat avec un niveau de confiance de {confidence}/10.

## Analyse technique
{setup_analysis}

## Niveaux clés
{key_levels_formatted}

## Indicateurs utilisés
{indicators_formatted}

## Stratégie d'entrée
- Direction: BUY
- Point d'entrée: {entry_point}
- Stop Loss: {stop_loss}
- Take Profit: {take_profit}
- Ratio risque/récompense: {risk_reward}

## Notes supplémentaires
{notes}

## Timestamp
{timestamp}
""")
        
        if not os.path.exists(template_sell):
            with open(template_sell, 'w') as f:
                f.write("""# Setup SELL sur {instrument} ({timeframe})

## Description générale
Ce setup {setup_type} sur {instrument} présente une opportunité de vente avec un niveau de confiance de {confidence}/10.

## Analyse technique
{setup_analysis}

## Niveaux clés
{key_levels_formatted}

## Indicateurs utilisés
{indicators_formatted}

## Stratégie d'entrée
- Direction: SELL
- Point d'entrée: {entry_point}
- Stop Loss: {stop_loss}
- Take Profit: {take_profit}
- Ratio risque/récompense: {risk_reward}

## Notes supplémentaires
{notes}

## Timestamp
{timestamp}
""")
        
        logger.info("Templates MBONGI vérifiés et disponibles")
    
    def find_pending_setups(self) -> List[str]:
        """
        Trouve les setups qui ont été importés mais n'ont pas encore de description MBONGI.
        
        Returns:
            List[str]: Liste des chemins des répertoires contenant des setups en attente.
        """
        # Liste tous les répertoires de setup
        all_setup_dirs = []
        for date_dir in glob.glob(os.path.join(self.base_dir, "????-??-??")):
            if os.path.isdir(date_dir):
                setup_dirs = glob.glob(os.path.join(date_dir, "setup_*"))
                all_setup_dirs.extend([d for d in setup_dirs if os.path.isdir(d)])
        
        # Filtre les setups qui n'ont pas encore de description standardisée
        pending_setups = []
        for setup_dir in all_setup_dirs:
            has_metadata = os.path.exists(os.path.join(setup_dir, "metadata.json"))
            has_image = any(glob.glob(os.path.join(setup_dir, "*.png"))) or \
                       any(glob.glob(os.path.join(setup_dir, "*.jpg")))
            has_mbongi = os.path.exists(os.path.join(setup_dir, "mbongi_standard.md"))
            
            if has_metadata and has_image and not has_mbongi:
                pending_setups.append(setup_dir)
        
        logger.info(f"Trouvé {len(pending_setups)} setups en attente de description MBONGI")
        return pending_setups
    
    def analyze_setup_image(self, image_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse l'image du setup pour extraire des informations complémentaires.
        Cette méthode serait normalement plus sophistiquée avec de la vision par ordinateur,
        mais pour l'instant nous utilisons principalement les métadonnées.
        
        Args:
            image_path (str): Chemin vers l'image du setup.
            metadata (Dict[str, Any]): Métadonnées existantes.
            
        Returns:
            Dict[str, Any]: Métadonnées enrichies.
        """
        # Simule l'analyse d'image (serait normalement plus complexe)
        # Dans une version plus avancée, on pourrait utiliser OCR pour extraire les prix, etc.
        
        # Pour l'instant, nous générons des valeurs fictives basées sur les métadonnées
        enriched_data = metadata.copy()
        
        # Simule un prix d'entrée, SL et TP basés sur la direction
        if metadata["direction"] == "BUY":
            enriched_data["entry_point"] = "Au prix du marché"
            enriched_data["stop_loss"] = "2% sous le point d'entrée"
            enriched_data["take_profit"] = "3% au-dessus du point d'entrée"
            enriched_data["risk_reward"] = "1:1.5"
        else:  # SELL
            enriched_data["entry_point"] = "Au prix du marché"
            enriched_data["stop_loss"] = "2% au-dessus du point d'entrée"
            enriched_data["take_profit"] = "3% sous le point d'entrée"
            enriched_data["risk_reward"] = "1:1.5"
        
        # Génère une analyse basée sur le type de setup
        setup_analyses = {
            "Breakout": f"Le prix a cassé une résistance/support clé avec un volume significatif, indiquant un probable mouvement dans la direction de la cassure.",
            "Pullback": f"Le prix a connu un retrait temporaire dans une tendance établie, offrant une opportunité d'entrée dans le sens de la tendance principale.",
            "Reversal": f"Des signes d'épuisement de la tendance actuelle sont visibles, avec formation de patterns de retournement et divergences sur les indicateurs.",
            "Range": f"Le prix évolue dans un canal horizontal bien défini, avec des rebonds prévisibles sur les bornes.",
            "Trend Continuation": f"La tendance principale reste intacte avec une série de plus hauts/bas confirmant la direction du mouvement.",
            "Autre": f"Ce setup présente des caractéristiques particulières qui méritent attention."
        }
        
        enriched_data["setup_analysis"] = setup_analyses.get(
            metadata["setup_type"], "Analyse technique non disponible.")
        
        logger.info(f"Analyse complétée pour l'image {image_path}")
        return enriched_data
    
    def generate_mbongi_description(self, setup_dir: str) -> bool:
        """
        Génère une description MBONGI standardisée pour un setup.
        
        Args:
            setup_dir (str): Chemin vers le répertoire du setup.
            
        Returns:
            bool: True si la génération a réussi, False sinon.
        """
        try:
            # Vérifie l'existence des fichiers nécessaires
            metadata_path = os.path.join(setup_dir, "metadata.json")
            if not os.path.exists(metadata_path):
                logger.error(f"Métadonnées manquantes pour {setup_dir}")
                return False
            
            # Trouve l'image
            image_files = glob.glob(os.path.join(setup_dir, "*.png")) + \
                         glob.glob(os.path.join(setup_dir, "*.jpg"))
            
            if not image_files:
                logger.error(f"Image manquante pour {setup_dir}")
                return False
            
            image_path = image_files[0]  # Utilise la première image trouvée
            
            # Charge les métadonnées
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Analyse l'image et enrichit les métadonnées
            enriched_data = self.analyze_setup_image(image_path, metadata)
            
            # Prépare les données pour le template
            template_data = enriched_data.copy()
            
            # Formate les listes
            template_data["key_levels_formatted"] = "\n".join([f"- {level}" for level in 
                                                   enriched_data.get("key_levels", []) or ["Non spécifié"]])
            
            template_data["indicators_formatted"] = "\n".join([f"- {ind}" for ind in 
                                                   enriched_data.get("indicators", []) or ["Non spécifié"]])
            
            # Si les notes sont vides, ajoute un message par défaut
            if not template_data.get("notes"):
                template_data["notes"] = "Aucune note supplémentaire."
            
            # Ajoute le timestamp formaté
            dt = datetime.datetime.fromisoformat(template_data.get("timestamp", datetime.datetime.now().isoformat()))
            template_data["timestamp"] = dt.strftime("%Y-%m-%d %H:%M:%S")
            
            # Charge le template approprié
            template_file = "template_buy.md" if enriched_data["direction"] == "BUY" else "template_sell.md"
            template_path = os.path.join(self.template_dir, template_file)
            
            with open(template_path, 'r') as f:
                template_content = f.read()
            
            # Remplace les placeholders
            mbongi_content = template_content
            for key, value in template_data.items():
                placeholder = "{" + key + "}"
                mbongi_content = mbongi_content.replace(placeholder, str(value))
            
            # Sauvegarde la description MBONGI
            mbongi_path = os.path.join(setup_dir, "mbongi_standard.md")
            with open(mbongi_path, 'w') as f:
                f.write(mbongi_content)
            
            # Génère également un fichier JSON standardisé pour l'apprentissage automatique
            standardized_data = {
                "setup_id": os.path.basename(setup_dir),
                "instrument": enriched_data["instrument"],
                "timeframe": enriched_data["timeframe"],
                "setup_type": enriched_data["setup_type"],
                "direction": enriched_data["direction"],
                "confidence": enriched_data["confidence"],
                "key_levels": enriched_data.get("key_levels", []),
                "indicators": enriched_data.get("indicators", []),
                "entry_point": enriched_data.get("entry_point", ""),
                "stop_loss": enriched_data.get("stop_loss", ""),
                "take_profit": enriched_data.get("take_profit", ""),
                "risk_reward": enriched_data.get("risk_reward", ""),
                "image_path": os.path.relpath(image_path, self.base_dir),
                "mbongi_path": os.path.relpath(mbongi_path, self.base_dir),
                "timestamp": enriched_data.get("timestamp", ""),
                "features": {
                    # Ces caractéristiques seraient normalement extraites par analyse d'image
                    # Pour l'instant, nous utilisons des valeurs par défaut pour démonstration
                    "price_action": {
                        "trend": "up" if enriched_data["direction"] == "BUY" else "down",
                        "volatility": "medium",
                        "volume": "increasing" if enriched_data["confidence"] > 5 else "stable"
                    },
                    "technical_indicators": {
                        ind: "positive" if enriched_data["direction"] == "BUY" else "negative"
                        for ind in enriched_data.get("indicators", [])
                    }
                }
            }
            
            # Sauvegarde les données standardisées
            standard_path = os.path.join(setup_dir, "standardized.json")
            with open(standard_path, 'w') as f:
                json.dump(standardized_data, f, indent=2)
            
            logger.info(f"Description MBONGI générée avec succès pour {setup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération MBONGI pour {setup_dir}: {str(e)}")
            return False
    
    def process_all_pending_setups(self) -> Tuple[int, int]:
        """
        Traite tous les setups en attente de description MBONGI.
        
        Returns:
            Tuple[int, int]: (nombre de setups traités avec succès, nombre total de setups)
        """
        pending_setups = self.find_pending_setups()
        success_count = 0
        
        for setup_dir in pending_setups:
            if self.generate_mbongi_description(setup_dir):
                success_count += 1
        
        logger.info(f"Traitement terminé: {success_count}/{len(pending_setups)} setups traités avec succès")
        return success_count, len(pending_setups)
    
    def run(self) -> None:
        """
        Exécute le générateur MBONGI sur tous les setups en attente.
        """
        logger.info("Démarrage du générateur MBONGI")
        success_count, total_count = self.process_all_pending_setups()
        logger.info(f"Génération MBONGI terminée. {success_count}/{total_count} setups traités avec succès")

def main():
    """Point d'entrée principal."""
    generator = MbongiGenerator()
    generator.run()

if __name__ == "__main__":
    main()