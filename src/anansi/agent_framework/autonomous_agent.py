"""
Agent Autonome de Base pour Akoben
"""

import os
import time
import json
import logging
from abc import ABC, abstractmethod

class AutonomousAgent(ABC):
    """
    Agent autonome de base pour le système Akoben.
    Tous les agents spécialisés héritent de cette classe.
    
    Implémente le cycle percevoir-penser-agir et gère la
    communication avec Anansi.
    """
    
    def __init__(self, name, config=None, anansi_core=None):
        self.name = name
        self.config = config or {}
        self.anansi_core = anansi_core
        self.state = {}
        self.perception_history = []
        self.action_history = []
        
        # Configuration du logger
        self.logger = self._setup_logger()
        
        self.logger.info(f"Agent {self.name} initialisé")
    
    def _setup_logger(self):
        """Configure le logger pour cet agent."""
        logger = logging.getLogger(f"akoben.agent.{self.name}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    @abstractmethod
    def perceive(self, inputs):
        """
        Perçoit des informations depuis l'environnement.
        Cette méthode doit être implémentée par chaque agent spécifique.
        
        Args:
            inputs: Données d'entrée à percevoir (format variable selon l'agent)
            
        Returns:
            Perceptions traitées (format variable selon l'agent)
        """
        pass
    
    @abstractmethod
    def think(self, perceptions, context=None):
        """
        Analyse les perceptions et détermine les actions à entreprendre.
        Cette méthode doit être implémentée par chaque agent spécifique.
        
        Args:
            perceptions: Perceptions issues de la méthode perceive()
            context: Contexte supplémentaire (optionnel)
            
        Returns:
            Décisions prises suite à l'analyse
        """
        pass
    
    @abstractmethod
    def act(self, decisions):
        """
        Exécute les actions déterminées par le processus de réflexion.
        Cette méthode doit être implémentée par chaque agent spécifique.
        
        Args:
            decisions: Décisions issues de la méthode think()
            
        Returns:
            Résultats des actions entreprises
        """
        pass
    
    def cognitive_cycle(self, inputs, context=None):
        """
        Exécute un cycle cognitif complet: percevoir → penser → agir.
        
        Args:
            inputs: Données d'entrée pour le cycle
            context: Contexte supplémentaire (optionnel)
            
        Returns:
            Résultats du cycle cognitif complet
        """
        # Étape 1: Perception
        self.logger.debug(f"Début du cycle cognitif - Étape de perception")
        perceptions = self.perceive(inputs)
        self.perception_history.append({
            "timestamp": time.time(),
            "inputs": inputs,
            "perceptions": perceptions
        })
        
        # Étape 2: Réflexion
        self.logger.debug(f"Étape de réflexion")
        decisions = self.think(perceptions, context)
        
        # Étape 3: Action
        self.logger.debug(f"Étape d'action")
        results = self.act(decisions)
        self.action_history.append({
            "timestamp": time.time(),
            "decisions": decisions,
            "results": results
        })
        
        self.logger.debug(f"Fin du cycle cognitif")
        # Retourne les résultats
        return results
    
    def save_state(self, file_path=None):
        """
        Sauvegarde l'état actuel de l'agent.
        
        Args:
            file_path: Chemin du fichier où sauvegarder l'état (optionnel)
            
        Returns:
            Chemin du fichier où l'état a été sauvegardé
        """
        if not file_path:
            file_path = f"data/agent_states/{self.name}_state.json"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        state_data = {
            "name": self.name,
            "timestamp": time.time(),
            "state": self.state,
            # Ne pas sauvegarder les historiques complets, trop volumineux
            "perception_count": len(self.perception_history),
            "action_count": len(self.action_history)
        }
        
        with open(file_path, "w") as f:
            json.dump(state_data, f, indent=2)
        
        self.logger.info(f"État sauvegardé dans {file_path}")
        return file_path
    
    def load_state(self, file_path=None):
        """
        Charge l'état de l'agent depuis un fichier.
        
        Args:
            file_path: Chemin du fichier d'état (optionnel)
            
        Returns:
            bool: True si le chargement a réussi, False sinon
        """
        if not file_path:
            file_path = f"data/agent_states/{self.name}_state.json"
        
        if not os.path.exists(file_path):
            self.logger.warning(f"Fichier d'état {file_path} non trouvé")
            return False
        
        with open(file_path, "r") as f:
            state_data = json.load(f)
        
        self.state = state_data.get("state", {})
        self.logger.info(f"État chargé depuis {file_path}")
        return True
    
    def communicate(self, message, target_agent=None):
        """
        Communique avec un autre agent ou avec Anansi.
        
        Args:
            message: Message à transmettre
            target_agent: Nom de l'agent cible (None pour Anansi)
            
        Returns:
            Réponse obtenue
        """
        if not self.anansi_core:
            self.logger.error("Impossible de communiquer: anansi_core non défini")
            return None
            
        if target_agent:
            # Communication avec un agent spécifique
            if hasattr(self.anansi_core, 'agent_manager') and target_agent in self.anansi_core.agent_manager.agents:
                # Implémentation à adapter selon le mécanisme de communication inter-agents choisi
                self.logger.info(f"Communication avec l'agent {target_agent}")
                return {"status": "message_delivered", "target": target_agent}
            else:
                self.logger.warning(f"Agent cible {target_agent} non trouvé")
                return None
        else:
            # Communication avec Anansi (cerveau central)
            self.logger.info("Communication avec Anansi")
            return {"status": "message_delivered", "target": "anansi"}
    
    def get_full_name(self):
        """
        Renvoie le nom complet de l'agent (inclut le type).
        
        Returns:
            str: Nom complet de l'agent
        """
        return f"{self.__class__.__name__}:{self.name}"