import requests
import time
import json

# Fonction simple pour appeler Ollama directement
def call_ollama(prompt, model="llama3"):
    print(f"Envoi de la requête à Ollama (modèle: {model})...")
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False}
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        print(f"Erreur lors de l'appel à Ollama: {e}")
        return "Je ne peux pas répondre pour le moment."

# Notre système multi-agents simplifié
def run_trading_analysis():
    # Agent 1: Recherche sur le trading algorithmique
    print("Phase 1: Agent de recherche sur le trading algorithmique")
    research_prompt = """
    Tu es un expert chercheur spécialisé dans le trading algorithmique.
    
    Ta tâche est de fournir un rapport détaillé sur les fondamentaux du trading algorithmique.
    
    Inclus:
    1. Définition et principes de base du trading algorithmique
    2. Types de stratégies algorithmiques courantes
    3. Composants clés d'un système de trading algorithmique
    
    Format ton rapport avec des titres clairs et des points détaillés.
    """
    
    research_result = call_ollama(research_prompt, model="llama3")
    print("\n" + "="*50 + "\nRésultat de la recherche:\n" + "="*50)
    print(research_result)
    
    # Agent 2: Analyse et optimisation des stratégies
    print("\nPhase 2: Agent d'analyse des stratégies")
    analysis_prompt = f"""
    Tu es un expert en stratégies de trading algorithmique.
    
    En te basant sur ces informations de recherche:
    
    {research_result}
    
    Ta tâche est d'approfondir et d'analyser:
    1. Les stratégies les plus efficaces pour le trading algorithmique du US30
    2. Les principaux risques et comment les gérer
    3. Les meilleures pratiques pour l'optimisation de stratégies
    
    Format ton analyse avec des titres clairs et des recommandations concrètes.
    """
    
    analysis_result = call_ollama(analysis_prompt, model="llama3")
    print("\n" + "="*50 + "\nRésultat de l'analyse:\n" + "="*50)
    print(analysis_result)
    
    return research_result, analysis_result

if __name__ == "__main__":
    print("Démarrage du système d'analyse de trading avec appel direct à Ollama...\n")
    start_time = time.time()
    research, analysis = run_trading_analysis()
    end_time = time.time()
    print(f"\nTemps d'exécution total: {end_time - start_time:.2f} secondes")
