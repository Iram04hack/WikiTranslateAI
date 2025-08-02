# -*- coding: utf-8 -*-
# src/utils/error_handler.py

import sys
import traceback
import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from functools import wraps
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class WikiTranslateError(Exception):
    """Classe de base pour toutes les erreurs WikiTranslateAI"""
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "GENERAL_ERROR"
        self.details = details or {}
        self.timestamp = datetime.now()

class TranslationError(WikiTranslateError):
    """Erreurs li�es � la traduction"""
    def __init__(self, message: str, source_text: str = None, target_language: str = None, **kwargs):
        super().__init__(message, "TRANSLATION_ERROR", kwargs)
        self.source_text = source_text
        self.target_language = target_language

class DatabaseError(WikiTranslateError):
    """Erreurs li�es � la base de donn�es"""
    def __init__(self, message: str, query: str = None, **kwargs):
        super().__init__(message, "DATABASE_ERROR", kwargs)
        self.query = query

class ExtractionError(WikiTranslateError):
    """Erreurs li�es � l'extraction Wikipedia"""
    def __init__(self, message: str, article_title: str = None, **kwargs):
        super().__init__(message, "EXTRACTION_ERROR", kwargs)
        self.article_title = article_title

class ConfigurationError(WikiTranslateError):
    """Erreurs de configuration"""
    def __init__(self, message: str, config_key: str = None, **kwargs):
        super().__init__(message, "CONFIG_ERROR", kwargs)
        self.config_key = config_key

class ErrorHandler:
    """Gestionnaire d'erreurs centralis� pour WikiTranslateAI"""
    
    def __init__(self, log_file: str = None, max_log_size_mb: int = 50):
        """
        Initialise le gestionnaire d'erreurs
        
        Args:
            log_file: Fichier de log des erreurs
            max_log_size_mb: Taille max du fichier de log en MB
        """
        self.log_file = Path(log_file) if log_file else Path("logs/errors.log")
        self.max_log_size = max_log_size_mb * 1024 * 1024
        self.error_counts = {}
        self.last_errors = []
        self.max_recent_errors = 100
        
        # Cr�er le r�pertoire de logs
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configuration du logging sp�cialis� pour les erreurs
        self._setup_error_logging()
        
        logger.info(f"Gestionnaire d'erreurs initialis�: {self.log_file}")
    
    def _setup_error_logging(self):
        """Configure le logging sp�cialis� pour les erreurs"""
        # Handler pour fichier d'erreurs
        error_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        
        # Format d�taill� pour les erreurs
        error_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s'
        )
        error_handler.setFormatter(error_formatter)
        
        # Ajouter le handler au logger racine
        root_logger = logging.getLogger()
        root_logger.addHandler(error_handler)
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> str:
        """
        G�re une erreur de fa�on centralis�e
        
        Args:
            error: Exception � traiter
            context: Contexte additionnel
        
        Returns:
            ID unique de l'erreur
        """
        error_id = f"ERR_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(error)}"
        
        # Informations de base
        error_info = {
            'error_id': error_id,
            'timestamp': datetime.now().isoformat(),
            'type': type(error).__name__,
            'message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        # Informations sp�cialis�es pour WikiTranslateError
        if isinstance(error, WikiTranslateError):
            error_info.update({
                'error_code': error.error_code,
                'details': error.details
            })
        
        # Ajouter info syst�me
        error_info['system'] = {
            'python_version': sys.version,
            'platform': sys.platform,
            'working_directory': os.getcwd()
        }
        
        # Enregistrer l'erreur
        self._log_error(error_info)
        self._update_error_stats(error_info)
        
        # Rotation du fichier de log si n�cessaire
        self._rotate_log_if_needed()
        
        logger.error(f"Erreur trait�e: {error_id} - {error_info['type']}: {error_info['message']}")
        return error_id
    
    def _log_error(self, error_info: Dict[str, Any]):
        """Enregistre l'erreur dans le fichier de log"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                json.dump(error_info, f, ensure_ascii=False, indent=2)
                f.write('\n' + '='*80 + '\n')
        except Exception as e:
            # Erreur critique : impossible d'�crire dans le log
            print(f"ERREUR CRITIQUE: Impossible d'�crire dans {self.log_file}: {e}", file=sys.stderr)
    
    def _update_error_stats(self, error_info: Dict[str, Any]):
        """Met � jour les statistiques d'erreurs"""
        error_type = error_info['type']
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Garder les derni�res erreurs en m�moire
        self.last_errors.append({
            'error_id': error_info['error_id'],
            'timestamp': error_info['timestamp'],
            'type': error_type,
            'message': error_info['message'][:200]  # Tronquer pour �conomiser la m�moire
        })
        
        # Limiter le nombre d'erreurs r�centes
        if len(self.last_errors) > self.max_recent_errors:
            self.last_errors = self.last_errors[-self.max_recent_errors:]
    
    def _rotate_log_if_needed(self):
        """Effectue la rotation du fichier de log si n�cessaire"""
        try:
            if self.log_file.exists() and self.log_file.stat().st_size > self.max_log_size:
                # Cr�er une sauvegarde
                backup_path = self.log_file.with_suffix(f'.{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
                self.log_file.rename(backup_path)
                logger.info(f"Rotation log d'erreurs: {backup_path}")
        except Exception as e:
            logger.warning(f"�chec rotation log d'erreurs: {e}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques d'erreurs"""
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_counts_by_type': self.error_counts.copy(),
            'recent_errors': self.last_errors[-10:],  # 10 derni�res erreurs
            'log_file_size_mb': round(self.log_file.stat().st_size / (1024 * 1024), 2) if self.log_file.exists() else 0
        }
    
    def clear_error_statistics(self):
        """Remet � z�ro les statistiques d'erreurs"""
        self.error_counts.clear()
        self.last_errors.clear()
        logger.info("Statistiques d'erreurs remises � z�ro")


# Instance globale du gestionnaire d'erreurs
_global_error_handler = None

def get_error_handler() -> ErrorHandler:
    """Retourne l'instance globale du gestionnaire d'erreurs"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler

def handle_error(error: Exception, context: Dict[str, Any] = None) -> str:
    """Fonction utilitaire pour g�rer une erreur"""
    return get_error_handler().handle_error(error, context)

@contextmanager
def error_context(operation_name: str, **context_data):
    """
    Context manager pour capturer automatiquement les erreurs
    
    Args:
        operation_name: Nom de l'op�ration en cours
        **context_data: Donn�es de contexte additionnelles
    """
    context = {'operation': operation_name, **context_data}
    try:
        yield
    except Exception as e:
        error_id = handle_error(e, context)
        logger.error(f"Erreur dans {operation_name}: {error_id}")
        raise

def error_handler_decorator(operation_name: str = None, reraise: bool = True):
    """
    D�corateur pour capturer automatiquement les erreurs dans les fonctions
    
    Args:
        operation_name: Nom de l'op�ration (auto-d�tect� si None)
        reraise: Si True, relance l'exception apr�s l'avoir trait�e
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            context = {
                'function': func.__name__,
                'module': func.__module__,
                'args_count': len(args),
                'kwargs_keys': list(kwargs.keys())
            }
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_id = handle_error(e, context)
                logger.error(f"Erreur dans {op_name}: {error_id}")
                
                if reraise:
                    raise
                else:
                    return None
        
        return wrapper
    return decorator

# Fonctions utilitaires pour cr�er des erreurs sp�cialis�es
def create_translation_error(message: str, source_text: str = None, target_language: str = None, **kwargs) -> TranslationError:
    """Cr�e une erreur de traduction"""
    return TranslationError(message, source_text, target_language, **kwargs)

def create_database_error(message: str, query: str = None, **kwargs) -> DatabaseError:
    """Cr�e une erreur de base de donn�es"""
    return DatabaseError(message, query, **kwargs)

def create_extraction_error(message: str, article_title: str = None, **kwargs) -> ExtractionError:
    """Cr�e une erreur d'extraction"""
    return ExtractionError(message, article_title, **kwargs)

def create_config_error(message: str, config_key: str = None, **kwargs) -> ConfigurationError:
    """Cr�e une erreur de configuration"""
    return ConfigurationError(message, config_key, **kwargs)

# Configuration globale des erreurs non captur�es
def setup_global_error_handling():
    """Configure la gestion globale des erreurs non captur�es"""
    def global_exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Laisser Ctrl+C fonctionner normalement
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Traiter toutes les autres exceptions non captur�es
        error_id = handle_error(exc_value, {
            'uncaught': True,
            'exc_type': exc_type.__name__
        })
        
        logger.critical(f"Exception non captur�e: {error_id}")
        
        # Appeler le handler par d�faut pour afficher l'erreur
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = global_exception_handler

if __name__ == "__main__":
    # Configuration du gestionnaire d'erreurs global
    setup_global_error_handling()
    
    # Tests du gestionnaire d'erreurs
    error_handler = get_error_handler()
    
    # Test avec une erreur simple
    try:
        raise ValueError("Test d'erreur simple")
    except Exception as e:
        error_id = handle_error(e, {'test': 'error_handler'})
        print(f"Erreur trait�e: {error_id}")
    
    # Test avec une erreur sp�cialis�e
    try:
        raise create_translation_error(
            "�chec traduction test", 
            source_text="Hello world", 
            target_language="fon"
        )
    except Exception as e:
        error_id = handle_error(e)
        print(f"Erreur traduction trait�e: {error_id}")
    
    # Afficher les statistiques
    stats = error_handler.get_error_statistics()
    print(f"Statistiques d'erreurs: {stats}")