#!/usr/bin/env python3
# src/adaptation/linguistic_adapter.py

import os
import json
import logging
import re
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LinguisticAdapter:
    """Classe pour le traitement des particularités linguistiques des langues africaines"""
    
    def __init__(self, rules_dir=None):
        """
        Initialise l'adaptateur linguistique
        
        Args:
            rules_dir: Répertoire contenant les règles linguistiques (optionnel)
        """
        self.rules_dir = rules_dir or os.path.join("data", "rules", "linguistic")
        self.rules_cache = {}  # Cache des règles chargées
        
        # Créer le répertoire des règles s'il n'existe pas
        os.makedirs(self.rules_dir, exist_ok=True)
        
        # Charger les règles prédéfinies si aucun fichier externe n'est disponible
        self._ensure_default_rules()
    
    def _ensure_default_rules(self):
        """Assure que des règles par défaut sont disponibles pour les langues cibles"""
        default_rules = {
            "fon": self._get_default_fon_rules(),
            "dindi": self._get_default_dindi_rules(),
            "ewe": self._get_default_ewe_rules(),
            "yor": self._get_default_yoruba_rules()
        }
        
        for lang, rules in default_rules.items():
            rules_file = os.path.join(self.rules_dir, f"{lang}_rules.json")
            
            if not os.path.exists(rules_file):
                try:
                    os.makedirs(os.path.dirname(rules_file), exist_ok=True)
                    with open(rules_file, 'w', encoding='utf-8') as f:
                        json.dump(rules, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"Règles linguistiques par défaut créées pour {lang}")
                except Exception as e:
                    logger.error(f"Erreur lors de la création des règles par défaut pour {lang}: {e}")
    
    def _get_default_fon_rules(self):
        """Renvoie les règles linguistiques par défaut pour le fon"""
        return {
            "name": "Règles linguistiques du Fon",
            "description": "Règles grammaticales et particularités du Fon (Bénin)",
            "noun_classes": [
                {
                    "name": "Personnes",
                    "singular_prefix": "",
                    "plural_prefix": "",
                    "singular_suffix": "",
                    "plural_suffix": "lɛ",
                    "examples": ["mɛ (personne)", "mɛlɛ (personnes)"]
                },
                {
                    "name": "Objets",
                    "singular_prefix": "",
                    "plural_prefix": "",
                    "singular_suffix": "",
                    "plural_suffix": "lɛ",
                    "examples": ["han (porte)", "hanlɛ (portes)"]
                }
            ],
            "verb_tenses": [
                {
                    "name": "Présent",
                    "marker": "",
                    "position": "none",
                    "examples": ["un ɖu (je mange)"]
                },
                {
                    "name": "Passé",
                    "marker": "kò",
                    "position": "before",
                    "examples": ["un kò ɖu (j'ai mangé)"]
                },
                {
                    "name": "Futur",
                    "marker": "ná",
                    "position": "before",
                    "examples": ["un ná ɖu (je mangerai)"]
                }
            ],
            "pronouns": {
                "personal": [
                    {"person": "1sg", "form": "un", "meaning": "je"},
                    {"person": "2sg", "form": "a", "meaning": "tu"},
                    {"person": "3sg", "form": "e", "meaning": "il/elle"},
                    {"person": "1pl", "form": "mí", "meaning": "nous"},
                    {"person": "2pl", "form": "mi", "meaning": "vous"},
                    {"person": "3pl", "form": "yé", "meaning": "ils/elles"}
                ],
                "possessive": [
                    {"person": "1sg", "form": "ce", "meaning": "mon/ma"},
                    {"person": "2sg", "form": "towe", "meaning": "ton/ta"},
                    {"person": "3sg", "form": "etɔn", "meaning": "son/sa"},
                    {"person": "1pl", "form": "mítɔn", "meaning": "notre"},
                    {"person": "2pl", "form": "mitɔn", "meaning": "votre"},
                    {"person": "3pl", "form": "yétɔn", "meaning": "leur"}
                ]
            },
            "word_order": "SVO",
            "adjective_position": "after_noun",
            "special_rules": [
                {
                    "name": "Négation",
                    "pattern": "a ... ǎ",
                    "examples": ["un ná jí ǎ (je ne viendrai pas)"]
                },
                {
                    "name": "Interrogation",
                    "pattern": "... a?",
                    "examples": ["a wa a? (es-tu venu?)"]
                }
            ]
        }
    
    def _get_default_dindi_rules(self):
        """Renvoie les règles linguistiques par défaut pour le dindi"""
        return {
            "name": "Règles linguistiques du Dindi",
            "description": "Règles grammaticales et particularités du Dindi (Bénin/Togo)",
            "noun_classes": [
                {
                    "name": "Général",
                    "singular_prefix": "",
                    "plural_prefix": "",
                    "singular_suffix": "",
                    "plural_suffix": "yo",
                    "examples": ["ɔzɔ (personne)", "ɔzɔyo (personnes)"]
                }
            ],
            "verb_tenses": [
                {
                    "name": "Présent",
                    "marker": "ga",
                    "position": "after",
                    "examples": ["a ga tɛ (tu manges)"]
                },
                {
                    "name": "Passé",
                    "marker": "na",
                    "position": "after",
                    "examples": ["a na tɛ (tu as mangé)"]
                },
                {
                    "name": "Futur",
                    "marker": "ga na",
                    "position": "after",
                    "examples": ["a ga na tɛ (tu mangeras)"]
                }
            ],
            "pronouns": {
                "personal": [
                    {"person": "1sg", "form": "ay", "meaning": "je"},
                    {"person": "2sg", "form": "ni", "meaning": "tu"},
                    {"person": "3sg", "form": "a", "meaning": "il/elle"},
                    {"person": "1pl", "form": "iri", "meaning": "nous"},
                    {"person": "2pl", "form": "wɔ", "meaning": "vous"},
                    {"person": "3pl", "form": "i", "meaning": "ils/elles"}
                ],
                "possessive": [
                    {"person": "1sg", "form": "ay", "meaning": "mon/ma"},
                    {"person": "2sg", "form": "ni", "meaning": "ton/ta"},
                    {"person": "3sg", "form": "nga", "meaning": "son/sa"},
                    {"person": "1pl", "form": "iri", "meaning": "notre"},
                    {"person": "2pl", "form": "wɔ", "meaning": "votre"},
                    {"person": "3pl", "form": "ngey", "meaning": "leur"}
                ]
            },
            "word_order": "SOV",
            "adjective_position": "after_noun",
            "special_rules": [
                {
                    "name": "Négation",
                    "pattern": "si ... wa",
                    "examples": ["ay si koy wa (je ne vais pas)"]
                }
            ]
        }
    
    def _get_default_ewe_rules(self):
        """Renvoie les règles linguistiques par défaut pour l'ewe"""
        return {
            "name": "Règles linguistiques de l'Ewe",
            "description": "Règles grammaticales et particularités de l'Ewe (Ghana/Togo)",
            "noun_classes": [
                {
                    "name": "Général",
                    "singular_prefix": "",
                    "plural_prefix": "",
                    "singular_suffix": "",
                    "plural_suffix": "wo",
                    "examples": ["ame (personne)", "amewo (personnes)"]
                }
            ],
            "verb_tenses": [
                {
                    "name": "Présent",
                    "marker": "le ... m",
                    "position": "surround",
                    "examples": ["me le nu ɖu m (je mange)"]
                },
                {
                    "name": "Passé",
                    "marker": "",
                    "position": "none",
                    "examples": ["me ɖu nu (j'ai mangé)"]
                },
                {
                    "name": "Futur",
                    "marker": "a",
                    "position": "before",
                    "examples": ["ma ɖu nu (je mangerai)"]
                }
            ],
            "pronouns": {
                "personal": [
                    {"person": "1sg", "form": "me", "meaning": "je"},
                    {"person": "2sg", "form": "nè", "meaning": "tu"},
                    {"person": "3sg", "form": "e", "meaning": "il/elle"},
                    {"person": "1pl", "form": "míe", "meaning": "nous"},
                    {"person": "2pl", "form": "mie", "meaning": "vous"},
                    {"person": "3pl", "form": "wo", "meaning": "ils/elles"}
                ],
                "possessive": [
                    {"person": "1sg", "form": "nye", "meaning": "mon/ma"},
                    {"person": "2sg", "form": "wò", "meaning": "ton/ta"},
                    {"person": "3sg", "form": "e", "meaning": "son/sa"},
                    {"person": "1pl", "form": "míaƒe", "meaning": "notre"},
                    {"person": "2pl", "form": "miaƒe", "meaning": "votre"},
                    {"person": "3pl", "form": "woƒe", "meaning": "leur"}
                ]
            },
            "word_order": "SVO",
            "adjective_position": "after_noun",
            "special_rules": [
                {
                    "name": "Négation",
                    "pattern": "me ... o",
                    "examples": ["nyemeyi o (je ne suis pas allé)"]
                },
                {
                    "name": "Reduplication",
                    "pattern": "repetition de la base verbale",
                    "examples": ["zɔzɔ (marcher beaucoup)"]
                }
            ]
        }
    
    def _get_default_yoruba_rules(self):
        """Renvoie les règles linguistiques par défaut pour le yoruba"""
        return {
            "name": "Règles linguistiques du Yoruba",
            "description": "Règles grammaticales et particularités du Yoruba (Nigeria/Bénin)",
            "noun_classes": [
                {
                    "name": "Général",
                    "singular_prefix": "",
                    "plural_prefix": "àwọn",
                    "singular_suffix": "",
                    "plural_suffix": "",
                    "examples": ["ọmọ (enfant)", "àwọn ọmọ (enfants)"]
                }
            ],
            "verb_tenses": [
                {
                    "name": "Présent",
                    "marker": "ń",
                    "position": "before",
                    "examples": ["mo ń jẹun (je mange)"]
                },
                {
                    "name": "Passé",
                    "marker": "ti",
                    "position": "before",
                    "examples": ["mo ti jẹun (j'ai mangé)"]
                },
                {
                    "name": "Futur",
                    "marker": "yóò",
                    "position": "before",
                    "examples": ["mo yóò jẹun (je mangerai)"]
                }
            ],
            "pronouns": {
                "personal": [
                    {"person": "1sg", "form": "mo/mi", "meaning": "je"},
                    {"person": "2sg", "form": "o/ìwọ", "meaning": "tu"},
                    {"person": "3sg", "form": "ó/òun", "meaning": "il/elle"},
                    {"person": "1pl", "form": "a/àwa", "meaning": "nous"},
                    {"person": "2pl", "form": "ẹ/ẹ̀yin", "meaning": "vous"},
                    {"person": "3pl", "form": "wọ́n/àwọn", "meaning": "ils/elles"}
                ],
                "possessive": [
                    {"person": "1sg", "form": "mi", "meaning": "mon/ma"},
                    {"person": "2sg", "form": "rẹ", "meaning": "ton/ta"},
                    {"person": "3sg", "form": "rẹ̀", "meaning": "son/sa"},
                    {"person": "1pl", "form": "wa", "meaning": "notre"},
                    {"person": "2pl", "form": "yín", "meaning": "votre"},
                    {"person": "3pl", "form": "wọn", "meaning": "leur"}
                ]
            },
            "word_order": "SVO",
            "adjective_position": "after_noun",
            "special_rules": [
                {
                    "name": "Négation",
                    "pattern": "kò/kì í",
                    "examples": ["n kò lọ (je ne suis pas allé)"]
                },
                {
                    "name": "Reduplication",
                    "pattern": "répétition totale ou partielle",
                    "examples": ["gbogbo (tout) -> gbogbogbo (tous)"]
                }
            ]
        }
    
    def load_rules(self, language):
        """
        Charge les règles linguistiques pour une langue
        
        Args:
            language: Code de la langue (fon, dindi, ewe, yor)
            
        Returns:
            Dictionnaire des règles ou None en cas d'erreur
        """
        # Vérifier le cache
        if language in self.rules_cache:
            return self.rules_cache[language]
        
        # Normaliser le code de langue
        lang_map = {
            "yoruba": "yor", "yo": "yor",
            "ee": "ewe",
            "fongbe": "fon",
            "dendi": "dindi", "ddn": "dindi"
        }
        
        norm_lang = lang_map.get(language.lower(), language.lower())
        
        # Chercher le fichier de règles
        rules_file = os.path.join(self.rules_dir, f"{norm_lang}_rules.json")
        
        try:
            if os.path.exists(rules_file):
                with open(rules_file, 'r', encoding='utf-8') as f:
                    rules = json.load(f)
                
                # Mettre en cache
                self.rules_cache[language] = rules
                self.rules_cache[norm_lang] = rules
                
                logger.info(f"Règles linguistiques chargées pour {language}")
                return rules
            else:
                logger.warning(f"Fichier de règles linguistiques introuvable pour {language}: {rules_file}")
                return None
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement des règles linguistiques pour {language}: {e}")
            return None
    
    def apply_noun_class(self, noun, language, is_plural=False):
        """
        Applique les règles de classe nominale à un nom
        
        Args:
            noun: Nom à transformer
            language: Code de la langue
            is_plural: Booléen indiquant si le nom doit être au pluriel
            
        Returns:
            Nom transformé
        """
        rules = self.load_rules(language)
        
        if not rules or 'noun_classes' not in rules:
            logger.warning(f"Règles de classes nominales non trouvées pour {language}")
            return noun
        
        # Par défaut, utiliser la première classe nominale
        noun_class = rules['noun_classes'][0]
        
        # Appliquer les préfixes et suffixes
        if is_plural:
            prefix = noun_class['plural_prefix']
            suffix = noun_class['plural_suffix']
        else:
            prefix = noun_class['singular_prefix']
            suffix = noun_class['singular_suffix']
        
        # Construire le nom
        if prefix:
            transformed_noun = f"{prefix} {noun}"
        else:
            transformed_noun = noun
        
        if suffix:
            transformed_noun = f"{transformed_noun}{suffix}"
        
        return transformed_noun
    
    def conjugate_verb(self, verb, language, tense, subject=None):
        """
        Conjugue un verbe selon les règles de la langue
        
        Args:
            verb: Verbe à conjuguer
            language: Code de la langue
            tense: Temps verbal ('present', 'past', 'future')
            subject: Sujet du verbe (optionnel)
            
        Returns:
            Verbe conjugué
        """
        rules = self.load_rules(language)
        
        if not rules or 'verb_tenses' not in rules:
            logger.warning(f"Règles de conjugaison non trouvées pour {language}")
            return verb
        
        # Normaliser le temps verbal
        tense_map = {
            'present': 'Présent',
            'past': 'Passé',
            'future': 'Futur'
        }
        
        norm_tense = tense_map.get(tense.lower(), tense)
        
        # Trouver le temps verbal correspondant
        verb_tense = None
        for vt in rules['verb_tenses']:
            if vt['name'] == norm_tense:
                verb_tense = vt
                break
        
        if not verb_tense:
            logger.warning(f"Temps verbal {tense} non trouvé pour {language}")
            return verb
        
        # Appliquer le marqueur de temps
        marker = verb_tense['marker']
        position = verb_tense['position']
        
        if position == 'before':
            conjugated_verb = f"{marker} {verb}"
        elif position == 'after':
            conjugated_verb = f"{verb} {marker}"
        elif position == 'surround' and ' ' in marker:
            marker_parts = marker.split(' ', 1)
            conjugated_verb = f"{marker_parts[0]} {verb} {marker_parts[1]}"
        else:
            conjugated_verb = verb
        
        # Appliquer le sujet si fourni
        if subject and rules.get('pronouns') and rules['pronouns'].get('personal'):
            pronouns = rules['pronouns']['personal']
            for pronoun in pronouns:
                if pronoun['meaning'].lower() == subject.lower() or pronoun['person'].lower() == subject.lower():
                    return f"{pronoun['form']} {conjugated_verb}"
        
        return conjugated_verb
    
    def build_sentence(self, subject, verb, object, language, tense='present'):
        """
        Construit une phrase selon l'ordre des mots de la langue
        
        Args:
            subject: Sujet de la phrase
            verb: Verbe
            object: Objet de la phrase
            language: Code de la langue
            tense: Temps verbal
            
        Returns:
            Phrase construite
        """
        rules = self.load_rules(language)
        
        if not rules or 'word_order' not in rules:
            logger.warning(f"Ordre des mots non trouvé pour {language}")
            return f"{subject} {verb} {object}"
        
        word_order = rules['word_order']
        
        # Conjuguer le verbe
        conjugated_verb = self.conjugate_verb(verb, language, tense, subject)
        
        # Construire la phrase selon l'ordre des mots
        if word_order == 'SVO':
            return f"{subject} {conjugated_verb} {object}"
        elif word_order == 'SOV':
            return f"{subject} {object} {conjugated_verb}"
        elif word_order == 'VSO':
            return f"{conjugated_verb} {subject} {object}"
        else:
            logger.warning(f"Ordre des mots non reconnu: {word_order}")
            return f"{subject} {conjugated_verb} {object}"
    
    def apply_adjective(self, noun, adjective, language):
        """
        Place l'adjectif correctement par rapport au nom selon les règles de la langue
        
        Args:
            noun: Nom
            adjective: Adjectif
            language: Code de la langue
            
        Returns:
            Expression nom-adjectif correctement formée
        """
        rules = self.load_rules(language)
        
        if not rules or 'adjective_position' not in rules:
            logger.warning(f"Position de l'adjectif non trouvée pour {language}")
            return f"{noun} {adjective}"
        
        adj_position = rules['adjective_position']
        
        if adj_position == 'after_noun':
            return f"{noun} {adjective}"
        elif adj_position == 'before_noun':
            return f"{adjective} {noun}"
        else:
            logger.warning(f"Position de l'adjectif non reconnue: {adj_position}")
            return f"{noun} {adjective}"
    
    def apply_negation(self, sentence, language):
        """
        Applique la négation à une phrase selon les règles de la langue
        
        Args:
            sentence: Phrase à mettre à la forme négative
            language: Code de la langue
            
        Returns:
            Phrase à la forme négative
        """
        rules = self.load_rules(language)
        
        if not rules or 'special_rules' not in rules:
            logger.warning(f"Règles de négation non trouvées pour {language}")
            return f"ne {sentence} pas"
        
        # Trouver la règle de négation
        negation_rule = None
        for rule in rules['special_rules']:
            if rule['name'] == 'Négation':
                negation_rule = rule
                break
        
        if not negation_rule:
            logger.warning(f"Règle de négation non trouvée pour {language}")
            return f"ne {sentence} pas"
        
        pattern = negation_rule['pattern']
        
        # Appliquer le modèle de négation
        if '...' in pattern:
            parts = pattern.split('...')
            return f"{parts[0]}{sentence}{parts[1]}"
        else:
            return f"{pattern} {sentence}"
    
    def get_pronoun(self, person, language, possessive=False):
        """
        Récupère un pronom personnel ou possessif dans la langue cible
        
        Args:
            person: Personne grammaticale (1sg, 2pl, etc.) ou description (je, tu, etc.)
            language: Code de la langue
            possessive: True pour les pronoms possessifs, False pour les personnels
            
        Returns:
            Pronom correspondant ou None si non trouvé
        """
        rules = self.load_rules(language)
        
        if not rules or 'pronouns' not in rules:
            logger.warning(f"Pronoms non trouvés pour {language}")
            return None
        
        pronoun_type = 'possessive' if possessive else 'personal'
        
        if pronoun_type not in rules['pronouns']:
            logger.warning(f"Pronoms {pronoun_type} non trouvés pour {language}")
            return None
        
        for pronoun in rules['pronouns'][pronoun_type]:
            if pronoun['person'] == person or pronoun['meaning'] == person:
                return pronoun['form']
        
        logger.warning(f"Pronom {person} non trouvé pour {language}")
        return None