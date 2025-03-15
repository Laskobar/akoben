"""
Module de surveillance des sessions pour Mbongi.
Permet de détecter les connexions et déconnexions XRDP.
"""

import os
import time
import subprocess
import re
import psutil
import threading
import logging
from typing import Dict, List, Any, Optional, Callable, Set, Tuple
from datetime import datetime


class SessionMonitor:
    """
    Moniteur de sessions pour Mbongi.
    Détecte les sessions XRDP et permet des actions automatiques en début et fin de session.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialise le moniteur de sessions.
        
        Args:
            config: Dictionnaire de configuration optionnel
        """
        self.config = config or {}
        self.log_dir = self.config.get('log_dir', 'logs')
        self.check_interval = self.config.get('check_interval', 60)  # Secondes
        self.xrdp_process_names = self.config.get('xrdp_process_names', ['xrdp-sesman', 'xrdp'])
        
        # Callbacks
        self.on_session_start = None
        self.on_session_end = None
        
        # État interne
        self.session_active = False
        self.monitoring_thread = None
        self.should_stop = threading.Event()
        self.last_active_time = None
        
        # Configuration du logging
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        """Configure le logging pour le moniteur."""
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.logger = logging.getLogger('SessionMonitor')
        self.logger.setLevel(logging.INFO)
        
        # Handler pour fichier
        log_file = os.path.join(self.log_dir, 'session_monitor.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Handler pour console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Ajouter les handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def start_monitoring(self) -> None:
        """Démarre la surveillance des sessions en arrière-plan."""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.logger.warning("Le thread de surveillance est déjà en cours d'exécution.")
            return
        
        self.should_stop.clear()
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        self.logger.info("Surveillance des sessions démarrée.")
    
    def stop_monitoring(self) -> None:
        """Arrête la surveillance des sessions."""
        if not self.monitoring_thread or not self.monitoring_thread.is_alive():
            self.logger.warning("Aucun thread de surveillance en cours d'exécution.")
            return
        
        self.logger.info("Arrêt de la surveillance des sessions...")
        self.should_stop.set()
        self.monitoring_thread.join(timeout=5)
        
        if self.monitoring_thread.is_alive():
            self.logger.warning("Le thread de surveillance ne s'est pas arrêté proprement.")
        else:
            self.logger.info("Surveillance des sessions arrêtée.")
    
    def _monitoring_loop(self) -> None:
        """Boucle principale de surveillance."""
        self.logger.info("Démarrage de la boucle de surveillance.")
        
        while not self.should_stop.is_set():
            try:
                is_session_active = self._check_session_active()
                
                # Détection de changement d'état
                if is_session_active and not self.session_active:
                    self._handle_session_start()
                elif not is_session_active and self.session_active:
                    self._handle_session_end()
                
                # Mettre à jour l'état
                self.session_active = is_session_active
                
                # Pause avant la prochaine vérification
                self.should_stop.wait(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de surveillance: {str(e)}")
                time.sleep(10)  # Pause plus longue en cas d'erreur
    
    def _check_session_active(self) -> bool:
        """
        Vérifie si une session XRDP est actuellement active.
        
        Returns:
            True si une session est active, False sinon
        """
        # Vérifier les processus XRDP
        xrdp_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username']):
            try:
                process_info = proc.info
                process_name = process_info['name'].lower()
                
                # Vérifier si c'est un processus XRDP
                if any(xrdp_name in process_name for xrdp_name in self.xrdp_process_names):
                    xrdp_processes.append(process_info)
                    
                # Détecter également les sessions X
                if 'xorg' in process_name or 'x11' in process_name:
                    xrdp_processes.append(process_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Vérifier l'activité utilisateur récente
        idle_time = self._get_idle_time()
        
        # Vérifier les sessions utilisateur
        who_output = self._run_command(['who'])
        has_user_sessions = bool(who_output.strip())
        
        # Combiner les facteurs
        is_active = (
            len(xrdp_processes) > 0 and  # Processus XRDP en cours
            idle_time <= 3600 and        # Pas d'inactivité prolongée (1 heure)
            has_user_sessions            # Session utilisateur présente
        )
        
        # Mise à jour du temps d'activité
        if is_active:
            self.last_active_time = datetime.now()
        
        return is_active
    
    def _get_idle_time(self) -> int:
        """
        Tente de déterminer le temps d'inactivité de l'utilisateur en secondes.
        
        Returns:
            Temps d'inactivité en secondes, ou une grande valeur par défaut
        """
        # Si on n'a jamais détecté d'activité, retourner une grande valeur
        if not self.last_active_time:
            return 24 * 3600  # 24 heures
        
        # Calculer le temps écoulé depuis la dernière activité détectée
        elapsed = (datetime.now() - self.last_active_time).total_seconds()
        
        # Essayer d'obtenir une mesure plus précise avec xprintidle si disponible
        try:
            xprintidle_output = self._run_command(['xprintidle'])
            if xprintidle_output.strip():
                idle_ms = int(xprintidle_output.strip())
                return idle_ms / 1000  # Convertir en secondes
        except Exception:
            # Si xprintidle échoue, utiliser le temps écoulé comme approximation
            pass
        
        return elapsed
    
    def _handle_session_start(self) -> None:
        """Gère le début d'une session."""
        self.logger.info("Session XRDP détectée - début de session.")
        
        if self.on_session_start:
            try:
                self.on_session_start()
            except Exception as e:
                self.logger.error(f"Erreur lors de l'exécution du callback de début de session: {str(e)}")
    
    def _handle_session_end(self) -> None:
        """Gère la fin d'une session."""
        self.logger.info("Fin de session XRDP détectée.")
        
        if self.on_session_end:
            try:
                self.on_session_end()
            except Exception as e:
                self.logger.error(f"Erreur lors de l'exécution du callback de fin de session: {str(e)}")
    
    def _run_command(self, command: List[str]) -> str:
        """
        Exécute une commande système et renvoie sa sortie.
        
        Args:
            command: Liste contenant la commande et ses arguments
            
        Returns:
            Sortie de la commande
        """
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            return result.stdout
        except subprocess.SubprocessError as e:
            self.logger.error(f"Erreur lors de l'exécution de {' '.join(command)}: {str(e)}")
            return ""
    
    def register_session_start_callback(self, callback: Callable[[], None]) -> None:
        """
        Enregistre un callback à appeler lors du début d'une session.
        
        Args:
            callback: Fonction à appeler sans arguments
        """
        self.on_session_start = callback
    
    def register_session_end_callback(self, callback: Callable[[], None]) -> None:
        """
        Enregistre un callback à appeler lors de la fin d'une session.
        
        Args:
            callback: Fonction à appeler sans arguments
        """
        self.on_session_end = callback


# Test simple du module si exécuté directement
if __name__ == "__main__":
    # Définir les callbacks de test
    def on_start():
        print("Session démarrée!")
    
    def on_end():
        print("Session terminée!")
    
    # Créer et configurer le moniteur
    monitor = SessionMonitor()
    monitor.register_session_start_callback(on_start)
    monitor.register_session_end_callback(on_end)
    
    # Démarrer la surveillance
    print("Démarrage de la surveillance des sessions XRDP...")
    monitor.start_monitoring()
    
    try:
        # Boucle principale pour garder le script en vie
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nArrêt de la surveillance...")
        monitor.stop_monitoring()
        print("Surveillance arrêtée.")