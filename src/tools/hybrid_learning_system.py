"""
Akoben Hybrid Learning System - Système d'apprentissage hybride pour Akoben.
Ce module coordonne l'ensemble du processus d'apprentissage hybride combinant:
- Trading live sur MT5 pendant la journée
- Importation manuelle des captures TradingView
- Génération automatique des descriptions MBONGI 
- Réentraînement nocturne et déploiement automatique

Il fournit également des scripts de configuration pour l'automatisation.
"""

import os
import sys
import json
import glob
import datetime
import logging
import time
import subprocess
import argparse
import shutil
# Ajoute le répertoire parent au chemin d'import
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from typing import Dict, List, Any, Optional

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("hybrid_learning_system.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("HybridLearningSystem")

class HybridLearningSystem:
    """Système d'apprentissage hybride pour Akoben."""
    
    def __init__(self, base_dir=None):
        """
        Initialise le système d'apprentissage hybride.
        
        Args:
            base_dir (str): Répertoire de base pour le système Akoben.
        """
        # Configuration des répertoires
        if base_dir is None:
            self.base_dir = os.path.join(os.path.expanduser("~"), "akoben")
        else:
            self.base_dir = base_dir
        
        # Structure des répertoires
        self.tradingview_dir = os.path.join(self.base_dir, "tradingview_captures")
        self.mt5_data_dir = os.path.join(self.base_dir, "mt5_data")
        self.models_dir = os.path.join(self.base_dir, "models")
        self.tools_dir = os.path.join(self.base_dir, "src", "tools")
        self.scripts_dir = os.path.join(self.base_dir, "scripts")
        
        # S'assure que les répertoires existent
        for directory in [self.tradingview_dir, self.mt5_data_dir, 
                        self.models_dir, self.tools_dir, self.scripts_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Chemins des scripts
        self.importer_script = os.path.join(self.tools_dir, "tradingview_importer.py")
        self.mbongi_generator_script = os.path.join(self.tools_dir, "mbongi_generator.py")
        self.retraining_script = os.path.join(self.tools_dir, "nightly_retraining.py")
        
        logger.info(f"Système d'apprentissage hybride initialisé avec répertoire de base: {self.base_dir}")
    
    def setup_scripts(self) -> bool:
        """
        Configure les scripts nécessaires au fonctionnement du système.
        
        Returns:
            bool: True si la configuration a réussi, False sinon.
        """
        try:
            # Crée le script d'importation TradingView s'il n'existe pas
            if not os.path.exists(self.importer_script):
                logger.info(f"Création du script d'importation TradingView: {self.importer_script}")
                with open(self.importer_script, 'w') as f:
                    f.write("""#!/usr/bin/env python3
'''
Script d'importation des captures d'écran TradingView pour Akoben.
'''
import os
import sys

# Ajoute le répertoire parent au chemin d'import
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(parent_dir)

from src.tools.tradingview_importer import main

if __name__ == "__main__":
    main()
""")
                os.chmod(self.importer_script, 0o755)
            
            # Crée le script générateur MBONGI s'il n'existe pas
            if not os.path.exists(self.mbongi_generator_script):
                logger.info(f"Création du script générateur MBONGI: {self.mbongi_generator_script}")
                with open(self.mbongi_generator_script, 'w') as f:
                    f.write("""#!/usr/bin/env python3
'''
Script de génération automatique des descriptions MBONGI pour Akoben.
'''
import os
import sys

# Ajoute le répertoire parent au chemin d'import
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(parent_dir)

from src.tools.mbongi_generator import main

if __name__ == "__main__":
    main()
""")
                os.chmod(self.mbongi_generator_script, 0o755)
            
            # Crée le script de réentraînement nocturne s'il n'existe pas
            if not os.path.exists(self.retraining_script):
                logger.info(f"Création du script de réentraînement nocturne: {self.retraining_script}")
                with open(self.retraining_script, 'w') as f:
                    f.write("""#!/usr/bin/env python3
'''
Script de réentraînement nocturne pour Akoben.
'''
import os
import sys

# Ajoute le répertoire parent au chemin d'import
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(parent_dir)

from src.tools.nightly_retraining import main

if __name__ == "__main__":
    main()
""")
                os.chmod(self.retraining_script, 0o755)
            
            # Crée un script de workflow complet
            workflow_script = os.path.join(self.scripts_dir, "run_hybrid_workflow.sh")
            if not os.path.exists(workflow_script):
                logger.info(f"Création du script de workflow: {workflow_script}")
                with open(workflow_script, 'w') as f:
                    f.write("""#!/bin/bash
# Script de workflow pour le système d'apprentissage hybride Akoben

# Répertoire de base Akoben
AKOBEN_DIR="$HOME/akoben"
TOOLS_DIR="$AKOBEN_DIR/src/tools"

# Fonction de logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# 1. Exécution du générateur MBONGI (crée des descriptions standardisées pour les captures importées)
log "Démarrage du générateur MBONGI..."
python3 "$TOOLS_DIR/mbongi_generator.py"
if [ $? -ne 0 ]; then
    log "ERREUR: Échec du générateur MBONGI"
    exit 1
fi
log "Générateur MBONGI terminé avec succès"

# 2. Exécution du réentraînement nocturne
log "Démarrage du réentraînement nocturne..."
python3 "$TOOLS_DIR/nightly_retraining.py"
if [ $? -ne 0 ]; then
    log "ERREUR: Échec du réentraînement nocturne"
    exit 1
fi
log "Réentraînement nocturne terminé avec succès"

# 3. Vérification si un nouveau modèle a été déployé
if [ -f "$AKOBEN_DIR/models/model_updated.flag" ]; then
    log "Un nouveau modèle a été déployé, redémarrage du trading..."
    # Ici, vous pourriez ajouter un script pour redémarrer le système de trading
    # par exemple: systemctl restart akoben_trader.service
    rm "$AKOBEN_DIR/models/model_updated.flag"
else
    log "Aucun nouveau modèle déployé, le trading continue avec le modèle actuel"
fi

log "Workflow hybride terminé avec succès"
exit 0
""")
                os.chmod(workflow_script, 0o755)
            
            # Crée un script pour l'importation TradingView
            import_script = os.path.join(self.scripts_dir, "import_tradingview.sh")
            if not os.path.exists(import_script):
                logger.info(f"Création du script d'importation: {import_script}")
                with open(import_script, 'w') as f:
                    f.write("""#!/bin/bash
# Script pour lancer l'interface d'importation TradingView

# Répertoire de base Akoben
AKOBEN_DIR="$HOME/akoben"
TOOLS_DIR="$AKOBEN_DIR/src/tools"

# Fonction de logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Lance l'interface d'importation
log "Démarrage de l'interface d'importation TradingView..."
python3 "$TOOLS_DIR/tradingview_importer.py"
exit $?
""")
                os.chmod(import_script, 0o755)
            
            # Crée un fichier de service systemd pour le workflow nocturne
            service_file = os.path.join(self.scripts_dir, "akoben_hybrid_learning.service")
            if not os.path.exists(service_file):
                logger.info(f"Création du fichier de service systemd: {service_file}")
                with open(service_file, 'w') as f:
                    f.write(f"""[Unit]
Description=Akoben Hybrid Learning System
After=network.target

[Service]
User={os.environ.get('USER', 'akoben')}
WorkingDirectory={self.base_dir}
ExecStart={os.path.join(self.scripts_dir, "run_hybrid_workflow.sh")}
Restart=no
Type=oneshot

[Install]
WantedBy=multi-user.target
""")
            
            # Crée un fichier timer systemd pour exécuter le workflow toutes les nuits
            timer_file = os.path.join(self.scripts_dir, "akoben_hybrid_learning.timer")
            if not os.path.exists(timer_file):
                logger.info(f"Création du fichier timer systemd: {timer_file}")
                with open(timer_file, 'w') as f:
                    f.write("""[Unit]
Description=Exécute le workflow d'apprentissage hybride Akoben chaque nuit

[Timer]
OnCalendar=*-*-* 01:00:00
Persistent=true

[Install]
WantedBy=timers.target
""")
            
            logger.info("Configuration des scripts terminée avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration des scripts: {str(e)}")
            return False
    
    def install_systemd_service(self) -> bool:
        """
        Installe le service systemd pour le réentraînement nocturne.
        
        Returns:
            bool: True si l'installation a réussi, False sinon.
        """
        try:
            service_file = os.path.join(self.scripts_dir, "akoben_hybrid_learning.service")
            timer_file = os.path.join(self.scripts_dir, "akoben_hybrid_learning.timer")
            
            if not os.path.exists(service_file) or not os.path.exists(timer_file):
                logger.error("Fichiers de service ou timer manquants")
                return False
            
            # Copie les fichiers dans le répertoire systemd
            user_systemd_dir = os.path.expanduser("~/.config/systemd/user")
            os.makedirs(user_systemd_dir, exist_ok=True)
            
            shutil.copy2(service_file, os.path.join(user_systemd_dir, "akoben_hybrid_learning.service"))
            shutil.copy2(timer_file, os.path.join(user_systemd_dir, "akoben_hybrid_learning.timer"))
            
            # Recharge les services systemd
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
            
            # Active et démarre le timer
            subprocess.run(["systemctl", "--user", "enable", "akoben_hybrid_learning.timer"], check=True)
            subprocess.run(["systemctl", "--user", "start", "akoben_hybrid_learning.timer"], check=True)
            
            logger.info("Service systemd installé et activé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'installation du service systemd: {str(e)}")
            return False
    
    def create_desktop_shortcut(self) -> bool:
        """
        Crée un raccourci bureau pour l'importation TradingView.
        
        Returns:
            bool: True si la création a réussi, False sinon.
        """
        try:
            desktop_dir = os.path.expanduser("~/Desktop")
            if not os.path.exists(desktop_dir):
                desktop_dir = os.path.expanduser("~/Bureau")  # Pour les systèmes en français
            
            if not os.path.exists(desktop_dir):
                logger.warning(f"Répertoire bureau introuvable, création du raccourci impossible")
                return False
            
            shortcut_path = os.path.join(desktop_dir, "Akoben TradingView Importer.desktop")
            
            with open(shortcut_path, 'w') as f:
                f.write(f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Akoben TradingView Importer
Comment=Interface d'importation des captures d'écran TradingView
Exec={os.path.join(self.scripts_dir, "import_tradingview.sh")}
Icon=utilities-terminal
Terminal=false
Categories=Utility;
""")
            
            os.chmod(shortcut_path, 0o755)
            
            logger.info(f"Raccourci bureau créé: {shortcut_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du raccourci bureau: {str(e)}")
            return False
    
    def copy_module_files(self) -> bool:
        """
        Copie les modules implémentés dans les répertoires appropriés.
        
        Returns:
            bool: True si la copie a réussi, False sinon.
        """
        try:
            # Dans une implémentation réelle, vous copieriez ici
            # les fichiers Python que nous avons développés précédemment
            # dans les répertoires appropriés.
            
            # Pour simplifier, nous allons juste créer des placeholders
            modules = {
                "tradingview_importer.py": """
# Placeholder pour le module TradingView Importer
# Dans une implémentation réelle, ce fichier serait remplacé par le code complet
from src.tools.tradingview_importer_impl import TradingViewImporter

def main():
    importer = TradingViewImporter()
    importer.run()

if __name__ == "__main__":
    main()
""",
                "mbongi_generator.py": """
# Placeholder pour le module MBONGI Generator
# Dans une implémentation réelle, ce fichier serait remplacé par le code complet
from src.tools.mbongi_generator_impl import MbongiGenerator

def main():
    generator = MbongiGenerator()
    generator.run()

if __name__ == "__main__":
    main()
""",
                "nightly_retraining.py": """
# Placeholder pour le module Nightly Retraining
# Dans une implémentation réelle, ce fichier serait remplacé par le code complet
from src.tools.nightly_retraining_impl import NightlyRetrainingSystem

def main():
    retraining_system = NightlyRetrainingSystem()
    success = retraining_system.run()
    import sys
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
"""
            }
            
            # Crée les modules d'implémentation
            impl_dir = os.path.join(self.tools_dir, "impls")
            os.makedirs(impl_dir, exist_ok=True)
            
            for module_name, content in modules.items():
                # Crée le module principal
                module_path = os.path.join(self.tools_dir, module_name)
                with open(module_path, 'w') as f:
                    f.write(content)
                os.chmod(module_path, 0o755)
                
                # Crée un module d'implémentation vide
                impl_name = module_name.replace(".py", "_impl.py")
                impl_path = os.path.join(self.tools_dir, impl_name)
                if not os.path.exists(impl_path):
                    with open(impl_path, 'w') as f:
                        f.write(f"# Implémentation de {module_name}\n# Ce fichier sera remplacé par le code réel\n")
            
            logger.info("Modules copiés avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la copie des modules: {str(e)}")
            return False
    
    def setup(self) -> bool:
        """
        Configure l'ensemble du système d'apprentissage hybride.
        
        Returns:
            bool: True si la configuration a réussi, False sinon.
        """
        logger.info("Démarrage de la configuration du système d'apprentissage hybride")
        
        # 1. Configuration des scripts
        if not self.setup_scripts():
            logger.error("Échec de la configuration des scripts")
            return False
        
        # 2. Copie des modules
        if not self.copy_module_files():
            logger.error("Échec de la copie des modules")
            return False
        
        # 3. Création du raccourci bureau
        self.create_desktop_shortcut()  # Optionnel, ne pas bloquer en cas d'échec
        
        # 4. Installation du service systemd
        if not self.install_systemd_service():
            logger.warning("Échec de l'installation du service systemd")
            # Ne pas bloquer en cas d'échec, le système peut fonctionner manuellement
        
        logger.info("Configuration du système d'apprentissage hybride terminée avec succès")
        return True
    
    def run_manual_workflow(self) -> bool:
        """
        Exécute manuellement le workflow d'apprentissage hybride.
        
        Returns:
            bool: True si l'exécution a réussi, False sinon.
        """
        try:
            logger.info("Démarrage manuel du workflow d'apprentissage hybride")
            
            # 1. Exécution du générateur MBONGI
            logger.info("Exécution du générateur MBONGI...")
            mbongi_result = subprocess.run([sys.executable, self.mbongi_generator_script], 
                                         capture_output=True, text=True, check=False)
            
            if mbongi_result.returncode != 0:
                logger.error(f"Échec du générateur MBONGI: {mbongi_result.stderr}")
                return False
            
            logger.info("Générateur MBONGI terminé avec succès")
            
            # 2. Exécution du réentraînement nocturne
            logger.info("Exécution du réentraînement nocturne...")
            retraining_result = subprocess.run([sys.executable, self.retraining_script],
                                             capture_output=True, text=True, check=False)
            
            if retraining_result.returncode != 0:
                logger.error(f"Échec du réentraînement nocturne: {retraining_result.stderr}")
                return False
            
            logger.info("Réentraînement nocturne terminé avec succès")
            
            # 3. Vérification si un nouveau modèle a été déployé
            model_updated_flag = os.path.join(self.models_dir, "model_updated.flag")
            if os.path.exists(model_updated_flag):
                logger.info("Un nouveau modèle a été déployé")
                os.remove(model_updated_flag)
            else:
                logger.info("Aucun nouveau modèle déployé")
            
            logger.info("Workflow manuel terminé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du workflow manuel: {str(e)}")
            return False
    
    def launch_importer(self) -> bool:
        """
        Lance l'interface d'importation TradingView.
        
        Returns:
            bool: True si le lancement a réussi, False sinon.
        """
        try:
            logger.info("Lancement de l'interface d'importation TradingView")
            
            # Exécute le script d'importation en arrière-plan
            subprocess.Popen([sys.executable, self.importer_script])
            
            logger.info("Interface d'importation lancée avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du lancement de l'interface d'importation: {str(e)}")
            return False

def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description="Système d'apprentissage hybride Akoben")
    parser.add_argument("--setup", action="store_true", help="Configure le système")
    parser.add_argument("--run", action="store_true", help="Exécute le workflow manuellement")
    parser.add_argument("--import", dest="import_tv", action="store_true", help="Lance l'interface d'importation")
    
    args = parser.parse_args()
    
    hybrid_system = HybridLearningSystem()
    
    if args.setup:
        success = hybrid_system.setup()
        sys.exit(0 if success else 1)
    elif args.import_tv:
        success = hybrid_system.launch_importer()
        sys.exit(0 if success else 1)
    elif args.run:
        success = hybrid_system.run_manual_workflow()
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(0)

if __name__ == "__main__":
    main()