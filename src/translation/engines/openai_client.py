# -*- coding: utf-8 -*-
# src/translation/engines/openai_client.py

import os
import time
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not available")

from src.utils.error_handler import handle_error, create_translation_error

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Types de modeles OpenAI supportes"""
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4 = "gpt-4"
    GPT_3_5_TURBO = "gpt-3.5-turbo"

@dataclass
class TranslationConfig:
    """Configuration pour une traduction"""
    model: ModelType = ModelType.GPT_4O_MINI
    temperature: float = 0.3
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    use_system_prompt: bool = True
    context_window: int = 4000

class EnhancedOpenAIClient:
    """Client OpenAI ameliore pour WikiTranslateAI"""
    
    def __init__(self, api_key: str = None, organization: str = None):
        """
        Initialise le client OpenAI ameliore
        
        Args:
            api_key: Cle API OpenAI
            organization: Organisation OpenAI (optionnel)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library is required but not installed")
        
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(
            api_key=self.api_key,
            organization=organization
        )
        
        # Configuration par defaut
        self.default_config = TranslationConfig()
        
        # Prompts systeme specialises
        self.system_prompts = {
            'general': """You are an expert translator specializing in African languages, particularly Fon, Yoruba, Ewe, and Dindi. 
Your translations are culturally sensitive and preserve the original meaning while adapting to the target culture.""",
            
            'cultural': """You are a cultural translator expert in West African languages and traditions. 
Preserve cultural concepts, religious terms, and traditional expressions. 
When translating cultural terms, maintain their original form and provide context when necessary.""",
            
            'technical': """You are a technical translator with expertise in African languages. 
Preserve technical terms, proper nouns, and specialized vocabulary. 
Maintain precision and clarity in technical contexts.""",
            
            'academic': """You are an academic translator specializing in African linguistics and anthropology. 
Your translations are scholarly, precise, and respect the academic conventions of both source and target languages."""
        }
        
        # Statistiques
        self.stats = {
            'total_requests': 0,
            'successful_translations': 0,
            'failed_translations': 0,
            'total_tokens_used': 0,
            'average_response_time': 0.0
        }
        
        logger.info("Client OpenAI ameliore initialise")
    
    def translate_text(self, 
                      text: str, 
                      source_language: str, 
                      target_language: str,
                      domain: str = 'general',
                      config: TranslationConfig = None) -> str:
        """
        Traduit un texte avec le modele OpenAI
        
        Args:
            text: Texte a traduire
            source_language: Langue source
            target_language: Langue cible
            domain: Domaine de traduction
            config: Configuration personnalisee
        
        Returns:
            Texte traduit
        """
        if not text or not text.strip():
            return ""
        
        config = config or self.default_config
        start_time = time.time()
        
        try:
            # Construire le prompt optimise
            messages = self._build_translation_messages(
                text, source_language, target_language, domain, config
            )
            
            # Appel API
            response = self.client.chat.completions.create(
                model=config.model.value,
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
                frequency_penalty=config.frequency_penalty,
                presence_penalty=config.presence_penalty
            )
            
            # Extraire la traduction
            translation = response.choices[0].message.content.strip()
            
            # Mettre a jour les statistiques
            response_time = time.time() - start_time
            self._update_stats(response, response_time, success=True)
            
            logger.info(f"Traduction reussie: {len(text)} -> {len(translation)} chars en {response_time:.2f}s")
            
            return translation
            
        except Exception as e:
            response_time = time.time() - start_time
            self._update_stats(None, response_time, success=False)
            
            error_id = handle_error(
                create_translation_error(
                    f"Erreur traduction OpenAI: {str(e)}",
                    source_text=text[:100],
                    target_language=target_language
                ),
                context={
                    'model': config.model.value,
                    'source_language': source_language,
                    'target_language': target_language,
                    'domain': domain
                }
            )
            
            return f"ERREUR_OPENAI_ENHANCED_{error_id[:8]}"
    
    def translate_batch(self, 
                       texts: List[str], 
                       source_language: str, 
                       target_language: str,
                       domain: str = 'general',
                       config: TranslationConfig = None,
                       batch_size: int = 5) -> List[str]:
        """
        Traduit plusieurs textes en lot
        
        Args:
            texts: Liste des textes a traduire
            source_language: Langue source
            target_language: Langue cible
            domain: Domaine de traduction
            config: Configuration personnalisee
            batch_size: Taille des lots
        
        Returns:
            Liste des traductions
        """
        if not texts:
            return []
        
        translations = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Traduire le lot comme un seul texte structure
            batch_text = self._format_batch_text(batch)
            
            try:
                batch_translation = self.translate_text(
                    batch_text, source_language, target_language, domain, config
                )
                
                # Extraire les traductions individuelles
                individual_translations = self._parse_batch_translation(
                    batch_translation, len(batch)
                )
                
                translations.extend(individual_translations)
                
            except Exception as e:
                logger.error(f"Erreur traduction lot {i//batch_size + 1}: {e}")
                # Fallback: traduire individuellement
                for text in batch:
                    try:
                        translation = self.translate_text(
                            text, source_language, target_language, domain, config
                        )
                        translations.append(translation)
                    except:
                        translations.append(f"ERREUR_LOT_{i}")
        
        logger.info(f"Traduction en lot completee: {len(texts)} textes traites")
        return translations
    
    def get_optimal_config(self, 
                          text_length: int, 
                          domain: str = 'general',
                          quality_priority: bool = True) -> TranslationConfig:
        """
        Determine la configuration optimale selon le contexte
        
        Args:
            text_length: Longueur du texte
            domain: Domaine de traduction
            quality_priority: Privilegier la qualite vs vitesse
        
        Returns:
            Configuration optimisee
        """
        config = TranslationConfig()
        
        # Choix du modele selon la longueur et qualite souhaitee
        if quality_priority:
            if text_length > 2000:
                config.model = ModelType.GPT_4O  # Meilleur pour longs textes
            else:
                config.model = ModelType.GPT_4O_MINI  # Bon rapport qualite/prix
        else:
            config.model = ModelType.GPT_3_5_TURBO  # Plus rapide
        
        # Temperature selon le domaine
        if domain == 'technical':
            config.temperature = 0.1  # Plus deterministe
        elif domain == 'cultural':
            config.temperature = 0.4  # Plus de creativite
        else:
            config.temperature = 0.3  # Equilibre
        
        # Tokens max selon la longueur
        if text_length > 1000:
            config.max_tokens = min(2000, text_length * 2)
        else:
            config.max_tokens = 1000
        
        return config
    
    def _build_translation_messages(self, 
                                   text: str, 
                                   source_lang: str, 
                                   target_lang: str, 
                                   domain: str,
                                   config: TranslationConfig) -> List[Dict[str, str]]:
        """
        Construit les messages optimises pour l'API
        
        Args:
            text: Texte a traduire
            source_lang: Langue source
            target_lang: Langue cible
            domain: Domaine
            config: Configuration
        
        Returns:
            Liste des messages pour l'API
        """
        messages = []
        
        # Message systeme
        if config.use_system_prompt:
            system_prompt = self.system_prompts.get(domain, self.system_prompts['general'])
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Instructions specifiques pour langues africaines
        african_instructions = ""
        if target_lang in ['fon', 'yor', 'yoruba', 'ewe', 'dindi']:
            african_instructions = f"""
            
IMPORTANT INSTRUCTIONS FOR {target_lang.upper()} TRANSLATION:
- Preserve cultural and religious terms in their original form
- Maintain proper names and place names
- Use appropriate honorifics and cultural expressions
- If uncertain about cultural terms, keep them in the source language
- Ensure the translation respects {target_lang} cultural context
"""
        
        # Message utilisateur avec instructions detaillees
        user_prompt = f"""Translate the following text from {source_lang} to {target_lang}.

{african_instructions}

Text to translate:
{text}

Translation:"""
        
        messages.append({
            "role": "user", 
            "content": user_prompt
        })
        
        return messages
    
    def _format_batch_text(self, texts: List[str]) -> str:
        """
        Formate plusieurs textes pour traduction en lot
        
        Args:
            texts: Liste des textes
        
        Returns:
            Texte formate pour le lot
        """
        formatted_texts = []
        for i, text in enumerate(texts, 1):
            formatted_texts.append(f"[TEXT {i}]\n{text}\n[END TEXT {i}]")
        
        return "\n\n".join(formatted_texts)
    
    def _parse_batch_translation(self, batch_translation: str, expected_count: int) -> List[str]:
        """
        Parse la traduction en lot pour extraire les traductions individuelles
        
        Args:
            batch_translation: Traduction du lot
            expected_count: Nombre de traductions attendues
        
        Returns:
            Liste des traductions individuelles
        """
        import re
        
        # Chercher les patterns de separation
        patterns = [
            r'\[TEXT \d+\](.*?)\[END TEXT \d+\]',
            r'\d+\.\s*(.*?)(?=\d+\.|$)',
            r'(?:^|\n)([^\\n]+)(?=\n|$)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, batch_translation, re.DOTALL | re.MULTILINE)
            if len(matches) == expected_count:
                return [match.strip() for match in matches]
        
        # Fallback: diviser par lignes vides
        parts = batch_translation.split('\n\n')
        if len(parts) >= expected_count:
            return parts[:expected_count]
        
        # Fallback final: retourner le texte complet pour chaque element
        logger.warning(f"Impossible de parser le lot, retour du texte complet")
        return [batch_translation] * expected_count
    
    def _update_stats(self, response, response_time: float, success: bool):
        """Met a jour les statistiques"""
        self.stats['total_requests'] += 1
        
        if success:
            self.stats['successful_translations'] += 1
            if response and hasattr(response, 'usage'):
                self.stats['total_tokens_used'] += response.usage.total_tokens
        else:
            self.stats['failed_translations'] += 1
        
        # Mettre a jour le temps de reponse moyen
        total_time = self.stats['average_response_time'] * (self.stats['total_requests'] - 1)
        self.stats['average_response_time'] = (total_time + response_time) / self.stats['total_requests']
    
    def get_model_info(self, model: ModelType) -> Dict[str, Any]:
        """
        Retourne les informations sur un modele
        
        Args:
            model: Type de modele
        
        Returns:
            Informations sur le modele
        """
        model_info = {
            ModelType.GPT_4O: {
                'name': 'GPT-4O',
                'context_window': 128000,
                'best_for': ['long_texts', 'complex_reasoning', 'high_quality'],
                'cost_per_1k_tokens': {'input': 0.005, 'output': 0.015}
            },
            ModelType.GPT_4O_MINI: {
                'name': 'GPT-4O Mini',
                'context_window': 128000,
                'best_for': ['general_translation', 'cost_effective', 'fast'],
                'cost_per_1k_tokens': {'input': 0.00015, 'output': 0.0006}
            },
            ModelType.GPT_4_TURBO: {
                'name': 'GPT-4 Turbo',
                'context_window': 128000,
                'best_for': ['complex_tasks', 'reasoning', 'analysis'],
                'cost_per_1k_tokens': {'input': 0.01, 'output': 0.03}
            },
            ModelType.GPT_4: {
                'name': 'GPT-4',
                'context_window': 8192,
                'best_for': ['high_quality', 'creative_tasks'],
                'cost_per_1k_tokens': {'input': 0.03, 'output': 0.06}
            },
            ModelType.GPT_3_5_TURBO: {
                'name': 'GPT-3.5 Turbo',
                'context_window': 16385,
                'best_for': ['speed', 'cost_effective', 'simple_tasks'],
                'cost_per_1k_tokens': {'input': 0.0015, 'output': 0.002}
            }
        }
        
        return model_info.get(model, {})
    
    def estimate_cost(self, text: str, model: ModelType = None) -> Dict[str, float]:
        """
        Estime le cout d'une traduction
        
        Args:
            text: Texte a traduire
            model: Modele a utiliser
        
        Returns:
            Estimation des couts
        """
        model = model or self.default_config.model
        model_info = self.get_model_info(model)
        
        # Estimation grossiere des tokens (1 token H 4 caracteres)
        input_tokens = len(text) // 4
        estimated_output_tokens = input_tokens * 1.2  # Estimation
        
        input_cost = (input_tokens / 1000) * model_info.get('cost_per_1k_tokens', {}).get('input', 0)
        output_cost = (estimated_output_tokens / 1000) * model_info.get('cost_per_1k_tokens', {}).get('output', 0)
        
        return {
            'input_tokens': input_tokens,
            'estimated_output_tokens': estimated_output_tokens,
            'input_cost_usd': round(input_cost, 6),
            'output_cost_usd': round(output_cost, 6),
            'total_cost_usd': round(input_cost + output_cost, 6)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques d'utilisation"""
        return {
            **self.stats,
            'success_rate': (self.stats['successful_translations'] / max(1, self.stats['total_requests'])) * 100,
            'average_tokens_per_request': self.stats['total_tokens_used'] / max(1, self.stats['successful_translations'])
        }


# Fonction utilitaire pour creation rapide
def create_openai_translator(api_key: str = None, model: str = "gpt-4o-mini") -> EnhancedOpenAIClient:
    """
    Cree un traducteur OpenAI avec configuration par defaut
    
    Args:
        api_key: Cle API (optionnel si dans env)
        model: Modele a utiliser
    
    Returns:
        Instance du traducteur
    """
    client = EnhancedOpenAIClient(api_key=api_key)
    
    # Configurer le modele par defaut
    try:
        client.default_config.model = ModelType(model)
    except ValueError:
        logger.warning(f"Modele {model} non reconnu, utilisation de gpt-4o-mini")
        client.default_config.model = ModelType.GPT_4O_MINI
    
    return client


if __name__ == "__main__":
    # Test du client OpenAI ameliore
    if OPENAI_AVAILABLE and os.environ.get('OPENAI_API_KEY'):
        client = create_openai_translator()
        
        test_text = "L'histoire du royaume du Dahomey est fascinante."
        
        # Test traduction simple
        translation = client.translate_text(test_text, 'fr', 'fon', 'cultural')
        print(f"Traduction: {translation}")
        
        # Test estimation de cout
        cost = client.estimate_cost(test_text)
        print(f"Cout estime: ${cost['total_cost_usd']:.6f}")
        
        # Statistiques
        stats = client.get_statistics()
        print(f"Statistiques: {stats}")
        
    else:
        print("OpenAI non disponible ou cle API manquante")