#!/usr/bin/env python3
# src/adaptation/orthographic_adapter.py

import re
import logging
import json
import os
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OrthographicAdapter:
    """Classe pour l'adaptation orthographique des langues africaines"""
    
    def __init__(self, rules_dir=None):
        """
        Initialise l'adaptateur orthographique
        
        Args:
            rules_dir: Répertoire contenant les règles d'adaptation (optionnel)
        """
        self.rules_dir = rules_dir or os.path.join("data", "rules", "orthographic")
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
                    
                    logger.info(f"Règles orthographiques par défaut créées pour {lang}")
                except Exception as e:
                    logger.error(f"Erreur lors de la création des règles par défaut pour {lang}: {e}")
    
    def _get_default_fon_rules(self):
        """Renvoie les règles orthographiques par défaut pour le fon"""
        return {
            "name": "Règles orthographiques du Fon",
            "description": "Règles de normalisation pour le Fon (Bénin)",
            "tone_marks": {
                "high": "\u0301",  # Ton haut: á
                "low": "\u0300",   # Ton bas: à
                "mid": "",         # Ton moyen: pas de marque
                "rising": "\u030C", # Ton montant: ǎ
                "falling": "\u0302" # Ton descendant: â
            },
            "vowels": [
                {"base": "a", "variants": ["a", "â", "à", "á", "ǎ"]},
                {"base": "e", "variants": ["e", "ê", "è", "é", "ě"]},
                {"base": "ɛ", "variants": ["ɛ", "ɛ̂", "ɛ̀", "ɛ́", "ɛ̌"]},
                {"base": "i", "variants": ["i", "î", "ì", "í", "ǐ"]},
                {"base": "o", "variants": ["o", "ô", "ò", "ó", "ǒ"]},
                {"base": "ɔ", "variants": ["ɔ", "ɔ̂", "ɔ̀", "ɔ́", "ɔ̌"]},
                {"base": "u", "variants": ["u", "û", "ù", "ú", "ǔ"]}
            ],
            "nasal_marker": "\u0303",  # Tilde: ã
            "special_characters": ["ɖ", "ɛ", "ɔ", "ŋ", "ʋ", "ɣ"],
            "replacements": [
                {"from": "dh", "to": "ɖ"},
                {"from": "ny", "to": "ɲ"},
                {"from": "ng", "to": "ŋ"},
                {"from": "sh", "to": "ʃ"},
                {"from": "gb", "to": "gb"},
                {"from": "kp", "to": "kp"}
            ],
            "dialectal_variations": [
                {"dialect": "Abomey", "variations": [
                    {"from": "t", "to": "c", "context": "before_i"}
                ]},
                {"dialect": "Ouidah", "variations": [
                    {"from": "ɔ", "to": "o", "context": "word_final"}
                ]}
            ]
        }
    
    def _get_default_dindi_rules(self):
        """Renvoie les règles orthographiques par défaut pour le dindi"""
        return {
            "name": "Règles orthographiques du Dindi",
            "description": "Règles de normalisation pour le Dindi (Bénin/Togo)",
            "tone_marks": {
                "high": "\u0301",  # Ton haut: á
                "low": "\u0300",   # Ton bas: à
                "mid": "",         # Ton moyen: pas de marque
            },
            "vowels": [
                {"base": "a", "variants": ["a", "à", "á"]},
                {"base": "e", "variants": ["e", "è", "é"]},
                {"base": "ɛ", "variants": ["ɛ", "ɛ̀", "ɛ́"]},
                {"base": "i", "variants": ["i", "ì", "í"]},
                {"base": "o", "variants": ["o", "ò", "ó"]},
                {"base": "ɔ", "variants": ["ɔ", "ɔ̀", "ɔ́"]},
                {"base": "u", "variants": ["u", "ù", "ú"]}
            ],
            "nasal_marker": "\u0303",  # Tilde: ã
            "special_characters": ["ɖ", "ɛ", "ɔ", "ŋ"],
            "replacements": [
                {"from": "dh", "to": "ɖ"},
                {"from": "ng", "to": "ŋ"},
                {"from": "ny", "to": "ɲ"}
            ],
            "dialectal_variations": []
        }
    
    def _get_default_ewe_rules(self):
        """Renvoie les règles orthographiques par défaut pour l'ewe"""
        return {
            "name": "Règles orthographiques de l'Ewe",
            "description": "Règles de normalisation pour l'Ewe (Ghana/Togo)",
            "tone_marks": {
                "high": "\u0301",  # Ton haut: á
                "low": "\u0300",   # Ton bas: à
                "mid": "",         # Ton moyen: pas de marque
                "rising": "\u030C", # Ton montant: ǎ
                "falling": "\u0302" # Ton descendant: â
            },
            "vowels": [
                {"base": "a", "variants": ["a", "â", "à", "á", "ǎ"]},
                {"base": "e", "variants": ["e", "ê", "è", "é", "ě"]},
                {"base": "ɛ", "variants": ["ɛ", "ɛ̂", "ɛ̀", "ɛ́", "ɛ̌"]},
                {"base": "i", "variants": ["i", "î", "ì", "í", "ǐ"]},
                {"base": "o", "variants": ["o", "ô", "ò", "ó", "ǒ"]},
                {"base": "ɔ", "variants": ["ɔ", "ɔ̂", "ɔ̀", "ɔ́", "ɔ̌"]},
                {"base": "u", "variants": ["u", "û", "ù", "ú", "ǔ"]}
            ],
            "nasal_marker": "\u0303",  # Tilde: ã
            "special_characters": ["ɖ", "ɛ", "ɔ", "ŋ", "ƒ", "ʋ", "ɣ"],
            "replacements": [
                {"from": "dh", "to": "ɖ"},
                {"from": "f", "to": "ƒ", "context": "between_vowels"},
                {"from": "ny", "to": "ɲ"},
                {"from": "ng", "to": "ŋ"},
                {"from": "x", "to": "ɣ"},
                {"from": "v", "to": "ʋ"}
            ],
            "dialectal_variations": [
                {"dialect": "Anlo", "variations": [
                    {"from": "l", "to": "ɖ", "context": "word_initial"}
                ]},
                {"dialect": "Peki", "variations": [
                    {"from": "ƒ", "to": "f", "context": "all"}
                ]}
            ]
        }
    
    def _get_default_yoruba_rules(self):
        """Renvoie les règles orthographiques par défaut pour le yoruba"""
        return {
            "name": "Règles orthographiques du Yoruba",
            "description": "Règles de normalisation pour le Yoruba (Nigeria/Bénin)",
            "tone_marks": {
                "high": "\u0301",  # Ton haut: á
                "low": "\u0300",   # Ton bas: à
                "mid": "",         # Ton moyen: pas de marque
            },
            "vowels": [
                {"base": "a", "variants": ["a", "à", "á"]},
                {"base": "e", "variants": ["e", "è", "é"]},
                {"base": "ẹ", "variants": ["ẹ", "ẹ̀", "ẹ́"]},
                {"base": "i", "variants": ["i", "ì", "í"]},
                {"base": "o", "variants": ["o", "ò", "ó"]},
                {"base": "ọ", "variants": ["ọ", "ọ̀", "ọ́"]},
                {"base": "u", "variants": ["u", "ù", "ú"]}
            ],
            "nasal_marker": "\u0303",  # Tilde: ã
            "special_characters": ["ẹ", "ọ", "ṣ", "gb", "kp"],
            "replacements": [
                {"from": "sh", "to": "ṣ"},
                {"from": "e", "to": "ẹ", "context": "open_e"},
                {"from": "o", "to": "ọ", "context": "open_o"},
                {"from": "gb", "to": "gb"},
                {"from": "kp", "to": "kp"}
            ],
            "dialectal_variations": [
                {"dialect": "Oyo", "variations": [
                    {"from": "ẹ", "to": "e", "context": "word_final"}
                ]},
                {"dialect": "Ijebu", "variations": [
                    {"from": "ṣ", "to": "s", "context": "all"}
                ]}
            ]
        }
    
    def load_rules(self, language):
        """
        Charge les règles d'adaptation orthographique pour une langue
        
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
                
                logger.info(f"Règles orthographiques chargées pour {language}")
                return rules
            else:
                logger.warning(f"Fichier de règles introuvable pour {language}: {rules_file}")
                return None
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement des règles pour {language}: {e}")
            return None
    
    def normalize_text(self, text, language, dialect=None):
        """
        Normalise un texte selon les règles orthographiques d'une langue
        
        Args:
            text: Texte à normaliser
            language: Code de la langue
            dialect: Dialecte spécifique (optionnel)
            
        Returns:
            Texte normalisé
        """
        rules = self.load_rules(language)
        
        if not rules:
            logger.warning(f"Aucune règle trouvée pour {language}, texte non modifié")
            return text
        
        normalized_text = text
        
        # Appliquer les remplacements de base
        for replacement in rules.get('replacements', []):
            from_text = replacement['from']
            to_text = replacement['to']
            context = replacement.get('context', 'all')
            
            if context == 'all':
                normalized_text = normalized_text.replace(from_text, to_text)
            elif context == 'word_initial':
                normalized_text = re.sub(r'\b' + from_text, to_text, normalized_text)
            elif context == 'word_final':
                normalized_text = re.sub(from_text + r'\b', to_text, normalized_text)
            elif context == 'between_vowels':
                vowels = ''.join([v['base'] for v in rules.get('vowels', [])])
                pattern = f"([{vowels}]){from_text}([{vowels}])"
                replacement = f"\\1{to_text}\\2"
                normalized_text = re.sub(pattern, replacement, normalized_text)
        
        # Appliquer les variations dialectales si spécifiées
        if dialect and 'dialectal_variations' in rules:
            for dialect_info in rules['dialectal_variations']:
                if dialect_info['dialect'].lower() == dialect.lower():
                    for variation in dialect_info.get('variations', []):
                        from_text = variation['from']
                        to_text = variation['to']
                        context = variation.get('context', 'all')
                        
                        if context == 'all':
                            normalized_text = normalized_text.replace(from_text, to_text)
                        elif context == 'word_initial':
                            normalized_text = re.sub(r'\b' + from_text, to_text, normalized_text)
                        elif context == 'word_final':
                            normalized_text = re.sub(from_text + r'\b', to_text, normalized_text)
        
        return normalized_text
    
    def add_tones(self, text, language, tone_pattern):
        """
        Ajoute des tons à un texte selon un schéma spécifié
        
        Args:
            text: Texte sans tons
            language: Code de la langue
            tone_pattern: Séquence de tons à appliquer ('H'=haut, 'L'=bas, 'M'=moyen, 'R'=montant, 'F'=descendant)
            
        Returns:
            Texte avec tons
        """
        rules = self.load_rules(language)
        
        if not rules or 'tone_marks' not in rules or 'vowels' not in rules:
            logger.warning(f"Règles de tonalité non trouvées pour {language}")
            return text
        
        # Extraire les voyelles et les marques de ton
        vowels = []
        for vowel_info in rules['vowels']:
            vowels.extend(vowel_info['variants'])
            vowels.append(vowel_info['base'])
        
        tone_marks = {
            'H': rules['tone_marks']['high'],
            'L': rules['tone_marks']['low'],
            'M': rules['tone_marks']['mid'],
            'R': rules['tone_marks'].get('rising', ''),
            'F': rules['tone_marks'].get('falling', '')
        }
        
        # Convertir le texte en liste de caractères pour faciliter la modification
        chars = list(text)
        vowel_positions = []
        
        # Identifier les positions des voyelles
        for i, char in enumerate(chars):
            if char.lower() in vowels:
                vowel_positions.append(i)
        
        # Appliquer les tons selon le modèle
        for i, pos in enumerate(vowel_positions):
            if i < len(tone_pattern):
                tone = tone_pattern[i].upper()
                if tone in tone_marks:
                    chars[pos] = chars[pos] + tone_marks[tone]
        
        return ''.join(chars)
    
    def extract_tones(self, text, language):
        """
        Extrait les tons d'un texte
        
        Args:
            text: Texte avec tons
            language: Code de la langue
            
        Returns:
            Tuple (texte sans tons, séquence de tons)
        """
        rules = self.load_rules(language)
        
        if not rules or 'tone_marks' not in rules:
            logger.warning(f"Règles de tonalité non trouvées pour {language}")
            return (text, "")
        
        tone_marks_inverse = {
            rules['tone_marks']['high']: 'H',
            rules['tone_marks']['low']: 'L',
            rules['tone_marks']['mid']: 'M'
        }
        
        if 'rising' in rules['tone_marks']:
            tone_marks_inverse[rules['tone_marks']['rising']] = 'R'
        
        if 'falling' in rules['tone_marks']:
            tone_marks_inverse[rules['tone_marks']['falling']] = 'F'
        
        # Analyser le texte pour extraire les tons
        normalized_text = ""
        tone_sequence = ""
        
        i = 0
        while i < len(text):
            char = text[i]
            normalized_text += char
            
            # Vérifier si le caractère suivant est une marque de ton
            if i + 1 < len(text) and text[i+1] in tone_marks_inverse:
                tone = tone_marks_inverse[text[i+1]]
                tone_sequence += tone
                i += 2  # Sauter la marque de ton
            else:
                # Aucune marque de ton, donc ton moyen par défaut
                if char.lower() in ''.join([v['base'] for v in rules.get('vowels', [])]):
                    tone_sequence += 'M'
                i += 1
        
        return (normalized_text, tone_sequence)
    
    def convert_latin_script(self, text, source_script, target_language):
        """
        Convertit un texte d'un script latin général vers l'orthographe spécifique d'une langue
        
        Args:
            text: Texte à convertir
            source_script: Script source (ex: 'latin_general')
            target_language: Langue cible avec orthographe spécifique
            
        Returns:
            Texte converti
        """
        rules = self.load_rules(target_language)
        
        if not rules:
            logger.warning(f"Aucune règle trouvée pour {target_language}, texte non modifié")
            return text
        
        converted_text = text
        
        # Appliquer les règles de conversion
        for replacement in rules.get('replacements', []):
            from_text = replacement['from']
            to_text = replacement['to']
            context = replacement.get('context', 'all')
            
            if context == 'all':
                converted_text = converted_text.replace(from_text, to_text)
            elif context == 'word_initial':
                converted_text = re.sub(r'\b' + from_text, to_text, converted_text)
            elif context == 'word_final':
                converted_text = re.sub(from_text + r'\b', to_text, converted_text)
            elif context == 'between_vowels':
                vowels = ''.join([v['base'] for v in rules.get('vowels', [])])
                pattern = f"([{vowels}]){from_text}([{vowels}])"
                replacement = f"\\1{to_text}\\2"
                converted_text = re.sub(pattern, replacement, converted_text)
        
        return converted_text
    
    def save_rules(self, language, rules):
        """
        Sauvegarde les règles d'adaptation pour une langue
        
        Args:
            language: Code de la langue
            rules: Dictionnaire des règles
            
        Returns:
            Booléen indiquant le succès de l'opération
        """
        # Normaliser le code de langue
        lang_map = {
            "yoruba": "yor", "yo": "yor",
            "ee": "ewe",
            "fongbe": "fon",
            "dendi": "dindi", "ddn": "dindi"
        }
        
        norm_lang = lang_map.get(language.lower(), language.lower())
        
        # Chemin du fichier de règles
        rules_file = os.path.join(self.rules_dir, f"{norm_lang}_rules.json")
        
        try:
            # Créer le répertoire si nécessaire
            os.makedirs(os.path.dirname(rules_file), exist_ok=True)
            
            # Sauvegarder les règles
            with open(rules_file, 'w', encoding='utf-8') as f:
                json.dump(rules, f, ensure_ascii=False, indent=2)
            
            # Mettre à jour le cache
            self.rules_cache[language] = rules
            self.rules_cache[norm_lang] = rules
            
            logger.info(f"Règles orthographiques sauvegardées pour {language}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des règles pour {language}: {e}")
            return False