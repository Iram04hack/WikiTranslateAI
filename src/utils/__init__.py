# -*- coding: utf-8 -*-
"""
Module utilitaires WikiTranslateAI

Fournit les utilitaires système essentiels pour le fonctionnement du pipeline :
gestion des erreurs, checkpoints, configuration, validation, logging, etc.

Composants:
- ErrorHandler: Gestion robuste des erreurs avec tracking
- CheckpointManager: Système de sauvegarde et récupération
- Configuration: Gestion centralisée de la configuration
- Validation: Validation des données avec schémas Pydantic
- Logger: Système de logging centralisé
- ProgressTracker: Suivi de progression des tâches
"""

try:
    # Gestion des erreurs
    from .error_handler import (
        handle_error, 
        create_translation_error,
        get_error_statistics,
        ErrorType,
        TranslationError
    )
    
    # Système de checkpoints
    from .checkpoint_manager import (
        CheckpointManager,
        CheckpointType,
        CheckpointStatus,
        Checkpoint,
        create_translation_checkpoint
    )
    
    # Configuration et validation
    from .config import load_config, save_config, get_config_value
    from .json_validator import (
        TonalProcessorValidator,
        validate_translation_result,
        validate_article_structure
    )
    from .schemas import (
        ArticleSchema,
        TranslationSchema, 
        SegmentSchema,
        EvaluationSchema
    )
    
    # Logging et progression
    from .logger import setup_logger, get_logger
    from .progress import ProgressBar, ProgressCallback
    
    __all__ = [
        # Gestion d'erreurs
        'handle_error',
        'create_translation_error', 
        'get_error_statistics',
        'ErrorType',
        'TranslationError',
        
        # Checkpoints
        'CheckpointManager',
        'CheckpointType',
        'CheckpointStatus', 
        'Checkpoint',
        'create_translation_checkpoint',
        
        # Configuration
        'load_config',
        'save_config',
        'get_config_value',
        
        # Validation
        'TonalProcessorValidator',
        'validate_translation_result',
        'validate_article_structure',
        'ArticleSchema',
        'TranslationSchema',
        'SegmentSchema', 
        'EvaluationSchema',
        
        # Logging
        'setup_logger',
        'get_logger',
        'ProgressBar',
        'ProgressCallback'
    ]
    
    def initialize_system(config_file: str = None, 
                         log_level: str = 'INFO',
                         enable_checkpoints: bool = True) -> dict:
        """
        Initialise le système WikiTranslateAI avec configuration
        
        Args:
            config_file: Fichier de configuration (optionnel)
            log_level: Niveau de logging (DEBUG, INFO, WARNING, ERROR)
            enable_checkpoints: Activer le système de checkpoints
            
        Returns:
            Dictionnaire avec status d'initialisation
        """
        initialization_status = {
            'config_loaded': False,
            'logging_setup': False,
            'checkpoints_enabled': False,
            'errors': []
        }
        
        try:
            # Configuration
            if config_file:
                config = load_config(config_file)
            else:
                config = load_config()  # Configuration par défaut
            initialization_status['config_loaded'] = True
            
            # Logging
            logger = setup_logger(level=log_level)
            logger.info("WikiTranslateAI system initializing...")
            initialization_status['logging_setup'] = True
            
            # Checkpoints
            if enable_checkpoints:
                checkpoint_manager = CheckpointManager()
                logger.info("Checkpoint system enabled")
                initialization_status['checkpoints_enabled'] = True
            
            logger.info("WikiTranslateAI system initialized successfully")
            
        except Exception as e:
            error_msg = f"System initialization failed: {str(e)}"
            initialization_status['errors'].append(error_msg)
            if 'logger' in locals():
                logger.error(error_msg)
        
        return initialization_status
    
    def validate_system_health() -> dict:
        """
        Vérifie la santé du système WikiTranslateAI
        
        Returns:
            Rapport de santé système
        """
        health_report = {
            'overall_status': 'healthy',
            'components': {},
            'issues': [],
            'timestamp': None
        }
        
        try:
            from datetime import datetime
            health_report['timestamp'] = datetime.now().isoformat()
            
            # Vérifier les composants principaux
            components_to_check = [
                ('error_handler', lambda: get_error_statistics()),
                ('config', lambda: load_config()),
                ('validation', lambda: TonalProcessorValidator()),
            ]
            
            for component_name, check_func in components_to_check:
                try:
                    check_func()
                    health_report['components'][component_name] = 'ok'
                except Exception as e:
                    health_report['components'][component_name] = 'error'
                    health_report['issues'].append(f"{component_name}: {str(e)}")
            
            # Déterminer le statut global
            if health_report['issues']:
                health_report['overall_status'] = 'degraded' if len(health_report['issues']) < 3 else 'unhealthy'
                
        except Exception as e:
            health_report['overall_status'] = 'unhealthy'
            health_report['issues'].append(f"Health check failed: {str(e)}")
        
        return health_report
    
    __all__.extend(['initialize_system', 'validate_system_health'])
    
except ImportError as e:
    __all__ = []
    import warnings
    warnings.warn(f"Impossible d'importer les modules utilitaires: {e}")

# Configuration par défaut du système
SYSTEM_CONFIG = {
    'default_log_level': 'INFO',
    'max_checkpoint_size_mb': 100,
    'error_retention_days': 30,
    'config_validation': True,
    'auto_cleanup': True,
    'performance_monitoring': True
}