"""
Module de mémoire pour Anansi, adapté du composant memory.py de Goose
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AnansiMemory")

class Memory:
    """
    Système de mémoire multi-niveaux pour Anansi (inspiré de Goose)
    
    Implémente trois types de mémoire:
    - Épisodique: stocke les expériences de trading spécifiques
    - Sémantique: stocke les connaissances générales sur les marchés
    - Procédurale: stocke les stratégies de trading efficaces
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialise le système de mémoire.
        
        Args:
            config: Configuration du système de mémoire
        """
        self.config = config or {}
        self.base_path = self.config.get("memory_path", "data/memory")
        os.makedirs(self.base_path, exist_ok=True)
        
        # Création des sous-dossiers pour chaque type de mémoire
        self.episodic_path = os.path.join(self.base_path, "episodic")
        self.semantic_path = os.path.join(self.base_path, "semantic")
        self.procedural_path = os.path.join(self.base_path, "procedural")
        
        os.makedirs(self.episodic_path, exist_ok=True)
        os.makedirs(self.semantic_path, exist_ok=True)
        os.makedirs(self.procedural_path, exist_ok=True)
        
        logger.info(f"Système de mémoire initialisé dans {self.base_path}")
    
    def store_episodic(self, experience: Dict[str, Any]) -> str:
        """
        Stocke une expérience de trading dans la mémoire épisodique.
        
        Args:
            experience: Dictionnaire contenant les détails de l'expérience
            
        Returns:
            str: Identifiant unique de l'expérience stockée
        """
        # Ajout de métadonnées
        timestamp = time.time()
        experience["timestamp"] = timestamp
        experience["date"] = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        
        # Génération d'un ID unique basé sur le timestamp
        experience_id = f"exp_{int(timestamp)}"
        
        # Sauvegarde dans un fichier JSON
        file_path = os.path.join(self.episodic_path, f"{experience_id}.json")
        with open(file_path, "w") as f:
            json.dump(experience, f, indent=2)
        
        logger.info(f"Expérience stockée dans la mémoire épisodique: {experience_id}")
        return experience_id
    
    def retrieve_episodic(self, query: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Récupère des expériences similaires de la mémoire épisodique.
        
        Args:
            query: Critères de recherche
            limit: Nombre maximum d'expériences à retourner
            
        Returns:
            List[Dict]: Liste des expériences correspondantes
        """
        # Implémentation simple pour l'instant - à améliorer avec une vraie recherche sémantique
        results = []
        
        # Parcours des fichiers dans le dossier de mémoire épisodique
        for filename in os.listdir(self.episodic_path):
            if not filename.endswith(".json"):
                continue
                
            file_path = os.path.join(self.episodic_path, filename)
            try:
                with open(file_path, "r") as f:
                    experience = json.load(f)
                
                # Vérification simple des correspondances
                matches = all(
                    key in experience and experience[key] == value
                    for key, value in query.items()
                    if key != "similarity_threshold"
                )
                
                if matches:
                    results.append(experience)
                    if len(results) >= limit:
                        break
            except Exception as e:
                logger.error(f"Erreur lors de la lecture de {filename}: {str(e)}")
        
        logger.info(f"Récupération de {len(results)} expériences de la mémoire épisodique")
        return results
    
    # Les autres méthodes seront implémentées progressivement
    
    def store(self, content: Dict[str, Any], content_type: str = "episodic") -> str:
        """
        Méthode générique pour stocker du contenu dans le type de mémoire spécifié.
        
        Args:
            content: Contenu à stocker
            content_type: Type de mémoire ("episodic", "semantic", "procedural")
            
        Returns:
            str: Identifiant du contenu stocké
        """
        if content_type == "episodic":
            return self.store_episodic(content)
        # Les autres types seront implémentés progressivement
        logger.warning(f"Type de mémoire non implémenté: {content_type}")
        return ""
    
    def retrieve(self, query: Dict[str, Any], context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Méthode générique pour récupérer du contenu de la mémoire.
        
        Args:
            query: Critères de recherche
            context: Contexte additionnel pour affiner la recherche
            
        Returns:
            List[Dict]: Résultats de la recherche
        """
        # Pour l'instant, recherche uniquement dans la mémoire épisodique
        # À améliorer avec une recherche dans tous les types de mémoire
        return self.retrieve_episodic(query)
