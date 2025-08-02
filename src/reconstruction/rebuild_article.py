#!/usr/bin/env python3
# src/reconstruction/rebuild_article.py

import os
import json
import logging
import argparse
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ArticleReconstructor:
    """Classe pour reconstruire les articles après traduction"""
    
    def __init__(self, output_dir=None):
        """
        Initialise le reconstructeur d'articles
        
        Args:
            output_dir: Répertoire de sortie pour les articles reconstruits
        """
        self.output_dir = output_dir
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
    
    def reconstruct_article(self, translated_data):
        """
        Reconstruit un article à partir des données traduites
        
        Args:
            translated_data: Données de l'article traduit
            
        Returns:
            Article reconstruit
        """
        title = translated_data.get('title', '')
        original_title = translated_data.get('original_title', '')
        metadata = translated_data.get('metadata', {})
        source_language = translated_data.get('source_language', '')
        target_language = translated_data.get('target_language', '')
        translated_sections = translated_data.get('translated_sections', [])
        
        # Créer la structure de l'article reconstruit
        reconstructed_article = {
            'title': title,
            'original_title': original_title,
            'metadata': metadata,
            'source_language': source_language,
            'target_language': target_language,
            'article_content': self._build_content(translated_sections),
            'sections_hierarchy': self._build_hierarchy(translated_sections),
            'original_to_translated_mapping': self._build_mapping(translated_sections)
        }
        
        return reconstructed_article
    
    def _build_content(self, sections):
        """
        Construit le contenu textuel complet de l'article
        
        Args:
            sections: Sections traduites
            
        Returns:
            Contenu textuel de l'article
        """
        content = []
        
        for section in sections:
            title = section.get('title', '')
            level = section.get('level', 0)
            segments = section.get('segments', [])
            
            # Ajouter le titre de section avec le bon niveau de titre
            if title:
                content.append('#' * (level + 1) + ' ' + title)
                content.append('')  # Ligne vide après le titre
            
            # Ajouter les segments de texte
            for segment in segments:
                if segment and not segment.startswith('[ERREUR'):
                    content.append(segment)
                    content.append('')  # Ligne vide entre les paragraphes
        
        return '\n'.join(content)
    
    def _build_hierarchy(self, sections):
        """
        Construit la hiérarchie des sections de l'article
        
        Args:
            sections: Sections traduites
            
        Returns:
            Hiérarchie des sections
        """
        hierarchy = []
        
        # Pile pour suivre les sections parentes
        section_stack = []
        
        for section in sections:
            title = section.get('title', '')
            level = section.get('level', 0)
            
            # Nouvelle entrée de section
            section_entry = {
                'title': title,
                'level': level,
                'subsections': []
            }
            
            # Gérer la hiérarchie des sections
            while section_stack and section_stack[-1]['level'] >= level:
                section_stack.pop()
            
            if not section_stack:
                # Section de premier niveau
                hierarchy.append(section_entry)
            else:
                # Sous-section
                section_stack[-1]['subsections'].append(section_entry)
            
            section_stack.append(section_entry)
        
        return hierarchy
    
    def _build_mapping(self, sections):
        """
        Construit une correspondance entre segments originaux et traduits
        
        Args:
            sections: Sections traduites
            
        Returns:
            Mapping des segments
        """
        mapping = []
        
        for section in sections:
            original_segments = section.get('original_segments', [])
            translated_segments = section.get('segments', [])
            
            # Créer les correspondances de segments
            for orig, trans in zip(original_segments, translated_segments):
                if orig and trans:
                    mapping.append({
                        'original': orig,
                        'translated': trans
                    })
        
        return mapping
    
    def save_reconstructed_article(self, article_data, output_format='all'):
        """
        Sauvegarde l'article reconstruit dans différents formats
        
        Args:
            article_data: Données de l'article reconstruit
            output_format: Format de sortie ('json', 'txt', 'html', 'all')
            
        Returns:
            Chemins des fichiers sauvegardés
        """
        if not self.output_dir:
            logger.warning("Pas de répertoire de sortie spécifié")
            return None
        
        title = article_data.get('title', 'article')
        target_language = article_data.get('target_language', 'unknown')
        
        # Créer un nom de fichier sécurisé
        safe_title = title.replace('/', '_').replace('\\', '_').replace(':', '_')
        
        output_paths = {}
        
        # Répertoire spécifique à la langue
        lang_dir = os.path.join(self.output_dir, target_language)
        os.makedirs(lang_dir, exist_ok=True)
        
        # Sauvegarde au format JSON
        if output_format in ['json', 'all']:
            json_path = os.path.join(lang_dir, f"{safe_title}.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(article_data, f, ensure_ascii=False, indent=2)
            output_paths['json'] = json_path
            logger.info(f"Article sauvegardé au format JSON: {json_path}")
        
        # Sauvegarde au format TXT
        if output_format in ['txt', 'all']:
            txt_dir = os.path.join(self.output_dir, f"{target_language}_txt")
            os.makedirs(txt_dir, exist_ok=True)
            
            txt_path = os.path.join(txt_dir, f"{safe_title}.txt")
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"Titre original: {article_data.get('original_title', '')}\n")
                f.write(f"Titre traduit: {article_data.get('title', '')}\n\n")
                f.write(article_data.get('article_content', ''))
            
            output_paths['txt'] = txt_path
            logger.info(f"Article sauvegardé au format TXT: {txt_path}")
        
        # Sauvegarde au format HTML
        if output_format in ['html', 'all']:
            html_dir = os.path.join(self.output_dir, f"{target_language}_html")
            os.makedirs(html_dir, exist_ok=True)
            
            html_path = os.path.join(html_dir, f"{safe_title}.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(self._generate_html(article_data))
            
            output_paths['html'] = html_path
            logger.info(f"Article sauvegardé au format HTML: {html_path}")
        
        return output_paths
    
    def _generate_html(self, article_data):
        """
        Génère une représentation HTML de l'article
        
        Args:
            article_data: Données de l'article
            
        Returns:
            Contenu HTML
        """
        title = article_data.get('title', '')
        original_title = article_data.get('original_title', '')
        content = article_data.get('article_content', '')
        source_language = article_data.get('source_language', '')
        target_language = article_data.get('target_language', '')
        
        # Conversion simple du contenu Markdown en HTML
        import re
        
        # Convertir les titres
        html_content = content
        for i in range(6, 0, -1):
            pattern = r'^{0} (.+)$'.format('#' * i)
            replacement = r'<h{0}>\1</h{0}>'.format(i)
            html_content = re.sub(pattern, replacement, html_content, flags=re.MULTILINE)
        
        # Convertir les paragraphes
        paragraphs = []
        for line in html_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('<h'):
                paragraphs.append(f"<p>{line}</p>")
            elif line:
                paragraphs.append(line)
        
        html_content = '\n'.join(paragraphs)
        
        # Construire la page HTML complète
        html = f"""<!DOCTYPE html>
<html lang="{target_language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0 auto; max-width: 800px; padding: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
        h2, h3, h4, h5, h6 {{ color: #2c3e50; margin-top: 30px; }}
        p {{ margin-bottom: 20px; }}
        .metadata {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .original-title {{ color: #7f8c8d; font-style: italic; }}
    </style>
</head>
<body>
    <header>
        <h1>{title}</h1>
        <div class="metadata">
            <p class="original-title">Titre original: {original_title}</p>
            <p>Traduit de: {source_language} vers: {target_language}</p>
        </div>
    </header>
    <main>
        {html_content}
    </main>
    <footer>
        <p><small>Généré par WikiTranslateAI</small></p>
    </footer>
</body>
</html>
"""
        return html

def reconstruct_from_file(input_file, output_dir, output_format='all'):
    """
    Reconstruit un article à partir d'un fichier de traduction
    
    Args:
        input_file: Chemin vers le fichier de traduction
        output_dir: Répertoire de sortie
        output_format: Format de sortie ('json', 'txt', 'html', 'all')
        
    Returns:
        Chemins des fichiers sauvegardés
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            translated_data = json.load(f)
        
        reconstructor = ArticleReconstructor(output_dir)
        article_data = reconstructor.reconstruct_article(translated_data)
        
        return reconstructor.save_reconstructed_article(article_data, output_format)
    
    except Exception as e:
        logger.error(f"Erreur lors de la reconstruction de l'article {input_file}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Reconstruction d'articles traduits")
    parser.add_argument('--input', type=str, required=True, 
                        help="Fichier ou répertoire contenant les articles traduits")
    parser.add_argument('--output-dir', type=str, default='data/articles_reconstructed', 
                        help="Répertoire de sortie pour les articles reconstruits")
    parser.add_argument('--format', type=str, choices=['json', 'txt', 'html', 'all'], default='all', 
                        help="Format de sortie des articles reconstruits")
    
    args = parser.parse_args()
    
    # Créer le répertoire de sortie
    os.makedirs(args.output_dir, exist_ok=True)
    
    if os.path.isdir(args.input):
        # Traiter un répertoire
        successful = 0
        for file in os.listdir(args.input):
            if file.endswith('.json'):
                input_path = os.path.join(args.input, file)
                if reconstruct_from_file(input_path, args.output_dir, args.format):
                    successful += 1
        
        logger.info(f"{successful} articles reconstruits avec succès")
    
    elif os.path.isfile(args.input):
        # Traiter un fichier
        paths = reconstruct_from_file(args.input, args.output_dir, args.format)
        if paths:
            logger.info(f"Article reconstruit avec succès: {', '.join(paths.values())}")
        else:
            logger.error(f"Échec de la reconstruction de l'article")
    
    else:
        logger.error(f"Le chemin spécifié n'existe pas: {args.input}")

if __name__ == "__main__":
    main()