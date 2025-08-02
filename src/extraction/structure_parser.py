# -*- coding: utf-8 -*-
# src/extraction/structure_parser.py

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ElementType(Enum):
    """Types d'elements dans la structure Wikipedia"""
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    LIST_ITEM = "list_item"
    TABLE = "table"
    INFOBOX = "infobox"
    TEMPLATE = "template"
    LINK = "link"
    CATEGORY = "category"
    IMAGE = "image"
    REFERENCE = "reference"

@dataclass
class WikiElement:
    """Representation d'un element structurel Wikipedia"""
    element_type: ElementType
    content: str
    level: int = 0
    attributes: Dict[str, Any] = None
    position: int = 0
    
    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}

class WikipediaStructureParser:
    """Analyseur de structure pour le contenu Wikipedia"""
    
    def __init__(self):
        """Initialise l'analyseur de structure"""
        # Patterns regex pour identifier les elements
        self.patterns = {
            'heading': re.compile(r'^(=+)\s*(.+?)\s*=+$', re.MULTILINE),
            'list_item': re.compile(r'^(\*+|#+)\s*(.+)$', re.MULTILINE),
            'template': re.compile(r'\{\{([^}]+)\}\}', re.DOTALL),
            'link': re.compile(r'\[\[([^|\]]+)(?:\|([^\]]+))?\]\]'),
            'external_link': re.compile(r'\[(https?://[^\s\]]+)(?:\s+([^\]]+))?\]'),
            'image': re.compile(r'\[\[(?:File|Image):([^|\]]+)(?:\|([^\]]+))?\]\]', re.IGNORECASE),
            'category': re.compile(r'\[\[Category:([^\]]+)\]\]', re.IGNORECASE),
            'reference': re.compile(r'<ref[^>]*>(.*?)</ref>', re.DOTALL | re.IGNORECASE),
            'infobox': re.compile(r'\{\{Infobox\s+([^}]+)\}\}', re.DOTALL | re.IGNORECASE),
            'table': re.compile(r'\{\|(.+?)\|\}', re.DOTALL)
        }
        
        # Configuration pour les langues africaines
        self.african_language_markers = {
            'fon': ['gb', 'fon', 'dahomey'],
            'yor': ['yoruba', 'nigerian', 'oyo'],
            'ewe': ['ewe', 'togolese', 'ghanaian'],
            'dindi': ['dendi', 'benin', 'niger']
        }
    
    def parse_structure(self, wikitext: str) -> Dict[str, Any]:
        """
        Analyse la structure complete d'un texte Wikipedia
        
        Args:
            wikitext: Texte brut Wikipedia
        
        Returns:
            Structure analysee avec elements hierachises
        """
        logger.info(f"Debut analyse structure: {len(wikitext)} caracteres")
        
        # Structure principale
        structure = {
            'elements': [],
            'metadata': {
                'total_chars': len(wikitext),
                'element_counts': {},
                'headings_hierarchy': [],
                'links': [],
                'categories': [],
                'infoboxes': [],
                'tables': [],
                'references': []
            }
        }
        
        # Analyse ligne par ligne
        lines = wikitext.split('\n')
        current_position = 0
        current_level = 0
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Detecter le type d'element
            element = self._parse_line(line, line_num, current_position)
            
            if element:
                # Ajuster le niveau hierarchique pour les titres
                if element.element_type == ElementType.HEADING:
                    current_level = element.level
                    structure['metadata']['headings_hierarchy'].append({
                        'level': element.level,
                        'title': element.content,
                        'position': current_position
                    })
                else:
                    element.level = current_level
                
                structure['elements'].append(element)
                
                # Mettre a jour les metadonnees
                element_type_str = element.element_type.value
                structure['metadata']['element_counts'][element_type_str] = \
                    structure['metadata']['element_counts'].get(element_type_str, 0) + 1
            
            current_position += len(line) + 1  # +1 pour le retour ligne
        
        # Extraire les elements speciaux
        self._extract_special_elements(wikitext, structure)
        
        logger.info(f"Structure analysee: {len(structure['elements'])} elements, "
                   f"{len(structure['metadata']['headings_hierarchy'])} titres")
        
        return structure
    
    def _parse_line(self, line: str, line_num: int, position: int) -> Optional[WikiElement]:
        """
        Analyse une ligne pour determiner son type
        
        Args:
            line: Ligne a analyser
            line_num: Numero de ligne
            position: Position dans le texte
        
        Returns:
            WikiElement ou None
        """
        # Titres
        heading_match = self.patterns['heading'].match(line)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            return WikiElement(
                ElementType.HEADING,
                title,
                level=level,
                position=position,
                attributes={'raw_title': line}
            )
        
        # Elements de liste
        list_match = self.patterns['list_item'].match(line)
        if list_match:
            markers = list_match.group(1)
            content = list_match.group(2).strip()
            list_type = 'ordered' if markers[0] == '#' else 'unordered'
            return WikiElement(
                ElementType.LIST_ITEM,
                content,
                level=len(markers),
                position=position,
                attributes={'list_type': list_type, 'markers': markers}
            )
        
        # Paragraphe normal
        if line and not line.startswith('{|') and not line.startswith('|}'):
            return WikiElement(
                ElementType.PARAGRAPH,
                line,
                position=position,
                attributes={'line_number': line_num}
            )
        
        return None
    
    def _extract_special_elements(self, wikitext: str, structure: Dict[str, Any]):
        """
        Extrait les elements speciaux du texte complet
        
        Args:
            wikitext: Texte Wikipedia complet
            structure: Structure en cours de construction
        """
        # Liens internes
        for match in self.patterns['link'].finditer(wikitext):
            link_target = match.group(1)
            link_text = match.group(2) if match.group(2) else link_target
            structure['metadata']['links'].append({
                'target': link_target,
                'text': link_text,
                'position': match.start(),
                'type': 'internal'
            })
        
        # Liens externes
        for match in self.patterns['external_link'].finditer(wikitext):
            url = match.group(1)
            text = match.group(2) if match.group(2) else url
            structure['metadata']['links'].append({
                'target': url,
                'text': text,
                'position': match.start(),
                'type': 'external'
            })
        
        # Categories
        for match in self.patterns['category'].finditer(wikitext):
            category = match.group(1)
            structure['metadata']['categories'].append({
                'name': category,
                'position': match.start()
            })
        
        # Infoboxes
        for match in self.patterns['infobox'].finditer(wikitext):
            infobox_content = match.group(1)
            infobox_data = self._parse_infobox(infobox_content)
            structure['metadata']['infoboxes'].append({
                'type': infobox_data.get('type', 'unknown'),
                'data': infobox_data,
                'position': match.start()
            })
        
        # References
        for match in self.patterns['reference'].finditer(wikitext):
            ref_content = match.group(1)
            structure['metadata']['references'].append({
                'content': ref_content,
                'position': match.start()
            })
        
        # Tables
        for match in self.patterns['table'].finditer(wikitext):
            table_content = match.group(1)
            table_data = self._parse_table(table_content)
            structure['metadata']['tables'].append({
                'data': table_data,
                'position': match.start()
            })
    
    def _parse_infobox(self, infobox_content: str) -> Dict[str, Any]:
        """
        Analyse le contenu d'une infobox
        
        Args:
            infobox_content: Contenu brut de l'infobox
        
        Returns:
            Donnees structurees de l'infobox
        """
        infobox_data = {'fields': {}}
        
        # Premiere ligne = type d'infobox
        lines = infobox_content.strip().split('\n')
        if lines:
            infobox_data['type'] = lines[0].strip()
        
        # Analyser les champs
        for line in lines[1:]:
            line = line.strip()
            if '=' in line and line.startswith('|'):
                key_value = line[1:].split('=', 1)  # Retirer le | initial
                if len(key_value) == 2:
                    key = key_value[0].strip()
                    value = key_value[1].strip()
                    infobox_data['fields'][key] = value
        
        return infobox_data
    
    def _parse_table(self, table_content: str) -> Dict[str, Any]:
        """
        Analyse le contenu d'une table Wikipedia
        
        Args:
            table_content: Contenu brut de la table
        
        Returns:
            Donnees structurees de la table
        """
        table_data = {
            'rows': [],
            'headers': [],
            'caption': None
        }
        
        lines = table_content.strip().split('\n')
        current_row = []
        
        for line in lines:
            line = line.strip()
            
            # Caption de table
            if line.startswith('|+'):
                table_data['caption'] = line[2:].strip()
            
            # Ligne de header
            elif line.startswith('!'):
                headers = [h.strip() for h in line[1:].split('!!')]
                table_data['headers'].extend(headers)
            
            # Ligne de donnees
            elif line.startswith('|-'):
                if current_row:
                    table_data['rows'].append(current_row)
                    current_row = []
            
            elif line.startswith('|') and not line.startswith('|}'):
                cells = [c.strip() for c in line[1:].split('||')]
                current_row.extend(cells)
        
        # Ajouter la derniere ligne
        if current_row:
            table_data['rows'].append(current_row)
        
        return table_data
    
    def extract_content_sections(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extrait les sections de contenu pour la traduction
        
        Args:
            structure: Structure analysee
        
        Returns:
            Liste des sections avec leur contenu
        """
        sections = []
        current_section = None
        
        for element in structure['elements']:
            if element.element_type == ElementType.HEADING:
                # Finir la section precedente
                if current_section:
                    sections.append(current_section)
                
                # Commencer nouvelle section
                current_section = {
                    'title': element.content,
                    'level': element.level,
                    'content': '',
                    'elements': [],
                    'word_count': 0
                }
            
            elif current_section and element.element_type in [ElementType.PARAGRAPH, ElementType.LIST_ITEM]:
                current_section['content'] += element.content + '\n'
                current_section['elements'].append({
                    'type': element.element_type.value,
                    'content': element.content,
                    'attributes': element.attributes
                })
                current_section['word_count'] += len(element.content.split())
        
        # Ajouter la derniere section
        if current_section:
            sections.append(current_section)
        
        logger.info(f"Sections extraites: {len(sections)} sections de contenu")
        return sections
    
    def identify_african_content(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identifie le contenu lie aux langues africaines
        
        Args:
            structure: Structure analysee
        
        Returns:
            Informations sur le contenu africain
        """
        african_content = {
            'detected_languages': [],
            'relevant_sections': [],
            'cultural_markers': [],
            'geographic_markers': []
        }
        
        # Analyser tous les elements pour detecter les marqueurs africains
        all_text = ' '.join([elem.content for elem in structure['elements']])
        all_text_lower = all_text.lower()
        
        # Detection des langues
        for lang, markers in self.african_language_markers.items():
            for marker in markers:
                if marker in all_text_lower:
                    if lang not in african_content['detected_languages']:
                        african_content['detected_languages'].append(lang)
                    african_content['cultural_markers'].append({
                        'language': lang,
                        'marker': marker,
                        'occurrences': all_text_lower.count(marker)
                    })
        
        # Marqeurs geographiques
        geographic_markers = ['benin', 'nigeria', 'togo', 'ghana', 'west africa', 'gulf of guinea']
        for marker in geographic_markers:
            if marker in all_text_lower:
                african_content['geographic_markers'].append({
                    'marker': marker,
                    'occurrences': all_text_lower.count(marker)
                })
        
        logger.info(f"Contenu africain detecte: {len(african_content['detected_languages'])} langues, "
                   f"{len(african_content['cultural_markers'])} marqueurs culturels")
        
        return african_content
    
    def get_translation_priority_sections(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identifie les sections prioritaires pour la traduction
        
        Args:
            structure: Structure analysee
        
        Returns:
            Sections triees par priorite de traduction
        """
        sections = self.extract_content_sections(structure)
        
        # Criteres de priorite
        priority_keywords = ['history', 'culture', 'language', 'tradition', 'geography', 'overview']
        skip_keywords = ['references', 'external links', 'see also', 'bibliography']
        
        # Calculer le score de priorite
        for section in sections:
            score = 0
            title_lower = section['title'].lower()
            
            # Bonus pour mots-cles prioritaires
            for keyword in priority_keywords:
                if keyword in title_lower:
                    score += 10
            
            # Malus pour sections a ignorer
            for keyword in skip_keywords:
                if keyword in title_lower:
                    score -= 20
            
            # Bonus pour longueur du contenu
            score += min(section['word_count'] / 50, 10)  # Max 10 points
            
            # Bonus pour niveau de titre (sections principales)
            if section['level'] <= 2:
                score += 5
            
            section['translation_priority'] = max(0, score)
        
        # Trier par priorite
        sections.sort(key=lambda s: s['translation_priority'], reverse=True)
        
        logger.info(f"Priorites calculees: {len(sections)} sections triees")
        return sections


if __name__ == "__main__":
    # Test de l'analyseur de structure
    sample_wikitext = """
= Histoire du Benin =

Le [[Benin]] est un pays d'[[Afrique de l'Ouest]].

== Periode precoloniale ==

Les [[Fon]] et les [[Yoruba]] sont les principaux groupes ethniques.

* Premier royaume: [[Dahomey]]
* Langue principale: [[Fon (langue)|Fon]]

{{Infobox Country
|name = Benin
|capital = Porto-Novo
|language = Francais, Fon
}}

[[Category:Histoire du Benin]]
"""
    
    parser = WikipediaStructureParser()
    structure = parser.parse_structure(sample_wikitext)
    
    print(f"Elements: {len(structure['elements'])}")
    print(f"Titres: {len(structure['metadata']['headings_hierarchy'])}")
    print(f"Liens: {len(structure['metadata']['links'])}")
    
    sections = parser.extract_content_sections(structure)
    print(f"Sections: {len(sections)}")
    
    african_content = parser.identify_african_content(structure)
    print(f"Langues africaines detectees: {african_content['detected_languages']}")