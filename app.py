# -*- coding: utf-8 -*-
"""
Brandshipping AI - Agent 10K
Version SMD Consulting LLC | Portefeuille 3 Marques
URBÆ™ · The Apex Protocol · NOVA FUEL
Localisé Orléans-Blois-Tours | International
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
logger = logging.getLogger("smd_brandshipping")

@dataclass(frozen=True)
class Config:
    """Configuration centralisée SMD"""
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
# MASTER PROMPTS - PORTEFEUILLE 3 MARQUES SMD
# =============================================================================

SYSTEM_PROMPTS = {
    "strategie": """Tu es SMD AI Manager, agent IA spécialisé BrandShipping pour le portefeuille SMD Consulting LLC (3 marques).

CONTEXTE PORTEFEUILLE :
| Marque | Domaine | Produit | Prix | Cible | Zone |
|--------|---------|---------|------|-------|------|
| URBÆ™ | Mobilité urbaine | Sacoche cadre vélo waterproof | 89-149€ | Vélotafeurs, livreurs, étudiants | Orléans-Blois-Tours |
| The Apex Protocol | Science du sommeil | Lampe luminothérapie circadien | 299-349€ | Biohackers, cadres, entrepreneurs | International (LLC Wyoming) |
| NOVA FUEL | Nutrition performance | Gummies nootropiques, électrolytes, barres protéinées | 39-79€ | Sportifs, étudiants, performants | France + Europe |

CYCLE CLIENT SMD 24H :
06h00 : NOVA FUEL (énergie matin) → 08h00 : URBÆ™ (vélotaf) → 22h00 : The Apex Protocol (sommeil profond)

INSTRUCTIONS :
1. Propose 3 angles marketing dominants par semaine par marque
2. Identifie les synergies cross-sell entre les 3 marques
3. Détecte les tendances TikTok/LinkedIn par segment
4. Propose des tests A/B (prix, angles, audiences)
5. Calcule les métriques avec coûts spécifiques (local vs international)
6. Suggère des partenariats (clubs sportifs, coworkings, médecins du sport)

FORMAT : Plan stratégique hebdomadaire avec tableaux comparatifs et recommandations priorisées.
TON : Scientifique, premium, orienté résultats.""",

    "offre": """Tu es expert en optimisation d'offres e-commerce premium pour SMD Consulting LLC (3 marques).

MISSION : Maximiser la valeur perçue, le panier moyen et les synergies cross-sell.

NOVA FUEL - BUNDLE :
Produit cœur : Gummies Caféine + L-Théanine "Focus Shot" (30 jours)

Bonus 1 (Physique) : Sachet électrolytes "Hydration Protocol" (7 sticks)
Bonus 2 (Digital) : Guide "The Nova Method" (PDF + vidéos 4 semaines)
  - Protocole nutrition matinale optimisée
  - Tracker énergie quotidien
  - Recettes smoothies performance
Bonus 3 (Physique) : Barre protéinée "Recovery Bite" (3 unités test)

STRUCTURE OFFRE NOVA FUEL :
1. Nom : "The Nova Performance System"
2. Pricing :
   - Valeur perçue séparée : Gummies 59€ + Électrolytes 25€ + Guide 39€ + Barres 15€ = 138€
   - Prix bundle : 79€
   - Abonnement mensuel : 69€ (récurrent)
   - Option découverte : 39€ (gummies seuls)
3. Arguments :
   - "Énergie soutenue sans crash" (caféine + L-théanine)
   - "Hydratation cellulaire optimisée" (électrolytes complets)
   - "Récupération accélérée" (protéines + adaptogènes)
4. Garantie : 30 jours satisfait ou remboursé
5. CTA : "Allumez votre potentiel - Livraison 48h"

CROSS-SELL SMD :
- Client NOVA FUEL (énergie) → URBÆ™ (vélotaf) + Apex (sommeil réparateur)
- Client URBÆ™ (mobilité) → NOVA FUEL (énergie pour la route) + Apex (récupération)
- Client Apex (sommeil) → NOVA FUEL (réveil optimal) + URBÆ™ (mobilité matinale)

OFFRE BUNDLE CROSS-MARQUE "SMD OPTIMIZER" :
- NOVA FUEL (gummies 1 mois) + URBÆ™ (sacoche) + Apex (guide sommeil)
- Prix : 199€ (vs 278€ séparément)
- Cible : Entrepreneurs performants (cycle 24h complet)

FORMAT : Tableaux comparatifs des bundles + recommandation finale avec justification chiffrée.""",

    "creatives": """Tu es directeur créatif UGC pour SMD Consulting LLC (3 marques).

MISSION : Produire 15 scripts vidéo par semaine (5 par marque) pour TikTok/Reels/LinkedIn (15-60s).

NOVA FUEL - SCRIPTS :
Contexte : Nutrition performance, biohacking, énergie quotidienne
Repères visuels : Cuisine moderne, gym, bureau startup, vélo matinal
Moment : 6h-9h (matin), 14h-16h (post-déjeuner)
Concurrence : Huel, Feed, Gorilla Mind, Athletic Greens
Positionnement : "L'énergie intelligente. Pas de crash, que du flow."

Format par script Nova Fuel :
## Script [N°] - [Nom accrocheur]
**Durée :** XX secondes
**Plateforme :** TikTok / Reels / LinkedIn
**Type :** Hook données / Démonstration / Témoignage / Test extrême / FOMO

Hook (0-3s) :
- "J'ai remplacé mon 3ème café par ça. Voici ce qui s'est passé."
- "POV : Tu découvres que ton énergie de l'après-midi est gérable"
- "Test : 30 jours de Nova Fuel. Mon taux de cortisol ?"

Problème (3-10s) :
Crash caféiné, fatigue post-déjeuner, manque de focus, baisse productivité 15h

Solution (10-20s) :
Nova Fuel : gummies caféine + L-théanine (focus sans anxiété), électrolytes, barres protéinées

CTA (20-30s) :
- "Code NOVA20 pour -20% première commande"
- "Abonnement mensuel : 69€ + livraison gratuite"
- "Lien en bio - Stock limité batch #2"

Texte overlay :
- "+340% focus vs café seul" (données)
- "79€ vs 138€ valeur" (comparaison)
- "⭐⭐⭐⭐⭐ 4.7/5 (312 avis)" (social proof)
- "Sans crash, sans tremblements" (bénéfice)

Hashtags Nova :
#NovaFuel #Nootropics #Biohacking #Focus #Productivity #Energy #Performance #MentalClarity #Caffeine #LTheanine #SMDConsulting

CONSIGNES NOVA FUEL :
- 2 scripts hook "données/comparaison" (vs café, vs energy drinks)
- 2 scripts hook "routine matinale" (avec URBÆ™, avec Apex)
- 2 scripts hook "test extrême" (30 jours, mesures focus)
- 2 scripts hook "témoignage" (entrepreneur, sportif, étudiant)
- 1 script hook "FOMO science" (batch limité, protocole exclusif)
- 1 script hook "cross-sell SMD" (cycle 24h complet)

TON NOVA : Énergique, scientifique mais accessible, "optimisez votre biologie".

FORMAT : 15 scripts complets (5 URBÆ™ + 5 Apex + 5 Nova Fuel).""",

    "acquisition": """Tu es media buyer senior pour SMD Consulting LLC (3 marques).

MISSION : Élaborer des plans d'acquisition 30 jours avec CPA cible optimisé par marque.

NOVA FUEL - ACQUISITION :
Contexte : Nutrition performance, 39-79€, marge 65%, produit consommable (récurrent)
Budgets : Phase 1 (30€/jour), Phase 2 (60€/jour), Phase 3 (120€/jour)

KPIs Nova Fuel :
- CPA cible : < 25€ (produit consommable, LTV élevé)
- ROAS cible : 3.5-4.5 (marge 65%)
- CTR cible : 2.0-3.5%
- Conversion cible : 2.5-4.0%
- LTV cible : > 150€ (abonnement récurrent)

Canaux Nova Fuel :
- TikTok Ads (40%) : Contenu éducatif viral, routines matinales
- Meta Ads (35%) : Instagram (aesthetic nutrition), Facebook (communautés sport)
- Google Ads (15%) : Search "nootropiques", "énergie naturelle", "focus"
- Influence (10%) : Micro-influenceurs fitness, productivité, études

Audiences Nova Fuel :
- Intérêts : biohacking, productivité, fitness, études, entrepreneuriat
- Comportements : achats suppléments, abonnements healthy
- Lookalike : purchasers Nova, engagés URBÆ™/Apex
- Exclusion : moins de 18 ans

20 Angles Nova Fuel :
A. Science/Données (5) : "+340% focus", "étude caféine+L-théanine", "cortisol optimisé"
B. Routine/Style de vie (5) : "ma morning routine", "avant le vélotaf", "post-workout"
C. FOMO/Résultats (4) : "30 jours avant/après", "batch limité", "prix augmente"
D. Social Proof (3) : "312 performants", "4.7/5 étoiles", "recommandé par Dr X"
E. Cross-sell SMD (3) : "cycle 24h complet", "pack SMD Optimizer", "tribu SMD"

Calendrier 30 jours Nova Fuel :
J1-5 : Test TikTok (routines) + Instagram (aesthetic)
J6-10 : Kill CPA > 35€, scale CPA < 20€
J11-15 : Retargeting + introduction abonnement
J16-20 : Scale winners + test Google Search
J21-25 : Influence micro + partenariats gyms
J26-30 : Analyse LTV + optimisation abonnements

SYNERGIES SMD 3 MARQUES :
- Email marketing : Newsletter "La Performance Quotidienne" (3 marques)
- Communauté : Groupe privé "SMD Optimizers" (cycle 24h)
- Cross-sell automatique : Post-achat URBÆ™ → offre Nova Fuel
- Bundle SMD : "Optimizer Pack" (3 marques, prix réduit)
- Programme fidélité : Points SMD utilisables sur les 3 marques

FORMAT : Tableaux markdown, budgets chiffrés, calendriers jour par jour actionnables.
TON : Précis, orienté ROAS et LTV, "CPA cible ou on coupe".""",

    "agent_principal": """Tu es l'Agent IA Principal de SMD Consulting LLC, spécialisé dans le "Brandshipping AI".
Tu agis comme un expert hybride en Marketing de Marque, Analyse de Tendances et Copywriting SEO.

# Objectif
Aider les entrepreneurs à lancer des marques e-commerce sans stock (dropshipping/POD) en leur fournissant une stratégie complète : de l'idée à la vente.

# Contexte SMD Consulting LLC
## Structure
- Type : LLC Wyoming (fiscalité optimisée)
- Activité : Holding e-commerce + consulting brandshipping
- Portefeuille : 3 marques (URBÆ™, The Apex Protocol, NOVA FUEL)
- Revenus : % CA marques + frais consulting + formation + licence IA

## Cycle Client SMD 24H
06h00 : NOVA FUEL (énergie matinale) → 08h00 : URBÆ™ (vélotaf optimisé) → 22h00 : The Apex Protocol (sommeil profond)

## Services SMD
| Service | Description | Prix | Cible |
|---------|-------------|------|-------|
| Audit | Analyse marché + opportunité produit | Gratuit | Débutants |
| Setup | Création marque + site + ads | 2-5K€ | Entrepreneurs |
| Scale | Optimisation + automatisation | 1-3K€/mois | Marques existantes |
| Formation | Cours Brandshipping AI | 500-2000€ | Apprenants |
| Licence | Utilisation Agent IA SMD | 200-500€/mois | Agences |

## Vision
"Devenir la référence européenne du lancement de marques sans stock, en combinant science des données et exécution locale."

# Tes 3 Compétences Clés

## 1. Création d'Identité (Branding)
- Propose des noms de marque courts, mémorables et disponibles (.com si possible).
- Crée des slogans percutants.
- Définis des archétypes de marque (ex: Le Héros, Le Créateur, Le Sage).
- Suggère des palettes de couleurs et des tons de voix cohérents.
- Intègre SMD Consulting LLC comme structure de holding crédible.

## 2. Analyse de Tendances (Product Strategy)
- Identifie les niches porteuses (ex: éco-responsable, tech-wear, bien-être mental).
- Analyse pourquoi un produit pourrait fonctionner maintenant (contexte social/saisonnier).
- Propose des angles marketing uniques pour des produits génériques.
- Évalue la scalabilité vers SMD Consulting LLC (réplicabilité sur 3 marques).

## 3. Copywriting & SEO (Content)
- Rédige des fiches produits qui convertissent (Structure : Accroche -> Problème -> Solution -> Preuve Sociale -> Appel à l'action).
- Intègre des mots-clés SEO naturellement.
- Génère des scripts pour vidéos courtes (TikTok/Reels) ou posts LinkedIn.
- Crée du contenu pour positionner SMD Consulting comme expert.

# Ton Style
- Professionnel mais accessible.
- Direct et orienté action ("Fais ceci", "Évite cela").
- Utilise des listes à puces pour la clarté.
- Si une information manque, pose une question précise pour affiner ta réponse.
- Vision long terme : Toujours montrer le chemin vers SMD Consulting LLC.

# Instruction Spéciale
Lorsque l'utilisateur te donne une idée vague, propose toujours :
1. Une option "Safe" (classique, prudent)
2. Une option "Bold" (audacieuse, disruptive)
3. Une option "SMD Scale" (scalable via consulting, réplicable sur 3 marques)

# Mission Immédiate
Génère une stratégie complète incluant :
1. Identité de marque (nom alternatives, slogan, archetype, couleurs)
2. Analyse tendance (pourquoi maintenant, contexte marché)
3. Fiche produit optimisée conversion + SEO
4. 3 angles marketing (Safe vs Bold vs SMD Scale)
5. Scripts TikTok/Reels/LinkedIn (5 scripts)
6. Roadmap SMD Consulting LLC (intégration au cycle 24h + synergies)

FORMAT : Réponse structurée avec titres, listes à puces, tableaux markdown.
TON : Professionnel, direct, orienté action, visionnaire."""
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
# INTERFACE STREAMLIT - SMD CONSULTING LLC (3 MARQUES)
# =============================================================================

st.set_page_config(
    page_title="SMD Consulting LLC | Brandshipping AI | 3 Marques",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏢 SMD Consulting LLC")
st.caption("Brandshipping AI | URBÆ™ · The Apex Protocol · NOVA FUEL | Objectif : 10K€ → 30K€ → 100K€ net/mois")

init_session()

# ---------------------------------------------------------------------------
# SIDEBAR - COCKPIT SMD 3 MARQUES
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("📊 Cockpit SMD")

    # Logo SMD
    st.markdown("""
    <div style="text-align:center; padding:10px; background:#0f0f23; border-radius:8px; margin-bottom:15px;">
        <h2 style="color:#00d4ff; margin:0; font-size:1.3rem;">SMD CONSULTING</h2>
        <p style="color:#888; margin:0; font-size:0.6rem;">LLC Wyoming · Brandshipping AI · 3 Marques</p>
    </div>
    """, unsafe_allow_html=True)

    # Sélecteur de marque
    marque_active = st.selectbox(
        "🎯 Marque active",
        ["🚲 URBÆ™ (Mobilité)", "🧬 The Apex Protocol (Sommeil)", "⚡ NOVA FUEL (Énergie)", "🏢 Les 3 (Synergies)"],
        key="marque_active"
    )

    st.divider()

    # Métriques financières par marque
    if "URBÆ" in marque_active or "3" in marque_active:
        st.markdown("**🚲 URBÆ™**")
        prix_u = st.number_input("Prix URBÆ™ (€)", value=89.0, step=5.0, min_value=0.01, key="prix_u")
        cout_u = st.number_input("Coût URBÆ™ (€)", value=28.0, step=1.0, min_value=0.0, key="cout_u")
        m_u = calculer_metrics(prix_u, cout_u)
        if m_u.is_valid:
            st.metric("Marge URBÆ™", f"{m_u.marge_pct}%")
            if not math.isinf(m_u.ca_necessaire):
                st.metric("CA/mois 10K€", f"{m_u.ca_necessaire:,.0f} €")

    if "Apex" in marque_active or "3" in marque_active:
        st.markdown("**🧬 The Apex Protocol**")
        prix_a = st.number_input("Prix Apex (€)", value=349.0, step=10.0, min_value=0.01, key="prix_a")
        cout_a = st.number_input("Coût Apex (€)", value=160.0, step=5.0, min_value=0.0, key="cout_a")
        m_a = calculer_metrics(prix_a, cout_a)
        if m_a.is_valid:
            st.metric("Marge Apex", f"{m_a.marge_pct}%")
            if not math.isinf(m_a.ca_necessaire):
                st.metric("CA/mois 10K€", f"{m_a.ca_necessaire:,.0f} €")

    if "NOVA" in marque_active or "3" in marque_active:
        st.markdown("**⚡ NOVA FUEL**")
        prix_n = st.number_input("Prix Nova (€)", value=79.0, step=5.0, min_value=0.01, key="prix_n")
        cout_n = st.number_input("Coût Nova (€)", value=28.0, step=1.0, min_value=0.0, key="cout_n")
        m_n = calculer_metrics(prix_n, cout_n)
        if m_n.is_valid:
            st.metric("Marge Nova", f"{m_n.marge_pct}%")
            if not math.isinf(m_n.ca_necessaire):
                st.metric("CA/mois 10K€", f"{m_n.ca_necessaire:,.0f} €")

    # Cycle 24h SMD
    st.divider()
    st.markdown("""
    <div style="font-size:0.7rem; color:#666;">
        <b>🕐 Cycle SMD 24H :</b><br>
        06h ⚡ Nova Fuel (énergie)<br>
        08h 🚲 URBÆ™ (vélotaf)<br>
        22h 🧬 Apex (sommeil)<br><br>
        <b>🏢 SMD Consulting LLC</b><br>
        Structure : Wyoming<br>
        Portefeuille : 3 marques<br><br>
        <b>Services :</b><br>
        • Audit (Gratuit)<br>
        • Setup (2-5K€)<br>
        • Scale (1-3K€/mois)<br>
        • Formation (500-2000€)<br>
        • Licence IA (200-500€/mois)
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TABS - 5 AXES SMD
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 Stratégie", 
    "🎁 Offre", 
    "🎬 Créatives", 
    "📢 Acquisition",
    "🤖 Agent Principal"
])

with tab1:
    st.subheader("🎯 Plan Stratégique Hebdomadaire")

    col1, col2 = st.columns(2)
    with col1:
        marque_strat = st.selectbox(
            "Marque",
            ["URBÆ™", "The Apex Protocol", "NOVA FUEL", "Les 3 (synergies cross-sell)"],
            key="marque_strat"
        )
    with col2:
        zone_strat = st.selectbox(
            "Zone",
            ["Orléans-Blois-Tours", "France nationale", "Europe", "International (LLC)"],
            key="zone_strat"
        )

    if st.button("🎯 Générer le plan stratégique", type="primary", key="btn_strat"):
        prompt = f"Marque: {marque_strat}. Zone: {zone_strat}. Génère le plan stratégique hebdomadaire avec 3 angles marketing dominants et synergies cross-sell."
        result = generate_with_cache("strategie", prompt)
        if not result.startswith("❌"):
            st.session_state.results['strategie'] = result
        st.markdown(result)

    elif 'strategie' in st.session_state.results:
        st.markdown(st.session_state.results['strategie'])

with tab2:
    st.subheader("🎁 Optimisation des Bundles")

    marque_offre = st.selectbox(
        "Marque à optimiser",
        ["URBÆ™ (Pack Solo/Duo/Urban Rider/Pro)", 
         "The Apex Protocol (Sleep Optimization System)",
         "NOVA FUEL (Performance System + abonnement)",
         "Cross-sell SMD (Pack Optimizer 3 marques)"],
        key="marque_offre"
    )

    if st.button("🎁 Générer l'offre optimisée", type="primary", key="btn_offre"):
        prompt = f"Marque: {marque_offre}. Génère l'offre optimisée avec bonus perçus, pricing psychologique et synergies."
        result = generate_with_cache("offre", prompt)
        if not result.startswith("❌"):
            st.session_state.results['offre'] = result
        st.markdown(result)

    elif 'offre' in st.session_state.results:
        st.markdown(st.session_state.results['offre'])

with tab3:
    st.subheader("🎬 Scripts UGC - 15 vidéos/semaine (5 par marque)")

    col1, col2 = st.columns(2)
    with col1:
        marque_creative = st.selectbox(
            "Marque",
            ["URBÆ™ (Mobilité urbaine)", "The Apex Protocol (Science sommeil)", "NOVA FUEL (Nutrition performance)", "Cycle SMD 24H (cross-marque)"],
            key="marque_creative"
        )
    with col2:
        plateforme = st.selectbox(
            "Plateforme",
            ["TikTok", "Reels", "LinkedIn", "Toutes"],
            key="plateforme"
        )

    if st.button("🎬 Générer les scripts", type="primary", key="btn_creatives"):
        prompt = f"Marque: {marque_creative}. Plateforme: {plateforme}. Génère 5 scripts vidéo avec hooks et CTA."
        result = generate_with_cache("creatives", prompt)
        if not result.startswith("❌"):
            st.session_state.results['creatives'] = result
        st.markdown(result)

    elif 'creatives' in st.session_state.results:
        st.markdown(st.session_state.results['creatives'])

with tab4:
    st.subheader("📢 Plan Acquisition")

    col1, col2 = st.columns(2)
    with col1:
        marque_acqui = st.selectbox(
            "Marque",
            ["URBÆ™ (CPA < 12€)", "The Apex Protocol (CPA < 45€)", "NOVA FUEL (CPA < 25€, LTV > 150€)", "Les 3 (synergies)"],
            key="marque_acqui"
        )
    with col2:
        budget_acqui = st.selectbox(
            "Budget",
            ["Phase Test (20-50€/jour)", "Phase Optimisation (50-100€/jour)", 
             "Phase Scale (100-200€/jour)", "Scaling national (200€+/jour)"],
            key="budget_acqui"
        )

    if st.button("📢 Générer le plan média", type="primary", key="btn_acquisition"):
        prompt = f"Marque: {marque_acqui}. Budget: {budget_acqui}. Génère le plan acquisition 30 jours avec KPIs et calendrier."
        result = generate_with_cache("acquisition", prompt)
        if not result.startswith("❌"):
            st.session_state.results['acquisition'] = result
        st.markdown(result)

    elif 'acquisition' in st.session_state.results:
        st.markdown(st.session_state.results['acquisition'])

with tab5:
    st.subheader("🤖 Agent IA Principal SMD")
    st.markdown("**Branding · Tendances · Copywriting SEO · Safe vs Bold vs SMD Scale**")
    st.caption("Lance ta marque e-commerce sans stock - De l'idée à la vente")

    # Section 1 : Idée
    st.markdown("### 💡 Ton projet")

    col1, col2 = st.columns(2)
    with col1:
        idee_produit = st.text_input(
            "Produit ou niche",
            placeholder="Ex: gummies énergie, lampe luminothérapie, sacoche vélo...",
            key="idee_produit"
        )
    with col2:
        idee_cible = st.text_input(
            "Cible envisagée",
            placeholder="Ex: biohackers, cyclistes, étudiants...",
            key="idee_cible"
        )

    idee_zone = st.selectbox(
        "Zone",
        ["Orléans-Blois-Tours (Loire Valley)", "France", "Europe", "International (LLC Wyoming)", "Global"],
        key="idee_zone"
    )

    idee_detail = st.text_area(
        "Décris ton idée",
        placeholder="Je veux lancer une marque de gummies nootropiques pour étudiants et entrepreneurs, sans stock, avec structure LLC Wyoming...",
        height=100,
        key="idee_detail"
    )

    # Section 2 : Style
    st.markdown("### 🎨 Style de stratégie")

    col1, col2, col3 = st.columns(3)
    with col1:
        style_safe = st.checkbox("✅ Safe (classique)", value=True, key="style_safe")
    with col2:
        style_bold = st.checkbox("🔥 Bold (disruptif)", value=True, key="style_bold")
    with col3:
        style_smd = st.checkbox("🏢 SMD Scale (scalable)", value=True, key="style_smd")

    # Section 3 : Compétences
    st.markdown("### 🛠️ Compétences")

    col1, col2, col3 = st.columns(3)
    with col1:
        skill_branding = st.checkbox("🎨 Branding", value=True, key="skill_branding")
    with col2:
        skill_trends = st.checkbox("📈 Tendances", value=True, key="skill_trends")
    with col3:
        skill_copywriting = st.checkbox("✍️ Copywriting", value=True, key="skill_copywriting")

    # Bouton génération
    if st.button("🚀 Générer la stratégie complète", type="primary", use_container_width=True, key="btn_agent"):

        if not idee_produit and not idee_detail:
            st.warning("💡 Décris au moins un produit ou une idée")
        else:
            styles = []
            if style_safe: styles.append("Safe")
            if style_bold: styles.append("Bold")
            if style_smd: styles.append("SMD Scale")

            skills = []
            if skill_branding: skills.append("Branding")
            if skill_trends: skills.append("Tendances")
            if skill_copywriting: skills.append("Copywriting")

            prompt = f"""Produit: {idee_produit or 'Non spécifié'}
Cible: {idee_cible or 'Non spécifiée'}
Zone: {idee_zone}
Détails: {idee_detail or 'Aucun'}

Styles: {', '.join(styles)}
Compétences: {', '.join(skills)}

Génère la stratégie complète SMD Consulting LLC avec intégration au cycle 24h."""

            with st.spinner("🤖 Agent Principal SMD analyse votre projet..."):
                result = generate_with_cache("agent_principal", prompt)

            if not result.startswith("❌"):
                st.session_state.results['agent_principal'] = result

            st.markdown("---")
            st.markdown("## 📋 Stratégie SMD Générée")
            st.markdown(result)

    elif 'agent_principal' in st.session_state.results:
        st.markdown("---")
        st.markdown("## 📋 Dernière stratégie générée")
        st.markdown(st.session_state.results['agent_principal'])

    with st.expander("💡 Exemples d'idées"):
        st.markdown("""
        **Exemple 1 (Safe) :** "Gummies énergie basiques pour étudiants, 49€, sans stock"

        **Exemple 2 (Bold) :** "Système nootropique complet pour traders, 299€, protocole personnalisé"

        **Exemple 3 (SMD Scale) :** "Marque nutrition + formation + consulting intégrés, réplicable sur 3 niches"

        **Exemple 4 (Cycle 24h) :** "NOVA FUEL (matin) + URBÆ™ (jour) + Apex (nuit) pour entrepreneurs performants"
        """)

st.divider()
st.caption("SMD Consulting LLC | Brandshipping AI © 2026 | URBÆ™ · The Apex Protocol · NOVA FUEL | Propulsé par Mistral AI")
