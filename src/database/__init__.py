# -*- coding: utf-8 -*-
"""
Module base de données WikiTranslateAI

Système de gestion des données avec SQLite pour le stockage des glossaires,
cache des traductions, métadonnées des articles et ressources linguistiques.

Composants:
- DatabaseConnection: Connexion et gestion de la base SQLite
- GlossaryManager: Gestion des glossaires multilingues
- CacheManager: Cache intelligent des traductions
- TerminologyImporter: Import de terminologies externes
- Schema: Définition des schémas de base de données
"""

try:
    # Composants principaux
    from .db_connection import DatabaseConnection, get_db_connection
    from .glossary_manager import GlossaryManager, GlossaryEntry
    from .cache_manager import CacheManager, CacheEntry
    from .terminology_importer import TerminologyImporter
    from .schema import (
        create_tables,
        SCHEMA_VERSION,
        upgrade_schema,
        DatabaseSchema
    )
    from .glossary_learner import GlossaryLearner
    from .wiktionary_extractor import WiktionaryExtractor
    
    __all__ = [
        # Connexion base
        'DatabaseConnection',
        'get_db_connection',
        
        # Gestion glossaires
        'GlossaryManager',
        'GlossaryEntry',
        'GlossaryLearner',
        
        # Cache
        'CacheManager', 
        'CacheEntry',
        
        # Import/Export
        'TerminologyImporter',
        'WiktionaryExtractor',
        
        # Schéma
        'create_tables',
        'SCHEMA_VERSION',
        'upgrade_schema',
        'DatabaseSchema'
    ]
    
    def initialize_database(db_path: str = "data/wikitranslateai.db",
                          force_recreate: bool = False) -> dict:
        """
        Initialise la base de données WikiTranslateAI
        
        Args:
            db_path: Chemin vers la base de données SQLite
            force_recreate: Forcer la recréation des tables
            
        Returns:
            Statut d'initialisation
        """
        init_status = {
            'database_created': False,
            'tables_created': False,
            'schema_version': None,
            'errors': []
        }
        
        try:
            # Connexion à la base
            db_conn = DatabaseConnection(db_path)
            init_status['database_created'] = True
            
            # Création/mise à jour du schéma
            if force_recreate:
                db_conn.execute("DROP TABLE IF EXISTS glossary_entries")
                db_conn.execute("DROP TABLE IF EXISTS translation_cache") 
                db_conn.execute("DROP TABLE IF EXISTS article_metadata")
            
            schema_result = create_tables(db_conn)
            init_status['tables_created'] = schema_result['success']
            init_status['schema_version'] = SCHEMA_VERSION
            
            if not schema_result['success']:
                init_status['errors'].extend(schema_result.get('errors', []))
            
            db_conn.close()
            
        except Exception as e:
            init_status['errors'].append(f"Database initialization failed: {str(e)}")
            
        return init_status
    
    def setup_glossaries(languages: list = None) -> dict:
        """
        Configure les glossaires pour les langues spécifiées
        
        Args:
            languages: Liste des langues (par défaut: ['fon', 'yor', 'ewe', 'dindi'])
            
        Returns:
            Statut de configuration des glossaires
        """
        if languages is None:
            languages = ['fon', 'yor', 'ewe', 'dindi']
        
        setup_status = {
            'glossaries_created': 0,
            'entries_imported': 0,
            'errors': []
        }
        
        try:
            glossary_manager = GlossaryManager()
            
            for language in languages:
                try:
                    # Créer/configurer le glossaire
                    glossary_id = glossary_manager.create_glossary(
                        name=f"Glossaire {language.upper()}",
                        source_language="fr",
                        target_language=language,
                        description=f"Glossaire français-{language} pour WikiTranslateAI"
                    )
                    
                    setup_status['glossaries_created'] += 1
                    
                    # Importer des entrées de base si disponibles
                    importer = TerminologyImporter()
                    base_entries_file = f"data/glossaries/{language}_base_terms.json"
                    
                    import os
                    if os.path.exists(base_entries_file):
                        imported_count = importer.import_from_json(base_entries_file, glossary_id)
                        setup_status['entries_imported'] += imported_count
                        
                except Exception as e:
                    setup_status['errors'].append(f"Error setting up {language} glossary: {str(e)}")
            
        except Exception as e:
            setup_status['errors'].append(f"Glossary setup failed: {str(e)}")
        
        return setup_status
    
    def get_database_statistics() -> dict:
        """
        Retourne les statistiques de la base de données
        
        Returns:
            Statistiques détaillées
        """
        stats = {
            'database_size_mb': 0,
            'total_glossary_entries': 0,
            'cached_translations': 0,
            'article_metadata_count': 0,
            'glossaries_by_language': {},
            'cache_hit_rate': 0.0
        }
        
        try:
            db_conn = get_db_connection()
            
            # Taille de la base
            import os
            if os.path.exists(db_conn.db_path):
                stats['database_size_mb'] = round(os.path.getsize(db_conn.db_path) / (1024*1024), 2)
            
            # Statistiques des tables
            glossary_manager = GlossaryManager()
            cache_manager = CacheManager()
            
            stats['total_glossary_entries'] = glossary_manager.count_entries()
            stats['cached_translations'] = cache_manager.count_entries()
            stats['glossaries_by_language'] = glossary_manager.get_glossaries_by_language()
            stats['cache_hit_rate'] = cache_manager.get_hit_rate()
            
            db_conn.close()
            
        except Exception as e:
            stats['error'] = str(e)
        
        return stats
    
    __all__.extend(['initialize_database', 'setup_glossaries', 'get_database_statistics'])
    
except ImportError as e:
    __all__ = []
    import warnings
    warnings.warn(f"Impossible d'importer les modules de base de données: {e}")

# Configuration par défaut
DATABASE_CONFIG = {
    'default_db_path': 'data/wikitranslateai.db',
    'cache_size_mb': 50,
    'auto_vacuum': True,
    'backup_frequency_hours': 24,
    'max_cache_entries': 10000,
    'supported_languages': ['fon', 'yor', 'ewe', 'dindi']
}