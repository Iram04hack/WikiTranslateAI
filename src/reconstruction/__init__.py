# -*- coding: utf-8 -*-
"""
Module de reconstruction WikiTranslateAI

Système de reconstruction d'articles Wikipedia traduits avec préservation
de la structure, formatage et métadonnées originales.

Composants:
- ArticleReconstructor: Reconstruction complète des articles
- FormatHandler: Gestion des formats de sortie (HTML, TXT, JSON)
- StructurePreserver: Préservation de la structure Wikipedia
- MediaHandler: Gestion des médias et liens
"""

try:
    from .rebuild_article import (
        ArticleReconstructor,
        ReconstructionOptions,
        reconstruct_article
    )
    from .format_handler import (
        FormatHandler,
        OutputFormat,
        HTMLFormatter,
        TextFormatter,
        JSONFormatter
    )
    
    __all__ = [
        # Reconstruction principale
        'ArticleReconstructor',
        'ReconstructionOptions', 
        'reconstruct_article',
        
        # Formatage
        'FormatHandler',
        'OutputFormat',
        'HTMLFormatter',
        'TextFormatter',
        'JSONFormatter'
    ]
    
    def quick_reconstruct(translated_sections: list,
                         original_metadata: dict,
                         output_format: str = 'html') -> str:
        """
        Reconstruction rapide d'un article traduit
        
        Args:
            translated_sections: Sections traduites avec structure
            original_metadata: Métadonnées de l'article original
            output_format: Format de sortie ('html', 'txt', 'json')
            
        Returns:
            Article reconstruit dans le format demandé
        """
        reconstructor = ArticleReconstructor()
        
        # Configuration par défaut
        options = ReconstructionOptions(
            preserve_links=True,
            preserve_formatting=True,
            include_metadata=True,
            output_format=OutputFormat(output_format.upper())
        )
        
        return reconstructor.reconstruct(
            translated_sections=translated_sections,
            original_metadata=original_metadata,
            options=options
        )
    
    def reconstruct_with_validation(translated_sections: list,
                                  original_metadata: dict,
                                  validate_structure: bool = True,
                                  validate_links: bool = True) -> dict:
        """
        Reconstruction avec validation complète
        
        Args:
            translated_sections: Sections traduites
            original_metadata: Métadonnées originales
            validate_structure: Valider la structure HTML
            validate_links: Valider les liens internes/externes
            
        Returns:
            Dictionnaire avec article reconstruit et rapport de validation
        """
        reconstructor = ArticleReconstructor()
        
        options = ReconstructionOptions(
            preserve_links=True,
            preserve_formatting=True,
            include_metadata=True,
            validate_output=validate_structure,
            validate_links=validate_links
        )
        
        result = reconstructor.reconstruct_with_validation(
            translated_sections=translated_sections,
            original_metadata=original_metadata,
            options=options
        )
        
        return {
            'reconstructed_article': result['article'],
            'validation_report': result['validation'],
            'statistics': {
                'sections_count': len(translated_sections),
                'total_length': len(result['article']),
                'links_preserved': result['validation'].get('links_valid', 0),
                'structure_valid': result['validation'].get('structure_valid', False)
            }
        }
    
    def batch_reconstruct(translated_articles: list,
                         output_directory: str = 'output/reconstructed',
                         output_format: str = 'html') -> dict:
        """
        Reconstruction en lot de plusieurs articles
        
        Args:
            translated_articles: Liste d'articles traduits
            output_directory: Répertoire de sortie
            output_format: Format de sortie
            
        Returns:
            Rapport de reconstruction en lot
        """
        import os
        
        batch_report = {
            'total_articles': len(translated_articles),
            'successful_reconstructions': 0,
            'failed_reconstructions': 0,
            'output_files': [],
            'errors': []
        }
        
        # Créer le répertoire de sortie
        os.makedirs(output_directory, exist_ok=True)
        
        reconstructor = ArticleReconstructor()
        
        for i, article_data in enumerate(translated_articles):
            try:
                title = article_data.get('title', f'article_{i}')
                translated_sections = article_data.get('translated_sections', [])
                original_metadata = article_data.get('metadata', {})
                
                # Reconstruction
                reconstructed = quick_reconstruct(
                    translated_sections=translated_sections,
                    original_metadata=original_metadata,
                    output_format=output_format
                )
                
                # Sauvegarde
                filename = f"{title.replace(' ', '_')}.{output_format}"
                file_path = os.path.join(output_directory, filename)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(reconstructed)
                
                batch_report['output_files'].append(file_path)
                batch_report['successful_reconstructions'] += 1
                
            except Exception as e:
                batch_report['failed_reconstructions'] += 1
                batch_report['errors'].append({
                    'article_index': i,
                    'title': article_data.get('title', f'article_{i}'),
                    'error': str(e)
                })
        
        return batch_report
    
    __all__.extend(['quick_reconstruct', 'reconstruct_with_validation', 'batch_reconstruct'])
    
except ImportError as e:
    __all__ = []
    import warnings
    warnings.warn(f"Impossible d'importer les modules de reconstruction: {e}")

# Configuration par défaut
RECONSTRUCTION_CONFIG = {
    'default_output_format': 'html',
    'preserve_original_structure': True,
    'include_metadata': True,
    'validate_by_default': True,
    'supported_formats': ['html', 'txt', 'json', 'xml'],
    'max_article_size_mb': 10,
    'encoding': 'utf-8'
}