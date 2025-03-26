"""
Vision Agent - Agent d'analyse automatique des graphiques de trading.
Ce module fait partie du système d'apprentissage hybride Akoben.
Il analyse les images de graphiques pour détecter les patterns, niveaux clés,
et générer automatiquement des descriptions standardisées.
"""

import os
import sys
import numpy as np
import json
import cv2
from datetime import datetime
import logging
from typing import Dict, List, Any, Tuple, Optional
import matplotlib.pyplot as plt
from PIL import Image
import re

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("vision_agent.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("VisionAgent")

class VisionAgent:
    """Agent de vision pour l'analyse automatique des graphiques de trading."""
    
    def __init__(self, models_dir=None):
        """
        Initialise l'agent de vision.
        
        Args:
            models_dir (str): Répertoire contenant les modèles pré-entraînés.
        """
        if models_dir is None:
            self.models_dir = os.path.join(os.path.expanduser("~"), "akoben", "models", "vision")
        else:
            self.models_dir = models_dir
            
        # Crée le répertoire des modèles s'il n'existe pas
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Configuration des paramètres d'analyse
        self.config = {
            "candle_detection": {
                "threshold": 0.6,
                "min_size": 5,
                "max_gap": 3
            },
            "support_resistance": {
                "horizontal_threshold": 0.95,  # Horizontalité minimale (0-1)
                "min_touches": 2,              # Nombre minimal de touches
                "proximity_threshold": 0.02,   # % de l'échelle des prix
                "strength_weight": {
                    "touches": 0.5,            # Poids du nombre de touches
                    "length": 0.3,             # Poids de la longueur de la ligne
                    "recency": 0.2,            # Poids de la récence des touches
                }
            },
            "pattern_detection": {
                "threshold": 0.7,
                "window_size": 10
            },
            "indicator_detection": {
                "ma_threshold": 0.7,
                "rsi_threshold": 0.7,
                "macd_threshold": 0.7
            }
        }
        
        logger.info("Agent de vision initialisé")
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analyse complète d'une image de graphique.
        
        Args:
            image_path (str): Chemin vers l'image à analyser.
            
        Returns:
            Dict[str, Any]: Résultats de l'analyse.
        """
        try:
            logger.info(f"Analyse de l'image: {image_path}")
            
            # Charge l'image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Impossible de charger l'image: {image_path}")
                
            # Convertit en RGB pour le traitement
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Analyse des différents éléments
            chart_info = self.detect_chart_type(image_rgb)
            timeframe = self.detect_timeframe(image_rgb)
            price_range = self.detect_price_range(image_rgb)
            candles = self.detect_candles(image_rgb)
            
            # Analyse des support/résistances et niveaux clés
            support_resistance = self.detect_support_resistance(image_rgb, price_range, candles)
            
            # Détection des patterns
            patterns = self.detect_patterns(image_rgb, candles)
            
            # Détection des indicateurs
            indicators = self.detect_indicators(image_rgb)
            
            # Analyse de tendance
            trend = self.analyze_trend(candles, support_resistance)
            
            # Détection des signaux
            signals = self.detect_signals(candles, patterns, indicators, support_resistance, trend)
            
            # Compilation des résultats
            results = {
                "chart_info": chart_info,
                "timeframe": timeframe,
                "price_range": price_range,
                "support_resistance": support_resistance,
                "patterns": patterns,
                "indicators": indicators,
                "trend": trend,
                "signals": signals,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Analyse complétée pour {image_path}")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de l'image {image_path}: {str(e)}")
            return {
                "error": str(e),
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    def detect_chart_type(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Détecte le type de graphique (chandeliers, barres, ligne).
        
        Args:
            image (np.ndarray): Image à analyser.
            
        Returns:
            Dict[str, Any]: Informations sur le type de graphique.
        """
        # Note: Dans une version complète, cette fonction utiliserait
        # des techniques de vision par ordinateur avancées pour la détection
        
        # Implémentation simplifiée: détecte les chandeliers par défaut
        # Nous pourrions utiliser des méthodes de détection de formes pour un système complet
        
        # Détermine la taille de l'image et d'autres caractéristiques générales
        height, width, channels = image.shape
        
        # Pour cette version simplifiée, on suppose que c'est un graphique en chandeliers
        chart_info = {
            "type": "candlestick",
            "width": width,
            "height": height,
            "background_color": self._detect_background_color(image),
            "confidence": 0.9  # Confiance arbitraire pour la démo
        }
        
        return chart_info
    
    def _detect_background_color(self, image: np.ndarray) -> str:
        """
        Détecte la couleur de fond du graphique.
        
        Args:
            image (np.ndarray): Image à analyser.
            
        Returns:
            str: Description de la couleur de fond ("light", "dark", etc.).
        """
        # Échantillonne les coins de l'image pour déterminer la couleur de fond
        h, w, _ = image.shape
        corners = [
            image[0, 0],      # Coin supérieur gauche
            image[0, w-1],    # Coin supérieur droit
            image[h-1, 0],    # Coin inférieur gauche
            image[h-1, w-1]   # Coin inférieur droit
        ]
        
        # Calcule la moyenne des valeurs RGB
        avg_color = np.mean(corners, axis=0)
        avg_intensity = np.mean(avg_color)
        
        # Détermine si le fond est clair ou sombre
        if avg_intensity > 128:
            return "light"
        else:
            return "dark"
    
    def detect_timeframe(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Détecte le timeframe du graphique.
        
        Args:
            image (np.ndarray): Image à analyser.
            
        Returns:
            Dict[str, Any]: Informations sur le timeframe détecté.
        """
        # Note: Dans une implémentation complète, cette fonction utiliserait
        # de l'OCR pour détecter le texte indiquant le timeframe
        
        # Version simplifiée: retourne une valeur par défaut avec faible confiance
        return {
            "value": "unknown",
            "confidence": 0.3
        }
    
    def detect_price_range(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Détecte la plage de prix sur le graphique.
        
        Args:
            image (np.ndarray): Image à analyser.
            
        Returns:
            Dict[str, Any]: Informations sur la plage de prix.
        """
        # Version simplifiée: estime la plage de prix en fonction de la hauteur de l'image
        # Dans une version complète, nous utiliserions l'OCR pour lire les valeurs d'échelle
        
        height, _, _ = image.shape
        
        # Valeurs fictives pour la démo
        # Une implémentation réelle utiliserait l'OCR pour détecter les valeurs sur l'axe Y
        return {
            "min": 0,
            "max": 100,
            "range": 100,
            "confidence": 0.3
        }
    
    def detect_candles(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Détecte les chandeliers sur le graphique.
        
        Args:
            image (np.ndarray): Image à analyser.
            
        Returns:
            List[Dict[str, Any]]: Liste des chandeliers détectés.
        """
        # Version simplifiée: génère des chandeliers fictifs
        # Une implémentation réelle utiliserait des techniques de vision par ordinateur
        # pour détecter les formes et couleurs des chandeliers
        
        # Génère 20 chandeliers fictifs pour la démo
        candles = []
        for i in range(20):
            open_val = 50 + np.random.normal(0, 5)
            close_val = open_val + np.random.normal(0, 3)
            high_val = max(open_val, close_val) + abs(np.random.normal(0, 2))
            low_val = min(open_val, close_val) - abs(np.random.normal(0, 2))
            
            candle = {
                "index": i,
                "open": open_val,
                "high": high_val,
                "low": low_val,
                "close": close_val,
                "bullish": close_val > open_val,
                "x_pos": 50 + i * 15,  # Position horizontale fictive
                "confidence": 0.7
            }
            candles.append(candle)
        
        return candles
    
    def detect_support_resistance(self, image: np.ndarray, price_range: Dict[str, Any], 
                               candles: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Détecte les niveaux de support et résistance.
        
        Args:
            image (np.ndarray): Image à analyser.
            price_range (Dict[str, Any]): Plage de prix.
            candles (List[Dict[str, Any]]): Liste des chandeliers.
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Niveaux de support et résistance.
        """
        # Version simplifiée: génère des niveaux fictifs basés sur les chandeliers
        # Une implémentation réelle utiliserait la détection de lignes horizontales
        # et l'analyse des points de contact
        
        if not candles:
            return {"support": [], "resistance": []}
        
        # Extraction des prix
        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]
        
        # Recherche des résistances (maximums locaux)
        resistance_candidates = []
        for i in range(1, len(highs)-1):
            if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                resistance_candidates.append({
                    "price": highs[i],
                    "index": i,
                    "strength": 0.5 + np.random.random() * 0.3  # Force fictive
                })
        
        # Recherche des supports (minimums locaux)
        support_candidates = []
        for i in range(1, len(lows)-1):
            if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                support_candidates.append({
                    "price": lows[i],
                    "index": i,
                    "strength": 0.5 + np.random.random() * 0.3  # Force fictive
                })
        
        # Sélection des niveaux les plus significatifs (pour la démo)
        supports = sorted(support_candidates, key=lambda x: x["strength"], reverse=True)[:3]
        resistances = sorted(resistance_candidates, key=lambda x: x["strength"], reverse=True)[:3]
        
        return {
            "support": supports,
            "resistance": resistances
        }
    
    def detect_patterns(self, image: np.ndarray, candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Détecte les patterns chartistes.
        
        Args:
            image (np.ndarray): Image à analyser.
            candles (List[Dict[str, Any]]): Liste des chandeliers.
            
        Returns:
            List[Dict[str, Any]]: Patterns détectés.
        """
        # Version simplifiée: détecte des patterns fictifs
        # Une implémentation réelle analyserait les séquences de chandeliers
        # pour identifier des patterns connus
        
        patterns = []
        
        # Fonction simplifiée qui retourne un pattern aléatoire pour la démo
        pattern_types = [
            "doji", "hammer", "engulfing_bullish", "engulfing_bearish", 
            "morning_star", "evening_star", "harami"
        ]
        
        # Choisit un pattern au hasard pour la démo
        if np.random.random() > 0.3:  # 70% de chance de détecter un pattern
            pattern_type = np.random.choice(pattern_types)
            patterns.append({
                "type": pattern_type,
                "start_index": max(0, len(candles) - 5),
                "end_index": len(candles) - 1,
                "confidence": 0.6 + np.random.random() * 0.3,
                "description": f"Possible {pattern_type.replace('_', ' ')} pattern"
            })
        
        return patterns
    
    def detect_indicators(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Détecte les indicateurs techniques sur le graphique.
        
        Args:
            image (np.ndarray): Image à analyser.
            
        Returns:
            Dict[str, Any]: Indicateurs détectés.
        """
        # Version simplifiée: détecte des indicateurs fictifs
        # Une implémentation réelle analyserait les lignes et couleurs
        # pour identifier les indicateurs techniques
        
        indicators = {
            "moving_averages": [],
            "oscillators": [],
            "other": []
        }
        
        # Génère des indicateurs fictifs pour la démo
        if np.random.random() > 0.3:  # 70% de chance de détecter des MAs
            # Détection fictive de moyennes mobiles
            ma_types = ["SMA", "EMA"]
            ma_periods = [20, 50, 200]
            
            for _ in range(np.random.randint(1, 3)):
                ma_type = np.random.choice(ma_types)
                ma_period = np.random.choice(ma_periods)
                indicators["moving_averages"].append({
                    "type": ma_type,
                    "period": ma_period,
                    "value": 50 + np.random.normal(0, 5),
                    "trend": np.random.choice(["up", "down", "sideways"]),
                    "confidence": 0.6 + np.random.random() * 0.3
                })
        
        if np.random.random() > 0.5:  # 50% de chance de détecter des oscillateurs
            # Détection fictive d'oscillateurs
            if np.random.random() > 0.5:
                indicators["oscillators"].append({
                    "type": "RSI",
                    "period": 14,
                    "value": np.random.randint(0, 100),
                    "condition": np.random.choice(["overbought", "oversold", "neutral"]),
                    "confidence": 0.6 + np.random.random() * 0.3
                })
            
            if np.random.random() > 0.5:
                indicators["oscillators"].append({
                    "type": "MACD",
                    "settings": "12,26,9",
                    "histogram": np.random.choice(["positive", "negative"]),
                    "signal": np.random.choice(["bullish_crossover", "bearish_crossover", "neutral"]),
                    "confidence": 0.6 + np.random.random() * 0.3
                })
        
        return indicators
    
    def analyze_trend(self, candles: List[Dict[str, Any]], 
                    support_resistance: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Analyse la tendance globale du graphique.
        
        Args:
            candles (List[Dict[str, Any]]): Liste des chandeliers.
            support_resistance (Dict[str, List[Dict[str, Any]]]): Niveaux de support et résistance.
            
        Returns:
            Dict[str, Any]: Analyse de la tendance.
        """
        # Version simplifiée: détermine la tendance fictive
        # Une implémentation réelle analyserait la pente des prix, les niveaux
        # de support/résistance et les moyennes mobiles
        
        if not candles:
            return {
                "direction": "unknown",
                "strength": 0,
                "confidence": 0
            }
        
        # Calcule la direction globale en comparant le premier et dernier chandelier
        if len(candles) >= 2:
            first_close = candles[0]["close"]
            last_close = candles[-1]["close"]
            
            if last_close > first_close:
                direction = "uptrend"
                strength = (last_close - first_close) / first_close
            elif last_close < first_close:
                direction = "downtrend"
                strength = (first_close - last_close) / first_close
            else:
                direction = "sideways"
                strength = 0
        else:
            direction = "unknown"
            strength = 0
        
        # Compte les chandeliers haussiers et baissiers
        bullish_count = sum(1 for c in candles if c["bullish"])
        bearish_count = len(candles) - bullish_count
        
        # Ajuste la confiance en fonction de la distribution des chandeliers
        if direction == "uptrend" and bullish_count > bearish_count:
            confidence = 0.5 + 0.5 * (bullish_count / len(candles))
        elif direction == "downtrend" and bearish_count > bullish_count:
            confidence = 0.5 + 0.5 * (bearish_count / len(candles))
        else:
            # Tendance contradictoire avec les chandeliers
            confidence = 0.3
            
            # Si les chandeliers contredisent fortement la tendance, on révise
            if direction == "uptrend" and bearish_count > bullish_count * 2:
                direction = "mixed_bearish"
            elif direction == "downtrend" and bullish_count > bearish_count * 2:
                direction = "mixed_bullish"
        
        return {
            "direction": direction,
            "strength": float(strength),
            "bullish_candles": bullish_count,
            "bearish_candles": bearish_count,
            "confidence": float(confidence)
        }
    
    def detect_signals(self, candles: List[Dict[str, Any]], 
                     patterns: List[Dict[str, Any]], 
                     indicators: Dict[str, Any],
                     support_resistance: Dict[str, List[Dict[str, Any]]],
                     trend: Dict[str, Any]) -> Dict[str, Any]:
        """
        Détecte les signaux de trading basés sur l'analyse complète.
        
        Args:
            candles (List[Dict[str, Any]]): Liste des chandeliers.
            patterns (List[Dict[str, Any]]): Patterns détectés.
            indicators (Dict[str, Any]): Indicateurs détectés.
            support_resistance (Dict[str, List[Dict[str, Any]]]): Niveaux de support et résistance.
            trend (Dict[str, Any]): Analyse de la tendance.
            
        Returns:
            Dict[str, Any]: Signaux de trading détectés.
        """
        # Version simplifiée: génère des signaux fictifs basés sur les données
        # Une implémentation réelle combinerait tous les facteurs d'analyse
        # pour produire des signaux de trading cohérents
        
        # Initialisation du signal
        signal = {
            "type": "neutral",
            "direction": "none",
            "strength": 0.0,
            "confidence": 0.0,
            "reasoning": []
        }
        
        # Analyse de la tendance
        if trend["direction"] == "uptrend" and trend["confidence"] > 0.6:
            signal["reasoning"].append(f"Strong uptrend detected (confidence: {trend['confidence']:.2f})")
            signal["direction"] = "buy"
            signal["strength"] += trend["confidence"] * 0.3
            
        elif trend["direction"] == "downtrend" and trend["confidence"] > 0.6:
            signal["reasoning"].append(f"Strong downtrend detected (confidence: {trend['confidence']:.2f})")
            signal["direction"] = "sell"
            signal["strength"] += trend["confidence"] * 0.3
        
        # Analyse des patterns
        for pattern in patterns:
            if "bullish" in pattern["type"] and pattern["confidence"] > 0.7:
                signal["reasoning"].append(f"Bullish pattern detected: {pattern['type']} (confidence: {pattern['confidence']:.2f})")
                
                # Renforce un signal d'achat ou atténue un signal de vente
                if signal["direction"] == "buy" or signal["direction"] == "none":
                    signal["direction"] = "buy"
                    signal["strength"] += pattern["confidence"] * 0.2
                elif signal["direction"] == "sell":
                    signal["strength"] -= pattern["confidence"] * 0.1
            
            elif "bearish" in pattern["type"] and pattern["confidence"] > 0.7:
                signal["reasoning"].append(f"Bearish pattern detected: {pattern['type']} (confidence: {pattern['confidence']:.2f})")
                
                # Renforce un signal de vente ou atténue un signal d'achat
                if signal["direction"] == "sell" or signal["direction"] == "none":
                    signal["direction"] = "sell"
                    signal["strength"] += pattern["confidence"] * 0.2
                elif signal["direction"] == "buy":
                    signal["strength"] -= pattern["confidence"] * 0.1
        
        # Analyse des indicateurs
        # Moyennes mobiles
        for ma in indicators.get("moving_averages", []):
            if ma["trend"] == "up" and ma["confidence"] > 0.6:
                signal["reasoning"].append(f"{ma['type']}{ma['period']} trending up (confidence: {ma['confidence']:.2f})")
                
                if signal["direction"] == "buy" or signal["direction"] == "none":
                    signal["direction"] = "buy"
                    signal["strength"] += ma["confidence"] * 0.15
            
            elif ma["trend"] == "down" and ma["confidence"] > 0.6:
                signal["reasoning"].append(f"{ma['type']}{ma['period']} trending down (confidence: {ma['confidence']:.2f})")
                
                if signal["direction"] == "sell" or signal["direction"] == "none":
                    signal["direction"] = "sell"
                    signal["strength"] += ma["confidence"] * 0.15
        
        # Oscillateurs
        for osc in indicators.get("oscillators", []):
            if osc["type"] == "RSI":
                if osc["condition"] == "oversold" and osc["confidence"] > 0.6:
                    signal["reasoning"].append(f"RSI oversold (confidence: {osc['confidence']:.2f})")
                    
                    if signal["direction"] == "buy" or signal["direction"] == "none":
                        signal["direction"] = "buy"
                        signal["strength"] += osc["confidence"] * 0.15
                
                elif osc["condition"] == "overbought" and osc["confidence"] > 0.6:
                    signal["reasoning"].append(f"RSI overbought (confidence: {osc['confidence']:.2f})")
                    
                    if signal["direction"] == "sell" or signal["direction"] == "none":
                        signal["direction"] = "sell"
                        signal["strength"] += osc["confidence"] * 0.15
            
            elif osc["type"] == "MACD":
                if osc["signal"] == "bullish_crossover" and osc["confidence"] > 0.6:
                    signal["reasoning"].append(f"MACD bullish crossover (confidence: {osc['confidence']:.2f})")
                    
                    if signal["direction"] == "buy" or signal["direction"] == "none":
                        signal["direction"] = "buy"
                        signal["strength"] += osc["confidence"] * 0.15
                
                elif osc["signal"] == "bearish_crossover" and osc["confidence"] > 0.6:
                    signal["reasoning"].append(f"MACD bearish crossover (confidence: {osc['confidence']:.2f})")
                    
                    if signal["direction"] == "sell" or signal["direction"] == "none":
                        signal["direction"] = "sell"
                        signal["strength"] += osc["confidence"] * 0.15
        
        # Niveaux de support et résistance
        if candles:
            last_close = candles[-1]["close"]
            
            # Vérifie si le prix est proche d'un support
            for support in support_resistance.get("support", []):
                if abs(last_close - support["price"]) / support["price"] < 0.01:  # Moins de 1% d'écart
                    signal["reasoning"].append(f"Price near support level at {support['price']:.2f} (strength: {support['strength']:.2f})")
                    
                    if signal["direction"] == "buy" or signal["direction"] == "none":
                        signal["direction"] = "buy"
                        signal["strength"] += support["strength"] * 0.2
            
            # Vérifie si le prix est proche d'une résistance
            for resistance in support_resistance.get("resistance", []):
                if abs(last_close - resistance["price"]) / resistance["price"] < 0.01:  # Moins de 1% d'écart
                    signal["reasoning"].append(f"Price near resistance level at {resistance['price']:.2f} (strength: {resistance['strength']:.2f})")
                    
                    if signal["direction"] == "sell" or signal["direction"] == "none":
                        signal["direction"] = "sell"
                        signal["strength"] += resistance["strength"] * 0.2
        
        # Normalise la force du signal entre 0 et 1
        signal["strength"] = min(max(signal["strength"], 0.0), 1.0)
        
        # Détermine le type de signal en fonction de la force
        if signal["strength"] < 0.3:
            signal["type"] = "weak"
        elif signal["strength"] < 0.6:
            signal["type"] = "moderate"
        else:
            signal["type"] = "strong"
        
        # Détermine la confiance globale
        signal["confidence"] = signal["strength"]
        
        # Si pas de direction claire, revient à neutre
        if signal["direction"] == "none" or signal["strength"] < 0.2:
            signal["direction"] = "neutral"
            signal["type"] = "neutral"
        
        return signal
    
    def generate_mbongi_description(self, analysis_results: Dict[str, Any], 
                                  metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Génère une description MBONGI à partir des résultats d'analyse.
        
        Args:
            analysis_results (Dict[str, Any]): Résultats de l'analyse d'image.
            metadata (Dict[str, Any], optional): Métadonnées supplémentaires.
            
        Returns:
            str: Description MBONGI au format markdown.
        """
        if not analysis_results:
            return "# Erreur d'analyse\n\nAucun résultat d'analyse disponible."
        
        # Récupère les informations de base
        signals = analysis_results.get("signals", {})
        trend = analysis_results.get("trend", {})
        patterns = analysis_results.get("patterns", [])
        indicators = analysis_results.get("indicators", {})
        support_resistance = analysis_results.get("support_resistance", {})
        
        # Détermine la direction et le type de setup
        direction = signals.get("direction", "neutral").upper()
        if direction == "BUY":
            setup_type = "Bullish"
        elif direction == "SELL":
            setup_type = "Bearish"
        else:
            setup_type = "Neutral"
        
        # Détermine le timeframe
        timeframe = "Unknown"
        if metadata and "timeframe" in metadata:
            timeframe = metadata["timeframe"]
        elif analysis_results.get("timeframe", {}).get("value", "unknown") != "unknown":
            timeframe = analysis_results["timeframe"]["value"]
        
        # Détermine l'instrument
        instrument = "Unknown"
        if metadata and "instrument" in metadata:
            instrument = metadata["instrument"]
        
        # Construit la description MBONGI
        mbongi = f"# Setup {direction} sur {instrument} ({timeframe})\n\n"
        
        # Type de setup et confiance
        setup_types = []
        if patterns:
            for pattern in patterns:
                pattern_name = pattern["type"].replace("_", " ").title()
                setup_types.append(pattern_name)
        
        if not setup_types:
            if trend.get("direction") == "uptrend":
                setup_types.append("Trend Continuation (Bull)")
            elif trend.get("direction") == "downtrend":
                setup_types.append("Trend Continuation (Bear)")
            else:
                setup_types.append("Range Trading")
        
        setup_type_str = ", ".join(setup_types)
        mbongi += f"Type: {setup_type_str}\n"
        mbongi += f"Confiance: {int(signals.get('confidence', 0) * 10)}/10\n\n"
        
        # Analyse technique
        mbongi += "## Analyse technique\n"
        
        # Tendance
        if trend:
            trend_dir = trend.get("direction", "unknown")
            if trend_dir == "uptrend":
                mbongi += "Le marché est en tendance haussière "
            elif trend_dir == "downtrend":
                mbongi += "Le marché est en tendance baissière "
            elif trend_dir == "sideways":
                mbongi += "Le marché évolue dans un range "
            else:
                mbongi += "La tendance du marché est incertaine "
            
            mbongi += f"avec une force de {int(trend.get('strength', 0) * 100)}%. "
            mbongi += f"Il y a {trend.get('bullish_candles', 0)} chandeliers haussiers et {trend.get('bearish_candles', 0)} chandeliers baissiers visibles.\n\n"
        
        # Patterns
        if patterns:
            mbongi += "### Patterns identifiés\n"
            for pattern in patterns:
                pattern_name = pattern["type"].replace("_", " ").title()
                mbongi += f"- {pattern_name} (confiance: {int(pattern.get('confidence', 0) * 10)}/10)\n"
            mbongi += "\n"
        
        # Indicateurs techniques
        if indicators:
            mbongi += "### Indicateurs techniques\n"
            
            # Moyennes mobiles
            if indicators.get("moving_averages"):
                mbongi += "#### Moyennes mobiles\n"
                for ma in indicators["moving_averages"]:
                    ma_type = ma.get("type", "MA")
                    ma_period = ma.get("period", "?")
                    ma_trend = ma.get("trend", "neutre")
                    if ma_trend == "up":
                        trend_desc = "haussière"
                    elif ma_trend == "down":
                        trend_desc = "baissière"
                    else:
                        trend_desc = "neutre"
                    
                    mbongi += f"- {ma_type}{ma_period}: Tendance {trend_desc}\n"
                mbongi += "\n"
            
            # Oscillateurs
            if indicators.get("oscillators"):
                mbongi += "#### Oscillateurs\n"
                for osc in indicators["oscillators"]:
                    if osc["type"] == "RSI":
                        mbongi += f"- RSI({osc.get('period', 14)}): {osc.get('value', '?')} - Condition: {osc.get('condition', 'neutre')}\n"
                    elif osc["type"] == "MACD":
                        mbongi += f"- MACD({osc.get('settings', '12,26,9')}): Histogramme {osc.get('histogram', 'neutre')}, Signal: {osc.get('signal', 'neutre')}\n"
                mbongi += "\n"
        
        # Niveaux clés
        mbongi += "## Niveaux clés\n"
        
        # Supports
        if support_resistance.get("support"):
            mbongi += "### Supports\n"
            for support in support_resistance["support"]:
                mbongi += f"- {support.get('price', 0):.2f} (force: {int(support.get('strength', 0) * 10)}/10)\n"
            mbongi += "\n"
        else:
            mbongi += "### Supports\n- Aucun support significatif identifié\n\n"
        
        # Résistances
        if support_resistance.get("resistance"):
            mbongi += "### Résistances\n"
            for resistance in support_resistance["resistance"]:
                mbongi += f"- {resistance.get('price', 0):.2f} (force: {int(resistance.get('strength', 0) * 10)}/10)\n"
            mbongi += "\n"
        else:
            mbongi += "### Résistances\n- Aucune résistance significative identifiée\n\n"
        
        # Raisonnement de trading
        mbongi += "## Signal de trading\n"
        if signals:
            signal_type = signals.get("type", "neutral")
            signal_dir = signals.get("direction", "neutral")
            
            if signal_dir == "buy":
                mbongi += f"Signal d'achat "
                if signal_type == "strong":
                    mbongi += "fort"
                elif signal_type == "moderate":
                    mbongi += "modéré"
                else:
                    mbongi += "faible"
            elif signal_dir == "sell":
                mbongi += f"Signal de vente "
                if signal_type == "strong":
                    mbongi += "fort"
                elif signal_type == "moderate":
                    mbongi += "modéré"
                else:
                    mbongi += "faible"
            else:
                mbongi += "Pas de signal clair"
            
            mbongi += f" (confiance: {int(signals.get('confidence', 0) * 10)}/10)\n\n"
            
            if signals.get("reasoning"):
                mbongi += "### Raisonnement\n"
                for reason in signals["reasoning"]:
                    mbongi += f"- {reason}\n"
                mbongi += "\n"
        
        # Horodatage
        mbongi += f"\n## Timestamp\n"
        mbongi += f"Analyse générée automatiquement le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return mbongi
    
    def integrate_with_tradingview_importer(self, importer_module_path: str) -> bool:
        """
        Intègre l'agent de vision avec l'interface d'importation TradingView.
        
        Args:
            importer_module_path (str): Chemin vers le module d'importation TradingView.
            
        Returns:
            bool: True si l'intégration a réussi, False sinon.
        """
        try:
            # Vérifie si le module existe
            if not os.path.exists(importer_module_path):
                logger.error(f"Module d'importation introuvable: {importer_module_path}")
                return False
            
            # Tente d'importé le module
            sys.path.append(os.path.dirname(importer_module_path))
            import importlib.util
            spec = importlib.util.spec_from_file_location("tradingview_importer", importer_module_path)
            importer_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(importer_module)
            
            # Vérifie si la classe TradingViewImporter existe
            if not hasattr(importer_module, "TradingViewImporter"):
                logger.error("Module d'importation ne contient pas la classe TradingViewImporter")
                return False
            
            logger.info(f"Module d'importation TradingView intégré avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'intégration avec l'importateur TradingView: {str(e)}")
            return False
    
    def save_analysis_results(self, image_path: str, results: Dict[str, Any], 
                            output_dir: Optional[str] = None) -> str:
        """
        Sauvegarde les résultats d'analyse dans un fichier JSON.
        
        Args:
            image_path (str): Chemin de l'image analysée.
            results (Dict[str, Any]): Résultats de l'analyse.
            output_dir (str, optional): Répertoire de sortie.
            
        Returns:
            str: Chemin du fichier JSON créé.
        """
        try:
            # Détermine le répertoire de sortie
            if output_dir is None:
                # Utilise le même répertoire que l'image
                output_dir = os.path.dirname(image_path)
            
            # Crée le répertoire s'il n'existe pas
            os.makedirs(output_dir, exist_ok=True)
            
            # Génère un nom de fichier basé sur l'image
            image_basename = os.path.splitext(os.path.basename(image_path))[0]
            output_path = os.path.join(output_dir, f"{image_basename}_analysis.json")
            
            # Sauvegarde les résultats en JSON
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=lambda x: str(x) if isinstance(x, (datetime, np.float32, np.float64)) else x)
            
            logger.info(f"Résultats d'analyse sauvegardés: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des résultats: {str(e)}")
            return ""
    
    def save_mbongi_description(self, image_path: str, mbongi_content: str,
                              output_dir: Optional[str] = None) -> str:
        """
        Sauvegarde la description MBONGI dans un fichier markdown.
        
        Args:
            image_path (str): Chemin de l'image analysée.
            mbongi_content (str): Contenu de la description MBONGI.
            output_dir (str, optional): Répertoire de sortie.
            
        Returns:
            str: Chemin du fichier markdown créé.
        """
        try:
            # Détermine le répertoire de sortie
            if output_dir is None:
                # Utilise le même répertoire que l'image
                output_dir = os.path.dirname(image_path)
            
            # Crée le répertoire s'il n'existe pas
            os.makedirs(output_dir, exist_ok=True)
            
            # Génère un nom de fichier basé sur l'image
            image_basename = os.path.splitext(os.path.basename(image_path))[0]
            output_path = os.path.join(output_dir, f"{image_basename}_mbongi.md")
            
            # Sauvegarde la description MBONGI
            with open(output_path, 'w') as f:
                f.write(mbongi_content)
            
            logger.info(f"Description MBONGI sauvegardée: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la description MBONGI: {str(e)}")
            return ""
    
    def process_image(self, image_path: str, metadata: Optional[Dict[str, Any]] = None,
                    save_results: bool = True, output_dir: Optional[str] = None) -> Dict[str, str]:
        """
        Traite une image complète: analyse, génération MBONGI et sauvegarde.
        
        Args:
            image_path (str): Chemin de l'image à analyser.
            metadata (Dict[str, Any], optional): Métadonnées supplémentaires.
            save_results (bool): Si True, sauvegarde les résultats.
            output_dir (str, optional): Répertoire de sortie.
            
        Returns:
            Dict[str, str]: Chemins des fichiers générés.
        """
        try:
            # Analyse l'image
            analysis_results = self.analyze_image(image_path)
            
            # Génère la description MBONGI
            mbongi_content = self.generate_mbongi_description(analysis_results, metadata)
            
            # Sauvegarde les résultats si demandé
            results_paths = {
                "analysis": "",
                "mbongi": ""
            }
            
            if save_results:
                results_paths["analysis"] = self.save_analysis_results(
                    image_path, analysis_results, output_dir)
                
                results_paths["mbongi"] = self.save_mbongi_description(
                    image_path, mbongi_content, output_dir)
            
            return {
                "paths": results_paths,
                "analysis": analysis_results,
                "mbongi": mbongi_content
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'image {image_path}: {str(e)}")
            return {
                "paths": {"analysis": "", "mbongi": ""},
                "analysis": {"error": str(e)},
                "mbongi": f"# Erreur d'analyse\n\nUne erreur s'est produite lors de l'analyse: {str(e)}"
            }
    
    def process_directory(self, directory_path: str, metadata: Optional[Dict[str, Any]] = None,
                         recursive: bool = False) -> Dict[str, List[Dict[str, str]]]:
        """
        Traite toutes les images dans un répertoire.
        
        Args:
            directory_path (str): Chemin du répertoire à traiter.
            metadata (Dict[str, Any], optional): Métadonnées supplémentaires.
            recursive (bool): Si True, traite aussi les sous-répertoires.
            
        Returns:
            Dict[str, List[Dict[str, str]]]: Résultats par répertoire.
        """
        try:
            # Vérifie si le répertoire existe
            if not os.path.isdir(directory_path):
                logger.error(f"Répertoire inexistant: {directory_path}")
                return {"error": f"Répertoire inexistant: {directory_path}"}
            
            results = {
                "processed_images": [],
                "failed_images": []
            }
            
            # Trouve toutes les images dans le répertoire
            image_paths = []
            for ext in ['.png', '.jpg', '.jpeg', '.bmp']:
                image_paths.extend(glob.glob(os.path.join(directory_path, f"*{ext}")))
                if recursive:
                    image_paths.extend(glob.glob(os.path.join(directory_path, f"**/*{ext}")))
            
            # Traite chaque image
            for image_path in image_paths:
                try:
                    result = self.process_image(image_path, metadata, True)
                    results["processed_images"].append({
                        "image_path": image_path,
                        "results_paths": result["paths"]
                    })
                except Exception as e:
                    results["failed_images"].append({
                        "image_path": image_path,
                        "error": str(e)
                    })
            
            logger.info(f"Traitement terminé: {len(results['processed_images'])} images traitées, "
                       f"{len(results['failed_images'])} échecs.")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du répertoire {directory_path}: {str(e)}")
            return {"error": str(e)}

def main():
    """Fonction principale pour tester l'agent de vision."""
    import argparse
    parser = argparse.ArgumentParser(description='Agent de vision pour l\'analyse de graphiques de trading.')
    parser.add_argument('--image', type=str, help='Chemin de l\'image à analyser')
    parser.add_argument('--dir', type=str, help='Répertoire contenant des images à analyser')
    parser.add_argument('--recursive', action='store_true', help='Traiter récursivement les sous-répertoires')
    parser.add_argument('--output', type=str, help='Répertoire de sortie pour les résultats')
    parser.add_argument('--instrument', type=str, default='US30', help='Instrument financier')
    parser.add_argument('--timeframe', type=str, default='M5', help='Timeframe')
    
    args = parser.parse_args()
    
    # Crée l'agent de vision
    vision_agent = VisionAgent()
    
    # Métadonnées
    metadata = {
        "instrument": args.instrument,
        "timeframe": args.timeframe
    }
    
    # Traite une image ou un répertoire
    if args.image:
        if os.path.isfile(args.image):
            result = vision_agent.process_image(args.image, metadata, True, args.output)
            print(f"Analyse terminée:")
            print(f"- Analyse: {result['paths']['analysis']}")
            print(f"- MBONGI: {result['paths']['mbongi']}")
        else:
            print(f"Erreur: Image introuvable: {args.image}")
    
    elif args.dir:
        if os.path.isdir(args.dir):
            results = vision_agent.process_directory(args.dir, metadata, args.recursive)
            print(f"Traitement terminé:")
            print(f"- Images traitées: {len(results['processed_images'])}")
            print(f"- Échecs: {len(results['failed_images'])}")
        else:
            print(f"Erreur: Répertoire introuvable: {args.dir}")
    
    else:
        print("Erreur: Vous devez spécifier une image (--image) ou un répertoire (--dir)")

if __name__ == "__main__":
    main()