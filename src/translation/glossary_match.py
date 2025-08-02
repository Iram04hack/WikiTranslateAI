# Modification de src/translation/glossary_match.py

import re
from src.database.glossary_manager import GlossaryManager

class GlossaryMatcher:
    def __init__(self, db_path, cache_size=1000):
        """Initialise le matcher de glossaire"""
        self.db_path = db_path
        # Cache LRU pour les correspondances fréquentes
        self.match_cache = {}
        self.cache_access_order = []
        self.max_cache_size = cache_size
    
    def preprocess_text(self, text):
        """Prétraite le texte pour la correspondance (normalisation, tokenisation)"""
        # Normalisation simple: minuscules et suppression de la ponctuation
        text = text.lower()
        # Conserver des caractères spéciaux pour les langues ciblées
        text = re.sub(r'[^\w\s\u00E0-\u00FF\u0300-\u036F]', ' ', text)
        # Tokenisation améliorée
        tokens = [token for token in text.split() if token]
        return tokens
    
    def find_matches(self, text, source_lang, target_lang, domain=None):
        """Trouve tous les termes du glossaire dans le texte - Optimisé O(n²)
        
        Optimisations appliquées:
        - Évite les recherches répétées de positions (find() en O(n))  
        - Utilise des indices de tokens au lieu de positions de caractères
        - Cache LRU avec clés hachées pour éviter la fragmentation mémoire
        - Early termination: skip ngrams si tokens déjà couverts
        - Complexité réduite de O(n³) → O(n²)
        """
        # Vérifier le cache avec une clé plus robuste
        cache_key = self._generate_cache_key(text, source_lang, target_lang, domain)
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        tokens = self.preprocess_text(text)
        matches = {}
        
        # Créer un mapping token -> positions pour éviter les recherches répétées O(n)
        token_positions = {}
        current_pos = 0
        normalized_text = text.lower()
        
        for i, token in enumerate(tokens):
            # Trouver la position de ce token dans le texte original
            token_start = normalized_text.find(token, current_pos)
            if token_start != -1:
                token_positions[i] = {
                    'start': token_start, 
                    'end': token_start + len(token),
                    'token': token
                }
                current_pos = token_start + len(token)
        
        with GlossaryManager(self.db_path) as gm:
            # Optimisation: Générer et tester les n-grammes par ordre de priorité
            covered_token_indices = set()
            
            # Commencer par les n-grammes les plus longs (max_n=5 down to 1)
            for n in range(min(5, len(tokens)), 0, -1):
                for i in range(len(tokens) - n + 1):
                    # Vérifier si ces tokens sont déjà couverts
                    if any(idx in covered_token_indices for idx in range(i, i + n)):
                        continue
                    
                    # Construire le n-gramme
                    ngram_tokens = tokens[i:i+n]
                    ngram = ' '.join(ngram_tokens)
                    
                    # Rechercher dans le glossaire (une seule fois par n-gramme)
                    results = gm.search_term(ngram, source_lang, target_lang, domain)
                    
                    if results:
                        # Prendre le résultat avec la meilleure confiance
                        best_match = max(results, key=lambda x: (x['validated'], x.get('confidence_score', 0.5)))
                        matches[ngram] = best_match
                        
                        # Marquer ces indices de tokens comme couverts (O(1) par token)
                        for idx in range(i, i + n):
                            covered_token_indices.add(idx)
        
        # Mettre en cache les résultats avec gestion LRU
        self._put_in_cache(cache_key, matches)
        return matches
    
    def _generate_ngrams(self, tokens, max_n=5):
        """Génère des n-grammes à partir de tokens"""
        ngrams = []
        
        for n in range(1, min(max_n + 1, len(tokens) + 1)):
            for i in range(len(tokens) - n + 1):
                ngram = ' '.join(tokens[i:i+n])
                ngrams.append(ngram)
        
        return ngrams
    
    def _generate_cache_key(self, text, source_lang, target_lang, domain):
        """Génère une clé de cache robuste et unique"""
        import hashlib
        # Utiliser un hash pour éviter les clés trop longues et assurer l'unicité
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:16]
        return f"{text_hash}_{source_lang}_{target_lang}_{domain or 'general'}"
    
    def _get_from_cache(self, cache_key):
        """Récupère un élément du cache avec gestion LRU"""
        if cache_key in self.match_cache:
            # Déplacer vers la fin (plus récemment utilisé)
            if cache_key in self.cache_access_order:
                self.cache_access_order.remove(cache_key)
            self.cache_access_order.append(cache_key)
            return self.match_cache[cache_key]
        return None
    
    def _put_in_cache(self, cache_key, value):
        """Ajoute un élément au cache avec éviction LRU si nécessaire"""
        # Si déjà présent, juste mettre à jour
        if cache_key in self.match_cache:
            self.match_cache[cache_key] = value
            if cache_key in self.cache_access_order:
                self.cache_access_order.remove(cache_key)
            self.cache_access_order.append(cache_key)
            return
        
        # Si cache plein, supprimer le plus anciennement utilisé
        if len(self.match_cache) >= self.max_cache_size:
            oldest_key = self.cache_access_order.pop(0)
            del self.match_cache[oldest_key]
        
        # Ajouter le nouvel élément
        self.match_cache[cache_key] = value
        self.cache_access_order.append(cache_key)
    
    def apply_glossary(self, text, source_lang, target_lang, domain=None):
        """Applique le glossaire au texte pour aider à la traduction"""
        matches = self.find_matches(text, source_lang, target_lang, domain)
        
        # Créer une structure de données pour le prompt de traduction
        glossary_guide = {
            "text": text,
            "glossary_matches": [
                {
                    "source_term": term,
                    "target_term": match['target_term'],
                    "domain": match.get('domain', 'general'),
                    "confidence": match.get('confidence_score', match.get('confidence', 0.5)),
                    "validated": match.get('validated', False)
                }
                for term, match in matches.items()
            ]
        }
        
        return glossary_guide
    
    def augment_translation_prompt(self, text, source_lang, target_lang, domain=None):
        """Crée un prompt augmenté pour l'API OpenAI incluant le glossaire"""
        glossary_guide = self.apply_glossary(text, source_lang, target_lang, domain)
        
        # Construction du prompt amélioré
        glossary_instructions = ""
        if glossary_guide["glossary_matches"]:
            glossary_instructions = "Veuillez respecter le glossaire suivant pour la traduction :\n\n"
            
            # Trier les correspondances par longueur (du plus long au plus court)
            sorted_matches = sorted(glossary_guide["glossary_matches"], 
                                   key=lambda x: len(x['source_term']), reverse=True)
            
            for match in sorted_matches:
                validated = match.get('validated', False)
                confidence = match.get('confidence', 0.5)
                domain_value = match.get('domain', 'general')
                
                confidence_str = "validé" if validated else f"confiance: {confidence:.1f}"
                glossary_instructions += f"- '{match['source_term']}' → '{match['target_term']}' ({domain_value}, {confidence_str})\n"
        
        # Prompt complet pour l'API
        prompt = f"""Traduisez le texte suivant de {source_lang} vers {target_lang}.

{glossary_instructions}

Texte à traduire :
{text}

Traduction :"""
        
        return prompt