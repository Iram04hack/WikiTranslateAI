# src/utils/progress.py
import sys
import time
import threading
from datetime import datetime, timedelta

class ProgressBar:
    """Barre de progression améliorée pour le suivi de traduction"""
    
    def __init__(self, total, description="Progression"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = datetime.now()
        self.last_update = self.start_time
        self.speed = 0  # éléments par seconde
        self.finished = False
        self.lock = threading.Lock()
        self.status_text = ""
        self._thread = None
    
    def update(self, current=None, status=None):
        """Met à jour la progression"""
        with self.lock:
            if current is not None:
                self.current = current
            else:
                self.current += 1
            
            if status is not None:
                self.status_text = status
            
            now = datetime.now()
            elapsed = (now - self.last_update).total_seconds()
            
            # Calculer la vitesse sur les 5 dernières secondes
            if elapsed >= 5:
                self.speed = (self.current / (now - self.start_time).total_seconds())
                self.last_update = now
    
    def _render(self):
        """Rend la barre de progression dans le terminal"""
        while not self.finished:
            with self.lock:
                # Calcul des statistiques
                percent = min(100, self.current / self.total * 100)
                elapsed = (datetime.now() - self.start_time).total_seconds()
                
                # Estimation du temps restant
                if self.speed > 0:
                    remaining_items = self.total - self.current
                    eta_seconds = remaining_items / self.speed
                    eta = str(timedelta(seconds=int(eta_seconds)))
                else:
                    eta = "??:??:??"
                
                # Créer la barre visuelle
                bar_length = 40
                filled_length = int(bar_length * self.current // self.total)
                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                
                # Ligne d'état
                status = f"{self.status_text}" if self.status_text else ""
                
                # Message complet
                message = f"\r{self.description}: |{bar}| {percent:.1f}% {self.current}/{self.total} "
                message += f"[Vitesse: {self.speed:.2f}/s, Temps restant: {eta}] {status}"
                
                # Afficher
                sys.stdout.write(message)
                sys.stdout.flush()
            
            time.sleep(0.5)  # Mise à jour toutes les 500ms
    
    def start(self):
        """Démarre l'affichage de la barre de progression"""
        self._thread = threading.Thread(target=self._render)
        self._thread.daemon = True
        self._thread.start()
    
    def finish(self):
        """Marque la tâche comme terminée"""
        with self.lock:
            self.finished = True
            self.current = self.total
        
        if self._thread:
            self._thread.join(1)
        
        # Affichage final
        elapsed = (datetime.now() - self.start_time).total_seconds()
        message = f"\r{self.description}: Terminé! {self.total}/{self.total} éléments en {elapsed:.2f} secondes "
        message += f"(vitesse moyenne: {self.total/elapsed:.2f}/s)\n"
        sys.stdout.write(message)
        sys.stdout.flush()