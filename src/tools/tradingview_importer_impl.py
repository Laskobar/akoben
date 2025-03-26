"""
TradingView Importer - Interface pour l'importation des captures d'écran TradingView.
Ce module fait partie du système d'apprentissage hybride Akoben.
"""

import os
import shutil
import datetime
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import json
from PIL import Image, ImageTk

class TradingViewImporter:
    """Interface graphique pour l'importation des captures d'écran TradingView."""
    
    def __init__(self, base_dir=None):
        """
        Initialise l'interface d'importation TradingView.
        
        Args:
            base_dir (str): Répertoire de base pour le stockage des captures d'écran.
        """
        if base_dir is None:
            self.base_dir = os.path.join(os.path.expanduser("~"), "akoben", "tradingview_captures")
        else:
            self.base_dir = base_dir
            
        self.imported_count = 0
        self.ensure_directories()
        
        # Liste des timeframes disponibles
        self.timeframes = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]
        
        # Liste des types de setups
        self.setup_types = ["Breakout", "Pullback", "Reversal", "Range", "Trend Continuation", "Autre"]
        
        # Métadonnées par défaut
        self.metadata = {
            "instrument": "US30",
            "timeframe": "M5",
            "setup_type": "Breakout",
            "direction": "BUY",
            "confidence": 7,  # Sur une échelle de 1 à 10
            "key_levels": [],
            "indicators": [],
            "notes": ""
        }
        
        self.current_image_path = None
        
    def ensure_directories(self):
        """Crée la structure de répertoires nécessaire."""
        # Répertoire principal
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Sous-répertoires par date
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.today_dir = os.path.join(self.base_dir, today)
        os.makedirs(self.today_dir, exist_ok=True)
        
        # Répertoire des captures non traitées
        self.pending_dir = os.path.join(self.base_dir, "pending")
        os.makedirs(self.pending_dir, exist_ok=True)
        
    def create_ui(self):
        """Crée l'interface utilisateur."""
        self.root = tk.Tk()
        self.root.title("Akoben - TradingView Importer")
        self.root.geometry("1200x800")
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame gauche (image)
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Zone d'affichage de l'image
        self.image_label = ttk.Label(left_frame)
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Frame droit (contrôles)
        right_frame = ttk.Frame(main_frame, width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        
        # Section 1: Importation
        import_frame = ttk.LabelFrame(right_frame, text="Importation", padding="10")
        import_frame.pack(fill=tk.X, expand=False, pady=(0, 10))
        
        ttk.Button(import_frame, text="Importer des captures d'écran", 
                   command=self.import_images).pack(fill=tk.X)
        
        ttk.Button(import_frame, text="Parcourir les setups existants", 
                   command=self.browse_existing_setups).pack(fill=tk.X, pady=(5, 0))
        
        # Compteur d'imports
        self.import_count_var = tk.StringVar(value="0 captures importées")
        ttk.Label(import_frame, textvariable=self.import_count_var).pack(pady=(5, 0))
        
        # Section 2: Métadonnées
        metadata_frame = ttk.LabelFrame(right_frame, text="Métadonnées", padding="10")
        metadata_frame.pack(fill=tk.X, expand=False, pady=(0, 10))
        
        # Instrument
        ttk.Label(metadata_frame, text="Instrument:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.instrument_var = tk.StringVar(value=self.metadata["instrument"])
        ttk.Entry(metadata_frame, textvariable=self.instrument_var).grid(row=0, column=1, sticky=tk.EW, pady=2)
        
        # Timeframe
        ttk.Label(metadata_frame, text="Timeframe:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.timeframe_var = tk.StringVar(value=self.metadata["timeframe"])
        ttk.Combobox(metadata_frame, textvariable=self.timeframe_var, 
                     values=self.timeframes).grid(row=1, column=1, sticky=tk.EW, pady=2)
        
        # Type de setup
        ttk.Label(metadata_frame, text="Type de setup:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.setup_type_var = tk.StringVar(value=self.metadata["setup_type"])
        ttk.Combobox(metadata_frame, textvariable=self.setup_type_var, 
                     values=self.setup_types).grid(row=2, column=1, sticky=tk.EW, pady=2)
        
        # Direction
        ttk.Label(metadata_frame, text="Direction:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.direction_var = tk.StringVar(value=self.metadata["direction"])
        direction_frame = ttk.Frame(metadata_frame)
        direction_frame.grid(row=3, column=1, sticky=tk.EW, pady=2)
        ttk.Radiobutton(direction_frame, text="BUY", value="BUY", 
                        variable=self.direction_var).pack(side=tk.LEFT)
        ttk.Radiobutton(direction_frame, text="SELL", value="SELL", 
                        variable=self.direction_var).pack(side=tk.LEFT)
        
        # Confiance
        ttk.Label(metadata_frame, text="Confiance (1-10):").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.confidence_var = tk.IntVar(value=self.metadata["confidence"])
        ttk.Spinbox(metadata_frame, from_=1, to=10, textvariable=self.confidence_var).grid(
            row=4, column=1, sticky=tk.EW, pady=2)
        
        # Niveaux clés
        ttk.Label(metadata_frame, text="Niveaux clés:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.key_levels_var = tk.StringVar()
        ttk.Entry(metadata_frame, textvariable=self.key_levels_var).grid(
            row=5, column=1, sticky=tk.EW, pady=2)
        
        # Indicateurs
        ttk.Label(metadata_frame, text="Indicateurs:").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.indicators_var = tk.StringVar()
        ttk.Entry(metadata_frame, textvariable=self.indicators_var).grid(
            row=6, column=1, sticky=tk.EW, pady=2)
        
        # Notes
        ttk.Label(metadata_frame, text="Notes:").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.notes_var = tk.StringVar()
        ttk.Entry(metadata_frame, textvariable=self.notes_var).grid(
            row=7, column=1, sticky=tk.EW, pady=2)
        
        # Configuration du grid
        metadata_frame.columnconfigure(1, weight=1)
        
        # Section 3: Navigation
        nav_frame = ttk.LabelFrame(right_frame, text="Navigation", padding="10")
        nav_frame.pack(fill=tk.X, expand=False, pady=(0, 10))
        
        nav_buttons = ttk.Frame(nav_frame)
        nav_buttons.pack(fill=tk.X)
        
        ttk.Button(nav_buttons, text="Précédent", command=self.previous_image).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(nav_buttons, text="Suivant", command=self.next_image).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Indicateur d'image
        self.image_indicator_var = tk.StringVar(value="Aucune image")
        ttk.Label(nav_frame, textvariable=self.image_indicator_var).pack(pady=(5, 0))
        
        # Section 4: Actions
        action_frame = ttk.LabelFrame(right_frame, text="Actions", padding="10")
        action_frame.pack(fill=tk.X, expand=False)
        
        ttk.Button(action_frame, text="Valider et générer MBONGI", 
                   command=self.validate_and_generate).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(action_frame, text="Voir la description MBONGI", 
                   command=self.load_existing_mbongi).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(action_frame, text="Passer", 
                   command=self.skip_current).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(action_frame, text="Quitter", 
                   command=self.root.destroy).pack(fill=tk.X)
        
        return self.root
    
    def import_images(self):
        """Importe des captures d'écran."""
        files = filedialog.askopenfilenames(
            title="Sélectionner les captures d'écran TradingView",
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        
        if not files:
            return
        
        # Copie les fichiers dans le dossier pending
        for file in files:
            filename = os.path.basename(file)
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            new_filename = f"{timestamp}_{filename}"
            shutil.copy2(file, os.path.join(self.pending_dir, new_filename))
            self.imported_count += 1
        
        # Met à jour le compteur
        self.import_count_var.set(f"{self.imported_count} captures importées")
        
        # Charge la première image
        self.load_pending_images()
    
    def load_pending_images(self):
        """Charge les images en attente."""
        self.pending_images = [f for f in os.listdir(self.pending_dir) 
                               if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        
        if self.pending_images:
            self.current_image_index = 0
            self.display_current_image()
        else:
            self.image_label.config(image='')
            self.current_image_path = None
            self.image_indicator_var.set("Aucune image")
    
    def display_current_image(self):
        """Affiche l'image courante."""
        if not hasattr(self, 'pending_images') or not self.pending_images:
            return
        
        filename = self.pending_images[self.current_image_index]
        self.current_image_path = os.path.join(self.pending_dir, filename)
        
        # Charge et redimensionne l'image
        image = Image.open(self.current_image_path)
        width, height = image.size
        max_width = 700
        max_height = 700
        
        # Calcule les nouvelles dimensions en gardant le ratio
        if width > max_width or height > max_height:
            ratio = min(max_width / width, max_height / height)
            width = int(width * ratio)
            height = int(height * ratio)
            image = image.resize((width, height), Image.LANCZOS)
        
        # Convertit en format Tkinter
        photo = ImageTk.PhotoImage(image)
        self.image_label.config(image=photo)
        self.image_label.image = photo  # Garde une référence
        
        # Met à jour l'indicateur
        self.image_indicator_var.set(f"Image {self.current_image_index + 1}/{len(self.pending_images)}")
    
    def next_image(self):
        """Passe à l'image suivante."""
        if not hasattr(self, 'pending_images') or not self.pending_images:
            return
        
        if self.current_image_index < len(self.pending_images) - 1:
            self.current_image_index += 1
            self.display_current_image()
    
    def previous_image(self):
        """Passe à l'image précédente."""
        if not hasattr(self, 'pending_images') or not self.pending_images:
            return
        
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.display_current_image()
    
    def collect_metadata(self):
        """Collecte les métadonnées depuis l'interface."""
        metadata = {
            "instrument": self.instrument_var.get(),
            "timeframe": self.timeframe_var.get(),
            "setup_type": self.setup_type_var.get(),
            "direction": self.direction_var.get(),
            "confidence": self.confidence_var.get(),
            "key_levels": [level.strip() for level in self.key_levels_var.get().split(',') if level.strip()],
            "indicators": [ind.strip() for ind in self.indicators_var.get().split(',') if ind.strip()],
            "notes": self.notes_var.get(),
            "timestamp": datetime.datetime.now().isoformat()
        }
        return metadata
    
    def validate_and_generate(self):
        """Valide l'image courante et génère une description MBONGI."""
        if not self.current_image_path:
            return
        
        # Collecte les métadonnées
        metadata = self.collect_metadata()
        
        # Crée un dossier spécifique pour ce setup
        setup_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        setup_dir = os.path.join(self.today_dir, f"setup_{setup_id}")
        os.makedirs(setup_dir, exist_ok=True)
        
        # Copie l'image
        dest_image_path = os.path.join(setup_dir, "original.png")
        shutil.copy2(self.current_image_path, dest_image_path)
        
        # Sauvegarde les métadonnées
        metadata_path = os.path.join(setup_dir, "metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Génère la description MBONGI (ici, nous appellerons un générateur externe)
        # Pour l'instant, nous utilisons un placeholder
        mbongi_path = os.path.join(setup_dir, "description.md")
        with open(mbongi_path, 'w') as f:
            f.write(f"# Setup {metadata['direction']} sur {metadata['instrument']} ({metadata['timeframe']})\n\n")
            f.write(f"Type: {metadata['setup_type']}\n")
            f.write(f"Confiance: {metadata['confidence']}/10\n\n")
            f.write("## Niveaux clés\n")
            for level in metadata['key_levels']:
                f.write(f"- {level}\n")
            f.write("\n## Indicateurs\n")
            for ind in metadata['indicators']:
                f.write(f"- {ind}\n")
            f.write("\n## Notes\n")
            f.write(metadata['notes'] or "Aucune note spécifique.")
        
        # Recherche d'images supplémentaires dans le même répertoire
        if hasattr(self, 'browse_mode') and self.browse_mode:
            setup_dir = os.path.dirname(self.current_image_path)
            additional_images = []
            for file in os.listdir(setup_dir):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    img_path = os.path.join(setup_dir, file)
                    if img_path != self.current_image_path:  # Exclure l'image principale
                        additional_images.append(img_path)
            
            # Copie des images supplémentaires
            for i, img_path in enumerate(additional_images):
                img_suffix = f"additional_{i+1}{os.path.splitext(img_path)[1]}"
                dest_path = os.path.join(setup_dir, img_suffix)
                shutil.copy2(img_path, dest_path)
        
        # Supprime l'image traitée du dossier pending si elle n'est pas en mode parcourir
        if not hasattr(self, 'browse_mode') or not self.browse_mode:
            os.remove(self.current_image_path)
            self.pending_images.pop(self.current_image_index)
        
        # Affiche la prochaine image ou réinitialise
        if self.pending_images:
            if self.current_image_index >= len(self.pending_images):
                self.current_image_index = len(self.pending_images) - 1
            self.display_current_image()
        else:
            self.image_label.config(image='')
            self.current_image_path = None
            self.image_indicator_var.set("Aucune image")
            
        # Affiche un message de confirmation
        messagebox.showinfo("Succès", f"Setup généré avec succès: setup_{setup_id}")
    
    def skip_current(self):
        """Ignore l'image courante."""
        if not self.current_image_path:
            return
        
        # Supprime l'image du dossier pending si elle n'est pas en mode parcourir
        if not hasattr(self, 'browse_mode') or not self.browse_mode:
            os.remove(self.current_image_path)
            self.pending_images.pop(self.current_image_index)
        else:
            # En mode parcourir, on passe juste à l'image suivante
            self.pending_images.remove(self.current_image_path)
        
        # Affiche la prochaine image ou réinitialise
        if self.pending_images:
            if self.current_image_index >= len(self.pending_images):
                self.current_image_index = len(self.pending_images) - 1
            self.display_current_image()
        else:
            self.image_label.config(image='')
            self.current_image_path = None
            self.image_indicator_var.set("Aucune image")
    
    def browse_existing_setups(self):
        """Parcourt les setups existants."""
        # Demande à l'utilisateur de sélectionner un répertoire
        setup_dir = filedialog.askdirectory(
            title="Sélectionner le répertoire des setups existants")
    
        if not setup_dir:
            return
    
        # Trouve toutes les images dans ce répertoire et ses sous-répertoires
        image_files = []
        for root, dirs, files in os.walk(setup_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    image_files.append(os.path.join(root, file))
    
        if not image_files:
            messagebox.showinfo("Information", "Aucune image trouvée dans ce répertoire")
            return
    
        # Stocke les images et affiche la première
        self.pending_images = image_files
        self.current_image_index = 0
        
        # Active le mode parcourir
        self.browse_mode = True
        
        self.display_current_image()
    
        # Met à jour l'indicateur
        self.image_indicator_var.set(f"Image {self.current_image_index + 1}/{len(self.pending_images)}")      

    def load_existing_mbongi(self):
        """Charge le texte MBONGI associé à l'image courante."""
        if not self.current_image_path:
            return
    
        # Cherche un fichier texte ou markdown dans le même répertoire
        directory = os.path.dirname(self.current_image_path)
        text_files = []
        for file in os.listdir(directory):
            if file.lower().endswith(('.txt', '.md')):
                text_files.append(os.path.join(directory, file))
    
        if not text_files:
            messagebox.showinfo("Information", "Aucun fichier texte trouvé pour cette image")
            return
    
        # Si plusieurs fichiers, demande à l'utilisateur de choisir
        if len(text_files) > 1:
            file_to_open = filedialog.askopenfilename(
                title="Sélectionner le fichier MBONGI",
                filetypes=[("Fichiers texte", "*.txt;*.md")],
                initialdir=directory)
            if not file_to_open:
                return
        else:
            file_to_open = text_files[0]
    
        # Lit le contenu du fichier
        try:
            with open(file_to_open, 'r') as f:
                content = f.read()
        
            # Affiche le contenu dans une nouvelle fenêtre
            text_window = tk.Toplevel(self.root)
            text_window.title("Description MBONGI")
            text_window.geometry("800x600")
        
            text_frame = ttk.Frame(text_window, padding="10")
            text_frame.pack(fill=tk.BOTH, expand=True)
        
            text_widget = tk.Text(text_frame)
            text_widget.pack(fill=tk.BOTH, expand=True)
        
            text_widget.insert(tk.END, content)
            text_widget.config(state=tk.DISABLED)  # Lecture seule
        
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lire le fichier : {str(e)}")

    def run(self):
        """Lance l'application."""
        self.create_ui()
        self.load_pending_images()
        self.root.mainloop()

def main():
    """Point d'entrée principal."""
    importer = TradingViewImporter()
    importer.run()

if __name__ == "__main__":
    main()