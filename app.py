"""
Brandshipping AI - Agent 10K
Version Expert Pro - Monolithique optimisée
"""
import os
import re
import time
import math
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CONFIGURATION & LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("brandshipping_ai")

@dataclass(frozen=True)
class Config:
    """Configuration centralisée"""
    API_URL: str = "https://api.mistral.ai/v1/chat/completions"
    MODEL: str = "mistral-large-latest"
    TEMPERATURE: float = 0.7
    TIMEOUT: int = 60
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 2.0
    OBJECTIF_10K: float = 10000.0
    SEUIL_ADS: float = 0.35
    MAX_INPUT: int = 500
    CACHE_TTL: int = 3600


cfg = Config()

# =============================================================================
# PROMPTS SYSTÈME
# =============================================================================

SYSTEM_PROMPTS = {
    "strategie": """Tu es un expert en Brandshipping et e-commerce DTC. 
Ton objectif est d'aider l'utilisateur à atteindre 10K€/mois de bénéfice net.
Analyse sa niche et propose 3 produits avec une marge minimum x3.
Sois concret : donne des exemples de produits, de fournisseurs potentiels et justifie la marge.""",

    "offre": """Tu es un copywriter spécialisé en offres irrésistibles.
Crée un 'Bundle Premium' à forte valeur perçue basé sur le produit sélectionné.
Inclus : le nom de l'offre, le pricing psychologique, les bonus perçus, et l'argumentaire de vente principal.""",

    "creatives": """Tu es un directeur créatif UGC (User Generated Content).
Génère 5 scripts vidéo courts (15-30s) pour TikTok/Reels.
Format pour chaque script : Hook (3s) + Problème + Solution (Produit) + CTA.
Ton ton doit être authentique, dynamique et adapté à la Gen Z / Millennials.""",

    "acquisition": """Tu es un media buyer expert Meta Ads & TikTok Ads.
Élabore un plan de test sur 7 jours avec un budget défini.
Inclus : structure de campagne, audiences à tester, KPIs cibles (CPA, ROAS) et 20 angles publicitaires variés."""
}

# =============================================================================
# VALIDATION & SÉCURITÉ
# =============================================================================

def sanitize_input(text: str, max_len: int = 500) -> str:
    """Nettoie les entrées utilisateur"""
    if not isinstance(text, str):
        text = str(text)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()[:max_len]

def validate_niche(niche: str) -> tuple[bool, str]:
    """Valide une niche"""
    if not niche or len(niche.strip()) < 3:
        return False, "La niche doit faire au moins 3 caractères"
    if not re.search(r'[a-zA-Z]', niche):
        return False, "La niche doit contenir des lettres"
    return True, ""

def validate_context(contexte: str) -> tuple[bool, str]:
    """Valide le contexte"""
    if not contexte or len(contexte.strip()) < 10:
        return False, "Le contexte doit faire au moins 10 caractères"
    return True, ""

def check_injection(text: str) -> tuple[bool, str]:
    """Détecte les injections de prompt"""
    patterns = [
        r'ignore\s+(previous|above|all)\s+instructions',
        r'forget\s+(everything|all|previous)',
        r'system\s*prompt',
        r'you\s+are\s+now',
        r'<\s*/\s*system\s*>',
        r'<\s*script\s*>',
    ]
    for p in patterns:
        if re.search(p, text.lower()):
            return False, "⚠️ Contenu suspect détecté"
    return True, ""

# =============================================================================
# MODÈLE FINANCIER (avec validation complète)
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
        return MetricsResult(0, math.inf, 0, False, "Coût >= Prix : marge impossible")
    
    marge_unitaire = prix - cout
    marge_pct = marge_unitaire / prix
    marge_reelle = marge_pct - cfg.SEUIL_ADS
    
    if marge_reelle <= 0:
        return MetricsResult(
            round(marge_pct * 100, 1), math.inf, 0, False,
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
# CLIENT API MISTRAL (Robuste avec retry)
# =============================================================================

class APIError(Exception):
    pass

def get_api_key() -> str:
    """Récupère la clé API de manière sécurisée"""
    key = st.secrets.get("MISTRAL_API_KEY") or os.getenv("MISTRAL_API_KEY")
    if not key:
        raise APIError("❌ Clé MISTRAL_API_KEY manquante dans Settings > Secrets ou .env")
    return key

def call_mistral_api(system_prompt: str, user_prompt: str) -> str:
    """
    Appel API Mistral avec retry exponentiel et gestion d'erreurs détaillée
    """
    api_key = get_api_key()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": cfg.MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": cfg.TEMPERATURE
    }
    
    last_error = None
    
    for attempt in range(cfg.MAX_RETRIES):
        try:
            response = requests.post(
                cfg.API_URL,
                headers=headers,
                json=payload,
                timeout=cfg.TIMEOUT
            )
            
            # Gestion codes HTTP spécifiques
            if response.status_code == 401:
                raise APIError("🔑 Clé API invalide")
            elif response.status_code == 429:
                raise APIError("⏱️ Rate limit atteint - patientez")
            elif response.status_code >= 500:
                raise APIError(f"🔥 Erreur serveur Mistral ({response.status_code})")
            
            response.raise_for_status()
            data = response.json()
            
            if not data.get("choices"):
                raise APIError("Réponse API invalide")
            
            return data["choices"][0]["message"]["content"]
            
        except requests.exceptions.Timeout:
            last_error = "Timeout"
            wait = cfg.RETRY_DELAY * (2 ** attempt)
            logger.warning(f"Tentative {attempt+1} échouée (timeout), retry dans {wait}s")
            if attempt < cfg.MAX_RETRIES - 1:
                time.sleep(wait)
                
        except requests.exceptions.ConnectionError:
            last_error = "Erreur connexion"
            wait = cfg.RETRY_DELAY * (2 ** attempt)
            logger.warning(f"Tentative {attempt+1} échouée (connexion), retry dans {wait}s")
            if attempt < cfg.MAX_RETRIES - 1:
                time.sleep(wait)
                
        except APIError:
            raise  # Ne pas retry sur erreurs client
            
        except Exception as e:
            last_error = str(e)
            logger.error(f"Erreur inattendue: {e}")
            break
    
    raise APIError(f"Échec après {cfg.MAX_RETRIES} tentatives: {last_error}")

# =============================================================================
# CACHE (Session State)
# =============================================================================

def get_cache_key(system_prompt: str, user_prompt: str) -> str:
    """Génère une clé de cache unique"""
    import hashlib
    combined = f"{system_prompt}:{user_prompt}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]

def get_cached_result(system_prompt: str, user_prompt: str) -> Optional[str]:
    """Récupère du cache si existe et valide"""
    if 'api_cache' not in st.session_state:
        st.session_state.api_cache = {}
        return None
    
    key = get_cache_key(system_prompt, user_prompt)
    entry = st.session_state.api_cache.get(key)
    
    if not entry:
        return None
    
    # Vérifier expiration (1h)
    age = (datetime.now() - datetime.fromisoformat(entry['time'])).total_seconds()
    if age > cfg.CACHE_TTL:
        del st.session_state.api_cache[key]
        return None
    
    logger.info(f"Cache hit: {key}")
    return entry['value']

def set_cached_result(system_prompt: str, user_prompt: str, value: str) -> None:
    """Stocke dans le cache"""
    if 'api_cache' not in st.session_state:
        st.session_state.api_cache = {}
    
    key = get_cache_key(system_prompt, user_prompt)
    st.session_state.api_cache[key] = {
        'value': value,
        'time': datetime.now().isoformat()
    }

def generate_with_cache(prompt_key: str, user_input: str) -> str:
    """Génère avec cache intelligent"""
    system_prompt = SYSTEM_PROMPTS.get(prompt_key, "")
    
    # Vérifier cache
    cached = get_cached_result(system_prompt, user_input)
    if cached:
        st.info("📦 Résultat chargé depuis le cache")
        return cached
    
    # Générer
    try:
        result = call_mistral_api(system_prompt, user_input)
        set_cached_result(system_prompt, user_input, result)
        return result
    except APIError as e:
        return f"❌ {e}"
    except Exception as e:
        logger.error(f"Erreur: {e}", exc_info=True)
        return f"❌ Erreur: {e}"

# =============================================================================
# INITIALISATION SESSION STATE
# =============================================================================

def init_session():
    """Initialise les variables de session"""
    defaults = {
        'results': {},
        'initialized': True
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# =============================================================================
# INTERFACE STREAMLIT
# =============================================================================

st.set_page_config(
    page_title="Brandshipping AI - Agent 10K",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🚀 Brandshipping AI - Agent 10K")
st.caption("Produit · Offre · Créatives · Acquisition | Objectif : 10K€ net/mois")

init_session()

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("📊 Cockpit IA")
    
    prix = st.number_input(
        "Prix de vente (€)", value=89.0, step=5.0,
        min_value=0.01, format="%.2f"
    )
    cout = st.number_input(
        "Coût produit (€)", value=34.0, step=1.0,
        min_value=0.0, format="%.2f"
    )
    ads_pct = st.slider("Budget Ads (% du CA)", 10, 50, 22) / 100

    metrics = calculer_metrics(prix, cout)
    
    if not metrics.is_valid:
        st.error(f"⚠️ {metrics.error}")
        st.info("💡 Ajustez prix ou coût pour continuer")
    else:
        st.metric("Marge Brute", f"{metrics.marge_pct}%")
        
        if math.isinf(metrics.ca_necessaire):
            st.metric("CA nécessaire", "∞ €")
        else:
            st.metric("CA nécessaire / mois", f"{metrics.ca_necessaire:,.0f} €")
        
        st.metric("Commandes / jour", f"{metrics.commandes_jour:.1f}")

        st.divider()
        ca_test = st.number_input(
            "CA mensuel estimé (€)", value=15930, step=500, min_value=0
        )
        
        try:
            proj = calculer_projection(ca_test, metrics.marge_pct/100, ca_test * ads_pct)
            
            col1, col2 = st.columns(2)
            delta = "✅ Rentable" if proj.is_profitable else "❌ Déficit"
            delta_color = "normal" if proj.is_profitable else "inverse"
            
            col1.metric("Résultat Net", f"{proj.resultat_net:,.0f} €", delta=delta, delta_color=delta_color)
            col2.metric("Progression 10K", f"{proj.progression_10k}%")
            st.progress(min(proj.progression_10k / 100, 1.0))
            
            if proj.progression_10k >= 100:
                st.success("🎉 Objectif atteint !")
                
        except Exception as e:
            st.error(f"Erreur calcul: {e}")

# -----------------------------------------------------------------------------
# TABS
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Stratégie", "🎁 Offre", "🎬 Créatives", "📢 Acquisition"])

with tab1:
    st.subheader("Trouver 3 produits à marge x3")
    niche = st.text_input("Niche ou passion ?", placeholder="Ex: Accessoires yoga éco-responsables", key="niche_input")
    
    if niche:
        valid, err = validate_niche(niche)
        if not valid:
            st.warning(f"⚠️ {err}")
    
    if st.button("Générer la stratégie", type="primary", key="btn_strat"):
        valid, err = validate_niche(niche)
        if not valid:
            st.error(f"❌ {err}")
        else:
            safe, warn = check_injection(niche)
            if not safe:
                st.error(warn)
            else:
                clean = sanitize_input(niche)
                with st.spinner("🔍 Analyse de niche..."):
                    result = generate_with_cache("strategie", f"Niche: {clean}. Propose 3 produits concrets avec analyse marge x3.")
                st.session_state.results['strategie'] = result
                st.markdown(result)
    
    elif 'strategie' in st.session_state.results:
        st.markdown(st.session_state.results['strategie'])

with tab2:
    st.subheader("Créer une offre Bundle Premium")
    produit = st.text_input("Produit sélectionné", placeholder="Ex: Tapis liège + Gourde inox", key="produit_input")
    
    if st.button("Générer l'offre", type="primary", key="btn_offre"):
        if not produit or len(produit.strip()) < 3:
            st.error("❌ Renseignez un produit valide (min 3 caractères)")
        else:
            safe, warn = check_injection(produit)
            if not safe:
                st.error(warn)
            else:
                clean = sanitize_input(produit)
                with st.spinner("🎨 Création de l'offre..."):
                    result = generate_with_cache("offre", f"Produit: {clean}. Crée un bundle premium irrésistible.")
                st.session_state.results['offre'] = result
                st.markdown(result)
    
    elif 'offre' in st.session_state.results:
        st.markdown(st.session_state.results['offre'])

with tab3:
    st.subheader("5 Scripts Vidéo UGC (15-30s)")
    produit_video = st.text_input("Produit pour vidéos", placeholder="Ex: Correcteur de posture", key="video_input")
    
    if st.button("Générer les scripts", type="primary", key="btn_creatives"):
        if not produit_video or len(produit_video.strip()) < 3:
            st.error("❌ Renseignez un produit valide")
        else:
            safe, warn = check_injection(produit_video)
            if not safe:
                st.error(warn)
            else:
                clean = sanitize_input(produit_video)
                with st.spinner("🎬 Génération des scripts..."):
                    result = generate_with_cache("creatives", f"Produit: {clean}. Génère 5 scripts UGC format Hook+Problème+Solution+CTA.")
                st.session_state.results['creatives'] = result
                st.markdown(result)
    
    elif 'creatives' in st.session_state.results:
        st.markdown(st.session_state.results['creatives'])

with tab4:
    st.subheader("Plan d'Acquisition & 20 Angles Pub")
    contexte = st.text_area("Contexte (cible, budget, canal)", placeholder="Femmes 25-35 ans, 50€/jour, TikTok Shop", key="context_input")
    
    if contexte and len(contexte.strip()) < 10:
        st.warning("⚠️ Contexte trop court")
    
    if st.button("Générer le plan média", type="primary", key="btn_acquisition"):
        valid, err = validate_context(contexte)
        if not valid:
            st.error(f"❌ {err}")
        else:
            safe, warn = check_injection(contexte)
            if not safe:
                st.error(warn)
            else:
                clean = sanitize_input(contexte)
                with st.spinner("📊 Élaboration du plan média..."):
                    result = generate_with_cache("acquisition", f"Contexte: {clean}. Plan test 7j + 20 angles pub.")
                st.session_state.results['acquisition'] = result
                st.markdown(result)
    
    elif 'acquisition' in st.session_state.results:
        st.markdown(st.session_state.results['acquisition'])

st.divider()
st.caption("Brandshipping AI - Agent 10K © 2026 | Propulsé par Mistral AI")
