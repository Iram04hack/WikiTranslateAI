# src/utils/progress_tracker.py

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """Statuts possibles pour les t�ches"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"

class Priority(Enum):
    """Niveaux de priorit�"""
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
        """Charge ou cr�e le fichier de progression"""
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
        """Cr�e la structure par d�faut du fichier de progression"""
        return {
            "project_info": {
                "name": "WikiTranslateAI",
                "version": "1.0.0",
                "description": "Syst�me de traduction d'articles Wikipedia vers les langues africaines",
                "target_languages": ["fon", "yoruba", "ewe", "dindi"],
                "last_updated": datetime.now().isoformat()
            },
            "phases": {
                "phase_1": {
                    "name": "Corrections Critiques",
                    "description": "Fixer les bugs critiques emp�chant le fonctionnement",
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
                                "1_1_1": {"name": "Mettre � jour requirements.txt", "status": TaskStatus.NOT_STARTED.value, "hours": 0.5},
                                "1_1_2": {"name": "Refactoriser azure_client.py", "status": TaskStatus.NOT_STARTED.value, "hours": 4},
                                "1_1_3": {"name": "Modifier m�thode translate_text()", "status": TaskStatus.NOT_STARTED.value, "hours": 6},
                                "1_1_4": {"name": "Tester traduction simple", "status": TaskStatus.NOT_STARTED.value, "hours": 2},
                                "1_1_5": {"name": "Valider avec article complet", "status": TaskStatus.NOT_STARTED.value, "hours": 3.5}
                            }
                        },
                        "step_1_2": {
                            "name": "Fixer probl�mes d'imports",
                            "status": TaskStatus.NOT_STARTED.value,
                            "progress": 0.0,
                            "priority": Priority.HIGH.value,
                            "estimated_hours": 8
                        },
                        "step_1_3": {
                            "name": "R�soudre erreurs de configuration",
                            "status": TaskStatus.NOT_STARTED.value,
                            "progress": 0.0,
                            "priority": Priority.HIGH.value,
                            "estimated_hours": 6
                        },
                        "step_1_4": {
                            "name": "Tests de validation compl�te",
                            "status": TaskStatus.NOT_STARTED.value,
                            "progress": 0.0,
                            "priority": Priority.MEDIUM.value,
                            "estimated_hours": 6
                        }
                    }
                },
                "phase_2": {
                    "name": "Optimisations Performance",
                    "description": "Am�liorer les performances et l'efficacit�",
                    "status": TaskStatus.NOT_STARTED.value,
                    "progress": 0.0,
                    "estimated_hours": 48,
                    "actual_hours": 0
                },
                "phase_3": {
                    "name": "Nouvelles Fonctionnalit�s",
                    "description": "Ajouter des fonctionnalit�s avanc�es",
                    "status": TaskStatus.NOT_STARTED.value,
                    "progress": 0.0,
                    "estimated_hours": 72,
                    "actual_hours": 0
                }
            },
            "next_actions": [
                {
                    "action": "Fixer l'API OpenAI obsol�te (v0.x � v1.x)",
                    "priority": Priority.CRITICAL.value,
                    "estimated_time": "16h",
                    "phase": "phase_1",
                    "step": "step_1_1"
                }
            ],
            "current_blockers": [
                {
                    "id": "blocker_001",
                    "description": "API OpenAI obsol�te emp�che tout fonctionnement",
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
        Met � jour le statut d'une t�che
        
        Args:
            phase: ID de la phase (ex: "phase_1")
            step: ID de l'�tape (ex: "step_1_1", optionnel)
            subtask: ID de la sous-t�che (ex: "1_1_1", optionnel)
            status: Nouveau statut
            progress: Nouveau pourcentage de progression (0.0-1.0)
            actual_hours: Heures r�ellement pass�es
            
        Returns:
            True si la mise � jour a r�ussi
        """
        try:
            # Valider que la phase existe
            if phase not in self.data["phases"]:
                logger.error(f"Phase {phase} non trouv�e")
                return False
            
            # D�terminer la cible de la mise � jour
            if subtask and step:
                # Mise � jour d'une sous-t�che
                if (step not in self.data["phases"][phase]["steps"] or 
                    "subtasks" not in self.data["phases"][phase]["steps"][step] or
                    subtask not in self.data["phases"][phase]["steps"][step]["subtasks"]):
                    logger.error(f"Sous-t�che {phase}.{step}.{subtask} non trouv�e")
                    return False
                target = self.data["phases"][phase]["steps"][step]["subtasks"][subtask]
            elif step:
                # Mise � jour d'une �tape
                if step not in self.data["phases"][phase]["steps"]:
                    logger.error(f"�tape {phase}.{step} non trouv�e")
                    return False
                target = self.data["phases"][phase]["steps"][step]
            else:
                # Mise � jour d'une phase
                target = self.data["phases"][phase]
            
            # Appliquer les mises � jour
            if status:
                target["status"] = status.value if isinstance(status, TaskStatus) else status
            
            if progress is not None:
                target["progress"] = max(0.0, min(1.0, progress))
            
            if actual_hours is not None:
                target["actual_hours"] = max(0.0, actual_hours)
            
            # Mettre � jour la timestamp
            self.data["project_info"]["last_updated"] = datetime.now().isoformat()
            
            # Recalculer les progressions si n�cessaire
            if subtask and step:
                self._recalculate_step_progress(phase, step)
                self._recalculate_phase_progress(phase)
            elif step:
                self._recalculate_phase_progress(phase)
                
            self._recalculate_overall_progress()
            
            # Sauvegarder
            self._save_progress()
            
            logger.info(f"T�che {phase}.{step or ''}.{subtask or ''} mise � jour: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise � jour de la t�che: {e}")
            return False
    
    def _recalculate_step_progress(self, phase: str, step: str):
        """Recalcule la progression d'une �tape bas�e sur ses sous-t�ches"""
        step_data = self.data["phases"][phase]["steps"][step]
        
        if "subtasks" in step_data:
            subtasks = step_data["subtasks"]
            total_subtasks = len(subtasks)
            completed_subtasks = sum(1 for st in subtasks.values() 
                                   if st.get("status") == TaskStatus.COMPLETED.value)
            
            step_data["progress"] = completed_subtasks / total_subtasks if total_subtasks > 0 else 0.0
            
            # Mettre � jour le statut de l'�tape
            if completed_subtasks == 0:
                step_data["status"] = TaskStatus.NOT_STARTED.value
            elif completed_subtasks == total_subtasks:
                step_data["status"] = TaskStatus.COMPLETED.value
            else:
                step_data["status"] = TaskStatus.IN_PROGRESS.value
    
    def _recalculate_phase_progress(self, phase: str):
        """Recalcule la progression d'une phase bas�e sur ses �tapes"""
        phase_data = self.data["phases"][phase]
        
        if "steps" in phase_data:
            steps = phase_data["steps"]
            total_progress = sum(step.get("progress", 0.0) for step in steps.values())
            phase_data["progress"] = total_progress / len(steps) if steps else 0.0
            
            # Mettre � jour le statut de la phase
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
        
        # Calculer le ratio d'efficacit�
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
            priority: Priorit� du bloqueur
            phase: Phase concern�e (optionnel)
            step: �tape concern�e (optionnel)
            
        Returns:
            ID du bloqueur cr��
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
        
        logger.info(f"Nouveau bloqueur ajout�: {blocker_id}")
        return blocker_id
    
    def resolve_blocker(self, blocker_id: str) -> bool:
        """
        R�sout un bloqueur
        
        Args:
            blocker_id: ID du bloqueur � r�soudre
            
        Returns:
            True si le bloqueur a �t� r�solu
        """
        for blocker in self.data["current_blockers"]:
            if blocker["id"] == blocker_id:
                blocker["status"] = "resolved"
                blocker["resolved_date"] = datetime.now().isoformat()
                self._save_progress()
                logger.info(f"Bloqueur {blocker_id} r�solu")
                return True
        
        logger.warning(f"Bloqueur {blocker_id} non trouv�")
        return False
    
    def get_next_actions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        R�cup�re les prochaines actions recommand�es
        
        Args:
            limit: Nombre maximum d'actions � retourner
            
        Returns:
            Liste des prochaines actions tri�es par priorit�
        """
        # Trier par priorit� et retourner les premi�res
        actions = sorted(self.data["next_actions"], 
                        key=lambda x: ["critical", "high", "medium", "low"].index(x.get("priority", "low")))
        return actions[:limit]
    
    def get_status_summary(self) -> Dict[str, Any]:
        """
        G�n�re un r�sum� du statut actuel
        
        Returns:
            Dictionnaire avec le r�sum� du statut
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
        """D�termine la phase actuelle du projet"""
        for phase_id, phase_data in self.data["phases"].items():
            if phase_data["status"] in [TaskStatus.NOT_STARTED.value, TaskStatus.IN_PROGRESS.value]:
                return phase_id
        return list(self.data["phases"].keys())[-1]  # Derni�re phase si tout est termin�
    
    def _save_progress(self):
        """Sauvegarde le fichier de progression"""
        try:
            with open(self.json_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error(f"Erreur lors de la sauvegarde de {self.json_file_path}: {e}")
    
    def export_progress_report(self, output_file: str = None) -> str:
        """
        G�n�re un rapport de progression au format Markdown
        
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
- **Heures estim�es**: {status['total_estimated_hours']}h
- **Heures r�elles**: {status['total_actual_hours']}h
- **Ratio d'efficacit�**: {status['efficiency_ratio']:.2f}

## Prochaine Action Recommand�e

"""
        
        if status['next_action']:
            action = status['next_action']
            report += f"**{action['action']}**\n"
            report += f"- Priorit�: {action['priority']}\n"
            report += f"- Temps estim�: {action['estimated_time']}\n"
            report += f"- Phase: {action['phase']}\n\n"
        else:
            report += "Aucune action d�finie.\n\n"
        
        # Bloqueurs ouverts
        if status['open_blockers']:
            report += "## Bloqueurs Actifs\n\n"
            for blocker in status['open_blockers']:
                report += f"- **{blocker['id']}**: {blocker['description']} (Priorit�: {blocker['priority']})\n"
            report += "\n"
        
        # D�tails par phase
        report += "## D�tails par Phase\n\n"
        for phase_id, phase_data in self.data["phases"].items():
            report += f"### {phase_data['name']}\n"
            report += f"- Statut: {phase_data['status']}\n"
            report += f"- Progression: {phase_data['progress']:.1%}\n"
            report += f"- Description: {phase_data['description']}\n\n"
        
        # Sauvegarder si un fichier est sp�cifi�
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Rapport sauvegard� dans {output_file}")
        
        return report


# Fonctions utilitaires pour CLI

def show_status():
    """Affiche le statut actuel du projet"""
    tracker = ProgressTracker()
    status = tracker.get_status_summary()
    
    print(f"\n=� STATUT WIKITRANSLATEAI")
    print(f"=� Progression globale: {status['overall_progress']:.1%}")
    print(f"<� Phase courante: {status['current_phase']}")
    
    if status['next_action']:
        print(f"\n<� PROCHAINE ACTION:")
        print(f"   {status['next_action']['action']}")
        print(f"   Priorit�: {status['next_action']['priority'].upper()}")
        print(f"   Temps estim�: {status['next_action']['estimated_time']}")
    
    if status['open_blockers']:
        print(f"\n=� BLOQUEURS ACTIFS ({len(status['open_blockers'])}):")
        for blocker in status['open_blockers']:
            print(f"   - {blocker['description']}")
    
    print(f"\n�  TEMPS:")
    print(f"   Estim�: {status['total_estimated_hours']}h")
    print(f"   R�el: {status['total_actual_hours']}h")
    
    if status['efficiency_ratio'] > 0:
        print(f"   Efficacit�: {status['efficiency_ratio']:.2f}")


def update_task(phase: str, step: str = None, subtask: str = None, 
               status: str = None, progress: float = None):
    """Fonction CLI pour mettre � jour une t�che"""
    tracker = ProgressTracker()
    
    status_enum = None
    if status:
        try:
            status_enum = TaskStatus(status)
        except ValueError:
            print(f"Statut invalide: {status}")
            return False
    
    return tracker.update_task_status(phase, step, subtask, status_enum, progress)