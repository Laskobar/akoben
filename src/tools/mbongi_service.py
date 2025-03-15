#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# mbongi_service.py - Service automatique pour Mbongi

import os
import sys
import time
import logging
import signal
import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='/home/lasko/akoben-clean/logs/mbongi_service.log',
    filemode='a'
)

# Ajout du chemin du projet
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import de Mbongi
try:
    from src.agents.documentation.mbongi import Mbongi
except ImportError:
    logging.error("Impossible d'importer Mbongi")
    sys.exit(1)

# Variables globales
mbongi = None
is_running = True

def initialize_mbongi():
    """Initialise Mbongi avec configuration"""
    global mbongi
    
    try:
        # Configuration
        config = {
            "knowledge_base": {
                "base_path": os.path.join(project_root, "docs", "knowledge_base")
            },
            "code_analyzer": {
                "excluded_dirs": ["venv", "__pycache__", ".git", ".vscode", "docs"]
            },
            "documentation_generator": {
                "templates_dir": os.path.join(project_root, "src", "agents", "documentation", "templates"),
                "output_dir": os.path.join(project_root, "docs")
            },
            "session_monitor": {
                "check_interval": 60,  # secondes
                "auto_detect": True    # Détection auto des sessions
            },
            "git_integrator": {
                "repo_path": project_root,
                "remote_name": "origin",
                "default_branch": "main",
                "auto_commit": True,
                "auto_push": True,
                "commit_interval": 1800,  # 30 minutes
                "message_template": "MBONGI: {message}",
                "tracked_extensions": [".py", ".md", ".txt", ".yaml", ".yml", ".json"],
                "username": os.environ.get("GIT_USERNAME", ""),
                "email": os.environ.get("GIT_EMAIL", "")
            }
        }
        
        # Initialiser Mbongi
        mbongi = Mbongi(project_root, config)
        logging.info("Mbongi initialisé avec succès")
        
        # Démarrage de la surveillance des sessions
        mbongi.session_monitor.start_monitoring()
        logging.info("Surveillance des sessions démarrée")
        
        return True
    except Exception as e:
        logging.error(f"Erreur lors de l'initialisation de Mbongi: {e}")
        return False

def sync_git():
    """Synchronise Git"""
    global mbongi
    
    try:
        # Vérification des changements
        untracked = mbongi.git_integrator.repo.untracked_files
        modified = [item.a_path for item in mbongi.git_integrator.repo.index.diff(None)]
        
        has_changes = bool(untracked or modified)
        
        if has_changes:
            logging.info(f"Détection de changements: {len(untracked)} non suivis, {len(modified)} modifiés")
            
            # Message de commit
            commit_message = f"MBONGI: Mise à jour automatique {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # Ajouter tous les fichiers modifiés
            mbongi.git_integrator.repo.git.add("--all")
            
            # Commit
            commit = mbongi.git_integrator.repo.index.commit(commit_message)
            logging.info(f"Commit effectué: {commit.hexsha[:8]} - {commit_message}")
            
            # Push
            try:
                mbongi.git_integrator.repo.remote("origin").push()
                logging.info("Push effectué vers origin")
            except Exception as e:
                logging.warning(f"Échec du push: {e}")
            
            return True
        else:
            logging.info("Aucun changement détecté")
            return False
    except Exception as e:
        logging.error(f"Erreur lors de la synchronisation Git: {e}")
        return False

def signal_handler(signum, frame):
    """Gère les signaux pour arrêter proprement le service"""
    global is_running
    
    logging.info(f"Signal {signum} reçu, arrêt du service")
    is_running = False

def main():
    """Fonction principale du service"""
    global mbongi, is_running
    
    # Créer le dossier de logs s'il n'existe pas
    os.makedirs(os.path.join(project_root, "logs"), exist_ok=True)
    
    # Initialiser Mbongi
    logging.info("Démarrage du service Mbongi")
    if not initialize_mbongi():
        logging.error("Échec de l'initialisation de Mbongi, arrêt du service")
        return
    
    # Configurer le gestionnaire de signaux
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Intervalle de vérification Git en secondes
    git_check_interval = 3600   # 1 heure
    last_git_check = time.time()
    
    # Boucle principale
    try:
        while is_running:
            # Vérifier Git périodiquement
            current_time = time.time()
            if current_time - last_git_check >= git_check_interval:
                sync_git()
                last_git_check = current_time
            
            # Attendre avant la prochaine itération
            time.sleep(60)  # Vérification chaque minute
    except Exception as e:
        logging.error(f"Erreur dans la boucle principale: {e}")
    finally:
        # Nettoyage avant de quitter (correction de l'indentation ici)
        if mbongi:
            try:
                # Arrêter la surveillance des sessions
                mbongi.session_monitor.stop_monitoring()
                logging.info("Surveillance des sessions arrêtée")
                
                # Synchronisation finale
                sync_git()
                logging.info("Service Mbongi arrêté proprement")
            except Exception as e:
                logging.error(f"Erreur lors de l'arrêt du service: {e}")

if __name__ == "__main__":
    main()