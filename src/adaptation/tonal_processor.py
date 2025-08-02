#!/usr/bin/env python3
# src/adaptation/tonal_processor.py

import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ToneType(Enum):
    """Types de tons fondamentaux"""
    HIGH = "high"           # Ton haut (´)
    LOW = "low"            # Ton bas (`)
    MID = "mid"            # Ton moyen (-)
    RISING = "rising"      # Ton montant (ˇ)
    FALLING = "falling"    # Ton descendant (ˆ)
    EXTRA_HIGH = "extra_high"  # Ton extra-haut
    EXTRA_LOW = "extra_low"    # Ton extra-bas


@dataclass
class TonalWord:
    """Représente un mot avec ses informations tonales"""
    word: str
    base_form: str  # Forme sans diacritiques tonaux
    tones: List[ToneType]  # Séquence de tons
    syllables: List[str]   # Syllabes du mot
    language: str
    pos: Optional[str] = None  # Partie du discours


@dataclass
class SandhiRule:
    """Règle de sandhi tonal"""
    name: str
    context: str  # Contexte d'application (regex)
    tone_from: ToneType
    tone_to: ToneType
    position: str  # 'initial', 'final', 'medial', 'boundary'
    condition: Optional[str] = None  # Condition supplémentaire


class TonalProcessor:
    """Processeur tonal pour les langues africaines à tons"""
    
    def __init__(self, data_dir=None):
        """
        Initialise le processeur tonal
        
        Args:
            data_dir: Répertoire contenant les données tonales
        """
        self.data_dir = data_dir or "data/tonal"
        self.lexicons_dir = os.path.join(self.data_dir, "lexicons")
        self.rules_dir = os.path.join(self.data_dir, "sandhi_rules")
        
        # Cache des lexiques et règles chargés
        self.lexicons = {}
        self.sandhi_rules = {}
        
        # Marques diacritiques pour chaque type de ton
        self.tone_markers = {
            ToneType.HIGH: "́",      # accent aigu
            ToneType.LOW: "̀",       # accent grave
            ToneType.MID: "̄",       # macron
            ToneType.RISING: "̌",    # caron
            ToneType.FALLING: "̂",   # accent circonflexe
            ToneType.EXTRA_HIGH: "̋",
            ToneType.EXTRA_LOW: "̏"
        }
        
        # Voyelles communes dans les langues africaines
        self.vowels = set("aeiouɛɔẹọ")
        
        # Créer les répertoires nécessaires
        os.makedirs(self.lexicons_dir, exist_ok=True)
        os.makedirs(self.rules_dir, exist_ok=True)
        
        # Initialiser les données par défaut
        self._ensure_default_data()
    
    def _ensure_default_data(self):
        """Crée les données tonales par défaut si elles n'existent pas"""
        languages = ["fon", "yor", "ewe", "dindi"]
        
        for lang in languages:
            lexicon_file = os.path.join(self.lexicons_dir, f"{lang}_tonal_lexicon.json")
            rules_file = os.path.join(self.rules_dir, f"{lang}_sandhi_rules.json")
            
            if not os.path.exists(lexicon_file):
                self._create_default_lexicon(lang, lexicon_file)
            
            if not os.path.exists(rules_file):
                self._create_default_sandhi_rules(lang, rules_file)
    
    def _create_default_lexicon(self, language: str, file_path: str):
        """Crée un lexique tonal par défaut pour une langue"""
        lexicons = {
            "fon": self._get_fon_lexicon(),
            "yor": self._get_yoruba_lexicon(),
            "ewe": self._get_ewe_lexicon(),
            "dindi": self._get_dindi_lexicon()
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(lexicons.get(language, {}), f, ensure_ascii=False, indent=2)
            logger.info(f"Lexique tonal par défaut créé pour {language}")
        except Exception as e:
            logger.error(f"Erreur lors de la création du lexique tonal pour {language}: {e}")
    
    def _create_default_sandhi_rules(self, language: str, file_path: str):
        """Crée les règles de sandhi par défaut pour une langue"""
        rules = {
            "fon": self._get_fon_sandhi_rules(),
            "yor": self._get_yoruba_sandhi_rules(),
            "ewe": self._get_ewe_sandhi_rules(),
            "dindi": self._get_dindi_sandhi_rules()
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(rules.get(language, {}), f, ensure_ascii=False, indent=2)
            logger.info(f"Règles de sandhi par défaut créées pour {language}")
        except Exception as e:
            logger.error(f"Erreur lors de la création des règles de sandhi pour {language}: {e}")
    
    def _get_yoruba_lexicon(self) -> Dict:
        """Lexique tonal de base pour le yoruba"""
        return {
            "metadata": {
                "language": "yoruba",
                "tone_system": "3-level",  # haut, moyen, bas
                "description": "Lexique tonal de base pour le yoruba"
            },
            "words": {
                # Pronoms personnels
                "mo": {"tones": ["mid"], "syllables": ["mo"], "pos": "pronoun", "meaning": "je"},
                "ó": {"tones": ["high"], "syllables": ["ó"], "pos": "pronoun", "meaning": "il/elle"},
                "a": {"tones": ["mid"], "syllables": ["a"], "pos": "pronoun", "meaning": "nous"},
                "ẹ": {"tones": ["mid"], "syllables": ["ẹ"], "pos": "pronoun", "meaning": "vous"},
                "wọ́n": {"tones": ["high"], "syllables": ["wọ́n"], "pos": "pronoun", "meaning": "ils/elles"},
                
                # Verbes courants
                "jẹ": {"tones": ["mid"], "syllables": ["jẹ"], "pos": "verb", "meaning": "manger"},
                "lọ": {"tones": ["mid"], "syllables": ["lọ"], "pos": "verb", "meaning": "aller"},
                "wá": {"tones": ["high"], "syllables": ["wá"], "pos": "verb", "meaning": "venir"},
                "sọ": {"tones": ["mid"], "syllables": ["sọ"], "pos": "verb", "meaning": "dire"},
                "rí": {"tones": ["high"], "syllables": ["rí"], "pos": "verb", "meaning": "voir"},
                
                # Noms courants
                "ilé": {"tones": ["mid", "high"], "syllables": ["i", "lé"], "pos": "noun", "meaning": "maison"},
                "ọmọ": {"tones": ["mid", "mid"], "syllables": ["ọ", "mọ"], "pos": "noun", "meaning": "enfant"},
                "obì": {"tones": ["mid", "low"], "syllables": ["o", "bì"], "pos": "noun", "meaning": "cola"},
                "àgbà": {"tones": ["low", "low"], "syllables": ["à", "gbà"], "pos": "noun", "meaning": "ancien"},
                
                # Marqueurs grammaticaux
                "ti": {"tones": ["mid"], "syllables": ["ti"], "pos": "aux", "meaning": "passé"},
                "yóò": {"tones": ["high", "low"], "syllables": ["yó", "ò"], "pos": "aux", "meaning": "futur"},
                "ń": {"tones": ["high"], "syllables": ["ń"], "pos": "aux", "meaning": "présent"},
                
                # Adjectifs
                "dára": {"tones": ["mid", "mid"], "syllables": ["dá", "ra"], "pos": "adj", "meaning": "bon"},
                "pupa": {"tones": ["mid", "mid"], "syllables": ["pu", "pa"], "pos": "adj", "meaning": "rouge"},
                "funfun": {"tones": ["mid", "mid"], "syllables": ["fun", "fun"], "pos": "adj", "meaning": "blanc"}
            }
        }
    
    def _get_fon_lexicon(self) -> Dict:
        """Lexique tonal de base pour le fon"""
        return {
            "metadata": {
                "language": "fon",
                "tone_system": "3-level",
                "description": "Lexique tonal de base pour le fon"
            },
            "words": {
                # Pronoms personnels
                "un": {"tones": ["mid"], "syllables": ["un"], "pos": "pronoun", "meaning": "je"},
                "à": {"tones": ["low"], "syllables": ["à"], "pos": "pronoun", "meaning": "tu"},
                "é": {"tones": ["high"], "syllables": ["é"], "pos": "pronoun", "meaning": "il/elle"},
                "mí": {"tones": ["high"], "syllables": ["mí"], "pos": "pronoun", "meaning": "nous"},
                "yé": {"tones": ["high"], "syllables": ["yé"], "pos": "pronoun", "meaning": "ils/elles"},
                
                # Verbes courants
                "ɖu": {"tones": ["mid"], "syllables": ["ɖu"], "pos": "verb", "meaning": "manger"},
                "yi": {"tones": ["mid"], "syllables": ["yi"], "pos": "verb", "meaning": "aller"},
                "wá": {"tones": ["high"], "syllables": ["wá"], "pos": "verb", "meaning": "venir"},
                "ɖɔ": {"tones": ["mid"], "syllables": ["ɖɔ"], "pos": "verb", "meaning": "dire"},
                
                # Noms courants
                "xwé": {"tones": ["high"], "syllables": ["xwé"], "pos": "noun", "meaning": "maison"},
                "vi": {"tones": ["mid"], "syllables": ["vi"], "pos": "noun", "meaning": "enfant"},
                "àzɔ̀n": {"tones": ["low", "low"], "syllables": ["à", "zɔ̀n"], "pos": "noun", "meaning": "travail"},
                
                # Marqueurs temporels
                "kò": {"tones": ["low"], "syllables": ["kò"], "pos": "aux", "meaning": "passé"},
                "ná": {"tones": ["high"], "syllables": ["ná"], "pos": "aux", "meaning": "futur"}
            }
        }
    
    def _get_ewe_lexicon(self) -> Dict:
        """Lexique tonal de base pour l'ewe"""
        return {
            "metadata": {
                "language": "ewe",
                "tone_system": "2-level", # haut, bas
                "description": "Lexique tonal de base pour l'ewe"
            },
            "words": {
                # Pronoms personnels
                "me": {"tones": ["mid"], "syllables": ["me"], "pos": "pronoun", "meaning": "je"},
                "nè": {"tones": ["low"], "syllables": ["nè"], "pos": "pronoun", "meaning": "tu"},
                "é": {"tones": ["high"], "syllables": ["é"], "pos": "pronoun", "meaning": "il/elle"},
                
                # Verbes courants
                "ɖu": {"tones": ["mid"], "syllables": ["ɖu"], "pos": "verb", "meaning": "manger"},
                "yi": {"tones": ["mid"], "syllables": ["yi"], "pos": "verb", "meaning": "aller"},
                "va": {"tones": ["mid"], "syllables": ["va"], "pos": "verb", "meaning": "venir"},
                
                # Noms courants
                "aƒe": {"tones": ["mid", "mid"], "syllables": ["a", "ƒe"], "pos": "noun", "meaning": "maison"},
                "ame": {"tones": ["mid", "mid"], "syllables": ["a", "me"], "pos": "noun", "meaning": "personne"}
            }
        }
    
    def _get_dindi_lexicon(self) -> Dict:
        """Lexique tonal de base pour le dindi"""
        return {
            "metadata": {
                "language": "dindi", 
                "tone_system": "2-level",
                "description": "Lexique tonal de base pour le dindi"
            },
            "words": {
                # Pronoms personnels
                "ay": {"tones": ["mid"], "syllables": ["ay"], "pos": "pronoun", "meaning": "je"},
                "ni": {"tones": ["mid"], "syllables": ["ni"], "pos": "pronoun", "meaning": "tu"},
                "a": {"tones": ["mid"], "syllables": ["a"], "pos": "pronoun", "meaning": "il/elle"},
                
                # Verbes courants
                "tɛ": {"tones": ["mid"], "syllables": ["tɛ"], "pos": "verb", "meaning": "manger"},
                "koy": {"tones": ["mid"], "syllables": ["koy"], "pos": "verb", "meaning": "aller"}
            }
        }
    
    def _get_yoruba_sandhi_rules(self) -> Dict:
        """Règles de sandhi tonal pour le yoruba"""
        return {
            "language": "yoruba",
            "rules": [
                {
                    "name": "High-Low_Sequence",
                    "description": "Ton haut suivi d'un ton bas en contexte rapide",
                    "pattern": "HIGH + LOW",
                    "context": "rapid_speech",
                    "transformation": "HIGH -> MID / _LOW",
                    "examples": ["bá + bà -> bā bà"]
                },
                {
                    "name": "Tone_Spreading",
                    "description": "Propagation tonale sur les mots grammaticaux",
                    "pattern": "MID + FUNCTION_WORD",
                    "context": "grammatical",
                    "transformation": "MID spreads to function word",
                    "examples": ["mo + ni -> mo ni (même ton)"]
                },
                {
                    "name": "Boundary_Lowering",
                    "description": "Abaissement tonal aux frontières de phrase",
                    "pattern": "ANY -> LOW",
                    "context": "phrase_final",
                    "transformation": "final tone lowered",
                    "examples": ["wá -> wà (en fin de phrase)"]
                }
            ]
        }
    
    def _get_fon_sandhi_rules(self) -> Dict:
        """Règles de sandhi tonal pour le fon"""
        return {
            "language": "fon",
            "rules": [
                {
                    "name": "Tone_Assimilation",
                    "description": "Assimilation tonale entre mots adjacents",
                    "pattern": "LOW + HIGH",
                    "context": "word_boundary",
                    "transformation": "LOW -> MID / _HIGH",
                    "examples": ["kò + é -> kō é"]
                }
            ]
        }
    
    def _get_ewe_sandhi_rules(self) -> Dict:
        """Règles de sandhi tonal pour l'ewe"""
        return {
            "language": "ewe",
            "rules": [
                {
                    "name": "Downstep",
                    "description": "Abaissement graduel des tons hauts",
                    "pattern": "HIGH + HIGH",
                    "context": "sequence",
                    "transformation": "Second HIGH -> MID",
                    "examples": ["é + é -> é ē"]
                }
            ]
        }
    
    def _get_dindi_sandhi_rules(self) -> Dict:
        """Règles de sandhi tonal pour le dindi"""
        return {
            "language": "dindi",
            "rules": [
                {
                    "name": "Basic_Assimilation",
                    "description": "Assimilation tonale de base",
                    "pattern": "MID + LOW",
                    "context": "normal",
                    "transformation": "MID remains, LOW remains",
                    "examples": ["basic patterns"]
                }
            ]
        }
    
    def load_lexicon(self, language: str) -> Optional[Dict]:
        """Charge le lexique tonal pour une langue"""
        if language in self.lexicons:
            return self.lexicons[language]
        
        lexicon_file = os.path.join(self.lexicons_dir, f"{language}_tonal_lexicon.json")
        
        try:
            if os.path.exists(lexicon_file):
                with open(lexicon_file, 'r', encoding='utf-8') as f:
                    lexicon = json.load(f)
                self.lexicons[language] = lexicon
                logger.info(f"Lexique tonal chargé pour {language}")
                return lexicon
        except Exception as e:
            logger.error(f"Erreur lors du chargement du lexique tonal pour {language}: {e}")
        
        return None
    
    def load_sandhi_rules(self, language: str) -> Optional[Dict]:
        """Charge les règles de sandhi pour une langue"""
        if language in self.sandhi_rules:
            return self.sandhi_rules[language]
        
        rules_file = os.path.join(self.rules_dir, f"{language}_sandhi_rules.json")
        
        try:
            if os.path.exists(rules_file):
                with open(rules_file, 'r', encoding='utf-8') as f:
                    rules = json.load(f)
                self.sandhi_rules[language] = rules
                logger.info(f"Règles de sandhi chargées pour {language}")
                return rules
        except Exception as e:
            logger.error(f"Erreur lors du chargement des règles sandhi pour {language}: {e}")
        
        return None
    
    def extract_base_form(self, word: str) -> str:
        """Extrait la forme de base d'un mot en supprimant les diacritiques tonaux"""
        base_form = word
        for tone_marker in self.tone_markers.values():
            base_form = base_form.replace(tone_marker, "")
        return base_form
    
    def detect_tones(self, word: str) -> List[ToneType]:
        """Détecte les tons dans un mot à partir des diacritiques"""
        tones = []
        
        # Inverser le dictionnaire des marqueurs pour la détection
        marker_to_tone = {v: k for k, v in self.tone_markers.items()}
        
        for char in word:
            for marker, tone in marker_to_tone.items():
                if marker in char:
                    tones.append(tone)
                    break
        
        # Si aucun ton détecté, supposer tons moyens
        if not tones:
            syllable_count = self.count_syllables(word)
            tones = [ToneType.MID] * syllable_count
        
        return tones
    
    def count_syllables(self, word: str) -> int:
        """Compte approximativement le nombre de syllabes dans un mot"""
        vowel_count = 0
        prev_was_vowel = False
        
        clean_word = self.extract_base_form(word).lower()
        
        for char in clean_word:
            is_vowel = char in self.vowels
            if is_vowel and not prev_was_vowel:
                vowel_count += 1
            prev_was_vowel = is_vowel
        
        return max(1, vowel_count)  # Au moins une syllabe
    
    def apply_tone_to_word(self, base_word: str, tones: List[ToneType], language: str) -> str:
        """Applique des tons à un mot de base"""
        if not tones:
            return base_word
        
        result = list(base_word)
        vowel_index = 0
        
        for i, char in enumerate(result):
            if char.lower() in self.vowels and vowel_index < len(tones):
                tone = tones[vowel_index]
                if tone in self.tone_markers:
                    # Ajouter le diacritique tonal
                    result[i] = char + self.tone_markers[tone]
                vowel_index += 1
        
        return ''.join(result)
    
    def lookup_word_tones(self, word: str, language: str) -> Optional[TonalWord]:
        """Recherche les informations tonales d'un mot dans le lexique"""
        lexicon = self.load_lexicon(language)
        if not lexicon or 'words' not in lexicon:
            return None
        
        base_word = self.extract_base_form(word.lower())
        
        if base_word in lexicon['words']:
            word_data = lexicon['words'][base_word]
            
            # Convertir les strings de tons en ToneType
            tones = []
            for tone_str in word_data.get('tones', []):
                try:
                    tones.append(ToneType(tone_str))
                except ValueError:
                    tones.append(ToneType.MID)  # Par défaut
            
            return TonalWord(
                word=word,
                base_form=base_word,
                tones=tones,
                syllables=word_data.get('syllables', [base_word]),
                language=language,
                pos=word_data.get('pos')
            )
        
        return None
    
    def apply_sandhi_rules(self, words: List[TonalWord], language: str) -> List[TonalWord]:
        """Applique les règles de sandhi tonal à une séquence de mots"""
        rules = self.load_sandhi_rules(language)
        if not rules or not words:
            return words
        
        modified_words = words.copy()
        
        # Appliquer les règles séquentiellement
        for rule in rules.get('rules', []):
            rule_name = rule.get('name', '')
            pattern = rule.get('pattern', '')
            
            # Implémentation simplifiée de quelques règles courantes
            if 'HIGH + LOW' in pattern and len(modified_words) > 1:
                for i in range(len(modified_words) - 1):
                    curr_word = modified_words[i]
                    next_word = modified_words[i + 1]
                    
                    if (curr_word.tones and next_word.tones and
                        curr_word.tones[-1] == ToneType.HIGH and
                        next_word.tones[0] == ToneType.LOW):
                        
                        # Appliquer la règle: HIGH -> MID avant LOW
                        new_tones = curr_word.tones.copy()
                        new_tones[-1] = ToneType.MID
                        
                        modified_words[i] = TonalWord(
                            word=curr_word.word,
                            base_form=curr_word.base_form,
                            tones=new_tones,
                            syllables=curr_word.syllables,
                            language=curr_word.language,
                            pos=curr_word.pos
                        )
        
        return modified_words
    
    def process_text(self, text: str, language: str) -> str:
        """Traite un texte pour appliquer le système tonal approprié"""
        if not text.strip():
            return text
        
        # Séparer le texte en mots
        words = re.findall(r'\b\w+\b', text)
        non_words = re.split(r'\b\w+\b', text)
        
        # Traiter chaque mot
        tonal_words = []
        processed_words = []
        
        for word in words:
            tonal_word = self.lookup_word_tones(word, language)
            if tonal_word:
                tonal_words.append(tonal_word)
                # Appliquer les tons au mot
                processed_word = self.apply_tone_to_word(
                    tonal_word.base_form, 
                    tonal_word.tones, 
                    language
                )
                processed_words.append(processed_word)
            else:
                # Garder le mot tel quel si pas trouvé dans le lexique
                processed_words.append(word)
                # Créer un TonalWord par défaut
                syllables = self.count_syllables(word)
                default_tones = [ToneType.MID] * syllables
                tonal_words.append(TonalWord(
                    word=word,
                    base_form=self.extract_base_form(word),
                    tones=default_tones,
                    syllables=[word],
                    language=language
                ))
        
        # Appliquer les règles de sandhi
        if tonal_words:
            tonal_words = self.apply_sandhi_rules(tonal_words, language)
            
            # Reconstruire les mots avec les modifications de sandhi
            for i, tonal_word in enumerate(tonal_words):
                if i < len(processed_words):
                    processed_words[i] = self.apply_tone_to_word(
                        tonal_word.base_form,
                        tonal_word.tones,
                        language
                    )
        
        # Reconstruire le texte
        result = []
        for i in range(len(non_words)):
            if i < len(non_words):
                result.append(non_words[i])
            if i < len(processed_words):
                result.append(processed_words[i])
        
        return ''.join(result)
    
    def validate_tones(self, text: str, language: str) -> List[str]:
        """Valide les tons dans un texte et retourne les erreurs potentielles"""
        errors = []
        
        # Vérifications de base
        words = re.findall(r'\b\w+\b', text)
        
        for word in words:
            # Vérifier si le mot a des diacritiques tonaux incohérents
            tones = self.detect_tones(word)
            syllables = self.count_syllables(word)
            
            if len(tones) != syllables and tones:
                errors.append(f"Mot '{word}': nombre de tons ({len(tones)}) != nombre de syllabes ({syllables})")
            
            # Vérifier les séquences tonales impossibles (selon la langue)
            if language == "yoruba" and len(tones) > 1:
                for i in range(len(tones) - 1):
                    # Exemple de règle: éviter trop de tons hauts consécutifs
                    if (tones[i] == ToneType.HIGH and 
                        tones[i + 1] == ToneType.HIGH and 
                        i + 2 < len(tones) and 
                        tones[i + 2] == ToneType.HIGH):
                        errors.append(f"Mot '{word}': séquence de 3 tons hauts consécutifs inhabituelle")
        
        return errors
    
    def get_language_tone_info(self, language: str) -> Dict:
        """Retourne les informations sur le système tonal d'une langue"""
        lexicon = self.load_lexicon(language)
        if lexicon and 'metadata' in lexicon:
            return lexicon['metadata']
        
        # Informations par défaut
        return {
            "language": language,
            "tone_system": "unknown",
            "description": f"Informations tonales pour {language} non disponibles"
        }