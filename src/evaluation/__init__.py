# -*- coding: utf-8 -*-
"""
Module d'évaluation WikiTranslateAI

Système d'évaluation spécialisé pour les traductions vers les langues africaines,
incluant des métriques personnalisées pour la préservation culturelle et la
qualité linguistique spécifique aux langues tonales.

Composants:
- TranslationEvaluator: Évaluateur principal avec métriques standard
- AfricanLanguageEvaluator: Évaluateur spécialisé pour langues africaines
- Métriques BLEU/METEOR: Implémentations optimisées
- Métriques personnalisées: Préservation culturelle, cohérence tonale
- Visualisation: Rapports et graphiques détaillés
"""

try:
    # Évaluateurs principaux
    from .evaluate_translation import TranslationEvaluator
    from .comparison import AfricanLanguageEvaluator, evaluate_translation
    from .visualize_results import TranslationResultsVisualizer, quick_visualize
    
    # Métriques spécialisées
    from .metrics.bleu import calculate_bleu_score, compute_bleu, compute_corpus_bleu
    from .metrics.meteor import calculate_meteor_score, compute_meteor, compute_corpus_meteor
    from .metrics.custom_metrics import (
        calculate_custom_metrics,
        CulturalPreservationMetric,
        SemanticCoherenceMetric,
        FluentReformulationMetric
    )
    
    __all__ = [
        # Évaluateurs
        'TranslationEvaluator',
        'AfricanLanguageEvaluator',
        'evaluate_translation',
        
        # Visualisation
        'TranslationResultsVisualizer',
        'quick_visualize',
        
        # Métriques BLEU
        'calculate_bleu_score',
        'compute_bleu',
        'compute_corpus_bleu',
        
        # Métriques METEOR
        'calculate_meteor_score', 
        'compute_meteor',
        'compute_corpus_meteor',
        
        # Métriques personnalisées
        'calculate_custom_metrics',
        'CulturalPreservationMetric',
        'SemanticCoherenceMetric',
        'FluentReformulationMetric'
    ]
    
    def evaluate_african_translation(candidate: str, reference: str, 
                                   target_language: str = 'fon',
                                   include_visualization: bool = False) -> dict:
        """
        Évaluation complète d'une traduction vers une langue africaine
        
        Args:
            candidate: Traduction candidate
            reference: Traduction de référence
            target_language: Langue cible (fon, yor, ewe, dindi)
            include_visualization: Générer des visualisations
            
        Returns:
            Dictionnaire avec scores détaillés
        """
        evaluator = AfricanLanguageEvaluator(target_language)
        result = evaluator.evaluate_translation(candidate, reference)
        
        # Ajouter métriques standard
        bleu_result = calculate_bleu_score([reference], [candidate])
        meteor_result = calculate_meteor_score([reference], [candidate])
        custom_result = calculate_custom_metrics([reference], [candidate], target_language)
        
        complete_result = {
            'african_metrics': {
                'bleu_score': result.bleu_score,
                'rouge_l': result.rouge_l,
                'cultural_preservation': result.cultural_preservation,
                'tonal_accuracy': result.tonal_accuracy,
                'overall_score': result.overall_score
            },
            'standard_metrics': {
                'bleu': bleu_result['score'],
                'meteor': meteor_result['score']
            },
            'custom_metrics': custom_result['breakdown'],
            'detailed_metrics': result.detailed_metrics
        }
        
        if include_visualization:
            visualizer = TranslationResultsVisualizer()
            # Logique de visualisation ici
            
        return complete_result
    
    def batch_evaluate(references: list, candidates: list, 
                      target_language: str = 'fon',
                      metrics: list = None) -> dict:
        """
        Évaluation en lot avec métriques sélectionnées
        
        Args:
            references: Liste des références
            candidates: Liste des candidats
            target_language: Langue cible
            metrics: Liste des métriques à calculer
            
        Returns:
            Résultats d'évaluation en lot
        """
        if metrics is None:
            metrics = ['bleu', 'meteor', 'custom']
        
        results = {}
        
        if 'bleu' in metrics:
            results['bleu'] = calculate_bleu_score(references, candidates)
        
        if 'meteor' in metrics:
            results['meteor'] = calculate_meteor_score(references, candidates)
            
        if 'custom' in metrics:
            results['custom'] = calculate_custom_metrics(
                references, candidates, target_language
            )
        
        return results
    
    __all__.extend(['evaluate_african_translation', 'batch_evaluate'])
    
except ImportError as e:
    __all__ = []
    import warnings
    warnings.warn(f"Impossible d'importer les modules d'évaluation: {e}")

# Configuration par défaut
EVALUATION_CONFIG = {
    'default_metrics': ['bleu', 'meteor', 'custom'],
    'quality_thresholds': {
        'excellent': 0.8,
        'good': 0.6,
        'acceptable': 0.4
    },
    'african_languages': ['fon', 'yor', 'yoruba', 'ewe', 'dindi'],
    'visualization_formats': ['png', 'html', 'json']
}