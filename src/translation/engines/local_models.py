# -*- coding: utf-8 -*-
# src/translation/engines/local_models.py

import os
import json
import logging
import threading
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

try:
    from transformers import MarianMTModel, MarianTokenizer, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from src.utils.error_handler import handle_error, create_translation_error

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Types de modeles locaux supportes"""
    MARIAN_MT = "marian_mt"           # Modeles MarianMT d'Hugging Face
    OPUS_MT = "opus_mt"               # Modeles OPUS-MT
    M2M100 = "m2m100"                # Meta M2M-100 multilingual
    NLLB = "nllb"                    # Meta No Language Left Behind
    CUSTOM = "custom"                # Modeles personnalises

@dataclass
class ModelConfig:
    """Configuration d'un modele local"""
    model_name: str
    model_type: ModelType
    source_languages: List[str]
    target_languages: List[str]
    model_path: Optional[str] = None
    tokenizer_path: Optional[str] = None
    device: str = "cpu"              # "cpu", "cuda", "auto"
    max_length: int = 512
    batch_size: int = 8
    use_cache: bool = True
    precision: str = "float32"       # "float32", "float16", "int8"

class LocalModelManager:
    """Gestionnaire de modeles de traduction locaux"""
    
    def __init__(self, models_dir: str = "data/models", cache_dir: str = "data/cache"):
        """
        Initialise le gestionnaire de modeles locaux
        
        Args:
            models_dir: Repertoire de stockage des modeles
            cache_dir: Repertoire de cache
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers library is required but not installed")
        
        self.models_dir = Path(models_dir)
        self.cache_dir = Path(cache_dir)
        
        # Creer les repertoires
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Modeles charges en memoire
        self.loaded_models: Dict[str, Dict[str, Any]] = {}
        self.model_configs: Dict[str, ModelConfig] = {}
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Detection automatique du device
        self.default_device = self._detect_optimal_device()
        
        # Modeles preconfigures pour les langues africaines
        self.predefined_models = {
            # Francais vers langues africaines
            "fr-multi-africa": ModelConfig(
                model_name="Helsinki-NLP/opus-mt-fr-mul",
                model_type=ModelType.OPUS_MT,
                source_languages=["fr"],
                target_languages=["yor", "ewe", "swa", "lin", "lug"],
                device=self.default_device
            ),
            
            # Anglais vers langues africaines
            "en-multi-africa": ModelConfig(
                model_name="Helsinki-NLP/opus-mt-en-mul",
                model_type=ModelType.OPUS_MT,
                source_languages=["en"],
                target_languages=["yor", "ewe", "swa", "lin", "lug"],
                device=self.default_device
            ),
            
            # Modele multilingual M2M100
            "m2m100-418M": ModelConfig(
                model_name="facebook/m2m100_418M",
                model_type=ModelType.M2M100,
                source_languages=["en", "fr"],
                target_languages=["yor", "swa", "lin"],
                device=self.default_device,
                max_length=1024
            ),
            
            # NLLB pour langues peu dotees
            "nllb-200-600M": ModelConfig(
                model_name="facebook/nllb-200-600M",
                model_type=ModelType.NLLB,
                source_languages=["eng_Latn", "fra_Latn"],
                target_languages=["yor_Latn", "ewe_Latn", "fon_Latn"],
                device=self.default_device,
                max_length=1024
            )
        }
        
        # Statistiques
        self.stats = {
            'models_loaded': 0,
            'total_translations': 0,
            'successful_translations': 0,
            'failed_translations': 0,
            'average_translation_time': 0.0,
            'memory_usage_mb': 0.0
        }
        
        logger.info(f"Gestionnaire de modeles locaux initialise (device: {self.default_device})")
    
    def load_model(self, model_key: str, config: ModelConfig = None) -> bool:
        """
        Charge un modele en memoire
        
        Args:
            model_key: Cle identificatrice du modele
            config: Configuration du modele (optionnel si predefini)
        
        Returns:
            True si chargement reussi
        """
        with self.lock:
            if model_key in self.loaded_models:
                logger.info(f"Modele deja charge: {model_key}")
                return True
            
            # Utiliser config predefini si non fourni
            if config is None:
                config = self.predefined_models.get(model_key)
                if config is None:
                    logger.error(f"Configuration manquante pour modele: {model_key}")
                    return False
            
            try:
                logger.info(f"Chargement du modele: {model_key} ({config.model_name})")
                
                model_data = self._load_model_by_type(config)
                
                self.loaded_models[model_key] = {
                    'config': config,
                    'model': model_data['model'],
                    'tokenizer': model_data['tokenizer'],
                    'pipeline': model_data.get('pipeline'),
                    'load_time': model_data['load_time']
                }
                
                self.model_configs[model_key] = config
                self.stats['models_loaded'] += 1
                
                logger.info(f"Modele charge avec succes: {model_key} "
                           f"(temps: {model_data['load_time']:.2f}s)")
                return True
                
            except Exception as e:
                error_id = handle_error(
                    create_translation_error(
                        f"Erreur chargement modele {model_key}: {str(e)}",
                        context="model_loading"
                    ),
                    context={'model_key': model_key, 'config': config.__dict__}
                )
                logger.error(f"Echec chargement modele {model_key}: {e}")
                return False
    
    def translate_text(self, 
                      text: str, 
                      source_language: str, 
                      target_language: str,
                      model_key: str = None) -> str:
        """
        Traduit un texte avec un modele local
        
        Args:
            text: Texte a traduire
            source_language: Langue source
            target_language: Langue cible
            model_key: Cle du modele a utiliser (auto-detection si None)
        
        Returns:
            Texte traduit
        """
        if not text or not text.strip():
            return ""
        
        # Auto-selection du modele si non specifie
        if model_key is None:
            model_key = self._select_optimal_model(source_language, target_language)
            if model_key is None:
                return f"ERREUR_AUCUN_MODELE_DISPONIBLE_{source_language}_{target_language}"
        
        # Charger le modele si necessaire
        if model_key not in self.loaded_models:
            if not self.load_model(model_key):
                return f"ERREUR_CHARGEMENT_MODELE_{model_key}"
        
        start_time = time.time()
        
        try:
            model_data = self.loaded_models[model_key]
            config = model_data['config']
            
            # Adapter les codes de langue selon le type de modele
            src_lang = self._adapt_language_code(source_language, config.model_type, 'source')
            tgt_lang = self._adapt_language_code(target_language, config.model_type, 'target')
            
            # Traduire selon le type de modele
            if config.model_type in [ModelType.MARIAN_MT, ModelType.OPUS_MT]:
                translation = self._translate_with_marian(text, model_data, src_lang, tgt_lang)
            elif config.model_type == ModelType.M2M100:
                translation = self._translate_with_m2m100(text, model_data, src_lang, tgt_lang)
            elif config.model_type == ModelType.NLLB:
                translation = self._translate_with_nllb(text, model_data, src_lang, tgt_lang)
            else:
                translation = self._translate_with_pipeline(text, model_data, src_lang, tgt_lang)
            
            # Mettre a jour les statistiques
            translation_time = time.time() - start_time
            self._update_stats(translation_time, success=True)
            
            logger.debug(f"Traduction reussie avec {model_key}: {len(text)} -> {len(translation)} chars "
                        f"en {translation_time:.2f}s")
            
            return translation
            
        except Exception as e:
            translation_time = time.time() - start_time
            self._update_stats(translation_time, success=False)
            
            error_id = handle_error(
                create_translation_error(
                    f"Erreur traduction locale: {str(e)}",
                    source_text=text[:100],
                    target_language=target_language
                ),
                context={
                    'model_key': model_key,
                    'source_language': source_language,
                    'target_language': target_language
                }
            )
            
            return f"ERREUR_TRADUCTION_LOCALE_{error_id[:8]}"
    
    def translate_batch(self, 
                       texts: List[str], 
                       source_language: str, 
                       target_language: str,
                       model_key: str = None,
                       batch_size: int = None) -> List[str]:
        """
        Traduit plusieurs textes en lot
        
        Args:
            texts: Liste des textes a traduire
            source_language: Langue source
            target_language: Langue cible
            model_key: Cle du modele a utiliser
            batch_size: Taille des lots (utilise config du modele si None)
        
        Returns:
            Liste des traductions
        """
        if not texts:
            return []
        
        # Auto-selection du modele
        if model_key is None:
            model_key = self._select_optimal_model(source_language, target_language)
            if model_key is None:
                return [f"ERREUR_AUCUN_MODELE_{i}" for i in range(len(texts))]
        
        # Charger le modele
        if model_key not in self.loaded_models:
            if not self.load_model(model_key):
                return [f"ERREUR_CHARGEMENT_{i}" for i in range(len(texts))]
        
        config = self.loaded_models[model_key]['config']
        effective_batch_size = batch_size or config.batch_size
        
        translations = []
        
        for i in range(0, len(texts), effective_batch_size):
            batch = texts[i:i + effective_batch_size]
            
            try:
                batch_translations = []
                for text in batch:
                    translation = self.translate_text(text, source_language, target_language, model_key)
                    batch_translations.append(translation)
                
                translations.extend(batch_translations)
                
            except Exception as e:
                logger.error(f"Erreur traduction lot {i//effective_batch_size + 1}: {e}")
                # Fallback: traduction individuelle
                for text in batch:
                    try:
                        translation = self.translate_text(text, source_language, target_language, model_key)
                        translations.append(translation)
                    except:
                        translations.append(f"ERREUR_LOT_{i}")
        
        logger.info(f"Traduction en lot completee: {len(texts)} textes avec {model_key}")
        return translations
    
    def _detect_optimal_device(self) -> str:
        """Detecte le device optimal (CPU/GPU)"""
        if not TORCH_AVAILABLE:
            return "cpu"
        
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
            
            if gpu_memory >= 4:  # Au moins 4GB de VRAM
                logger.info(f"GPU detecte: {gpu_count} device(s), {gpu_memory:.1f}GB VRAM")
                return "cuda"
        
        logger.info("GPU non disponible ou insuffisant, utilisation CPU")
        return "cpu"
    
    def _load_model_by_type(self, config: ModelConfig) -> Dict[str, Any]:
        """Charge un modele selon son type"""
        import time
        start_time = time.time()
        
        if config.model_type in [ModelType.MARIAN_MT, ModelType.OPUS_MT]:
            return self._load_marian_model(config, start_time)
        elif config.model_type == ModelType.M2M100:
            return self._load_m2m100_model(config, start_time)
        elif config.model_type == ModelType.NLLB:
            return self._load_nllb_model(config, start_time)
        else:
            raise ValueError(f"Type de modele non supporte: {config.model_type}")
    
    def _load_marian_model(self, config: ModelConfig, start_time: float) -> Dict[str, Any]:
        """Charge un modele MarianMT"""
        model = MarianMTModel.from_pretrained(config.model_name)
        tokenizer = MarianTokenizer.from_pretrained(config.model_name)
        
        if config.device != "cpu" and TORCH_AVAILABLE:
            model = model.to(config.device)
        
        return {
            'model': model,
            'tokenizer': tokenizer,
            'load_time': time.time() - start_time
        }
    
    def _load_m2m100_model(self, config: ModelConfig, start_time: float) -> Dict[str, Any]:
        """Charge un modele M2M100"""
        translation_pipeline = pipeline(
            "translation",
            model=config.model_name,
            device=0 if config.device == "cuda" else -1
        )
        
        return {
            'model': None,
            'tokenizer': None,
            'pipeline': translation_pipeline,
            'load_time': time.time() - start_time
        }
    
    def _load_nllb_model(self, config: ModelConfig, start_time: float) -> Dict[str, Any]:
        """Charge un modele NLLB"""
        translation_pipeline = pipeline(
            "translation",
            model=config.model_name,
            device=0 if config.device == "cuda" else -1
        )
        
        return {
            'model': None,
            'tokenizer': None,
            'pipeline': translation_pipeline,
            'load_time': time.time() - start_time
        }
    
    def _translate_with_marian(self, text: str, model_data: Dict, src_lang: str, tgt_lang: str) -> str:
        """Traduction avec modele MarianMT"""
        model = model_data['model']
        tokenizer = model_data['tokenizer']
        
        # Encoder le texte
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        
        if model_data['config'].device != "cpu" and TORCH_AVAILABLE:
            inputs = {k: v.to(model_data['config'].device) for k, v in inputs.items()}
        
        # Generer la traduction
        with torch.no_grad():
            outputs = model.generate(**inputs, max_length=model_data['config'].max_length)
        
        # Decoder le resultat
        translation = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return translation.strip()
    
    def _translate_with_m2m100(self, text: str, model_data: Dict, src_lang: str, tgt_lang: str) -> str:
        """Traduction avec modele M2M100"""
        pipeline_obj = model_data['pipeline']
        
        result = pipeline_obj(text, src_lang=src_lang, tgt_lang=tgt_lang)
        return result[0]['translation_text'].strip()
    
    def _translate_with_nllb(self, text: str, model_data: Dict, src_lang: str, tgt_lang: str) -> str:
        """Traduction avec modele NLLB"""
        pipeline_obj = model_data['pipeline']
        
        result = pipeline_obj(text, src_lang=src_lang, tgt_lang=tgt_lang)
        return result[0]['translation_text'].strip()
    
    def _translate_with_pipeline(self, text: str, model_data: Dict, src_lang: str, tgt_lang: str) -> str:
        """Traduction avec pipeline generique"""
        if 'pipeline' in model_data and model_data['pipeline']:
            result = model_data['pipeline'](text)
            return result[0]['translation_text'].strip()
        else:
            raise ValueError("Pipeline de traduction non disponible")
    
    def _select_optimal_model(self, source_lang: str, target_lang: str) -> Optional[str]:
        """Selectionne le modele optimal pour une paire de langues"""
        best_model = None
        best_score = 0
        
        for model_key, config in self.predefined_models.items():
            score = 0
            
            # Verifier compatibilite langue source
            if source_lang in config.source_languages:
                score += 10
            elif any(source_lang.startswith(lang) for lang in config.source_languages):
                score += 5
            
            # Verifier compatibilite langue cible
            if target_lang in config.target_languages:
                score += 10
            elif any(target_lang.startswith(lang) for lang in config.target_languages):
                score += 5
            
            # Bonus pour modeles multilingues
            if config.model_type in [ModelType.M2M100, ModelType.NLLB]:
                score += 2
            
            if score > best_score:
                best_score = score
                best_model = model_key
        
        logger.debug(f"Modele selectionne pour {source_lang}->{target_lang}: {best_model} (score: {best_score})")
        return best_model
    
    def _adapt_language_code(self, lang_code: str, model_type: ModelType, direction: str) -> str:
        """Adapte le code de langue selon le type de modele"""
        # Mapping pour NLLB (codes avec script)
        nllb_mapping = {
            'en': 'eng_Latn', 'fr': 'fra_Latn', 'es': 'spa_Latn',
            'fon': 'fon_Latn', 'yor': 'yor_Latn', 'yoruba': 'yor_Latn',
            'ewe': 'ewe_Latn', 'swa': 'swh_Latn', 'swahili': 'swh_Latn'
        }
        
        # Mapping pour M2M100
        m2m100_mapping = {
            'en': 'en', 'fr': 'fr', 'es': 'es',
            'yor': 'yo', 'yoruba': 'yo', 'swa': 'sw', 'swahili': 'sw'
        }
        
        if model_type == ModelType.NLLB:
            return nllb_mapping.get(lang_code, lang_code)
        elif model_type == ModelType.M2M100:
            return m2m100_mapping.get(lang_code, lang_code)
        else:
            # Pour MarianMT/OPUS-MT, garder codes originaux
            return lang_code
    
    def _update_stats(self, translation_time: float, success: bool):
        """Met a jour les statistiques"""
        self.stats['total_translations'] += 1
        
        if success:
            self.stats['successful_translations'] += 1
        else:
            self.stats['failed_translations'] += 1
        
        # Mettre a jour temps moyen
        total_time = self.stats['average_translation_time'] * (self.stats['total_translations'] - 1)
        self.stats['average_translation_time'] = (total_time + translation_time) / self.stats['total_translations']
    
    def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """Retourne la liste des modeles disponibles"""
        models_info = {}
        
        for model_key, config in self.predefined_models.items():
            models_info[model_key] = {
                'name': config.model_name,
                'type': config.model_type.value,
                'source_languages': config.source_languages,
                'target_languages': config.target_languages,
                'device': config.device,
                'loaded': model_key in self.loaded_models
            }
        
        return models_info
    
    def get_model_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques des modeles"""
        return {
            **self.stats,
            'loaded_models': list(self.loaded_models.keys()),
            'available_models': list(self.predefined_models.keys()),
            'device': self.default_device,
            'transformers_available': TRANSFORMERS_AVAILABLE,
            'torch_available': TORCH_AVAILABLE
        }
    
    def unload_model(self, model_key: str) -> bool:
        """Decharge un modele de la memoire"""
        with self.lock:
            if model_key not in self.loaded_models:
                return False
            
            try:
                del self.loaded_models[model_key]
                self.stats['models_loaded'] -= 1
                logger.info(f"Modele decharge: {model_key}")
                return True
            except Exception as e:
                logger.error(f"Erreur dechargement modele {model_key}: {e}")
                return False
    
    def clear_all_models(self):
        """Decharge tous les modeles de la memoire"""
        with self.lock:
            model_keys = list(self.loaded_models.keys())
            for model_key in model_keys:
                self.unload_model(model_key)
            logger.info("Tous les modeles ont ete decharges")


# Fonction utilitaire pour creation rapide
def create_local_translator(model_key: str = "m2m100-418M", 
                           auto_load: bool = True) -> LocalModelManager:
    """
    Cree un traducteur de modeles locaux
    
    Args:
        model_key: Cle du modele par defaut
        auto_load: Charger automatiquement le modele
    
    Returns:
        Instance du gestionnaire
    """
    manager = LocalModelManager()
    
    if auto_load:
        success = manager.load_model(model_key)
        if not success:
            logger.warning(f"Impossible de charger le modele par defaut: {model_key}")
    
    return manager


import time  # Import necessaire pour time.time()

if __name__ == "__main__":
    # Test du gestionnaire de modeles locaux
    if TRANSFORMERS_AVAILABLE:
        manager = LocalModelManager()
        
        # Afficher les modeles disponibles
        models = manager.get_available_models()
        print("Modeles disponibles:")
        for key, info in models.items():
            print(f"  {key}: {info['name']} ({info['type']})")
        
        # Test avec un modele leger si disponible
        test_model = "en-multi-africa"  # Modele OPUS-MT
        
        print(f"\nTest de chargement: {test_model}")
        if manager.load_model(test_model):
            print(" Modele charge avec succes")
            
            # Test de traduction
            test_text = "The history of Benin is fascinating."
            translation = manager.translate_text(test_text, "en", "yor", test_model)
            print(f"Traduction test: {test_text} -> {translation}")
            
            # Statistiques
            stats = manager.get_model_statistics()
            print(f"Statistiques: {stats}")
        else:
            print("L Echec du chargement")
    else:
        print("L Bibliotheque transformers non disponible")
        print("Installation requise: pip install transformers torch")