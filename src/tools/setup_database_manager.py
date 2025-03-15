import os
import json
import random
import glob
import pandas as pd
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
import shutil

class SetupDatabaseManager:
    """
    Gestionnaire de la base de données des setups de trading.
    Permet d'indexer, stocker et récupérer les paires image-texte des setups.
    """
    def __init__(self, data_root: str = "data/training", 
                 index_file: str = "data/index.json"):
        """
        Initialise le gestionnaire de base de données de setups.
        
        Args:
            data_root: Répertoire racine des données d'entraînement
            index_file: Fichier d'index pour stocker les métadonnées
        """
        self.data_root = data_root
        self.index_file = index_file
        
        # Créer les répertoires nécessaires s'ils n'existent pas
        os.makedirs(data_root, exist_ok=True)
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        
        # Charger ou créer l'index
        self.setup_index = self._load_or_create_index()
        
        print(f"SetupDatabaseManager initialisé avec {len(self.setup_index)} setups indexés")
    
    def _load_or_create_index(self) -> List[Dict[str, Any]]:
        """
        Charge l'index existant ou en crée un nouveau si nécessaire.
        
        Returns:
            Liste des métadonnées des setups
        """
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Erreur lors de la lecture du fichier d'index. Création d'un nouvel index.")
                return []
        else:
            # Construire un nouvel index
            return self._build_index()
    
    def _build_index(self) -> List[Dict[str, Any]]:
        """
        Construit un index complet de tous les setups dans data_root.
        
        Returns:
            Liste des métadonnées des setups
        """
        index = []
        
        # Parcourir tous les dossiers de setup
        setup_dirs = [d for d in os.listdir(self.data_root) 
                      if os.path.isdir(os.path.join(self.data_root, d))]
        
        for setup_type in setup_dirs:
            setup_path = os.path.join(self.data_root, setup_type)
            
            # Trouver toutes les images
            image_files = glob.glob(os.path.join(setup_path, "*.png")) + \
                         glob.glob(os.path.join(setup_path, "*.jpg"))
            
            for image_file in image_files:
                # Trouver le fichier texte correspondant
                base_name = os.path.splitext(image_file)[0]
                text_file = f"{base_name}.txt"
                
                if os.path.exists(text_file):
                    # Extraire les métadonnées de base
                    setup_id = os.path.basename(base_name)
                    creation_time = datetime.fromtimestamp(os.path.getctime(image_file))
                    
                    # Ajouter à l'index
                    setup_info = {
                        "id": setup_id,
                        "type": setup_type,
                        "image_path": image_file,
                        "text_path": text_file,
                        "created": creation_time.isoformat(),
                        "metadata": self._extract_basic_metadata(text_file)
                    }
                    
                    index.append(setup_info)
        
        # Sauvegarder l'index
        self._save_index(index)
        
        return index
    
    def _extract_basic_metadata(self, text_file: str) -> Dict[str, Any]:
        """
        Extrait les métadonnées de base du fichier texte.
        Cette méthode est flexible et sera affinée lorsque le format exact sera établi.
        
        Args:
            text_file: Chemin vers le fichier texte
            
        Returns:
            Dictionnaire des métadonnées extraites
        """
        metadata = {}
        
        if os.path.exists(text_file):
            try:
                with open(text_file, 'r') as f:
                    content = f.read()
                
                # Extraction simple des paires clé-valeur
                lines = content.split('\n')
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip().lower()] = value.strip()
                
                # Détection de l'action (achat/vente)
                content_lower = content.lower()
                if 'buy' in content_lower or 'achat' in content_lower or 'long' in content_lower:
                    metadata['action'] = 'buy'
                elif 'sell' in content_lower or 'vente' in content_lower or 'short' in content_lower:
                    metadata['action'] = 'sell'
                
            except Exception as e:
                print(f"Erreur lors de l'extraction des métadonnées de {text_file}: {e}")
        
        return metadata
    
    def _save_index(self, index: List[Dict[str, Any]]) -> None:
        """
        Sauvegarde l'index dans un fichier JSON.
        
        Args:
            index: Liste des métadonnées des setups
        """
        with open(self.index_file, 'w') as f:
            json.dump(index, f, indent=2)
    
    def refresh_index(self) -> None:
        """
        Rafraîchit l'index en parcourant à nouveau le répertoire des données.
        """
        self.setup_index = self._build_index()
        print(f"Index rafraîchi avec {len(self.setup_index)} setups.")
    
    def add_setup(self, image_path: str, text_content: str, setup_type: str) -> str:
        """
        Ajoute un nouveau setup à la base de données.
        
        Args:
            image_path: Chemin vers l'image source
            text_content: Contenu du fichier texte
            setup_type: Type de setup (utilisé pour le classement)
            
        Returns:
            ID du nouveau setup
        """
        # Créer un ID unique
        setup_id = f"{setup_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Créer le dossier de destination si nécessaire
        dest_dir = os.path.join(self.data_root, setup_type)
        os.makedirs(dest_dir, exist_ok=True)
        
        # Chemin de destination pour l'image
        _, ext = os.path.splitext(image_path)
        dest_image = os.path.join(dest_dir, f"{setup_id}{ext}")
        
        # Chemin pour le fichier texte
        dest_text = os.path.join(dest_dir, f"{setup_id}.txt")
        
        # Copier l'image
        shutil.copy(image_path, dest_image)
        
        # Créer le fichier texte
        with open(dest_text, 'w') as f:
            f.write(text_content)
        
        # Ajouter à l'index
        setup_info = {
            "id": setup_id,
            "type": setup_type,
            "image_path": dest_image,
            "text_path": dest_text,
            "created": datetime.now().isoformat(),
            "metadata": self._extract_basic_metadata(dest_text)
        }
        
        self.setup_index.append(setup_info)
        self._save_index(self.setup_index)
        
        return setup_id
    
    def get_setup_by_id(self, setup_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un setup par son ID.
        
        Args:
            setup_id: ID du setup à récupérer
            
        Returns:
            Informations du setup ou None si non trouvé
        """
        for setup in self.setup_index:
            if setup["id"] == setup_id:
                return setup
        return None
    
    def get_setups_by_type(self, setup_type: str) -> List[Dict[str, Any]]:
        """
        Récupère tous les setups d'un type donné.
        
        Args:
            setup_type: Type de setup à rechercher
            
        Returns:
            Liste des setups correspondants
        """
        return [setup for setup in self.setup_index if setup["type"] == setup_type]
    
    def get_setups_by_action(self, action: str) -> List[Dict[str, Any]]:
        """
        Récupère tous les setups d'une action donnée (buy/sell).
        
        Args:
            action: Action à rechercher (buy/sell)
            
        Returns:
            Liste des setups correspondants
        """
        return [setup for setup in self.setup_index 
                if setup.get("metadata", {}).get("action", "").lower() == action.lower()]
    
    def get_random_batch(self, batch_size: int = 10) -> List[Dict[str, Any]]:
        """
        Récupère un batch aléatoire de setups pour l'entraînement.
        
        Args:
            batch_size: Nombre de setups à récupérer
            
        Returns:
            Liste des setups sélectionnés
        """
        if not self.setup_index:
            return []
        
        actual_size = min(batch_size, len(self.setup_index))
        return random.sample(self.setup_index, actual_size)
    
    def get_all_setup_types(self) -> List[str]:
        """
        Récupère la liste de tous les types de setup disponibles.
        
        Returns:
            Liste des types de setup
        """
        return list(set(setup["type"] for setup in self.setup_index))
    
    def search_setups(self, query: str) -> List[Dict[str, Any]]:
        """
        Recherche des setups contenant le terme spécifié dans les métadonnées ou le texte.
        
        Args:
            query: Terme de recherche
            
        Returns:
            Liste des setups correspondants
        """
        query = query.lower()
        results = []
        
        for setup in self.setup_index:
            # Vérifier les métadonnées
            metadata_match = any(query in str(v).lower() 
                               for v in setup.get("metadata", {}).values())
            
            # Vérifier le contenu du fichier texte
            text_match = False
            if os.path.exists(setup["text_path"]):
                try:
                    with open(setup["text_path"], 'r') as f:
                        text_match = query in f.read().lower()
                except:
                    pass
            
            if metadata_match or text_match:
                results.append(setup)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Calcule des statistiques sur la base de données de setups.
        
        Returns:
            Dictionnaire des statistiques
        """
        if not self.setup_index:
            return {
                "total_setups": 0,
                "setup_types": {},
                "action_distribution": {"buy": 0, "sell": 0, "unknown": 0}
            }
        
        # Comptage par type
        setup_types = {}
        for setup in self.setup_index:
            setup_type = setup["type"]
            setup_types[setup_type] = setup_types.get(setup_type, 0) + 1
        
        # Distribution des actions
        action_distribution = {"buy": 0, "sell": 0, "unknown": 0}
        for setup in self.setup_index:
            action = setup.get("metadata", {}).get("action", "unknown")
            if action not in action_distribution:
                action = "unknown"
            action_distribution[action] += 1
        
        return {
            "total_setups": len(self.setup_index),
            "setup_types": setup_types,
            "action_distribution": action_distribution,
            "oldest_setup": min(setup["created"] for setup in self.setup_index),
            "newest_setup": max(setup["created"] for setup in self.setup_index)
        }
    
    def export_to_dataframe(self) -> pd.DataFrame:
        """
        Exporte les données indexées vers un DataFrame pandas.
        
        Returns:
            DataFrame contenant les informations des setups
        """
        records = []
        
        for setup in self.setup_index:
            record = {
                "id": setup["id"],
                "type": setup["type"],
                "created": setup["created"],
                "image_path": setup["image_path"],
                "text_path": setup["text_path"]
            }
            
            # Ajouter les métadonnées
            for key, value in setup.get("metadata", {}).items():
                record[f"metadata_{key}"] = value
            
            records.append(record)
        
        return pd.DataFrame(records)
    
    def delete_setup(self, setup_id: str) -> bool:
        """
        Supprime un setup de la base de données.
        
        Args:
            setup_id: ID du setup à supprimer
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        setup = self.get_setup_by_id(setup_id)
        if not setup:
            return False
        
        # Supprimer les fichiers
        try:
            if os.path.exists(setup["image_path"]):
                os.remove(setup["image_path"])
            if os.path.exists(setup["text_path"]):
                os.remove(setup["text_path"])
        except Exception as e:
            print(f"Erreur lors de la suppression des fichiers: {e}")
            return False
        
        # Mettre à jour l'index
        self.setup_index = [s for s in self.setup_index if s["id"] != setup_id]
        self._save_index(self.setup_index)
        
        return True