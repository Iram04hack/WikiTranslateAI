# src/corpus/corpus_extractor.py

import os
import logging
import requests
import csv
import zipfile
import io
from pathlib import Path

logger = logging.getLogger(__name__)

class CorpusExtractor:
    """Extraction et gestion de corpus parallèles depuis diverses sources"""
    
    def __init__(self, output_dir="data/corpus"):
        """Initialise l'extracteur de corpus"""
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    def download_opus_corpus(self, source_lang, target_lang, domain="WikiMatrix", max_size=None):
        """
        Télécharge un corpus parallèle depuis OPUS
        
        Args:
            source_lang: Code de la langue source
            target_lang: Code de la langue cible
            domain: Domaine du corpus (ex: WikiMatrix, Bible, etc.)
            max_size: Taille maximale à télécharger (en Mo)
            
        Returns:
            Chemin vers le corpus téléchargé
        """
        # Construire l'URL OPUS
        opus_url = f"https://object.pouta.csc.fi/OPUS-{domain}/v1/moses/{source_lang}-{target_lang}.txt.zip"
        logger.info(f"Téléchargement du corpus {domain} pour {source_lang}-{target_lang}")
        
        try:
            # Télécharger le fichier
            response = requests.get(opus_url, stream=True)
            response.raise_for_status()
            
            # Vérifier la taille
            content_length = int(response.headers.get('content-length', 0))
            if max_size and content_length > max_size * 1024 * 1024:
                logger.warning(f"Corpus trop volumineux: {content_length/(1024*1024):.2f} Mo > {max_size} Mo")
                return None
            
            # Extraire le contenu du zip
            z = zipfile.ZipFile(io.BytesIO(response.content))
            
            # Créer un dossier pour ce corpus
            corpus_dir = os.path.join(self.output_dir, f"{domain}_{source_lang}_{target_lang}")
            Path(corpus_dir).mkdir(exist_ok=True)
            
            # Extraire les fichiers pertinents
            source_file = None
            target_file = None
            
            for file in z.namelist():
                if f"{domain}.{source_lang}-{target_lang}.{source_lang}" in file:
                    source_file = file
                elif f"{domain}.{source_lang}-{target_lang}.{target_lang}" in file:
                    target_file = file
            
            if not source_file or not target_file:
                logger.error(f"Fichiers source ou cible non trouvés dans le corpus")
                return None
            
            # Extraire les fichiers
            z.extract(source_file, corpus_dir)
            z.extract(target_file, corpus_dir)
            
            # Créer un fichier parallèle aligné
            source_path = os.path.join(corpus_dir, source_file)
            target_path = os.path.join(corpus_dir, target_file)
            aligned_path = os.path.join(corpus_dir, f"{source_lang}_{target_lang}_aligned.tsv")
            
            with open(source_path, 'r', encoding='utf-8') as src_file, \
                 open(target_path, 'r', encoding='utf-8') as tgt_file, \
                 open(aligned_path, 'w', encoding='utf-8', newline='') as out_file:
                
                writer = csv.writer(out_file, delimiter='\t')
                writer.writerow(['source_text', 'target_text'])
                
                for src_line, tgt_line in zip(src_file, tgt_file):
                    writer.writerow([src_line.strip(), tgt_line.strip()])
            
            logger.info(f"Corpus aligné créé: {aligned_path}")
            return aligned_path
            
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement du corpus: {e}")
            return None
    
    def filter_corpus_by_quality(self, corpus_path, min_length=3, max_length=100, min_length_ratio=0.5, max_length_ratio=2.0):
        """
        Filtre un corpus parallèle pour ne garder que les segments de bonne qualité
        
        Args:
            corpus_path: Chemin vers le corpus TSV
            min_length: Longueur minimale des segments (en mots)
            max_length: Longueur maximale des segments (en mots)
            min_length_ratio: Ratio min longueur cible/source
            max_length_ratio: Ratio max longueur cible/source
            
        Returns:
            Chemin vers le corpus filtré
        """
        filtered_path = corpus_path.replace('.tsv', '_filtered.tsv')
        
        try:
            with open(corpus_path, 'r', encoding='utf-8') as in_file, \
                 open(filtered_path, 'w', encoding='utf-8', newline='') as out_file:
                
                reader = csv.reader(in_file, delimiter='\t')
                writer = csv.writer(out_file, delimiter='\t')
                
                # Copier l'en-tête
                header = next(reader)
                writer.writerow(header)
                
                filtered_count = 0
                total_count = 0
                
                for row in reader:
                    total_count += 1
                    
                    if len(row) != 2:
                        continue
                    
                    source_text, target_text = row
                    
                    # Vérifier les longueurs
                    source_words = len(source_text.split())
                    target_words = len(target_text.split())
                    
                    if source_words < min_length or source_words > max_length:
                        continue
                    
                    if target_words < min_length or target_words > max_length:
                        continue
                    
                    # Vérifier le ratio des longueurs
                    if source_words > 0:
                        ratio = target_words / source_words
                        if ratio < min_length_ratio or ratio > max_length_ratio:
                            continue
                    
                    # Ligne conservée
                    writer.writerow(row)
                    filtered_count += 1
            
            logger.info(f"Corpus filtré: {filtered_count}/{total_count} segments conservés")
            return filtered_path
            
        except Exception as e:
            logger.error(f"Erreur lors du filtrage du corpus: {e}")
            return None