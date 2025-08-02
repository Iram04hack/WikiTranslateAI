# src/database/insert_glossary.py

import argparse
import json
import os
from pathlib import Path
from .glossary_manager import GlossaryManager

def insert_initial_glossary(db_path, json_files_dir):
    """Insère les glossaires initiaux depuis les fichiers JSON"""
    with GlossaryManager(db_path) as gm:
        total_imported = 0
        for lang in ['fon', 'dindi', 'ewe', 'yor']:
            # Pour chaque langue cible, chercher des fichiers de glossaire
            for source_lang in ['en', 'fr']:
                json_file = os.path.join(json_files_dir, f"{source_lang}_{lang}_glossary.json")
                if os.path.exists(json_file):
                    count = gm.batch_import(json_file)
                    print(f"Importé {count} termes depuis {json_file}")
                    total_imported += count
        
        return total_imported

def create_sample_glossary(output_dir):
    """Crée un exemple de fichier de glossaire"""
    sample_glossary = [
        {
            "source_term": "computer",
            "source_lang": "en",
            "target_term": "ordinatɛ",
            "target_lang": "fon",
            "domain": "tech",
            "context": "A computer is an electronic device that manipulates information.",
            "confidence": 0.9,
            "validated": True,
            "variants": [
                {"term": "computing", "is_source": True},
                {"term": "ordinatɛ lɛ", "is_source": False}
            ]
        },
        {
            "source_term": "democracy",
            "source_lang": "en",
            "target_term": "togbihɛn",
            "target_lang": "fon",
            "domain": "politics",
            "context": "Democracy is a system of government by the whole population.",
            "confidence": 0.8,
            "validated": True
        }
    ]
    
    # Créer le répertoire s'il n'existe pas
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Sauvegarder l'exemple
    output_file = os.path.join(output_dir, "en_fon_glossary.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sample_glossary, f, ensure_ascii=False, indent=2)
    
    print(f"Exemple de glossaire créé: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Gestionnaire de glossaire")
    parser.add_argument('--db', type=str, required=True, help="Chemin vers la base de données SQLite")
    parser.add_argument('--input-dir', type=str, help="Répertoire contenant les fichiers de glossaire JSON")
    parser.add_argument('--create-sample', action='store_true', help="Créer un exemple de fichier de glossaire")
    parser.add_argument('--output-dir', type=str, help="Répertoire pour les fichiers de sortie")
    
    args = parser.parse_args()
    
    if args.create_sample:
        output_dir = args.output_dir or 'data/glossaries'
        create_sample_glossary(output_dir)
    
    if args.input_dir:
        count = insert_initial_glossary(args.db, args.input_dir)
        print(f"Total de {count} termes importés dans le glossaire.")

if __name__ == "__main__":
    main()