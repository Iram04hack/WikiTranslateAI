# src/database/terminology_importer.py

import os
import csv
import json
import logging
import re
from pathlib import Path
from src.database.glossary_manager import GlossaryManager

logger = logging.getLogger(__name__)

class TerminologyImporter:
    """Importation de ressources terminologiques depuis diverses sources"""
    
    def __init__(self, db_path):
        """Initialise l'importateur de terminologie"""
        self.db_path = db_path
    
    def import_multilingual_terminology(self, file_path, source_lang, target_langs=None, domain=None):
        """
        Importe un fichier de terminologie multilingue
        
        Args:
            file_path: Chemin vers le fichier de terminologie
            source_lang: Code de la langue source
            target_langs: Liste des langues cibles (toutes si None)
            domain: Domaine des termes
            
        Returns:
            Dictionnaire {langue: nombre de termes importés}
        """
        # Déterminer le format du fichier
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.tbx':
            return self._import_tbx(file_path, source_lang, target_langs, domain)
        elif file_ext == '.csv' or file_ext == '.tsv':
            return self._import_tabular(file_path, source_lang, target_langs, domain)
        elif file_ext == '.json':
            return self._import_json(file_path, source_lang, target_langs, domain)
        else:
            logger.error(f"Format de fichier non pris en charge: {file_ext}")
            return {}
    
    def _import_tbx(self, file_path, source_lang, target_langs, domain):
        """Importe un fichier TBX (TermBase eXchange)"""
        try:
            import xml.etree.ElementTree as ET
            
            # Statistiques d'importation
            import_stats = {}
            
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            ns = {'tbx': 'urn:iso:std:iso:30042:ed-1'}
            
            with GlossaryManager(self.db_path) as gm:
                # Parcourir les concepts
                for concept in root.findall('.//tbx:conceptEntry', ns):
                    source_term = None
                    translations = {}
                    
                    # Extraire le terme source
                    for term_sec in concept.findall('.//tbx:termSec', ns):
                        lang_code = term_sec.find('.//tbx:termNote[@type="language"]', ns)
                        if lang_code is None:
                            # Essayer d'autres formats
                            lang_code = term_sec.get('xml:lang', '')
                        else:
                            lang_code = lang_code.text
                        
                        # Normaliser le code de langue
                        lang_code = lang_code.split('-')[0].lower()
                        
                        if lang_code == source_lang:
                            term = term_sec.find('.//tbx:term', ns)
                            if term is not None:
                                source_term = term.text
                        elif target_langs is None or lang_code in target_langs:
                            term = term_sec.find('.//tbx:term', ns)
                            if term is not None:
                                translations[lang_code] = term.text
                    
                    # Si un terme source a été trouvé, ajouter les traductions
                    if source_term:
                        for target_lang, target_term in translations.items():
                            # Mettre à jour les statistiques
                            if target_lang not in import_stats:
                                import_stats[target_lang] = 0
                            
                            # Ajouter au glossaire
                            gm.add_term(
                                source_term=source_term,
                                source_lang=source_lang,
                                target_term=target_term,
                                target_lang=target_lang,
                                domain=domain or 'terminology',
                                confidence=0.85,  # Confiance élevée pour les ressources terminologiques
                                validated=True
                            )
                            
                            import_stats[target_lang] += 1
            
            return import_stats
            
        except Exception as e:
            logger.error(f"Erreur lors de l'importation du fichier TBX: {e}")
            return {}
    
    def _import_tabular(self, file_path, source_lang, target_langs, domain):
        """Importe un fichier CSV/TSV"""
        try:
            # Déterminer le délimiteur
            delimiter = '\t' if file_path.endswith('.tsv') else ','
            
            # Statistiques d'importation
            import_stats = {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                
                # Identifier les colonnes de langue
                lang_columns = {}
                for header in reader.fieldnames:
                    # Format attendu: "term_XX" où XX est le code de langue
                    match = re.match(r'term_([a-z]{2,5})$', header.lower())
                    if match:
                        lang_code = match.group(1)
                        lang_columns[lang_code] = header
                
                if source_lang not in lang_columns:
                    logger.error(f"Colonne pour la langue source {source_lang} non trouvée")
                    return {}
                
                with GlossaryManager(self.db_path) as gm:
                    for row in reader:
                        source_term = row[lang_columns[source_lang]]
                        
                        if not source_term:
                            continue
                        
                        # Extraire les traductions
                        for lang_code, column in lang_columns.items():
                            if lang_code == source_lang:
                                continue
                                
                            if target_langs and lang_code not in target_langs:
                                continue
                            
                            target_term = row[column]
                            if not target_term:
                                continue
                            
                            # Mettre à jour les statistiques
                            if lang_code not in import_stats:
                                import_stats[lang_code] = 0
                            
                            # Ajouter au glossaire
                            term_domain = row.get('domain', domain or 'terminology')
                            
                            gm.add_term(
                                source_term=source_term,
                                source_lang=source_lang,
                                target_term=target_term,
                                target_lang=lang_code,
                                domain=term_domain,
                                confidence=0.85,
                                validated=True
                            )
                            
                            import_stats[lang_code] += 1
            
            return import_stats
            
        except Exception as e:
            logger.error(f"Erreur lors de l'importation du fichier tabulaire: {e}")
            return {}
    
    def _import_json(self, file_path, source_lang, target_langs, domain):
        """Importe un fichier JSON"""
        try:
            # Statistiques d'importation
            import_stats = {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            with GlossaryManager(self.db_path) as gm:
                # Format attendu: liste de concepts
                if isinstance(data, list):
                    for item in data:
                        if "source_term" in item and "translations" in item:
                            source_term = item["source_term"]
                            translations = item["translations"]
                            
                            for trans in translations:
                                lang_code = trans.get("language")
                                target_term = trans.get("term")
                                
                                if not lang_code or not target_term:
                                    continue
                                
                                if target_langs and lang_code not in target_langs:
                                    continue
                                
                                # Mettre à jour les statistiques
                                if lang_code not in import_stats:
                                    import_stats[lang_code] = 0
                                
                                # Ajouter au glossaire
                                term_domain = trans.get("domain", item.get("domain", domain or "terminology"))
                                
                                gm.add_term(
                                    source_term=source_term,
                                    source_lang=source_lang,
                                    target_term=target_term,
                                    target_lang=lang_code,
                                    domain=term_domain,
                                    confidence=0.9,
                                    validated=True
                                )
                                
                                import_stats[lang_code] += 1
                
                # Format alternatif: structure imbriquée par langue
                elif isinstance(data, dict) and "terms" in data:
                    for term_entry in data["terms"]:
                        source_term = term_entry.get(source_lang)
                        
                        if not source_term:
                            continue
                        
                        for lang_code, target_term in term_entry.items():
                            if lang_code == source_lang:
                                continue
                            
                            if target_langs and lang_code not in target_langs:
                                continue
                            
                            if not target_term:
                                continue
                            
                            # Mettre à jour les statistiques
                            if lang_code not in import_stats:
                                import_stats[lang_code] = 0
                            
                            # Ajouter au glossaire
                            term_domain = term_entry.get("domain", domain or "terminology")
                            
                            gm.add_term(
                                source_term=source_term,
                                source_lang=source_lang,
                                target_term=target_term,
                                target_lang=lang_code,
                                domain=term_domain,
                                confidence=0.85,
                                validated=True
                            )
                            
                            import_stats[lang_code] += 1
            
            return import_stats
            
        except Exception as e:
            logger.error(f"Erreur lors de l'importation du fichier JSON: {e}")
            return {} 