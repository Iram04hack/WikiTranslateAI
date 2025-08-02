# -*- coding: utf-8 -*-
# src/evaluation/metrics/custom_metrics.py

import re
import math
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import Counter, defaultdict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MetricResult:
    """Resultat d'une metrique d'evaluation"""
    score: float
    details: Dict[str, Any] = None
    explanation: str = ""

class CulturalPreservationMetric:
    """Metrique de preservation culturelle pour les langues africaines"""
    
    def __init__(self, target_language: str):
        self.target_language = target_language.lower()
        
        # Termes culturels par langue
        self.cultural_terms = {
            'fon': {
                'religious': ['vodun', 'legba', 'mami wata', 'sakpata', 'heviesso', 'dan'],
                'historical': ['dahomey', 'abomey', 'ouidah', 'agassu', 'behanzin', 'glele'],
                'social': ['agbo', 'bo', 'axe', 'tata', 'mama'],
                'places': ['porto-novo', 'cotonou', 'abomey-calavi', 'parakou']
            },
            'yor': {
                'religious': ['orisha', 'ifa', 'ogun', 'shango', 'yemoja', 'oshun', 'obatala'],
                'social': ['egungun', 'ori', 'ase', 'iyalocha', 'babalocha', 'baba', 'mama'],
                'historical': ['ile-ife', 'oyo', 'benin', 'yorubaland'],
                'places': ['lagos', 'ibadan', 'abeokuta', 'ilorin', 'ogbomoso']
            },
            'ewe': {
                'religious': ['vodu', 'trowo', 'afa', 'legba', 'sogbo', 'nyigbla', 'mawu', 'lisa'],
                'social': ['gbetsi', 'amedzro', 'dufia', 'torgbui', 'mama'],
                'places': ['lome', 'kpalime', 'atakpame', 'kara', 'volta']
            },
            'dindi': {
                'religious': ['zima', 'holle', 'spirits'],
                'social': ['borey', 'gourma', 'zarma', 'songhai'],
                'places': ['niamey', 'tillaberi', 'dosso', 'gao']
            }
        }
        
        # Patterns linguistiques specifiques
        self.linguistic_patterns = {
            'fon': [
                r'\b\w+gb\w+\b',  # Pattern typique en fon (gb)
                r'\b\w+kp\w+\b',  # Pattern kp
                r'\b\w+x[wv]\w+\b'  # Pattern xw/xv
            ],
            'yor': [
                r'\b\w+gb\w+\b',  # Pattern gb
                r'\b\w+p\w+\b',   # Sons p
                r"[àáâäÎ]",       # Tons yoruba
                r"[èéêë]",
                r"[ìíîïÐ]",
                r"[òóôöÒ]",
                r"[ùúûüÔ]"
            ],
            'ewe': [
                r'\bK\w+\b',      # Lettre K specifique
                r'\b\w+V\w+\b',   # Lettre V
                r'[àáâäÎ]',       # Tons ewe
                r'[èéêë]'
            ]
        }
    
    def evaluate(self, candidate: str, reference: str) -> MetricResult:
        """
        Evalue la preservation culturelle
        
        Args:
            candidate: Traduction candidate
            reference: Traduction de reference
        
        Returns:
            Resultat de la metrique
        """
        try:
            cultural_score = self._calculate_cultural_preservation(candidate, reference)
            linguistic_score = self._calculate_linguistic_preservation(candidate, reference)
            
            # Score combine
            overall_score = (cultural_score * 0.7) + (linguistic_score * 0.3)
            
            details = {
                'cultural_preservation': cultural_score,
                'linguistic_preservation': linguistic_score,
                'cultural_terms_found': self._count_cultural_terms(candidate),
                'total_cultural_terms': self._count_cultural_terms(reference)
            }
            
            explanation = f"Preservation culturelle: {cultural_score:.2f}, " \
                         f"Preservation linguistique: {linguistic_score:.2f}"
            
            return MetricResult(
                score=overall_score,
                details=details,
                explanation=explanation
            )
            
        except Exception as e:
            logger.error(f"Erreur evaluation culturelle: {e}")
            return MetricResult(score=0.0, explanation=f"Erreur: {e}")
    
    def _calculate_cultural_preservation(self, candidate: str, reference: str) -> float:
        """Calcule la preservation des termes culturels"""
        if self.target_language not in self.cultural_terms:
            return 0.5  # Score neutre si langue non supportee
        
        candidate_lower = candidate.lower()
        reference_lower = reference.lower()
        
        all_cultural_terms = []
        for category in self.cultural_terms[self.target_language].values():
            all_cultural_terms.extend(category)
        
        # Termes culturels dans la reference
        cultural_in_ref = []
        for term in all_cultural_terms:
            if term in reference_lower:
                cultural_in_ref.append(term)
        
        if not cultural_in_ref:
            return 1.0  # Aucun terme culturel a preserver
        
        # Termes preserves dans le candidat
        preserved = []
        for term in cultural_in_ref:
            if term in candidate_lower:
                preserved.append(term)
        
        return len(preserved) / len(cultural_in_ref)
    
    def _calculate_linguistic_preservation(self, candidate: str, reference: str) -> float:
        """Calcule la preservation des patterns linguistiques"""
        if self.target_language not in self.linguistic_patterns:
            return 0.5
        
        patterns = self.linguistic_patterns[self.target_language]
        pattern_scores = []
        
        for pattern in patterns:
            ref_matches = len(re.findall(pattern, reference, re.IGNORECASE))
            cand_matches = len(re.findall(pattern, candidate, re.IGNORECASE))
            
            if ref_matches == 0:
                score = 1.0  # Pas de pattern a preserver
            else:
                score = min(1.0, cand_matches / ref_matches)
            
            pattern_scores.append(score)
        
        return sum(pattern_scores) / len(pattern_scores) if pattern_scores else 0.5
    
    def _count_cultural_terms(self, text: str) -> int:
        """Compte les termes culturels dans un texte"""
        if self.target_language not in self.cultural_terms:
            return 0
        
        text_lower = text.lower()
        count = 0
        
        for category in self.cultural_terms[self.target_language].values():
            for term in category:
                count += text_lower.count(term)
        
        return count

class SemanticCoherenceMetric:
    """Metrique de coherence semantique"""
    
    def __init__(self):
        # Mots de liaison et connecteurs
        self.connectors = {
            'fr': ['et', 'ou', 'mais', 'donc', 'car', 'ainsi', 'cependant', 'néanmoins'],
            'en': ['and', 'or', 'but', 'so', 'because', 'thus', 'however', 'nevertheless'],
            'fon': ['kpo', 'loo', 'amT', 'enye'],  # Exemples approximatifs
            'yor': ['ati', 'tabi', 'sugbon', 'nitori'],
            'ewe': ['kple', 'alo', 'gake', 'ta']
        }
    
    def evaluate(self, candidate: str, reference: str, source_language: str = 'fr') -> MetricResult:
        """
        Evalue la coherence semantique
        
        Args:
            candidate: Traduction candidate
            reference: Traduction de reference
            source_language: Langue source
        
        Returns:
            Resultat de la metrique
        """
        try:
            # Coherence structurelle
            structure_score = self._evaluate_structure_coherence(candidate, reference)
            
            # Coherence des connecteurs
            connector_score = self._evaluate_connector_coherence(candidate, reference, source_language)
            
            # Coherence de longueur
            length_score = self._evaluate_length_coherence(candidate, reference)
            
            # Score combine
            overall_score = (structure_score * 0.4) + (connector_score * 0.3) + (length_score * 0.3)
            
            details = {
                'structure_coherence': structure_score,
                'connector_coherence': connector_score,
                'length_coherence': length_score,
                'candidate_sentences': len(re.split(r'[.!?]+', candidate)),
                'reference_sentences': len(re.split(r'[.!?]+', reference))
            }
            
            return MetricResult(
                score=overall_score,
                details=details,
                explanation=f"Coherence structurelle: {structure_score:.2f}, "
                           f"Connecteurs: {connector_score:.2f}, "
                           f"Longueur: {length_score:.2f}"
            )
            
        except Exception as e:
            logger.error(f"Erreur evaluation coherence: {e}")
            return MetricResult(score=0.0, explanation=f"Erreur: {e}")
    
    def _evaluate_structure_coherence(self, candidate: str, reference: str) -> float:
        """Evalue la coherence structurelle"""
        # Nombre de phrases
        cand_sentences = len(re.split(r'[.!?]+', candidate.strip()))
        ref_sentences = len(re.split(r'[.!?]+', reference.strip()))
        
        if ref_sentences == 0:
            return 1.0
        
        # Penaliser les differences importantes de structure
        sentence_ratio = min(cand_sentences, ref_sentences) / max(cand_sentences, ref_sentences)
        
        return sentence_ratio
    
    def _evaluate_connector_coherence(self, candidate: str, reference: str, source_lang: str) -> float:
        """Evalue la coherence des connecteurs"""
        if source_lang not in self.connectors:
            return 0.5
        
        connectors = self.connectors[source_lang]
        
        # Compter connecteurs dans reference et candidat
        ref_connectors = sum(1 for conn in connectors if conn in reference.lower())
        cand_connectors = sum(1 for conn in connectors if conn in candidate.lower())
        
        if ref_connectors == 0:
            return 1.0
        
        # Score base sur la preservation des connecteurs
        connector_ratio = min(1.0, cand_connectors / ref_connectors)
        
        return connector_ratio
    
    def _evaluate_length_coherence(self, candidate: str, reference: str) -> float:
        """Evalue la coherence de longueur"""
        ref_len = len(reference.split())
        cand_len = len(candidate.split())
        
        if ref_len == 0:
            return 1.0 if cand_len == 0 else 0.0
        
        # Ratio de longueur (penaliser les differences extremes)
        length_ratio = min(cand_len, ref_len) / max(cand_len, ref_len)
        
        # Penaliser les differences de plus de 50%
        if length_ratio < 0.5:
            length_ratio *= 0.5
        
        return length_ratio

class FluentReformulationMetric:
    """Metrique de fluidite et reformulation naturelle"""
    
    def __init__(self):
        # Patterns de repetition problematiques
        self.repetition_patterns = [
            r'\b(\w+)\s+\1\b',  # Repetition directe
            r'\b(\w+)\s+\w+\s+\1\b',  # Repetition avec un mot entre
        ]
        
        # Patterns de fluidite
        self.fluency_indicators = {
            'positive': [
                r'\b(?:le|la|les|un|une|des)\s+\w+',  # Articles français
                r'\b(?:qui|que|dont|où)\s+\w+',       # Pronoms relatifs
                r'\b(?:et|ou|mais)\s+\w+',            # Conjonctions
            ],
            'negative': [
                r'\b(?:ERREUR|ERROR|TRADUCTION_IMPOSSIBLE)\b',  # Erreurs explicites
                r'\b\w+_\w+_\w+\b',  # Patterns d'erreur techniques
                r'\[\w+\]',          # Balises d'erreur
            ]
        }
    
    def evaluate(self, candidate: str, reference: str) -> MetricResult:
        """
        Evalue la fluidite et reformulation
        
        Args:
            candidate: Traduction candidate
            reference: Traduction de reference
        
        Returns:
            Resultat de la metrique
        """
        try:
            # Evaluation repetitions
            repetition_score = self._evaluate_repetitions(candidate)
            
            # Evaluation fluidite
            fluency_score = self._evaluate_fluency(candidate)
            
            # Evaluation naturalite
            naturalness_score = self._evaluate_naturalness(candidate, reference)
            
            # Score combine
            overall_score = (repetition_score * 0.3) + (fluency_score * 0.4) + (naturalness_score * 0.3)
            
            details = {
                'repetition_score': repetition_score,
                'fluency_score': fluency_score,
                'naturalness_score': naturalness_score,
                'repetitions_found': self._count_repetitions(candidate),
                'error_markers_found': self._count_error_markers(candidate)
            }
            
            return MetricResult(
                score=overall_score,
                details=details,
                explanation=f"Repetitions: {repetition_score:.2f}, "
                           f"Fluidite: {fluency_score:.2f}, "
                           f"Naturalite: {naturalness_score:.2f}"
            )
            
        except Exception as e:
            logger.error(f"Erreur evaluation fluidite: {e}")
            return MetricResult(score=0.0, explanation=f"Erreur: {e}")
    
    def _evaluate_repetitions(self, text: str) -> float:
        """Evalue les repetitions problematiques"""
        repetitions = 0
        
        for pattern in self.repetition_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            repetitions += len(matches)
        
        # Penaliser les repetitions
        word_count = len(text.split())
        if word_count == 0:
            return 1.0
        
        repetition_ratio = repetitions / word_count
        repetition_score = max(0.0, 1.0 - (repetition_ratio * 5))  # Penalite forte
        
        return repetition_score
    
    def _evaluate_fluency(self, text: str) -> float:
        """Evalue la fluidite du texte"""
        positive_score = 0
        negative_score = 0
        
        # Compter indicateurs positifs
        for pattern in self.fluency_indicators['positive']:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            positive_score += matches
        
        # Compter indicateurs negatifs
        for pattern in self.fluency_indicators['negative']:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            negative_score += matches
        
        word_count = len(text.split())
        if word_count == 0:
            return 0.0
        
        # Score base sur les indicateurs
        positive_ratio = positive_score / word_count
        negative_ratio = negative_score / word_count
        
        fluency_score = min(1.0, positive_ratio * 2) - (negative_ratio * 10)
        
        return max(0.0, fluency_score)
    
    def _evaluate_naturalness(self, candidate: str, reference: str) -> float:
        """Evalue la naturalite de la reformulation"""
        # Diversite lexicale
        cand_words = set(candidate.lower().split())
        ref_words = set(reference.lower().split())
        
        if not ref_words:
            return 1.0
        
        # Overlap lexical (ni trop faible ni trop fort)
        overlap = len(cand_words & ref_words) / len(ref_words)
        
        # Score optimal autour de 0.6-0.8 (reformulation naturelle)
        if 0.6 <= overlap <= 0.8:
            naturalness = 1.0
        elif overlap < 0.6:
            naturalness = overlap / 0.6  # Penaliser le manque de similarite
        else:
            naturalness = 1.0 - ((overlap - 0.8) / 0.2)  # Penaliser trop de similarite
        
        return max(0.0, min(1.0, naturalness))
    
    def _count_repetitions(self, text: str) -> int:
        """Compte les repetitions dans le texte"""
        count = 0
        for pattern in self.repetition_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            count += len(matches)
        return count
    
    def _count_error_markers(self, text: str) -> int:
        """Compte les marqueurs d'erreur"""
        count = 0
        for pattern in self.fluency_indicators['negative']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            count += len(matches)
        return count

def calculate_custom_metrics(references: List[str], candidates: List[str],
                           target_language: str = 'fon',
                           source_language: str = 'fr',
                           individual_scores: bool = False) -> Dict[str, Any]:
    """
    Interface principale pour le calcul des metriques personnalisees
    
    Args:
        references: Liste de traductions de reference
        candidates: Liste de traductions candidates
        target_language: Langue cible
        source_language: Langue source
        individual_scores: Renvoyer aussi les scores individuels
    
    Returns:
        Dictionnaire contenant les scores des metriques personnalisees
    """
    if len(references) != len(candidates):
        logger.error(f"Nombre different de references ({len(references)}) et de candidats ({len(candidates)})")
        return {"score": 0.0, "error": "Nombre different de references et de candidats"}
    
    # Initialiser les metriques
    cultural_metric = CulturalPreservationMetric(target_language)
    coherence_metric = SemanticCoherenceMetric()
    fluenty_metric = FluentReformulationMetric()
    
    # Calculer les scores agregés
    cultural_scores = []
    coherence_scores = []
    fluency_scores = []
    
    individual_results = []
    
    for ref, cand in zip(references, candidates):
        # Evaluer chaque metrique
        cultural_result = cultural_metric.evaluate(cand, ref)
        coherence_result = coherence_metric.evaluate(cand, ref, source_language)
        fluency_result = fluenty_metric.evaluate(cand, ref)
        
        cultural_scores.append(cultural_result.score)
        coherence_scores.append(coherence_result.score)
        fluency_scores.append(fluency_result.score)
        
        if individual_scores:
            individual_results.append({
                'reference': ref,
                'candidate': cand,
                'cultural_preservation': cultural_result.score,
                'semantic_coherence': coherence_result.score,
                'fluency_reformulation': fluency_result.score,
                'overall_custom': (cultural_result.score + coherence_result.score + fluency_result.score) / 3
            })
    
    # Scores moyens
    avg_cultural = sum(cultural_scores) / len(cultural_scores) if cultural_scores else 0.0
    avg_coherence = sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0.0
    avg_fluency = sum(fluency_scores) / len(fluency_scores) if fluency_scores else 0.0
    
    # Score global personnalise
    overall_custom_score = (avg_cultural + avg_coherence + avg_fluency) / 3
    
    result = {
        "score": overall_custom_score,
        "method": "Custom Metrics (African Languages)",
        "breakdown": {
            "cultural_preservation": avg_cultural,
            "semantic_coherence": avg_coherence,
            "fluency_reformulation": avg_fluency
        },
        "target_language": target_language,
        "source_language": source_language,
        "segment_count": len(references)
    }
    
    if individual_scores:
        result["individual_scores"] = individual_results
    
    return result

if __name__ == "__main__":
    # Test des metriques personnalisees
    references = [
        "Le vodun est une religion importante au Benin.",
        "Les rois du Dahomey etaient puissants.",
        "Legba est un orisha respecte."
    ]
    
    candidates = [
        "Vodun religion importante Benin.", # Preservation culturelle bonne mais fluidite moyenne
        "Kings Dahomey were powerful.",    # Mauvaise preservation culturelle
        "Legba est orisha respecte."       # Bonne preservation
    ]
    
    # Test
    result = calculate_custom_metrics(references, candidates, 'fon', 'fr', individual_scores=True)
    
    print("Resultats des metriques personnalisees:")
    print(f"Score global: {result['score']:.3f}")
    print(f"Preservation culturelle: {result['breakdown']['cultural_preservation']:.3f}")
    print(f"Coherence semantique: {result['breakdown']['semantic_coherence']:.3f}")
    print(f"Fluidite: {result['breakdown']['fluency_reformulation']:.3f}")
    
    if 'individual_scores' in result:
        print("\nScores individuels:")
        for i, individual in enumerate(result['individual_scores']):
            print(f"  Segment {i+1}: {individual['overall_custom']:.3f}")