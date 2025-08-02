# src/database/glossary_learner.py
import logging
import json
import re
from difflib import SequenceMatcher
from src.database.glossary_manager import GlossaryManager
import itertools

logger = logging.getLogger(__name__)

class GlossaryLearner:
    """Enrichit le glossaire en apprenant de nouvelles traductions"""
    
    def __init__(self, db_path):
        """Initialise le GlossaryLearner avec le chemin vers la BDD"""
        self.db_path = db_path
    
    def import_external_glossary(self, file_path, source_lang, target_lang, confidence=0.8, validated=True):
        """Importe un glossaire externe depuis un fichier"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Déterminer le format du fichier
                if file_path.endswith('.json'):
                    data = json.load(f)
                    return self._process_json_glossary(data, source_lang, target_lang, confidence, validated)
                elif file_path.endswith('.csv'):
                    import csv
                    glossary_data = []
                    with open(file_path, 'r', encoding='utf-8') as csvfile:
                        reader = csv.DictReader(csvfile)
                        for row in reader:
                            if 'source' in row and 'target' in row:
                                glossary_data.append({
                                    'source_term': row['source'],
                                    'target_term': row['target'],
                                    'domain': row.get('domain', 'general'),
                                    'context': row.get('context', '')
                                })
                    return self._process_custom_glossary(glossary_data, source_lang, target_lang, confidence, validated)
                else:
                    logger.warning(f"Format de fichier non pris en charge: {file_path}")
                    return 0
        except Exception as e:
            logger.error(f"Erreur lors de l'import du glossaire: {e}")
            return 0
    
    def _process_json_glossary(self, data, source_lang, target_lang, confidence, validated):
        """Traite un glossaire au format JSON"""
        if isinstance(data, list):
            # Format type [{source_term, target_term, ...}, ...]
            return self._process_custom_glossary(data, source_lang, target_lang, confidence, validated)
        
        # Autres formats JSON possibles
        glossary_data = []
        
        # Format {terme1: traduction1, terme2: traduction2, ...}
        if all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()):
            for source, target in data.items():
                glossary_data.append({
                    'source_term': source,
                    'target_term': target,
                    'domain': 'general'
                })
            
            return self._process_custom_glossary(glossary_data, source_lang, target_lang, confidence, validated)
        
        logger.warning("Format JSON non reconnu")
        return 0
    
    def _process_custom_glossary(self, glossary_data, source_lang, target_lang, confidence, validated):
        """Traite un glossaire au format personnalisé"""
        count = 0
        with GlossaryManager(self.db_path) as gm:
            for entry in glossary_data:
                try:
                    source_term = entry.get('source_term')
                    target_term = entry.get('target_term')
                    domain = entry.get('domain', 'general')
                    context = entry.get('context', None)
                    
                    if source_term and target_term:
                        gm.add_term(
                            source_term=source_term,
                            source_lang=source_lang,
                            target_term=target_term,
                            target_lang=target_lang,
                            domain=domain,
                            context=context,
                            confidence=entry.get('confidence', confidence),
                            validated=entry.get('validated', validated)
                        )
                        count += 1
                except Exception as e:
                    logger.warning(f"Erreur lors de l'ajout du terme {entry.get('source_term')}: {e}")
                    continue
        
        return count
    
    def learn_from_translations(self, source_text, target_text, source_lang, target_lang, min_length=3, min_similarity=0.7):
        """Apprend de nouvelles traductions à partir de traductions existantes"""
        # Tokeniser simplement par espaces et ponctuations
        def tokenize(text):
            return re.findall(r'\b\w+\b', text.lower())
        
        source_tokens = tokenize(source_text)
        target_tokens = tokenize(target_text)
        
        # Pour les phrases courtes, essayer d'apprendre des mots individuels
        if len(source_tokens) <= 10 and len(target_tokens) <= 15:
            # Si les nombres de mots sont proches, tenter d'aligner
            if 0.7 <= len(target_tokens)/len(source_tokens) <= 1.5:
                learned_terms = []
                
                # Chercher des mots similaires (mêmes positions relatives)
                with GlossaryManager(self.db_path) as gm:
                    for i, s_token in enumerate(source_tokens):
                        if len(s_token) >= min_length:
                            # Déterminer les positions possibles dans la cible
                            start_pos = max(0, int(i * len(target_tokens) / len(source_tokens)) - 1)
                            end_pos = min(len(target_tokens), int((i+1) * len(target_tokens) / len(source_tokens)) + 1)
                            
                            # Chercher le terme existant pour confirmer
                            existing_terms = gm.search_term(s_token, source_lang, target_lang)
                            
                            if existing_terms:
                                # Terme déjà connu, confirmer ou améliorer la confiance
                                for term in existing_terms:
                                    for j in range(start_pos, end_pos):
                                        if j < len(target_tokens):
                                            if term['target_term'].lower() == target_tokens[j]:
                                                # Confirmation, augmenter confiance
                                                if term['confidence_score'] < 0.95:
                                                    gm.add_term(
                                                        s_token, source_lang, term['target_term'], 
                                                        target_lang, term['domain'],
                                                        confidence=min(0.95, term['confidence_score'] + 0.05),
                                                        validated=term['validated']
                                                    )
                                                    learned_terms.append((s_token, term['target_term'], "confirmé"))
                            else:
                                # Nouveau terme potentiel
                                for j in range(start_pos, end_pos):
                                    if j < len(target_tokens) and len(target_tokens[j]) >= min_length:
                                        # Ajouter comme terme potentiel avec confiance basse
                                        gm.add_term(
                                            s_token, source_lang, target_tokens[j], 
                                            target_lang, 'general',
                                            confidence=0.5,
                                            validated=False
                                        )
                                        learned_terms.append((s_token, target_tokens[j], "nouveau"))
                
                return learned_terms
        
        return []
    
    def extract_terms_from_article(self, article_data, source_lang, target_lang):
        """Extrait des termes d'un article traduit"""
        learned_terms = []
        
        # Parcourir toutes les sections
        for section in article_data.get('translated_sections', []):
            original_segments = section.get('original_segments', [])
            translated_segments = section.get('segments', [])
            
            # Traiter chaque paire de segments
            for orig, trans in zip(original_segments, translated_segments):
                if orig and trans and not trans.startswith('[ERREUR'):
                    terms = self.learn_from_translations(orig, trans, source_lang, target_lang)
                    learned_terms.extend(terms)
        
        return learned_terms
    
# Amélioration de src/database/glossary_learner.py


class EnhancedGlossaryLearner:
    """Version améliorée pour l'enrichissement du glossaire"""
    
    def __init__(self, db_path):
        """Initialise le GlossaryLearner avec le chemin vers la BDD"""
        self.db_path = db_path
    
    def learn_from_aligned_corpus(self, corpus_path, source_lang, target_lang, min_confidence=0.6):
        """
        Apprend des termes à partir d'un corpus parallèle aligné
        
        Args:
            corpus_path: Chemin vers le corpus TSV aligné
            source_lang: Code de la langue source
            target_lang: Code de la langue cible
            min_confidence: Confiance minimale pour l'ajout au glossaire
            
        Returns:
            Nombre de termes appris
        """
        import csv
        
        terms_added = 0
        try:
            with open(corpus_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter='\t')
                # Ignorer l'en-tête
                next(reader, None)
                
                # Traitement par lots
                batch_size = 100
                segments = []
                
                for row in reader:
                    if len(row) == 2:
                        segments.append((row[0], row[1]))
                    
                    if len(segments) >= batch_size:
                        terms = self._process_segment_batch(segments, source_lang, target_lang, min_confidence)
                        terms_added += len(terms)
                        segments = []
                
                # Traiter le dernier lot
                if segments:
                    terms = self._process_segment_batch(segments, source_lang, target_lang, min_confidence)
                    terms_added += len(terms)
            
            return terms_added
            
        except Exception as e:
            logger.error(f"Erreur lors de l'apprentissage depuis le corpus: {e}")
            return 0
    
    def _process_segment_batch(self, segments, source_lang, target_lang, min_confidence):
        """
        Traite un lot de segments pour en extraire des termes
        
        Args:
            segments: Liste de tuples (texte_source, texte_cible)
            source_lang: Code de la langue source
            target_lang: Code de la langue cible
            min_confidence: Confiance minimale
            
        Returns:
            Liste des termes appris
        """
        # Calcul des cooccurrences
        word_pairs = self._extract_potential_translations(segments)
        
        # Filtrer et ajouter au glossaire
        learned_terms = []
        
        with GlossaryManager(self.db_path) as gm:
            for (source_term, target_term), stats in word_pairs.items():
                # Calculer un score de confiance
                confidence = self._calculate_confidence_score(stats)
                
                if confidence >= min_confidence:
                    # Vérifier si le terme existe déjà
                    existing = gm.search_term(source_term, source_lang, target_lang)
                    
                    if existing:
                        # Terme existant avec meilleure confiance, ignorer
                        if any(term['confidence_score'] >= confidence for term in existing):
                            continue
                    
                    # Ajouter ou mettre à jour
                    gm.add_term(
                        source_term=source_term,
                        source_lang=source_lang,
                        target_term=target_term,
                        target_lang=target_lang,
                        domain='general',
                        confidence=confidence,
                        validated=False
                    )
                    
                    learned_terms.append((source_term, target_term, confidence))
        
        return learned_terms
    
    def _extract_potential_translations(self, segments):
        """
        Extrait des traductions potentielles de termes à partir de segments alignés
        
        Args:
            segments: Liste de tuples (texte_source, texte_cible)
            
        Returns:
            Dictionnaire {(terme_source, terme_cible): statistiques}
        """
        word_pairs = {}
        
        for source_text, target_text in segments:
            # Tokenisation simple
            source_tokens = self._tokenize(source_text)
            target_tokens = self._tokenize(target_text)
            
            # Générer des n-grammes
            source_ngrams = self._generate_ngrams(source_tokens, max_n=3)
            target_ngrams = self._generate_ngrams(target_tokens, max_n=3)
            
            # Analyser les cooccurrences
            for source_ngram in source_ngrams:
                for target_ngram in target_ngrams:
                    pair = (source_ngram, target_ngram)
                    
                    if pair not in word_pairs:
                        word_pairs[pair] = {
                            'count': 0,
                            'source_occurrences': 0,
                            'target_occurrences': 0,
                            'similarity': SequenceMatcher(None, source_ngram, target_ngram).ratio()
                        }
                    
                    word_pairs[pair]['count'] += 1
                    
            # Compter les occurrences individuelles
            for source_ngram in set(source_ngrams):
                for pair in word_pairs:
                    if pair[0] == source_ngram:
                        word_pairs[pair]['source_occurrences'] += 1
            
            for target_ngram in set(target_ngrams):
                for pair in word_pairs:
                    if pair[1] == target_ngram:
                        word_pairs[pair]['target_occurrences'] += 1
        
        return word_pairs
    
    def _tokenize(self, text):
        """Tokenisation améliorée avec gestion des caractères spéciaux"""
        # Préserver certains caractères spéciaux importants pour les langues ciblées
        text = text.lower()
        # Remplacer la ponctuation par des espaces
        text = re.sub(r'[^\w\s\u00E0-\u00FF\u0300-\u036F]', ' ', text)
        # Diviser en tokens et filtrer les tokens vides
        return [token for token in text.split() if token]
    
    def _generate_ngrams(self, tokens, max_n=3):
        """Génère des n-grammes à partir d'une liste de tokens"""
        ngrams = []
        
        for n in range(1, min(max_n + 1, len(tokens) + 1)):
            for i in range(len(tokens) - n + 1):
                ngram = ' '.join(tokens[i:i+n])
                ngrams.append(ngram)
        
        return ngrams
    
    def _calculate_confidence_score(self, stats):
        """
        Calcule un score de confiance pour une paire de termes
        
        Args:
            stats: Statistiques de la paire
            
        Returns:
            Score de confiance entre 0 et 1
        """
        # Facteurs considérés:
        # - Fréquence de cooccurrence
        # - Ratio de cooccurrence par rapport aux occurrences individuelles
        # - Similarité des chaînes
        
        count = stats['count']
        source_occurrences = max(1, stats['source_occurrences'])
        target_occurrences = max(1, stats['target_occurrences'])
        
        # Ratio de cooccurrence
        cooccurrence_ratio = count / max(source_occurrences, target_occurrences)
        
        # Similarité des chaînes (pour les cognats)
        string_similarity = stats['similarity']
        
        # Score combiné
        confidence = 0.4 * cooccurrence_ratio + 0.3 * (count / 10) + 0.3 * string_similarity
        
        # Normaliser entre 0 et 1
        return min(0.95, confidence)
    
# Ajouter cette classe dans src/database/glossary_learner.py

class EnhancedGlossaryLearner(GlossaryLearner):
    """Version améliorée du GlossaryLearner avec des fonctionnalités supplémentaires"""
    
    def learn_from_aligned_corpus(self, corpus_path, source_lang, target_lang, min_confidence=0.6):
        """
        Apprend des termes à partir d'un corpus parallèle aligné
        
        Args:
            corpus_path: Chemin vers le corpus TSV aligné
            source_lang: Code de la langue source
            target_lang: Code de la langue cible
            min_confidence: Confiance minimale pour l'ajout au glossaire
            
        Returns:
            Nombre de termes appris
        """
        import csv
        
        terms_added = 0
        try:
            with open(corpus_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter='\t')
                # Ignorer l'en-tête
                next(reader, None)
                
                # Traitement par lots
                batch_size = 100
                segments = []
                
                for row in reader:
                    if len(row) == 2:
                        segments.append((row[0], row[1]))
                    
                    if len(segments) >= batch_size:
                        terms = self._process_segment_batch(segments, source_lang, target_lang, min_confidence)
                        terms_added += len(terms)
                        segments = []
                
                # Traiter le dernier lot
                if segments:
                    terms = self._process_segment_batch(segments, source_lang, target_lang, min_confidence)
                    terms_added += len(terms)
            
            return terms_added
            
        except Exception as e:
            logger.error(f"Erreur lors de l'apprentissage depuis le corpus: {e}")
            return 0
    
    def _process_segment_batch(self, segments, source_lang, target_lang, min_confidence):
        """
        Traite un lot de segments pour en extraire des termes
        
        Args:
            segments: Liste de tuples (texte_source, texte_cible)
            source_lang: Code de la langue source
            target_lang: Code de la langue cible
            min_confidence: Confiance minimale
            
        Returns:
            Liste des termes appris
        """
        # Calcul des cooccurrences
        word_pairs = self._extract_potential_translations(segments)
        
        # Filtrer et ajouter au glossaire
        learned_terms = []
        
        with GlossaryManager(self.db_path) as gm:
            for (source_term, target_term), stats in word_pairs.items():
                # Calculer un score de confiance
                confidence = self._calculate_confidence_score(stats)
                
                if confidence >= min_confidence:
                    # Vérifier si le terme existe déjà
                    existing = gm.search_term(source_term, source_lang, target_lang)
                    
                    if existing:
                        # Terme existant avec meilleure confiance, ignorer
                        if any(term['confidence_score'] >= confidence for term in existing):
                            continue
                    
                    # Ajouter ou mettre à jour
                    gm.add_term(
                        source_term=source_term,
                        source_lang=source_lang,
                        target_term=target_term,
                        target_lang=target_lang,
                        domain='general',
                        confidence=confidence,
                        validated=False
                    )
                    
                    learned_terms.append((source_term, target_term, confidence))
        
        return learned_terms
    
    def _extract_potential_translations(self, segments):
        """
        Extrait des traductions potentielles de termes à partir de segments alignés
        
        Args:
            segments: Liste de tuples (texte_source, texte_cible)
            
        Returns:
            Dictionnaire {(terme_source, terme_cible): statistiques}
        """
        word_pairs = {}
        
        for source_text, target_text in segments:
            # Tokenisation simple
            source_tokens = self._tokenize(source_text)
            target_tokens = self._tokenize(target_text)
            
            # Générer des n-grammes
            source_ngrams = self._generate_ngrams(source_tokens, max_n=3)
            target_ngrams = self._generate_ngrams(target_tokens, max_n=3)
            
            # Analyser les cooccurrences
            for source_ngram in source_ngrams:
                for target_ngram in target_ngrams:
                    pair = (source_ngram, target_ngram)
                    
                    if pair not in word_pairs:
                        word_pairs[pair] = {
                            'count': 0,
                            'source_occurrences': 0,
                            'target_occurrences': 0,
                            'similarity': SequenceMatcher(None, source_ngram, target_ngram).ratio()
                        }
                    
                    word_pairs[pair]['count'] += 1
                    
            # Compter les occurrences individuelles
            for source_ngram in set(source_ngrams):
                for pair in word_pairs:
                    if pair[0] == source_ngram:
                        word_pairs[pair]['source_occurrences'] += 1
            
            for target_ngram in set(target_ngrams):
                for pair in word_pairs:
                    if pair[1] == target_ngram:
                        word_pairs[pair]['target_occurrences'] += 1
        
        return word_pairs
    
    def _tokenize(self, text):
        """Tokenisation améliorée avec gestion des caractères spéciaux"""
        # Préserver certains caractères spéciaux importants pour les langues ciblées
        text = text.lower()
        # Remplacer la ponctuation par des espaces
        text = re.sub(r'[^\w\s\u00E0-\u00FF\u0300-\u036F]', ' ', text)
        # Diviser en tokens et filtrer les tokens vides
        return [token for token in text.split() if token]
    
    def _generate_ngrams(self, tokens, max_n=3):
        """Génère des n-grammes à partir d'une liste de tokens"""
        ngrams = []
        
        for n in range(1, min(max_n + 1, len(tokens) + 1)):
            for i in range(len(tokens) - n + 1):
                ngram = ' '.join(tokens[i:i+n])
                ngrams.append(ngram)
        
        return ngrams
    
    def _calculate_confidence_score(self, stats):
        """
        Calcule un score de confiance pour une paire de termes
        
        Args:
            stats: Statistiques de la paire
            
        Returns:
            Score de confiance entre 0 et 1
        """
        # Facteurs considérés:
        # - Fréquence de cooccurrence
        # - Ratio de cooccurrence par rapport aux occurrences individuelles
        # - Similarité des chaînes
        
        count = stats['count']
        source_occurrences = max(1, stats['source_occurrences'])
        target_occurrences = max(1, stats['target_occurrences'])
        
        # Ratio de cooccurrence
        cooccurrence_ratio = count / max(source_occurrences, target_occurrences)
        
        # Similarité des chaînes (pour les cognats)
        string_similarity = stats['similarity']
        
        # Score combiné
        confidence = 0.4 * cooccurrence_ratio + 0.3 * (count / 10) + 0.3 * string_similarity
        
        # Normaliser entre 0 et 1
        return min(0.95, confidence)