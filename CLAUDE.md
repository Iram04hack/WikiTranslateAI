# 📋 INSTRUCTIONS CLAUDE POUR WIKITRANSLATEAI

## 🎯 **CONTEXTE PROJET**
WikiTranslateAI est un système de traduction d'articles Wikipedia vers les langues africaines sous-représentées (Fon, Yoruba, Ewe, Dindi). Le projet vise à démocratiser l'accès au savoir pour 350+ millions de locuteurs africains.

## 📊 **ÉTAT ACTUEL**
- **Statut**: Prototype non-fonctionnel avec bugs critiques
- **Problème principal**: API OpenAI obsolète (v0.x) empêche tout fonctionnement
- **Phase actuelle**: Phase 1 - Corrections Critiques (0% complété)
- **Priorité absolue**: Fixer l'API OpenAI (Étape 1.1)

## 🚀 **COMMANDES DE DÉMARRAGE**

### **Pour reprendre le travail immédiatement:**
```bash
# 1. Vérifier l'état actuel
python scripts/update_progress.py --show-status

# 2. Identifier prochaine tâche
cat PROGRESS_TRACKER.json | jq '.next_actions[0]'

# 3. Lire feuille de route détaillée
head -50 ROADMAP.md
```

### **Test rapide du système:**
```bash
# Test import (doit échouer actuellement)
python -c "from src.translation.azure_client import AzureOpenAITranslator; print('✅ Import OK')" 2>/dev/null || echo "❌ CASSÉ - API OpenAI obsolète"

# Test configuration
python -c "from src.utils.config import load_config; config = load_config(); print('✅ Config OK')"
```

## 🛠️ **TÂCHE PRIORITAIRE ACTUELLE**

**ÉTAPE 1.1: Fixer l'API OpenAI** (16h estimées)

### **Sous-tâches dans l'ordre:**
1. **1.1.1** - Mettre à jour `requirements.txt`: `openai>=1.3.0` (0.5h)
2. **1.1.2** - Refactoriser `src/translation/azure_client.py` (4h)
3. **1.1.3** - Modifier méthode `translate_text()` (6h) 
4. **1.1.4** - Tester traduction segment simple (2h)
5. **1.1.5** - Valider avec article complet (3.5h)

### **Code exact à remplacer:**
```python
# DANS src/translation/azure_client.py ligne 19-23
# REMPLACER:
openai.api_type = "azure"
openai.api_key = api_key  
openai.api_version = api_version
openai.api_base = azure_endpoint

# PAR:
from openai import AzureOpenAI
self.client = AzureOpenAI(
    api_key=api_key,
    azure_endpoint=azure_endpoint, 
    api_version=api_version
)
```

## 📋 **WORKFLOW DE TRAVAIL**

### **Après chaque modification:**
```bash
# 1. Tester import
python -c "from src.translation.azure_client import AzureOpenAITranslator; print('✅')"

# 2. Mettre à jour progression
python scripts/update_progress.py --phase phase_1 --step step_1_1 --subtask 1_1_1 --status completed

# 3. Recalculer pourcentages
python scripts/update_progress.py --recalculate
```

### **Tests de validation:**
```bash
# Test avec API keys (si configurées)
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_ENDPOINT="your-endpoint"

# Test traduction simple
python -c "
from src.translation.azure_client import create_translator_from_env
translator = create_translator_from_env()
result = translator.translate_text('Hello', 'en', 'fr')
print(f'Résultat: {result}')
"
```

## 🔧 **STRUCTURE RECOMMANDÉE**

### **Session de travail type:**
1. **Lire état actuel** avec `--show-status`
2. **Choisir tâche prioritaire** (status="not_started" + priority="critical")
3. **Travailler sur 1 sous-tâche uniquement**
4. **Tester après chaque changement**
5. **Mettre à jour progression** dans JSON
6. **Passer à sous-tâche suivante**

### **En cas de problème:**
```bash
# Restaurer version précédente
git checkout HEAD~1 src/translation/azure_client.py

# Vérifier logs
tail -20 logs/latest.log

# Debug imports
python -c "import sys; print(sys.path)"
```

## 🚨 **POINTS CRITIQUES**

### **À vérifier absolument:**
- [ ] Variables environnement API configurées
- [ ] Python 3.8+ installé  
- [ ] Au moins 4GB RAM disponible
- [ ] Backup code fait avant modifications importantes

### **Tests obligatoires après modifications:**
- [ ] Import des modules sans erreur
- [ ] Configuration chargée correctement
- [ ] Traduction simple fonctionne (si API keys)
- [ ] Aucune régression sur fonctionnalités existantes

## 📊 **COMMANDES DE MONITORING**

```bash
# État général
python scripts/update_progress.py --show-status

# Progression détaillée 
cat PROGRESS_TRACKER.json | jq '.phases.phase_1.progress'

# Prochaines actions
cat PROGRESS_TRACKER.json | jq '.next_actions'

# Bloqueurs actifs
cat PROGRESS_TRACKER.json | jq '.current_blockers[] | select(.status == "open")'
```

## 🎯 **OBJECTIFS MESURABLES**

### **Fin Étape 1.1 (API OpenAI fixée):**
- [ ] ✅ Import `AzureOpenAITranslator` sans erreur
- [ ] ✅ Traduction simple "Hello" → "Bonjour" réussit
- [ ] ✅ Pipeline complet s'exécute sans crash
- [ ] ✅ Tests existants passent

### **Fin Phase 1 (Corrections Critiques):**
- [ ] ✅ Système fonctionnel de bout en bout
- [ ] ✅ Traduction complète d'un article Wikipedia
- [ ] ✅ Zéro crash sur cas de test standard
- [ ] ✅ Performance baseline établie

## 💡 **CONSEILS POUR CLAUDE**

### **Bonnes pratiques:**
- Toujours lire `PROGRESS_TRACKER.json` en début de conversation
- Travailler sur 1 seule tâche à la fois
- Tester immédiatement après chaque modification
- Mettre à jour progression régulièrement
- Documenter problèmes rencontrés

### **À éviter:**
- Modifier plusieurs fichiers simultanément
- Ignorer les tests de validation
- Oublier de mettre à jour la progression
- Travailler sans avoir lu l'état actuel

---

**Cette documentation permet de reprendre efficacement le travail sur WikiTranslateAI sans re-analyser l'ensemble du code à chaque fois.**