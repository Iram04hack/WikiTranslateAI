#!/usr/bin/env python3
# src/evaluation/metrics/meteor.py

import math
import logging
import string
from collections import Counter
from typing import List, Dict, Tuple, Set, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def preprocess_text(text: str) -> List[str]:
    """
    Prétraitement du texte pour évaluation METEOR
    
    Args:
        text: Texte à prétraiter
        
    Returns:
        Liste de tokens
    """
    # Supprimer la ponctuation et passer en minuscules
    translator = str.maketrans('', '', string.punctuation)
    text = text.translate(translator).lower()
    
    # Tokeniser (division simple par espaces)
    tokens = text.split()
    
    return tokens

def _compute_precision_recall(reference_tokens: List[str], candidate_tokens: List[str]) -> Tuple[float, float]:
    """
    Calcule la précision et le rappel entre les tokens de référence et candidats
    
    Args:
        reference_tokens: Tokens de la référence
        candidate_tokens: Tokens du candidat
        
    Returns:
        Tuple (précision, rappel)
    """
    ref_counter = Counter(reference_tokens)
    cand_counter = Counter(candidate_tokens)
    
    # Compter les correspondances
    matches = sum(min(ref_counter[token], cand_counter[token]) for token in ref_counter)
    
    # Calculer précision et rappel
    precision = matches / max(len(candidate_tokens), 1)
    recall = matches / max(len(reference_tokens), 1)
    
    return precision, recall

def _compute_fragmentation(reference_tokens: List[str], candidate_tokens: List[str], matches: int) -> float:
    """
    Calcule la pénalité de fragmentation pour METEOR
    
    Args:
        reference_tokens: Tokens de la référence
        candidate_tokens: Tokens du candidat
        matches: Nombre de tokens correspondants
        
    Returns:
        Pénalité de fragmentation
    """
    if matches <= 1:
        return 0.0
    
    # Identifier les chunks (séquences de tokens correspondants contigus)
    chunks = 0
    ref_matched = set()
    cand_matched = set()
    
    # Calculer les correspondances exactes
    for i, ref_token in enumerate(reference_tokens):
        for j, cand_token in enumerate(candidate_tokens):
            if ref_token == cand_token and i not in ref_matched and j not in cand_matched:
                ref_matched.add(i)
                cand_matched.add(j)
                break
    
    # Compter les chunks
    in_chunk = False
    for i in range(len(candidate_tokens)):
        if i in cand_matched:
            if not in_chunk:
                chunks += 1
                in_chunk = True
        else:
            in_chunk = False
    
    # Calculer la pénalité de fragmentation
    fragmentation = chunks / matches
    penalty = 0.5 * (fragmentation ** 3)
    
    return penalty

def compute_meteor(reference: str, candidate: str, alpha: float = 0.9, beta: float = 3.0, gamma: float = 0.5) -> float:
    """
    Calcule le score METEOR entre une référence et une traduction candidate
    
    Args:
        reference: Traduction de référence
        candidate: Traduction candidate à évaluer
        alpha: Poids de la précision (par défaut 0.9)
        beta: Facteur d'équilibre précision/rappel (par défaut 3.0)
        gamma: Poids de la pénalité de fragmentation (par défaut 0.5)
        
    Returns:
        Score METEOR entre 0 et 1
    """
    # Vérifier que les entrées ne sont pas vides
    if not reference or not candidate:
        logger.warning("Référence ou candidat vide, METEOR non calculable")
        return 0.0
    
    # Prétraitement
    ref_tokens = preprocess_text(reference)
    cand_tokens = preprocess_text(candidate)
    
    if len(ref_tokens) == 0 or len(cand_tokens) == 0:
        logger.warning("Référence ou candidat sans tokens, METEOR non calculable")
        return 0.0
    
    # Calculer précision et rappel
    precision, recall = _compute_precision_recall(ref_tokens, cand_tokens)
    
    # Si aucune correspondance, le score est nul
    if precision == 0.0 or recall == 0.0:
        return 0.0
    
    # Calculer la F-mesure harmonique (pondérée)
    fmean_numerator = precision * recall
    fmean_denominator = alpha * precision + (1 - alpha) * recall
    fmean = fmean_numerator / fmean_denominator
    
    # Calculer les correspondances
    ref_counter = Counter(ref_tokens)
    cand_counter = Counter(cand_tokens)
    matches = sum(min(ref_counter[token], cand_counter[token]) for token in ref_counter)
    
    # Calculer la pénalité de fragmentation
    penalty = _compute_fragmentation(ref_tokens, cand_tokens, matches)
    
    # Score METEOR final
    meteor = fmean * (1 - gamma * penalty)
    
    return meteor

def compute_corpus_meteor(references: List[str], candidates: List[str],
                         alpha: float = 0.9, beta: float = 3.0, gamma: float = 0.5) -> float:
    """
    Calcule le score METEOR moyen sur un corpus
    
    Args:
        references: Liste de traductions de référence
        candidates: Liste de traductions candidates
        alpha: Poids de la précision
        beta: Facteur d'équilibre précision/rappel
        gamma: Poids de la pénalité de fragmentation
        
    Returns:
        Score METEOR moyen entre 0 et 1
    """
    if len(references) != len(candidates):
        logger.error(f"Nombre différent de références ({len(references)}) et de candidats ({len(candidates)})")
        return 0.0
    
    if len(references) == 0:
        logger.warning("Aucun segment à évaluer")
        return 0.0
    
    # Calculer les scores METEOR pour chaque paire
    scores = []
    for reference, candidate in zip(references, candidates):
        score = compute_meteor(reference, candidate, alpha, beta, gamma)
        scores.append(score)
    
    # Moyenne des scores
    avg_score = sum(scores) / len(scores)
    
    return avg_score

def calculate_meteor_score(references: List[str], candidates: List[str],
                          alpha: float = 0.9, beta: float = 3.0, gamma: float = 0.5,
                          individual_scores: bool = False) -> Dict[str, Any]:
    """
    Interface principale pour le calcul du score METEOR
    
    Args:
        references: Liste de traductions de référence
        candidates: Liste de traductions candidates
        alpha: Poids de la précision
        beta: Facteur d'équilibre précision/rappel
        gamma: Poids de la pénalité de fragmentation
        individual_scores: Renvoyer aussi les scores individuels
        
    Returns:
        Dictionnaire contenant le score METEOR et d'autres informations
    """
    if len(references) != len(candidates):
        logger.error(f"Nombre différent de références ({len(references)}) et de candidats ({len(candidates)})")
        return {"score": 0.0, "error": "Nombre différent de références et de candidats"}
    
    # Score global
    corpus_score = compute_corpus_meteor(references, candidates, alpha, beta, gamma)
    
    result = {
        "score": corpus_score,
        "method": "METEOR",
        "parameters": {
            "alpha": alpha,
            "beta": beta,
            "gamma": gamma
        },
        "segment_count": len(references)
    }
    
    # Scores individuels si demandés
    if individual_scores:
        individual = []
        for ref, cand in zip(references, candidates):
            score = compute_meteor(ref, cand, alpha, beta, gamma)
            individual.append({
                "reference": ref,
                "candidate": cand,
                "score": score
            })
        result["individual_scores"] = individual
    
    return result