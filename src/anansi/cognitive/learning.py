"""
Module d'apprentissage pour Anansi, adapté du composant learning.py de Goose
"""

import logging
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AnansiLearning")

class Learning:
    """
    Système d'apprentissage pour Anansi (inspiré de Goose)
    
    Responsable de:
    - Extraire des leçons des expériences passées
    - Améliorer les stratégies de trading
    - Adapter les paramètres des modèles
    """
    
    def __init__(self, config: Dict = None, llm_caller=None):
        """
        Initialise le système d'apprentissage.
        
        Args:
            config: Configuration du système d'apprentissage
            llm_caller: Fonction pour appeler le LLM
        """
        self.config = config or {}
        self.llm_caller = llm_caller
        self.learning_path = self.config.get("learning_path", "data/learning")
        os.makedirs(self.learning_path, exist_ok=True)
        
        # Sous-dossiers pour différents types d'apprentissage
        self.lessons_path = os.path.join(self.learning_path, "lessons")
        self.patterns_path = os.path.join(self.learning_path, "patterns")
        self.improvements_path = os.path.join(self.learning_path, "improvements")
        
        os.makedirs(self.lessons_path, exist_ok=True)
        os.makedirs(self.patterns_path, exist_ok=True)
        os.makedirs(self.improvements_path, exist_ok=True)
        
        logger.info(f"Système d'apprentissage initialisé dans {self.learning_path}")
    
    def update(self, 
              inputs: Dict[str, Any], 
              reasoning_results: Dict[str, Any],
              decision: Dict[str, Any], 
              context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Met à jour les connaissances à partir d'une nouvelle expérience.
        
        Args:
            inputs: Données d'entrée qui ont été analysées
            reasoning_results: Résultats de l'analyse du module de raisonnement
            decision: Décision prise par le module de décision
            context: Contexte additionnel
            
        Returns:
            Dict: Résultats de l'apprentissage
        """
        context = context or {}
        
        # Extraction des leçons de cette expérience
        lessons = self._extract_lessons(inputs, reasoning_results, decision, context)
        
        # Enregistrement des leçons
        lesson_id = self._save_lesson(lessons)
        
        # Si des patterns récurrents sont détectés, les enregistrer
        patterns = self._identify_patterns(inputs, reasoning_results, context)
        if patterns:
            pattern_id = self._save_pattern(patterns)
        
        # Si des améliorations sont suggérées, les enregistrer
        improvements = reasoning_results.get("learning", "")
        if improvements:
            improvement_id = self._save_improvement(improvements)
        
        logger.info(f"Apprentissage mis à jour à partir de la nouvelle expérience")
        
        return {
            "lesson_id": lesson_id,
            "patterns": patterns,
            "improvements": improvements
        }
    
    def _extract_lessons(self, 
                        inputs: Dict[str, Any], 
                        reasoning_results: Dict[str, Any],
                        decision: Dict[str, Any], 
                        context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrait des leçons à partir d'une expérience.
        
        Args:
            inputs: Données d'entrée
            reasoning_results: Résultats du raisonnement
            decision: Décision prise
            context: Contexte
            
        Returns:
            Dict: Leçons extraites
        """
        # Base de données pour les leçons
        lessons = {
            "timestamp": time.time(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": context.get("symbol", "inconnu"),
            "timeframe": context.get("timeframe", "inconnu"),
            "action": decision.get("action", "inconnu"),
            "inputs_summary": self._summarize_inputs(inputs),
            "reasoning_summary": self._summarize_reasoning(reasoning_results),
            "decision_summary": self._summarize_decision(decision),
            "context_summary": self._summarize_context(context),
            "explicit_lessons": reasoning_results.get("learning", "Aucune leçon explicite")
        }
        
        return lessons
    
    def _summarize_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un résumé des inputs pour l'apprentissage.
        
        Args:
            inputs: Données d'entrée
            
        Returns:
            Dict: Résumé des inputs
        """
        summary = {}
        
        # Extraction des données clés de manière sélective
        if "market_data" in inputs:
            market_data = inputs["market_data"]
            summary["market_condition"] = market_data.get("condition", "unknown")
            summary["trend"] = market_data.get("trend", "unknown")
            summary["volatility"] = market_data.get("volatility", "unknown")
        
        if "indicators" in inputs:
            indicators = inputs["indicators"]
            summary["indicators"] = {
                k: v for k, v in indicators.items() 
                if k in ["macd", "rsi", "atr", "ema"]  # Indicateurs clés uniquement
            }
        
        return summary
    
    def _summarize_reasoning(self, reasoning_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un résumé du raisonnement pour l'apprentissage.
        
        Args:
            reasoning_results: Résultats du raisonnement
            
        Returns:
            Dict: Résumé du raisonnement
        """
        return {
            "perception": reasoning_results.get("perception", "")[:200] + "...",  # Version tronquée
            "reasoning": reasoning_results.get("reasoning", "")[:200] + "...",
            "decision": reasoning_results.get("decision", "")[:200] + "..."
        }
    
    def _summarize_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un résumé de la décision pour l'apprentdef _summarize_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        
        Crée un résumé de la décision pour l'apprentissage.
        
        Args:
            decision: Décision prise
            
        Returns:
            Dict: Résumé de la décision
        """
        # Extraction des éléments clés de la décision
        return {
            "action": decision.get("action", "unknown"),
            "entry_price": decision.get("entry_price"),
            "stop_loss": decision.get("stop_loss"),
            "take_profit": decision.get("take_profit"),
            "position_size": decision.get("position_size"),
            "validation_status": decision.get("validation_status", "unknown")
        }
    
    def _summarize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un résumé du contexte pour l'apprentissage.
        
        Args:
            context: Contexte
            
        Returns:
            Dict: Résumé du contexte
        """
        summary = {}
        
        # Extraction des informations de contexte pertinentes
        keys_to_include = ["symbol", "timeframe", "capital", "market_hours", "news_impact"]
        for key in keys_to_include:
            if key in context:
                summary[key] = context[key]
        
        return summary
    
    def _save_lesson(self, lesson: Dict[str, Any]) -> str:
        """
        Enregistre une leçon dans la base de connaissances.
        
        Args:
            lesson: Leçon à enregistrer
            
        Returns:
            str: Identifiant de la leçon
        """
        lesson_id = f"lesson_{int(time.time())}"
        file_path = os.path.join(self.lessons_path, f"{lesson_id}.json")
        
        with open(file_path, "w") as f:
            json.dump(lesson, f, indent=2)
        
        logger.info(f"Leçon enregistrée: {lesson_id}")
        return lesson_id
    
    def _identify_patterns(self, 
                          inputs: Dict[str, Any], 
                          reasoning_results: Dict[str, Any],
                          context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identifie des patterns récurrents dans les données.
        
        Args:
            inputs: Données d'entrée
            reasoning_results: Résultats du raisonnement
            context: Contexte
            
        Returns:
            List[Dict]: Patterns identifiés
        """
        # Cette méthode sera implémentée ultérieurement avec des techniques plus avancées
        # Pour l'instant, simplement extraire de l'analyse
        
        patterns = []
        
        # Recherche dans le texte de raisonnement pour des mentions de patterns
        reasoning_text = reasoning_results.get("reasoning", "")
        if "pattern" in reasoning_text.lower() or "motif" in reasoning_text.lower():
            pattern_lines = []
            for line in reasoning_text.split("\n"):
                if "pattern" in line.lower() or "motif" in line.lower():
                    pattern_lines.append(line)
            
            if pattern_lines:
                patterns.append({
                    "type": "text_extracted",
                    "source": "reasoning",
                    "description": "\n".join(pattern_lines)
                })
        
        return patterns
    
    def _save_pattern(self, patterns: List[Dict[str, Any]]) -> str:
        """
        Enregistre des patterns identifiés.
        
        Args:
            patterns: Patterns à enregistrer
            
        Returns:
            str: Identifiant du fichier de patterns
        """
        pattern_id = f"pattern_{int(time.time())}"
        file_path = os.path.join(self.patterns_path, f"{pattern_id}.json")
        
        with open(file_path, "w") as f:
            json.dump(patterns, f, indent=2)
        
        logger.info(f"Patterns enregistrés: {pattern_id}")
        return pattern_id
    
    def _save_improvement(self, improvements: str) -> str:
        """
        Enregistre des suggestions d'amélioration.
        
        Args:
            improvements: Texte des améliorations suggérées
            
        Returns:
            str: Identifiant du fichier d'améliorations
        """
        improvement_id = f"improvement_{int(time.time())}"
        file_path = os.path.join(self.improvements_path, f"{improvement_id}.json")
        
        with open(file_path, "w") as f:
            json.dump({"timestamp": time.time(), "improvements": improvements}, f, indent=2)
        
        logger.info(f"Améliorations enregistrées: {improvement_id}")
        return improvement_id
    
    def get_lessons(self, 
                   filter_criteria: Dict[str, Any] = None, 
                   limit: int = 10) -> List[Dict[str, Any]]:
        """
        Récupère des leçons selon des critères.
        
        Args:
            filter_criteria: Critères de filtrage
            limit: Nombre maximum de leçons à retourner
            
        Returns:
            List[Dict]: Leçons correspondantes
        """
        filter_criteria = filter_criteria or {}
        lessons = []
        
        try:
            # Parcours des fichiers de leçons
            for filename in sorted(os.listdir(self.lessons_path), reverse=True):
                if not filename.endswith(".json"):
                    continue
                    
                file_path = os.path.join(self.lessons_path, filename)
                
                with open(file_path, "r") as f:
                    lesson = json.load(f)
                
                # Application des filtres si spécifiés
                if self._matches_criteria(lesson, filter_criteria):
                    lessons.append(lesson)
                
                if len(lessons) >= limit:
                    break
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des leçons: {str(e)}")
        
        return lessons
    
    def _matches_criteria(self, 
                         item: Dict[str, Any], 
                         criteria: Dict[str, Any]) -> bool:
        """
        Vérifie si un item correspond aux critères de filtrage.
        
        Args:
            item: Item à vérifier
            criteria: Critères de filtrage
            
        Returns:
            bool: True si l'item correspond aux critères
        """
        for key, value in criteria.items():
            # Gestion des clés imbriquées (avec notation par points)
            if "." in key:
                parts = key.split(".")
                current = item
                for part in parts[:-1]:
                    if part not in current:
                        return False
                    current = current[part]
                    
                last_key = parts[-1]
                if last_key not in current or current[last_key] != value:
                    return False
            # Clés simples
            elif key not in item or item[key] != value:
                return False
        
        return True
