#!/usr/bin/env python3
"""
Script d'installation du système d'apprentissage hybride Akoben.
Ce script installe tous les composants nécessaires et configure l'environnement.
"""

import os
import sys
import shutil
import subprocess
import argparse
import logging
import datetime
import platform
import time

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("hybrid_learning_setup.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("HybridLearningSetup")

class HybridLearningSetup:
    """Installation et configuration du système d'apprentissage hybride Akoben."""
    
    def __init__(self, akoben_dir=None):
        """
        Initialise le configurateur.
        
        Args:
            akoben_dir (str): Répertoire de base Akoben.
        """
        # Détermine le répertoire de base
        if akoben_dir is None:
            self.akoben_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        else:
            self.akoben_dir = akoben_dir
        
        # Détermine le répertoire de base
        if akoben_dir is None:
            self.akoben_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        else:
            self.akoben_dir = akoben_dir
        
        # Répertoires importants
        self.src_dir = os.path.join(self.akoben_dir, "src")
        self.tools_dir = os.path.join(self.src_dir, "tools")
        self.scripts_dir = os.path.join(self.akoben_dir, "scripts")
        
        # Crée les répertoires s'ils n'existent pas
        for directory in [self.src_dir, self.tools_dir, self.scripts_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Répertoires de données
        self.base_dir = os.path.join(os.path.expanduser("~"), "akoben")
        self.tradingview_dir = os.path.join(self.base_dir, "tradingview_captures")
        self.models_dir = os.path.join(self.base_dir, "models")
        self.vision_models_dir = os.path.join(self.models_dir, "vision")
        
        # Crée les répertoires de données s'ils n'existent pas
        for directory in [self.base_dir, self.tradingview_dir, self.models_dir, self.vision_models_dir]:
            os.makedirs(directory, exist_ok=True)
        
        logger.info(f"Configuration initialisée avec répertoire Akoben: {self.akoben_dir}")
    
    def check_dependencies(self):
        """
        Vérifie les dépendances nécessaires.
        
        Returns:
            bool: True si toutes les dépendances sont satisfaites, False sinon.
        """
        try:
            # Vérifie la version de Python
            python_version = platform.python_version()
            logger.info(f"Version Python: {python_version}")
            
            major, minor, _ = map(int, python_version.split('.'))
            if major < 3 or (major == 3 and minor < 6):
                logger.error(f"Version Python {python_version} trop ancienne. Python 3.6+ requis.")
                return False
            
            # Liste des bibliothèques requises
            required_packages = [
                "numpy", "opencv-python", "Pillow", "matplotlib", 
                "pandas", "scikit-learn", "joblib"
            ]
            
            missing_packages = []
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_packages.append(package)
            
            if missing_packages:
                logger.warning(f"Bibliothèques manquantes: {', '.join(missing_packages)}")
                return False
            
            logger.info("Toutes les dépendances sont satisfaites")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des dépendances: {str(e)}")
            return False
    
    def install_dependencies(self):
        """
        Installe les dépendances manquantes.
        
        Returns:
            bool: True si l'installation a réussi, False sinon.
        """
        try:
            # Liste des bibliothèques requises
            required_packages = [
                "numpy", "opencv-python", "Pillow", "matplotlib", 
                "pandas", "scikit-learn", "joblib"
            ]
            
            # Installe pip si nécessaire
            try:
                import pip
            except ImportError:
                logger.warning("pip non trouvé, tentative d'installation...")
                subprocess.run([sys.executable, "-m", "ensurepip", "--default-pip"], check=True)
            
            # Installe les bibliothèques
            logger.info("Installation des dépendances...")
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
            subprocess.run([sys.executable, "-m", "pip", "install"] + required_packages, check=True)
            
            logger.info("Dépendances installées avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'installation des dépendances: {str(e)}")
            return False
    
    def install_vision_agent(self):
        """
        Installe l'agent de vision.
        
        Returns:
            bool: True si l'installation a réussi, False sinon.
        """
        try:
            # Chemin source pour le fichier vision_agent.py
            vision_agent_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vision_agent.py")
            
            # Chemin de destination
            dest_path = os.path.join(self.tools_dir, "vision_agent.py")
            
            # Vérifie si le fichier source existe
            if not os.path.exists(vision_agent_path):
                logger.error(f"Fichier source introuvable: {vision_agent_path}")
                return False
            
            # Copie le fichier
            shutil.copy2(vision_agent_path, dest_path)
            
            logger.info(f"Agent de vision installé: {dest_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'installation de l'agent de vision: {str(e)}")
            return False
    
    def install_tradingview_importer(self):
        """
        Installe l'interface d'importation TradingView avec vision.
        
        Returns:
            bool: True si l'installation a réussi, False sinon.
        """
        try:
            # Chemin source pour le fichier tradingview_importer_impl.py
            importer_source = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                        "tradingview_importer_with_vision.py")
            
            # Chemins de destination
            impl_path = os.path.join(self.tools_dir, "tradingview_importer_impl.py")
            wrapper_path = os.path.join(self.tools_dir, "tradingview_importer.py")
            
            # Vérifie si le fichier source existe
            if not os.path.exists(importer_source):
                logger.error(f"Fichier source introuvable: {importer_source}")
                return False
            
            # Copie le fichier d'implémentation
            shutil.copy2(importer_source, impl_path)
            
            # Crée le fichier wrapper
            with open(wrapper_path, 'w') as f:
                f.write("""#!/usr/bin/env python3
'''
Script d'importation des captures d'écran TradingView pour Akoben.
'''
import os
import sys

# Ajoute le répertoire parent au chemin d'import
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.tools.tradingview_importer_impl import TradingViewImporterWithVision as TradingViewImporter

def main():
    importer = TradingViewImporter()
    importer.run()

if __name__ == "__main__":
    main()
""")
            
            # Rend le fichier exécutable
            os.chmod(wrapper_path, 0o755)
            
            logger.info(f"Interface d'importation TradingView installée: {impl_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'installation de l'interface d'importation: {str(e)}")
            return False
    
    def create_desktop_shortcut(self):
        """
        Crée un raccourci bureau pour l'importation TradingView.
        
        Returns:
            bool: True si la création a réussi, False sinon.
        """
        try:
            # Détermine le répertoire bureau
            desktop_dir = os.path.expanduser("~/Desktop")
            if not os.path.exists(desktop_dir):
                desktop_dir = os.path.expanduser("~/Bureau")  # Pour les systèmes en français
            
            if not os.path.exists(desktop_dir):
                logger.warning(f"Répertoire bureau introuvable, création du raccourci impossible")
                return False
            
            # Chemin du raccourci
            shortcut_path = os.path.join(desktop_dir, "Akoben TradingView Importer.desktop")
            
            # Crée le fichier .desktop
            with open(shortcut_path, 'w') as f:
                f.write(f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Akoben TradingView Importer
Comment=Interface d'importation des captures d'écran TradingView avec vision
Exec={sys.executable} {os.path.join(self.tools_dir, "tradingview_importer.py")}
Icon=utilities-terminal
Terminal=false
Categories=Utility;
""")
            
            # Rend le fichier exécutable
            os.chmod(shortcut_path, 0o755)
            
            logger.info(f"Raccourci bureau créé: {shortcut_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du raccourci bureau: {str(e)}")
            return False
    
    def install_hybrid_learning_system(self):
        """
        Installe tous les composants du système d'apprentissage hybride.
        
        Returns:
            bool: True si l'installation a réussi, False sinon.
        """
        logger.info("Installation du système d'apprentissage hybride...")
        
        # Vérifie les dépendances
        if not self.check_dependencies():
            logger.info("Installation des dépendances manquantes...")
            if not self.install_dependencies():
                logger.error("Échec de l'installation des dépendances")
                return False
        
        # Installe l'agent de vision
        logger.info("Installation de l'agent de vision...")
        if not self.install_vision_agent():
            logger.error("Échec de l'installation de l'agent de vision")
            return False
        
        # Installe l'interface d'importation TradingView
        logger.info("Installation de l'interface d'importation TradingView...")
        if not self.install_tradingview_importer():
            logger.error("Échec de l'installation de l'interface d'importation")
            return False
        
        # Crée un raccourci bureau
        logger.info("Création d'un raccourci bureau...")
        self.create_desktop_shortcut()  # Optionnel, ne pas bloquer en cas d'échec
        
        logger.info("Installation du système d'apprentissage hybride terminée avec succès")
        return True
    
    def setup_nightly_retraining(self):
        """
        Configure le réentraînement nocturne automatique.
        
        Returns:
            bool: True si la configuration a réussi, False sinon.
        """
        try:
            # Chemin pour le script de réentraînement nocturne
            retraining_script = os.path.join(self.scripts_dir, "run_nightly_retraining.sh")
            
            # Crée le script
            with open(retraining_script, 'w') as f:
                f.write(f"""#!/bin/bash
# Script de réentraînement nocturne pour le système Akoben

# Répertoire de base Akoben
AKOBEN_DIR="{self.akoben_dir}"
TOOLS_DIR="$AKOBEN_DIR/src/tools"

# Fonction de logging
log() {{
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}}

# Exécute le réentraînement nocturne
log "Démarrage du réentraînement nocturne..."
{sys.executable} "$TOOLS_DIR/nightly_retraining.py"
if [ $? -ne 0 ]; then
    log "ERREUR: Échec du réentraînement nocturne"
    exit 1
fi
log "Réentraînement nocturne terminé avec succès"

# Vérifie si un nouveau modèle a été déployé
if [ -f "$AKOBEN_DIR/models/model_updated.flag" ]; then
    log "Un nouveau modèle a été déployé, redémarrage du trading..."
    # Ici, vous pourriez ajouter un script pour redémarrer le système de trading
    # par exemple: systemctl restart akoben_trader.service
    rm "$AKOBEN_DIR/models/model_updated.flag"
else
    log "Aucun nouveau modèle déployé, le trading continue avec le modèle actuel"
fi

exit 0
""")
            
            # Rend le script exécutable
            os.chmod(retraining_script, 0o755)
            
            # Crée les fichiers systemd pour l'exécution automatique
            systemd_service = os.path.join(self.scripts_dir, "akoben_nightly_retraining.service")
            systemd_timer = os.path.join(self.scripts_dir, "akoben_nightly_retraining.timer")
            
            with open(systemd_service, 'w') as f:
                f.write(f"""[Unit]
Description=Akoben Nightly Retraining
After=network.target

[Service]
User={os.environ.get('USER', 'akoben')}
WorkingDirectory={self.akoben_dir}
ExecStart={retraining_script}
Restart=no
Type=oneshot

[Install]
WantedBy=multi-user.target
""")
            
            with open(systemd_timer, 'w') as f:
                f.write("""[Unit]
Description=Exécute le réentraînement nocturne Akoben chaque nuit

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
""")
            
            # Donne les instructions pour installer le service
            logger.info("Configuration du réentraînement nocturne terminée")
            logger.info("")
            logger.info("Pour installer le service systemd, exécutez les commandes suivantes:")
            logger.info("  mkdir -p ~/.config/systemd/user/")
            logger.info(f"  cp {systemd_service} ~/.config/systemd/user/")
            logger.info(f"  cp {systemd_timer} ~/.config/systemd/user/")
            logger.info("  systemctl --user daemon-reload")
            logger.info("  systemctl --user enable akoben_nightly_retraining.timer")
            logger.info("  systemctl --user start akoben_nightly_retraining.timer")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration du réentraînement nocturne: {str(e)}")
            return False
    
    def run(self):
        """
        Exécute le processus d'installation complet.
        
        Returns:
            bool: True si l'installation a réussi, False sinon.
        """
        logger.info("Démarrage de l'installation du système d'apprentissage hybride Akoben")
        
        # Installe le système d'apprentissage hybride
        if not self.install_hybrid_learning_system():
            logger.error("Échec de l'installation du système d'apprentissage hybride")
            return False
        
        # Configure le réentraînement nocturne
        if not self.setup_nightly_retraining():
            logger.warning("Échec de la configuration du réentraînement nocturne")
            # Continue malgré l'échec
        
        logger.info("")
        logger.info("Installation terminée avec succès!")
        logger.info("")
        logger.info("Pour lancer l'interface d'importation TradingView, utilisez la commande:")
        logger.info(f"  {sys.executable} {os.path.join(self.tools_dir, 'tradingview_importer.py')}")
        logger.info("")
        logger.info("Ou utilisez le raccourci sur le bureau.")
        
        return True

def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description='Installation du système d\'apprentissage hybride Akoben.')
    parser.add_argument('--akoben-dir', type=str, help='Répertoire de base Akoben')
    
    args = parser.parse_args()
    
    setup = HybridLearningSetup(args.akoben_dir)
    if setup.run():
        print("\nInstallation terminée avec succès!")
    else:
        print("\nÉchec de l'installation. Consultez le fichier de log pour plus de détails.")
        sys.exit(1)

if __name__ == "__main__":
    main()