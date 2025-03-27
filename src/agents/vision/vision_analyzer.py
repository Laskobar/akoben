# ~/akoben-clean/src/agents/vision/vision_analyzer.py
import cv2
import os
import numpy as np
import math

# Définir les chemins de base
AKOBEN_CLEAN_DIR = "/home/lasko/akoben-clean"
AKOBEN_RUNTIME_DIR = "/home/lasko/akoben"

def analyze_image_lines(relative_image_path_in_runtime: str):
    """
    Charge une image, détecte les contours, puis détecte les lignes droites
    (horizontales et verticales) via la transformée de Hough probabiliste.
    Sauvegarde une image avec les lignes détectées dessinées.

    Args:
        relative_image_path_in_runtime (str): Chemin relatif de l'image DANS ~/akoben/tradingview_captures/
    """
    image_path = os.path.join(AKOBEN_RUNTIME_DIR, "tradingview_captures", relative_image_path_in_runtime)
    print(f"Analyse des lignes pour l'image : {image_path}")

    if not os.path.exists(image_path):
        print(f"ERREUR : Le fichier image n'existe pas : {image_path}")
        return

    # Charger l'image en couleur pour y dessiner plus tard
    img_color = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img_color is None:
        print(f"ERREUR : Impossible de charger l'image : {image_path}")
        return
    height, width, _ = img_color.shape
    print(f"Image couleur chargée ({height}x{width}).")

    # Prétraitement : Niveaux de gris, Flou, Canny (comme avant)
    img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
    img_blurred = cv2.GaussianBlur(img_gray, (5, 5), 0)
    edges = cv2.Canny(img_blurred, 50, 150)
    print(f"  - Prétraitement (Gris, Flou, Canny) effectué.")

    # 2. Détection de lignes avec HoughLinesP
    # Arguments de cv2.HoughLinesP:
    # - edges: L'image des contours (sortie de Canny).
    # - rho=1: Résolution de distance en pixels.
    # - theta=np.pi/180: Résolution angulaire en radians (ici, 1 degré).
    # - threshold=50: Nombre minimum d'intersections pour détecter une ligne.
    # - minLineLength=50: Longueur minimale d'une ligne en pixels.
    # - maxLineGap=10: Écart maximal autorisé entre des segments pour les considérer comme une seule ligne.
    # Vous devrez peut-être ajuster threshold, minLineLength et maxLineGap pour vos graphiques.
    lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi/180, threshold=50, minLineLength=50, maxLineGap=10)

    horizontal_lines = []
    vertical_lines = []

    if lines is not None:
        print(f"  - HoughLinesP a détecté {len(lines)} segments de ligne potentiels.")
        for line in lines:
            x1, y1, x2, y2 = line[0]

            # Calculer l'angle de la ligne
            angle = math.degrees(math.atan2(y2 - y1, x2 - x1))

            # Filtrer les lignes approximativement horizontales (proches de 0 ou 180 degrés)
            # Tolérance de +/- quelques degrés (ex: 2 degrés)
            if abs(angle) < 2 or abs(angle - 180) < 2 or abs(angle + 180) < 2 :
                 # Vérifier aussi une longueur minimale pour éviter les petits segments bruités
                length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                if length > 50: # Gardons la même longueur minimale que HoughLinesP ou un peu plus
                    horizontal_lines.append(line[0])
            # Filtrer les lignes approximativement verticales (proches de 90 ou -90 degrés)
            elif abs(angle - 90) < 2 or abs(angle + 90) < 2:
                length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                if length > 50:
                     vertical_lines.append(line[0])
        print(f"  - Filtré : {len(horizontal_lines)} lignes horizontales et {len(vertical_lines)} lignes verticales.")
    else:
        print("  - Aucune ligne détectée par HoughLinesP.")

    # 3. Dessiner les lignes détectées sur une copie de l'image originale
    img_with_lines = img_color.copy()

    # Dessiner les lignes horizontales en bleu (BGR: 255, 0, 0)
    for x1, y1, x2, y2 in horizontal_lines:
        cv2.line(img_with_lines, (x1, y1), (x2, y2), (255, 0, 0), 2) # Bleu, épaisseur 2

    # Dessiner les lignes verticales en vert (BGR: 0, 255, 0)
    for x1, y1, x2, y2 in vertical_lines:
        cv2.line(img_with_lines, (x1, y1), (x2, y2), (0, 255, 0), 2) # Vert, épaisseur 2

    # 4. Sauvegarder l'image avec les lignes
    output_lines_path = os.path.join(AKOBEN_CLEAN_DIR, "output_detected_lines.png")
    try:
        cv2.imwrite(output_lines_path, img_with_lines)
        print(f"  - Image avec lignes horizontales (bleu) et verticales (vert) sauvegardée : {output_lines_path}")
    except Exception as e:
        print(f"  - ERREUR lors de la sauvegarde de l'image avec lignes : {e}")

# --- Point d'entrée ---
if __name__ == "__main__":
    print("--- Test d'analyse d'image (Détection de Lignes Horizontales/Verticales) ---")

    test_image_relative_path = '2025-03-26/setup_20250326083927/original.png' # <--- Vérifiez si c'est toujours bon

    if test_image_relative_path == 'VOTRE_IMAGE_ICI.png':
         print("\n!!! ATTENTION : Veuillez modifier la variable 'test_image_relative_path' !!!\n")
    else:
        analyze_image_lines(test_image_relative_path)

    print("--- Fin du test ---")