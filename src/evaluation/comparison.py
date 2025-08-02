# -*- coding: utf-8 -*-
"""
Evaluation system for African language translations
"""

import re
import json
import math
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from collections import Counter
import logging

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Translation evaluation result"""
    bleu_score: float
    rouge_l: float
    cultural_preservation: float
    tonal_accuracy: float
    overall_score: float
    detailed_metrics: Dict[str, Any]


class AfricanLanguageEvaluator:
    """Evaluator specialized for African languages"""
    
    def __init__(self, language: str):
        self.language = language.lower()
        
        # Cultural terms for each language
        self.cultural_terms = {
            'yor': ['bawo', 'pele', 'iya', 'baba', 'orisha', 'oba'],
            'fon': ['migblon', 'vodun', 'legba', 'mawu'],
            'ewe': ['nogbe', 'mawu', 'legba', 'togbe'],
            'dindi': ['sannu', 'sarki', 'gari']
        }.get(language, [])
        
        # Weights for overall score
        self.weights = {
            'bleu': 0.30,
            'rouge_l': 0.25,
            'cultural_preservation': 0.25,
            'tonal_accuracy': 0.20
        }
    
    def evaluate_translation(self, candidate: str, reference: str, source_text: Optional[str] = None) -> EvaluationResult:
        """Evaluate a translation against reference"""
        try:
            # Normalize texts
            candidate_norm = self._normalize_text(candidate)
            reference_norm = self._normalize_text(reference)
            
            # Calculate metrics
            bleu_score = self._calculate_bleu(candidate_norm, reference_norm)
            rouge_l = self._calculate_rouge_l(candidate_norm, reference_norm)
            cultural_preservation = self._evaluate_cultural_preservation(candidate_norm, reference_norm)
            tonal_accuracy = self._evaluate_tonal_accuracy(candidate_norm, reference_norm)
            
            # Overall score
            overall_score = (
                bleu_score * self.weights['bleu'] +
                rouge_l * self.weights['rouge_l'] +
                cultural_preservation * self.weights['cultural_preservation'] +
                tonal_accuracy * self.weights['tonal_accuracy']
            )
            
            # Detailed metrics
            detailed_metrics = {
                'candidate_length': len(candidate_norm.split()),
                'reference_length': len(reference_norm.split()),
                'cultural_terms_found': self._count_cultural_terms(candidate_norm)
            }
            
            return EvaluationResult(
                bleu_score=bleu_score,
                rouge_l=rouge_l,
                cultural_preservation=cultural_preservation,
                tonal_accuracy=tonal_accuracy,
                overall_score=overall_score,
                detailed_metrics=detailed_metrics
            )
            
        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            return EvaluationResult(
                bleu_score=0.0,
                rouge_l=0.0,
                cultural_preservation=0.0,
                tonal_accuracy=0.0,
                overall_score=0.0,
                detailed_metrics={}
            )
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for evaluation"""
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _calculate_bleu(self, candidate: str, reference: str, max_n: int = 4) -> float:
        """Calculate BLEU score"""
        candidate_tokens = candidate.split()
        reference_tokens = reference.split()
        
        if not candidate_tokens or not reference_tokens:
            return 0.0
        
        precisions = []
        
        for n in range(1, max_n + 1):
            candidate_ngrams = Counter(self._get_ngrams(candidate_tokens, n))
            reference_ngrams = Counter(self._get_ngrams(reference_tokens, n))
            
            if not candidate_ngrams:
                precisions.append(0.0)
                continue
            
            matches = sum(min(candidate_ngrams[ngram], reference_ngrams[ngram]) 
                         for ngram in candidate_ngrams)
            
            precision = matches / sum(candidate_ngrams.values())
            precisions.append(precision)
        
        if 0.0 in precisions:
            return 0.0
        
        brevity_penalty = min(1.0, math.exp(1 - len(reference_tokens) / len(candidate_tokens)))
        bleu = brevity_penalty * math.exp(sum(math.log(p) for p in precisions) / len(precisions))
        return bleu
    
    def _calculate_rouge_l(self, candidate: str, reference: str) -> float:
        """Calculate ROUGE-L score"""
        candidate_tokens = candidate.split()
        reference_tokens = reference.split()
        
        if not candidate_tokens or not reference_tokens:
            return 0.0
        
        lcs_length = self._lcs_length(candidate_tokens, reference_tokens)
        
        if lcs_length == 0:
            return 0.0
        
        precision = lcs_length / len(candidate_tokens)
        recall = lcs_length / len(reference_tokens)
        
        if precision + recall == 0:
            return 0.0
        
        rouge_l = 2 * precision * recall / (precision + recall)
        return rouge_l
    
    def _evaluate_cultural_preservation(self, candidate: str, reference: str) -> float:
        """Evaluate cultural term preservation"""
        if not self.cultural_terms:
            return 0.5  # Neutral score
        
        candidate_tokens = set(candidate.split())
        reference_tokens = set(reference.split())
        
        cultural_in_reference = set()
        for term in self.cultural_terms:
            if term.lower() in reference_tokens:
                cultural_in_reference.add(term.lower())
        
        if not cultural_in_reference:
            return 1.0  # No cultural terms to preserve
        
        preserved = sum(1 for term in cultural_in_reference if term in candidate_tokens)
        return preserved / len(cultural_in_reference)
    
    def _evaluate_tonal_accuracy(self, candidate: str, reference: str) -> float:
        """Evaluate tonal accuracy (simplified)"""
        # Simplified tonal evaluation based on common patterns
        tonal_patterns = {
            'yor': ['o', 'a', 'e'],  # Common vowels with tones
            'fon': ['o', 'a', 'e'],
            'ewe': ['o', 'a', 'e'],
            'dindi': ['a', 'i', 'u']
        }
        
        patterns = tonal_patterns.get(self.language, [])
        if not patterns:
            return 0.5
        
        # Count matching vowel patterns (simplified tonal check)
        candidate_vowels = [c for c in candidate if c in patterns]
        reference_vowels = [c for c in reference if c in patterns]
        
        if not reference_vowels:
            return 1.0
        
        matches = sum(1 for cv, rv in zip(candidate_vowels, reference_vowels) if cv == rv)
        return matches / len(reference_vowels) if reference_vowels else 0.0
    
    def _count_cultural_terms(self, text: str) -> int:
        """Count cultural terms in text"""
        tokens = text.split()
        return sum(1 for term in self.cultural_terms if term.lower() in tokens)
    
    def _get_ngrams(self, tokens: List[str], n: int) -> List[Tuple[str, ...]]:
        """Generate n-grams from tokens"""
        return [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]
    
    def _lcs_length(self, seq1: List[str], seq2: List[str]) -> int:
        """Calculate longest common subsequence length"""
        m, n = len(seq1), len(seq2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i-1] == seq2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]


def evaluate_translation(candidate: str, reference: str, language: str) -> EvaluationResult:
    """Quick evaluation function"""
    evaluator = AfricanLanguageEvaluator(language)
    return evaluator.evaluate_translation(candidate, reference)