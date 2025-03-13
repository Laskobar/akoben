import os
import json
import requests
from datetime import datetime

class StrategyDeveloper:
    """
    Agent spécialisé dans le développement et l'optimisation de stratégies de trading
    """
    def __init__(self, config=None, llm_caller=None, code_llm_caller=None):
        self.config = config or {}
        self.llm_caller = llm_caller
        self.code_llm_caller = code_llm_caller or llm_caller
        print("Agent StrategyDeveloper initialisé")
    
    def develop_strategy(self, strategy_type="mean_reversion", instrument="US30", parameters=None):
        """
        Développe une stratégie de trading selon les paramètres fournis
        """
        parameters = parameters or {}
        print(f"Développement d'une stratégie {strategy_type} pour {instrument}")
        
        # Préparation du contexte pour le LLM
        context = {
            "strategy_type": strategy_type,
            "instrument": instrument,
            "timestamp": datetime.now().isoformat(),
            "parameters": parameters
        }
        
        # Appel au LLM pour le développement de la stratégie
        strategy_description = self._create_strategy_description(context)
        
        # Génération du code Python pour la stratégie
        strategy_code = self._generate_strategy_code(strategy_description, context)
        
        return {
            "context": context,
            "strategy_description": strategy_description,
            "strategy_code": strategy_code,
            "timestamp": datetime.now().isoformat()
        }
    
    def _create_strategy_description(self, context):
        """
        Utilise le LLM pour créer une description détaillée de la stratégie
        """
        if not self.llm_caller:
            return "Aucun LLM disponible pour le développement de stratégie"
        
        strategy_type = context["strategy_type"]
        instrument = context["instrument"]
        parameters = context["parameters"]
        
        strategy_prompts = {
            "mean_reversion": f"""
                Développe une stratégie de trading "retour à la moyenne" (mean reversion) pour l'instrument {instrument}.
                
                Inclus les éléments suivants dans ta description:
                1. Principe de base et logique de la stratégie
                2. Indicateurs techniques utilisés
                3. Conditions précises d'entrée en position
                4. Règles de sortie (take profit et stop loss)
                5. Gestion du risque et dimensionnement des positions
                6. Filtres de tendance ou conditions de marché
                7. Paramètres optimaux suggérés
                8. Avantages et inconvénients potentiels
                
                Crée une stratégie complète et détaillée qui pourrait être implémentée directement en code.
            """,
            
            "trend_following": f"""
                Développe une stratégie de trading "suivi de tendance" (trend following) pour l'instrument {instrument}.
                
                Inclus les éléments suivants dans ta description:
                1. Principe de base et logique de la stratégie
                2. Indicateurs techniques utilisés pour identifier les tendances
                3. Conditions précises d'entrée en position
                4. Règles de sortie (take profit et stop loss)
                5. Gestion du risque et dimensionnement des positions
                6. Filtres ou conditions de marché spécifiques
                7. Paramètres optimaux suggérés
                8. Avantages et inconvénients potentiels
                
                Crée une stratégie complète et détaillée qui pourrait être implémentée directement en code.
            """,
            
            "breakout": f"""
                Développe une stratégie de trading "breakout" (cassure) pour l'instrument {instrument}.
                
                Inclus les éléments suivants dans ta description:
                1. Principe de base et logique de la stratégie
                2. Méthodes d'identification des niveaux clés
                3. Conditions précises de validation des cassures
                4. Règles d'entrée en position
                5. Règles de sortie (take profit et stop loss)
                6. Gestion du risque et dimensionnement des positions
                7. Filtres pour éviter les faux breakouts
                8. Paramètres optimaux suggérés
                9. Avantages et inconvénients potentiels
                
                Crée une stratégie complète et détaillée qui pourrait être implémentée directement en code.
            """
        }
        
        prompt = strategy_prompts.get(
            strategy_type,
            f"""
            Développe une stratégie de trading pour l'instrument {instrument}.
            
            Type de stratégie: {strategy_type}
            
            Inclus les éléments suivants dans ta description:
            1. Principe de base et logique de la stratégie
            2. Indicateurs techniques ou méthodes d'analyse utilisés
            3. Conditions précises d'entrée en position
            4. Règles de sortie (take profit et stop loss)
            5. Gestion du risque et dimensionnement des positions
            6. Filtres ou conditions spécifiques
            7. Paramètres optimaux suggérés
            8. Avantages et inconvénients potentiels
            
            Crée une stratégie complète et détaillée qui pourrait être implémentée directement en code.
            """
        )
        
        return self.llm_caller(prompt)
    
    def _generate_strategy_code(self, strategy_description, context):
        """
        Utilise le LLM spécialisé en code pour générer le code Python de la stratégie
        """
        if not self.code_llm_caller:
            return "Aucun LLM disponible pour la génération de code"
        
        instrument = context["instrument"]
        strategy_type = context["strategy_type"]
        
        prompt = f"""
        Écris un code Python complet pour implémenter la stratégie de trading suivante sur MT5.
        La stratégie est pour l'instrument {instrument} et est de type {strategy_type}.
        
        Voici la description détaillée de la stratégie:
        
        {strategy_description}
        
        Crée une classe Python bien structurée qui hérite d'une classe de base "BaseStrategy".
        Utilise la bibliothèque MetaTrader5 pour Python.
        Implémente toutes les méthodes nécessaires:
        - Initialisation
        - Analyse du marché
        - Calcul des signaux
        - Entrée et sortie de position
        - Gestion des risques
        - Boucle principale
        
        Inclus des commentaires détaillés pour expliquer la logique et les composants.
        Le code doit être complet, fonctionnel et prêt à être utilisé.
        """
        
        return self.code_llm_caller(prompt)