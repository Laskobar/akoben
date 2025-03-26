import os
import re
from typing import Dict, Any, List, Optional, Tuple
import json
from datetime import datetime

class SetupTextProcessor:
    """
    Analyse les fichiers texte de description des setups.
    Extrait les informations structurées pour faciliter l'apprentissage.
    """
    def __init__(self, config=None):
        """
        Initialise le processeur de texte avec une configuration optionnelle.
        
        Args:
            config: Configuration pour l'extraction (dictionnaire)
        """
        self.config = config or {}
        
        # Patterns pour l'extraction
        self.patterns = {
            'setup': [
                r"setup\s*:\s*(.*?)(?:\n|$)",
                r"pattern\s*:\s*(.*?)(?:\n|$)",
                r"configuration\s*:\s*(.*?)(?:\n|$)"
            ],
            'action': [
                r"action\s*:\s*(buy|sell|long|short)(?:\n|$)",
                r"(buy|sell|long|short)(?:\s+signal|\s+entry|\s+position)?(?:\n|$)"
            ],
            'entry': [
                r"entry\s*:\s*([\d\.]+)(?:\n|$)",
                r"entry\s*(?:price|level)\s*:\s*([\d\.]+)(?:\n|$)",
                r"open\s*(?:price|level)\s*:\s*([\d\.]+)(?:\n|$)"
            ],
            'stop_loss': [
                r"stop\s*loss\s*:\s*([\d\.]+)(?:\n|$)",
                r"stop\s*:\s*([\d\.]+)(?:\n|$)",
                r"sl\s*:\s*([\d\.]+)(?:\n|$)"
            ],
            'take_profit': [
                r"take\s*profit\s*:\s*([\d\.]+)(?:\n|$)",
                r"target\s*:\s*([\d\.]+)(?:\n|$)",
                r"tp\s*:\s*([\d\.]+)(?:\n|$)"
            ],
            'risk_reward': [
                r"risk\s*[\-:]?\s*reward\s*:\s*([\d\.]+)\s*:\s*([\d\.]+)(?:\n|$)",
                r"r\s*[\-:]?\s*r\s*:\s*([\d\.]+)\s*:\s*([\d\.]+)(?:\n|$)"
            ],
            'timeframe': [
                r"timeframe\s*:\s*([a-zA-Z0-9]+)(?:\n|$)",
                r"tf\s*:\s*([a-zA-Z0-9]+)(?:\n|$)"
            ]
        }
        
        # Adaptable aux indicateurs communs
        self.indicator_patterns = [
            r"rsi\s*(?:\(?\s*\d+\s*\)?)?\s*[=:]\s*([\d\.]+)",
            r"macd\s*[=:]\s*([a-zA-Z0-9 ]+)",
            r"ema\s*(?:\(?\s*\d+\s*\)?)?\s*[=:]\s*([\d\.]+)",
            r"sma\s*(?:\(?\s*\d+\s*\)?)?\s*[=:]\s*([\d\.]+)",
            r"bollinger\s*[=:]\s*([a-zA-Z0-9 ]+)",
            r"stoch(?:astic)?\s*[=:]\s*([\d\.]+)"
        ]
    
    def extract_info(self, text_path: str) -> Dict[str, Any]:
        """
        Extrait les informations structurées d'un fichier texte.
        
        Args:
            text_path: Chemin vers le fichier texte
            
        Returns:
            Dictionnaire des informations extraites
        """
        if not os.path.exists(text_path):
            return {"error": "Fichier non trouvé"}
        
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            return self.extract_from_text(text)
        
        except Exception as e:
            return {"error": f"Erreur lors de l'extraction: {str(e)}"}
    
    def extract_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extrait les informations d'un texte.
        
        Args:
            text: Texte à analyser
            
        Returns:
            Dictionnaire des informations extraites
        """
        info = {}
        
        # Normaliser le texte pour faciliter l'extraction
        text = text.lower()
        
        # Extraire les informations de base
        for key, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    if key == 'risk_reward' and len(match.groups()) >= 2:
                        info[key] = f"{match.group(1)}:{match.group(2)}"
                    else:
                        info[key] = match.group(1)
                    break
        
        # Normaliser l'action
        if 'action' in info:
            action = info['action'].lower()
            if action in ['buy', 'long']:
                info['action'] = 'buy'
            elif action in ['sell', 'short']:
                info['action'] = 'sell'
        
        # Extraire les indicateurs
        indicators = {}
        for pattern in self.indicator_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                indicator_name = match.re.pattern.split(r'[=:]')[0].strip()
                indicator_name = re.sub(r'\s*\(?\s*\d+\s*\)?', '', indicator_name).strip()
                indicators[indicator_name] = match.group(1)
        
        if indicators:
            info['indicators'] = indicators
        
        # Extraire les raisons/contexte (paragraphes plus longs)
        reasoning_sections = self._extract_sections(text)
        if reasoning_sections:
            info.update(reasoning_sections)
        
        return info
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """
        Extrait les sections de texte libre comme le contexte ou les raisons.
        
        Args:
            text: Texte à analyser
            
        Returns:
            Dictionnaire des sections extraites
        """
        sections = {}
        
        # Rechercher les sections courantes
        section_patterns = [
            (r"contexte\s*:\s*(.*?)(?:\n\n|\n[a-zA-Z]+\s*:|$)", "context"),
            (r"raisons\s*:\s*(.*?)(?:\n\n|\n[a-zA-Z]+\s*:|$)", "reasons"),
            (r"notes\s*:\s*(.*?)(?:\n\n|\n[a-zA-Z]+\s*:|$)", "notes"),
            (r"strategie\s*:\s*(.*?)(?:\n\n|\n[a-zA-Z]+\s*:|$)", "strategy")
        ]
        
        for pattern, key in section_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                if content:
                    sections[key] = content
        
        # Si on ne trouve pas de sections avec les patterns, essayer de diviser par lignes vides
        if not sections:
            paragraphs = re.split(r'\n\s*\n', text)
            if len(paragraphs) > 1:
                # Prendre le dernier paragraphe comme notes
                sections["notes"] = paragraphs[-1].strip()
        
        return sections
    
    def standardize_setup_info(self, setup_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardise les informations extraites pour faciliter l'apprentissage.
        
        Args:
            setup_info: Informations brutes extraites
            
        Returns:
            Informations standardisées
        """
        standardized = setup_info.copy()
        
        # Convertir les valeurs numériques
        numeric_fields = ['entry', 'stop_loss', 'take_profit']
        for field in numeric_fields:
            if field in standardized:
                try:
                    standardized[field] = float(standardized[field])
                except (ValueError, TypeError):
                    # Si la conversion échoue, garder la valeur originale
                    pass
        
        # Standardiser le risk:reward
        if 'risk_reward' in standardized:
            rr = standardized['risk_reward']
            if isinstance(rr, str) and ':' in rr:
                risk, reward = rr.split(':')
                try:
                    risk = float(risk)
                    reward = float(reward)
                    standardized['risk_reward_ratio'] = reward / risk
                except (ValueError, ZeroDivisionError):
                    pass
        
        # Standardiser les timeframes
        if 'timeframe' in standardized:
            tf = standardized['timeframe'].upper()
            # Normaliser les formats courants
            tf_mapping = {
                'M1': 'M1', '1M': 'M1', '1MIN': 'M1', '1': 'M1',
                'M5': 'M5', '5M': 'M5', '5MIN': 'M5', '5': 'M5',
                'M15': 'M15', '15M': 'M15', '15MIN': 'M15', '15': 'M15',
                'M30': 'M30', '30M': 'M30', '30MIN': 'M30', '30': 'M30',
                'H1': 'H1', '1H': 'H1', '1HOUR': 'H1',
                'H4': 'H4', '4H': 'H4', '4HOUR': 'H4',
                'D1': 'D1', '1D': 'D1', 'DAILY': 'D1',
                'W1': 'W1', '1W': 'W1', 'WEEKLY': 'W1'
            }
            standardized['timeframe'] = tf_mapping.get(tf, tf)
        
        # Ajouter des champs calculés
        if 'entry' in standardized and 'stop_loss' in standardized and 'take_profit' in standardized:
            try:
                entry = float(standardized['entry'])
                sl = float(standardized['stop_loss'])
                tp = float(standardized['take_profit'])
                
                # Calculer la distance en points
                standardized['sl_distance'] = abs(entry - sl)
                standardized['tp_distance'] = abs(entry - tp)
                
                # Calculer le RR si non défini
                if 'risk_reward_ratio' not in standardized:
                    if standardized['sl_distance'] > 0:
                        standardized['risk_reward_ratio'] = standardized['tp_distance'] / standardized['sl_distance']
            except (ValueError, TypeError):
                pass
        
        return standardized
    
    def extract_batch(self, text_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Extrait les informations d'un batch de fichiers texte.
        
        Args:
            text_paths: Liste des chemins vers les fichiers texte
            
        Returns:
            Liste des informations extraites
        """
        results = []
        
        for path in text_paths:
            info = self.extract_info(path)
            standardized = self.standardize_setup_info(info)
            results.append({
                "file": path,
                "raw_info": info,
                "standardized_info": standardized
            })
        
        return results
    
    def save_to_json(self, setup_info: Dict[str, Any], output_path: str) -> bool:
        """
        Sauvegarde les informations extraites au format JSON.
        
        Args:
            setup_info: Informations extraites
            output_path: Chemin de sortie pour le fichier JSON
            
        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(setup_info, f, indent=2)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde en JSON: {e}")
            return False
    
    def text_to_structured_format(self, text: str) -> Dict[str, Any]:
        """
        Convertit un texte libre en format structuré.
        Utile pour générer un format standard à partir d'une description libre.
        
        Args:
            text: Texte libre à structurer
            
        Returns:
            Format structuré
        """
        # Extraire ce qu'on peut du texte libre
        info = self.extract_from_text(text)
        
        # Créer un template structuré
        template = {
            "setup": info.get("setup", ""),
            "action": info.get("action", ""),
            "entry": info.get("entry", ""),
            "stop_loss": info.get("stop_loss", ""),
            "take_profit": info.get("take_profit", ""),
            "risk_reward": info.get("risk_reward", ""),
            "timeframe": info.get("timeframe", ""),
            "indicators": info.get("indicators", {}),
            "context": info.get("context", ""),
            "reasons": info.get("reasons", ""),
            "notes": info.get("notes", "")
        }
        
        # Générer le texte structuré
        structured_text = f"""Setup: {template['setup']}
Action: {template['action']}
Entry: {template['entry']}
Stop Loss: {template['stop_loss']}
Take Profit: {template['take_profit']}
Risk:Reward: {template['risk_reward']}
Timeframe: {template['timeframe']}

Indicators:
"""
        
        # Ajouter les indicateurs
        for ind_name, ind_value in template["indicators"].items():
            structured_text += f"- {ind_name}: {ind_value}\n"
        
        # Ajouter les sections de texte
        if template["context"]:
            structured_text += f"\nContext:\n{template['context']}\n"
        
        if template["reasons"]:
            structured_text += f"\nReasons:\n{template['reasons']}\n"
        
        if template["notes"]:
            structured_text += f"\nNotes:\n{template['notes']}\n"
        
        return {
            "structured_text": structured_text,
            "structured_data": template
        }
    
    def generate_template(self) -> str:
        """
        Génère un template vide pour la création manuelle de descriptions de setup.
        
        Returns:
            Template au format texte
        """
        template = """Setup: [Type de setup, ex: Flag Pattern Breakout]
Action: [BUY/SELL]
Entry: [Niveau d'entrée]
Stop Loss: [Niveau de stop loss]
Take Profit: [Niveau de take profit]
Risk:Reward: [Ratio risque/récompense, ex: 1:2]
Timeframe: [Temporalité, ex: M15, H1]

Indicators:
- RSI: [Valeur ou état]
- MACD: [État: crossing up, divergence, etc.]
- EMA(20): [Valeur ou situation relative au prix]
- Bollinger: [Position par rapport aux bandes]

Context:
[Description du contexte de marché plus large, tendance sur timeframes supérieurs, niveau de supports/résistances importants, etc.]

Reasons:
[Raisons spécifiques pour prendre cette position, logique de trading, signaux confirmations, etc.]

Notes:
[Observations supplémentaires, considérations particulières, ou points d'attention]
"""
        return template
        
    def extract_key_elements(self, setup_info: Dict[str, Any]) -> List[str]:
        """
        Extrait les éléments clés d'un setup pour l'apprentissage.
        Fournit une liste de caractéristiques qui peuvent être utilisées pour l'entraînement.
        
        Args:
            setup_info: Informations du setup
            
        Returns:
            Liste des éléments clés
        """
        elements = []
        
        # Direction du trade
        if setup_info.get('action') == 'buy':
            elements.append('bullish_bias')
        elif setup_info.get('action') == 'sell':
            elements.append('bearish_bias')
        
        # Type de setup
        setup_type = setup_info.get('setup', '').lower()
        if setup_type:
            elements.append(f'setup_{setup_type.replace(" ", "_")}')
        
        # Indicateurs
        indicators = setup_info.get('indicators', {})
        for ind, value in indicators.items():
            ind_name = ind.lower().replace(' ', '_')
            
            # RSI
            if 'rsi' in ind_name:
                try:
                    rsi_value = float(value)
                    if rsi_value > 70:
                        elements.append('rsi_overbought')
                    elif rsi_value < 30:
                        elements.append('rsi_oversold')
                    elif 40 <= rsi_value <= 60:
                        elements.append('rsi_neutral')
                except (ValueError, TypeError):
                    if 'overbought' in value.lower():
                        elements.append('rsi_overbought')
                    elif 'oversold' in value.lower():
                        elements.append('rsi_oversold')
            
            # MACD
            if 'macd' in ind_name:
                if 'cross' in value.lower() and 'up' in value.lower():
                    elements.append('macd_bullish_cross')
                elif 'cross' in value.lower() and 'down' in value.lower():
                    elements.append('macd_bearish_cross')
                elif 'diverg' in value.lower() and ('pos' in value.lower() or 'bull' in value.lower()):
                    elements.append('macd_bullish_divergence')
                elif 'diverg' in value.lower() and ('neg' in value.lower() or 'bear' in value.lower()):
                    elements.append('macd_bearish_divergence')
            
            # Bollinger
            if 'bollinger' in ind_name or 'bb' in ind_name:
                if 'upper' in value.lower() or 'top' in value.lower():
                    elements.append('price_at_upper_bollinger')
                elif 'lower' in value.lower() or 'bottom' in value.lower():
                    elements.append('price_at_lower_bollinger')
                elif 'squeeze' in value.lower() or 'contract' in value.lower():
                    elements.append('bollinger_squeeze')
        
        # Risk/Reward
        if 'risk_reward_ratio' in setup_info:
            rr = setup_info['risk_reward_ratio']
            if rr >= 2:
                elements.append('high_reward_risk')
            elif rr >= 1:
                elements.append('balanced_reward_risk')
            else:
                elements.append('low_reward_risk')
        
        # Contexte et raisons
        context = setup_info.get('context', '').lower()
        reasons = setup_info.get('reasons', '').lower()
        combined_text = context + ' ' + reasons
        
        # Chercher des mots clés dans le texte
        key_patterns = {
            'support_test': ['test.*support', 'support.*test', 'bounce.*support'],
            'resistance_test': ['test.*resistance', 'resistance.*test', 'reject.*resistance'],
            'breakout': ['break.*out', 'breakout'],
            'breakdown': ['break.*down', 'breakdown'],
            'trend_continuation': ['continuation', 'with.*trend'],
            'trend_reversal': ['reversal', 'against.*trend', 'counter.*trend'],
            'double_top': ['double.*top'],
            'double_bottom': ['double.*bottom'],
            'head_shoulders': ['head.*shoulder', 'h.*s.*pattern'],
            'fibonacci_retracement': ['fibonacci', 'fib.*retrace'],
            'volume_confirmation': ['volume.*increas', 'high.*volume'],
            'low_volatility': ['low.*volatility', 'contract.*volatility'],
            'high_volatility': ['high.*volatility', 'volatility.*expan']
        }
        
        for element, patterns in key_patterns.items():
            for pattern in patterns:
                if re.search(pattern, combined_text):
                    elements.append(element)
                    break
        
        return elements