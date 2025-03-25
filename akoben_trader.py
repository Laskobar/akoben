#!/usr/bin/env python3
"""
Akoben Trader - Script principal de trading automatisé
"""

import os
import time
import json
import logging
import argparse
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Importation des composants Akoben
from src.agents.execution.mt5_connector import MT5FileConnector
from src.agents.chaka.oba import Oba
from src.agents.chaka.iklwa import Iklwa  # Gestionnaire de risque à intégrer ultérieurement
from src.learning.imitation_learning_manager import ImitationLearningManager

# Configuration du logging
log_dir = "logs/trading"
os.makedirs(log_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Configurer le logger principal
logger = logging.getLogger("akoben_trader")
logger.setLevel(logging.INFO)

# Handler pour fichier
file_handler = logging.FileHandler(f"{log_dir}/akoben_trader_{timestamp}.log")
file_handler.setLevel(logging.INFO)

# Handler pour console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Ajouter les handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)

class AkobenTrader:
    """
    Système de trading automatisé Akoben
    """
    
    def __init__(self, config=None):
        """
        Initialise le système de trading Akoben
        
        Args:
            config: Configuration du système
        """
        self.config = config or {}
        self.logger = logging.getLogger("akoben_trader.main")
        
        # Paramètres de configuration
        self.instrument = self.config.get("instrument", "US30")
        self.timeframes = self.config.get("timeframes", ["M1", "M5", "M15"])
        self.main_timeframe = self.config.get("main_timeframe", "M1")
        self.check_interval = self.config.get("check_interval", 60)  # Secondes
        self.confidence_threshold = self.config.get("confidence_threshold", 0.7)
        self.max_daily_trades = self.config.get("max_daily_trades", 3)
        self.risk_per_trade = self.config.get("risk_per_trade", 1.0)  # Pourcentage
        self.max_daily_risk = self.config.get("max_daily_risk", 5.0)  # Pourcentage
        self.model_id = self.config.get("model_id", None)  # ID du modèle à utiliser
        self.dry_run = self.config.get("dry_run", True)  # Mode simulation par défaut
        
        # Chemins pour le stockage des données
        self.data_dir = Path(self.config.get("data_dir", "data/trading"))
        self.chart_captures_dir = self.data_dir / "chart_captures"
        self.predictions_dir = self.data_dir / "predictions"
        self.trades_dir = self.data_dir / "trades"
        self.stats_dir = self.data_dir / "stats"
        
        # Créer les répertoires
        for dir_path in [self.data_dir, self.chart_captures_dir, 
                        self.predictions_dir, self.trades_dir, self.stats_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # État interne
        self.start_time = datetime.now()
        self.last_check_time = None
        self.today_trades = []  # Trades effectués aujourd'hui
        self.daily_profit_loss = 0.0  # P&L journalier
        self.daily_drawdown = 0.0  # Drawdown journalier maximum
        self.active_trades = []  # Trades actuellement ouverts
        
        # Compteurs et statistiques
        self.stats = {
            "checks_performed": 0,
            "predictions_made": 0,
            "trades_executed": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "total_profit": 0.0,
            "total_loss": 0.0,
            "connection_errors": 0
        }
        
        self.logger.info(f"Akoben Trader initialisé pour l'instrument: {self.instrument}")
        self.logger.info(f"Timeframes surveillés: {', '.join(self.timeframes)}")
        self.logger.info(f"Seuil de confiance: {self.confidence_threshold:.2%}")
        
        # Initialiser les composants
        self._initialize_components()
    
    def _initialize_components(self):
        """
        Initialise les composants du système Akoben
        """
        self.logger.info("Initialisation des composants...")
        
        # Initialiser le connecteur MT5
        try:
            self.mt5 = MT5FileConnector()
            self.logger.info("Connecteur MT5 initialisé")
        except Exception as e:
            self.logger.error(f"Erreur lors de l'initialisation du connecteur MT5: {e}")
            raise
        
        # Initialiser l'agent d'imitation Oba
        try:
            self.oba_config = {
                "model_id": self.model_id,
                "confidence_threshold": self.confidence_threshold
            }
            self.oba = Oba(config=self.oba_config)
            self.logger.info(f"Agent Oba initialisé avec le modèle: {self.model_id}")
        except Exception as e:
            self.logger.error(f"Erreur lors de l'initialisation de l'agent Oba: {e}")
            raise
        
        # Vérifier que le modèle est chargé
        model_info = self.oba.get_model_info()
        if model_info.get("status") == "loaded":
            self.logger.info(f"Modèle chargé: {model_info.get('model_id')}")
            self.logger.info(f"Type de modèle: {model_info.get('model_type')}")
            self.logger.info(f"Précision: {model_info.get('metrics', {}).get('accuracy', 'N/A')}")
        else:
            self.logger.warning(f"Aucun modèle chargé. Statut: {model_info.get('status')}")
        
        # Initialiser le gestionnaire d'apprentissage
        self.imitation_manager = ImitationLearningManager()
        self.logger.info("Gestionnaire d'apprentissage par imitation initialisé")
        
        # Initialiser l'agent de gestion des risques (à faire ultérieurement)
        # TODO: Implémenter l'agent Iklwa
        
        self.logger.info("Tous les composants initialisés avec succès")
    
    def start(self):
        """
        Démarre le système de trading
        """
        self.logger.info(f"Démarrage du système de trading Akoben en mode {'simulation' if self.dry_run else 'réel'}")
        
        # Vérifier la connexion à MT5
        if not self.mt5.connect():
            self.logger.error("Impossible de se connecter à MetaTrader 5. Veuillez vérifier que MT5 est en cours d'exécution.")
            return False
        
        # Vérifier les informations du compte
        account_info = self.mt5.get_account_info()
        if account_info:
            self.logger.info(f"Connecté au compte: {account_info.get('LOGIN', 'N/A')}")
            self.logger.info(f"Solde: {account_info.get('BALANCE', 0)}")
            self.logger.info(f"Equity: {account_info.get('EQUITY', 0)}")
            
            # Stocker les informations initiales du compte
            self.initial_balance = account_info.get('BALANCE', 0)
            self.initial_equity = account_info.get('EQUITY', 0)
        else:
            self.logger.warning("Impossible d'obtenir les informations du compte")
        
        # Boucle principale
        try:
            while True:
                # Vérifier si nous sommes dans une période de trading
                if not self._is_trading_time():
                    self.logger.info("En dehors des heures de trading. Attente...")
                    time.sleep(300)  # 5 minutes
                    continue
                
                # Effectuer une vérification du marché
                self._check_market()
                
                # Vérifier les trades ouverts
                self._monitor_active_trades()
                
                # Enregistrer les statistiques
                self._save_statistics()
                
                # Attendre avant la prochaine vérification
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Interruption utilisateur. Arrêt du système.")
        except Exception as e:
            self.logger.error(f"Erreur dans la boucle principale: {e}")
            raise
        finally:
            # Nettoyage
            self.mt5.disconnect()
            self._save_statistics()
            self.logger.info("Système de trading arrêté")
    
    def _is_trading_time(self):
        """
        Vérifie si nous sommes dans les heures de trading
        
        Returns:
            bool: True si c'est le moment de trader, False sinon
        """
        # Pour l'US30, les heures de trading sont généralement:
        # - Du lundi au vendredi
        # - De 9h30 à 16h00 EST (heure de New York)
        
        # Exemple simple, à adapter selon les besoins
        now = datetime.now()
        
        # Vérifier le jour de la semaine (0=Lundi, 6=Dimanche)
        if now.weekday() >= 5:  # Samedi ou dimanche
            return False
        
        # Pour la démo, nous permettons le trading 24/5
        return True
    
    def _check_market(self):
        """
        Vérifie le marché et prend des décisions de trading
        """
        self.last_check_time = datetime.now()
        self.stats["checks_performed"] += 1
        
        self.logger.info(f"Vérification ##{self.stats['checks_performed']} du marché pour {self.instrument}")
        
        try:
            # 1. Récupérer les données de marché
            market_data = self._collect_market_data()
            if not market_data:
                self.logger.warning("Impossible de récupérer les données de marché")
                return
            
            # 2. Extraire les caractéristiques pour la prédiction
            features = self._extract_features(market_data)
            
            # 3. Faire une prédiction
            prediction = self._make_prediction(features)
            if not prediction:
                self.logger.info("Aucune prédiction générée")
                return
            
            # 4. Enregistrer la prédiction
            self._log_prediction(prediction, market_data)
            
            # 5. Vérifier si nous devons trader
            if self._should_execute_trade(prediction):
                # 6. Exécuter l'ordre
                trade_result = self._execute_trade(prediction, market_data)
                
                # 7. Enregistrer le résultat
                if trade_result:
                    self._log_trade(trade_result, prediction, market_data)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification du marché: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _collect_market_data(self):
        """
        Collecte les données de marché pour l'analyse
        
        Returns:
            dict: Données de marché ou None en cas d'erreur
        """
        self.logger.info(f"Collecte des données de marché pour {self.instrument}...")
        
        market_data = {
            "timestamp": datetime.now().isoformat(),
            "instrument": self.instrument,
            "current_price": None,
            "candles": {},
            "indicators": {}
        }
        
        try:
            # Récupérer le prix actuel
            price_info = self.mt5.get_current_price(self.instrument)
            if price_info:
                market_data["current_price"] = {
                    "bid": price_info.get("bid"),
                    "ask": price_info.get("ask"),
                    "spread": price_info.get("spread")
                }
            else:
                self.logger.warning(f"Impossible d'obtenir le prix actuel pour {self.instrument}")
                return None
            
            # Récupérer les données historiques pour chaque timeframe
            for tf in self.timeframes:
                candles = self.mt5.get_data(self.instrument, tf, 100)
                if candles is not None:
                    market_data["candles"][tf] = candles.to_dict('records')
                else:
                    self.logger.warning(f"Impossible d'obtenir les données {tf} pour {self.instrument}")
            
            # Si le timeframe principal est manquant, impossible de faire une analyse
            if self.main_timeframe not in market_data["candles"]:
                self.logger.error(f"Données {self.main_timeframe} manquantes, impossible de continuer")
                return None
            
            # Capturer l'image du graphique (non implémenté pour le moment)
            # TODO: Implémenter la capture d'écran du graphique
            
            # Calculer quelques indicateurs de base
            market_data["indicators"] = self._calculate_indicators(market_data["candles"])
            
            self.logger.info(f"Données de marché collectées avec succès pour {self.instrument}")
            
            # Sauvegarder les données pour réentraînement
            self._save_market_data(market_data)
            
            return market_data
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la collecte des données de marché: {e}")
            self.stats["connection_errors"] += 1
            return None
    
    def _calculate_indicators(self, candles_data):
        """
        Calcule les indicateurs techniques de base
        
        Args:
            candles_data: Données des chandelles pour différents timeframes
            
        Returns:
            dict: Indicateurs calculés
        """
        indicators = {}
        
        try:
            # Calculs pour le timeframe principal
            main_candles = candles_data.get(self.main_timeframe, [])
            if not main_candles:
                return indicators
            
            # Convertir en DataFrame pour faciliter les calculs
            df = pd.DataFrame(main_candles)
            
            # Calculer les moyennes mobiles (exemple)
            if len(df) >= 20:
                df['ma20'] = df['close'].rolling(window=20).mean()
                df['ma50'] = df['close'].rolling(window=50).mean()
                
                # Tendance basée sur les MM
                last_values = df.iloc[-1]
                if last_values['close'] > last_values['ma20'] > last_values['ma50']:
                    indicators['trend'] = 'UP'
                elif last_values['close'] < last_values['ma20'] < last_values['ma50']:
                    indicators['trend'] = 'DOWN'
                else:
                    indicators['trend'] = 'NEUTRAL'
                
                # Valeurs des moyennes mobiles
                indicators['ma20'] = last_values['ma20']
                indicators['ma50'] = last_values['ma50']
                
                # Positions relatives
                indicators['price_vs_ma20'] = (last_values['close'] / last_values['ma20'] - 1) * 100  # en %
                indicators['ma20_vs_ma50'] = (last_values['ma20'] / last_values['ma50'] - 1) * 100  # en %
            
            # Calculer la volatilité (ATR simplifié)
            if len(df) >= 14:
                df['high_low'] = df['high'] - df['low']
                df['high_close'] = abs(df['high'] - df['close'].shift(1))
                df['low_close'] = abs(df['low'] - df['close'].shift(1))
                df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
                df['atr14'] = df['tr'].rolling(window=14).mean()
                
                # ATR en points
                indicators['atr14'] = df['atr14'].iloc[-1]
                
                # ATR en % du prix
                indicators['atr14_percent'] = (indicators['atr14'] / df['close'].iloc[-1]) * 100
            
            # Momentum
            if len(df) >= 14:
                # ROC (Rate of Change)
                df['roc14'] = (df['close'] / df['close'].shift(14) - 1) * 100
                indicators['roc14'] = df['roc14'].iloc[-1]
            
            # Divergence prix-volume (si volume disponible)
            if 'tick_volume' in df.columns and len(df) >= 10:
                price_change = df['close'].iloc[-1] - df['close'].iloc[-5]
                volume_change = df['tick_volume'].iloc[-1] - df['tick_volume'].iloc[-5]
                
                if price_change > 0 and volume_change < 0:
                    indicators['price_volume_divergence'] = 'BEARISH'
                elif price_change < 0 and volume_change < 0:
                    indicators['price_volume_divergence'] = 'BULLISH'
                else:
                    indicators['price_volume_divergence'] = 'NONE'
            
            # Détection de pattern chandelier simplifié
            if len(df) >= 3:
                # Détection de marteau/étoile filante simplifiée
                last_candle = df.iloc[-1]
                body_size = abs(last_candle['close'] - last_candle['open'])
                wick_size = max(last_candle['high'] - max(last_candle['open'], last_candle['close']),
                               min(last_candle['open'], last_candle['close']) - last_candle['low'])
                
                if body_size > 0 and wick_size / body_size > 2:
                    if last_candle['close'] > last_candle['open']:
                        indicators['candle_pattern'] = 'POSSIBLE_HAMMER'
                    else:
                        indicators['candle_pattern'] = 'POSSIBLE_SHOOTING_STAR'
                else:
                    indicators['candle_pattern'] = 'NONE'
            
            # Performance récente
            if len(df) >= 10:
                indicators['last_5_candles_direction'] = 'UP' if df['close'].iloc[-1] > df['close'].iloc[-5] else 'DOWN'
                indicators['last_10_candles_direction'] = 'UP' if df['close'].iloc[-1] > df['close'].iloc[-10] else 'DOWN'
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"Erreur lors du calcul des indicateurs: {e}")
            return {}
    
    def _extract_features(self, market_data):
        """
        Extrait les caractéristiques pour la prédiction
        
        Args:
            market_data: Données de marché collectées
            
        Returns:
            dict: Caractéristiques pour la prédiction
        """
        features = {}
        
        try:
            # Tendance basée sur les indicateurs
            indicators = market_data.get("indicators", {})
            if 'trend' in indicators:
                features[f"trend_{indicators['trend'].lower()}"] = 1
            
            # Position par rapport aux moyennes mobiles
            if 'price_vs_ma20' in indicators:
                if indicators['price_vs_ma20'] > 0:
                    features['price_above_ma20'] = 1
                else:
                    features['price_below_ma20'] = 1
            
            if 'ma20_vs_ma50' in indicators:
                if indicators['ma20_vs_ma50'] > 0:
                    features['ma20_above_ma50'] = 1
                else:
                    features['ma20_below_ma50'] = 1
            
            # Momentum
            if 'roc14' in indicators:
                if indicators['roc14'] > 0:
                    features['positive_momentum'] = 1
                else:
                    features['negative_momentum'] = 1
            
            # Volatilité
            if 'atr14_percent' in indicators:
                if indicators['atr14_percent'] > 1.0:  # Plus de 1% de volatilité
                    features['high_volatility'] = 1
                else:
                    features['low_volatility'] = 1
            
            # Divergence prix-volume
            if 'price_volume_divergence' in indicators:
                features[f"divergence_{indicators['price_volume_divergence'].lower()}"] = 1
            
            # Pattern chandelier
            if 'candle_pattern' in indicators and indicators['candle_pattern'] != 'NONE':
                features[f"pattern_{indicators['candle_pattern'].lower()}"] = 1
            
            # Direction récente
            if 'last_5_candles_direction' in indicators:
                features[f"recent_trend_{indicators['last_5_candles_direction'].lower()}"] = 1
            
            # Instrument
            features[f"instrument_{self.instrument.lower()}"] = 1
            
            # Timeframe
            features[f"timeframe_{self.main_timeframe.lower()}"] = 1
            
            self.logger.info(f"Caractéristiques extraites: {len(features)} éléments")
            return features
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'extraction des caractéristiques: {e}")
            return {}
    
    def _make_prediction(self, features):
        """
        Génère une prédiction de trading
        
        Args:
            features: Caractéristiques extraites
            
        Returns:
            dict: Prédiction ou None en cas d'erreur
        """
        if not features:
            return None
        
        try:
            # Faire la prédiction avec l'agent Oba
            prediction = self.oba.imitation_manager.predict(features)
            
            if prediction:
                self.stats["predictions_made"] += 1
                self.logger.info(f"Prédiction: {prediction['action']} avec confiance {max(prediction.get('confidences', {}).values() or [0]):.2%}")
                return prediction
            else:
                self.logger.warning("Aucune prédiction générée")
                return None
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération de la prédiction: {e}")
            return None
    
    def _should_execute_trade(self, prediction):
        """
        Détermine si un trade doit être exécuté
        
        Args:
            prediction: Prédiction générée
            
        Returns:
            bool: True si le trade doit être exécuté, False sinon
        """
        # Vérifier l'action prédite
        if not prediction or prediction.get("action") not in ["BUY", "SELL"]:
            return False
        
        # Vérifier la confiance
        confidence = max(prediction.get("confidences", {}).values() or [0])
        if confidence < self.confidence_threshold:
            self.logger.info(f"Confiance trop faible pour trader: {confidence:.2%} < {self.confidence_threshold:.2%}")
            return False
        
        # Vérifier le nombre de trades quotidiens
        if len(self.today_trades) >= self.max_daily_trades:
            self.logger.info(f"Limite de trades quotidiens atteinte: {len(self.today_trades)}/{self.max_daily_trades}")
            return False
        
        # Vérifier le risque quotidien
        if self.daily_drawdown >= self.max_daily_risk:
            self.logger.info(f"Limite de risque quotidien atteinte: {self.daily_drawdown:.2%} >= {self.max_daily_risk:.2%}")
            return False
        
        # Vérifier qu'il n'y a pas déjà une position ouverte sur cet instrument
        if any(trade.get("instrument") == self.instrument for trade in self.active_trades):
            self.logger.info(f"Position déjà ouverte sur {self.instrument}")
            return False
        
        # En mode simulation, toujours retourner True si les conditions sont remplies
        if self.dry_run:
            return True
        
        # Ajoutez d'autres vérifications si nécessaire
        
        return True
    
    def _execute_trade(self, prediction, market_data):
        """
        Exécute un ordre de trading
        
        Args:
            prediction: Prédiction générée
            market_data: Données de marché
            
        Returns:
            dict: Résultat de l'exécution ou None en cas d'erreur
        """
        action = prediction.get("action")
        confidence = max(prediction.get("confidences", {}).values() or [0])
        
        self.logger.info(f"Exécution d'un ordre {action} pour {self.instrument} avec confiance {confidence:.2%}")
        
        # Obtenir le prix actuel
        current_price = market_data.get("current_price", {})
        if not current_price or "bid" not in current_price or "ask" not in current_price:
            self.logger.error("Prix actuel non disponible")
            return None
        
        # Déterminer les niveaux de prix
        entry_price = current_price.get("bid") if action == "SELL" else current_price.get("ask")
        
        # Calculer les niveaux SL et TP (exemple simpliste)
        atr = market_data.get("indicators", {}).get("atr14", 0)
        if not atr or atr <= 0:
            atr = entry_price * 0.005  # Valeur par défaut: 0.5% du prix
        
        # Stop Loss: 1.5 x ATR
        sl_distance = atr * 1.5
        # Take Profit: 2 x ATR (RR = 1.33)
        tp_distance = atr * 2.0
        
        if action == "BUY":
            stop_loss = entry_price - sl_distance
            take_profit = entry_price + tp_distance
        else:  # SELL
            stop_loss = entry_price + sl_distance
            take_profit = entry_price - tp_distance
        
        # Arrondir les prix
        stop_loss = round(stop_loss, 2)
        take_profit = round(take_profit, 2)
        
        # Calculer la taille de la position
        position_size = self._calculate_position_size(entry_price, stop_loss)
        if position_size <= 0:
            self.logger.error("Taille de position invalide")
            return None
        
        # Résultat du trade (pour le mode simulation)
        if self.dry_run:
            trade_result = {
                "id": f"SIM_{int(time.time())}",
                "instrument": self.instrument,
                "action": action,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "position_size": position_size,
                "timestamp": datetime.now().isoformat(),
                "status": "SIMULATED",
                "predicted_confidence": confidence
            }
            
            self.logger.info(f"Mode simulation: Trade {action} simulé à {entry_price}")
            self.stats["trades_executed"] += 1
            self.today_trades.append(trade_result)
            self.active_trades.append(trade_result)
            
            return trade_result
        
        # Exécution réelle de l'ordre
        try:
            # Placer l'ordre via MT5
            order_result = self.mt5.place_order(
                symbol=self.instrument,
                order_type=action,
                volume=position_size,
                price=0.0,  # 0 = prix du marché
                sl=stop_loss,
                tp=take_profit,
                comment=f"Akoben-{confidence:.2%}"
            )
            
            if order_result:
                trade_result = {
                    "id": str(order_result.get("ticket", "")),
                    "instrument": self.instrument,
                    "action": action,
                    "entry_price": order_result.get("price", entry_price),
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "position_size": position_size,
                    "timestamp": datetime.now().isoformat(),
                    "status": "OPEN",
                    "predicted_confidence": confidence,
                    "mt5_details": order_result
                }
                
                self.logger.info(f"Trade {action} exécuté à {trade_result['entry_price']}")
                self.stats["trades_executed"] += 1
                self.today_trades.append(trade_result)
                self.active_trades.append(trade_result)
                
                return trade_result
            else:
                self.logger.error("Échec de l'exécution de l'ordre")
                return None
                
        except Exception as e:
            self.logger.error(f"Erreur lors de l'exécution de l'ordre: {e}")
            return None
    
    def _calculate_position_size(self, entry_price, stop_loss):
        """
        Calcule la taille de position optimale
        
        Args:
            entry_price: Prix d'entrée
            stop_loss: Niveau de stop loss
            
        Returns:
            float: Taille de position en lots
        """
        try:
            # Récupérer les informations du compte
            account_info = self.mt5.get_account_info()
            if not account_info:
                return 0.01  # Valeur par défaut minimale
            
            # Récupérer le solde du compte
            balance = account_info.get('BALANCE', 0)
            if balance <= 0:
                return 0.01
            
            # Calculer le montant à risquer
            risk_amount = balance * (self.risk_per_trade / 100.0)
            
            # Calculer la distance en points
            stop_distance = abs(entry_price - stop_loss)
            if stop_distance <= 0:
                return 0.01
            
            # Pour l'US30, calculer la valeur d'un pip
            pip_value = 0.1  # Valeur approximative pour 0.01 lot d'US30
            
            # Calculer la taille de position
            position_size = risk_amount / (stop_distance * pip_value)
            
            # Arrondir à 0.01 près (taille minimum de lot)
            position_size = max(round(position_size / 0.01) * 0.01, 0.01)
            
            # Limiter la taille de position maximale (par sécurité)
            max_position = min(balance / 1000, 1.0)  # Maximum 1 lot ou 0.1% du solde
            position_size = min(position_size, max_position)
            
            self.logger.info(f"Taille de position calculée: {position_size} lot(s)")
            return position_size
            
        except Exception as e:
            self.logger.error(f"Erreur lors du calcul de la taille de position: {e}")
            return 0.01  # Valeur par défaut minimale en cas d'erreur
    
    def _monitor_active_trades(self):
        """
        Surveille les trades actifs et met à jour leur statut
        """
        if not self.active_trades:
            return
        
        self.logger.info(f"Surveillance de {len(self.active_trades)} trades actifs")
        
        # Pour le mode simulation, nous simulons les résultats
        if self.dry_run:
            self._simulate_trade_results()
            return
        
        # Pour le mode réel, vérifier l'état des positions dans MT5
        try:
            positions = self.mt5.get_positions(self.instrument)
            if positions is None:
                self.logger.warning("Impossible de récupérer les positions ouvertes")
                return
            
            # Créer un dictionnaire des positions actives par ticket
            active_positions = {str(pos.get("ticket", "")): pos for pos in positions}
            
            # Vérifier chaque trade actif
            updated_active_trades = []
            
            for trade in self.active_trades:
                trade_id = trade.get("id", "")
                
                # Si le trade n'est plus dans les positions actives, il a été fermé
                if trade_id not in active_positions:
                    # Récupérer l'historique pour obtenir le résultat
                    history = self.mt5.get_history_orders(1)  # Dernier jour
                    
                    # Chercher le trade dans l'historique
                    for order in history or []:
                        if str(order.get("ticket", "")) == trade_id:
                            # Mettre à jour le statut du trade
                            trade["status"] = "CLOSED"
                            trade["close_time"] = datetime.now().isoformat()
                            trade["profit"] = order.get("profit", 0)
                            
                            # Mettre à jour les statistiques
                            if trade["profit"] > 0:
                                self.stats["successful_trades"] += 1
                                self.stats["total_profit"] += trade["profit"]
                            else:
                                self.stats["failed_trades"] += 1
                                self.stats["total_loss"] += abs(trade["profit"])
                            
                            # Journaliser le résultat
                            self.logger.info(f"Trade {trade_id} fermé avec profit: {trade['profit']}")
                            
                            # Enregistrer le trade fermé
                            self._log_closed_trade(trade)
                            break
                else:
                    # Le trade est toujours actif
                    position = active_positions[trade_id]
                    
                    # Mettre à jour les informations
                    trade["current_price"] = position.get("price_current", trade.get("entry_price"))
                    trade["current_profit"] = position.get("profit", 0)
                    
                    # Garder le trade dans la liste des actifs
                    updated_active_trades.append(trade)
            
            # Mettre à jour la liste des trades actifs
            self.active_trades = updated_active_trades
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la surveillance des trades actifs: {e}")
    
    def _simulate_trade_results(self):
        """
        Simule les résultats des trades en mode dry run
        """
        updated_active_trades = []
        
        # Récupérer le prix actuel
        price_info = self.mt5.get_current_price(self.instrument)
        if not price_info:
            self.logger.warning("Impossible d'obtenir le prix actuel pour la simulation")
            return
        
        current_bid = price_info.get("bid", 0)
        current_ask = price_info.get("ask", 0)
        
        for trade in self.active_trades:
            # Déterminer le prix actuel selon la direction
            current_price = current_bid if trade["action"] == "BUY" else current_ask
            
            # Vérifier si le trade a atteint TP ou SL
            if trade["action"] == "BUY":
                if current_price >= trade["take_profit"]:
                    # Take Profit atteint
                    profit = (trade["take_profit"] - trade["entry_price"]) * trade["position_size"] * 100
                    trade["status"] = "CLOSED"
                    trade["close_price"] = trade["take_profit"]
                    trade["close_time"] = datetime.now().isoformat()
                    trade["profit"] = profit
                    trade["close_reason"] = "TAKE_PROFIT"
                    
                    self.logger.info(f"Simulation: TP atteint sur {trade['id']} avec profit {profit:.2f}")
                    self.stats["successful_trades"] += 1
                    self.stats["total_profit"] += profit
                    
                    # Enregistrer le trade fermé
                    self._log_closed_trade(trade)
                    
                elif current_price <= trade["stop_loss"]:
                    # Stop Loss atteint
                    loss = (trade["stop_loss"] - trade["entry_price"]) * trade["position_size"] * 100
                    trade["status"] = "CLOSED"
                    trade["close_price"] = trade["stop_loss"]
                    trade["close_time"] = datetime.now().isoformat()
                    trade["profit"] = loss
                    trade["close_reason"] = "STOP_LOSS"
                    
                    self.logger.info(f"Simulation: SL atteint sur {trade['id']} avec perte {loss:.2f}")
                    self.stats["failed_trades"] += 1
                    self.stats["total_loss"] += abs(loss)
                    
                    # Enregistrer le trade fermé
                    self._log_closed_trade(trade)
                    
                else:
                    # Trade toujours ouvert
                    trade["current_price"] = current_price
                    trade["current_profit"] = (current_price - trade["entry_price"]) * trade["position_size"] * 100
                    updated_active_trades.append(trade)
                    
            elif trade["action"] == "SELL":
                if current_price <= trade["take_profit"]:
                    # Take Profit atteint
                    profit = (trade["entry_price"] - trade["take_profit"]) * trade["position_size"] * 100
                    trade["status"] = "CLOSED"
                    trade["close_price"] = trade["take_profit"]
                    trade["close_time"] = datetime.now().isoformat()
                    trade["profit"] = profit
                    trade["close_reason"] = "TAKE_PROFIT"
                    
                    self.logger.info(f"Simulation: TP atteint sur {trade['id']} avec profit {profit:.2f}")
                    self.stats["successful_trades"] += 1
                    self.stats["total_profit"] += profit
                    
                    # Enregistrer le trade fermé
                    self._log_closed_trade(trade)
                    
                elif current_price >= trade["stop_loss"]:
                    # Stop Loss atteint
                    loss = (trade["entry_price"] - trade["stop_loss"]) * trade["position_size"] * 100
                    trade["status"] = "CLOSED"
                    trade["close_price"] = trade["stop_loss"]
                    trade["close_time"] = datetime.now().isoformat()
                    trade["profit"] = loss
                    trade["close_reason"] = "STOP_LOSS"
                    
                    self.logger.info(f"Simulation: SL atteint sur {trade['id']} avec perte {loss:.2f}")
                    self.stats["failed_trades"] += 1
                    self.stats["total_loss"] += abs(loss)
                    
                    # Enregistrer le trade fermé
                    self._log_closed_trade(trade)
                    
                else:
                    # Trade toujours ouvert
                    trade["current_price"] = current_price
                    trade["current_profit"] = (trade["entry_price"] - current_price) * trade["position_size"] * 100
                    updated_active_trades.append(trade)
        
        # Mettre à jour la liste des trades actifs
        self.active_trades = updated_active_trades
    
    def _log_prediction(self, prediction, market_data):
        """
        Enregistre une prédiction pour analyse ultérieure
        
        Args:
            prediction: Prédiction générée
            market_data: Données de marché utilisées
        """
        try:
            # Créer un identifiant unique pour la prédiction
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prediction_id = f"prediction_{self.instrument}_{timestamp}"
            
            # Structurer les données
            prediction_data = {
                "id": prediction_id,
                "timestamp": datetime.now().isoformat(),
                "instrument": self.instrument,
                "timeframe": self.main_timeframe,
                "action": prediction.get("action"),
                "confidence": prediction.get("confidences"),
                "features_used": prediction.get("features_used", []),
                "price": market_data.get("current_price"),
                "indicators": market_data.get("indicators"),
                "resulted_in_trade": False
            }
            
            # Enregistrer dans un fichier JSON
            prediction_file = self.predictions_dir / f"{prediction_id}.json"
            with open(prediction_file, 'w', encoding='utf-8') as f:
                json.dump(prediction_data, f, indent=2)
                
            self.logger.info(f"Prédiction enregistrée: {prediction_file}")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement de la prédiction: {e}")
    
    def _log_trade(self, trade_result, prediction, market_data):
        """
        Enregistre un trade exécuté pour analyse ultérieure
        
        Args:
            trade_result: Résultat de l'exécution du trade
            prediction: Prédiction ayant conduit au trade
            market_data: Données de marché utilisées
        """
        try:
            # Créer un identifiant unique pour le trade
            trade_id = trade_result.get("id", f"trade_{int(time.time())}")
            
            # Enrichir les données du trade
            trade_data = trade_result.copy()
            trade_data.update({
                "prediction": {
                    "action": prediction.get("action"),
                    "confidence": prediction.get("confidences"),
                    "features_used": prediction.get("features_used", [])
                },
                "market_data": {
                    "price": market_data.get("current_price"),
                    "indicators": market_data.get("indicators")
                },
                "trade_time": datetime.now().isoformat(),
                "initial_status": trade_result.get("status", "OPEN")
            })
            
            # Enregistrer dans un fichier JSON
            trade_file = self.trades_dir / f"{trade_id}.json"
            with open(trade_file, 'w', encoding='utf-8') as f:
                json.dump(trade_data, f, indent=2)
                
            self.logger.info(f"Trade enregistré: {trade_file}")
            
            # Mettre à jour le fichier de prédiction pour indiquer qu'il a conduit à un trade
            for pred_file in self.predictions_dir.glob("*.json"):
                try:
                    with open(pred_file, 'r') as f:
                        pred_data = json.load(f)
                    
                    # Vérifier si cette prédiction correspond au trade
                    if (pred_data.get("action") == prediction.get("action") and 
                        pred_data.get("timestamp", "").split("T")[0] == datetime.now().isoformat().split("T")[0]):
                        
                        # Mettre à jour l'indication
                        pred_data["resulted_in_trade"] = True
                        pred_data["trade_id"] = trade_id
                        
                        # Enregistrer les modifications
                        with open(pred_file, 'w') as f:
                            json.dump(pred_data, f, indent=2)
                        
                        break
                        
                except Exception:
                    pass
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement du trade: {e}")
    
    def _log_closed_trade(self, trade):
        """
        Enregistre les détails d'un trade fermé
        
        Args:
            trade: Données du trade fermé
        """
        try:
            # Identifier le fichier de trade
            trade_id = trade.get("id", "unknown")
            trade_file = self.trades_dir / f"{trade_id}.json"
            
            # Si le fichier existe, le mettre à jour
            if trade_file.exists():
                with open(trade_file, 'r', encoding='utf-8') as f:
                    trade_data = json.load(f)
                
                # Mettre à jour les données
                trade_data.update({
                    "status": trade.get("status", "CLOSED"),
                    "close_time": trade.get("close_time", datetime.now().isoformat()),
                    "close_price": trade.get("close_price"),
                    "profit": trade.get("profit"),
                    "close_reason": trade.get("close_reason")
                })
                
                # Enregistrer les modifications
                with open(trade_file, 'w', encoding='utf-8') as f:
                    json.dump(trade_data, f, indent=2)
            else:
                # Créer un nouveau fichier
                with open(trade_file, 'w', encoding='utf-8') as f:
                    json.dump(trade, f, indent=2)
            
            self.logger.info(f"Trade fermé enregistré: {trade_file}")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement du trade fermé: {e}")
    
    def _save_market_data(self, market_data):
        """
        Sauvegarde les données de marché pour analyse ultérieure
        
        Args:
            market_data: Données de marché à sauvegarder
        """
        try:
            # Créer un identifiant unique
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            data_id = f"market_{self.instrument}_{timestamp}"
            
            # Enregistrer dans un fichier JSON
            data_file = self.data_dir / "market_data" / f"{data_id}.json"
            data_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(market_data, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde des données de marché: {e}")
    
    def _save_statistics(self):
        """
        Sauvegarde les statistiques du système
        """
        try:
            # Préparer les statistiques
            stats = self.stats.copy()
            
            # Ajouter des informations supplémentaires
            stats.update({
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                "active_trades_count": len(self.active_trades),
                "today_trades_count": len(self.today_trades),
                "account_balance": self.mt5.get_account_info().get("BALANCE", 0) if not self.dry_run else None,
                "profit_factor": (stats["total_profit"] / max(stats["total_loss"], 0.01)) if stats["total_loss"] > 0 else 0,
                "success_rate": (stats["successful_trades"] / max(stats["trades_executed"], 1)) * 100,
                "mode": "simulation" if self.dry_run else "real"
            })
            
            # Enregistrer dans un fichier JSON
            stats_file = self.stats_dir / "latest_stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)
            
            # Enregistrer un snapshot horodaté
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            snapshot_file = self.stats_dir / f"stats_{timestamp}.json"
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)
            
            self.logger.info(f"Statistiques sauvegardées: Win Rate {stats['success_rate']:.2f}%, Trades: {stats['trades_executed']}")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde des statistiques: {e}")
    
    def reprocess_historical_data(self, days=7):
        """
        Retraite les données historiques pour l'entraînement
        
        Args:
            days: Nombre de jours d'historique à traiter
        """
        self.logger.info(f"Retraitement des données historiques des {days} derniers jours")
        
        # Collecter les candles
        try:
            # Récupérer les données historiques
            candles = self.mt5.get_data(self.instrument, self.main_timeframe, 1440 * days // int(self.main_timeframe[1:]))
            if candles is None or len(candles) == 0:
                self.logger.warning("Aucune donnée historique disponible")
                return
            
            self.logger.info(f"Données récupérées: {len(candles)} bougies")
            
            # Convertir en liste de dictionnaires
            candles_data = candles.to_dict('records')
            
            # Créer un dossier pour les données historiques
            historical_dir = self.data_dir / "historical" / self.instrument
            historical_dir.mkdir(parents=True, exist_ok=True)
            
            # Enregistrer les données
            file_path = historical_dir / f"historical_{self.main_timeframe}_{datetime.now().strftime('%Y%m%d')}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(candles_data, f, indent=2)
            
            self.logger.info(f"Données historiques enregistrées: {file_path}")
            
            # Traiter les données pour simuler des prédictions
            results = self._simulate_predictions_on_historical(candles_data)
            
            # Enregistrer les résultats
            results_path = historical_dir / f"historical_predictions_{self.main_timeframe}_{datetime.now().strftime('%Y%m%d')}.json"
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            
            self.logger.info(f"Résultats des prédictions historiques enregistrés: {results_path}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Erreur lors du retraitement des données historiques: {e}")
            return None
    
    def _simulate_predictions_on_historical(self, candles_data):
        """
        Simule des prédictions sur des données historiques
        
        Args:
            candles_data: Liste des données de bougies historiques
            
        Returns:
            dict: Résultats des prédictions
        """
        results = {
            "predictions": [],
            "accuracy": 0,
            "total_predictions": 0,
            "correct_predictions": 0
        }
        
        try:
            # Parcourir les bougies (sauf les dernières)
            for i in range(len(candles_data) - 10):
                # Créer un sous-ensemble de candles pour l'analyse
                subset = candles_data[i:i+50]  # Prendre 50 bougies
                
                # Créer des données de marché simulées
                market_data = {
                    "instrument": self.instrument,
                    "timestamp": subset[-1]["time"],
                    "current_price": {
                        "bid": subset[-1]["close"],
                        "ask": subset[-1]["close"] + (subset[-1]["high"] - subset[-1]["low"]) * 0.1,
                        "spread": (subset[-1]["high"] - subset[-1]["low"]) * 0.1
                    },
                    "candles": {
                        self.main_timeframe: subset
                    }
                }
                
                # Calculer les indicateurs
                market_data["indicators"] = self._calculate_indicators(market_data["candles"])
                
                # Extraire les caractéristiques
                features = self._extract_features(market_data)
                
                # Faire une prédiction
                prediction = self.oba.imitation_manager.predict(features)
                
                if prediction:
                    # Déterminer la direction réelle
                    # La direction est considérée comme correcte si le prix se déplace dans cette direction
                    # dans les 5 bougies suivantes
                    future_price = candles_data[i+5]["close"] if i+5 < len(candles_data) else None
                    current_price = subset[-1]["close"]
                    
                    if future_price is not None:
                        actual_direction = "BUY" if future_price > current_price else "SELL"
                        prediction_correct = prediction["action"] == actual_direction
                        
                        # Enregistrer la prédiction
                        prediction_result = {
                            "timestamp": subset[-1]["time"],
                            "predicted_action": prediction["action"],
                            "predicted_confidence": max(prediction.get("confidences", {}).values() or [0]),
                            "actual_direction": actual_direction,
                            "correct": prediction_correct,
                            "price_at_prediction": current_price,
                            "future_price": future_price,
                            "price_change": future_price - current_price
                        }
                        
                        results["predictions"].append(prediction_result)
                        results["total_predictions"] += 1
                        if prediction_correct:
                            results["correct_predictions"] += 1
            
            # Calculer la précision
            if results["total_predictions"] > 0:
                results["accuracy"] = results["correct_predictions"] / results["total_predictions"]
            
            self.logger.info(f"Simulation historique: {results['total_predictions']} prédictions, "
                           f"précision: {results['accuracy']:.2%}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la simulation des prédictions historiques: {e}")
            return results


def parse_arguments():
    """
    Parse les arguments de ligne de commande
    
    Returns:
        dict: Arguments parsés
    """
    parser = argparse.ArgumentParser(description='Akoben Trader - Système de trading algorithmique')
    
    parser.add_argument('--instrument', type=str, default='US30',
                        help='Instrument à trader (par défaut: US30)')
    
    parser.add_argument('--timeframe', type=str, default='M1',
                        help='Timeframe principal (par défaut: M1)')
    
    parser.add_argument('--interval', type=int, default=60,
                        help='Intervalle de vérification en secondes (par défaut: 60)')
    
    parser.add_argument('--confidence', type=float, default=0.7,
                        help='Seuil de confiance pour les trades (par défaut: 0.7)')
    
    parser.add_argument('--risk', type=float, default=1.0,
                        help='Risque par trade en pourcentage (par défaut: 1.0)')
    
    parser.add_argument('--max-trades', type=int, default=3,
                        help='Nombre maximum de trades par jour (par défaut: 3)')
    
    parser.add_argument('--model', type=str, default=None,
                        help='ID du modèle à utiliser (par défaut: aucun)')
    
    parser.add_argument('--dry-run', action='store_true',
                        help='Mode simulation (pas d\'ordres réels)')
    
    parser.add_argument('--reprocess', action='store_true',
                        help='Retraiter les données historiques pour l\'entraînement')
    
    parser.add_argument('--days', type=int, default=7,
                        help='Nombre de jours d\'historique à retraiter (par défaut: 7)')
    
    args = parser.parse_args()
    
    return vars(args)


def main():
    """
    Fonction principale
    """
    # Analyser les arguments
    args = parse_arguments()
    
    # Préparer la configuration
    config = {
        "instrument": args['instrument'],
        "main_timeframe": args['timeframe'],
        "timeframes": [args['timeframe'], "M5", "M15"],
        "check_interval": args['interval'],
        "confidence_threshold": args['confidence'],
        "risk_per_trade": args['risk'],
        "max_daily_trades": args['max_trades'],
        "model_id": args['model'],
        "dry_run": args['dry_run']
    }
    
    # Créer l'instance du trader
    trader = AkobenTrader(config)
    
    # Retraiter les données historiques si demandé
    if args['reprocess']:
        trader.reprocess_historical_data(days=args['days'])
        return
    
    # Démarrer le système de trading
    trader.start()


if __name__ == "__main__":
    main()