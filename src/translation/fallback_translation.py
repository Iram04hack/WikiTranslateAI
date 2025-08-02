# src/translation/fallback_translator.py
import os
import logging
import json
import requests

# Import conditionnel pour permettre le fonctionnement sans transformers
try:
    from transformers import MarianMTModel, MarianTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)

class FallbackTranslator:
    """Traducteur de secours lorsque l'API OpenAI échoue"""
    
    def __init__(self, source_lang, target_lang):
        """Initialise le traducteur de secours pour la paire de langues"""
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.models = self._get_available_models()
    
    def _get_available_models(self):
        """Renvoie les modèles disponibles pour cette paire de langues"""
        models = []
        
        # Option 1: Google Translate API (priorité haute)
        google_api_key = os.environ.get('GOOGLE_TRANSLATE_API_KEY')
        if google_api_key:
            models.append({
                'name': 'GoogleTranslate',
                'type': 'api',
                'api_key': google_api_key,
                'priority': 1
            })
        
        # Option 2: LibreTranslate (si disponible)
        libre_translate_url = os.environ.get('LIBRE_TRANSLATE_URL')
        if libre_translate_url:
            models.append({
                'name': 'LibreTranslate',
                'type': 'api',
                'url': libre_translate_url,
                'api_key': os.environ.get('LIBRE_TRANSLATE_API_KEY', ''),
                'priority': 2
            })
        
        # Option 3: Modèles Marian locaux via Hugging Face (si disponible)
        if TRANSFORMERS_AVAILABLE:
            source_code = self._language_to_code(self.source_lang)
            target_code = self._language_to_code(self.target_lang)
            
            if source_code and target_code:
                model_name = f'Helsinki-NLP/opus-mt-{source_code}-{target_code}'
                try:
                    # Vérifier si le modèle est disponible sans le télécharger
                    from huggingface_hub import model_info
                    model_info(model_name)
                    models.append({
                        'name': 'MarianMT',
                        'type': 'local',
                        'model_name': model_name,
                        'priority': 3
                    })
                except:
                    # Essayer avec un modèle pivot
                    if source_code != 'en' and target_code != 'en':
                        models.append({
                            'name': 'MarianMT-Pivot',
                            'type': 'local',
                            'source_model': f'Helsinki-NLP/opus-mt-{source_code}-en',
                            'target_model': f'Helsinki-NLP/opus-mt-en-{target_code}',
                            'priority': 4
                        })
        
        # Trier par priorité
        models.sort(key=lambda x: x.get('priority', 999))
        return models
    
    def _language_to_code(self, language):
        """Convertit un nom de langue en code pour les modèles Marian"""
        mapping = {
            'fr': 'fr', 'en': 'en', 
            'fon': 'yor',  # Utiliser yoruba comme approximation pour fon
            'ewe': 'yor',  # Utiliser yoruba comme approximation pour ewe
            'dindi': 'yor',  # Utiliser yoruba comme approximation pour dindi
            'yor': 'yor', 'yoruba': 'yor'
        }
        return mapping.get(language.lower())
    
    def translate(self, text):
        """Traduit un texte en utilisant la meilleure méthode disponible"""
        if not text or not text.strip():
            return ""
        
        for model in self.models:
            try:
                if model['type'] == 'api' and model['name'] == 'GoogleTranslate':
                    translation = self._translate_with_google(text, model)
                    if translation:
                        logger.info(f"Traduction effectuée avec {model['name']}")
                        return f"[FALLBACK-GOOGLE] {translation}"
                
                elif model['type'] == 'api' and model['name'] == 'LibreTranslate':
                    translation = self._translate_with_libretranslate(text, model)
                    if translation:
                        logger.info(f"Traduction effectuée avec {model['name']}")
                        return f"[FALLBACK-LIBRE] {translation}"
                
                elif model['type'] == 'local' and model['name'] == 'MarianMT' and TRANSFORMERS_AVAILABLE:
                    translation = self._translate_with_marian(text, model['model_name'])
                    if translation:
                        logger.info(f"Traduction effectuée avec {model['name']}")
                        return f"[FALLBACK-MARIAN] {translation}"
                
                elif model['type'] == 'local' and model['name'] == 'MarianMT-Pivot' and TRANSFORMERS_AVAILABLE:
                    # Traduction en deux étapes
                    english = self._translate_with_marian(text, model['source_model'])
                    if english:
                        translation = self._translate_with_marian(english, model['target_model'])
                        if translation:
                            logger.info(f"Traduction effectuée avec {model['name']}")
                            return f"[FALLBACK-MARIAN-PIVOT] {translation}"
            
            except Exception as e:
                logger.warning(f"Erreur avec le modèle {model['name']}: {e}")
                continue
        
        # Si aucune traduction n'a fonctionné
        logger.error(f"Échec de traduction avec tous les modèles de fallback pour: {text[:50]}...")
        # Retourner une chaîne sécurisée pour noms de fichiers (sans caractères spéciaux)
        return "TRADUCTION_IMPOSSIBLE_MODELES_FALLBACK_INDISPONIBLES"
    
    def _translate_with_google(self, text, model_config):
        """Traduit avec l'API Google Translate"""
        try:
            # Mapper les langues pour Google Translate
            source_lang = self._language_to_google_code(self.source_lang)
            target_lang = self._language_to_google_code(self.target_lang)
            
            if not source_lang or not target_lang:
                logger.warning(f"Langues non supportées par Google Translate: {self.source_lang} -> {self.target_lang}")
                return None
            
            api_key = model_config.get('api_key')
            if not api_key:
                logger.warning("Clé API Google Translate manquante")
                return None
            
            # URL de l'API Google Translate
            url = "https://translation.googleapis.com/language/translate/v2"
            
            payload = {
                'q': text,
                'source': source_lang,
                'target': target_lang,
                'key': api_key,
                'format': 'text'
            }
            
            response = requests.post(url, data=payload)
            
            if response.status_code == 200:
                result = response.json()
                if 'data' in result and 'translations' in result['data']:
                    translations = result['data']['translations']
                    if translations and len(translations) > 0:
                        return translations[0].get('translatedText', '')
            else:
                logger.warning(f"Erreur Google Translate API: {response.status_code} - {response.text}")
            
            return None
            
        except Exception as e:
            logger.warning(f"Erreur avec Google Translate: {e}")
            return None
    
    def _language_to_google_code(self, language):
        """Convertit un nom de langue en code pour Google Translate API"""
        mapping = {
            'fr': 'fr', 'french': 'fr',
            'en': 'en', 'english': 'en',
            'fon': 'yo',  # Utiliser yoruba comme approximation pour fon
            'ewe': 'yo',  # Utiliser yoruba comme approximation pour ewe  
            'dindi': 'yo',  # Utiliser yoruba comme approximation pour dindi
            'yor': 'yo', 'yoruba': 'yo'
        }
        return mapping.get(language.lower())
    
    def _translate_with_libretranslate(self, text, model_config):
        """Traduit avec l'API LibreTranslate"""
        payload = {
            "q": text,
            "source": self.source_lang,
            "target": self.target_lang,
            "format": "text"
        }
        
        if model_config.get('api_key'):
            payload["api_key"] = model_config['api_key']
        
        response = requests.post(
            f"{model_config['url']}/translate", 
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('translatedText', '')
        
        return None
    
    def _translate_with_marian(self, text, model_name):
        """Traduit avec un modèle Marian local"""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers non disponible pour les modèles Marian")
            return None
            
        try:
            # Charger le modèle et tokenizer
            tokenizer = MarianTokenizer.from_pretrained(model_name)
            model = MarianMTModel.from_pretrained(model_name)
            
            # Tokeniser et traduire
            inputs = tokenizer(text, return_tensors="pt", padding=True)
            translated = model.generate(**inputs)
            translation = tokenizer.decode(translated[0], skip_special_tokens=True)
            
            return translation
        except Exception as e:
            logger.warning(f"Erreur avec le modèle Marian {model_name}: {e}")
            return None