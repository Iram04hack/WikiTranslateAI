# -*- coding: utf-8 -*-
"""
Module de traduction WikiTranslateAI

Fournit tous les composants nécessaires pour la traduction d'articles Wikipedia
vers les langues africaines avec préservation culturelle et qualité optimisée.

Composants principaux:
- TranslationPipeline: Pipeline principal de traduction
- TermProtectionManager: Protection des termes culturels
- PivotLanguageTranslator: Traduction via langues pivot
- FallbackTranslator: Système de fallback robuste
- Queue management: Traitement parallèle
"""

# Imports des composants principaux
try:
    from .translate import TranslationPipeline
    from .term_protection import TermProtectionManager
    from .pivot_language import PivotLanguageTranslator
    from .fallback_translation import FallbackTranslator
    from .queue_manager import TranslationQueueManager, TaskPriority
    from .post_processing import PostProcessor
    from .glossary_match import GlossaryMatcher
    
    # Engines de traduction
    from .engines.openai_client import EnhancedOpenAIClient
    from .engines.local_models import LocalModelManager
    
    __all__ = [
        # Pipeline principal
        'TranslationPipeline',
        
        # Composants de traduction
        'TermProtectionManager',
        'PivotLanguageTranslator', 
        'FallbackTranslator',
        'PostProcessor',
        'GlossaryMatcher',
        
        # Gestion des tâches
        'TranslationQueueManager',
        'TaskPriority',
        
        # Engines
        'EnhancedOpenAIClient',
        'LocalModelManager'
    ]
    
    # Fonctions utilitaires
    def create_translation_pipeline(source_lang: str = "fr", target_lang: str = "fon", 
                                   enable_protection: bool = True, 
                                   use_pivot: bool = True) -> TranslationPipeline:
        """
        Crée un pipeline de traduction pré-configuré
        
        Args:
            source_lang: Langue source (fr, en)
            target_lang: Langue cible (fon, yor, ewe, dindi)
            enable_protection: Activer la protection des termes culturels
            use_pivot: Utiliser la traduction pivot pour améliorer la qualité
            
        Returns:
            Pipeline de traduction configuré
        """
        pipeline = TranslationPipeline()
        pipeline.configure(
            source_language=source_lang,
            target_language=target_lang,
            enable_term_protection=enable_protection,
            enable_pivot_translation=use_pivot
        )
        return pipeline
    
    def quick_translate(text: str, source_lang: str, target_lang: str) -> str:
        """
        Traduction rapide d'un texte
        
        Args:
            text: Texte à traduire
            source_lang: Langue source
            target_lang: Langue cible
            
        Returns:
            Texte traduit
        """
        pipeline = create_translation_pipeline(source_lang, target_lang)
        return pipeline.translate_text(text)
    
    __all__.extend(['create_translation_pipeline', 'quick_translate'])
    
except ImportError as e:
    __all__ = []
    import warnings
    warnings.warn(f"Impossible d'importer les modules de traduction: {e}")

# Configuration par défaut pour le module
TRANSLATION_CONFIG = {
    'max_segment_length': 1000,
    'batch_size': 5,
    'timeout_seconds': 30,
    'retry_attempts': 3,
    'quality_threshold': 0.7,
    'enable_caching': True
}