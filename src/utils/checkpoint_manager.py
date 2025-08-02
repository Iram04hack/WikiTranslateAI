# -*- coding: utf-8 -*-
# src/utils/checkpoint_manager.py

import json
import time
import hashlib
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class CheckpointType(Enum):
    """Types de points de sauvegarde"""
    ARTICLE_EXTRACTION = "article_extraction"
    ARTICLE_CLEANING = "article_cleaning"
    ARTICLE_SEGMENTATION = "article_segmentation"
    TRANSLATION_START = "translation_start"
    TRANSLATION_PROGRESS = "translation_progress"
    TRANSLATION_COMPLETE = "translation_complete"
    BATCH_PROCESSING = "batch_processing"
    ERROR_RECOVERY = "error_recovery"

class CheckpointStatus(Enum):
    """Statuts des checkpoints"""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERED = "recovered"

@dataclass
class Checkpoint:
    """Representation d'un point de sauvegarde"""
    checkpoint_id: str
    checkpoint_type: CheckpointType
    status: CheckpointStatus
    created_at: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any] = None
    progress_percentage: float = 0.0
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le checkpoint en dictionnaire"""
        data = asdict(self)
        data['checkpoint_type'] = self.checkpoint_type.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        if self.estimated_completion:
            data['estimated_completion'] = self.estimated_completion.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Checkpoint':
        """Cree un checkpoint depuis un dictionnaire"""
        data['checkpoint_type'] = CheckpointType(data['checkpoint_type'])
        data['status'] = CheckpointStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('estimated_completion'):
            data['estimated_completion'] = datetime.fromisoformat(data['estimated_completion'])
        return cls(**data)

class CheckpointManager:
    """Gestionnaire de points de sauvegarde pour WikiTranslateAI"""
    
    def __init__(self, checkpoint_dir: str = "data/checkpoints", max_checkpoints: int = 100):
        """
        Initialise le gestionnaire de checkpoints
        
        Args:
            checkpoint_dir: Repertoire de sauvegarde
            max_checkpoints: Nombre maximum de checkpoints a conserver
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.max_checkpoints = max_checkpoints
        self.checkpoints: Dict[str, Checkpoint] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Statistiques
        self.stats = {
            'total_checkpoints': 0,
            'successful_recoveries': 0,
            'failed_recoveries': 0,
            'storage_size_mb': 0.0
        }
        
        # Creer le repertoire
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Charger les checkpoints existants
        self._load_existing_checkpoints()
        
        logger.info(f"Gestionnaire de checkpoints initialise: {checkpoint_dir}, "
                   f"max: {max_checkpoints}")
    
    def create_checkpoint(self, 
                         checkpoint_type: CheckpointType,
                         data: Dict[str, Any],
                         session_id: str = None,
                         metadata: Dict[str, Any] = None,
                         progress_percentage: float = 0.0) -> str:
        """
        Cree un nouveau checkpoint
        
        Args:
            checkpoint_type: Type de checkpoint
            data: Donnees a sauvegarder
            session_id: ID de session (optionnel)
            metadata: Metadonnees additionnelles
            progress_percentage: Pourcentage de progression
        
        Returns:
            ID du checkpoint cree
        """
        # Generer un ID unique
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()[:8]
        checkpoint_id = f"{checkpoint_type.value}_{timestamp}_{data_hash}"
        
        # Estimer le temps de completion si en cours
        estimated_completion = None
        if checkpoint_type in [CheckpointType.TRANSLATION_PROGRESS, CheckpointType.BATCH_PROCESSING]:
            if progress_percentage > 0:
                estimated_completion = self._estimate_completion_time(progress_percentage)
        
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            checkpoint_type=checkpoint_type,
            status=CheckpointStatus.IN_PROGRESS,
            created_at=datetime.now(),
            data=data,
            metadata=metadata or {},
            progress_percentage=progress_percentage,
            estimated_completion=estimated_completion
        )
        
        # Ajouter des metadonnees automatiques
        checkpoint.metadata.update({
            'session_id': session_id,
            'data_size': len(json.dumps(data)),
            'python_pid': os.getpid() if 'os' in globals() else None
        })
        
        with self.lock:
            self.checkpoints[checkpoint_id] = checkpoint
            self.stats['total_checkpoints'] += 1
            
            # Associer a une session si specifie
            if session_id:
                if session_id not in self.active_sessions:
                    self.active_sessions[session_id] = {
                        'created_at': datetime.now(),
                        'checkpoints': [],
                        'current_checkpoint': None
                    }
                self.active_sessions[session_id]['checkpoints'].append(checkpoint_id)
                self.active_sessions[session_id]['current_checkpoint'] = checkpoint_id
        
        # Sauvegarder sur disque
        self._save_checkpoint(checkpoint)
        
        # Nettoyer les anciens checkpoints si necessaire
        self._cleanup_old_checkpoints()
        
        logger.info(f"Checkpoint cree: {checkpoint_id} ({checkpoint_type.value}, "
                   f"session: {session_id})")
        
        return checkpoint_id
    
    def update_checkpoint(self, 
                         checkpoint_id: str, 
                         status: CheckpointStatus = None,
                         data: Dict[str, Any] = None,
                         progress_percentage: float = None,
                         error_message: str = None) -> bool:
        """
        Met a jour un checkpoint existant
        
        Args:
            checkpoint_id: ID du checkpoint
            status: Nouveau statut
            data: Nouvelles donnees
            progress_percentage: Nouveau pourcentage
            error_message: Message d'erreur
        
        Returns:
            True si mise a jour reussie
        """
        with self.lock:
            if checkpoint_id not in self.checkpoints:
                logger.warning(f"Checkpoint introuvable: {checkpoint_id}")
                return False
            
            checkpoint = self.checkpoints[checkpoint_id]
            
            # Mettre a jour les champs
            if status is not None:
                checkpoint.status = status
            if data is not None:
                checkpoint.data.update(data)
            if progress_percentage is not None:
                checkpoint.progress_percentage = progress_percentage
                # Recalculer l'estimation
                if progress_percentage > 0 and checkpoint.status == CheckpointStatus.IN_PROGRESS:
                    checkpoint.estimated_completion = self._estimate_completion_time(progress_percentage)
            if error_message is not None:
                checkpoint.error_message = error_message
        
        # Sauvegarder les modifications
        self._save_checkpoint(checkpoint)
        
        logger.debug(f"Checkpoint mis a jour: {checkpoint_id}")
        return True
    
    def complete_checkpoint(self, checkpoint_id: str, final_data: Dict[str, Any] = None) -> bool:
        """
        Marque un checkpoint comme complete
        
        Args:
            checkpoint_id: ID du checkpoint
            final_data: Donnees finales (optionnel)
        
        Returns:
            True si reussi
        """
        return self.update_checkpoint(
            checkpoint_id, 
            status=CheckpointStatus.COMPLETED,
            data=final_data,
            progress_percentage=100.0
        )
    
    def fail_checkpoint(self, checkpoint_id: str, error_message: str) -> bool:
        """
        Marque un checkpoint comme echoue
        
        Args:
            checkpoint_id: ID du checkpoint
            error_message: Message d'erreur
        
        Returns:
            True si reussi
        """
        return self.update_checkpoint(
            checkpoint_id,
            status=CheckpointStatus.FAILED,
            error_message=error_message
        )
    
    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """
        Recupere un checkpoint par son ID
        
        Args:
            checkpoint_id: ID du checkpoint
        
        Returns:
            Checkpoint ou None
        """
        with self.lock:
            return self.checkpoints.get(checkpoint_id)
    
    def get_latest_checkpoint(self, checkpoint_type: CheckpointType = None, session_id: str = None) -> Optional[Checkpoint]:
        """
        Recupere le checkpoint le plus recent
        
        Args:
            checkpoint_type: Type de checkpoint (optionnel)
            session_id: ID de session (optionnel)
        
        Returns:
            Checkpoint le plus recent ou None
        """
        with self.lock:
            candidates = []
            
            for checkpoint in self.checkpoints.values():
                # Filtrer par type si specifie
                if checkpoint_type and checkpoint.checkpoint_type != checkpoint_type:
                    continue
                
                # Filtrer par session si specifie
                if session_id and checkpoint.metadata.get('session_id') != session_id:
                    continue
                
                candidates.append(checkpoint)
            
            if not candidates:
                return None
            
            # Trier par date de creation (plus recent en premier)
            candidates.sort(key=lambda c: c.created_at, reverse=True)
            return candidates[0]
    
    def recover_from_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupere les donnees d'un checkpoint pour reprendre le traitement
        
        Args:
            checkpoint_id: ID du checkpoint
        
        Returns:
            Donnees du checkpoint ou None
        """
        checkpoint = self.get_checkpoint(checkpoint_id)
        if not checkpoint:
            logger.error(f"Impossible de recuperer le checkpoint: {checkpoint_id}")
            self.stats['failed_recoveries'] += 1
            return None
        
        try:
            # Marquer comme recupere
            self.update_checkpoint(checkpoint_id, status=CheckpointStatus.RECOVERED)
            
            recovery_data = {
                'checkpoint_id': checkpoint_id,
                'checkpoint_type': checkpoint.checkpoint_type.value,
                'original_data': checkpoint.data.copy(),
                'progress_percentage': checkpoint.progress_percentage,
                'metadata': checkpoint.metadata.copy(),
                'recovery_timestamp': datetime.now().isoformat()
            }
            
            self.stats['successful_recoveries'] += 1
            logger.info(f"Recuperation reussie du checkpoint: {checkpoint_id}")
            
            return recovery_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la recuperation du checkpoint {checkpoint_id}: {e}")
            self.stats['failed_recoveries'] += 1
            return None
    
    def list_checkpoints(self, 
                        checkpoint_type: CheckpointType = None,
                        status: CheckpointStatus = None,
                        session_id: str = None,
                        limit: int = 50) -> List[Dict[str, Any]]:
        """
        Liste les checkpoints selon des criteres
        
        Args:
            checkpoint_type: Filtrer par type
            status: Filtrer par statut
            session_id: Filtrer par session
            limit: Nombre maximum de resultats
        
        Returns:
            Liste des checkpoints
        """
        with self.lock:
            results = []
            
            for checkpoint in self.checkpoints.values():
                # Appliquer les filtres
                if checkpoint_type and checkpoint.checkpoint_type != checkpoint_type:
                    continue
                if status and checkpoint.status != status:
                    continue
                if session_id and checkpoint.metadata.get('session_id') != session_id:
                    continue
                
                results.append(checkpoint.to_dict())
            
            # Trier par date (plus recent en premier)
            results.sort(key=lambda c: c['created_at'], reverse=True)
            
            return results[:limit]
    
    def cleanup_session(self, session_id: str) -> int:
        """
        Nettoie tous les checkpoints d'une session
        
        Args:
            session_id: ID de la session
        
        Returns:
            Nombre de checkpoints nettoyes
        """
        with self.lock:
            checkpoints_to_remove = []
            
            for checkpoint_id, checkpoint in self.checkpoints.items():
                if checkpoint.metadata.get('session_id') == session_id:
                    checkpoints_to_remove.append(checkpoint_id)
            
            # Supprimer les checkpoints
            for checkpoint_id in checkpoints_to_remove:
                self._delete_checkpoint(checkpoint_id)
            
            # Nettoyer la session active
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            logger.info(f"Session nettoyee: {session_id}, {len(checkpoints_to_remove)} checkpoints supprimes")
            return len(checkpoints_to_remove)
    
    def get_checkpoint_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques des checkpoints"""
        with self.lock:
            # Calculer la taille de stockage
            total_size = 0
            for checkpoint_file in self.checkpoint_dir.glob("*.json"):
                total_size += checkpoint_file.stat().st_size
            
            self.stats['storage_size_mb'] = round(total_size / (1024 * 1024), 2)
            
            # Statistiques par type
            type_counts = {}
            status_counts = {}
            
            for checkpoint in self.checkpoints.values():
                ptype = checkpoint.checkpoint_type.value
                status = checkpoint.status.value
                
                type_counts[ptype] = type_counts.get(ptype, 0) + 1
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                **self.stats,
                'current_checkpoints': len(self.checkpoints),
                'active_sessions': len(self.active_sessions),
                'checkpoints_by_type': type_counts,
                'checkpoints_by_status': status_counts
            }
    
    def _estimate_completion_time(self, progress_percentage: float) -> datetime:
        """
        Estime le temps de completion base sur le progres
        
        Args:
            progress_percentage: Pourcentage de progression
        
        Returns:
            Temps estime de completion
        """
        if progress_percentage <= 0:
            return None
        
        # Estimation simple basee sur le temps ecoule
        now = datetime.now()
        # Estimer qu'il reste (100 - progress) / progress du temps deja ecoule
        remaining_ratio = (100 - progress_percentage) / progress_percentage
        # Estimer 1 heure par defaut si pas d'info
        estimated_remaining = timedelta(hours=remaining_ratio)
        
        return now + estimated_remaining
    
    def _save_checkpoint(self, checkpoint: Checkpoint):
        """Sauvegarde un checkpoint sur disque"""
        try:
            checkpoint_file = self.checkpoint_dir / f"{checkpoint.checkpoint_id}.json"
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erreur sauvegarde checkpoint {checkpoint.checkpoint_id}: {e}")
    
    def _load_existing_checkpoints(self):
        """Charge les checkpoints existants depuis le disque"""
        try:
            checkpoint_files = list(self.checkpoint_dir.glob("*.json"))
            loaded_count = 0
            
            for checkpoint_file in checkpoint_files:
                try:
                    with open(checkpoint_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    checkpoint = Checkpoint.from_dict(data)
                    self.checkpoints[checkpoint.checkpoint_id] = checkpoint
                    loaded_count += 1
                    
                except Exception as e:
                    logger.warning(f"Impossible de charger {checkpoint_file}: {e}")
            
            logger.info(f"Checkpoints charges: {loaded_count}")
            
        except Exception as e:
            logger.error(f"Erreur chargement checkpoints: {e}")
    
    def _cleanup_old_checkpoints(self):
        """Nettoie les anciens checkpoints si limite depassee"""
        with self.lock:
            if len(self.checkpoints) <= self.max_checkpoints:
                return
            
            # Trier par date (plus anciens en premier)
            sorted_checkpoints = sorted(
                self.checkpoints.items(),
                key=lambda item: item[1].created_at
            )
            
            # Supprimer les plus anciens
            to_remove = len(sorted_checkpoints) - self.max_checkpoints
            for i in range(to_remove):
                checkpoint_id = sorted_checkpoints[i][0]
                self._delete_checkpoint(checkpoint_id)
            
            logger.info(f"Nettoyage: {to_remove} anciens checkpoints supprimes")
    
    def _delete_checkpoint(self, checkpoint_id: str):
        """Supprime un checkpoint"""
        try:
            # Supprimer du dictionnaire
            if checkpoint_id in self.checkpoints:
                del self.checkpoints[checkpoint_id]
            
            # Supprimer le fichier
            checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
            if checkpoint_file.exists():
                checkpoint_file.unlink()
                
        except Exception as e:
            logger.error(f"Erreur suppression checkpoint {checkpoint_id}: {e}")


# Fonctions utilitaires pour utilisation simple
def create_translation_checkpoint(article_title: str, source_lang: str, target_lang: str, 
                                segments_data: List[Dict], progress: float = 0.0) -> str:
    """
    Cree un checkpoint pour une traduction d'article
    
    Args:
        article_title: Titre de l'article
        source_lang: Langue source
        target_lang: Langue cible
        segments_data: Donnees des segments
        progress: Progression en pourcentage
    
    Returns:
        ID du checkpoint
    """
    checkpoint_manager = CheckpointManager()
    
    data = {
        'article_title': article_title,
        'source_language': source_lang,
        'target_language': target_lang,
        'segments': segments_data,
        'total_segments': len(segments_data)
    }
    
    return checkpoint_manager.create_checkpoint(
        CheckpointType.TRANSLATION_PROGRESS,
        data,
        progress_percentage=progress,
        metadata={'article_title': article_title}
    )


import os  # Import necessaire pour os.getpid()

if __name__ == "__main__":
    # Test du gestionnaire de checkpoints
    checkpoint_manager = CheckpointManager()
    
    # Creer un checkpoint de test
    test_data = {
        'article_title': 'Histoire du Benin',
        'segments_completed': 5,
        'segments_total': 20,
        'current_segment': 'Le royaume du Dahomey...'
    }
    
    checkpoint_id = checkpoint_manager.create_checkpoint(
        CheckpointType.TRANSLATION_PROGRESS,
        test_data,
        session_id="test_session",
        progress_percentage=25.0
    )
    
    print(f"Checkpoint cree: {checkpoint_id}")
    
    # Mettre a jour le progres
    checkpoint_manager.update_checkpoint(
        checkpoint_id,
        progress_percentage=50.0,
        data={'segments_completed': 10}
    )
    
    # Completer le checkpoint
    checkpoint_manager.complete_checkpoint(
        checkpoint_id,
        {'final_result': 'Translation completed successfully'}
    )
    
    # Afficher les statistiques
    stats = checkpoint_manager.get_checkpoint_statistics()
    print(f"Statistiques: {stats}")
    
    # Lister les checkpoints
    checkpoints = checkpoint_manager.list_checkpoints(limit=5)
    print(f"Checkpoints recents: {len(checkpoints)}")