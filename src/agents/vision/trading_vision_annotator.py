import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import cv2
import shutil

class TradingVisionAnnotator:
    """
    Outil pour annoter et analyser les screenshots de trading.
    Permet de créer un dataset pour l'entraînement de l'équipe de vision Djeli.
    """
    def __init__(self, data_root: str = "data/vision", 
                 output_dir: str = "data/annotated",
                 annotation_file: str = "data/vision/annotations.json"):
        """
        Initialise l'annotateur de vision de trading.
        
        Args:
            data_root: Répertoire contenant les images
            output_dir: Répertoire pour les images annotées
            annotation_file: Fichier pour sauvegarder les annotations
        """
        self.data_root = data_root
        self.output_dir = output_dir
        self.annotation_file = annotation_file
        
        # Créer les répertoires nécessaires
        os.makedirs(data_root, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.dirname(annotation_file), exist_ok=True)
        
        # Charger les annotations existantes
        self.annotations = self._load_annotations()
        
        # Types d'éléments visuels à détecter
        self.element_types = {
            "candle_bullish": {"color": "green", "description": "Bougie haussière"},
            "candle_bearish": {"color": "red", "description": "Bougie baissière"},
            "candle_doji": {"color": "blue", "description": "Bougie doji"},
            "candle_hammer": {"color": "orange", "description": "Bougie en marteau"},
            "candle_shooting_star": {"color": "purple", "description": "Bougie étoile filante"},
            "support_level": {"color": "green", "description": "Niveau de support"},
            "resistance_level": {"color": "red", "description": "Niveau de résistance"},
            "trend_line": {"color": "blue", "description": "Ligne de tendance"},
            "moving_average": {"color": "orange", "description": "Moyenne mobile"},
            "rsi_indicator": {"color": "purple", "description": "Indicateur RSI"},
            "macd_indicator": {"color": "brown", "description": "Indicateur MACD"},
            "bollinger_bands": {"color": "teal", "description": "Bandes de Bollinger"},
            "volume_bar": {"color": "gray", "description": "Barre de volume"},
            "pattern_flag": {"color": "yellow", "description": "Pattern drapeau"},
            "pattern_triangle": {"color": "cyan", "description": "Pattern triangle"},
            "pattern_head_shoulders": {"color": "magenta", "description": "Pattern tête et épaules"},
            "pattern_double_top": {"color": "lime", "description": "Pattern double sommet"},
            "pattern_double_bottom": {"color": "pink", "description": "Pattern double creux"},
            "price_level": {"color": "white", "description": "Niveau de prix"},
            "fibonacci_level": {"color": "gold", "description": "Niveau de Fibonacci"}
        }
        
        print(f"TradingVisionAnnotator initialisé avec {len(self.annotations)} annotations")
    
    def _load_annotations(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Charge les annotations existantes depuis le fichier JSON.
        
        Returns:
            Dictionnaire d'annotations par image
        """
        if os.path.exists(self.annotation_file):
            try:
                with open(self.annotation_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Erreur lors de la lecture du fichier d'annotations. Création d'un nouveau fichier.")
                return {}
        else:
            return {}
    
    def _save_annotations(self) -> None:
        """
        Sauvegarde les annotations dans le fichier JSON.
        """
        with open(self.annotation_file, 'w') as f:
            json.dump(self.annotations, f, indent=2)
    
    def add_annotation(self, image_path: str, element_type: str, 
                     coordinates: List[int], label: str = "",
                     confidence: float = 1.0) -> bool:
        """
        Ajoute une annotation pour un élément visuel dans une image.
        
        Args:
            image_path: Chemin de l'image
            element_type: Type d'élément (bougie, support, etc.)
            coordinates: Coordonnées [x1, y1, x2, y2] ou [x1, y1, x2, y2, ...] pour polygones
            label: Étiquette optionnelle (valeur, description)
            confidence: Niveau de confiance de l'annotation
            
        Returns:
            True si l'annotation a été ajoutée avec succès
        """
        # Vérifier que le type d'élément est valide
        if element_type not in self.element_types:
            print(f"Type d'élément inconnu: {element_type}")
            return False
        
        # Vérifier que l'image existe
        if not os.path.exists(image_path):
            print(f"Image non trouvée: {image_path}")
            return False
        
        # Créer une entrée pour cette image si elle n'existe pas
        image_rel_path = os.path.relpath(image_path, self.data_root)
        if image_rel_path not in self.annotations:
            self.annotations[image_rel_path] = []
        
        # Ajouter l'annotation
        annotation = {
            "element_type": element_type,
            "coordinates": coordinates,
            "label": label,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
        
        self.annotations[image_rel_path].append(annotation)
        self._save_annotations()
        
        return True
    
    def remove_annotation(self, image_path: str, annotation_index: int) -> bool:
        """
        Supprime une annotation existante.
        
        Args:
            image_path: Chemin de l'image
            annotation_index: Index de l'annotation à supprimer
            
        Returns:
            True si la suppression a réussi
        """
        image_rel_path = os.path.relpath(image_path, self.data_root)
        
        if image_rel_path not in self.annotations:
            print(f"Aucune annotation trouvée pour cette image")
            return False
        
        if annotation_index < 0 or annotation_index >= len(self.annotations[image_rel_path]):
            print(f"Index d'annotation invalide")
            return False
        
        # Supprimer l'annotation
        del self.annotations[image_rel_path][annotation_index]
        
        # Si plus d'annotations pour cette image, supprimer l'entrée
        if not self.annotations[image_rel_path]:
            del self.annotations[image_rel_path]
        
        self._save_annotations()
        return True
    
    def get_annotations(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Récupère les annotations pour une image.
        
        Args:
            image_path: Chemin de l'image
            
        Returns:
            Liste des annotations pour cette image
        """
        image_rel_path = os.path.relpath(image_path, self.data_root)
        return self.annotations.get(image_rel_path, [])
    
    def create_annotated_image(self, image_path: str, output_path: Optional[str] = None) -> str:
        """
        Crée une version annotée de l'image avec les éléments visuels mis en évidence.
        
        Args:
            image_path: Chemin de l'image originale
            output_path: Chemin de sortie (générée automatiquement si None)
            
        Returns:
            Chemin de l'image annotée
        """
        if not os.path.exists(image_path):
            print(f"Image non trouvée: {image_path}")
            return ""
        
        # Générer un chemin de sortie par défaut
        if output_path is None:
            filename = os.path.basename(image_path)
            output_path = os.path.join(self.output_dir, f"annotated_{filename}")
        
        # Charger l'image et créer un objet de dessin
        image = Image.open(image_path)
        draw = ImageDraw.Draw(image)
        
        # Essayer de charger une police, avec fallback sur une taille plus petite si nécessaire
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except IOError:
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", 14)
            except IOError:
                font = ImageFont.load_default()
        
        # Récupérer les annotations pour cette image
        image_rel_path = os.path.relpath(image_path, self.data_root)
        annotations = self.annotations.get(image_rel_path, [])
        
        # Dessiner chaque annotation
        for anno in annotations:
            element_type = anno["element_type"]
            coords = anno["coordinates"]
            label = anno["label"]
            
            # Récupérer la couleur pour ce type d'élément
            color = self.element_types.get(element_type, {}).get("color", "white")
            
            # Dessiner selon le type d'annotation
            if len(coords) == 4:  # Rectangle simple [x1, y1, x2, y2]
                # Dessiner un rectangle
                draw.rectangle(coords, outline=color, width=2)
                
                # Ajouter l'étiquette au-dessus du rectangle
                label_with_type = f"{element_type}{': ' + label if label else ''}"
                draw.text((coords[0], coords[1] - 15), label_with_type, fill=color, font=font)
            
            elif len(coords) == 2:  # Point [x, y]
                # Dessiner un point
                point_size = 5
                x, y = coords
                draw.ellipse((x - point_size, y - point_size, x + point_size, y + point_size), 
                           fill=color)
                
                # Ajouter l'étiquette à côté du point
                label_with_type = f"{element_type}{': ' + label if label else ''}"
                draw.text((x + point_size + 2, y - point_size), label_with_type, fill=color, font=font)
            
            elif len(coords) >= 6 and len(coords) % 2 == 0:  # Polygone ou ligne [x1, y1, x2, y2, ...]
                # Dessiner une ligne ou un polygone
                points = [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]
                draw.line(points, fill=color, width=2)
                
                # Ajouter l'étiquette au premier point
                label_with_type = f"{element_type}{': ' + label if label else ''}"
                draw.text((points[0][0], points[0][1] - 15), label_with_type, fill=color, font=font)
        
        # Sauvegarder l'image annotée
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path)
        
        return output_path
    
    def detect_elements_yolo(self, image_path: str, confidence_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        Simulation de détection d'éléments avec YOLO (à remplacer par un vrai modèle).
        Dans cette version, nous simulons la détection pour la démonstration.
        
        Args:
            image_path: Chemin de l'image à analyser
            confidence_threshold: Seuil de confiance minimal
            
        Returns:
            Liste des détections
        """
        if not os.path.exists(image_path):
            print(f"Image non trouvée: {image_path}")
            return []
        
        # Charger l'image pour obtenir ses dimensions
        image = Image.open(image_path)
        width, height = image.size
        
        # Simuler quelques détections
        # Dans une vraie implémentation, ce serait remplacé par un modèle YOLO
        detections = []
        
        # Simuler des bougies japonaises
        for i in range(5):
            candle_type = np.random.choice(["candle_bullish", "candle_bearish", "candle_doji"])
            x1 = int(width * 0.1 + i * width * 0.1)
            y1 = int(height * 0.3 + np.random.random() * height * 0.3)
            x2 = int(x1 + width * 0.02)
            y2 = int(y1 + height * 0.1)
            
            detections.append({
                "element_type": candle_type,
                "coordinates": [x1, y1, x2, y2],
                "label": "",
                "confidence": 0.7 + np.random.random() * 0.2
            })
        
        # Simuler un niveau de support
        detections.append({
            "element_type": "support_level",
            "coordinates": [int(width * 0.1), int(height * 0.7), 
                          int(width * 0.9), int(height * 0.7)],
            "label": "Support",
            "confidence": 0.85
        })
        
        # Simuler un niveau de résistance
        detections.append({
            "element_type": "resistance_level",
            "coordinates": [int(width * 0.1), int(height * 0.3), 
                          int(width * 0.9), int(height * 0.3)],
            "label": "Résistance",
            "confidence": 0.82
        })
        
        # Filtrer par seuil de confiance
        detections = [d for d in detections if d["confidence"] >= confidence_threshold]
        
        return detections
    
    def auto_annotate(self, image_path: str, confidence_threshold: float = 0.3) -> int:
        """
        Annote automatiquement une image en utilisant la détection d'éléments.
        
        Args:
            image_path: Chemin de l'image à annoter
            confidence_threshold: Seuil de confiance minimal
            
        Returns:
            Nombre d'annotations ajoutées
        """
        if not os.path.exists(image_path):
            print(f"Image non trouvée: {image_path}")
            return 0
        
        # Détecter les éléments
        detections = self.detect_elements_yolo(image_path, confidence_threshold)
        
        # Supprimer les annotations existantes
        image_rel_path = os.path.relpath(image_path, self.data_root)
        if image_rel_path in self.annotations:
            self.annotations[image_rel_path] = []
        
        # Ajouter les nouvelles annotations
        for detection in detections:
            self.add_annotation(
                image_path,
                detection["element_type"],
                detection["coordinates"],
                detection["label"],
                detection["confidence"]
            )
        
        return len(detections)
    
    def extract_features(self, image_path: str) -> Dict[str, Any]:
        """
        Extrait des caractéristiques visuelles de l'image pour l'apprentissage.
        
        Args:
            image_path: Chemin de l'image
            
        Returns:
            Dictionnaire des caractéristiques extraites
        """
        if not os.path.exists(image_path):
            print(f"Image non trouvée: {image_path}")
            return {}
        
        # Charger l'image avec OpenCV pour le traitement
        img = cv2.imread(image_path)
        if img is None:
            print(f"Erreur lors du chargement de l'image avec OpenCV")
            return {}
        
        # Convertir en niveaux de gris pour certaines analyses
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Extraire des caractéristiques de base
        height, width, channels = img.shape
        
        # Calculer l'histogramme de couleurs
        color_hist = cv2.calcHist([img], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        color_hist = cv2.normalize(color_hist, color_hist).flatten()
        
        # Calculer des statistiques sur les bords (détection de Canny)
        edges = cv2.Canny(gray, 100, 200)
        edge_density = np.count_nonzero(edges) / (height * width)
        
        # Diviser l'image en régions et calculer des statistiques
        regions = []
        h_step = height // 3
        w_step = width // 3
        
        for i in range(3):
            for j in range(3):
                y1 = i * h_step
                y2 = (i + 1) * h_step if i < 2 else height
                x1 = j * w_step
                x2 = (j + 1) * w_step if j < 2 else width
                
                region = gray[y1:y2, x1:x2]
                
                region_stats = {
                    "mean": np.mean(region),
                    "std": np.std(region),
                    "min": np.min(region),
                    "max": np.max(region)
                }
                
                regions.append(region_stats)
        
        # Calculer le nombre de lignes horizontales potentielles (pour supports/résistances)
        horizontal_lines = self._detect_horizontal_lines(edges)
        
        # Collecter toutes les caractéristiques
        features = {
            "dimensions": {
                "width": width,
                "height": height,
                "aspect_ratio": width / height
            },
            "color_distribution": {
                "histogram": color_hist.tolist(),
                "mean_color": [np.mean(img[:,:,i]) for i in range(3)]
            },
            "edge_analysis": {
                "edge_density": edge_density,
                "horizontal_lines_count": len(horizontal_lines)
            },
            "regions": regions
        }
        
        return features
    
    def _detect_horizontal_lines(self, edges, min_length=50, max_gap=5):
        """
        Détecte les lignes horizontales dans une image de contours.
        Utile pour identifier les supports et résistances.
        
        Args:
            edges: Image binaire des contours
            min_length: Longueur minimale des lignes
            max_gap: Écart maximal autorisé dans une ligne
            
        Returns:
            Liste de lignes horizontales [x1, y1, x2, y2]
        """
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, 
                              minLineLength=min_length, maxLineGap=max_gap)
        
        horizontal_lines = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                # Filtrer les lignes presque horizontales
                if abs(y2 - y1) < 10:  # Tolérance de 10 pixels
                    horizontal_lines.append([x1, y1, x2, y2])
        
        return horizontal_lines
    
    def match_pattern_template(self, image_path: str, pattern_template: str, 
                             threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Recherche un pattern spécifique dans l'image en utilisant la correspondance de modèle.
        
        Args:
            image_path: Chemin de l'image principale
            pattern_template: Chemin du modèle à rechercher
            threshold: Seuil de correspondance
            
        Returns:
            Liste des correspondances trouvées
        """
        if not os.path.exists(image_path) or not os.path.exists(pattern_template):
            print(f"Image ou modèle non trouvé")
            return []
        
        # Charger les images
        img = cv2.imread(image_path, 0)  # En niveaux de gris
        template = cv2.imread(pattern_template, 0)
        
        if img is None or template is None:
            print(f"Erreur lors du chargement des images")
            return []
        
        # Appliquer la correspondance de modèle
        h, w = template.shape
        result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        
        # Trouver les emplacements où le résultat dépasse le seuil
        locations = np.where(result >= threshold)
        matches = []
        
        for pt in zip(*locations[::-1]):
            matches.append({
                "coordinates": [pt[0], pt[1], pt[0] + w, pt[1] + h],
                "confidence": float(result[pt[1], pt[0]])
            })
        
        return matches
    
    def analyze_screenshot(self, image_path: str) -> Dict[str, Any]:
        """
        Analyse complète d'un screenshot de trading.
        
        Args:
            image_path: Chemin de l'image à analyser
            
        Returns:
            Résultats de l'analyse
        """
        if not os.path.exists(image_path):
            return {"error": "Image non trouvée"}
        
        # Extraire les caractéristiques
        features = self.extract_features(image_path)
        
        # Détecter les éléments
        detections = self.detect_elements_yolo(image_path)
        
        # Résumé des détections
        detection_summary = {}
        for det in detections:
            element_type = det["element_type"]
            detection_summary[element_type] = detection_summary.get(element_type, 0) + 1
        
        # Calculer la composition du graphique
        composition = {
            "candles_count": sum([detection_summary.get(f"candle_{t}", 0) 
                                for t in ["bullish", "bearish", "doji", "hammer", "shooting_star"]]),
            "support_resistance_count": detection_summary.get("support_level", 0) + 
                                     detection_summary.get("resistance_level", 0),
            "indicators_present": [t for t in ["moving_average", "rsi_indicator", "macd_indicator", "bollinger_bands"]
                                 if detection_summary.get(t, 0) > 0],
            "patterns_detected": [t.replace("pattern_", "") for t in detection_summary.keys()
                                if t.startswith("pattern_") and detection_summary[t] > 0]
        }
        
        # Déterminer le biais probable du marché
        bullish_elements = (
            detection_summary.get("candle_bullish", 0) +
            (1 if "pattern_flag" in detection_summary and detection_summary.get("pattern_flag", 0) > 0 else 0) +
            (1 if "pattern_double_bottom" in detection_summary and detection_summary.get("pattern_double_bottom", 0) > 0 else 0)
        )
        
        bearish_elements = (
            detection_summary.get("candle_bearish", 0) +
            (1 if "pattern_head_shoulders" in detection_summary and detection_summary.get("pattern_head_shoulders", 0) > 0 else 0) +
            (1 if "pattern_double_top" in detection_summary and detection_summary.get("pattern_double_top", 0) > 0 else 0)
        )
        
        market_bias = "neutral"
        if bullish_elements > bearish_elements:
            market_bias = "bullish"
        elif bearish_elements > bullish_elements:
            market_bias = "bearish"
        
        # Résultats de l'analyse
        return {
            "image_path": image_path,
            "features": features,
            "detections": detections,
            "detection_summary": detection_summary,
            "composition": composition,
            "market_bias": market_bias,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def create_training_dataset(self, output_dir: str = "data/training_dataset") -> str:
        """
        Crée un dataset d'entraînement à partir des images annotées.
        
        Args:
            output_dir: Répertoire de sortie pour le dataset
            
        Returns:
            Chemin du dataset généré
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Créer un sous-dossier pour les étiquettes
        labels_dir = os.path.join(output_dir, "labels")
        images_dir = os.path.join(output_dir, "images")
        os.makedirs(labels_dir, exist_ok=True)
        os.makedirs(images_dir, exist_ok=True)
        
        # Fichier de métadonnées pour le dataset
        dataset_info = {
            "created": datetime.now().isoformat(),
            "image_count": 0,
            "class_distribution": {},
            "classes": list(self.element_types.keys())
        }
        
        # Traitement de chaque image annotée
        processed_count = 0
        class_distribution = {cls: 0 for cls in self.element_types.keys()}
        
        for image_rel_path, annotations in self.annotations.items():
            if not annotations:
                continue
            
            image_path = os.path.join(self.data_root, image_rel_path)
            if not os.path.exists(image_path):
                print(f"Image non trouvée: {image_path}")
                continue
            
            # Charger l'image pour obtenir ses dimensions
            try:
                img = Image.open(image_path)
                width, height = img.size
            except Exception as e:
                print(f"Erreur lors du chargement de {image_path}: {e}")
                continue
            
            # Créer le fichier d'étiquettes au format YOLO
            # Format: <class_id> <x_center> <y_center> <width> <height>
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            label_file = os.path.join(labels_dir, f"{base_name}.txt")
            
            with open(label_file, 'w') as f:
                for anno in annotations:
                    element_type = anno["element_type"]
                    coords = anno["coordinates"]
                    
                    # Ignorer les annotations sans type valide
                    if element_type not in self.element_types:
                        continue
                    
                    # Seuls les rectangles sont supportés pour l'instant
                    if len(coords) != 4:
                        continue
                    
                    # Convertir les coordonnées en format YOLO
                    x1, y1, x2, y2 = coords
                    x_center = (x1 + x2) / 2 / width
                    y_center = (y1 + y2) / 2 / height
                    box_width = (x2 - x1) / width
                    box_height = (y2 - y1) / height
                    
                    # ID de classe (position dans la liste)
                    class_id = list(self.element_types.keys()).index(element_type)
                    
                    # Écrire la ligne
                    f.write(f"{class_id} {x_center} {y_center} {box_width} {box_height}\n")
                    
                    # Mettre à jour les statistiques
                    class_distribution[element_type] += 1
            
            # Copier l'image
            dest_image = os.path.join(images_dir, os.path.basename(image_path))
            shutil.copy(image_path, dest_image)
            
            processed_count += 1
        
        # Mettre à jour les métadonnées
        dataset_info["image_count"] = processed_count
        dataset_info["class_distribution"] = class_distribution
        
        # Sauvegarder les métadonnées
        with open(os.path.join(output_dir, "dataset_info.json"), 'w') as f:
            json.dump(dataset_info, f, indent=2)
        
        # Créer le fichier de classes
        with open(os.path.join(output_dir, "classes.txt"), 'w') as f:
            for cls in self.element_types.keys():
                f.write(f"{cls}\n")
        
        print(f"Dataset créé avec {processed_count} images dans {output_dir}")
        return output_dir
    
    def prepare_yolo_config(self, training_dir: str) -> Dict[str, str]:
        """
        Prépare les fichiers de configuration pour l'entraînement YOLO.
        
        Args:
            training_dir: Répertoire du dataset d'entraînement
            
        Returns:
            Dictionnaire des fichiers de configuration créés
        """
        # Créer le dossier de configuration
        config_dir = os.path.join(training_dir, "config")
        os.makedirs(config_dir, exist_ok=True)
        
        # Fichier data.yaml (définition du dataset)
        data_yaml = os.path.join(config_dir, "data.yaml")
        classes = list(self.element_types.keys())
        
        with open(data_yaml, 'w') as f:
            f.write(f"train: {os.path.join(training_dir, 'images')}\n")
            f.write(f"val: {os.path.join(training_dir, 'images')}\n")  # Utiliser le même dossier pour la validation
            f.write(f"nc: {len(classes)}\n")
            f.write("names:\n")
            for cls in classes:
                f.write(f"  - '{cls}'\n")
        
        # Créer un script d'entraînement minimal
        train_script = os.path.join(config_dir, "train.py")
        
        with open(train_script, 'w') as f:
            f.write("""import os
import yaml
from ultralytics import YOLO

# Charger le fichier de configuration
with open('config/data.yaml', 'r') as file:
    data_config = yaml.safe_load(file)

# Initialiser le modèle
model = YOLO('yolov8n.pt')  # Charger un modèle pré-entraîné YOLOv8 nano

# Entraîner le modèle
results = model.train(
    data='config/data.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    name='trading_elements_detector'
)

print(f"Entraînement terminé. Résultats disponibles dans {results.save_dir}")
""")
        
        return {
            "data_yaml": data_yaml,
            "train_script": train_script
        }
    
    def associate_with_setup(self, image_path: str, setup_id: str, 
                           setup_db_manager=None) -> bool:
        """
        Associe une image annotée à un setup de trading spécifique.
        
        Args:
            image_path: Chemin de l'image annotée
            setup_id: ID du setup dans la base de données
            setup_db_manager: Instance de SetupDatabaseManager
            
        Returns:
            True si l'association a réussi
        """
        if setup_db_manager is None:
            print("Aucun gestionnaire de base de données de setup fourni")
            return False
        
        # Vérifier que l'image existe et contient des annotations
        image_rel_path = os.path.relpath(image_path, self.data_root)
        if image_rel_path not in self.annotations or not self.annotations[image_rel_path]:
            print(f"Aucune annotation trouvée pour cette image")
            return False
        
        # Récupérer les informations du setup
        setup_info = setup_db_manager.get_setup_by_id(setup_id)
        if not setup_info:
            print(f"Setup non trouvé: {setup_id}")
            return False
        
        # Ajouter une référence au setup dans les métadonnées des annotations
        for anno in self.annotations[image_rel_path]:
            if "metadata" not in anno:
                anno["metadata"] = {}
            
            anno["metadata"]["setup_id"] = setup_id
            anno["metadata"]["setup_type"] = setup_info.get("type", "")
            
            # Ajouter l'action (buy/sell) si disponible
            if "metadata" in setup_info and "action" in setup_info["metadata"]:
                anno["metadata"]["action"] = setup_info["metadata"]["action"]
        
        self._save_annotations()
        
        # Créer une version annotée de l'image avec les références au setup
        output_path = os.path.join(self.output_dir, f"setup_{setup_id}_{os.path.basename(image_path)}")
        self.create_annotated_image(image_path, output_path)
        
        return True
    
    def analyze_setup_visuals(self, setup_db_manager=None) -> Dict[str, Dict[str, Any]]:
        """
        Analyse les caractéristiques visuelles par type de setup.
        Utile pour comprendre les corrélations entre visuels et types de setup.
        
        Args:
            setup_db_manager: Instance de SetupDatabaseManager
            
        Returns:
            Dictionnaire des analyses par type de setup
        """
        if setup_db_manager is None:
            print("Aucun gestionnaire de base de données de setup fourni")
            return {}
        
        setup_types = setup_db_manager.get_all_setup_types()
        analyses = {}
        
        for setup_type in setup_types:
            # Récupérer tous les setups de ce type
            setups = setup_db_manager.get_setups_by_type(setup_type)
            
            # Trouver toutes les annotations associées à ces setups
            setup_annotations = []
            
            for image_rel_path, annotations in self.annotations.items():
                for anno in annotations:
                    if "metadata" in anno and "setup_type" in anno["metadata"]:
                        if anno["metadata"]["setup_type"] == setup_type:
                            setup_annotations.append({
                                "image": image_rel_path,
                                "annotation": anno
                            })
            
            # Compter les types d'éléments visuels pour ce setup
            element_counts = {}
            for anno_info in setup_annotations:
                element_type = anno_info["annotation"]["element_type"]
                element_counts[element_type] = element_counts.get(element_type, 0) + 1
            
            # Calculer les caractéristiques typiques
            analyses[setup_type] = {
                "setup_count": len(setups),
                "annotations_count": len(setup_annotations),
                "element_distribution": element_counts,
                "top_elements": sorted(element_counts.items(), key=lambda x: x[1], reverse=True)[:5] if element_counts else []
            }
        
        return analyses