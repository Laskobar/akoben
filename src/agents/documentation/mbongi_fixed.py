"""
Agent Mbongi - Documentaliste et gestionnaire des connaissances pour Akoben.
Adapté du projet Eliza pour Akoben.
Permet la documentation automatique du code, le suivi du développement et la gestion des connaissances.
"""

import os
import sys
import json
import re
import datetime
import time

from typing import Dict, List, Any, Optional, Union, Tuple
import threading

# Import des composants internes
from .knowledge_base import KnowledgeBase
from .code_analyzer import CodeAnalyzer
from .documentation_generator import DocumentationGenerator
from .session_monitor import SessionMonitor
from .git_integrator import GitIntegrator


class Mbongi:
    """
    Agent Mbongi - Documentaliste et gestionnaire des connaissances d'Akoben
    """
    def __init__(self, project_path: str, config: Optional[Dict] = None):
        """
        Initialise l'agent Mbongi.
        
        Args:
            project_path: Chemin du projet Akoben
            config: Configuration optionnelle
        """
        self.project_path = os.path.abspath(project_path)
        self.config = config or self._default_config()
        
        # Initialiser les composants
        self.knowledge_base = KnowledgeBase(self.config.get("knowledge_base", {}))
        self.code_analyzer = CodeAnalyzer({
            "project_base_path": self.project_path,
            **self.config.get("code_analyzer", {})
        })
        self.documentation_generator = DocumentationGenerator(self.config.get("documentation_generator", {}))
        self.session_monitor = SessionMonitor(self.config.get("session_monitor", {}))
        self.git_integrator = GitIntegrator({
            "repo_path": self.project_path,
            **self.config.get("git_integrator", {})
        })
        
        # Initialiser les chemins importants
        self.doc_path = os.path.join(self.project_path, 'docs')
        self.journal_path = os.path.join(self.doc_path, 'journal')
        
        # Créer les dossiers nécessaires
        self._ensure_directories()
        
        # État interne
        self.session_active = False
        self.session_start_time = None
        self.session_ideas = []
        
        # Configurer les callbacks du moniteur de session
        self.session_monitor.register_session_start_callback(self.start_session)
        self.session_monitor.register_session_end_callback(self.end_session)
        
        print(f"Agent Mbongi initialisé, surveillant le projet à {self.project_path}")
    
    def _default_config(self) -> Dict[str, Any]:
        """Configuration par défaut pour Mbongi."""
        return {
            "knowledge_base": {
                "base_path": os.path.join(self.project_path, "docs", "knowledge_base")
            },
            "code_analyzer": {
                "project_base_path": self.project_path
            }
        }
    
    def _ensure_directories(self) -> None:
        """Crée les dossiers nécessaires à Mbongi."""
        os.makedirs(self.doc_path, exist_ok=True)
        os.makedirs(self.journal_path, exist_ok=True)
    
    # === Gestion de session ===
    
    def start_session(self) -> None:
        """Démarre une nouvelle session de développement."""
        if self.session_active:
            print("Une session est déjà active.")
            return
        
        self.session_active = True
        self.session_start_time = datetime.datetime.now()
        self.session_ideas = []
        
        print(f"Session démarrée à {self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Enregistrer le début de session dans le journal
        session_entry = {
            "type": "session_start",
            "timestamp": self.session_start_time.isoformat(),
            "metadata": {
                "workdir": os.getcwd()
            }
        }
        
        self._append_to_journal(session_entry)
    
    def end_session(self, generate_summary: bool = True) -> Optional[Dict[str, Any]]:
        """
        Termine la session en cours.
        
        Args:
            generate_summary: Si True, génère un résumé de la session
            
        Returns:
            Résumé de la session si generate_summary est True
        """
        if not self.session_active:
            print("Aucune session active à terminer.")
            return None
        
        end_time = datetime.datetime.now()
        duration = end_time - self.session_start_time
        
        print(f"Session terminée à {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Durée: {duration}")
        
        # Enregistrer la fin de session dans le journal
        session_entry = {
            "type": "session_end",
            "timestamp": end_time.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "ideas_count": len(self.session_ideas)
        }
        
        self._append_to_journal(session_entry)
        
        # Réinitialiser l'état de la session
        session_summary = None
        if generate_summary:
            session_summary = self._generate_session_summary(end_time, duration)
            self._save_session_summary(session_summary)
        
        self.session_active = False
        self.session_start_time = None
        
        return session_summary
    
    # === Surveillance automatique ===
    
    def start_auto_monitoring(self) -> None:
        """Démarre la surveillance automatique des sessions et du code."""
        self.session_monitor.start_monitoring()
        print("Surveillance automatique des sessions démarrée.")
        
        # Vérifier si des modifications sont présentes dès le démarrage
        if self.git_integrator:
            changes = self.git_integrator.check_changes()
            if any(files for files in changes.values()):
                print(f"Détection de {sum(len(files) for files in changes.values())} fichiers modifiés.")

    def stop_auto_monitoring(self) -> None:
        """Arrête la surveillance automatique."""
        self.session_monitor.stop_monitoring()
        print("Surveillance automatique des sessions arrêtée.")
        
        # Proposer de committer les changements en attente
        if self.git_integrator:
            changes = self.git_integrator.check_changes()
            if any(files for files in changes.values()):
                print(f"Attention: {sum(len(files) for files in changes.values())} fichiers modifiés non commités.")
                print("Vous pouvez commiter ces changements manuellement via le GitIntegrator.")
    
    def _generate_session_summary(self, end_time: datetime.datetime, 
                                  duration: datetime.timedelta) -> Dict[str, Any]:
        """
        Génère un résumé de la session de développement.
        
        Args:
            end_time: Heure de fin de la session
            duration: Durée de la session
            
        Returns:
            Résumé de la session
        """
        summary = {
            "start_time": self.session_start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "duration_formatted": str(duration).split('.')[0],  # HH:MM:SS format
            "ideas": self.session_ideas,
            "ideas_count": len(self.session_ideas)
        }
        
        return summary
    
    def _save_session_summary(self, summary: Dict[str, Any]) -> str:
        """
        Sauvegarde le résumé de session dans un fichier.
        
        Args:
            summary: Résumé de la session
            
        Returns:
            Chemin du fichier de résumé
        """
        date_str = self.session_start_time.strftime('%Y-%m-%d')
        time_str = self.session_start_time.strftime('%H-%M-%S')
        filename = f"session_{date_str}_{time_str}.json"
        
        file_path = os.path.join(self.journal_path, filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"Résumé de session sauvegardé dans {file_path}")
        return file_path
    
    # === Gestion des idées ===
    
    def process_idea(self, idea_content: str) -> bool:
        """
        Traite une idée au format MBONGI:IDEA.
        
        Args:
            idea_content: Contenu de l'idée au format MBONGI:IDEA
            
        Returns:
            True si l'idée a été traitée avec succès
        """
        # Vérifier que le format est correct
        if not re.search(r'\[MBONGI:IDEA\].*\[/MBONGI:IDEA\]', idea_content, re.DOTALL):
            print("Format d'idée invalide. Utilisez le format MBONGI:IDEA.")
            return False
        
        # Extraire les métadonnées de l'idée
        title_match = re.search(r'Title:\s*(.+)', idea_content)
        component_match = re.search(r'Component:\s*(.+)', idea_content)
        type_match = re.search(r'Type:\s*(.+)', idea_content)
        priority_match = re.search(r'Priority:\s*(.+)', idea_content)
        description_match = re.search(r'Description:\s*(.+?)\n\n', idea_content, re.DOTALL)
        implementation_match = re.search(r'Implementation:\s*(.+?)\n\n', idea_content, re.DOTALL)
        dependencies_match = re.search(r'Dependencies:\s*(.+?)\n\n', idea_content, re.DOTALL)
        status_match = re.search(r'Status:\s*(.+)', idea_content)
        
        # Créer l'objet idée structuré
        idea = {
            "timestamp": datetime.datetime.now().isoformat(),
            "title": title_match.group(1).strip() if title_match else "Idée sans titre",
            "component": component_match.group(1).strip() if component_match else "Non spécifié",
            "type": type_match.group(1).strip() if type_match else "Non spécifié",
            "priority": priority_match.group(1).strip() if priority_match else "Moyenne",
            "description": description_match.group(1).strip() if description_match else "",
            "implementation": implementation_match.group(1).strip() if implementation_match else "",
            "dependencies": [],
            "status": status_match.group(1).strip() if status_match else "À explorer",
            "raw_content": idea_content
        }
        
        # Traiter les dépendances
        if dependencies_match:
            deps_text = dependencies_match.group(1)
            deps = [d.strip() for d in re.findall(r'-\s*(.+)', deps_text)]
            idea["dependencies"] = deps
        
        # Ajouter l'idée à la session courante
        if self.session_active:
            self.session_ideas.append(idea)
        
        # Enregistrer l'idée dans le journal
        idea_entry = {
            "type": "idea",
            "timestamp": idea["timestamp"],
            "idea": idea
        }
        self._append_to_journal(idea_entry)
        
        # Stocker l'idée dans la base de connaissances
        self.knowledge_base.store("ideas", self._generate_idea_id(idea), idea)
        
        print(f"Idée '{idea['title']}' traitée et stockée avec succès.")
        return True
    
    def _generate_idea_id(self, idea: Dict[str, Any]) -> str:
        """Génère un identifiant unique pour une idée."""
        date_str = datetime.datetime.now().strftime('%Y%m%d')
        title_part = re.sub(r'[^a-zA-Z0-9]', '_', idea['title'].lower())[:30]
        return f"{date_str}_{title_part}"
    
    # === Documentation de code ===
    
    def analyze_component(self, component_path: str) -> Dict[str, Any]:
        """
        Analyse un composant (fichier ou dossier) et génère sa documentation.
        
        Args:
            component_path: Chemin relatif au projet ou absolu du composant
            
        Returns:
            Résultat de l'analyse
        """
        full_path = os.path.join(self.project_path, component_path) if not os.path.isabs(component_path) else component_path
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Le composant {full_path} n'existe pas")
        
        if os.path.isdir(full_path):
            result = self.code_analyzer.analyze_directory(full_path)
            component_type = "directory"
        else:
            result = self.code_analyzer.analyze_file(full_path)
            component_type = "file"
        
        # Créer/mettre à jour la fiche technique du composant
        self._create_component_card(result, component_type, os.path.relpath(full_path, self.project_path))
        
        # Journaliser l'analyse
        analysis_entry = {
            "type": "analysis",
            "timestamp": datetime.datetime.now().isoformat(),
            "component_path": os.path.relpath(full_path, self.project_path),
            "component_type": component_type,
            "summary": {
                "classes": result["metrics"]["class_count"] if component_type == "file" else result["summary"]["class_count"],
                "functions": result["metrics"]["function_count"] if component_type == "file" else result["summary"]["function_count"],
            }
        }
        self._append_to_journal(analysis_entry)
        
        return result
    
    def _create_component_card(self, analysis: Dict[str, Any], 
                           component_type: str, relative_path: str) -> None:
        """
        Crée ou met à jour une fiche technique pour un composant.
        
        Args:
            analysis: Résultat de l'analyse
            component_type: Type de composant ('file' ou 'directory')
            relative_path: Chemin relatif du composant dans le projet
        """
        # Déterminer la catégorie de composant
        category = "components"
        if "src/agents" in relative_path:
            category = "agents"
        elif "src/anansi" in relative_path:
            category = "teams"
        
        # Créer l'identifiant du composant
        component_id = re.sub(r'[^a-zA-Z0-9]', '_', relative_path.lower())
        
        # Déterminer le nom propre du composant
        name = os.path.basename(relative_path)
        if name.endswith('.py'):
            name = name[:-3]
        
        # Extraire des informations pertinentes selon le type
        if component_type == "file":
            component_data = {
                "name": name,
                "path": relative_path,
                "type": "File" if relative_path.endswith('.py') else "Other",
                "docstring": analysis.get('module_docstring', ''),
                "classes": [cls['name'] for cls in analysis.get('classes', [])],
                "functions": [func['name'] for func in analysis.get('functions', [])],
                "line_count": analysis.get('line_count', 0),
                "metrics": analysis.get('metrics', {}),
                "dependencies": analysis.get('dependencies', []),
                "last_analyzed": datetime.datetime.now().isoformat()
            }
        else:
            component_data = {
                "name": name,
                "path": relative_path,
                "type": "Directory",
                "summary": analysis.get('summary', {}),
                "files": [os.path.basename(f['file_path']) for f in analysis.get('files', [])],
                "last_analyzed": datetime.datetime.now().isoformat()
            }
        
        # Stocker ou mettre à jour la fiche dans la base de connaissances
        self.knowledge_base.update(category, component_id, component_data)
        
        # Générer la version Markdown de la fiche
        output_file = f"{category}/{component_id}.md"
        self.documentation_generator.generate_component_card(component_data, output_file)
        
        print(f"Fiche technique du composant '{relative_path}' mise à jour.")
    
    def update_all_documentation(self) -> Dict[str, Any]:
        """
        Met à jour la documentation pour tous les composants importants du projet.
        
        Returns:
            Résumé des mises à jour
        """
        print("Mise à jour de la documentation pour tout le projet...")
        
        key_paths = [
            "src/agents",
            "src/anansi",
            "src/tools"
        ]
        
        update_summary = {
            "timestamp": datetime.datetime.now().isoformat(),
            "components_analyzed": 0,
            "files_analyzed": 0,
            "classes_documented": 0,
            "functions_documented": 0,
            "errors": []
        }
        
        for path in key_paths:
            full_path = os.path.join(self.project_path, path)
            if not os.path.exists(full_path):
                update_summary["errors"].append(f"Chemin {path} non trouvé")
                continue
            
            try:
                result = self.analyze_component(path)
                update_summary["components_analyzed"] += 1
                
                if os.path.isdir(full_path):
                    update_summary["files_analyzed"] += result["summary"]["file_count"]
                    update_summary["classes_documented"] += result["summary"]["class_count"]
                    update_summary["functions_documented"] += result["summary"]["function_count"]
                else:
                    update_summary["files_analyzed"] += 1
                    update_summary["classes_documented"] += result["metrics"]["class_count"]
                    update_summary["functions_documented"] += result["metrics"]["function_count"]
            
            except Exception as e:
                update_summary["errors"].append(f"Erreur lors de l'analyse de {path}: {str(e)}")
        
        # Journaliser l'opération
        update_entry = {
            "type": "documentation_update",
            "timestamp": update_summary["timestamp"],
            "summary": update_summary
        }
        self._append_to_journal(update_entry)
        
        print(f"Documentation mise à jour. {update_summary['files_analyzed']} fichiers analysés.")
        return update_summary
    
    # === Journal de développement ===
    
    def _append_to_journal(self, entry: Dict[str, Any]) -> None:
        """
        Ajoute une entrée au journal de développement.
        
        Args:
            entry: Entrée à ajouter (doit contenir 'type' et 'timestamp')
        """
        if 'type' not in entry or 'timestamp' not in entry:
            raise ValueError("Les entrées du journal doivent contenir 'type' et 'timestamp'")
        
        date_str = entry['timestamp'].split('T')[0]
        journal_file = os.path.join(self.journal_path, f"journal_{date_str}.jsonl")
        
        with open(journal_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    def get_development_journal(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Récupère les entrées récentes du journal de développement.
        
        Args:
            days: Nombre de jours en arrière à considérer
            
        Returns:
            Liste des entrées de journal
        """
        entries = []
        today = datetime.datetime.now().date()
        
        for i in range(days):
            date = today - datetime.timedelta(days=i)
            date_str = date.isoformat()
            journal_file = os.path.join(self.journal_path, f"journal_{date_str}.jsonl")
            
            if os.path.exists(journal_file):
                with open(journal_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            entries.append(json.loads(line))
        
        # Trier par horodatage
        entries.sort(key=lambda x: x['timestamp'], reverse=True)
        return entries
    
    def generate_development_report(self, days: int = 7) -> Dict[str, Any]:
        """
        Génère un rapport de développement basé sur le journal.
        
        Args:
            days: Nombre de jours à inclure dans le rapport
            
        Returns:
            Rapport de développement
        """
        journal_entries = self.get_development_journal(days)
        
        report = {
            "period": {
                "days": days,
                "start_date": (datetime.datetime.now().date() - datetime.timedelta(days=days-1)).isoformat(),
                "end_date": datetime.datetime.now().date().isoformat()
            },
            "sessions": {
                "count": 0,
                "total_duration_hours": 0,
                "average_duration_minutes": 0
            },
            "ideas": {
                "count": 0,
                "by_component": {},
                "by_priority": {"Haute": 0, "Moyenne": 0, "Basse": 0}
            },
            "components": {
                "analyzed": 0,
                "files_count": 0,
                "classes_count": 0,
                "functions_count": 0
            }
        }
        
        # Extraire les sessions
        sessions = []
        session_starts = {}
        
        for entry in journal_entries:
            entry_type = entry['type']
            
            if entry_type == 'session_start':
                session_id = entry['timestamp']
                session_starts[session_id] = entry
            
            elif entry_type == 'session_end':
                # Trouver le début de session correspondant
                matching_start = None
                for start_id, start_entry in session_starts.items():
                    # Supposer que la correspondance est le début de session le plus proche dans le temps
                    matching_start = start_id
                    break
                
                if matching_start:
                    start_time = datetime.datetime.fromisoformat(session_starts[matching_start]['timestamp'])
                    end_time = datetime.datetime.fromisoformat(entry['timestamp'])
                    duration = (end_time - start_time).total_seconds() / 3600  # en heures
                    
                    sessions.append({
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat(),
                        "duration_hours": duration
                    })
                    
                    # Supprimer cette session des débuts en attente
                    del session_starts[matching_start]
            
            elif entry_type == 'idea':
                report["ideas"]["count"] += 1
                
                # Compter par composant
                component = entry['idea'].get('component', 'Non spécifié')
                if component not in report["ideas"]["by_component"]:
                    report["ideas"]["by_component"][component] = 0
                report["ideas"]["by_component"][component] += 1
                
                # Compter par priorité
                priority = entry['idea'].get('priority', 'Moyenne')
                if priority in report["ideas"]["by_priority"]:
                    report["ideas"]["by_priority"][priority] += 1
            
            elif entry_type == 'documentation_update':
                if 'summary' in entry:
                    summary = entry['summary']
                    report["components"]["analyzed"] += summary.get('components_analyzed', 0)
                    report["components"]["files_count"] += summary.get('files_analyzed', 0)
                    report["components"]["classes_count"] += summary.get('classes_documented', 0)
                    report["components"]["functions_count"] += summary.get('functions_documented', 0)
        
        # Calculer les métriques de session
        report["sessions"]["count"] = len(sessions)
        if sessions:
            total_duration = sum(s["duration_hours"] for s in sessions)
            report["sessions"]["total_duration_hours"] = total_duration
            report["sessions"]["average_duration_minutes"] = (total_duration / len(sessions)) * 60
        
        return report
    
    # === Interface avec Anansi ===
    
    def query_component(self, component_name: str) -> Optional[Dict[str, Any]]:
        """
        Interroge la base de connaissances pour obtenir des informations sur un composant.
        
        Args:
            component_name: Nom du composant (peut être un chemin, un nom de fichier, etc.)
            
        Returns:
            Informations sur le composant ou None si non trouvé
        """
        # Normaliser le nom du composant
        component_name = component_name.lower()
        
        # Chercher dans toutes les catégories pertinentes
        for category in ["agents", "teams", "components"]:
            # Essayer une correspondance directe
            component_id = re.sub(r'[^a-zA-Z0-9]', '_', component_name)
            component = self.knowledge_base.retrieve(category, component_id)
            if component:
                return {
                    "category": category,
                    "id": component_id,
                    "data": component
                }
            
            # Chercher par nom dans tous les documents de la catégorie
            docs = self.knowledge_base.list_documents(category)
            for doc_id in docs:
                doc = self.knowledge_base.retrieve(category, doc_id)
                if doc and doc.get('name', '').lower() == component_name:
                    return {
                        "category": category,
                        "id": doc_id,
                        "data": doc
                    }
        
        # Essayer une recherche plus large
        search_results = self.knowledge_base.search(component_name)
        if search_results:
            return {
                "category": search_results[0]['category'],
                "id": search_results[0]['name'],
                "data": search_results[0]['document'],
                "search_results_count": len(search_results)
            }
        
        return None
    
    def register_update(self, component_name: str, update_type: str) -> bool:
        """
        Enregistre une mise à jour d'un composant effectuée par Anansi.
        
        Args:
            component_name: Nom ou chemin du composant mis à jour
            update_type: Type de mise à jour (création, modification, etc.)
            
        Returns:
            True si l'enregistrement a réussi
        """
        update_entry = {
            "type": "anansi_update",
            "timestamp": datetime.datetime.now().isoformat(),
            "component": component_name,
            "update_type": update_type
        }
        
        self._append_to_journal(update_entry)
        
        # Si le composant existe dans la base de connaissances, mettre à jour la date de dernière modification
        component_info = self.query_component(component_name)
        if component_info:
            category = component_info["category"]
            comp_id = component_info["id"]
            component_data = component_info["data"]
            
            if "last_modified" not in component_data:
                component_data["last_modified"] = []
                
            component_data["last_modified"].append({
                "timestamp": update_entry["timestamp"],
                "type": update_type
            })
            
            self.knowledge_base.update(category, comp_id, component_data)
        
        return True
    
    def add_idea(self, idea_data):
        """
        Ajoute une idée au journal de la session.
        """
        # Vérifier les champs obligatoires
        if "title" not in idea_data or "description" not in idea_data:
            raise ValueError("Les champs 'title' et 'description' sont obligatoires pour une idée")
        
        # Créer l'objet idée
        idea = {
            "id": f"IDEA_{int(time.time())}",
            "timestamp": datetime.datetime.now().isoformat(),
            "title": idea_data["title"],
            "description": idea_data["description"],
            "components": idea_data.get("components", []),
            "priority": idea_data.get("priority", "Medium"),
            "tags": idea_data.get("tags", []),
            "status": "new"
        }
        
        # Ajouter à la session active
        if self.session_active:
            self.session_ideas.append(idea)
            print(f"Idée '{idea['title']}' ajoutée à la session en cours")
        
        # Créer le dossier des idées
        ideas_dir = os.path.join(self.doc_path, "ideas")
        os.makedirs(ideas_dir, exist_ok=True)
        
        # Créer le chemin du fichier
        idea_path = os.path.join(ideas_dir, f"{idea['id']}.md")
        
        # Créer le contenu
        content = f"""# {idea['title']}

## Description
{idea['description']}

## Métadonnées
- **ID**: {idea['id']}
- **Date**: {idea['timestamp']}
- **Composants**: {', '.join(idea['components'])}
- **Priorité**: {idea['priority']}
- **Tags**: {', '.join(idea['tags'])}
- **Statut**: {idea['status']}

## MBONGI:IDEA
```json
{json.dumps(idea, indent=2)}
```
"""
        # Écrire le fichier
        with open(idea_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
        print(f"Idée enregistrée dans {idea_path}")
        return idea["id"]