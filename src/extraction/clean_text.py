# src/extraction/clean_text.py

import os
import re
import json
import logging
import argparse
from bs4 import BeautifulSoup
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WikiTextCleaner:
    """Classe pour nettoyer et normaliser les textes extraits de Wikipedia"""
    
    def __init__(self, output_dir=None):
        """
        Initialise le nettoyeur de texte
        
        Args:
            output_dir: Répertoire de sortie pour les textes nettoyés
        """
        self.output_dir = output_dir
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
    
    def clean_html(self, html_content):
        """
        Nettoie le contenu HTML d'un article Wikipedia
        
        Args:
            html_content: Contenu HTML brut
        
        Returns:
            Texte extrait et nettoyé
        """
        if not html_content:
            return ""
        
        # Parser le HTML
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Supprimer les éléments non désirés
        for element in soup.select(
            '.mw-editsection, .reference, .noprint, .mw-empty-elt, '
            '.mw-cite-backlink, .error, .mbox-image, .mbox-text'
        ):
            element.decompose()
        
        # Extraire le texte par sections
        sections = []
        
        # Traiter les titres de section et leurs contenus
        current_section = {"title": "Introduction", "level": 0, "content": ""}
        
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol']):
            if element.name.startswith('h') and element.get_text().strip():
                # Ajouter la section précédente si elle contient du texte
                if current_section["content"].strip():
                    sections.append(current_section)
                
                # Commencer une nouvelle section
                level = int(element.name[1])
                current_section = {
                    "title": element.get_text().strip(),
                    "level": level,
                    "content": ""
                }
            elif element.name == 'p':
                # Ajouter le paragraphe au contenu de la section courante
                text = element.get_text().strip()
                if text:
                    current_section["content"] += text + "\n\n"
            elif element.name in ['ul', 'ol']:
                # Traiter les listes
                list_text = ""
                for li in element.find_all('li', recursive=False):
                    item_text = li.get_text().strip()
                    if item_text:
                        list_text += f"• {item_text}\n"
                
                if list_text:
                    current_section["content"] += list_text + "\n"
        
        # Ajouter la dernière section
        if current_section["content"].strip():
            sections.append(current_section)
        
        return sections
    
    def clean_wikitext(self, wikitext_content):
        """
        Nettoie le contenu wikitext d'un article Wikipedia
        
        Args:
            wikitext_content: Contenu wikitext brut
        
        Returns:
            Texte nettoyé et structuré
        """
        if not wikitext_content:
            return []
        
        # Supprimer les références, templates et autres éléments non désirés
        text = re.sub(r'<ref[^>]*>.*?</ref>', '', wikitext_content, flags=re.DOTALL)
        text = re.sub(r'<ref[^/]*?/>', '', text)
        text = re.sub(r'\{\{[^\{\}]*?\}\}', '', text, flags=re.DOTALL)
        text = re.sub(r'\[\[File:[^\]]*\]\]', '', text)
        text = re.sub(r'\[\[Image:[^\]]*\]\]', '', text)
        
        # Extraire les sections
        sections = []
        lines = text.split('\n')
        current_section = {"title": "Introduction", "level": 0, "content": ""}
        content_buffer = []
        
        for line in lines:
            # Détecter les titres de section
            section_match = re.match(r'(={2,6})\s*([^=]+?)\s*\1', line)
            if section_match:
                # Ajouter la section précédente
                if content_buffer:
                    current_section["content"] = '\n'.join(content_buffer)
                    sections.append(current_section)
                    content_buffer = []
                
                # Créer une nouvelle section
                level = len(section_match.group(1)) - 1  # == est niveau 1, === est niveau 2, etc.
                title = section_match.group(2).strip()
                current_section = {"title": title, "level": level, "content": ""}
            elif line.strip() and not line.startswith('[[') and not line.startswith('{{'):
                # Ajouter la ligne au contenu de la section courante si ce n'est pas un lien ou un template
                content_buffer.append(line.strip())
        
        # Ajouter la dernière section
        if content_buffer:
            current_section["content"] = '\n'.join(content_buffer)
            sections.append(current_section)
        
        return sections
    
    def clean_article_file(self, input_file_path, prefer_html=True):
        """
        Nettoie un fichier d'article extrait
        
        Args:
            input_file_path: Chemin vers le fichier d'article JSON
            prefer_html: Préférer le HTML au wikitext si disponible
        
        Returns:
            Article nettoyé sous forme de dictionnaire
        """
        logger.info(f"Nettoyage de l'article: {input_file_path}")
        
        try:
            with open(input_file_path, 'r', encoding='utf-8') as f:
                article = json.load(f)
            
            metadata = article.get('metadata', {})
            title = metadata.get('title', os.path.basename(input_file_path).replace('.json', ''))
            
            # Nettoyer le contenu
            sections = []
            if prefer_html and article.get('html'):
                sections = self.clean_html(article['html'])
            elif article.get('wikitext'):
                sections = self.clean_wikitext(article['wikitext'])
            
            # Créer l'article nettoyé
            cleaned_article = {
                'title': title,
                'metadata': metadata,
                'sections': sections
            }
            
            # Sauvegarder si un répertoire de sortie est spécifié
            if self.output_dir:
                output_path = os.path.join(self.output_dir, os.path.basename(input_file_path))
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(cleaned_article, f, ensure_ascii=False, indent=2)
                logger.info(f"Article nettoyé sauvegardé: {output_path}")
            
            return cleaned_article
        
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage de l'article {input_file_path}: {e}")
            return None
    
    def clean_directory(self, input_dir, prefer_html=True):
        """
        Nettoie tous les articles dans un répertoire
        
        Args:
            input_dir: Répertoire contenant les articles JSON
            prefer_html: Préférer le HTML au wikitext si disponible
        
        Returns:
            Nombre d'articles nettoyés
        """
        count = 0
        for filename in os.listdir(input_dir):
            if filename.endswith('.json'):
                input_path = os.path.join(input_dir, filename)
                if self.clean_article_file(input_path, prefer_html):
                    count += 1
        
        logger.info(f"{count} articles nettoyés depuis {input_dir}")
        return count


def main():
    parser = argparse.ArgumentParser(description="Nettoyage d'articles Wikipedia")
    parser.add_argument('--input', type=str, required=True, 
                        help="Fichier article ou répertoire d'articles à nettoyer")
    parser.add_argument('--output-dir', type=str, default='data/articles_cleaned', 
                        help="Répertoire de sortie pour les articles nettoyés")
    parser.add_argument('--prefer-wikitext', action='store_true', 
                        help="Préférer le wikitext au HTML pour l'extraction du texte")
    
    args = parser.parse_args()
    
    cleaner = WikiTextCleaner(args.output_dir)
    
    if os.path.isdir(args.input):
        cleaner.clean_directory(args.input, not args.prefer_wikitext)
    elif os.path.isfile(args.input):
        cleaner.clean_article_file(args.input, not args.prefer_wikitext)
    else:
        parser.error(f"Le chemin d'entrée n'existe pas: {args.input}")

if __name__ == "__main__":
    main()