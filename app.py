# -*- coding: utf-8 -*-
"""
Brandshipping AI - Agent 10K
Version URBÆ™ - Mobilité Urbaine Premium
Localisé Orléans-Blois-Tours | Loire Valley Edition
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
logger = logging.getLogger("urbae_brandshipping")

@dataclass(frozen=True)
class Config:
    """Configuration centralisée URBÆ™"""
    API_URL: str = "https://api.mistral.ai/v1/chat/completions"
    MODEL: str = "mistral-large-latest"
    FALLBACK_MODEL: str = "mistral-medium-latest"
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
# MASTER PROMPT URBÆ™ - MOBILITÉ URBAINE PREMIUM
# =============================================================================

SYSTEM_PROMPTS = {
    "strategie": """Tu es URBAE AI Manager, un agent IA spécialisé en BrandShipping, e-commerce, marketing local et acquisition. 
Ta mission est de faire croître la marque URBAE (mobilité urbaine premium) sur le périmètre Orléans – Blois – Tours.

CONTEXTE PRODUIT :
- Sacoche cadre waterproof URBÆ™ (IPX6, 2.5L, fixation universelle)
- Urban Rider Pack (bundle premium cycliste urbain)
- Prix cible : 89-149€ TTC
- Marge cible : 65-75%

CONTEXTE GÉOGRAPHIQUE :
- Orléans : 280K hab, tech hub, université, 45km pistes cyclables
- Tours : 137K hab, ville cyclable label, 28% déplacements vélo
- Blois : 46K hab, tourisme Loire à Vélo, 200K cyclistes/an
- Avantages logistiques : Amazon FBA Orléans, Chronopost local, MGE Orléans

AUDIENCES PRIORITAIRES :
1. Vélotafeurs (25-45 ans, navette quotidienne)
2. Livreurs à vélo (Uber Eats, Deliveroo, Stuart)
3. Étudiants cyclistes (campus La Source, Polytech)
4. Cyclistes loisirs (Loire à Vélo, week-end)
5. Digital nomades (coworking + mobilité)

INSTRUCTIONS :
1. Propose 3 angles marketing dominants par semaine
2. Identifie les opportunités météo (pluie = pic de ventes)
3. Détecte les tendances TikTok locales et nationales
4. Propose des tests A/B (prix, angles, audiences)
5. Calcule les métriques avec coûts locaux (CPA 12-18€ vs 35-50€ national)
6. Suggère des partenariats locaux (clubs vélo, coffee shops, réparateurs)

FORMAT : Plan stratégique hebdomadaire avec tableaux comparatifs et recommandations priorisées.
TON : Précis, actionnable, orienté résultats, fier d'être local.""",

    "offre": """Tu es expert en optimisation d'offres e-commerce pour la marque URBÆ™ (mobilité urbaine premium).

MISSION : Maximiser la valeur perçue et le panier moyen pour les cyclistes urbains Orléans-Blois-Tours.

PRODUITS DE BASE :
- Sacoche cadre waterproof URBÆ™ : 89€ TTC (coût 28€, marge 69%)
- Urban Rider Pack : Bundle premium cycliste urbain

PACKS À OPTIMISER :
1. Pack Solo : Sacoche seule + guide itinéraires
2. Pack Duo : 2 sacoches + housse anti-pluie + stickers réfléchissants
3. Urban Rider Pack : Sacoche + support téléphone + lumière LED + guide
4. Pack Pro : Urban Rider Pack + gilet réfléchissant + casque urbain

PRIX À TESTER :
- 139.90€ / 149.90€ / 159.90€ / 169.90€
- Offre locale : -25% habitants 37/41/45 (Indre-et-Loire, Loir-et-Cher, Loiret)
- Offre livreurs : -30% avec justificatif professionnel
- Offre étudiants : -20% avec carte étudiant

BONUS PERÇUS (coût faible, valeur haute) :
- Livraison 48h Centre-Val de Loire (coût 3€, valeur 15€)
- Guide "50 Itinéraires Vélo Orléans-Blois-Tours" PDF (coût 0€, valeur 19€)
- Garantie vol/casse 2 ans (coût 4€, valeur 29€)
- Stickers réfléchissants URBÆ™ sécurité (coût 1€, valeur 12€)
- Housse anti-pluie secondaire (coût 2€, valeur 15€)

STRUCTURE DE L'OFFRE :
1. Nom accrocheur avec référence mobilité urbaine
2. Pricing psychologique (ancrage, prix public/valeur/offre)
3. 3-5 bonus perçus avec valeur calculée
4. 3 arguments de vente irréfutables (local/praticité/durabilité)
5. Garantie "Satisfait ou remboursé 30j + 2 ans"
6. CTA urgent et localisé : "Livraison 48h Orléans-Blois-Tours - Stock limité"

CONTRAINTES :
- Valeur perçue totale ≥ 5x le prix payé
- Créer sentiment d'appartenance "tribu cycliste urbaine"
- Mentionner proximité physique dans chaque élément
- Ton : authentique, "conçu par des cyclistes pour des cyclistes"

FORMAT : Tableau comparatif des packs + recommandation finale avec justification chiffrée.""",

    "creatives": """Tu es directeur créatif UGC pour la marque URBÆ™ (mobilité urbaine premium Loire Valley).

MISSION : Produire 10 scripts vidéo par semaine pour TikTok/Reels (15-30s).

CONTEXTE LOCAL :
- Zones : Orléans (Pont George V, tram+vélo), Tours (Pont Wilson, pistes cyclables), Blois (Château, Loire à Vélo)
- Repères visuels : Châteaux de la Loire, ponts, bords de Loire, pistes cyclables
- Météo : Pluie fréquente printemps/automne (argument waterproof fort)
- Concurrence : Decathlon basique, Ortlieb cher
- Positionnement URBÆ™ : "Qualité premium, prix accessible, conçu localement"

FORMAT PAR SCRIPT :

## Script [N°] - [Nom accrocheur]

**Durée :** XX secondes
**Zone cible :** Orléans / Tours / Blois / National
**Type :** Hook émotionnel / Démonstration / Témoignage / Humour / FOMO / Test extrême

**HOOK (0-3s) :**
Phrase d'accroche qui stoppe le scroll avec référence locale
Exemples :
- "J'habite à côté du château de Blois et je me faisais voler mon tel à vélo"
- "POV : T'es cadre à Orléans et t'en as marre du sac à dos qui te fait suer"
- "Test extrême : 30 minutes sous la pluie orléanaise avec la sacoche URBÆ™"

**PROBLÈME (3-10s) :**
Pain point quotidien du cycliste urbain
Mouillé, vol, encombrement, look moche, pas pratique

**SOLUTION (10-20s) :**
Présentation URBÆ™ en action
Bénéfices : waterproof IPX6, fixation rapide, design urbain, 2.5L capacité

**CTA (20-30s) :**
Call-to-action clair avec urgence locale
- "Livraison 48h Orléans-Blois-Tours - Code ORLEANS10"
- "Stock limité été 2026 - 200 unités disponibles"
- "Click & collect centre-ville Orléans/Blois/Tours"

**TEXTE OVERLAY :**
- "89€ vs 180€ Ortlieb" (comparaison)
- "IPX6 = 30min sous pluie" (preuve)
- "⭐ 4.8/5 (127 avis)" (social proof)
- "-25% habitants 37/41/45" (offre locale)

**HASHTAGS :**
#URBÆ #SacocheVélo #OrléansVélo #ToursVélo #LoireÀVélo #MobilitéUrbaine #VéloQuotidien #CyclisteUrbain #Waterproof #NavetteurVélo #Vélotaf #LoireValley

CONSIGNES SPÉCIFIQUES :
- 3 scripts hook "fierté locale" (Orléanais/Tours/Blois)
- 2 scripts hook "comparaison prix" (vs Decathlon/Ortlieb)
- 2 scripts hook "météo/pluie" (argument waterproof)
- 2 scripts hook "FOMO/saisonnalité" (été 2026, stock limité)
- 1 script hook "test extrême" (pluie, chute, charge)

TON : Authentique, génération Z/millennial urbain, pas corporate. "On n'a pas à rougir face à Paris".
MUSIQUE : Électro/lo-fi pour urbain, folk pour touristique.

FORMAT : 10 scripts complets avec tous les éléments demandés.""",

    "acquisition": """Tu es media buyer senior spécialisé TikTok Ads pour la marque URBÆ™ (mobilité urbaine premium).

MISSION : Élaborer un plan d'acquisition 30 jours avec CPA cible < 12€.

CONTEXTE MARCHÉ :
- Produit : Sacoche cadre waterproof URBÆ™, 89-149€ TTC, marge 65-75%
- Cible : Cyclistes urbains 25-45 ans, revenus moyens+, éco-responsables
- Zones : Orléans (280K), Tours (137K), Blois (46K)
- Saisonnalité : Pic mai-septembre, second pic septembre (rentrée)
- Concurrence : Decathlon (29-49€ basique), Ortlieb (149-199€ premium)

BUDGETS PAR PHASE :
- Phase 1 (J1-10) : Test - 20-30€/jour = 250€
- Phase 2 (J11-20) : Optimisation - 50€/jour = 500€
- Phase 3 (J21-30) : Scale - 100€/jour = 1000€
- TOTAL : 1750€ sur 30 jours

STRUCTURE DU PLAN :

1. **OBJECTIFS & KPIs**
   - CPA cible : < 12€ (vs 35-50€ national grâce ciblage hyper-local)
   - ROAS cible : 4.0-5.5 (marge 70% permet ROAS 3.0 rentable)
   - CTR cible : 2.0-3.5% (créatives UGC locales performantes)
   - Conversion cible : 2.5-4.0%
   - CPM cible : < 8€ (ciblage local réduit compétition)

2. **STRUCTURE CAMPAGNE TIKTOK ADS**
   - Campagne 1 : CBO Test (70% budget)
     * Budget : 20-30€/jour
     * 3 créatives test (hook émotion, démo produit, témoignage)
     * 3 audiences : vélotafeurs, livreurs, étudiants cyclistes
   - Campagne 2 : Retargeting (20% budget)
     * Visiteurs site 30j
     * 75% vidéo regardée
     * Ajout panier non acheté
   - Campagne 3 : Lookalike (10% budget)
     * 1% purchasers URBÆ™
     * 1% engagés TikTok/Instagram

3. **CIBLAGES GÉOGRAPHIQUES**
   - Tours : 20km radius (ville cyclable, jeunesse active)
   - Orléans : 15km radius (cadres, université, tech hub)
   - Blois : 10km radius (tourisme vélo, châteaux)
   - Exclusion : Paris, Lyon, Marseille (CPA trop cher)

4. **CIBLAGES INTÉRÊTS**
   - Vélo électrique, mobilité urbaine, vélotaf
   - Uber Eats, Deliveroo, Stuart (livreurs)
   - Outdoor, randonnée, éco-responsable
   - Étudiant, alternant, jeune actif
   - Exclusion : cyclisme sportif compétition (pas la cible)

5. **20 ANGLES PUBLICITAIRES**

   A. ÉMOTION LOCAL (5 angles)
   - "Fabriqué/testé sous la pluie orléanaise"
   - "Conçu par des cyclistes de Tours pour des cyclistes de Tours"
   - "Soutenez l'économie locale Centre-Val de Loire"
   - "Votre voisin cycliste l'a déjà"
   - "La sacoche des vrais Orléanais"

   B. LOGIQUE PRIX (5 angles)
   - "89€ vs 180€ Ortlieb - Même qualité waterproof"
   - "1 sacoche = 3 mois d'abonnement bus Orléans"
   - "Garantie 2 ans = 3.7€/mois"
   - "-25% si vous habitez 37/41/45"
   - "Livraison 48h gratuite Centre-Val de Loire"

   C. FOMO / SAISONNALITÉ (4 angles)
   - "Stock limité été 2026 - 200 unités"
   - "Derniers jours - Code ORLEANS10"
   - "La pluie arrive, soyez prêt"
   - "Rentrez à vélo cette année"

   D. SOCIAL PROOF (3 angles)
   - "127 cyclistes orléanais l'ont adopté"
   - "4.8/5 étoiles - 'Enfin une sacoche qui tient !'"
   - "Vu sur le vélo de [influenceur local]"

   E. ÉDUCATION / TEST (3 angles)
   - "IPX6 expliqué en 15 secondes"
   - "Test extrême : 30min sous pluie, résultat ?"
   - "3 erreurs quand on choisit une sacoche vélo"

6. **CALENDRIER 30 JOURS DÉTAILLÉ**
   - J1-3 : Lancement 3 créatives × 3 audiences (9 combinaisons)
   - J4-5 : Kill CPA > 20€, scale CPA < 12€
   - J6-7 : Introduction retargeting visiteurs
   - J8-10 : Scale winners + test nouveaux hooks
   - J11-15 : Optimisation lookalike + micro-influenceurs
   - J16-20 : Scale national si ROAS > 4.5
   - J21-25 : Maximisation conversion + préparation mois 2
   - J26-30 : Analyse + planification cycle suivant

7. **CHECKLIST OPTIMISATION**
   - Kill : CPA > 20€ ou ROAS < 2.5 pendant 2j consécutifs
   - Scale : CPA < 12€ et ROAS > 4.0 pendant 3j consécutifs
   - A/B test : 2 nouvelles créatives par semaine minimum
   - Budget : Augmenter de 25% max par jour
   - Dupliquer : Les gagnants avec 10-20% variation

RESSOURCES LOCALES À EXPLOITER :
- Clubs vélo : Orléans Vélo Campus, Tours Vélo Ville, Blois Vélo
- Événements : Fête du Vélo (juin), Loire à Vélo (avril-octobre)
- Partenariats : Loueurs vélos, réparateurs, coffee shops cyclistes
- Micro-influenceurs : Cyclistes locaux 5K-50K abonnés
- Livreurs : Communautés Uber Eats/Deliveroo (offre spéciale)

FORMAT : Tableaux markdown, budgets chiffrés, calendrier jour par jour actionnable.
TON : Précis, orienté résultats, "CPA < 12€ ou on coupe"."""
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
# CLIENT API MISTRAL - ROBUSTE AVEC RETRY
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
                timeout=(10, cfg.TIMEOUT)
            )

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
            wait = cfg.RETRY_DELAY * (cfg.RETRY_BACKOFF ** attempt)
            logger.warning(f"Tentative {attempt+1} échouée (timeout), retry dans {wait}s")
            if attempt < cfg.MAX_RETRIES - 1:
                time.sleep(wait)

        except requests.exceptions.ConnectionError:
            last_error = "Erreur connexion"
            wait = cfg.RETRY_DELAY * (cfg.RETRY_BACKOFF ** attempt)
            logger.warning(f"Tentative {attempt+1} échouée (connexion), retry dans {wait}s")
            if attempt < cfg.MAX_RETRIES - 1:
                time.sleep(wait)

        except APIError:
            raise

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

    cached = get_cached_result(system_prompt, user_input)
    if cached:
        st.success("📦 Résultat chargé depuis le cache")
        return cached

    try:
        with st.spinner("🤖 Génération en cours... (~10-30s)"):
            result = call_mistral_api(system_prompt, user_input)
        set_cached_result(system_prompt, user_input, result)
        return result
    except APIError as e:
        st.error(str(e))
        return f"❌ {e}"
    except Exception as e:
        logger.error(f"Erreur: {e}")
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

    prix = st.number_input(
        "Prix de vente URBÆ™ (€)", 
        value=89.0, 
        step=5.0,
        min_value=0.01,
        help="Prix TTC de la sacoche ou du pack"
    )
    cout = st.number_input(
        "Coût produit (€)", 
        value=28.0, 
        step=1.0,
        min_value=0.0,
        help="Coût d'achat ou production unitaire"
    )
    ads_pct = st.slider(
        "Budget Ads TikTok (% du CA)", 
        10, 50, 25
    ) / 100

    metrics = calculer_metrics(prix, cout)

    if not metrics.is_valid:
        st.error(f"⚠️ {metrics.error}")
        st.info("💡 Ajustez prix ou coût pour continuer")
    else:
        st.metric("Marge Brute URBÆ™", f"{metrics.marge_pct}%")

        if math.isinf(metrics.ca_necessaire):
            st.metric("CA nécessaire", "∞ €")
        else:
            st.metric(
                "CA/mois pour 10K€", 
                f"{metrics.ca_necessaire:,.0f} €"
            )

        st.metric("Commandes/jour", f"{metrics.commandes_jour:.1f}")

        st.divider()
        ca_test = st.number_input(
            "CA mensuel estimé (€)", 
            value=15930, 
            step=500, 
            min_value=0
        )

        try:
            proj = calculer_projection(
                ca_test, 
                metrics.marge_pct/100, 
                ca_test * ads_pct
            )

            col1, col2 = st.columns(2)
            delta = "✅ Rentable" if proj.is_profitable else "❌ Déficit"
            delta_color = "normal" if proj.is_profitable else "inverse"

            col1.metric(
                "Résultat Net", 
                f"{proj.resultat_net:,.0f} €",
                delta=delta,
                delta_color=delta_color
            )
            col2.metric("Progression 10K", f"{proj.progression_10k}%")
            st.progress(min(proj.progression_10k / 100, 1.0))

            if proj.progression_10k >= 100:
                st.success("🎉 Objectif 10K€ atteint !")
            elif proj.progression_10k >= 75:
                st.info("📈 Proche de l'objectif !")

        except Exception as e:
            st.error(f"Erreur calcul: {e}")

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
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 Stratégie", 
    "🎁 Offre", 
    "🎬 Créatives", 
    "📢 Acquisition"
])

with tab1:
    st.subheader("🎯 Plan Stratégique Hebdomadaire URBÆ™")
    st.markdown("**Angles marketing dominants · Opportunités météo · Tendances TikTok locales**")

    zone = st.selectbox(
        "Zone prioritaire",
        ["Orléans (280K hab, tech hub)", "Tours (137K hab, ville cyclable)", 
         "Blois (46K hab, tourisme Loire)", "National (scaling)"],
        key="zone_strat"
    )

    saison = st.selectbox(
        "Saisonnalité",
        ["Printemps (mars-mai)", "Été (juin-août)", 
         "Automne (sept-nov)", "Hiver (déc-fév)"],
        key="saison_strat"
    )

    if st.button("🎯 Générer le plan stratégique", type="primary", key="btn_strat"):
        prompt = f"Zone: {zone}. Saison: {saison}. Génère le plan stratégique hebdomadaire URBÆ™ avec 3 angles marketing dominants."
        result = generate_with_cache("strategie", prompt)
        if not result.startswith("❌"):
            st.session_state.results['strategie'] = result
        st.markdown(result)

    elif 'strategie' in st.session_state.results:
        st.markdown(st.session_state.results['strategie'])

with tab2:
    st.subheader("🎁 Optimisation Urban Rider Pack")
    st.markdown("**Packs · Pricing · Bonus · Offres locales**")

    pack_type = st.selectbox(
        "Type de pack à optimiser",
        ["Pack Solo (sacoche seule)", "Pack Duo (2 sacoches)",
         "Urban Rider Pack (bundle premium)", "Pack Pro (complet)"],
        key="pack_type"
    )

    prix_test = st.selectbox(
        "Prix à tester",
        ["139.90€", "149.90€", "159.90€", "169.90€"],
        key="prix_test"
    )

    if st.button("🎁 Générer l'offre optimisée", type="primary", key="btn_offre"):
        prompt = f"Pack: {pack_type}. Prix test: {prix_test}. Génère l'offre URBÆ™ optimisée avec bonus perçus et pricing psychologique."
        result = generate_with_cache("offre", prompt)
        if not result.startswith("❌"):
            st.session_state.results['offre'] = result
        st.markdown(result)

    elif 'offre' in st.session_state.results:
        st.markdown(st.session_state.results['offre'])

with tab3:
    st.subheader("🎬 Scripts UGC - 10 vidéos/semaine")
    st.markdown("**Hooks · Démonstrations · Témoignages · Tests extrêmes**")

    type_script = st.selectbox(
        "Type de scripts",
        ["Fierté locale (Orléans/Tours/Blois)", "Comparaison prix (vs Decathlon/Ortlieb)",
         "Météo/Pluie (argument waterproof)", "FOMO/Saisonnalité", "Test extrême"],
        key="type_script"
    )

    lieu_tournage = st.text_input(
        "Lieu de tournage suggéré",
        placeholder="Ex: Pont George V Orléans, Bords de Loire Blois",
        key="lieu_tournage"
    )

    if st.button("🎬 Générer les 10 scripts", type="primary", key="btn_creatives"):
        prompt = f"Type: {type_script}. Lieu: {lieu_tournage}. Génère 10 scripts vidéo URBÆ™ 15-30s avec hooks localisés."
        result = generate_with_cache("creatives", prompt)
        if not result.startswith("❌"):
            st.session_state.results['creatives'] = result
        st.markdown(result)

    elif 'creatives' in st.session_state.results:
        st.markdown(st.session_state.results['creatives'])

with tab4:
    st.subheader("📢 Plan Acquisition TikTok Ads")
    st.markdown("**CPA cible < 12€ · Ciblage hyper-local · Scale 30 jours**")

    budget_jour = st.selectbox(
        "Budget quotidien",
        ["20-30€ (Phase Test)", "50€ (Phase Optimisation)", 
         "100€ (Phase Scale)", "200€+ (Scaling national)"],
        key="budget_jour"
    )

    audience_cible = st.selectbox(
        "Audience prioritaire",
        ["Vélotafeurs (25-45 ans, cadres)", "Livreurs à vélo (Uber/Deliveroo)",
         "Étudiants cyclistes", "Cyclistes loisirs (Loire à Vélo)",
         "Digital nomades"],
        key="audience_cible"
    )

    if st.button("📢 Générer le plan média", type="primary", key="btn_acquisition"):
        prompt = f"Budget: {budget_jour}. Audience: {audience_cible}. Génère le plan acquisition TikTok Ads 30 jours URBÆ™ avec CPA < 12€."
        result = generate_with_cache("acquisition", prompt)
        if not result.startswith("❌"):
            st.session_state.results['acquisition'] = result
        st.markdown(result)

    elif 'acquisition' in st.session_state.results:
        st.markdown(st.session_state.results['acquisition'])

st.divider()
st.caption("URBÆ™ Brandshipping AI - Mobilité Urbaine Premium © 2026 | Orléans · Blois · Tours | Propulsé par Mistral AI")
