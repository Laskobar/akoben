#!/usr/bin/env python3
'''
Script d'importation des captures d'écran TradingView pour Akoben.
'''
import os
import sys

# Ajoute le répertoire parent au chemin d'import
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.tools.tradingview_importer_impl import TradingViewImporter

def main():
    importer = TradingViewImporter()
    importer.run()

if __name__ == "__main__":
    main()