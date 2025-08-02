# main.py

import os
import argparse
import logging
from pathlib import Path
from src.utils.config import load_config
from src.extraction.get_wiki_articles import WikipediaExtractor
from src.extraction.clean_text import WikiTextCleaner
from src.extraction.segmentation import TextSegmenter
from src.translation.translate import translate_article, translate_directory

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_extraction(config, title=None, search=None, random=False, count=5, language=None):
    """
    Exécute l'étape d'extraction
    
    Args:
        config: Configuration
        title: Titre d'un article spécifique
        search: Terme de recherche
        random: Extraire des articles aléatoires
        count: Nombre d'articles
        language: Langue source
    
    Returns:
        Liste des chemins des fichiers extraits
    """
    output_dir = config['paths']['articles_raw']
    lang = language or config['extraction']['default_language']
    
    extractor = WikipediaExtractor(output_dir, lang)
    
    if title:
        path = extractor.extract_article_by_title(
            title,
            config['extraction']['include_wikitext'],
            config['extraction']['include_html']
        )
        return [path] if path else []
    
    elif search:
        return extractor.search_and_extract(
            search,
            count,
            config['extraction']['include_wikitext'],
            config['extraction']['include_html']
        )
    
    elif random:
        return extractor.extract_random_articles(
            count,
            config['extraction']['include_wikitext'],
            config['extraction']['include_html']
        )
    
    else:
        logger.error("Aucun mode d'extraction spécifié (titre, recherche ou aléatoire)")
        return []

def run_cleaning(config, input_path, prefer_html=True):
    """
    Exécute l'étape de nettoyage
    
    Args:
        config: Configuration
        input_path: Chemin d'entrée (fichier ou répertoire)
        prefer_html: Préférer le HTML au wikitext
    
    Returns:
        Liste des chemins des fichiers nettoyés
    """
    output_dir = config['paths']['articles_cleaned']
    
    cleaner = WikiTextCleaner(output_dir)
    
    if os.path.isdir(input_path):
        count = cleaner.clean_directory(input_path, prefer_html)
        return [os.path.join(output_dir, f) for f in os.listdir(output_dir) 
                if os.path.isfile(os.path.join(output_dir, f))]
    elif os.path.isfile(input_path):
        result = cleaner.clean_article_file(input_path, prefer_html)
        if result:
            return [os.path.join(output_dir, os.path.basename(input_path))]
        return []
    else:
        logger.error(f"Le chemin d'entrée n'existe pas: {input_path}")
        return []

def run_segmentation(config, input_path):
    """
    Exécute l'étape de segmentation
    
    Args:
        config: Configuration
        input_path: Chemin d'entrée (fichier ou répertoire)
    
    Returns:
        Liste des chemins des fichiers segmentés
    """
    output_dir = config['paths']['articles_segmented']
    
    segmenter = TextSegmenter(
        output_dir,
        config['segmentation']['max_segment_length'],
        config['segmentation']['min_segment_length']
    )
    
    if os.path.isdir(input_path):
        count = segmenter.segment_directory(input_path)
        return [os.path.join(output_dir, f) for f in os.listdir(output_dir) 
                if os.path.isfile(os.path.join(output_dir, f))]
    elif os.path.isfile(input_path):
        result = segmenter.segment_article_file(input_path)
        if result:
            return [os.path.join(output_dir, os.path.basename(input_path))]
        return []
    else:
        logger.error(f"Le chemin d'entrée n'existe pas: {input_path}")
        return []

def run_translation(config, input_path, source_lang, target_lang):
    """
    Exécute l'étape de traduction
    
    Args:
        config: Configuration
        input_path: Chemin d'entrée (fichier ou répertoire)
        source_lang: Langue source
        target_lang: Langue cible
    
    Returns:
        Liste des chemins des fichiers traduits
    """
    output_dir = config['paths']['articles_translated']
    
    if os.path.isdir(input_path):
        count = translate_directory(
            input_dir=input_path,
            source_lang=source_lang,
            target_lang=target_lang,
            output_dir=output_dir,
            api_key=config['translation']['api_key'],
            api_version=config['translation']['api_version'],
            azure_endpoint=config['translation']['azure_endpoint'],
            model=config['translation']['model'],
            glossary_db=config['paths'].get('glossary_db'),
            use_glossary=config['translation']['use_glossary']
        )
        return [os.path.join(output_dir, target_lang, f) 
                for f in os.listdir(os.path.join(output_dir, target_lang)) 
                if os.path.isfile(os.path.join(output_dir, target_lang, f))]
    elif os.path.isfile(input_path):
        result = translate_article(
            input_file=input_path,
            source_lang=source_lang,
            target_lang=target_lang,
            output_dir=output_dir,
            api_key=config['translation']['api_key'],
            api_version=config['translation']['api_version'],
            azure_endpoint=config['translation']['azure_endpoint'],
            model=config['translation']['model'],
            glossary_db=config['paths'].get('glossary_db'),
            use_glossary=config['translation']['use_glossary']
        )
        if result:
            return [result]
        return []
    else:
        logger.error(f"Le chemin d'entrée n'existe pas: {input_path}")
        return []

def run_pipeline(config, title=None, search=None, random=False, count=5, 
                source_lang=None, target_lang=None, steps=None):
    """
    Exécute le pipeline complet ou des étapes spécifiques
    
    Args:
        config: Configuration
        title: Titre d'un article spécifique
        search: Terme de recherche
        random: Extraire des articles aléatoires
        count: Nombre d'articles
        source_lang: Langue source
        target_lang: Langue cible
        steps: Liste des étapes à exécuter ('extract', 'clean', 'segment', 'translate')
    
    Returns:
        Résultat de la dernière étape exécutée
    """
    # Étapes par défaut: tout le pipeline
    if not steps:
        steps = ['extract', 'clean', 'segment', 'translate']
    
    # Validation des langues
    source_lang = source_lang or config['extraction']['default_language']
    if not target_lang and 'translate' in steps:
        target_lang = config['languages']['target'][0]
        logger.info(f"Langue cible non spécifiée, utilisation de {target_lang}")
    
    result = []
    
    # Extraction
    if 'extract' in steps:
        logger.info("Étape 1: Extraction d'articles Wikipedia")
        result = run_extraction(config, title, search, random, count, source_lang)
        
        if not result:
            logger.error("Extraction échouée ou aucun article trouvé")
            return []
        
        logger.info(f"Extraction terminée: {len(result)} articles extraits")
    
    # Nettoyage
    if 'clean' in steps:
        logger.info("Étape 2: Nettoyage des articles")
        
        if 'extract' not in steps:
            # Si l'extraction n'a pas été exécutée, utiliser le répertoire des articles bruts
            input_path = config['paths']['articles_raw']
            if title:
                # Chercher un fichier spécifique
                filename = title.replace('/', '_').replace('\\', '_').replace(':', '_') + '.json'
                input_path = os.path.join(input_path, source_lang, filename)
                if not os.path.exists(input_path):
                    logger.error(f"Article non trouvé: {input_path}")
                    return []
        else:
            input_path = result[0] if len(result) == 1 else os.path.dirname(result[0])
        
        result = run_cleaning(config, input_path)
        
        if not result:
            logger.error("Nettoyage échoué ou aucun article nettoyé")
            return []
        
        logger.info(f"Nettoyage terminé: {len(result)} articles nettoyés")
    
    # Segmentation
    if 'segment' in steps:
        logger.info("Étape 3: Segmentation des articles")
        
        if 'clean' not in steps:
            # Si le nettoyage n'a pas été exécuté, utiliser le répertoire des articles nettoyés
            input_path = config['paths']['articles_cleaned']
            if title:
                # Chercher un fichier spécifique
                filename = title.replace('/', '_').replace('\\', '_').replace(':', '_') + '.json'
                input_path = os.path.join(input_path, filename)
                if not os.path.exists(input_path):
                    logger.error(f"Article nettoyé non trouvé: {input_path}")
                    return []
        else:
            input_path = result[0] if len(result) == 1 else os.path.dirname(result[0])
        
        result = run_segmentation(config, input_path)
        
        if not result:
            logger.error("Segmentation échouée ou aucun article segmenté")
            return []
        
        logger.info(f"Segmentation terminée: {len(result)} articles segmentés")
    
    # Traduction
    if 'translate' in steps:
        logger.info(f"Étape 4: Traduction des articles de {source_lang} vers {target_lang}")
        
        if 'segment' not in steps:
            # Si la segmentation n'a pas été exécutée, utiliser le répertoire des articles segmentés
            input_path = config['paths']['articles_segmented']
            if title:
                # Chercher un fichier spécifique
                filename = title.replace('/', '_').replace('\\', '_').replace(':', '_') + '.json'
                input_path = os.path.join(input_path, filename)
                if not os.path.exists(input_path):
                    logger.error(f"Article segmenté non trouvé: {input_path}")
                    return []
        else:
            input_path = result[0] if len(result) == 1 else os.path.dirname(result[0])
        
        result = run_translation(config, input_path, source_lang, target_lang)
        
        if not result:
            logger.error("Traduction échouée ou aucun article traduit")
            return []
        
        logger.info(f"Traduction terminée: {len(result)} articles traduits")
    
    return result

def main():
    parser = argparse.ArgumentParser(description="Pipeline de traduction d'articles Wikipedia")
    parser.add_argument('--config', type=str, default='config.yaml', 
                        help="Chemin vers le fichier de configuration")
    parser.add_argument('--title', type=str, 
                        help="Titre d'un article spécifique à traiter")
    parser.add_argument('--search', type=str, 
                        help="Terme de recherche pour trouver des articles")
    parser.add_argument('--random', action='store_true', 
                        help="Traiter des articles aléatoires")
    parser.add_argument('--count', type=int, default=5, 
                        help="Nombre d'articles à traiter")
    parser.add_argument('--source-lang', type=str, 
                        help="Langue source")
    parser.add_argument('--target-lang', type=str, 
                        help="Langue cible (fon, dindi, ewe, yor)")
    parser.add_argument('--steps', type=str, nargs='+', 
                        choices=['extract', 'clean', 'segment', 'translate'], 
                        help="Étapes spécifiques à exécuter")
    
    args = parser.parse_args()
    
    # Charger la configuration
    config = load_config(args.config)
    
    # Exécuter le pipeline
    run_pipeline(
        config=config,
        title=args.title,
        search=args.search,
        random=args.random,
        count=args.count,
        source_lang=args.source_lang,
        target_lang=args.target_lang,
        steps=args.steps
    )

if __name__ == "__main__":
    main()