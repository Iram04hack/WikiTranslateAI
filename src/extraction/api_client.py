import requests
import time
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)

class MediaWikiClient:
    """Client pour interagir avec l'API MediaWiki de Wikipedia"""
    
    def __init__(self, base_url="https://en.wikipedia.org/w/api.php", user_agent="WikiTranslateAI/1.0"):
        """
        Initialise le client MediaWiki
        
        Args:
            base_url: URL de base de l'API MediaWiki (par défaut: Wikipedia en anglais)
            user_agent: Identifiant pour les requêtes (important pour respecter les règles d'usage)
        """
        self.base_url = base_url
        self.headers = {
            'User-Agent': user_agent
        }
        self.session = requests.Session()
        self.rate_limit_delay = 1  # Délai en secondes entre les requêtes pour respecter les limites
    
    def set_language(self, language_code):
        """
        Change la langue de Wikipedia à utiliser
        
        Args:
            language_code: Code de langue (fr, en, etc.)
        """
        self.base_url = f"https://{language_code}.wikipedia.org/w/api.php"
        return self
    
    def _make_request(self, params):
        """
        Effectue une requête à l'API avec gestion des erreurs et limites de taux
        
        Args:
            params: Paramètres de la requête
        
        Returns:
            Données de réponse JSON
        """
        # Paramètres de base pour toutes les requêtes
        base_params = {
            'format': 'json',
            'formatversion': '2'
        }
        
        # Fusionner avec les paramètres spécifiques
        params.update(base_params)
        
        # Respecter les limites de taux
        time.sleep(self.rate_limit_delay)
        
        try:
            response = self.session.get(self.base_url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erreur HTTP lors de la requête: {e}")
            if response.status_code == 429:  # Too Many Requests
                retry_after = int(response.headers.get('Retry-After', 5))
                logger.warning(f"Limite de taux atteinte, attente de {retry_after} secondes")
                time.sleep(retry_after)
                return self._make_request(params)  # Réessayer après l'attente
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la requête: {e}")
            raise
        except ValueError as e:
            logger.error(f"Erreur lors du décodage JSON: {e}")
            raise
    
    def search_articles(self, query, limit=10):
        """
        Recherche des articles dans Wikipedia
        
        Args:
            query: Terme de recherche
            limit: Nombre maximum de résultats (défaut: 10)
        
        Returns:
            Liste des articles correspondants (titre, pageid, snippet)
        """
        params = {
            'action': 'query',
            'list': 'search',
            'srsearch': query,
            'srlimit': limit,
            'srinfo': 'totalhits',
            'srprop': 'snippet|titlesnippet'
        }
        
        data = self._make_request(params)
        
        if 'query' in data and 'search' in data['query']:
            return data['query']['search']
        return []
    
    def get_article_content(self, title=None, pageid=None):
        """
        Récupère le contenu d'un article par son titre ou ID
        
        Args:
            title: Titre de l'article (optionnel si pageid est fourni)
            pageid: ID de la page (optionnel si title est fourni)
        
        Returns:
            Contenu de l'article avec métadonnées
        """
        if not title and not pageid:
            raise ValueError("Titre ou ID de page requis")
        
        params = {
            'action': 'parse',
            'prop': 'text|sections|displaytitle|categories|templates|images|externallinks',
            'redirects': '1'
        }
        
        if title:
            params['page'] = title
        else:
            params['pageid'] = pageid
        
        data = self._make_request(params)
        
        if 'parse' in data:
            return data['parse']
        
        logger.warning(f"Article non trouvé: {title or pageid}")
        return None
    
    def get_article_html(self, title=None, pageid=None):
        """
        Récupère le contenu HTML complet d'un article
        
        Args:
            title: Titre de l'article (optionnel si pageid est fourni)
            pageid: ID de la page (optionnel si title est fourni)
        
        Returns:
            Contenu HTML de l'article
        """
        content = self.get_article_content(title, pageid)
        
        if content and 'text' in content:
            if isinstance(content['text'], dict) and '*' in content['text']:
                return content['text']['*']
            elif isinstance(content['text'], str):
                return content['text']
        return None
    
    def get_article_wikitext(self, title=None, pageid=None):
        """
        Récupère le wikitext (source) d'un article
        
        Args:
            title: Titre de l'article (optionnel si pageid est fourni)
            pageid: ID de la page (optionnel si title est fourni)
        
        Returns:
            Wikitext de l'article
        """
        if not title and not pageid:
            raise ValueError("Titre ou ID de page requis")
        
        params = {
            'action': 'query',
            'prop': 'revisions',
            'rvprop': 'content',
            'rvslots': 'main'
        }
        
        if title:
            params['titles'] = title
        else:
            params['pageids'] = pageid
        
        data = self._make_request(params)
        
        if 'query' in data and 'pages' in data['query']:
            pages = data['query']['pages']
            
            # Traiter la structure de pages quelle que soit sa forme (liste ou dictionnaire)
            if isinstance(pages, dict):
                for page_id, page_data in pages.items():
                    if 'revisions' in page_data and len(page_data['revisions']) > 0:
                        revision = page_data['revisions'][0]
                        if 'slots' in revision and 'main' in revision['slots']:
                            return revision['slots']['main']['content']
            elif isinstance(pages, list):
                for page_data in pages:
                    if 'revisions' in page_data and len(page_data['revisions']) > 0:
                        revision = page_data['revisions'][0]
                        if 'slots' in revision and 'main' in revision['slots']:
                            return revision['slots']['main']['content']
                    # Format alternatif possible
                    if 'revisions' in page_data and page_data['revisions']:
                        if '*' in page_data['revisions'][0]:
                            return page_data['revisions'][0]['*']
        
        logger.warning(f"Wikitext non trouvé pour: {title or pageid}")
        # Méthode alternative d'extraction si la première méthode a échoué
        try:
            if title:
                # Requête directe vers action=raw
                raw_url = self.base_url.replace('w/api.php', 'wiki/' + quote(title)) + '?action=raw'
                response = self.session.get(raw_url, headers=self.headers)
                if response.status_code == 200:
                    return response.text
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction alternative du wikitext: {e}")
        
        return None
    
    def get_random_articles(self, count=1):
        """
        Récupère des articles aléatoires
        
        Args:
            count: Nombre d'articles à récupérer
        
        Returns:
            Liste d'articles aléatoires
        """
        params = {
            'action': 'query',
            'list': 'random',
            'rnlimit': count,
            'rnnamespace': 0  # Namespace principal (articles)
        }
        
        data = self._make_request(params)
        
        if 'query' in data and 'random' in data['query']:
            return data['query']['random']
        return []
