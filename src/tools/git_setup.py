#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# git_setup.py - Configuration de l'intégration Git pour Mbongi

import os
import sys
import time
import logging
from datetime import datetime

# Configurer la journalisation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Ajout du chemin du projet aux chemins de recherche Python
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import de l'agent Mbongi
try:
    from src.agents.documentation.mbongi import Mbongi
except ImportError:
    print("Erreur: Impossible d'importer Mbongi. Vérifiez le chemin du projet.")
    sys.exit(1)

def setup_mbongi_git():
    """
    Configure Mbongi avec l'intégration Git de base.
    """
    # Chemin du projet
    project_path = project_root
    
    # Configuration pour Mbongi et GitIntegrator
    config = {
        "knowledge_base": {
            "base_path": os.path.join(project_path, "docs", "knowledge_base")
        },
        "code_analyzer": {
            "excluded_dirs": ["venv", "__pycache__", ".git", ".vscode", "docs"]
        },
        "documentation_generator": {
            "templates_dir": os.path.join(project_path, "src", "agents", "documentation", "templates"),
            "output_dir": os.path.join(project_path, "docs")
        },
        "session_monitor": {
            "check_interval": 60  # secondes
        },
        "git_integrator": {
            "repo_path": project_path,
            "remote_name": "origin",
            "default_branch": "main",
            "auto_commit": True,
            "auto_push": True,
            "commit_interval": 3600,  # 1 heure
            "message_template": "MBONGI: {message}",
            "tracked_extensions": [".py", ".md", ".txt", ".yaml", ".yml", ".json"],
            "username": os.environ.get("GIT_USERNAME", ""),
            "email": os.environ.get("GIT_EMAIL", ""),
            "github_token": os.environ.get("GITHUB_TOKEN", "")
        }
    }
    
    # Initialiser Mbongi
    try:
        mbongi = Mbongi(project_path, config)
        logging.info("Mbongi initialisé avec succès")
    except Exception as e:
        logging.error(f"Erreur lors de l'initialisation de Mbongi: {e}")
        return None
    
    # Configuration GitIntegrator basique
    try:
        # Vérifier si nous avons des informations Git
        git_config = config.get("git_integrator", {})
        username = git_config.get("username", "")
        email = git_config.get("email", "")
        
        # Définir la configuration Git si nécessaire
        if username and email:
            # Note: Nous devrions vérifier si la configuration est déjà définie,
            # mais comme get_repo_status n'est pas disponible, nous allons simplement
            # essayer de définir la configuration directement
            try:
                mbongi.git_integrator.repo.config_writer().set_value("user", "name", username)
                mbongi.git_integrator.repo.config_writer().set_value("user", "email", email)
                logging.info(f"Configuration Git définie pour {username} <{email}>")
            except Exception as e:
                logging.error(f"Échec de la configuration Git: {e}")
        
        logging.info("GitIntegrator configuré avec succès")
        return mbongi
    except Exception as e:
        logging.error(f"Erreur lors de la configuration de GitIntegrator: {e}")
        return mbongi

def run_git_sync_now(mbongi):
    """
    Exécute une synchronisation Git simplifiée.
    """
    if not mbongi or not mbongi.git_integrator:
        logging.error("Mbongi ou GitIntegrator non disponible")
        return False
    
    try:
        # Vérification simplifiée pour les changements
        # Comme detect_changes n'est pas disponible, nous allons utiliser git status directement
        try:
            # Vérifier s'il y a des fichiers modifiés/non suivis
            untracked = mbongi.git_integrator.repo.untracked_files
            modified = [item.a_path for item in mbongi.git_integrator.repo.index.diff(None)]
            
            has_changes = bool(untracked or modified)
            
            if has_changes:
                logging.info(f"Détection de changements: {len(untracked)} non suivis, {len(modified)} modifiés")
                
                # Créer un message de commit simple
                commit_message = f"MBONGI: Mise à jour automatique {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                
                # Ajouter tous les fichiers
                mbongi.git_integrator.repo.git.add("--all")
                
                # Commit
                commit = mbongi.git_integrator.repo.index.commit(commit_message)
                logging.info(f"Commit effectué: {commit.hexsha[:8]} - {commit_message}")
                
                # Push si configuré
                try:
                    mbongi.git_integrator.repo.remote("origin").push()
                    logging.info("Push effectué vers origin")
                    return True
                except Exception as e:
                    logging.warning(f"Échec du push: {e}")
            else:
                logging.info("Aucun changement détecté")
            
            return has_changes
        except Exception as e:
            logging.error(f"Erreur lors de la détection des changements: {e}")
            return False
    except Exception as e:
        logging.error(f"Erreur lors de la synchronisation Git: {e}")
        return False

def run_git_monitor(mbongi, interval=900):
    """
    Exécute une surveillance Git simplifiée.
    """
    print(f"Surveillance Git démarrée (intervalle: {interval} secondes)")
    print("Appuyez sur Ctrl+C pour arrêter.")
    
    try:
        while True:
            # Comme check_and_update n'est pas disponible, nous utilisons run_git_sync_now
            if run_git_sync_now(mbongi):
                print(f"Changements détectés et commités à {datetime.now().strftime('%H:%M:%S')}")
            else:
                print(f"Pas de changements détectés à {datetime.now().strftime('%H:%M:%S')}")
            
            # Attendre avant la prochaine vérification
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nSurveillance Git arrêtée par l'utilisateur")

def main():
    """
    Fonction principale.
    """
    print("\n=== Configuration de l'intégration Git pour Mbongi ===\n")
    
    # Configurer Mbongi avec Git
    mbongi = setup_mbongi_git()
    if not mbongi:
        print("Échec de la configuration. Consultez les logs pour plus de détails.")
        return
    
    # Menu principal
    while True:
        print("\n--- Menu Principal ---")
        print("1. Générer la documentation du projet")
        print("2. Exécuter une synchronisation Git immédiate")
        print("3. Démarrer une surveillance Git continue")
        print("4. Démarrer une session de développement")
        print("5. Terminer une session de développement")
        print("6. Ajouter une idée")
        print("7. Quitter")
        
        choice = input("\nVotre choix: ")
        
        if choice == "1":
            print("\n--- Génération de la documentation ---")
            # Remplacer generate_project_documentation par update_all_documentation
            mbongi.update_all_documentation()
            print("Documentation générée avec succès")
        
        elif choice == "2":
            print("\n--- Synchronisation Git ---")
            if run_git_sync_now(mbongi):
                print("Synchronisation Git réussie")
            else:
                print("Pas de synchronisation Git effectuée")
        
        elif choice == "3":
            print("\n--- Surveillance Git ---")
            interval = input("Intervalle de vérification en secondes (défaut: 900): ")
            interval = int(interval) if interval.isdigit() else 900
            run_git_monitor(mbongi, interval)
        
        elif choice == "4":
            print("\n--- Démarrage d'une session de développement ---")
            mbongi.start_session()
            print("Session de développement démarrée")
        
        elif choice == "5":
            print("\n--- Fin de la session de développement ---")
            mbongi.end_session()
            print("Session de développement terminée")
        
        elif choice == "6":
            print("\n--- Ajout d'une idée ---")
            title = input("Titre de l'idée: ")
            description = input("Description: ")
            components = input("Composants (séparés par des virgules): ").split(",")
            priority = input("Priorité (Low, Medium, High): ")
            tags = input("Tags (séparés par des virgules): ").split(",")
            
            idea = {
                "title": title,
                "description": description,
                "components": [c.strip() for c in components if c.strip()],
                "priority": priority.strip(),
                "tags": [t.strip() for t in tags if t.strip()]
            }
            
            mbongi.add_idea(idea)
            print("Idée ajoutée avec succès")
        
        elif choice == "7":
            print("\nAu revoir!")
            break
        
        else:
            print("\nOption invalide. Veuillez réessayer.")

if __name__ == "__main__":
    main()