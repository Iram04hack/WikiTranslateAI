#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# src/utils/json_validator.py

"""
Module de validation JSON avec gestion d'erreurs gracieuse pour WikiTranslateAI
"""

import json
import logging
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
from contextlib import contextmanager

from .schemas import (
    validate_json_with_schema, get_schema_for_file_type,
    RawArticle, SegmentedArticle, TranslatedArticle,
    TonalLexicon, SandhiRules, Glossary, ProgressTracker,
    TranslationStats, LinguisticRules
)

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Erreur de validation JSON"""
    def __init__(self, message: str, file_path: Optional[str] = None, original_error: Optional[Exception] = None):
        self.message = message
        self.file_path = file_path
        self.original_error = original_error
        super().__init__(self.message)


class JSONValidator:
    """Validateur JSON avec gestion d'erreurs gracieuse"""
    
    def __init__(self, strict_mode: bool = False, log_errors: bool = True):
        """
        Initialise le validateur JSON
        
        Args:
            strict_mode: Si True, lève des exceptions pour toute erreur de validation
            log_errors: Si True, log les erreurs de validation
        """
        self.strict_mode = strict_mode
        self.log_errors = log_errors
        self.validation_errors = []  # Historique des erreurs
        
    def clear_errors(self):
        """Efface l'historique des erreurs"""
        self.validation_errors.clear()
    
    def get_errors(self) -> List[str]:
        """Retourne la liste des erreurs de validation"""
        return self.validation_errors.copy()
    
    def _log_error(self, error_msg: str, file_path: Optional[str] = None):
        """Log une erreur de validation"""
        self.validation_errors.append(error_msg)
        if self.log_errors:
            if file_path:
                logger.error(f"Erreur validation JSON [{file_path}]: {error_msg}")
            else:
                logger.error(f"Erreur validation JSON: {error_msg}")
    
    def _handle_validation_error(self, error: Exception, file_path: Optional[str] = None, context: str = ""):
        """Gère une erreur de validation selon le mode strict"""
        error_msg = f"{context}: {str(error)}" if context else str(error)
        self._log_error(error_msg, file_path)
        
        if self.strict_mode:
            raise ValidationError(error_msg, file_path, error)
    
    @contextmanager
    def validation_context(self, context: str, file_path: Optional[str] = None):
        """Contexte de validation avec gestion d'erreurs"""
        try:
            yield
        except Exception as e:
            self._handle_validation_error(e, file_path, context)
    
    def load_and_validate_json(self, file_path: str, schema_class: Optional[Any] = None, 
                              file_type: Optional[str] = None) -> Optional[Any]:
        """
        Charge et valide un fichier JSON
        
        Args:
            file_path: Chemin vers le fichier JSON
            schema_class: Classe de schéma Pydantic (optionnel)
            file_type: Type de fichier pour auto-détection du schéma (optionnel)
            
        Returns:
            Instance validée du modèle ou None en cas d'erreur (mode non-strict)
        """
        file_path = Path(file_path)
        
        # Vérifier que le fichier existe
        if not file_path.exists():
            error_msg = f"Fichier non trouvé: {file_path}"
            self._handle_validation_error(FileNotFoundError(error_msg), str(file_path))
            return None
        
        # Charger le JSON
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            error_msg = f"JSON invalide: {e}"
            self._handle_validation_error(e, str(file_path), "Chargement JSON")
            return None
        except Exception as e:
            error_msg = f"Erreur de lecture: {e}"
            self._handle_validation_error(e, str(file_path), "Lecture fichier")
            return None
        
        # Déterminer le schéma à utiliser
        if not schema_class and file_type:
            schema_class = get_schema_for_file_type(file_type)
        
        if not schema_class:
            if self.log_errors:
                logger.warning(f"Aucun schéma trouvé pour {file_path}, validation ignorée")
            return data  # Retourner les données brutes si pas de schéma
        
        # Valider avec le schéma
        with self.validation_context("Validation schéma", str(file_path)):
            validated = validate_json_with_schema(data, schema_class)
            if self.log_errors:
                logger.info(f"Validation réussie pour {file_path} avec {schema_class.__name__}")
            return validated
    
    def save_and_validate_json(self, data: Union[Dict[str, Any], Any], file_path: str, 
                              schema_class: Optional[Any] = None, 
                              file_type: Optional[str] = None,
                              indent: int = 2) -> bool:
        """
        Valide et sauvegarde des données en JSON
        
        Args:
            data: Données à sauvegarder (dict ou instance Pydantic)
            file_path: Chemin de sauvegarde
            schema_class: Classe de schéma pour validation (optionnel)
            file_type: Type de fichier pour auto-détection du schéma (optionnel)
            indent: Indentation JSON
            
        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        file_path = Path(file_path)
        
        # Convertir l'instance Pydantic en dict si nécessaire
        if hasattr(data, 'model_dump'):
            json_data = data.model_dump(mode='json')  # Mode JSON pour sérialisation datetime
        elif hasattr(data, 'dict'):  # Pydantic v1 compatibility
            json_data = data.dict()
        else:
            json_data = data
        
        # Déterminer le schéma à utiliser
        if not schema_class and file_type:
            schema_class = get_schema_for_file_type(file_type)
        
        # Valider avant sauvegarde si schéma disponible
        if schema_class:
            with self.validation_context("Validation avant sauvegarde", str(file_path)):
                validate_json_with_schema(json_data, schema_class)
        
        # Créer le répertoire parent si nécessaire
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=indent)
            
            if self.log_errors:
                logger.info(f"Sauvegarde JSON réussie: {file_path}")
            return True
            
        except Exception as e:
            error_msg = f"Erreur de sauvegarde: {e}"
            self._handle_validation_error(e, str(file_path), "Sauvegarde JSON")
            return False
    
    def validate_data(self, data: Dict[str, Any], schema_class: Any) -> Optional[Any]:
        """
        Valide des données avec un schéma
        
        Args:
            data: Données à valider
            schema_class: Classe de schéma Pydantic
            
        Returns:
            Instance validée ou None en cas d'erreur (mode non-strict)
        """
        with self.validation_context(f"Validation {schema_class.__name__}"):
            return validate_json_with_schema(data, schema_class)
    
    def batch_validate_files(self, file_paths: List[str], file_type: str) -> Dict[str, bool]:
        """
        Valide un lot de fichiers du même type
        
        Args:
            file_paths: Liste des chemins de fichiers
            file_type: Type de fichier pour déterminer le schéma
            
        Returns:
            Dictionnaire {file_path: validation_success}
        """
        schema_class = get_schema_for_file_type(file_type)
        if not schema_class:
            logger.warning(f"Aucun schéma trouvé pour le type {file_type}")
            return {fp: False for fp in file_paths}
        
        results = {}
        for file_path in file_paths:
            try:
                validated = self.load_and_validate_json(file_path, schema_class)
                results[file_path] = validated is not None
            except Exception as e:
                results[file_path] = False
                if self.log_errors:
                    logger.error(f"Échec validation {file_path}: {e}")
        
        return results
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Retourne des statistiques de validation"""
        return {
            'total_errors': len(self.validation_errors),
            'strict_mode': self.strict_mode,
            'log_errors': self.log_errors,
            'recent_errors': self.validation_errors[-5:] if self.validation_errors else []
        }


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def create_validator(strict: bool = False) -> JSONValidator:
    """Crée un validateur JSON avec configuration par défaut"""
    return JSONValidator(strict_mode=strict, log_errors=True)


def quick_validate_file(file_path: str, file_type: str, strict: bool = False) -> bool:
    """
    Validation rapide d'un fichier
    
    Args:
        file_path: Chemin du fichier
        file_type: Type de fichier
        strict: Mode strict
        
    Returns:
        True si valide, False sinon
    """
    validator = create_validator(strict)
    result = validator.load_and_validate_json(file_path, file_type=file_type)
    return result is not None


def safe_load_json_with_schema(file_path: str, schema_class: Any, default_value: Any = None) -> Any:
    """
    Charge un JSON avec validation, retourne une valeur par défaut en cas d'échec
    
    Args:
        file_path: Chemin du fichier
        schema_class: Classe de schéma
        default_value: Valeur par défaut en cas d'échec
        
    Returns:
        Données validées ou valeur par défaut
    """
    validator = create_validator(strict=False)
    result = validator.load_and_validate_json(file_path, schema_class)
    return result if result is not None else default_value


# =============================================================================
# INTÉGRATIONS SPÉCIFIQUES AUX MODULES
# =============================================================================

class TonalProcessorValidator:
    """Validateur spécialisé pour les données tonales"""
    
    def __init__(self):
        self.validator = create_validator(strict=False)
    
    def validate_lexicon(self, file_path: str) -> Optional[TonalLexicon]:
        """Valide un lexique tonal"""
        return self.validator.load_and_validate_json(file_path, TonalLexicon)
    
    def validate_sandhi_rules(self, file_path: str) -> Optional[SandhiRules]:
        """Valide des règles de sandhi"""
        return self.validator.load_and_validate_json(file_path, SandhiRules)


class ArticleValidator:
    """Validateur spécialisé pour les articles"""
    
    def __init__(self):
        self.validator = create_validator(strict=False)
    
    def validate_raw_article(self, file_path: str) -> Optional[RawArticle]:
        """Valide un article brut"""
        return self.validator.load_and_validate_json(file_path, RawArticle)
    
    def validate_segmented_article(self, file_path: str) -> Optional[SegmentedArticle]:
        """Valide un article segmenté"""
        return self.validator.load_and_validate_json(file_path, SegmentedArticle)
    
    def validate_translated_article(self, file_path: str) -> Optional[TranslatedArticle]:
        """Valide un article traduit"""
        return self.validator.load_and_validate_json(file_path, TranslatedArticle)


class ProgressValidator:
    """Validateur spécialisé pour le suivi de progression"""
    
    def __init__(self):
        self.validator = create_validator(strict=True)  # Mode strict pour les données critiques
    
    def validate_progress_tracker(self, file_path: str) -> Optional[ProgressTracker]:
        """Valide le tracker de progression"""
        return self.validator.load_and_validate_json(file_path, ProgressTracker)
    
    def save_progress_tracker(self, data: ProgressTracker, file_path: str) -> bool:
        """Sauvegarde le tracker de progression avec validation"""
        return self.validator.save_and_validate_json(data, file_path, ProgressTracker)