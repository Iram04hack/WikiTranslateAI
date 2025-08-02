#!/usr/bin/env python3
# scripts/batch_processor.py

import os
import sys
import json
import time
import logging
import argparse
import concurrent.futures
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire parent au chemin de recherche
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.config import load_config
from src.extraction.get_wiki_articles import WikipediaExtractor
from src.extraction.api_client import MediaWikiClient
from src.extraction.clean_text import WikiTextCleaner
from src.extraction.segmentation import TextSegmenter
from src.translation.translate import translate_article
from src.utils.translation_tracker import get_tracker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BatchProcessor:
    """Traitement par lots d'articles Wikipedia"""
    
    def __init__(self, config, source_lang, target_lang, workers=1):
        """
        Initialise le processeur par lots
        
        Args:
            config: Configuration du projet
            source_lang: Langue source
            target_lang: Langue cible
            workers: Nombre de workers pour le traitement parallèle
        """
        self.config = config
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.workers = workers
        self.tracker = get_tracker()
        
        # Créer les répertoires de données s'ils n'existent pas
        for path in config['paths'].values():
            if isinstance(path, str) and not path.endswith('.db'):
                os.makedirs(path, exist_ok=True)
        
        # Créer aussi le répertoire de logs
        os.makedirs("logs", exist_ok=True)
        
        # Répertoire de checkpoints
        self.checkpoint_dir = os.path.join(config['paths'].get('data_dir', 'data'), 'checkpoints')
        os.makedirs(self.checkpoint_dir, exist_ok=True)
    
    def save_checkpoint(self, job_info):
        """
        Sauvegarde un point de contrôle pour une tâche
        
        Args:
            job_info: Informations sur la tâche en cours
        """
        checkpoint_file = os.path.join(
            self.checkpoint_dir,
            f"checkpoint_{self.source_lang}_{self.target_lang}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(job_info, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Checkpoint sauvegardé dans {checkpoint_file}")
        
        return checkpoint_file
    
    def load_checkpoint(self, checkpoint_file):
        """
        Charge un point de contrôle
        
        Args:
            checkpoint_file: Chemin vers le fichier de point de contrôle
        
        Returns:
            Informations sur la tâche
        """
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                job_info = json.load(f)
            
            logger.info(f"Checkpoint chargé depuis {checkpoint_file}")
            return job_info
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement du checkpoint {checkpoint_file}: {e}")
            return None
    
    def process_article(self, article_title):
        """
        Traite un article complet (extraction, nettoyage, segmentation, traduction)
        
        Args:
            article_title: Titre de l'article
        
        Returns:
            True en cas de succès, False sinon
        """
        try:
            logger.info(f"Traitement de l'article '{article_title}'")
            
            # 1. Extraction
            extractor = WikipediaExtractor(
                self.config['paths']['articles_raw'],
                self.source_lang
            )
            
            extracted_path = extractor.extract_article_by_title(
                article_title,
                self.config['extraction']['include_wikitext'],
                self.config['extraction']['include_html']
            )
            
            if not extracted_path:
                logger.error(f"Échec de l'extraction pour l'article '{article_title}'")
                return False
            
            # 2. Nettoyage
            cleaner = WikiTextCleaner(self.config['paths']['articles_cleaned'])
            cleaned_article = cleaner.clean_article_file(extracted_path)
            
            if not cleaned_article:
                logger.error(f"Échec du nettoyage pour l'article '{article_title}'")
                return False
            
            cleaned_path = os.path.join(
                self.config['paths']['articles_cleaned'],
                os.path.basename(extracted_path)
            )
            
            # 3. Segmentation
            segmenter = TextSegmenter(
                self.config['paths']['articles_segmented'],
                self.config['segmentation']['max_segment_length'],
                self.config['segmentation']['min_segment_length']
            )
            
            segmented_path = segmenter.segment_article_file(cleaned_path)
            
            if not segmented_path:
                logger.error(f"Échec de la segmentation pour l'article '{article_title}'")
                return False
            
            # 4. Traduction
            translated_path = translate_article(
                input_file=segmented_path,
                source_lang=self.source_lang,
                target_lang=self.target_lang,
                output_dir=self.config['paths']['articles_translated'],
                api_key=self.config['translation']['api_key'],
                api_version=self.config['translation']['api_version'],
                azure_endpoint=self.config['translation']['azure_endpoint'],
                model=self.config['translation']['model'],
                glossary_db=self.config['paths'].get('glossary_db'),
                use_glossary=self.config['translation']['use_glossary']
            )
            
            if not translated_path:
                logger.error(f"Échec de la traduction pour l'article '{article_title}'")
                return False
            
            logger.info(f"Article '{article_title}' traité avec succès")
            
            # 5. Enregistrer dans le tracker
            metadata = {}
            try:
                with open(cleaned_path, 'r', encoding='utf-8') as f:
                    article_data = json.load(f)
                    metadata = article_data.get('metadata', {})
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des métadonnées: {e}")
            
            # Enregistrer la traduction dans le tracker
            self.tracker.record_translation(
                article_title,
                self.source_lang,
                self.target_lang,
                metadata.get('categories', [])
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'article '{article_title}': {e}")
            return False
    
    def process_articles_category(self, category, count=10):
        """
        Traite des articles d'une catégorie spécifique
        
        Args:
            category: Nom de la catégorie
            count: Nombre d'articles à traiter
        
        Returns:
            Nombre d'articles traités avec succès
        """
        logger.info(f"Traitement de {count} articles de la catégorie '{category}'")
        
        # Obtenir les articles de la catégorie via l'API MediaWiki
        client = MediaWikiClient().set_language(self.source_lang)
        
        params = {
            'action': 'query',
            'list': 'categorymembers',
            'cmtitle': f"Category:{category}",
            'cmlimit': count,
            'cmtype': 'page',
            'cmsort': 'timestamp',
            'cmdir': 'desc'
        }
        
        try:
            data = client._make_request(params)
            
            if 'query' in data and 'categorymembers' in data['query']:
                articles = [item['title'] for item in data['query']['categorymembers']]
                
                logger.info(f"Trouvé {len(articles)} articles dans la catégorie '{category}'")
                
                # Créer un checkpoint initial
                job_info = {
                    'type': 'category',
                    'category': category,
                    'source_lang': self.source_lang,
                    'target_lang': self.target_lang,
                    'articles': articles,
                    'processed': [],
                    'failed': [],
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                self.save_checkpoint(job_info)
                
                # Traiter les articles
                return self._process_article_list(articles, job_info)
            
            else:
                logger.error(f"Aucun article trouvé dans la catégorie '{category}'")
                return 0
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des articles de la catégorie '{category}': {e}")
            return 0
    
    def process_popular_articles(self, count=10):
        """
        Traite les articles les plus populaires
        
        Args:
            count: Nombre d'articles à traiter
        
        Returns:
            Nombre d'articles traités avec succès
        """
        logger.info(f"Traitement des {count} articles les plus populaires")
        
        try:
            # Obtenir les articles les plus consultés via l'API MediaWiki
            client = MediaWikiClient().set_language(self.source_lang)
            
            params = {
                'action': 'query',
                'list': 'mostviewed',
                'pvimlimit': count
            }
            
            data = client._make_request(params)
            
            if 'query' in data and 'mostviewed' in data['query']:
                articles = [item['title'] for item in data['query']['mostviewed']]
                
                logger.info(f"Trouvé {len(articles)} articles populaires")
                
                # Créer un checkpoint initial
                job_info = {
                    'type': 'popular',
                    'source_lang': self.source_lang,
                    'target_lang': self.target_lang,
                    'articles': articles,
                    'processed': [],
                    'failed': [],
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                self.save_checkpoint(job_info)
                
                # Traiter les articles
                return self._process_article_list(articles, job_info)
            
            else:
                logger.error("Aucun article populaire trouvé")
                return 0
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des articles populaires: {e}")
            return 0
    
    def process_random_articles(self, count=10):
        """
        Traite des articles aléatoires
        
        Args:
            count: Nombre d'articles à traiter
        
        Returns:
            Nombre d'articles traités avec succès
        """
        logger.info(f"Traitement de {count} articles aléatoires")
        
        try:
            # Obtenir des articles aléatoires via l'API MediaWiki
            client = MediaWikiClient().set_language(self.source_lang)
            random_articles = client.get_random_articles(count)
            
            articles = [article['title'] for article in random_articles]
            
            logger.info(f"Trouvé {len(articles)} articles aléatoires")
            
            # Créer un checkpoint initial
            job_info = {
                'type': 'random',
                'source_lang': self.source_lang,
                'target_lang': self.target_lang,
                'articles': articles,
                'processed': [],
                'failed': [],
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.save_checkpoint(job_info)
            
            # Traiter les articles
            return self._process_article_list(articles, job_info)
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des articles aléatoires: {e}")
            return 0
    
    def process_from_list(self, file_path):
        """
        Traite des articles à partir d'une liste dans un fichier
        
        Args:
            file_path: Chemin vers le fichier contenant la liste d'articles
        
        Returns:
            Nombre d'articles traités avec succès
        """
        logger.info(f"Traitement des articles du fichier {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                articles = [line.strip() for line in f if line.strip()]
            
            logger.info(f"Trouvé {len(articles)} articles dans le fichier")
            
            # Créer un checkpoint initial
            job_info = {
                'type': 'list',
                'source_lang': self.source_lang,
                'target_lang': self.target_lang,
                'articles': articles,
                'processed': [],
                'failed': [],
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.save_checkpoint(job_info)
            
            # Traiter les articles
            return self._process_article_list(articles, job_info)
        
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du fichier {file_path}: {e}")
            return 0
    
    def resume_from_checkpoint(self, checkpoint_file):
        """
        Reprend le traitement à partir d'un point de contrôle
        
        Args:
            checkpoint_file: Chemin vers le fichier de point de contrôle
        
        Returns:
            Nombre d'articles traités avec succès
        """
        logger.info(f"Reprise du traitement depuis le checkpoint {checkpoint_file}")
        
        # Charger les informations du checkpoint
        job_info = self.load_checkpoint(checkpoint_file)
        
        if not job_info:
            logger.error(f"Impossible de charger le checkpoint {checkpoint_file}")
            return 0
        
        # Mettre à jour les langues
        self.source_lang = job_info.get('source_lang', self.source_lang)
        self.target_lang = job_info.get('target_lang', self.target_lang)
        
        # Articles restants à traiter
        remaining_articles = [a for a in job_info.get('articles', []) 
                             if a not in job_info.get('processed', []) 
                             and a not in job_info.get('failed', [])]
        
        logger.info(f"Reprise du traitement: {len(remaining_articles)} articles restants")
        
        # Mettre à jour le job_info
        job_info['articles'] = remaining_articles
        
        # Traiter les articles restants
        return self._process_article_list(remaining_articles, job_info)
    
    def _process_article_list(self, articles, job_info):
        """
        Traite une liste d'articles avec suivi de progression
        
        Args:
            articles: Liste des titres d'articles à traiter
            job_info: Informations sur la tâche
        
        Returns:
            Nombre d'articles traités avec succès
        """
        successful = 0
        
        if self.workers > 1:
            # Traitement parallèle
            logger.info(f"Traitement parallèle avec {self.workers} workers")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
                future_to_article = {executor.submit(self.process_article, article): article for article in articles}
                
                for i, future in enumerate(concurrent.futures.as_completed(future_to_article)):
                    article = future_to_article[future]
                    try:
                        result = future.result()
                        
                        if result:
                            successful += 1
                            job_info['processed'].append(article)
                        else:
                            job_info['failed'].append(article)
                        
                        # Sauvegarder le checkpoint tous les 5 articles
                        if (i + 1) % 5 == 0 or (i + 1) == len(articles):
                            self.save_checkpoint(job_info)
                            
                            logger.info(f"Progression: {i+1}/{len(articles)} articles traités")
                            logger.info(f"Succès: {successful}, Échecs: {len(job_info['failed'])}")
                    
                    except Exception as e:
                        logger.error(f"Erreur lors du traitement de l'article '{article}': {e}")
                        job_info['failed'].append(article)
        
        else:
            # Traitement séquentiel
            logger.info("Traitement séquentiel")
            
            for i, article in enumerate(articles):
                result = self.process_article(article)
                
                if result:
                    successful += 1
                    job_info['processed'].append(article)
                else:
                    job_info['failed'].append(article)
                
                # Sauvegarder le checkpoint tous les 5 articles
                if (i + 1) % 5 == 0 or (i + 1) == len(articles):
                    self.save_checkpoint(job_info)
                    
                    logger.info(f"Progression: {i+1}/{len(articles)} articles traités")
                    logger.info(f"Succès: {successful}, Échecs: {len(job_info['failed'])}")
        
        # Sauvegarde finale du checkpoint
        job_info['completed'] = True
        job_info['completion_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save_checkpoint(job_info)
        
        logger.info(f"Traitement terminé: {successful}/{len(articles)} articles traités avec succès")
        return successful

def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(description="Traitement par lots d'articles Wikipedia")
    parser.add_argument('--config', type=str, default='config.yaml', help="Chemin vers le fichier de configuration")
    parser.add_argument('--source-lang', type=str, help="Langue source")
    parser.add_argument('--target-lang', type=str, help="Langue cible")
    parser.add_argument('--count', type=int, default=10, help="Nombre d'articles à traiter")
    parser.add_argument('--category', type=str, help="Catégorie d'articles à traiter")
    parser.add_argument('--popular', action='store_true', help="Traiter les articles les plus populaires")
    parser.add_argument('--random', action='store_true', help="Traiter des articles aléatoires")
    parser.add_argument('--untranslated', action='store_true', help="Traiter les articles non traduits")
    parser.add_argument('--list-file', type=str, help="Fichier contenant une liste d'articles")
    parser.add_argument('--resume', type=str, help="Reprendre le traitement depuis un checkpoint")
    parser.add_argument('--parallel', action='store_true', help="Activer le traitement parallèle")
    parser.add_argument('--workers', type=int, default=4, help="Nombre de workers pour le traitement parallèle")
    
    args = parser.parse_args()
    
    # Charger la configuration
    config = load_config(args.config)
    
    # Déterminer les langues
    source_lang = args.source_lang or config['extraction']['default_language']
    
    if not args.target_lang and not args.resume:
        if config['languages']['target']:
            target_lang = config['languages']['target'][0]
        else:
            logger.error("Langue cible requise mais non spécifiée")
            return 1
    else:
        target_lang = args.target_lang
    
    # Créer le processeur par lots
    workers = args.workers if args.parallel else 1
    processor = BatchProcessor(config, source_lang, target_lang, workers)
    
    # Exécuter le traitement approprié
    start_time = time.time()
    count = args.count
    articles_processed = 0
    
    if args.resume:
        # Reprendre depuis un checkpoint
        articles_processed = processor.resume_from_checkpoint(args.resume)
    
    elif args.category:
        # Traiter une catégorie
        articles_processed = processor.process_articles_category(args.category, count)
    
    elif args.popular:
        # Traiter les articles populaires
        articles_processed = processor.process_popular_articles(count)
    
    elif args.untranslated:
        # Traiter les articles non traduits
        logger.error("Fonctionnalité non implémentée: traitement des articles non traduits")
        return 1
    
    elif args.list_file:
        # Traiter depuis une liste
        articles_processed = processor.process_from_list(args.list_file)
    
    elif args.random:
        # Traiter des articles aléatoires
        articles_processed = processor.process_random_articles(count)
    
    else:
        logger.error("Aucun mode de traitement spécifié")
        parser.print_help()
        return 1
    
    # Afficher les statistiques
    elapsed_time = time.time() - start_time
    logger.info(f"Traitement terminé en {elapsed_time:.1f} secondes")
    logger.info(f"Articles traités avec succès: {articles_processed}")
    
    if articles_processed > 0:
        logger.info(f"Temps moyen par article: {elapsed_time / articles_processed:.1f} secondes")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.error("Opération interrompue par l'utilisateur")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Erreur non gérée: {e}")
        sys.exit(1)