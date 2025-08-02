# src/database/glossary_manager.py

import sqlite3
import json
from datetime import datetime

class GlossaryManager:
    def __init__(self, db_path):
        """Initialise le gestionnaire de glossaire avec le chemin vers la base de données"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def __enter__(self):
        """Permet l'utilisation du gestionnaire dans un bloc with"""
        self.conn = sqlite3.connect(self.db_path)
        # Activer les clés étrangères
        self.conn.execute("PRAGMA foreign_keys = ON")
        # Permettre l'accès par nom de colonne
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ferme la connexion à la sortie du bloc with"""
        if self.conn:
            self.conn.close()
    
    def get_language_id(self, language_code):
        """Récupère l'ID d'une langue à partir de son code"""
        self.cursor.execute("SELECT id FROM languages WHERE code = ?", (language_code,))
        result = self.cursor.fetchone()
        if result:
            return result['id']
        return None
    
    def get_domain_id(self, domain_name):
        """Récupère l'ID d'un domaine à partir de son nom"""
        self.cursor.execute("SELECT id FROM domains WHERE name = ?", (domain_name,))
        result = self.cursor.fetchone()
        if result:
            return result['id']
        return None
    
    def add_term(self, source_term, source_lang, target_term, target_lang, 
                 domain='general', context=None, confidence=0.5, validated=False):
        """Ajoute un terme au glossaire"""
        source_lang_id = self.get_language_id(source_lang)
        target_lang_id = self.get_language_id(target_lang)
        domain_id = self.get_domain_id(domain)
        
        if not all([source_lang_id, target_lang_id, domain_id]):
            missing = []
            if not source_lang_id:
                missing.append(f"langue source '{source_lang}'")
            if not target_lang_id:
                missing.append(f"langue cible '{target_lang}'")
            if not domain_id:
                missing.append(f"domaine '{domain}'")
            raise ValueError(f"Éléments introuvables: {', '.join(missing)}")
        
        # Vérifier si l'entrée existe déjà
        self.cursor.execute("""
            SELECT id FROM glossary_entries 
            WHERE source_term = ? AND source_language_id = ? 
              AND target_language_id = ? AND (domain_id = ? OR (domain_id IS NULL AND ? IS NULL))
        """, (source_term, source_lang_id, target_lang_id, domain_id, domain_id))
        
        existing_entry = self.cursor.fetchone()
        
        if existing_entry:
            # Mise à jour de l'entrée existante
            self.cursor.execute("""
                UPDATE glossary_entries
                SET target_term = ?, context_example = ?, confidence_score = ?,
                    validated = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (target_term, context, confidence, validated, existing_entry['id']))
            entry_id = existing_entry['id']
        else:
            # Création d'une nouvelle entrée
            self.cursor.execute("""
                INSERT INTO glossary_entries
                (source_term, source_language_id, target_term, target_language_id,
                 domain_id, context_example, confidence_score, validated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (source_term, source_lang_id, target_term, target_lang_id,
                 domain_id, context, confidence, validated))
            entry_id = self.cursor.lastrowid
        
        self.conn.commit()
        return entry_id
    
    def add_term_variant(self, entry_id, variant, is_source=True):
        """Ajoute une variante d'un terme"""
        try:
            self.cursor.execute("""
                INSERT INTO term_variants (entry_id, variant, is_source)
                VALUES (?, ?, ?)
            """, (entry_id, variant, is_source))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            # La variante existe déjà
            return None
    
    def search_term(self, term, source_lang, target_lang, domain=None):
        """Recherche un terme dans le glossaire"""
        source_lang_id = self.get_language_id(source_lang)
        target_lang_id = self.get_language_id(target_lang)
        
        query = """
            SELECT ge.id, ge.source_term, ge.target_term, ge.context_example,
                   ge.confidence_score, ge.validated, d.name as domain
            FROM glossary_entries ge
            LEFT JOIN domains d ON ge.domain_id = d.id
            WHERE ge.source_term = ? AND ge.source_language_id = ? AND ge.target_language_id = ?
        """
        params = [term, source_lang_id, target_lang_id]
        
        if domain:
            domain_id = self.get_domain_id(domain)
            if domain_id:
                query += " AND ge.domain_id = ?"
                params.append(domain_id)
        
        self.cursor.execute(query, params)
        results = [dict(row) for row in self.cursor.fetchall()]
        
        # Recherche aussi dans les variantes
        variant_query = """
            SELECT ge.id, ge.source_term, ge.target_term, ge.context_example,
                   ge.confidence_score, ge.validated, d.name as domain
            FROM term_variants tv
            JOIN glossary_entries ge ON tv.entry_id = ge.id
            LEFT JOIN domains d ON ge.domain_id = d.id
            WHERE tv.variant = ? AND tv.is_source = 1
              AND ge.source_language_id = ? AND ge.target_language_id = ?
        """
        
        self.cursor.execute(variant_query, [term, source_lang_id, target_lang_id])
        variant_results = [dict(row) for row in self.cursor.fetchall()]
        
        # Combiner les résultats sans doublons
        all_results = results.copy()
        for vr in variant_results:
            if not any(r['id'] == vr['id'] for r in all_results):
                all_results.append(vr)
        
        return all_results
    
    def batch_import(self, json_file_path):
        """Importe un lot de termes à partir d'un fichier JSON"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                terms = json.load(f)
            
            imported_count = 0
            for term in terms:
                try:
                    entry_id = self.add_term(
                        term['source_term'],
                        term['source_lang'],
                        term['target_term'],
                        term['target_lang'],
                        term.get('domain', 'general'),
                        term.get('context'),
                        term.get('confidence', 0.5),
                        term.get('validated', False)
                    )
                    
                    # Ajouter les variantes si présentes
                    if 'variants' in term and entry_id:
                        for variant in term['variants']:
                            self.add_term_variant(
                                entry_id,
                                variant['term'],
                                variant.get('is_source', True)
                            )
                    
                    imported_count += 1
                except Exception as e:
                    print(f"Erreur lors de l'importation du terme {term.get('source_term')}: {e}")
            
            return imported_count
        except Exception as e:
            print(f"Erreur lors de l'importation du fichier {json_file_path}: {e}")
            return 0
    
    def export_glossary(self, output_file_path, source_lang=None, target_lang=None):
        """Exporte le glossaire au format JSON"""
        query = """
            SELECT ge.id, ge.source_term, l1.code as source_lang, ge.target_term,
                   l2.code as target_lang, d.name as domain, ge.context_example,
                   ge.confidence_score, ge.validated
            FROM glossary_entries ge
            JOIN languages l1 ON ge.source_language_id = l1.id
            JOIN languages l2 ON ge.target_language_id = l2.id
            LEFT JOIN domains d ON ge.domain_id = d.id
        """
        params = []
        
        if source_lang:
            source_lang_id = self.get_language_id(source_lang)
            if source_lang_id:
                query += " WHERE ge.source_language_id = ?"
                params.append(source_lang_id)
        
        if target_lang:
            target_lang_id = self.get_language_id(target_lang)
            if target_lang_id:
                query += " AND " if "WHERE" in query else " WHERE "
                query += "ge.target_language_id = ?"
                params.append(target_lang_id)
        
        self.cursor.execute(query, params)
        entries = [dict(row) for row in self.cursor.fetchall()]
        
        # Récupérer les variantes pour chaque entrée
        for entry in entries:
            self.cursor.execute("""
                SELECT variant, is_source
                FROM term_variants
                WHERE entry_id = ?
            """, (entry['id'],))
            
            variants = [dict(row) for row in self.cursor.fetchall()]
            if variants:
                entry['variants'] = variants
        
        # Écrire dans le fichier JSON
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        
        return len(entries)
    
    def validate_term(self, entry_id, validated=True):
        """Marque un terme comme validé ou non"""
        self.cursor.execute("""
            UPDATE glossary_entries
            SET validated = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (validated, entry_id))
        self.conn.commit()
        return self.cursor.rowcount > 0