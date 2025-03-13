import os
import sys
import time

# Ajoutez le répertoire parent au chemin pour pouvoir importer nos modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.anansi.core import Anansi

def clear_screen():
    """Efface l'écran du terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Affiche l'en-tête de l'application"""
    clear_screen()
    print("\n" + "="*50)
    print("             AKOBEN - SYSTÈME DE TRADING")
    print("="*50)
    print("Tapez 'exit' pour quitter, 'help' pour l'aide\n")

def print_help():
    """Affiche l'aide"""
    print("\n" + "-"*50)
    print("COMMANDES DISPONIBLES:")
    print("-"*50)
    print("help           - Affiche ce message d'aide")
    print("exit           - Quitte l'application")
    print("history        - Affiche l'historique des conversations")
    print("clear          - Efface l'écran")
    print("\nEXEMPLES DE QUESTIONS:")
    print("-"*50)
    print("- Analyse les tendances actuelles du US30")
    print("- Développe une stratégie de trading basée sur les moyennes mobiles")
    print("- Quels sont les meilleurs indicateurs pour le trading du US30?")
    print("-"*50 + "\n")

def main():
    """Fonction principale de l'interface en ligne de commande"""
    # Initialiser Anansi
    anansi = Anansi()
    
    print_header()
    print("Initialisation d'Anansi terminée. Prêt à interagir.\n")
    
    while True:
        try:
            # Demander l'instruction à l'utilisateur
            user_input = input("\033[1;32mVous:\033[0m ")
            
            # Traiter les commandes spéciales
            if user_input.lower() == 'exit':
                print("\nFermeture d'Akoben. À bientôt!")
                break
            elif user_input.lower() == 'help':
                print_help()
                continue
            elif user_input.lower() == 'clear':
                print_header()
                continue
            elif user_input.lower() == 'history':
                history = anansi.get_conversation_history()
                print("\n" + "-"*50)
                print("HISTORIQUE DES CONVERSATIONS:")
                print("-"*50)
                for entry in history:
                    role = "Vous" if entry["role"] == "user" else "Anansi"
                    print(f"[{entry['timestamp']}] {role}: {entry['content'][:50]}...")
                print("-"*50 + "\n")
                continue
            
            # Si ce n'est pas une commande spéciale, traiter comme une instruction
            if user_input.strip():
                print("\nTraitement en cours...\n")
                
                # Obtenir la réponse d'Anansi
                start_time = time.time()
                response = anansi.process_instruction(user_input)
                end_time = time.time()
                
                # Afficher la réponse
                print(f"\033[1;34mAnansi\033[0m ({end_time - start_time:.2f}s):")
                print(f"{response}\n")
            
        except KeyboardInterrupt:
            print("\n\nInterruption détectée. Pour quitter, tapez 'exit'.")
        except Exception as e:
            print(f"\n\033[1;31mErreur:\033[0m {str(e)}")
    
if __name__ == "__main__":
    main()
