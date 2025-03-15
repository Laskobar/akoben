# Système de Trading Autonome "Akoben" avec Architecture Hybride - Document Mis à Jour

## Introduction

"Akoben" (cor d'appel Akan, symbole de vigilance, d'éveil et de préparation au combat) est un système de trading algorithmique entièrement autonome, open source et hautement personnalisé. Il est conçu pour trader l'instrument US30 sur la plateforme MT5, en utilisant un compte démo FTMO pour les phases initiales (paper trading). Le système repose sur une architecture modulaire et évolutive, pilotée par une approche hybride d'agents intelligents utilisant différents modèles de langage (LLMs).

## Objectifs du Projet

- **Automatisation Complète**: Akoben prendra des décisions de trading de manière autonome, 24h/24 et 7j/7, sans intervention humaine constante.

- **Performance**: Le système vise des performances supérieures à celles d'un trader humain, en termes de précision des signaux, de win rate, de profit factor, et de drawdown maximum.

- **Apprentissage Continu**: Akoben s'améliorera en continu, grâce à l'analyse de ses propres performances, à l'intégration de nouvelles données, et à vos feedbacks.

- **Transparence**: Vous comprendrez pourquoi Akoben prend chaque décision, et vous pourrez intervenir à tout moment pour modifier ou corriger son comportement.

- **Personnalisation**: Le système sera adapté à votre style de trading spécifique, à vos préférences en matière de risque, et à vos règles de trading.

- **Maîtrise des Coûts**: Akoben est basé sur des technologies open source, et il fonctionnera sur votre propre infrastructure (VDS), sans dépendance à des API payantes.

- **Veille Technologique**: Le système intègrera un agent dédié à la veille, assurant une adaptation continue aux dernières avancées en IA.

## Philosophie de Conception

- **Modularité Maximale**: Chaque fonction du système (analyse visuelle, prise de décision, exécution, etc.) est assurée par un agent intelligent spécialisé. Ces agents sont indépendants, mais collaborent au sein d'équipes pour accomplir des tâches complexes.

- **Architecture Hybride**: Le système utilise une combinaison de modèles de langage optimisés pour différentes tâches. Actuellement, Llama3 est utilisé pour les tâches de raisonnement général, tandis que DeepSeek Coder est spécialisé pour le code et les analyses techniques. Une migration prévue vers Qwen est envisagée dans les prochaines phases.

- **Approche Itérative et Incrémentale**: Le système est développé par petites étapes, avec des tests et des ajustements continus. Vous serez impliqué à chaque étape du processus.

- **Implémentation Progressive**: Le développement commence par une base fonctionnelle simple avec des appels API directs, puis évolue vers une architecture plus sophistiquée pour l'orchestration des agents.

## Spécifications Techniques (VDS)

Le système est conçu pour fonctionner sur votre infrastructure existante:

- CPU: 6 cœurs
- RAM: 24 Go
- Stockage: 180 Go
- OS: Linux (Ubuntu Server recommandé)
- Localisation: Europe (EU)

## Architecture Technique Détaillée

### Cerveau Central: "Anansi" (Orchestrateur + LLMs Hybrides)

Anansi (araignée rusée de la mythologie Akan, symbole d'intelligence, de créativité et de sagesse) est le cœur du système.

**Rôle**:

1. **Orchestration des Agents**:
   - Définir les agents (leurs rôles, leurs compétences, leurs outils)
   - Créer les équipes d'agents
   - Configurer les workflows (séquences d'actions)
   - Gérer la communication et la collaboration entre les agents

2. **Prompt Manager Avancé**:
   - Analyser vos instructions (en langage naturel)
   - Décomposer les tâches complexes en sous-tâches plus simples
   - Attribuer ces sous-tâches aux agents appropriés
   - Adapter dynamiquement le workflow en fonction du contexte et des résultats intermédiaires
   - Gérer le contexte multi-modal (texte + images)

3. **Interface Conversationnelle**:
   - Permettre d'interagir avec le système en langage naturel
   - Donner des instructions
   - Poser des questions
   - Demander des explications
   - Fournir des feedbacks
   - Modifier les paramètres du système

4. **Génération et Auto-Correction de Code**:
   - Générer du code Python (pour les agents, les scripts d'automatisation, etc.)
   - Analyser le code existant (pour identifier les erreurs, les optimisations possibles)
   - Proposer et appliquer des corrections (après validation humaine)

5. **Synthèse des Connaissances**:
   - Générer des rapports, des analyses, et des résumés
   - Tenir informé des performances du système et de ses décisions

**Implémentation Technique**:

- **Architecture Hybride de LLMs**:
  - **Llama3**: Actuellement utilisé pour le raisonnement général, la coordination et les interactions en langage naturel
  - **DeepSeek Coder (7B)**: Pour les tâches spécialisées en programmation et l'analyse technique
  - **Qwen 1.5 (14B)**: Prévu pour remplacer Llama3 dans une phase ultérieure

- **Infrastructure**:
  - Ollama: Déploiement et gestion des LLMs en local avec API REST
  - Interface Utilisateur: Développée avec Streamlit ou Gradio

### Équipe de Vision "Djeli" (Agents Spécialisés)

Djeli (ou Griot): Gardien de la tradition orale, historien, conteur et conseiller en Afrique de l'Ouest.

**Rôle**: Analyser en détail et en temps réel les graphiques US30 M1 de TradingView.

**Agents**:

1. **"Kora" (Scout)**:
   - **Fonction**: Détection rapide des éléments visuels clés (bougies, indicateurs, débuts de patterns)
   - **Technologie**: YOLOv8-small (optimisé avec ONNX Runtime)
   - **Sortie**: Coordonnées des éléments détectés, type d'élément, niveau de confiance

2. **"Balafon" (Analyst)**:
   - **Fonction**: Analyse détaillée des zones et éléments signalés (patterns chartistes, indicateurs complexes)
   - **Technologie**: Vision Transformer (ViT) compact fine-tuné
   - **Sortie**: Patterns confirmés, signaux d'achat/vente potentiels, niveau de confiance

3. **"Ngoni" (Data Extractor)**:
   - **Fonction**: Extraction des valeurs numériques précises (indicateurs, niveaux de prix)
   - **Technologie**: Tesseract OCR optimisé
   - **Sortie**: Valeurs numériques extraites, coordonnées des zones de texte

4. **"Sanza" (Research)**:
   - **Fonction**: Comparaison avec configurations historiques similaires
   - **Technologie**: Algorithmes de similarité de séries temporelles (DTW)
   - **Sortie**: Configurations historiques similaires, probabilités d'évolution

5. **"Djeli" (Vision Manager)**:
   - **Fonction**: Supervision et coordination de l'équipe de vision
   - **Technologie**: Llama3 LLM + code Python
   - **Sortie**: Synthèse des analyses, signaux validés

### Équipe de Trading "Chaka" (Agents Spécialisés)

Chaka: Roi et stratège militaire zoulou, symbole de puissance, de discipline et de leadership.

**Rôle**: Prendre les décisions de trading en fonction de l'analyse visuelle, des règles de trading et de la gestion du risque.

**Agents**:

1. **"Shaka" (Strategist)**:
   - **Fonction**: Élaboration de stratégies de trading complètes
   - **Technologie**: FinRL (algorithmes d'apprentissage par renforcement)
   - **Sortie**: Stratégie complète (point d'entrée, stop-loss, take-profit, taille de position)

2. **"Iklwa" (Risk Manager)**:
   - **Fonction**: Évaluation du risque des stratégies proposées
   - **Technologie**: Code Python + bibliothèques d'analyse financière
   - **Sortie**: Risque évalué, taille de position ajustée si nécessaire

3. **"Knobkierrie" (Pattern Matcher)**:
   - **Fonction**: Identifier des stratégies prédéfinies correspondant à la configuration actuelle
   - **Technologie**: Base de données de stratégies, algorithmes de recherche
   - **Sortie**: Liste de stratégies pertinentes avec probabilités de succès

4. **"Assegai" (Decision Maker)**:
   - **Fonction**: Prendre la décision finale (acheter, vendre, attendre)
   - **Technologie**: Logique de décision basée sur règles et informations des autres agents
   - **Sortie**: Décision de trading avec justification détaillée

5. **"Chaka" (Trading Manager)**:
   - **Fonction**: Supervision et coordination de l'équipe de trading
   - **Technologie**: Llama3 LLM + code Python
   - **Sortie**: Décision finale validée, ordre transmis à l'exécuteur

### Équipe de Support "Ubuntu" (Agents Spécialisés)

Ubuntu: Philosophie africaine qui met l'accent sur l'humanité, la communauté et l'interconnexion.

**Rôle**: Assurer le bon fonctionnement du système, la gestion des données et l'amélioration continue.

**Agents**:

1. **"Fihavanana" (Executor)**:
   - **Fonction**: Exécution des ordres de trading
   - **Technologie**: Connecteur MT5 basé sur fichiers + code Python
   - **Sortie**: Confirmation d'exécution ou message d'erreur
   - **État actuel**: Implémenté et fonctionnel, utilisant un système d'identifiants uniques pour une communication fiable

2. **"Maat" (Mentor)**:
   - **Fonction**: Analyse des performances du système
   - **Technologie**: Bibliothèques d'analyse de données
   - **Sortie**: Rapports de performance, propositions d'amélioration

3. **"Endurance" (Sherlock)**:
   - **Fonction**: Debugging et maintenance proactive
   - **Technologie**: Outils de monitoring + code Python
   - **Sortie**: Diagnostics, propositions de solutions

4. **"Aya" (Historian)**:
   - **Fonction**: Gestion de la base de données
   - **Technologie**: PostgreSQL + code Python
   - **Sortie**: Données organisées et accessibles

5. **"Ubuntu" (Ops Manager)**:
   - **Fonction**: Supervision générale du système
   - **Technologie**: Outils de monitoring + interface utilisateur
   - **Sortie**: Alertes, rapports, interface de contrôle

### Agent de Veille Technologique "Sankofa"

Sankofa: Symbole Adinkra qui représente l'importance d'apprendre du passé pour construire l'avenir.

**Rôle**: Assurer que le système reste à la pointe de la technologie, surveiller les avancées en IA et trading algorithmique.

**Fonctionnement**:

1. **Collecte**:
   - Scraping des sources pertinentes (arXiv, GitHub, forums, blogs)
   - Filtrage initial des contenus

2. **Analyse**:
   - Évaluation de l'applicabilité au système Akoben
   - Estimation de l'impact potentiel
   - Priorisation des suggestions

3. **Proposition**:
   - Génération d'un rapport hebdomadaire
   - Documentation détaillée
   - Proposition de code de preuve de concept

4. **Intégration** (avec validation humaine):
   - Génération de code
   - Adaptation des workflows
   - Tests non intrusifs
   - Mesure de l'impact

## Infrastructure Technique Détaillée

### Base de Données: PostgreSQL

- Schéma optimisé pour le trading
- Partitionnement des tables
- Backups réguliers

### Stockage: Système de fichiers hiérarchique

- Organisation claire des fichiers
- Compression intelligente des données

### Communication:

1. **API REST Interne**:
   - Communication entre agents
   - Communication avec le cerveau central
   - Communication avec l'interface utilisateur

2. **Redis**:
   - Communication temps réel
   - Publication/souscription à des événements

3. **Communication MT5**:
   - **Méthode actuelle**: Communication via fichiers partagés avec système d'ID unique
   - **Avantages**: Simplicité, fiabilité, pas de dépendances externes
   - **Alternative possible**: ZeroMQ (si une communication en temps réel plus rapide devient nécessaire)

### Monitoring:

- Prometheus: Collecte des métriques
- Grafana: Dashboards interactifs
- OpenTelemetry: Traçage distribué

### Sécurité:

- HashiCorp Vault (optionnel): Gestion sécurisée des secrets

## Intégration avec MetaTrader 5

### Solution actuelle: Communication par fichiers

Akoben utilise actuellement une architecture de communication par fichiers partagés:

1. **Côté MT5 (sous Wine)**:
   - EA MQL5 implémentant un serveur de fichiers
   - Traitement des requêtes avec système d'ID unique
   - Lecture et écriture dans des fichiers partagés

2. **Côté Python (Akoben)**:
   - Classe MT5FileConnector pour la communication
   - Génération et vérification des IDs de requêtes
   - Interface abstraite masquant les détails de communication

Cette architecture a été choisie pour sa simplicité et sa fiabilité, et permet à Akoben de fonctionner entièrement sous Linux tout en interagissant avec MT5 sous Wine.

### État actuel de l'intégration MT5:

- **Fonctionnalités implémentées**:
  - Connexion et vérification de l'état
  - Récupération des prix actuels
  - Récupération des informations de compte
  - Placement d'ordres d'achat et de vente
  - Gestion des positions ouvertes
  - Calcul de taille de position optimale
  - Métriques de performance

- **Tests effectués**:
  - Vérification de la connexion
  - Récupération de prix
  - Ouverture de positions avec volume spécifié
  - Récupération de l'état du compte et des positions

- **Évolution future possible**:
  - Migration vers ZeroMQ si les performances de communication deviennent un facteur limitant

## Modèles LLM et Allocation des Ressources

L'architecture hybride d'Akoben utilise différents modèles optimisés pour leurs tâches spécifiques:

| Agent/Composant | Modèle LLM actuel | Modèle LLM prévu | Justification |
|-----------------|-------------------|------------------|---------------|
| Anansi (cerveau central) | Llama3 | Qwen 1.5 (14B) | Meilleures performances attendues, contexte plus long (32K tokens), bon multilinguisme |
| Agents d'analyse | Llama3 | Qwen 1.5 (14B) | Raisonnement avancé pour l'analyse de marché et la prise de décision |
| Génération de code | DeepSeek Coder (7B) | DeepSeek Coder (7B) | Spécialisé pour la génération de code, performances supérieures sur les tâches de programmation |
| Agents visuels | YOLOv8 + Llama3 | YOLOv8 + Qwen | Combinaison de détection d'objets et d'analyse d'image |

Cette architecture optimise le rapport performance/ressources pour chaque type de tâche.

| Composant | Allocation RAM | Cores CPU | Justification |
|-----------|---------------|-----------|---------------|
| Anansi (LLMs Hybrides) | 8 GB | 2 | LLMs plus performants nécessitant plus de RAM |
| Équipe Djeli (Vision) | 4 GB | 1.5 | YOLOv8 et ViT ont besoin de RAM pour les modèles et images |
| Équipe Chaka (Trading) | 3 GB | 1 | Analyse et décision de trading |
| Équipe Ubuntu (Support) | 3 GB | 0.5 | Agents de support et connecteur MT5 |
| Sankofa (Veille) | 0.5 GB | (partagé) | Fonctionne principalement en heures creuses |
| PostgreSQL + Redis | 3 GB | 0.5 | Base de données et système de messaging |
| OS & Services | 2 GB | 0.5 | Système d'exploitation et services de base |
| Réserve | 0.5 GB | | Marge de sécurité réduite pour accueillir les modèles plus grands |
| **TOTAL** | **24 GB** | **6** | |

## Prototype Anansi : Interface Conversationnelle

### Objectifs et fonctionnalités
Le prototype initial d'Anansi fournit une interface conversationnelle simple permettant :
- La réception et l'interprétation des instructions en langage naturel
- La décomposition des tâches complexes en sous-tâches assignables aux agents spécialisés
- La présentation des résultats et des analyses dans un format clair et structuré
- La conservation d'un historique des interactions pour référence et traçabilité

### Implémentation technique
L'implémentation repose sur une architecture Python modulaire :
```python
class Anansi:
    def __init__(self, config=None):
        self.config = config or {}
        self.conversation_history = []
        self.ollama_base_url = "http://localhost:11434/api"
        
        # Modèles par défaut
        self.general_model = self.config.get("general_model", "llama3")
        self.code_model = self.config.get("code_model", "deepseek-coder")
        
        # Initialisation des agents
        self.agents = self._initialize_agents()
        
    def process_instruction(self, instruction):
        """Traite une instruction utilisateur en langage naturel"""
        # Analyser l'intention de l'utilisateur
        task_type = self._analyze_instruction(instruction)
        
        # Traiter selon le type de tâche
        if task_type == "market_analysis":
            response = self._handle_market_analysis(instruction)
        elif task_type == "strategy_development":
            response = self._handle_strategy_development(instruction)
        elif task_type == "visual_analysis":
            response = self._handle_visual_analysis(instruction)
        elif task_type == "trading_execution":
            response = self._handle_trading_execution(instruction)
        elif task_type == "general_question":
            response = self._handle_general_question(instruction)
        else:
            response = self._handle_unknown_instruction(instruction)
        
        # Enregistrer l'interaction
        self._log_interaction(instruction, response)
        
        return response
```

### Interface utilisateur
L'interface utilisateur sera implémentée avec Streamlit pour offrir :
- Un champ de saisie pour les instructions
- Une zone d'affichage pour les réponses et résultats
- Des indicateurs visuels de l'état des agents et des tâches en cours
- Des options pour consulter l'historique et les analyses précédentes

## Approche de Développement des Stratégies de Trading

### Processus en deux phases

#### Phase 1 : Système complet pour développement et optimisation
Cette phase utilise l'infrastructure complète d'Akoben pour :
1. Analyser les marchés et identifier des opportunités
2. Développer et tester des stratégies variées
3. Optimiser les paramètres en fonction des performances historiques
4. Valider les stratégies sur des données de marché récentes

Les stratégies seront évaluées selon des métriques clés :
- Win rate
- Profit factor
- Drawdown maximal
- Ratio de Sharpe
- Cohérence des performances dans diverses conditions de marché

#### Phase 2 : Déploiement sous forme d'EAs en Python
Les stratégies validées seront implémentées sous forme de scripts Python autonomes :

**Extraction des règles de trading**
- Codification des logiques de décision identifiées par Akoben
- Documentation claire des conditions d'entrée/sortie

**Implémentation en Python**
- Utilisation de notre connecteur MT5FileConnector
- Structure modulaire pour faciliter les mises à jour

**Architecture des EAs Python**
- Classe de base pour les fonctionnalités communes
- Classes spécialisées pour chaque stratégie
- Gestion des risques intégrée

**Système de configuration externe**
- Paramètres stockés dans des fichiers configuration (YAML/JSON)
- Possibilité d'ajuster les paramètres sans modifier le code

**Logging et monitoring**
- Journalisation détaillée des décisions et exécutions
- Métriques de performance en temps réel

**Exemple de structure d'un EA Python**
```python
class BaseStrategy:
    def __init__(self, symbol, timeframe, risk_percent, config_file):
        self.symbol = symbol
        self.timeframe = timeframe
        self.risk_percent = risk_percent
        
        # Charger la configuration spécifique
        self.config = self.load_config(config_file)
        
        # Connexion à MT5
        self.mt5_connector = MT5FileConnector()
        self.mt5_connector.connect()
        
    def calculate_position_size(self, stop_loss_pips):
        """Calcule la taille de position basée sur le risque"""
        return self.mt5_connector.calculate_position_size(
            self.symbol, stop_loss_pips, self.risk_percent
        )
        
    def get_market_data(self):
        """Récupère les données de marché nécessaires"""
        # Obtenir les données historiques
        return self.mt5_connector.get_data(self.symbol, self.timeframe, 100)
        
    def analyze_market(self):
        """Analyse le marché selon la stratégie spécifique"""
        # À implémenter dans les sous-classes
        
    def should_enter_trade(self):
        """Détermine si les conditions d'entrée sont remplies"""
        # À implémenter dans les sous-classes
        
    def place_order(self, order_type, stop_loss, take_profit):
        """Place un ordre sur MT5"""
        self.mt5_connector.place_order(
            symbol=self.symbol,
            order_type=order_type,
            volume=self.calculate_position_size(stop_loss),
            sl=stop_loss,
            tp=take_profit
        )
        
    def run(self, interval=1):
        """Boucle principale de la stratégie"""
        while True:
            try:
                data = self.get_market_data()
                if self.should_enter_trade():
                    # Logique d'entrée
                    pass
                # Gestion des positions ouvertes
                time.sleep(interval)
            except Exception as e:
                self.logger.error(f"Erreur : {e}")
                time.sleep(10)  # Attente avant nouvelle tentative
```

**Stratégies spécifiques dérivées**
```python
class MeanReversionStrategy(BaseStrategy):
    def analyze_market(self):
        # Implémentation de l'analyse de marché spécifique
        
    def should_enter_trade(self):
        # Conditions spécifiques pour une entrée en mean-reversion
```

Cette approche en Python avec notre connecteur MT5FileConnector offre plusieurs avantages :
- Meilleure modularité et maintenance simplifiée
- Intégration facile avec d'autres outils d'analyse (pandas, numpy, etc.)
- Possibilité d'intégrer de l'apprentissage machine et des méthodes avancées
- Écosystème plus riche de bibliothèques et communauté plus active
- Facilité d'extension avec de nouvelles fonctionnalités

### Types de stratégies à développer

1. **Stratégies basées sur la moyenne mobile**
   - Croisements de moyennes mobiles (rapides/lentes)
   - Bandes de Bollinger et écarts à la moyenne
   - Configurations MACD optimisées pour US30

2. **Stratégies de retour à la moyenne (Mean-Reversion)**
   - Identification des conditions de surachat/survente
   - Mesures de volatilité et établissement de seuils dynamiques
   - Détection des divergences prix/indicateur

3. **Stratégies basées sur le momentum**
   - Détection des accélérations de prix
   - Suivi des tendances avec confirmation de volume
   - Entrées sur pullbacks dans les tendances fortes

4. **Stratégies basées sur les patterns de prix**
   - Reconnaissance de formations chartistes (triangles, drapeaux, etc.)
   - Configurations de chandeliers japonais significatives
   - Points de rupture structurels

5. **Stratégies hybrides adaptatives**
   - Alternance automatique entre approches selon les conditions de marché
   - Ajustement dynamique des paramètres selon la volatilité
   - Combinaison pondérée de signaux de différentes stratégies

### Infrastructure de test et validation

Un environnement complet de backtesting sera mis en place :
- Tests sur données historiques (minimum 3 ans)
- Validation croisée pour éviter le surajustement
- Tests de robustesse avec variations de paramètres
- Simulations Monte Carlo pour évaluer la distribution des résultats possibles

## Plan d'Implémentation Détaillé

Le plan d'implémentation est divisé en 3 phases principales:

### Phase 1: Base Fonctionnelle Directe (2-3 semaines) - COMPLÉTÉE

1. **Configuration initiale et approche directe**
   - Installation de l'environnement Linux et Ollama
   - Prototype initial d'Anansi avec appels API directs
   - Tests fonctionnels de base

2. **Anansi et premiers agents**
   - Développement de l'interface conversationnelle
   - Implémentation des agents de base (analyse, stratégie, vision)
   - Structure de communication simple

### Phase 2: Extension et Intégration (en cours, 3-4 semaines)

1. **Intégration MT5** - ✅ COMPLÉTÉE
   - Développement du connecteur MT5 basé sur fichiers
   - Implémentation du système d'ID unique pour une communication fiable
   - Tests de communication et d'exécution d'ordres
   - Vérification de la fonctionnalité d'ouverture de positions

2. **Migration vers modèles optimisés** - 🔄 EN ATTENTE
   - Transition de Llama3 vers Qwen pour le raisonnement général
   - Optimisation des prompts pour les nouveaux modèles
   - Tests de performances et ajustements

3. **Équipes Vision et Trading** - 🔄 EN COURS
   - Amélioration des agents d'analyse visuelle
   - Développement des agents de décision de trading
   - Intégration et tests des équipes

### Phase 3: Optimisation et Finalisation (3-4 semaines)

1. **Infrastructure de support**
   - Développement complet des agents de l'équipe Ubuntu
   - Configuration de PostgreSQL et Redis
   - Mise en place du monitoring (Prometheus, Grafana)

2. **Finalisation et lancement**
   - Tests complets end-to-end avec compte démo FTMO
   - Optimisation des performances et de la fiabilité
   - Développement de l'agent Sankofa (veille technologique)

## Plan d'implémentation court terme pour les stratégies

### Semaine 1-2 : Améliorations d'Anansi et Intégration MT5
- Amélioration de l'interface conversationnelle pour la détection des intentions
- Développement des scripts pour tester le connecteur MT5
- Exploration des données historiques via le connecteur MT5

### Semaine 3-4 : Stratégies Initiales
- Développement des premières stratégies de trading
- Création des outils de backtesting
- Tests initiaux sur données historiques

### Semaine 5-6 : Optimisation et Validation
- Optimisation des paramètres de stratégie
- Validation croisée des performances
- Préparation des premiers EAs Python pour tests en environnement démo

## Conclusion

Akoben est un système sophistiqué qui combine des technologies de pointe en IA et trading algorithmique. Son architecture modulaire, hybride et évolutive permet une adaptation continue aux conditions du marché et aux avancées technologiques. L'approche progressive d'implémentation garantit un développement robuste, avec des tests et validations à chaque étape.

Le développement récent du connecteur MT5 avec système d'ID est une avancée majeure qui permet maintenant l'exécution fiable d'ordres et la récupération de données de marché. Cette base solide constitue une étape cruciale vers l'automatisation complète du système.

Les prochaines étapes se concentreront sur l'amélioration des capacités de prise de décision, la mise en œuvre des stratégies de trading initiales et l'optimisation des performances du système. Le système final offrira une automatisation complète des décisions de trading sur US30, avec une transparence totale, des performances élevées et une adaptation constante à votre style de trading spécifique.
