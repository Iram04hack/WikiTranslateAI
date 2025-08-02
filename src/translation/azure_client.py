import os
import sys
import time
import logging
import json
import asyncio
from openai import OpenAI
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AzureOpenAITranslator:
    """Client pour la traduction via l'API Azure OpenAI"""

    def __init__(self, api_key, api_version=None, azure_endpoint=None, model="gpt-4o-mini", glossary_db_path=None):
        # Utiliser OpenAI standard plutôt qu'Azure pour cette clé
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.glossary_db_path = glossary_db_path
        self.glossary_matcher = None

        if glossary_db_path:
            try:
                from ..database.glossary_manager import GlossaryManager
                from ..translation.glossary_match import GlossaryMatcher
                self.glossary_matcher = GlossaryMatcher(glossary_db_path)
            except (ImportError, ModuleNotFoundError) as e:
                logger.warning(f"Impossible de charger le glossaire: {e}")

        self.max_retries = 3
        self.retry_delay = 2
        self.rate_limit_delay = 0.5

    def translate_text(self, text, source_language, target_language, domain=None, use_glossary=True):
        if not text or not text.strip():
            return ""

        prompt = self._create_translation_prompt(
            text, source_language, target_language, domain, use_glossary
        )

        for attempt in range(self.max_retries):
            try:
                time.sleep(self.rate_limit_delay)
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}]
                )

                translation = response.choices[0].message.content
                return translation.strip() if translation else ""

            except Exception as e:
                logger.warning(f"Erreur lors de la traduction (tentative {attempt+1}/{self.max_retries}): {e}")

                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    time.sleep(delay)
                else:
                    logger.error(f"Échec de la traduction après {self.max_retries} tentatives.")

                    try:
                        from src.translation.fallback_translation import FallbackTranslator
                        fallback = FallbackTranslator(source_language, target_language)
                        fallback_translation = fallback.translate(text)
                        logger.info("Traduction effectuée avec le modèle de secours")
                        return fallback_translation
                    except Exception as fallback_error:
                        logger.error(f"Erreur avec le traducteur de secours: {fallback_error}")
                        # Retourner une chaîne sécurisée pour noms de fichiers (sans caractères spéciaux)
                        return "ERREUR_TRADUCTION_COMPLETE_TOUS_SYSTEMES_ECHECS"

    def _create_translation_prompt(self, text, source_language, target_language, domain=None, use_glossary=True):
        if use_glossary and self.glossary_matcher:
            try:
                return self.glossary_matcher.augment_translation_prompt(
                    text, source_language, target_language, domain
                )
            except Exception as e:
                logger.warning(f"Erreur lors de l'utilisation du glossaire: {e}")

        prompt = f"""Traduisez le texte suivant de {source_language} vers {target_language}.

Texte à traduire :
{text}

Traduction :"""
        return prompt

    def translate_segments(self, segments, source_language, target_language, domain=None, use_glossary=True):
        translated_segments = []
        total_segments = len(segments)

        logger.info(f"Début de la traduction de {total_segments} segments")

        try:
            from src.utils.progress import ProgressBar
            progress = ProgressBar(total_segments, f"Traduction {source_language} → {target_language}")
            progress.start()
        except ImportError:
            progress = None
            logger.info(f"[0/{total_segments}] Démarrage...")

        success_count = 0
        fallback_count = 0
        error_count = 0

        for i, segment in enumerate(segments):
            if progress:
                progress.update(i, f"Traduction segment {i+1}")
            else:
                logger.info(f"Traduction du segment {i+1}/{total_segments}")

            preview = segment[:50] + "..." if len(segment) > 50 else segment
            logger.info(f"Source: {preview}")

            translation = self.translate_text(
                segment, source_language, target_language, domain, use_glossary
            )

            if translation:
                if "ERREUR_TRADUCTION_COMPLETE" in translation or "TRADUCTION_IMPOSSIBLE" in translation:
                    error_count += 1
                elif "[FALLBACK]" in translation:
                    fallback_count += 1
                    translation = translation.replace("[FALLBACK] ", "")
                else:
                    success_count += 1

            if translation:
                trans_preview = translation[:50] + "..." if len(translation) > 50 else translation
                logger.info(f"Traduction: {trans_preview}")

            translated_segments.append(translation)

            if progress:
                status = f"Succès: {success_count}, Repli: {fallback_count}, Erreurs: {error_count}"
                progress.update(i + 1, status)

            if i % 5 == 0 and i > 0:
                temp_file = f"temp_translations_{source_language}_{target_language}.json"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'source_language': source_language,
                        'target_language': target_language,
                        'progress': f"{i+1}/{total_segments}",
                        'stats': {
                            'success': success_count,
                            'fallback': fallback_count,
                            'errors': error_count
                        },
                        'translated_segments': translated_segments
                    }, f, ensure_ascii=False, indent=2)
                logger.info(f"Sauvegarde des traductions partielles dans {temp_file}")

        if progress:
            progress.finish()

        logger.info(f"Traduction de la section terminée: {len(translated_segments)}/{total_segments} segments")
        logger.info(f"Statistiques: Succès: {success_count}, Repli: {fallback_count}, Erreurs: {error_count}")

        return translated_segments

    def translate_article(self, article_data, source_language, target_language, use_glossary=True):
        title = article_data.get('title', '')
        metadata = article_data.get('metadata', {})
        segmented_sections = article_data.get('segmented_sections', [])

        logger.info(f"Traduction du titre: {title}")
        translated_title = self.translate_text(
            title, source_language, target_language, 'general', use_glossary
        )
        logger.info(f"Titre traduit: {translated_title}")

        translated_sections = []

        for section_index, section in enumerate(segmented_sections):
            section_title = section.get('title', '')
            section_level = section.get('level', 0)
            segments = section.get('segments', [])

            logger.info(f"Traduction de la section {section_index+1}/{len(segmented_sections)}: {section_title}")

            translated_section_title = self.translate_text(
                section_title, source_language, target_language, 'general', use_glossary
            )
            logger.info(f"Titre de section traduit: {translated_section_title}")

            domain = metadata.get('categories', ['general'])[0] if metadata.get('categories') else 'general'
            logger.info(f"Domaine: {domain}, Nombre de segments: {len(segments)}")

            translated_segments = self.translate_segments(
                segments, source_language, target_language, domain, use_glossary
            )

            translated_sections.append({
                'title': translated_section_title,
                'level': section_level,
                'segments': translated_segments,
                'original_segments': segments
            })

            partial_article = {
                'title': translated_title,
                'original_title': title,
                'metadata': metadata,
                'source_language': source_language,
                'target_language': target_language,
                'translated_sections': translated_sections
            }

            temp_file = f"temp_article_{source_language}_{target_language}.json"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(partial_article, f, ensure_ascii=False, indent=2)
            logger.info(f"État intermédiaire sauvegardé dans {temp_file}")

        translated_article = {
            'title': translated_title,
            'original_title': title,
            'metadata': metadata,
            'source_language': source_language,
            'target_language': target_language,
            'translated_sections': translated_sections
        }

        return translated_article

    def translate_article_file(self, input_file_path, source_language, target_language, output_dir=None, use_glossary=True):
        logger.info(f"Traduction de l'article {input_file_path} de {source_language} vers {target_language}")

        try:
            with open(input_file_path, 'r', encoding='utf-8') as f:
                article_data = json.load(f)

            translated_article = self.translate_article(
                article_data, source_language, target_language, use_glossary
            )

            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                target_dir = os.path.join(output_dir, target_language)
                os.makedirs(target_dir, exist_ok=True)

                filename = os.path.basename(input_file_path)
                output_path = os.path.join(target_dir, filename)

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(translated_article, f, ensure_ascii=False, indent=2)

                logger.info(f"Article traduit sauvegardé: {output_path}")

                txt_dir = os.path.join(output_dir, f"{target_language}_txt")
                os.makedirs(txt_dir, exist_ok=True)
                txt_filename = os.path.splitext(os.path.basename(input_file_path))[0] + ".txt"
                txt_path = os.path.join(txt_dir, txt_filename)

                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(f"Titre original: {article_data.get('title', '')}\n")
                    f.write(f"Titre traduit: {translated_article.get('title', '')}\n\n")
                    for section in translated_article.get('translated_sections', []):
                        level = section.get('level', 0)
                        section_title = section.get('title', '')
                        segments = section.get('segments', [])
                        f.write(f"{'#' * (level + 1)} {section_title}\n\n")
                        for segment in segments:
                            if segment and not segment.startswith("ERREUR_TRADUCTION_COMPLETE"):
                                f.write(f"{segment}\n\n")

                logger.info(f"Version texte de l'article traduit sauvegardée: {txt_path}")
                return output_path

            return translated_article

        except Exception as e:
            logger.error(f"Erreur lors de la traduction de l'article {input_file_path}: {e}")
            return None


def create_translator_from_env(glossary_db_path=None):
    api_key = os.environ.get('OPENAI_API_KEY')
    model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')

    if not api_key:
        raise ValueError("La variable d'environnement OPENAI_API_KEY est requise")

    return AzureOpenAITranslator(api_key, model=model, glossary_db_path=glossary_db_path)
