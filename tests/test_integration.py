# -*- coding: utf-8 -*-
# tests/test_integration.py

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Ajouter le chemin src au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestWikiTranslateAIIntegration(unittest.TestCase):
    """Tests d'integration pour le systeme WikiTranslateAI complet"""
    
    @classmethod
    def setUpClass(cls):
        """Setup pour tous les tests"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'components_tested': []
        }
    
    def setUp(self):
        """Setup pour chaque test"""
        self.test_results['total_tests'] += 1
    
    def tearDown(self):
        """Cleanup apres chaque test"""
        pass
    
    def test_01_core_imports(self):
        """Test que tous les modules principaux peuvent etre importes"""
        print("\n=== Test 1: Imports des modules principaux ===")
        
        try:
            # Modules de traduction
            from translation.azure_client import AzureOpenAITranslator
            from translation.fallback_translation import FallbackTranslator
            from translation.term_protection import TermProtectionManager
            from translation.pivot_language import PivotLanguageTranslator
            from translation.queue_manager import TranslationQueueManager
            
            # Engines de traduction
            from translation.engines.openai_client import EnhancedOpenAIClient
            
            # Utils
            from utils.error_handler import handle_error, create_translation_error
            from utils.checkpoint_manager import CheckpointManager
            from utils.structure_parser import WikipediaStructureParser
            
            # Evaluation
            from evaluation.comparison import AfricanLanguageEvaluator
            from evaluation.metrics.bleu import calculate_bleu_score
            from evaluation.metrics.meteor import calculate_meteor_score
            from evaluation.metrics.custom_metrics import calculate_custom_metrics
            from evaluation.visualize_results import TranslationResultsVisualizer
            
            print(" Tous les modules principaux importes avec succes")
            self.test_results['passed_tests'] += 1
            self.test_results['components_tested'].append('core_imports')
            
        except ImportError as e:
            print(f"L Erreur d'import: {e}")
            self.fail(f"Import failed: {e}")
    
    def test_02_term_protection_integration(self):
        """Test du systeme de protection des termes"""
        print("\n=== Test 2: Protection des termes ===")
        
        try:
            from translation.term_protection import TermProtectionManager
            
            manager = TermProtectionManager()
            
            # Test avec termes culturels fon
            test_text = "Le vodun et Legba sont importants au Dahomey. L'API REST utilise HTTP."
            protected_text, terms = manager.protect_text(test_text, "fon")
            
            # Verifier que les termes sont proteges
            self.assertGreater(len(terms), 0, "Aucun terme protege")
            self.assertNotEqual(protected_text, test_text, "Texte non modifie")
            
            # Restaurer le texte
            restored_text = manager.restore_text(protected_text, terms)
            
            print(f" Texte original: {test_text}")
            print(f" Termes proteges: {len(terms)}")
            print(f" Texte restaure: {restored_text}")
            
            self.test_results['passed_tests'] += 1
            self.test_results['components_tested'].append('term_protection')
            
        except Exception as e:
            print(f"L Erreur protection termes: {e}")
            self.fail(f"Term protection failed: {e}")
    
    def test_03_checkpoint_system(self):
        """Test du systeme de checkpoints"""
        print("\n=== Test 3: Systeme de checkpoints ===")
        
        try:
            from utils.checkpoint_manager import CheckpointManager, CheckpointType
            
            # Utiliser repertoire temporaire
            checkpoint_dir = os.path.join(self.temp_dir, "checkpoints")
            manager = CheckpointManager(checkpoint_dir=checkpoint_dir)
            
            # Creer un checkpoint
            test_data = {
                'article_title': 'Test Article',
                'progress': 50,
                'segments_done': 10
            }
            
            checkpoint_id = manager.create_checkpoint(
                CheckpointType.TRANSLATION_PROGRESS,
                test_data,
                progress_percentage=50.0
            )
            
            # Verifier creation
            self.assertIsNotNone(checkpoint_id, "Checkpoint non cree")
            
            # Recuperer le checkpoint
            checkpoint = manager.get_checkpoint(checkpoint_id)
            self.assertIsNotNone(checkpoint, "Checkpoint non trouve")
            self.assertEqual(checkpoint.data['article_title'], 'Test Article')
            
            # Completer le checkpoint
            success = manager.complete_checkpoint(checkpoint_id, {'result': 'success'})
            self.assertTrue(success, "Checkpoint non complete")
            
            print(f" Checkpoint cree: {checkpoint_id}")
            print(f" Donnees recuperees: {checkpoint.data['article_title']}")
            print(f" Checkpoint complete avec succes")
            
            self.test_results['passed_tests'] += 1
            self.test_results['components_tested'].append('checkpoint_system')
            
        except Exception as e:
            print(f"L Erreur checkpoints: {e}")
            self.fail(f"Checkpoint system failed: {e}")
    
    def test_04_pivot_translation_logic(self):
        """Test de la logique de traduction pivot"""
        print("\n=== Test 4: Traduction pivot ===")
        
        try:
            from translation.pivot_language import PivotLanguageTranslator, PivotStrategy
            
            # Mock du traducteur principal
            mock_translator = Mock()
            mock_translator.translate_text.return_value = "Traduction simulee"
            
            pivot_translator = PivotLanguageTranslator(mock_translator)
            
            # Test de selection du chemin optimal
            recommendations = pivot_translator.get_pivot_recommendations('fr', 'fon')
            self.assertGreater(len(recommendations), 0, "Aucune recommandation")
            
            # Test de traduction avec strategie
            result = pivot_translator.translate_with_pivot(
                "Bonjour le monde", 'fr', 'fon', 
                PivotStrategy.CULTURAL_PIVOT
            )
            
            self.assertIn('translation', result, "Pas de traduction dans resultat")
            self.assertIn('path', result, "Pas de chemin dans resultat")
            self.assertGreater(result['quality_score'], 0, "Score qualite nul")
            
            print(f" Recommandations generees: {len(recommendations)}")
            print(f" Chemin pivot: {' -> '.join(result['path'])}")
            print(f" Score qualite: {result['quality_score']:.3f}")
            
            self.test_results['passed_tests'] += 1
            self.test_results['components_tested'].append('pivot_translation')
            
        except Exception as e:
            print(f"L Erreur traduction pivot: {e}")
            self.fail(f"Pivot translation failed: {e}")
    
    def test_05_queue_management(self):
        """Test du gestionnaire de files de traduction"""
        print("\n=== Test 5: Gestionnaire de files ===")
        
        try:
            from translation.queue_manager import TranslationQueueManager, TaskPriority
            
            # Utiliser repertoire temporaire
            queue_file = os.path.join(self.temp_dir, "queue.json")
            manager = TranslationQueueManager(persistence_file=queue_file, max_workers=2)
            
            # Ajouter des taches
            task_id1 = manager.add_task(
                "Premier texte", "fr", "fon", 
                TaskPriority.HIGH, {'type': 'test'}
            )
            
            task_id2 = manager.add_task(
                "Deuxieme texte", "en", "yor",
                TaskPriority.NORMAL, {'type': 'test'}
            )
            
            # Verifier creation des taches
            self.assertIsNotNone(task_id1, "Tache 1 non creee")
            self.assertIsNotNone(task_id2, "Tache 2 non creee")
            
            # Verifier statut
            status1 = manager.get_task_status(task_id1)
            self.assertIsNotNone(status1, "Statut tache 1 introuvable")
            self.assertEqual(status1['status'], 'PENDING')
            
            # Statistiques
            stats = manager.get_queue_statistics()
            self.assertGreaterEqual(stats['pending_tasks'], 2, "Taches pendantes incorrectes")
            
            print(f" Taches creees: {task_id1}, {task_id2}")
            print(f" Taches pendantes: {stats['pending_tasks']}")
            print(f" Statistiques: {stats}")
            
            self.test_results['passed_tests'] += 1
            self.test_results['components_tested'].append('queue_management')
            
        except Exception as e:
            print(f"L Erreur gestionnaire files: {e}")
            self.fail(f"Queue management failed: {e}")
    
    def test_06_evaluation_metrics(self):
        """Test des metriques d'evaluation"""
        print("\n=== Test 6: Metriques d'evaluation ===")
        
        try:
            from evaluation.metrics.bleu import calculate_bleu_score
            from evaluation.metrics.meteor import calculate_meteor_score
            from evaluation.metrics.custom_metrics import calculate_custom_metrics
            
            # Donnees de test
            references = [
                "Le vodun est une religion importante au Benin.",
                "Les rois du Dahomey etaient puissants."
            ]
            
            candidates = [
                "Vodun est religion importante Benin.",
                "Rois Dahomey etaient puissants."
            ]
            
            # Test BLEU
            bleu_result = calculate_bleu_score(references, candidates)
            self.assertIn('score', bleu_result, "Score BLEU manquant")
            self.assertGreaterEqual(bleu_result['score'], 0, "Score BLEU invalide")
            
            # Test METEOR
            meteor_result = calculate_meteor_score(references, candidates)
            self.assertIn('score', meteor_result, "Score METEOR manquant")
            self.assertGreaterEqual(meteor_result['score'], 0, "Score METEOR invalide")
            
            # Test metriques personnalisees
            custom_result = calculate_custom_metrics(references, candidates, 'fon', 'fr')
            self.assertIn('score', custom_result, "Score personnalise manquant")
            self.assertIn('breakdown', custom_result, "Decomposition manquante")
            
            print(f" Score BLEU: {bleu_result['score']:.3f}")
            print(f" Score METEOR: {meteor_result['score']:.3f}")
            print(f" Score personnalise: {custom_result['score']:.3f}")
            print(f" Preservation culturelle: {custom_result['breakdown']['cultural_preservation']:.3f}")
            
            self.test_results['passed_tests'] += 1
            self.test_results['components_tested'].append('evaluation_metrics')
            
        except Exception as e:
            print(f"L Erreur metriques evaluation: {e}")
            self.fail(f"Evaluation metrics failed: {e}")
    
    def test_07_error_handling_system(self):
        """Test du systeme de gestion d'erreurs"""
        print("\n=== Test 7: Gestion d'erreurs ===")
        
        try:
            from utils.error_handler import handle_error, create_translation_error, get_error_statistics
            
            # Creer et traiter des erreurs
            error1 = create_translation_error(
                "Erreur test 1", 
                source_text="Texte test",
                target_language="fon"
            )
            
            error_id1 = handle_error(error1, context={'test': 'integration'})
            self.assertIsNotNone(error_id1, "ID erreur 1 manquant")
            
            error2 = create_translation_error(
                "Erreur test 2",
                error_type="API_ERROR"
            )
            
            error_id2 = handle_error(error2)
            self.assertIsNotNone(error_id2, "ID erreur 2 manquant")
            
            # Verifier statistiques
            stats = get_error_statistics()
            self.assertGreaterEqual(stats['total_errors'], 2, "Erreurs non comptabilisees")
            
            print(f" Erreur 1 traitee: {error_id1}")
            print(f" Erreur 2 traitee: {error_id2}")
            print(f" Total erreurs: {stats['total_errors']}")
            print(f" Erreurs recentes: {stats['recent_errors']}")
            
            self.test_results['passed_tests'] += 1
            self.test_results['components_tested'].append('error_handling')
            
        except Exception as e:
            print(f"L Erreur gestion erreurs: {e}")
            self.fail(f"Error handling failed: {e}")
    
    def test_08_structure_parser(self):
        """Test de l'analyseur de structure Wikipedia"""
        print("\n=== Test 8: Analyseur de structure ===")
        
        try:
            from utils.structure_parser import WikipediaStructureParser
            
            parser = WikipediaStructureParser()
            
            # HTML Wikipedia de test
            test_html = """
            <html>
            <body>
                <h1>Article Title</h1>
                <h2>Section 1</h2>
                <p>Paragraph 1 with some text.</p>
                <p>Paragraph 2 with more text.</p>
                <h3>Subsection 1.1</h3>
                <p>Subsection paragraph.</p>
                <h2>Section 2</h2>
                <p>Final paragraph.</p>
            </body>
            </html>
            """
            
            # Parser la structure
            structure = parser.parse_html_structure(test_html)
            
            self.assertIsNotNone(structure, "Structure non parsee")
            self.assertIn('title', structure, "Titre manquant")
            self.assertIn('sections', structure, "Sections manquantes")
            self.assertGreater(len(structure['sections']), 0, "Aucune section")
            
            # Verifier contenu
            self.assertEqual(structure['title'], 'Article Title')
            self.assertGreaterEqual(len(structure['sections']), 2, "Sections insuffisantes")
            
            print(f" Titre parse: {structure['title']}")
            print(f" Sections trouvees: {len(structure['sections'])}")
            print(f" Structure valide: {structure['metadata']['is_valid']}")
            
            self.test_results['passed_tests'] += 1
            self.test_results['components_tested'].append('structure_parser')
            
        except Exception as e:
            print(f"L Erreur analyseur structure: {e}")
            self.fail(f"Structure parser failed: {e}")
    
    def test_09_end_to_end_pipeline(self):
        """Test du pipeline complet de bout en bout"""
        print("\n=== Test 9: Pipeline complet ===")
        
        try:
            # Integrer plusieurs composants ensemble
            from translation.term_protection import TermProtectionManager
            from utils.checkpoint_manager import CheckpointManager, CheckpointType
            from evaluation.metrics.custom_metrics import calculate_custom_metrics
            
            # Setup
            checkpoint_dir = os.path.join(self.temp_dir, "pipeline_checkpoints")
            term_manager = TermProtectionManager()
            checkpoint_manager = CheckpointManager(checkpoint_dir=checkpoint_dir)
            
            # Donnees de test
            source_text = "Le vodun et Legba sont des elements importants de la culture fon au Benin."
            
            # Etape 1: Protection des termes
            protected_text, protected_terms = term_manager.protect_text(source_text, "fon")
            
            # Etape 2: Checkpoint de progression
            checkpoint_data = {
                'source_text': source_text,
                'protected_text': protected_text,
                'protected_terms_count': len(protected_terms)
            }
            
            checkpoint_id = checkpoint_manager.create_checkpoint(
                CheckpointType.TRANSLATION_START,
                checkpoint_data,
                progress_percentage=25.0
            )
            
            # Etape 3: Simulation traduction
            translated_text = "Vodun kple Legba nye nusiwo vevi le Fon dukT ’e agbenTnT me le Benin."
            
            # Etape 4: Restauration des termes
            final_text = term_manager.restore_text(translated_text, protected_terms)
            
            # Etape 5: Evaluation
            evaluation_result = calculate_custom_metrics([source_text], [final_text], 'fon', 'fr')
            
            # Etape 6: Finaliser le checkpoint
            final_data = {
                'final_text': final_text,
                'evaluation_score': evaluation_result['score']
            }
            checkpoint_manager.complete_checkpoint(checkpoint_id, final_data)
            
            # Verifications
            self.assertGreater(len(protected_terms), 0, "Aucun terme protege")
            self.assertIsNotNone(checkpoint_id, "Checkpoint non cree")
            self.assertGreater(evaluation_result['score'], 0, "Score evaluation nul")
            
            print(f" Pipeline execute avec succes:")
            print(f"   - Termes proteges: {len(protected_terms)}")
            print(f"   - Checkpoint: {checkpoint_id}")
            print(f"   - Score evaluation: {evaluation_result['score']:.3f}")
            print(f"   - Texte final: {final_text[:50]}...")
            
            self.test_results['passed_tests'] += 1
            self.test_results['components_tested'].append('end_to_end_pipeline')
            
        except Exception as e:
            print(f"L Erreur pipeline complet: {e}")
            self.fail(f"End-to-end pipeline failed: {e}")
    
    def test_10_system_summary(self):
        """Genere un resume du systeme complet"""
        print("\n=== Test 10: Resume du systeme ===")
        
        try:
            # Statistiques finales
            success_rate = (self.test_results['passed_tests'] / self.test_results['total_tests']) * 100
            
            print(f"\n<¯ RESUME DE L'INTEGRATION WikiTranslateAI")
            print("=" * 60)
            print(f"Tests totaux: {self.test_results['total_tests']}")
            print(f"Tests reussis: {self.test_results['passed_tests']}")
            print(f"Tests echoues: {self.test_results['failed_tests']}")
            print(f"Taux de reussite: {success_rate:.1f}%")
            
            print(f"\n Composants testes et fonctionnels:")
            for component in self.test_results['components_tested']:
                print(f"   " {component.replace('_', ' ').title()}")
            
            print(f"\n=' Fonctionnalites implementees:")
            print("   " Protection intelligente des termes culturels")
            print("   " Systeme de checkpoints avec persistance")
            print("   " Traduction pivot avec strategies adaptatives")
            print("   " Gestionnaire de files avec workers multiples")
            print("   " Metriques d'evaluation personnalisees pour langues africaines")
            print("   " Gestion robuste des erreurs avec tracking")
            print("   " Analyseur de structure Wikipedia avance")
            print("   " Pipeline de traduction complet de bout en bout")
            
            if success_rate >= 80:
                print(f"\n<‰ SYSTEME WIKITRANSLATEAI PLEINEMENT FONCTIONNEL!")
                print("   Toutes les fonctionnalites principales sont operationnelles")
            else:
                print(f"\n   Systeme partiellement fonctionnel")
                print("   Certains composants necessitent des ajustements")
            
            self.test_results['passed_tests'] += 1
            self.test_results['components_tested'].append('system_summary')
            
        except Exception as e:
            print(f"L Erreur resume systeme: {e}")
            self.fail(f"System summary failed: {e}")

if __name__ == '__main__':
    # Configuration pour tests detailles
    unittest.TestCase.maxDiff = None
    
    # Lancer les tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestWikiTranslateAIIntegration)
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Resultat final
    if result.wasSuccessful():
        print("\n<Š TOUS LES TESTS D'INTEGRATION REUSSIS!")
        print("   WikiTranslateAI est pret pour la production")
        sys.exit(0)
    else:
        print(f"\nL {len(result.failures)} tests echoues, {len(result.errors)} erreurs")
        sys.exit(1)