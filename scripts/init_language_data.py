#!/usr/bin/env python3
# scripts/init_language_data.py

import os
import sys
import argparse
import logging
from pathlib import Path

# Ajouter le répertoire parent au chemin de recherche
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.adaptation.orthographic_adapter import OrthographicAdapter
from src.adaptation.linguistic_adapter import LinguisticAdapter
from src.adaptation.named_entity_adapter import NamedEntityAdapter
from src.adaptation.language_adapter import LanguageAdapter
from src.utils.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_all_language_data(config_file=None):
    """
    Initialise toutes les données linguistiques pour les langues cibles
    
    Args:
        config_file: Chemin vers le fichier de configuration (optionnel)
    """
    # Charger la configuration
    config = load_config(config_file)
    
    # Répertoires de données
    data_dir = config['paths'].get('data_dir', 'data')
    rules_dir = os.path.join(data_dir, "rules")
    entities_dir = os.path.join(data_dir, "entities")
    
    # Créer les répertoires si nécessaire
    os.makedirs(os.path.join(rules_dir, "orthographic"), exist_ok=True)
    os.makedirs(os.path.join(rules_dir, "linguistic"), exist_ok=True)
    os.makedirs(entities_dir, exist_ok=True)
    
    # Initialiser les adaptateurs pour charger les règles par défaut
    logger.info("Initialisation des règles orthographiques")
    ortho_adapter = OrthographicAdapter(os.path.join(rules_dir, "orthographic"))
    
    logger.info("Initialisation des règles linguistiques")
    ling_adapter = LinguisticAdapter(os.path.join(rules_dir, "linguistic"))
    
    logger.info("Initialisation des entités nommées")
    entity_adapter = NamedEntityAdapter(entities_dir)
    
    # Langues cibles
    target_languages = config['languages']['target']
    
    # S'assurer que les règles par défaut sont créées pour chaque langue
    for lang in target_languages:
        logger.info(f"Initialisation des données pour la langue: {lang}")
        
        # Charger les règles pour s'assurer qu'elles sont créées
        ortho_rules = ortho_adapter.load_rules(lang)
        ling_rules = ling_adapter.load_rules(lang)
        entities = entity_adapter.load_entities(lang)
        
        # Vérifier que les données sont bien chargées
        if ortho_rules:
            logger.info(f"Règles orthographiques chargées pour {lang}")
        else:
            logger.warning(f"Échec du chargement des règles orthographiques pour {lang}")
        
        if ling_rules:
            logger.info(f"Règles linguistiques chargées pour {lang}")
        else:
            logger.warning(f"Échec du chargement des règles linguistiques pour {lang}")
        
        if entities:
            logger.info(f"Entités nommées chargées pour {lang}")
        else:
            logger.warning(f"Échec du chargement des entités nommées pour {lang}")
    
    logger.info("Initialisation des données linguistiques terminée")

def init_common_entities():
    """Initialise les entités communes à toutes les langues"""
    entity_adapter = NamedEntityAdapter()
    
    # Entités communes
    common_entities = {
        "name": "Entités nommées communes",
        "description": "Entités nommées communes aux langues africaines",
        "people": [
            {"original": "Nelson Mandela", "local": "Nelson Mandela"},
            {"original": "Kwame Nkrumah", "local": "Kwame Nkrumah"},
            {"original": "Kofi Annan", "local": "Kofi Annan"},
            {"original": "Wole Soyinka", "local": "Wole Soyinka"},
            {"original": "Chinua Achebe", "local": "Chinua Achebe"},
            {"original": "Patrice Lumumba", "local": "Patrice Lumumba"},
            {"original": "Thomas Sankara", "local": "Thomas Sankara"},
            {"original": "Julius Nyerere", "local": "Julius Nyerere"},
            {"original": "Desmond Tutu", "local": "Desmond Tutu"},
            {"original": "Cheikh Anta Diop", "local": "Cheikh Anta Diop"}
        ],
        "places": [
            {"original": "Africa", "local": "Afrika"},
            {"original": "Sahara", "local": "Sahara"},
            {"original": "Nile River", "local": "Nil"},
            {"original": "Congo River", "local": "Congo"},
            {"original": "Lake Victoria", "local": "Victoria"},
            {"original": "Niger River", "local": "Niger"},
            {"original": "Mount Kilimanjaro", "local": "Kilimanjaro"},
            {"original": "Kalahari Desert", "local": "Kalahari"},
            {"original": "Serengeti", "local": "Serengeti"},
            {"original": "Maghreb", "local": "Maghreb"}
        ],
        "organizations": [
            {"original": "African Union", "local": "Union Africaine"},
            {"original": "ECOWAS", "local": "CEDEAO"},
            {"original": "United Nations", "local": "Nations Unies"},
            {"original": "World Health Organization", "local": "OMS"},
            {"original": "UNESCO", "local": "UNESCO"},
            {"original": "UNICEF", "local": "UNICEF"},
            {"original": "African Development Bank", "local": "BAD"},
            {"original": "European Union", "local": "Union Européenne"},
            {"original": "World Bank", "local": "Banque Mondiale"},
            {"original": "International Criminal Court", "local": "CPI"}
        ],
        "cultural_terms": [
            {"original": "Griot", "local": "Griot"},
            {"original": "Ubuntu", "local": "Ubuntu"},
            {"original": "Adinkra", "local": "Adinkra"},
            {"original": "Kente", "local": "Kente"},
            {"original": "Djembe", "local": "Djembé"},
            {"original": "Kora", "local": "Kora"},
            {"original": "Mancala", "local": "Mancala"},
            {"original": "Shea butter", "local": "Karité"},
            {"original": "Baobab", "local": "Baobab"},
            {"original": "Kola nut", "local": "Kola"}
        ]
    }
    
    # Sauvegarder les entités communes
    entity_adapter.save_entities(common_entities, "common")
    logger.info("Entités communes initialisées")

def main():
    parser = argparse.ArgumentParser(description="Initialisation des données linguistiques")
    parser.add_argument('--config', type=str, default='config.yaml',
                        help="Chemin vers le fichier de configuration")
    parser.add_argument('--only-common', action='store_true',
                        help="Initialiser uniquement les entités communes")
    parser.add_argument('--language', type=str,
                        help="Initialiser les données pour une langue spécifique")
    
    args = parser.parse_args()
    
    if args.only_common:
        init_common_entities()
    elif args.language:
        # Charger la configuration
        config = load_config(args.config)
        
        # Réinitialiser seulement pour la langue spécifiée
        target_languages = [args.language]
        
        # Adapter la configuration temporairement
        temp_config = config.copy()
        temp_config['languages']['target'] = target_languages
        
        # Initialiser les données pour cette langue
        init_all_language_data(temp_config)
    else:
        init_all_language_data(args.config)
    
    logger.info("Initialisation terminée avec succès")

if __name__ == "__main__":
    main()