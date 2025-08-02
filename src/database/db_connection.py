# -*- coding: utf-8 -*-
# src/database/db_connection.py

import os
import sqlite3
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Gestionnaire de connexions de base de donnees centralise pour WikiTranslateAI"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialise le gestionnaire de connexion DB
        
        Args:
            db_path: Chemin vers la base de donnees SQLite
        """
        if db_path is None:
            # Utiliser le chemin par defaut depuis les variables d'environnement
            db_path = os.environ.get('DATABASE_URL', 'sqlite:///data/glossaries/glossary.db')
            if db_path.startswith('sqlite:///'):
                db_path = db_path[10:]  # Retirer 'sqlite://'
        
        self.db_path = Path(db_path)
        self.connection_params = {}
        self._active_connections = {}
        
        # Creer les repertoires parents si necessaire
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Gestionnaire DB initialise: {self.db_path}")
    
    @contextmanager
    def get_connection(self, connection_id: str = "default"):
        """
        Context manager pour obtenir une connexion DB
        
        Args:
            connection_id: Identifiant unique pour la connexion
        
        Yields:
            sqlite3.Connection: Connexion a la base de donnees
        """
        conn = None
        try:
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=30.0,
                check_same_thread=False
            )
            
            # Configuration optimisee pour SQLite
            conn.execute("PRAGMA journal_mode=WAL")  # Mode Write-Ahead Logging
            conn.execute("PRAGMA synchronous=NORMAL")  # Balance performance/securite
            conn.execute("PRAGMA temp_store=MEMORY")  # Tables temporaires en memoire
            conn.execute("PRAGMA cache_size=10000")  # Cache plus large
            conn.execute("PRAGMA foreign_keys=ON")  # Activer contraintes FK
            
            # Fonctions SQL personnalisees pour WikiTranslateAI
            conn.create_function("normalize_text", 1, self._normalize_text)
            conn.create_function("calculate_similarity", 2, self._calculate_similarity)
            
            self._active_connections[connection_id] = conn
            logger.debug(f"Connexion DB ouverte: {connection_id}")
            
            yield conn
            
        except sqlite3.Error as e:
            logger.error(f"Erreur connexion DB {connection_id}: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                try:
                    conn.close()
                    if connection_id in self._active_connections:
                        del self._active_connections[connection_id]
                    logger.debug(f"Connexion DB fermee: {connection_id}")
                except sqlite3.Error as e:
                    logger.warning(f"Erreur fermeture connexion {connection_id}: {e}")
    
    def execute_query(self, query: str, params: tuple = (), connection_id: str = "default") -> list:
        """
        Execute une requete SELECT et retourne les resultats
        
        Args:
            query: Requete SQL SELECT
            params: Parametres de la requete
            connection_id: ID de connexion
        
        Returns:
            List des resultats
        """
        with self.get_connection(connection_id) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            logger.debug(f"Requete executee: {len(results)} resultats")
            return results
    
    def execute_update(self, query: str, params: tuple = (), connection_id: str = "default") -> int:
        """
        Execute une requete INSERT/UPDATE/DELETE
        
        Args:
            query: Requete SQL de modification
            params: Parametres de la requete
            connection_id: ID de connexion
        
        Returns:
            Nombre de lignes affectees
        """
        with self.get_connection(connection_id) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            affected_rows = cursor.rowcount
            logger.debug(f"Requete UPDATE executee: {affected_rows} lignes affectees")
            return affected_rows
    
    def check_database_health(self) -> Dict[str, Any]:
        """
        Verifie l'etat de sante de la base de donnees
        
        Returns:
            Dict avec les metriques de sante
        """
        health_info = {
            'db_exists': self.db_path.exists(),
            'db_size_mb': 0,
            'connection_test': False,
            'tables_count': 0,
            'last_error': None
        }
        
        try:
            if health_info['db_exists']:
                health_info['db_size_mb'] = round(self.db_path.stat().st_size / (1024 * 1024), 2)
            
            with self.get_connection("health_check") as conn:
                health_info['connection_test'] = True
                
                # Compter les tables
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                health_info['tables_count'] = cursor.fetchone()[0]
                
        except Exception as e:
            health_info['last_error'] = str(e)
            logger.error(f"Echec check sante DB: {e}")
        
        return health_info
    
    def _normalize_text(self, text: str) -> str:
        """Fonction SQL personnalisee pour normaliser le texte"""
        if not text:
            return ""
        return text.lower().strip()
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Fonction SQL personnalisee pour calculer la similarite"""
        if not text1 or not text2:
            return 0.0
        
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())
        
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0


# Instance globale pour utilisation dans tout le projet
_global_db_connection = None

def get_database_connection(db_path: Optional[str] = None) -> DatabaseConnection:
    """
    Retourne l'instance globale du gestionnaire de DB
    
    Args:
        db_path: Chemin vers la DB (utilise seulement a la premiere initialisation)
    
    Returns:
        Instance DatabaseConnection
    """
    global _global_db_connection
    
    if _global_db_connection is None:
        _global_db_connection = DatabaseConnection(db_path)
    
    return _global_db_connection


if __name__ == "__main__":
    # Test du gestionnaire de connexion
    db_conn = get_database_connection("test_db.sqlite")
    
    # Test de sante
    health = db_conn.check_database_health()
    print(f"Etat de sante DB: {health}")