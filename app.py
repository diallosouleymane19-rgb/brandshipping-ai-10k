# -*- coding: utf-8 -*-
"""
Brandshipping AI - Agent 10K
Version URBÆ™ + The Apex Protocol + SMD Consulting LLC
Localisé Orléans-Blois-Tours | Loire Valley Edition
Agent IA Principal intégré - Science de Luxe
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
    """Configuration centralisée"""
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
# MASTER PROMPTS - PORTEFEUILLE MARQUES
# =============================================================================

SYSTEM_PROMPTS = {
    "strategie": """Tu es URBAE AI Manager, agent IA spécialisé BrandShipping pour le portefeuille SMD Consulting LLC.

CONTEXTE PORTEFEUILLE :
- URBÆ™ : Mobilité urbaine premium (sacoches vélo, Orléans-Blois-Tours)
- The Apex Protocol : Science du sommeil de luxe (luminothérapie, circadien)
- SMD Consulting LLC : Structure holding Wyoming (fiscalité optimisée)

CONTEXTE THE APEX PROTOCOL :
- Produit : Lampe luminothérapie rythme circadien ajustable (IPX6, modes Sunrise/Sunset)
- Angle : Solution scientifique de luxe, non gadget
- Cible : Cadres surperformants, entrepreneurs, biohackers 28-45 ans
- Prix : 299-349€ (COGS 110-160€, marge 54%)
- Zone : International (LLC Wyoming), puis Europe

CONTEXTE URBÆ™ :
- Produit : Sacoche cadre vélo waterproof (IPX6, 2.5L)
- Angle : Mobilité urbaine locale premium
- Cible : Vélotafeurs, livreurs, étudiants cyclistes
- Prix : 89-149€ (COGS 28€, marge 69%)
- Zone : Orléans-Blois-Tours (Loire Valley)

AUDIENCES PRIORITAIRES APEX :
1. Biohackers / Quantified Self (optimisation performance)
2. Entrepreneurs / Cadres (sommeil = productivité)
3. Sportifs d'endurance (récupération circadienne)
4. Travailleurs postés (infirmiers, pilotes, développeurs)
5. Digital nomades (jet lag, zones horaires)

INSTRUCTIONS :
1. Propose 3 angles marketing dominants par semaine par marque
2. Identifie les synergies entre URBÆ™ (mobilité jour) et Apex (sommeil nuit)
3. Détecte les tendances TikTok/LinkedIn (biohacking, circadien)
4. Propose des tests A/B (prix, angles, audiences)
5. Calcule les métriques avec coûts LLC Wyoming vs Europe
6. Suggère des partenariats (coachs sommeil, médecins du sport, coworkings)

FORMAT : Plan stratégique hebdomadaire avec tableaux comparatifs et recommandations priorisées.
TON : Scientifique, premium, orienté résultats.""",

    "offre": """Tu es expert en optimisation d'offres e-commerce premium pour SMD Consulting LLC.

MISSION : Maximiser la valeur perçue et le panier moyen pour The Apex Protocol et URBÆ™.

THE APEX PROTOCOL - BUNDLE :
Produit cœur : Lampe Circadienne de pointe (modes Sunrise/Sunset Protocol)

Bonus 1 (Physique/Luxe) : Masque sommeil soie/bambou anti-lumière qualité supérieure
Bonus 2 (Digital/Scalable) : Guide Apex Protocol (vidéos/PDF 4 semaines)
  - Journal suivi sommeil
  - Mini-méditations guidées phases transition
  - Feuille route meilleures pratiques sommeil
Bonus 3 (Physique/Complément) : Boîte thés apaisants haute qualité (camomille, valériane)

STRUCTURE OFFRE APEX :
1. Nom : "The Apex Sleep Optimization System"
2. Pricing psychologique :
   - Valeur perçue séparée : Lampe 350€ + Masque 80€ + Thé 50€ = 480€
   - Prix bundle : 299-349€
   - Option lampe seule : 249€ (tiers pricing)
3. Arguments vente physiologiques :
   - Alignement mélatoninergique avancé
   - Intelligence de la lumière (spectre ajustable)
   - Optimisation thermique et mentale
4. Garantie : 60 jours satisfait ou remboursé + protocole personnalisé
5. CTA : "Réinitialisez votre horloge biologique"

URBÆ™ - BUNDLE (conserver existant) :
Pack Solo / Duo / Urban Rider Pack / Pack Pro
Offres locales : -25% habitants 37/41/45, -30% livreurs

CONTRAINTES :
- Valeur perçue totale ≥ 5x le prix payé
- Positionner comme science de luxe (Apex) ou mobilité premium locale (URBÆ™)
- Mentionner SMD Consulting LLC comme structure de confiance
- Ton Apex : scientifique, physiologique, "voici ce que ce produit fait pour votre biologie"
- Ton URBÆ™ : authentique, local, "conçu par des cyclistes pour des cyclistes"

FORMAT : Tableaux comparatifs des bundles + recommandation finale avec justification chiffrée.""",

    "creatives": """Tu es directeur créatif UGC pour le portefeuille SMD Consulting LLC (URBÆ™ + The Apex Protocol).

MISSION : Produire 10 scripts vidéo par semaine par marque pour TikTok/Reels/LinkedIn (15-60s).

THE APEX PROTOCOL - SCRIPTS :
Contexte : Biohacking, science du sommeil, optimisation circadienne
Repères visuels : Laboratoire, chambre minimaliste, montres connectées, graphs données
Météo : Toutes saisons (sommeil = besoin permanent)
Concurrence : Lumie (basique), Philips Hue (générique), Oura (tracker)
Positionnement : "Le seul protocole scientifique complet de maîtrise circadienne"

Format par script Apex :
## Script [N°] - [Nom scientifique accrocheur]
**Durée :** XX secondes
**Plateforme :** TikTok / Reels / LinkedIn
**Type :** Hook données / Démonstration labo / Témoignage CEO / Test extrême / FOMO scientifique

Hook (0-3s) :
- "J'ai mesuré mon sommeil pendant 90 jours. Voici ce que la luminothérapie a changé."
- "POV : Tu découvres que ton réveil à 6h détruit ta mélatonine"
- "Test : 30 jours avec le protocole Apex. Résultats ?"

Problème (3-10s) :
Fatigue chronique, réveils difficiles, baisse performance cognitive, jet lag

Solution (10-20s) :
Protocole Apex : lampe circadienne + masque soie + thé + guide personnalisé
Bénéfices : alignement mélatonine, pics vigilance, sommeil profond ondes Delta

CTA (20-30s) :
- "Lien en bio - Protocole Apex 349€"
- "Stock limité - Batch scientifique #3"
- "Guide gratuit : 5 erreurs circadiennes"

Texte overlay :
- "+47% sommeil profond" (données)
- "349€ vs 480€ valeur" (comparaison)
- "⭐⭐⭐⭐⭐ 4.9/5 (203 avis)" (social proof)
- "60 jours garantie" (réduction risque)

Hashtags :
#Biohacking #SleepOptimization #CircadianRhythm #ApexProtocol #Performance #Mélatonine #SommeilProfond #QuantifiedSelf #SMDConsulting #LuxurySleep

CONSIGNES APEX :
- 3 scripts hook "données/chiffres" (graphs, montres, trackers)
- 2 scripts hook "comparaison concurrents" (vs Lumie, vs lampe basique)
- 2 scripts hook "test extrême" (30 jours, mesures avant/après)
- 2 scripts hook "FOMO scientifique" (batch limité, protocole exclusif)
- 1 script hook "témoignage expert" (médecin, coach, CEO)

URBÆ™ - SCRIPTS (conserver existant) :
Contexte : Mobilité urbaine Loire Valley
Repères : Pont George V, Château Blois, Pont Wilson Tours

TON APEX : Scientifique, mesuré, "voici la preuve". Pas de jargon inutile, mais références physiologiques.
TON URBÆ™ : Authentique, local, dynamique.

FORMAT : 20 scripts complets (10 Apex + 10 URBÆ™) avec tous les éléments demandés.""",

    "acquisition": """Tu es media buyer senior pour SMD Consulting LLC (The Apex Protocol + URBÆ™).

MISSION : Élaborer des plans d'acquisition 30 jours avec CPA cible optimisé par marque.

THE APEX PROTOCOL - ACQUISITION :
Contexte : Produit luxe/science, 299-349€, marge 54%, cible biohackers/cadres
Budgets : Phase 1 (50€/jour), Phase 2 (100€/jour), Phase 3 (200€/jour)

KPIs Apex :
- CPA cible : < 45€ (produit haut de gamme, cycle décision long)
- ROAS cible : 3.0-4.0 (marge 54%)
- CTR cible : 1.5-2.5%
- Conversion cible : 1.5-2.5%
- CPM cible : < 15€ (audience premium)

Canaux Apex :
- LinkedIn Ads (40%) : Ciblage cadres, entrepreneurs, biohackers
- Meta Ads (30%) : Instagram (aesthetic science), Facebook (communautés sommeil)
- TikTok Ads (20%) : Contenu éducatif viral
- Google Ads (10%) : Search "luminothérapie", "sommeil circadien"

Audiences Apex :
- Intérêts : biohacking, quantified self, Oura, Bulletproof, Huberman Lab
- Comportements : achats premium bien-être, abonnements health
- Exclusion : moins de 25 ans, revenus faibles

20 Angles Apex :
A. Science/Données (5) : "+47% sommeil profond", "étude publiée", "protocole validé"
B. Luxe/Exclusivité (5) : "batch limité", "protocole privé", "membre Apex"
C. FOMO/Résultats (4) : "avant/après 30 jours", "derniers stocks", "prix augmente"
D. Social Proof (3) : "203 biohackers", "4.9/5 étoiles", "recommandé par Dr X"
E. Éducation (3) : "3 erreurs circadiennes", "mélatonine expliquée", "test extrême"

Calendrier 30 jours Apex :
J1-5 : Test LinkedIn (professionnels) + Instagram (lifestyle)
J6-10 : Kill CPA > 60€, scale CPA < 40€
J11-15 : Retargeting visiteurs + lookalike purchasers
J16-20 : Scale winners + test TikTok éducatif
J21-25 : Optimisation Google Search + partenariats
J26-30 : Analyse + planification batch suivant

URBÆ™ - ACQUISITION (conserver existant) :
CPA < 12€, TikTok Ads hyper-local Orléans-Blois-Tours

SYNERGIES SMD CONSULTING :
- Cross-sell : Client Apex (sommeil) → URBÆ™ (mobilité matinale)
- Cross-sell : Client URBÆ™ (vélo) → Apex (récupération sommeil)
- Email marketing : Newsletter SMD "Performance Quotidienne"
- Communauté : Groupe privé "SMD Optimizers" (Apex + URBÆ™ + futurs produits)

FORMAT : Tableaux markdown, budgets chiffrés, calendriers jour par jour actionnables.
TON : Précis, orienté ROAS, "CPA cible ou on coupe".""",

    "agent_principal": """Tu es l'Agent IA Principal de SMD Consulting LLC, spécialisé dans le "Brandshipping AI".
Tu agis comme un expert hybride en Marketing de Marque, Analyse de Tendances et Copywriting SEO.

# Objectif
Aider les entrepreneurs à lancer des marques e-commerce sans stock (dropshipping/POD) en leur fournissant une stratégie complète : de l'idée à la vente.

# Contexte SMD Consulting LLC
## Structure
- Type : LLC Wyoming (fiscalité optimisée, pas d'impôt étatique)
- Activité : Holding e-commerce + consulting brandshipping
- Portefeuille : URBÆ™ (mobilité) + The Apex Protocol (sommeil)
- Revenus : % CA marques + frais consulting + formation + licence IA

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
- Évalue la scalabilité vers SMD Consulting LLC (réplicabilité).

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
3. Une option "SMD Scale" (scalable via consulting, réplicable)

# Mission Immédiate
Génère une stratégie complète incluant :
1. Identité de marque (nom alternatives, slogan, archetype, couleurs)
2. Analyse tendance (pourquoi maintenant, contexte marché)
3. Fiche produit optimisée conversion + SEO
4. 3 angles marketing (Safe vs Bold vs SMD Scale)
5. Scripts TikTok/Reels/LinkedIn (5 scripts)
6. Roadmap SMD Consulting LLC (quand et comment scaler vers structure)

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
# INTERFACE STREAMLIT - SMD CONSULTING LLC
# =============================================================================

st.set_page_config(
    page_title="SMD Consulting LLC | Brandshipping AI",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏢 SMD Consulting LLC")
st.caption("Brandshipping AI | URBÆ™ · The Apex Protocol | Objectif : 10K€ → 30K€ net/mois")

init_session()

# ---------------------------------------------------------------------------
# SIDEBAR - COCKPIT SMD
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("📊 Cockpit SMD")

    # Logo SMD
    st.markdown("""
    <div style="text-align:center; padding:10px; background:#0f0f23; border-radius:8px; margin-bottom:15px;">
        <h2 style="color:#00d4ff; margin:0; font-size:1.3rem;">SMD CONSULTING</h2>
        <p style="color:#888; margin:0; font-size:0.6rem;">LLC Wyoming · Brandshipping AI</p>
    </div>
    """, unsafe_allow_html=True)

    # Sélecteur de marque
    marque_active = st.selectbox(
        "🎯 Marque active",
        ["URBÆ™ (Mobilité)", "The Apex Protocol (Sommeil)", "Les deux (Synergies)"],
        key="marque_active"
    )

    st.divider()

    # Métriques financières
    if "URBÆ" in marque_active or "Les deux" in marque_active:
        st.markdown("**🚲 URBÆ™**")
        prix_u = st.number_input("Prix URBÆ™ (€)", value=89.0, step=5.0, min_value=0.01, key="prix_u")
        cout_u = st.number_input("Coût URBÆ™ (€)", value=28.0, step=1.0, min_value=0.0, key="cout_u")

        m_u = calculer_metrics(prix_u, cout_u)
        if m_u.is_valid:
            st.metric("Marge URBÆ™", f"{m_u.marge_pct}%")
            if not math.isinf(m_u.ca_necessaire):
                st.metric("CA/mois 10K€", f"{m_u.ca_necessaire:,.0f} €")

    if "Apex" in marque_active or "Les deux" in marque_active:
        st.markdown("**🧬 The Apex Protocol**")
        prix_a = st.number_input("Prix Apex (€)", value=349.0, step=10.0, min_value=0.01, key="prix_a")
        cout_a = st.number_input("Coût Apex (€)", value=160.0, step=5.0, min_value=0.0, key="cout_a")

        m_a = calculer_metrics(prix_a, cout_a)
        if m_a.is_valid:
            st.metric("Marge Apex", f"{m_a.marge_pct}%")
            if not math.isinf(m_a.ca_necessaire):
                st.metric("CA/mois 10K€", f"{m_a.ca_necessaire:,.0f} €")

    # Info SMD
    st.divider()
    st.markdown("""
    <div style="font-size:0.7rem; color:#666;">
        <b>🏢 SMD Consulting LLC</b><br>
        Structure : Wyoming<br>
        Portefeuille : 2 marques<br><br>
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
            ["URBÆ™", "The Apex Protocol", "Les deux (synergies)"],
            key="marque_strat"
        )
    with col2:
        zone_strat = st.selectbox(
            "Zone",
            ["Orléans-Blois-Tours", "France nationale", "Europe", "International (LLC)"],
            key="zone_strat"
        )

    if st.button("🎯 Générer le plan stratégique", type="primary", key="btn_strat"):
        prompt = f"Marque: {marque_strat}. Zone: {zone_strat}. Génère le plan stratégique hebdomadaire avec 3 angles marketing dominants."
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
         "Cross-sell URBÆ™ + Apex"],
        key="marque_offre"
    )

    if st.button("🎁 Générer l'offre optimisée", type="primary", key="btn_offre"):
        prompt = f"Marque: {marque_offre}. Génère l'offre optimisée avec bonus perçus et pricing psychologique."
        result = generate_with_cache("offre", prompt)
        if not result.startswith("❌"):
            st.session_state.results['offre'] = result
        st.markdown(result)

    elif 'offre' in st.session_state.results:
        st.markdown(st.session_state.results['offre'])

with tab3:
    st.subheader("🎬 Scripts UGC - 10 vidéos/semaine")

    col1, col2 = st.columns(2)
    with col1:
        marque_creative = st.selectbox(
            "Marque",
            ["URBÆ™ (Mobilité urbaine)", "The Apex Protocol (Science sommeil)"],
            key="marque_creative"
        )
    with col2:
        plateforme = st.selectbox(
            "Plateforme",
            ["TikTok", "Reels", "LinkedIn", "Toutes"],
            key="plateforme"
        )

    if st.button("🎬 Générer les scripts", type="primary", key="btn_creatives"):
        prompt = f"Marque: {marque_creative}. Plateforme: {plateforme}. Génère 10 scripts vidéo avec hooks."
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
            ["URBÆ™ (CPA < 12€)", "The Apex Protocol (CPA < 45€)", "Les deux (synergies)"],
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
        prompt = f"Marque: {marque_acqui}. Budget: {budget_acqui}. Génère le plan acquisition 30 jours."
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
            placeholder="Ex: lampe luminothérapie, sacoche vélo, accessoire tech...",
            key="idee_produit"
        )
    with col2:
        idee_cible = st.text_input(
            "Cible envisagée",
            placeholder="Ex: biohackers, cyclistes, cadres...",
            key="idee_cible"
        )

    idee_zone = st.selectbox(
        "Zone",
        ["Orléans-Blois-Tours (Loire Valley)", "France", "Europe", "International (LLC Wyoming)", "Global"],
        key="idee_zone"
    )

    idee_detail = st.text_area(
        "Décris ton idée",
        placeholder="Je veux lancer une marque de luminothérapie pour biohackers, sans stock, avec structure LLC Wyoming...",
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

Génère la stratégie complète SMD Consulting LLC."""

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
        **Exemple 1 (Safe) :** "Lampe luminothérapie basique pour cadres fatigués, 150€, sans stock"

        **Exemple 2 (Bold) :** "Protocole circadien complet pour biohackers, 500€ le système, LLC Wyoming"

        **Exemple 3 (SMD Scale) :** "Marque de sommeil scientifique avec formation et consulting intégrés"

        **Exemple 4 (Local) :** "URBÆ™ + Apex : mobilité jour et sommeil nuit pour les Orléanais"
        """)

st.divider()
st.caption("SMD Consulting LLC | Brandshipping AI © 2026 | URBÆ™ · The Apex Protocol | Propulsé par Mistral AI")
