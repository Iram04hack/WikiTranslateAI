# src/utils/translation_tracker.py

import os
import json
import logging
from datetime import datetime
from threading import Lock, RLock

logger = logging.getLogger(__name__)

class TranslationTracker:
    """Suivi des traductions et statistiques du projet"""
    
    _instance = None
    _lock = Lock()
    
    @classmethod
    def get_instance(cls):
        """Singleton pattern pour accéder à l'instance du tracker"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = TranslationTracker()
            return cls._instance
    
    def __init__(self):
        """Initialise le tracker de traductions"""
        self.history_file = os.path.join("data", "translation_history.json")
        self._stats_lock = RLock()  # RLock pour protéger les opérations sur les stats
        self.stats = {
            'project_start': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'last_translation': None,
            'total_global': 0,
            'total_by_language': {},
            'daily_progress': {},
            'categories': {}
        }
        
        # Charger l'historique existant s'il existe
        self._load_history()
    
    def _load_history(self):
        """Charge l'historique des traductions"""
        with self._stats_lock:
            try:
                if os.path.exists(self.history_file):
                    with open(self.history_file, 'r', encoding='utf-8') as f:
                        self.stats = json.load(f)
                    logger.info(f"Historique des traductions chargé depuis {self.history_file}")
            except Exception as e:
                logger.error(f"Erreur lors du chargement de l'historique: {e}")
    
    def _save_history(self):
        """Sauvegarde l'historique des traductions"""
        with self._stats_lock:
            try:
                os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump(self.stats, f, ensure_ascii=False, indent=2)
                logger.info(f"Historique des traductions sauvegardé dans {self.history_file}")
            except Exception as e:
                logger.error(f"Erreur lors de la sauvegarde de l'historique: {e}")
    
    def record_translation(self, article_title, source_lang, target_lang, categories=None):
        """
        Enregistre une nouvelle traduction
        
        Args:
            article_title: Titre de l'article
            source_lang: Langue source
            target_lang: Langue cible
            categories: Liste des catégories de l'article
        """
        with self._stats_lock:
            # Mise à jour de la date de dernière traduction
            now = datetime.now()
            self.stats['last_translation'] = now.strftime("%Y-%m-%d %H:%M:%S")
            
            # Incrémenter le compteur global
            self.stats['total_global'] += 1
            
            # Mise à jour des compteurs par langue
            lang_pair = f"{source_lang}-{target_lang}"
            if lang_pair not in self.stats['total_by_language']:
                self.stats['total_by_language'][lang_pair] = 0
            self.stats['total_by_language'][lang_pair] += 1
            
            # Mise à jour des compteurs par catégorie
            if categories:
                for category in categories:
                    if category not in self.stats['categories']:
                        self.stats['categories'][category] = 0
                    self.stats['categories'][category] += 1
            
            # Mise à jour des statistiques quotidiennes
            today = now.strftime("%Y-%m-%d")
            if today not in self.stats['daily_progress']:
                self.stats['daily_progress'][today] = {}
            
            if target_lang not in self.stats['daily_progress'][today]:
                self.stats['daily_progress'][today][target_lang] = 0
                
            self.stats['daily_progress'][today][target_lang] += 1
            
            # Sauvegarde des statistiques
            self._save_history()
            
            logger.info(f"Traduction enregistrée: {article_title} ({source_lang} → {target_lang})")
    
    def get_stats(self):
        """Renvoie les statistiques courantes"""
        with self._stats_lock:
            return self.stats.copy()  # Retourne une copie pour éviter la modification externe

def get_tracker():
    """Fonction utilitaire pour obtenir l'instance du tracker"""
    return TranslationTracker.get_instance()