# src/database/wiktionary_extractor.py

import re
import requests
import logging
import time
from bs4 import BeautifulSoup
from src.database.glossary_manager import GlossaryManager

logger = logging.getLogger(__name__)

class WiktionaryExtractor:
    """Extraction de termes et traductions depuis Wiktionary"""
    
    def __init__(self, db_path, user_agent="WikiTranslateAI/1.0"):
        """Initialise l'extracteur Wiktionary"""
        self.db_path = db_path
        self.headers = {'User-Agent': user_agent}
        self.rate_limit_delay = 1  # Délai entre les requêtes
    
    def extract_translations(self, source_lang, target_lang, word_list=None, max_words=100):
        """
        Extrait les traductions de mots depuis Wiktionary
        
        Args:
            source_lang: Code de la langue source (en, fr)
            target_lang: Code de la langue cible (fon, ewe, etc.)
            word_list: Liste de mots à extraire (facultatif)
            max_words: Nombre maximum de mots à extraire si word_list non fournie
            
        Returns:
            Nombre de traductions extraites
        """
        if not word_list:
            # Si aucune liste fournie, extraire les mots les plus fréquents
            word_list = self._get_frequent_words(source_lang, max_words)
        
        extracted_count = 0
        
        with GlossaryManager(self.db_path) as gm:
            for word in word_list:
                try:
                    # Vérifier si le terme existe déjà dans le glossaire
                    existing = gm.search_term(word, source_lang, target_lang)
                    if existing:
                        logger.info(f"Le terme '{word}' existe déjà dans le glossaire")
                        continue
                    
                    # Extraire la traduction depuis Wiktionary
                    translation = self._get_wiktionary_translation(word, source_lang, target_lang)
                    
                    if translation:
                        # Ajouter au glossaire
                        gm.add_term(
                            source_term=word,
                            source_lang=source_lang,
                            target_term=translation,
                            target_lang=target_lang,
                            domain='general',
                            confidence=0.7,  # Confiance moyenne pour Wiktionary
                            validated=False  # Nécessite validation
                        )
                        extracted_count += 1
                        logger.info(f"Ajouté: {word} → {translation}")
                    
                    # Respecter la limite de taux
                    time.sleep(self.rate_limit_delay)
                    
                except Exception as e:
                    logger.error(f"Erreur lors de l'extraction de '{word}': {e}")
                    continue
        
        return extracted_count
    
    def _get_frequent_words(self, lang, count=100):
        """
        Récupère une liste de mots fréquents dans la langue
        
        Args:
            lang: Code de la langue
            count: Nombre de mots à récupérer
            
        Returns:
            Liste de mots fréquents
        """
        # URL des listes de fréquence (exemple)
        frequency_urls = {
            'en': "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2016/en/en_50k.txt",
            'fr': "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2016/fr/fr_50k.txt"
        }
        
        if lang not in frequency_urls:
            logger.warning(f"Pas de liste de fréquence disponible pour {lang}")
            return []
        
        try:
            response = requests.get(frequency_urls[lang])
            response.raise_for_status()
            
            # Format: mot fréquence
            words = []
            for line in response.text.splitlines():
                if line.strip():
                    parts = line.strip().split(' ')
                    if len(parts) >= 1:
                        words.append(parts[0])
                
                if len(words) >= count:
                    break
            
            return words
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des mots fréquents: {e}")
            return []
    
    def _get_wiktionary_translation(self, word, source_lang, target_lang):
        """
        Extrait la traduction d'un mot depuis Wiktionary
        
        Args:
            word: Mot à traduire
            source_lang: Code de la langue source
            target_lang: Code de la langue cible
            
        Returns:
            Traduction ou None si non trouvée
        """
        # Construire l'URL Wiktionary
        lang_codes = {
            'en': 'en', 'fr': 'fr', 
            'fon': 'fon', 'ewe': 'ee', 
            'dindi': 'ddn', 'yor': 'yo'
        }
        
        # Adapter les codes de langue pour Wiktionary
        target_code = lang_codes.get(target_lang, target_lang)
        
        # Utiliser l'édition Wiktionary dans la langue source
        wiktionary_url = f"https://{source_lang}.wiktionary.org/wiki/{word}"
        
        try:
            response = requests.get(wiktionary_url, headers=self.headers)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Chercher la section de traductions
            translation_sections = soup.find_all('div', class_='translations')
            
            for section in translation_sections:
                # Chercher le bloc de la langue cible
                target_blocks = section.find_all('li', class_='interwiki')
                
                for block in target_blocks:
                    if target_code in block.text or target_lang in block.text:
                        # Extraire la traduction
                        translation_match = re.search(r'\(([^)]+)\)', block.text)
                        if translation_match:
                            return translation_match.group(1).strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction depuis Wiktionary: {e}")
            return None