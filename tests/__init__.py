# -*- coding: utf-8 -*-
"""
Suite de tests WikiTranslateAI

Tests complets pour tous les modules du système de traduction Wikipedia
vers les langues africaines.

Modules de tests:
- test_translation: Pipeline de traduction principal
- test_extraction: Extraction d'articles Wikipedia
- test_reconstruction: Reconstruction d'articles traduits
- test_evaluation: Métriques d'évaluation de qualité
- test_integration: Tests d'intégration bout-en-bout
- test_tonal_system: Système de tonalité africaine
- test_concurrency: Tests de performance et concurrence
"""

import os
import sys
import unittest
from pathlib import Path

# Ajouter le répertoire src au path pour les imports
TEST_ROOT = Path(__file__).parent
PROJECT_ROOT = TEST_ROOT.parent
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

# Configuration des tests
TEST_CONFIG = {
    'test_data_dir': str(PROJECT_ROOT / 'data' / 'test'),
    'output_dir': str(PROJECT_ROOT / 'test_output'),
    'mock_api_calls': True,  # Par défaut, mocker les appels API
    'cleanup_after_tests': True,
    'parallel_tests': False,
    'verbose_output': True
}

def setup_test_environment():
    """
    Configure l'environnement de test
    
    Returns:
        True si configuration réussie
    """
    try:
        # Créer les répertoires de test
        os.makedirs(TEST_CONFIG['test_data_dir'], exist_ok=True)
        os.makedirs(TEST_CONFIG['output_dir'], exist_ok=True)
        
        # Variables d'environnement pour les tests
        os.environ['WIKITRANSLATE_TEST_MODE'] = 'true'
        os.environ['WIKITRANSLATE_TEST_DATA'] = TEST_CONFIG['test_data_dir']
        
        return True
        
    except Exception as e:
        print(f"Erreur configuration environnement de test: {e}")
        return False

def cleanup_test_environment():
    """Nettoie l'environnement après les tests"""
    if TEST_CONFIG['cleanup_after_tests']:
        try:
            import shutil
            # Nettoyer seulement les fichiers temporaires, pas les données de test
            temp_dirs = [
                TEST_CONFIG['output_dir'],
                str(PROJECT_ROOT / 'temp_test_data')
            ]
            
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    
        except Exception as e:
            print(f"Erreur nettoyage environnement de test: {e}")

def discover_and_run_tests(test_pattern: str = 'test_*.py', 
                          verbosity: int = 2) -> unittest.TestResult:
    """
    Découvre et exécute tous les tests
    
    Args:
        test_pattern: Pattern pour découvrir les tests
        verbosity: Niveau de verbosité (0=quiet, 1=normal, 2=verbose)
        
    Returns:
        Résultats des tests
    """
    # Configuration environnement
    setup_test_environment()
    
    try:
        # Découverte des tests
        loader = unittest.TestLoader()
        start_dir = str(TEST_ROOT)
        suite = loader.discover(start_dir, pattern=test_pattern)
        
        # Exécution des tests
        runner = unittest.TextTestRunner(
            verbosity=verbosity,
            stream=sys.stdout,
            descriptions=True,
            failfast=False
        )
        
        result = runner.run(suite)
        
        # Rapport final
        print(f"\n{'='*60}")
        print(f"RÉSULTATS DES TESTS WIKITRANSLATEAI")
        print(f"{'='*60}")
        print(f"Tests exécutés: {result.testsRun}")
        print(f"Succès: {result.testsRun - len(result.failures) - len(result.errors)}")
        print(f"Échecs: {len(result.failures)}")
        print(f"Erreurs: {len(result.errors)}")
        
        if result.failures:
            print(f"\nÉCHECS:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback.split(chr(10))[-2] if chr(10) in traceback else traceback}")
        
        if result.errors:
            print(f"\nERREURS:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback.split(chr(10))[-2] if chr(10) in traceback else traceback}")
        
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / max(result.testsRun, 1)) * 100
        print(f"\nTaux de réussite: {success_rate:.1f}%")
        
        return result
        
    finally:
        cleanup_test_environment()

def run_specific_test_module(module_name: str) -> unittest.TestResult:
    """
    Exécute un module de test spécifique
    
    Args:
        module_name: Nom du module (ex: 'test_translation')
        
    Returns:
        Résultats du test
    """
    setup_test_environment()
    
    try:
        # Import et exécution du module spécifique
        test_module = __import__(module_name)
        
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_module)
        
        runner = unittest.TextTestRunner(verbosity=2)
        return runner.run(suite)
        
    except ImportError as e:
        print(f"Impossible d'importer le module de test {module_name}: {e}")
        return None
    finally:
        cleanup_test_environment()

# Classes de base pour les tests
class WikiTranslateTestCase(unittest.TestCase):
    """Classe de base pour tous les tests WikiTranslateAI"""
    
    @classmethod
    def setUpClass(cls):
        """Configuration pour toute la classe de test"""
        setup_test_environment()
    
    @classmethod
    def tearDownClass(cls):
        """Nettoyage après toute la classe de test"""
        cleanup_test_environment()
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.test_data_dir = Path(TEST_CONFIG['test_data_dir'])
        self.output_dir = Path(TEST_CONFIG['output_dir'])
        
        # Créer des répertoires temporaires pour ce test
        self.temp_dir = self.output_dir / f"temp_{self._testMethodName}"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        # Nettoyer les fichiers temporaires de ce test
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)

class IntegrationTestCase(WikiTranslateTestCase):
    """Classe de base pour les tests d'intégration"""
    
    def setUp(self):
        super().setUp()
        # Configuration spécifique aux tests d'intégration
        self.integration_timeout = 60  # 60 secondes pour les tests d'intégration

class MockTestCase(WikiTranslateTestCase):
    """Classe de base pour les tests avec mocks"""
    
    def setUp(self):
        super().setUp()
        # Configuration des mocks
        if TEST_CONFIG['mock_api_calls']:
            self.setup_mocks()
    
    def setup_mocks(self):
        """Configure les mocks pour les appels externes"""
        # À implémenter dans les classes enfants
        pass

# Exports principaux
__all__ = [
    'TEST_CONFIG',
    'setup_test_environment',
    'cleanup_test_environment', 
    'discover_and_run_tests',
    'run_specific_test_module',
    'WikiTranslateTestCase',
    'IntegrationTestCase',
    'MockTestCase'
]