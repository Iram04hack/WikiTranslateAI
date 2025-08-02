# src/extraction/get_wiki_articles.py

import os
import json
import argparse
import logging
from pathlib import Path
from .api_client import MediaWikiClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WikipediaExtractor:
    """Classe pour extraire des articles de Wikipedia"""

    def __init__(self, output_dir, language="en"):
        """
        Initialise l'extracteur

        Args:
            output_dir: Répertoire de sortie pour les articles extraits
            language: Code de langue Wikipedia (défaut: en)
        """
        self.output_dir = output_dir
        self.language = language
        self.client = MediaWikiClient().set_language(language)

        # Créer le répertoire de sortie s'il n'existe pas
        os.makedirs(os.path.join(output_dir, language), exist_ok=True)

    def extract_article_by_title(self, title, include_wikitext=True, include_html=True):
        """
        Extrait un article Wikipedia par son titre

        Args:
            title: Titre de l'article
            include_wikitext: Inclure le wikitext source
            include_html: Inclure le HTML

        Returns:
            Chemin du fichier sauvegardé
        """
        logger.info(f"Extraction de l'article: {title}")

        # Récupérer les contenus
        article_data = self.client.get_article_content(title=title)

        if not article_data:
            logger.error(f"Article non trouvé: {title}")
            return None

        # Extraire les métadonnées
        metadata = {
            'title': article_data.get('title', title),
            'pageid': article_data.get('pageid'),
            'language': self.language,
            'categories': [cat.get('*', cat.get('title', '')) for cat in article_data.get('categories', [])]
        }

        if 'sections' in article_data:
            metadata['sections'] = article_data.get('sections', [])

        # Récupérer le HTML
        html_content = None
        if include_html and 'text' in article_data:
            if isinstance(article_data['text'], dict) and '*' in article_data['text']:
                html_content = article_data['text']['*']
            elif isinstance(article_data['text'], str):
                html_content = article_data['text']

        # Récupérer le wikitext
        wikitext_content = None
        if include_wikitext:
            wikitext_content = self.client.get_article_wikitext(title=title)

        # Assembler l'article complet
        full_article = {
            'metadata': metadata,
            'html': html_content,
            'wikitext': wikitext_content
        }

        # Générer un nom de fichier sécurisé
        safe_title = title.replace('/', '_').replace('\\', '_').replace(':', '_')
        output_path = os.path.join(self.output_dir, self.language, f"{safe_title}.json")

        # Sauvegarder le contenu
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(full_article, f, ensure_ascii=False, indent=2)

        logger.info(f"Article sauvegardé: {output_path}")
        return output_path

    def extract_multiple_articles(self, titles, include_wikitext=True, include_html=True):
        """
        Extrait plusieurs articles par leurs titres

        Args:
            titles: Liste des titres d'articles
            include_wikitext: Inclure le wikitext source
            include_html: Inclure le HTML

        Returns:
            Liste des chemins de fichiers sauvegardés
        """
        saved_paths = []
        for title in titles:
            path = self.extract_article_by_title(title, include_wikitext, include_html)
            if path:
                saved_paths.append(path)

        return saved_paths

    def extract_random_articles(self, count=5, include_wikitext=True, include_html=True):
        """
        Extrait des articles aléatoires

        Args:
            count: Nombre d'articles à extraire
            include_wikitext: Inclure le wikitext source
            include_html: Inclure le HTML

        Returns:
            Liste des chemins de fichiers sauvegardés
        """
        random_articles = self.client.get_random_articles(count)
        titles = [article['title'] for article in random_articles]

        return self.extract_multiple_articles(titles, include_wikitext, include_html)

    def search_and_extract(self, query, limit=5, include_wikitext=True, include_html=True):
        """
        Recherche et extrait des articles correspondant à une requête

        Args:
            query: Terme de recherche
            limit: Nombre maximum d'articles à extraire
            include_wikitext: Inclure le wikitext source
            include_html: Inclure le HTML

        Returns:
            Liste des chemins de fichiers sauvegardés
        """
        search_results = self.client.search_articles(query, limit)
        titles = [result['title'] for result in search_results]

        return self.extract_multiple_articles(titles, include_wikitext, include_html)


def main():
    parser = argparse.ArgumentParser(description="Extraction d'articles Wikipedia")
    parser.add_argument('--output-dir', type=str, default='data/articles_raw',
                        help="Répertoire de sortie pour les articles extraits")
    parser.add_argument('--language', type=str, default='en',
                        help="Code de langue Wikipedia (ex: en, fr)")
    parser.add_argument('--title', type=str,
                        help="Titre d'un article spécifique à extraire")
    parser.add_argument('--search', type=str,
                        help="Terme de recherche pour trouver des articles")
    parser.add_argument('--random', action='store_true',
                        help="Extraire des articles aléatoires")
    parser.add_argument('--count', type=int, default=5,
                        help="Nombre d'articles aléatoires ou de résultats de recherche")
    parser.add_argument('--no-wikitext', action='store_true',
                        help="Ne pas inclure le wikitext source")
    parser.add_argument('--no-html', action='store_true',
                        help="Ne pas inclure le HTML")

    args = parser.parse_args()

    extractor = WikipediaExtractor(args.output_dir, args.language)

    include_wikitext = not args.no_wikitext
    include_html = not args.no_html

    if args.title:
        extractor.extract_article_by_title(args.title, include_wikitext, include_html)
    elif args.search:
        extractor.search_and_extract(args.search, args.count, include_wikitext, include_html)
    elif args.random:
        extractor.extract_random_articles(args.count, include_wikitext, include_html)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
