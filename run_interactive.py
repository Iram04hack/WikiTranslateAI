#!/usr/bin/env python3
# run_interactive.py
# Script interactif pour WikiTranslateAI

import os
import sys
import time
import json
import argparse
import logging
import subprocess
from pathlib import Path

os.makedirs("data/corpus", exist_ok=True)
os.makedirs("data/terminology", exist_ok=True)

# Vérifier et installer les dépendances
try:
    from colorama import init, Fore, Style
except ImportError:
    print("Installation des dépendances manquantes...")
    subprocess.call([sys.executable, "-m", "pip", "install", "colorama"])
    from colorama import init, Fore, Style

# Initialiser colorama pour les couleurs de terminal
init()

# Ajouter le répertoire parent au chemin de recherche
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Créer les répertoires nécessaires
os.makedirs("data/temp", exist_ok=True)
os.makedirs("data/glossaries", exist_ok=True)
os.makedirs("data/evaluations", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Importer les modules du projet
try:
    from src.utils.config import load_config, save_config
except ImportError:
    print(f"{Fore.RED}Erreur: Module de configuration non trouvé{Style.RESET_ALL}")
    sys.exit(1)

def clear_screen():
    """Nettoie l'écran du terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Affiche l'en-tête de l'application."""
    clear_screen()
    header = f"""
{Fore.CYAN}╔═════════════════════════════════════════════════════════════════════╗
║                                                                     ║
║  {Fore.YELLOW}██╗    ██╗██╗██╗  ██╗██╗████████╗██████╗  █████╗ ███╗   ██╗███████╗{Fore.CYAN}  ║
║  {Fore.YELLOW}██║    ██║██║██║ ██╔╝██║╚══██╔══╝██╔══██╗██╔══██╗████╗  ██║██╔════╝{Fore.CYAN}  ║
║  {Fore.YELLOW}██║ █╗ ██║██║█████╔╝ ██║   ██║   ██████╔╝███████║██╔██╗ ██║███████╗{Fore.CYAN}  ║
║  {Fore.YELLOW}██║███╗██║██║██╔═██╗ ██║   ██║   ██╔══██╗██╔══██║██║╚██╗██║╚════██║{Fore.CYAN}  ║
║  {Fore.YELLOW}╚███╔███╔╝██║██║  ██╗██║   ██║   ██║  ██║██║  ██║██║ ╚████║███████║{Fore.CYAN}  ║
║  {Fore.YELLOW} ╚══╝╚══╝ ╚═╝╚═╝  ╚═╝╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝{Fore.CYAN}  ║
║                                                                     ║
║                     {Fore.GREEN}A I   T R A D U C T I O N{Fore.CYAN}                          ║
║                                                                     ║
╚═════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

Traduction d'articles Wikipedia vers les langues africaines
"""
    print(header)

def print_menu(title, options):
    """
    Affiche un menu avec des options numérotées.
    
    Args:
        title: Titre du menu
        options: Liste de chaînes pour les options de menu
    
    Returns:
        Choix de l'utilisateur
    """
    print(f"\n{Fore.CYAN}══ {title} ══{Style.RESET_ALL}\n")
    
    for i, option in enumerate(options, 1):
        print(f"  {Fore.GREEN}{i}{Style.RESET_ALL}. {option}")
    
    print(f"\n  {Fore.RED}0{Style.RESET_ALL}. Retour/Quitter")
    
    return input(f"\n{Fore.YELLOW}Votre choix: {Style.RESET_ALL}")

def get_user_input(prompt, default=None):
    """
    Demande une entrée utilisateur avec valeur par défaut optionnelle.
    
    Args:
        prompt: Message à afficher
        default: Valeur par défaut (optionnelle)
    
    Returns:
        Entrée utilisateur ou valeur par défaut
    """
    if default:
        user_input = input(f"{Fore.YELLOW}{prompt} [{default}]: {Style.RESET_ALL}")
        return user_input if user_input else default
    else:
        return input(f"{Fore.YELLOW}{prompt}: {Style.RESET_ALL}")

def execute_command(command):
    """
    Exécute une commande shell et affiche la sortie.
    
    Args:
        command: Commande à exécuter (chaîne ou liste)
    """
    print(f"\n{Fore.CYAN}Exécution de la commande: {Style.RESET_ALL}{' '.join(command) if isinstance(command, list) else command}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    try:
        if isinstance(command, list):
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        else:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # Afficher la sortie en temps réel
        for line in iter(process.stdout.readline, ''):
            print(line, end='')
        
        process.wait()
        
        if process.returncode != 0:
            print(f"\n{Fore.RED}La commande a échoué avec le code de retour {process.returncode}{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.GREEN}Commande exécutée avec succès{Style.RESET_ALL}")
    
    except Exception as e:
        print(f"\n{Fore.RED}Erreur lors de l'exécution de la commande: {e}{Style.RESET_ALL}")
    
    input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")

def extract_translate_article(config):
    """Menu pour extraire et traduire un article spécifique."""
    print_header()
    
    article_title = get_user_input("Titre de l'article Wikipedia")
    
    if not article_title:
        print(f"{Fore.RED}Titre d'article requis{Style.RESET_ALL}")
        time.sleep(1)
        return
    
    # Options de langues
    source_languages = config['languages']['source']
    target_languages = config['languages']['target']
    
    print(f"\n{Fore.CYAN}Langues source disponibles:{Style.RESET_ALL}")
    for i, lang in enumerate(source_languages, 1):
        print(f"  {i}. {lang}")
    
    source_idx = int(get_user_input("Choisissez la langue source (numéro)", "1")) - 1
    if source_idx < 0 or source_idx >= len(source_languages):
        source_idx = 0
    
    source_lang = source_languages[source_idx]
    
    print(f"\n{Fore.CYAN}Langues cibles disponibles:{Style.RESET_ALL}")
    for i, lang in enumerate(target_languages, 1):
        print(f"  {i}. {lang}")
    
    target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
    if target_idx < 0 or target_idx >= len(target_languages):
        target_idx = 0
    
    target_lang = target_languages[target_idx]
    
    # Options d'étapes
    steps = ["extract", "clean", "segment", "translate"]
    selected_steps = []
    
    print(f"\n{Fore.CYAN}Étapes du pipeline:{Style.RESET_ALL}")
    print("  1. Extraction depuis Wikipedia")
    print("  2. Nettoyage du texte")
    print("  3. Segmentation")
    print("  4. Traduction")
    print(f"\n  5. Toutes les étapes")
    
    steps_choice = get_user_input("Choisissez les étapes à exécuter (ex: 1,2,3 ou 5 pour toutes)", "5")
    
    if "5" in steps_choice:
        selected_steps = steps
    else:
        steps_nums = [int(s.strip()) for s in steps_choice.split(",") if s.strip().isdigit()]
        for num in steps_nums:
            if 1 <= num <= 4:
                selected_steps.append(steps[num-1])
    
    # Confirmation
    print(f"\n{Fore.CYAN}Récapitulatif:{Style.RESET_ALL}")
    print(f"  Article: {article_title}")
    print(f"  De: {source_lang} vers: {target_lang}")
    print(f"  Étapes: {', '.join(selected_steps)}")
    
    confirm = get_user_input("Confirmer (o/n)", "o")
    
    if confirm.lower() in ["o", "oui", "y", "yes"]:
        # Construire et exécuter la commande
        cmd = [
            "python3", "main.py",
            "--title", article_title,
            "--source-lang", source_lang,
            "--target-lang", target_lang
        ]
        
        if selected_steps and selected_steps != steps:
            cmd.extend(["--steps"] + selected_steps)
        
        execute_command(cmd)

def search_translate_articles(config):
    """Menu pour rechercher et traduire des articles."""
    print_header()
    
    search_term = get_user_input("Terme de recherche Wikipedia")
    
    if not search_term:
        print(f"{Fore.RED}Terme de recherche requis{Style.RESET_ALL}")
        time.sleep(1)
        return
    
    # Nombre d'articles
    count = get_user_input("Nombre d'articles à traiter", "3")
    
    # Options de langues
    source_languages = config['languages']['source']
    target_languages = config['languages']['target']
    
    print(f"\n{Fore.CYAN}Langues source disponibles:{Style.RESET_ALL}")
    for i, lang in enumerate(source_languages, 1):
        print(f"  {i}. {lang}")
    
    source_idx = int(get_user_input("Choisissez la langue source (numéro)", "1")) - 1
    if source_idx < 0 or source_idx >= len(source_languages):
        source_idx = 0
    
    source_lang = source_languages[source_idx]
    
    print(f"\n{Fore.CYAN}Langues cibles disponibles:{Style.RESET_ALL}")
    for i, lang in enumerate(target_languages, 1):
        print(f"  {i}. {lang}")
    
    target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
    if target_idx < 0 or target_idx >= len(target_languages):
        target_idx = 0
    
    target_lang = target_languages[target_idx]
    
    # Confirmation
    print(f"\n{Fore.CYAN}Récapitulatif:{Style.RESET_ALL}")
    print(f"  Recherche: {search_term}")
    print(f"  Nombre d'articles: {count}")
    print(f"  De: {source_lang} vers: {target_lang}")
    
    confirm = get_user_input("Confirmer (o/n)", "o")
    
    if confirm.lower() in ["o", "oui", "y", "yes"]:
        # Construire et exécuter la commande
        cmd = [
            "python3", "main.py",
            "--search", search_term,
            "--count", count,
            "--source-lang", source_lang,
            "--target-lang", target_lang
        ]
        
        execute_command(cmd)

def random_translate_articles(config):
    """Menu pour extraire et traduire des articles aléatoires."""
    print_header()
    
    # Nombre d'articles
    count = get_user_input("Nombre d'articles aléatoires à traiter", "3")
    
    # Options de langues
    source_languages = config['languages']['source']
    target_languages = config['languages']['target']
    
    print(f"\n{Fore.CYAN}Langues source disponibles:{Style.RESET_ALL}")
    for i, lang in enumerate(source_languages, 1):
        print(f"  {i}. {lang}")
    
    source_idx = int(get_user_input("Choisissez la langue source (numéro)", "1")) - 1
    if source_idx < 0 or source_idx >= len(source_languages):
        source_idx = 0
    
    source_lang = source_languages[source_idx]
    
    print(f"\n{Fore.CYAN}Langues cibles disponibles:{Style.RESET_ALL}")
    for i, lang in enumerate(target_languages, 1):
        print(f"  {i}. {lang}")
    
    target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
    if target_idx < 0 or target_idx >= len(target_languages):
        target_idx = 0
    
    target_lang = target_languages[target_idx]
    
    # Confirmation
    print(f"\n{Fore.CYAN}Récapitulatif:{Style.RESET_ALL}")
    print(f"  Nombre d'articles aléatoires: {count}")
    print(f"  De: {source_lang} vers: {target_lang}")
    
    confirm = get_user_input("Confirmer (o/n)", "o")
    
    if confirm.lower() in ["o", "oui", "y", "yes"]:
        # Construire et exécuter la commande
        cmd = [
            "python3", "main.py",
            "--random",
            "--count", count,
            "--source-lang", source_lang,
            "--target-lang", target_lang
        ]
        
        execute_command(cmd)

def manage_glossary(config):
    """Menu pour gérer le glossaire."""
    while True:
        print_header()
        
        choice = print_menu("Gestion du Glossaire", [
            "Consulter le glossaire",
            "Importer un glossaire",
            "Exporter le glossaire",
            "Créer un exemple de glossaire"
        ])
        
        if choice == "0":
            break
        elif choice == "1":
            # Consulter le glossaire
            glossary_db = config['paths']['glossary_db']
            
            # Options de langues
            source_languages = config['languages']['source']
            target_languages = config['languages']['target']
            
            print(f"\n{Fore.CYAN}Langue source:{Style.RESET_ALL}")
            for i, lang in enumerate(source_languages, 1):
                print(f"  {i}. {lang}")
            
            source_idx = int(get_user_input("Choisissez la langue source (numéro)", "1")) - 1
            if source_idx < 0 or source_idx >= len(source_languages):
                source_idx = 0
            
            source_lang = source_languages[source_idx]
            
            print(f"\n{Fore.CYAN}Langue cible:{Style.RESET_ALL}")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
            if target_idx < 0 or target_idx >= len(target_languages):
                target_idx = 0
            
            target_lang = target_languages[target_idx]
            
            output_file = f"glossary_{source_lang}_{target_lang}.json"
            output_path = os.path.join("data", "temp", output_file)
            
            # Exécuter la commande pour exporter le glossaire
            try:
                cmd = [
                    "python3", "-c", 
                    f"from src.database.glossary_manager import GlossaryManager; gm = GlossaryManager('{glossary_db}'); gm.export_glossary('{output_path}', '{source_lang}', '{target_lang}'); gm.__exit__(None, None, None)"
                ]
                
                # Créer le répertoire si nécessaire
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                execute_command(cmd)
                
                # Afficher le contenu du glossaire
                if os.path.exists(output_path):
                    import json
                    try:
                        with open(output_path, 'r', encoding='utf-8') as f:
                            glossary_data = json.load(f)
                        
                        print(f"\n{Fore.CYAN}Glossaire {source_lang} → {target_lang}:{Style.RESET_ALL}")
                        print(f"  Nombre d'entrées: {len(glossary_data)}")
                        
                        if glossary_data:
                            print("\n  Quelques entrées:")
                            for i, entry in enumerate(glossary_data[:10], 1):
                                confidence = entry.get('confidence_score', 0)
                                validated = "✓" if entry.get('validated', False) else " "
                                print(f"  {i}. {entry['source_term']} → {entry['target_term']} [{confidence:.1f}] [{validated}]")
                            
                            if len(glossary_data) > 10:
                                print(f"  ... et {len(glossary_data) - 10} autres entrées")
                    except Exception as e:
                        print(f"\n{Fore.RED}Erreur lors de la lecture du glossaire: {e}{Style.RESET_ALL}")
                
                input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
            except Exception as e:
                print(f"\n{Fore.RED}Erreur: {e}{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
        
        elif choice == "2":
            # Importer un glossaire
            try:
                print(f"\n{Fore.CYAN}Import de glossaire{Style.RESET_ALL}")
                
                glossary_path = get_user_input("Chemin du fichier de glossaire (JSON ou CSV)")
                
                if not os.path.exists(glossary_path):
                    print(f"{Fore.RED}Fichier introuvable: {glossary_path}{Style.RESET_ALL}")
                    time.sleep(1.5)
                    continue
                
                # Options de langues
                source_languages = config['languages']['source']
                target_languages = config['languages']['target']
                
                print(f"\n{Fore.CYAN}Langue source:{Style.RESET_ALL}")
                for i, lang in enumerate(source_languages, 1):
                    print(f"  {i}. {lang}")
                
                source_idx = int(get_user_input("Choisissez la langue source (numéro)", "1")) - 1
                if source_idx < 0 or source_idx >= len(source_languages):
                    source_idx = 0
                
                source_lang = source_languages[source_idx]
                
                print(f"\n{Fore.CYAN}Langue cible:{Style.RESET_ALL}")
                for i, lang in enumerate(target_languages, 1):
                    print(f"  {i}. {lang}")
                
                target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
                if target_idx < 0 or target_idx >= len(target_languages):
                    target_idx = 0
                
                target_lang = target_languages[target_idx]
                
                confidence = get_user_input("Niveau de confiance (0.0-1.0)", "0.8")
                validated = get_user_input("Marquer comme validé (o/n)", "n").lower() in ["o", "oui", "y", "yes"]
                
                # Exécuter la commande pour importer le glossaire
                glossary_db = config['paths']['glossary_db']
                
                cmd = [
                    "python3", "-c", 
                    f"from src.database.glossary_learner import GlossaryLearner; "
                    f"gl = GlossaryLearner('{glossary_db}'); "
                    f"count = gl.import_external_glossary('{glossary_path}', '{source_lang}', '{target_lang}', {confidence}, {validated}); "
                    f"print(f'Importé {{count}} termes')"
                ]
                
                execute_command(cmd)
            except Exception as e:
                print(f"\n{Fore.RED}Erreur: {e}{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
        
        elif choice == "3":
            # Exporter le glossaire
            try:
                print(f"\n{Fore.CYAN}Export de glossaire{Style.RESET_ALL}")
                
                # Options de langues
                source_languages = config['languages']['source']
                target_languages = config['languages']['target']
                
                print(f"\n{Fore.CYAN}Langue source (laisser vide pour toutes):{Style.RESET_ALL}")
                print("  0. Toutes les langues")
                for i, lang in enumerate(source_languages, 1):
                    print(f"  {i}. {lang}")
                
                source_idx = int(get_user_input("Choisissez la langue source (numéro)", "0"))
                source_lang = None if source_idx == 0 else source_languages[source_idx-1] if 0 < source_idx <= len(source_languages) else None
                
                print(f"\n{Fore.CYAN}Langue cible (laisser vide pour toutes):{Style.RESET_ALL}")
                print("  0. Toutes les langues")
                for i, lang in enumerate(target_languages, 1):
                    print(f"  {i}. {lang}")
                
                target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "0"))
                target_lang = None if target_idx == 0 else target_languages[target_idx-1] if 0 < target_idx <= len(target_languages) else None
                
                output_file = get_user_input("Nom du fichier de sortie", "glossary_export.json")
                output_path = os.path.join("data", "glossaries", output_file)
                
                # Exécuter la commande pour exporter le glossaire
                glossary_db = config['paths']['glossary_db']
                
                source_param = f"'{source_lang}'" if source_lang else "None"
                target_param = f"'{target_lang}'" if target_lang else "None"
                
                cmd = [
                    "python3", "-c", 
                    f"from src.database.glossary_manager import GlossaryManager; "
                    f"with GlossaryManager('{glossary_db}') as gm: "
                    f"count = gm.export_glossary('{output_path}', {source_param}, {target_param}); "
                    f"print(f'Exporté {{count}} termes vers {{output_path}}')"
                ]
                
                # Créer le répertoire si nécessaire
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                execute_command(cmd)
            except Exception as e:
                print(f"\n{Fore.RED}Erreur: {e}{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
        
        elif choice == "4":
            # Créer un exemple de glossaire
            try:
                output_dir = os.path.join("data", "glossaries")
                
                # Options de langues
                source_languages = config['languages']['source']
                target_languages = config['languages']['target']
                
                print(f"\n{Fore.CYAN}Langue source:{Style.RESET_ALL}")
                for i, lang in enumerate(source_languages, 1):
                    print(f"  {i}. {lang}")
                
                source_idx = int(get_user_input("Choisissez la langue source (numéro)", "1")) - 1
                if source_idx < 0 or source_idx >= len(source_languages):
                    source_idx = 0
                
                source_lang = source_languages[source_idx]
                
                print(f"\n{Fore.CYAN}Langue cible:{Style.RESET_ALL}")
                for i, lang in enumerate(target_languages, 1):
                    print(f"  {i}. {lang}")
                
                target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
                if target_idx < 0 or target_idx >= len(target_languages):
                    target_idx = 0
                
                target_lang = target_languages[target_idx]
                
                # Exécuter la commande pour créer un exemple de glossaire
                cmd = [
                    "python3", "-m", "src.database.insert_glossary",
                    "--create-sample",
                    "--output-dir", output_dir
                ]
                
                # Créer le répertoire si nécessaire
                os.makedirs(output_dir, exist_ok=True)
                
                execute_command(cmd)
            except Exception as e:
                print(f"\n{Fore.RED}Erreur: {e}{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")

def evaluate_translations(config):
    """Menu pour évaluer les traductions existantes."""
    print_header()
    
    # Vérifier si le module d'évaluation est disponible
    try:
        from src.evaluation.evaluate_translation import evaluate_article
        evaluation_available = True
    except ImportError:
        print(f"{Fore.RED}Le module d'évaluation n'est pas encore implémenté.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Cette fonctionnalité sera disponible prochainement.{Style.RESET_ALL}")
        evaluation_available = False
        time.sleep(2)
        return
    
    if evaluation_available:
        try:
            # Liste des articles traduits
            translated_dir = config['paths']['articles_translated']
            
            # Vérifier si le répertoire existe
            if not os.path.exists(translated_dir):
                print(f"{Fore.RED}Répertoire des traductions non trouvé: {translated_dir}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Veuillez d'abord traduire quelques articles.{Style.RESET_ALL}")
                time.sleep(2)
                return
            
            # Trouver les langues cibles disponibles
            available_langs = []
            for item in os.listdir(translated_dir):
                if os.path.isdir(os.path.join(translated_dir, item)) and not item.endswith("_txt"):
                    available_langs.append(item)
            
            if not available_langs:
                print(f"{Fore.RED}Aucun article traduit trouvé.{Style.RESET_ALL}")
                time.sleep(2)
                return
            
            print(f"\n{Fore.CYAN}Langues disponibles pour l'évaluation:{Style.RESET_ALL}")
            for i, lang in enumerate(available_langs, 1):
                print(f"  {i}. {lang}")
            
            lang_idx = int(get_user_input("Choisissez la langue à évaluer (numéro)", "1")) - 1
            if lang_idx < 0 or lang_idx >= len(available_langs):
                lang_idx = 0
            
            target_lang = available_langs[lang_idx]
            target_dir = os.path.join(translated_dir, target_lang)
            
            # Liste des articles disponibles
            articles = [f for f in os.listdir(target_dir) if f.endswith('.json')]
            
            if not articles:
                print(f"{Fore.RED}Aucun article traduit trouvé pour la langue {target_lang}.{Style.RESET_ALL}")
                time.sleep(2)
                return
            
            print(f"\n{Fore.CYAN}Articles disponibles pour l'évaluation:{Style.RESET_ALL}")
            for i, article in enumerate(articles, 1):
                print(f"  {i}. {article.replace('.json', '')}")
            
            article_idx = int(get_user_input("Choisissez l'article à évaluer (numéro)", "1")) - 1
            if article_idx < 0 or article_idx >= len(articles):
                article_idx = 0
            
            article_file = articles[article_idx]
            article_path = os.path.join(target_dir, article_file)
            
            # Options d'évaluation
            print(f"\n{Fore.CYAN}Métriques d'évaluation:{Style.RESET_ALL}")
            print("  1. BLEU (BiLingual Evaluation Understudy)")
            print("  2. METEOR (Metric for Evaluation of Translation with Explicit Ordering)")
            print("  3. Toutes les métriques")
            
            metrics_choice = get_user_input("Choisissez les métriques à utiliser (ex: 1,2 ou 3 pour toutes)", "3")
            
            metrics = []
            if "3" in metrics_choice:
                metrics = ["bleu", "meteor"]
            else:
                if "1" in metrics_choice:
                    metrics.append("bleu")
                if "2" in metrics_choice:
                    metrics.append("meteor")
            
            # Exécuter l'évaluation
            print(f"\n{Fore.CYAN}Évaluation de l'article {article_file.replace('.json', '')} en {target_lang}...{Style.RESET_ALL}")
            
            try:
                output_file = f"evaluation_{article_file.replace('.json', '')}.json"
                output_path = os.path.join("data", "evaluations", output_file)
                
                # Créer le répertoire si nécessaire
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Exécuter la commande pour évaluer l'article
                cmd = [
                    "python3", "-m", "src.evaluation.evaluate_translation",
                    "--input", article_path,
                    "--output", output_path,
                    "--metrics", ",".join(metrics)
                ]
                
                execute_command(cmd)
                
                # Afficher les résultats
                if os.path.exists(output_path):
                    with open(output_path, 'r', encoding='utf-8') as f:
                        results = json.load(f)
                    
                    print(f"\n{Fore.CYAN}Résultats de l'évaluation:{Style.RESET_ALL}")
                    for metric, score in results.get('scores', {}).items():
                        print(f"  {metric.upper()}: {score:.4f}")
                
            except Exception as e:
                print(f"\n{Fore.RED}Erreur lors de l'évaluation: {e}{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
        except Exception as e:
            print(f"\n{Fore.RED}Erreur générale: {e}{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")

def view_statistics(config):
    """Menu pour visualiser les statistiques du projet."""
    print_header()
    
    print(f"\n{Fore.CYAN}Statistiques du projet:{Style.RESET_ALL}\n")
    
    try:
        # Statistiques des articles
        raw_dir = config['paths']['articles_raw']
        cleaned_dir = config['paths']['articles_cleaned']
        segmented_dir = config['paths']['articles_segmented']
        translated_dir = config['paths']['articles_translated']
        
        # Nombre d'articles à chaque étape
        raw_count = 0
        if os.path.exists(raw_dir):
            for lang in os.listdir(raw_dir):
                lang_dir = os.path.join(raw_dir, lang)
                if os.path.isdir(lang_dir):
                    raw_count += len(os.listdir(lang_dir))
        
        cleaned_count = len(os.listdir(cleaned_dir)) if os.path.exists(cleaned_dir) else 0
        segmented_count = len(os.listdir(segmented_dir)) if os.path.exists(segmented_dir) else 0
        
        translated_langs = {}
        if os.path.exists(translated_dir):
            for lang in os.listdir(translated_dir):
                lang_dir = os.path.join(translated_dir, lang)
                if os.path.isdir(lang_dir) and not lang.endswith('_txt'):
                    translated_langs[lang] = len(os.listdir(lang_dir))
        
        # Afficher les statistiques
        print(f"  {Fore.GREEN}Articles extraits:{Style.RESET_ALL} {raw_count}")
        print(f"  {Fore.GREEN}Articles nettoyés:{Style.RESET_ALL} {cleaned_count}")
        print(f"  {Fore.GREEN}Articles segmentés:{Style.RESET_ALL} {segmented_count}")
        
        print(f"\n  {Fore.GREEN}Articles traduits par langue:{Style.RESET_ALL}")
        for lang, count in translated_langs.items():
            print(f"    - {lang}: {count}")
        
        # Statistiques du glossaire
        glossary_db = config['paths']['glossary_db']
        if os.path.exists(glossary_db):
            try:
                from src.database.glossary_manager import GlossaryManager
                
                print(f"\n  {Fore.GREEN}Statistiques du glossaire:{Style.RESET_ALL}")
                
                with GlossaryManager(glossary_db) as gm:
                    # Compte total des termes
                    gm.cursor.execute("SELECT COUNT(*) FROM glossary_entries")
                    total_terms = gm.cursor.fetchone()[0]
                    
                    # Termes par paire de langues
                    gm.cursor.execute("""
                        SELECT l1.code as source, l2.code as target, COUNT(*) as count
                        FROM glossary_entries ge
                        JOIN languages l1 ON ge.source_language_id = l1.id
                        JOIN languages l2 ON ge.target_language_id = l2.id
                        GROUP BY l1.code, l2.code
                    """)
                    lang_pairs = gm.cursor.fetchall()
                    
                    # Termes validés vs non validés
                    gm.cursor.execute("SELECT COUNT(*) FROM glossary_entries WHERE validated = 1")
                    validated_terms = gm.cursor.fetchone()[0]
                
                print(f"    - Total des termes: {total_terms}")
                if total_terms > 0:
                    print(f"    - Termes validés: {validated_terms} ({validated_terms/total_terms*100:.1f}%)")
                
                print(f"    - Paires de langues:")
                for pair in lang_pairs:
                    print(f"      * {pair['source']} → {pair['target']}: {pair['count']}")
            
            except Exception as e:
                print(f"    {Fore.RED}Erreur lors de l'accès au glossaire: {e}{Style.RESET_ALL}")
        
        # Statistiques de progression globale Wikipedia
        try:
            print(f"\n  {Fore.GREEN}Statistiques de couverture Wikipedia:{Style.RESET_ALL}")
            
            # Tenter d'obtenir le nombre total d'articles pour les langues source
            source_langs = config['languages']['source']
            target_langs = config['languages']['target']
            
            # Utiliser l'API MediaWiki pour obtenir les statistiques
            try:
                from src.extraction.api_client import MediaWikiClient
                
                wiki_stats = {}
                for lang in source_langs:
                    try:
                        client = MediaWikiClient().set_language(lang)
                        response = client._make_request({
                            'action': 'query',
                            'meta': 'siteinfo',
                            'siprop': 'statistics'
                        })
                        
                        if 'query' in response and 'statistics' in response['query']:
                            wiki_stats[lang] = response['query']['statistics'].get('articles', 0)
                    except Exception as e:
                        print(f"    {Fore.RED}Erreur lors de la récupération des statistiques pour {lang}: {e}{Style.RESET_ALL}")
                
                # Afficher les statistiques de couverture
                for lang, total in wiki_stats.items():
                    print(f"    - Total d'articles Wikipedia en {lang}: {total:,}")
                    
                    for target_lang in target_langs:
                        translated = translated_langs.get(target_lang, 0)
                        if total > 0:
                            coverage = (translated / total) * 100
                            print(f"      * Couverture en {target_lang}: {translated:,}/{total:,} ({coverage:.5f}%)")
            except ImportError:
                print(f"    {Fore.YELLOW}Module API non disponible, impossible de récupérer les statistiques Wikipedia.{Style.RESET_ALL}")
        
        except Exception as e:
            print(f"    {Fore.RED}Erreur lors du calcul des statistiques de couverture: {e}{Style.RESET_ALL}")
        
        # Historique des traductions
        try:
            # Vérifier si le fichier d'historique existe
            history_file = os.path.join("data", "translation_history.json")
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                
                print(f"\n  {Fore.GREEN}Historique des traductions:{Style.RESET_ALL}")
                print(f"    - Début du projet: {history.get('project_start', 'Inconnu')}")
                print(f"    - Dernière traduction: {history.get('last_translation', 'Inconnue')}")
                
                # Statistiques de progression par jour
                if 'daily_progress' in history:
                    print(f"    - Progression quotidienne (5 derniers jours):")
                    
                    # Trier et prendre les 5 derniers jours
                    daily_progress = sorted(history['daily_progress'].items(), reverse=True)[:5]
                    
                    for date, stats in daily_progress:
                        total_day = sum(stats.values())
                        print(f"      * {date}: {total_day} articles")
                        for lang, count in stats.items():
                            print(f"        - {lang}: {count}")
        except Exception as e:
            print(f"    {Fore.RED}Erreur lors de la lecture de l'historique: {e}{Style.RESET_ALL}")
    
    except Exception as e:
        print(f"\n{Fore.RED}Erreur lors de l'affichage des statistiques: {e}{Style.RESET_ALL}")
    
    input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")

def batch_processing_menu(config):
    """Menu pour le traitement par lots à grande échelle."""
    print_header()
    
    # Vérifier si le script de traitement par lots existe
    batch_script = os.path.join("scripts", "batch_processor.py")
    if not os.path.exists(batch_script):
        print(f"{Fore.RED}Script de traitement par lots non trouvé: {batch_script}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Cette fonctionnalité sera disponible prochainement.{Style.RESET_ALL}")
        time.sleep(2)
        return
    
    choice = print_menu("Traitement par Lots", [
        "Traiter par catégories",
        "Traiter les articles les plus consultés",
        "Traiter les articles non traduits",
        "Importer une liste d'articles",
        "Reprendre un traitement interrompu"
    ])
    
    try:
        if choice == "0":
            return
        elif choice == "1":
            # Traitement par catégories
            category = get_user_input("Catégorie à traiter (ex: science, history, geography)")
            count = int(get_user_input("Nombre d'articles à traiter", "50"))
            
            # Options de langues
            source_languages = config['languages']['source']
            target_languages = config['languages']['target']
            
            print(f"\n{Fore.CYAN}Langue source:{Style.RESET_ALL}")
            for i, lang in enumerate(source_languages, 1):
                print(f"  {i}. {lang}")
            
            source_idx = int(get_user_input("Choisissez la langue source (numéro)", "1")) - 1
            if source_idx < 0 or source_idx >= len(source_languages):
                source_idx = 0
            
            source_lang = source_languages[source_idx]
            
            print(f"\n{Fore.CYAN}Langue cible:{Style.RESET_ALL}")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
            if target_idx < 0 or target_idx >= len(target_languages):
                target_idx = 0
            
            target_lang = target_languages[target_idx]
            
            print(f"\n{Fore.CYAN}Mode de traitement:{Style.RESET_ALL}")
            print("  1. Séquentiel (un par un)")
            print("  2. Parallèle (plusieurs en même temps)")
            
            mode = get_user_input("Choisissez le mode de traitement (1-2)", "1")
            parallel = mode == "2"
            
            # Confirmation
            print(f"\n{Fore.CYAN}Récapitulatif:{Style.RESET_ALL}")
            print(f"  Catégorie: {category}")
            print(f"  Nombre d'articles: {count}")
            print(f"  De: {source_lang} vers: {target_lang}")
            print(f"  Mode: {'Parallèle' if parallel else 'Séquentiel'}")
            
            confirm = get_user_input("Confirmer (o/n)", "o")
            
            if confirm.lower() in ["o", "oui", "y", "yes"]:
                # Exécuter le traitement par lots
                if parallel:
                    workers = int(get_user_input("Nombre de workers parallèles", "4"))
                    cmd = [
                        "python3", "scripts/batch_processor.py",
                        "--category", category,
                        "--count", str(count),
                        "--source-lang", source_lang,
                        "--target-lang", target_lang,
                        "--parallel",
                        "--workers", str(workers)
                    ]
                else:
                    cmd = [
                        "python3", "scripts/batch_processor.py",
                        "--category", category,
                        "--count", str(count),
                        "--source-lang", source_lang,
                        "--target-lang", target_lang
                    ]
                
                execute_command(cmd)
        
        elif choice == "2":
            # Traiter les articles les plus consultés
            count = int(get_user_input("Nombre d'articles populaires à traiter", "50"))
            
            # Options de langues
            source_languages = config['languages']['source']
            target_languages = config['languages']['target']
            
            print(f"\n{Fore.CYAN}Langue source:{Style.RESET_ALL}")
            for i, lang in enumerate(source_languages, 1):
                print(f"  {i}. {lang}")
            
            source_idx = int(get_user_input("Choisissez la langue source (numéro)", "1")) - 1
            if source_idx < 0 or source_idx >= len(source_languages):
                source_idx = 0
            
            source_lang = source_languages[source_idx]
            
            print(f"\n{Fore.CYAN}Langue cible:{Style.RESET_ALL}")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
            if target_idx < 0 or target_idx >= len(target_languages):
                target_idx = 0
            
            target_lang = target_languages[target_idx]
            
            # Confirmation
            print(f"\n{Fore.CYAN}Récapitulatif:{Style.RESET_ALL}")
            print(f"  Articles populaires: {count}")
            print(f"  De: {source_lang} vers: {target_lang}")
            
            confirm = get_user_input("Confirmer (o/n)", "o")
            
            if confirm.lower() in ["o", "oui", "y", "yes"]:
                cmd = [
                    "python3", "scripts/batch_processor.py",
                    "--popular",
                    "--count", str(count),
                    "--source-lang", source_lang,
                    "--target-lang", target_lang
                ]
                
                execute_command(cmd)
        
        # [...]  (les autres options de traitement par lots suivent le même modèle)
        
    except Exception as e:
        print(f"\n{Fore.RED}Erreur lors du traitement par lots: {e}{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")

# Modification de run_interactive.py pour intégrer les nouvelles fonctionnalités

# Ajouter cette fonction dans la section des menus
def manage_linguistic_resources(config):
    """Menu pour gérer les ressources linguistiques"""
    while True:
        print_header()
        
        choice = print_menu("Gestion des Ressources Linguistiques", [
            "Télécharger et filtrer un corpus",
            "Extraire des termes depuis Wiktionary",
            "Importer des terminologies",
            "Enrichir automatiquement depuis toutes les sources",
            "Afficher les statistiques des ressources"
        ])
        
        if choice == "0":
            break
        elif choice == "1":
            # Télécharger et filtrer un corpus
            print(f"\n{Fore.CYAN}Téléchargement de corpus{Style.RESET_ALL}")
            
            # Options de langues
            source_languages = config['languages']['source']
            target_languages = config['languages']['target']
            
            print(f"\n{Fore.CYAN}Langue source:{Style.RESET_ALL}")
            for i, lang in enumerate(source_languages, 1):
                print(f"  {i}. {lang}")
            
            source_idx = int(get_user_input("Choisissez la langue source (numéro)", "1")) - 1
            if source_idx < 0 or source_idx >= len(source_languages):
                source_idx = 0
            
            source_lang = source_languages[source_idx]
            
            print(f"\n{Fore.CYAN}Langue cible:{Style.RESET_ALL}")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
            if target_idx < 0 or target_idx >= len(target_languages):
                target_idx = 0
            
            target_lang = target_languages[target_idx]
            
            domain = get_user_input("Domaine du corpus (WikiMatrix, Bible, OpenSubtitles, etc.)", "WikiMatrix")
            
            # Confirmation
            print(f"\n{Fore.CYAN}Récapitulatif:{Style.RESET_ALL}")
            print(f"  Téléchargement du corpus {domain}")
            print(f"  Langues: {source_lang} → {target_lang}")
            
            confirm = get_user_input("Confirmer (o/n)", "o").lower()
            if confirm in ["o", "oui", "y", "yes"]:
                try:
                    # Importer dynamiquement pour éviter les erreurs si le module n'est pas encore créé
                    import_cmd = [
                        "python", "scripts/enrich_resources.py", 
                        "corpus",
                        "--download",
                        "--source-lang", source_lang,
                        "--target-lang", target_lang,
                        "--domain", domain
                    ]
                    execute_command(import_cmd)
                except Exception as e:
                    print(f"\n{Fore.RED}Erreur: {e}{Style.RESET_ALL}")
                    input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
        
        elif choice == "2":
            # Extraction depuis Wiktionary
            print(f"\n{Fore.CYAN}Extraction de termes depuis Wiktionary{Style.RESET_ALL}")
            
            # Options de langues
            source_languages = config['languages']['source']
            target_languages = config['languages']['target']
            
            print(f"\n{Fore.CYAN}Langue source:{Style.RESET_ALL}")
            for i, lang in enumerate(source_languages, 1):
                print(f"  {i}. {lang}")
            
            source_idx = int(get_user_input("Choisissez la langue source (numéro)", "1")) - 1
            if source_idx < 0 or source_idx >= len(source_languages):
                source_idx = 0
            
            source_lang = source_languages[source_idx]
            
            print(f"\n{Fore.CYAN}Langue cible:{Style.RESET_ALL}")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
            if target_idx < 0 or target_idx >= len(target_languages):
                target_idx = 0
            
            target_lang = target_languages[target_idx]
            
            max_words = get_user_input("Nombre maximum de mots à extraire", "300")
            
            # Confirmation
            print(f"\n{Fore.CYAN}Récapitulatif:{Style.RESET_ALL}")
            print(f"  Extraction depuis Wiktionary")
            print(f"  Langues: {source_lang} → {target_lang}")
            print(f"  Max mots: {max_words}")
            
            confirm = get_user_input("Confirmer (o/n)", "o").lower()
            if confirm in ["o", "oui", "y", "yes"]:
                try:
                    import_cmd = [
                        "python", "scripts/enrich_resources.py", 
                        "wiktionary",
                        "--source-lang", source_lang,
                        "--target-lang", target_lang,
                        "--max-words", max_words
                    ]
                    execute_command(import_cmd)
                except Exception as e:
                    print(f"\n{Fore.RED}Erreur: {e}{Style.RESET_ALL}")
                    input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
        
        elif choice == "3":
            # Importation de terminologies
            print(f"\n{Fore.CYAN}Importation de terminologies{Style.RESET_ALL}")
            
            file_path = get_user_input("Chemin vers le fichier de terminologie (.tbx, .csv, .tsv, .json)")
            
            if not os.path.exists(file_path):
                print(f"{Fore.RED}Le fichier n'existe pas: {file_path}{Style.RESET_ALL}")
                time.sleep(1.5)
                continue
            
            # Options de langues
            source_languages = config['languages']['source']
            target_languages = config['languages']['target']
            
            print(f"\n{Fore.CYAN}Langue source:{Style.RESET_ALL}")
            for i, lang in enumerate(source_languages, 1):
                print(f"  {i}. {lang}")
            
            source_idx = int(get_user_input("Choisissez la langue source (numéro)", "1")) - 1
            if source_idx < 0 or source_idx >= len(source_languages):
                source_idx = 0
            
            source_lang = source_languages[source_idx]
            
            print(f"\n{Fore.CYAN}Langue cible (vide pour toutes):{Style.RESET_ALL}")
            print("  0. Toutes les langues cibles")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "0"))
            target_lang = None if target_idx == 0 else target_languages[target_idx-1] if 0 < target_idx <= len(target_languages) else None
            
            domain = get_user_input("Domaine des termes (vide pour auto-détection)")
            
            # Confirmation
            print(f"\n{Fore.CYAN}Récapitulatif:{Style.RESET_ALL}")
            print(f"  Fichier: {file_path}")
            print(f"  Source: {source_lang}")
            print(f"  Cible: {target_lang if target_lang else 'Toutes'}")
            print(f"  Domaine: {domain if domain else 'Auto-détection'}")
            
            confirm = get_user_input("Confirmer (o/n)", "o").lower()
            if confirm in ["o", "oui", "y", "yes"]:
                try:
                    cmd = ["python", "scripts/enrich_resources.py", "terminology", "--file", file_path, "--source-lang", source_lang]
                    
                    if target_lang:
                        cmd.extend(["--target-lang", target_lang])
                    if domain:
                        cmd.extend(["--domain", domain])
                    
                    execute_command(cmd)
                except Exception as e:
                    print(f"\n{Fore.RED}Erreur: {e}{Style.RESET_ALL}")
                    input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
        
        elif choice == "4":
            # Enrichissement automatique depuis toutes les sources
            print(f"\n{Fore.CYAN}Enrichissement automatique depuis toutes les sources{Style.RESET_ALL}")
            
            # Options de langues
            source_languages = config['languages']['source']
            target_languages = config['languages']['target']
            
            print(f"\n{Fore.CYAN}Langue source:{Style.RESET_ALL}")
            for i, lang in enumerate(source_languages, 1):
                print(f"  {i}. {lang}")
            
            source_idx = int(get_user_input("Choisissez la langue source (numéro)", "1")) - 1
            if source_idx < 0 or source_idx >= len(source_languages):
                source_idx = 0
            
            source_lang = source_languages[source_idx]
            
            print(f"\n{Fore.CYAN}Langue cible:{Style.RESET_ALL}")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
            if target_idx < 0 or target_idx >= len(target_languages):
                target_idx = 0
            
            target_lang = target_languages[target_idx]
            
            # Confirmation
            print(f"\n{Fore.CYAN}Récapitulatif:{Style.RESET_ALL}")
            print(f"  Enrichissement automatique depuis toutes les sources")
            print(f"  Langues: {source_lang} → {target_lang}")
            print(f"  Sources: Corpus, Wiktionary, Terminologies")
            
            confirm = get_user_input("Confirmer (o/n)", "o").lower()
            if confirm in ["o", "oui", "y", "yes"]:
                try:
                    cmd = [
                        "python", "scripts/enrich_resources.py", 
                        "enrich-all",
                        "--source-lang", source_lang,
                        "--target-lang", target_lang
                    ]
                    execute_command(cmd)
                except Exception as e:
                    print(f"\n{Fore.RED}Erreur: {e}{Style.RESET_ALL}")
                    input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
        
        elif choice == "5":
            # Afficher les statistiques
            print(f"\n{Fore.CYAN}Statistiques des ressources linguistiques{Style.RESET_ALL}")
            
            # Options de langues
            source_languages = config['languages']['source']
            target_languages = config['languages']['target']
            
            print(f"\n{Fore.CYAN}Langue source (vide pour toutes):{Style.RESET_ALL}")
            print("  0. Toutes les langues sources")
            for i, lang in enumerate(source_languages, 1):
                print(f"  {i}. {lang}")
            
            source_idx = int(get_user_input("Choisissez la langue source (numéro)", "0"))
            source_lang = None if source_idx == 0 else source_languages[source_idx-1] if 0 < source_idx <= len(source_languages) else None
            
            print(f"\n{Fore.CYAN}Langue cible (vide pour toutes):{Style.RESET_ALL}")
            print("  0. Toutes les langues cibles")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "0"))
            target_lang = None if target_idx == 0 else target_languages[target_idx-1] if 0 < target_idx <= len(target_languages) else None
            
            try:
                cmd = ["python", "scripts/enrich_resources.py", "stats"]
                
                if source_lang:
                    cmd.extend(["--source-lang", source_lang])
                if target_lang:
                    cmd.extend(["--target-lang", target_lang])
                
                execute_command(cmd)
            except Exception as e:
                print(f"\n{Fore.RED}Erreur: {e}{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")

def system_configuration(config):
    """Menu pour configurer le système."""
    while True:
        print_header()
        
        choice = print_menu("Configuration du Système", [
            "Voir la configuration actuelle",
            "Éditer la configuration",
            "Réinitialiser la configuration",
            "Configurer les API Keys"
        ])
        
        try:
            if choice == "0":
                break
            elif choice == "1":
                # Afficher la configuration
                print(f"\n{Fore.CYAN}Configuration actuelle:{Style.RESET_ALL}\n")
                
                try:
                    import yaml
                    print(yaml.dump(config, sort_keys=False, default_flow_style=False))
                except ImportError:
                    print(json.dumps(config, indent=2))
                
                input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
            
            elif choice == "2":
                # Éditer la configuration
                print(f"\n{Fore.CYAN}Édition de la configuration{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Note: L'édition manuelle du fichier est recommandée pour des modifications complexes.{Style.RESET_ALL}\n")
                
                # Options de configuration simples
                config_file = "config.yaml"
                
                print(f"1. Langues source ({', '.join(config['languages']['source'])})")
                print(f"2. Langues cible ({', '.join(config['languages']['target'])})")
                print(f"3. Paramètres de segmentation (max: {config['segmentation']['max_segment_length']}, min: {config['segmentation']['min_segment_length']})")
                print(f"4. Modèle de traduction ({config['translation']['model']})")
                print(f"5. Délai de limitation de taux ({config['translation']['rate_limit_delay']})")
                
                option = get_user_input("Choisissez un paramètre à modifier (1-5)", "0")
                
                if option == "1":
                    # Modifier les langues source
                    langs = get_user_input("Entrez les langues source séparées par des virgules (ex: fr,en)", ",".join(config['languages']['source']))
                    config['languages']['source'] = [lang.strip() for lang in langs.split(",") if lang.strip()]
                
                elif option == "2":
                    # Modifier les langues cible
                    langs = get_user_input("Entrez les langues cible séparées par des virgules (ex: fon,ewe,yor)", ",".join(config['languages']['target']))
                    config['languages']['target'] = [lang.strip() for lang in langs.split(",") if lang.strip()]
                
                elif option == "3":
                    # Modifier les paramètres de segmentation
                    max_len = get_user_input(f"Longueur maximale d'un segment ({config['segmentation']['max_segment_length']})", str(config['segmentation']['max_segment_length']))
                    min_len = get_user_input(f"Longueur minimale d'un segment ({config['segmentation']['min_segment_length']})", str(config['segmentation']['min_segment_length']))
                    
                    config['segmentation']['max_segment_length'] = int(max_len)
                    config['segmentation']['min_segment_length'] = int(min_len)
                
                elif option == "4":
                    # Modifier le modèle de traduction
                    model = get_user_input(f"Modèle de traduction ({config['translation']['model']})", config['translation']['model'])
                    config['translation']['model'] = model
                
                elif option == "5":
                    # Modifier le délai de limitation de taux
                    delay = get_user_input(f"Délai de limitation de taux ({config['translation']['rate_limit_delay']})", str(config['translation']['rate_limit_delay']))
                    config['translation']['rate_limit_delay'] = float(delay)
                
                # Sauvegarder la configuration
                if option in ["1", "2", "3", "4", "5"]:
                    save_config(config, config_file)
                    print(f"\n{Fore.GREEN}Configuration mise à jour avec succès.{Style.RESET_ALL}")
                    time.sleep(1.5)
            
            elif choice == "3":
                # Réinitialiser la configuration
                confirm = get_user_input("Êtes-vous sûr de vouloir réinitialiser la configuration? (o/n)", "n")
                
                if confirm.lower() in ["o", "oui", "y", "yes"]:
                    from src.utils.config import create_config_file
                    create_config_file("config.yaml")
                    print(f"\n{Fore.GREEN}Configuration réinitialisée avec succès.{Style.RESET_ALL}")
                    
                    # Recharger la configuration
                    config = load_config("config.yaml")
                    
                    time.sleep(1.5)
            
            elif choice == "4":
                # Configurer les API Keys
                print(f"\n{Fore.CYAN}Configuration des clés API{Style.RESET_ALL}\n")
                
                api_key = get_user_input(f"Clé API Azure OpenAI", config['translation'].get('api_key', ''))
                api_endpoint = get_user_input(f"Endpoint Azure OpenAI", config['translation'].get('azure_endpoint', ''))
                
                if api_key or api_endpoint:
                    config['translation']['api_key'] = api_key
                    config['translation']['azure_endpoint'] = api_endpoint
                    
                    # Sauvegarder la configuration
                    save_config(config, "config.yaml")
                    
                    print(f"\n{Fore.GREEN}Clés API mises à jour avec succès.{Style.RESET_ALL}")
                    time.sleep(1.5)
        except Exception as e:
            print(f"\n{Fore.RED}Erreur lors de la configuration: {e}{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")

def show_help():
    """Affiche l'aide du programme."""
    print_header()
    
    help_text = f"""
{Fore.CYAN}Guide d'utilisation de WikiTranslateAI{Style.RESET_ALL}

WikiTranslateAI est un outil de traduction d'articles Wikipedia vers les langues africaines
peu dotées: fon, dindi, ewe et yoruba.

{Fore.GREEN}Fonctionnalités principales:{Style.RESET_ALL}

1. {Fore.YELLOW}Extraire et traduire un article spécifique{Style.RESET_ALL}
   Permet de traduire un article Wikipedia particulier en spécifiant son titre.

2. {Fore.YELLOW}Rechercher et traduire des articles{Style.RESET_ALL}
   Recherche des articles Wikipedia correspondant à un terme et les traduit.

3. {Fore.YELLOW}Traduire des articles aléatoires{Style.RESET_ALL}
   Sélectionne aléatoirement des articles Wikipedia et les traduit.

4. {Fore.YELLOW}Gérer le glossaire{Style.RESET_ALL}
   Consulte, importe, exporte et crée des glossaires pour améliorer les traductions.

5. {Fore.YELLOW}Évaluer les traductions existantes{Style.RESET_ALL}
   Évalue la qualité des traductions à l'aide de métriques comme BLEU et METEOR.

6. {Fore.YELLOW}Visualiser les statistiques{Style.RESET_ALL}
   Affiche des statistiques sur les articles traités et les glossaires.

7. {Fore.YELLOW}Traitement par lots{Style.RESET_ALL}
   Permet de traduire un grand nombre d'articles en même temps.

8. {Fore.YELLOW}Configuration du système{Style.RESET_ALL}
   Permet de modifier les paramètres du système comme les langues et les API keys.

{Fore.GREEN}Processus de traduction:{Style.RESET_ALL}

Le processus se déroule en plusieurs étapes:
1. Extraction de l'article depuis Wikipedia
2. Nettoyage du contenu HTML/wikitext
3. Segmentation du texte en unités traduisibles
4. Traduction de chaque segment avec l'API Azure OpenAI
5. Reconstruction de l'article traduit

{Fore.GREEN}Structure des données:{Style.RESET_ALL}

Les articles et traductions sont stockés dans le dossier 'data':
- articles_raw: Articles bruts extraits de Wikipedia
- articles_cleaned: Articles nettoyés
- articles_segmented: Articles découpés en segments
- articles_translated: Articles traduits
- glossaries: Glossaires pour améliorer les traductions

{Fore.GREEN}Dépendances:{Style.RESET_ALL}

Le projet nécessite:
- Python 3.8 ou supérieur
- Accès à l'API Azure OpenAI
- Connexion internet pour accéder à Wikipedia

{Fore.YELLOW}Pour plus d'informations, consultez le fichier README.md{Style.RESET_ALL}
"""
    
    print(help_text)
    input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")

def manage_linguistic_resources(config):
    """Menu pour gérer les ressources linguistiques"""
    while True:
        print_header()
        
        choice = print_menu("Gestion des Ressources Linguistiques", [
            "Télécharger et filtrer un corpus",
            "Extraire des termes depuis Wiktionary",
            "Importer des terminologies",
            "Enrichir automatiquement depuis toutes les sources",
            "Télécharger des ressources spécifiques par langue",
            "Consolider les corpus par langue",
            "Afficher les statistiques des ressources"
        ])
        
        if choice == "0":
            break
        elif choice == "1":
            # Télécharger et filtrer un corpus
            print(f"\n{Fore.CYAN}Téléchargement de corpus{Style.RESET_ALL}")
            
            # Options de langues
            source_languages = config['languages']['source']
            target_languages = config['languages']['target']
            
            print(f"\n{Fore.CYAN}Langue source:{Style.RESET_ALL}")
            for i, lang in enumerate(source_languages, 1):
                print(f"  {i}. {lang}")
            
            source_idx = int(get_user_input("Choisissez la langue source (numéro)", "1")) - 1
            if source_idx < 0 or source_idx >= len(source_languages):
                source_idx = 0
            
            source_lang = source_languages[source_idx]
            
            print(f"\n{Fore.CYAN}Langue cible:{Style.RESET_ALL}")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
            if target_idx < 0 or target_idx >= len(target_languages):
                target_idx = 0
            
            target_lang = target_languages[target_idx]
            
            domain = get_user_input("Domaine du corpus (WikiMatrix, Bible, OpenSubtitles, etc.)", "WikiMatrix")
            
            # Confirmation
            print(f"\n{Fore.CYAN}Récapitulatif:{Style.RESET_ALL}")
            print(f"  Téléchargement du corpus {domain}")
            print(f"  Langues: {source_lang} → {target_lang}")
            
            confirm = get_user_input("Confirmer (o/n)", "o").lower()
            if confirm in ["o", "oui", "y", "yes"]:
                try:
                    from src.corpus.resource_manager import LinguisticResourceManager
                    resource_manager = LinguisticResourceManager(config)
                    
                    print(f"\n{Fore.CYAN}Téléchargement en cours...{Style.RESET_ALL}")
                    corpus_path = resource_manager.download_corpus(source_lang, target_lang, domain)
                    
                    if corpus_path:
                        print(f"\n{Fore.GREEN}Corpus téléchargé avec succès: {corpus_path}{Style.RESET_ALL}")
                    else:
                        print(f"\n{Fore.RED}Échec du téléchargement du corpus{Style.RESET_ALL}")
                    
                    input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
                except Exception as e:
                    print(f"\n{Fore.RED}Erreur: {e}{Style.RESET_ALL}")
                    input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
        
        elif choice == "2":
            # Extraction depuis Wiktionary
            print(f"\n{Fore.CYAN}Extraction de termes depuis Wiktionary{Style.RESET_ALL}")
            
            # Options de langues
            source_languages = config['languages']['source']
            target_languages = config['languages']['target']
            
            print(f"\n{Fore.CYAN}Langue source:{Style.RESET_ALL}")
            for i, lang in enumerate(source_languages, 1):
                print(f"  {i}. {lang}")
            
            source_idx = int(get_user_input("Choisissez la langue source (numéro)", "1")) - 1
            if source_idx < 0 or source_idx >= len(source_languages):
                source_idx = 0
            
            source_lang = source_languages[source_idx]
            
            print(f"\n{Fore.CYAN}Langue cible:{Style.RESET_ALL}")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
            if target_idx < 0 or target_idx >= len(target_languages):
                target_idx = 0
            
            target_lang = target_languages[target_idx]
            
            max_words = int(get_user_input("Nombre maximum de mots à extraire", "300"))
            
            # Confirmation
            print(f"\n{Fore.CYAN}Récapitulatif:{Style.RESET_ALL}")
            print(f"  Extraction depuis Wiktionary")
            print(f"  Langues: {source_lang} → {target_lang}")
            print(f"  Max mots: {max_words}")
            
            confirm = get_user_input("Confirmer (o/n)", "o").lower()
            if confirm in ["o", "oui", "y", "yes"]:
                try:
                    from src.corpus.resource_manager import LinguisticResourceManager
                    resource_manager = LinguisticResourceManager(config)
                    
                    print(f"\n{Fore.CYAN}Extraction des termes en cours...{Style.RESET_ALL}")
                    count = resource_manager.extract_wiktionary_terms(source_lang, target_lang, max_words)
                    
                    if count > 0:
                        print(f"\n{Fore.GREEN}{count} termes extraits avec succès depuis Wiktionary.{Style.RESET_ALL}")
                    else:
                        print(f"\n{Fore.YELLOW}Aucun terme extrait depuis Wiktionary.{Style.RESET_ALL}")
                    
                    input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
                except Exception as e:
                    print(f"\n{Fore.RED}Erreur: {e}{Style.RESET_ALL}")
                    input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
        
        elif choice == "3":
            # Importation de terminologies
            print(f"\n{Fore.CYAN}Importation de terminologies{Style.RESET_ALL}")
            
            file_path = get_user_input("Chemin vers le fichier de terminologie (.tbx, .csv, .tsv, .json)")
            
            if not os.path.exists(file_path):
                print(f"{Fore.RED}Le fichier n'existe pas: {file_path}{Style.RESET_ALL}")
                time.sleep(1.5)
                continue
            
            # Options de langues
            source_languages = config['languages']['source']
            target_languages = config['languages']['target']
            
            print(f"\n{Fore.CYAN}Langue source:{Style.RESET_ALL}")
            for i, lang in enumerate(source_languages, 1):
                print(f"  {i}. {lang}")
            
            source_idx = int(get_user_input("Choisissez la langue source (numéro)", "1")) - 1
            
            if source_idx < 0 or source_idx >= len(source_languages):
                source_idx = 0
            
            source_lang = source_languages[source_idx]
            
            print(f"\n{Fore.CYAN}Langue cible (vide pour toutes):{Style.RESET_ALL}")
            print("  0. Toutes les langues cibles")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "0"))
            target_lang = None if target_idx == 0 else target_languages[target_idx-1] if 0 < target_idx <= len(target_languages) else None
            
            domain = get_user_input("Domaine des termes (vide pour auto-détection)")
            
            # Confirmation
            print(f"\n{Fore.CYAN}Récapitulatif:{Style.RESET_ALL}")
            print(f"  Fichier: {file_path}")
            print(f"  Source: {source_lang}")
            print(f"  Cible: {target_lang if target_lang else 'Toutes'}")
            print(f"  Domaine: {domain if domain else 'Auto-détection'}")
            
            confirm = get_user_input("Confirmer (o/n)", "o").lower()
            if confirm in ["o", "oui", "y", "yes"]:
                try:
                    from src.corpus.resource_manager import LinguisticResourceManager
                    resource_manager = LinguisticResourceManager(config)
                    
                    print(f"\n{Fore.CYAN}Importation des termes en cours...{Style.RESET_ALL}")
                    results = resource_manager.import_terminology(file_path, source_lang, target_lang, domain)
                    
                    if results:
                        print(f"\n{Fore.GREEN}Résultats de l'importation:{Style.RESET_ALL}")
                        for lang, count in results.items():
                            print(f"  - {lang}: {count} termes importés")
                    else:
                        print(f"\n{Fore.YELLOW}Aucun terme importé.{Style.RESET_ALL}")
                    
                    input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
                except Exception as e:
                    print(f"\n{Fore.RED}Erreur: {e}{Style.RESET_ALL}")
                    input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
        
        elif choice == "4":
            # Enrichissement automatique depuis toutes les sources
            print(f"\n{Fore.CYAN}Enrichissement automatique depuis toutes les sources{Style.RESET_ALL}")
            
            # Options de langues
            source_languages = config['languages']['source']
            target_languages = config['languages']['target']
            
            print(f"\n{Fore.CYAN}Langue source:{Style.RESET_ALL}")
            for i, lang in enumerate(source_languages, 1):
                print(f"  {i}. {lang}")
            
            source_idx = int(get_user_input("Choisissez la langue source (numéro)", "1")) - 1
            if source_idx < 0 or source_idx >= len(source_languages):
                source_idx = 0
            
            source_lang = source_languages[source_idx]
            
            print(f"\n{Fore.CYAN}Langue cible:{Style.RESET_ALL}")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
            if target_idx < 0 or target_idx >= len(target_languages):
                target_idx = 0
            
            target_lang = target_languages[target_idx]
            
            # Confirmation
            print(f"\n{Fore.CYAN}Récapitulatif:{Style.RESET_ALL}")
            print(f"  Enrichissement automatique depuis toutes les sources")
            print(f"  Langues: {source_lang} → {target_lang}")
            print(f"  Sources: Corpus, Wiktionary, Terminologies")
            
            confirm = get_user_input("Confirmer (o/n)", "o").lower()
            if confirm in ["o", "oui", "y", "yes"]:
                try:
                    from src.corpus.resource_manager import LinguisticResourceManager
                    resource_manager = LinguisticResourceManager(config)
                    
                    print(f"\n{Fore.CYAN}Enrichissement en cours... Cette opération peut prendre plusieurs minutes.{Style.RESET_ALL}")
                    stats = resource_manager.enrich_from_all_sources(source_lang, target_lang)
                    
                    print(f"\n{Fore.GREEN}Résultats de l'enrichissement:{Style.RESET_ALL}")
                    print(f"  - Corpus: {stats['corpus']} termes")
                    print(f"  - Wiktionary: {stats['wiktionary']} termes")
                    print(f"  - Terminologie: {stats['terminology']} termes")
                    print(f"  - Ressources spécifiques: {stats.get('custom_resources', 0)} termes")
                    print(f"  - TOTAL: {stats['total']} termes")
                    
                    input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
                except Exception as e:
                    print(f"\n{Fore.RED}Erreur: {e}{Style.RESET_ALL}")
                    input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
        
        elif choice == "5":
            # Télécharger des ressources spécifiques par langue
            print(f"\n{Fore.CYAN}Téléchargement de ressources spécifiques par langue{Style.RESET_ALL}")
            
            # Options de langues cibles (seulement les langues africaines)
            target_languages = [lang for lang in config['languages']['target'] if lang in ["fon", "dindi", "ewe", "yor"]]
            
            print(f"\n{Fore.CYAN}Langue cible:{Style.RESET_ALL}")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
            if target_idx < 0 or target_idx >= len(target_languages):
                target_idx = 0
            
            target_lang = target_languages[target_idx]
            
            # Confirmation
            print(f"\n{Fore.CYAN}Récapitulatif:{Style.RESET_ALL}")
            print(f"  Téléchargement de ressources spécifiques pour: {target_lang}")
            
            confirm = get_user_input("Confirmer (o/n)", "o").lower()
            if confirm in ["o", "oui", "y", "yes"]:
                try:
                    from src.corpus.custom_corpus import CustomCorpusManager
                    
                    corpus_dir = os.path.join(config['paths']['data_dir'], 'corpus')
                    manager = CustomCorpusManager(corpus_dir)
                    
                    print(f"\n{Fore.CYAN}Téléchargement en cours... Cela peut prendre plusieurs minutes.{Style.RESET_ALL}")
                    
                    resources = manager.download_language_specific_resources(target_lang)
                    
                    if resources:
                        print(f"\n{Fore.GREEN}Ressources téléchargées avec succès pour {target_lang}:{Style.RESET_ALL}")
                        resource_count = 0
                        
                        for resource in resources:
                            if isinstance(resource, list):
                                for res in resource:
                                    print(f"  - {res['name']}: {res['path']}")
                                    resource_count += 1
                            else:
                                print(f"  - {resource['name']}: {resource['path']}")
                                resource_count += 1
                        
                        print(f"\n{Fore.GREEN}Total: {resource_count} ressources téléchargées{Style.RESET_ALL}")
                    else:
                        print(f"\n{Fore.RED}Aucune ressource n'a pu être téléchargée pour {target_lang}.{Style.RESET_ALL}")
                    
                    input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
                except Exception as e:
                    print(f"\n{Fore.RED}Erreur: {e}{Style.RESET_ALL}")
                    input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
        
        elif choice == "6":
            # Consolider les corpus par langue
            print(f"\n{Fore.CYAN}Consolidation des corpus par langue{Style.RESET_ALL}")
            
            # Options de langues cibles
            target_languages = config['languages']['target']
            
            print(f"\n{Fore.CYAN}Langue cible:{Style.RESET_ALL}")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
            if target_idx < 0 or target_idx >= len(target_languages):
                target_idx = 0
            
            target_lang = target_languages[target_idx]
            
            # Confirmation
            print(f"\n{Fore.CYAN}Récapitulatif:{Style.RESET_ALL}")
            print(f"  Consolidation des corpus pour: {target_lang}")
            print(f"  Cette opération fusionnera tous les corpus disponibles pour cette langue")
            
            confirm = get_user_input("Confirmer (o/n)", "o").lower()
            if confirm in ["o", "oui", "y", "yes"]:
                try:
                    from src.corpus.custom_corpus import CustomCorpusManager
                    
                    corpus_dir = os.path.join(config['paths']['data_dir'], 'corpus')
                    manager = CustomCorpusManager(corpus_dir)
                    
                    print(f"\n{Fore.CYAN}Consolidation en cours...{Style.RESET_ALL}")
                    
                    # Appeler la méthode de consolidation
                    consolidated = manager.consolidate_corpus(target_lang)
                    
                    if consolidated:
                        print(f"\n{Fore.GREEN}Corpus consolidés avec succès:{Style.RESET_ALL}")
                        for source_lang, path in consolidated.items():
                            print(f"  - {source_lang} → {target_lang}: {path}")
                    else:
                        print(f"\n{Fore.RED}Aucun corpus consolidé pour {target_lang}.{Style.RESET_ALL}")
                    
                    input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
                except Exception as e:
                    print(f"\n{Fore.RED}Erreur: {e}{Style.RESET_ALL}")
                    input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
        
        elif choice == "7":
            # Afficher les statistiques
            print(f"\n{Fore.CYAN}Statistiques des ressources linguistiques{Style.RESET_ALL}")
            
            # Options de langues
            source_languages = config['languages']['source']
            target_languages = config['languages']['target']
            
            print(f"\n{Fore.CYAN}Langue source (vide pour toutes):{Style.RESET_ALL}")
            print("  0. Toutes les langues sources")
            for i, lang in enumerate(source_languages, 1):
                print(f"  {i}. {lang}")
            
            source_idx = int(get_user_input("Choisissez la langue source (numéro)", "0"))
            source_lang = None if source_idx == 0 else source_languages[source_idx-1] if 0 < source_idx <= len(source_languages) else None
            
            print(f"\n{Fore.CYAN}Langue cible (vide pour toutes):{Style.RESET_ALL}")
            print("  0. Toutes les langues cibles")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "0"))
            target_lang = None if target_idx == 0 else target_languages[target_idx-1] if 0 < target_idx <= len(target_languages) else None
            
            try:
                from src.corpus.resource_manager import LinguisticResourceManager
                resource_manager = LinguisticResourceManager(config)
                
                print(f"\n{Fore.CYAN}Récupération des statistiques...{Style.RESET_ALL}")
                stats = resource_manager.get_glossary_statistics(source_lang, target_lang)
                
                print(f"\n{Fore.GREEN}Statistiques du glossaire:{Style.RESET_ALL}")
                print(f"  - Entrées totales: {stats['total_entries']}")
                
                if 'pair_entries' in stats:
                    print(f"  - Entrées {source_lang}-{target_lang}: {stats['pair_entries']}")
                
                print(f"  - Entrées validées: {stats['validated']}")
                print(f"  - Entrées non validées: {stats['unvalidated']}")
                
                print("\n  - Domaines:")
                for domain, count in stats['domains'].items():
                    print(f"    * {domain}: {count}")
                
                print("\n  - Confiance:")
                print(f"    * Élevée: {stats['confidence']['high']}")
                print(f"    * Moyenne: {stats['confidence']['medium']}")
                print(f"    * Faible: {stats['confidence']['low']}")
                
                input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
            except Exception as e:
                print(f"\n{Fore.RED}Erreur: {e}{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")

def reconstruct_articles(config):
    """Menu pour reconstruire et exporter les articles traduits."""
    print_header()
    
    try:
        from src.reconstruction.rebuild_article import ArticleReconstructor
        from src.reconstruction.format_handler import FormatHandler
        
        # Répertoire des traductions
        translated_dir = config['paths']['articles_translated']
        
        # Vérifier si le répertoire existe
        if not os.path.exists(translated_dir):
            print(f"{Fore.RED}Répertoire des traductions non trouvé: {translated_dir}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Veuillez d'abord traduire quelques articles.{Style.RESET_ALL}")
            time.sleep(2)
            return
        
        # Trouver les langues cibles disponibles
        available_langs = []
        for item in os.listdir(translated_dir):
            if os.path.isdir(os.path.join(translated_dir, item)) and not item.endswith("_txt") and item != "reconstructed":
                available_langs.append(item)
        
        if not available_langs:
            print(f"{Fore.RED}Aucun article traduit trouvé.{Style.RESET_ALL}")
            time.sleep(2)
            return
        
        print(f"\n{Fore.CYAN}Langues disponibles:{Style.RESET_ALL}")
        for i, lang in enumerate(available_langs, 1):
            print(f"  {i}. {lang}")
        
        lang_idx = int(get_user_input("Choisissez la langue à reconstruire (numéro)", "1")) - 1
        if lang_idx < 0 or lang_idx >= len(available_langs):
            lang_idx = 0
        
        target_lang = available_langs[lang_idx]
        target_dir = os.path.join(translated_dir, target_lang)
        
        # Liste des articles disponibles
        articles = [f for f in os.listdir(target_dir) if f.endswith('.json')]
        
        if not articles:
            print(f"{Fore.RED}Aucun article traduit trouvé pour la langue {target_lang}.{Style.RESET_ALL}")
            time.sleep(2)
            return
        
        # Choix entre un article spécifique ou tous les articles
        print(f"\n{Fore.CYAN}Mode de reconstruction:{Style.RESET_ALL}")
        print("  1. Reconstruire un article spécifique")
        print("  2. Reconstruire tous les articles de cette langue")
        
        mode = get_user_input("Choisissez le mode (numéro)", "1")
        
        if mode == "1":
            # Afficher la liste des articles
            print(f"\n{Fore.CYAN}Articles disponibles:{Style.RESET_ALL}")
            for i, article in enumerate(articles, 1):
                print(f"  {i}. {article.replace('.json', '')}")
            
            article_idx = int(get_user_input("Choisissez l'article à reconstruire (numéro)", "1")) - 1
            if article_idx < 0 or article_idx >= len(articles):
                article_idx = 0
            
            article_file = articles[article_idx]
            article_path = os.path.join(target_dir, article_file)
            
            # Formats d'exportation
            print(f"\n{Fore.CYAN}Formats d'exportation:{Style.RESET_ALL}")
            print("  1. JSON seulement")
            print("  2. Texte seulement")
            print("  3. HTML seulement")
            print("  4. Markdown seulement")
            print("  5. Tous les formats")
            
            format_choice = get_user_input("Choisissez les formats (numéro)", "5")
            
            if format_choice == "1":
                output_format = "json"
            elif format_choice == "2":
                output_format = "txt"
            elif format_choice == "3":
                output_format = "html"
            elif format_choice == "4":
                output_format = "markdown"
            else:
                output_format = "all"
            
            # Répertoire de sortie
            output_dir = os.path.join(translated_dir, "reconstructed")
            
            # Reconstruire l'article
            print(f"\n{Fore.CYAN}Reconstruction de l'article {article_file.replace('.json', '')}...{Style.RESET_ALL}")
            
            try:
                # Lire le fichier de l'article
                with open(article_path, 'r', encoding='utf-8') as f:
                    article_data = json.load(f)
                
                # Initialiser le reconstructeur
                reconstructor = ArticleReconstructor(output_dir)
                
                # Reconstruire l'article
                reconstructed_data = reconstructor.reconstruct_article(article_data)
                
                # Sauvegarder dans les formats demandés
                output_paths = reconstructor.save_reconstructed_article(reconstructed_data, output_format)
                
                print(f"\n{Fore.GREEN}Article reconstruit avec succès:{Style.RESET_ALL}")
                for format_name, path in output_paths.items():
                    print(f"  - Format {format_name.upper()}: {path}")
                
            except Exception as e:
                print(f"\n{Fore.RED}Erreur lors de la reconstruction: {e}{Style.RESET_ALL}")
            
        elif mode == "2":
            # Reconstruire tous les articles
            print(f"\n{Fore.CYAN}Reconstruction de tous les articles en {target_lang}...{Style.RESET_ALL}")
            
            # Formats d'exportation
            print(f"\n{Fore.CYAN}Formats d'exportation:{Style.RESET_ALL}")
            print("  1. JSON seulement")
            print("  2. Texte seulement")
            print("  3. HTML seulement")
            print("  4. Markdown seulement")
            print("  5. Tous les formats")
            
            format_choice = get_user_input("Choisissez les formats (numéro)", "5")
            
            if format_choice == "1":
                output_format = "json"
            elif format_choice == "2":
                output_format = "txt"
            elif format_choice == "3":
                output_format = "html"
            elif format_choice == "4":
                output_format = "markdown"
            else:
                output_format = "all"
            
            # Répertoire de sortie
            output_dir = os.path.join(translated_dir, "reconstructed")
            
            try:
                # Initialiser le reconstructeur
                reconstructor = ArticleReconstructor(output_dir)
                format_handler = FormatHandler(output_dir)
                
                success_count = 0
                error_count = 0
                
                print(f"\n{Fore.CYAN}Traitement de {len(articles)} articles...{Style.RESET_ALL}")
                
                for i, article_file in enumerate(articles, 1):
                    article_path = os.path.join(target_dir, article_file)
                    
                    try:
                        # Lire le fichier de l'article
                        with open(article_path, 'r', encoding='utf-8') as f:
                            article_data = json.load(f)
                        
                        # Reconstruire l'article
                        reconstructed_data = reconstructor.reconstruct_article(article_data)
                        
                        # Sauvegarder dans les formats demandés
                        reconstructor.save_reconstructed_article(reconstructed_data, output_format)
                        
                        success_count += 1
                        print(f"  {i}/{len(articles)} - {Fore.GREEN}Succès:{Style.RESET_ALL} {article_file}")
                    
                    except Exception as e:
                        error_count += 1
                        print(f"  {i}/{len(articles)} - {Fore.RED}Erreur:{Style.RESET_ALL} {article_file} - {e}")
                
                print(f"\n{Fore.GREEN}Reconstruction terminée:{Style.RESET_ALL}")
                print(f"  - Articles traités avec succès: {success_count}")
                print(f"  - Articles en erreur: {error_count}")
                print(f"  - Répertoire de sortie: {output_dir}")
            
            except Exception as e:
                print(f"\n{Fore.RED}Erreur lors de la reconstruction: {e}{Style.RESET_ALL}")
        
        input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
    
    except ImportError as e:
        print(f"{Fore.RED}Les modules de reconstruction ne sont pas disponibles: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Veuillez vérifier l'installation des modules de reconstruction.{Style.RESET_ALL}")
        time.sleep(2)
        return
    except Exception as e:
        print(f"\n{Fore.RED}Erreur générale: {e}{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")

def batch_processing_menu(config):
    """Menu pour le traitement par lots à grande échelle."""
    print_header()
    
    try:
        choice = print_menu("Traitement par Lots", [
            "Traiter par catégories",
            "Traiter les articles les plus consultés",
            "Traiter des articles aléatoires",
            "Importer une liste d'articles",
            "Reprendre un traitement interrompu",
            "Consulter les checkpoints sauvegardés",
            "Options avancées du traitement par lots"
        ])
        
        if choice == "0":
            return
        elif choice == "1":
            # Traitement par catégories
            category = get_user_input("Catégorie à traiter (ex: science, history, geography)")
            count = int(get_user_input("Nombre d'articles à traiter", "50"))
            
            # Options de langues
            source_languages = config['languages']['source']
            target_languages = config['languages']['target']
            
            print(f"\n{Fore.CYAN}Langue source:{Style.RESET_ALL}")
            for i, lang in enumerate(source_languages, 1):
                print(f"  {i}. {lang}")
            
            source_idx = int(get_user_input("Choisissez la langue source (numéro)", "1")) - 1
            if source_idx < 0 or source_idx >= len(source_languages):
                source_idx = 0
            
            source_lang = source_languages[source_idx]
            
            print(f"\n{Fore.CYAN}Langue cible:{Style.RESET_ALL}")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
            if target_idx < 0 or target_idx >= len(target_languages):
                target_idx = 0
            
            target_lang = target_languages[target_idx]
            
            print(f"\n{Fore.CYAN}Mode de traitement:{Style.RESET_ALL}")
            print("  1. Séquentiel (un par un)")
            print("  2. Parallèle (plusieurs en même temps)")
            
            mode = get_user_input("Choisissez le mode de traitement (1-2)", "1")
            parallel = mode == "2"
            
            # Options d'adaptation linguistique
            print(f"\n{Fore.CYAN}Options avancées:{Style.RESET_ALL}")
            use_adaptation = get_user_input("Appliquer l'adaptation linguistique (o/n)", "o").lower() in ["o", "oui", "y", "yes"]
            reconstruct_after = get_user_input("Reconstruire les articles après traduction (o/n)", "o").lower() in ["o", "oui", "y", "yes"]
            
            # Confirmation
            print(f"\n{Fore.CYAN}Récapitulatif:{Style.RESET_ALL}")
            print(f"  Catégorie: {category}")
            print(f"  Nombre d'articles: {count}")
            print(f"  De: {source_lang} vers: {target_lang}")
            print(f"  Mode: {'Parallèle' if parallel else 'Séquentiel'}")
            print(f"  Adaptation linguistique: {'Oui' if use_adaptation else 'Non'}")
            print(f"  Reconstruction: {'Oui' if reconstruct_after else 'Non'}")
            
            confirm = get_user_input("Confirmer (o/n)", "o")
            
            if confirm.lower() in ["o", "oui", "y", "yes"]:
                # Exécuter le traitement par lots
                cmd = [
                    "python3", "scripts/batch_processor.py",
                    "--config", "config.yaml",
                    "--category", category,
                    "--count", str(count),
                    "--source-lang", source_lang,
                    "--target-lang", target_lang
                ]
                
                if parallel:
                    workers = int(get_user_input("Nombre de workers parallèles", "4"))
                    cmd.extend(["--parallel", "--workers", str(workers)])
                
                if use_adaptation:
                    cmd.append("--apply-adaptation")
                
                if reconstruct_after:
                    cmd.append("--reconstruct")
                
                execute_command(cmd)
        
        elif choice == "2":
            # Traiter les articles les plus consultés
            count = int(get_user_input("Nombre d'articles populaires à traiter", "50"))
            
            # Options de langues
            source_languages = config['languages']['source']
            target_languages = config['languages']['target']
            
            print(f"\n{Fore.CYAN}Langue source:{Style.RESET_ALL}")
            for i, lang in enumerate(source_languages, 1):
                print(f"  {i}. {lang}")
            
            source_idx = int(get_user_input("Choisissez la langue source (numéro)", "1")) - 1
            if source_idx < 0 or source_idx >= len(source_languages):
                source_idx = 0
            
            source_lang = source_languages[source_idx]
            
            print(f"\n{Fore.CYAN}Langue cible:{Style.RESET_ALL}")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
            if target_idx < 0 or target_idx >= len(target_languages):
                target_idx = 0
            
            target_lang = target_languages[target_idx]
            
            # Options d'adaptation linguistique
            print(f"\n{Fore.CYAN}Options avancées:{Style.RESET_ALL}")
            use_adaptation = get_user_input("Appliquer l'adaptation linguistique (o/n)", "o").lower() in ["o", "oui", "y", "yes"]
            reconstruct_after = get_user_input("Reconstruire les articles après traduction (o/n)", "o").lower() in ["o", "oui", "y", "yes"]
            parallel = get_user_input("Traitement parallèle (o/n)", "o").lower() in ["o", "oui", "y", "yes"]
            
            # Confirmation
            print(f"\n{Fore.CYAN}Récapitulatif:{Style.RESET_ALL}")
            print(f"  Articles populaires: {count}")
            print(f"  De: {source_lang} vers: {target_lang}")
            print(f"  Mode: {'Parallèle' if parallel else 'Séquentiel'}")
            print(f"  Adaptation linguistique: {'Oui' if use_adaptation else 'Non'}")
            print(f"  Reconstruction: {'Oui' if reconstruct_after else 'Non'}")
            
            confirm = get_user_input("Confirmer (o/n)", "o")
            
            if confirm.lower() in ["o", "oui", "y", "yes"]:
                cmd = [
                    "python3", "scripts/batch_processor.py",
                    "--config", "config.yaml",
                    "--popular",
                    "--count", str(count),
                    "--source-lang", source_lang,
                    "--target-lang", target_lang
                ]
                
                if parallel:
                    workers = int(get_user_input("Nombre de workers parallèles", "4"))
                    cmd.extend(["--parallel", "--workers", str(workers)])
                
                if use_adaptation:
                    cmd.append("--apply-adaptation")
                
                if reconstruct_after:
                    cmd.append("--reconstruct")
                
                execute_command(cmd)
        
        elif choice == "3":
            # Traiter des articles aléatoires
            count = int(get_user_input("Nombre d'articles aléatoires à traiter", "20"))
            
            # Options de langues
            source_languages = config['languages']['source']
            target_languages = config['languages']['target']
            
            print(f"\n{Fore.CYAN}Langue source:{Style.RESET_ALL}")
            for i, lang in enumerate(source_languages, 1):
                print(f"  {i}. {lang}")
            
            source_idx = int(get_user_input("Choisissez la langue source (numéro)", "1")) - 1
            if source_idx < 0 or source_idx >= len(source_languages):
                source_idx = 0
            
            source_lang = source_languages[source_idx]
            
            print(f"\n{Fore.CYAN}Langue cible:{Style.RESET_ALL}")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
            if target_idx < 0 or target_idx >= len(target_languages):
                target_idx = 0
            
            target_lang = target_languages[target_idx]
            
            # Options d'adaptation linguistique
            print(f"\n{Fore.CYAN}Options avancées:{Style.RESET_ALL}")
            use_adaptation = get_user_input("Appliquer l'adaptation linguistique (o/n)", "o").lower() in ["o", "oui", "y", "yes"]
            reconstruct_after = get_user_input("Reconstruire les articles après traduction (o/n)", "o").lower() in ["o", "oui", "y", "yes"]
            parallel = get_user_input("Traitement parallèle (o/n)", "o").lower() in ["o", "oui", "y", "yes"]
            
            # Confirmation
            print(f"\n{Fore.CYAN}Récapitulatif:{Style.RESET_ALL}")
            print(f"  Articles aléatoires: {count}")
            print(f"  De: {source_lang} vers: {target_lang}")
            print(f"  Mode: {'Parallèle' if parallel else 'Séquentiel'}")
            print(f"  Adaptation linguistique: {'Oui' if use_adaptation else 'Non'}")
            print(f"  Reconstruction: {'Oui' if reconstruct_after else 'Non'}")
            
            confirm = get_user_input("Confirmer (o/n)", "o")
            
            if confirm.lower() in ["o", "oui", "y", "yes"]:
                cmd = [
                    "python3", "scripts/batch_processor.py",
                    "--config", "config.yaml",
                    "--random",
                    "--count", str(count),
                    "--source-lang", source_lang,
                    "--target-lang", target_lang
                ]
                
                if parallel:
                    workers = int(get_user_input("Nombre de workers parallèles", "4"))
                    cmd.extend(["--parallel", "--workers", str(workers)])
                
                if use_adaptation:
                    cmd.append("--apply-adaptation")
                
                if reconstruct_after:
                    cmd.append("--reconstruct")
                
                execute_command(cmd)
        
        elif choice == "4":
            # Importer une liste d'articles
            list_file = get_user_input("Chemin vers le fichier de liste d'articles")
            
            if not os.path.exists(list_file):
                print(f"{Fore.RED}Le fichier n'existe pas: {list_file}{Style.RESET_ALL}")
                time.sleep(1.5)
                return
            
            # Options de langues
            source_languages = config['languages']['source']
            target_languages = config['languages']['target']
            
            print(f"\n{Fore.CYAN}Langue source:{Style.RESET_ALL}")
            for i, lang in enumerate(source_languages, 1):
                print(f"  {i}. {lang}")
            
            source_idx = int(get_user_input("Choisissez la langue source (numéro)", "1")) - 1
            if source_idx < 0 or source_idx >= len(source_languages):
                source_idx = 0
            
            source_lang = source_languages[source_idx]
            
            print(f"\n{Fore.CYAN}Langue cible:{Style.RESET_ALL}")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
            if target_idx < 0 or target_idx >= len(target_languages):
                target_idx = 0
            
            target_lang = target_languages[target_idx]
            
            # Options d'adaptation linguistique
            print(f"\n{Fore.CYAN}Options avancées:{Style.RESET_ALL}")
            use_adaptation = get_user_input("Appliquer l'adaptation linguistique (o/n)", "o").lower() in ["o", "oui", "y", "yes"]
            reconstruct_after = get_user_input("Reconstruire les articles après traduction (o/n)", "o").lower() in ["o", "oui", "y", "yes"]
            parallel = get_user_input("Traitement parallèle (o/n)", "o").lower() in ["o", "oui", "y", "yes"]
            
            # Confirmation
            print(f"\n{Fore.CYAN}Récapitulatif:{Style.RESET_ALL}")
            print(f"  Fichier de liste: {list_file}")
            print(f"  De: {source_lang} vers: {target_lang}")
            print(f"  Mode: {'Parallèle' if parallel else 'Séquentiel'}")
            print(f"  Adaptation linguistique: {'Oui' if use_adaptation else 'Non'}")
            print(f"  Reconstruction: {'Oui' if reconstruct_after else 'Non'}")
            
            confirm = get_user_input("Confirmer (o/n)", "o")
            
            if confirm.lower() in ["o", "oui", "y", "yes"]:
                cmd = [
                    "python3", "scripts/batch_processor.py",
                    "--config", "config.yaml",
                    "--list-file", list_file,
                    "--source-lang", source_lang,
                    "--target-lang", target_lang
                ]
                
                if parallel:
                    workers = int(get_user_input("Nombre de workers parallèles", "4"))
                    cmd.extend(["--parallel", "--workers", str(workers)])
                
                if use_adaptation:
                    cmd.append("--apply-adaptation")
                
                if reconstruct_after:
                    cmd.append("--reconstruct")
                
                execute_command(cmd)
        
        elif choice == "5":
            # Reprendre un traitement interrompu
            checkpoint_dir = os.path.join(config['paths'].get('data_dir', 'data'), 'checkpoints')
            
            if not os.path.exists(checkpoint_dir):
                print(f"{Fore.RED}Répertoire de checkpoints introuvable: {checkpoint_dir}{Style.RESET_ALL}")
                time.sleep(1.5)
                return
            
            # Liste des checkpoints disponibles
            checkpoints = [f for f in os.listdir(checkpoint_dir) if f.startswith('checkpoint_') and f.endswith('.json')]
            
            if not checkpoints:
                print(f"{Fore.RED}Aucun checkpoint trouvé dans {checkpoint_dir}{Style.RESET_ALL}")
                time.sleep(1.5)
                return
            
            # Trier par date (plus récent d'abord)
            checkpoints.sort(reverse=True)
            
            print(f"\n{Fore.CYAN}Checkpoints disponibles:{Style.RESET_ALL}")
            for i, ckpt in enumerate(checkpoints, 1):
                # Extraire des informations du nom du fichier
                parts = ckpt.replace('checkpoint_', '').replace('.json', '').split('_')
                
                if len(parts) >= 3:
                    src_lang = parts[0]
                    tgt_lang = parts[1]
                    date_str = '_'.join(parts[2:])
                    print(f"  {i}. {src_lang} → {tgt_lang}, {date_str}")
                else:
                    print(f"  {i}. {ckpt}")
            
            checkpoint_idx = int(get_user_input("Choisissez le checkpoint à reprendre (numéro)", "1")) - 1
            if checkpoint_idx < 0 or checkpoint_idx >= len(checkpoints):
                checkpoint_idx = 0
            
            checkpoint_file = os.path.join(checkpoint_dir, checkpoints[checkpoint_idx])
            
            # Options d'adaptation linguistique
            print(f"\n{Fore.CYAN}Options avancées:{Style.RESET_ALL}")
            use_adaptation = get_user_input("Appliquer l'adaptation linguistique (o/n)", "o").lower() in ["o", "oui", "y", "yes"]
            reconstruct_after = get_user_input("Reconstruire les articles après traduction (o/n)", "o").lower() in ["o", "oui", "y", "yes"]
            parallel = get_user_input("Traitement parallèle (o/n)", "o").lower() in ["o", "oui", "y", "yes"]
            
            # Confirmation
            print(f"\n{Fore.CYAN}Récapitulatif:{Style.RESET_ALL}")
            print(f"  Checkpoint: {checkpoints[checkpoint_idx]}")
            print(f"  Mode: {'Parallèle' if parallel else 'Séquentiel'}")
            print(f"  Adaptation linguistique: {'Oui' if use_adaptation else 'Non'}")
            print(f"  Reconstruction: {'Oui' if reconstruct_after else 'Non'}")
            
            confirm = get_user_input("Confirmer (o/n)", "o")
            
            if confirm.lower() in ["o", "oui", "y", "yes"]:
                cmd = [
                    "python3", "scripts/batch_processor.py",
                    "--config", "config.yaml",
                    "--resume", checkpoint_file
                ]
                
                if parallel:
                    workers = int(get_user_input("Nombre de workers parallèles", "4"))
                    cmd.extend(["--parallel", "--workers", str(workers)])
                
                if use_adaptation:
                    cmd.append("--apply-adaptation")
                
                if reconstruct_after:
                    cmd.append("--reconstruct")
                
                execute_command(cmd)
        
        elif choice == "6":
            # Consulter les checkpoints sauvegardés
            checkpoint_dir = os.path.join(config['paths'].get('data_dir', 'data'), 'checkpoints')
            
            if not os.path.exists(checkpoint_dir):
                print(f"{Fore.RED}Répertoire de checkpoints introuvable: {checkpoint_dir}{Style.RESET_ALL}")
                time.sleep(1.5)
                return
            
            # Liste des checkpoints disponibles
            checkpoints = [f for f in os.listdir(checkpoint_dir) if f.startswith('checkpoint_') and f.endswith('.json')]
            
            if not checkpoints:
                print(f"{Fore.RED}Aucun checkpoint trouvé dans {checkpoint_dir}{Style.RESET_ALL}")
                time.sleep(1.5)
                return
            
            # Trier par date (plus récent d'abord)
            checkpoints.sort(reverse=True)
            
            print(f"\n{Fore.CYAN}Checkpoints disponibles:{Style.RESET_ALL}")
            for i, ckpt in enumerate(checkpoints, 1):
                # Extraire des informations du nom du fichier
                parts = ckpt.replace('checkpoint_', '').replace('.json', '').split('_')
                
                if len(parts) >= 3:
                    src_lang = parts[0]
                    tgt_lang = parts[1]
                    date_str = '_'.join(parts[2:])
                    print(f"  {i}. {src_lang} → {tgt_lang}, {date_str}")
                else:
                    print(f"  {i}. {ckpt}")
            
            checkpoint_idx = int(get_user_input("Choisissez le checkpoint à consulter (numéro)", "1")) - 1
            if checkpoint_idx < 0 or checkpoint_idx >= len(checkpoints):
                checkpoint_idx = 0
            
            checkpoint_file = os.path.join(checkpoint_dir, checkpoints[checkpoint_idx])
            
            # Afficher les détails du checkpoint
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    checkpoint_data = json.load(f)
                
                print(f"\n{Fore.GREEN}Détails du checkpoint:{Style.RESET_ALL}")
                print(f"  Type: {checkpoint_data.get('type', 'Inconnu')}")
                print(f"  Langue source: {checkpoint_data.get('source_lang', 'Inconnue')}")
                print(f"  Langue cible: {checkpoint_data.get('target_lang', 'Inconnue')}")
                print(f"  Date de création: {checkpoint_data.get('timestamp', 'Inconnue')}")
                
                # Afficher les statistiques
                total_articles = len(checkpoint_data.get('articles', []))
                processed = len(checkpoint_data.get('processed', []))
                failed = len(checkpoint_data.get('failed', []))
                remaining = total_articles - processed - failed
                
                print(f"\n{Fore.CYAN}Progression:{Style.RESET_ALL}")
                print(f"  Articles totaux: {total_articles}")
                print(f"  Articles traités: {processed} ({processed/total_articles*100:.1f}%)")
                print(f"  Articles en échec: {failed} ({failed/total_articles*100:.1f}%)")
                print(f"  Articles restants: {remaining} ({remaining/total_articles*100:.1f}%)")
                
                # Afficher le statut du traitement
                completed = checkpoint_data.get('completed', False)
                completion_time = checkpoint_data.get('completion_time', 'Inconnu')
                
                print(f"\n{Fore.CYAN}Statut:{Style.RESET_ALL}")
                if completed:
                    print(f"  {Fore.GREEN}Traitement terminé le {completion_time}{Style.RESET_ALL}")
                else:
                    print(f"  {Fore.YELLOW}Traitement en cours ou interrompu{Style.RESET_ALL}")
                
                # Option pour afficher la liste des articles
                show_articles = get_user_input("\nAfficher la liste des articles? (o/n)", "n")
                
                if show_articles.lower() in ["o", "oui", "y", "yes"]:
                    print(f"\n{Fore.CYAN}Articles à traiter:{Style.RESET_ALL}")
                    for i, article in enumerate(checkpoint_data.get('articles', [])[:10], 1):
                        print(f"  {i}. {article}")
                    
                    if len(checkpoint_data.get('articles', [])) > 10:
                        print(f"  ... et {len(checkpoint_data.get('articles', [])) - 10} autres")
                    
                    print(f"\n{Fore.CYAN}Articles traités:{Style.RESET_ALL}")
                    for i, article in enumerate(checkpoint_data.get('processed', [])[:10], 1):
                        print(f"  {i}. {article}")
                    
                    if len(checkpoint_data.get('processed', [])) > 10:
                        print(f"  ... et {len(checkpoint_data.get('processed', [])) - 10} autres")
                    
                    print(f"\n{Fore.CYAN}Articles en échec:{Style.RESET_ALL}")
                    for i, article in enumerate(checkpoint_data.get('failed', [])[:10], 1):
                        print(f"  {i}. {article}")
                    
                    if len(checkpoint_data.get('failed', [])) > 10:
                        print(f"  ... et {len(checkpoint_data.get('failed', [])) - 10} autres")
            
            except Exception as e:
                print(f"\n{Fore.RED}Erreur lors de la lecture du checkpoint: {e}{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
        
        elif choice == "7":
            # Options avancées du traitement par lots
            print(f"\n{Fore.CYAN}Options avancées du traitement par lots{Style.RESET_ALL}")
            print("Cette fonctionnalité permet de configurer des paramètres avancés pour le traitement par lots.")
            
            # Ajouter ou modifier le fichier batch_config.json
            batch_config_file = os.path.join(config['paths'].get('data_dir', 'data'), 'batch_config.json')
            
            # Charger la configuration existante ou créer une nouvelle
            batch_config = {}
            if os.path.exists(batch_config_file):
                try:
                    with open(batch_config_file, 'r', encoding='utf-8') as f:
                        batch_config = json.load(f)
                except Exception as e:
                    print(f"{Fore.RED}Erreur lors de la lecture de la configuration: {e}{Style.RESET_ALL}")
            
            # Options configurables
            print(f"\n{Fore.CYAN}Paramètres de traitement par lots:{Style.RESET_ALL}")
            
            # Nombre maximal de workers
            max_workers = int(get_user_input("Nombre maximal de workers pour le traitement parallèle", 
                                            str(batch_config.get('max_workers', 4))))
            
            # Délai entre les requêtes API
            rate_limit_delay = float(get_user_input("Délai entre les requêtes API (secondes)", 
                                                  str(batch_config.get('rate_limit_delay', 0.5))))
            
            # Nombre maximal de tentatives
            max_retries = int(get_user_input("Nombre maximal de tentatives en cas d'erreur", 
                                           str(batch_config.get('max_retries', 3))))
            
            # Intervalle de sauvegarde des checkpoints
            checkpoint_interval = int(get_user_input("Intervalle de sauvegarde des checkpoints (articles)", 
                                                   str(batch_config.get('checkpoint_interval', 5))))
            
            # Appliquer l'adaptation linguistique par défaut
            default_adaptation = get_user_input("Appliquer l'adaptation linguistique par défaut (o/n)", 
                                              "o" if batch_config.get('default_adaptation', True) else "n")
            default_adaptation = default_adaptation.lower() in ["o", "oui", "y", "yes"]
            
            # Reconstruire les articles par défaut
            default_reconstruction = get_user_input("Reconstruire les articles par défaut (o/n)", 
                                                  "o" if batch_config.get('default_reconstruction', True) else "n")
            default_reconstruction = default_reconstruction.lower() in ["o", "oui", "y", "yes"]
            
            # Formats d'exportation par défaut
            default_formats = batch_config.get('default_formats', ['json', 'txt'])
            formats_str = get_user_input("Formats d'exportation par défaut (json,txt,html,markdown)", 
                                       ",".join(default_formats))
            default_formats = [f.strip() for f in formats_str.split(",") if f.strip()]
            
            # Évaluation automatique
            auto_evaluate = get_user_input("Évaluer automatiquement les traductions (o/n)", 
                                         "o" if batch_config.get('auto_evaluate', False) else "n")
            auto_evaluate = auto_evaluate.lower() in ["o", "oui", "y", "yes"]
            
            # Métriques d'évaluation
            eval_metrics = batch_config.get('eval_metrics', ['bleu', 'meteor'])
            metrics_str = get_user_input("Métriques d'évaluation (bleu,meteor)", 
                                       ",".join(eval_metrics))
            eval_metrics = [m.strip() for m in metrics_str.split(",") if m.strip()]
            
            # Mettre à jour la configuration
            batch_config = {
                'max_workers': max_workers,
                'rate_limit_delay': rate_limit_delay,
                'max_retries': max_retries,
                'checkpoint_interval': checkpoint_interval,
                'default_adaptation': default_adaptation,
                'default_reconstruction': default_reconstruction,
                'default_formats': default_formats,
                'auto_evaluate': auto_evaluate,
                'eval_metrics': eval_metrics
            }
            
            # Enregistrer la configuration
            try:
                with open(batch_config_file, 'w', encoding='utf-8') as f:
                    json.dump(batch_config, f, ensure_ascii=False, indent=2)
                print(f"\n{Fore.GREEN}Configuration du traitement par lots enregistrée dans {batch_config_file}{Style.RESET_ALL}")
            except Exception as e:
                print(f"\n{Fore.RED}Erreur lors de l'enregistrement de la configuration: {e}{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
    
    except Exception as e:
        print(f"\n{Fore.RED}Erreur lors du traitement par lots: {e}{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")

def manage_language_adaptation(config):
    """Menu pour gérer l'adaptation linguistique pour les langues africaines."""
    
    from src.adaptation.language_adapter import LanguageAdapter
    adapter = LanguageAdapter()
    
    while True:
        print_header()
        
        choice = print_menu("Adaptation Linguistique", [
            "Normalisation orthographique",
            "Traitement des particularités grammaticales",
            "Gestion des entités nommées",
            "Tester l'adaptation complète sur un texte",
            "Ajouter une entité nommée personnalisée",
            "Voir les caractéristiques linguistiques"
        ])
        
        if choice == "0":
            break
        elif choice == "1":
            # Normalisation orthographique
            print(f"\n{Fore.CYAN}Normalisation orthographique{Style.RESET_ALL}")
            
            # Options de langues
            target_languages = config['languages']['target']
            
            print(f"\n{Fore.CYAN}Langue cible:{Style.RESET_ALL}")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
            if target_idx < 0 or target_idx >= len(target_languages):
                target_idx = 0
            
            target_lang = target_languages[target_idx]
            
            # Dialecte (optionnel)
            dialect = get_user_input("Dialecte spécifique (laisser vide si aucun)")
            
            # Texte à normaliser
            print(f"\n{Fore.CYAN}Entrez le texte à normaliser:{Style.RESET_ALL}")
            text = get_user_input("Texte")
            
            if not text:
                print(f"{Fore.RED}Aucun texte fourni.{Style.RESET_ALL}")
                time.sleep(1)
                continue
            
            # Normaliser le texte
            normalized_text = adapter.orthographic.normalize_text(text, target_lang, dialect)
            
            print(f"\n{Fore.GREEN}Texte normalisé:{Style.RESET_ALL}")
            print(f"{normalized_text}")
            
            input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
        
        elif choice == "2":
            # Traitement des particularités grammaticales
            print(f"\n{Fore.CYAN}Traitement des particularités grammaticales{Style.RESET_ALL}")
            
            # Options de langues
            target_languages = config['languages']['target']
            
            print(f"\n{Fore.CYAN}Langue cible:{Style.RESET_ALL}")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
            if target_idx < 0 or target_idx >= len(target_languages):
                target_idx = 0
            
            target_lang = target_languages[target_idx]
            
            # Type d'opération grammaticale
            print(f"\n{Fore.CYAN}Type d'opération:{Style.RESET_ALL}")
            print("  1. Conjugaison de verbe")
            print("  2. Construction de phrase")
            print("  3. Pluriel d'un nom")
            print("  4. Description avec adjectif")
            print("  5. Négation")
            
            grammar_op = get_user_input("Choisissez l'opération (numéro)", "1")
            
            if grammar_op == "1":
                # Conjugaison
                verb = get_user_input("Verbe à conjuguer")
                tense = get_user_input("Temps verbal (present, past, future)", "present")
                subject = get_user_input("Sujet (optionnel)")
                
                result = adapter.conjugate_verb(verb, target_lang, tense, subject)
                print(f"\n{Fore.GREEN}Résultat: {result}{Style.RESET_ALL}")
            
            elif grammar_op == "2":
                # Construction de phrase
                subject = get_user_input("Sujet")
                verb = get_user_input("Verbe")
                object = get_user_input("Objet")
                tense = get_user_input("Temps verbal (present, past, future)", "present")
                
                result = adapter.build_phrase(subject, verb, object, target_lang, tense)
                print(f"\n{Fore.GREEN}Résultat: {result}{Style.RESET_ALL}")
            
            elif grammar_op == "3":
                # Pluriel
                noun = get_user_input("Nom")
                is_plural = get_user_input("Mettre au pluriel (o/n)", "o").lower() in ["o", "oui", "y", "yes"]
                
                result = adapter.get_noun_form(noun, target_lang, is_plural)
                print(f"\n{Fore.GREEN}Résultat: {result}{Style.RESET_ALL}")
            
            elif grammar_op == "4":
                # Description avec adjectif
                noun = get_user_input("Nom")
                adjective = get_user_input("Adjectif")
                
                result = adapter.describe_noun(noun, adjective, target_lang)
                print(f"\n{Fore.GREEN}Résultat: {result}{Style.RESET_ALL}")
            
            elif grammar_op == "5":
                # Négation
                sentence = get_user_input("Phrase à nier")
                
                result = adapter.negate_sentence(sentence, target_lang)
                print(f"\n{Fore.GREEN}Résultat: {result}{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
        
        elif choice == "3":
            # Gestion des entités nommées
            print(f"\n{Fore.CYAN}Gestion des entités nommées{Style.RESET_ALL}")
            
            # Options de langues
            target_languages = config['languages']['target']
            
            print(f"\n{Fore.CYAN}Langue cible:{Style.RESET_ALL}")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
            if target_idx < 0 or target_idx >= len(target_languages):
                target_idx = 0
            
            target_lang = target_languages[target_idx]
            
            # Opérations sur les entités
            print(f"\n{Fore.CYAN}Opération:{Style.RESET_ALL}")
            print("  1. Détecter les entités dans un texte")
            print("  2. Remplacer les entités dans un texte")
            print("  3. Translittérer un nom propre")
            
            entity_op = get_user_input("Choisissez l'opération (numéro)", "1")
            
            if entity_op == "1":
                # Détection
                text = get_user_input("Texte à analyser")
                
                entities = adapter.detect_entities_in_text(text, target_lang)
                
                print(f"\n{Fore.GREEN}Entités détectées:{Style.RESET_ALL}")
                if entities:
                    for i, entity in enumerate(entities, 1):
                        print(f"  {i}. {entity['text']} ({entity['type']}) -> {entity['local']}")
                else:
                    print("  Aucune entité détectée.")
            
            elif entity_op == "2":
                # Remplacement
                text = get_user_input("Texte à traiter")
                use_local = get_user_input("Utiliser les formes locales (o/n)", "o").lower() in ["o", "oui", "y", "yes"]
                
                result = adapter.entities.replace_entities(text, target_lang, use_local)
                print(f"\n{Fore.GREEN}Résultat:{Style.RESET_ALL}")
                print(f"{result}")
            
            elif entity_op == "3":
                # Translittération
                name = get_user_input("Nom à translittérer")
                
                result = adapter.transliterate_name(name, target_lang)
                print(f"\n{Fore.GREEN}Résultat: {result}{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
        
        elif choice == "4":
            # Tester l'adaptation complète
            print(f"\n{Fore.CYAN}Adaptation complète d'un texte{Style.RESET_ALL}")
            
            # Options de langues
            target_languages = config['languages']['target']
            
            print(f"\n{Fore.CYAN}Langue cible:{Style.RESET_ALL}")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
            if target_idx < 0 or target_idx >= len(target_languages):
                target_idx = 0
            
            target_lang = target_languages[target_idx]
            
            # Dialecte (optionnel)
            dialect = get_user_input("Dialecte spécifique (laisser vide si aucun)")
            
            # Options d'adaptation
            use_entities = get_user_input("Utiliser les entités locales (o/n)", "o").lower() in ["o", "oui", "y", "yes"]
            apply_tones = get_user_input("Appliquer les tons (o/n)", "n").lower() in ["o", "oui", "y", "yes"]
            
            # Texte à adapter
            print(f"\n{Fore.CYAN}Entrez le texte à adapter:{Style.RESET_ALL}")
            text = get_user_input("Texte")
            
            if not text:
                print(f"{Fore.RED}Aucun texte fourni.{Style.RESET_ALL}")
                time.sleep(1)
                continue
            
            # Adapter le texte
            adapted_text = adapter.adapt_text(text, target_lang, dialect, use_entities, apply_tones)
            
            print(f"\n{Fore.GREEN}Texte adapté:{Style.RESET_ALL}")
            print(f"{adapted_text}")
            
            input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
        
        elif choice == "5":
            # Ajouter une entité personnalisée
            print(f"\n{Fore.CYAN}Ajout d'une entité nommée personnalisée{Style.RESET_ALL}")
            
            # Options de langues
            target_languages = config['languages']['target']
            
            print(f"\n{Fore.CYAN}Langue cible:{Style.RESET_ALL}")
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            
            target_idx = int(get_user_input("Choisissez la langue cible (numéro)", "1")) - 1
            if target_idx < 0 or target_idx >= len(target_languages):
                target_idx = 0
            
            target_lang = target_languages[target_idx]
            
            # Catégorie
            print(f"\n{Fore.CYAN}Catégorie:{Style.RESET_ALL}")
            print("  1. Personnes (people)")
            print("  2. Lieux (places)")
            print("  3. Organisations (organizations)")
            print("  4. Termes culturels (cultural_terms)")
            print("  5. Titres (titles)")
            
            cat_choice = get_user_input("Choisissez la catégorie (numéro)", "1")
            
            cat_map = {
                "1": "people",
                "2": "places",
                "3": "organizations",
                "4": "cultural_terms",
                "5": "titles"
            }
            
            category = cat_map.get(cat_choice, "people")
            
            # Information sur l'entité
            original = get_user_input("Forme originale")
            local = get_user_input("Forme locale/adaptée")
            
            if not original or not local:
                print(f"{Fore.RED}Les deux formes sont requises.{Style.RESET_ALL}")
                time.sleep(1)
                continue
            
            # Ajouter l'entité
            success = adapter.add_custom_entity(category, original, local, target_lang)
            
            if success:
                print(f"\n{Fore.GREEN}Entité ajoutée avec succès.{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.RED}Erreur lors de l'ajout de l'entité.{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
        
        elif choice == "6":
            # Voir les caractéristiques linguistiques
            print(f"\n{Fore.CYAN}Caractéristiques linguistiques{Style.RESET_ALL}")
            
            languages = adapter.list_supported_languages()
            
            for code, info in languages.items():
                print(f"\n{Fore.GREEN}{info['name']} ({code}):{Style.RESET_ALL}")
                print(f"  Régions: {', '.join(info['regions'])}")
                print(f"  Code ISO: {info['iso_code']}")
                print(f"  Script: {info['script']}")
                print(f"  Caractéristiques: {', '.join(info['features'])}")
            
            input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")

def evaluate_translations(config):
    """Menu pour évaluer les traductions existantes."""
    print_header()
    
    # Vérifier si le module d'évaluation est disponible
    try:
        from src.evaluation.evaluate_translation import TranslationEvaluator
        evaluation_available = True
    except ImportError:
        print(f"{Fore.RED}Le module d'évaluation n'est pas encore implémenté.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Cette fonctionnalité sera disponible prochainement.{Style.RESET_ALL}")
        evaluation_available = False
        time.sleep(2)
        return
    
    if evaluation_available:
        try:
            # Liste des articles traduits
            translated_dir = config['paths']['articles_translated']
            
            # Vérifier si le répertoire existe
            if not os.path.exists(translated_dir):
                print(f"{Fore.RED}Répertoire des traductions non trouvé: {translated_dir}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Veuillez d'abord traduire quelques articles.{Style.RESET_ALL}")
                time.sleep(2)
                return
            
            # Trouver les langues cibles disponibles
            available_langs = []
            for item in os.listdir(translated_dir):
                if os.path.isdir(os.path.join(translated_dir, item)) and not item.endswith("_txt") and item != "reconstructed":
                    available_langs.append(item)
            
            if not available_langs:
                print(f"{Fore.RED}Aucun article traduit trouvé.{Style.RESET_ALL}")
                time.sleep(2)
                return
            
            print(f"\n{Fore.CYAN}Langues disponibles pour l'évaluation:{Style.RESET_ALL}")
            for i, lang in enumerate(available_langs, 1):
                print(f"  {i}. {lang}")
            
            lang_idx = int(get_user_input("Choisissez la langue à évaluer (numéro)", "1")) - 1
            if lang_idx < 0 or lang_idx >= len(available_langs):
                lang_idx = 0
            
            target_lang = available_langs[lang_idx]
            target_dir = os.path.join(translated_dir, target_lang)
            
            # Liste des articles disponibles
            articles = [f for f in os.listdir(target_dir) if f.endswith('.json')]
            
            if not articles:
                print(f"{Fore.RED}Aucun article traduit trouvé pour la langue {target_lang}.{Style.RESET_ALL}")
                time.sleep(2)
                return
            
            print(f"\n{Fore.CYAN}Articles disponibles pour l'évaluation:{Style.RESET_ALL}")
            for i, article in enumerate(articles, 1):
                print(f"  {i}. {article.replace('.json', '')}")
            
            article_idx = int(get_user_input("Choisissez l'article à évaluer (numéro)", "1")) - 1
            if article_idx < 0 or article_idx >= len(articles):
                article_idx = 0
            
            article_file = articles[article_idx]
            article_path = os.path.join(target_dir, article_file)
            
            # Options d'évaluation
            print(f"\n{Fore.CYAN}Métriques d'évaluation:{Style.RESET_ALL}")
            print("  1. BLEU (BiLingual Evaluation Understudy)")
            print("  2. METEOR (Metric for Evaluation of Translation with Explicit Ordering)")
            print("  3. Toutes les métriques")
            
            metrics_choice = get_user_input("Choisissez les métriques à utiliser (ex: 1,2 ou 3 pour toutes)", "3")
            
            metrics = []
            if "3" in metrics_choice:
                metrics = ["bleu", "meteor"]
            else:
                if "1" in metrics_choice:
                    metrics.append("bleu")
                if "2" in metrics_choice:
                    metrics.append("meteor")
            
            # Exécuter l'évaluation
            print(f"\n{Fore.CYAN}Évaluation de l'article {article_file.replace('.json', '')} en {target_lang}...{Style.RESET_ALL}")
            
            try:
                output_file = f"evaluation_{article_file.replace('.json', '')}.json"
                output_path = os.path.join("data", "evaluations", output_file)
                
                # Créer le répertoire si nécessaire
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Initialiser l'évaluateur et évaluer l'article
                evaluator = TranslationEvaluator(metrics)
                results = evaluator.evaluate_translated_article(article_path, output_path)
                
                # Afficher les résultats
                if 'error' in results:
                    print(f"\n{Fore.RED}Erreur lors de l'évaluation: {results['error']}{Style.RESET_ALL}")
                else:
                    print(f"\n{Fore.GREEN}Résultats de l'évaluation:{Style.RESET_ALL}")
                    print(f"  Segments évalués: {results.get('segment_count', 0)}")
                    
                    print(f"\n{Fore.CYAN}Scores:{Style.RESET_ALL}")
                    for metric, score in results.get('scores', {}).items():
                        print(f"  {metric.upper()}: {score:.4f}")
                    
                    if 'article' in results:
                        print(f"\n{Fore.CYAN}Article: {results['article']['title']}{Style.RESET_ALL}")
                        print(f"  Original: {results['article']['original_title']}")
                        print(f"  Langues: {results['article']['source_language']} → {results['article']['target_language']}")
                    
                    print(f"\n{Fore.GREEN}Résultats complets sauvegardés dans: {output_path}{Style.RESET_ALL}")
                
                # Option pour visualiser des exemples
                if 'scores' in results and results.get('segment_count', 0) > 0:
                    view_examples = get_user_input("\nVoulez-vous voir des exemples de segments évalués? (o/n)", "o")
                    
                    if view_examples.lower() in ["o", "oui", "y", "yes"]:
                        # Charger l'article pour extraire des exemples
                        with open(article_path, 'r', encoding='utf-8') as f:
                            article_data = json.load(f)
                        
                        # Extraire quelques segments pour affichage
                        examples = []
                        count = 0
                        max_examples = 5
                        
                        for section in article_data.get('translated_sections', []):
                            original_segments = section.get('original_segments', [])
                            translated_segments = section.get('segments', [])
                            
                            for orig, trans in zip(original_segments, translated_segments):
                                if orig and trans and not trans.startswith('[ERREUR'):
                                    examples.append((orig, trans))
                                    count += 1
                                    
                                    if count >= max_examples:
                                        break
                            
                            if count >= max_examples:
                                break
                        
                        # Afficher les exemples
                        print(f"\n{Fore.CYAN}Exemples de segments évalués:{Style.RESET_ALL}")
                        for i, (original, translated) in enumerate(examples, 1):
                            print(f"\n{Fore.YELLOW}Exemple {i}:{Style.RESET_ALL}")
                            print(f"  {Fore.CYAN}Original:{Style.RESET_ALL} {original}")
                            print(f"  {Fore.GREEN}Traduit:{Style.RESET_ALL} {translated}")
            
            except Exception as e:
                print(f"\n{Fore.RED}Erreur lors de l'évaluation: {e}{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")
        except Exception as e:
            print(f"\n{Fore.RED}Erreur générale: {e}{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Appuyez sur Entrée pour continuer...{Style.RESET_ALL}")

def ensure_directories_exist(config):
    """S'assure que tous les répertoires nécessaires existent"""
    for path in config['paths'].values():
        if isinstance(path, str):
            os.makedirs(path, exist_ok=True)
    
    # Répertoires supplémentaires
    os.makedirs(os.path.join(config['paths'].get('data_dir', 'data'), 'temp'), exist_ok=True)
    os.makedirs(os.path.join(config['paths'].get('data_dir', 'data'), 'evaluations'), exist_ok=True)

def init_glossary_db(config):
    """Initialise la base de données du glossaire si elle n'existe pas déjà"""
    glossary_db = config['paths'].get('glossary_db')
    if not os.path.exists(glossary_db):
        from src.database.schema import create_database_schema
        create_database_schema(glossary_db)
        logger.info(f"Base de données du glossaire créée: {glossary_db}")

def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(description="Interface interactive pour WikiTranslateAI")
    parser.add_argument('--config', type=str, default='config.yaml', help="Chemin vers le fichier de configuration")
    parser.add_argument('--batch', action='store_true', help="Mode traitement par lots")
    parser.add_argument('--count', type=int, default=10, help="Nombre d'articles à traiter en mode batch")
    
    args = parser.parse_args()
    
    # Charger la configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"{Fore.RED}Erreur lors du chargement de la configuration: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Création d'une configuration par défaut...{Style.RESET_ALL}")
        from src.utils.config import create_config_file
        create_config_file(args.config)
        config = load_config(args.config)
    
    

    # Mode interactif
    while True:
        print_header()
        
        choice = print_menu("Menu Principal", [
            "Extraire et traduire un article spécifique",
            "Rechercher et traduire des articles",
            "Traduire des articles aléatoires",
            "Gérer le glossaire",
            "Gérer les ressources linguistiques",
            "Adaptation linguistique pour langues africaines",
            "Reconstruction et exportation d'articles",
            "Évaluer les traductions existantes",
            "Visualiser les statistiques",
            "Traitement par lots (grande échelle)",
            "Configuration du système",
            "Aide",
            "Quitter"
        ])
        
        if choice == "1":
            extract_translate_article(config)
        elif choice == "2":
            search_translate_articles(config)
        elif choice == "3":
            random_translate_articles(config)
        elif choice == "4":
            manage_glossary(config)
        elif choice == "5":
            manage_linguistic_resources(config)
        elif choice == "6":
            manage_language_adaptation(config)
        elif choice == "7":
            reconstruct_articles(config)
        elif choice == "8":
            evaluate_translations(config)
        elif choice == "9":
            view_statistics(config)
        elif choice == "10":
            batch_processing_menu(config)
        elif choice == "11":
            system_configuration(config)
        elif choice == "12":
            show_help()
        elif choice == "13" or choice == "0":
            print(f"\n{Fore.GREEN}Au revoir!{Style.RESET_ALL}")
            break
        else:
            print(f"\n{Fore.RED}Option invalide. Veuillez réessayer.{Style.RESET_ALL}")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.RED}Programme interrompu par l'utilisateur.{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}Erreur non gérée: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)