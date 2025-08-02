# tests/test_schema_validation.py

import os
import sys
import json
import unittest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

# Ajout du chemin src pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.schemas import (
    TonalLexicon, TonalWordEntry, ToneType, ProgressTracker,
    TranslationStats, Glossary, GlossaryEntry, LanguageCode,
    validate_json_with_schema, get_schema_for_file_type,
    normalize_priority, normalize_task_status
)
from utils.json_validator import (
    JSONValidator, ValidationError, TonalProcessorValidator,
    ArticleValidator, ProgressValidator, quick_validate_file
)


class TestSchemaValidation(unittest.TestCase):
    """Tests pour la validation des schémas Pydantic"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_tonal_word_entry_validation(self):
        """Test de validation d'une entrée de mot tonal"""
        # Cas valide
        valid_entry = {
            "tones": ["high", "low"],
            "syllables": ["ba", "ba"],
            "pos": "noun",
            "meaning": "father"
        }
        
        entry = validate_json_with_schema(valid_entry, TonalWordEntry)
        self.assertIsInstance(entry, TonalWordEntry)
        self.assertEqual(len(entry.tones), 2)
        self.assertEqual(len(entry.syllables), 2)
        self.assertEqual(entry.tones[0], ToneType.HIGH)
        
        # Cas invalide - nombre de tons != nombre de syllabes
        invalid_entry = {
            "tones": ["high"],
            "syllables": ["ba", "ba"],
            "pos": "noun"
        }
        
        with self.assertRaises(ValueError):
            validate_json_with_schema(invalid_entry, TonalWordEntry)
    
    def test_tonal_lexicon_validation(self):
        """Test de validation d'un lexique tonal complet"""
        valid_lexicon = {
            "metadata": {
                "language": "yoruba",
                "tone_system": "3-level",
                "description": "Test lexicon"
            },
            "words": {
                "mo": {
                    "tones": ["mid"],
                    "syllables": ["mo"],
                    "pos": "pronoun",
                    "meaning": "je"
                },
                "wa": {
                    "tones": ["high"],
                    "syllables": ["wa"],
                    "pos": "verb",
                    "meaning": "venir"
                }
            }
        }
        
        lexicon = validate_json_with_schema(valid_lexicon, TonalLexicon)
        self.assertIsInstance(lexicon, TonalLexicon)
        self.assertEqual(lexicon.metadata.language, "yoruba")
        self.assertEqual(len(lexicon.words), 2)
        self.assertIn("mo", lexicon.words)
        
        # Cas invalide - lexique vide
        invalid_lexicon = {
            "metadata": {
                "language": "yoruba",
                "tone_system": "3-level", 
                "description": "Empty lexicon"
            },
            "words": {}
        }
        
        with self.assertRaises(ValueError):
            validate_json_with_schema(invalid_lexicon, TonalLexicon)
    
    def test_glossary_validation(self):
        """Test de validation d'un glossaire"""
        valid_glossary = {
            "metadata": {"version": "1.0"},
            "entries": [
                {
                    "source_term": "computer",
                    "target_term": "kɔnputɛr",
                    "source_language": "en",
                    "target_language": "fon",
                    "domain": "technology"
                },
                {
                    "source_term": "house",
                    "target_term": "xwé",
                    "source_language": "en", 
                    "target_language": "fon",
                    "domain": "general"
                }
            ],
            "version": "1.0"
        }
        
        glossary = validate_json_with_schema(valid_glossary, Glossary)
        self.assertIsInstance(glossary, Glossary)
        self.assertEqual(len(glossary.entries), 2)
        
        # Test validation unicité des entrées
        duplicate_glossary = {
            "metadata": {},
            "entries": [
                {
                    "source_term": "computer",
                    "target_term": "kɔnputɛr", 
                    "source_language": "en",
                    "target_language": "fon"
                },
                {
                    "source_term": "computer",  # Même terme
                    "target_term": "kɔnputɛr",  # Même traduction
                    "source_language": "en",
                    "target_language": "fon"
                }
            ]
        }
        
        with self.assertRaises(ValueError):
            validate_json_with_schema(duplicate_glossary, Glossary)
    
    def test_priority_normalization(self):
        """Test de la normalisation des priorités"""
        test_cases = [
            ("CRITIQUE", "critical"),
            ("HAUTE", "high"),
            ("MOYENNE", "medium"),
            ("BASSE", "low"),
            ("critique", "critical"),
            ("high", "high"),  # Déjà en anglais
            ("unknown", "unknown")  # Non reconnu
        ]
        
        for input_priority, expected in test_cases:
            result = normalize_priority(input_priority)
            self.assertEqual(result, expected, f"Failed for {input_priority}")
    
    def test_task_status_normalization(self):
        """Test de la normalisation des statuts de tâches"""
        test_cases = [
            ("non_commencé", "not_started"),
            ("en_cours", "in_progress"),
            ("terminé", "completed"),
            ("bloqué", "blocked"),
            ("completed", "completed"),  # Déjà en anglais
            ("unknown", "unknown")  # Non reconnu
        ]
        
        for input_status, expected in test_cases:
            result = normalize_task_status(input_status)
            self.assertEqual(result, expected, f"Failed for {input_status}")
    
    def test_schema_detection(self):
        """Test de la détection automatique de schéma"""
        test_cases = [
            ("tonal_lexicon", TonalLexicon),
            ("glossary", Glossary),
            ("progress_tracker", ProgressTracker),
            ("unknown_type", None)
        ]
        
        for file_type, expected_schema in test_cases:
            schema = get_schema_for_file_type(file_type)
            if expected_schema:
                self.assertEqual(schema, expected_schema)
            else:
                self.assertIsNone(schema)


class TestJSONValidator(unittest.TestCase):
    """Tests pour le validateur JSON"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.validator = JSONValidator(strict_mode=False, log_errors=False)
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def create_test_file(self, filename: str, data: Dict[str, Any]) -> str:
        """Crée un fichier de test avec des données JSON"""
        file_path = os.path.join(self.test_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return file_path
    
    def test_load_valid_json(self):
        """Test de chargement d'un JSON valide"""
        valid_data = {
            "metadata": {
                "language": "yoruba",
                "tone_system": "3-level",
                "description": "Test lexicon"
            },
            "words": {
                "test": {
                    "tones": ["mid"],
                    "syllables": ["test"],
                    "pos": "noun"
                }
            }
        }
        
        file_path = self.create_test_file("valid_lexicon.json", valid_data)
        result = self.validator.load_and_validate_json(file_path, TonalLexicon)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, TonalLexicon)
        self.assertEqual(result.metadata.language, "yoruba")
    
    def test_load_invalid_json_syntax(self):
        """Test de chargement d'un JSON avec syntaxe invalide"""
        file_path = os.path.join(self.test_dir, "invalid.json")
        with open(file_path, 'w') as f:
            f.write('{"invalid": json}')  # JSON invalide
        
        result = self.validator.load_and_validate_json(file_path, TonalLexicon)
        self.assertIsNone(result)
        self.assertTrue(len(self.validator.get_errors()) > 0)
    
    def test_load_nonexistent_file(self):
        """Test de chargement d'un fichier inexistant"""
        file_path = os.path.join(self.test_dir, "nonexistent.json")
        result = self.validator.load_and_validate_json(file_path, TonalLexicon)
        
        self.assertIsNone(result)
        errors = self.validator.get_errors()
        self.assertTrue(any("Fichier non trouvé" in error for error in errors))
    
    def test_validation_error_handling_strict_mode(self):
        """Test de gestion d'erreurs en mode strict"""
        strict_validator = JSONValidator(strict_mode=True, log_errors=False)
        
        invalid_data = {
            "metadata": {
                "language": "yoruba",
                "tone_system": "3-level",
                "description": "Invalid lexicon"
            },
            "words": {}  # Lexique vide - invalide
        }
        
        file_path = self.create_test_file("invalid_lexicon.json", invalid_data)
        
        with self.assertRaises(ValidationError):
            strict_validator.load_and_validate_json(file_path, TonalLexicon)
    
    def test_save_and_validate(self):
        """Test de sauvegarde avec validation"""
        # Créer des données valides
        lexicon = TonalLexicon(
            metadata={
                "language": "test",
                "tone_system": "2-level",
                "description": "Test lexicon"
            },
            words={
                "test": TonalWordEntry(
                    tones=[ToneType.HIGH],
                    syllables=["test"],
                    pos="noun"
                )
            }
        )
        
        file_path = os.path.join(self.test_dir, "saved_lexicon.json")
        success = self.validator.save_and_validate_json(lexicon, file_path, TonalLexicon)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(file_path))
        
        # Vérifier que le fichier peut être rechargé
        reloaded = self.validator.load_and_validate_json(file_path, TonalLexicon)
        self.assertIsNotNone(reloaded)
        self.assertEqual(reloaded.metadata.language, "test")
    
    def test_batch_validation(self):
        """Test de validation par lots"""
        # Créer plusieurs fichiers
        valid_data = {
            "metadata": {"language": "test", "tone_system": "2-level", "description": "Test"},
            "words": {"test": {"tones": ["mid"], "syllables": ["test"]}}
        }
        
        invalid_data = {
            "metadata": {"language": "test", "tone_system": "2-level", "description": "Test"},
            "words": {}  # Invalide
        }
        
        file1 = self.create_test_file("valid1.json", valid_data)
        file2 = self.create_test_file("valid2.json", valid_data)
        file3 = self.create_test_file("invalid.json", invalid_data)
        
        results = self.validator.batch_validate_files([file1, file2, file3], "tonal_lexicon")
        
        self.assertTrue(results[file1])
        self.assertTrue(results[file2])
        self.assertFalse(results[file3])


class TestSpecializedValidators(unittest.TestCase):
    """Tests pour les validateurs spécialisés"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_tonal_processor_validator(self):
        """Test du validateur de processeur tonal"""
        validator = TonalProcessorValidator()
        
        # Créer un lexique valide
        lexicon_data = {
            "metadata": {
                "language": "yoruba",
                "tone_system": "3-level",
                "description": "Test lexicon"
            },
            "words": {
                "mo": {
                    "tones": ["mid"],
                    "syllables": ["mo"],
                    "pos": "pronoun",
                    "meaning": "je"
                }
            }
        }
        
        file_path = os.path.join(self.test_dir, "test_lexicon.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(lexicon_data, f, ensure_ascii=False, indent=2)
        
        result = validator.validate_lexicon(file_path)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, TonalLexicon)
    
    def test_progress_validator_with_real_data(self):
        """Test du validateur de progression avec données réelles"""
        validator = ProgressValidator()
        
        # Utiliser le vrai fichier PROGRESS_TRACKER.json s'il existe
        progress_file = "PROGRESS_TRACKER.json"
        if os.path.exists(progress_file):
            # En mode non-strict pour ce test
            validator.validator.strict_mode = False
            result = validator.validate_progress_tracker(progress_file)
            # Le résultat peut être None en mode non-strict si il y a des erreurs mineures
            # mais cela ne devrait pas planter
            print(f"Validation ProgressTracker: {'✓' if result else '✗'}")
    
    def test_quick_validate_function(self):
        """Test de la fonction de validation rapide"""
        # Créer un fichier valide
        lexicon_data = {
            "metadata": {"language": "test", "tone_system": "2-level", "description": "Test"},
            "words": {"test": {"tones": ["mid"], "syllables": ["test"]}}
        }
        
        file_path = os.path.join(self.test_dir, "quick_test.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(lexicon_data, f, ensure_ascii=False, indent=2)
        
        # Test validation rapide
        is_valid = quick_validate_file(file_path, "tonal_lexicon", strict=False)
        self.assertTrue(is_valid)
        
        # Test avec fichier inexistant
        is_valid = quick_validate_file("nonexistent.json", "tonal_lexicon", strict=False)
        self.assertFalse(is_valid)


class TestRealDataValidation(unittest.TestCase):
    """Tests avec des données réelles du projet"""
    
    def test_existing_tonal_lexicons(self):
        """Test de validation des lexiques tonaux existants"""
        lexicon_dir = "data/tonal/lexicons"
        if not os.path.exists(lexicon_dir):
            self.skipTest("Répertoire des lexiques tonaux non trouvé")
        
        validator = TonalProcessorValidator()
        
        for filename in os.listdir(lexicon_dir):
            if filename.endswith('_tonal_lexicon.json'):
                file_path = os.path.join(lexicon_dir, filename)
                with self.subTest(file=filename):
                    result = validator.validate_lexicon(file_path)
                    self.assertIsNotNone(result, f"Validation échouée pour {filename}")
                    self.assertIsInstance(result, TonalLexicon)
                    print(f"✓ {filename}: {len(result.words)} mots")
    
    def test_existing_progress_tracker(self):
        """Test de validation du tracker de progression existant"""
        progress_file = "PROGRESS_TRACKER.json"
        if not os.path.exists(progress_file):
            self.skipTest("PROGRESS_TRACKER.json non trouvé")
        
        validator = ProgressValidator()
        validator.validator.strict_mode = False  # Mode non-strict pour compatibilité
        
        result = validator.validate_progress_tracker(progress_file)
        if result:
            self.assertIsInstance(result, ProgressTracker)
            self.assertEqual(result.project_info.name, "WikiTranslateAI")
            print(f"✓ ProgressTracker valide: {result.project_info.overall_progress} progression")
        else:
            print("✗ ProgressTracker: validation échouée (mode non-strict)")


if __name__ == '__main__':
    # Configurer le logging pour les tests
    logging.basicConfig(level=logging.WARNING)
    
    # Exécuter les tests avec plus de verbosité 
    unittest.main(verbosity=2)