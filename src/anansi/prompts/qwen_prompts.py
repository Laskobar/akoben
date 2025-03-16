"""
Prompts optimisés pour le modèle Qwen, utilisés par Anansi
"""

# Prompt système général pour Qwen
SYSTEM_PROMPT = """Tu es un assistant spécialisé dans l'analyse de trading, l'optimisation de stratégies et l'automatisation des marchés financiers.
Ton objectif est d'aider à développer le système Akoben, un système de trading autonome qui utilise l'intelligence artificielle.
Sois précis, analytique et direct dans tes réponses. Évite les longues introductions et conclusions inutiles.
Concentre-toi sur des réponses factuelles, techniques et pratiques."""

# Prompts spécifiques pour différentes tâches

# Analyse technique
TECHNICAL_ANALYSIS_PROMPT = """Analyse la configuration technique suivante sur le marché US30 :
{context}

Identifie :
1. La tendance principale (haussière, baissière, neutre)
2. Les niveaux de support et résistance clés
3. Les signaux des indicateurs techniques pertinents
4. Les configurations graphiques notables (patterns)
5. Les prochains mouvements probables

Format ta réponse de manière structurée et concise, en te concentrant uniquement sur les éléments les plus significatifs."""

# Analyse des risques
RISK_ANALYSIS_PROMPT = """Évalue les risques pour cette opportunité de trading :
{context}

Calcule et analyse :
1. Le risque en pourcentage du capital si le stop-loss est déclenché
2. Le ratio risque/récompense basé sur les niveaux d'entrée, stop et target
3. La probabilité approximative de succès basée sur les conditions de marché actuelles
4. La corrélation avec d'autres positions ouvertes et impact sur l'exposition globale
5. Recommandation finale (risque faible, moyen, élevé) avec justification

Sois méthodique et précis dans ton évaluation."""

# Prise de décision de trading
TRADING_DECISION_PROMPT = """Basé sur l'analyse technique et l'évaluation des risques suivantes :
Analyse technique : {technical_analysis}
Évaluation des risques : {risk_assessment}

Prends une décision de trading claire :
1. Action recommandée (acheter, vendre, attendre)
2. Point d'entrée précis
3. Stop-loss recommandé (niveau précis)
4. Objectif(s) de profit (niveaux précis)
5. Taille de position recommandée (% du capital)
6. Justification courte et pertinente de cette décision

Assure-toi que ta décision est cohérente avec les règles de gestion des risques (max 2% du capital par trade)."""

# Génération de code pour stratégie
CODE_GENERATION_PROMPT = """Génère le code Python pour implémenter la stratégie de trading suivante :
{strategy_description}

Le code doit :
1. Être modulaire et bien documenté
2. Inclure une fonction principale clear_entry_conditions() qui vérifie les conditions d'entrée
3. Inclure une fonction calculate_position_size() pour gérer le risque
4. Utiliser le connecteur MT5 d'Akoben pour l'exécution
5. Inclure une gestion appropriée des erreurs
6. Suivre les conventions de codage PEP 8

Génère uniquement le code sans explications supplémentaires."""

# Evaluation de performance
PERFORMANCE_EVALUATION_PROMPT = """Analyse les performances de trading suivantes :
{performance_data}

Fournis une évaluation détaillée incluant :
1. Métriques clés (win rate, profit factor, drawdown maximum, ratio de Sharpe)
2. Points forts et faiblesses identifiés
3. Biais et erreurs récurrentes
4. Opportunités d'amélioration spécifiques
5. Recommandations d'ajustements pour les prochains trades

Utilise une analyse quantitative rigoureuse et évite les généralités."""

# Optimisation de stratégie
STRATEGY_OPTIMIZATION_PROMPT = """Optimise la stratégie de trading suivante en fonction des résultats de backtest :
{strategy_details}
{backtest_results}

Propose des modifications spécifiques pour :
1. Améliorer les règles d'entrée et de sortie
2. Affiner les paramètres des indicateurs utilisés
3. Réduire le drawdown maximum
4. Augmenter le profit factor
5. Améliorer la robustesse de la stratégie face à différentes conditions de marché

Justifie chaque suggestion d'optimisation avec des données précises."""

# Aide à retrouver des fichiers et à comprendre le code existant
CODE_UNDERSTANDING_PROMPT = """Examine le code suivant d'Akoben :
{code_snippet}

Explique clairement :
1. La fonction principale de ce module
2. Les classes et méthodes clés et leurs interactions
3. Le flux de données et la logique métier
4. Les dépendances avec d'autres composants d'Akoben
5. Suggestions d'amélioration potentielles pour ce code

Fournis une analyse technique détaillée qui aiderait un développeur à comprendre et modifier ce code."""

# Integration Goose - pour les futures modifications
COGNITIVE_CYCLE_PROMPT = """Exécute un cycle cognitif complet pour ce problème de trading :
{input_situation}

Ton analyse doit suivre ces étapes :
1. MÉMOIRE : Rappelle-toi des situations similaires et des connaissances pertinentes
2. PERCEPTION : Identifie les éléments clés présents dans la situation actuelle
3. RAISONNEMENT : Analyse logique des causes, effets et implications
4. DÉCISION : Choix d'action optimal basé sur l'analyse précédente
5. APPRENTISSAGE : Points à retenir pour améliorer les futures décisions

Structure rigoureusement ta réponse selon ces 5 étapes, en utilisant des titres clairs pour chaque section."""
