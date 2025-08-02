# src/database/schema.py

import sqlite3
from pathlib import Path

def create_database_schema(db_path):
    """Crée le schéma de la base de données pour le glossaire"""
    
    # Assurez-vous que le dossier parent existe
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Table des langues
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS languages (
        id INTEGER PRIMARY KEY,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL
    )
    ''')
    
    # Table des domaines/contextes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS domains (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        description TEXT
    )
    ''')
    
    # Table principale du glossaire
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS glossary_entries (
        id INTEGER PRIMARY KEY,
        source_term TEXT NOT NULL,
        source_language_id INTEGER NOT NULL,
        target_term TEXT NOT NULL,
        target_language_id INTEGER NOT NULL,
        domain_id INTEGER,
        context_example TEXT,
        confidence_score REAL DEFAULT 0.5,
        validated BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (source_language_id) REFERENCES languages(id),
        FOREIGN KEY (target_language_id) REFERENCES languages(id),
        FOREIGN KEY (domain_id) REFERENCES domains(id),
        UNIQUE (source_term, source_language_id, target_language_id, domain_id)
    )
    ''')
    
    # Table pour les variantes et inflexions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS term_variants (
        id INTEGER PRIMARY KEY,
        entry_id INTEGER NOT NULL,
        variant TEXT NOT NULL,
        is_source BOOLEAN NOT NULL,  -- True pour langue source, False pour langue cible
        FOREIGN KEY (entry_id) REFERENCES glossary_entries(id),
        UNIQUE (entry_id, variant, is_source)
    )
    ''')
    
    # Insertion des langues de base
    languages = [
        ('en', 'English'),
        ('fr', 'French'),
        ('fon', 'Fon'),
        ('dindi', 'Dindi'),
        ('ewe', 'Ewe'),
        ('yor', 'Yoruba')
    ]
    
    cursor.executemany(
        'INSERT OR IGNORE INTO languages (code, name) VALUES (?, ?)',
        languages
    )
    
    # Insertion des domaines de base
    domains = [
        ('general', 'Termes généraux'),
        ('science', 'Termes scientifiques'),
        ('tech', 'Technologie'),
        ('culture', 'Culture et arts'),
        ('history', 'Histoire'),
        ('geography', 'Géographie'),
        ('medicine', 'Médecine'),
        ('politics', 'Politique')
    ]
    
    cursor.executemany(
        'INSERT OR IGNORE INTO domains (name, description) VALUES (?, ?)',
        domains
    )
    
    conn.commit()
    conn.close()
    
    print(f"Base de données créée à {db_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        create_database_schema(db_path)
        print(f"Schéma créé avec succès dans {db_path}")
    else:
        print("Usage: python schema.py <chemin_base_de_données>")