# 🚀 QUICK START - WIKITRANSLATEAI

## 📌 **POUR NOUVELLE CONVERSATION**

Si vous commencez une nouvelle conversation Claude Code, voici exactement ce qu'il faut faire :

### **1. État Actuel (À Lire Absolument)**
```bash
# Lire l'état du projet
cat ROADMAP.md | head -20
cat PROGRESS_TRACKER.json | jq '.project_info'
```

**Résumé Express :**
- ❌ **Système NON-FONCTIONNEL** (API OpenAI cassée)
- 🎯 **Objectif**: Traduire Wikipedia vers langues africaines
- 📊 **Progression**: Phase 1/3 (0% complété)
- ⚡ **Action Prioritaire**: Fixer API OpenAI (Étape 1.1)

### **2. Commandes de Diagnostic**
```bash
# Vérifier l'état des composants
python -c "import openai; print(f'OpenAI version: {openai.__version__}')"
python -c "from src.translation.azure_client import AzureOpenAITranslator; print('Import OK')" 2>/dev/null || echo "❌ IMPORT FAILED"

# Tester configuration
python -c "from src.utils.config import load_config; print('Config loaded')"
```

### **3. Prochaine Étape À Exécuter**
**ÉTAPE 1.1: Fixer l'API OpenAI** (16h estimées)

#### **Sous-tâches dans l'ordre :**
1. **1.1.1** - Mettre à jour `requirements.txt`
2. **1.1.2** - Refactoriser `src/translation/azure_client.py`  
3. **1.1.3** - Modifier méthode `translate_text()`
4. **1.1.4** - Tester traduction simple
5. **1.1.5** - Valider avec article complet

---

## 🎯 **COMMANDES POUR COMMENCER IMMÉDIATEMENT**

### **Étape 1.1.1: Mettre à jour requirements.txt**
```bash
# Backup actuel
cp requirements.txt requirements.txt.backup

# Modifier requirements.txt
sed -i 's/openai==1.13.3/openai>=1.3.0/' requirements.txt
echo "pydantic>=2.0.0" >> requirements.txt
echo "redis>=4.0.0" >> requirements.txt

# Réinstaller
pip install -r requirements.txt
```

### **Étape 1.1.2: Code à remplacer dans azure_client.py**
```python
# REMPLACER lignes 19-23 :
# openai.api_type = "azure"
# openai.api_key = api_key
# openai.api_version = api_version
# openai.api_base = azure_endpoint

# PAR :
from openai import AzureOpenAI

# Dans __init__:
self.client = AzureOpenAI(
    api_key=api_key,
    azure_endpoint=azure_endpoint,
    api_version=api_version
)
```

### **Étape 1.1.3: Nouvelle méthode translate_text()**
```python
# REMPLACER ligne 40-80 dans translate_text()
async def translate_text(self, text, source_language, target_language, domain=None, use_glossary=True):
    if not text or not text.strip():
        return ""

    prompt = self._create_translation_prompt(text, source_language, target_language, domain, use_glossary)

    for attempt in range(self.max_retries):
        try:
            await asyncio.sleep(self.rate_limit_delay)
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            # ... gestion erreur existante
```

---

## 📊 **COMMANDES DE VALIDATION**

### **Test Après Chaque Étape**
```bash
# Test import après modification
python -c "from src.translation.azure_client import AzureOpenAITranslator; print('✅ Import réussi')"

# Test traduction simple (nécessite API keys)
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_ENDPOINT="your-endpoint"
python -c "
from src.translation.azure_client import create_translator_from_env
translator = create_translator_from_env()
result = translator.translate_text('Hello', 'en', 'fr')
print(f'Test: {result}')
"

# Test pipeline complet
python main.py --title "Computer" --target-lang yor --steps extract,clean,segment,translate
```

### **Mise à Jour Progression**
```python
# Script pour mettre à jour PROGRESS_TRACKER.json
import json

with open('PROGRESS_TRACKER.json', 'r') as f:
    progress = json.load(f)

# Marquer sous-tâche complétée
progress['phases']['phase_1']['steps']['step_1_1']['subtasks']['1_1_1']['status'] = 'completed'

# Recalculer progression
total_subtasks = sum(len(step['subtasks']) for step in progress['phases']['phase_1']['steps'].values())
completed_subtasks = sum(
    1 for step in progress['phases']['phase_1']['steps'].values() 
    for subtask in step['subtasks'].values() 
    if subtask['status'] == 'completed'
)
progress['phases']['phase_1']['progress']['completed'] = completed_subtasks
progress['phases']['phase_1']['progress']['percentage'] = round((completed_subtasks / total_subtasks) * 100)

with open('PROGRESS_TRACKER.json', 'w') as f:
    json.dump(progress, f, indent=2)

print(f"Progression Phase 1: {completed_subtasks}/{total_subtasks} ({progress['phases']['phase_1']['progress']['percentage']}%)")
```

---

## 🔧 **STRUCTURE DE TRAVAIL RECOMMANDÉE**

### **Session de Travail Type (2-4h)**
1. **Lire état actuel** : `cat PROGRESS_TRACKER.json | jq '.next_actions'`
2. **Choisir tâche prioritaire** : Toujours commencer par status="not_started" + priority="critical"
3. **Travailler sur 1 sous-tâche à la fois**
4. **Tester après chaque modification**
5. **Mettre à jour progression** dans JSON
6. **Commit git si réussi**

### **Commandes de Debug Utiles**
```bash
# Logs en temps réel
tail -f logs/batch_$(date +%Y%m%d).log

# Vérifier structure données
find data/ -name "*.json" -exec python -m json.tool {} \; >/dev/null && echo "✅ JSONs valides" || echo "❌ JSON invalide"

# Test mémoire/performance  
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Mémoire: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"
```

---

## 🚨 **POINTS D'ATTENTION CRITIQUES**

### **Avant de Commencer**
- [ ] ✅ Variables environnement API configurées
- [ ] ✅ Backup du code actuel fait
- [ ] ✅ Python 3.8+ installé
- [ ] ✅ Au moins 4GB RAM disponible

### **Pendant le Travail**
- [ ] ✅ Tester chaque modification individuellement
- [ ] ✅ Ne pas modifier plusieurs fichiers simultanément
- [ ] ✅ Garder logs visibles pour debug
- [ ] ✅ Sauvegarder progression toutes les heures

### **En Cas de Problème**
1. **Revenir version précédente** : `git checkout HEAD~1 src/translation/azure_client.py`
2. **Vérifier logs** : `tail -20 logs/latest.log`
3. **Tester imports** : `python -c "import sys; print(sys.path)"`
4. **Restart clean** : `rm -rf __pycache__/ && python main.py --help`

---

## 📋 **CHECKLIST SESSION COMPLÈTE**

### **Début Session**
- [ ] Lire PROGRESS_TRACKER.json
- [ ] Identifier prochaine tâche prioritaire
- [ ] Configurer environnement (API keys, etc.)
- [ ] Créer backup si modifications importantes

### **Pendant Session**
- [ ] Travailler sur 1 seule tâche à la fois
- [ ] Tester après chaque sous-tâche
- [ ] Documenter problèmes rencontrés
- [ ] Mettre à jour JSON de progression

### **Fin Session**
- [ ] Valider toutes modifications avec tests
- [ ] Mettre à jour PROGRESS_TRACKER.json
- [ ] Commit changes si étape complète
- [ ] Noter prochaines actions dans team_notes

---

*Cette feuille de route détaillée permet de reprendre le travail efficacement à tout moment, sans re-analyser l'ensemble du code à chaque nouvelle conversation.*