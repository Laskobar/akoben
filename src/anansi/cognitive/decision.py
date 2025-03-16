"""
Module de décision pour Anansi, adapté du composant decision.py de Goose
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from src.anansi.prompts.qwen_prompts import TRADING_DECISION_PROMPT

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AnansiDecision")

class Decision:
    """
    Système de prise de décision pour Anansi (inspiré de Goose)
    
    Responsable de:
    - Évaluer les options disponibles
    - Sélectionner la meilleure action
    - Justifier la décision prise
    """
    
    def __init__(self, config: Dict = None, llm_caller=None):
        """
        Initialise le système de prise de décision.
        
        Args:
            config: Configuration du système de décision
            llm_caller: Fonction pour appeler le LLM
        """
        self.config = config or {}
        self.llm_caller = llm_caller
        self.max_risk_per_trade = self.config.get("max_risk_per_trade", 0.02)  # 2% par défaut
        self.min_risk_reward = self.config.get("min_risk_reward", 1.5)  # Ratio risque/récompense minimum
        
        logger.info(f"Système de décision initialisé (risque max: {self.max_risk_per_trade*100}%, ratio R/R min: {self.min_risk_reward})")
    
    def decide(self, 
              reasoning_results: Dict[str, Any], 
              context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Prend une décision basée sur les résultats du raisonnement et le contexte.
        
        Args:
            reasoning_results: Résultats de l'analyse du module de raisonnement
            context: Contexte additionnel pour la prise de décision
            
        Returns:
            Dict: Décision prise avec justification et détails
        """
        if not self.llm_caller:
            logger.error("LLM caller non défini pour la prise de décision")
            return {"error": "LLM caller non défini"}
        
        context = context or {}
        
        # Extraction des analyses pertinentes du raisonnement
        technical_analysis = reasoning_results.get("perception", "") + "\n" + reasoning_results.get("reasoning", "")
        risk_assessment = self._extract_risk_assessment(reasoning_results, context)
        
        # Création du prompt pour la décision de trading
        prompt = TRADING_DECISION_PROMPT.format(
            technical_analysis=technical_analysis,
            risk_assessment=risk_assessment
        )
        
        # Appel au LLM pour la décision
        decision_result = self.llm_caller(prompt)
        
        # Structuration de la décision
        structured_decision = self._parse_decision(decision_result)
        
        # Vérification de conformité avec les règles de gestion des risques
        validated_decision = self._validate_decision(structured_decision, context)
        
        logger.info(f"Décision prise: {validated_decision.get('action', 'inconnue')}")
        return validated_decision
    
    def _extract_risk_assessment(self, 
                               reasoning_results: Dict[str, Any], 
                               context: Dict[str, Any]) -> str:
        """
        Extrait l'évaluation des risques des résultats du raisonnement.
        
        Args:
            reasoning_results: Résultats du module de raisonnement
            context: Contexte additionnel
            
        Returns:
            str: Évaluation des risques formatée
        """
        # Si l'analyse contient déjà une section sur les risques, l'utiliser
        if "risk_assessment" in reasoning_results:
            return reasoning_results["risk_assessment"]
        
        # Sinon, extraire des informations de risque de différentes parties de l'analyse
        risk_info = []
        
        # Chercher des informations sur les risques dans le raisonnement
        reasoning_text = reasoning_results.get("reasoning", "")
        if "risque" in reasoning_text.lower():
            risk_lines = [line for line in reasoning_text.split("\n") 
                          if "risque" in line.lower() or "stop" in line.lower()]
            risk_info.extend(risk_lines)
        
        # Chercher des informations sur les risques dans la décision
        decision_text = reasoning_results.get("decision", "")
        if "risque" in decision_text.lower():
            risk_lines = [line for line in decision_text.split("\n") 
                          if "risque" in line.lower() or "stop" in line.lower()]
            risk_info.extend(risk_lines)
        
        # Si un actif est spécifié dans le contexte, inclure sa volatilité
        symbol = context.get("symbol", "")
        if symbol:
            volatility = context.get("volatility", {}).get(symbol, "inconnue")
            risk_info.append(f"Volatilité de {symbol}: {volatility}")
        
        # Si un capital est spécifié, calculer l'exposition maximale
        capital = context.get("capital", 0)
        if capital > 0:
            max_risk_amount = capital * self.max_risk_per_trade
            risk_info.append(f"Capital: {capital}, Risque maximum autorisé: {max_risk_amount} ({self.max_risk_per_trade*100}%)")
        
        return "\n".join(risk_info) if risk_info else "Évaluation des risques non disponible"
    
    def _parse_decision(self, decision_text: str) -> Dict[str, Any]:
        """
        Parse le texte de décision du LLM en structure exploitable.
        
        Args:
            decision_text: Texte brut de la décision
            
        Returns:
            Dict: Décision structurée
        """
        decision = {
            "action": "attendre",  # Valeur par défaut
            "entry_price": None,
            "stop_loss": None,
            "take_profit": None,
            "position_size": None,
            "justification": "",
            "raw_decision": decision_text
        }
        
        # Recherche de l'action (acheter, vendre, attendre)
        if "acheter" in decision_text.lower() or "achat" in decision_text.lower() or "long" in decision_text.lower():
            decision["action"] = "acheter"
        elif "vendre" in decision_text.lower() or "vente" in decision_text.lower() or "short" in decision_text.lower():
            decision["action"] = "vendre"
        
        # Recherche des niveaux de prix
        lines = decision_text.split("\n")
        for line in lines:
            line = line.lower()
            
            # Point d'entrée
            if "entrée" in line or "entry" in line:
                numbers = self._extract_numbers(line)
                if numbers:
                    decision["entry_price"] = numbers[0]
            
            # Stop-loss
            if "stop" in line or "sl" in line:
                numbers = self._extract_numbers(line)
                if numbers:
                    decision["stop_loss"] = numbers[0]
            
            # Take-profit / objectif
            if "profit" in line or "objectif" in line or "target" in line or "tp" in line:
                numbers = self._extract_numbers(line)
                if numbers:
                    decision["take_profit"] = numbers[0]
            
            # Taille de position
            if "position" in line or "taille" in line or "size" in line or "%" in line:
                numbers = self._extract_numbers(line)
                if numbers:
                    for num in numbers:
                        # Si le nombre est entre 0 et 100, et qu'il y a un % dans la ligne, c'est probablement un pourcentage
                        if 0 <= num <= 100 and "%" in line:
                            decision["position_size"] = num / 100  # Conversion en décimal
                            break
                        # Si le nombre est entre 0 et 1, c'est probablement déjà un décimal
                        elif 0 <= num <= 1:
                            decision["position_size"] = num
                            break
        
        # Extraction de la justification (derniers paragraphes généralement)
        paragraphs = decision_text.split("\n\n")
        if paragraphs:
            # On prend le dernier paragraphe non vide comme justification
            for p in reversed(paragraphs):
                if p.strip():
                    decision["justification"] = p.strip()
                    break
        
        return decision
    
    def _extract_numbers(self, text: str) -> List[float]:
        """
        Extrait les nombres d'un texte.
        
        Args:
            text: Texte à analyser
            
        Returns:
            List[float]: Liste des nombres trouvés
        """
        import re
        # Recherche de nombres avec ou sans décimales, avec point ou virgule comme séparateur
        pattern = r"(\d+[.,]?\d*)"
        matches = re.findall(pattern, text)
        
        numbers = []
        for match in matches:
            # Remplacement de la virgule par un point pour la conversion
            match = match.replace(",", ".")
            try:
                numbers.append(float(match))
            except ValueError:
                pass
        
        return numbers
    
    def _validate_decision(self, 
                          decision: Dict[str, Any], 
                          context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide et ajuste la décision selon les règles de gestion des risques.
        
        Args:
            decision: Décision structurée à valider
            context: Contexte incluant le capital, etc.
            
        Returns:
            Dict: Décision validée et potentiellement ajustée
        """
        validated = decision.copy()
        validation_notes = []
        
        # Si l'action est d'attendre, pas besoin de validation supplémentaire
        if decision["action"] == "attendre":
            validated["validation_status"] = "accepted"
            validated["validation_notes"] = ["Décision d'attendre acceptée sans modification"]
            return validated
        
        # Vérification des prix d'entrée et de stop-loss
        if decision["entry_price"] is None:
            validation_notes.append("⚠️ Point d'entrée non spécifié")
            validated["validation_status"] = "warning"
        
        if decision["stop_loss"] is None:
            validation_notes.append("⚠️ Stop-loss non spécifié")
            validated["validation_status"] = "warning"
        
        # Calcul du ratio risque/récompense si possible
        if all([decision["entry_price"], decision["stop_loss"], decision["take_profit"]]):
            entry = decision["entry_price"]
            stop = decision["stop_loss"]
            target = decision["take_profit"]
            
            # Calcul du ratio selon que c'est un achat ou une vente
            if decision["action"] == "acheter":
                risk = abs(entry - stop)
                reward = abs(target - entry)
            else:  # vendre
                risk = abs(stop - entry)
                reward = abs(entry - target)
            
            if risk > 0:
                risk_reward_ratio = reward / risk
                validated["risk_reward_ratio"] = risk_reward_ratio
                
                if risk_reward_ratio < self.min_risk_reward:
                    validation_notes.append(f"⚠️ Ratio risque/récompense ({risk_reward_ratio:.2f}) inférieur au minimum requis ({self.min_risk_reward})")
                    validated["validation_status"] = "warning"
                else:
                    validation_notes.append(f"✅ Ratio risque/récompense acceptable: {risk_reward_ratio:.2f}")
        
        # Vérification de la taille de position
        capital = context.get("capital", 0)
        if capital > 0 and decision["position_size"] is not None:
            position_risk = decision["position_size"]
            
            if position_risk > self.max_risk_per_trade:
                validation_notes.append(f"⚠️ Risque par trade ({position_risk*100}%) supérieur au maximum autorisé ({self.max_risk_per_trade*100}%)")
                validated["position_size"] = self.max_risk_per_trade
                validation_notes.append(f"✅ Taille de position ajustée à {self.max_risk_per_trade*100}%")
                validated["validation_status"] = "adjusted"
            else:
                validation_notes.append(f"✅ Taille de position acceptable: {position_risk*100}%")
        
        # Statut final de validation si non défini précédemment
        if "validation_status" not in validated:
            validated["validation_status"] = "accepted"
        
        validated["validation_notes"] = validation_notes
        return validated
    
    def get_trading_options(self, 
                           symbol: str, 
                           analysis: Dict[str, Any],
                           risk_profile: str = "moderate") -> List[Dict[str, Any]]:
        """
        Génère plusieurs options de trading possibles pour un symbole donné.
        
        Args:
            symbol: Symbole de l'actif
            analysis: Analyse du marché
            risk_profile: Profil de risque (conservative, moderate, aggressive)
            
        Returns:
            List[Dict]: Liste d'options de trading avec leurs caractéristiques
        """
        # Cette méthode sera implémentée ultérieurement
        logger.warning("Méthode get_trading_options pas encore implémentée")
        return [{"status": "not_implemented"}]
