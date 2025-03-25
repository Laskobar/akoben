import os
import numpy as np
import requests
from datetime import datetime
from PIL import Image, ImageDraw
import io

class Kora:
    """
    Agent de vision 'Kora' - Spécialisé dans la détection rapide d'éléments visuels clés
    sur les graphiques de trading.
    """
    def __init__(self, config=None, llm_caller=None):
        self.config = config or {}
        self.llm_caller = llm_caller
        print("Agent Kora (Vision Scout) initialisé")
        
        # Simulation de modèle - Dans une version réelle, nous chargerions ici un modèle YOLOv8
        self.detection_model = None
    
    def analyze_chart(self, image_path=None, image_url=None, image_data=None):
        """
        Analyse un graphique de trading pour détecter les éléments visuels clés
        
        Args:
            image_path: Chemin local vers l'image
            image_url: URL d'une image à télécharger
            image_data: Données binaires de l'image
            
        Returns:
            Dictionnaire contenant les résultats de l'analyse
        """
        # Charger l'image (priorité: chemin > url > données)
        if image_path and os.path.exists(image_path):
            try:
                image = Image.open(image_path)
                image_source = f"fichier local: {image_path}"
            except Exception as e:
                return {"error": f"Impossible d'ouvrir l'image: {str(e)}"}
        elif image_url:
            try:
                response = requests.get(image_url, stream=True)
                response.raise_for_status()
                image = Image.open(io.BytesIO(response.content))
                image_source = f"URL: {image_url}"
            except Exception as e:
                return {"error": f"Impossible de télécharger l'image: {str(e)}"}
        elif image_data:
            try:
                image = Image.open(io.BytesIO(image_data))
                image_source = "données binaires fournies"
            except Exception as e:
                return {"error": f"Impossible de décoder les données d'image: {str(e)}"}
        else:
            return {"error": "Aucune source d'image fournie"}
        
        # Dans cette version de prototype, nous simulons la détection
        # Plus tard, nous intégrerons ici un modèle YOLOv8 réel
        detection_results = self._simulate_detections(image)
        
        # Utiliser le LLM pour analyser les détections si disponible
        if self.llm_caller:
            analysis = self._analyze_detections(detection_results, image_source)
        else:
            analysis = "Pas de LLM disponible pour l'analyse des détections"
        
        return {
            "image_info": {
                "source": image_source,
                "size": image.size,
                "format": image.format
            },
            "detections": detection_results,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
    
    def _simulate_detections(self, image):
        """Simule la détection d'éléments visuels sur un graphique de trading"""
        width, height = image.size
        
        # Simuler quelques bougies japonaises détectées
        candles = [
            {
                "type": "bullish",
                "confidence": 0.92,
                "bbox": [int(width * 0.8), int(height * 0.4), int(width * 0.81), int(height * 0.5)]
            },
            {
                "type": "bearish",
                "confidence": 0.88,
                "bbox": [int(width * 0.82), int(height * 0.45), int(width * 0.83), int(height * 0.55)]
            }
        ]
        
        # Simuler quelques indicateurs techniques détectés
        indicators = [
            {
                "type": "support_level",
                "confidence": 0.85,
                "bbox": [int(width * 0.1), int(height * 0.6), int(width * 0.9), int(height * 0.61)]
            },
            {
                "type": "resistance_level",
                "confidence": 0.82,
                "bbox": [int(width * 0.1), int(height * 0.3), int(width * 0.9), int(height * 0.31)]
            }
        ]
        
        return {
            "candles": candles,
            "indicators": indicators,
            "patterns": []
        }
    
    def _analyze_detections(self, detections, image_source):
        """Utilise le LLM pour analyser les détections"""
        candles_info = "\n".join([f"- {c['type']} (confiance: {c['confidence']:.2f})" for c in detections["candles"]])
        indicators_info = "\n".join([f"- {i['type']} (confiance: {i['confidence']:.2f})" for i in detections["indicators"]])
        
        prompt = f"""
        Analyse technique pour {image_source}:
        
        Bougies détectées:
        {candles_info}
        
        Niveaux clés:
        {indicators_info}
        """
        return self.llm_caller(prompt) if self.llm_caller else "Analyse LLM désactivée"
    
    def save_screenshot(self, symbol: str, timeframe: str, config: dict):
        """
        Gère la capture manuelle des graphiques
        Args:
            symbol: Symbole (ex: 'US30')
            timeframe: Période (ex: 'M1')
            config: {'screenshot_path': '/chemin/vers/dossier'}
        """
        try:
            os.makedirs(config['screenshot_path'], exist_ok=True)
            filename = f"{datetime.now().strftime('%Y-%m-%d_%H-%M')}_{timeframe}_{symbol}.png"
            path = os.path.join(config['screenshot_path'], filename)
            
            print(f"""
            === INSTRUCTIONS CAPTURE ===
            1. Ouvrez TradingView {symbol} {timeframe}
            2. Configurez votre graphique
            3. Prenez un screenshot
            4. Sauvegardez-le sous : {path}
            Appuyez sur Entrée quand c'est fait...""")
            
            input()  # Pause manuelle
            
            if os.path.exists(path):
                print(f"[SUCCÈS] Capture sauvegardée : {path}")
                return path
            else:
                print("[ERREUR] Fichier non trouvé. Vérifiez :")
                print(f"- Le chemin {path}")
                print(f"- Les permissions du dossier")
                return None
                
        except Exception as e:
            print(f"[ERREUR CRITIQUE] {str(e)}")
            return None

# Exemple d'utilisation minimaliste
if __name__ == "__main__":
    kora = Kora()
    kora.save_screenshot(
        symbol="US30",
        timeframe="M1",
        config={'screenshot_path': os.path.expanduser('~/akoben-screenshots')}
    )