"""
Brandshipping AI - Agent 10K
Version Pro - Gestion timeout & retry améliorée
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
    """Configuration centralisée - TIMEOUTS AUGMENTÉS"""
    API_URL: str = "https://api.mistral.ai/v1/chat/completions"
    MODEL: str = "mistral-large-latest"
    TEMPERATURE: float = 0.7
    TIMEOUT: int = 120  # ⬆️ Augmenté à 120s (était 60s)
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 3.0  # ⬆️ Délai initial augmenté
    RETRY_BACKOFF: float = 2.5  # ⬆️ Backoff plus agressif
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
# CLIENT API MISTRAL - CORRIGÉ POUR TIMEOUTS
# =============================================================================

class APIError(Exception):
    pass

def get_api_key() -> str:
    """Récupère la clé API"""
    key = st.secrets.get("MISTRAL_API_KEY") or os.getenv("MISTRAL_API_KEY")
    if not key:
        raise APIError("❌ Clé MISTRAL_API_KEY manquante dans Settings > Secrets ou .env")
    return key

def call_mistral_api(system_prompt: str, user_prompt: str) -> str:
    """
    Appel API Mistral avec gestion robuste des timeouts et retry exponentiel
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
            # ⬆️ Timeout augmenté + gestion connexion séparée
            response = requests.post(
                cfg.API_URL,
                headers=headers,
                json=payload,
                timeout=(10, cfg.TIMEOUT)  # (connect timeout, read timeout)
            )
            
            # Gestion codes HTTP spécifiques
            if response.status_code == 401:
                raise APIError("🔑 Clé API invalide - vérifiez votre MISTRAL_API_KEY")
            elif response.status_code == 429:
                raise APIError("⏱️ Rate limit atteint - patientez quelques minutes")
            elif response.status_code == 422:
                detail = response.json().get("detail", "Données invalides")
                raise APIError(f"❌ Erreur de validation: {detail}")
            elif response.status_code >= 500:
                raise APIError(f"🔥 Erreur serveur Mistral ({response.status_code}) - Réessayez plus tard")
            
            response.raise_for_status()
            data = response.json()
            
            if not data.get("choices"):
                raise APIError("Réponse API invalide: aucun contenu généré")
            
            content = data["choices"][0].get("message", {}).get("content")
            if not content:
                raise APIError("Réponse API vide")
            
            logger.info(f"✅ Génération réussie ({len(content)} caractères)")
            return content
            
        except requests.exceptions.ConnectTimeout:
            last_error = "Timeout connexion (serveur injoignable)"
            wait = cfg.RETRY_DELAY * (cfg.RETRY_BACKOFF ** attempt)
            logger.warning(f"⏱️ Tentative {attempt+1}/{cfg.MAX_RETRIES} - Connexion timeout, retry dans {wait:.1f}s")
            if attempt < cfg.MAX_RETRIES - 1:
                time.sleep(wait)
                
        except requests.exceptions.ReadTimeout:
            last_error = "Timeout lecture (réponse trop lente)"
            wait = cfg.RETRY_DELAY * (cfg.RETRY_BACKOFF ** attempt)
            logger.warning(f"⏱️ Tentative {attempt+1}/{cfg.MAX_RETRIES} - Read timeout, retry dans {wait:.1f}s")
            if attempt < cfg.MAX_RETRIES - 1:
                time.sleep(wait)
                
        except requests.exceptions.ConnectionError as e:
            last_error = f"Erreur connexion: {str(e)}"
            wait = cfg.RETRY_DELAY * (cfg.RETRY_BACKOFF ** attempt)
            logger.warning(f"🔌 Tentative {attempt+1}/{cfg.MAX_RETRIES} - Erreur connexion, retry dans {wait:.1f}s")
            if attempt < cfg.MAX_RETRIES - 1:
                time.sleep(wait)
                
        except APIError:
            raise  # Ne pas retry sur erreurs client (401, 422, etc.)
            
        except requests.exceptions.RequestException as e:
            last_error = f"Erreur réseau: {str(e)}"
            wait = cfg.RETRY_DELAY * (cfg.RETRY_BACKOFF ** attempt)
            logger.warning(f"🌐 Tentative {attempt+1}/{cfg.MAX_RETRIES} - {last_error}, retry dans {wait:.1f}s")
            if attempt < cfg.MAX_RETRIES - 1:
                time.sleep(wait)
                
        except Exception as e:
            last_error = f"Erreur inattendue: {str(e)}"
            logger.error(f"💥 Erreur critique: {e}", exc_info=True)
            break
    
    # Message final clair pour l'utilisateur
    raise APIError(
        f"⏱️ Échec après {cfg.MAX_RETRIES} tentatives.\n\n"
        f"**Dernière erreur:** {last_error}\n\n"
        f"**Solutions possibles:**\n"
        f"• Vérifiez votre connexion internet\n"
        f"• L'API Mistral peut être temporairement surchargée\n"
        f"• Réessayez dans 1-2 minutes\n"
        f"• Si le problème persiste, contactez le support Mistral"
    )

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
    
    age = (datetime.now() - datetime.fromisoformat(entry['time'])).total_seconds()
    if age > cfg.CACHE_TTL:
        del st.session_state.api_cache[key]
        return None
    
    logger.info(f"📦 Cache hit: {key}")
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
        st.success("📦 Résultat chargé depuis le cache (pas d'appel API)")
        return cached
    
    # Générer avec indicateur de progression
    try:
        with st.status("🤖 Appel API Mistral en cours...", expanded=True) as status:
            st.write("⏳ Connexion à l'API...")
            result = call_mistral_api(system_prompt, user_input)
            st.write("✅ Réponse reçue !")
            status.update(label="Génération terminée", state="complete")
        
        set_cached_result(system_prompt, user_input, result)
        return result
        
    except APIError as e:
        st.error(str(e))
        # Option de retry manuel
        if st.button("🔄 Réessayer maintenant", key=f"retry_{prompt_key}"):
            return generate_with_cache(prompt_key, user_input)
        return f"❌ {e}"
        
    except Exception as e:
        logger.error(f"Erreur: {e}", exc_info=True)
        return f"❌ Erreur inattendue: {e}"

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
                result = generate_with_cache("strategie", f"Niche: {clean}. Propose 3 produits concrets avec analyse marge x3.")
                if not result.startswith("❌"):
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
                result = generate_with_cache("offre", f"Produit: {clean}. Crée un bundle premium irrésistible.")
                if not result.startswith("❌"):
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
                result = generate_with_cache("creatives", f"Produit: {clean}. Génère 5 scripts UGC format Hook+Problème+Solution+CTA.")
                if not result.startswith("❌"):
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
                result = generate_with_cache("acquisition", f"Contexte: {clean}. Plan test 7j + 20 angles pub.")
                if not result.startswith("❌"):
                    st.session_state.results['acquisition'] = result
                st.markdown(result)
    
    elif 'acquisition' in st.session_state.results:
        st.markdown(st.session_state.results['acquisition'])

st.divider()
st.caption("Brandshipping AI - Agent 10K © 2026 | Propulsé par Mistral AI")
