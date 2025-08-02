#!/usr/bin/env python3
# src/evaluation/metrics/bleu.py

import math
import logging
from collections import Counter
from typing import List, Dict, Tuple, Set, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_ngrams(segment: str, n: int) -> Counter:
    """
    Extrait les n-grammes d'un segment de texte
    
    Args:
        segment: Segment de texte
        n: Taille des n-grammes
        
    Returns:
        Counter des n-grammes avec leur fréquence
    """
    # Prétraitement du segment (tokenisation simplifiée)
    tokens = segment.lower().split()
    
    # Générer les n-grammes
    ngrams = Counter()
    for i in range(len(tokens) - n + 1):
        ngram = tuple(tokens[i:i+n])
        ngrams[ngram] += 1
    
    return ngrams

def compute_bleu(reference: str, candidate: str, max_ngram: int = 4) -> float:
    """
    Calcule le score BLEU entre une référence et une traduction candidate
    
    Args:
        reference: Traduction de référence
        candidate: Traduction candidate à évaluer
        max_ngram: Ordre maximum des n-grammes (par défaut 4)
        
    Returns:
        Score BLEU entre 0 et 1
    """
    # Vérifier que les entrées ne sont pas vides
    if not reference or not candidate:
        logger.warning("Référence ou candidat vide, BLEU non calculable")
        return 0.0
    
    # Prétraitement
    ref_tokens = reference.lower().split()
    cand_tokens = candidate.lower().split()
    
    # Longueur des segments
    ref_length = len(ref_tokens)
    cand_length = len(cand_tokens)
    
    if ref_length == 0 or cand_length == 0:
        logger.warning("Référence ou candidat sans tokens, BLEU non calculable")
        return 0.0
    
    # Calcul de la pénalité de brièveté
    bp = math.exp(min(0, 1 - ref_length / max(cand_length, 1)))
    
    # Calcul des précisions modifiées pour différents ordres de n-grammes
    precisions = []
    
    for n in range(1, min(max_ngram + 1, min(ref_length, cand_length) + 1)):
        ref_ngrams = get_ngrams(reference, n)
        cand_ngrams = get_ngrams(candidate, n)
        
        # Clipping - Limiter le nombre d'occurrences au maximum dans la référence
        clipped_counts = sum(min(cand_ngrams[ngram], ref_ngrams[ngram]) for ngram in cand_ngrams)
        
        # Total des n-grammes dans le candidat
        total_ngrams = sum(cand_ngrams.values())
        
        # Précision pour cet ordre de n-gramme
        if total_ngrams == 0:
            precision = 0.0
        else:
            precision = clipped_counts / total_ngrams
        
        precisions.append(precision)
    
    # Si toutes les précisions sont nulles, le score BLEU est nul
    if all(p == 0 for p in precisions):
        return 0.0
    
    # Calculer la moyenne géométrique des précisions
    log_precisions = sum(math.log(max(p, 1e-10)) for p in precisions) / len(precisions)
    
    # Score BLEU final
    bleu = bp * math.exp(log_precisions)
    
    return bleu

def compute_corpus_bleu(references: List[str], candidates: List[str], max_ngram: int = 4) -> float:
    """
    Calcule le score BLEU au niveau d'un corpus
    
    Args:
        references: Liste de traductions de référence
        candidates: Liste de traductions candidates
        max_ngram: Ordre maximum des n-grammes (par défaut 4)
        
    Returns:
        Score BLEU entre 0 et 1
    """
    if len(references) != len(candidates):
        logger.error(f"Nombre différent de références ({len(references)}) et de candidats ({len(candidates)})")
        return 0.0
    
    if len(references) == 0:
        logger.warning("Aucun segment à évaluer")
        return 0.0
    
    # Prétraitement
    ref_tokens_list = [ref.lower().split() for ref in references]
    cand_tokens_list = [cand.lower().split() for cand in candidates]
    
    # Longueur totale
    total_ref_length = sum(len(tokens) for tokens in ref_tokens_list)
    total_cand_length = sum(len(tokens) for tokens in cand_tokens_list)
    
    # Pénalité de brièveté
    bp = math.exp(min(0, 1 - total_ref_length / max(total_cand_length, 1)))
    
    # Statistiques globales pour tous les n-grammes
    total_match_ngrams = [0] * max_ngram
    total_count_ngrams = [0] * max_ngram
    
    # Calculer les correspondances pour chaque paire de segments
    for reference, candidate in zip(references, candidates):
        for n in range(1, max_ngram + 1):
            if len(reference.split()) < n or len(candidate.split()) < n:
                continue
                
            ref_ngrams = get_ngrams(reference, n)
            cand_ngrams = get_ngrams(candidate, n)
            
            # Nombre de n-grammes correspondants
            matches = sum(min(cand_ngrams[ngram], ref_ngrams[ngram]) for ngram in cand_ngrams)
            
            # Total des n-grammes dans le candidat
            total = sum(cand_ngrams.values())
            
            total_match_ngrams[n-1] += matches
            total_count_ngrams[n-1] += total
    
    # Calcul des précisions
    precisions = []
    for i in range(max_ngram):
        if total_count_ngrams[i] > 0:
            precision = total_match_ngrams[i] / total_count_ngrams[i]
            precisions.append(precision)
        else:
            precisions.append(0.0)
    
    # Si toutes les précisions sont nulles, le score BLEU est nul
    if all(p == 0 for p in precisions):
        return 0.0
    
    # Calculer la moyenne géométrique des précisions
    log_precisions = sum(math.log(max(p, 1e-10)) for p in precisions) / len(precisions)
    
    # Score BLEU final
    bleu = bp * math.exp(log_precisions)
    
    return bleu

def calculate_bleu_score(references: List[str], candidates: List[str], smoothing: bool = True, 
                       max_ngram: int = 4, individual_scores: bool = False) -> Dict[str, Any]:
    """
    Interface principale pour le calcul du score BLEU
    
    Args:
        references: Liste de traductions de référence
        candidates: Liste de traductions candidates
        smoothing: Activer le lissage pour éviter les scores nuls
        max_ngram: Ordre maximum des n-grammes (par défaut 4)
        individual_scores: Renvoyer aussi les scores individuels
        
    Returns:
        Dictionnaire contenant le score BLEU et d'autres informations
    """
    if len(references) != len(candidates):
        logger.error(f"Nombre différent de références ({len(references)}) et de candidats ({len(candidates)})")
        return {"score": 0.0, "error": "Nombre différent de références et de candidats"}
    
    # Score global
    corpus_score = compute_corpus_bleu(references, candidates, max_ngram)
    
    result = {
        "score": corpus_score,
        "method": "BLEU",
        "max_ngram": max_ngram,
        "segment_count": len(references)
    }
    
    # Scores individuels si demandés
    if individual_scores:
        individual = []
        for ref, cand in zip(references, candidates):
            score = compute_bleu(ref, cand, max_ngram)
            individual.append({
                "reference": ref,
                "candidate": cand,
                "score": score
            })
        result["individual_scores"] = individual
    
    return result