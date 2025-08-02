#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# src/utils/schemas.py

"""
Schémas Pydantic pour la validation des données JSON dans WikiTranslateAI
"""

from typing import List, Dict, Optional, Union, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from enum import Enum


# =============================================================================
# ENUMS ET TYPES DE BASE
# =============================================================================

class LanguageCode(str, Enum):
    """Codes des langues supportées"""
    FRENCH = "fr"
    ENGLISH = "en"  
    YORUBA = "yor"
    YORUBA_ALT = "yo"
    FON = "fon"
    FONGBE = "fongbe"
    EWE = "ewe"
    DINDI = "dindi"
    DENDI = "dendi"


class ToneType(str, Enum):
    """Types de tons"""
    HIGH = "high"
    LOW = "low"
    MID = "mid"
    RISING = "rising"
    FALLING = "falling"
    EXTRA_HIGH = "extra_high"
    EXTRA_LOW = "extra_low"


class TaskStatus(str, Enum):
    """Statuts des tâches"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class Priority(str, Enum):
    """Niveaux de priorité"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# MÉTADONNÉES ET CONFIGURATION
# =============================================================================

class ArticleMetadata(BaseModel):
    """Métadonnées d'un article Wikipedia"""
    title: str = Field(..., min_length=1, description="Titre de l'article")
    pageid: int = Field(..., gt=0, description="ID de la page Wikipedia")
    language: LanguageCode = Field(..., description="Code de langue")
    categories: List[str] = Field(default_factory=list, description="Catégories de l'article")
    sections: Optional[List[Dict[str, Any]]] = Field(default=None, description="Structure des sections")
    word_count: Optional[int] = Field(default=None, ge=0, description="Nombre de mots")
    last_modified: Optional[datetime] = Field(default=None, description="Dernière modification")
    
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class TranslationMetadata(BaseModel):
    """Métadonnées pour une traduction"""
    source_language: LanguageCode = Field(..., description="Langue source")
    target_language: LanguageCode = Field(..., description="Langue cible") 
    translation_date: datetime = Field(default_factory=datetime.now, description="Date de traduction")
    translator_model: str = Field(default="gpt-4o-mini", description="Modèle utilisé pour la traduction")
    use_glossary: bool = Field(default=True, description="Utilisation du glossaire")
    post_processed: bool = Field(default=False, description="Post-traitement appliqué")
    
    @field_validator('target_language')
    def validate_target_language(cls, v):
        """Valide que la langue cible est une langue africaine supportée"""
        african_languages = {LanguageCode.YORUBA, LanguageCode.YORUBA_ALT, 
                           LanguageCode.FON, LanguageCode.FONGBE, 
                           LanguageCode.EWE, LanguageCode.DINDI, LanguageCode.DENDI}
        if v not in african_languages:
            raise ValueError(f'Langue cible doit être une langue africaine: {african_languages}')
        return v
    
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )


# =============================================================================
# STRUCTURES D'ARTICLES
# =============================================================================

class ArticleSection(BaseModel):
    """Section d'un article"""
    title: str = Field(..., description="Titre de la section")
    level: int = Field(..., ge=0, le=6, description="Niveau de la section (0-6)")
    content: Optional[str] = Field(default=None, description="Contenu de la section")
    segments: Optional[List[str]] = Field(default=None, description="Segments de la section")
    subsections: Optional[List['ArticleSection']] = Field(default=None, description="Sous-sections")


class RawArticle(BaseModel):
    """Article Wikipedia brut"""
    title: str = Field(..., min_length=1, description="Titre de l'article")
    metadata: ArticleMetadata = Field(..., description="Métadonnées")
    content: str = Field(..., description="Contenu HTML brut de l'article")
    extracted_date: datetime = Field(default_factory=datetime.now, description="Date d'extraction")
    
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class SegmentedArticle(BaseModel):
    """Article segmenté en sections et paragraphes"""
    title: str = Field(..., min_length=1)
    metadata: ArticleMetadata = Field(...)
    segmented_sections: List[ArticleSection] = Field(..., min_length=1, description="Sections segmentées")
    total_segments: int = Field(..., ge=0, description="Nombre total de segments")
    segmentation_date: datetime = Field(default_factory=datetime.now)
    
    @model_validator(mode='after')
    def validate_total_segments(self):
        """Valide que le nombre total de segments correspond aux sections"""
        if self.segmented_sections:
            actual_count = sum(len(section.segments or []) for section in self.segmented_sections)
            if self.total_segments != actual_count:
                raise ValueError(f'Total segments ({self.total_segments}) ne correspond pas au compte réel ({actual_count})')
        return self
    
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class TranslatedSection(BaseModel):
    """Section traduite"""
    title: str = Field(..., description="Titre traduit de la section")
    level: int = Field(..., ge=0, le=6)
    segments: List[str] = Field(..., description="Segments traduits")
    original_segments: Optional[List[str]] = Field(default=None, description="Segments originaux")
    translation_quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Score de qualité")


class TranslatedArticle(BaseModel):
    """Article traduit"""
    title: str = Field(..., min_length=1, description="Titre traduit")
    original_title: str = Field(..., min_length=1, description="Titre original")
    metadata: ArticleMetadata = Field(..., description="Métadonnées originales")
    translation_metadata: TranslationMetadata = Field(..., description="Métadonnées de traduction")
    translated_sections: List[TranslatedSection] = Field(..., min_length=1, description="Sections traduites")
    translation_stats: Optional[Dict[str, Any]] = Field(default=None, description="Statistiques de traduction")


# =============================================================================
# DONNÉES TONALES
# =============================================================================

class TonalWordEntry(BaseModel):
    """Entrée de mot dans le lexique tonal"""
    tones: List[ToneType] = Field(..., min_length=1, description="Séquence de tons")
    syllables: List[str] = Field(..., min_length=1, description="Syllabes du mot")
    pos: Optional[str] = Field(default=None, description="Partie du discours")
    meaning: Optional[str] = Field(default=None, description="Signification")
    
    @model_validator(mode='after')
    def validate_tones_syllables_match(self):
        """Valide que le nombre de tons correspond au nombre de syllabes"""
        if len(self.tones) != len(self.syllables):
            raise ValueError(f'Le nombre de tons ({len(self.tones)}) doit correspondre au nombre de syllabes ({len(self.syllables)})')
        return self


class TonalLexiconMetadata(BaseModel):
    """Métadonnées du lexique tonal"""
    language: str = Field(..., description="Nom de la langue")
    tone_system: str = Field(..., description="Type de système tonal")
    description: str = Field(..., description="Description du lexique")
    version: Optional[str] = Field(default="1.0", description="Version du lexique")
    created_date: Optional[datetime] = Field(default_factory=datetime.now, description="Date de création")
    
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class TonalLexicon(BaseModel):
    """Lexique tonal complet"""
    metadata: TonalLexiconMetadata = Field(..., description="Métadonnées")
    words: Dict[str, TonalWordEntry] = Field(..., min_length=1, description="Dictionnaire des mots")
    
    @field_validator('words')
    def validate_words_not_empty(cls, v):
        """Valide que le lexique contient au moins quelques mots"""
        if len(v) < 1:
            raise ValueError('Le lexique doit contenir au moins un mot')
        return v


class SandhiRule(BaseModel):
    """Règle de sandhi tonal"""
    name: str = Field(..., min_length=1, description="Nom de la règle")
    description: str = Field(..., description="Description de la règle")
    pattern: str = Field(..., description="Motif de la règle")
    context: str = Field(..., description="Contexte d'application")
    transformation: str = Field(..., description="Transformation effectuée")
    examples: List[str] = Field(default_factory=list, description="Exemples d'application")


class SandhiRules(BaseModel):
    """Collection de règles de sandhi pour une langue"""
    language: str = Field(..., description="Langue cible")
    rules: List[SandhiRule] = Field(..., description="Liste des règles")
    version: Optional[str] = Field(default="1.0", description="Version des règles")


# =============================================================================
# DONNÉES DE GLOSSAIRE
# =============================================================================

class GlossaryEntry(BaseModel):
    """Entrée de glossaire"""
    source_term: str = Field(..., min_length=1, description="Terme source")
    target_term: str = Field(..., min_length=1, description="Terme cible")
    source_language: LanguageCode = Field(..., description="Langue source")
    target_language: LanguageCode = Field(..., description="Langue cible")
    domain: Optional[str] = Field(default="general", description="Domaine spécialisé")
    confidence: Optional[float] = Field(default=1.0, ge=0.0, le=1.0, description="Niveau de confiance")
    context: Optional[str] = Field(default=None, description="Contexte d'usage")
    created_date: datetime = Field(default_factory=datetime.now, description="Date de création")
    
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class Glossary(BaseModel):
    """Glossaire complet"""
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Métadonnées du glossaire")
    entries: List[GlossaryEntry] = Field(..., min_length=1, description="Entrées du glossaire")
    version: str = Field(default="1.0", description="Version du glossaire")
    
    @field_validator('entries')
    def validate_unique_entries(cls, v):
        """Valide l'unicité des entrées source-cible"""
        seen = set()
        for entry in v:
            key = (entry.source_term.lower(), entry.target_term.lower(), 
                   entry.source_language, entry.target_language)
            if key in seen:
                raise ValueError(f'Entrée dupliquée: {entry.source_term} -> {entry.target_term}')
            seen.add(key)
        return v


# =============================================================================
# DONNÉES DE SUIVI ET PROGRESSION
# =============================================================================

class SubTask(BaseModel):
    """Sous-tâche dans le système de suivi"""
    description: str = Field(..., min_length=1, description="Description de la sous-tâche")
    status: TaskStatus = Field(default=TaskStatus.NOT_STARTED, description="Statut")
    estimated_hours: float = Field(..., ge=0, description="Heures estimées")
    completed_date: Optional[datetime] = Field(default=None, description="Date de completion")
    
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class ProjectStep(BaseModel):
    """Étape de projet dans le roadmap"""
    name: str = Field(..., min_length=1, description="Nom de l'étape")
    status: TaskStatus = Field(default=TaskStatus.NOT_STARTED, description="Statut")
    priority: Priority = Field(..., description="Priorité")
    estimated_hours: int = Field(..., ge=0, description="Heures estimées")
    assigned_to: Optional[str] = Field(default=None, description="Assigné à")
    start_date: Optional[datetime] = Field(default=None, description="Date de début")
    end_date: Optional[datetime] = Field(default=None, description="Date de fin")
    blockers: List[str] = Field(default_factory=list, description="Bloqueurs")
    dependencies: List[str] = Field(default_factory=list, description="Dépendances")
    subtasks: Dict[str, SubTask] = Field(default_factory=dict, description="Sous-tâches")
    
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class PhaseProgress(BaseModel):
    """Progrès d'une phase"""
    completed: int = Field(default=0, ge=0, description="Tâches terminées")
    total: int = Field(..., ge=0, description="Total des tâches")
    percentage: int = Field(default=0, ge=0, le=100, description="Pourcentage de completion")
    
    @model_validator(mode='after')
    def calculate_percentage(self):
        """Calcule le pourcentage basé sur completed/total"""
        if self.total > 0:
            calculated = int((self.completed / self.total) * 100)
            self.percentage = calculated
        return self


class ProjectPhase(BaseModel):
    """Phase de projet"""
    name: str = Field(..., min_length=1, description="Nom de la phase")
    priority: Priority = Field(..., description="Priorité")
    status: TaskStatus = Field(default=TaskStatus.NOT_STARTED, description="Statut")
    duration_estimate: str = Field(..., description="Estimation de durée")
    progress: PhaseProgress = Field(..., description="Progrès")
    dependencies: List[str] = Field(default_factory=list, description="Dépendances")
    steps: Dict[str, ProjectStep] = Field(..., description="Étapes de la phase")


class ProjectInfo(BaseModel):
    """Informations générales du projet"""
    name: str = Field(..., min_length=1, description="Nom du projet")
    version: str = Field(..., description="Version")
    last_updated: str = Field(..., description="Dernière mise à jour")
    current_phase: str = Field(..., description="Phase actuelle")
    overall_progress: str = Field(..., description="Progrès global")


class TeamNote(BaseModel):
    """Note d'équipe"""
    date: str = Field(..., description="Date de la note")
    author: str = Field(..., min_length=1, description="Auteur")
    note: str = Field(..., min_length=1, description="Contenu de la note")


class ProjectBlocker(BaseModel):
    """Bloqueur de projet"""
    id: str = Field(..., min_length=1, description="ID du bloqueur")
    description: str = Field(..., min_length=1, description="Description")
    severity: Priority = Field(..., description="Sévérité")
    affects: List[str] = Field(..., description="Éléments affectés")
    created_date: str = Field(..., description="Date de création")
    status: Literal["open", "resolved"] = Field(..., description="Statut")
    resolved_date: Optional[str] = Field(default=None, description="Date de résolution")


class NextAction(BaseModel):
    """Action suivante recommandée"""
    action: str = Field(..., min_length=1, description="Description de l'action")
    priority: Priority = Field(..., description="Priorité")
    estimated_hours: int = Field(..., ge=0, description="Heures estimées")
    can_start_immediately: bool = Field(..., description="Peut commencer immédiatement")


class ProjectMetrics(BaseModel):
    """Métriques du projet"""
    total_estimated_hours: int = Field(default=0, ge=0, description="Heures totales estimées")
    critical_bugs_fixed: int = Field(default=0, ge=0, description="Bugs critiques corrigés")
    performance_improvements: int = Field(default=0, ge=0, description="Améliorations de performance")
    new_features_added: int = Field(default=0, ge=0, description="Nouvelles fonctionnalités")
    test_coverage: str = Field(default="0%", description="Couverture de test")
    documentation_coverage: str = Field(default="0%", description="Couverture documentation")


class ProgressTracker(BaseModel):
    """Tracker de progression complet"""
    project_info: ProjectInfo = Field(..., description="Informations projet")
    phases: Dict[str, ProjectPhase] = Field(..., description="Phases du projet")
    metrics: ProjectMetrics = Field(..., description="Métriques")
    current_blockers: List[ProjectBlocker] = Field(default_factory=list, description="Bloqueurs actuels")
    next_actions: List[NextAction] = Field(default_factory=list, description="Actions suivantes")
    team_notes: List[TeamNote] = Field(default_factory=list, description="Notes d'équipe")


# =============================================================================
# DONNÉES DE TRADUCTION ET STATISTIQUES
# =============================================================================

class TranslationStats(BaseModel):
    """Statistiques de traduction"""
    project_start: str = Field(..., description="Début du projet")
    last_translation: Optional[str] = Field(default=None, description="Dernière traduction")
    total_global: int = Field(default=0, ge=0, description="Total global")
    total_by_language: Dict[str, int] = Field(default_factory=dict, description="Total par paire de langues")
    daily_progress: Dict[str, Dict[str, int]] = Field(default_factory=dict, description="Progrès quotidien")
    categories: Dict[str, int] = Field(default_factory=dict, description="Compteurs par catégorie")


# =============================================================================
# RÈGLES LINGUISTIQUES
# =============================================================================

class NounClass(BaseModel):
    """Classe nominale"""
    name: str = Field(..., description="Nom de la classe")
    singular_prefix: str = Field(default="", description="Préfixe singulier")
    plural_prefix: str = Field(default="", description="Préfixe pluriel")
    singular_suffix: str = Field(default="", description="Suffixe singulier")
    plural_suffix: str = Field(default="", description="Suffixe pluriel")
    examples: List[str] = Field(default_factory=list, description="Exemples")


class VerbTense(BaseModel):
    """Temps verbal"""
    name: str = Field(..., description="Nom du temps")
    marker: str = Field(..., description="Marqueur temporel")
    position: str = Field(..., description="Position du marqueur")
    examples: List[str] = Field(default_factory=list, description="Exemples")


class Pronoun(BaseModel):
    """Pronom"""
    person: str = Field(..., description="Personne grammaticale")
    form: str = Field(..., description="Forme du pronom")
    meaning: str = Field(..., description="Signification")


class PronounSet(BaseModel):
    """Set de pronoms"""
    personal: List[Pronoun] = Field(default_factory=list, description="Pronoms personnels")
    possessive: List[Pronoun] = Field(default_factory=list, description="Pronoms possessifs")


class SpecialRule(BaseModel):
    """Règle linguistique spéciale"""
    name: str = Field(..., description="Nom de la règle")
    pattern: str = Field(..., description="Motif")
    examples: List[str] = Field(default_factory=list, description="Exemples")


class LinguisticRules(BaseModel):
    """Règles linguistiques complètes"""
    name: str = Field(..., description="Nom des règles")
    description: str = Field(..., description="Description")
    noun_classes: List[NounClass] = Field(default_factory=list, description="Classes nominales")
    verb_tenses: List[VerbTense] = Field(default_factory=list, description="Temps verbaux")
    pronouns: PronounSet = Field(default_factory=PronounSet, description="Pronoms")
    word_order: str = Field(default="SVO", description="Ordre des mots")
    adjective_position: str = Field(default="after_noun", description="Position des adjectifs")
    special_rules: List[SpecialRule] = Field(default_factory=list, description="Règles spéciales")


# =============================================================================
# FONCTIONS UTILITAIRES DE VALIDATION
# =============================================================================

def normalize_priority(priority_str: str) -> str:
    """Normalise les priorités françaises vers anglaises"""
    priority_mapping = {
        'CRITIQUE': 'critical',
        'HAUTE': 'high', 
        'MOYENNE': 'medium',
        'BASSE': 'low',
        'critique': 'critical',
        'haute': 'high',
        'moyenne': 'medium', 
        'basse': 'low'
    }
    return priority_mapping.get(priority_str, priority_str.lower())


def normalize_task_status(status_str: str) -> str:
    """Normalise les statuts de tâches"""
    status_mapping = {
        'non_commencé': 'not_started',
        'en_cours': 'in_progress',
        'terminé': 'completed',
        'bloqué': 'blocked'
    }
    return status_mapping.get(status_str, status_str.lower())

def normalize_progress_tracker_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise les données du ProgressTracker pour la validation"""
    normalized = data.copy()
    
    # Normaliser les priorités dans les phases
    if 'phases' in normalized:
        for phase_key, phase_data in normalized['phases'].items():
            if 'priority' in phase_data:
                phase_data['priority'] = normalize_priority(phase_data['priority'])
            
            # Normaliser les priorités dans les steps
            if 'steps' in phase_data:
                for step_key, step_data in phase_data['steps'].items():
                    if 'priority' in step_data:
                        step_data['priority'] = normalize_priority(step_data['priority'])
                    if 'status' in step_data:
                        step_data['status'] = normalize_task_status(step_data['status'])
    
    # Normaliser les priorités dans les bloqueurs
    if 'current_blockers' in normalized:
        for blocker in normalized['current_blockers']:
            if 'severity' in blocker:
                blocker['severity'] = normalize_priority(blocker['severity'])
    
    # Normaliser les priorités dans les actions suivantes
    if 'next_actions' in normalized:
        for action in normalized['next_actions']:
            if 'priority' in action:
                action['priority'] = normalize_priority(action['priority'])
    
    return normalized


def validate_json_with_schema(data: Dict[str, Any], schema_class: BaseModel, normalize_data: bool = True) -> BaseModel:
    """
    Valide des données JSON avec un schéma Pydantic
    
    Args:
        data: Données JSON à valider
        schema_class: Classe Pydantic pour la validation
        normalize_data: Si True, normalise les données avant validation
        
    Returns:
        Instance validée du modèle
        
    Raises:
        ValueError: Si les données ne sont pas valides
    """
    try:
        # Normaliser les données si nécessaire
        if normalize_data and schema_class == ProgressTracker:
            data = normalize_progress_tracker_data(data)
        
        return schema_class(**data)
    except Exception as e:
        raise ValueError(f"Validation échouée pour {schema_class.__name__}: {e}")


def get_schema_for_file_type(file_type: str) -> Optional[BaseModel]:
    """
    Retourne le schéma approprié pour un type de fichier
    
    Args:
        file_type: Type de fichier ('raw_article', 'translated_article', etc.)
        
    Returns:
        Classe de schéma appropriée ou None
    """
    schema_mapping = {
        'raw_article': RawArticle,
        'segmented_article': SegmentedArticle,
        'translated_article': TranslatedArticle,
        'tonal_lexicon': TonalLexicon,
        'sandhi_rules': SandhiRules,
        'glossary': Glossary,
        'progress_tracker': ProgressTracker,
        'translation_stats': TranslationStats,
        'linguistic_rules': LinguisticRules
    }
    
    return schema_mapping.get(file_type)


# Permettre la référence circulaire pour ArticleSection
ArticleSection.model_rebuild()