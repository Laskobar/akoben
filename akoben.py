#!/usr/bin/env python3
"""
Script principal pour lancer Akoben
"""
import sys
import argparse
from src.ui.cli import main as cli_main

def parse_args():
    """Parse les arguments de ligne de commande"""
    parser = argparse.ArgumentParser(description='Akoben - Système de trading automatisé')
    parser.add_argument('--ui', choices=['cli', 'web'], default='cli',
                        help='Interface utilisateur à utiliser (cli ou web)')
    return parser.parse_args()

def main():
    """Fonction principale"""
    args = parse_args()
    
    if args.ui == 'cli':
        cli_main()
    elif args.ui == 'web':
        print("Interface web non implémentée pour le moment. Utilisation de l'interface CLI.")
        cli_main()
    else:
        print(f"Interface {args.ui} inconnue. Utilisation de l'interface CLI.")
        cli_main()

if __name__ == "__main__":
    sys.exit(main())
