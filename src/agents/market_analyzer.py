import os
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime

class MarketAnalyzer:
    """
    Agent spécialisé dans l'analyse de marché pour les instruments financiers
    """
    def __init__(self, config=None, llm_caller=None):
        self.config = config or {}
        self.llm_caller = llm_caller
        print("Agent MarketAnalyzer initialisé")
    
    def analyze_market(self, instrument="US30", timeframe="M1", parameters=None):
        """
        Analyse le marché pour un instrument et timeframe donnés
        """
        parameters = parameters or {}
        print(f"Analyse du marché pour {instrument} sur timeframe {timeframe}")
        
        # Simulation de l'analyse de marché
        # Dans une implémentation réelle, nous récupérerions les données de marché
        # via une API ou une connexion à MT5
        
        # Préparation du contexte pour le LLM
        context = {
            "instrument": instrument,
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat(),
            "parameters": parameters
        }
        
        # Simulation des résultats d'analyse technique
        market_data = self._simulate_market_data(instrument, timeframe)
        context["market_data"] = market_data
        
        # Appel au LLM pour l'analyse
        analysis = self._perform_analysis(context)
        
        return {
            "context": context,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
    
    def _simulate_market_data(self, instrument, timeframe):
        """
        Simule des données de marché pour test
        Dans une version réelle, nous prendrions les données réelles
        """
        # Simulation simple pour tests
        return {
            "current_price": 38750.25,
            "daily_range": {
                "high": 39120.50,
                "low": 38520.75
            },
            "indicators": {
                "rsi": 62.5,
                "macd": {
                    "line": 25.5,
                    "signal": 15.2,
                    "histogram": 10.3
                },
                "ma": {
                    "ma20": 38500.25,
                    "ma50": 38200.50,
                    "ma200": 37800.75
                },
                "bollinger_bands": {
                    "upper": 39200.50,
                    "middle": 38750.25,
                    "lower": 38300.00
                }
            },
            "volume": 1250000,
            "trend": {
                "short_term": "bullish",
                "medium_term": "neutral",
                "long_term": "bullish"
            },
            "support_resistance": {
                "support": [38500, 38200, 37800],
                "resistance": [39000, 39500, 40000]
            }
        }
    
    def _perform_analysis(self, context):
        """
        Utilise le LLM pour analyser les données de marché
        """
        if not self.llm_caller:
            return "Aucun LLM disponible pour l'analyse"
        
        instrument = context["instrument"]
        market_data = context["market_data"]
        
        prompt = f"""
        En tant qu'expert en analyse technique de marchés financiers, analyse les données suivantes pour l'instrument {instrument}:
        
        Prix actuel: {market_data['current_price']}
        Plage journalière: Haut={market_data['daily_range']['high']}, Bas={market_data['daily_range']['low']}
        
        Indicateurs techniques:
        - RSI: {market_data['indicators']['rsi']}
        - MACD: Ligne={market_data['indicators']['macd']['line']}, Signal={market_data['indicators']['macd']['signal']}, Histogramme={market_data['indicators']['macd']['histogram']}
        - Moyennes Mobiles: MA20={market_data['indicators']['ma']['ma20']}, MA50={market_data['indicators']['ma']['ma50']}, MA200={market_data['indicators']['ma']['ma200']}
        - Bandes de Bollinger: Supérieure={market_data['indicators']['bollinger_bands']['upper']}, Moyenne={market_data['indicators']['bollinger_bands']['middle']}, Inférieure={market_data['indicators']['bollinger_bands']['lower']}
        
        Volume: {market_data['volume']}
        
        Tendances:
        - Court terme: {market_data['trend']['short_term']}
        - Moyen terme: {market_data['trend']['medium_term']}
        - Long terme: {market_data['trend']['long_term']}
        
        Niveaux de support et résistance:
        - Supports: {', '.join(map(str, market_data['support_resistance']['support']))}
        - Résistances: {', '.join(map(str, market_data['support_resistance']['resistance']))}
        
        Fournir une analyse détaillée qui inclut:
        1. Évaluation de la tendance actuelle
        2. Identification des configurations techniques importantes
        3. Zones d'intérêt pour entrées potentielles
        4. Évaluation des risques
        5. Perspective à court terme (prochaines 24h)
        
        Format ton analyse de manière professionnelle et structurée.
        """
        
        return self.llm_caller(prompt)