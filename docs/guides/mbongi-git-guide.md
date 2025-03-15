# Guide pratique: Utilisation de Mbongi avec Git

Ce guide vous explique comment configurer et utiliser Mbongi pour gérer automatiquement la documentation et les mises à jour Git du projet Akoben.

## Table des matières
1. [Configuration initiale](#configuration-initiale)
2. [Utilisation quotidienne](#utilisation-quotidienne)
3. [GitIntegrator en détail](#gitintegrator-en-détail)
4. [Automatisation](#automatisation)
5. [Résolution des problèmes courants](#résolution-des-problèmes-courants)

## Configuration initiale

### Prérequis
- Git installé et configuré sur votre système
- Les packages Python nécessaires: `gitpython`
- Un token GitHub si vous souhaitez utiliser l'authentification automatique

### Étape 1: Configuration des variables d'environnement
Pour une utilisation sécurisée, configurez ces variables d'environnement:

```bash
export GIT_USERNAME="votre_nom_utilisateur"
export GIT_EMAIL="votre_email@exemple.com"
export GITHUB_TOKEN="votre_token_github"  # Optionnel, pour l'authentification automatique
```

Pour rendre ces variables permanentes, ajoutez-les à votre fichier `~/.bashrc` ou équivalent.

### Étape 2: Modification du fichier de test pour Mbongi

Utilisez le fichier `test_mbongi.py` amélioré fourni dans ce guide. Ce fichier configure Mbongi pour utiliser GitIntegrator efficacement.

Assurez-vous que les chemins sont corrects et que les configurations correspondent à votre environnement.

### Étape 3: Premier lancement

Exécutez le script de test pour initialiser Mbongi avec Git:

```bash
python src/test_mbongi.py
```

Lors de la première exécution, si les variables d'environnement ne sont pas définies, le script vous demandera vos informations Git.

## Utilisation quotidienne

### Démarrer une session de développement

Au début de votre session de travail, exécutez:

```python
from src.agents.documentation.mbongi import Mbongi

# Initialiser Mbongi avec votre configuration
mbongi = Mbongi(project_path="/chemin/vers/akoben", config=your_config)

# Démarrer une session
mbongi.start_session()
```

### Enregistrer des idées pendant le développement

Lorsque vous avez une idée pendant le développement:

```python
idea = {
    "title": "Amélioration de X",
    "description": "Détails de l'amélioration...",
    "components": ["Composant1", "Composant2"],
    "priority": "Medium",
    "tags": ["feature", "optimization"]
}
mbongi.add_idea(idea)
```

### Terminer une session de développement

À la fin de votre session:

```python
# Terminer la session
mbongi.end_session()
```

Mbongi générera automatiquement un résumé de session, mettra à jour la documentation et effectuera un commit/push si configuré.

## GitIntegrator en détail

### Configuration recommandée

```python
git_config = {
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
```

### Règles de commit personnalisées

Les règles de commit permettent de générer des messages intelligents basés sur les fichiers modifiés:

```python
commit_rules = {
    "documentation": {
        "pattern": ["docs/", "*.md"],
        "message": "Mise à jour de la documentation"
    },
    "code_source": {
        "pattern": ["src/", "*.py"],
        "message": "Mise à jour du code source"
    },
    "configuration": {
        "pattern": ["configs/", "*.yaml", "*.yml", "*.json"],
        "message": "Mise à jour des fichiers de configuration"
    },
    "anansi": {
        "pattern": ["src/anansi/", "src/anansi/*"],
        "message": "Amélioration d'Anansi"
    },
    "mbongi": {
        "pattern": ["src/agents/documentation/", "src/agents/documentation/*"],
        "message": "Amélioration de Mbongi"
    },
    "test": {
        "pattern": ["tests/", "test_*.py"],
        "message": "Ajout ou mise à jour des tests"
    }
}

# Configurer les règles
mbongi.git_integrator.set_commit_rules(commit_rules)
```

### Fonctions utiles de GitIntegrator

- Vérifier l'état du dépôt: `git_status = mbongi.git_integrator.get_repo_status()`
- Détecter les changements: `changes = mbongi.git_integrator.detect_changes()`
- Commit manuel: `mbongi.git_integrator.commit_changes("Mon message de commit")`
- Push manuel: `mbongi.git_integrator.push_changes()`
- Créer une branche: `mbongi.git_integrator.create_branch("nouvelle-fonctionnalite")`
- Lister les branches: `branches = mbongi.git_integrator.list_branches()`

## Automatisation

### Script d'automatisation des commits

Pour automatiser complètement la gestion Git, créez un script qui s'exécute en arrière-plan:

```python
#!/usr/bin/env python3
# git_monitor.py

import time
import logging
from src.agents.documentation.mbongi import Mbongi

# Configuration de la journalisation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='git_monitor.log'
)

# Initialiser Mbongi
project_path = "/chemin/vers/akoben"
mbongi = Mbongi(project_path, config=your_config)

# Activer le suivi automatique
mbongi.git_integrator.enable_auto_tracking()

# Boucle principale
try:
    logging.info("Surveillance Git démarrée")
    while True:
        # Vérifier et mettre à jour Git
        result = mbongi.git_integrator.check_and_update()
        
        if result["changes_detected"]:
            logging.info(f"Action: {result['action']}")
            if result.get("commit_result"):
                logging.info(f"Commit: {result['commit_result']['message']}")
            if result.get("push_result"):
                logging.info(f"Push: {result['push_result']['message']}")
        
        # Attendre avant la prochaine vérification (15 minutes)
        time.sleep(900)
except KeyboardInterrupt:
    logging.info("Surveillance Git arrêtée par l'utilisateur")
except Exception as e:
    logging.error(f"Erreur: {e}")
finally:
    logging.info("Surveillance Git terminée")
```

### Configuration comme service système

Pour exécuter le script en tant que service système sous Linux:

1. Créez un fichier de service:

```bash
sudo nano /etc/systemd/system/git-monitor.service
```

2. Ajoutez le contenu suivant:

```
[Unit]
Description=Akoben Git Monitor Service
After=network.target

[Service]
Type=simple
User=votre_utilisateur
WorkingDirectory=/chemin/vers/akoben
ExecStart=/usr/bin/python3 /chemin/vers/akoben/git_monitor.py
Restart=on-failure
Environment=GIT_USERNAME=votre_nom_utilisateur
Environment=GIT_EMAIL=votre_email@exemple.com
Environment=GITHUB_TOKEN=votre_token_github

[Install]
WantedBy=multi-user.target
```

3. Activez et démarrez le service:

```bash
sudo systemctl enable git-monitor.service
sudo systemctl start git-monitor.service
```

4. Vérifiez l'état du service:

```bash
sudo systemctl status git-monitor.service
```

## Résolution des problèmes courants

### Problème: Conflits Git lors des push

**Solution:** Configurez Mbongi pour effectuer un pull avant de push:

```python
# Dans votre configuration GitIntegrator
git_config["pull_before_push"] = True

# Dans le code de GitIntegrator, ajoutez cette fonction
def pull_changes(self, remote_name=None, branch=None):
    """
    Récupère les changements du dépôt distant.
    """
    remote_name = remote_name or self.config["remote_name"]
    branch = branch or self.config["default_branch"]
    
    try:
        self.repo.git.pull(remote_name, branch)
        return True
    except Exception as e:
        logging.error(f"Erreur lors du pull: {e}")
        return False

# Et modifiez push_changes pour utiliser pull_before_push
if self.config.get("pull_before_push", False):
    self.pull_changes(remote_name, branch)
```

### Problème: Messages de commit inadaptés

**Solution:** Affinez vos règles de commit ou utilisez des patterns plus spécifiques:

```python
# Règle plus spécifique pour différentes parties du code
commit_rules["anansi_cognitive"] = {
    "pattern": ["src/anansi/cognitive/*"],
    "message": "Amélioration des capacités cognitives d'Anansi"
}
```

### Problème: Fichiers sensibles commités par erreur

**Solution:** Améliorez votre .gitignore et configurez des patterns à ignorer:

```python
# Ajoutez à la configuration
git_config["ignored_patterns"] = [
    "*.log",
    "credentials.json",
    "config_local.yaml"
]

# Dans le code de detect_changes, ajoutez:
ignored_patterns = self.config.get("ignored_patterns", [])
if any(fnmatch.fnmatch(rel_path, pattern) for pattern in ignored_patterns):
    continue
```

### Problème: Erreurs d'authentification GitHub

**Solution:** Vérifiez que votre token a les bons droits et utilisez une URL HTTPS:

```bash
# Vérifiez la configuration de votre remote
git remote -v

# Si nécessaire, changez pour HTTPS
git remote set-url origin https://github.com/username/repo.git
```

Ensuite, assurez-vous que votre token GitHub a les scopes `repo` pour l'accès complet au dépôt.