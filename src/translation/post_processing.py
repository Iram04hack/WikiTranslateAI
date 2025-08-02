#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# src/translation/post_processing.py

import os
import re
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Imports des modules d'adaptation
from ..adaptation.tonal_processor import TonalProcessor
from ..adaptation.orthographic_adapter import OrthographicAdapter
from ..adaptation.linguistic_adapter import LinguisticAdapter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PostProcessor:
    """Processeur de post-traitement pour les traductions"""
    
    def __init__(self, data_dir=None):
        """
        Initialise le post-processeur
        
        Args:
            data_dir: Repertoire de donnees (optionnel)
        """
        self.data_dir = data_dir or "data"
        
        # Initialiser les composants d'adaptation
        try:
            self.tonal_processor = TonalProcessor(os.path.join(self.data_dir, "tonal"))
            logger.info("Processeur tonal initialise")
        except Exception as e:
            logger.warning(f"Impossible d'initialiser le processeur tonal: {e}")
            self.tonal_processor = None
        
        try:
            self.orthographic_adapter = OrthographicAdapter(
                os.path.join(self.data_dir, "rules", "orthographic")
            )
            logger.info("Adaptateur orthographique initialise")
        except Exception as e:
            logger.warning(f"Impossible d'initialiser l'adaptateur orthographique: {e}")
            self.orthographic_adapter = None
        
        try:
            self.linguistic_adapter = LinguisticAdapter(
                os.path.join(self.data_dir, "rules", "linguistic")
            )
            logger.info("Adaptateur linguistique initialise")
        except Exception as e:
            logger.warning(f"Impossible d'initialiser l'adaptateur linguistique: {e}")
            self.linguistic_adapter = None
        
        # Configuration des etapes de post-processing
        self.processing_steps = {
            'clean_text': True,
            'apply_orthographic_rules': True,
            'apply_tonal_processing': True,
            'validate_linguistic_rules': True,
            'final_cleanup': True
        }
    
    def enable_step(self, step_name: str, enabled: bool = True):
        """Active ou desactive une etape de post-processing"""
        if step_name in self.processing_steps:
            self.processing_steps[step_name] = enabled
            logger.info(f"Etape '{step_name}' {'activee' if enabled else 'desactivee'}")
        else:
            logger.warning(f"Etape '{step_name}' inconnue")
    
    def clean_text(self, text: str) -> str:
        """Nettoie le texte de base"""
        if not text or not text.strip():
            return text
        
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer les espaces en debut et fin
        text = text.strip()
        
        # Corriger la ponctuation mal espacee
        text = re.sub(r'\s+([,.!?;:])', r'\1', text)
        text = re.sub(r'([,.!?;:])\s*', r'\1 ', text)
        
        # Supprimer les caracteres de controle
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        return text.strip()
    
    def apply_orthographic_rules(self, text: str, language: str) -> str:
        """Applique les regles orthographiques specifiques a la langue"""
        if not self.orthographic_adapter or not text:
            return text
        
        try:
            # Appliquer les regles orthographiques
            adapted_text = self.orthographic_adapter.normalize_text(text, language)
            logger.debug(f"Regles orthographiques appliquees pour {language}")
            return adapted_text
        except Exception as e:
            logger.error(f"Erreur lors de l'application des regles orthographiques: {e}")
            return text
    
    def apply_tonal_processing(self, text: str, language: str) -> str:
        """Applique le traitement tonal au texte"""
        if not self.tonal_processor or not text:
            return text
        
        # Verifier si la langue supporte les tons
        tonal_languages = ['yor', 'yoruba', 'fon', 'fongbe', 'ewe', 'dindi', 'dendi']
        if language.lower() not in tonal_languages:
            logger.debug(f"Langue {language} non tonale, traitement tonal ignore")  
            return text
        
        try:
            # Appliquer le traitement tonal
            processed_text = self.tonal_processor.process_text(text, language)
            
            # Valider les tons appliques
            errors = self.tonal_processor.validate_tones(processed_text, language)
            if errors:
                logger.warning(f"Erreurs tonales detectees dans le texte traite:")
                for error in errors[:3]:  # Limiter le nombre d'erreurs affichees
                    logger.warning(f"  - {error}")
            
            logger.debug(f"Traitement tonal applique pour {language}")
            return processed_text
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement tonal: {e}")
            return text
    
    def validate_linguistic_rules(self, text: str, language: str) -> str:
        """Valide et applique les regles linguistiques"""
        if not self.linguistic_adapter or not text:
            return text
        
        try:
            # Pour l'instant, juste charger les regles pour validation
            rules = self.linguistic_adapter.load_rules(language)
            if rules:
                logger.debug(f"Regles linguistiques validees pour {language}")
            
            # TODO: Implementer des validations specifiques
            # Par exemple, verifier l'ordre des mots, la conjugaison, etc.
            
            return text
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation linguistique: {e}")
            return text
    
    def final_cleanup(self, text: str) -> str:
        """Nettoyage final du texte"""
        if not text:
            return text
        
        # Derniere passe de nettoyage
        text = re.sub(r'\s+', ' ', text)  # Espaces multiples
        text = re.sub(r'\s+([.!?])', r'\1', text)  # Espaces avant ponctuation finale
        text = text.strip()
        
        # Capitaliser la premiere lettre si necessaire
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        
        return text
    
    def process_text(self, text: str, language: str, 
                    custom_steps: Optional[Dict[str, bool]] = None) -> str:
        """
        Traite un texte avec toutes les etapes de post-processing
        
        Args:
            text: Texte a traiter
            language: Code de langue cible
            custom_steps: Configuration personnalisee des etapes (optionnel)
            
        Returns:
            Texte post-traite
        """
        if not text or not text.strip():
            return text
        
        # Utiliser la configuration personnalisee si fournie
        steps = custom_steps or self.processing_steps
        
        processed_text = text
        original_text = text
        
        logger.info(f"Debut du post-processing pour '{language}'")
        logger.debug(f"Texte original: {original_text[:100]}...")
        
        # Etape 1: Nettoyage de base
        if steps.get('clean_text', True):
            processed_text = self.clean_text(processed_text)
            logger.debug("Nettoyage de base effectue")
        
        # Etape 2: Regles orthographiques
        if steps.get('apply_orthographic_rules', True):
            processed_text = self.apply_orthographic_rules(processed_text, language)
            logger.debug("Regles orthographiques appliquees")
        
        # Etape 3: Traitement tonal (crucial pour les langues africaines)
        if steps.get('apply_tonal_processing', True):
            processed_text = self.apply_tonal_processing(processed_text, language)
            logger.debug("Traitement tonal applique")
        
        # Etape 4: Validation linguistique
        if steps.get('validate_linguistic_rules', True):
            processed_text = self.validate_linguistic_rules(processed_text, language)
            logger.debug("Validation linguistique effectuee")
        
        # Etape 5: Nettoyage final
        if steps.get('final_cleanup', True):
            processed_text = self.final_cleanup(processed_text)
            logger.debug("Nettoyage final effectue")
        
        logger.info(f"Post-processing termine")
        logger.debug(f"Texte final: {processed_text[:100]}...")
        
        return processed_text
    
    def process_segments(self, segments: List[str], language: str,
                        custom_steps: Optional[Dict[str, bool]] = None) -> List[str]:
        """
        Traite une liste de segments de texte
        
        Args:
            segments: Liste des segments a traiter
            language: Code de langue cible
            custom_steps: Configuration personnalisee des etapes
            
        Returns:
            Liste des segments post-traites
        """
        if not segments:
            return segments
        
        processed_segments = []
        total_segments = len(segments)
        
        logger.info(f"Traitement de {total_segments} segments en {language}")
        
        for i, segment in enumerate(segments):
            if i % 10 == 0:  # Log de progression tous les 10 segments
                logger.info(f"Traitement segment {i+1}/{total_segments}")
            
            processed_segment = self.process_text(segment, language, custom_steps)
            processed_segments.append(processed_segment)
        
        logger.info(f"Traitement de {total_segments} segments termine")
        return processed_segments
    
    def get_processing_stats(self) -> Dict:
        """Retourne des statistiques sur les composants de post-processing"""
        stats = {
            'components': {
                'tonal_processor': self.tonal_processor is not None,
                'orthographic_adapter': self.orthographic_adapter is not None, 
                'linguistic_adapter': self.linguistic_adapter is not None
            },
            'enabled_steps': self.processing_steps.copy()
        }
        
        if self.tonal_processor:
            stats['tonal_languages'] = ['yor', 'fon', 'ewe', 'dindi']
        
        return stats
    
    def get_language_support(self, language: str) -> Dict:
        """Retourne les informations de support pour une langue donnee"""
        support_info = {
            'language': language,
            'orthographic_rules': False,
            'tonal_processing': False,
            'linguistic_rules': False
        }
        
        # Verifier le support orthographique
        if self.orthographic_adapter:
            try:
                rules = self.orthographic_adapter.load_rules(language)
                support_info['orthographic_rules'] = rules is not None
            except:
                pass
        
        # Verifier le support tonal
        if self.tonal_processor:
            tonal_languages = ['yor', 'yoruba', 'fon', 'fongbe', 'ewe', 'dindi', 'dendi']
            support_info['tonal_processing'] = language.lower() in tonal_languages
        
        # Verifier le support linguistique
        if self.linguistic_adapter:
            try:
                rules = self.linguistic_adapter.load_rules(language)
                support_info['linguistic_rules'] = rules is not None
            except:
                pass
        
        return support_info


def create_post_processor(data_dir=None):
    """Fonction utilitaire pour creer un post-processeur"""
    return PostProcessor(data_dir)