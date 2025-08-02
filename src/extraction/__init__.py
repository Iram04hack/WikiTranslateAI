# -*- coding: utf-8 -*-
"""
Module d'extraction WikiTranslateAI

Système d'extraction d'articles Wikipedia avec analyse structurelle avancée,
segmentation intelligente et préparation pour la traduction.

Composants:
- WikipediaExtractor: Extraction d'articles depuis l'API Wikipedia
- WikipediaStructureParser: Analyse et parsing de la structure HTML
- TextSegmentation: Segmentation intelligente pour la traduction
- CleanText: Nettoyage et normalisation du contenu
- APIClient: Interface avec l'API Wikipedia
"""

try:
    # Composants principaux
    from .get_wiki_articles import WikipediaExtractor, extract_article
    from .structure_parser import WikipediaStructureParser, ParsedStructure
    from .segmentation import TextSegmentation, Segment
    from .clean_text import TextCleaner, clean_wikipedia_text
    from .api_client import WikipediaAPIClient
    
    __all__ = [
        # Extracteurs
        'WikipediaExtractor',
        'extract_article',
        
        # Parsing et structure
        'WikipediaStructureParser',
        'ParsedStructure',
        
        # Segmentation
        'TextSegmentation',
        'Segment',
        
        # Nettoyage
        'TextCleaner',
        'clean_wikipedia_text',
        
        # API
        'WikipediaAPIClient'
    ]
    
    def extract_and_prepare(title: str, language: str = 'fr', 
                           clean: bool = True, 
                           segment: bool = True) -> dict:
        """
        Extraction et préparation complète d'un article
        
        Args:
            title: Titre de l'article Wikipedia
            language: Code de langue (fr, en, etc.)
            clean: Nettoyer le contenu extrait
            segment: Segmenter le texte pour la traduction
            
        Returns:
            Dictionnaire avec article structuré et préparé
        """
        # Extraction
        extractor = WikipediaExtractor(language)
        article_data = extractor.extract_article(title)
        
        if not article_data:
            return {'error': f'Article "{title}" non trouvé en {language}'}
        
        # Parsing de structure
        parser = WikipediaStructureParser()
        structure = parser.parse_article_structure(article_data)
        
        # Nettoyage si demandé
        if clean:
            cleaner = TextCleaner()
            structure = cleaner.clean_structure(structure)
        
        # Segmentation si demandée
        if segment:
            segmenter = TextSegmentation()
            structure = segmenter.segment_structure(structure)
        
        return {
            'title': title,
            'language': language,
            'structure': structure,
            'metadata': {
                'cleaned': clean,
                'segmented': segment,
                'sections_count': len(structure.get('sections', [])),
                'total_content_length': sum(
                    len(section.get('content', '')) 
                    for section in structure.get('sections', [])
                )
            }
        }
    
    def quick_extract(title: str, language: str = 'fr') -> str:
        """
        Extraction rapide du contenu principal d'un article
        
        Args:
            title: Titre de l'article
            language: Code de langue
            
        Returns:
            Contenu principal de l'article (texte brut)
        """
        extractor = WikipediaExtractor(language)
        article_data = extractor.extract_article(title)
        
        if not article_data:
            return ""
        
        # Extraction du contenu principal seulement
        cleaner = TextCleaner()
        return cleaner.extract_main_content(article_data.get('content', ''))
    
    def get_article_info(title: str, language: str = 'fr') -> dict:
        """
        Récupère les métadonnées d'un article sans le contenu complet
        
        Args:
            title: Titre de l'article
            language: Code de langue
            
        Returns:
            Métadonnées de l'article
        """
        api_client = WikipediaAPIClient(language)
        return api_client.get_page_info(title)
    
    __all__.extend(['extract_and_prepare', 'quick_extract', 'get_article_info'])
    
except ImportError as e:
    __all__ = []
    import warnings
    warnings.warn(f"Impossible d'importer les modules d'extraction: {e}")

# Configuration par défaut
EXTRACTION_CONFIG = {
    'default_language': 'fr',
    'supported_languages': ['fr', 'en', 'es', 'de', 'it'],
    'max_content_length': 100000,  # 100KB max par article
    'timeout_seconds': 30,
    'retry_attempts': 3,
    'user_agent': 'WikiTranslateAI/1.0 (https://github.com/wikitranslateai)',
    'clean_by_default': True,
    'segment_by_default': True,
    'min_segment_length': 50,
    'max_segment_length': 1000
}