#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de standardisation des exemples de trading pour Akoben.
Ce script permet de traiter les exemples bruts de trading et de les convertir
en un format standardisé adapté à l'apprentissage par imitation.
Optimisé pour le format MBONGI.
"""

import os
import sys
import json
import re
import uuid
import logging
import argparse
from pathlib import Path
from datetime import datetime
import shutil

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("SetupStandardizer")

def extract_mbongi_info(text, setup_id):
    """
    Extrait les informations structurées à partir d'une description au format MBONGI.
    
    Args:
        text (str): Texte de description du setup au format MBONGI
        setup_id (str): Identifiant du setup pour extraction d'informations supplémentaires
        
    Returns:
        dict: Dictionnaire contenant les informations structurées
    """
    # Initialisation du dictionnaire de résultats
    setup_info = {
        'instrument': None,
        'timeframe': None,
        'date_time': None,
        'action': None,
        'entry_price': None,
        'stop_loss': None,
        'take_profit': None,
        'risk_reward': None,
        'confidence': None,
        'patterns': [],
        'indicators': [],
        'reasons': [],
        'market_context': None,
        'result': None
    }
    
    # Extraction de l'instrument
    instrument_match = re.search(r'Instrument:\s*(\w+)', text)
    if instrument_match:
        setup_info['instrument'] = instrument_match.group(1)
    
    # Extraction du timeframe
    timeframe_match = re.search(r'Unité de Temps:\s*(\w+)', text)
    if timeframe_match:
        setup_info['timeframe'] = timeframe_match.group(1)
    
    # Extraction de la date et heure
    datetime_match = re.search(r'Date et Heure:\s*([\d-]+)[\.|\s]+(.*?UTC[\+\-]\d+)', text)
    if datetime_match:
        setup_info['date_time'] = f"{datetime_match.group(1)} {datetime_match.group(2)}"
    
    # Extraction du type d'ordre (achat/vente)
    if "achat" in setup_id.lower() or "long" in text.lower() or "buy" in text.lower():
        setup_info['action'] = "BUY"
    elif "vente" in setup_id.lower() or "short" in text.lower() or "sell" in text.lower():
        setup_info['action'] = "SELL"
    else:
        # Recherche explicite dans le texte
        action_match = re.search(r"Type d[''']Ordre:\s*(\w+)", text)
        if action_match:
            action = action_match.group(1).upper()
            if action in ['ACHAT', 'LONG']:
                setup_info['action'] = 'BUY'
            elif action in ['VENTE', 'SHORT']:
                setup_info['action'] = 'SELL'
            else:
                setup_info['action'] = action
    
    # Extraction des prix
    entry_match = re.search(r"Prix d[''']Entrée:\s*(\d+\.?\d*)", text)
    if entry_match:
        setup_info['entry_price'] = float(entry_match.group(1))
    
    sl_match = re.search(r'Stop Loss \(SL\):\s*(\d+\.?\d*)', text)
    if sl_match:
        setup_info['stop_loss'] = float(sl_match.group(1))
    
    tp_match = re.search(r'Take Profit \(TP\):\s*(\d+\.?\d*)', text)
    if tp_match:
        setup_info['take_profit'] = float(tp_match.group(1))
    
    # Extraction du ratio risque/récompense
    rr_match = re.search(r'Ratio Risque[/\s]*Rendement:\s*(\d+\.?\d*):(\d+\.?\d*)', text)
    if rr_match:
        setup_info['risk_reward'] = f"{rr_match.group(1)}:{rr_match.group(2)}"
    
    # Extraction du niveau de confiance
    confidence_match = re.search(r'Niveau de confiance:\s*(\w+)', text)
    if confidence_match:
        setup_info['confidence'] = confidence_match.group(1)
    
    # Extraction des patterns
    pattern_section = re.search(r'Patterns identifiés:(.*?)(?:\n\n|\n##)', text, re.DOTALL)
    if pattern_section:
        patterns_text = pattern_section.group(1).strip()
        if patterns_text and "Aucun pattern" not in patterns_text:
            setup_info['patterns'] = [p.strip() for p in re.split(r',|\n', patterns_text) if p.strip()]
    
    # Recherche de patterns spécifiques dans tout le texte
    pattern_keywords = [
        'double top', 'double bottom', 'head and shoulders', 'inverse head and shoulders',
        'triangle', 'wedge', 'flag', 'pennant', 'channel', 'support', 'resistance',
        'trend line', 'fibonacci', 'divergence', 'englobante', 'doji', 'hammer', 'harami',
        'pullback', 'retracement', 'breakout'
    ]
    
    for pattern in pattern_keywords:
        if pattern not in setup_info['patterns'] and re.search(r'\b' + pattern + r'\b', text, re.IGNORECASE):
            setup_info['patterns'].append(pattern)
    
    # Extraction des indicateurs
    indicators_section = re.search(r'Indicateurs (utilisés|Techniques):(.*?)(?:\n\n|\n##)', text, re.DOTALL)
    if indicators_section:
        indicators_text = indicators_section.group(2).strip()
        if indicators_text and "Aucun indicateur" not in indicators_text:
            setup_info['indicators'] = [i.strip() for i in re.split(r',|\n', indicators_text) if i.strip()]
    
    # Recherche d'indicateurs spécifiques dans tout le texte
    indicator_keywords = [
        'MA', 'EMA', 'SMA', 'MACD', 'RSI', 'stochastic', 'bollinger',
        'ichimoku', 'ATR', 'volume', 'OBV', 'momentum', 'CCI', 'ADX', 'VPVR'
    ]
    
    for indicator in indicator_keywords:
        if indicator not in setup_info['indicators'] and re.search(r'\b' + indicator + r'\b', text, re.IGNORECASE):
            setup_info['indicators'].append(indicator)
    
    # Extraction des raisons
    reasons_section = re.search(r"Logique d[''']entrée:(.*?)(?:\n\n|\n##|Risques:)", text, re.DOTALL)
    if reasons_section:
        reasons_text = reasons_section.group(1).strip()
        setup_info['reasons'] = [r.strip() for r in re.split(r'\n-|\n•|\n\*', reasons_text) if r.strip()]
    
    # Extraction du contexte de marché
    context_section = re.search(r'Tendance Générale:(.*?)(?:\n\n|\n##|Fourchette de prix:)', text, re.DOTALL)
    if context_section:
        setup_info['market_context'] = context_section.group(1).strip()
    
    # Extraction du résultat
    result_section = re.search(r'Résultat \(Après Coup\)(.*?)(?:\n\n|\n##|Éléments d)', text, re.DOTALL)
    if result_section:
        result_text = result_section.group(1).strip()
        
        # Détecter le type de résultat
        if "Gain" in result_text:
            setup_info['result'] = "WIN"
        elif "Perte" in result_text:
            setup_info['result'] = "LOSS"
        
        # Extraire le montant du gain/perte
        amount_match = re.search(r'Montant du gain/perte:\s*([+-]\d+)', result_text)
        if amount_match:
            setup_info['result_amount'] = amount_match.group(1)
    
    return setup_info

def format_mbongi_description(setup_id, setup_info):
    """
    Crée une version formatée et standardisée de la description MBONGI.
    
    Args:
        setup_id (str): ID du setup
        setup_info (dict): Informations structurées du setup
        
    Returns:
        str: Description formatée
    """
    formatted_description = f"""# Setup {setup_id}

## Informations générales
- Instrument: {setup_info['instrument'] or 'Non spécifié'}
- Timeframe: {setup_info['timeframe'] or 'Non spécifié'}
- Date et heure: {setup_info['date_time'] or 'Non spécifié'}

## Action de trading
{setup_info['action'] or 'Non spécifiée'}

## Niveaux de prix
- Entrée: {setup_info['entry_price'] or 'Non spécifié'}
- Stop Loss: {setup_info['stop_loss'] or 'Non spécifié'}
- Take Profit: {setup_info['take_profit'] or 'Non spécifié'}

## Ratio Risk/Reward
{setup_info['risk_reward'] or 'Non spécifié'}

## Niveau de confiance
{setup_info['confidence'] or 'Non spécifié'}

## Patterns identifiés
{', '.join(setup_info['patterns']) if setup_info['patterns'] else 'Aucun pattern spécifié'}

## Indicateurs utilisés
{', '.join(setup_info['indicators']) if setup_info['indicators'] else 'Aucun indicateur spécifié'}

## Raisons d'entrée
{os.linesep.join(['- ' + r for r in setup_info['reasons']]) if setup_info['reasons'] else 'Non spécifiées'}

## Contexte de marché
{setup_info['market_context'] or 'Non spécifié'}

## Résultat
- Statut: {setup_info.get('result') or 'Non spécifié'}
- Montant: {setup_info.get('result_amount') or 'Non spécifié'}
"""
    return formatted_description

def extract_setup_info(text):
    """
    Extrait les informations structurées à partir d'une description textuelle de setup.
    
    Args:
        text (str): Texte de description du setup
        
    Returns:
        dict: Dictionnaire contenant les informations structurées
    """
    # Initialisation du dictionnaire de résultats
    setup_info = {
        'action': None,
        'timeframe': None,
        'entry_price': None,
        'stop_loss': None,
        'take_profit': None,
        'risk_reward': None,
        'confidence': None,
        'reasons': [],
        'patterns': [],
        'indicators': [],
        'market_context': None
    }
    
    # Recherche de l'action (BUY ou SELL)
    action_match = re.search(r'\b(BUY|SELL|LONG|SHORT)\b', text, re.IGNORECASE)
    if action_match:
        action = action_match.group(0).upper()
        if action in ['LONG']:
            setup_info['action'] = 'BUY'
        elif action in ['SHORT']:
            setup_info['action'] = 'SELL'
        else:
            setup_info['action'] = action
    
    # Recherche du timeframe
    timeframe_match = re.search(r'\b(M1|M5|M15|M30|H1|H4|D1|W1)\b', text)
    if timeframe_match:
        setup_info['timeframe'] = timeframe_match.group(0)
    
    # Recherche des prix d'entrée, stop loss et take profit
    entry_match = re.search(r'entry\s*(?:price|level|point)?\s*(?:at|:|\s)\s*(\d+\.?\d*)', text, re.IGNORECASE)
    if entry_match:
        setup_info['entry_price'] = float(entry_match.group(1))
    
    sl_match = re.search(r'stop\s*loss\s*(?:at|:|\s)\s*(\d+\.?\d*)', text, re.IGNORECASE)
    if sl_match:
        setup_info['stop_loss'] = float(sl_match.group(1))
    
    tp_match = re.search(r'take\s*profit\s*(?:at|:|\s)\s*(\d+\.?\d*)', text, re.IGNORECASE)
    if tp_match:
        setup_info['take_profit'] = float(tp_match.group(1))
    
    # Recherche du risk/reward ratio
    rr_match = re.search(r'risk[/\s]*reward\s*(?:ratio|:|\s)\s*(\d+\.?\d*)[:/](\d+\.?\d*)', text, re.IGNORECASE)
    if rr_match:
        r = float(rr_match.group(1))
        rw = float(rr_match.group(2))
        setup_info['risk_reward'] = rw/r if r != 0 else None
    
    # Recherche du niveau de confiance
    confidence_match = re.search(r'confidence\s*(?:level|:|\s)\s*(\d+)%?', text, re.IGNORECASE)
    if confidence_match:
        setup_info['confidence'] = int(confidence_match.group(1))
    
    # Recherche des patterns
    pattern_keywords = [
        'double top', 'double bottom', 'head and shoulders', 'inverse head and shoulders',
        'triangle', 'wedge', 'flag', 'pennant', 'channel', 'support', 'resistance',
        'trend line', 'fibonacci', 'divergence', 'engulfing', 'doji', 'hammer', 'harami'
    ]
    
    for pattern in pattern_keywords:
        if re.search(r'\b' + pattern + r'\b', text, re.IGNORECASE):
            setup_info['patterns'].append(pattern)
    
    # Recherche des indicateurs
    indicator_keywords = [
        'MA', 'EMA', 'SMA', 'MACD', 'RSI', 'stochastic', 'bollinger',
        'ichimoku', 'ATR', 'volume', 'OBV', 'momentum', 'CCI', 'ADX'
    ]
    
    for indicator in indicator_keywords:
        if re.search(r'\b' + indicator + r'\b', text, re.IGNORECASE):
            setup_info['indicators'].append(indicator)
    
    # Extraction des raisons (analyse plus complexe, simplifiée ici)
    reason_matches = re.findall(r'because\s+([^.]*\.)', text, re.IGNORECASE)
    setup_info['reasons'] = reason_matches
    
    # Context de marché (tendance globale, volatilité, etc.)
    context_matches = re.search(r'market\s+(?:is|seems|appears)\s+([^.]*\.)', text, re.IGNORECASE)
    if context_matches:
        setup_info['market_context'] = context_matches.group(1)
    
    return setup_info

def find_description_file(setup_id, project_root):
    """
    Recherche un fichier de description pour le setup dans différents emplacements du projet.
    
    Args:
        setup_id (str): ID du setup
        project_root (Path): Chemin racine du projet
        
    Returns:
        Path: Chemin vers le fichier de description, ou None si non trouvé
    """
    # Liste des emplacements possibles pour rechercher le fichier de description
    search_paths = [
        project_root / "data" / "setups" / "us30" / setup_id / f"{setup_id}.txt",
        project_root / "data" / "setups" / "us30" / f"{setup_id}.txt",
        project_root / "data" / "setups" / f"{setup_id}.txt",
        project_root / "data" / f"{setup_id}.txt",
        # Recherche directe dans le dossier data/setups
        project_root / "data" / "setups" / "us30" / setup_id / "description.txt",
    ]
    
    # Rechercher globalement dans le projet (peut être lent mais exhaustif)
    for path in search_paths:
        if path.exists():
            return path
    
    # Recherche récursive dans tout le projet (à utiliser en dernier recours)
    for root, dirs, files in os.walk(str(project_root)):
        for file in files:
            if file == f"{setup_id}.txt" or (file.endswith(".txt") and setup_id in file):
                return Path(root) / file
    
    return None

def standardize_setup(input_dir, output_dir, setup_id=None, project_root=None):
    """
    Standardise un setup spécifique ou tous les setups dans le répertoire d'entrée.
    
    Args:
        input_dir (str): Répertoire contenant les setups bruts
        output_dir (str): Répertoire où sauvegarder les setups standardisés
        setup_id (str, optional): ID du setup à standardiser. Si None, traite tous les setups.
        project_root (Path, optional): Chemin racine du projet pour la recherche de fichiers.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Définir project_root s'il n'est pas fourni
    if project_root is None:
        project_root = input_path.parent.parent  # Remonte de deux niveaux depuis input_dir
    
    # Création du répertoire de sortie s'il n'existe pas
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Liste des répertoires de setup à traiter
    if setup_id:
        setup_dirs = [input_path / setup_id]
        if not setup_dirs[0].exists():
            logger.error(f"Le setup {setup_id} n'existe pas dans {input_dir}")
            return
    else:
        setup_dirs = [d for d in input_path.iterdir() if d.is_dir()]
    
    total_setups = len(setup_dirs)
    processed_setups = 0
    
    for setup_dir in setup_dirs:
        setup_id = setup_dir.name
        logger.info(f"Traitement du setup {setup_id}...")
        
        # Vérification des fichiers nécessaires
        image_files = list(setup_dir.glob("*.png")) + list(setup_dir.glob("*.jpg"))
        
        # Recherche avancée du fichier de description
        description_file = find_description_file(setup_id, project_root)
        
        if not description_file:
            logger.warning(f"Le setup {setup_id} ne contient pas de description. Ignoré.")
            continue
        
        if not image_files:
            logger.warning(f"Le setup {setup_id} ne contient pas d'image. Ignoré.")
            continue
        
        # Lecture de la description
        with open(description_file, 'r', encoding='utf-8') as f:
            description_text = f.read()
        
        logger.info(f"Fichier de description trouvé: {description_file}")
        
        # Extraction des informations pour le format MBONGI
        setup_info = extract_mbongi_info(description_text, setup_id)
        
        # Création du répertoire de sortie pour ce setup
        output_setup_dir = output_path / setup_id
        output_setup_dir.mkdir(exist_ok=True)
        
        # Copie des images
        for img_file in image_files:
            shutil.copy2(img_file, output_setup_dir)
        
        # Création du fichier de métadonnées standardisé
        metadata = {
            'id': setup_id,
            'original_description': description_text,
            'standardized_info': setup_info,
            'timestamp': datetime.now().isoformat(),
            'image_files': [img.name for img in image_files]
        }
        
        # Sauvegarde des métadonnées
        with open(output_setup_dir / 'metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # Sauvegarde d'une version formatée de la description
        formatted_description = format_mbongi_description(setup_id, setup_info)
        
        with open(output_setup_dir / 'formatted_description.md', 'w', encoding='utf-8') as f:
            f.write(formatted_description)
        
        processed_setups += 1
        logger.info(f"Setup {setup_id} standardisé avec succès!")
    
    logger.info(f"Standardisation terminée. {processed_setups}/{total_setups} setups traités.")

def create_new_setup_template(output_dir):
    """
    Crée un nouveau template de setup standardisé pour faciliter l'ajout de nouveaux exemples.
    
    Args:
        output_dir (str): Répertoire où sauvegarder le template
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Génération d'un ID unique
    setup_id = f"setup_{datetime.now().strftime('%Y%m%d')}_{str(uuid.uuid4())[:8]}"
    template_dir = output_path / setup_id
    template_dir.mkdir(exist_ok=True)
    
    # Création du template de description au format MBONGI
    template_description = """Format MBONGI
Contexte Général

Instrument: INSTRUMENT
Unité de Temps: TIMEFRAME (M1, M5, M15, M30, H1, H4, D1)
Date et Heure: YYYY-MM-DD. Analyse initiale autour de HH:MM UTC+1. Entrée à HH:MM UTC+1.
Tendance Générale:

M15: DESCRIPTION_TENDANCE_M15
M5: DESCRIPTION_TENDANCE_M5
M1: DESCRIPTION_TENDANCE_M1
Conclusion: CONCLUSION_GENERALE

Fourchette de prix: PRIX_MIN - PRIX_MAX
Captures d'Écran:

M1 (avant trade): /chemin/vers/image_M1.png
M1 (après trade): /chemin/vers/image_resultat.png
M5 (avant trade): /chemin/vers/image_M5.png
M15 (avant trade): /chemin/vers/image_M15.png

Analyse Technique (Pré-Trade)

Structure du Marché:
M1:
DESCRIPTION_STRUCTURE_M1

M5:
DESCRIPTION_STRUCTURE_M5

M15:
DESCRIPTION_STRUCTURE_M15

Indicateurs Techniques:
Moyennes Mobiles:
DESCRIPTION_MOYENNES_MOBILES

RSI (14, close):
DESCRIPTION_RSI

Volume net:
DESCRIPTION_VOLUME

Volume Profile (VPVR):
DESCRIPTION_VPVR

Chandeliers:
DESCRIPTION_CHANDELIERS

Décision de Trading

Type d'Ordre: ACHAT ou VENTE
Prix d'Entrée: PRIX_ENTREE
Stop Loss (SL): PRIX_SL
Take Profit (TP): PRIX_TP
Taille de la Position: TAILLE_POSITION
Ratio Risque/Rendement: RATIO_RR (points de risque pour points de gain potentiel)

Justification (Raisonnement - Purement Technique)

Logique d'entrée:
- RAISON_1
- RAISON_2
- RAISON_3

Risques:
- RISQUE_1
- RISQUE_2

Niveau de confiance: NIVEAU_CONFIANCE

Résultat (Après Coup)

Ordre exécuté ? OUI/NON
Prix d'exécution: PRIX_EXECUTION
Résultat: GAIN/PERTE
Montant du gain/perte: +/- POINTS
Analyse post-trade (technique):
DESCRIPTION_ANALYSE_POST_TRADE

Fin MBONGI
"""
    
    with open(template_dir / 'description_template.md', 'w', encoding='utf-8') as f:
        f.write(template_description)
    
    # Fichier README pour expliquer comment compléter le template
    readme = """# Comment utiliser ce template de setup au format MBONGI

1. Complétez le fichier 'description_template.md' avec les détails de votre setup
2. Ajoutez les captures d'écran du graphique dans ce dossier (format PNG ou JPG)
3. Renommez ce dossier selon le format 'YYYY-MM-DD_HH-MM_TIMEFRAME_INSTRUMENT_ACTION_TYPE1_TYPE2_XX'
   Exemple: '2025-03-05_17-53_M1_US30_achat_divergence_englobante_16'
4. Exécutez le script de standardisation pour générer les métadonnées

Note: Le format MBONGI est conçu pour capturer tous les détails importants d'un setup de trading.
Soyez aussi précis et complet que possible pour permettre au système d'apprentissage par imitation
de comprendre votre processus décisionnel.
"""
    
    with open(template_dir / 'README.md', 'w', encoding='utf-8') as f:
        f.write(readme)
    
    logger.info(f"Template de setup créé: {template_dir}")
    return template_dir

def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(description="Standardisation des exemples de trading pour Akoben")
    parser.add_argument('--input_dir', '-i', type=str, help="Répertoire contenant les setups bruts")
    parser.add_argument('--output_dir', '-o', type=str, help="Répertoire où sauvegarder les setups standardisés")
    parser.add_argument('--setup_id', '-s', type=str, help="ID du setup à standardiser (optionnel)")
    parser.add_argument('--create_template', '-t', action='store_true', help="Créer un nouveau template de setup")
    
    args = parser.parse_args()
    
    # Définition des répertoires par défaut
    current_dir = Path(__file__).resolve().parent
    project_dir = current_dir.parent.parent  # Remonter au répertoire racine du projet
    default_input_dir = project_dir / "data" / "setups" / "us30"
    default_output_dir = project_dir / "data" / "setups" / "standardized"
    
    input_dir = args.input_dir or str(default_input_dir)
    output_dir = args.output_dir or str(default_output_dir)
    
    if args.create_template:
        template_dir = create_new_setup_template(output_dir)
        print(f"\nTemplate de setup créé dans: {template_dir}")
        print("Complétez le fichier 'description_template.md' et ajoutez vos captures d'écran.")
    else:
        if not Path(input_dir).exists():
            logger.error(f"Le répertoire d'entrée {input_dir} n'existe pas.")
            return
        
        # Ajout du chemin du projet racine pour la recherche avancée de fichiers
        project_root = Path.cwd()
        logger.info(f"Recherche de fichiers dans: {project_root}")
        
        standardize_setup(input_dir, output_dir, args.setup_id, project_root)
        print(f"\nLes setups standardisés ont été sauvegardés dans: {output_dir}")

if __name__ == "__main__":
    main()