#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import git
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

class GitIntegrator:
    """
    Composant de Mbongi pour l'intégration avec Git.
    Permet de suivre les modifications, générer des commit messages intelligents,
    et synchroniser avec le dépôt distant.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le GitIntegrator avec une configuration donnée.
        
        Args:
            config: Dictionnaire de configuration contenant:
                - repo_path: Chemin vers le dépôt Git
                - remote_name: Nom du remote (default: "origin")
                - default_branch: Branche par défaut (default: "main")
                - auto_commit: Activer les commits automatiques (default: False)
                - auto_push: Activer les push automatiques (default: True)
                - commit_interval: Intervalle entre les commits en secondes (default: 3600)
                - message_template: Template pour les messages de commit (default: "MBONGI: {message}")
                - tracked_extensions: Extensions des fichiers à suivre (default: [".py", ".md"])
                - username: Nom d'utilisateur Git (optionnel)
                - email: Email Git (optionnel)
                - github_token: Token GitHub pour l'authentification (optionnel)
        """
        self.config = {
            "remote_name": "origin",
            "default_branch": "main",
            "auto_commit": False,
            "auto_push": True,
            "commit_interval": 3600,  # 1 heure
            "message_template": "MBONGI: {message}",
            "tracked_extensions": [".py", ".md", ".txt", ".yaml", ".yml", ".json"],
        }
        self.config.update(config)
        
        # Validation des chemins
        self.repo_path = self.config.get("repo_path")
        if not self.repo_path or not os.path.exists(self.repo_path):
            raise ValueError(f"Chemin du dépôt invalide: {self.repo_path}")
        
        # Initialisation du repo Git
        try:
            self.repo = git.Repo(self.repo_path)
            logging.info(f"Dépôt Git initialisé à {self.repo_path}")
        except git.InvalidGitRepositoryError:
            logging.warning(f"{self.repo_path} n'est pas un dépôt Git valide. Initialisation d'un nouveau dépôt.")
            self.repo = git.Repo.init(self.repo_path)
            logging.info(f"Nouveau dépôt Git initialisé à {self.repo_path}")
        
        # État interne
        self.last_commit_time = time.time()
        self.auto_tracking_enabled = False
        self.commit_rules = {}
        self.file_cache = {}
        self.init_file_cache()
        
        logging.info("GitIntegrator initialisé")
    
    def init_file_cache(self) -> None:
        """
        Initialise le cache des fichiers pour suivre les modifications.
        """
        self.file_cache = {}
        for root, _, files in os.walk(self.repo_path):
            # Ignorer les dossiers .git et autres dossiers exclus
            if ".git" in root or any(excluded in root for excluded in [
                "__pycache__", "venv", ".vscode", "node_modules"
            ]):
                continue
            
            for file in files:
                # Vérifier si l'extension est dans les extensions suivies
                ext = os.path.splitext(file)[1]
                if ext not in self.config["tracked_extensions"]:
                    continue
                
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.repo_path)
                
                try:
                    mtime = os.path.getmtime(file_path)
                    self.file_cache[rel_path] = {
                        "mtime": mtime,
                        "last_checked": time.time()
                    }
                except OSError:
                    # Ignorer les fichiers inaccessibles
                    continue
        
        logging.info(f"Cache de fichiers initialisé: {len(self.file_cache)} fichiers en suivi")
    
    def is_git_config_set(self) -> bool:
        """
        Vérifie si les informations de configuration Git (user.name et user.email) sont définies.
        
        Returns:
            bool: True si la configuration est complète, False sinon
        """
        try:
            with self.repo.config_reader() as config:
                username = config.get_value("user", "name", None)
                email = config.get_value("user", "email", None)
                return bool(username and email)
        except Exception as e:
            logging.error(f"Erreur lors de la vérification de la configuration Git: {e}")
            return False
    
    def set_git_config(self, username: str, email: str) -> bool:
        """
        Configure les informations user.name et user.email dans le dépôt Git.
        
        Args:
            username: Nom d'utilisateur Git
            email: Email Git
            
        Returns:
            bool: True si la configuration a réussi, False sinon
        """
        try:
            with self.repo.config_writer() as config:
                config.set_value("user", "name", username)
                config.set_value("user", "email", email)
            logging.info(f"Configuration Git définie: {username} <{email}>")
            return True
        except Exception as e:
            logging.error(f"Erreur lors de la configuration Git: {e}")
            return False
    
    # Correction de la méthode get_repo_status dans GitIntegrator



def get_repo_status(self) -> Dict[str, List[str]]:

    """

    Obtient l'état actuel du dépôt Git.

    

    Returns:

        Dict contenant les fichiers non suivis, modifiés et indexés

    """

    status = {

        "untracked": [],

        "modified": [],

        "staged": []

    }

    

    try:

        # Fichiers non suivis (correction)

        untracked_files = self.repo.untracked_files

        status["untracked"] = untracked_files if isinstance(untracked_files, list) else []

        

        # Fichiers modifiés

        diff = self.repo.index.diff(None)

        status["modified"] = [item.a_path for item in diff]

        

        # Fichiers indexés (staged)

        diff = self.repo.index.diff("HEAD")

        status["staged"] = [item.a_path for item in diff]

        

        return status

    except Exception as e:

        logging.error(f"Erreur lors de la récupération de l'état du dépôt: {e}")

        return status
    
    def enable_auto_tracking(self) -> None:
        """
        Active le suivi automatique des modifications.
        """
        self.auto_tracking_enabled = True
        logging.info("Suivi automatique des modifications Git activé")
    
    def disable_auto_tracking(self) -> None:
        """
        Désactive le suivi automatique des modifications.
        """
        self.auto_tracking_enabled = False
        logging.info("Suivi automatique des modifications Git désactivé")
    
    def set_commit_rules(self, rules: Dict[str, Dict[str, Any]]) -> None:
        """
        Définit les règles pour les commits automatiques.
        
        Args:
            rules: Dictionnaire de règles de commit, où chaque règle contient:
                - pattern: Liste de patterns de fichiers (glob ou regex)
                - message: Message de commit à utiliser quand ces fichiers sont modifiés
        """
        self.commit_rules = rules
        logging.info(f"Règles de commit configurées: {len(rules)} règles définies")
    
    def detect_changes(self) -> List[Dict[str, Any]]:
        """
        Détecte les changements dans le dépôt par rapport au dernier check.
        
        Returns:
            Liste des fichiers modifiés avec leurs métadonnées
        """
        changes = []
        
        for root, _, files in os.walk(self.repo_path):
            # Ignorer les dossiers .git et autres dossiers exclus
            if ".git" in root or any(excluded in root for excluded in [
                "__pycache__", "venv", ".vscode", "node_modules"
            ]):
                continue
            
            for file in files:
                # Vérifier si l'extension est dans les extensions suivies
                ext = os.path.splitext(file)[1]
                if ext not in self.config["tracked_extensions"]:
                    continue
                
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.repo_path)
                
                try:
                    mtime = os.path.getmtime(file_path)
                    
                    # Vérifier si le fichier est nouveau ou modifié
                    if rel_path not in self.file_cache:
                        changes.append({
                            "path": rel_path,
                            "type": "new",
                            "mtime": mtime
                        })
                        self.file_cache[rel_path] = {
                            "mtime": mtime,
                            "last_checked": time.time()
                        }
                    elif mtime > self.file_cache[rel_path]["mtime"]:
                        changes.append({
                            "path": rel_path,
                            "type": "modified",
                            "mtime": mtime,
                            "previous_mtime": self.file_cache[rel_path]["mtime"]
                        })
                        self.file_cache[rel_path]["mtime"] = mtime
                        self.file_cache[rel_path]["last_checked"] = time.time()
                except OSError:
                    # Ignorer les fichiers inaccessibles
                    continue
        
        # Détecter les fichiers supprimés
        for rel_path in list(self.file_cache.keys()):
            file_path = os.path.join(self.repo_path, rel_path)
            if not os.path.exists(file_path):
                changes.append({
                    "path": rel_path,
                    "type": "deleted",
                    "previous_mtime": self.file_cache[rel_path]["mtime"]
                })
                del self.file_cache[rel_path]
        
        if changes:
            logging.info(f"Détection de {len(changes)} changements: {[c['path'] for c in changes]}")
        
        return changes
    
    def generate_commit_message(self, changes: List[Dict[str, Any]]) -> str:
        """
        Génère un message de commit intelligent basé sur les fichiers modifiés
        et les règles de commit définies.
        
        Args:
            changes: Liste des fichiers modifiés avec leurs métadonnées
        
        Returns:
            Message de commit généré
        """
        # Classement des changements par type
        changes_by_type = {
            "new": [],
            "modified": [],
            "deleted": []
        }
        
        for change in changes:
            changes_by_type[change["type"]].append(change["path"])
        
        # Classement des changements par règle
        matched_rules = {}
        
        for change in changes:
            for rule_name, rule in self.commit_rules.items():
                patterns = rule["pattern"]
                if not isinstance(patterns, list):
                    patterns = [patterns]
                
                for pattern in patterns:
                    # Si le pattern est une extension
                    if pattern.startswith("."):
                        if change["path"].endswith(pattern):
                            matched_rules[rule_name] = matched_rules.get(rule_name, []) + [change["path"]]
                            break
                    # Si le pattern est un dossier
                    elif pattern.endswith("/"):
                        if change["path"].startswith(pattern):
                            matched_rules[rule_name] = matched_rules.get(rule_name, []) + [change["path"]]
                            break
                    # Si le pattern est un glob
                    elif "*" in pattern:
                        import fnmatch
                        if fnmatch.fnmatch(change["path"], pattern):
                            matched_rules[rule_name] = matched_rules.get(rule_name, []) + [change["path"]]
                            break
                    # Sinon, on considère que c'est un match exact
                    elif change["path"] == pattern:
                        matched_rules[rule_name] = matched_rules.get(rule_name, []) + [change["path"]]
                        break
        
        # Génération du message de commit
        if matched_rules:
            # Si des règles ont été matchées, on utilise leurs messages
            messages = []
            for rule_name, files in matched_rules.items():
                rule = self.commit_rules[rule_name]
                rule_message = rule["message"]
                
                # Si on a plusieurs fichiers pour une même règle, on peut les lister
                if len(files) > 1:
                    affected_files = ", ".join(os.path.basename(f) for f in files[:3])
                    if len(files) > 3:
                        affected_files += f" et {len(files) - 3} autres"
                    rule_message += f" ({affected_files})"
                    
                messages.append(rule_message)
            
            commit_message = "; ".join(messages)
        else:
            # Si aucune règle n'a été matchée, on génère un message générique
            parts = []
            
            if changes_by_type["new"]:
                files = changes_by_type["new"]
                msg = f"Ajout de {len(files)} fichier{'s' if len(files) > 1 else ''}"
                if len(files) <= 3:
                    msg += f": {', '.join(os.path.basename(f) for f in files)}"
                parts.append(msg)
            
            if changes_by_type["modified"]:
                files = changes_by_type["modified"]
                msg = f"Mise à jour de {len(files)} fichier{'s' if len(files) > 1 else ''}"
                if len(files) <= 3:
                    msg += f": {', '.join(os.path.basename(f) for f in files)}"
                parts.append(msg)
            
            if changes_by_type["deleted"]:
                files = changes_by_type["deleted"]
                msg = f"Suppression de {len(files)} fichier{'s' if len(files) > 1 else ''}"
                if len(files) <= 3:
                    msg += f": {', '.join(os.path.basename(f) for f in files)}"
                parts.append(msg)
            
            commit_message = "; ".join(parts)
        
        # Utilisation du template de message
        commit_message = self.config["message_template"].format(message=commit_message)
        
        return commit_message
    
    def stage_changes(self, paths: Optional[List[str]] = None) -> bool:
        """
        Ajoute les fichiers modifiés à l'index Git (git add).
        
        Args:
            paths: Liste des chemins à ajouter (None pour tous les fichiers)
            
        Returns:
            bool: True si l'ajout a réussi, False sinon
        """
        try:
            if paths:
                # Ajouter des chemins spécifiques
                for path in paths:
                    full_path = os.path.join(self.repo_path, path)
                    # Si le fichier existe, on l'ajoute
                    if os.path.exists(full_path):
                        self.repo.git.add(path)
                    # Sinon, c'est qu'il a été supprimé, donc on le retire
                    else:
                        self.repo.git.rm(path)
            else:
                # Ajouter tous les fichiers modifiés
                self.repo.git.add("--all")
            
            logging.info("Fichiers ajoutés à l'index Git")
            return True
        except Exception as e:
            logging.error(f"Erreur lors de l'ajout des fichiers à l'index: {e}")
            return False
    
    def commit_changes(self, message: str, paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Effectue un commit des changements.
        
        Args:
            message: Message de commit
            paths: Liste des chemins à inclure dans le commit (None pour tous les fichiers indexés)
            
        Returns:
            Dict contenant le résultat du commit (succès, message, etc.)
        """
        result = {
            "success": False,
            "message": "",
            "commit_id": None,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Vérifier s'il y a des changements à committer
            status = self.get_repo_status()
            if not status["untracked"] and not status["modified"] and not status["staged"]:
                result["message"] = "Aucun changement à committer"
                return result
            
            # Ajouter les fichiers à l'index
            self.stage_changes(paths)
            
            # Vérifier à nouveau après staging
            staged_status = self.get_repo_status()
            if not staged_status["staged"]:
                result["message"] = "Aucun changement indexé pour le commit"
                return result
            
            # Effectuer le commit
            commit = self.repo.git.commit("-m", message)
            commit_id = self.repo.head.commit.hexsha
            
            result["success"] = True
            result["message"] = f"Commit effectué avec succès: {commit_id[:8]}"
            result["commit_id"] = commit_id
            self.last_commit_time = time.time()
            
            logging.info(f"Commit effectué: {commit_id[:8]} - {message}")
            return result
        except Exception as e:
            logging.error(f"Erreur lors du commit: {e}")
            result["message"] = f"Erreur lors du commit: {str(e)}"
            return result
    
    def push_changes(self, remote_name: Optional[str] = None, branch: Optional[str] = None) -> Dict[str, Any]:
        """
        Pousse les changements vers le dépôt distant (git push).
        
        Args:
            remote_name: Nom du dépôt distant (défaut: config["remote_name"])
            branch: Nom de la branche (défaut: config["default_branch"])
            
        Returns:
            Dict contenant le résultat du push (succès, message, etc.)
        """
        result = {
            "success": False,
            "message": "",
            "timestamp": datetime.now().isoformat()
        }
        
        # Utiliser les valeurs par défaut si non spécifiées
        remote_name = remote_name or self.config["remote_name"]
        branch = branch or self.config["default_branch"]
        
        try:
            # Vérifier si le remote existe
            remotes = [r.name for r in self.repo.remotes]
            if remote_name not in remotes:
                result["message"] = f"Le remote '{remote_name}' n'existe pas"
                return result
            
            # Utiliser un token GitHub si disponible
            if self.config.get("github_token"):
                # Construire l'URL avec le token intégré
                token = self.config["github_token"]
                remote = self.repo.remote(remote_name)
                github_url = remote.url
                
                # Remplacer l'URL par une URL avec le token
                if github_url.startswith("https://"):
                    auth_url = github_url.replace("https://", f"https://{token}@")
                    self.repo.git.remote("set-url", remote_name, auth_url)
                    
                    # Push avec la nouvelle URL
                    push_result = self.repo.git.push(remote_name, branch)
                    
                    # Restaurer l'URL d'origine (pour des raisons de sécurité)
                    self.repo.git.remote("set-url", remote_name, github_url)
                else:
                    # Si l'URL n'est pas HTTPS, utiliser la méthode standard
                    push_result = self.repo.git.push(remote_name, branch)
            else:
                # Méthode standard sans token
                push_result = self.repo.git.push(remote_name, branch)
            
            result["success"] = True
            result["message"] = f"Push effectué avec succès vers {remote_name}/{branch}"
            
            logging.info(f"Push effectué vers {remote_name}/{branch}")
            return result
        except Exception as e:
            logging.error(f"Erreur lors du push: {e}")
            result["message"] = f"Erreur lors du push: {str(e)}"
            return result
    
    def should_auto_commit(self) -> bool:
        """
        Détermine si un commit automatique doit être effectué en fonction du temps écoulé.
        
        Returns:
            bool: True si un commit automatique doit être effectué, False sinon
        """
        if not self.config["auto_commit"]:
            return False
        
        elapsed = time.time() - self.last_commit_time
        return elapsed >= self.config["commit_interval"]
    
    def check_and_update(self) -> Dict[str, Any]:
        """
        Vérifie les modifications et effectue un commit/push si nécessaire.
        Cette méthode est destinée à être appelée périodiquement.
        
        Returns:
            Dict contenant le résultat de l'opération
        """
        result = {
            "action": "none",
            "changes_detected": False,
            "commit_result": None,
            "push_result": None
        }
        
        if not self.auto_tracking_enabled:
            return result
        
        # Détecter les changements
        changes = self.detect_changes()
        result["changes_detected"] = bool(changes)
        
        if not changes:
            return result
        
        # Vérifier si un commit automatique doit être effectué
        if self.should_auto_commit():
            # Générer un message de commit
            commit_message = self.generate_commit_message(changes)
            
            # Effectuer le commit
            commit_result = self.commit_changes(commit_message)
            result["action"] = "commit"
            result["commit_result"] = commit_result
            
            # Effectuer un push si configuré
            if commit_result["success"] and self.config["auto_push"]:
                push_result = self.push_changes()
                result["action"] = "commit_and_push"
                result["push_result"] = push_result
        
        return result
    
    def create_gitignore(self, templates: List[str] = None) -> bool:
        """
        Crée ou met à jour le fichier .gitignore dans le dépôt.
        
        Args:
            templates: Liste des templates à inclure (ex: ["python", "vscode"])
            
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        try:
            # Templates de base pour les projets Python
            default_ignores = [
                "# Python",
                "__pycache__/",
                "*.py[cod]",
                "*$py.class",
                "*.so",
                ".Python",
                "env/",
                "build/",
                "develop-eggs/",
                "dist/",
                "downloads/",
                "eggs/",
                ".eggs/",
                "lib/",
                "lib64/",
                "parts/",
                "sdist/",
                "var/",
                "*.egg-info/",
                ".installed.cfg",
                "*.egg",
                "",
                "# Virtualenv",
                "venv/",
                "ENV/",
                "",
                "# IDEs and editors",
                ".idea/",
                ".vscode/",
                "*.swp",
                "*.swo",
                "",
                "# OS specific",
                ".DS_Store",
                "Thumbs.db",
            ]
            
            gitignore_path = os.path.join(self.repo_path, ".gitignore")
            
            # Lire le fichier .gitignore existant s'il existe
            existing_ignores = []
            if os.path.exists(gitignore_path):
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    existing_ignores = f.read().splitlines()
            
            # Combiner les ignores existants avec les nouveaux
            combined = set(existing_ignores)
            for item in default_ignores:
                combined.add(item)
            
            # Écrire le fichier .gitignore
            with open(gitignore_path, "w", encoding="utf-8") as f:
                f.write("\n".join(sorted(combined)))
            
            logging.info(f"Fichier .gitignore créé/mis à jour à {gitignore_path}")
            return True
        except Exception as e:
            logging.error(f"Erreur lors de la création du fichier .gitignore: {e}")
            return False
    
    def create_branch(self, branch_name: str, from_branch: Optional[str] = None) -> Dict[str, Any]:
        """
        Crée une nouvelle branche et bascule dessus.
        
        Args:
            branch_name: Nom de la nouvelle branche
            from_branch: Branche de base (None pour la branche actuelle)
            
        Returns:
            Dict contenant le résultat de l'opération
        """
        result = {
            "success": False,
            "message": "",
            "branch": None
        }
        
        try:
            # Récupérer la branche de base
            if from_branch:
                base = self.repo.heads[from_branch]
            else:
                base = self.repo.active_branch
            
            # Créer la nouvelle branche
            new_branch = self.repo.create_head(branch_name, base)
            
            # Basculer sur la nouvelle branche
            new_branch.checkout()
            
            result["success"] = True
            result["message"] = f"Branche '{branch_name}' créée et activée"
            result["branch"] = branch_name
            
            logging.info(f"Branche '{branch_name}' créée à partir de '{base.name}'")
            return result
        except Exception as e:
            logging.error(f"Erreur lors de la création de la branche: {e}")
            result["message"] = f"Erreur lors de la création de la branche: {str(e)}"
            return result
    
    def list_branches(self) -> List[Dict[str, Any]]:
        """
        Liste toutes les branches locales du dépôt.
        
        Returns:
            Liste des branches avec leurs informations
        """
        branches = []
        
        try:
            active_branch = self.repo.active_branch.name
            
            for branch in self.repo.heads:
                branches.append({
                    "name": branch.name,
                    "commit": branch.commit.hexsha,
                    "message": branch.commit.message.strip(),
                    "author": f"{branch.commit.author.name} <{branch.commit.author.email}>",
                    "date": datetime.fromtimestamp(branch.commit.committed_date).isoformat(),
                    "is_active": branch.name == active_branch
                })
            
            return branches
        except Exception as e:
            logging.error(f"Erreur lors de la récupération des branches: {e}")
            return []
    
    def setup_github_workflow(self, workflow_type: str = "basic") -> bool:
        """
        Crée un workflow GitHub Actions de base.
        
        Args:
            workflow_type: Type de workflow à créer ("basic", "python", "docs")
            
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        try:
            # Créer le dossier .github/workflows s'il n'existe pas
            workflows_dir = os.path.join(self.repo_path, ".github", "workflows")
            os.makedirs(workflows_dir, exist_ok=True)
            
            workflow_file = None
            workflow_content = ""
            
            if workflow_type == "python":
                workflow_file = "python-test.yml"
                workflow_content = """name: Python Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
    - name: Run tests
      run: |
        python -m unittest discover
"""
            elif workflow_type == "docs":
                workflow_file = "docs-build.yml"
                workflow_content = """name: Documentation

on:
  push:
    branches: [ main ]
    paths:
      - 'docs/**'
      - '**.md'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install mkdocs
    - name: Build docs
      run: |
        mkdocs build
"""
            else:  # basic
                workflow_file = "basic-check.yml"
                workflow_content = """name: Basic Check

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Run file check
      run: |
        echo "Repository structure:"
        find . -type f -not -path "*/\.*" | sort
"""
            
            # Écrire le fichier de workflow
            if workflow_file and workflow_content:
                workflow_path = os.path.join(workflows_dir, workflow_file)
                with open(workflow_path, "w", encoding="utf-8") as f:
                    f.write(workflow_content)
                
                logging.info(f"Workflow GitHub Actions '{workflow_file}' créé")
                return True
            
            return False
        except Exception as e:
            logging.error(f"Erreur lors de la création du workflow GitHub Actions: {e}")
            return False