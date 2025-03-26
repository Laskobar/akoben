"""
TradingView Importer - Interface simplifiée pour l'importation des captures d'écran TradingView.
Version finale corrigée pour résoudre les problèmes de sélection d'images.
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
        self.additional_images = []  # Liste pour stocker les chemins des images additionnelles
        self.mbongi_path = None  # Chemin du fichier MBONGI sélectionné
        
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
        self.root.title("Akoben - TradingView Importer (Simplifié)")
        self.root.geometry("1200x800")
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame gauche (image)
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Zone d'affichage de l'image
        self.image_frame = ttk.Frame(left_frame)
        self.image_frame.pack(fill=tk.BOTH, expand=True)
        
        self.image_label = ttk.Label(self.image_frame)
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Frame droit (contrôles)
        right_frame = ttk.Frame(main_frame, width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        
        # Section 1: Importation
        import_frame = ttk.LabelFrame(right_frame, text="Importation", padding="10")
        import_frame.pack(fill=tk.X, expand=False, pady=(0, 10))
        
        ttk.Button(import_frame, text="1. Sélectionner l'image principale", 
                   command=self.select_main_image).pack(fill=tk.X)
        
        ttk.Button(import_frame, text="2. Ajouter des images additionnelles", 
                   command=self.select_additional_images).pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(import_frame, text="3. Importer une description MBONGI", 
                   command=self.select_mbongi_file).pack(fill=tk.X, pady=(5, 0))
        
        # Statut
        self.main_image_var = tk.StringVar(value="Image principale: Non sélectionnée")
        ttk.Label(import_frame, textvariable=self.main_image_var).pack(pady=(5, 0), anchor=tk.W)
        
        self.additional_images_var = tk.StringVar(value="Images additionnelles: 0")
        ttk.Label(import_frame, textvariable=self.additional_images_var).pack(pady=(2, 0), anchor=tk.W)
        
        self.mbongi_var = tk.StringVar(value="MBONGI: Non sélectionné")
        ttk.Label(import_frame, textvariable=self.mbongi_var).pack(pady=(2, 0), anchor=tk.W)
        
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
        
        # Section 3: Images additionnelles
        additional_frame = ttk.LabelFrame(right_frame, text="Images additionnelles", padding="10")
        additional_frame.pack(fill=tk.X, expand=False, pady=(0, 10))
        
        self.additional_listbox = tk.Listbox(additional_frame, height=5)
        self.additional_listbox.pack(fill=tk.X, expand=True)
        
        additional_buttons = ttk.Frame(additional_frame)
        additional_buttons.pack(fill=tk.X, expand=True, pady=(5, 0))
        
        ttk.Button(additional_buttons, text="Voir", 
                  command=self.view_selected_additional).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(additional_buttons, text="Supprimer", 
                  command=self.remove_selected_additional).pack(side=tk.LEFT)
        
        # Section 4: Actions
        action_frame = ttk.LabelFrame(right_frame, text="Actions", padding="10")
        action_frame.pack(fill=tk.X, expand=False)
        
        ttk.Button(action_frame, text="Valider et générer le setup", 
                   command=self.generate_setup).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(action_frame, text="Voir le MBONGI", 
                   command=self.view_mbongi).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(action_frame, text="Réinitialiser", 
                   command=self.reset_form).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(action_frame, text="Quitter", 
                   command=self.root.destroy).pack(fill=tk.X)
        
        return self.root
    
    def select_main_image(self):
        """Sélectionne l'image principale."""
        file = filedialog.askopenfilename(
            title="Sélectionner l'image principale",
            filetypes=[
                ("Tous les formats d'image", "*.png *.jpg *.jpeg *.bmp"),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("BMP", "*.bmp"),
                ("Tous les fichiers", "*.*")
            ]
        )
        
        if not file:
            return
        
        # Vérifie que c'est bien une image
        try:
            Image.open(file)
        except:
            messagebox.showerror("Erreur", "Le fichier sélectionné n'est pas une image valide.")
            return
        
        self.current_image_path = file
        self.main_image_var.set(f"Image principale: {os.path.basename(file)}")
        self.display_image(file)
    
    def select_additional_images(self):
        """Sélectionne des images additionnelles."""
        if not self.current_image_path:
            messagebox.showwarning("Attention", "Veuillez d'abord sélectionner une image principale.")
            return
        
        files = filedialog.askopenfilenames(
            title="Sélectionner des images additionnelles",
            filetypes=[
                ("Tous les formats d'image", "*.png *.jpg *.jpeg *.bmp"),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("BMP", "*.bmp"),
                ("Tous les fichiers", "*.*")
            ]
        )
        
        if not files:
            return
        
        # Vérifie et ajoute chaque image
        added_count = 0
        for file in files:
            try:
                Image.open(file)  # Vérifie que c'est une image valide
                if file not in self.additional_images:
                    self.additional_images.append(file)
                    self.additional_listbox.insert(tk.END, os.path.basename(file))
                    added_count += 1
            except:
                messagebox.showwarning("Attention", f"Le fichier {os.path.basename(file)} n'est pas une image valide et sera ignoré.")
        
        if added_count > 0:
            self.additional_images_var.set(f"Images additionnelles: {len(self.additional_images)}")
            messagebox.showinfo("Succès", f"{added_count} image(s) ajoutée(s) avec succès.")
    
    def view_selected_additional(self):
        """Affiche l'image additionnelle sélectionnée."""
        selected = self.additional_listbox.curselection()
        if not selected:
            messagebox.showinfo("Information", "Veuillez d'abord sélectionner une image dans la liste.")
            return
        
        index = selected[0]
        if 0 <= index < len(self.additional_images):
            self.display_image(self.additional_images[index])
    
    def remove_selected_additional(self):
        """Supprime l'image additionnelle sélectionnée."""
        selected = self.additional_listbox.curselection()
        if not selected:
            messagebox.showinfo("Information", "Veuillez d'abord sélectionner une image dans la liste.")
            return
        
        index = selected[0]
        if 0 <= index < len(self.additional_images):
            filename = os.path.basename(self.additional_images[index])
            del self.additional_images[index]
            self.additional_listbox.delete(index)
            self.additional_images_var.set(f"Images additionnelles: {len(self.additional_images)}")
            messagebox.showinfo("Succès", f"Image '{filename}' supprimée.")
    
    def select_mbongi_file(self):
        """Sélectionne un fichier MBONGI existant."""
        file = filedialog.askopenfilename(
            title="Sélectionner un fichier MBONGI",
            filetypes=[
                ("Fichiers texte", "*.txt *.md"),
                ("Markdown", "*.md"),
                ("Texte", "*.txt"),
                ("Tous les fichiers", "*.*")
            ]
        )
        
        if not file:
            return
        
        # Vérifie que le fichier est lisible
        try:
            with open(file, 'r') as f:
                content = f.read()
                if len(content) == 0:
                    messagebox.showwarning("Attention", "Le fichier MBONGI est vide.")
                    return
        except:
            messagebox.showerror("Erreur", "Impossible de lire le fichier MBONGI sélectionné.")
            return
        
        self.mbongi_path = file
        self.mbongi_var.set(f"MBONGI: {os.path.basename(file)}")
        messagebox.showinfo("Succès", f"Fichier MBONGI '{os.path.basename(file)}' importé avec succès.")
    
    def display_image(self, image_path):
        """Affiche une image dans le panneau principal."""
        try:
            # Charge l'image
            image = Image.open(image_path)
            
            # Redimensionne si nécessaire
            max_width = 700
            max_height = 500
            width, height = image.size
            
            if width > max_width or height > max_height:
                ratio = min(max_width / width, max_height / height)
                width = int(width * ratio)
                height = int(height * ratio)
                image = image.resize((width, height), Image.LANCZOS)
            
            # Affiche l'image
            photo = ImageTk.PhotoImage(image)
            self.image_label.config(image=photo)
            self.image_label.image = photo  # Garde une référence
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'afficher l'image : {str(e)}")
    
    def view_mbongi(self):
        """Affiche le contenu du fichier MBONGI."""
        if not self.mbongi_path:
            messagebox.showinfo("Information", "Aucun fichier MBONGI sélectionné.")
            return
        
        try:
            with open(self.mbongi_path, 'r') as f:
                content = f.read()
            
            # Crée une nouvelle fenêtre pour afficher le contenu
            text_window = tk.Toplevel(self.root)
            text_window.title(f"MBONGI - {os.path.basename(self.mbongi_path)}")
            text_window.geometry("800x600")
            
            text_frame = ttk.Frame(text_window, padding="10")
            text_frame.pack(fill=tk.BOTH, expand=True)
            
            # Crée un widget Text avec scrollbar
            text_widget = tk.Text(text_frame, wrap=tk.WORD)
            scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            text_widget.insert(tk.END, content)
            text_widget.config(state=tk.DISABLED)  # Lecture seule
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lire le fichier MBONGI : {str(e)}")
    
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
            "timestamp": datetime.datetime.now().isoformat(),
            "additional_images": len(self.additional_images)
        }
        return metadata
    
    def generate_setup(self):
        """Génère un nouveau setup avec l'image et les métadonnées."""
        if not self.current_image_path:
            messagebox.showwarning("Attention", "Veuillez d'abord sélectionner une image principale.")
            return
        
        # Collecte les métadonnées
        metadata = self.collect_metadata()
        
        # Crée un nouveau dossier pour ce setup
        setup_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        setup_dir = os.path.join(self.today_dir, f"setup_{setup_id}")
        os.makedirs(setup_dir, exist_ok=True)
        
        # Copie l'image principale
        main_ext = os.path.splitext(self.current_image_path)[1]
        main_dest = os.path.join(setup_dir, f"main{main_ext}")
        shutil.copy2(self.current_image_path, main_dest)
        
        # Copie les images additionnelles
        for i, img_path in enumerate(self.additional_images):
            ext = os.path.splitext(img_path)[1]
            dest_path = os.path.join(setup_dir, f"additional_{i+1}{ext}")
            shutil.copy2(img_path, dest_path)
        
        # Sauvegarde les métadonnées
        metadata_path = os.path.join(setup_dir, "metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Copie ou génère le fichier MBONGI
        mbongi_dest = os.path.join(setup_dir, "mbongi_standard.md")
        if self.mbongi_path:
            shutil.copy2(self.mbongi_path, mbongi_dest)
        else:
            # Génère un fichier MBONGI basique
            with open(mbongi_dest, 'w') as f:
                f.write(self.generate_mbongi_content(metadata))
        
        # Affiche un message de succès
        messagebox.showinfo("Succès", 
                          f"Setup généré avec succès !\n\nID: setup_{setup_id}\n\nChemin: {setup_dir}")
        
        # Réinitialise le formulaire
        self.reset_form()
    
    def generate_mbongi_content(self, metadata):
        """Génère un contenu MBONGI basique à partir des métadonnées."""
        content = f"# Setup {metadata['direction']} sur {metadata['instrument']} ({metadata['timeframe']})\n\n"
        content += f"Type: {metadata['setup_type']}\n"
        content += f"Confiance: {metadata['confidence']}/10\n\n"
        
        content += "## Niveaux clés\n"
        if metadata['key_levels']:
            for level in metadata['key_levels']:
                content += f"- {level}\n"
        else:
            content += "- Aucun niveau spécifié\n"
        
        content += "\n## Indicateurs\n"
        if metadata['indicators']:
            for ind in metadata['indicators']:
                content += f"- {ind}\n"
        else:
            content += "- Aucun indicateur spécifié\n"
        
        content += "\n## Notes\n"
        content += metadata['notes'] if metadata['notes'] else "Aucune note spécifique."
        
        if metadata['additional_images'] > 0:
            content += f"\n\n## Images additionnelles\n"
            content += f"Ce setup contient {metadata['additional_images']} image(s) additionnelle(s).\n"
        
        content += f"\n\nTimestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return content
    
    def reset_form(self):
        """Réinitialise le formulaire."""
        self.current_image_path = None
        self.additional_images = []
        self.mbongi_path = None
        
        # Réinitialise les variables d'affichage
        self.main_image_var.set("Image principale: Non sélectionnée")
        self.additional_images_var.set("Images additionnelles: 0")
        self.mbongi_var.set("MBONGI: Non sélectionné")
        
        # Vide la liste des images additionnelles
        self.additional_listbox.delete(0, tk.END)
        
        # Réinitialise l'affichage de l'image
        self.image_label.config(image='')
        
        # Réinitialise les métadonnées
        self.instrument_var.set(self.metadata["instrument"])
        self.timeframe_var.set(self.metadata["timeframe"])
        self.setup_type_var.set(self.metadata["setup_type"])
        self.direction_var.set(self.metadata["direction"])
        self.confidence_var.set(self.metadata["confidence"])
        self.key_levels_var.set("")
        self.indicators_var.set("")
        self.notes_var.set("")
    
    def run(self):
        """Lance l'application."""
        self.create_ui()
        self.root.mainloop()

def main():
    """Point d'entrée principal."""
    importer = TradingViewImporter()
    importer.run()

if __name__ == "__main__":
    main()