"""
Anansi - Le cerveau central du système Akoben
"""

import os
import json
import requests
import logging
from datetime import datetime
from pprint import pprint

# Importer les agents
from src.agents.market_analyzer import MarketAnalyzer
from src.agents.strategy_developer import StrategyDeveloper
from src.agents.vision.kora import Kora
from src.agents.execution.mt5_connector import MT5FileConnector
from src.anansi.prompts.qwen_prompts import SYSTEM_PROMPT
from src.anansi.cognitive.memory import Memory
from src.anansi.cognitive.reasoning import Reasoning
from src.anansi.cognitive.decision import Decision
from src.anansi.cognitive.learning import Learning
from src.anansi.agent_manager import AgentManager  # Importer le nouveau gestionnaire d'agents

class Anansi:
    """
    Anansi - Le cerveau central du système Akoben
    """
    def __init__(self, config=None):
        self.config = config or {}
        self.conversation_history = []
        self.ollama_base_url = "http://localhost:11434/api"
        
        # Modèles par défaut
        self.general_model = self.config.get("general_model", "qwen:14b")
        self.code_model = self.config.get("code_model", "deepseek-coder")
        
        # Nouveaux modules cognitifs adaptés de Goose
        self.memory = Memory(self.config.get("memory", {}))
        self.reasoning = Reasoning(
            self.config.get("reasoning", {}),
            llm_caller=lambda prompt: self.call_llm(prompt)
        )
        self.learning = Learning(
            self.config.get("learning", {}),
            llm_caller=lambda prompt: self.call_llm(prompt)
        )
        self.decision = Decision(
            self.config.get("decision", {}),
            llm_caller=lambda prompt: self.call_llm(prompt)
        )
        
        # Nouveau gestionnaire d'agents
        self.agent_manager = AgentManager(self)
        
        # Initialisation des agents de base
        self.agents = self._initialize_agents()
        
        # Initialisation des équipes et workflows
        self._initialize_teams()
        self._initialize_workflows()
        
        print(f"Anansi initialisé avec modèle général: {self.general_model}, modèle code: {self.code_model}")
        print(f"Agents initialisés: {', '.join(self.agents.keys())}")
    
    def process_cognitive_cycle(self, inputs, context=None):
        """
        Exécute un cycle cognitif complet: mémoire, raisonnement, 
        apprentissage et décision.
        """
        context = context or {}
        
        # Récupération des souvenirs pertinents
        relevant_memories = self.memory.retrieve(inputs, context)
        
        # Raisonnement basé sur les inputs et les souvenirs
        reasoning_results = self.reasoning.analyze(
            inputs, 
            relevant_memories, 
            context
        )
        
        # Prise de décision
        decision = self.decision.decide(reasoning_results, context)
        
        # Apprentissage à partir de cette nouvelle expérience
        self.learning.update(inputs, reasoning_results, decision, context)
        
        # Stockage de cette nouvelle expérience
        self.memory.store(inputs, "episodic")
        
        return {
            "memories": relevant_memories,
            "reasoning": reasoning_results,
            "decision": decision
        }

    def _initialize_agents(self):
        """
        Initialise les agents spécialisés
        """
        agents = {}
        
        # Créer les agents avec les fonctions d'appel au LLM appropriées
        agents["market_analyzer"] = MarketAnalyzer(
            config=self.config,
            llm_caller=lambda prompt: self.call_llm(prompt, self.general_model)
        )
        
        agents["strategy_developer"] = StrategyDeveloper(
            config=self.config,
            llm_caller=lambda prompt: self.call_llm(prompt, self.general_model),
            code_llm_caller=lambda prompt: self.call_llm(prompt, self.code_model)
        )
        
        agents["vision_kora"] = Kora(
            config=self.config,
            llm_caller=lambda prompt: self.call_llm(prompt, self.general_model)
        )

        agents["mt5_connector"] = MT5FileConnector(
            config=self.config.get("mt5_config", {}),
            llm_caller=lambda prompt: self.call_llm(prompt, self.general_model)
        )
        
        # Enregistrer également ces agents dans le gestionnaire d'agents
        for name, agent in agents.items():
            self.agent_manager.register_agent(agent)

        return agents
    
    def _initialize_teams(self):
        """
        Initialise les équipes d'agents
        """
        # Équipe Ubuntu (support)
        self.agent_manager.create_team("ubuntu", ["mt5_connector"])
        
        # Équipe Djeli (vision)
        self.agent_manager.create_team("djeli", ["vision_kora"])
        
        # Équipe Chaka (trading)
        self.agent_manager.create_team("chaka", ["market_analyzer", "strategy_developer"])
        
        print(f"Équipes d'agents créées: {', '.join(self.agent_manager.agent_teams.keys())}")
    
    def _initialize_workflows(self):
        """
        Initialise les workflows standard
        """
        # Workflow d'analyse de marché
        self.agent_manager.define_workflow(
            "market_analysis_flow",
            [
                {"agent": "market_analyzer", "action": "analyze_market", "params": {}}
            ]
        )
        
        # Workflow d'exécution d'ordre de trading
        self.agent_manager.define_workflow(
            "execute_trade_order",
            [
                {"agent": "mt5_connector", "action": "connect", "params": {}},
                {"agent": "mt5_connector", "action": "place_order", "params": {}}
            ]
        )
        
        print(f"Workflows définis: {', '.join(self.agent_manager.workflows.keys())}")
    
    def call_llm(self, prompt, model=None):
        """
        Appelle un modèle LLM via Ollama
        """
        model = model or self.general_model
        try:
            payload = {"model": model, "prompt": prompt, "stream": False}
            
            # Ajouter le prompt système pour Qwen
            if "qwen" in model.lower():
                payload["system"] = SYSTEM_PROMPT
                
            response = requests.post(
                f"{self.ollama_base_url}/generate",
                json=payload
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            pprint(f"Erreur lors de l'appel au LLM: {str(e)}")
            return "Erreur de communication avec le LLM"
    
    def process_instruction(self, instruction):
        """
        Traite une instruction utilisateur
        """
        # Enregistrer l'instruction dans l'historique
        self.conversation_history.append({
            "role": "user",
            "content": instruction,
            "timestamp": datetime.now().isoformat()
        })
        
        # Analyser l'instruction
        task_type = self._analyze_instruction(instruction)
        
        # Traiter selon le type de tâche
        if task_type == "market_analysis":
            response = self._handle_market_analysis(instruction)
        elif task_type == "strategy_development":
            response = self._handle_strategy_development(instruction)
        elif task_type == "visual_analysis":
             # Utiliser un chemin absolu pour l'image
            demo_image_path = os.path.join(os.path.expanduser("~"), "akoben-clean/data/images/2.png")
            response = self._handle_visual_analysis(instruction, image_path=demo_image_path)
        elif task_type == "trading_execution":
            response = self._handle_trading_execution(instruction)
        elif task_type == "general_question":
            response = self._handle_general_question(instruction)
        else:
            response = self._handle_unknown_instruction(instruction)
        
        # Enregistrer la réponse dans l'historique
        self.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return response
    
    def _analyze_instruction(self, instruction):
        """
        Analyse le type d'instruction reçue
        """
        prompt = f"""
        Analyse cette instruction et détermine à quelle catégorie elle appartient:
        - market_analysis: Analyse du marché, des graphiques, des tendances
        - strategy_development: Développement ou optimisation de stratégies de trading
        - visual_analysis: Analyse visuelle d'un graphique ou d'une image
        - trading_execution: Exécution d'ordres de trading ou gestion de positions
        - general_question: Question générale sur le trading ou le système
        - unknown: Autre type d'instruction
        
        Instruction: "{instruction}"
        
        Réponds uniquement avec la catégorie, sans autre texte.
        """
        
        response = self.call_llm(prompt)
        return response.strip().lower()
    
    def _extract_parameters(self, instruction, task_type):
        """
        Extrait les paramètres pertinents de l'instruction
        """
        if task_type == "market_analysis":
            prompt = f"""
            Extrais les paramètres suivants de cette instruction d'analyse de marché:
            - instrument: Le nom de l'instrument financier à analyser (par défaut: US30)
            - timeframe: La temporalité à analyser (M1, M5, M15, H1, H4, D1, etc., par défaut: M1)
            
            Instruction: "{instruction}"
            
            Réponds au format JSON uniquement, comme ceci:
            {{
                "instrument": "nom_de_instrument",
                "timeframe": "temporalité"
            }}
            """
        elif task_type == "strategy_development":
            prompt = f"""
            Extrais les paramètres suivants de cette instruction de développement de stratégie:
            - strategy_type: Le type de stratégie demandée (mean_reversion, trend_following, breakout, etc.)
            - instrument: L'instrument financier cible (par défaut: US30)
            
            Instruction: "{instruction}"
            
            Réponds au format JSON uniquement, comme ceci:
            {{
                "strategy_type": "type_de_stratégie",
                "instrument": "nom_de_instrument"
            }}
            """
        elif task_type == "trading_execution":
            prompt = f"""
            Extrais les paramètres suivants de cette instruction d'exécution de trading:
            - action: L'action à effectuer (buy, sell, close, status)
            - instrument: L'instrument financier concerné (par défaut: US30)
            - volume: Le volume de l'ordre (par défaut: 0.01)
            - price: Le prix d'entrée si spécifié (0 pour ordre au marché)
            - sl: Le niveau de stop loss si spécifié (0 pour aucun)
            - tp: Le niveau de take profit si spécifié (0 pour aucun)
            
            Instruction: "{instruction}"
            
            Réponds au format JSON uniquement, comme ceci:
            {{
                "action": "action_à_effectuer",
                "instrument": "nom_de_instrument",
                "volume": volume_numérique,
                "price": prix_numérique,
                "sl": stop_loss_numérique,
                "tp": take_profit_numérique
            }}
            """
        else:
            return {}
        
        response = self.call_llm(prompt)
        try:
            # Tenter de parser la réponse JSON
            params = json.loads(response)
            return params
        except:
            # En cas d'échec, retourner des valeurs par défaut
            if task_type == "market_analysis":
                return {"instrument": "US30", "timeframe": "M1"}
            elif task_type == "strategy_development":
                return {"strategy_type": "mean_reversion", "instrument": "US30"}
            elif task_type == "trading_execution":
                return {"action": "status", "instrument": "US30", "volume": 0.01, "price": 0, "sl": 0, "tp": 0}
            return {}
    
    def _handle_market_analysis(self, instruction):
        """
        Traite une demande d'analyse de marché
        """
        # Extraire les paramètres
        params = self._extract_parameters(instruction, "market_analysis")
        
        # Utiliser l'agent d'analyse de marché
        result = self.agents["market_analyzer"].analyze_market(
            instrument=params.get("instrument", "US30"),
            timeframe=params.get("timeframe", "M1")
        )
        
        return result["analysis"]
    
    def _handle_strategy_development(self, instruction):
        """
        Traite une demande de développement de stratégie
        """
        # Extraire les paramètres
        params = self._extract_parameters(instruction, "strategy_development")
        
        # Utiliser l'agent de développement de stratégie
        result = self.agents["strategy_developer"].develop_strategy(
            strategy_type=params.get("strategy_type", "mean_reversion"),
            instrument=params.get("instrument", "US30")
        )
        
        return f"""
# Description de la stratégie
{result['strategy_description']}

# Code Python pour implémentation
```python
{result['strategy_code']}
```
"""
    
    def _handle_visual_analysis(self, instruction, image_path=None):
        """
        Traite une demande d'analyse visuelle
        """
        if "vision_kora" not in self.agents:
            return "L'agent de vision n'est pas disponible."
        
        if not image_path:
            return "Aucune image fournie pour l'analyse. Veuillez spécifier un chemin d'image."
        
        # Utiliser l'agent Kora pour analyser l'image
        result = self.agents["vision_kora"].analyze_chart(image_path=image_path)
        
        if "error" in result:
            return f"Erreur lors de l'analyse de l'image: {result['error']}"
        
        # Créer un rapport d'analyse combinant les détections et l'analyse
        detections_summary = self._summarize_detections(result["detections"])
        
        report = f"""
# Analyse du Graphique de Trading

## Informations sur l'Image
- Source: {result['image_info']['source']}
- Dimensions: {result['image_info']['size'][0]}x{result['image_info']['size'][1]}
- Format: {result['image_info']['format']}

## Éléments Détectés
{detections_summary}

## Analyse
{result['analysis']}
"""
        
        return report

    def _handle_trading_execution(self, instruction):
        """
        Traite une demande d'exécution de trading
        """
        if "mt5_connector" not in self.agents:
            return "L'agent de connexion MT5 n'est pas disponible."
        
        # Extraction des paramètres
        params = self._extract_parameters(instruction, "trading_execution")
        
        action = params.get("action", "status").lower()
        instrument = params.get("instrument", "US30")
        volume = params.get("volume", 0.01)
        price = params.get("price", 0)
        sl = params.get("sl", 0)
        tp = params.get("tp", 0)
        
        # Réinitialiser le fichier de réponse pour garantir une communication propre
        try:
            mt5_path = os.path.expanduser("~/.wine/drive_c/Program Files/MetaTrader 5/MQL5/Files")
            response_file = os.path.join(mt5_path, "responses.txt")
            with open(response_file, 'w', encoding='latin-1') as f:
                f.write("READY")
        except Exception as e:
            print(f"Avertissement: Impossible de réinitialiser le fichier de réponse: {e}")
        
        # Exécuter l'action demandée
        if action == "status":
            # Vérifier la connexion MT5
            if not self.agents["mt5_connector"].connect():
                return "Impossible de se connecter à MetaTrader 5. Veuillez vérifier l'installation."
            
            # Récupérer les informations de compte
            account_info = self.agents["mt5_connector"].get_account_info()
            if account_info:
                account_details = f"""
# Informations de Compte MT5
- Compte: {account_info.get('login')}
- Serveur: {account_info.get('server')}
- Balance: {account_info.get('balance')} {account_info.get('currency')}
- Équité: {account_info.get('equity')} {account_info.get('currency')}
- Margin libre: {account_info.get('free_margin')} {account_info.get('currency')}
- Niveau de margin: {account_info.get('margin_level')}%
- Levier: 1:{account_info.get('leverage')}
"""
            else:
                account_details = "Impossible de récupérer les informations du compte."
            
            # Récupérer les positions ouvertes
            positions = self.agents["mt5_connector"].get_positions()
            positions_details = "## Positions Ouvertes\n"
            if positions and len(positions) > 0:
                for pos in positions:
                    positions_details += f"- {pos['symbol']} {pos['type']} {pos['volume']} lot(s) @ {pos['open_price']} (Profit: {pos['profit']})\n"
            else:
                positions_details += "Aucune position ouverte.\n"
            
            return f"{account_details}\n{positions_details}"
            
        elif action == "buy":
            # Récupérer le prix actuel pour le calcul des SL/TP relatifs si nécessaire
            current_price = None
            if sl != 0 or tp != 0:
                price_data = self.agents["mt5_connector"].get_current_price(instrument)
                if price_data:
                    current_price = price_data.get("ask")
            
            # Convertir SL/TP relatifs en absolus si nécessaire
            sl_absolute = sl
            tp_absolute = tp
            if current_price and sl < 0:  # SL relatif en points négatifs
                sl_absolute = current_price + sl * 0.1  # Convertir points en prix
            if current_price and tp > 0:  # TP relatif en points positifs
                tp_absolute = current_price + tp * 0.1  # Convertir points en prix
            
            result = self.agents["mt5_connector"].place_order(
                symbol=instrument,
                order_type="BUY",
                volume=volume,
                price=price,
                sl=sl_absolute,
                tp=tp_absolute,
                comment="Akoben Trading System"
            )
            
            if result:
                return f"""
# Ordre d'achat placé avec succès
- Instrument: {instrument}
- Volume: {result.get('volume')} lot(s)
- Prix d'exécution: {result.get('price')}
- ID de l'ordre: {result.get('order_id')}
"""
            else:
                return "Échec de l'ordre d'achat. Veuillez vérifier les paramètres et réessayer."
                
        elif action == "sell":
            # Récupérer le prix actuel pour le calcul des SL/TP relatifs si nécessaire
            current_price = None
            if sl != 0 or tp != 0:
                price_data = self.agents["mt5_connector"].get_current_price(instrument)
                if price_data:
                    current_price = price_data.get("bid")
            
            # Convertir SL/TP relatifs en absolus si nécessaire
            sl_absolute = sl
            tp_absolute = tp
            if current_price and sl > 0:  # SL relatif en points positifs
                sl_absolute = current_price - sl * 0.1  # Convertir points en prix
            if current_price and tp < 0:  # TP relatif en points négatifs
                tp_absolute = current_price - abs(tp) * 0.1  # Convertir points en prix
            
            result = self.agents["mt5_connector"].place_order(
                symbol=instrument,
                order_type="SELL",
                volume=volume,
                price=price,
                sl=sl_absolute,
                tp=tp_absolute,
                comment="Akoben Trading System"
            )
            
            if result:
                return f"""
# Ordre de vente placé avec succès
- Instrument: {instrument}
- Volume: {result.get('volume')} lot(s)
- Prix d'exécution: {result.get('price')}
- ID de l'ordre: {result.get('order_id')}
"""
            else:
                return "Échec de l'ordre de vente. Veuillez vérifier les paramètres et réessayer."
                
        elif action == "close":
            if instrument.lower() == "all":
                success = self.agents["mt5_connector"].close_all_positions()
                if success:
                    return "Toutes les positions ont été fermées avec succès."
                else:
                    return "Échec de fermeture de certaines positions."
            else:
                success = self.agents["mt5_connector"].close_position(symbol=instrument)
                if success:
                    return f"Position {instrument} fermée avec succès."
                else:
                    return f"Échec de fermeture de la position {instrument}."
                    
        elif action == "price":
            # Action spéciale pour obtenir juste le prix actuel
            price_data = self.agents["mt5_connector"].get_current_price(instrument)
            if price_data:
                return f"""
# Prix Actuel de {instrument}
- Bid (Vente): {price_data.get('bid')}
- Ask (Achat): {price_data.get('ask')}
- Spread: {price_data.get('spread')}
- Timestamp: {price_data.get('time').strftime('%Y-%m-%d %H:%M:%S')}
"""
            else:
                return f"Impossible d'obtenir le prix actuel pour {instrument}."
                
        elif action == "performance":
            # Action pour obtenir les métriques de performance
            days = params.get("days", 30)  # Par défaut, 30 jours
            metrics = self.agents["mt5_connector"].calculate_performance_metrics(days, instrument if instrument != "all" else None)
            
            if metrics:
                return f"""
# Métriques de Performance ({days} jours)
- Total trades: {metrics.get('total_trades')}
- Trades gagnants: {metrics.get('winning_trades')}
- Trades perdants: {metrics.get('losing_trades')}
- Win rate: {metrics.get('win_rate')}%
- Profit factor: {metrics.get('profit_factor')}
- Profit total: {metrics.get('total_profit')}
- Profit moyen par trade: {metrics.get('average_trade')}
"""
            else:
                return f"Impossible d'obtenir les métriques de performance."
        
        elif action == "history":
            # Action pour obtenir l'historique des ordres
            days = params.get("days", 7)  # Par défaut, 7 jours
            history = self.agents["mt5_connector"].get_history_orders(days, instrument if instrument != "all" else None)
            
            if history and len(history) > 0:
                history_text = "# Historique des Ordres\n"
                for order in history:
                    history_text += f"- ID: {order.get('ticket')}, {order.get('symbol')} {order.get('type')}, Volume: {order.get('volume')}\n"
                return history_text
            else:
                return "Aucun ordre dans l'historique pour la période spécifiée."
        
        elif action == "size":
            # Action pour calculer la taille de position optimale
            stop_loss_pips = params.get("sl", 100)  # Par défaut, 100 pips
            risk_percent = params.get("risk", 1)  # Par défaut, 1% de risque
            
            size = self.agents["mt5_connector"].calculate_position_size(instrument, stop_loss_pips, risk_percent)
            
            if size is not None:
                return f"""
# Calcul de Taille de Position
- Instrument: {instrument}
- Stop Loss: {stop_loss_pips} pips
- Risque: {risk_percent}% du compte
- Taille recommandée: {size} lot(s)
"""
            else:
                return "Impossible de calculer la taille de position."
        else:
            return f"Action '{action}' non reconnue. Actions disponibles: status, buy, sell, close, price, performance, history, size."

    def _summarize_detections(self, detections):
        """
        Résume les détections en format texte
        """
        summary = ""
        
        if detections.get("candles"):
            summary += "### Bougies Japonaises\n"
            for candle in detections["candles"]:
                summary += f"- {candle['type'].capitalize()} (confiance: {candle['confidence']:.2f})\n"
            summary += "\n"
        
        if detections.get("indicators"):
            summary += "### Indicateurs Techniques\n"
            for indicator in detections["indicators"]:
                summary += f"- {indicator['type'].replace('_', ' ').capitalize()} (confiance: {indicator['confidence']:.2f})\n"
            summary += "\n"
        
        if detections.get("patterns"):
            summary += "### Patterns Détectés\n"
            for pattern in detections["patterns"]:
                summary += f"- {pattern['type'].replace('_', ' ').capitalize()} (confiance: {pattern['confidence']:.2f})\n"
            summary += "\n"
        
        return summary
    
    def _handle_general_question(self, instruction):
        """
        Traite une question générale
        """
        prompt = f"""
        En tant qu'assistant spécialisé en trading algorithmique, réponds à cette question:
        
        "{instruction}"
        
        Fournis une réponse claire et informative.
        """
        return self.call_llm(prompt)
    
    def _handle_unknown_instruction(self, instruction):
        """
        Traite une instruction non reconnue
        """
        return f"""
        Je ne suis pas sûr de comprendre cette instruction. Pourriez-vous la reformuler ou préciser si vous souhaitez:
        - Une analyse de marché
        - Le développement d'une stratégie de trading
        - Une analyse visuelle d'un graphique
        - Une exécution d'ordre de trading
        - Une réponse à une question générale sur le trading
        """
    
    def get_conversation_history(self):
        """
        Retourne l'historique de conversation
        """
        return self.conversation_history