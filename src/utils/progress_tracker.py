# src/utils/progress_tracker.py

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """Statuts possibles pour les tâches"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"

class Priority(Enum):
    """Niveaux de priorité"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ProgressTracker:
    """Gestionnaire de progression pour WikiTranslateAI"""
    
    def __init__(self, json_file_path: str = "PROGRESS_TRACKER.json"):
        """
        Initialise le tracker de progression
        
        Args:
            json_file_path: Chemin vers le fichier JSON de progression
        """
        self.json_file_path = json_file_path
        self.data = self._load_or_create_progress_file()
    
    def _load_or_create_progress_file(self) -> Dict[str, Any]:
        """Charge ou crée le fichier de progression"""
        if os.path.exists(self.json_file_path):
            try:
                with open(self.json_file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Erreur lors du chargement de {self.json_file_path}: {e}")
                return self._create_default_structure()
        else:
            return self._create_default_structure()
    
    def _create_default_structure(self) -> Dict[str, Any]:
        """Crée la structure par défaut du fichier de progression"""
        return {
            "project_info": {
                "name": "WikiTranslateAI",
                "version": "1.0.0",
                "description": "Système de traduction d'articles Wikipedia vers les langues africaines",
                "target_languages": ["fon", "yoruba", "ewe", "dindi"],
                "last_updated": datetime.now().isoformat()
            },
            "phases": {
                "phase_1": {
                    "name": "Corrections Critiques",
                    "description": "Fixer les bugs critiques empêchant le fonctionnement",
                    "status": TaskStatus.NOT_STARTED.value,
                    "progress": 0.0,
                    "estimated_hours": 36,
                    "actual_hours": 0,
                    "steps": {
                        "step_1_1": {
                            "name": "Fixer API OpenAI",
                            "status": TaskStatus.NOT_STARTED.value,
                            "progress": 0.0,
                            "priority": Priority.CRITICAL.value,
                            "estimated_hours": 16,
                            "subtasks": {
                                "1_1_1": {"name": "Mettre à jour requirements.txt", "status": TaskStatus.NOT_STARTED.value, "hours": 0.5},
                                "1_1_2": {"name": "Refactoriser azure_client.py", "status": TaskStatus.NOT_STARTED.value, "hours": 4},
                                "1_1_3": {"name": "Modifier méthode translate_text()", "status": TaskStatus.NOT_STARTED.value, "hours": 6},
                                "1_1_4": {"name": "Tester traduction simple", "status": TaskStatus.NOT_STARTED.value, "hours": 2},
                                "1_1_5": {"name": "Valider avec article complet", "status": TaskStatus.NOT_STARTED.value, "hours": 3.5}
                            }
                        },
                        "step_1_2": {
                            "name": "Fixer problèmes d'imports",
                            "status": TaskStatus.NOT_STARTED.value,
                            "progress": 0.0,
                            "priority": Priority.HIGH.value,
                            "estimated_hours": 8
                        },
                        "step_1_3": {
                            "name": "Résoudre erreurs de configuration",
                            "status": TaskStatus.NOT_STARTED.value,
                            "progress": 0.0,
                            "priority": Priority.HIGH.value,
                            "estimated_hours": 6
                        },
                        "step_1_4": {
                            "name": "Tests de validation complète",
                            "status": TaskStatus.NOT_STARTED.value,
                            "progress": 0.0,
                            "priority": Priority.MEDIUM.value,
                            "estimated_hours": 6
                        }
                    }
                },
                "phase_2": {
                    "name": "Optimisations Performance",
                    "description": "Améliorer les performances et l'efficacité",
                    "status": TaskStatus.NOT_STARTED.value,
                    "progress": 0.0,
                    "estimated_hours": 48,
                    "actual_hours": 0
                },
                "phase_3": {
                    "name": "Nouvelles Fonctionnalités",
                    "description": "Ajouter des fonctionnalités avancées",
                    "status": TaskStatus.NOT_STARTED.value,
                    "progress": 0.0,
                    "estimated_hours": 72,
                    "actual_hours": 0
                }
            },
            "next_actions": [
                {
                    "action": "Fixer l'API OpenAI obsolète (v0.x ’ v1.x)",
                    "priority": Priority.CRITICAL.value,
                    "estimated_time": "16h",
                    "phase": "phase_1",
                    "step": "step_1_1"
                }
            ],
            "current_blockers": [
                {
                    "id": "blocker_001",
                    "description": "API OpenAI obsolète empêche tout fonctionnement",
                    "status": "open",
                    "priority": Priority.CRITICAL.value,
                    "created_date": datetime.now().isoformat(),
                    "phase": "phase_1",
                    "step": "step_1_1"
                }
            ],
            "metrics": {
                "total_estimated_hours": 156,
                "total_actual_hours": 0,
                "overall_progress": 0.0,
                "efficiency_ratio": 0.0,
                "files_implemented": 0,
                "tests_passing": 0,
                "translations_successful": 0
            }
        }
    
    def update_task_status(self, phase: str, step: str = None, subtask: str = None, 
                          status: TaskStatus = None, progress: float = None, 
                          actual_hours: float = None) -> bool:
        """
        Met à jour le statut d'une tâche
        
        Args:
            phase: ID de la phase (ex: "phase_1")
            step: ID de l'étape (ex: "step_1_1", optionnel)
            subtask: ID de la sous-tâche (ex: "1_1_1", optionnel)
            status: Nouveau statut
            progress: Nouveau pourcentage de progression (0.0-1.0)
            actual_hours: Heures réellement passées
            
        Returns:
            True si la mise à jour a réussi
        """
        try:
            # Valider que la phase existe
            if phase not in self.data["phases"]:
                logger.error(f"Phase {phase} non trouvée")
                return False
            
            # Déterminer la cible de la mise à jour
            if subtask and step:
                # Mise à jour d'une sous-tâche
                if (step not in self.data["phases"][phase]["steps"] or 
                    "subtasks" not in self.data["phases"][phase]["steps"][step] or
                    subtask not in self.data["phases"][phase]["steps"][step]["subtasks"]):
                    logger.error(f"Sous-tâche {phase}.{step}.{subtask} non trouvée")
                    return False
                target = self.data["phases"][phase]["steps"][step]["subtasks"][subtask]
            elif step:
                # Mise à jour d'une étape
                if step not in self.data["phases"][phase]["steps"]:
                    logger.error(f"Étape {phase}.{step} non trouvée")
                    return False
                target = self.data["phases"][phase]["steps"][step]
            else:
                # Mise à jour d'une phase
                target = self.data["phases"][phase]
            
            # Appliquer les mises à jour
            if status:
                target["status"] = status.value if isinstance(status, TaskStatus) else status
            
            if progress is not None:
                target["progress"] = max(0.0, min(1.0, progress))
            
            if actual_hours is not None:
                target["actual_hours"] = max(0.0, actual_hours)
            
            # Mettre à jour la timestamp
            self.data["project_info"]["last_updated"] = datetime.now().isoformat()
            
            # Recalculer les progressions si nécessaire
            if subtask and step:
                self._recalculate_step_progress(phase, step)
                self._recalculate_phase_progress(phase)
            elif step:
                self._recalculate_phase_progress(phase)
                
            self._recalculate_overall_progress()
            
            # Sauvegarder
            self._save_progress()
            
            logger.info(f"Tâche {phase}.{step or ''}.{subtask or ''} mise à jour: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la tâche: {e}")
            return False
    
    def _recalculate_step_progress(self, phase: str, step: str):
        """Recalcule la progression d'une étape basée sur ses sous-tâches"""
        step_data = self.data["phases"][phase]["steps"][step]
        
        if "subtasks" in step_data:
            subtasks = step_data["subtasks"]
            total_subtasks = len(subtasks)
            completed_subtasks = sum(1 for st in subtasks.values() 
                                   if st.get("status") == TaskStatus.COMPLETED.value)
            
            step_data["progress"] = completed_subtasks / total_subtasks if total_subtasks > 0 else 0.0
            
            # Mettre à jour le statut de l'étape
            if completed_subtasks == 0:
                step_data["status"] = TaskStatus.NOT_STARTED.value
            elif completed_subtasks == total_subtasks:
                step_data["status"] = TaskStatus.COMPLETED.value
            else:
                step_data["status"] = TaskStatus.IN_PROGRESS.value
    
    def _recalculate_phase_progress(self, phase: str):
        """Recalcule la progression d'une phase basée sur ses étapes"""
        phase_data = self.data["phases"][phase]
        
        if "steps" in phase_data:
            steps = phase_data["steps"]
            total_progress = sum(step.get("progress", 0.0) for step in steps.values())
            phase_data["progress"] = total_progress / len(steps) if steps else 0.0
            
            # Mettre à jour le statut de la phase
            completed_steps = sum(1 for step in steps.values() 
                                if step.get("status") == TaskStatus.COMPLETED.value)
            
            if completed_steps == 0:
                phase_data["status"] = TaskStatus.NOT_STARTED.value
            elif completed_steps == len(steps):
                phase_data["status"] = TaskStatus.COMPLETED.value
            else:
                phase_data["status"] = TaskStatus.IN_PROGRESS.value
    
    def _recalculate_overall_progress(self):
        """Recalcule la progression globale du projet"""
        phases = self.data["phases"]
        total_progress = sum(phase.get("progress", 0.0) for phase in phases.values())
        self.data["metrics"]["overall_progress"] = total_progress / len(phases) if phases else 0.0
        
        # Calculer le ratio d'efficacité
        total_estimated = sum(phase.get("estimated_hours", 0) for phase in phases.values())
        total_actual = sum(phase.get("actual_hours", 0) for phase in phases.values())
        
        if total_actual > 0:
            self.data["metrics"]["efficiency_ratio"] = total_estimated / total_actual
    
    def add_blocker(self, description: str, priority: Priority, phase: str = None, 
                   step: str = None) -> str:
        """
        Ajoute un nouveau bloqueur
        
        Args:
            description: Description du bloqueur
            priority: Priorité du bloqueur
            phase: Phase concernée (optionnel)
            step: Étape concernée (optionnel)
            
        Returns:
            ID du bloqueur créé
        """
        blocker_id = f"blocker_{len(self.data['current_blockers']) + 1:03d}"
        
        blocker = {
            "id": blocker_id,
            "description": description,
            "status": "open",
            "priority": priority.value if isinstance(priority, Priority) else priority,
            "created_date": datetime.now().isoformat(),
            "phase": phase,
            "step": step
        }
        
        self.data["current_blockers"].append(blocker)
        self._save_progress()
        
        logger.info(f"Nouveau bloqueur ajouté: {blocker_id}")
        return blocker_id
    
    def resolve_blocker(self, blocker_id: str) -> bool:
        """
        Résout un bloqueur
        
        Args:
            blocker_id: ID du bloqueur à résoudre
            
        Returns:
            True si le bloqueur a été résolu
        """
        for blocker in self.data["current_blockers"]:
            if blocker["id"] == blocker_id:
                blocker["status"] = "resolved"
                blocker["resolved_date"] = datetime.now().isoformat()
                self._save_progress()
                logger.info(f"Bloqueur {blocker_id} résolu")
                return True
        
        logger.warning(f"Bloqueur {blocker_id} non trouvé")
        return False
    
    def get_next_actions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Récupère les prochaines actions recommandées
        
        Args:
            limit: Nombre maximum d'actions à retourner
            
        Returns:
            Liste des prochaines actions triées par priorité
        """
        # Trier par priorité et retourner les premières
        actions = sorted(self.data["next_actions"], 
                        key=lambda x: ["critical", "high", "medium", "low"].index(x.get("priority", "low")))
        return actions[:limit]
    
    def get_status_summary(self) -> Dict[str, Any]:
        """
        Génère un résumé du statut actuel
        
        Returns:
            Dictionnaire avec le résumé du statut
        """
        return {
            "overall_progress": self.data["metrics"]["overall_progress"],
            "current_phase": self._get_current_phase(),
            "next_action": self.get_next_actions(1)[0] if self.data["next_actions"] else None,
            "open_blockers": [b for b in self.data["current_blockers"] if b["status"] == "open"],
            "total_estimated_hours": self.data["metrics"]["total_estimated_hours"],
            "total_actual_hours": self.data["metrics"]["total_actual_hours"],
            "efficiency_ratio": self.data["metrics"]["efficiency_ratio"]
        }
    
    def _get_current_phase(self) -> str:
        """Détermine la phase actuelle du projet"""
        for phase_id, phase_data in self.data["phases"].items():
            if phase_data["status"] in [TaskStatus.NOT_STARTED.value, TaskStatus.IN_PROGRESS.value]:
                return phase_id
        return list(self.data["phases"].keys())[-1]  # Dernière phase si tout est terminé
    
    def _save_progress(self):
        """Sauvegarde le fichier de progression"""
        try:
            with open(self.json_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error(f"Erreur lors de la sauvegarde de {self.json_file_path}: {e}")
    
    def export_progress_report(self, output_file: str = None) -> str:
        """
        Génère un rapport de progression au format Markdown
        
        Args:
            output_file: Fichier de sortie (optionnel)
            
        Returns:
            Contenu du rapport
        """
        status = self.get_status_summary()
        report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# Rapport de Progression WikiTranslateAI

**Date**: {report_date}
**Progression globale**: {status['overall_progress']:.1%}

## Statut Actuel

- **Phase courante**: {status['current_phase']}
- **Heures estimées**: {status['total_estimated_hours']}h
- **Heures réelles**: {status['total_actual_hours']}h
- **Ratio d'efficacité**: {status['efficiency_ratio']:.2f}

## Prochaine Action Recommandée

"""
        
        if status['next_action']:
            action = status['next_action']
            report += f"**{action['action']}**\n"
            report += f"- Priorité: {action['priority']}\n"
            report += f"- Temps estimé: {action['estimated_time']}\n"
            report += f"- Phase: {action['phase']}\n\n"
        else:
            report += "Aucune action définie.\n\n"
        
        # Bloqueurs ouverts
        if status['open_blockers']:
            report += "## Bloqueurs Actifs\n\n"
            for blocker in status['open_blockers']:
                report += f"- **{blocker['id']}**: {blocker['description']} (Priorité: {blocker['priority']})\n"
            report += "\n"
        
        # Détails par phase
        report += "## Détails par Phase\n\n"
        for phase_id, phase_data in self.data["phases"].items():
            report += f"### {phase_data['name']}\n"
            report += f"- Statut: {phase_data['status']}\n"
            report += f"- Progression: {phase_data['progress']:.1%}\n"
            report += f"- Description: {phase_data['description']}\n\n"
        
        # Sauvegarder si un fichier est spécifié
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Rapport sauvegardé dans {output_file}")
        
        return report


# Fonctions utilitaires pour CLI

def show_status():
    """Affiche le statut actuel du projet"""
    tracker = ProgressTracker()
    status = tracker.get_status_summary()
    
    print(f"\n=Ê STATUT WIKITRANSLATEAI")
    print(f"=È Progression globale: {status['overall_progress']:.1%}")
    print(f"<¯ Phase courante: {status['current_phase']}")
    
    if status['next_action']:
        print(f"\n<¯ PROCHAINE ACTION:")
        print(f"   {status['next_action']['action']}")
        print(f"   Priorité: {status['next_action']['priority'].upper()}")
        print(f"   Temps estimé: {status['next_action']['estimated_time']}")
    
    if status['open_blockers']:
        print(f"\n=« BLOQUEURS ACTIFS ({len(status['open_blockers'])}):")
        for blocker in status['open_blockers']:
            print(f"   - {blocker['description']}")
    
    print(f"\nñ  TEMPS:")
    print(f"   Estimé: {status['total_estimated_hours']}h")
    print(f"   Réel: {status['total_actual_hours']}h")
    
    if status['efficiency_ratio'] > 0:
        print(f"   Efficacité: {status['efficiency_ratio']:.2f}")


def update_task(phase: str, step: str = None, subtask: str = None, 
               status: str = None, progress: float = None):
    """Fonction CLI pour mettre à jour une tâche"""
    tracker = ProgressTracker()
    
    status_enum = None
    if status:
        try:
            status_enum = TaskStatus(status)
        except ValueError:
            print(f"Statut invalide: {status}")
            return False
    
    return tracker.update_task_status(phase, step, subtask, status_enum, progress)