# Composant: {{name}}

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
- **Ratio de documentation**: {{metrics.documentation_ratio|percentage}}
{% endif %}

## Historique des modifications
{% if last_modified %}
{% for modification in last_modified %}
- **{{modification.timestamp}}**: {{modification.type}}
{% endfor %}
{% else %}
*Aucune modification enregistrée*
{% endif %}