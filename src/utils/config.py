# src/utils/config.py

import os
import yaml
import argparse
from pathlib import Path

# Chargement automatique du fichier .env si présent
try:
    from dotenv import load_dotenv
    # Chercher .env dans le répertoire racine du projet
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Configuration .env chargée depuis {env_file}")
    else:
        print("ℹ️ Fichier .env non trouvé, utilisation variables système")
except ImportError:
    print("⚠️ python-dotenv non installé, variables .env ignorées")

def load_config(config_file=None):
    """
    Charge la configuration depuis un fichier YAML
    
    Args:
        config_file: Chemin vers le fichier de configuration (optionnel)
    
    Returns:
        Dictionnaire de configuration
    """
    default_config = {
        'extraction': {
            'default_language': 'en',
            'include_html': True,
            'include_wikitext': True
        },
        'segmentation': {
            'max_segment_length': 500,
            'min_segment_length': 20
        },
        'translation': {
            # OpenAI standard
            'openai_api_key': os.environ.get('OPENAI_API_KEY', ''),
            # Azure OpenAI (optionnel)
            'api_key': os.environ.get('AZURE_OPENAI_API_KEY', ''),
            'api_version': os.environ.get('AZURE_OPENAI_API_VERSION', '2024-05-01-preview'),
            'azure_endpoint': os.environ.get('AZURE_OPENAI_ENDPOINT', ''),
            'model': os.environ.get('AZURE_OPENAI_MODEL', 'gpt-4o'),
            # Configuration générale
            'use_glossary': True,
            'max_retries': 3,
            'retry_delay': 2,
            'rate_limit_delay': 0.5
        },
        'languages': {
            'source': ['en', 'fr'],
            'target': ['fon', 'dindi', 'ewe', 'yor']
        },
        'paths': {
            'data_dir': 'data',
            'articles_raw': 'data/articles_raw',
            'articles_cleaned': 'data/articles_cleaned',
            'articles_segmented': 'data/articles_segmented',
            'articles_translated': 'data/articles_translated',
            'glossary_db': 'data/glossaries/glossary.db'
        },
        'database': {
            'url': os.environ.get('DATABASE_URL', 'sqlite:///data/glossaries/glossary.db')
        },
        'cache': {
            'redis_url': os.environ.get('REDIS_URL', 'redis://localhost:6379')
        },
        'development': {
            'debug': os.environ.get('DEBUG', 'false').lower() == 'true',
            'log_level': os.environ.get('LOG_LEVEL', 'INFO')
        },
        # Variables d'environnement pour compatibilité
        'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY', ''),
        'DATABASE_URL': os.environ.get('DATABASE_URL', ''),
        'DEBUG': os.environ.get('DEBUG', 'false').lower() == 'true'
    }
    
    if not config_file:
        return default_config
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Fusionner avec les valeurs par défaut
        config = merge_configs(default_config, config)
        return config
    except Exception as e:
        print(f"Erreur lors du chargement de la configuration: {e}")
        return default_config

def merge_configs(default_config, user_config):
    """
    Fusionne les configurations par défaut et utilisateur
    
    Args:
        default_config: Configuration par défaut
        user_config: Configuration utilisateur
    
    Returns:
        Configuration fusionnée
    """
    merged = default_config.copy()
    
    for section, values in user_config.items():
        if section in merged and isinstance(merged[section], dict) and isinstance(values, dict):
            merged[section].update(values)
        else:
            merged[section] = values
    
    return merged

def save_config(config, output_file):
    """
    Sauvegarde la configuration dans un fichier YAML
    
    Args:
        config: Configuration à sauvegarder
        output_file: Chemin du fichier de sortie
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        print(f"Configuration sauvegardée dans {output_file}")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de la configuration: {e}")

def create_config_file(output_file='config.yaml'):
    """
    Crée un fichier de configuration par défaut
    
    Args:
        output_file: Chemin du fichier de sortie
    """
    config = load_config()
    save_config(config, output_file)

def main():
    parser = argparse.ArgumentParser(description="Gestionnaire de configuration")
    parser.add_argument('--create', action='store_true', 
                        help="Créer un fichier de configuration par défaut")
    parser.add_argument('--output', type=str, default='config.yaml', 
                        help="Chemin du fichier de configuration de sortie")
    
    args = parser.parse_args()
    
    if args.create:
        create_config_file(args.output)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()