#!/usr/bin/env python3
# src/adaptation/language_adapter.py

import os
import logging
from .orthographic_adapter import OrthographicAdapter
from .linguistic_adapter import LinguisticAdapter
from .named_entity_adapter import NamedEntityAdapter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LanguageAdapter:
    """Classe d'intégration pour l'adaptation linguistique des langues africaines"""
    
    def __init__(self, data_dir=None):
        """
        Initialise l'adaptateur linguistique intégré
        
        Args:
            data_dir: Répertoire de base pour les données linguistiques (optionnel)
        """
        self.data_dir = data_dir or os.path.join("data")
        
        # Initialiser les adaptateurs spécifiques
        self.orthographic = OrthographicAdapter(os.path.join(self.data_dir, "rules", "orthographic"))
        self.linguistic = LinguisticAdapter(os.path.join(self.data_dir, "rules", "linguistic"))
        self.entities = NamedEntityAdapter(os.path.join(self.data_dir, "entities"))
    
    def adapt_text(self, text, language, dialect=None, use_local_entities=True, apply_tones=False):
        """
        Adapte un texte selon les règles linguistiques d'une langue
        
        Args:
            text: Texte à adapter
            language: Code de la langue cible
            dialect: Dialecte spécifique (optionnel)
            use_local_entities: Utiliser les formes locales des entités nommées
            apply_tones: Appliquer les tons (si disponibles)
            
        Returns:
            Texte adapté
        """
        # 1. Normalisation orthographique
        normalized = self.orthographic.normalize_text(text, language, dialect)
        
        # 2. Remplacement des entités nommées
        with_entities = self.entities.replace_entities(normalized, language, use_local_entities)
        
        # 3. Application des tons (si demandée)
        if apply_tones:
            final_text = self._apply_tones_to_text(with_entities, language)
        else:
            final_text = with_entities
        
        return final_text
    
    def _apply_tones_to_text(self, text, language):
        """
        Applique les tons à un texte en se basant sur des règles simplifiées
        
        Args:
            text: Texte sans tons
            language: Code de la langue
            
        Returns:
            Texte avec tons (si possible)
        """
        # Cette implémentation est simplifiée. 
        # En pratique, l'application des tons nécessiterait une analyse linguistique plus complexe.
        
        # Pour l'instant, nous n'appliquons pas de tons mais indiquons l'opération
        logger.info(f"Application des tons pour la langue {language} (fonctionnalité à développer)")
        return text
    
    def detect_text_features(self, text, language):
        """
        Détecte les caractéristiques linguistiques d'un texte
        
        Args:
            text: Texte à analyser
            language: Code de la langue
            
        Returns:
            Dictionnaire des caractéristiques détectées
        """
        features = {
            "entities": self.entities.detect_entities(text, language),
            "word_count": len(text.split()),
            "char_count": len(text),
            "special_chars": self._count_special_chars(text, language),
            "dialect_features": self._detect_dialect(text, language)
        }
        
        return features
    
    def _count_special_chars(self, text, language):
        """
        Compte les caractères spéciaux spécifiques à une langue
        
        Args:
            text: Texte à analyser
            language: Code de la langue
            
        Returns:
            Dictionnaire des caractères spéciaux et leur nombre d'occurrences
        """
        rules = self.orthographic.load_rules(language)
        
        if not rules or 'special_characters' not in rules:
            return {}
        
        special_chars = rules['special_characters']
        counts = {}
        
        for char in special_chars:
            count = text.count(char)
            if count > 0:
                counts[char] = count
        
        return counts
    
    def _detect_dialect(self, text, language):
        """
        Détecte les caractéristiques dialectales dans un texte
        
        Args:
            text: Texte à analyser
            language: Code de la langue
            
        Returns:
            Dictionnaire des caractéristiques dialectales détectées
        """
        rules = self.orthographic.load_rules(language)
        
        if not rules or 'dialectal_variations' not in rules:
            return {}
        
        dialect_features = {}
        
        # Pour chaque dialecte, calculer un score de correspondance
        for dialect_info in rules['dialectal_variations']:
            dialect_name = dialect_info['dialect']
            score = 0
            features = []
            
            # Vérifier les variations spécifiques au dialecte
            for variation in dialect_info.get('variations', []):
                from_text = variation['from']
                to_text = variation['to']
                context = variation.get('context', 'all')
                
                # Détection simplifiée basée sur la présence de la forme variante
                if to_text in text:
                    score += 1
                    features.append(f"{from_text} → {to_text}")
            
            if score > 0:
                dialect_features[dialect_name] = {
                    "score": score,
                    "features": features
                }
        
        return dialect_features
    
    def list_supported_languages(self):
        """
        Liste les langues supportées par l'adaptateur
        
        Returns:
            Liste des langues supportées avec leurs descriptions
        """
        languages = {
            "fon": {
                "name": "Fon",
                "regions": ["Bénin"],
                "iso_code": "fon",
                "script": "Latin étendu",
                "features": ["tons", "classes nominales", "SVO"]
            },
            "dindi": {
                "name": "Dendi/Dindi",
                "regions": ["Bénin", "Niger", "Nigeria"],
                "iso_code": "ddn",
                "script": "Latin étendu",
                "features": ["tons", "SOV"]
            },
            "ewe": {
                "name": "Ewe",
                "regions": ["Ghana", "Togo"],
                "iso_code": "ee",
                "script": "Latin étendu",
                "features": ["tons", "SVO", "reduplication"]
            },
            "yor": {
                "name": "Yoruba",
                "regions": ["Nigeria", "Bénin"],
                "iso_code": "yo",
                "script": "Latin étendu",
                "features": ["tons", "SVO", "préfixes nominaux"]
            }
        }
        
        return languages
    
    def conjugate_verb(self, verb, language, tense='present', subject=None):
        """
        Conjugue un verbe dans la langue cible
        
        Args:
            verb: Verbe à conjuguer
            language: Code de la langue
            tense: Temps verbal ('present', 'past', 'future')
            subject: Sujet du verbe (optionnel)
            
        Returns:
            Verbe conjugué
        """
        return self.linguistic.conjugate_verb(verb, language, tense, subject)
    
    def build_phrase(self, subject, verb, object, language, tense='present'):
        """
        Construit une phrase selon les règles grammaticales de la langue
        
        Args:
            subject: Sujet de la phrase
            verb: Verbe
            object: Objet de la phrase
            language: Code de la langue
            tense: Temps verbal
            
        Returns:
            Phrase construite
        """
        return self.linguistic.build_sentence(subject, verb, object, language, tense)
    
    def get_noun_form(self, noun, language, is_plural=False):
        """
        Obtient la forme correcte d'un nom (singulier/pluriel)
        
        Args:
            noun: Nom à transformer
            language: Code de la langue
            is_plural: Booléen indiquant si le nom doit être au pluriel
            
        Returns:
            Nom transformé
        """
        return self.linguistic.apply_noun_class(noun, language, is_plural)
    
    def describe_noun(self, noun, adjective, language):
        """
        Combine un nom et un adjectif selon l'ordre correct
        
        Args:
            noun: Nom
            adjective: Adjectif
            language: Code de la langue
            
        Returns:
            Expression nom-adjectif correctement formée
        """
        return self.linguistic.apply_adjective(noun, adjective, language)
    
    def negate_sentence(self, sentence, language):
        """
        Met une phrase à la forme négative
        
        Args:
            sentence: Phrase à nier
            language: Code de la langue
            
        Returns:
            Phrase à la forme négative
        """
        return self.linguistic.apply_negation(sentence, language)
    
    def transliterate_name(self, name, language):
        """
        Translittère un nom propre selon les règles phonologiques
        
        Args:
            name: Nom à translittérer
            language: Langue cible
            
        Returns:
            Nom translittéré
        """
        return self.entities.transliterate_name(name, language)
    
    def add_custom_entity(self, category, original, local, language):
        """
        Ajoute une entité nommée personnalisée
        
        Args:
            category: Catégorie (people, places, etc.)
            original: Forme originale
            local: Forme locale/adaptée
            language: Code de la langue
            
        Returns:
            Booléen indiquant le succès de l'opération
        """
        return self.entities.add_entity(category, original, local, language)
    
    def detect_entities_in_text(self, text, language):
        """
        Détecte et extrait les entités nommées d'un texte
        
        Args:
            text: Texte à analyser
            language: Code de la langue
            
        Returns:
            Liste des entités détectées avec leur type
        """
        return self.entities.detect_entities(text, language)
    
    def apply_linguistic_rules(self, text, language, dialect=None):
        """
        Applique les règles linguistiques à un texte complet
        
        Args:
            text: Texte à adapter
            language: Code de la langue
            dialect: Dialecte spécifique (optionnel)
            
        Returns:
            Texte adapté linguistiquement
        """
        # Cette méthode applique une série de transformations linguistiques complexes
        # pour adapter un texte selon les règles grammaticales et culturelles de la langue cible
        
        paragraphs = text.split("\n\n")
        adapted_paragraphs = []
        
        for paragraph in paragraphs:
            # 1. Normalisation orthographique
            normalized = self.orthographic.normalize_text(paragraph, language, dialect)
            
            # 2. Remplacement des entités nommées
            with_entities = self.entities.replace_entities(normalized, language, True)
            
            # 3. Adaptation des structures syntaxiques (simplifiée ici)
            # En pratique, cela nécessiterait une analyse syntaxique plus profonde
            sentences = with_entities.split(". ")
            adapted_sentences = []
            
            for sentence in sentences:
                if not sentence.strip():
                    continue
                    
                # Simplification: nous ne modifions pas réellement la structure ici
                # Une implémentation complète nécessiterait une analyse grammaticale
                adapted_sentences.append(sentence)
            
            adapted_paragraph = ". ".join(adapted_sentences)
            if not adapted_paragraph.endswith('.') and len(adapted_paragraph) > 0:
                adapted_paragraph += '.'
                
            adapted_paragraphs.append(adapted_paragraph)
        
        return "\n\n".join(adapted_paragraphs)