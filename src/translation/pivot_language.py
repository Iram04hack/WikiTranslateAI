# -*- coding: utf-8 -*-
# src/translation/pivot_language.py

import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from src.translation.azure_client import AzureOpenAITranslator
from src.translation.fallback_translation import FallbackTranslator
from src.utils.error_handler import handle_error, create_translation_error

logger = logging.getLogger(__name__)

class PivotStrategy(Enum):
    """Strategies de traduction pivot"""
    DIRECT = "direct"                    # Traduction directe si possible
    SINGLE_PIVOT = "single_pivot"        # Une langue pivot (ex: fr->en->fon)
    DUAL_PIVOT = "dual_pivot"           # Deux langues pivot (ex: fon->en->fr->yor)
    QUALITY_PIVOT = "quality_pivot"      # Pivot base sur la qualite
    CULTURAL_PIVOT = "cultural_pivot"    # Pivot culturellement approprie

@dataclass
class PivotPath:
    """Representation d'un chemin de traduction pivot"""
    source_language: str
    target_language: str
    pivot_languages: List[str]
    strategy: PivotStrategy
    estimated_quality: float = 0.0
    estimated_time: float = 0.0
    complexity_score: float = 0.0

class PivotLanguageTranslator:
    """Traducteur utilisant des langues pivot pour ameliorer la qualite"""
    
    def __init__(self, primary_translator: AzureOpenAITranslator = None):
        """
        Initialise le traducteur pivot
        
        Args:
            primary_translator: Traducteur principal a utiliser
        """
        self.primary_translator = primary_translator
        self.fallback_translator = None
        
        # Matrice de qualite des paires de langues (estimee)
        self.language_quality_matrix = {
            # Scores de qualite de traduction (0.0 = mauvais, 1.0 = excellent)
            ('en', 'fr'): 0.95,    # Anglais -> Francais (excellent)
            ('fr', 'en'): 0.95,    # Francais -> Anglais (excellent)
            ('en', 'fon'): 0.3,    # Anglais -> Fon (limite)
            ('fr', 'fon'): 0.7,    # Francais -> Fon (bon, contexte colonial)
            ('en', 'yor'): 0.4,    # Anglais -> Yoruba (moyen)
            ('fr', 'yor'): 0.3,    # Francais -> Yoruba (limite)
            ('en', 'ewe'): 0.3,    # Anglais -> Ewe (limite)
            ('fr', 'ewe'): 0.6,    # Francais -> Ewe (moyen, presence francophone)
            ('en', 'dindi'): 0.2,  # Anglais -> Dindi (tres limite)
            ('fr', 'dindi'): 0.5,  # Francais -> Dindi (moyen)
        }
        
        # Langues pivot optimales pour chaque langue cible
        self.optimal_pivots = {
            'fon': ['fr', 'en'],      # Francais prioritaire (contexte Benin)
            'yor': ['en', 'fr'],      # Anglais prioritaire (contexte Nigeria)
            'ewe': ['fr', 'en'],      # Francais prioritaire (contexte Togo)
            'dindi': ['fr', 'en']     # Francais prioritaire (contexte Niger/Benin)
        }
        
        # Affinites culturelles (langues partageant des concepts)
        self.cultural_affinity = {
            ('fon', 'yor'): 0.8,      # Grande affinite culturelle
            ('fon', 'ewe'): 0.6,      # Affinite moyenne
            ('fon', 'dindi'): 0.4,    # Affinite limitee
            ('yor', 'ewe'): 0.5,      # Affinite moyenne
            ('yor', 'dindi'): 0.3,    # Affinite limitee
            ('ewe', 'dindi'): 0.3     # Affinite limitee
        }
        
        logger.info("Traducteur pivot initialise")
    
    def translate_with_pivot(self, 
                           text: str, 
                           source_language: str, 
                           target_language: str,
                           strategy: PivotStrategy = PivotStrategy.QUALITY_PIVOT) -> Dict[str, Any]:
        """
        Traduit un texte en utilisant une strategie pivot
        
        Args:
            text: Texte a traduire
            source_language: Langue source
            target_language: Langue cible
            strategy: Strategie de pivot a utiliser
        
        Returns:
            Dictionnaire avec resultats de traduction
        """
        if not text or not text.strip():
            return {'translation': '', 'path': [], 'quality_score': 0.0}
        
        start_time = time.time()
        
        try:
            # Determiner le meilleur chemin de traduction
            optimal_path = self._find_optimal_pivot_path(
                source_language, target_language, strategy
            )
            
            logger.info(f"Chemin pivot choisi: {source_language} -> {' -> '.join(optimal_path.pivot_languages)} -> {target_language}")
            
            # Executer la traduction par etapes
            translation_result = self._execute_pivot_translation(text, optimal_path)
            
            # Calculer les metriques finales
            processing_time = time.time() - start_time
            
            result = {
                'translation': translation_result['final_translation'],
                'path': [source_language] + optimal_path.pivot_languages + [target_language],
                'strategy': strategy.value,
                'quality_score': translation_result['estimated_quality'],
                'processing_time': processing_time,
                'intermediate_translations': translation_result['intermediate_results'],
                'confidence': translation_result['confidence']
            }
            
            logger.info(f"Traduction pivot completee en {processing_time:.2f}s, "
                       f"qualite estimee: {result['quality_score']:.2f}")
            
            return result
            
        except Exception as e:
            error_id = handle_error(
                create_translation_error(
                    f"Erreur traduction pivot: {str(e)}",
                    source_text=text[:100],
                    target_language=target_language
                ),
                context={
                    'source_language': source_language,
                    'target_language': target_language,
                    'strategy': strategy.value
                }
            )
            
            return {
                'translation': f"ERREUR_TRADUCTION_PIVOT_{error_id[:8]}",
                'path': [source_language, target_language],
                'quality_score': 0.0,
                'error': str(e)
            }
    
    def _find_optimal_pivot_path(self, 
                                source_lang: str, 
                                target_lang: str, 
                                strategy: PivotStrategy) -> PivotPath:
        """
        Trouve le chemin pivot optimal selon la strategie
        
        Args:
            source_lang: Langue source
            target_lang: Langue cible
            strategy: Strategie de selection
        
        Returns:
            Chemin pivot optimal
        """
        # Traduction directe si haute qualite
        direct_quality = self._get_translation_quality(source_lang, target_lang)
        if direct_quality >= 0.8 and strategy != PivotStrategy.SINGLE_PIVOT:
            return PivotPath(
                source_language=source_lang,
                target_language=target_lang,
                pivot_languages=[],
                strategy=PivotStrategy.DIRECT,
                estimated_quality=direct_quality
            )
        
        # Generer les chemins possibles selon la strategie
        possible_paths = []
        
        if strategy == PivotStrategy.SINGLE_PIVOT or strategy == PivotStrategy.QUALITY_PIVOT:
            # Essayer avec chaque langue pivot possible
            pivot_candidates = ['en', 'fr']  # Langues avec le plus de ressources
            
            for pivot_lang in pivot_candidates:
                if pivot_lang != source_lang and pivot_lang != target_lang:
                    path_quality = self._calculate_pivot_path_quality(
                        source_lang, [pivot_lang], target_lang
                    )
                    
                    possible_paths.append(PivotPath(
                        source_language=source_lang,
                        target_language=target_lang,
                        pivot_languages=[pivot_lang],
                        strategy=strategy,
                        estimated_quality=path_quality,
                        complexity_score=1.0  # Un seul pivot
                    ))
        
        if strategy == PivotStrategy.DUAL_PIVOT:
            # Essayer avec deux langues pivot
            pivot_pairs = [['en', 'fr'], ['fr', 'en']]
            
            for pivot_pair in pivot_pairs:
                if source_lang not in pivot_pair and target_lang not in pivot_pair:
                    path_quality = self._calculate_pivot_path_quality(
                        source_lang, pivot_pair, target_lang
                    )
                    
                    possible_paths.append(PivotPath(
                        source_language=source_lang,
                        target_language=target_lang,
                        pivot_languages=pivot_pair,
                        strategy=strategy,
                        estimated_quality=path_quality,
                        complexity_score=2.0  # Deux pivots
                    ))
        
        if strategy == PivotStrategy.CULTURAL_PIVOT:
            # Utiliser l'affinite culturelle pour choisir les pivots
            optimal_pivots = self.optimal_pivots.get(target_lang, ['en', 'fr'])
            
            for pivot_lang in optimal_pivots:
                if pivot_lang != source_lang:
                    # Bonus culturel
                    cultural_bonus = self._get_cultural_affinity(source_lang, target_lang) * 0.2
                    
                    path_quality = self._calculate_pivot_path_quality(
                        source_lang, [pivot_lang], target_lang
                    ) + cultural_bonus
                    
                    possible_paths.append(PivotPath(
                        source_language=source_lang,
                        target_language=target_lang,
                        pivot_languages=[pivot_lang],
                        strategy=strategy,
                        estimated_quality=min(1.0, path_quality),  # Cap a 1.0
                        complexity_score=1.0 + cultural_bonus
                    ))
        
        # Selectionner le meilleur chemin
        if not possible_paths:
            # Fallback vers traduction directe
            return PivotPath(
                source_language=source_lang,
                target_language=target_lang,
                pivot_languages=[],
                strategy=PivotStrategy.DIRECT,
                estimated_quality=direct_quality
            )
        
        # Trier par qualite estimee (puis par simplicite si egalite)
        possible_paths.sort(
            key=lambda p: (p.estimated_quality, -p.complexity_score), 
            reverse=True
        )
        
        return possible_paths[0]
    
    def _execute_pivot_translation(self, text: str, path: PivotPath) -> Dict[str, Any]:
        """
        Execute la traduction selon le chemin pivot
        
        Args:
            text: Texte a traduire
            path: Chemin de traduction
        
        Returns:
            Resultats de traduction avec intermediaires
        """
        if not path.pivot_languages:
            # Traduction directe
            return self._direct_translation(text, path.source_language, path.target_language)
        
        # Traduction par etapes
        current_text = text
        current_lang = path.source_language
        intermediate_results = []
        cumulative_quality = 1.0
        
        # Traduction vers chaque langue pivot
        for pivot_lang in path.pivot_languages:
            step_result = self._direct_translation(current_text, current_lang, pivot_lang)
            
            intermediate_results.append({
                'from': current_lang,
                'to': pivot_lang,
                'text': step_result['translation'],
                'quality': step_result['quality']
            })
            
            current_text = step_result['translation']
            current_lang = pivot_lang
            cumulative_quality *= step_result['quality']
        
        # Traduction finale vers la langue cible
        final_result = self._direct_translation(current_text, current_lang, path.target_language)
        cumulative_quality *= final_result['quality']
        
        intermediate_results.append({
            'from': current_lang,
            'to': path.target_language,
            'text': final_result['translation'],
            'quality': final_result['quality']
        })
        
        return {
            'final_translation': final_result['translation'],
            'estimated_quality': cumulative_quality,
            'confidence': min(0.9, cumulative_quality),  # Plus conservateur
            'intermediate_results': intermediate_results
        }
    
    def _direct_translation(self, text: str, source_lang: str, target_lang: str) -> Dict[str, Any]:
        """
        Execute une traduction directe
        
        Args:
            text: Texte a traduire
            source_lang: Langue source
            target_lang: Langue cible
        
        Returns:
            Resultat de traduction directe
        """
        try:
            # Utiliser le traducteur principal si disponible
            if self.primary_translator:
                translation = self.primary_translator.translate_text(
                    text, source_lang, target_lang
                )
            else:
                # Utiliser le traducteur de fallback
                if not self.fallback_translator:
                    self.fallback_translator = FallbackTranslator(source_lang, target_lang)
                translation = self.fallback_translator.translate(text)
            
            # Estimer la qualite
            quality = self._get_translation_quality(source_lang, target_lang)
            
            # Detecter les erreurs evidentes
            if not translation or translation.startswith("ERREUR_") or translation.startswith("TRADUCTION_IMPOSSIBLE"):
                quality *= 0.1  # Tres mauvaise qualite
            
            return {
                'translation': translation,
                'quality': quality,
                'method': 'primary' if self.primary_translator else 'fallback'
            }
            
        except Exception as e:
            logger.error(f"Erreur traduction directe {source_lang}->{target_lang}: {e}")
            return {
                'translation': f"ERREUR_TRADUCTION_DIRECTE_{source_lang}_{target_lang}",
                'quality': 0.0,
                'method': 'error'
            }
    
    def _get_translation_quality(self, source_lang: str, target_lang: str) -> float:
        """
        Estime la qualite de traduction pour une paire de langues
        
        Args:
            source_lang: Langue source
            target_lang: Langue cible
        
        Returns:
            Score de qualite (0.0 - 1.0)
        """
        # Verifier les deux directions
        quality = self.language_quality_matrix.get((source_lang, target_lang))
        if quality is not None:
            return quality
        
        # Essayer la direction inverse
        reverse_quality = self.language_quality_matrix.get((target_lang, source_lang))
        if reverse_quality is not None:
            return reverse_quality * 0.9  # Leger malus pour direction inverse
        
        # Qualite par defaut selon les langues
        if source_lang in ['en', 'fr'] and target_lang in ['en', 'fr']:
            return 0.95  # Tres bonne qualite entre langues principales
        elif source_lang in ['en', 'fr'] or target_lang in ['en', 'fr']:
            return 0.4   # Qualite moyenne avec une langue principale
        else:
            return 0.2   # Qualite faible entre langues peu dotees
    
    def _calculate_pivot_path_quality(self, source_lang: str, pivot_langs: List[str], target_lang: str) -> float:
        """
        Calcule la qualite estimee d'un chemin pivot
        
        Args:
            source_lang: Langue source
            pivot_langs: Liste des langues pivot
            target_lang: Langue cible
        
        Returns:
            Qualite estimee du chemin complet
        """
        current_lang = source_lang
        cumulative_quality = 1.0
        
        # Qualite pour chaque etape
        for pivot_lang in pivot_langs:
            step_quality = self._get_translation_quality(current_lang, pivot_lang)
            cumulative_quality *= step_quality
            current_lang = pivot_lang
        
        # Etape finale
        final_quality = self._get_translation_quality(current_lang, target_lang)
        cumulative_quality *= final_quality
        
        # Penalite pour la complexite (plus d'etapes = plus de perte)
        complexity_penalty = 0.95 ** len(pivot_langs)
        
        return cumulative_quality * complexity_penalty
    
    def _get_cultural_affinity(self, lang1: str, lang2: str) -> float:
        """
        Retourne l'affinite culturelle entre deux langues
        
        Args:
            lang1: Premiere langue
            lang2: Deuxieme langue
        
        Returns:
            Score d'affinite (0.0 - 1.0)
        """
        affinity = self.cultural_affinity.get((lang1, lang2))
        if affinity is not None:
            return affinity
        
        # Essayer la direction inverse
        affinity = self.cultural_affinity.get((lang2, lang1))
        if affinity is not None:
            return affinity
        
        # Affinite par defaut
        if lang1 == lang2:
            return 1.0
        else:
            return 0.1  # Affinite faible par defaut
    
    def get_pivot_recommendations(self, source_lang: str, target_lang: str) -> List[Dict[str, Any]]:
        """
        Retourne des recommandations de strategies pivot
        
        Args:
            source_lang: Langue source
            target_lang: Langue cible
        
        Returns:
            Liste des recommandations triees par qualite
        """
        recommendations = []
        
        for strategy in PivotStrategy:
            try:
                path = self._find_optimal_pivot_path(source_lang, target_lang, strategy)
                
                recommendations.append({
                    'strategy': strategy.value,
                    'path': [source_lang] + path.pivot_languages + [target_lang],
                    'estimated_quality': path.estimated_quality,
                    'complexity': path.complexity_score,
                    'recommended': path.estimated_quality > 0.5
                })
            except Exception as e:
                logger.warning(f"Erreur evaluation strategie {strategy}: {e}")
        
        # Trier par qualite estimee
        recommendations.sort(key=lambda r: r['estimated_quality'], reverse=True)
        
        return recommendations
    
    def benchmark_translation_paths(self, text: str, source_lang: str, target_lang: str) -> Dict[str, Any]:
        """
        Compare toutes les strategies pour un texte donne
        
        Args:
            text: Texte de test
            source_lang: Langue source
            target_lang: Langue cible
        
        Returns:
            Comparaison des resultats
        """
        results = {}
        
        for strategy in PivotStrategy:
            try:
                result = self.translate_with_pivot(text, source_lang, target_lang, strategy)
                results[strategy.value] = result
            except Exception as e:
                results[strategy.value] = {'error': str(e), 'quality_score': 0.0}
        
        # Identifier la meilleure strategie
        best_strategy = max(results.keys(), 
                          key=lambda s: results[s].get('quality_score', 0.0))
        
        return {
            'results': results,
            'best_strategy': best_strategy,
            'quality_ranking': sorted(
                results.keys(), 
                key=lambda s: results[s].get('quality_score', 0.0), 
                reverse=True
            )
        }


if __name__ == "__main__":
    # Test du traducteur pivot
    pivot_translator = PivotLanguageTranslator()
    
    test_text = "L'histoire du royaume du Dahomey au Benin est fascinante."
    
    # Test de toutes les strategies
    benchmark = pivot_translator.benchmark_translation_paths(
        test_text, 'fr', 'fon'
    )
    
    print(f"Texte original: {test_text}")
    print(f"Meilleure strategie: {benchmark['best_strategy']}")
    
    # Afficher les resultats
    for strategy, result in benchmark['results'].items():
        print(f"\n{strategy}:")
        print(f"  Qualite: {result.get('quality_score', 0.0):.2f}")
        print(f"  Chemin: {' -> '.join(result.get('path', []))}")
        if 'translation' in result:
            print(f"  Traduction: {result['translation'][:100]}...")
    
    # Recommandations
    recommendations = pivot_translator.get_pivot_recommendations('fr', 'fon')
    print(f"\nRecommandations pour fr->fon:")
    for rec in recommendations[:3]:
        print(f"  {rec['strategy']}: qualite {rec['estimated_quality']:.2f}, "
              f"chemin {' -> '.join(rec['path'])}")