# 🔐 GUIDE DE SÉCURITÉ WIKITRANSLATEAI

## 🚨 **ALERTE SÉCURITÉ RÉSOLUE**

**PROBLÈME IDENTIFIÉ (2025-08-01):** Clé API OpenAI exposée publiquement  
**STATUT:** ✅ **RÉSOLU** - Clé remplacée par placeholder sécurisé

---

## 📋 **CONFIGURATION SÉCURISÉE**

### **1. Configuration des clés API**

```bash
# 1. Copiez le fichier d'exemple
cp .env.example .env

# 2. Éditez avec vos vraies clés (utilisez un éditeur sécurisé)
nano .env  # ou vim, code, etc.

# 3. Vérifiez que .env est dans .gitignore
grep "\.env" .gitignore
```

### **2. Obtenir vos clés API**

**OpenAI Standard:**
- Site: https://platform.openai.com/api-keys
- Format: `sk-proj-...` (51+ caractères)
- Coût: Pay-per-use

**Azure OpenAI (optionnel):**
- Site: https://portal.azure.com
- Format: `32 caractères alphanumérique`
- Avantage: Conformité entreprise

### **3. Variables d'environnement (Production)**

```bash
# Production Linux/Docker
export OPENAI_API_KEY="sk-proj-votre-cle-ici"
export DATABASE_URL="postgresql://user:pass@host:port/db"

# Ou dans un fichier systemd
echo "OPENAI_API_KEY=sk-proj-votre-cle" > /etc/environment
```

---

## 🛡️ **BONNES PRATIQUES SÉCURITÉ**

### **✅ À FAIRE**

1. **Clés API distinctes par environnement**
   - Développement: Clé avec quotas limités
   - Production: Clé avec monitoring actif

2. **Rotation régulière des clés**
   - Changez les clés tous les 3-6 mois
   - Utilisez des clés temporaires pour les tests

3. **Monitoring des coûts**
   - Configurez des alertes de facturation
   - Surveillez l'usage quotidien/mensuel

4. **Validation des entrées**
   - Tous les inputs utilisateur sont validés
   - Échappement des caractères spéciaux

5. **Logs sécurisés**
   - Les clés API ne sont JAMAIS loggées
   - Logs rotatifs avec rétention limitée

### **❌ À ÉVITER**

1. **Clés en dur dans le code**
   ```python
   # ❌ DANGER
   api_key = "sk-proj-abc123..."
   
   # ✅ CORRECT
   api_key = os.getenv("OPENAI_API_KEY")
   ```

2. **Clés dans les URLs ou paramètres GET**
   ```python
   # ❌ DANGER
   url = f"https://api.com?key={api_key}"
   
   # ✅ CORRECT
   headers = {"Authorization": f"Bearer {api_key}"}
   ```

3. **Clés dans les messages d'erreur**
   ```python
   # ❌ DANGER
   raise Exception(f"API error with key {api_key}")
   
   # ✅ CORRECT
   raise Exception("API authentication failed")
   ```

---

## 🔍 **AUDIT SÉCURITÉ**

### **Commandes de vérification**

```bash
# 1. Vérifier qu'aucune clé n'est en dur dans le code
grep -r "sk-proj-" src/ --exclude-dir=__pycache__
grep -r "sk-" src/ --exclude-dir=__pycache__ | grep -v "example"

# 2. Vérifier .env dans .gitignore
git check-ignore .env

# 3. Vérifier l'historique git (clés accidentellement commitées)
git log --all --grep="key\|secret\|password" --oneline
git log --all -S "sk-proj" --oneline

# 4. Scanner les dépendances vulnérables
pip audit  # Python 3.11+
# ou
pip install safety && safety check
```

### **Checklist pré-déploiement**

- [ ] ✅ `.env` contient des placeholders, pas de vraies clés
- [ ] ✅ `.env` est dans `.gitignore`
- [ ] ✅ `.env.example` existe avec instructions
- [ ] ✅ Variables d'environnement configurées en production
- [ ] ✅ Monitoring coûts API activé
- [ ] ✅ Logs ne contiennent pas de secrets
- [ ] ✅ Permissions fichiers restrictives (`chmod 600 .env`)
- [ ] ✅ Scan sécurité passé sans alertes

---

## 🚨 **EN CAS DE COMPROMISSION**

Si une clé API a été exposée publiquement:

### **Actions immédiates (< 5 minutes)**

1. **Révoquer la clé exposée**
   ```bash
   # OpenAI: https://platform.openai.com/api-keys
   # Azure: https://portal.azure.com
   ```

2. **Générer nouvelle clé**
   ```bash
   # Créer nouvelle clé avec nom descriptif
   # Ex: "WikiTranslateAI-Prod-2025-08"
   ```

3. **Mettre à jour production**
   ```bash
   # Mettre à jour variables d'environnement
   export OPENAI_API_KEY="nouvelle-cle"
   # Redémarrer services
   systemctl restart wikitranslate
   ```

### **Actions de suivi (< 24 heures)**

4. **Audit facturation**
   - Vérifier usage suspect sur tableau de bord API
   - Contacter support si usage anormal

5. **Audit sécurité complet**
   - Scanner tout le codebase pour autres secrets
   - Réviser permissions et accès

6. **Documentation incident**
   - Noter date/heure exposition
   - Actions prises et leçons apprises

---

## 📞 **CONTACTS URGENCE**

**Support OpenAI:** https://help.openai.com  
**Support Azure:** https://azure.microsoft.com/support  
**Équipe sécurité projet:** security@wikitranslateai.org (si applicable)

---

## 🔄 **CHANGELOG SÉCURITÉ**

### **2025-08-01**
- ✅ **RÉSOLU:** Clé API OpenAI exposée dans `.env`
- ✅ **AJOUTÉ:** Fichier `.env.example` sécurisé
- ✅ **AJOUTÉ:** Guide sécurité complet
- ✅ **VÉRIFIÉ:** `.env` protégé par `.gitignore`

---

*Ce guide est mis à jour après chaque audit sécurité.*  
*Dernière révision: 2025-08-01*