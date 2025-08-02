# src/corpus/custom_corpus.py

import os
import csv
import json
import logging
import requests
import zipfile
import io
from pathlib import Path
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class CustomCorpusManager:
    """Gestion de corpus personnalisés pour les langues africaines"""
    
    def __init__(self, corpus_dir):
        """Initialise le gestionnaire de corpus personnalisés"""
        self.corpus_dir = corpus_dir
        
        # Créer les répertoires pour les corpus personnalisés
        for target_lang in ["fon", "dindi", "ewe", "yor"]:
            for source_lang in ["fr", "en"]:
                custom_dir = os.path.join(corpus_dir, f"custom_{source_lang}_{target_lang}")
                Path(custom_dir).mkdir(parents=True, exist_ok=True)
    
    def download_language_specific_resources(self, target_lang):
        """
        Télécharge et intègre des ressources spécifiques à une langue africaine
        
        Args:
            target_lang: Code de la langue cible
            
        Returns:
            Liste des ressources téléchargées
        """
        downloaded_resources = []
        
        # Ressources spécifiques par langue
        resources_by_language = {
            "yor": self._get_yoruba_resources(),
            "yo": self._get_yoruba_resources(),
            "ewe": self._get_ewe_resources(),
            "ee": self._get_ewe_resources(),
            "fon": self._get_fon_resources(),
            "dindi": self._get_dindi_resources(),
            "ddn": self._get_dindi_resources()
        }
        
        # Vérifier si nous avons des ressources pour cette langue
        if target_lang not in resources_by_language:
            logger.warning(f"Pas de ressources spécifiques connues pour {target_lang}")
            return downloaded_resources
        
        # Récupérer les ressources pour cette langue
        resources = resources_by_language[target_lang]
        
        # Télécharger chaque ressource
        for resource in resources:
            try:
                logger.info(f"Téléchargement de la ressource: {resource['name']}")
                
                if resource['type'] == 'github':
                    # Télécharger depuis GitHub
                    result = self._download_github_resource(resource, target_lang)
                    if result:
                        downloaded_resources.append(result)
                
                elif resource['type'] == 'web':
                    # Télécharger depuis une URL web
                    result = self._download_web_resource(resource, target_lang)
                    if result:
                        downloaded_resources.append(result)
                
                elif resource['type'] == 'opus':
                    # Télécharger depuis OPUS
                    result = self._download_opus_resource(resource, target_lang)
                    if result:
                        downloaded_resources.append(result)
                
                elif resource['type'] == 'local':
                    # Ressource intégrée localement
                    result = self._create_local_resource(resource, target_lang)
                    if result:
                        downloaded_resources.append(result)
            
            except Exception as e:
                logger.error(f"Erreur lors du téléchargement de la ressource {resource['name']}: {e}")
        
        # Rechercher automatiquement les corpus OPUS disponibles
        try:
            available_corpora = self.search_available_opus_corpora(target_lang)
            if available_corpora:
                logger.info(f"Corpus OPUS disponibles trouvés automatiquement: {len(available_corpora)}")
                for corpus_info in available_corpora:
                    try:
                        from src.corpus.corpus_extractor import CorpusExtractor
                        extractor = CorpusExtractor(self.corpus_dir)
                        
                        corpus_path = extractor.download_opus_corpus(
                            corpus_info['source_lang'], 
                            corpus_info['target_lang'], 
                            corpus_info['corpus']
                        )
                        
                        if corpus_path:
                            filtered_path = extractor.filter_corpus_by_quality(corpus_path)
                            if filtered_path:
                                logger.info(f"Corpus OPUS automatique téléchargé: {filtered_path}")
                                downloaded_resources.append({
                                    "name": f"auto_{corpus_info['corpus']}_{corpus_info['source_lang']}",
                                    "path": filtered_path,
                                    "source_lang": corpus_info['source_lang'],
                                    "target_lang": corpus_info['target_lang']
                                })
                    except Exception as e:
                        logger.error(f"Erreur avec corpus automatique {corpus_info['corpus']}: {e}")
        except Exception as e:
            logger.error(f"Erreur lors de la recherche automatique de corpus: {e}")
        
        return downloaded_resources
    
    def _get_yoruba_resources(self):
        """Renvoie la liste des ressources spécifiques au yoruba"""
        return [
            {
                "name": "masakhane_mt",
                "type": "github",
                "url": "https://raw.githubusercontent.com/masakhane-io/masakhane-mt/master/language_pairs/en_yo/data/test.yo",
                "source_lang": "en",
                "format": "parallel"
            },
            {
                "name": "nllb_flores",
                "type": "github",
                "url": "https://raw.githubusercontent.com/facebookresearch/flores/main/flores200/devtest/yor_Latn.devtest",
                "source_lang": "en",
                "format": "parallel"
            },
            {
                "name": "lorelei_corpus",
                "type": "web",
                "url": "https://catalog.ldc.upenn.edu/LDC2021T07",
                "source_lang": "en",
                "format": "dictionary"
            },
            {
                "name": "jw300_yo",
                "type": "opus",
                "corpus": "JW300",
                "source_langs": ["en", "fr"],
                "format": "parallel"
            },
            {
                "name": "bible_yo",
                "type": "opus",
                "corpus": "Bible",
                "source_langs": ["en", "fr"],
                "format": "parallel"
            },
            {
                "name": "basic_yoruba_vocabulary",
                "type": "local",
                "data": [
                    {"en": "hello", "fr": "bonjour", "yor": "báwo ni"},
                    {"en": "goodbye", "fr": "au revoir", "yor": "ó dàbọ̀"},
                    {"en": "please", "fr": "s'il vous plaît", "yor": "jọ̀wọ́"},
                    {"en": "thank you", "fr": "merci", "yor": "e se"},
                    {"en": "yes", "fr": "oui", "yor": "bẹ́ẹ̀ni"},
                    {"en": "no", "fr": "non", "yor": "bẹ́ẹ̀kọ́"},
                    {"en": "water", "fr": "eau", "yor": "omi"},
                    {"en": "food", "fr": "nourriture", "yor": "oúnjẹ"},
                    {"en": "money", "fr": "argent", "yor": "owó"},
                    {"en": "house", "fr": "maison", "yor": "ilé"},
                    {"en": "work", "fr": "travail", "yor": "iṣẹ́"},
                    {"en": "book", "fr": "livre", "yor": "ìwé"},
                    {"en": "child", "fr": "enfant", "yor": "ọmọ"},
                    {"en": "person", "fr": "personne", "yor": "ènìyàn"},
                    {"en": "day", "fr": "jour", "yor": "ọjọ́"},
                    {"en": "night", "fr": "nuit", "yor": "òru"},
                    {"en": "sun", "fr": "soleil", "yor": "òòrùn"},
                    {"en": "moon", "fr": "lune", "yor": "òṣùpá"},
                    {"en": "rain", "fr": "pluie", "yor": "òjò"},
                    {"en": "good", "fr": "bon", "yor": "dára"}
                ]
            },
            {
                "name": "yoruba_expressions",
                "type": "local",
                "data": [
                    {"en": "Good morning", "fr": "Bonjour", "yor": "E kaaro"},
                    {"en": "Good afternoon", "fr": "Bon après-midi", "yor": "E kaasan"},
                    {"en": "Good evening", "fr": "Bonsoir", "yor": "E kaale"},
                    {"en": "How are you?", "fr": "Comment allez-vous?", "yor": "Bawo ni?"},
                    {"en": "I am fine", "fr": "Je vais bien", "yor": "Mo wa daadaa"},
                    {"en": "What is your name?", "fr": "Comment vous appelez-vous?", "yor": "Kini oruko re?"},
                    {"en": "My name is...", "fr": "Je m'appelle...", "yor": "Oruko mi ni..."},
                    {"en": "Nice to meet you", "fr": "Enchanté", "yor": "O dabo"},
                    {"en": "Welcome", "fr": "Bienvenue", "yor": "E kaabo"},
                    {"en": "Thank you very much", "fr": "Merci beaucoup", "yor": "E seun pupo"}
                ]
            }
        ]
    
    def _get_ewe_resources(self):
        """Renvoie la liste des ressources spécifiques à l'ewe"""
        return [
            {
                "name": "lafand_mt",
                "type": "github",
                "url": "https://raw.githubusercontent.com/masakhane-io/lafand-mt/main/data/ee-en/ee_en_lafand.txt",
                "source_lang": "en",
                "format": "parallel"
            },
            {
                "name": "flores_ewe",
                "type": "github",
                "url": "https://raw.githubusercontent.com/facebookresearch/flores/main/flores200/devtest/ewe_Latn.devtest",
                "source_lang": "en",
                "format": "parallel"
            },
            {
                "name": "language_explorer",
                "type": "web",
                "url": "https://www.language-explorer.com/ewe/",
                "source_lang": "en",
                "format": "dictionary"
            },
            {
                "name": "jw300_ewe",
                "type": "opus",
                "corpus": "JW300",
                "source_langs": ["en", "fr"],
                "format": "parallel"
            },
            {
                "name": "bible_ewe",
                "type": "opus",
                "corpus": "Bible",
                "source_langs": ["en", "fr"],
                "format": "parallel"
            },
            {
                "name": "basic_ewe_vocabulary",
                "type": "local",
                "data": [
                    {"en": "hello", "fr": "bonjour", "ewe": "ndi"},
                    {"en": "goodbye", "fr": "au revoir", "ewe": "hede nyuie"},
                    {"en": "please", "fr": "s'il vous plaît", "ewe": "taflatse"},
                    {"en": "thank you", "fr": "merci", "ewe": "akpe"},
                    {"en": "yes", "fr": "oui", "ewe": "ɛe"},
                    {"en": "no", "fr": "non", "ewe": "ao"},
                    {"en": "water", "fr": "eau", "ewe": "tsi"},
                    {"en": "food", "fr": "nourriture", "ewe": "nuɖuɖu"},
                    {"en": "money", "fr": "argent", "ewe": "ga"},
                    {"en": "house", "fr": "maison", "ewe": "xɔ"},
                    {"en": "work", "fr": "travail", "ewe": "dɔ"},
                    {"en": "book", "fr": "livre", "ewe": "agbalẽ"},
                    {"en": "child", "fr": "enfant", "ewe": "ɖevi"},
                    {"en": "person", "fr": "personne", "ewe": "ame"},
                    {"en": "day", "fr": "jour", "ewe": "ŋkeke"},
                    {"en": "night", "fr": "nuit", "ewe": "zã"},
                    {"en": "good", "fr": "bon", "ewe": "nyuie"}
                ]
            },
            {
                "name": "ewe_expressions",
                "type": "local",
                "data": [
                    {"en": "Good morning", "fr": "Bonjour", "ewe": "Ŋdi na mi"},
                    {"en": "Good afternoon", "fr": "Bon après-midi", "ewe": "Ɣetrɔ na mi"},
                    {"en": "Good evening", "fr": "Bonsoir", "ewe": "Fiẽ na mi"},
                    {"en": "How are you?", "fr": "Comment allez-vous?", "ewe": "Èle agbe nyuiea?"},
                    {"en": "I am fine", "fr": "Je vais bien", "ewe": "Mele agbe nyuie"},
                    {"en": "What is your name?", "fr": "Comment vous appelez-vous?", "ewe": "Ŋkɔwò de?"},
                    {"en": "My name is...", "fr": "Je m'appelle...", "ewe": "Ŋkɔnye enye..."},
                    {"en": "Welcome", "fr": "Bienvenue", "ewe": "Woezɔ"},
                    {"en": "Thank you very much", "fr": "Merci beaucoup", "ewe": "Akpe kakaka"},
                    {"en": "Goodbye", "fr": "Au revoir", "ewe": "Heyi nyuie"}
                ]
            }
        ]
    
    def _get_fon_resources(self):
        """Renvoie la liste des ressources spécifiques au fon"""
        return [
            {
                "name": "reflex_corpus",
                "type": "web",
                "url": "https://www.reflex.cnrs.fr/dataset/fon_word_list_basic.txt",
                "source_lang": "fr",
                "format": "dictionary"
            },
            {
                "name": "glottolog_fon",
                "type": "web",
                "url": "https://glottolog.org/resource/languoid/id/fonn1241",
                "source_lang": "en",
                "format": "information"
            },
            {
                "name": "lexvo_fon",
                "type": "web",
                "url": "http://lexvo.org/id/iso639-3/fon",
                "source_lang": "en",
                "format": "information"
            },
            {
                "name": "basic_fon_vocabulary",
                "type": "local",
                "data": [
                    {"en": "hello", "fr": "bonjour", "fon": "kudo"},
                    {"en": "goodbye", "fr": "au revoir", "fon": "odabo"},
                    {"en": "please", "fr": "s'il vous plaît", "fon": "miɖekuku"},
                    {"en": "thank you", "fr": "merci", "fon": "awanou"},
                    {"en": "yes", "fr": "oui", "fon": "oui"},
                    {"en": "no", "fr": "non", "fon": "ǎyi"},
                    {"en": "water", "fr": "eau", "fon": "sin"},
                    {"en": "food", "fr": "nourriture", "fon": "núɖùɖù"},
                    {"en": "money", "fr": "argent", "fon": "akwɛ́"},
                    {"en": "house", "fr": "maison", "fon": "xwé"},
                    {"en": "work", "fr": "travail", "fon": "azɔn"},
                    {"en": "book", "fr": "livre", "fon": "wémà"},
                    {"en": "child", "fr": "enfant", "fon": "ví"},
                    {"en": "person", "fr": "personne", "fon": "gbɛtɔ́"},
                    {"en": "day", "fr": "jour", "fon": "azǎn"},
                    {"en": "night", "fr": "nuit", "fon": "zǎn"},
                    {"en": "good", "fr": "bon", "fon": "ɖagbé"}
                ]
            },
            {
                "name": "fon_expressions",
                "type": "local",
                "data": [
                    {"en": "Good morning", "fr": "Bonjour", "fon": "Kudo"},
                    {"en": "How are you?", "fr": "Comment allez-vous?", "fon": "A fɔn a?"},
                    {"en": "I am fine", "fr": "Je vais bien", "fon": "Un fɔn"},
                    {"en": "What is your name?", "fr": "Comment vous appelez-vous?", "fon": "Nyi nyikɔ tɛn?"},
                    {"en": "My name is...", "fr": "Je m'appelle...", "fon": "Nyikɔ ce nyɛ..."},
                    {"en": "Welcome", "fr": "Bienvenue", "fon": "Mí ká wǎ"},
                    {"en": "Have a good day", "fr": "Bonne journée", "fon": "Ní dó azǎngbé"},
                    {"en": "I love you", "fr": "Je t'aime", "fon": "Un yí wɛ"},
                    {"en": "Thank you very much", "fr": "Merci beaucoup", "fon": "Ɛ ná wǎn tawún"},
                    {"en": "God bless you", "fr": "Que Dieu vous bénisse", "fon": "Mawu ni xo ɖɛ dó jí mɛ"}
                ]
            }
        ]
    
    def _get_dindi_resources(self):
        """Renvoie la liste des ressources spécifiques au dindi"""
        # Très peu de ressources disponibles pour le dindi
        return [
            {
                "name": "ethnologue_dindi",
                "type": "web",
                "url": "https://www.ethnologue.com/language/ddn",
                "source_lang": "en",
                "format": "information"
            },
            {
                "name": "basic_dindi_vocabulary",
                "type": "local",
                "data": [
                    {"en": "hello", "fr": "bonjour", "dindi": "mba"},
                    {"en": "thank you", "fr": "merci", "dindi": "useko"},
                    {"en": "yes", "fr": "oui", "dindi": "ɛɛ"},
                    {"en": "no", "fr": "non", "dindi": "ayi"},
                    {"en": "water", "fr": "eau", "dindi": "minɖi"},
                    {"en": "food", "fr": "nourriture", "dindi": "aɖiɖi"},
                    {"en": "person", "fr": "personne", "dindi": "ɔzɔ"},
                    {"en": "house", "fr": "maison", "dindi": "sɔ"},
                    {"en": "village", "fr": "village", "dindi": "tɔwn"},
                    {"en": "man", "fr": "homme", "dindi": "ɔnuburɔ"},
                    {"en": "woman", "fr": "femme", "dindi": "ɔnɔkɔ"},
                    {"en": "child", "fr": "enfant", "dindi": "ɔbi"},
                    {"en": "head", "fr": "tête", "dindi": "eto"},
                    {"en": "hand", "fr": "main", "dindi": "anɔ"},
                    {"en": "foot", "fr": "pied", "dindi": "itiri"}
                ]
            }
        ]
    
    def search_available_opus_corpora(self, target_lang):
        """
        Recherche les corpus OPUS disponibles pour une langue cible
        
        Args:
            target_lang: Code de la langue cible
        
        Returns:
            Liste des corpus disponibles
        """
        available_corpora = []
        
        # Liste des corpus à vérifier
        corpora_to_check = [
            "JW300", "Bible", "QED", "MultiCCAligned", 
            "OpenSubtitles", "TED2020", "GNOME", "Ubuntu"
        ]
        
        # Variantes de code de langue
        language_variants = {
            "yor": ["yo", "yor"],
            "ewe": ["ee", "ewe"],
            "fon": ["fon"],
            "dindi": ["ddn", "dindi"]
        }
        
        lang_codes = language_variants.get(target_lang, [target_lang])
        
        for corpus in corpora_to_check:
            for source_lang in ["en", "fr"]:
                for lang_code in lang_codes:
                    url = f"https://object.pouta.csc.fi/OPUS-{corpus}/v1/moses/{source_lang}-{lang_code}.txt.zip"
                    try:
                        response = requests.head(url, timeout=5)
                        if response.status_code == 200:
                            available_corpora.append({
                                "corpus": corpus,
                                "source_lang": source_lang,
                                "target_lang": lang_code,
                                "url": url
                            })
                    except:
                        pass
        
        return available_corpora
    
    def _download_github_resource(self, resource, target_lang):
        """Télécharge une ressource depuis GitHub"""
        try:
            response = requests.get(resource['url'])
            response.raise_for_status()
            
            source_lang = resource['source_lang']
            
            # Déterminer le format du fichier et le traiter en conséquence
            corpus_name = resource['name']
            output_dir = os.path.join(self.corpus_dir, f"custom_{source_lang}_{target_lang}")
            output_path = os.path.join(output_dir, f"{corpus_name}_aligned.tsv")
            
            if resource['format'] == 'parallel':
                # Format: lignes alternées source/cible ou lignes avec tabulation
                content = response.text
                
                with open(output_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f, delimiter='\t')
                    writer.writerow(['source_text', 'target_text'])
                    
                    # Vérifier le format des données
                    if '\t' in content:
                        # Format: "source \t target"
                        for line in content.splitlines():
                            if line.strip():
                                parts = line.split('\t')
                                if len(parts) >= 2:
                                    writer.writerow([parts[0].strip(), parts[1].strip()])
                    else:
                        # Format: lignes alternées - essayer de détecter automatiquement
                        lines = [line.strip() for line in content.splitlines() if line.strip()]
                        
                        if len(lines) % 2 == 0:  # Nombre pair de lignes
                            for i in range(0, len(lines), 2):
                                if i + 1 < len(lines):
                                    writer.writerow([lines[i], lines[i+1]])
            
            elif resource['format'] == 'alignable':
                # Fichier nécessitant un alignement plus complexe
                # Pour simplifier, nous prenons juste les 1000 premières lignes
                content = response.text
                lines = [line.strip() for line in content.splitlines() if line.strip()]
                
                with open(output_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f, delimiter='\t')
                    writer.writerow(['source_text', 'target_text'])
                    
                    # Extraire des phrases sources et cibles du mieux possible
                    for line in lines[:1000]:
                        if ' :: ' in line:
                            # Format FFR avec séparateur
                            parts = line.split(' :: ')
                            if len(parts) >= 2:
                                writer.writerow([parts[0].strip(), parts[1].strip()])
            
            logger.info(f"Ressource GitHub téléchargée: {output_path}")
            
            return {
                "name": corpus_name,
                "path": output_path,
                "source_lang": source_lang,
                "target_lang": target_lang
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement de la ressource GitHub: {e}")
            return None
    
    def _download_web_resource(self, resource, target_lang):
        """Télécharge une ressource depuis un site web"""
        try:
            response = requests.get(resource['url'])
            response.raise_for_status()
            
            source_lang = resource['source_lang']
            corpus_name = resource['name']
            output_dir = os.path.join(self.corpus_dir, f"custom_{source_lang}_{target_lang}")
            output_path = os.path.join(output_dir, f"{corpus_name}_aligned.tsv")
            
            if resource['format'] == 'dictionary':
                # Traiter comme dictionnaire web
                soup = BeautifulSoup(response.text, 'lxml')
                pairs = []
                
                # Différentes stratégies d'extraction selon le site
                if "yorubaname.com" in resource['url']:
                    # Proverbes yoruba
                    for item in soup.select('.proverb-item'):
                        source = item.select_one('.original-proverb')
                        target = item.select_one('.proverb-translation')
                        if source and target:
                            pairs.append((source.text.strip(), target.text.strip()))
                
                elif "language-explorer.com" in resource['url']:
                    # Language Explorer
                    for item in soup.select('.entry'):
                        source = item.select_one('.english')
                        target = item.select_one('.ewe')
                        if source and target:
                            pairs.append((source.text.strip(), target.text.strip()))
                
                elif "reflex.cnrs.fr" in resource['url'] or resource['url'].endswith('.txt'):
                    # Fichier texte simple ou RefLex
                    for line in response.text.splitlines():
                        if '\t' in line:
                            parts = line.split('\t')
                            if len(parts) >= 2:
                                pairs.append((parts[0].strip(), parts[1].strip()))
                
                # Écrire les paires dans un fichier TSV
                with open(output_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f, delimiter='\t')
                    writer.writerow(['source_text', 'target_text'])
                    for src, tgt in pairs:
                        writer.writerow([src, tgt])
                
                logger.info(f"Ressource web téléchargée: {output_path} avec {len(pairs)} entrées")
                
                return {
                    "name": corpus_name,
                    "path": output_path,
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "entries": len(pairs)
                }
            
            elif resource['format'] == 'information' or resource['format'] == 'proverbs':
                # Pour les ressources informatives, on crée quand même un fichier
                # avec quelques exemples extraits de la page si possible
                soup = BeautifulSoup(response.text, 'lxml')
                pairs = []
                
                # Tenter d'extraire des paires de mots/phrases
                for p in soup.select('p'):
                    text = p.get_text()
                    if ':' in text and len(text.split(':')) == 2:
                        parts = text.split(':')
                        pairs.append((parts[0].strip(), parts[1].strip()))
                
                # Écrire ce qu'on a trouvé dans un fichier TSV
                with open(output_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f, delimiter='\t')
                    writer.writerow(['source_text', 'target_text'])
                    for src, tgt in pairs:
                        writer.writerow([src, tgt])
                
                logger.info(f"Ressource informative traitée: {output_path} avec {len(pairs)} entrées potentielles")
                
                if len(pairs) > 0:
                    return {
                        "name": corpus_name,
                        "path": output_path,
                        "source_lang": source_lang,
                        "target_lang": target_lang,
                        "entries": len(pairs)
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement de la ressource web: {e}")
            return None
    
    def _download_opus_resource(self, resource, target_lang):
        """Télécharge une ressource depuis OPUS"""
        from src.corpus.corpus_extractor import CorpusExtractor
        
        results = []
        
        for source_lang in resource['source_langs']:
            try:
                extractor = CorpusExtractor(self.corpus_dir)
                corpus_path = extractor.download_opus_corpus(source_lang, target_lang, resource['corpus'])
                
                if corpus_path:
                   filtered_path = extractor.filter_corpus_by_quality(corpus_path)
                   if filtered_path:
                       logger.info(f"Corpus OPUS téléchargé: {filtered_path}")
                       results.append({
                           "name": f"{resource['name']}_{source_lang}",
                           "path": filtered_path,
                           "source_lang": source_lang,
                           "target_lang": target_lang
                       })
            except Exception as e:
               logger.error(f"Erreur avec OPUS {resource['corpus']} {source_lang}-{target_lang}: {e}")
       
            return results if results else None
   
    def _create_local_resource(self, resource, target_lang):
       """Crée une ressource à partir de données locales prédéfinies"""
       data = resource['data']
       source_langs = ['en', 'fr']
       results = []
       
       for source_lang in source_langs:
           corpus_name = f"{resource['name']}_{source_lang}"
           output_dir = os.path.join(self.corpus_dir, f"custom_{source_lang}_{target_lang}")
           output_path = os.path.join(output_dir, f"{corpus_name}_aligned.tsv")
           
           # Collecter les paires pour cette langue source
           pairs = []
           for item in data:
               if source_lang in item and target_lang in item:
                   source_text = item[source_lang]
                   target_text = item[target_lang]
                   if source_text and target_text:
                       pairs.append((source_text, target_text))
           
           # Écrire les paires dans un fichier TSV
           with open(output_path, 'w', encoding='utf-8', newline='') as f:
               writer = csv.writer(f, delimiter='\t')
               writer.writerow(['source_text', 'target_text'])
               for src, tgt in pairs:
                   writer.writerow([src, tgt])
           
           logger.info(f"Ressource locale créée: {output_path} avec {len(pairs)} entrées")
           
           results.append({
               "name": corpus_name,
               "path": output_path,
               "source_lang": source_lang,
               "target_lang": target_lang,
               "entries": len(pairs)
           })
       
       return results
   
def consolidate_corpus(self, target_lang):
       """
       Consolide toutes les ressources disponibles pour une langue en un seul corpus
       
       Args:
           target_lang: Code de la langue cible
           
       Returns:
           Dictionnaire {source_lang: chemin_corpus_consolidé}
       """
       source_langs = ['en', 'fr']
       consolidated = {}
       
       for source_lang in source_langs:
           input_dir = os.path.join(self.corpus_dir, f"custom_{source_lang}_{target_lang}")
           output_path = os.path.join(self.corpus_dir, f"consolidated_{source_lang}_{target_lang}.tsv")
           
           if not os.path.exists(input_dir):
               logger.warning(f"Répertoire non trouvé: {input_dir}")
               continue
           
           # Collecter toutes les paires de textes
           all_pairs = []
           
           for filename in os.listdir(input_dir):
               if filename.endswith("_aligned.tsv"):
                   file_path = os.path.join(input_dir, filename)
                   try:
                       with open(file_path, 'r', encoding='utf-8') as f:
                           reader = csv.reader(f, delimiter='\t')
                           # Ignorer l'en-tête
                           next(reader, None)
                           for row in reader:
                               if len(row) == 2 and row[0] and row[1]:
                                   all_pairs.append((row[0], row[1]))
                   except Exception as e:
                       logger.error(f"Erreur lors de la lecture de {file_path}: {e}")
           
           # Écrire le corpus consolidé
           if all_pairs:
               with open(output_path, 'w', encoding='utf-8', newline='') as f:
                   writer = csv.writer(f, delimiter='\t')
                   writer.writerow(['source_text', 'target_text'])
                   for src, tgt in all_pairs:
                       writer.writerow([src, tgt])
               
               consolidated[source_lang] = output_path
               logger.info(f"Corpus consolidé créé: {output_path} avec {len(all_pairs)} entrées")
           else:
               logger.warning(f"Aucune paire trouvée pour {source_lang}-{target_lang}")
       
       return consolidated