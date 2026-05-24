"""
Brandshipping AI - Agent 10K
Version Finale - Optimisée pour performances
"""
import os
import re
import time
import math
import logging
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("brandshipping_ai")

@dataclass(frozen=True)
class Config:
    API_URL: str = "https://api.mistral.ai/v1/chat/completions"
    MODEL: str = "mistral-large-latest"
    FALLBACK_MODEL: str = "mistral-medium-latest"  # Plus rapide si timeout
    TEMPERATURE: float = 0.7
    TIMEOUT: int = 120
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 3.0
    RETRY_BACKOFF: float = 2.5
    OBJECTIF_10K: float = 10000.0
    SEUIL_ADS: float = 0.35
    MAX_INPUT: int = 500
    CACHE_TTL: int = 3600

cfg = Config()

# =============================================================================
# PROMPTS
# =============================================================================

SYSTEM_PROMPTS = {
    "strategie": """Tu es un expert en Brandshipping et e-commerce DTC. 
Analyse la niche et propose 3 produits concrets avec marge minimum x3.
Format: tableau markdown avec prix, coût, marge, fournisseurs.""",

    "offre": """Tu es un copywriter expert. Crée un Bundle Premium avec:
- Nom accrocheur
- Pricing psychologique (prix public / valeur / offre)
- 3-5 bonus perçus
- 3 arguments de vente
- Garantie + CTA""",

    "creatives": """Directeur créatif UGC. Génère 5 scripts TikTok/Reels 15-30s.
Format par script: Hook(3s) | Problème | Solution | CTA + text overlay + hashtags.""",

    "acquisition": """Media buyer expert Meta/TikTok Ads. Plan test 7 jours:
- Budget et KPIs cibles
- 5-7 audiences
- 20 angles publicitaires classés
- Calendrier jour par jour
- Checklist optimisation"""
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
        return False, f"Minimum {min_len} caractères requis"
    if not re.search(r'[a-zA-Z]', text):
        return False, "Doit contenir des lettres"
    return True, ""

def check_injection(text: str) -> bool:
    patterns = [r'ignore\s+instructions', r'forget\s+everything', r'system\s*prompt', r'<\s*script\s*>']
    return not any(re.search(p, text.lower()) for p in patterns)

# =============================================================================
# FINANCIER
# =============================================================================

@dataclass
class Metrics:
    marge_pct: float
    ca_nec: float
    cmd_jour: float
    ok: bool
    err: str = ""

@dataclass
class Projection:
    ca: float
    marge_brute: float
    cout_ads: float
    net: float
    prog: float
    profitable: bool

def calc_metrics(prix: float, cout: float) -> Metrics:
    if prix <= 0: return Metrics(0, 0, 0, False, "Prix > 0€ requis")
    if cout < 0: return Metrics(0, 0, 0, False, "Coût positif requis")
    if cout >= prix: return Metrics(0, float('inf'), 0, False, "Coût >= Prix impossible")
    
    marge_pct = (prix - cout) / prix
    marge_reelle = marge_pct - cfg.SEUIL_ADS
    
    if marge_reelle <= 0:
        return Metrics(round(marge_pct*100,1), float('inf'), 0, False, 
                      f"Marge {marge_pct*100:.0f}% < {cfg.SEUIL_ADS*100:.0f}% requis")
    
    ca_nec = cfg.OBJECTIF_10K / marge_reelle
    return Metrics(round(marge_pct*100,1), round(ca_nec,2), round((ca_nec/prix)/30,1), True)

def calc_projection(ca: float, marge_pct: float, cout_ads: float) -> Projection:
    marge_brute = ca * marge_pct
    net = marge_brute - cout_ads
    return Projection(ca, round(marge_brute,2), round(cout_ads,2), 
                     round(net,2), round(min(net/cfg.OBJECTIF_10K*100,100),1), net>0)

# =============================================================================
# API MISTRAL - OPTIMISÉ
# =============================================================================

class APIError(Exception): pass

def get_key() -> str:
    key = st.secrets.get("MISTRAL_API_KEY") or os.getenv("MISTRAL_API_KEY")
    if not key: raise APIError("Clé MISTRAL_API_KEY manquante dans Secrets ou .env")
    return key

def call_api(system: str, user: str, use_fallback: bool = False) -> str:
    """Appel API avec retry, fallback modèle, et gestion timeout avancée"""
    key = get_key()
    model = cfg.FALLBACK_MODEL if use_fallback else cfg.MODEL
    
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": cfg.TEMPERATURE,
        "max_tokens": 2000  # Limite pour réponses plus rapides
    }
    
    last_err = None
    
    for attempt in range(cfg.MAX_RETRIES):
        try:
            resp = requests.post(cfg.API_URL, headers=headers, json=payload, 
                              timeout=(10, cfg.TIMEOUT))
            
            if resp.status_code == 401: raise APIError("🔑 Clé API invalide")
            if resp.status_code == 429: raise APIError("⏱️ Rate limit - patientez")
            if resp.status_code >= 500: raise APIError(f"🔥 Serveur Mistral {resp.status_code}")
            
            resp.raise_for_status()
            data = resp.json()
            
            if not data.get("choices"): raise APIError("Réponse vide")
            content = data["choices"][0].get("message", {}).get("content")
            if not content: raise APIError("Contenu vide")
            
            logger.info(f"✅ {len(content)} chars | Modèle: {model}")
            return content
            
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError) as e:
            last_err = str(e)
            wait = cfg.RETRY_DELAY * (cfg.RETRY_BACKOFF ** attempt)
            logger.warning(f"⏱️ Retry {attempt+1}/{cfg.MAX_RETRIES} dans {wait:.1f}s")
            if attempt < cfg.MAX_RETRIES - 1: time.sleep(wait)
            
        except APIError: raise
        except Exception as e:
            last_err = str(e)
            break
    
    # Si échec avec modèle principal, essayer fallback
    if not use_fallback:
        logger.info("🔄 Bascule vers modèle fallback...")
        try:
            return call_api(system, user, use_fallback=True)
        except APIError:
            pass
    
    raise APIError(
        f"⏱️ Échec après {cfg.MAX_RETRIES} tentatives.\n\n"
        f"**Erreur:** {last_err}\n\n"
        f"**Solutions:**\n"
        f"• Vérifiez votre connexion\n"
        f"• Réessayez dans 1-2 min\n"
        f"• L'API Mistral peut être surchargée"
    )

# =============================================================================
# CACHE
# =============================================================================

def cache_key(system: str, user: str) -> str:
    import hashlib
    return hashlib.sha256(f"{system}:{user}".encode()).hexdigest()[:16]

def cache_get(system: str, user: str) -> Optional[str]:
    if 'cache' not in st.session_state: st.session_state.cache = {}
    key = cache_key(system, user)
    entry = st.session_state.cache.get(key)
    if not entry: return None
    if (datetime.now() - datetime.fromisoformat(entry['t'])).total_seconds() > cfg.CACHE_TTL:
        del st.session_state.cache[key]
        return None
    return entry['v']

def cache_set(system: str, user: str, value: str):
    if 'cache' not in st.session_state: st.session_state.cache = {}
    st.session_state.cache[cache_key(system, user)] = {'v': value, 't': datetime.now().isoformat()}

def generate(prompt_key: str, user_input: str) -> str:
    system = SYSTEM_PROMPTS.get(prompt_key, "")
    
    # Cache
    cached = cache_get(system, user_input)
    if cached:
        st.success("📦 Depuis le cache")
        return cached
    
    # Génération avec UI de progression
    try:
        with st.spinner("🤖 Génération en cours... (peut prendre 30-60s)"):
            result = call_api(system, user_input)
        cache_set(system, user_input, result)
        return result
    except APIError as e:
        st.error(str(e))
        return f"❌ {e}"
    except Exception as e:
        logger.error(f"Erreur: {e}")
        return f"❌ Erreur: {e}"

# =============================================================================
# SESSION
# =============================================================================

def init():
    for k, v in {'results': {}, 'init': True}.items():
        if k not in st.session_state: st.session_state[k] = v

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
        st.metric("CA/mois nécessaire", f"{m.ca_nec:,.0f} €" if not math.isinf(m.ca_nec) else "∞ €")
        st.metric("Cmd/jour", f"{m.cmd_jour:.1f}")

        st.divider()
        ca_test = st.number_input("CA mensuel estimé (€)", value=15930, step=500, min_value=0)
        
        p = calc_projection(ca_test, m.marge_pct/100, ca_test*ads_pct)
        c1, c2 = st.columns(2)
        c1.metric("Net", f"{p.net:,.0f} €", "✅" if p.profitable else "❌", 
                 "normal" if p.profitable else "inverse")
        c2.metric("10K", f"{p.prog}%")
        st.progress(min(p.prog/100, 1.0))
        if p.prog >= 100: st.success("🎉 Objectif atteint !")

# --- TABS ---
t1, t2, t3, t4 = st.tabs(["🎯 Stratégie", "🎁 Offre", "🎬 Créatives", "📢 Acquisition"])

def render_tab(tab, key, title, placeholder, prompt_key, template, min_len=3):
    with tab:
        st.subheader(title)
        val = st.text_input(placeholder.split(" | ")[0], placeholder=placeholder.split(" | ")[1], key=f"in_{key}")
        
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

render_tab(t1, "strat", "Trouver 3 produits à marge x3", 
           "Niche ou passion ? | Ex: Accessoires yoga éco-responsables",
           "strategie", "Niche: {}. Propose 3 produits concrets avec analyse marge x3.")

render_tab(t2, "offre", "Créer une offre Bundle Premium",
           "Produit sélectionné | Ex: Tapis liège + Gourde inox",
           "offre", "Produit: {}. Crée un bundle premium irrésistible.")

render_tab(t3, "creat", "5 Scripts Vidéo UGC (15-30s)",
           "Produit pour vidéos | Ex: Correcteur de posture",
           "creatives", "Produit: {}. Génère 5 scripts UGC Hook+Problème+Solution+CTA.")

render_tab(t4, "acqui", "Plan d'Acquisition & 20 Angles Pub",
           "Contexte (cible, budget, canal) | Femmes 25-35 ans, 50€/jour, TikTok Shop",
           "acquisition", "Contexte: {}. Plan test 7j + 20 angles pub.", min_len=10)

st.divider()
st.caption("Brandshipping AI - Agent 10K © 2026 | Propulsé par Mistral AI")
