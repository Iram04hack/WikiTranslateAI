# -*- coding: utf-8 -*-
"""
WikiTranslateAI - Système de traduction Wikipedia vers les langues africaines

Ce package fournit un pipeline complet pour :
- Extraction d'articles Wikipedia
- Traduction vers les langues africaines (Fon, Yoruba, Ewe, Dindi)
- Préservation culturelle et tonalité
- Évaluation de qualité spécialisée
- Reconstruction des articles traduits

Usage principal:
    from wikitranslateai import TranslationPipeline
    
    pipeline = TranslationPipeline()
    result = pipeline.translate_article("Histoire du Bénin", "fr", "fon")
"""

__version__ = "1.0.0"
__author__ = "WikiTranslateAI Team"
__license__ = "MIT"

# Imports principaux pour faciliter l'utilisation
try:
    from .translation.translate import TranslationPipeline
    from .extraction.get_wiki_articles import WikipediaExtractor
    from .reconstruction.rebuild_article import ArticleReconstructor
    from .evaluation.evaluate_translation import TranslationEvaluator
    
    # Composants avancés
    from .translation.term_protection import TermProtectionManager
    from .translation.pivot_language import PivotLanguageTranslator
    from .utils.checkpoint_manager import CheckpointManager
    from .utils.error_handler import handle_error, create_translation_error
    
    __all__ = [
        'TranslationPipeline',
        'WikipediaExtractor', 
        'ArticleReconstructor',
        'TranslationEvaluator',
        'TermProtectionManager',
        'PivotLanguageTranslator',
        'CheckpointManager',
        'handle_error',
        'create_translation_error'
    ]
    
except ImportError as e:
    # Imports optionnels en cas de dépendances manquantes
    __all__ = []
    import warnings
    warnings.warn(f"Certains modules WikiTranslateAI ne peuvent pas être importés: {e}")

# Configuration par défaut
DEFAULT_CONFIG = {
    'supported_languages': ['fon', 'yor', 'yoruba', 'ewe', 'dindi'],
    'source_languages': ['fr', 'en'],
    'default_models': {
        'openai': 'gpt-4o-mini',
        'fallback': 'google',
        'local': 'opus-mt'
    },
    'quality_threshold': 0.7,
    'enable_cultural_protection': True,
    'enable_tonal_processing': True
}

def get_version():
    """Retourne la version de WikiTranslateAI"""
    return __version__

def get_supported_languages():
    """Retourne la liste des langues supportées"""
    return DEFAULT_CONFIG['supported_languages'].copy()

def get_default_config():
    """Retourne la configuration par défaut"""
    return DEFAULT_CONFIG.copy()