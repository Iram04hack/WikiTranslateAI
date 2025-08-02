# src/translation/translate.py

import os
import json
import argparse
import logging
from pathlib import Path
from .azure_client import AzureOpenAITranslator, create_translator_from_env
from ..reconstruction.rebuild_article import ArticleReconstructor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def translate_article(input_file, source_lang, target_lang, output_dir, 
                    api_key, api_version, azure_endpoint, model, 
                    glossary_db=None, use_glossary=True):
    """
    Traduit un article
    
    Args:
        input_file: Chemin vers le fichier d'article segmenté
        source_lang: Langue source
        target_lang: Langue cible
        output_dir: Répertoire de sortie
        api_key: Clé API Azure OpenAI
        api_version: Version de l'API
        azure_endpoint: Endpoint de l'API
        model: Modèle à utiliser
        glossary_db: Chemin vers la base de données du glossaire
        use_glossary: Utiliser le glossaire
    
    Returns:
        Chemin du fichier traduit ou None en cas d'erreur
    """
    translator = AzureOpenAITranslator(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=azure_endpoint,
        model=model,
        glossary_db_path=glossary_db
    )
    
    translated_article_path = translator.translate_article_file(
        input_file_path=input_file,
        source_language=source_lang,
        target_language=target_lang,
        output_dir=output_dir,
        use_glossary=use_glossary
    )
    
    if translated_article_path:
        # Reconstruction de l'article après traduction
        try:
            reconstructed_dir = os.path.join(output_dir, 'reconstructed')
            os.makedirs(reconstructed_dir, exist_ok=True)
            
            reconstructor = ArticleReconstructor(reconstructed_dir)
            
            with open(translated_article_path, 'r', encoding='utf-8') as f:
                translated_data = json.load(f)
            
            article_data = reconstructor.reconstruct_article(translated_data)
            output_paths = reconstructor.save_reconstructed_article(article_data, output_format='all')
            
            logger.info(f"Article reconstruit avec succès")
            
            # Retourner le chemin du fichier JSON reconstruit
            if output_paths and 'json' in output_paths:
                return output_paths['json']
            else:
                return translated_article_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la reconstruction de l'article: {e}")
            return translated_article_path
    
    return None

def translate_directory(input_dir, source_lang, target_lang, output_dir, 
                      api_key, api_version, azure_endpoint, model, 
                      glossary_db=None, use_glossary=True):
    """
    Traduit tous les articles dans un répertoire
    
    Args:
        input_dir: Répertoire contenant les articles segmentés
        source_lang: Langue source
        target_lang: Langue cible
        output_dir: Répertoire de sortie
        api_key: Clé API Azure OpenAI
        api_version: Version de l'API
        azure_endpoint: Endpoint de l'API
        model: Modèle à utiliser
        glossary_db: Chemin vers la base de données du glossaire
        use_glossary: Utiliser le glossaire
    
    Returns:
        Nombre d'articles traduits
    """
    translator = AzureOpenAITranslator(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=azure_endpoint,
        model=model,
        glossary_db_path=glossary_db
    )
    
    count = 0
    translated_paths = []
    
    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            input_path = os.path.join(input_dir, filename)
            translated_path = translator.translate_article_file(
                input_file_path=input_path,
                source_language=source_lang,
                target_language=target_lang,
                output_dir=output_dir,
                use_glossary=use_glossary
            )
            
            if translated_path:
                translated_paths.append(translated_path)
                count += 1
    
    logger.info(f"{count} articles traduits de {source_lang} vers {target_lang}")
    
    # Reconstruire tous les articles traduits
    if translated_paths:
        try:
            reconstructed_dir = os.path.join(output_dir, 'reconstructed')
            os.makedirs(reconstructed_dir, exist_ok=True)
            
            reconstructor = ArticleReconstructor(reconstructed_dir)
            
            for path in translated_paths:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        translated_data = json.load(f)
                    
                    article_data = reconstructor.reconstruct_article(translated_data)
                    reconstructor.save_reconstructed_article(article_data, output_format='all')
                except Exception as e:
                    logger.error(f"Erreur lors de la reconstruction de l'article {path}: {e}")
            
            logger.info(f"{len(translated_paths)} articles reconstruits avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de la reconstruction des articles: {e}")
    
    return count


def main():
    parser = argparse.ArgumentParser(description="Traduction d'articles Wikipedia")
    parser.add_argument('--input', type=str, required=True, 
                        help="Fichier article ou répertoire d'articles à traduire")
    parser.add_argument('--output-dir', type=str, default='data/articles_translated', 
                        help="Répertoire de sortie pour les articles traduits")
    parser.add_argument('--source-lang', type=str, default='en', 
                        help="Langue source")
    parser.add_argument('--target-lang', type=str, required=True, 
                        help="Langue cible (fon, dindi, ewe, yor)")
    parser.add_argument('--api-key', type=str, 
                        help="Clé API Azure OpenAI")
    parser.add_argument('--api-version', type=str, default='2024-05-01-preview', 
                        help="Version de l'API Azure OpenAI")
    parser.add_argument('--azure-endpoint', type=str, 
                        help="Endpoint de l'API Azure OpenAI")
    parser.add_argument('--model', type=str, default='gpt-4o-pionners07', 
                        help="Modèle OpenAI à utiliser")
    parser.add_argument('--glossary-db', type=str, 
                        help="Chemin vers la base de données du glossaire")
    parser.add_argument('--no-glossary', action='store_true', 
                        help="Ne pas utiliser le glossaire")
    parser.add_argument('--no-reconstruction', action='store_true',
                        help="Ne pas reconstruire les articles après traduction")
    
    args = parser.parse_args()
    
    # Utiliser les variables d'environnement si les paramètres ne sont pas fournis
    api_key = args.api_key or os.environ.get('AZURE_OPENAI_API_KEY')
    api_version = args.api_version or os.environ.get('AZURE_OPENAI_API_VERSION', '2024-05-01-preview')
    azure_endpoint = args.azure_endpoint or os.environ.get('AZURE_OPENAI_ENDPOINT')
    model = args.model or os.environ.get('AZURE_OPENAI_MODEL', 'gpt-4o-pionners07')
    
    if not all([api_key, azure_endpoint]):
        parser.error("Les paramètres --api-key et --azure-endpoint sont requis, ou les variables d'environnement AZURE_OPENAI_API_KEY et AZURE_OPENAI_ENDPOINT doivent être définies.")
    
    if os.path.isdir(args.input):
        translate_directory(
            input_dir=args.input,
            source_lang=args.source_lang,
            target_lang=args.target_lang,
            output_dir=args.output_dir,
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=azure_endpoint,
            model=model,
            glossary_db=args.glossary_db,
            use_glossary=not args.no_glossary
        )
    elif os.path.isfile(args.input):
        translate_article(
            input_file=args.input,
            source_lang=args.source_lang,
            target_lang=args.target_lang,
            output_dir=args.output_dir,
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=azure_endpoint,
            model=model,
            glossary_db=args.glossary_db,
            use_glossary=not args.no_glossary
        )
    else:
        parser.error(f"Le chemin d'entrée n'existe pas: {args.input}")

if __name__ == "__main__":
    main()