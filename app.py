# -*- coding: utf-8 -*-
"""
Brandshipping AI - Agent 10K
Version URBÆ™ - Mobilité Urbaine Premium
Localisé Orléans-Blois-Tours | Loire Valley Edition
🔧 Version Production-Ready : Cache LRU + Streaming + Sécurité renforcée
"""

import os
import re
import time
import math
import json
import logging
import hashlib
import threading
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple, Generator
from datetime import datetime, timedelta
from collections import OrderedDict

import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CONFIGURATION & LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("urbae_brandshipping")

# Filtre pour masquer les clés API dans les logs (sécurité)
class SecretFilter(logging.Filter):
    def filter(self, record):
        if isinstance(record.getMessage(), str):
            record.msg = re.sub(r'Bearer\s+[a-zA-Z0-9_-]+', 'Bearer [REDACTED]', str(record.msg))
            record.msg = re.sub(r'MISTRAL_API_KEY[\'"]?\s*[:=]\s*[\'"]?[^\'"\s]+', 'MISTRAL_API_KEY=[REDACTED]', str(record.msg))
        return True

logger.addFilter(SecretFilter())

@dataclass(frozen=True)
class Config:
    """Configuration centralisée URBÆ™ - Documentée"""
    # API Mistral
    API_URL: str = "https://api.mistral.ai/v1/chat/completions"
    MODEL: str = "mistral-large-latest"
    FALLBACK_MODEL: str = "mistral-medium-latest"
    TEMPERATURE: float = 0.7
    TIMEOUT: int = 120
    
    # Retry policy
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 3.0
    RETRY_BACKOFF: float = 2.5
    
    # Business metrics
    OBJECTIF_10K: float = 10000.0
    SEUIL_ADS: float = 0.35  # 35% max du CA pour ads → marge nette ≥35%
    
    # Sécurité & performance
    MAX_INPUT: int = 500
    CACHE_TTL: int = 3600  # 1 heure
    CACHE_MAX_ENTRIES: int = 50
    
    # Zones & saisons
    ZONES: Tuple[str, ...] = field(default_factory=lambda: (
        "Orléans (280K hab, tech hub)", "Tours (137K hab, ville cyclable)", 
        "Blois (46K hab, tourisme Loire)", "National (scaling)"
    ))
    SAISONS: Tuple[str, ...] = field(default_factory=lambda: (
        "Printemps (mars-mai)", "Été (juin-août)", "Automne (sept-nov)", "Hiver (déc-fév)"
    ))

cfg = Config()

# =============================================================================
# CACHE LRU THREAD-SAFE (Inline - pas de module externe)
# =============================================================================

class LRUCache:
    """Cache LRU thread-safe avec TTL - implémentation inline"""
    
    def __init__(self, max_entries: int = 50, ttl_seconds: int = 3600):
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = threading.RLock()
    
    def _generate_key(self, system_prompt: str, user_prompt: str) -> str:
        """Génère une clé de cache unique"""
        combined = f"{system_prompt}|||{user_prompt}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]
    
    def get(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Récupère une valeur du cache si valide"""
        key = self._generate_key(system_prompt, user_prompt)
        
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            if datetime.now() > entry['expires_at']:
                del self._cache[key]
                return None
            
            self._cache.move_to_end(key)  # LRU update
            logger.debug(f"✓ Cache hit: {key[:8]}...")
            return entry['value']
    
    def set(self, system_prompt: str, user_prompt: str, value: str) -> None:
        """Stocke une valeur avec eviction LRU"""
        key = self._generate_key(system_prompt, user_prompt)
        expires_at = datetime.now() + timedelta(seconds=self.ttl_seconds)
        
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            elif len(self._cache) >= self.max_entries:
                oldest = next(iter(self._cache))
                del self._cache[oldest]
                logger.debug(f"🗑️ Cache eviction: {oldest[:8]}...")
            
            self._cache[key] = {'value': value, 'expires_at': expires_at}
    
    def stats(self) -> Dict[str, Any]:
        """Statistiques du cache"""
        with self._lock:
            now = datetime.now()
            valid = sum(1 for e in self._cache.values() if e['expires_at'] > now)
            return {'total': len(self._cache), 'valid': valid, 'max': self.max_entries}

# Instance globale du cache
response_cache = LRUCache(max_entries=cfg.CACHE_MAX_ENTRIES, ttl_seconds=cfg.CACHE_TTL)

# =============================================================================
# MASTER PROMPT URBÆ™ - Optimisé avec contexte de base
# =============================================================================

# Contexte de base partagé pour réduire les tokens
BASE_CONTEXT = """
[URBÆ™ CONTEXT - NE PAS MODIFIER]
Marque : Mobilité urbaine premium | Zones : Orléans/Blois/Tours | Produit : Sacoche IPX6 2.5L
Prix : 89-149€ TTC | Marge cible : 65-75% | CPA max : 12€ | Cible : Vélotafeurs 25-45 ans
Logistique : FBA Orléans, Chronopost local, Livraison 48h Centre-Val de Loire
"""

SYSTEM_PROMPTS = {
    "strategie": f"""{BASE_CONTEXT}

[TÂCHE : PLAN STRATÉGIQUE HEBDOMADAIRE]
Tu es URBAE AI Manager, agent IA spécialisé en BrandShipping et marketing local.

MISSION : Faire croître URBÆ™ sur Orléans–Blois–Tours avec un plan actionnable.

INSTRUCTIONS :
1. Propose 3 angles marketing dominants par semaine
2. Identifie les opportunités météo (pluie = pic ventes)
3. Détecte tendances TikTok locales/nationales
4. Propose tests A/B (prix, angles, audiences)
5. Calcule métriques avec coûts locaux (CPA 12-18€ vs 35-50€ national)
6. Suggère partenariats locaux (clubs vélo, coffee shops, réparateurs)

FORMAT : Plan stratégique hebdomadaire avec tableaux comparatifs et recommandations priorisées.
TON : Précis, actionnable, orienté résultats, fier d'être local.""",

    "offre": f"""{BASE_CONTEXT}

[TÂCHE : OPTIMISATION OFFRES E-COMMERCE]
Tu es expert en optimisation d'offres pour URBÆ™.

MISSION : Maximiser valeur perçue et panier moyen pour cyclistes urbains Orléans-Blois-Tours.

PRODUITS :
- Sacoche cadre waterproof URBÆ™ : 89€ TTC (coût 28€, marge 69%)
- Urban Rider Pack : Bundle premium cycliste urbain

PACKS À OPTIMISER :
1. Pack Solo : Sacoche + guide itinéraires
2. Pack Duo : 2 sacoches + housse anti-pluie + stickers
3. Urban Rider Pack : Sacoche + support téléphone + LED + guide
4. Pack Pro : Urban Rider + gilet + casque urbain

STRUCTURE DE L'OFFRE :
1. Nom accrocheur avec référence mobilité urbaine
2. Pricing psychologique (ancrage, prix public/valeur/offre)
3. 3-5 bonus perçus (coût faible, valeur haute)
4. 3 arguments irréfutables (local/praticité/durabilité)
5. Garantie "Satisfait 30j + 2 ans"
6. CTA urgent et localisé

CONTRAINTES : Valeur perçue ≥ 5x prix payé | Sentiment "tribu cycliste" | Ton authentique

FORMAT : Tableau comparatif des packs + recommandation finale chiffrée.""",

    "creatives": f"""{BASE_CONTEXT}

[TÂCHE : SCRIPTS VIDÉO UGC TIKTOK/REELS]
Tu es directeur créatif UGC pour URBÆ™ Loire Valley.

MISSION : Produire 10 scripts vidéo/semaine (15-30s).

FORMAT PAR SCRIPT :
## Script [N°] - [Nom accrocheur]
**Durée :** XX secondes | **Zone :** Orléans/Tours/Blois/National
**Type :** Hook émotionnel / Démo / Témoignage / Humour / FOMO / Test extrême

**HOOK (0-3s) :** Phrase qui stoppe le scroll avec référence locale
**PROBLÈME (3-10s) :** Pain point quotidien cycliste urbain
**SOLUTION (10-20s) :** URBÆ™ en action + bénéfices (IPX6, fixation, design)
**CTA (20-30s) :** Call-to-action clair avec urgence locale
**TEXTE OVERLAY :** Comparaisons, preuves, social proof, offres
**HASHTAGS :** #URBÆ #SacocheVélo #OrléansVélo #ToursVélo #LoireÀVélo #MobilitéUrbaine

CONSIGNES : 3 scripts "fierté locale" | 2 "comparaison prix" | 2 "météo/pluie" | 2 "FOMO" | 1 "test extrême"
TON : Authentique, génération Z/millennial urbain, pas corporate.

FORMAT : 10 scripts complets avec tous les éléments.""",

    "acquisition": f"""{BASE_CONTEXT}

[TÂCHE : PLAN ACQUISITION TIKTOK ADS 30 JOURS]
Tu es media buyer senior TikTok Ads pour URBÆ™.

MISSION : Plan d'acquisition avec CPA cible < 12€.

BUDGETS PAR PHASE :
- Phase 1 (J1-10) : Test - 20-30€/jour = 250€
- Phase 2 (J11-20) : Optimisation - 50€/jour = 500€
- Phase 3 (J21-30) : Scale - 100€/jour = 1000€
- TOTAL : 1750€ sur 30 jours

STRUCTURE DU PLAN :
1. OBJECTIFS & KPIs (CPA <12€, ROAS 4-5.5, CTR 2-3.5%)
2. STRUCTURE CAMPAGNE (CBO Test 70%, Retargeting 20%, Lookalike 10%)
3. CIBLAGES GÉOGRAPHIQUES (Orléans 15km, Tours 20km, Blois 10km)
4. CIBLAGES INTÉRÊTS (vélotaf, livreurs, étudiants, éco-responsable)
5. 20 ANGLES PUBLICITAIRES (émotion local, logique prix, FOMO, social proof, éducation)
6. CALENDRIER 30 JOURS DÉTAILLÉ
7. CHECKLIST OPTIMISATION (kill/scale rules)

RESSOURCES LOCALES : Clubs vélo, événements Loire à Vélo, micro-influenceurs, communautés livreurs

FORMAT : Tableaux markdown, budgets chiffrés, calendrier jour par jour actionnable.
TON : Précis, orienté résultats, "CPA < 12€ ou on coupe"."""
}

# =============================================================================
# VALIDATION & SÉCURITÉ RENFORCÉE
# =============================================================================

# Patterns d'injection de prompt - étendus
INJECTION_PATTERNS = [
    r'ignore\s+(previous|above|all|these)\s+instructions?',
    r'forget\s+(everything|all|previous|your\s+instructions)',
    r'bypass\s+(security|rules|filters)',
    r'override\s+(system\s+prompt|your\s+behavior)',
    r'you\s+are\s+now\s+(free|unrestricted|a\s+different\s+assistant)',
    r'act\s+as\s+(admin|developer|system)',
    r'<\s*/?\s*(script|iframe|object|embed)\s*>',
    r'eval\s*\(', r'exec\s*\(', r'__import__',
    r'os\.system', r'subprocess\.', r'__class__',
    r'show\s+me\s+your\s+(system\s+prompt|instructions|configuration)',
    r'<\s*/\s*system\s*>', r'\[\s*SYSTEM\s*\]',
]
COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

def sanitize_input(text: str, max_len: int = 500) -> str:
    """Nettoie les entrées utilisateur : contrôle chars, tags HTML, normalisation"""
    if not isinstance(text, str):
        text = str(text)
    # Suppression caractères de contrôle (sauf \n, \t)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # Suppression tags HTML/XML
    text = re.sub(r'<[^>]+>', '', text)
    # Normalisation espaces
    text = ' '.join(text.split())
    return text.strip()[:max_len]

def check_prompt_injection(text: str) -> Tuple[bool, str]:
    """Détecte les tentatives d'injection de prompt avec logging"""
    text_lower = text.lower()
    for pattern in COMPILED_PATTERNS:
        if pattern.search(text_lower):
            logger.warning(f"⚠️ Injection détectée - pattern: {pattern.pattern}")
            return False, "⚠️ Contenu suspect détecté - requête rejetée"
    return True, ""

def validate_niche(niche: str) -> Tuple[bool, str]:
    """Valide une niche : longueur + présence de lettres"""
    if not niche or len(niche.strip()) < 3:
        return False, "La niche doit faire au moins 3 caractères"
    if not re.search(r'[a-zA-ZÀ-ÿ]', niche):
        return False, "La niche doit contenir des lettres"
    return True, ""

def validate_context(contexte: str) -> Tuple[bool, str]:
    """Valide le contexte : longueur minimale"""
    if not contexte or len(contexte.strip()) < 10:
        return False, "Le contexte doit faire au moins 10 caractères"
    return True, ""

def validate_user_input(text: str, field_name: str = "input") -> Tuple[bool, str]:
    """Validation multi-couche : sanitization + injection + basique"""
    clean = sanitize_input(text, max_len=cfg.MAX_INPUT)
    if not clean or len(clean) < 3:
        return False, f"{field_name} trop court (min 3 caractères)"
    is_safe, error = check_prompt_injection(clean)
    if not is_safe:
        return False, error
    return True, ""

# =============================================================================
# MODÈLE FINANCIER
# =============================================================================

@dataclass
class MetricsResult:
    marge_pct: float
    ca_necessaire: float
    commandes_jour: float
    is_valid: bool
    error: str = ""

@dataclass
class ProjectionResult:
    ca_mensuel: float
    marge_brute: float
    cout_ads: float
    resultat_net: float
    progression_10k: float
    is_profitable: bool

def calculer_metrics(prix: float, cout: float) -> MetricsResult:
    """Calcule les métriques avec validation"""
    if prix <= 0:
        return MetricsResult(0, 0, 0, False, "Prix de vente doit être > 0€")
    if cout < 0:
        return MetricsResult(0, 0, 0, False, "Coût ne peut pas être négatif")
    if cout >= prix:
        return MetricsResult(0, float('inf'), 0, False, "Coût >= Prix : marge impossible")

    marge_unitaire = prix - cout
    marge_pct = marge_unitaire / prix
    marge_reelle = marge_pct - cfg.SEUIL_ADS

    if marge_reelle <= 0:
        return MetricsResult(
            round(marge_pct * 100, 1), float('inf'), 0, False,
            f"Marge {marge_pct*100:.1f}% trop faible (min {cfg.SEUIL_ADS*100:.0f}% pour ads)"
        )

    ca_nec = cfg.OBJECTIF_10K / marge_reelle
    cmd_jour = (ca_nec / prix) / 30

    return MetricsResult(
        round(marge_pct * 100, 1),
        round(ca_nec, 2),
        round(cmd_jour, 1),
        True
    )

def calculer_projection(ca: float, marge_pct: float, cout_ads: float) -> ProjectionResult:
    """Calcule la projection mensuelle"""
    marge_brute = ca * marge_pct
    resultat = marge_brute - cout_ads
    progression = min((resultat / cfg.OBJECTIF_10K) * 100, 100)

    return ProjectionResult(
        round(ca, 2), round(marge_brute, 2),
        round(cout_ads, 2), round(resultat, 2),
        round(progression, 1), resultat > 0
    )

# =============================================================================
# CLIENT API MISTRAL - ROBUSTE AVEC STREAMING & RETRY
# =============================================================================

class APIError(Exception):
    """Exception personnalisée pour erreurs API"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code

def get_api_key() -> str:
    """Récupère la clé API de manière sécurisée"""
    try:
        key = st.secrets.get("MISTRAL_API_KEY")
        if key:
            return key
    except Exception:
        pass
    key = os.getenv("MISTRAL_API_KEY")
    if not key:
        raise APIError("❌ Clé MISTRAL_API_KEY manquante dans Settings > Secrets ou .env")
    return key

def _build_payload(system_prompt: str, user_prompt: str, stream: bool = False) -> Dict[str, Any]:
    """Construit le payload pour l'API Mistral"""
    return {
        "model": cfg.MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": cfg.TEMPERATURE,
        "stream": stream
    }

def _handle_response_error(response: requests.Response) -> None:
    """Gestion centralisée des codes d'erreur HTTP"""
    status = response.status_code
    if status == 401:
        raise APIError("🔑 Clé API invalide ou expirée", status)
    elif status == 403:
        raise APIError("🚫 Accès refusé - vérifiez vos quotas Mistral", status)
    elif status == 429:
        retry_after = response.headers.get('Retry-After', 'quelques secondes')
        raise APIError(f"⏱️ Rate limit atteint - réessayez dans {retry_after}", status)
    elif 500 <= status < 600:
        raise APIError(f"🔥 Erreur serveur Mistral ({status})", status)
    elif status >= 400:
        try:
            error_detail = response.json().get('error', {}).get('message', 'Erreur inconnue')
            raise APIError(f"❌ Erreur API ({status}): {error_detail}", status)
        except json.JSONDecodeError:
            raise APIError(f"❌ Erreur HTTP {status}: {response.text[:200]}", status)

def call_mistral_api(system_prompt: str, user_prompt: str) -> str:
    """Appel API Mistral synchrone avec retry exponentiel (fallback pour compatibilité)"""
    api_key = get_api_key()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = _build_payload(system_prompt, user_prompt, stream=False)
    
    last_error = None
    for attempt in range(cfg.MAX_RETRIES):
        try:
            response = requests.post(cfg.API_URL, headers=headers, json=payload, timeout=(10, cfg.TIMEOUT))
            _handle_response_error(response)
            data = response.json()
            if not data.get("choices"):
                raise APIError("Réponse API invalide")
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout:
            last_error = "Timeout"
        except requests.exceptions.ConnectionError:
            last_error = "Erreur connexion"
        except APIError as e:
            if e.status_code and e.status_code >= 400 and e.status_code < 500:
                raise  # Ne pas retry sur erreurs client
            last_error = str(e)
        except Exception as e:
            last_error = str(e)
            logger.error(f"Erreur inattendue: {e}")
            break
        
        if attempt < cfg.MAX_RETRIES - 1:
            wait = cfg.RETRY_DELAY * (cfg.RETRY_BACKOFF ** attempt)
            logger.warning(f"Tentative {attempt+1} échouée ({last_error}), retry dans {wait:.1f}s")
            time.sleep(wait)
    
    raise APIError(f"Échec après {cfg.MAX_RETRIES} tentatives: {last_error}")

def call_mistral_stream(system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
    """Appel API Mistral avec streaming pour feedback en temps réel"""
    api_key = get_api_key()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = _build_payload(system_prompt, user_prompt, stream=True)
    
    response = requests.post(cfg.API_URL, headers=headers, json=payload, stream=True, timeout=cfg.TIMEOUT)
    _handle_response_error(response)
    
    for line in response.iter_lines(decode_unicode=True):
        if line and line.startswith('data: '):
            data = line[6:]  # Remove 'data: ' prefix
            if data.strip() == '[DONE]':
                break
            try:
                chunk = json.loads(data)
                content = chunk.get('choices', [{}])[0].get('delta', {}).get('content', '')
                if content:
                    yield content
            except json.JSONDecodeError:
                continue

# =============================================================================
# GÉNÉRATION AVEC CACHE & STREAMING
# =============================================================================

def generate_with_cache(prompt_key: str, user_input: str, use_streaming: bool = True) -> str:
    """Génère une réponse avec cache intelligent et option de streaming"""
    system_prompt = SYSTEM_PROMPTS.get(prompt_key, "")
    
    # Validation input
    is_valid, error = validate_user_input(user_input, "prompt")
    if not is_valid:
        return f"❌ {error}"
    
    # Vérification cache
    cached = response_cache.get(system_prompt, user_input)
    if cached:
        st.success("📦 Résultat chargé depuis le cache")
        return cached
    
    # Génération
    try:
        if use_streaming:
            # Affichage streaming avec placeholder
            placeholder = st.empty()
            full_response = ""
            with st.spinner("🤖 Génération en cours..."):
                for chunk in call_mistral_stream(system_prompt, user_input):
                    full_response += chunk
                    placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
            result = full_response
        else:
            with st.spinner("🤖 Génération en cours... (~10-30s)"):
                result = call_mistral_api(system_prompt, user_input)
            st.markdown(result)
        
        # Mise en cache
        response_cache.set(system_prompt, user_input, result)
        return result
        
    except APIError as e:
        st.error(str(e))
        return f"❌ {e}"
    except Exception as e:
        logger.error(f"Erreur génération: {e}")
        return f"❌ Erreur: {e}"

# =============================================================================
# INITIALISATION SESSION STATE
# =============================================================================

def init_session():
    """Initialise les variables de session"""
    defaults = {
        'results': {},
        'initialized': True,
        'use_streaming': True  # Option utilisateur pour activer/désactiver streaming
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# =============================================================================
# INTERFACE STREAMLIT - URBÆ™ BRANDED
# =============================================================================

st.set_page_config(
    page_title="URBÆ™ Brandshipping AI - Agent 10K",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🚲 URBÆ™ Brandshipping AI")
st.caption("Mobilité Urbaine Premium | Orléans · Blois · Tours | Objectif : 10K€ net/mois")

init_session()

# ---------------------------------------------------------------------------
# SIDEBAR - COCKPIT URBÆ™
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("📊 Cockpit URBÆ™")

    # Logo textuel
    st.markdown("""
    <div style="text-align:center; padding:10px; background:#1a1a2e; border-radius:8px; margin-bottom:15px;">
        <h2 style="color:#e94560; margin:0; font-size:1.5rem;">URBÆ™</h2>
        <p style="color:#eee; margin:0; font-size:0.7rem;">Mobilité Urbaine Premium</p>
    </div>
    """, unsafe_allow_html=True)

    # Option streaming
    st.session_state.use_streaming = st.checkbox(
        "🔄 Activer le streaming (recommandé)", 
        value=st.session_state.get('use_streaming', True),
        help="Affiche la réponse en temps réel au lieu d'attendre la fin"
    )

    prix = st.number_input("Prix de vente URBÆ™ (€)", value=89.0, step=5.0, min_value=0.01)
    cout = st.number_input("Coût produit (€)", value=28.0, step=1.0, min_value=0.0)
    ads_pct = st.slider("Budget Ads TikTok (% du CA)", 10, 50, 25) / 100

    metrics = calculer_metrics(prix, cout)

    if not metrics.is_valid:
        st.error(f"⚠️ {metrics.error}")
        st.info("💡 Ajustez prix ou coût pour continuer")
    else:
        st.metric("Marge Brute URBÆ™", f"{metrics.marge_pct}%")
        if math.isinf(metrics.ca_necessaire):
            st.metric("CA nécessaire", "∞ €")
        else:
            st.metric("CA/mois pour 10K€", f"{metrics.ca_necessaire:,.0f} €")
        st.metric("Commandes/jour", f"{metrics.commandes_jour:.1f}")

        st.divider()
        ca_test = st.number_input("CA mensuel estimé (€)", value=15930, step=500, min_value=0)

        try:
            proj = calculer_projection(ca_test, metrics.marge_pct/100, ca_test * ads_pct)
            col1, col2 = st.columns(2)
            delta = "✅ Rentable" if proj.is_profitable else "❌ Déficit"
            delta_color = "normal" if proj.is_profitable else "inverse"
            col1.metric("Résultat Net", f"{proj.resultat_net:,.0f} €", delta=delta, delta_color=delta_color)
            col2.metric("Progression 10K", f"{proj.progression_10k}%")
            st.progress(min(proj.progression_10k / 100, 1.0))
            if proj.progression_10k >= 100:
                st.success("🎉 Objectif 10K€ atteint !")
            elif proj.progression_10k >= 75:
                st.info("📈 Proche de l'objectif !")
        except Exception as e:
            st.error(f"Erreur calcul: {e}")

    # Stats cache
    st.divider()
    cache_stats = response_cache.stats()
    st.caption(f"💾 Cache : {cache_stats['valid']}/{cache_stats['total']} entrées valides")
    
    if st.button("🗑️ Vider le cache", type="secondary"):
        response_cache._cache.clear()
        st.rerun()

    # Info locale
    st.divider()
    st.markdown("""
    <div style="font-size:0.75rem; color:#666;">
        🚲 <b>Zones actives :</b><br>
        &nbsp;&nbsp;• Orléans (15km)<br>
        &nbsp;&nbsp;• Tours (20km)<br>
        &nbsp;&nbsp;• Blois (10km)<br><br>
        📦 <b>Logistique :</b><br>
        &nbsp;&nbsp;• FBA Orléans<br>
        &nbsp;&nbsp;• Chronopost local<br>
        &nbsp;&nbsp;• Livraison 48h CVL
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TABS - 4 AXES URBÆ™
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Stratégie", "🎁 Offre", "🎬 Créatives", "📢 Acquisition"])

with tab1:
    st.subheader("🎯 Plan Stratégique Hebdomadaire URBÆ™")
    st.markdown("**Angles marketing dominants · Opportunités météo · Tendances TikTok locales**")
    zone = st.selectbox("Zone prioritaire", cfg.ZONES, key="zone_strat")
    saison = st.selectbox("Saisonnalité", cfg.SAISONS, key="saison_strat")
    
    if st.button("🎯 Générer le plan stratégique", type="primary", key="btn_strat"):
        prompt = f"Zone: {zone}. Saison: {saison}. Génère le plan stratégique hebdomadaire URBÆ™ avec 3 angles marketing dominants."
        result = generate_with_cache("strategie", prompt, use_streaming=st.session_state.use_streaming)
        if not result.startswith("❌"):
            st.session_state.results['strategie'] = result
    elif 'strategie' in st.session_state.results:
        st.markdown(st.session_state.results['strategie'])

with tab2:
    st.subheader("🎁 Optimisation Urban Rider Pack")
    st.markdown("**Packs · Pricing · Bonus · Offres locales**")
    pack_type = st.selectbox("Type de pack à optimiser", ["Pack Solo (sacoche seule)", "Pack Duo (2 sacoches)", "Urban Rider Pack (bundle premium)", "Pack Pro (complet)"], key="pack_type")
    prix_test = st.selectbox("Prix à tester", ["139.90€", "149.90€", "159.90€", "169.90€"], key="prix_test")
    
    if st.button("🎁 Générer l'offre optimisée", type="primary", key="btn_offre"):
        prompt = f"Pack: {pack_type}. Prix test: {prix_test}. Génère l'offre URBÆ™ optimisée avec bonus perçus et pricing psychologique."
        result = generate_with_cache("offre", prompt, use_streaming=st.session_state.use_streaming)
        if not result.startswith("❌"):
            st.session_state.results['offre'] = result
    elif 'offre' in st.session_state.results:
        st.markdown(st.session_state.results['offre'])

with tab3:
    st.subheader("🎬 Scripts UGC - 10 vidéos/semaine")
    st.markdown("**Hooks · Démonstrations · Témoignages · Tests extrêmes**")
    type_script = st.selectbox("Type de scripts", ["Fierté locale (Orléans/Tours/Blois)", "Comparaison prix (vs Decathlon/Ortlieb)", "Météo/Pluie (argument waterproof)", "FOMO/Saisonnalité", "Test extrême"], key="type_script")
    lieu_tournage = st.text_input("Lieu de tournage suggéré", placeholder="Ex: Pont George V Orléans, Bords de Loire Blois", key="lieu_tournage")
    
    if st.button("🎬 Générer les 10 scripts", type="primary", key="btn_creatives"):
        prompt = f"Type: {type_script}. Lieu: {lieu_tournage}. Génère 10 scripts vidéo URBÆ™ 15-30s avec hooks localisés."
        result = generate_with_cache("creatives", prompt, use_streaming=st.session_state.use_streaming)
        if not result.startswith("❌"):
            st.session_state.results['creatives'] = result
    elif 'creatives' in st.session_state.results:
        st.markdown(st.session_state.results['creatives'])

with tab4:
    st.subheader("📢 Plan Acquisition TikTok Ads")
    st.markdown("**CPA cible < 12€ · Ciblage hyper-local · Scale 30 jours**")
    budget_jour = st.selectbox("Budget quotidien", ["20-30€ (Phase Test)", "50€ (Phase Optimisation)", "100€ (Phase Scale)", "200€+ (Scaling national)"], key="budget_jour")
    audience_cible = st.selectbox("Audience prioritaire", ["Vélotafeurs (25-45 ans, cadres)", "Livreurs à vélo (Uber/Deliveroo)", "Étudiants cyclistes", "Cyclistes loisirs (Loire à Vélo)", "Digital nomades"], key="audience_cible")
    
    if st.button("📢 Générer le plan média", type="primary", key="btn_acquisition"):
        prompt = f"Budget: {budget_jour}. Audience: {audience_cible}. Génère le plan acquisition TikTok Ads 30 jours URBÆ™ avec CPA < 12€."
        result = generate_with_cache("acquisition", prompt, use_streaming=st.session_state.use_streaming)
        if not result.startswith("❌"):
            st.session_state.results['acquisition'] = result
    elif 'acquisition' in st.session_state.results:
        st.markdown(st.session_state.results['acquisition'])

st.divider()
st.caption("URBÆ™ Brandshipping AI - Mobilité Urbaine Premium © 2026 | Orléans · Blois · Tours | Propulsé par Mistral AI")
