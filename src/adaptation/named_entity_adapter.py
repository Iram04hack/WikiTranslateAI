#!/usr/bin/env python3
# src/adaptation/named_entity_adapter.py

import os
import json
import logging
import re
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NamedEntityAdapter:
    """Classe pour la gestion des entités nommées spécifiques aux langues africaines"""
    
    def __init__(self, entities_dir=None):
        """
        Initialise l'adaptateur d'entités nommées
        
        Args:
            entities_dir: Répertoire contenant les entités nommées (optionnel)
        """
        self.entities_dir = entities_dir or os.path.join("data", "entities")
        self.entities_cache = {}  # Cache des entités chargées
        
        # Créer le répertoire des entités s'il n'existe pas
        os.makedirs(self.entities_dir, exist_ok=True)
        
        # Charger les entités prédéfinies si aucun fichier externe n'est disponible
        self._ensure_default_entities()
    
    def _ensure_default_entities(self):
        """Assure que des entités par défaut sont disponibles pour les langues cibles"""
        default_entities = {
            "fon": self._get_default_fon_entities(),
            "dindi": self._get_default_dindi_entities(),
            "ewe": self._get_default_ewe_entities(),
            "yor": self._get_default_yoruba_entities(),
            "common": self._get_common_entities()
        }
        
        for lang, entities in default_entities.items():
            entities_file = os.path.join(self.entities_dir, f"{lang}_entities.json")
            
            if not os.path.exists(entities_file):
                try:
                    os.makedirs(os.path.dirname(entities_file), exist_ok=True)
                    with open(entities_file, 'w', encoding='utf-8') as f:
                        json.dump(entities, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"Entités nommées par défaut créées pour {lang}")
                except Exception as e:
                    logger.error(f"Erreur lors de la création des entités par défaut pour {lang}: {e}")
    
    def _get_common_entities(self):
        """Renvoie les entités nommées communes à toutes les langues africaines"""
        return {
            "name": "Entités nommées communes",
            "description": "Entités nommées communes aux langues africaines",
            "people": [
                {"original": "Nelson Mandela", "local": "Nelson Mandela"},
                {"original": "Kwame Nkrumah", "local": "Kwame Nkrumah"},
                {"original": "Kofi Annan", "local": "Kofi Annan"},
                {"original": "Wole Soyinka", "local": "Wole Soyinka"},
                {"original": "Chinua Achebe", "local": "Chinua Achebe"}
            ],
            "places": [
                {"original": "Africa", "local": "Afrika"},
                {"original": "Sahara", "local": "Sahara"},
                {"original": "Nile", "local": "Nil"},
                {"original": "Congo River", "local": "Congo"},
                {"original": "Lake Victoria", "local": "Victoria"}
            ],
            "organizations": [
                {"original": "African Union", "local": "UA"},
                {"original": "ECOWAS", "local": "CEDEAO"},
                {"original": "United Nations", "local": "ONU"},
                {"original": "World Health Organization", "local": "OMS"}
            ]
        }
    
    def _get_default_fon_entities(self):
        """Renvoie les entités nommées par défaut pour le fon"""
        return {
            "name": "Entités nommées du Fon",
            "description": "Entités nommées spécifiques au Fon (Bénin)",
            "people": [
                {"original": "Behanzin", "local": "Gbɛhanzin"},
                {"original": "Agadja", "local": "Agaja"},
                {"original": "Ghezo", "local": "Gezo"},
                {"original": "Toffa", "local": "Tofa"},
                {"original": "Adandozan", "local": "Adandozan"}
            ],
            "places": [
                {"original": "Benin", "local": "Danhomɛ"},
                {"original": "Abomey", "local": "Agbomɛ"},
                {"original": "Ouidah", "local": "Glexwe"},
                {"original": "Cotonou", "local": "Kutonu"},
                {"original": "Porto-Novo", "local": "Xɔgbonou"},
                {"original": "Allada", "local": "Alada"}
            ],
            "cultural_terms": [
                {"original": "Vodun", "local": "Vodun"},
                {"original": "Legba", "local": "Legba"},
                {"original": "Dambada Hwedo", "local": "Dambada Hwedo"},
                {"original": "Sakpata", "local": "Sakpata"},
                {"original": "Fa", "local": "Fa"}
            ],
            "titles": [
                {"original": "King", "local": "Axɔsu"},
                {"original": "Queen", "local": "Kpojito"},
                {"original": "Chief", "local": "Dokpwɛgan"},
                {"original": "Priest", "local": "Bokonɔ"},
                {"original": "Warrior", "local": "Gangnihessou"}
            ]
        }
    
    def _get_default_dindi_entities(self):
        """Renvoie les entités nommées par défaut pour le dindi"""
        return {
            "name": "Entités nommées du Dindi",
            "description": "Entités nommées spécifiques au Dindi (Bénin/Togo)",
            "people": [
                {"original": "Boukari Koutou", "local": "Boukari Koutou"},
                {"original": "Sabi Chabi", "local": "Sabi Chabi"}
            ],
            "places": [
                {"original": "Djougou", "local": "Juugu"},
                {"original": "Parakou", "local": "Parakuu"},
                {"original": "Niger River", "local": "Kwara"}
            ],
            "cultural_terms": [
                {"original": "Dinde", "local": "Dindi"},
                {"original": "Baatonu", "local": "Baatɔnu"}
            ],
            "titles": [
                {"original": "Sultan", "local": "Sunɔn"},
                {"original": "Warrior", "local": "Kɛrɛkɛtigi"}
            ]
        }
    
    def _get_default_ewe_entities(self):
        """Renvoie les entités nommées par défaut pour l'ewe"""
        return {
            "name": "Entités nommées de l'Ewe",
            "description": "Entités nommées spécifiques à l'Ewe (Ghana/Togo)",
            "people": [
                {"original": "Togbe Tsali", "local": "Tɔgbui Tsali"},
                {"original": "Agokoli", "local": "Agɔkɔli"},
                {"original": "Sri I", "local": "Sri I"},
                {"original": "Foli Bebe", "local": "Foli Bebe"},
                {"original": "Togbe Wenya", "local": "Tɔgbui Wenya"}
            ],
            "places": [
                {"original": "Togo", "local": "Togo"},
                {"original": "Ghana", "local": "Ghana"},
                {"original": "Lome", "local": "Lomé"},
                {"original": "Kpalime", "local": "Kpalimé"},
                {"original": "Notsé", "local": "Notsé"},
                {"original": "Anloga", "local": "Anloga"}
            ],
            "cultural_terms": [
                {"original": "Trɔ", "local": "Trɔ"},
                {"original": "Afa", "local": "Afa"},
                {"original": "Yehwe", "local": "Yehwe"},
                {"original": "Hogbetsotso", "local": "Hogbetsotso"}
            ],
            "titles": [
                {"original": "King", "local": "Fia"},
                {"original": "Chief", "local": "Tɔgbui"},
                {"original": "Queen", "local": "Fiaga"},
                {"original": "Priest", "local": "Trɔnua"},
                {"original": "Elder", "local": "Ametsitsi"}
            ]
        }
    
    def _get_default_yoruba_entities(self):
        """Renvoie les entités nommées par défaut pour le yoruba"""
        return {
            "name": "Entités nommées du Yoruba",
            "description": "Entités nommées spécifiques au Yoruba (Nigeria/Bénin)",
            "people": [
                {"original": "Oduduwa", "local": "Odùduwà"},
                {"original": "Oranmiyan", "local": "Ọranmiyan"},
                {"original": "Shango", "local": "Ṣàngó"},
                {"original": "Moremi", "local": "Mọremí"},
                {"original": "Obafemi Awolowo", "local": "Obafẹmi Awolọwọ"}
            ],
            "places": [
                {"original": "Nigeria", "local": "Nàìjíríà"},
                {"original": "Ife", "local": "Ilé-Ifẹ̀"},
                {"original": "Oyo", "local": "Ọ̀yọ́"},
                {"original": "Ibadan", "local": "Ìbàdàn"},
                {"original": "Lagos", "local": "Èkó"},
                {"original": "Abeokuta", "local": "Abẹ́òkúta"}
            ],
            "cultural_terms": [
                {"original": "Orisha", "local": "Òrìṣà"},
                {"original": "Ifa", "local": "Ifá"},
                {"original": "Ogun", "local": "Ògún"},
                {"original": "Egungun", "local": "Egúngún"},
                {"original": "Aso Oke", "local": "Aṣọ Òkè"}
            ],
            "titles": [
                {"original": "King", "local": "Ọba"},
                {"original": "Chief", "local": "Baalẹ̀"},
                {"original": "Queen", "local": "Ayaba"},
                {"original": "Priest", "local": "Babalawo"},
                {"original": "Princess", "local": "Ọmọba"}
            ]
        }
    
    def load_entities(self, language):
        """
        Charge les entités nommées pour une langue
        
        Args:
            language: Code de la langue (fon, dindi, ewe, yor)
            
        Returns:
            Dictionnaire des entités ou None en cas d'erreur
        """
        # Vérifier le cache
        if language in self.entities_cache:
            return self.entities_cache[language]
        
        # Normaliser le code de langue
        lang_map = {
            "yoruba": "yor", "yo": "yor",
            "ee": "ewe",
            "fongbe": "fon",
            "dendi": "dindi", "ddn": "dindi"
        }
        
        norm_lang = lang_map.get(language.lower(), language.lower())
        
        # Chercher le fichier d'entités
        entities_file = os.path.join(self.entities_dir, f"{norm_lang}_entities.json")
        common_file = os.path.join(self.entities_dir, "common_entities.json")
        
        try:
            entities = {}
            
            # Charger les entités communes
            if os.path.exists(common_file):
                with open(common_file, 'r', encoding='utf-8') as f:
                    common_entities = json.load(f)
                entities.update(common_entities)
            
            # Charger les entités spécifiques à la langue
            if os.path.exists(entities_file):
                with open(entities_file, 'r', encoding='utf-8') as f:
                    lang_entities = json.load(f)
                
                # Fusionner avec les entités communes
                for category, items in lang_entities.items():
                    if category in entities and isinstance(items, list):
                        # Pour les listes d'entités, les fusionner
                        entities[category].extend(items)
                    else:
                        # Pour les autres catégories, remplacer ou ajouter
                        entities[category] = items
                
                # Mettre en cache
                self.entities_cache[language] = entities
                self.entities_cache[norm_lang] = entities
                
                logger.info(f"Entités nommées chargées pour {language}")
                return entities
            else:
                logger.warning(f"Fichier d'entités introuvable pour {language}: {entities_file}")
                return None
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement des entités pour {language}: {e}")
            return None
    
    def detect_entities(self, text, language):
        """
        Détecte les entités nommées dans un texte
        
        Args:
            text: Texte à analyser
            language: Code de la langue
            
        Returns:
            Liste des entités détectées avec leur type
        """
        entities = self.load_entities(language)
        
        if not entities:
            logger.warning(f"Aucune entité trouvée pour {language}, détection impossible")
            return []
        
        detected = []
        categories = ['people', 'places', 'organizations', 'cultural_terms', 'titles']
        
        for category in categories:
            if category in entities:
                for entity in entities[category]:
                    original = entity.get('original', '')
                    if original and original in text:
                        detected.append({
                            'text': original,
                            'type': category[:-1],  # Enlever le 's' à la fin
                            'local': entity.get('local', original)
                        })
        
        return detected
    
    def replace_entities(self, text, language, use_local=True):
        """
        Remplace les entités nommées dans un texte par leurs équivalents locaux
        
        Args:
            text: Texte à traiter
            language: Code de la langue
            use_local: Utiliser les formes locales (True) ou originales (False)
            
        Returns:
            Texte avec entités remplacées
        """
        entities = self.load_entities(language)
        
        if not entities:
            logger.warning(f"Aucune entité trouvée pour {language}, remplacement impossible")
            return text
        
        result = text
        categories = ['people', 'places', 'organizations', 'cultural_terms', 'titles']
        
        # Trier les entités par longueur décroissante pour éviter les remplacements partiels
        all_entities = []
        for category in categories:
            if category in entities:
                all_entities.extend(entities[category])
        
        sorted_entities = sorted(all_entities, key=lambda e: len(e.get('original', '')), reverse=True)
        
        # Remplacer les entités
        for entity in sorted_entities:
            original = entity.get('original', '')
            local = entity.get('local', original)
            
            if use_local:
                # Remplacer l'original par la forme locale
                result = result.replace(original, local)
            else:
                # Remplacer la forme locale par l'original
                result = result.replace(local, original)
        
        return result
    
    def transliterate_name(self, name, target_language):
        """
        Translittère un nom propre selon les règles phonologiques de la langue cible
        
        Args:
            name: Nom à translittérer
            target_language: Langue cible
            
        Returns:
            Nom translittéré
        """
        # Règles de translittération simplifiées par langue
        transliteration_rules = {
            "fon": [
                {"from": "c", "to": "k"},
                {"from": "j", "to": "dj"},
                {"from": "q", "to": "k"},
                {"from": "r", "to": "l"},
                {"from": "th", "to": "t"},
                {"from": "x", "to": "ks"},
                {"from": "w", "to": "w"}
            ],
            "dindi": [
                {"from": "c", "to": "s"},
                {"from": "j", "to": "z"},
                {"from": "q", "to": "k"},
                {"from": "th", "to": "t"},
                {"from": "x", "to": "ks"},
                {"from": "w", "to": "w"}
            ],
            "ewe": [
                {"from": "c", "to": "k"},
                {"from": "j", "to": "dz"},
                {"from": "q", "to": "kw"},
                {"from": "th", "to": "t"},
                {"from": "x", "to": "ks"},
                {"from": "w", "to": "ʋ"}
            ],
            "yor": [
                {"from": "c", "to": "k"},
                {"from": "j", "to": "j"},
                {"from": "q", "to": "k"},
                {"from": "th", "to": "t"},
                {"from": "x", "to": "ks"},
                {"from": "w", "to": "w"}
            ]
        }
        
        # Normaliser le code de langue
        lang_map = {
            "yoruba": "yor", "yo": "yor",
            "ee": "ewe",
            "fongbe": "fon",
            "dendi": "dindi", "ddn": "dindi"
        }
        
        norm_lang = lang_map.get(target_language.lower(), target_language.lower())
        
        if norm_lang not in transliteration_rules:
            logger.warning(f"Aucune règle de translittération pour {target_language}")
            return name
        
        # Appliquer les règles
        transliterated = name.lower()
        for rule in transliteration_rules[norm_lang]:
            transliterated = transliterated.replace(rule['from'], rule['to'])
        
        # Restaurer la casse
        if name[0].isupper():
            transliterated = transliterated.capitalize()
        
        return transliterated
    
    def save_entities(self, entities, language):
        """
        Sauvegarde les entités nommées pour une langue
        
        Args:
            entities: Dictionnaire des entités
            language: Code de la langue
            
        Returns:
            Booléen indiquant le succès de l'opération
        """
        # Normaliser le code de langue
        lang_map = {
            "yoruba": "yor", "yo": "yor",
            "ee": "ewe",
            "fongbe": "fon",
            "dendi": "dindi", "ddn": "dindi"
        }
        
        norm_lang = lang_map.get(language.lower(), language.lower())
        
        # Chemin du fichier d'entités
        entities_file = os.path.join(self.entities_dir, f"{norm_lang}_entities.json")
        
        try:
            # Créer le répertoire si nécessaire
            os.makedirs(os.path.dirname(entities_file), exist_ok=True)
            
            # Sauvegarder les entités
            with open(entities_file, 'w', encoding='utf-8') as f:
                json.dump(entities, f, ensure_ascii=False, indent=2)
            
            # Mettre à jour le cache
            self.entities_cache[language] = entities
            self.entities_cache[norm_lang] = entities
            
            logger.info(f"Entités nommées sauvegardées pour {language}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des entités pour {language}: {e}")
            return False
    
    def add_entity(self, category, original, local, language):
        """
        Ajoute une nouvelle entité nommée
        
        Args:
            category: Catégorie de l'entité (people, places, etc.)
            original: Forme originale de l'entité
            local: Forme locale de l'entité
            language: Code de la langue
            
        Returns:
            Booléen indiquant le succès de l'opération
        """
        entities = self.load_entities(language)
        
        if not entities:
            # Créer une nouvelle structure d'entités
            entities = {
                "name": f"Entités nommées de {language}",
                "description": f"Entités nommées spécifiques à {language}",
                "people": [],
                "places": [],
                "organizations": [],
                "cultural_terms": [],
                "titles": []
            }
        
        # S'assurer que la catégorie existe
        if category not in entities or not isinstance(entities[category], list):
            entities[category] = []
        
        # Vérifier si l'entité existe déjà
        for entity in entities[category]:
            if entity.get('original') == original:
                # Mettre à jour l'entité existante
                entity['local'] = local
                return self.save_entities(entities, language)
        
        # Ajouter la nouvelle entité
        entities[category].append({
            "original": original,
            "local": local
        })
        
        return self.save_entities(entities, language)