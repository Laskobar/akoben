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
        """
        Simule la détection d'éléments visuels sur un graphique de trading
        
        Dans une implémentation réelle, cette méthode utiliserait YOLOv8
        """
        # Simuler différents types de détections qu'un modèle YOLOv8 pourrait identifier
        # sur un graphique de trading
        
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
            },
            {
                "type": "doji",
                "confidence": 0.75,
                "bbox": [int(width * 0.84), int(height * 0.48), int(width * 0.85), int(height * 0.51)]
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
            },
            {
                "type": "ma20",
                "confidence": 0.95,
                "bbox": [int(width * 0.1), int(height * 0.45), int(width * 0.9), int(height * 0.45)]
            }
        ]
        
        # Simuler quelques patterns potentiels
        patterns = [
            {
                "type": "double_bottom",
                "confidence": 0.65,
                "bbox": [int(width * 0.5), int(height * 0.7), int(width * 0.7), int(height * 0.8)]
            }
        ]
        
        return {
            "candles": candles,
            "indicators": indicators,
            "patterns": patterns
        }
    
    def _analyze_detections(self, detections, image_source):
        """
        Utilise le LLM pour analyser les détections et fournir un aperçu
        """
        # Préparer un prompt pour le LLM
        candles_info = "\n".join([f"- {c['type']} (confiance: {c['confidence']:.2f})" for c in detections["candles"]])
        indicators_info = "\n".join([f"- {i['type']} (confiance: {i['confidence']:.2f})" for i in detections["indicators"]])
        patterns_info = "\n".join([f"- {p['type']} (confiance: {p['confidence']:.2f})" for p in detections["patterns"]])
        
        prompt = f"""
        En tant qu'expert en analyse technique de graphiques de trading, examine ces détections d'éléments visuels clés sur un graphique ({image_source}):
        
        Bougies japonaises détectées:
        {candles_info}
        
        Indicateurs techniques détectés:
        {indicators_info}
        
        Patterns potentiels détectés:
        {patterns_info}
        
        Fournis une analyse concise de ces éléments visuels, en indiquant:
        1. Les éléments les plus significatifs et leur implication
        2. Les configurations techniques potentielles
        3. Les zones d'intérêt à surveiller
        
        Reste factuel et objectif dans ton analyse.
        """
        
        # Appeler le LLM
        return self.llm_caller(prompt)
    
    def draw_annotations(self, image_path, detections, output_path=None):
        """
        Dessine les annotations des détections sur l'image
        
        Args:
            image_path: Chemin de l'image
            detections: Résultats des détections
            output_path: Chemin de sortie pour l'image annotée
                         (si None, utilise le chemin original avec un suffixe)
        
        Returns:
            Chemin de l'image annotée
        """
        try:
            # Ouvrir l'image
            image = Image.open(image_path)
            draw = ImageDraw.Draw(image)
            
            # Dessiner les bougies
            for candle in detections.get("candles", []):
                bbox = candle["bbox"]
                # Couleur selon le type de bougie
                color = {
                    "bullish": "green",
                    "bearish": "red",
                    "doji": "blue"
                }.get(candle["type"], "yellow")
                
                draw.rectangle(bbox, outline=color, width=2)
                draw.text((bbox[0], bbox[1] - 10), f"{candle['type']} ({candle['confidence']:.2f})", fill=color)
            
            # Dessiner les indicateurs
            for indicator in detections.get("indicators", []):
                bbox = indicator["bbox"]
                draw.line([bbox[0], bbox[1], bbox[2], bbox[3]], fill="blue", width=2)
                draw.text((bbox[0], bbox[1] - 10), f"{indicator['type']}", fill="blue")
            
            # Dessiner les patterns
            for pattern in detections.get("patterns", []):
                bbox = pattern["bbox"]
                draw.rectangle(bbox, outline="purple", width=2)
                draw.text((bbox[0], bbox[1] - 10), f"{pattern['type']}", fill="purple")
            
            # Sauvegarder l'image annotée
            if output_path is None:
                name, ext = os.path.splitext(image_path)
                output_path = f"{name}_annotated{ext}"
            
            image.save(output_path)
            return output_path
        
        except Exception as e:
            print(f"Erreur lors de l'annotation de l'image: {e}")
            return None

    # Dans /home/lasko/akoben-clean/src/agents/vision/kora.py
    def save_screenshot(symbol: str, timeframe: str):
        """Attend une capture manuelle et la sauvegarde"""
        path = f"{config['screenshot_path']}/{datetime.now().strftime('%Y-%m-%d_%H-%M')}_{timeframe}_{symbol}.png"
        input(f"Prêt pour {symbol} {timeframe} ? Appuyez sur Entrée après la capture...")
        # Ici vous collerez manuellement le screenshot dans le dossier
        return path    