# -*- coding: utf-8 -*-
# src/translation/term_protection.py

import re
import json
import logging
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

class ProtectionType(Enum):
    """Types de protection pour les termes"""
    TECHNICAL = "technical"        # Termes techniques (API, URL, etc.)
    PROPER_NOUN = "proper_noun"    # Noms propres (noms de personnes, lieux)
    NUMERICAL = "numerical"        # Donnees numeriques
    CODE = "code"                  # Code informatique
    FORMULA = "formula"            # Formules mathematiques
    CULTURAL = "cultural"          # Termes culturels specifiques
    CURRENCY = "currency"          # Devises et montants

@dataclass
class ProtectedTerm:
    """Representation d'un terme protege"""
    original: str
    placeholder: str
    protection_type: ProtectionType
    confidence: float = 1.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class TermProtectionManager:
    """Gestionnaire de protection des termes techniques et culturels"""
    
    def __init__(self, custom_terms_file: str = None):
        """
        Initialise le gestionnaire de protection des termes
        
        Args:
            custom_terms_file: Fichier JSON avec termes personnalises
        """
        self.protected_terms: Dict[str, ProtectedTerm] = {}
        self.reverse_mapping: Dict[str, str] = {}  # placeholder -> original
        self.term_counter = 0
        
        # Patterns de detection automatique
        self.patterns = {
            ProtectionType.TECHNICAL: [
                r'\b(?:API|HTTP|HTTPS|URL|JSON|XML|HTML|CSS|SQL|REST|SOAP)\b',
                r'\b(?:GitHub|Wikipedia|Google|Microsoft|OpenAI)\b',
                r'\b\w+\.(com|org|net|edu|gov)\b',
                r'\b(?:www\.)\w+\.\w+\b'
            ],
            ProtectionType.PROPER_NOUN: [
                r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Noms avec majuscules
                r'\b(?:M\.|Mme\.?|Dr\.?|Prof\.?)\s+[A-Z][a-z]+\b'  # Titres + noms
            ],
            ProtectionType.NUMERICAL: [
                r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:%|percent|pourcentage)\b',
                r'\b\d+(?:\.\d+)?\s*(?:km|m|cm|mm|kg|g|l|ml)\b',
                r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',  # Dates
                r'\b\d{1,2}:\d{2}(?::\d{2})?\b'      # Heures
            ],
            ProtectionType.CODE: [
                r'`[^`]+`',                           # Code inline
                r'```[\s\S]*?```',                    # Blocs de code
                r'\b(?:def|class|import|from|return|if|else|for|while)\s+\w+',
                r'\b\w+\(\s*\w*\s*\)'                # Appels de fonction
            ],
            ProtectionType.FORMULA: [
                r'\$[^$]+\$',                         # LaTeX math inline
                r'\$\$[\s\S]*?\$\$',                  # LaTeX math block
                r'\b[a-zA-Z]\s*=\s*[a-zA-Z0-9+\-*/()]+\b'  # Equations simples
            ],
            ProtectionType.CURRENCY: [
                r'\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:\$|USD|EUR|GBP|CFA|FCFA)\b',
                r'\b(?:\$|USD|EUR|GBP)\s*\d+(?:,\d{3})*(?:\.\d{2})?\b'
            ]
        }
        
        # Termes culturels africains a proteger
        self.african_cultural_terms = {
            'fon': [
                'vodun', 'legba', 'mami wata', 'dahomey', 'abomey', 'ouidah',
                'agassu', 'sakpata', 'heviesso', 'dan', 'agbo', 'bo'
            ],
            'yoruba': [
                'orisha', 'ifa', 'ogun', 'shango', 'yemoja', 'oshun', 'obatala',
                'egungun', 'ori', 'ase', 'iyalocha', 'babalocha', 'ile-ife'
            ],
            'ewe': [
                'vodu', 'trowo', 'afa', 'legba', 'sogbo', 'nyigbla',
                'mawu', 'lisa', 'gbetsi', 'amedzro', 'dufia'
            ],
            'dindi': [
                'zima', 'holle', 'borey', 'gourma', 'zarma', 'songhai'
            ]
        }
        
        # Charger termes personnalises
        if custom_terms_file:
            self._load_custom_terms(custom_terms_file)
        
        logger.info("Gestionnaire de protection des termes initialise")
    
    def protect_text(self, text: str, target_language: str = None) -> Tuple[str, Dict[str, ProtectedTerm]]:
        """
        Protege les termes dans un texte avant traduction
        
        Args:
            text: Texte a proteger
            target_language: Langue cible pour protection culturelle
        
        Returns:
            Tuple (texte_protege, mapping_des_termes)
        """
        if not text:
            return text, {}
        
        protected_text = text
        current_terms = {}
        
        # Protection par patterns automatiques
        for protection_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = list(re.finditer(pattern, protected_text, re.IGNORECASE))
                
                for match in reversed(matches):  # Inverser pour preserver positions
                    original_term = match.group(0)
                    
                    # Eviter de proteger les termes deja proteges
                    if self._is_already_protected(original_term):
                        continue
                    
                    placeholder = self._generate_placeholder(protection_type)
                    protected_term = ProtectedTerm(
                        original=original_term,
                        placeholder=placeholder,
                        protection_type=protection_type,
                        confidence=0.8,
                        metadata={'pattern': pattern, 'position': match.start()}
                    )
                    
                    current_terms[placeholder] = protected_term
                    self.reverse_mapping[placeholder] = original_term
                    
                    # Remplacer dans le texte
                    protected_text = (protected_text[:match.start()] + 
                                    placeholder + 
                                    protected_text[match.end():])
        
        # Protection culturelle specifique
        if target_language:
            protected_text, cultural_terms = self._protect_cultural_terms(
                protected_text, target_language
            )
            current_terms.update(cultural_terms)
        
        # Protection des entites nommees detectees
        protected_text, named_entities = self._protect_named_entities(protected_text)
        current_terms.update(named_entities)
        
        logger.info(f"Termes proteges: {len(current_terms)} dans {len(text)} caracteres")
        return protected_text, current_terms
    
    def restore_text(self, translated_text: str, protected_terms: Dict[str, ProtectedTerm]) -> str:
        """
        Restaure les termes proteges dans le texte traduit
        
        Args:
            translated_text: Texte traduit avec placeholders
            protected_terms: Mapping des termes proteges
        
        Returns:
            Texte avec termes originaux restaures
        """
        if not translated_text or not protected_terms:
            return translated_text
        
        restored_text = translated_text
        restoration_count = 0
        
        # Trier par longueur decroissante pour eviter les remplacements partiels
        sorted_placeholders = sorted(protected_terms.keys(), key=len, reverse=True)
        
        for placeholder in sorted_placeholders:
            if placeholder in restored_text:
                protected_term = protected_terms[placeholder]
                original_term = protected_term.original
                
                # Appliquer des transformations intelligentes
                restored_term = self._apply_restoration_rules(
                    original_term, protected_term, restored_text
                )
                
                restored_text = restored_text.replace(placeholder, restored_term)
                restoration_count += 1
        
        logger.info(f"Termes restaures: {restoration_count}/{len(protected_terms)}")
        return restored_text
    
    def _protect_cultural_terms(self, text: str, target_language: str) -> Tuple[str, Dict[str, ProtectedTerm]]:
        """
        Protege les termes culturels specifiques a une langue
        
        Args:
            text: Texte a proteger
            target_language: Langue cible
        
        Returns:
            Tuple (texte_protege, termes_culturels)
        """
        cultural_terms = {}
        protected_text = text
        
        # Obtenir les termes culturels pour cette langue
        terms_to_protect = []
        
        # Termes de la langue cible (a ne pas traduire)
        if target_language in self.african_cultural_terms:
            terms_to_protect.extend(self.african_cultural_terms[target_language])
        
        # Termes de toutes les langues africaines (contexte culturel)
        for lang_terms in self.african_cultural_terms.values():
            terms_to_protect.extend(lang_terms)
        
        # Dedupliquer
        terms_to_protect = list(set(terms_to_protect))
        
        for term in terms_to_protect:
            # Recherche insensible a la casse avec limites de mots
            pattern = r'\b' + re.escape(term) + r'\b'
            matches = list(re.finditer(pattern, protected_text, re.IGNORECASE))
            
            for match in reversed(matches):
                original_term = match.group(0)
                placeholder = self._generate_placeholder(ProtectionType.CULTURAL)
                
                protected_term = ProtectedTerm(
                    original=original_term,
                    placeholder=placeholder,
                    protection_type=ProtectionType.CULTURAL,
                    confidence=0.9,
                    metadata={
                        'cultural_context': target_language,
                        'term_category': 'african_heritage'
                    }
                )
                
                cultural_terms[placeholder] = protected_term
                self.reverse_mapping[placeholder] = original_term
                
                protected_text = (protected_text[:match.start()] + 
                                placeholder + 
                                protected_text[match.end():])
        
        return protected_text, cultural_terms
    
    def _protect_named_entities(self, text: str) -> Tuple[str, Dict[str, ProtectedTerm]]:
        """
        Protege les entites nommees detectees
        
        Args:
            text: Texte a analyser
        
        Returns:
            Tuple (texte_protege, entites_nommees)
        """
        named_entities = {}
        protected_text = text
        
        # Patterns pour detecter les entites nommees
        entity_patterns = [
            # Noms de lieux africains
            r'\b(?:Benin|Nigeria|Togo|Ghana|Burkina\s+Faso|Mali|Niger|Senegal)\b',
            r'\b(?:Cotonou|Lagos|Abuja|Accra|Lome|Ouagadougou|Bamako|Niamey|Dakar)\b',
            r'\b(?:Porto-Novo|Kano|Ibadan|Kumasi|Sokoto|Zaria|Kaduna)\b',
            
            # Noms de personnalites
            r'\b(?:Behanzin|Glele|Agaja|Tegbesu|Agonglo)\b',  # Rois du Dahomey
            r'\b(?:Felix\s+Houphouet-Boigny|Kwame\s+Nkrumah|Patrice\s+Lumumba)\b',
            
            # Organisations
            r'\b(?:CEDEAO|ECOWAS|UNESCO|ONU|UA|AU)\b',
            r'\b(?:Universite\s+\w+|University\s+of\s+\w+)\b'
        ]
        
        for pattern in entity_patterns:
            matches = list(re.finditer(pattern, protected_text, re.IGNORECASE))
            
            for match in reversed(matches):
                original_term = match.group(0)
                
                if self._is_already_protected(original_term):
                    continue
                
                placeholder = self._generate_placeholder(ProtectionType.PROPER_NOUN)
                
                protected_term = ProtectedTerm(
                    original=original_term,
                    placeholder=placeholder,
                    protection_type=ProtectionType.PROPER_NOUN,
                    confidence=0.85,
                    metadata={'entity_type': 'named_entity', 'pattern': pattern}
                )
                
                named_entities[placeholder] = protected_term
                self.reverse_mapping[placeholder] = original_term
                
                protected_text = (protected_text[:match.start()] + 
                                placeholder + 
                                protected_text[match.end():])
        
        return protected_text, named_entities
    
    def _generate_placeholder(self, protection_type: ProtectionType) -> str:
        """
        Generate un placeholder unique pour un type de protection
        
        Args:
            protection_type: Type de protection
        
        Returns:
            Placeholder unique
        """
        self.term_counter += 1
        type_prefix = {
            ProtectionType.TECHNICAL: "TECH",
            ProtectionType.PROPER_NOUN: "NAME", 
            ProtectionType.NUMERICAL: "NUM",
            ProtectionType.CODE: "CODE",
            ProtectionType.FORMULA: "FORM",
            ProtectionType.CULTURAL: "CULT",
            ProtectionType.CURRENCY: "CURR"
        }
        
        prefix = type_prefix.get(protection_type, "TERM")
        return f"__{prefix}_{self.term_counter:04d}__"
    
    def _is_already_protected(self, term: str) -> bool:
        """
        Verifie si un terme est deja protege
        
        Args:
            term: Terme a verifier
        
        Returns:
            True si deja protege
        """
        return term.startswith("__") and term.endswith("__")
    
    def _apply_restoration_rules(self, original_term: str, protected_term: ProtectedTerm, context: str) -> str:
        """
        Applique des regles intelligentes pour la restauration
        
        Args:
            original_term: Terme original
            protected_term: Terme protege avec metadata
            context: Contexte du texte traduit
        
        Returns:
            Terme a restaurer (potentiellement modifie)
        """
        restored_term = original_term
        
        # Regles specifiques par type
        if protected_term.protection_type == ProtectionType.CULTURAL:
            # Les termes culturels restent identiques
            restored_term = original_term
            
        elif protected_term.protection_type == ProtectionType.PROPER_NOUN:
            # Preserver la casse des noms propres
            restored_term = original_term
            
        elif protected_term.protection_type == ProtectionType.NUMERICAL:
            # Adapter les formats numeriques si necessaire
            if 'localization' in protected_term.metadata:
                restored_term = self._localize_number(original_term)
        
        elif protected_term.protection_type == ProtectionType.TECHNICAL:
            # Les termes techniques restent en anglais generalement
            restored_term = original_term
        
        return restored_term
    
    def _localize_number(self, number_str: str) -> str:
        """
        Localise un nombre selon les conventions
        
        Args:
            number_str: Nombre sous forme de string
        
        Returns:
            Nombre localise
        """
        # Pour l'instant, garder le format original
        # Futur: adapter selon les conventions de la langue cible
        return number_str
    
    def _load_custom_terms(self, custom_terms_file: str):
        """
        Charge des termes personnalises depuis un fichier
        
        Args:
            custom_terms_file: Chemin vers le fichier JSON
        """
        try:
            with open(custom_terms_file, 'r', encoding='utf-8') as f:
                custom_data = json.load(f)
            
            for category, terms in custom_data.items():
                if category in [pt.value for pt in ProtectionType]:
                    # Ajouter aux patterns existants
                    if isinstance(terms, list):
                        protection_type = ProtectionType(category)
                        if protection_type not in self.patterns:
                            self.patterns[protection_type] = []
                        self.patterns[protection_type].extend(terms)
            
            logger.info(f"Termes personnalises charges depuis {custom_terms_file}")
            
        except Exception as e:
            logger.warning(f"Impossible de charger les termes personnalises {custom_terms_file}: {e}")
    
    def get_protection_statistics(self) -> Dict[str, Any]:
        """
        Retourne les statistiques de protection
        
        Returns:
            Dictionnaire avec statistiques
        """
        type_counts = {}
        for term in self.protected_terms.values():
            ptype = term.protection_type.value
            type_counts[ptype] = type_counts.get(ptype, 0) + 1
        
        return {
            'total_protected_terms': len(self.protected_terms),
            'protection_types': type_counts,
            'cultural_terms_available': sum(len(terms) for terms in self.african_cultural_terms.values()),
            'patterns_loaded': sum(len(patterns) for patterns in self.patterns.values())
        }
    
    def export_protected_terms(self, export_file: str):
        """
        Exporte les termes proteges vers un fichier
        
        Args:
            export_file: Chemin du fichier d'export
        """
        export_data = {}
        for placeholder, term in self.protected_terms.items():
            export_data[placeholder] = {
                'original': term.original,
                'type': term.protection_type.value,
                'confidence': term.confidence,
                'metadata': term.metadata
            }
        
        try:
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Termes proteges exportes vers {export_file}")
        except Exception as e:
            logger.error(f"Erreur export termes proteges: {e}")


# Fonction utilitaire pour utilisation simple
def protect_and_translate(text: str, target_language: str, translation_function: callable) -> str:
    """
    Fonction utilitaire pour proteger, traduire et restaurer
    
    Args:
        text: Texte a traduire
        target_language: Langue cible
        translation_function: Fonction de traduction
    
    Returns:
        Texte traduit avec termes restaures
    """
    # Protection
    term_manager = TermProtectionManager()
    protected_text, protected_terms = term_manager.protect_text(text, target_language)
    
    # Traduction
    translated_text = translation_function(protected_text)
    
    # Restauration
    final_text = term_manager.restore_text(translated_text, protected_terms)
    
    return final_text


if __name__ == "__main__":
    # Test du gestionnaire de protection
    term_manager = TermProtectionManager()
    
    test_text = """
    Le royaume du Dahomey etait gouverne par le roi Behanzin.
    Les Fon pratiquent le vodun et venerent Legba.
    L'API REST utilise HTTP/HTTPS pour communiquer.
    Le montant est de 1,500.50 CFA en 2023.
    La formule est E = mc� selon Einstein.
    """
    
    print("Texte original:")
    print(test_text)
    
    # Protection
    protected_text, terms = term_manager.protect_text(test_text, "fon")
    print(f"\nTexte protege ({len(terms)} termes):")
    print(protected_text)
    
    # Simulation traduction
    simulated_translation = protected_text.replace("etait", "was").replace("royaume", "kingdom")
    
    # Restauration
    restored_text = term_manager.restore_text(simulated_translation, terms)
    print(f"\nTexte restaure:")
    print(restored_text)
    
    # Statistiques
    stats = term_manager.get_protection_statistics()
    print(f"\nStatistiques: {stats}")