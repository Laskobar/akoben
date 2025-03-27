# ~/akoben-clean/src/agents/vision/vision_analyzer.py
import cv2
import os
import numpy as np

# Définir les chemins de base (à ajuster si nécessaire)
# Attention: Utilisation de chemins absolus pour plus de robustesse lors de l'exécution depuis différents endroits.
AKOBEN_CLEAN_DIR = "/home/lasko/akoben-clean" # Chemin vers le code source
AKOBEN_RUNTIME_DIR = "/home/lasko/akoben"     # Chemin vers les données opérationnelles

def load_and_display_info(relative_image_path_in_runtime: str):
    """
    Charge une image depuis le dossier opérationnel (~/akoben) et affiche ses dimensions.

    Args:
        relative_image_path_in_runtime (str): Chemin relatif de l'image DANS le dossier ~/akoben/tradingview_captures/
                                              (ex: '2025-03-26/chart.png' ou 'image.png')
    """
    # Construire le chemin complet vers l'image
    image_path = os.path.join(AKOBEN_RUNTIME_DIR, "tradingview_captures", relative_image_path_in_runtime)
    print(f"Tentative de chargement de l'image : {image_path}")

    # Vérifier si le fichier existe avant de tenter de le lire
    if not os.path.exists(image_path):
        print(f"ERREUR : Le fichier image n'existe pas à l'emplacement : {image_path}")
        return

    # Charger l'image en utilisant OpenCV
    # cv2.IMREAD_COLOR (ou 1) charge l'image en couleur (par défaut)
    # cv2.IMREAD_GRAYSCALE (ou 0) charge en niveaux de gris
    # cv2.IMREAD_UNCHANGED (ou -1) charge avec le canal alpha si présent
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)

    # Vérifier si l'image a été chargée correctement
    if img is None:
        print(f"ERREUR : Impossible de charger l'image depuis : {image_path}")
        print("Vérifiez le chemin, les permissions et l'intégrité du fichier.")
    else:
        # Obtenir les dimensions (hauteur, largeur, nombre de canaux)
        height, width, channels = img.shape
        print(f"Image chargée avec succès.")
        print(f"  - Dimensions (Hauteur x Largeur) : {height} x {width} pixels")
        print(f"  - Nombre de canaux de couleur : {channels}")
        # Afficher un extrait des données (optionnel)
        # print(f"  - Type de données Numpy : {img.dtype}")
        # print(f"  - Premiers pixels : \n{img[0:2, 0:2]}") # Affiche les 2x2 premiers pixels

# --- Point d'entrée pour l'exécution directe du script ---
if __name__ == "__main__":
    print("--- Test de chargement d'image pour l'Agent de Vision Akoben ---")

    # !!! IMPORTANT : Remplacez ceci par le chemin relatif d'une image réelle !!!
    # Exemple: '2025-03-26/nom_de_votre_image.png' ou 'nom_image_racine.png'
    # Assurez-vous que cette image existe bien dans ~/akoben/tradingview_captures/
    test_image_relative_path = '2025-03-26/setup_20250326083927/original.png' # <--- METTRE UN VRAI NOM DE FICHIER ICI

    if test_image_relative_path == 'VOTRE_IMAGE_ICI.png':
         print("\n!!! ATTENTION : Veuillez modifier la variable 'test_image_relative_path' dans le code !!!\n")
    else:
        load_and_display_info(test_image_relative_path)

    print("--- Fin du test ---")