akoben-clean/
├── data/
│   └── images/          # Images pour l'analyse visuelle
├── src/
│   ├── agents/
│   │   ├── vision/      # Équipe Djeli - Agents visuels
│   │   │   ├── __init__.py
│   │   │   └── kora.py  # Agent de détection visuelle
│   │   ├── execution/   # Équipe Ubuntu - Agents d'exécution
│   │   │   ├── __init__.py
│   │   │   └── mt5_connector.py  # Agent Fihavanana - Exécution MT5
│   │   ├── __init__.py
│   │   ├── market_analyzer.py    # Analyse de marché
│   │   └── strategy_developer.py # Développement de stratégies
│   ├── anansi/          # Cerveau central
│   │   ├── __init__.py
│   │   └── core.py      # Orchestration des agents
│   ├── strategies/      # Stratégies générées
│   ├── tools/           # Outils divers
│   ├── ui/              # Interface utilisateur
│   │   ├── __init__.py
│   │   └── cli.py       # Interface ligne de commande
│   └── __init__.py
├── venv/                # Environnement virtuel Python
├── akoben.py            # Point d'entrée principal
├── create_test_image.py # Création d'images de test
├── direct_approach.py   # Approche directe (sans CrewAI)
└── mt5setup.exe         # Installateur MetaTrader5