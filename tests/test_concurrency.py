# tests/test_concurrency.py

import os
import sys
import unittest
import threading
import time
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ajout du chemin src pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.translation_tracker import TranslationTracker


class TestTranslationTrackerConcurrency(unittest.TestCase):
    """Tests de concurrence pour TranslationTracker"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        # Créer un répertoire temporaire pour les tests
        self.test_dir = tempfile.mkdtemp()
        self.original_history_file = None
        
        # Réinitialiser le singleton pour chaque test
        TranslationTracker._instance = None
        
    def tearDown(self):
        """Nettoyage après chaque test"""
        # Nettoyer le répertoire temporaire
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
        # Réinitialiser le singleton
        TranslationTracker._instance = None
        
    def test_singleton_thread_safety(self):
        """Test que le singleton est thread-safe"""
        instances = []
        
        def get_instance():
            instances.append(TranslationTracker.get_instance())
        
        # Lancer plusieurs threads qui créent l'instance
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=get_instance)
            threads.append(thread)
            thread.start()
        
        # Attendre que tous les threads se terminent
        for thread in threads:
            thread.join()
        
        # Vérifier que toutes les instances sont identiques
        first_instance = instances[0]
        for instance in instances:
            self.assertIs(instance, first_instance)
            
    def test_concurrent_record_translation(self):
        """Test d'enregistrement concurrent de traductions"""
        tracker = TranslationTracker.get_instance()
        tracker.history_file = os.path.join(self.test_dir, "test_history.json")
        
        # Fonction pour enregistrer une traduction
        def record_translation(thread_id):
            for i in range(20):
                tracker.record_translation(
                    article_title=f"Article_{thread_id}_{i}",
                    source_lang="fr",
                    target_lang="fon",
                    categories=[f"category_{thread_id}"]
                )
                # Petite pause pour simuler du travail réel
                time.sleep(0.001)
        
        # Lancer plusieurs threads
        threads = []
        num_threads = 5
        translations_per_thread = 20
        
        for thread_id in range(num_threads):
            thread = threading.Thread(target=record_translation, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Attendre que tous les threads se terminent
        for thread in threads:
            thread.join()
        
        # Vérifier les statistiques finales
        stats = tracker.get_stats()
        expected_total = num_threads * translations_per_thread
        
        self.assertEqual(stats['total_global'], expected_total)
        self.assertEqual(stats['total_by_language']['fr-fon'], expected_total)
        
        # Vérifier que chaque catégorie a le bon nombre d'enregistrements
        for thread_id in range(num_threads):
            category = f"category_{thread_id}"
            self.assertEqual(stats['categories'][category], translations_per_thread)
    
    def test_concurrent_file_operations(self):
        """Test des opérations de fichier concurrentes"""
        tracker = TranslationTracker.get_instance()
        tracker.history_file = os.path.join(self.test_dir, "test_concurrent_file.json")
        
        results = []
        errors = []
        
        def stress_test_translation(thread_id):
            try:
                for i in range(10):
                    tracker.record_translation(
                        article_title=f"StressTest_{thread_id}_{i}",
                        source_lang="en",
                        target_lang="yor",
                        categories=["stress_test"]
                    )
                    # Forcer la sauvegarde fréquente
                    time.sleep(0.002)
                results.append(f"Thread {thread_id} completed")
            except Exception as e:
                errors.append(f"Thread {thread_id} error: {str(e)}")
        
        # Utiliser ThreadPoolExecutor pour un test plus réaliste
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(stress_test_translation, i) 
                for i in range(8)
            ]
            
            # Attendre que tous les futures se terminent
            for future in as_completed(futures):
                future.result()
        
        # Vérifier qu'il n'y a pas eu d'erreurs
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 8)
        
        # Vérifier l'intégrité des données
        stats = tracker.get_stats()
        self.assertEqual(stats['total_global'], 80)  # 8 threads * 10 traductions
        self.assertEqual(stats['categories']['stress_test'], 80)
        
        # Vérifier que le fichier existe et est valide
        self.assertTrue(os.path.exists(tracker.history_file))
        
    def test_stats_consistency_under_load(self):
        """Test de cohérence des statistiques sous charge"""
        tracker = TranslationTracker.get_instance()
        tracker.history_file = os.path.join(self.test_dir, "test_consistency.json")
        
        # Données de test variées
        test_data = [
            ("Article1", "fr", "fon", ["science"]),
            ("Article2", "en", "yor", ["history"]),
            ("Article3", "fr", "ewe", ["culture"]),
            ("Article4", "en", "dindi", ["science", "history"]),
        ]
        
        def worker(data_set):
            for article, source, target, categories in data_set:
                tracker.record_translation(article, source, target, categories)
                time.sleep(0.001)
        
        # Créer plusieurs workers avec différents sets de données
        threads = []
        for i in range(4):
            # Chaque thread traite le même set de données 25 fois
            thread_data = test_data * 25
            thread = threading.Thread(target=worker, args=(thread_data,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Vérifier la cohérence des statistiques
        stats = tracker.get_stats()
        
        # Total global doit être égal à la somme des traductions par langue
        total_by_lang = sum(stats['total_by_language'].values())
        self.assertEqual(stats['total_global'], total_by_lang)
        self.assertEqual(stats['total_global'], 400)  # 4 threads * 4 articles * 25 répétitions
        
        # Vérifier les catégories
        expected_science = 200  # 2 articles avec "science" * 4 threads * 25 répétitions
        expected_history = 200  # 2 articles avec "history" * 4 threads * 25 répétitions
        expected_culture = 100  # 1 article avec "culture" * 4 threads * 25 répétitions
        
        self.assertEqual(stats['categories']['science'], expected_science)
        self.assertEqual(stats['categories']['history'], expected_history)
        self.assertEqual(stats['categories']['culture'], expected_culture)
        
    def test_get_stats_thread_safety(self):
        """Test que get_stats() retourne des données cohérentes pendant les modifications"""
        tracker = TranslationTracker.get_instance()
        tracker.history_file = os.path.join(self.test_dir, "test_get_stats.json")
        
        stats_snapshots = []
        stop_flag = threading.Event()
        
        def continuous_recording():
            counter = 0
            while not stop_flag.is_set():
                tracker.record_translation(
                    article_title=f"ContinuousArticle_{counter}",
                    source_lang="fr",
                    target_lang="fon",
                    categories=["continuous"]
                )
                counter += 1
                time.sleep(0.01)
        
        def periodic_stats():
            while not stop_flag.is_set():
                stats = tracker.get_stats()
                stats_snapshots.append(stats['total_global'])
                time.sleep(0.005)
        
        # Lancer les threads
        recording_thread = threading.Thread(target=continuous_recording)
        stats_thread = threading.Thread(target=periodic_stats)
        
        recording_thread.start()
        stats_thread.start()
        
        # Laisser tourner pendant 0.5 seconde
        time.sleep(0.5)
        stop_flag.set()
        
        recording_thread.join()
        stats_thread.join()
        
        # Vérifier que nous avons collecté des statistiques
        self.assertGreater(len(stats_snapshots), 0)
        
        # Vérifier que les statistiques sont monotones croissantes
        for i in range(1, len(stats_snapshots)):
            self.assertGreaterEqual(
                stats_snapshots[i], 
                stats_snapshots[i-1],
                "Les statistiques ne devraient jamais décroître"
            )


if __name__ == '__main__':
    unittest.main()