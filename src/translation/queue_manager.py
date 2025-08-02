# -*- coding: utf-8 -*-
# src/translation/queue_manager.py

import json
import time
import threading
import logging
from queue import Queue, PriorityQueue, Empty
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """Statuts possibles pour une tache de traduction"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """Niveaux de priorite pour les taches"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    URGENT = 0

@dataclass
class TranslationTask:
    """Representation d'une tache de traduction"""
    task_id: str
    source_language: str
    target_language: str
    content: str
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    attempts: int = 0
    max_attempts: int = 3
    result: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}
    
    def __lt__(self, other):
        # Pour PriorityQueue: priorite plus haute = valeur plus petite
        return self.priority.value < other.priority.value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit la tache en dictionnaire pour serialisation"""
        data = asdict(self)
        # Convertir les enums et datetime en strings
        data['priority'] = self.priority.name
        data['status'] = self.status.name
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TranslationTask':
        """Cree une tache depuis un dictionnaire"""
        # Convertir les strings en enums et datetime
        if isinstance(data['priority'], str):
            data['priority'] = TaskPriority[data['priority']]
        if isinstance(data['status'], str):
            data['status'] = TaskStatus[data['status']]
        
        for date_field in ['created_at', 'started_at', 'completed_at']:
            if data.get(date_field):
                data[date_field] = datetime.fromisoformat(data[date_field])
        
        return cls(**data)

class TranslationQueueManager:
    """Gestionnaire de files de traduction pour WikiTranslateAI"""
    
    def __init__(self, persistence_file: str = "data/translation_queue.json", max_workers: int = 3):
        """
        Initialise le gestionnaire de files
        
        Args:
            persistence_file: Fichier pour sauvegarder les taches
            max_workers: Nombre maximum de workers simultanes
        """
        self.persistence_file = Path(persistence_file)
        self.max_workers = max_workers
        
        # Files de taches
        self.pending_queue = PriorityQueue()
        self.active_tasks: Dict[str, TranslationTask] = {}
        self.completed_tasks: Dict[str, TranslationTask] = {}
        self.failed_tasks: Dict[str, TranslationTask] = {}
        
        # Gestion des workers
        self.workers: List[threading.Thread] = []
        self.worker_active = False
        self.task_handlers: Dict[str, Callable] = {}
        
        # Statistiques
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'processing_time_total': 0.0,
            'average_processing_time': 0.0
        }
        
        # Thread-safety
        self.lock = threading.RLock()
        self.shutdown_event = threading.Event()
        
        # Creer le repertoire de persistence
        self.persistence_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Charger les taches existantes
        self._load_tasks()
        
        logger.info(f"Gestionnaire de files initialise: {max_workers} workers, "
                   f"persistance: {persistence_file}")
    
    def add_task(self, 
                 content: str,
                 source_language: str, 
                 target_language: str,
                 priority: TaskPriority = TaskPriority.NORMAL,
                 metadata: Dict[str, Any] = None) -> str:
        """
        Ajoute une tache de traduction a la file
        
        Args:
            content: Contenu a traduire
            source_language: Langue source
            target_language: Langue cible
            priority: Priorite de la tache
            metadata: Metadonnees additionnelles
        
        Returns:
            ID de la tache
        """
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(content)}"
        
        task = TranslationTask(
            task_id=task_id,
            source_language=source_language,
            target_language=target_language,
            content=content,
            priority=priority,
            metadata=metadata or {}
        )
        
        with self.lock:
            self.pending_queue.put(task)
            self.stats['total_tasks'] += 1
            
        self._save_tasks()
        
        logger.info(f"Tache ajoutee: {task_id} ({source_language}->{target_language}, "
                   f"priorite: {priority.name})")
        
        return task_id
    
    def add_batch_tasks(self, 
                       tasks_data: List[Dict[str, Any]]) -> List[str]:
        """
        Ajoute plusieurs taches en lot
        
        Args:
            tasks_data: Liste des donnees de taches
        
        Returns:
            Liste des IDs des taches creees
        """
        task_ids = []
        
        with self.lock:
            for task_data in tasks_data:
                task_id = self.add_task(**task_data)
                task_ids.append(task_id)
        
        logger.info(f"Lot de taches ajoute: {len(task_ids)} taches")
        return task_ids
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupere le statut d'une tache
        
        Args:
            task_id: ID de la tache
        
        Returns:
            Informations sur la tache ou None
        """
        with self.lock:
            # Chercher dans les taches actives
            if task_id in self.active_tasks:
                return self.active_tasks[task_id].to_dict()
            
            # Chercher dans les taches completees
            if task_id in self.completed_tasks:
                return self.completed_tasks[task_id].to_dict()
            
            # Chercher dans les taches echouees
            if task_id in self.failed_tasks:
                return self.failed_tasks[task_id].to_dict()
            
            # Chercher dans la file d'attente (plus couteux)
            temp_tasks = []
            while not self.pending_queue.empty():
                try:
                    task = self.pending_queue.get_nowait()
                    temp_tasks.append(task)
                    if task.task_id == task_id:
                        # Remettre toutes les taches dans la file
                        for t in temp_tasks:
                            self.pending_queue.put(t)
                        return task.to_dict()
                except Empty:
                    break
            
            # Remettre les taches dans la file
            for task in temp_tasks:
                self.pending_queue.put(task)
        
        return None
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Annule une tache
        
        Args:
            task_id: ID de la tache a annuler
        
        Returns:
            True si annulee avec succes
        """
        with self.lock:
            # Chercher dans les taches actives
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.status = TaskStatus.CANCELLED
                del self.active_tasks[task_id]
                logger.info(f"Tache annulee: {task_id}")
                return True
            
            # Chercher dans la file d'attente
            temp_tasks = []
            found = False
            
            while not self.pending_queue.empty():
                try:
                    task = self.pending_queue.get_nowait()
                    if task.task_id == task_id:
                        task.status = TaskStatus.CANCELLED
                        found = True
                        logger.info(f"Tache annulee: {task_id}")
                    else:
                        temp_tasks.append(task)
                except Empty:
                    break
            
            # Remettre les taches non annulees
            for task in temp_tasks:
                self.pending_queue.put(task)
            
            return found
    
    def register_task_handler(self, task_type: str, handler: Callable):
        """
        Enregistre un gestionnaire pour un type de tache
        
        Args:
            task_type: Type de tache (ex: 'article', 'segment')
            handler: Fonction qui traite la tache
        """
        self.task_handlers[task_type] = handler
        logger.info(f"Gestionnaire enregistre pour type: {task_type}")
    
    def start_workers(self):
        """Demarre les workers de traitement"""
        if self.worker_active:
            logger.warning("Workers deja actifs")
            return
        
        self.worker_active = True
        self.shutdown_event.clear()
        
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop, args=(i,))
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"Workers demarres: {self.max_workers} threads actifs")
    
    def stop_workers(self, timeout: int = 30):
        """
        Arrete les workers
        
        Args:
            timeout: Timeout en secondes pour l'arret
        """
        if not self.worker_active:
            return
        
        logger.info("Arret des workers en cours...")
        
        self.shutdown_event.set()
        
        # Attendre l'arret des workers
        for worker in self.workers:
            worker.join(timeout=timeout)
        
        self.worker_active = False
        self.workers.clear()
        
        logger.info("Workers arretes")
    
    def _worker_loop(self, worker_id: int):
        """
        Boucle principale d'un worker
        
        Args:
            worker_id: ID du worker
        """
        logger.info(f"Worker {worker_id} demarre")
        
        while not self.shutdown_event.is_set():
            try:
                # Recuperer une tache (timeout de 1 seconde)
                task = self.pending_queue.get(timeout=1.0)
                
                if task.status == TaskStatus.CANCELLED:
                    continue
                
                # Traiter la tache
                self._process_task(task, worker_id)
                
            except Empty:
                # Pas de tache disponible, continuer
                continue
            except Exception as e:
                logger.error(f"Erreur dans worker {worker_id}: {e}")
        
        logger.info(f"Worker {worker_id} arrete")
    
    def _process_task(self, task: TranslationTask, worker_id: int):
        """
        Traite une tache de traduction
        
        Args:
            task: Tache a traiter
            worker_id: ID du worker
        """
        start_time = time.time()
        
        with self.lock:
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            task.attempts += 1
            self.active_tasks[task.task_id] = task
        
        logger.info(f"Worker {worker_id} traite tache {task.task_id} "
                   f"(tentative {task.attempts}/{task.max_attempts})")
        
        try:
            # Determiner le type de tache
            task_type = task.metadata.get('type', 'default')
            
            # Utiliser le gestionnaire approprie
            if task_type in self.task_handlers:
                result = self.task_handlers[task_type](task)
            else:
                # Gestionnaire par defaut (simulation)
                time.sleep(0.5)  # Simuler le temps de traitement
                result = f"[TRADUCTION SIMULEE] {task.content}"
            
            # Marquer comme completee
            with self.lock:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.result = result
                
                del self.active_tasks[task.task_id]
                self.completed_tasks[task.task_id] = task
                
                # Mettre a jour les statistiques
                processing_time = time.time() - start_time
                self.stats['completed_tasks'] += 1
                self.stats['processing_time_total'] += processing_time
                self.stats['average_processing_time'] = \
                    self.stats['processing_time_total'] / self.stats['completed_tasks']
            
            logger.info(f"Tache completee: {task.task_id} en {processing_time:.2f}s")
            
        except Exception as e:
            # Marquer comme echouee
            with self.lock:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                
                del self.active_tasks[task.task_id]
                
                # Remettre en file si pas trop de tentatives
                if task.attempts < task.max_attempts:
                    task.status = TaskStatus.PENDING
                    self.pending_queue.put(task)
                    logger.warning(f"Tache {task.task_id} remise en file "
                                 f"(tentative {task.attempts}/{task.max_attempts})")
                else:
                    self.failed_tasks[task.task_id] = task
                    self.stats['failed_tasks'] += 1
                    logger.error(f"Tache echouee definitivement: {task.task_id} - {e}")
        
        finally:
            self._save_tasks()
    
    def get_queue_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques de la file"""
        with self.lock:
            return {
                'pending_tasks': self.pending_queue.qsize(),
                'active_tasks': len(self.active_tasks),
                'completed_tasks': len(self.completed_tasks),
                'failed_tasks': len(self.failed_tasks),
                'total_tasks': self.stats['total_tasks'],
                'success_rate': (self.stats['completed_tasks'] / max(1, self.stats['total_tasks'])) * 100,
                'average_processing_time': self.stats['average_processing_time'],
                'workers_active': len(self.workers)
            }
    
    def _save_tasks(self):
        """Sauvegarde les taches sur disque"""
        try:
            # Sauvegarder seulement les taches importantes
            save_data = {
                'completed_tasks': [task.to_dict() for task in self.completed_tasks.values()],
                'failed_tasks': [task.to_dict() for task in self.failed_tasks.values()],
                'stats': self.stats,
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.persistence_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Erreur sauvegarde taches: {e}")
    
    def _load_tasks(self):
        """Charge les taches depuis le disque"""
        if not self.persistence_file.exists():
            return
        
        try:
            with open(self.persistence_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Charger les taches completees
            for task_data in data.get('completed_tasks', []):
                task = TranslationTask.from_dict(task_data)
                self.completed_tasks[task.task_id] = task
            
            # Charger les taches echouees
            for task_data in data.get('failed_tasks', []):
                task = TranslationTask.from_dict(task_data)
                self.failed_tasks[task.task_id] = task
            
            # Charger les statistiques
            if 'stats' in data:
                self.stats.update(data['stats'])
            
            logger.info(f"Taches chargees: {len(self.completed_tasks)} completees, "
                       f"{len(self.failed_tasks)} echouees")
            
        except Exception as e:
            logger.error(f"Erreur chargement taches: {e}")


if __name__ == "__main__":
    # Test du gestionnaire de files
    queue_manager = TranslationQueueManager()
    
    # Enregistrer un gestionnaire de test
    def test_handler(task: TranslationTask) -> str:
        time.sleep(0.1)  # Simuler traitement
        return f"Traduit: {task.content}"
    
    queue_manager.register_task_handler('test', test_handler)
    
    # Ajouter des taches de test
    task_ids = []
    for i in range(5):
        task_id = queue_manager.add_task(
            content=f"Texte de test {i}",
            source_language="fr",
            target_language="fon",
            priority=TaskPriority.NORMAL,
            metadata={'type': 'test'}
        )
        task_ids.append(task_id)
    
    # Demarrer les workers
    queue_manager.start_workers()
    
    # Attendre un peu
    time.sleep(2)
    
    # Afficher les statistiques
    stats = queue_manager.get_queue_statistics()
    print(f"Statistiques: {stats}")
    
    # Arreter les workers
    queue_manager.stop_workers()