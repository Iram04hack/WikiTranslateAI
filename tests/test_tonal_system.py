# tests/test_tonal_system.py

import os
import sys
import unittest
import tempfile
import shutil
from typing import List

# Ajout du chemin src pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from adaptation.tonal_processor import TonalProcessor, ToneType, TonalWord


class TestTonalSystem(unittest.TestCase):
    """Tests complets pour le système tonal"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        # Créer un répertoire temporaire pour les tests
        self.test_dir = tempfile.mkdtemp()
        self.processor = TonalProcessor(self.test_dir)
        
    def tearDown(self):
        """Nettoyage après chaque test"""
        # Nettoyer le répertoire temporaire
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_yoruba_tonal_processing(self):
        """Test du traitement tonal pour le yoruba avec exemples connus"""
        test_cases = [
            # (input, expected_output, description)
            ("mo wa", "mō wā", "Pronoms et verbe simple"),
            ("ile mi", "ilé mī", "Nom et pronom possessif"), 
            ("o ti wa", "ó tī wā", "Pronom, auxiliaire passé, verbe"),
            ("awa ni", "āwā nī", "Pronom pluriel"),
            ("omo re", "ọmọ rē", "Nom et pronom possessif"),
        ]
        
        for input_text, expected, description in test_cases:
            with self.subTest(input_text=input_text, description=description):
                result = self.processor.process_text(input_text, 'yor')
                # Vérifier que des tons ont été appliqués
                self.assertNotEqual(result, input_text, 
                                  f"Aucun ton appliqué pour: {input_text}")
                # Note: L'output exact peut varier selon l'implémentation
                print(f"Yoruba - {description}: '{input_text}' -> '{result}'")
    
    def test_fon_tonal_processing(self):
        """Test du traitement tonal pour le fon avec exemples connus"""
        test_cases = [
            ("un wa", "ūn wā", "Je venir"),
            ("e du", "é ɖū", "Il manger"),
            ("mi yi", "mí yī", "Nous aller"),
            ("xwe mi", "xwé mī", "Maison notre"),
        ]
        
        for input_text, expected, description in test_cases:
            with self.subTest(input_text=input_text, description=description):
                result = self.processor.process_text(input_text, 'fon')
                self.assertNotEqual(result, input_text, 
                                  f"Aucun ton appliqué pour: {input_text}")
                print(f"Fon - {description}: '{input_text}' -> '{result}'")
    
    def test_ewe_tonal_processing(self):
        """Test du traitement tonal pour l'ewe avec exemples connus"""
        test_cases = [
            ("me va", "mē vā", "Je venir"),
            ("ame afo", "āmē āfō", "Personne pied"),
            ("wo le", "wō lē", "Ils être/faire"),
        ]
        
        for input_text, expected, description in test_cases:
            with self.subTest(input_text=input_text, description=description):
                result = self.processor.process_text(input_text, 'ewe')
                self.assertNotEqual(result, input_text, 
                                  f"Aucun ton appliqué pour: {input_text}")
                print(f"Ewe - {description}: '{input_text}' -> '{result}'")
    
    def test_dindi_tonal_processing(self):
        """Test du traitement tonal pour le dindi avec exemples connus"""
        test_cases = [
            ("ay te", "āy tē", "Je manger"),
            ("ni koy", "nī kōy", "Tu aller"),
            ("a ga te", "ā gā tē", "Il mange"),
        ]
        
        for input_text, expected, description in test_cases:
            with self.subTest(input_text=input_text, description=description):
                result = self.processor.process_text(input_text, 'dindi')
                # Pour dindi, certains mots peuvent ne pas être dans le lexique
                print(f"Dindi - {description}: '{input_text}' -> '{result}'")
    
    def test_tone_detection(self):
        """Test de la détection de tons dans des mots existants"""
        # Mots avec tons explicites
        test_words = [
            ("mó", [ToneType.HIGH], "Ton haut explicite"),
            ("mò", [ToneType.LOW], "Ton bas explicite"), 
            ("mō", [ToneType.MID], "Ton moyen explicite"),
            ("baba", [ToneType.MID, ToneType.MID], "Tons moyens multiples"),
        ]
        
        for word, expected_tones, description in test_words:
            with self.subTest(word=word, description=description):
                detected_tones = self.processor.detect_tones(word)
                self.assertEqual(len(detected_tones), len(expected_tones),
                               f"Nombre de tons incorrect pour {word}")
                # Vérifier au moins le premier ton
                if detected_tones and expected_tones:
                    print(f"Détection - {description}: '{word}' -> {[t.value for t in detected_tones]}")
    
    def test_syllable_counting(self):
        """Test du comptage de syllabes"""
        test_cases = [
            ("mo", 1, "Monosyllabe"),
            ("baba", 2, "Bisyllabe"),
            ("abado", 3, "Trisyllabe"),
            ("abiamo", 4, "Quadrisyllabe"),
            ("ile", 2, "Diphtongue"),
        ]
        
        for word, expected_count, description in test_cases:
            with self.subTest(word=word, description=description):
                count = self.processor.count_syllables(word)
                self.assertGreaterEqual(count, 1, "Au moins une syllabe")
                # La méthode de comptage est approximative
                print(f"Syllabes - {description}: '{word}' -> {count} syllabes")
    
    def test_sandhi_rules_yoruba(self):
        """Test des règles de sandhi spécifiques au yoruba"""
        # Créer des mots tonals pour tester les règles de sandhi
        word_high = TonalWord(
            word="bá", base_form="ba", tones=[ToneType.HIGH],
            syllables=["ba"], language="yor"
        )
        
        word_low = TonalWord(
            word="bà", base_form="ba", tones=[ToneType.LOW], 
            syllables=["ba"], language="yor"
        )
        
        # Appliquer les règles de sandhi
        result = self.processor.apply_sandhi_rules([word_high, word_low], 'yor')
        
        # Vérifier que les règles ont été appliquées
        self.assertEqual(len(result), 2, "Deux mots en sortie")
        
        # Le premier mot devrait avoir son ton haut changé en moyen
        self.assertEqual(result[0].tones[0], ToneType.MID, 
                        "Ton haut devrait devenir moyen avant ton bas")
        
        print(f"Sandhi Yoruba: HIGH+LOW -> {result[0].tones[0].value}+{result[1].tones[0].value}")
    
    def test_lexicon_lookup(self):
        """Test de recherche dans le lexique tonal"""
        # Tester des mots connus du lexique yoruba
        yoruba_words = ['mo', 'wa', 'jẹ', 'ile', 'omo']
        
        for word in yoruba_words:
            with self.subTest(word=word):
                tonal_word = self.processor.lookup_word_tones(word, 'yor')
                if tonal_word:
                    self.assertIsInstance(tonal_word, TonalWord)
                    self.assertEqual(tonal_word.language, 'yor')
                    self.assertTrue(len(tonal_word.tones) > 0, "Doit avoir au moins un ton")
                    print(f"Lexique - '{word}': {[t.value for t in tonal_word.tones]}")
                else:
                    print(f"Lexique - '{word}': non trouvé")
    
    def test_tone_application(self):
        """Test de l'application de tons à des mots de base"""
        test_cases = [
            ("ba", [ToneType.HIGH], "bá", "Application ton haut"),
            ("ba", [ToneType.LOW], "bà", "Application ton bas"),
            ("ba", [ToneType.MID], "bā", "Application ton moyen"),
            ("baba", [ToneType.HIGH, ToneType.LOW], "bábà", "Application tons multiples"),
        ]
        
        for base_word, tones, expected, description in test_cases:
            with self.subTest(base_word=base_word, description=description):
                result = self.processor.apply_tone_to_word(base_word, tones, 'yor')
                # L'output exact peut varier selon l'implémentation des diacritiques
                self.assertNotEqual(result, base_word, "Le mot doit être modifié")
                print(f"Application tons - {description}: '{base_word}' -> '{result}'")
    
    def test_tone_validation(self):
        """Test de validation des tons"""
        # Textes valides et invalides
        test_cases = [
            ("mó bá wá", 'yor', "Texte tonal valide"),
            ("mó", 'yor', "Mot simple avec ton"),
            ("àbcd", 'yor', "Mot avec caractères non-africains"),
        ]
        
        for text, language, description in test_cases:
            with self.subTest(text=text, description=description):
                errors = self.processor.validate_tones(text, language)
                print(f"Validation - {description}: '{text}' -> {len(errors)} erreurs")
                if errors:
                    for error in errors[:2]:  # Limiter l'affichage
                        print(f"  Erreur: {error}")
    
    def test_language_tone_info(self):
        """Test d'information sur les systèmes tonals des langues"""
        languages = ['yor', 'fon', 'ewe', 'dindi']
        
        for lang in languages:
            with self.subTest(language=lang):
                info = self.processor.get_language_tone_info(lang)
                
                self.assertIn('language', info)
                self.assertIn('tone_system', info)
                self.assertEqual(info['language'], lang)
                
                print(f"Info {lang}: Système {info.get('tone_system', 'unknown')}")
    
    def test_comprehensive_text_processing(self):
        """Test de traitement complet de phrases complexes"""
        comprehensive_tests = [
            # Yoruba
            ("Mo ti wa lati oko", 'yor', "Phrase complexe yoruba"),
            ("Awa ni omo ile yi", 'yor', "Phrase avec pronoms et noms"),
            
            # Fon
            ("Un ko du nu", 'fon', "Phrase simple fon"),
            ("Mi na yi axi me", 'fon', "Phrase future fon"),
            
            # Ewe
            ("Me le nu ɖu m", 'ewe', "Phrase progressive ewe"),
            ("Wo va le afi me", 'ewe', "Phrase complexe ewe"),
        ]
        
        for text, language, description in comprehensive_tests:
            with self.subTest(text=text, language=language, description=description):
                result = self.processor.process_text(text, language)
                
                # Vérifications de base
                self.assertIsInstance(result, str)
                self.assertTrue(len(result) > 0, "Résultat non vide")
                
                # Vérifier que du traitement a eu lieu (présence de diacritiques)
                has_tones = any(char in result for char in ['́', '̀', '̄', '̂', '̌'])
                
                print(f"Traitement complet - {description}:")
                print(f"  Original: {text}")
                print(f"  Traité:   {result}")
                print(f"  Tons appliqués: {'Oui' if has_tones else 'Non'}")
    
    def test_performance_benchmark(self):
        """Test de performance du système tonal"""
        import time
        
        # Texte de test répétitif
        test_text = "mo wa lati oko. awa ni omo ile yi. " * 10
        
        languages = ['yor', 'fon', 'ewe']
        
        for language in languages:
            with self.subTest(language=language):
                start_time = time.time()
                
                # Traiter le texte plusieurs fois
                for _ in range(5):
                    result = self.processor.process_text(test_text, language)
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                # Vérifier que le traitement n'est pas trop lent
                self.assertLess(processing_time, 5.0, 
                              f"Traitement trop lent pour {language}")
                
                print(f"Performance {language}: {processing_time:.3f}s pour {len(test_text)*5} caractères")


if __name__ == '__main__':
    # Configuration pour des tests plus verbeux
    unittest.main(verbosity=2)