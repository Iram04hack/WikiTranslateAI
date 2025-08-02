#!/bin/bash

# Déterminer le chemin absolu du répertoire du script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activer l'environnement virtuel (avec chemin absolu)
source "$SCRIPT_DIR/venv/bin/activate"

# Vérifier les paramètres
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <target_language> [title|search_term] [source_language]"
    echo "Example: $0 fon 'COVID-19' fr"
    exit 1
fi

TARGET_LANG=$1
QUERY=$2
SOURCE_LANG=${3:-fr}

# Créer les répertoires nécessaires
mkdir -p data/articles_raw/$SOURCE_LANG
mkdir -p data/articles_cleaned
mkdir -p data/articles_segmented
mkdir -p data/articles_translated/$TARGET_LANG

# Exécuter le pipeline complet si un titre ou terme de recherche est fourni
if [ -n "$QUERY" ]; then
    if [[ "$QUERY" == *" "* ]]; then
        # Si la requête contient des espaces, la traiter comme un terme de recherche
        echo "Recherche et traduction d'articles sur '$QUERY' de $SOURCE_LANG vers $TARGET_LANG"
        python "$SCRIPT_DIR/main.py" --search "$QUERY" --source-lang $SOURCE_LANG --target-lang $TARGET_LANG --count 1
    else
        # Sinon, la traiter comme un titre d'article
        echo "Traduction de l'article '$QUERY' de $SOURCE_LANG vers $TARGET_LANG"
        python "$SCRIPT_DIR/main.py" --title "$QUERY" --source-lang $SOURCE_LANG --target-lang $TARGET_LANG
    fi
else
    # Sinon, extraire et traduire un article aléatoire
    echo "Traduction d'un article aléatoire de $SOURCE_LANG vers $TARGET_LANG"
    python "$SCRIPT_DIR/main.py" --random --count 1 --source-lang $SOURCE_LANG --target-lang $TARGET_LANG
fi