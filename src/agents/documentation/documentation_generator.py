"""
Module de génération de documentation pour Mbongi.
Adapté du projet Eliza pour Akoben.
Génère des documents Markdown à partir des informations extraites du code.
"""

import os
import re
import datetime
from typing import Dict, List, Any, Optional, Union
import jinja2


class DocumentationGenerator:
    """
    Générateur de documentation pour Akoben.
    Utilise Jinja2 pour générer des documents Markdown à partir de templates.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialise le générateur de documentation.
        
        Args:
            config: Dictionnaire de configuration optionnel
        """
        self.config = config or {}
        self.templates_dir = self.config.get('templates_dir', 'src/agents/documentation/templates')
        self.output_dir = self.config.get('output_dir', 'docs/generated')
        
        # Créer le dossier de sortie s'il n'existe pas
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialiser l'environnement Jinja2
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.templates_dir),
            autoescape=jinja2.select_autoescape(['html']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Ajouter des filtres personnalisés
        self.env.filters['percentage'] = lambda value: f"{value * 100:.1f}%"
        self.env.filters['date'] = lambda value: datetime.datetime.fromisoformat(value).strftime('%Y-%m-%d %H:%M:%S')
        self.env.filters['basename'] = lambda value: os.path.basename(value)
        
    def generate_component_card(self, component_data: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """
        Génère une fiche technique pour un composant.
        
        Args:
            component_data: Données du composant
            output_file: Chemin du fichier de sortie (optionnel)
            
        Returns:
            Contenu Markdown généré
        """
        try:
            template = self.env.get_template('component_card.md')
        except jinja2.exceptions.TemplateNotFound:
            # Utiliser un template par défaut si le fichier n'existe pas
            template_str = """# Composant: {{name}}

## Vue d'ensemble
- **Type**: {{type}}
- **Chemin**: `{{path}}`
- **Dernière analyse**: {{last_analyzed}}

{% if docstring %}
## Description
{{docstring}}
{% else %}
## Description
*Pas de description disponible*
{% endif %}

{% if classes %}
## Classes
{% for class in classes %}
- **{{class}}**
{% endfor %}
{% endif %}

{% if functions %}
## Fonctions
{% for function in functions %}
- **{{function}}**
{% endfor %}
{% endif %}

{% if dependencies %}
## Dépendances
{% for dependency in dependencies %}
- **{{dependency.name}}** ({{dependency.type}})
{% endfor %}
{% endif %}

{% if metrics %}
## Métriques
- **Lignes de code**: {{line_count}}
- **Classes**: {{metrics.class_count}}
- **Fonctions**: {{metrics.function_count}}
{% if metrics.documentation_ratio is defined %}
- **Ratio de documentation**: {{metrics.documentation_ratio|percentage}}
{% endif %}
{% endif %}

## Historique des modifications
{% if last_modified %}
{% for modification in last_modified %}
- **{{modification.timestamp|date}}**: {{modification.type}}
{% endfor %}
{% else %}
*Aucune modification enregistrée*
{% endif %}
"""
            template = jinja2.Template(template_str)
        
        # Générer le contenu Markdown
        markdown_content = template.render(**component_data)
        
        # Sauvegarder dans un fichier si demandé
        if output_file:
            full_path = os.path.join(self.output_dir, output_file)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
        
        return markdown_content
    
    def generate_team_documentation(self, team_data: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """
        Génère la documentation pour une équipe d'agents.
        
        Args:
            team_data: Données de l'équipe
            output_file: Chemin du fichier de sortie (optionnel)
            
        Returns:
            Contenu Markdown généré
        """
        try:
            template = self.env.get_template('team_documentation.md')
        except jinja2.exceptions.TemplateNotFound:
            # Utiliser un template par défaut
            template_str = """# Équipe: {{name}}

## Vue d'ensemble
- **Responsabilité**: {{responsibility}}
- **Membres**: {{member_count}} agents

## Description
{{description}}

## Agents
{% for agent in agents %}
### {{agent.name}}
- **Rôle**: {{agent.role}}
- **Statut**: {{agent.status}}
{% if agent.description %}
- **Description**: {{agent.description}}
{% endif %}
{% endfor %}

## Interactions
{% for interaction in interactions %}
- **{{interaction.with}}**: {{interaction.description}}
{% endfor %}
"""
            template = jinja2.Template(template_str)
        
        # Générer le contenu Markdown
        markdown_content = template.render(**team_data)
        
        # Sauvegarder dans un fichier si demandé
        if output_file:
            full_path = os.path.join(self.output_dir, output_file)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
        
        return markdown_content
    
    def generate_development_journal(self, entries: List[Dict[str, Any]], 
                                    output_file: Optional[str] = None) -> str:
        """
        Génère un journal de développement à partir des entrées.
        
        Args:
            entries: Liste des entrées de journal
            output_file: Chemin du fichier de sortie (optionnel)
            
        Returns:
            Contenu Markdown généré
        """
        # Grouper les entrées par jour
        days = {}
        for entry in entries:
            timestamp = entry['timestamp']
            day = timestamp.split('T')[0]
            
            if day not in days:
                days[day] = []
            
            days[day].append(entry)
        
        # Trier les jours et les entrées dans chaque jour
        sorted_days = sorted(days.items(), reverse=True)
        for day, day_entries in sorted_days:
            days[day] = sorted(day_entries, key=lambda x: x['timestamp'])
        
        try:
            template = self.env.get_template('development_journal.md')
        except jinja2.exceptions.TemplateNotFound:
            # Utiliser un template par défaut
            template_str = """# Journal de Développement Akoben

{% for day, entries in days.items() %}
## {{day}}

{% for entry in entries %}
### {{entry.timestamp|date}}

{% if entry.type == 'session_start' %}
**Début de session**

{% elif entry.type == 'session_end' %}
**Fin de session**
- Durée: {{entry.duration_seconds|format_duration}}
{% if entry.ideas_count %}
- Idées enregistrées: {{entry.ideas_count}}
{% endif %}

{% elif entry.type == 'idea' %}
**Nouvelle idée**: {{entry.idea.title}}
- Composant: {{entry.idea.component}}
- Priorité: {{entry.idea.priority}}
- Type: {{entry.idea.type}}

{% if entry.idea.description %}
#### Description
{{entry.idea.description}}
{% endif %}

{% elif entry.type == 'analysis' %}
**Analyse de composant**: {{entry.component_path}}
- Type: {{entry.component_type}}
- Classes: {{entry.summary.classes}}
- Fonctions: {{entry.summary.functions}}

{% elif entry.type == 'documentation_update' %}
**Mise à jour de la documentation**
- Composants analysés: {{entry.summary.components_analyzed}}
- Fichiers analysés: {{entry.summary.files_analyzed}}
- Classes documentées: {{entry.summary.classes_documented}}
- Fonctions documentées: {{entry.summary.functions_documented}}

{% elif entry.type == 'anansi_update' %}
**Mise à jour par Anansi**
- Composant: {{entry.component}}
- Type de mise à jour: {{entry.update_type}}

{% else %}
**{{entry.type}}**
{% endif %}

{% endfor %}
{% endfor %}
"""
            template = jinja2.Template(template_str)
            
            # Ajouter un filtre pour formater les durées
            self.env.filters['format_duration'] = lambda seconds: str(datetime.timedelta(seconds=seconds)).split('.')[0]
        
        # Générer le contenu Markdown
        markdown_content = template.render(days=dict(sorted_days))
        
        # Sauvegarder dans un fichier si demandé
        if output_file:
            full_path = os.path.join(self.output_dir, output_file)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
        
        return markdown_content
    
    def generate_project_overview(self, project_data: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """
        Génère une vue d'ensemble du projet.
        
        Args:
            project_data: Données du projet
            output_file: Chemin du fichier de sortie (optionnel)
            
        Returns:
            Contenu Markdown généré
        """
        try:
            template = self.env.get_template('project_overview.md')
        except jinja2.exceptions.TemplateNotFound:
            # Utiliser un template par défaut
            template_str = """# Vue d'ensemble du projet Akoben

## État du projet
- **Date de mise à jour**: {{last_updated|date}}
- **Version**: {{version}}
- **État général**: {{status}}

## Structure du projet
- **Nombre total de composants**: {{component_count}}
- **Nombre d'agents**: {{agent_count}}
- **Nombre d'équipes**: {{team_count}}

## Équipes
{% for team in teams %}
### {{team.name}}
- **Responsabilité**: {{team.responsibility}}
- **Membres**: {{team.member_count}} agents
- **État**: {{team.status}}
{% endfor %}

## Statistiques de code
- **Lignes de code totales**: {{code_stats.total_lines}}
- **Nombre de fichiers Python**: {{code_stats.python_files}}
- **Nombre de classes**: {{code_stats.class_count}}
- **Nombre de fonctions**: {{code_stats.function_count}}

## Dernières activités
{% for activity in recent_activities %}
- **{{activity.timestamp|date}}**: {{activity.description}}
{% endfor %}

## Prochaines étapes
{% for step in next_steps %}
- {{step}}
{% endfor %}
"""
            template = jinja2.Template(template_str)
        
        # Générer le contenu Markdown
        markdown_content = template.render(**project_data)
        
        # Sauvegarder dans un fichier si demandé
        if output_file:
            full_path = os.path.join(self.output_dir, output_file)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
        
        return markdown_content


# Test simple du module si exécuté directement
if __name__ == "__main__":
    # Créer une instance du générateur
    generator = DocumentationGenerator()
    
    # Tester la génération d'une fiche de composant
    component_data = {
        "name": "DocumentationGenerator",
        "type": "Class",
        "path": "src/agents/documentation/documentation_generator.py",
        "last_analyzed": datetime.datetime.now().isoformat(),
        "docstring": "Générateur de documentation pour Akoben.",
        "classes": ["DocumentationGenerator"],
        "functions": [
            "generate_component_card",
            "generate_team_documentation",
            "generate_development_journal",
            "generate_project_overview"
        ],
        "line_count": 200,
        "metrics": {
            "class_count": 1,
            "function_count": 4,
            "documentation_ratio": 0.85
        },
        "dependencies": [
            {"name": "os", "type": "stdlib"},
            {"name": "jinja2", "type": "external"}
        ],
        "last_modified": [
            {"timestamp": datetime.datetime.now().isoformat(), "type": "Création"}
        ]
    }
    
    # Générer et afficher la fiche
    markdown = generator.generate_component_card(component_data)
    print("Fiche de composant générée:")
    print(markdown)
    
    # Générer un fichier
    try:
        generator.generate_component_card(component_data, "components/documentation_generator.md")
        print("\nFiche sauvegardée dans docs/generated/components/documentation_generator.md")
    except Exception as e:
        print(f"\nErreur lors de la sauvegarde: {str(e)}")