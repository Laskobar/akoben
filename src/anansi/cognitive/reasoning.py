"""
Module de raisonnement pour Anansi, adapté du composant reasoning.py de Goose
"""

import logging
from typing import Dict, List, Any, Optional
from src.anansi.prompts.qwen_prompts import COGNITIVE_CYCLE_PROMPT

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AnansiReasoning")

class Reasoning:
    """
    Système de raisonnement pour Anansi (inspiré de Goose)
    
    Fournit des capacités de raisonnement pour analyser:
    - Situations de marché
    - Stratégies potentielles
    - Risques et opportunités
    """
    
    def __init__(self, config: Dict = None, llm_caller=None):
        """
        Initialise le système de raisonnement.
        
        Args:
            config: Configuration du système de raisonnement
            llm_caller: Fonction pour appeler le LLM
        """
        self.config = config or {}
        self.llm_caller = llm_caller
        logger.info("Système de raisonnement initialisé")
    
    def analyze(self, 
               inputs: Dict[str, Any], 
               memories: List[Dict[str, Any]],
               context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyse une situation en utilisant les inputs et les souvenirs pertinents.
        
        Args:
            inputs: Informations d'entrée à analyser
            memories: Souvenirs pertinents récupérés de la mémoire
            context: Contexte additionnel pour l'analyse
            
        Returns:
            Dict: Résultats de l'analyse avec différentes composantes de raisonnement
        """
        if not self.llm_caller:
            logger.error("LLM caller non défini pour le raisonnement")
            return {"error": "LLM caller non défini"}
        
        context = context or {}
        
        # Préparation des données pour le prompt
        situation_description = self._prepare_situation(inputs, memories, context)
        
        # Création du prompt pour le cycle cognitif
        prompt = COGNITIVE_CYCLE_PROMPT.format(input_situation=situation_description)
        
        # Appel au LLM pour l'analyse
        reasoning_result = self.llm_caller(prompt)
        
        # Extraction des composantes de l'analyse
        parsed_results = self._parse_reasoning_results(reasoning_result)
        
        logger.info("Analyse de raisonnement terminée")
        return parsed_results
    
    def _prepare_situation(self, 
                          inputs: Dict[str, Any], 
                          memories: List[Dict[str, Any]],
                          context: Dict[str, Any]) -> str:
        """
        Prépare une description détaillée de la situation à analyser.
        
        Args:
            inputs: Informations d'entrée
            memories: Souvenirs pertinents
            context: Contexte additionnel
            
        Returns:
            str: Description textuelle de la situation
        """
        # Extraction des informations pertinentes des inputs
        market_data = inputs.get("market_data", {})
        price_action = inputs.get("price_action", {})
        indicators = inputs.get("indicators", {})
        current_positions = inputs.get("current_positions", [])
        
        # Construction de la description du marché
        market_description = []
        
        if market_data:
            market_description.append("Données de marché actuelles:")
            for key, value in market_data.items():
                market_description.append(f"- {key}: {value}")
        
        if price_action:
            market_description.append("\nAction des prix:")
            for key, value in price_action.items():
                market_description.append(f"- {key}: {value}")
        
        if indicators:
            market_description.append("\nIndicateurs techniques:")
            for key, value in indicators.items():
                market_description.append(f"- {key}: {value}")
        
        if current_positions:
            market_description.append("\nPositions actuelles:")
            for position in current_positions:
                market_description.append(f"- Symbol: {position.get('symbol')}, Type: {position.get('type')}, Entrée: {position.get('entry_price')}, P/L: {position.get('profit_loss')}")
        
        # Ajout des souvenirs pertinents
        memory_description = []
        if memories:
            memory_description.append("\nSituations similaires précédentes:")
            for i, memory in enumerate(memories, 1):
                experience_date = memory.get("date", "date inconnue")
                outcome = memory.get("outcome", "résultat inconnu")
                memory_description.append(f"{i}. Le {experience_date}, situation similaire avec comme résultat: {outcome}")
        
        # Ajout du contexte additionnel
        context_description = []
        if context:
            context_description.append("\nContexte additionnel:")
            for key, value in context.items():
                if key not in ["market_data", "memories"]:
                    context_description.append(f"- {key}: {value}")
        
        # Assemblage de la description complète
        full_description = "\n".join(market_description + memory_description + context_description)
        
        return full_description
    
    def _parse_reasoning_results(self, reasoning_text: str) -> Dict[str, Any]:
        """
        Parse les résultats du raisonnement LLM en composantes structurées.
        
        Args:
            reasoning_text: Texte brut de l'analyse du LLM
            
        Returns:
            Dict: Composantes structurées du raisonnement
        """
        # Initialisation des composantes
        components = {
            "memory": "",
            "perception": "",
            "reasoning": "",
            "decision": "",
            "learning": "",
            "full_analysis": reasoning_text
        }
        
        # Division par sections (recherche des marqueurs MÉMOIRE, PERCEPTION, etc.)
        lines = reasoning_text.split("\n")
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if "MÉMOIRE" in line.upper() or "MEMOIRE" in line.upper():
                current_section = "memory"
                continue
            elif "PERCEPTION" in line.upper():
                current_section = "perception"
                continue
            elif "RAISONNEMENT" in line.upper():
                current_section = "reasoning"
                continue
            elif "DÉCISION" in line.upper() or "DECISION" in line.upper():
                current_section = "decision"
                continue
            elif "APPRENTISSAGE" in line.upper():
                current_section = "learning"
                continue
            
            if current_section and line:
                components[current_section] += line + "\n"
        
        # Nettoyage des composantes (suppression des espaces en début/fin)
        for key in components:
            if isinstance(components[key], str):
                components[key] = components[key].strip()
        
        return components
    
    def evaluate_strategy(self, 
                         strategy: Dict[str, Any], 
                         market_conditions: Dict[str, Any],
                         risk_parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Évalue une stratégie de trading dans les conditions de marché actuelles.
        
        Args:
            strategy: Détails de la stratégie à évaluer
            market_conditions: Conditions actuelles du marché
            risk_parameters: Paramètres de risque à considérer
            
        Returns:
            Dict: Évaluation détaillée de la stratégie
        """
        # Cette méthode sera implémentée ultérieurement
        logger.warning("Méthode evaluate_strategy pas encore implémentée")
        return {"status": "not_implemented"}
