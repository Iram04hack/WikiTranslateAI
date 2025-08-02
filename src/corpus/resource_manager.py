# src/corpus/resource_manager.py

import os
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class LinguisticResourceManager:
    """Gestion centralisée des ressources linguistiques"""
    
    def __init__(self, config):
        """
        Initialise le gestionnaire de ressources linguistiques
        
        Args:
            config: Configuration du projet
        """
        self.config = config
        self.db_path = config['paths']['glossary_db']
        self.corpus_dir = os.path.join(config['paths']['data_dir'], 'corpus')
        self.terminology_dir = os.path.join(config['paths']['data_dir'], 'terminology')
        
        # Créer les répertoires nécessaires
        Path(self.corpus_dir).mkdir(parents=True, exist_ok=True)
        Path(self.terminology_dir).mkdir(parents=True, exist_ok=True)
    
    def download_corpus(self, source_lang, target_lang, domain="WikiMatrix", max_size=None):
        """
        Télécharge un corpus parallèle depuis OPUS
        
        Args:
            source_lang: Code de la langue source
            target_lang: Code de la langue cible
            domain: Domaine du corpus (ex: WikiMatrix, Bible, etc.)
            max_size: Taille maximale à télécharger (en Mo)
            
        Returns:
            Chemin vers le corpus téléchargé et filtré
        """
        from src.corpus.corpus_extractor import CorpusExtractor
        extractor = CorpusExtractor(self.corpus_dir)
        
        corpus_path = extractor.download_opus_corpus(source_lang, target_lang, domain, max_size)
        if corpus_path:
            filtered_path = extractor.filter_corpus_by_quality(corpus_path)
            return filtered_path
        return None
    
    def extract_wiktionary_terms(self, source_lang, target_lang, max_words=500):
        """
        Extrait des termes depuis Wiktionary
        
        Args:
            source_lang: Code de la langue source
            target_lang: Code de la langue cible
            max_words: Nombre maximum de mots à extraire
            
        Returns:
            Nombre de termes extraits
        """
        from src.database.wiktionary_extractor import WiktionaryExtractor
        extractor = WiktionaryExtractor(self.db_path)
        
        return extractor.extract_translations(source_lang, target_lang, max_words=max_words)
    
    def import_terminology(self, file_path, source_lang, target_lang=None, domain=None):
        """
        Importe un fichier de terminologie
        
        Args:
            file_path: Chemin vers le fichier de terminologie
            source_lang: Code de la langue source
            target_lang: Code de la langue cible (optionnel)
            domain: Domaine des termes (optionnel)
            
        Returns:
            Dictionnaire {langue: nombre de termes importés}
        """
        from src.database.terminology_importer import TerminologyImporter
        importer = TerminologyImporter(self.db_path)
        
        target_langs = [target_lang] if target_lang else None
        return importer.import_multilingual_terminology(file_path, source_lang, target_langs, domain)
    
    # Dans src/corpus/resource_manager.py, modifiez la fonction enrich_from_all_sources

def enrich_from_all_sources(self, source_lang, target_lang):
    """
    Enrichit le glossaire à partir de toutes les sources disponibles
    
    Args:
        source_lang: Code de la langue source
        target_lang: Code de la langue cible
        
    Returns:
        Statistiques d'enrichissement
    """
    stats = {
        'corpus': 0,
        'wiktionary': 0,
        'terminology': 0,
        'custom_resources': 0,
        'total': 0
    }
    
    # 1. Extraire un corpus depuis OPUS si disponible
    corpus_path = self.download_corpus(source_lang, target_lang)
    if corpus_path:
            from src.database.glossary_learner import EnhancedGlossaryLearner
            learner = EnhancedGlossaryLearner(self.db_path)
            
            corpus_terms = learner.learn_from_aligned_corpus(
                corpus_path, source_lang, target_lang
            )
            stats['corpus'] = corpus_terms
        
        # 2. Extraire des termes depuis Wiktionary
    wiktionary_terms = self.extract_wiktionary_terms(source_lang, target_lang, max_words=300)
    stats['wiktionary'] = wiktionary_terms
        
        # 3. Importer des ressources terminologiques spécifiques si disponibles
    terminology_stats = {}
    for filename in os.listdir(self.terminology_dir):
            if filename.endswith(('.tbx', '.csv', '.tsv', '.json')):
                file_path = os.path.join(self.terminology_dir, filename)
                
                domain = None
                if '_' in filename:
                    # Format attendu: domaine_source_cible.ext
                    parts = os.path.splitext(filename)[0].split('_')
                    if len(parts) >= 1:
                        domain = parts[0]
                
                import_result = self.import_terminology(
                    file_path, source_lang, target_lang, domain
                )
                
                if target_lang in import_result:
                    if domain not in terminology_stats:
                        terminology_stats[domain] = 0
                    terminology_stats[domain] += import_result[target_lang]
        
    stats['terminology'] = sum(terminology_stats.values())
    stats['terminology_details'] = terminology_stats

    
    # Ajouter l'utilisation des ressources spécifiques par langue
    try:
        from src.corpus.custom_corpus import CustomCorpusManager
        custom_manager = CustomCorpusManager(self.corpus_dir)
        
        # Télécharger des ressources spécifiques pour cette langue
        custom_resources = custom_manager.download_language_specific_resources(target_lang)
        
        if custom_resources:
            from src.database.glossary_learner import EnhancedGlossaryLearner
            learner = EnhancedGlossaryLearner(self.db_path)
            
            custom_terms = 0
            
            # Traiter chaque ressource téléchargée
            for resource in custom_resources:
                if isinstance(resource, list):
                    # Liste de ressources
                    for res in resource:
                        if res['source_lang'] == source_lang:
                            corpus_path = res['path']
                            terms = learner.learn_from_aligned_corpus(
                                corpus_path, source_lang, target_lang
                            )
                            custom_terms += terms
                else:
                    # Ressource unique
                    if resource['source_lang'] == source_lang:
                        corpus_path = resource['path']
                        terms = learner.learn_from_aligned_corpus(
                            corpus_path, source_lang, target_lang
                        )
                        custom_terms += terms
            
            stats['custom_resources'] = custom_terms
            logger.info(f"Termes extraits des ressources spécifiques: {custom_terms}")
    except Exception as e:
        logger.error(f"Erreur lors de l'utilisation des ressources spécifiques: {e}")
    
    # Mettre à jour le total
    stats['total'] = stats['corpus'] + stats['wiktionary'] + stats['terminology'] + stats['custom_resources']
    
    return stats
    
def get_glossary_statistics(self, source_lang=None, target_lang=None):
        """
        Obtient des statistiques sur le glossaire actuel
        
        Args:
            source_lang: Code de langue source (optionnel)
            target_lang: Code de langue cible (optionnel)
            
        Returns:
            Statistiques du glossaire
        """
        stats = {}
        
        from src.database.glossary_manager import GlossaryManager
        with GlossaryManager(self.db_path) as gm:
            # Nombre total d'entrées
            gm.cursor.execute("SELECT COUNT(*) FROM glossary_entries")
            stats['total_entries'] = gm.cursor.fetchone()[0]
            
            # Entrées par paire de langues
            if source_lang and target_lang:
                source_lang_id = gm.get_language_id(source_lang)
                target_lang_id = gm.get_language_id(target_lang)
                
                if source_lang_id and target_lang_id:
                    gm.cursor.execute("""
                        SELECT COUNT(*) FROM glossary_entries
                        WHERE source_language_id = ? AND target_language_id = ?
                    """, (source_lang_id, target_lang_id))
                    stats['pair_entries'] = gm.cursor.fetchone()[0]
            
            # Statistiques par domaine
            gm.cursor.execute("""
                SELECT d.name, COUNT(*) as count
                FROM glossary_entries ge
                JOIN domains d ON ge.domain_id = d.id
                GROUP BY d.name
                ORDER BY count DESC
            """)
            stats['domains'] = {row['name']: row['count'] for row in gm.cursor.fetchall()}
            
            # Entrées validées vs non validées
            gm.cursor.execute("SELECT COUNT(*) FROM glossary_entries WHERE validated = 1")
            stats['validated'] = gm.cursor.fetchone()[0]
            stats['unvalidated'] = stats['total_entries'] - stats['validated']
            
            # Distribution des scores de confiance
            gm.cursor.execute("""
                SELECT 
                    SUM(CASE WHEN confidence_score < 0.3 THEN 1 ELSE 0 END) as low,
                    SUM(CASE WHEN confidence_score >= 0.3 AND confidence_score < 0.7 THEN 1 ELSE 0 END) as medium,
                    SUM(CASE WHEN confidence_score >= 0.7 THEN 1 ELSE 0 END) as high
                FROM glossary_entries
            """)
            confidence = gm.cursor.fetchone()
            stats['confidence'] = {
                'low': confidence['low'],
                'medium': confidence['medium'],
                'high': confidence['high']
            }
        
        return stats