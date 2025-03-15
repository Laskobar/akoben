"""
Module de base de connaissances pour Mbongi.
Adapté du projet Eliza pour Akoben.
Gère le stockage et la récupération des informations sur le projet.
"""

import os
import json
import datetime
from typing import Dict, List, Any, Optional, Union


class KnowledgeBase:
    """
    Base de connaissances pour stocker et organiser la documentation du projet Akoben.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialise la base de connaissances.
        
        Args:
            config: Dictionnaire de configuration optionnel
        """
        self.config = config or {}
        self.base_path = self.config.get('base_path', 'docs/knowledge_base')
        self.categories = {
            'agents': os.path.join(self.base_path, 'agents'),
            'teams': os.path.join(self.base_path, 'teams'),
            'components': os.path.join(self.base_path, 'components'),
            'development': os.path.join(self.base_path, 'development'),
            'ideas': os.path.join(self.base_path, 'ideas'),
            'strategies': os.path.join(self.base_path, 'strategies'),
        }
        
        # Créer les dossiers s'ils n'existent pas
        self._ensure_directories()
        
    def _ensure_directories(self) -> None:
        """Crée les dossiers de la base de connaissances s'ils n'existent pas."""
        os.makedirs(self.base_path, exist_ok=True)
        for category_path in self.categories.values():
            os.makedirs(category_path, exist_ok=True)
    
    def store(self, category: str, name: str, content: Dict[str, Any]) -> str:
        """
        Stocke un document dans la base de connaissances.
        
        Args:
            category: Catégorie du document (agents, teams, etc.)
            name: Nom unique du document
            content: Contenu du document (dict)
            
        Returns:
            Chemin du fichier où le document a été stocké
        """
        if category not in self.categories:
            raise ValueError(f"Catégorie '{category}' non reconnue. Catégories valides: {list(self.categories.keys())}")
        
        # Ajouter un timestamp aux métadonnées
        if 'metadata' not in content:
            content['metadata'] = {}
        
        content['metadata']['last_updated'] = datetime.datetime.now().isoformat()
        
        # Déterminer le chemin du fichier
        file_path = os.path.join(self.categories[category], f"{name}.json")
        
        # Sauvegarder le document
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
            
        return file_path
    
    def retrieve(self, category: str, name: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un document de la base de connaissances.
        
        Args:
            category: Catégorie du document
            name: Nom du document
            
        Returns:
            Contenu du document ou None si non trouvé
        """
        if category not in self.categories:
            raise ValueError(f"Catégorie '{category}' non reconnue. Catégories valides: {list(self.categories.keys())}")
        
        file_path = os.path.join(self.categories[category], f"{name}.json")
        
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_documents(self, category: str) -> List[str]:
        """
        Liste tous les documents d'une catégorie.
        
        Args:
            category: Catégorie à lister
            
        Returns:
            Liste des noms de documents (sans extension)
        """
        if category not in self.categories:
            raise ValueError(f"Catégorie '{category}' non reconnue. Catégories valides: {list(self.categories.keys())}")
        
        category_path = self.categories[category]
        
        # Vérifier que le dossier existe
        if not os.path.exists(category_path):
            return []
        
        # Lister tous les fichiers .json et enlever l'extension
        return [
            os.path.splitext(f)[0] for f in os.listdir(category_path)
            if f.endswith('.json')
        ]
    
    def search(self, query: str, categories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Recherche simple dans la base de connaissances.
        
        Args:
            query: Terme de recherche
            categories: Liste des catégories où chercher (toutes si None)
            
        Returns:
            Liste des documents correspondants avec métadonnées
        """
        query = query.lower()
        results = []
        
        # Déterminer les catégories à parcourir
        cats_to_search = categories or list(self.categories.keys())
        
        # Vérifier que toutes les catégories sont valides
        for cat in cats_to_search:
            if cat not in self.categories:
                raise ValueError(f"Catégorie '{cat}' non reconnue. Catégories valides: {list(self.categories.keys())}")
        
        # Parcourir chaque catégorie
        for category in cats_to_search:
            for doc_name in self.list_documents(category):
                doc = self.retrieve(category, doc_name)
                
                # Recherche simple dans le contenu sérialisé
                doc_str = json.dumps(doc).lower()
                if query in doc_str:
                    results.append({
                        'category': category,
                        'name': doc_name,
                        'document': doc
                    })
        
        return results
    
    def delete(self, category: str, name: str) -> bool:
        """
        Supprime un document de la base de connaissances.
        
        Args:
            category: Catégorie du document
            name: Nom du document
            
        Returns:
            True si supprimé, False sinon
        """
        if category not in self.categories:
            raise ValueError(f"Catégorie '{category}' non reconnue. Catégories valides: {list(self.categories.keys())}")
        
        file_path = os.path.join(self.categories[category], f"{name}.json")
        
        if not os.path.exists(file_path):
            return False
        
        os.remove(file_path)
        return True
    
    def update(self, category: str, name: str, content: Dict[str, Any]) -> str:
        """
        Met à jour un document existant ou le crée s'il n'existe pas.
        
        Args:
            category: Catégorie du document
            name: Nom du document
            content: Nouveau contenu
            
        Returns:
            Chemin du fichier mis à jour
        """
        existing = self.retrieve(category, name)
        
        if existing:
            # Mettre à jour le contenu existant tout en préservant les métadonnées
            if 'metadata' not in content:
                content['metadata'] = existing.get('metadata', {})
            
            # Mettre à jour le timestamp
            content['metadata']['last_updated'] = datetime.datetime.now().isoformat()
            content['metadata']['previous_update'] = existing.get('metadata', {}).get('last_updated')
            
        return self.store(category, name, content)


# Test simple du module si exécuté directement
if __name__ == "__main__":
    kb = KnowledgeBase()
    
    # Tester le stockage
    test_doc = {
        "title": "Test Document",
        "content": "This is a test document for the knowledge base.",
        "metadata": {
            "author": "Mbongi"
        }
    }
    
    kb.store("agents", "test_agent", test_doc)
    
    # Tester la récupération
    retrieved = kb.retrieve("agents", "test_agent")
    print("Document récupéré:", retrieved)
    
    # Tester la liste
    docs = kb.list_documents("agents")
    print("Documents dans 'agents':", docs)
    
    # Tester la recherche
    results = kb.search("test")
    print(f"Résultats de recherche ('{len(results)}'):", [r['name'] for r in results])
    
    # Tester la suppression
    kb.delete("agents", "test_agent")
    print("Document supprimé.")