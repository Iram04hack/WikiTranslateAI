#!/usr/bin/env python3
# src/reconstruction/format_handler.py

import os
import json
import logging
import markdown
import html
import re
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FormatHandler:
    """Classe pour gérer différents formats d'exportation d'articles"""
    
    def __init__(self, base_output_dir):
        """
        Initialise le gestionnaire de formats
        
        Args:
            base_output_dir: Répertoire de base pour les sorties
        """
        self.base_output_dir = base_output_dir
        os.makedirs(base_output_dir, exist_ok=True)
    
    def to_json(self, article_data, filename=None):
        """
        Convertit les données de l'article en JSON
        
        Args:
            article_data: Données de l'article
            filename: Nom du fichier de sortie (optionnel)
            
        Returns:
            Chemin du fichier sauvegardé
        """
        target_language = article_data.get('target_language', 'unknown')
        title = article_data.get('title', 'article')
        
        # Créer un nom de fichier sécurisé
        if not filename:
            safe_title = title.replace('/', '_').replace('\\', '_').replace(':', '_')
            filename = f"{safe_title}.json"
        
        # Répertoire spécifique à la langue
        lang_dir = os.path.join(self.base_output_dir, target_language)
        os.makedirs(lang_dir, exist_ok=True)
        
        output_path = os.path.join(lang_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(article_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Article exporté en JSON: {output_path}")
        return output_path
    
    def to_text(self, article_data, filename=None):
        """
        Convertit les données de l'article en texte brut
        
        Args:
            article_data: Données de l'article
            filename: Nom du fichier de sortie (optionnel)
            
        Returns:
            Chemin du fichier sauvegardé
        """
        target_language = article_data.get('target_language', 'unknown')
        title = article_data.get('title', 'article')
        original_title = article_data.get('original_title', '')
        content = article_data.get('article_content', '')
        
        # Créer un nom de fichier sécurisé
        if not filename:
            safe_title = title.replace('/', '_').replace('\\', '_').replace(':', '_')
            filename = f"{safe_title}.txt"
        
        # Répertoire spécifique à la langue
        txt_dir = os.path.join(self.base_output_dir, f"{target_language}_txt")
        os.makedirs(txt_dir, exist_ok=True)
        
        output_path = os.path.join(txt_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"Titre original: {original_title}\n")
            f.write(f"Titre traduit: {title}\n\n")
            f.write(content)
        
        logger.info(f"Article exporté en texte: {output_path}")
        return output_path
    
    def to_html(self, article_data, filename=None, template=None):
        """
        Convertit les données de l'article en HTML
        
        Args:
            article_data: Données de l'article
            filename: Nom du fichier de sortie (optionnel)
            template: Chemin vers un template HTML (optionnel)
            
        Returns:
            Chemin du fichier sauvegardé
        """
        target_language = article_data.get('target_language', 'unknown')
        title = article_data.get('title', 'article')
        original_title = article_data.get('original_title', '')
        content = article_data.get('article_content', '')
        
        # Créer un nom de fichier sécurisé
        if not filename:
            safe_title = title.replace('/', '_').replace('\\', '_').replace(':', '_')
            filename = f"{safe_title}.html"
        
        # Répertoire spécifique à la langue
        html_dir = os.path.join(self.base_output_dir, f"{target_language}_html")
        os.makedirs(html_dir, exist_ok=True)
        
        output_path = os.path.join(html_dir, filename)
        
        # Convertir le contenu Markdown en HTML
        md = markdown.Markdown(extensions=['tables', 'fenced_code'])
        html_content = md.convert(content)
        
        if template:
            try:
                with open(template, 'r', encoding='utf-8') as f:
                    template_content = f.read()
                
                # Remplacer les variables du template
                html_output = template_content.replace('{{title}}', html.escape(title))
                html_output = html_output.replace('{{original_title}}', html.escape(original_title))
                html_output = html_output.replace('{{content}}', html_content)
                html_output = html_output.replace('{{source_language}}', article_data.get('source_language', ''))
                html_output = html_output.replace('{{target_language}}', target_language)
            except Exception as e:
                logger.error(f"Erreur lors de l'utilisation du template HTML: {e}")
                # Utiliser le template par défaut
                html_output = self._default_html_template(article_data, html_content)
        else:
            # Utiliser le template par défaut
            html_output = self._default_html_template(article_data, html_content)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_output)
        
        logger.info(f"Article exporté en HTML: {output_path}")
        return output_path
    
    def to_markdown(self, article_data, filename=None):
        """
        Sauvegarde les données de l'article au format Markdown
        
        Args:
            article_data: Données de l'article
            filename: Nom du fichier de sortie (optionnel)
            
        Returns:
            Chemin du fichier sauvegardé
        """
        target_language = article_data.get('target_language', 'unknown')
        title = article_data.get('title', 'article')
        original_title = article_data.get('original_title', '')
        content = article_data.get('article_content', '')
        
        # Créer un nom de fichier sécurisé
        if not filename:
            safe_title = title.replace('/', '_').replace('\\', '_').replace(':', '_')
            filename = f"{safe_title}.md"
        
        # Répertoire spécifique à la langue
        md_dir = os.path.join(self.base_output_dir, f"{target_language}_md")
        os.makedirs(md_dir, exist_ok=True)
        
        output_path = os.path.join(md_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            f.write(f"*Titre original: {original_title}*\n\n")
            f.write(f"*Traduit de {article_data.get('source_language', '')} vers {target_language}*\n\n")
            f.write("---\n\n")
            f.write(content)
        
        logger.info(f"Article exporté en Markdown: {output_path}")
        return output_path
    
    def to_wikitext(self, article_data, filename=None):
        """
        Convertit les données de l'article en format Wikitext
        
        Args:
            article_data: Données de l'article
            filename: Nom du fichier de sortie (optionnel)
            
        Returns:
            Chemin du fichier sauvegardé
        """
        target_language = article_data.get('target_language', 'unknown')
        title = article_data.get('title', 'article')
        original_title = article_data.get('original_title', '')
        content = article_data.get('article_content', '')
        
        # Créer un nom de fichier sécurisé
        if not filename:
            safe_title = title.replace('/', '_').replace('\\', '_').replace(':', '_')
            filename = f"{safe_title}_wiki.txt"
        
        # Répertoire spécifique à la langue
        wiki_dir = os.path.join(self.base_output_dir, f"{target_language}_wiki")
        os.makedirs(wiki_dir, exist_ok=True)
        
        output_path = os.path.join(wiki_dir, filename)
        
        # Convertir le contenu Markdown en Wikitext
        wikitext = self._markdown_to_wikitext(content)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"= {title} =\n\n")
            f.write(f"''Titre original: {original_title}''\n\n")
            f.write(f"''Traduit de {article_data.get('source_language', '')} vers {target_language}''\n\n")
            f.write("----\n\n")
            f.write(wikitext)
        
        logger.info(f"Article exporté en Wikitext: {output_path}")
        return output_path
    
    def _default_html_template(self, article_data, html_content):
        """
        Génère un template HTML par défaut
        
        Args:
            article_data: Données de l'article
            html_content: Contenu HTML
            
        Returns:
            HTML complet
        """
        title = article_data.get('title', '')
        original_title = article_data.get('original_title', '')
        source_language = article_data.get('source_language', '')
        target_language = article_data.get('target_language', '')
        
        return f"""<!DOCTYPE html>
<html lang="{target_language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0 auto; max-width: 800px; padding: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
        h2, h3, h4, h5, h6 {{ color: #2c3e50; margin-top: 30px; }}
        p {{ margin-bottom: 20px; }}
        .metadata {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .original-title {{ color: #7f8c8d; font-style: italic; }}
        .translation-info {{ font-size: 0.9em; color: #7f8c8d; }}
        pre {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        code {{ font-family: monospace; background-color: #f1f1f1; padding: 2px 4px; border-radius: 4px; }}
        blockquote {{ border-left: 4px solid #eee; padding-left: 15px; color: #777; }}
        img {{ max-width: 100%; height: auto; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
    </style>
</head>
<body>
    <header>
        <h1>{html.escape(title)}</h1>
        <div class="metadata">
            <p class="original-title">Titre original: {html.escape(original_title)}</p>
            <p class="translation-info">Traduit de: {source_language} vers: {target_language}</p>
        </div>
    </header>
    <main>
        {html_content}
    </main>
    <footer>
        <hr>
        <p><small>Généré par WikiTranslateAI</small></p>
    </footer>
</body>
</html>
"""
    
    def _markdown_to_wikitext(self, markdown_content):
        """
        Convertit le contenu Markdown en Wikitext
        
        Args:
            markdown_content: Contenu Markdown
            
        Returns:
            Contenu Wikitext
        """
        # Convertir les titres (# Titre -> = Titre =)
        wikitext = markdown_content
        for i in range(6, 0, -1):
            markdown_pattern = r'^{0} (.+)$'.format('#' * i)
            wiki_equals = '=' * i
            wikitext = re.sub(markdown_pattern, f"{wiki_equals} \\1 {wiki_equals}", wikitext, flags=re.MULTILINE)
        
        # Convertir la mise en forme
        wikitext = re.sub(r'\*\*([^*]+)\*\*', r"'''\1'''", wikitext)  # **bold** -> '''bold'''
        wikitext = re.sub(r'\*([^*]+)\*', r"''\1''", wikitext)  # *italic* -> ''italic''
        wikitext = re.sub(r'`([^`]+)`', r"<code>\1</code>", wikitext)  # `code` -> <code>code</code>
        
        # Convertir les liens
        wikitext = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r"[\2 \1]", wikitext)  # [text](url) -> [url text]
        
        # Convertir les listes
        wikitext = re.sub(r'^\* (.+)$', r"* \1", wikitext, flags=re.MULTILINE)  # * item -> * item
        wikitext = re.sub(r'^\- (.+)$', r"* \1", wikitext, flags=re.MULTILINE)  # - item -> * item
        wikitext = re.sub(r'^(\d+)\. (.+)$', r"# \2", wikitext, flags=re.MULTILINE)  # 1. item -> # item
        
        return wikitext