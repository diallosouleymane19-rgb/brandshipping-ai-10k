"""
Brandshipping AI - Agent 10K
Version Ultra-Rapide - Fix connexion < 30s
"""
import os
import re
import time
import math
import logging
import socket
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from urllib.parse import urlparse

import streamlit as st
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CONFIGURATION - CONNEXION RAPIDE
# =============================================================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("brandshipping_ai")

@dataclass(frozen=True)
class Config:
    API_URL: str = "https://api.mistral.ai/v1/chat/completions"
    MODEL: str = "mistral-large-latest"
    FALLBACK_MODEL: str = "mistral-medium-latest"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 1500  # Réduit pour réponse plus rapide
    
    # ⬇️ TIMING CRITIQUE : Connexion rapide
    CONNECT_TIMEOUT: float = 8.0      # 8s max pour connecter
    READ_TIMEOUT: float = 45.0        # 45s max pour lire la réponse
    TOTAL_TIMEOUT: float = 55.0       # Timeout global
    
    MAX_RETRIES: int = 2              # 2 retries max (pas 3)
    RETRY_DELAY: float = 2.0        # Délai court
    RETRY_BACKOFF: float = 2.0
    
    OBJECTIF_10K: float = 10000.0
    SEUIL_ADS: float = 0.35
    MAX_INPUT: int = 500
    CACHE_TTL: int = 3600

cfg = Config()

# =============================================================================
# SESSION REUTILISABLE (Évite reconnexion à chaque appel)
# =============================================================================

def get_session() -> requests.Session:
    """Crée une session HTTP optimisée avec keep-alive"""
    if 'http_session' not in st.session_state:
        session = requests.Session()
        
        # Retry sur connexion/lecture seulement
        retry_strategy = Retry(
            total=cfg.MAX_RETRIES,
            backoff_factor=cfg.RETRY_DELAY,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"],
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=5,
            pool_maxsize=10
        )
        
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        # Headers keep-alive
        session.headers.update({
            "Connection": "keep-alive",
            "Accept-Encoding": "gzip, deflate"
        })
        
        st.session_state.http_session = session
        logger.info("Session HTTP créée avec keep-alive")
    
    return st.session_state.http_session

# =============================================================================
# PROMPTS (Raccourcis pour réponses plus rapides)
# =============================================================================

SYSTEM_PROMPTS = {
    "strategie": """Expert Brandshipping DTC. Analyse la niche, propose 3 produits concrets (nom, prix, coût, marge x3, 2 fournisseurs). Format: tableau markdown concis.""",

    "offre": """Copywriter expert. Bundle Premium: nom, pricing (public/valeur/offre), 3 bonus, 3 arguments, garantie, CTA. Format listé.""",

    "creatives": """Directeur créatif UGC. 5 scripts TikTok 15-30s. Par script: Hook(3s)|Problème|Solution|CTA + text overlay + 3 hashtags. Format numéroté.""",

    "acquisition": """Media buyer Meta/TikTok. Plan 7 jours: budget, 5 audiences, 20 angles (émotion/logique/urgence/social/edu), calendrier, checklist kill/scale. Tableaux."""
}

# =============================================================================
# UTILITAIRES
# =============================================================================

def sanitize(text: str) -> str:
    if not isinstance(text, str): text = str(text)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()[:cfg.MAX_INPUT]

def validate(text: str, min_len: int = 3) -> tuple[bool, str]:
    if not text or len(text.strip()) < min_len:
        return False, f"Min {min_len} caractères"
    if not re.search(r'[a-zA-Z]', text):
        return False, "Lettres requises"
    return True, ""

def check_injection(text: str) -> bool:
    patterns = [r'ignore\s+instructions', r'forget\s+everything', r'system\s*prompt', r'<\s*script\s*>']
    return not any(re.search(p, text.lower()) for p in patterns)

# =============================================================================
# FINANCIER
# =============================================================================

@dataclass
class Metrics:
    marge_pct: float; ca_nec: float; cmd_jour: float; ok: bool; err: str = ""

@dataclass
class Projection:
    ca: float; marge_brute: float; cout_ads: float; net: float; prog: float; profitable: bool

def calc_metrics(prix: float, cout: float) -> Metrics:
    if prix <= 0: return Metrics(0, 0, 0, False, "Prix > 0€")
    if cout < 0: return Metrics(0, 0, 0, False, "Coût positif")
    if cout >= prix: return Metrics(0, float('inf'), 0, False, "Coût >= Prix")
    
    marge_pct = (prix - cout) / prix
    marge_reelle = marge_pct - cfg.SEUIL_ADS
    
    if marge_reelle <= 0:
        return Metrics(round(marge_pct*100,1), float('inf'), 0, False, 
                      f"Marge {marge_pct*100:.0f}% < {cfg.SEUIL_ADS*100:.0f}%")
    
    ca_nec = cfg.OBJECTIF_10K / marge_reelle
    return Metrics(round(marge_pct*100,1), round(ca_nec,2), round((ca_nec/prix)/30,1), True)

def calc_projection(ca: float, marge_pct: float, cout_ads: float) -> Projection:
    marge_brute = ca * marge_pct
    net = marge_brute - cout_ads
    return Projection(ca, round(marge_brute,2), round(cout_ads,2), 
                     round(net,2), round(min(net/cfg.OBJECTIF_10K*100,100),1), net>0)

# =============================================================================
# API MISTRAL - ULTRA RAPIDE
# =============================================================================

class APIError(Exception): pass

def get_key() -> str:
    key = st.secrets.get("MISTRAL_API_KEY") or os.getenv("MISTRAL_API_KEY")
    if not key: raise APIError("Clé MISTRAL_API_KEY manquante")
    return key

def test_dns_resolution() -> bool:
    """Test rapide si api.mistral.ai est joignable"""
    try:
        socket.getaddrinfo("api.mistral.ai", None, socket.AF_INET, socket.SOCK_STREAM)
        return True
    except:
        return False

def call_api(system: str, user: str, use_fallback: bool = False) -> str:
    """Appel API optimisé pour connexion < 30s"""
    
    # Test DNS rapide avant appel
    if not test_dns_resolution():
        raise APIError("🌐 Impossible de résoudre api.mistral.ai - Vérifiez votre connexion internet")
    
    key = get_key()
    model = cfg.FALLBACK_MODEL if use_fallback else cfg.MODEL
    
    session = get_session()
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "temperature": cfg.TEMPERATURE,
        "max_tokens": cfg.MAX_TOKENS
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}"
    }
    
    last_err = None
    
    for attempt in range(cfg.MAX_RETRIES + 1):  # +1 pour tentative initiale
        try:
            # ⏱️ Timeout court : connexion rapide, lecture modérée
            resp = session.post(
                cfg.API_URL,
                headers=headers,
                json=payload,
                timeout=(cfg.CONNECT_TIMEOUT, cfg.READ_TIMEOUT)
            )
            
            if resp.status_code == 401: 
                raise APIError("🔑 Clé API invalide")
            if resp.status_code == 429: 
                raise APIError("⏱️ Rate limit")
            if resp.status_code >= 500: 
                raise APIError(f"🔥 Serveur {resp.status_code}")
            
            resp.raise_for_status()
            data = resp.json()
            
            if not data.get("choices"): 
                raise APIError("Réponse vide")
            
            content = data["choices"][0].get("message", {}).get("content")
            if not content: 
                raise APIError("Contenu vide")
            
            logger.info(f"✅ {len(content)} chars | {model} | {attempt+1} tentative(s)")
            return content
            
        except requests.exceptions.ConnectTimeout:
            last_err = f"Connexion timeout ({cfg.CONNECT_TIMEOUT}s) - serveur injoignable"
            wait = cfg.RETRY_DELAY * (cfg.RETRY_BACKOFF ** attempt)
            logger.warning(f"⏱️ Connect timeout, retry {attempt+1} dans {wait:.1f}s")
            if attempt < cfg.MAX_RETRIES: 
                time.sleep(wait)
                
        except requests.exceptions.ReadTimeout:
            last_err = f"Lecture timeout ({cfg.READ_TIMEOUT}s) - réponse trop lente"
            # Pas de retry sur read timeout, essayer fallback
            if not use_fallback:
                logger.info("🔄 Bascule fallback...")
                try:
                    return call_api(system, user, use_fallback=True)
                except:
                    pass
            raise APIError(f"⏱️ {last_err}\n\nL'API est lente. Réessayez ou utilisez une connexion plus stable.")
            
        except requests.exceptions.ConnectionError as e:
            last_err = f"Connexion impossible: {str(e)[:50]}"
            wait = cfg.RETRY_DELAY * (cfg.RETRY_BACKOFF ** attempt)
            if attempt < cfg.MAX_RETRIES: 
                time.sleep(wait)
                
        except APIError: 
            raise
        except Exception as e:
            last_err = str(e)[:100]
            break
    
    # Fallback automatique si échec avec modèle principal
    if not use_fallback:
        logger.info("🔄 Tentative avec modèle fallback...")
        try:
            return call_api(system, user, use_fallback=True)
        except APIError:
            pass
    
    raise APIError(
        f"❌ Échec après {cfg.MAX_RETRIES} tentatives.\n\n"
        f"**Dernier problème:** {last_err}\n\n"
        f"**Conseils:**\n• Vérifiez votre connexion (test DNS: {test_dns_resolution()})\n"
        f"• Réessayez dans 1 minute\n"
        f"• L'API Mistral peut être temporairement indisponible"
    )

# =============================================================================
# CACHE
# =============================================================================

def cache_key(system: str, user: str) -> str:
    import hashlib
    return hashlib.sha256(f"{system}:{user}".encode()).hexdigest()[:16]

def cache_get(system: str, user: str) -> Optional[str]:
    if 'cache' not in st.session_state: 
        st.session_state.cache = {}
    key = cache_key(system, user)
    entry = st.session_state.cache.get(key)
    if not entry: 
        return None
    if (datetime.now() - datetime.fromisoformat(entry['t'])).total_seconds() > cfg.CACHE_TTL:
        del st.session_state.cache[key]
        return None
    return entry['v']

def cache_set(system: str, user: str, value: str):
    if 'cache' not in st.session_state: 
        st.session_state.cache = {}
    st.session_state.cache[cache_key(system, user)] = {'v': value, 't': datetime.now().isoformat()}

def generate(prompt_key: str, user_input: str) -> str:
    system = SYSTEM_PROMPTS.get(prompt_key, "")
    
    cached = cache_get(system, user_input)
    if cached:
        st.success("📦 Cache")
        return cached
    
    try:
        with st.spinner("🤖 Génération... (~10-20s)"):
            result = call_api(system, user_input)
        cache_set(system, user_input, result)
        return result
    except APIError as e:
        st.error(str(e))
        return f"❌ {e}"
    except Exception as e:
        logger.error(f"Erreur: {e}")
        return f"❌ {e}"

# =============================================================================
# SESSION
# =============================================================================

def init():
    for k, v in {'results': {}, 'init': True}.items():
        if k not in st.session_state: 
            st.session_state[k] = v

# =============================================================================
# UI
# =============================================================================

st.set_page_config(page_title="Brandshipping AI - Agent 10K", page_icon="🚀", layout="wide")
st.title("🚀 Brandshipping AI - Agent 10K")
st.caption("Produit · Offre · Créatives · Acquisition | Objectif : 10K€ net/mois")

init()

# --- SIDEBAR ---
with st.sidebar:
    st.header("📊 Cockpit IA")
    
    prix = st.number_input("Prix vente (€)", value=89.0, step=5.0, min_value=0.01)
    cout = st.number_input("Coût produit (€)", value=34.0, step=1.0, min_value=0.0)
    ads_pct = st.slider("Budget Ads (% CA)", 10, 50, 22) / 100

    m = calc_metrics(prix, cout)
    
    if not m.ok:
        st.error(f"⚠️ {m.err}")
    else:
        st.metric("Marge", f"{m.marge_pct}%")
        st.metric("CA/mois", f"{m.ca_nec:,.0f} €" if not math.isinf(m.ca_nec) else "∞ €")
        st.metric("Cmd/jour", f"{m.cmd_jour:.1f}")

        st.divider()
        ca_test = st.number_input("CA estimé (€)", value=15930, step=500, min_value=0)
        
        p = calc_projection(ca_test, m.marge_pct/100, ca_test*ads_pct)
        c1, c2 = st.columns(2)
        c1.metric("Net", f"{p.net:,.0f} €", "✅" if p.profitable else "❌", 
                 "normal" if p.profitable else "inverse")
        c2.metric("10K", f"{p.prog}%")
        st.progress(min(p.prog/100, 1.0))
        if p.prog >= 100: 
            st.success("🎉 Objectif !")

# --- TABS ---
t1, t2, t3, t4 = st.tabs(["🎯 Stratégie", "🎁 Offre", "🎬 Créatives", "📢 Acquisition"])

def render_tab(tab, key, title, label, placeholder, prompt_key, template, min_len=3):
    with tab:
        st.subheader(title)
        val = st.text_input(label, placeholder=placeholder, key=f"in_{key}")
        
        if val and len(val.strip()) < min_len:
            st.warning(f"Min {min_len} caractères")
        
        if st.button("Générer", type="primary", key=f"btn_{key}", use_container_width=True):
            ok, err = validate(val, min_len)
            if not ok:
                st.error(err)
            elif not check_injection(val):
                st.error("⚠️ Contenu suspect")
            else:
                result = generate(prompt_key, template.format(sanitize(val)))
                if not result.startswith("❌"):
                    st.session_state.results[key] = result
                st.markdown(result)
        
        elif key in st.session_state.results:
            st.markdown(st.session_state.results[key])

render_tab(t1, "strat", "3 produits à marge x3", 
           "Niche ou passion ?", "Accessoires yoga éco-responsables",
           "strategie", "Niche: {}. 3 produits concrets marge x3.")

render_tab(t2, "offre", "Offre Bundle Premium",
           "Produit sélectionné", "Tapis liège + Gourde inox",
           "offre", "Produit: {}. Bundle premium.")

render_tab(t3, "creat", "5 Scripts UGC",
           "Produit pour vidéos", "Correcteur de posture",
           "creatives", "Produit: {}. 5 scripts UGC.")

render_tab(t4, "acqui", "Plan Acquisition",
           "Contexte (cible, budget, canal)", "Femmes 25-35 ans, 50€/jour, TikTok",
           "acquisition", "Contexte: {}. Plan 7j + 20 angles.", min_len=10)

st.divider()
st.caption("Brandshipping AI - Agent 10K © 2026 | Propulsé par Mistral AI")
