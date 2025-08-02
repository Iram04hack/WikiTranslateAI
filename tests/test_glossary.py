# tests/test_glossary.py

import os
import sys
import unittest
import tempfile
import json

# Ajouter le répertoire parent au chemin de recherche
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.schema import create_database_schema
from src.database.glossary_manager import GlossaryManager
from src.translation.glossary_match import GlossaryMatcher

class TestGlossary(unittest.TestCase):
    
    def setUp(self):
        # Créer une base de données temporaire pour les tests
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Initialiser le schéma
        create_database_schema(self.db_path)
        
        # Créer un fichier de glossaire temporaire
        self.temp_glossary = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
        self.glossary_path = self.temp_glossary.name
        
        sample_glossary = [
            {
                "source_term": "computer",
                "source_lang": "en",
                "target_term": "ordinatɛ",
                "target_lang": "fon",
                "domain": "tech",
                "confidence": 0.9,
                "validated": True
            },
            {
                "source_term": "artificial intelligence",
                "source_lang": "en",
                "target_term": "yɛyɛ nununɛ",
                "target_lang": "fon",
                "domain": "tech",
                "confidence": 0.8,
                "validated": False
            }
        ]
        
        with open(self.glossary_path, 'w', encoding='utf-8') as f:
            json.dump(sample_glossary, f, ensure_ascii=False)
    
    def tearDown(self):
        # Supprimer les fichiers temporaires
        os.unlink(self.db_path)
        os.unlink(self.glossary_path)
    
    def test_glossary_import(self):
        """Teste l'importation du glossaire"""
        with GlossaryManager(self.db_path) as gm:
            count = gm.batch_import(self.glossary_path)
            self.assertEqual(count, 2, "Deux termes devraient être importés")
            
            # Vérifier que les termes sont recherchables
            results = gm.search_term("computer", "en", "fon")
            self.assertEqual(len(results), 1, "Un terme devrait être trouvé")
            self.assertEqual(results[0]['target_term'], "ordinatɛ")
    
    def test_glossary_matcher(self):
        """Teste le matcher de glossaire"""
        with GlossaryManager(self.db_path) as gm:
            gm.batch_import(self.glossary_path)
        
        matcher = GlossaryMatcher(self.db_path)
        text = "The computer uses artificial intelligence to process data."
        
        matches = matcher.find_matches(text, "en", "fon")
        self.assertEqual(len(matches), 2, "Deux correspondances devraient être trouvées")
        self.assertIn("computer", matches)
        self.assertIn("artificial intelligence", matches)
        
        # Vérifier que les données nécessaires sont présentes
        for term, match in matches.items():
            self.assertIn('target_term', match, f"La clé 'target_term' manque pour {term}")
            # Vérifier que le terme a au moins certaines propriétés attendues
            self.assertTrue(
                'validated' in match, 
                f"La clé 'validated' manque pour {term}"
            )
        
        # Tester le prompt augmenté
        prompt = matcher.augment_translation_prompt(text, "en", "fon")
        self.assertIn("ordinatɛ", prompt)
        self.assertIn("yɛyɛ nununɛ", prompt)
    
    def test_glossary_export(self):
        """Teste l'exportation du glossaire"""
        with GlossaryManager(self.db_path) as gm:
            gm.batch_import(self.glossary_path)
            
            # Exporter vers un nouveau fichier
            temp_export = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
            export_path = temp_export.name
            temp_export.close()
            
            count = gm.export_glossary(export_path, "en", "fon")
            self.assertEqual(count, 2, "Deux termes devraient être exportés")
            
            # Vérifier le contenu du fichier exporté
            with open(export_path, 'r', encoding='utf-8') as f:
                exported = json.load(f)
                self.assertEqual(len(exported), 2)
                self.assertEqual(exported[0]['source_term'], "computer")
            
            os.unlink(export_path)

if __name__ == '__main__':
    unittest.main()