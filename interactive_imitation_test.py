"""
Test de l'infrastructure d'apprentissage par imitation.
"""

import os
import sys
import json
from datetime import datetime

# Ajouter le répertoire parent au path pour pouvoir importer les modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.learning.imitation_learning_manager import ImitationLearningManager
from src.tools.setup_database_manager import SetupDatabaseManager
from src.tools.setup_text_processor import SetupTextProcessor

def main():
    """
    Fonction principale de test.
    """
    print("=== Test de l'infrastructure d'apprentissage par imitation ===")
    
    # Initialiser les composants
    print("\nInitialisation des composants...")
    imitation_manager = ImitationLearningManager()
    setup_db = SetupDatabaseManager()
    text_processor = SetupTextProcessor()
    
    # Afficher des statistiques de base
    print("\nStatistiques de la base de données de setups:")
    stats = setup_db.get_statistics()
    print(f"- Total de setups: {stats.get('total_setups', 0)}")
    print(f"- Types de setup: {stats.get('setup_types', {})}")
    print(f"- Distribution des actions: {stats.get('action_distribution', {})}")
    
    # Vérifier les modèles disponibles
    print("\nModèles d'imitation disponibles:")
    models = imitation_manager.get_available_models()
    if models:
        for i, model in enumerate(models):
            print(f"{i+1}. {model.get('id')} - Créé le: {model.get('created')}")
            print(f"   Type: {model.get('model_type')}, Précision: {model.get('accuracy', 0)*100:.1f}%")
    else:
        print("Aucun modèle disponible. Vous devez en entraîner un.")
    
    # Menu d'options
    while True:
        print("\nOptions:")
        print("1. Ajouter un exemple de setup")
        print("2. Entraîner un nouveau modèle")
        print("3. Tester le modèle sur un exemple")
        print("4. Afficher les types de setup disponibles")
        print("5. Quitter")
        
        choice = input("\nChoisissez une option (1-5): ")
        
        if choice == "1":
            add_setup_example(setup_db, text_processor)
        elif choice == "2":
            train_model(imitation_manager)
        elif choice == "3":
            test_model(imitation_manager, text_processor)
        elif choice == "4":
            display_setup_types(setup_db)
        elif choice == "5":
            print("Au revoir!")
            break
        else:
            print("Option non valide. Veuillez réessayer.")


def add_setup_example(setup_db, text_processor):
    """
    Ajoute un exemple de setup dans la base de données.
    """
    print("\n=== Ajout d'un exemple de setup ===")
    
    # Demander les informations
    setup_type = input("Type de setup (ex: breakout, support_resistance, trend_following): ")
    action = input("Action de trading (BUY, SELL, WAIT): ").upper()
    
    # Créer une description à partir d'un template
    template = text_processor.generate_template()
    print(f"\nVoici un template pour la description:\n{template}")
    
    # Laisser l'utilisateur modifier le template ou entrer sa propre description
    description = input("\nEntrez la description du setup (ou appuyez sur Entrée pour utiliser le template): ")
    if not description.strip():
        description = template
    
    # Pour ce test, nous ne demanderons pas d'image, nous utiliserons juste la description
    # Dans une application réelle, vous voudriez charger une image de graphique
    
    # Générer un ID pour le fichier
    setup_id = f"{setup_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Créer le répertoire de destination si nécessaire
    data_dir = os.path.join("data", "training", setup_type)
    os.makedirs(data_dir, exist_ok=True)
    
    # Chemin du fichier texte
    text_path = os.path.join(data_dir, f"{setup_id}.txt")
    
    # Enregistrer la description
    with open(text_path, 'w') as f:
        f.write(description)
    
    print(f"Description enregistrée dans {text_path}")
    
    # Pour simuler une image, nous créons un fichier vide
    image_path = os.path.join(data_dir, f"{setup_id}.png")
    with open(image_path, 'w') as f:
        f.write("# Placeholder for image data")
    
    print(f"Image placeholder créé dans {image_path}")
    
    # Rafraîchir l'index
    setup_db.refresh_index()
    print("Index rafraîchi. L'exemple a été ajouté à la base de données.")


def train_model(imitation_manager):
    """
    Entraîne un nouveau modèle d'imitation.
    """
    print("\n=== Entraînement d'un nouveau modèle ===")
    
    # Demander le type de modèle
    print("Types de modèles disponibles:")
    print("1. baseline (Régression logistique)")
    print("2. decision_tree (Arbre de décision)")
    print("3. random_forest (Forêt aléatoire)")
    
    model_choice = input("Choisissez un type de modèle (1-3): ")
    
    if model_choice == "1":
        model_type = "baseline"
    elif model_choice == "2":
        model_type = "decision_tree"
    elif model_choice == "3":
        model_type = "random_forest"
    else:
        print("Choix non valide. Utilisation du modèle baseline par défaut.")
        model_type = "baseline"
    
    # Demander s'il faut filtrer par type de setup
    use_filter = input("Voulez-vous filtrer les données par type de setup? (o/n): ").lower() == 'o'
    
    setup_types = None
    if use_filter:
        setup_types_input = input("Entrez les types de setup séparés par des virgules: ")
        setup_types = [s.strip() for s in setup_types_input.split(',') if s.strip()]
    
    # Entraîner le modèle
    print(f"\nEntraînement du modèle {model_type}...")
    result = imitation_manager.train_imitation_model(model_type=model_type, training_data=None)
    
    if result:
        print(f"Modèle entraîné avec succès!")
        print(f"- Type: {result.get('model_type')}")
        print(f"- Précision: {result.get('metrics', {}).get('accuracy', 0)*100:.1f}%")
        print(f"- Nombre d'échantillons: {result.get('metrics', {}).get('sample_count', 0)}")
    else:
        print("Échec de l'entraînement du modèle. Vérifiez les logs pour plus de détails.")


def test_model(imitation_manager, text_processor):
    """
    Teste le modèle actuel sur un exemple.
    """
    print("\n=== Test du modèle sur un exemple ===")
    
    # Vérifier si un modèle est chargé
    if not imitation_manager.current_model:
        print("Aucun modèle n'est actuellement chargé. Chargement du modèle le plus récent...")
        model_result = imitation_manager.load_model()
        
        if not model_result:
            print("Échec du chargement du modèle. Veuillez d'abord entraîner un modèle.")
            return
    
    # Demander une description
    print("Entrez une description de setup pour tester le modèle.")
    print("Exemple: Support à 38500, RSI en zone de survente, prix au-dessus de la MA20.")
    description = input("\nDescription: ")
    
    if not description.strip():
        print("Description vide. Test annulé.")
        return
    
    # Structurer la description
    structured_result = text_processor.text_to_structured_format(description)
    structured_text = structured_result.get("structured_text", "")
    
    print(f"\nDescription structurée:\n{structured_text}")
    
    # Faire une prédiction
    print("\nPrédiction en cours...")
    prediction = imitation_manager.predict_from_setup(text_description=structured_text)
    
    if prediction:
        print(f"\nAction prédite: {prediction.get('action')}")
        
        # Afficher les confiances si disponibles
        if 'confidences' in prediction:
            print("\nConfiances:")
            for action, conf in sorted(prediction['confidences'].items(), key=lambda x: x[1], reverse=True):
                print(f"- {action}: {conf*100:.1f}%")
        
        # Afficher l'explication
        print("\nExplication:")
        print(prediction.get('explanation', 'Aucune explication disponible.'))
    else:
        print("Échec de la prédiction. Vérifiez les logs pour plus de détails.")


def display_setup_types(setup_db):
    """
    Affiche les types de setup disponibles.
    """
    print("\n=== Types de setup disponibles ===")
    
    # Rafraîchir l'index pour s'assurer qu'il est à jour
    setup_db.refresh_index()
    
    # Récupérer les types de setup
    setup_types = setup_db.get_all_setup_types()
    
    if setup_types:
        for i, setup_type in enumerate(setup_types):
            setups = setup_db.get_setups_by_type(setup_type)
            print(f"{i+1}. {setup_type} ({len(setups)} exemples)")
    else:
        print("Aucun type de setup trouvé dans la base de données.")


if __name__ == "__main__":
    main()