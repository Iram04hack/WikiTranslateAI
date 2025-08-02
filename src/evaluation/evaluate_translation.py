#!/usr/bin/env python3
# src/evaluation/evaluate_translation.py

import os
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from .metrics.bleu import calculate_bleu_score
from .metrics.meteor import calculate_meteor_score

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TranslationEvaluator:
    """Classe pour l'évaluation des traductions"""
    
    def __init__(self, metrics: List[str] = None):
        """
        Initialise l'évaluateur
        
        Args:
            metrics: Liste des métriques à utiliser (par défaut: toutes)
        """
        self.available_metrics = {
            "bleu": calculate_bleu_score,
            "meteor": calculate_meteor_score
        }
        
        self.metrics = metrics or list(self.available_metrics.keys())
        
        # Vérifier que toutes les métriques demandées sont disponibles
        invalid_metrics = [m for m in self.metrics if m not in self.available_metrics]
        if invalid_metrics:
            logger.warning(f"Métriques non disponibles: {', '.join(invalid_metrics)}")
            self.metrics = [m for m in self.metrics if m in self.available_metrics]
    
    def evaluate(self, references: List[str], candidates: List[str], 
                individual_scores: bool = False) -> Dict[str, Any]:
        """
        Évalue la qualité des traductions selon plusieurs métriques
        
        Args:
            references: Liste de traductions de référence
            candidates: Liste de traductions candidates
            individual_scores: Renvoyer aussi les scores individuels
            
        Returns:
            Dictionnaire des résultats d'évaluation
        """
        if len(references) != len(candidates):
            error_msg = f"Nombre différent de références ({len(references)}) et de candidats ({len(candidates)})"
            logger.error(error_msg)
            return {"error": error_msg}
        
        if len(references) == 0:
            error_msg = "Aucun segment à évaluer"
            logger.warning(error_msg)
            return {"error": error_msg}
        
        # Résultats globaux
        results = {
            "segment_count": len(references),
            "scores": {}
        }
        
        # Calculer les scores pour chaque métrique
        for metric in self.metrics:
            metric_function = self.available_metrics[metric]
            
            try:
                metric_result = metric_function(
                    references=references, 
                    candidates=candidates,
                    individual_scores=individual_scores
                )
                
                results["scores"][metric] = metric_result["score"]
                
                # Ajouter les détails si disponibles
                if "individual_scores" in metric_result and individual_scores:
                    if "individual" not in results:
                        results["individual"] = []
                        for i in range(len(references)):
                            results["individual"].append({
                                "reference": references[i],
                                "candidate": candidates[i],
                                "scores": {}
                            })
                    
                    for i, score_info in enumerate(metric_result["individual_scores"]):
                        results["individual"][i]["scores"][metric] = score_info["score"]
            
            except Exception as e:
                logger.error(f"Erreur lors du calcul de la métrique {metric}: {e}")
                results["scores"][metric] = None
        
        return results
    
    def evaluate_file(self, reference_file: str, candidate_file: str, 
                    output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Évalue la qualité des traductions à partir de fichiers texte
        
        Args:
            reference_file: Chemin vers le fichier de références
            candidate_file: Chemin vers le fichier de candidats
            output_file: Chemin où sauvegarder les résultats (optionnel)
            
        Returns:
            Dictionnaire des résultats d'évaluation
        """
        try:
            # Charger les fichiers
            with open(reference_file, 'r', encoding='utf-8') as f:
                references = [line.strip() for line in f if line.strip()]
            
            with open(candidate_file, 'r', encoding='utf-8') as f:
                candidates = [line.strip() for line in f if line.strip()]
            
            # Évaluer
            results = self.evaluate(references, candidates)
            
            # Sauvegarder si demandé
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                logger.info(f"Résultats sauvegardés dans {output_file}")
            
            return results
        
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation des fichiers: {e}")
            return {"error": str(e)}
    
    def evaluate_json_file(self, json_file: str, output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Évalue la qualité des traductions à partir d'un fichier JSON contenant des paires
        
        Args:
            json_file: Chemin vers le fichier JSON
            output_file: Chemin où sauvegarder les résultats (optionnel)
            
        Returns:
            Dictionnaire des résultats d'évaluation
        """
        try:
            # Charger le fichier JSON
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extraire les paires de segments
            references = []
            candidates = []
            
            # Format attendu: liste de dictionnaires avec "reference" et "candidate"
            if isinstance(data, list) and len(data) > 0 and "reference" in data[0] and "candidate" in data[0]:
                for item in data:
                    references.append(item["reference"])
                    candidates.append(item["candidate"])
            
            # Alternative: dictionnaire avec listes "references" et "candidates"
            elif isinstance(data, dict) and "references" in data and "candidates" in data:
                references = data["references"]
                candidates = data["candidates"]
            
            # Si aucun format reconnu
            else:
                error_msg = "Format JSON non reconnu pour l'évaluation"
                logger.error(error_msg)
                return {"error": error_msg}
            
            # Évaluer
            results = self.evaluate(references, candidates)
            
            # Sauvegarder si demandé
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                logger.info(f"Résultats sauvegardés dans {output_file}")
            
            return results
        
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation du fichier JSON: {e}")
            return {"error": str(e)}
    
    def evaluate_translated_article(self, article_file: str, output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Évalue la qualité des traductions à partir d'un article traduit
        
        Args:
            article_file: Chemin vers le fichier d'article traduit
            output_file: Chemin où sauvegarder les résultats (optionnel)
            
        Returns:
            Dictionnaire des résultats d'évaluation
        """
        try:
            # Charger l'article
            with open(article_file, 'r', encoding='utf-8') as f:
                article_data = json.load(f)
            
            # Extraire les segments originaux et traduits
            references = []  # Segments originaux
            candidates = []  # Segments traduits
            
            # Parcourir les sections
            for section in article_data.get('translated_sections', []):
                original_segments = section.get('original_segments', [])
                translated_segments = section.get('segments', [])
                
                # Ajouter les paires de segments
                for orig, trans in zip(original_segments, translated_segments):
                    if orig and trans and not trans.startswith('[ERREUR'):
                        references.append(orig)
                        candidates.append(trans)
            
            # Vérifier qu'on a des segments à évaluer
            if not references or not candidates:
                error_msg = "Aucun segment valide trouvé dans l'article"
                logger.warning(error_msg)
                return {"error": error_msg}
            
            # Évaluer
            results = self.evaluate(references, candidates)
            
            # Ajouter des métadonnées
            results["article"] = {
                "title": article_data.get('title', 'Unknown'),
                "original_title": article_data.get('original_title', 'Unknown'),
                "source_language": article_data.get('source_language', 'Unknown'),
                "target_language": article_data.get('target_language', 'Unknown')
            }
            
            # Sauvegarder si demandé
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                logger.info(f"Résultats sauvegardés dans {output_file}")
            
            return results
        
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation de l'article: {e}")
            return {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Évaluation de traductions")
    parser.add_argument('--input', type=str, required=True,
                        help="Fichier à évaluer (article traduit, JSON de paires, ou texte)")
    parser.add_argument('--reference', type=str,
                        help="Fichier de référence (si input est un fichier candidat)")
    parser.add_argument('--output', type=str,
                        help="Fichier de sortie pour les résultats")
    parser.add_argument('--metrics', type=str, default="bleu,meteor",
                        help="Métriques à utiliser, séparées par des virgules (défaut: bleu,meteor)")
    parser.add_argument('--file-type', type=str, choices=['article', 'json', 'text'],
                        help="Type de fichier d'entrée")
    
    args = parser.parse_args()
    
    # Initialiser l'évaluateur avec les métriques demandées
    metrics = args.metrics.split(',')
    evaluator = TranslationEvaluator(metrics)
    
    # Déterminer le type de fichier automatiquement si non spécifié
    file_type = args.file_type
    if not file_type:
        if args.input.endswith('.json'):
            if args.reference:
                file_type = 'text'  # Probablement des fichiers texte avec extension .json
            else:
                # Vérifier le contenu pour déterminer s'il s'agit d'un article ou de paires JSON
                try:
                    with open(args.input, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if 'translated_sections' in data:
                        file_type = 'article'
                    else:
                        file_type = 'json'
                except:
                    file_type = 'text'
        else:
            file_type = 'text'
    
    # Évaluer selon le type de fichier
    if file_type == 'article':
        results = evaluator.evaluate_translated_article(args.input, args.output)
    elif file_type == 'json':
        results = evaluator.evaluate_json_file(args.input, args.output)
    elif file_type == 'text':
        if not args.reference:
            logger.error("Le fichier de référence est requis pour l'évaluation de fichiers texte")
            return
        results = evaluator.evaluate_file(args.reference, args.input, args.output)
    
    # Afficher les résultats
    if 'error' in results:
        logger.error(f"Erreur lors de l'évaluation: {results['error']}")
    else:
        print("\nRésultats de l'évaluation:")
        print(f"Segments évalués: {results.get('segment_count', 0)}")
        
        for metric, score in results.get('scores', {}).items():
            print(f"{metric.upper()}: {score:.4f}")
        
        if 'article' in results:
            print(f"\nArticle: {results['article']['title']}")
            print(f"Langues: {results['article']['source_language']} → {results['article']['target_language']}")

if __name__ == "__main__":
    main()