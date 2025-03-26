"""
TradingView Importer with Vision - Interface intégrée pour l'importation des captures d'écran TradingView
avec analyse automatique par l'agent de vision.
"""

import os
import sys
import shutil
import datetime
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, scrolledtext
import json
from PIL import Image, ImageTk
import threading

# Ajoute le répertoire parent au chemin d'import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importe l'agent de vision
from src.tools.vision_agent import VisionAgent

class TradingViewImporterWithVision:
    """Interface graphique pour l'importation des captures d'écran TradingView avec analyse automatique."""
    
    def __init__(self, base_dir=None):
        """
        Initialise l'interface d'importation TradingView avec analyse automatique.
        
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
        self.mbongi_content = None  # Contenu MBONGI généré ou importé
        
        # Initialise l'agent de vision
        self.vision_agent = VisionAgent()
        
        # Indique si une analyse est en cours
        self.analysis_in_progress = False
        
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
        self.root.title("Akoben - TradingView Importer with Vision")
        self.root.geometry("1280x800")
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame gauche (image et MBONGI)
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Split vertical pour l'image et le texte MBONGI
        image_mbongi_paned = ttk.PanedWindow(left_frame, orient=tk.VERTICAL)
        image_mbongi_paned.pack(fill=tk.BOTH, expand=True)
        
        # Zone d'affichage de l'image
        self.image_frame = ttk.Frame(image_mbongi_paned)
        image_mbongi_paned.add(self.image_frame, weight=1)
        
        self.image_label = ttk.Label(self.image_frame)
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Zone d'affichage du texte MBONGI
        mbongi_frame = ttk.LabelFrame(image_mbongi_paned, text="Description MBONGI")
        image_mbongi_paned.add(mbongi_frame, weight=1)
        
        self.mbongi_text = scrolledtext.ScrolledText(mbongi_frame, wrap=tk.WORD)
        self.mbongi_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
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
        
        ttk.Button(import_frame, text="3. Analyser automatiquement (Vision)", 
                   command=self.analyze_with_vision).pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(import_frame, text="4. Importer une description MBONGI", 
                   command=self.select_mbongi_file).pack(fill=tk.X, pady=(5, 0))
        
        # Statut
        self.main_image_var = tk.StringVar(value="Image principale: Non sélectionnée")
        ttk.Label(import_frame, textvariable=self.main_image_var).pack(pady=(5, 0), anchor=tk.W)
        
        self.additional_images_var = tk.StringVar(value="Images additionnelles: 0")
        ttk.Label(import_frame, textvariable=self.additional_images_var).pack(pady=(2, 0), anchor=tk.W)
        
        self.mbongi_var = tk.StringVar(value="MBONGI: Aucun")
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
        ttk.Button(action_frame, text="Réinitialiser", 
                   command=self.reset_form).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(action_frame, text="Quitter", 
                   command=self.root.destroy).pack(fill=tk.X)
        
        # Barre de statut
        self.status_var = tk.StringVar(value="Prêt")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
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
        
        # Réinitialise le contenu MBONGI
        self.mbongi_content = None
        self.mbongi_path = None
        self.mbongi_var.set("MBONGI: Non généré")
        self.mbongi_text.delete('1.0', tk.END)
        
        # Met à jour le statut
        self.status_var.set(f"Image principale sélectionnée: {os.path.basename(file)}")
    
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
            
            # Met à jour le statut
            self.status_var.set(f"{added_count} image(s) additionnelle(s) ajoutée(s)")
    
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
            
            # Met à jour le statut
            self.status_var.set(f"Image additionnelle supprimée: {filename}")
    
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
                
                # Sauvegarde le contenu
                self.mbongi_content = content
                self.mbongi_path = file
                
                # Affiche le contenu
                self.mbongi_text.delete('1.0', tk.END)
                self.mbongi_text.insert(tk.END, content)
                
                # Met à jour l'interface
                self.mbongi_var.set(f"MBONGI: {os.path.basename(file)}")
                
                # Extraction des métadonnées depuis le contenu MBONGI
                self.extract_metadata_from_mbongi(content)
        except:
            messagebox.showerror("Erreur", "Impossible de lire le fichier MBONGI sélectionné.")
            return
        
        messagebox.showinfo("Succès", f"Fichier MBONGI '{os.path.basename(file)}' importé avec succès.")
        
        # Met à jour le statut
        self.status_var.set(f"MBONGI importé: {os.path.basename(file)}")
    
    def extract_metadata_from_mbongi(self, content: str):
        """
        Extrait les métadonnées depuis le contenu MBONGI.
        
        Args:
            content (str): Contenu du fichier MBONGI.
        """
        try:
            # Direction (BUY/SELL)
            direction_match = re.search(r"# Setup (BUY|SELL)", content)
            if direction_match:
                self.direction_var.set(direction_match.group(1))
            
            # Instrument
            instrument_match = re.search(r"# Setup .+ sur ([A-Za-z0-9]+)", content)
            if instrument_match:
                self.instrument_var.set(instrument_match.group(1))
            
            # Timeframe
            timeframe_match = re.search(r"# Setup .+ \(([A-Za-z0-9]+)\)", content)
            if timeframe_match:
                self.timeframe_var.set(timeframe_match.group(1))
            
            # Type de setup
            type_match = re.search(r"Type: (.+)", content)
            if type_match:
                setup_type = type_match.group(1).strip()
                # Cherche le type de setup le plus proche dans notre liste
                for st in self.setup_types:
                    if st.lower() in setup_type.lower():
                        self.setup_type_var.set(st)
                        break
            
            # Confiance
            confidence_match = re.search(r"Confiance: (\d+)/10", content)
            if confidence_match:
                self.confidence_var.set(int(confidence_match.group(1)))
            
            # Niveaux clés
            key_levels = []
            in_key_levels_section = False
            for line in content.split('\n'):
                if "## Niveaux clés" in line or "### Supports" in line or "### Résistances" in line:
                    in_key_levels_section = True
                    continue
                elif in_key_levels_section and line.strip() == "":
                    in_key_levels_section = False
                elif in_key_levels_section and line.strip().startswith('-'):
                    level = line.strip()[1:].strip()
                    if level and level != "Aucun niveau spécifié" and level != "Aucun support significatif identifié" and level != "Aucune résistance significative identifiée":
                        key_levels.append(level)
            
            self.key_levels_var.set(", ".join(key_levels))
            
            # Indicateurs
            indicators = []
            in_indicators_section = False
            for line in content.split('\n'):
                if "## Indicateurs" in line or "### Indicateurs techniques" in line:
                    in_indicators_section = True
                    continue
                elif in_indicators_section and line.strip() == "":
                    in_indicators_section = False
                elif in_indicators_section and line.strip().startswith('-'):
                    indicator = line.strip()[1:].strip()
                    if indicator and indicator != "Aucun indicateur spécifié":
                        indicators.append(indicator)
            
            self.indicators_var.set(", ".join(indicators))
            
            # Notes
            notes = ""
            in_notes_section = False
            for line in content.split('\n'):
                if "## Notes" in line:
                    in_notes_section = True
                    continue
                elif in_notes_section and (line.strip() == "" or "##" in line):
                    break
                elif in_notes_section:
                    notes += line.strip() + " "
            
            if notes and notes != "Aucune note spécifique.":
                self.notes_var.set(notes.strip())
            
        except Exception as e:
            messagebox.showwarning("Attention", f"Erreur lors de l'extraction des métadonnées: {str(e)}")
    
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
            
            # Convertit en format Tkinter
            photo = ImageTk.PhotoImage(image)
            self.image_label.config(image=photo)
            self.image_label.image = photo  # Garde une référence
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'afficher l'image : {str(e)}")
    
    def analyze_with_vision(self):
        """Analyse l'image avec l'agent de vision."""
        if not self.current_image_path:
            messagebox.showwarning("Attention", "Veuillez d'abord sélectionner une image principale.")
            return
        
        # Vérifie si une analyse est déjà en cours
        if self.analysis_in_progress:
            messagebox.showinfo("Information", "Une analyse est déjà en cours, veuillez patienter.")
            return
        
        # Met à jour l'interface
        self.status_var.set("Analyse en cours...")
        self.analysis_in_progress = True
        
        # Lance l'analyse dans un thread séparé pour ne pas bloquer l'interface
        threading.Thread(target=self._run_analysis, daemon=True).start()
    
    def _run_analysis(self):
        """Exécute l'analyse d'image dans un thread séparé."""
        try:
            # Prépare les métadonnées
            metadata = {
                "instrument": self.instrument_var.get(),
                "timeframe": self.timeframe_var.get()
            }
            
            # Exécute l'analyse
            result = self.vision_agent.process_image(self.current_image_path, metadata, False)
            
            # Récupère le contenu MBONGI généré
            mbongi_content = result["mbongi"]
            
            # Met à jour l'interface dans le thread principal
            self.root.after(0, lambda: self._update_with_analysis_results(mbongi_content, result["analysis"]))
            
        except Exception as e:
            # Gère les erreurs dans le thread principal
            self.root.after(0, lambda: self._handle_analysis_error(str(e)))
    
    def _update_with_analysis_results(self, mbongi_content, analysis):
        """Met à jour l'interface avec les résultats d'analyse."""
        # Sauvegarde le contenu MBONGI
        self.mbongi_content = mbongi_content
        
        # Affiche le contenu dans la zone de texte
        self.mbongi_text.delete('1.0', tk.END)
        self.mbongi_text.insert(tk.END, mbongi_content)
        
        # Met à jour les variables d'interface
        self.mbongi_var.set("MBONGI: Généré automatiquement")
        
        # Extraction des métadonnées depuis l'analyse
        self._update_metadata_from_analysis(analysis)
        
        # Met à jour le statut
        self.status_var.set("Analyse terminée avec succès")
        
        # Réinitialise le flag d'analyse
        self.analysis_in_progress = False
        
        # Affiche un message de confirmation
        messagebox.showinfo("Succès", "Analyse de l'image et génération MBONGI terminées avec succès.")
    
    def _handle_analysis_error(self, error_message):
        """Gère les erreurs d'analyse."""
        # Met à jour le statut
        self.status_var.set(f"Erreur d'analyse: {error_message}")
        
        # Réinitialise le flag d'analyse
        self.analysis_in_progress = False
        
        # Affiche un message d'erreur
        messagebox.showerror("Erreur d'analyse", f"Une erreur s'est produite lors de l'analyse: {error_message}")
    
    def _update_metadata_from_analysis(self, analysis):
        """
        Met à jour les métadonnées à partir des résultats d'analyse.
        
        Args:
            analysis (Dict[str, Any]): Résultats de l'analyse.
        """
        try:
            # Direction (BUY/SELL)
            signals = analysis.get("signals", {})
            if signals and "direction" in signals:
                direction = signals["direction"]
                if direction == "buy":
                    self.direction_var.set("BUY")
                elif direction == "sell":
                    self.direction_var.set("SELL")
            
            # Confiance
            if signals and "confidence" in signals:
                confidence = int(signals["confidence"] * 10)
                self.confidence_var.set(min(max(confidence, 1), 10))  # Limite entre 1 et 10
            
            # Type de setup
            patterns = analysis.get("patterns", [])
            if patterns:
                pattern = patterns[0]["type"].replace("_", " ").title()
                # Cherche le type de setup le plus proche dans notre liste
                for st in self.setup_types:
                    if st.lower() in pattern.lower():
                        self.setup_type_var.set(st)
                        break
                else:
                    # Si aucun match direct, utilise la tendance
                    trend = analysis.get("trend", {}).get("direction", "")
                    if trend == "uptrend":
                        self.setup_type_var.set("Trend Continuation")
                    elif trend == "downtrend":
                        self.setup_type_var.set("Trend Continuation")
                    elif trend == "sideways":
                        self.setup_type_var.set("Range")
            
            # Niveaux clés
            key_levels = []
            support_resistance = analysis.get("support_resistance", {})
            
            # Supports
            for support in support_resistance.get("support", []):
                if "price" in support:
                    key_levels.append(f"Support: {support['price']:.2f}")
            
            # Résistances
            for resistance in support_resistance.get("resistance", []):
                if "price" in resistance:
                    key_levels.append(f"Résistance: {resistance['price']:.2f}")
            
            self.key_levels_var.set(", ".join(key_levels))
            
            # Indicateurs
            indicators = []
            indicators_data = analysis.get("indicators", {})
            
            # Moyennes mobiles
            for ma in indicators_data.get("moving_averages", []):
                if "type" in ma and "period" in ma:
                    indicators.append(f"{ma['type']}{ma['period']}")
            
            # Oscillateurs
            for osc in indicators_data.get("oscillators", []):
                if osc["type"] == "RSI":
                    indicators.append(f"RSI({osc.get('period', 14)})")
                elif osc["type"] == "MACD":
                    indicators.append(f"MACD({osc.get('settings', '12,26,9')})")
            
            self.indicators_var.set(", ".join(indicators))
            
            # Notes (raisonnement de l'analyse)
            if signals and "reasoning" in signals:
                reasons = signals["reasoning"]
                if reasons:
                    self.notes_var.set("; ".join(reasons))
            
        except Exception as e:
            messagebox.showwarning("Attention", f"Erreur lors de la mise à jour des métadonnées: {str(e)}")
    
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
        
        # Vérifie si un contenu MBONGI est disponible
        if not self.mbongi_content:
            if messagebox.askyesno("Attention", "Aucune description MBONGI n'a été générée ou importée. Voulez-vous générer une description automatiquement?"):
                # Lance l'analyse automatique
                self.analyze_with_vision()
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
        
        if self.mbongi_content:
            # Utilise le contenu existant
            with open(mbongi_dest, 'w') as f:
                f.write(self.mbongi_content)
        else:
            # Génère une description MBONGI basique
            mbongi_content = self.generate_basic_mbongi(metadata)
            with open(mbongi_dest, 'w') as f:
                f.write(mbongi_content)
        
        # Affiche un message de succès
        messagebox.showinfo("Succès", 
                          f"Setup généré avec succès !\n\nID: setup_{setup_id}\n\nChemin: {setup_dir}")
        
        # Met à jour le statut
        self.status_var.set(f"Setup généré: setup_{setup_id}")
        
        # Réinitialise le formulaire
        self.reset_form()
    
    def generate_basic_mbongi(self, metadata):
        """
        Génère une description MBONGI basique à partir des métadonnées.
        
        Args:
            metadata (Dict[str, Any]): Métadonnées collectées.
            
        Returns:
            str: Description MBONGI au format markdown.
        """
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
        
        content += f"\n\n## Timestamp\n"
        content += f"Généré le {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return content
    
    def reset_form(self):
        """Réinitialise le formulaire."""
        self.current_image_path = None
        self.additional_images = []
        self.mbongi_path = None
        self.mbongi_content = None
        
        # Réinitialise les variables d'affichage
        self.main_image_var.set("Image principale: Non sélectionnée")
        self.additional_images_var.set("Images additionnelles: 0")
        self.mbongi_var.set("MBONGI: Aucun")
        
        # Vide la liste des images additionnelles
        self.additional_listbox.delete(0, tk.END)
        
        # Réinitialise l'affichage de l'image
        self.image_label.config(image='')
        
        # Réinitialise le texte MBONGI
        self.mbongi_text.delete('1.0', tk.END)
        
        # Réinitialise les métadonnées
        self.instrument_var.set(self.metadata["instrument"])
        self.timeframe_var.set(self.metadata["timeframe"])
        self.setup_type_var.set(self.metadata["setup_type"])
        self.direction_var.set(self.metadata["direction"])
        self.confidence_var.set(self.metadata["confidence"])
        self.key_levels_var.set("")
        self.indicators_var.set("")
        self.notes_var.set("")
        
        # Met à jour le statut
        self.status_var.set("Formulaire réinitialisé")
    
    def run(self):
        """Lance l'application."""
        self.create_ui()
        self.root.mainloop()

def main():
    """Point d'entrée principal."""
    importer = TradingViewImporterWithVision()
    importer.run()

if __name__ == "__main__":
    main()