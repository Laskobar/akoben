"""
Connecteur pour le modèle Qwen, facilitant l'interaction avec Ollama
"""

import json
import requests
import logging
from typing import Dict, Any, Optional, List

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("QwenConnector")

class QwenConnector:
    """
    Classe pour interagir avec le modèle Qwen via Ollama
    """
    
    def __init__(self, base_url: str = "http://localhost:11434/api", model_name: str = "qwen:14b"):
        """
        Initialise le connecteur Qwen.
        
        Args:
            base_url: URL de base pour l'API Ollama
            model_name: Nom du modèle Qwen à utiliser
        """
        self.base_url = base_url
        self.model_name = model_name
        self.generate_endpoint = f"{self.base_url}/generate"
        logger.info(f"QwenConnector initialisé avec le modèle {model_name}")
        
    def check_availability(self) -> bool:
        """
        Vérifie si le modèle est disponible via Ollama.
        
        Returns:
            bool: True si le modèle est disponible, False sinon
        """
        try:
            response = requests.get(f"{self.base_url}/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                available_models = [model.get("name") for model in models]
                is_available = self.model_name in available_models
                
                if is_available:
                    logger.info(f"Modèle {self.model_name} disponible")
                else:
                    logger.warning(f"Modèle {self.model_name} non trouvé dans les modèles disponibles: {available_models}")
                
                return is_available
            else:
                logger.error(f"Erreur lors de la vérification des modèles: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Exception lors de la vérification de disponibilité: {str(e)}")
            return False
    
    def generate(self, 
                prompt: str, 
                system_prompt: Optional[str] = None,
                temperature: float = 0.7, 
                max_tokens: int = 2000,
                stop_sequences: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Génère une réponse à partir du modèle Qwen.
        
        Args:
            prompt: Texte d'entrée pour le modèle
            system_prompt: Instructions système pour le modèle (optionnel)
            temperature: Température pour la génération (contrôle la créativité)
            max_tokens: Nombre maximum de tokens à générer
            stop_sequences: Liste de séquences qui arrêtent la génération

        Returns:
            Dict: Réponse du modèle avec texte généré et métadonnées
        """
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": temperature,
            "num_predict": max_tokens,
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        if stop_sequences:
            payload["stop"] = stop_sequences
            
        try:
            logger.info(f"Envoi de requête à Qwen (taille prompt: {len(prompt)} caractères)")
            response = requests.post(self.generate_endpoint, headers=headers, data=json.dumps(payload))
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("response", "")
                logger.info(f"Réponse reçue de Qwen (taille: {len(generated_text)} caractères)")
                
                # Formatage de la réponse pour standardisation avec d'autres connecteurs
                formatted_response = {
                    "text": generated_text,
                    "metadata": {
                        "prompt_eval_count": result.get("prompt_eval_count", 0),
                        "eval_count": result.get("eval_count", 0),
                        "eval_duration": result.get("eval_duration", 0)
                    }
                }
                return formatted_response
            else:
                error_msg = f"Erreur lors de la génération: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {"error": error_msg, "text": ""}
        except Exception as e:
            error_msg = f"Exception lors de la génération: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "text": ""}

    def get_completion(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Version simplifiée de generate qui renvoie uniquement le texte généré.
        
        Args:
            prompt: Texte d'entrée pour le modèle
            system_prompt: Instructions système pour le modèle (optionnel)
            
        Returns:
            str: Texte généré par le modèle
        """
        response = self.generate(prompt, system_prompt)
        return response.get("text", "")

# Exemple d'utilisation
if __name__ == "__main__":
    # Test simple du connecteur
    qwen = QwenConnector()
    if qwen.check_availability():
        response = qwen.get_completion("Qui est Chaka dans la tradition africaine?")
        print(f"Réponse: {response}")
    else:
        print("Modèle Qwen non disponible. Vérifiez qu'Ollama est en cours d'exécution et que le modèle est installé.")