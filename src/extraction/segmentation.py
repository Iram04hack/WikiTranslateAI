# src/extraction/segmentation.py

import os
import re
import json
import logging
import argparse
import nltk
from pathlib import Path

# Configuration du logging en premier
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Télécharger les ressources NLTK requises pour la tokenisation avancée
def ensure_nltk_data():
    """Télécharge les données NLTK nécessaires avec gestion d'erreurs robuste"""
    required_data = [
        ('tokenizers/punkt', 'punkt'),
        ('corpora/stopwords', 'stopwords')
    ]
    
    for path, name in required_data:
        try:
            nltk.data.find(path)
            logger.debug(f"Données NLTK trouvées: {name}")
        except (LookupError, OSError, Exception) as e:
            logger.info(f"Données NLTK manquantes: {name} - Mode fallback activé")
            # Ne pas télécharger automatiquement pour éviter les timeouts

# Initialiser les ressources NLTK avec gestion d'erreurs
try:
    ensure_nltk_data()
except Exception as e:
    logger.warning(f"Problème initialisation NLTK: {e} - Fonctionnalités de base maintenues")

# Import avancé pour la tokenisation multilangue avec fallback
try:
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    NLTK_ADVANCED_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Fonctionnalités NLTK avancées indisponibles: {e}")
    NLTK_ADVANCED_AVAILABLE = False
    # Fallback sur tokenisation basique
    def sent_tokenize(text, language=None):
        import re
        return re.split(r'[.!?]+', text)
    def word_tokenize(text, language=None):
        return text.split()

class TextSegmenter:
    """Classe pour segmenter le texte des articles en unités pour la traduction avec NLTK avancé"""
    
    def __init__(self, output_dir=None, max_segment_length=500, min_segment_length=20, language='french'):
        """
        Initialise le segmenteur de texte avec support NLTK multilangue
        
        Args:
            output_dir: Répertoire de sortie pour les textes segmentés
            max_segment_length: Longueur maximale d'un segment en caractères
            min_segment_length: Longueur minimale d'un segment en caractères
            language: Langue pour la tokenisation NLTK ('french', 'english', etc.)
        """
        self.output_dir = output_dir
        self.max_segment_length = max_segment_length
        self.min_segment_length = min_segment_length
        self.language = language
        
        # Configuration NLTK pour la langue cible
        self.nltk_language_map = {
            'fr': 'french',
            'french': 'french',
            'en': 'english', 
            'english': 'english',
            'fon': 'french',  # Utiliser français comme base pour les langues africaines
            'yor': 'english', # Utiliser anglais comme base pour yoruba
            'yoruba': 'english',
            'ewe': 'french',
            'dindi': 'french'
        }
        
        self.punkt_language = self.nltk_language_map.get(language.lower(), 'english')
        
        # Mots vides pour le preprocessing
        if NLTK_ADVANCED_AVAILABLE:
            try:
                self.stop_words = set(stopwords.words(self.punkt_language))
            except (OSError, LookupError):
                logger.warning(f"Mots vides indisponibles pour {self.punkt_language}, utilisation anglais")
                try:
                    self.stop_words = set(stopwords.words('english'))
                except (OSError, LookupError):
                    logger.warning("Mots vides NLTK indisponibles, utilisation liste basique")
                    self.stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        else:
            # Liste basique de mots vides multilingues
            self.stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                'le', 'la', 'les', 'un', 'une', 'des', 'et', 'ou', 'mais', 'dans', 'sur', 'à', 'pour', 'de', 'avec', 'par'
            }
        
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
        logger.info(f"Segmenteur initialisé - langue: {self.punkt_language}, segments: {min_segment_length}-{max_segment_length} chars")
    
    def segment_text(self, text):
        """
        Segmente un texte en unités de traduction
        
        Args:
            text: Texte à segmenter
        
        Returns:
            Liste des segments
        """
        if not text or not text.strip():
            return []
        
        # Diviser par paragraphes
        paragraphs = text.split('\n\n')
        segments = []
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # Si le paragraphe est court, le traiter comme un segment unique
            if len(paragraph) <= self.max_segment_length:
                segments.append(paragraph)
                continue
            
            # Sinon, diviser en phrases avec tokenisation spécifique à la langue (avec fallback)
            if NLTK_ADVANCED_AVAILABLE:
                try:
                    sentences = sent_tokenize(paragraph, language=self.punkt_language)
                except (LookupError, OSError):
                    sentences = [s.strip() for s in re.split(r'[.!?]+', paragraph) if s.strip()]
            else:
                sentences = [s.strip() for s in re.split(r'[.!?]+', paragraph) if s.strip()]
            current_segment = []
            current_length = 0
            
            for sentence in sentences:
                sentence_length = len(sentence)
                
                # Si une phrase est trop longue à elle seule, la diviser davantage
                if sentence_length > self.max_segment_length:
                    # Ajouter le segment en cours s'il existe
                    if current_segment:
                        segments.append(' '.join(current_segment))
                        current_segment = []
                        current_length = 0
                    
                    # Diviser la phrase longue par des virgules ou autres séparateurs
                    parts = re.split(r'([,;:])', sentence)
                    sub_segment = []
                    sub_length = 0
                    
                    for i in range(0, len(parts), 2):
                        part = parts[i]
                        delimiter = parts[i+1] if i+1 < len(parts) else ""
                        part_with_delim = part + delimiter
                        part_length = len(part_with_delim)
                        
                        if sub_length + part_length <= self.max_segment_length:
                            sub_segment.append(part_with_delim)
                            sub_length += part_length
                        else:
                            if sub_segment:
                                segments.append(''.join(sub_segment))
                            sub_segment = [part_with_delim]
                            sub_length = part_length
                    
                    if sub_segment:
                        segments.append(''.join(sub_segment))
                
                # Si ajouter la phrase ne dépasse pas la longueur maximale
                elif current_length + sentence_length <= self.max_segment_length:
                    current_segment.append(sentence)
                    current_length += sentence_length
                else:
                    # Finir le segment en cours et commencer un nouveau
                    if current_segment:
                        segments.append(' '.join(current_segment))
                    current_segment = [sentence]
                    current_length = sentence_length
            
            # Ajouter le dernier segment s'il existe
            if current_segment:
                segments.append(' '.join(current_segment))
        
        # Filtrer les segments trop courts
        segments = [s for s in segments if len(s) >= self.min_segment_length]
        
        return segments
    
    def analyze_text_properties(self, text):
        """
        Analyse les propriétés linguistiques d'un texte avec NLTK
        
        Args:
            text: Texte à analyser
        
        Returns:
            Dict avec les métriques linguistiques
        """
        if not text or not text.strip():
            return {}
        
        # Tokenisation en mots (avec fallback si NLTK non disponible)
        if NLTK_ADVANCED_AVAILABLE:
            try:
                words = word_tokenize(text.lower(), language=self.punkt_language)
                sentences = sent_tokenize(text, language=self.punkt_language)
            except (LookupError, OSError):
                # Fallback en cas d'échec NLTK
                words = text.lower().split()
                sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        else:
            words = text.lower().split()
            sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        
        # Filtrer les mots vides et la ponctuation
        content_words = [word for word in words if word.isalpha() and word not in self.stop_words]
        
        analysis = {
            'total_chars': len(text),
            'total_words': len(words),
            'content_words': len(content_words),
            'sentences': len(sentences),
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
            'avg_word_length': sum(len(word) for word in content_words) / len(content_words) if content_words else 0,
            'stop_word_ratio': (len(words) - len(content_words)) / len(words) if words else 0
        }
        
        return analysis
    
    def smart_segment_by_complexity(self, text):
        """
        Segmentation intelligente basée sur la complexité linguistique
        
        Args:
            text: Texte à segmenter
        
        Returns:
            Liste des segments optimisés
        """
        if not text or not text.strip():
            return []
        
        # Analyse initiale du texte
        analysis = self.analyze_text_properties(text)
        
        # Ajustement dynamique des paramètres selon la complexité
        if analysis.get('avg_sentence_length', 0) > 25:  # Phrases très longues
            effective_max_length = int(self.max_segment_length * 0.8)
            logger.debug("Phrases complexes détectées - réduction taille segments")
        elif analysis.get('avg_sentence_length', 0) < 10:  # Phrases courtes
            effective_max_length = int(self.max_segment_length * 1.2) 
            logger.debug("Phrases simples détectées - augmentation taille segments")
        else:
            effective_max_length = self.max_segment_length
        
        # Segmentation avec paramètres ajustés
        paragraphs = text.split('\n\n')
        segments = []
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            if len(paragraph) <= effective_max_length:
                segments.append(paragraph)
                continue
            
            # Tokenisation avancée pour les paragraphes longs (avec fallback)
            if NLTK_ADVANCED_AVAILABLE:
                try:
                    sentences = sent_tokenize(paragraph, language=self.punkt_language)
                except (LookupError, OSError):
                    sentences = [s.strip() for s in re.split(r'[.!?]+', paragraph) if s.strip()]
            else:
                sentences = [s.strip() for s in re.split(r'[.!?]+', paragraph) if s.strip()]
            current_segment = []
            current_length = 0
            
            for sentence in sentences:
                sentence_length = len(sentence)
                
                # Gestion intelligente des phrases longues
                if sentence_length > effective_max_length:
                    if current_segment:
                        segments.append(' '.join(current_segment))
                        current_segment = []
                        current_length = 0
                    
                    # Division par unités syntaxiques (virgules, points-virgules)
                    parts = re.split(r'([,;:])', sentence)
                    sub_segment = []
                    sub_length = 0
                    
                    for i in range(0, len(parts), 2):
                        part = parts[i]
                        delimiter = parts[i+1] if i+1 < len(parts) else ""
                        part_with_delim = part + delimiter
                        part_length = len(part_with_delim)
                        
                        if sub_length + part_length <= effective_max_length:
                            sub_segment.append(part_with_delim)
                            sub_length += part_length
                        else:
                            if sub_segment:
                                segments.append(''.join(sub_segment))
                            sub_segment = [part_with_delim]
                            sub_length = part_length
                    
                    if sub_segment:
                        segments.append(''.join(sub_segment))
                
                elif current_length + sentence_length <= effective_max_length:
                    current_segment.append(sentence)
                    current_length += sentence_length
                else:
                    if current_segment:
                        segments.append(' '.join(current_segment))
                    current_segment = [sentence]
                    current_length = sentence_length
            
            if current_segment:
                segments.append(' '.join(current_segment))
        
        # Filtrage final avec métriques de qualité
        quality_segments = []
        for segment in segments:
            if len(segment) >= self.min_segment_length:
                # Analyse de qualité du segment
                seg_analysis = self.analyze_text_properties(segment)
                if seg_analysis.get('content_words', 0) > 2:  # Au moins 3 mots de contenu
                    quality_segments.append(segment)
                else:
                    logger.debug(f"Segment écarté (qualité faible): {segment[:50]}...")
        
        logger.info(f"Segmentation intelligente: {len(quality_segments)} segments (complexité: {analysis.get('avg_sentence_length', 0):.1f} mots/phrase)")
        return quality_segments
    
    def segment_article(self, article_data, use_smart_segmentation=True):
        """
        Segmente un article complet avec NLTK avancé
        
        Args:
            article_data: Données d'article nettoyées
            use_smart_segmentation: Utiliser la segmentation intelligente (défaut: True)
        
        Returns:
            Article avec segments et métadonnées linguistiques
        """
        title = article_data.get('title', '')
        metadata = article_data.get('metadata', {})
        sections = article_data.get('sections', [])
        
        segmented_sections = []
        total_segments = 0
        total_analysis = {
            'total_chars': 0,
            'total_words': 0, 
            'content_words': 0,
            'sentences': 0
        }
        
        for section in sections:
            section_title = section.get('title', '')
            section_level = section.get('level', 0)
            section_content = section.get('content', '')
            
            # Choisir la méthode de segmentation
            if use_smart_segmentation:
                segments = self.smart_segment_by_complexity(section_content)
                segmentation_method = "smart_nltk"
            else:
                segments = self.segment_text(section_content)
                segmentation_method = "basic_nltk"
            
            # Analyse de la section
            section_analysis = self.analyze_text_properties(section_content)
            
            # Mise à jour des statistiques globales
            for key in total_analysis:
                total_analysis[key] += section_analysis.get(key, 0)
            
            total_segments += len(segments)
            
            segmented_sections.append({
                'title': section_title,
                'level': section_level,
                'segments': segments,
                'segment_count': len(segments),
                'analysis': section_analysis,
                'segmentation_method': segmentation_method
            })
        
        # Créer l'article segmenté avec métadonnées enrichies
        segmented_article = {
            'title': title,
            'metadata': metadata,
            'segmented_sections': segmented_sections,
            'segmentation_stats': {
                'total_segments': total_segments,
                'total_sections': len(sections),
                'segmentation_method': segmentation_method,
                'language': self.punkt_language,
                'analysis': total_analysis,
                'avg_segment_size': total_analysis['total_chars'] / total_segments if total_segments else 0
            }
        }
        
        logger.info(f"Article '{title}' segmenté: {total_segments} segments, {total_analysis['sentences']} phrases, langue: {self.punkt_language}")
        
        return segmented_article
    
    def segment_article_file(self, input_file_path):
        """
        Segmente un fichier d'article
        
        Args:
            input_file_path: Chemin vers le fichier d'article nettoyé
        
        Returns:
            Chemin du fichier segmenté ou None en cas d'erreur
        """
        logger.info(f"Segmentation de l'article: {input_file_path}")
        
        try:
            with open(input_file_path, 'r', encoding='utf-8') as f:
                article_data = json.load(f)
            
            segmented_article = self.segment_article(article_data)
            
            # Sauvegarder si un répertoire de sortie est spécifié
            if self.output_dir:
                output_path = os.path.join(self.output_dir, os.path.basename(input_file_path))
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(segmented_article, f, ensure_ascii=False, indent=2)
                logger.info(f"Article segmenté sauvegardé: {output_path}")
                return output_path
            
            return segmented_article
        
        except Exception as e:
            logger.error(f"Erreur lors de la segmentation de l'article {input_file_path}: {e}")
            return None
    
    def segment_directory(self, input_dir):
        """
        Segmente tous les articles dans un répertoire
        
        Args:
            input_dir: Répertoire contenant les articles nettoyés
        
        Returns:
            Nombre d'articles segmentés
        """
        count = 0
        for filename in os.listdir(input_dir):
            if filename.endswith('.json'):
                input_path = os.path.join(input_dir, filename)
                if self.segment_article_file(input_path):
                    count += 1
        
        logger.info(f"{count} articles segmentés depuis {input_dir}")
        return count


def main():
    parser = argparse.ArgumentParser(description="Segmentation d'articles pour la traduction avec NLTK avancé")
    parser.add_argument('--input', type=str, required=True, 
                        help="Fichier article ou répertoire d'articles à segmenter")
    parser.add_argument('--output-dir', type=str, default='data/articles_segmented', 
                        help="Répertoire de sortie pour les articles segmentés")
    parser.add_argument('--max-length', type=int, default=500, 
                        help="Longueur maximale d'un segment en caractères")
    parser.add_argument('--min-length', type=int, default=20, 
                        help="Longueur minimale d'un segment en caractères")
    parser.add_argument('--language', type=str, default='french',
                        choices=['french', 'english', 'fr', 'en', 'fon', 'yor', 'ewe', 'dindi'],
                        help="Langue source pour la tokenisation NLTK")
    parser.add_argument('--smart-segmentation', action='store_true', default=True,
                        help="Utiliser la segmentation intelligente basée sur la complexité")
    parser.add_argument('--basic-segmentation', action='store_true',
                        help="Utiliser la segmentation de base (remplace --smart-segmentation)")
    
    args = parser.parse_args()
    
    # Si --basic-segmentation est spécifié, désactiver smart-segmentation
    use_smart = args.smart_segmentation and not args.basic_segmentation
    
    segmenter = TextSegmenter(
        args.output_dir,
        max_segment_length=args.max_length,
        min_segment_length=args.min_length,
        language=args.language
    )
    
    logger.info(f"Configuration: langue={args.language}, segmentation={'intelligente' if use_smart else 'basique'}")
    
    if os.path.isdir(args.input):
        segmenter.segment_directory(args.input)
    elif os.path.isfile(args.input):
        segmenter.segment_article_file(args.input)
    else:
        parser.error(f"Le chemin d'entrée n'existe pas: {args.input}")

if __name__ == "__main__":
    main()