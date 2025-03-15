"""
Module d'intégration Git pour Mbongi.
Permet de suivre et d'enregistrer les modifications du code avec Git.
"""

import os
import subprocess
import re
import time
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime

class GitIntegrator:
    """
    Intégrateur Git pour Mbongi.
    Gère les interactions avec Git pour suivre les modifications du code.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialise l'intégrateur Git.
        
        Args:
            config: Dictionnaire de configuration optionnel
        """
        self.config = config or {}
        self.repo_path = self.config.get('repo_path', '.')
        self.branches = self.config.get('branches', {
            'main': 'main',
            'development': 'development'
        })
        self.current_branch = None
        self.auto_commit = self.config.get('auto_commit', True)
        self.auto_push = self.config.get('auto_push', False)
        self.commit_interval = self.config.get('commit_interval', 3600)  # 1 heure par défaut
        self.last_commit_time = None
        
        # Configuration du logging
        self.log_dir = self.config.get('log_dir', 'logs')
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.logger = logging.getLogger('GitIntegrator')
        self.logger.setLevel(logging.INFO)
        
        # Handler pour fichier
        log_file = os.path.join(self.log_dir, 'git_integrator.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Handler pour console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Ajouter les handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Vérifier que le dépôt est bien initialisé
        self._ensure_git_repo()
        
        # Déterminer la branche courante
        self.current_branch = self._get_current_branch()
        self.logger.info(f"Intégrateur Git initialisé sur la branche '{self.current_branch}'")
    
    def _ensure_git_repo(self) -> bool:
        """
        Vérifie que le dépôt Git est bien initialisé et le crée si nécessaire.
        
        Returns:
            True si le dépôt est correctement initialisé
        """
        git_dir = os.path.join(self.repo_path, '.git')
        
        if not os.path.exists(git_dir):
            self.logger.warning(f"Aucun dépôt Git trouvé dans {self.repo_path}")
            
            try:
                self._run_git_command(['init'])
                self.logger.info(f"Dépôt Git initialisé dans {self.repo_path}")
                
                # Créer un commit initial
                self._create_git_ignore()
                self._run_git_command(['add', '.gitignore'])
                self._run_git_command(['commit', '-m', 'Initial commit'])
                
                return True
            except Exception as e:
                self.logger.error(f"Erreur lors de l'initialisation du dépôt Git: {str(e)}")
                return False
        
        return True
    
    def _create_git_ignore(self) -> None:
        """Crée un fichier .gitignore standard."""
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/

# IDEs
.idea/
.vscode/
*.swp
*.swo

# Logs
logs/
*.log

# Documentation générée
docs/generated/

# Spécifiques au projet
/docs/knowledge_base/
/data/learning/
"""
        
        gitignore_path = os.path.join(self.repo_path, '.gitignore')
        
        # Ne pas écraser un .gitignore existant
        if not os.path.exists(gitignore_path):
            with open(gitignore_path, 'w') as f:
                f.write(gitignore_content)
            
            self.logger.info("Fichier .gitignore créé")
    
    def _run_git_command(self, command: List[str]) -> str:
        """
        Exécute une commande Git et renvoie sa sortie.
        
        Args:
            command: Liste contenant la commande Git et ses arguments
            
        Returns:
            Sortie de la commande
            
        Raises:
            Exception: Si la commande échoue
        """
        full_command = ['git', '-C', self.repo_path] + command
        
        try:
            result = subprocess.run(
                full_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_message = f"Erreur lors de l'exécution de 'git {' '.join(command)}': {e.stderr.strip()}"
            self.logger.error(error_message)
            raise Exception(error_message)
    
    def _get_current_branch(self) -> str:
        """
        Détermine la branche Git courante.
        
        Returns:
            Nom de la branche courante
        """
        try:
            branch = self._run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'])
            return branch
        except Exception:
            # En cas d'erreur, supposer que nous sommes sur la branche principale
            return self.branches.get('main', 'main')
    
    def _get_unstaged_changes(self) -> List[str]:
        """
        Récupère la liste des fichiers modifiés non stagés.
        
        Returns:
            Liste des chemins de fichiers modifiés
        """
        try:
            output = self._run_git_command(['status', '--porcelain'])
            
            changes = []
            for line in output.split('\n'):
                if line.strip():
                    # Extraire le statut et le chemin du fichier
                    status = line[:2].strip()
                    file_path = line[3:].strip()
                    
                    # Ignorer les fichiers déjà stagés (A, M, R, C dans la première colonne)
                    if status[0] not in ['A', 'M', 'R', 'C']:
                        changes.append(file_path)
            
            return changes
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des changements: {str(e)}")
            return []
    
    def check_changes(self) -> Dict[str, List[str]]:
        """
        Vérifie les changements dans le dépôt.
        
        Returns:
            Dictionnaire avec les différents types de changements
        """
        try:
            # Récupérer l'état du dépôt
            status_output = self._run_git_command(['status', '--porcelain'])
            
            changes = {
                'modified': [],
                'added': [],
                'deleted': [],
                'renamed': [],
                'untracked': []
            }
            
            # Analyser la sortie
            for line in status_output.split('\n'):
                if not line.strip():
                    continue
                
                status = line[:2]
                file_path = line[3:].strip()
                
                if status.startswith('M'):
                    changes['modified'].append(file_path)
                elif status.startswith('A'):
                    changes['added'].append(file_path)
                elif status.startswith('D'):
                    changes['deleted'].append(file_path)
                elif status.startswith('R'):
                    changes['renamed'].append(file_path)
                elif status.startswith('??'):
                    changes['untracked'].append(file_path)
            
            return changes
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification des changements: {str(e)}")
            return {'error': [str(e)]}
    
    def stage_file(self, file_path: str) -> bool:
        """
        Ajoute un fichier à l'index Git.
        
        Args:
            file_path: Chemin du fichier à ajouter
            
        Returns:
            True si l'opération a réussi
        """
        try:
            self._run_git_command(['add', file_path])
            self.logger.info(f"Fichier ajouté à l'index: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de l'ajout du fichier {file_path}: {str(e)}")
            return False
    
    def stage_all_changes(self) -> bool:
        """
        Ajoute tous les changements à l'index Git.
        
        Returns:
            True si l'opération a réussi
        """
        try:
            self._run_git_command(['add', '.'])
            self.logger.info("Tous les changements ont été ajoutés à l'index")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de l'ajout des changements: {str(e)}")
            return False
    
    def commit(self, message: str = None) -> bool:
        """
        Crée un commit avec les changements stagés.
        
        Args:
            message: Message de commit
            
        Returns:
            True si l'opération a réussi
        """
        if not message:
            message = self._generate_commit_message()
        
        try:
            self._run_git_command(['commit', '-m', message])
            self.last_commit_time = time.time()
            self.logger.info(f"Commit créé: {message}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la création du commit: {str(e)}")
            return False
    
    def _generate_commit_message(self) -> str:
        """
        Génère un message de commit automatique basé sur les changements.
        
        Returns:
            Message de commit
        """
        changes = self.check_changes()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Compter les changements par type
        counts = {k: len(v) for k, v in changes.items() if v}
        
        # Générer un résumé basé sur les types de changements
        if counts:
            change_summary = ", ".join(f"{count} {type}" for type, count in counts.items() if count > 0)
            return f"Auto-commit: {change_summary} - {timestamp}"
        else:
            return f"Auto-commit - {timestamp}"
    
    def push(self, remote: str = 'origin') -> bool:
        """
        Pousse les commits vers le dépôt distant.
        
        Args:
            remote: Nom du dépôt distant
            
        Returns:
            True si l'opération a réussi
        """
        try:
            self._run_git_command(['push', remote, self.current_branch])
            self.logger.info(f"Changements poussés vers {remote}/{self.current_branch}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors du push: {str(e)}")
            return False
    
    def auto_commit_if_needed(self) -> bool:
        """
        Crée un commit automatique si des changements sont en attente depuis longtemps.
        
        Returns:
            True si un commit a été créé
        """
        if not self.auto_commit:
            return False
        
        # Vérifier s'il y a des changements non stagés
        unstaged_changes = self._get_unstaged_changes()
        if not unstaged_changes:
            return False
        
        # Vérifier si le délai depuis le dernier commit est écoulé
        current_time = time.time()
        if (self.last_commit_time is None or 
            current_time - self.last_commit_time >= self.commit_interval):
            
            # Stager tous les changements
            self.stage_all_changes()
            
            # Créer un commit
            result = self.commit()
            
            # Pousser si configuré
            if result and self.auto_push:
                self.push()
            
            return result
        
        return False
    
    def get_commit_history(self, count: int = 10) -> List[Dict[str, str]]:
        """
        Récupère l'historique des commits.
        
        Args:
            count: Nombre de commits à récupérer
            
        Returns:
            Liste des commits sous forme de dictionnaires
        """
        try:
            output = self._run_git_command([
                'log',
                f'-{count}',
                '--pretty=format:%H|%an|%ad|%s',
                '--date=iso'
            ])
            
            commits = []
            for line in output.split('\n'):
                if line.strip():
                    parts = line.split('|', 3)
                    if len(parts) == 4:
                        commit = {
                            'hash': parts[0],
                            'author': parts[1],
                            'date': parts[2],
                            'message': parts[3]
                        }
                        commits.append(commit)
            
            return commits
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération de l'historique: {str(e)}")
            return []
    
    def create_branch(self, branch_name: str) -> bool:
        """
        Crée une nouvelle branche.
        
        Args:
            branch_name: Nom de la branche à créer
            
        Returns:
            True si l'opération a réussi
        """
        try:
            self._run_git_command(['checkout', '-b', branch_name])
            self.current_branch = branch_name
            self.logger.info(f"Branche créée et checkoutée: {branch_name}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la création de la branche {branch_name}: {str(e)}")
            return False
    
    def checkout_branch(self, branch_name: str) -> bool:
        """
        Bascule vers une branche existante.
        
        Args:
            branch_name: Nom de la branche
            
        Returns:
            True si l'opération a réussi
        """
        try:
            self._run_git_command(['checkout', branch_name])
            self.current_branch = branch_name
            self.logger.info(f"Branche checkoutée: {branch_name}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors du checkout de la branche {branch_name}: {str(e)}")
            return False


# Test simple du module si exécuté directement
if __name__ == "__main__":
    # Créer une instance de l'intégrateur Git
    integrator = GitIntegrator()
    
    # Vérifier les changements
    print("Vérification des changements...")
    changes = integrator.check_changes()
    for change_type, files in changes.items():
        if files:
            print(f"{change_type.capitalize()}: {len(files)} fichier(s)")
            for file in files[:5]:  # Afficher jusqu'à 5 fichiers
                print(f"  - {file}")
            if len(files) > 5:
                print(f"  - ... et {len(files) - 5} autres")
    
    # Récupérer l'historique des commits
    print("\nRécupération de l'historique des commits...")
    commits = integrator.get_commit_history(5)
    for commit in commits:
        print(f"{commit['date']} - {commit['message']} ({commit['hash'][:7]})")
    
    # Ne pas créer de commit automatique pendant les tests
    print("\nTest terminé.")