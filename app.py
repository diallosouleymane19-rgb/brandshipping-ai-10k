# -*- coding: utf-8 -*-
"""
Brandshipping AI - Agent 10K
Version SMD Global Consulting LLC | Portefeuille 3 Marques
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
import pandas as pd
import plotly.graph_objects as go
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
    "strategie": """Tu es SMD AI Manager, agent IA spécialisé BrandShipping pour le portefeuille SMD Global Consulting LLC (3 marques).

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

    "offre": """Tu es expert en optimisation d'offres e-commerce premium pour SMD Global Consulting LLC (3 marques).

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

    "creatives": """Tu es directeur créatif UGC pour SMD Global Consulting LLC (3 marques).

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
#NovaFuel #Nootropics #Biohacking #Focus #Productivity #Energy #Performance #MentalClarity #Caffeine #LTheanine #SMDGlobalConsulting

CONSIGNES NOVA FUEL :
- 2 scripts hook "données/comparaison" (vs café, vs energy drinks)
- 2 scripts hook "routine matinale" (avec URBÆ™, avec Apex)
- 2 scripts hook "test extrême" (30 jours, mesures focus)
- 2 scripts hook "témoignage" (entrepreneur, sportif, étudiant)
- 1 script hook "FOMO science" (batch limité, protocole exclusif)
- 1 script hook "cross-sell SMD" (cycle 24h complet)

TON NOVA : Énergique, scientifique mais accessible, "optimisez votre biologie".

FORMAT : 15 scripts complets (5 URBÆ™ + 5 Apex + 5 Nova Fuel).""",

    "acquisition": """Tu es media buyer senior pour SMD Global Consulting LLC (3 marques).

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

    "agent_principal": """Tu es l'Agent IA Principal de SMD Global Consulting LLC, spécialisé dans le "Brandshipping AI".
Tu agis comme un expert hybride en Marketing de Marque, Analyse de Tendances et Copywriting SEO.

# Objectif
Aider les entrepreneurs à lancer des marques e-commerce sans stock (dropshipping/POD) en leur fournissant une stratégie complète : de l'idée à la vente.

# Contexte SMD Global Consulting LLC
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
- Intègre SMD Global Consulting LLC comme structure de holding crédible.

## 2. Analyse de Tendances (Product Strategy)
- Identifie les niches porteuses (ex: éco-responsable, tech-wear, bien-être mental).
- Analyse pourquoi un produit pourrait fonctionner maintenant (contexte social/saisonnier).
- Propose des angles marketing uniques pour des produits génériques.
- Évalue la scalabilité vers SMD Global Consulting LLC (réplicabilité sur 3 marques).

## 3. Copywriting & SEO (Content)
- Rédige des fiches produits qui convertissent (Structure : Accroche -> Problème -> Solution -> Preuve Sociale -> Appel à l'action).
- Intègre des mots-clés SEO naturellement.
- Génère des scripts pour vidéos courtes (TikTok/Reels) ou posts LinkedIn.
- Crée du contenu pour positionner SMD Global Consulting comme expert.

# Ton Style
- Professionnel mais accessible.
- Direct et orienté action ("Fais ceci", "Évite cela").
- Utilise des listes à puces pour la clarté.
- Si une information manque, pose une question précise pour affiner ta réponse.
- Vision long terme : Toujours montrer le chemin vers SMD Global Consulting LLC.

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
6. Roadmap SMD Global Consulting LLC (intégration au cycle 24h + synergies)

FORMAT : Réponse structurée avec titres, listes à puces, tableaux markdown.
TON : Professionnel, direct, orienté action, visionnaire.""",

    "ugc_factory": """Tu es l'Agent Script UGC de SMD Global Consulting LLC, expert en création de scripts publicitaires vidéo ultra-convertissants.

MISSION : Produire des scripts UGC (User Generated Content) professionnels pour TikTok, Reels Instagram et YouTube Shorts.

PORTEFEUILLE SMD :
| Marque | Produit | Prix | Ton | Audience |
|--------|---------|------|-----|----------|
| URBÆ™ | Sacoche cadre vélo waterproof | 89-149€ | Lifestyle urbain, confiant | Vélotafeurs, livreurs, étudiants |
| The Apex Protocol | Lampe luminothérapie circadien | 299-349€ | Scientifique, premium | Biohackers, cadres, entrepreneurs |
| NOVA FUEL | Gummies nootropiques, électrolytes | 39-79€ | Énergique, accessible | Sportifs, étudiants, performants |

STRUCTURE OBLIGATOIRE DU SCRIPT :

## 🎬 [TITRE DU SCRIPT]
**Durée :** [X] secondes | **Plateforme :** [TikTok/Reels/Shorts] | **Type :** [Hook/Témoignage/Démonstration/FOMO]

### 🎯 HOOK (0-3s) — ACCROCHEZ EN UNE PHRASE
[Phrase d'accroche ultra-percutante. Exemples : "POV : Tu découvres que...", "J'ai testé X pendant 30 jours, voilà...", "Le truc que personne ne dit sur..."]

### ❗ PROBLÈME (3-8s) — DOULEUR DU CLIENT
[Douleur spécifique et relatable de l'audience cible]

### ✅ SOLUTION (8-20s) — LE PRODUIT EN ACTION
[Démonstration ou description du bénéfice concret. Chiffres, résultats, avant/après]

### 📢 CTA (20-30s) — APPEL À L'ACTION
[CTA clair + urgence + code promo si applicable]

### 🎨 TEXTE OVERLAY (incrustations à l'écran)
- [Stat ou bénéfice choc]
- [Preuve sociale]
- [Offre ou prix]

### 🎙️ VOIX OFF (texte exact pour ElevenLabs)
[Texte complet à lire en voix off — naturel, rythmé, sans ponctuation excessive]

### 🎵 RECOMMANDATION AUDIO
[Style musical : ex. "Beat lo-fi énergique", "Son viral TikTok ambiant"]

### #️⃣ HASHTAGS
[15-20 hashtags optimisés par plateforme]

RÈGLES DE PRODUCTION :
1. Hook en moins de 3 secondes — sinon l'audience zappe
2. Toujours 1 chiffre concret (ex : "+340% focus", "3.2 commandes/jour")
3. CTA avec friction minimale ("Lien en bio", "Code NOVA20")
4. Langage naturel, parlé, pas écrit — comme un vrai créateur UGC
5. Adapter le ton par marque (URBÆ = cool urbain / Apex = scientifique / Nova = punch énergie)

FORMAT : Produire le nombre exact de scripts demandé, chacun complet et prêt à tourner."""
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
        'initialized': True,
        'simulated_orders': [
            {"id": "SMD-2026-981", "client": "Lucas Martin", "ville": "Orléans", "marque": "🚲 URBÆ™", "produit": "Sacoche étanche cadre", "prix": 129.0, "status": "Impression Colis", "tracking": "DHL-MOCK-981"},
            {"id": "SMD-2026-982", "client": "Emma Bernard", "ville": "Tours", "marque": "⚡ NOVA FUEL", "produit": "Gummies Focus + Sticks", "prix": 79.0, "status": "En cours de préparation", "tracking": "DHL-MOCK-982"},
            {"id": "SMD-2026-983", "client": "Thomas Dubois", "ville": "Paris", "marque": "🧬 The Apex Protocol", "produit": "Lampe luminothérapie", "prix": 349.0, "status": "Expédié", "tracking": "DHL-987654321"}
        ]
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# =============================================================================
# INTERFACE STREAMLIT - SMD GLOBAL CONSULTING LLC (3 MARQUES)
# =============================================================================

st.set_page_config(
    page_title="SMD Global Consulting LLC | Brandshipping AI | 3 Marques",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injection de styles CSS personnalisés pour un look premium
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
    }
    
    [data-testid="stSidebar"] {
        background-color: #0c0e18 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    div.glass-card {
        background: rgba(255, 255, 255, 0.02) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    div.glass-card:hover {
        border-color: rgba(255, 255, 255, 0.12);
        transform: translateY(-2px);
    }
    
    div.generated-box {
        background: rgba(13, 15, 26, 0.5) !important;
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #0052D4, #4364F7, #6FB1FC) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 20px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(67, 100, 247, 0.3) !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(67, 100, 247, 0.5) !important;
    }
    
    .timeline {
        position: relative;
        padding-left: 20px;
        margin-top: 15px;
    }
    .timeline::before {
        content: '';
        position: absolute;
        left: 5px;
        top: 5px;
        bottom: 5px;
        width: 2px;
        background: rgba(255, 255, 255, 0.1);
    }
    .timeline-item {
        position: relative;
        margin-bottom: 20px;
    }
    .timeline-badge {
        position: absolute;
        left: -20px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #00d4ff;
        border: 2px solid #0d0f1a;
        top: 4px;
    }
    .timeline-content {
        padding: 8px 12px;
        background: rgba(255, 255, 255, 0.02);
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .timeline-content h5 {
        margin: 0 0 3px 0;
        font-size: 0.85rem;
    }
    .timeline-content p {
        margin: 0;
        font-size: 0.75rem;
        color: #aaa;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏢 SMD Global Consulting LLC")
st.caption("Brandshipping AI | URBÆ™ · The Apex Protocol · NOVA FUEL | Objectif : 10K€ → 30K€ → 100K€ net/mois")

init_session()

def render_chat_adjuster(key: str, prompt_key: str):
    """Affiche l'interface de chat pour ajuster un plan généré"""
    if key in st.session_state.results:
        result = st.session_state.results[key]
        
        # Bouton d'exportation
        st.download_button(
            label="📥 Télécharger ce rapport en Markdown",
            data=result,
            file_name=f"smd_{key}_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
            key=f"dl_{key}"
        )
        
        # Panel de chat
        st.markdown("#### 💬 Demander un ajustement à SMD AI Manager")
        chat_history_key = f"history_{key}"
        if chat_history_key not in st.session_state:
            st.session_state[chat_history_key] = []
            
        # Affichage de l'historique
        for chat in st.session_state[chat_history_key]:
            role_icon = "👤" if chat["role"] == "user" else "🤖"
            st.markdown(f"**{role_icon} {chat['sender']}** : {chat['content']}")
            
        with st.form(key=f"form_chat_{key}"):
            user_msg = st.text_input("Ajuster le résultat (ex: 'Rends le ton plus scientifique', 'Focalise sur Orléans') :", key=f"input_{key}")
            submit_btn = st.form_submit_button("Ajuster la stratégie")
            
        if submit_btn and user_msg:
            # Enregistrer le message de l'utilisateur
            st.session_state[chat_history_key].append({"role": "user", "sender": "Vous", "content": user_msg})
            
            # Construire le prompt d'ajustement
            system_prompt = SYSTEM_PROMPTS.get(prompt_key, "")
            user_prompt = f"""
            Voici la stratégie générée précédemment :
            {result}
            
            L'utilisateur demande la modification suivante :
            {user_msg}
            
            Mets à jour la stratégie précédente en prenant en compte cette demande. Conserve le formatage d'origine (tableaux markdown, listes), le style et le ton professionnel.
            """
            
            with st.spinner("🤖 SMD AI Manager ajuste la stratégie..."):
                updated_result = call_mistral_api(system_prompt, user_prompt)
                
            if not updated_result.startswith("❌"):
                st.session_state.results[key] = updated_result
                st.session_state[chat_history_key].append({"role": "assistant", "sender": "SMD AI Manager", "content": "La stratégie a été mise à jour !"})
                st.rerun()

def draw_customizer_canvas(primary_color, secondary_color, logo_text, bg_card_color, text_card_color, brand_name, message_card):
    logo_text_esc = logo_text.replace("'", "\\'")
    brand_name_esc = brand_name.replace("'", "\\'")
    message_card_esc = message_card.replace("'", "\\'").replace("\n", " ")
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                background: #0f111a;
                margin: 0;
                padding: 0;
                font-family: 'Outfit', -apple-system, sans-serif;
                color: white;
                display: flex;
                flex-direction: column;
                align-items: center;
                overflow: hidden;
            }}
            .container {{
                display: flex;
                width: 100%;
                justify-content: space-around;
                flex-wrap: wrap;
                padding-top: 15px;
            }}
            .panel {{
                text-align: center;
                background: rgba(255,255,255,0.02);
                border: 1px solid rgba(255,255,255,0.05);
                border-radius: 12px;
                padding: 10px;
                margin: 10px;
                width: 44%;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            }}
            h3 {{
                margin-top: 0;
                margin-bottom: 10px;
                font-size: 1.1rem;
                letter-spacing: 1px;
                color: #00d4ff;
            }}
            canvas {{
                background: #151824;
                border-radius: 8px;
                border: 1px solid rgba(255,255,255,0.05);
                max-width: 100%;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="panel">
                <h3>📦 Carton d'Expédition</h3>
                <canvas id="boxCanvas" width="350" height="320"></canvas>
            </div>
            <div class="panel">
                <h3>✉️ Carte de Remerciement</h3>
                <canvas id="cardCanvas" width="350" height="320"></canvas>
            </div>
        </div>
        
        <script>
            function shadeColor(color, percent) {{
                var num = parseInt(color.replace("#",""),16),
                amt = Math.round(2.55 * percent),
                R = (num >> 16) + amt,
                G = (num >> 8 & 0x00FF) + amt,
                B = (num & 0x0000FF) + amt;
                return "#" + (0x1000000 + (R<255?R<0?0:R:255)*0x10000 + (G<255?G<0?0:G:255)*0x100 + (B<255?B<0?0:B:255)).toString(16).slice(1);
            }}

            const boxCanvas = document.getElementById('boxCanvas');
            const bctx = boxCanvas.getContext('2d');
            
            function drawBox() {{
                const cx = boxCanvas.width / 2;
                const cy = boxCanvas.height / 2 + 10;
                const size = 90;
                const pColor = "{primary_color}";
                const sColor = "{secondary_color}";
                const logoText = "{logo_text_esc}";
                
                bctx.clearRect(0, 0, boxCanvas.width, boxCanvas.height);
                
                bctx.beginPath();
                bctx.ellipse(cx, cy + size - 10, size * 1.5, 20, 0, 0, 2 * Math.PI);
                bctx.fillStyle = 'rgba(0,0,0,0.4)';
                bctx.fill();
                
                bctx.beginPath();
                bctx.moveTo(cx, cy - size);
                bctx.lineTo(cx + size * 1.5, cy - size * 0.5);
                bctx.lineTo(cx, cy);
                bctx.lineTo(cx - size * 1.5, cy - size * 0.5);
                bctx.closePath();
                bctx.fillStyle = pColor;
                bctx.fill();
                bctx.strokeStyle = shadeColor(pColor, -15);
                bctx.lineWidth = 2;
                bctx.stroke();
                
                bctx.beginPath();
                bctx.moveTo(cx - size * 1.5, cy - size * 0.5);
                bctx.lineTo(cx, cy);
                bctx.lineTo(cx, cy + size);
                bctx.lineTo(cx - size * 1.5, cy + size - size * 0.5);
                bctx.closePath();
                bctx.fillStyle = shadeColor(pColor, -10);
                bctx.fill();
                bctx.stroke();
                
                bctx.beginPath();
                bctx.moveTo(cx, cy);
                bctx.lineTo(cx + size * 1.5, cy - size * 0.5);
                bctx.lineTo(cx + size * 1.5, cy + size - size * 0.5);
                bctx.lineTo(cx, cy + size);
                bctx.closePath();
                bctx.fillStyle = shadeColor(pColor, -25);
                bctx.fill();
                bctx.stroke();
                
                bctx.beginPath();
                bctx.moveTo(cx - size * 0.75, cy - size * 0.75);
                bctx.lineTo(cx + size * 0.75, cy - size * 0.25);
                bctx.strokeStyle = sColor;
                bctx.lineWidth = 14;
                bctx.lineCap = "round";
                bctx.stroke();
                
                bctx.beginPath();
                bctx.moveTo(cx, cy);
                bctx.lineTo(cx, cy + 30);
                bctx.strokeStyle = sColor;
                bctx.lineWidth = 14;
                bctx.stroke();
                
                bctx.save();
                bctx.translate(cx - size * 0.7, cy + 25);
                bctx.rotate(-Math.PI / 10);
                bctx.font = 'bold 16px "Outfit", Arial, sans-serif';
                bctx.fillStyle = sColor;
                bctx.textAlign = 'center';
                bctx.fillText(logoText, 0, 0);
                bctx.restore();
                
                bctx.save();
                bctx.translate(cx + size * 0.6, cy + 15);
                bctx.rotate(Math.PI / 10);
                bctx.fillStyle = '#f8f9fa';
                bctx.fillRect(-25, -35, 50, 60);
                bctx.strokeStyle = '#dee2e6';
                bctx.lineWidth = 1;
                bctx.strokeRect(-25, -35, 50, 60);
                
                bctx.fillStyle = '#000';
                bctx.fillRect(-20, 10, 5, 10);
                bctx.fillRect(-12, 10, 2, 10);
                bctx.fillRect(-8, 10, 6, 10);
                bctx.fillRect(0, 10, 3, 10);
                bctx.fillRect(5, 10, 8, 10);
                bctx.fillRect(15, 10, 3, 10);
                
                bctx.strokeStyle = '#495057';
                bctx.lineWidth = 2;
                bctx.beginPath();
                bctx.moveTo(-18, -25); bctx.lineTo(15, -25);
                bctx.moveTo(-18, -18); bctx.lineTo(5, -18);
                bctx.moveTo(-18, -11); bctx.lineTo(10, -11);
                bctx.moveTo(-18, -4); bctx.lineTo(18, -4);
                bctx.stroke();
                bctx.restore();
            }}

            const cardCanvas = document.getElementById('cardCanvas');
            const cctx = cardCanvas.getContext('2d');
            
            function drawCard() {{
                const pColor = "{bg_card_color}";
                const sColor = "{text_card_color}";
                const brandName = "{brand_name_esc}";
                const message = "{message_card_esc}";
                
                cctx.clearRect(0, 0, cardCanvas.width, cardCanvas.height);
                
                cctx.shadowColor = 'rgba(0,0,0,0.5)';
                cctx.shadowBlur = 10;
                cctx.shadowOffsetX = 2;
                cctx.shadowOffsetY = 4;
                
                cctx.fillStyle = pColor;
                cctx.fillRect(15, 15, cardCanvas.width - 30, cardCanvas.height - 30);
                cctx.shadowColor = 'transparent';
                
                cctx.strokeStyle = sColor;
                cctx.lineWidth = 2;
                cctx.strokeRect(25, 25, cardCanvas.width - 50, cardCanvas.height - 50);
                
                cctx.lineWidth = 1;
                cctx.strokeRect(30, 30, cardCanvas.width - 60, cardCanvas.height - 60);
                
                cctx.font = 'bold 22px "Outfit", Arial, sans-serif';
                cctx.fillStyle = sColor;
                cctx.textAlign = 'center';
                cctx.fillText(brandName.toUpperCase(), cardCanvas.width / 2, 70);
                
                cctx.beginPath();
                cctx.moveTo(cardCanvas.width/2 - 50, 85);
                cctx.lineTo(cardCanvas.width/2 + 50, 85);
                cctx.strokeStyle = sColor;
                cctx.stroke();
                
                cctx.font = 'italic 13px "Georgia", serif';
                cctx.fillStyle = sColor;
                
                function wrapText(context, text, x, y, maxWidth, lineHeight) {{
                    var words = text.split(' ');
                    var line = '';
                    for(var n = 0; n < words.length; n++) {{
                      var testLine = line + words[n] + ' ';
                      var metrics = context.measureText(testLine);
                      var testWidth = metrics.width;
                      if (testWidth > maxWidth && n > 0) {{
                        context.fillText(line, x, y);
                        line = words[n] + ' ';
                        y += lineHeight;
                      }}
                      else {{
                        line = testLine;
                      }}
                    }}
                    context.fillText(line, x, y);
                }}
                
                wrapText(cctx, message, cardCanvas.width / 2, 125, cardCanvas.width - 80, 20);
                
                cctx.font = 'bold 11px "Outfit", sans-serif';
                cctx.fillText("✨ MERCI POUR VOTRE COMMANDE ✨", cardCanvas.width / 2, cardCanvas.height - 55);
                
                cctx.font = '10px "Inter", sans-serif';
                cctx.fillText("Suivez-nous sur Instagram : @" + brandName.toLowerCase().replace(/\\s+/g, ''), cardCanvas.width / 2, cardCanvas.height - 35);
            }}
            
            drawBox();
            drawCard();
        </script>
    </body>
    </html>
    """
    return html_code

# ---------------------------------------------------------------------------
# SIDEBAR - COCKPIT SMD 3 MARQUES
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("📊 Cockpit SMD")

    # Logo SMD
    st.markdown("""
    <div style="text-align:center; padding:15px; background:#0e111a; border-radius:12px; margin-bottom:15px; border: 1px solid rgba(255, 255, 255, 0.05);">
        <h2 style="color:#00d4ff; margin:0; font-size:1.4rem; font-family:'Outfit';">SMD GLOBAL CONSULTING</h2>
        <p style="color:#888; margin:0; font-size:0.65rem;">LLC Wyoming · Brandshipping AI · 3 Marques</p>
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
    st.markdown("### 🕐 Cycle Client 24H")
    st.markdown("""
    <div class="timeline">
        <div class="timeline-item">
            <div class="timeline-badge" style="background: #FF2A85;"></div>
            <div class="timeline-content">
                <h5>06:00 ⚡ NOVA FUEL</h5>
                <p>Gummies "Focus Shot" & Électrolytes pour l'énergie matinale.</p>
            </div>
        </div>
        <div class="timeline-item">
            <div class="timeline-badge" style="background: #00FF66;"></div>
            <div class="timeline-content">
                <h5>08:00 🚲 URBÆ™</h5>
                <p>Sacoche étanche cadre pour un vélotaf urbain optimisé.</p>
            </div>
        </div>
        <div class="timeline-item">
            <div class="timeline-badge" style="background: #00D4FF;"></div>
            <div class="timeline-content">
                <h5>22:00 🧬 Apex Protocol</h5>
                <p>Luminothérapie circadienne pour un sommeil profond.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    st.markdown("""
    <div style="font-size:0.7rem; color:#666;">
        <b>🏢 SMD Global Consulting LLC</b><br>
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
# TABS - 7 AXES SMD (AMELIORE)
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "🎯 Stratégie",
    "🎁 Offre",
    "🎬 Créatives",
    "📢 Acquisition",
    "🤖 Agent Principal",
    "📦 Personnalisateur",
    "⚙️ Hub Opérationnel",
    "🏭 UGC Factory"
])

with tab1:
    st.subheader("🎯 Plan Stratégique & Cockpit Financier")

    # Cockpit financier avec graphiques Plotly
    with st.expander("📊 Cockpit Financier & Graphiques de Projection", expanded=True):
        st.markdown("### Simulateur P&L de la Marque")
        
        # Déterminer les paramètres de base selon la marque active
        if "URBÆ" in marque_active:
            base_prix = prix_u
            base_cout = cout_u
            color_accent = "#00FF66"
        elif "Apex" in marque_active:
            base_prix = prix_a
            base_cout = cout_a
            color_accent = "#00D4FF"
        elif "NOVA" in marque_active:
            base_prix = prix_n
            base_cout = cout_n
            color_accent = "#FF2A85"
        else:
            base_prix = 100.0
            base_cout = 30.0
            color_accent = "#9B5DE5"
            
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            budget_ads_m = st.slider("Budget Ads Mensuel (€)", 500, 20000, 3000, step=500)
        with c2:
            roas_sim = st.slider("ROAS Ciblé", 1.5, 8.0, 3.2, step=0.1)
        with c3:
            conversion_rate = st.slider("Taux Conv. (%)", 0.5, 6.0, 2.2, step=0.1)
        with c4:
            cogs_cost = st.number_input("Coût de Fabrication (€)", value=float(base_cout), step=1.0)
            
        # Calculs
        ca_mensuel_sim = budget_ads_m * roas_sim
        panier_moyen_sim = float(base_prix)
        commandes_sim = ca_mensuel_sim / panier_moyen_sim if panier_moyen_sim > 0 else 0
        cogs_total_sim = commandes_sim * cogs_cost
        profit_net_sim = ca_mensuel_sim - cogs_total_sim - budget_ads_m
        marge_nette_sim = (profit_net_sim / ca_mensuel_sim * 100) if ca_mensuel_sim > 0 else 0
        progression_10k_sim = min((profit_net_sim / 10000.0) * 100, 100.0)
        
        # Affichage
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("CA Mensuel Estimé", f"{ca_mensuel_sim:,.2f} €")
        m2.metric("Bénéfice Net Estimé", f"{profit_net_sim:,.2f} €", delta=f"{marge_nette_sim:.1f}% Marge Nette")
        m3.metric("Commandes / Mois", f"{commandes_sim:.0f} (soit {commandes_sim/30:.1f}/j)")
        m4.metric("Progression Objectif 10K€", f"{progression_10k_sim:.1f}%")
        
        # Tracé Plotly
        months = [f"Mois {i}" for i in range(1, 13)]
        
        branded_profit = []
        generic_profit = []
        curr_b = 0
        curr_g = 0
        
        for i in range(1, 13):
            # Le modèle de marque bénéficie de commandes récurrentes (rétention de 15%)
            retention_factor = 1.0 + (0.15 * min(i-1, 4))
            b_net = (profit_net_sim * retention_factor)
            g_net = profit_net_sim * (1.0 - (0.02 * (i-1))) # Perte due à l'augmentation du CPA sur du générique
            curr_b += b_net
            curr_g += g_net
            branded_profit.append(curr_b)
            generic_profit.append(curr_g)
            
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=months, y=branded_profit, name="Brandshipping (Optimisé)", line=dict(color=color_accent, width=3)))
        fig.add_trace(go.Scatter(x=months, y=generic_profit, name="Dropshipping Classique", line=dict(color="#888888", width=2, dash='dash')))
        fig.update_layout(
            title=dict(text="Projection Cumulée des Bénéfices sur 12 Mois (Modèle Brandshipping vs Classique)", font=dict(color="#ffffff")),
            xaxis_title="Période",
            yaxis_title="Bénéfices Cumulés (€)",
            # template="plotly_dark" supprimé : incompatible avec Plotly 6.0.0 (bug 'background')
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,17,26,0.8)",
            font=dict(color="#ffffff"),
            xaxis=dict(gridcolor="rgba(255,255,255,0.1)", color="#aaaaaa"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.1)", color="#aaaaaa"),
            legend=dict(font=dict(color="#ffffff")),
            height=320,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

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
        st.rerun()

    if 'strategie' in st.session_state.results:
        st.markdown("---")
        st.markdown(st.session_state.results['strategie'])
        render_chat_adjuster("strategie", "strategie")

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
        st.rerun()

    if 'offre' in st.session_state.results:
        st.markdown("---")
        st.markdown(st.session_state.results['offre'])
        render_chat_adjuster("offre", "offre")

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
        st.rerun()

    if 'creatives' in st.session_state.results:
        st.markdown("---")
        st.markdown(st.session_state.results['creatives'])
        render_chat_adjuster("creatives", "creatives")

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
        st.rerun()

    if 'acquisition' in st.session_state.results:
        st.markdown("---")
        st.markdown(st.session_state.results['acquisition'])
        render_chat_adjuster("acquisition", "acquisition")

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

Génère la stratégie complète SMD Global Consulting LLC avec intégration au cycle 24h."""

            with st.spinner("🤖 Agent Principal SMD analyse votre projet..."):
                result = generate_with_cache("agent_principal", prompt)

            if not result.startswith("❌"):
                st.session_state.results['agent_principal'] = result
            st.rerun()

    if 'agent_principal' in st.session_state.results:
        st.markdown("---")
        st.markdown("## 📋 Stratégie SMD Générée")
        st.markdown(st.session_state.results['agent_principal'])
        render_chat_adjuster("agent_principal", "agent_principal")

    with st.expander("💡 Exemples d'idées"):
        st.markdown("""
        **Exemple 1 (Safe) :** "Gummies énergie basiques pour étudiants, 49€, sans stock"

        **Exemple 2 (Bold) :** "Système nootropique complet pour traders, 299€, protocole personnalisé"

        **Exemple 3 (SMD Scale) :** "Marque nutrition + formation + consulting intégrés, réplicable sur 3 niches"

        **Exemple 4 (Cycle 24h) :** "NOVA FUEL (matin) + URBÆ™ (jour) + Apex (nuit) pour entrepreneurs performants"
        """)

with tab6:
    st.subheader("📦 Personnalisateur d'Emballage Virtuel")
    st.markdown("Configurez vos emballages et visualisez en temps réel le carton d'expédition et la carte de remerciement personnalisés.")

    # Paramètres de couleur et de texte
    col_custom1, col_custom2 = st.columns(2)
    with col_custom1:
        st.markdown("#### Conception du Carton d'Expédition")
        
        # Valeurs par défaut selon la marque
        if "URBÆ" in marque_active:
            def_p = "#1b1d28"
            def_s = "#00ff66"
            def_logo = "URBÆ"
        elif "Apex" in marque_active:
            def_p = "#090d16"
            def_s = "#00d4ff"
            def_logo = "APEX PROTOCOL"
        elif "NOVA" in marque_active:
            def_p = "#1c0d18"
            def_s = "#ff2a85"
            def_logo = "NOVA FUEL"
        else:
            def_p = "#212529"
            def_s = "#f8f9fa"
            def_logo = "SMD BRAND"
            
        box_p_color = st.color_picker("Couleur principale du colis", value=def_p, key="box_p")
        box_s_color = st.color_picker("Couleur du ruban / logo", value=def_s, key="box_s")
        box_logo_text = st.text_input("Texte du logo imprimé", value=def_logo, key="box_logo")
        
    with col_custom2:
        st.markdown("#### Conception de la Carte Insert")
        card_bg_color = st.color_picker("Couleur de fond de la carte", value="#ffffff", key="card_bg")
        card_text_color = st.color_picker("Couleur du texte de la carte", value="#111111", key="card_txt")
        card_brand = st.text_input("Nom de marque de la carte", value=def_logo, key="card_brand")
        card_message = st.text_area(
            "Message de remerciement",
            value="Merci d'avoir choisi notre marque pour optimiser votre quotidien ! Profitez de -10% sur votre prochain achat avec le code : BRAND10",
            key="card_msg"
        )
        
    st.markdown("---")
    
    # Rendu du visualiseur Canvas
    canvas_html = draw_customizer_canvas(
        box_p_color, box_s_color, box_logo_text,
        card_bg_color, card_text_color, card_brand, card_message
    )
    st.components.v1.html(canvas_html, height=360)
    
    st.success("✅ Maquette générée ! Vous pouvez utiliser ces codes couleur chez vos fournisseurs sélectionnés.")

with tab7:
    st.subheader("⚙️ Hub Opérationnel & Fournisseurs")
    
    # Ordres simulés
    st.subheader("🛒 Flux de Commandes Intégré")
    st.caption("Simulez des ventes et gérez les étapes logistiques d'emballage et d'expédition.")
    
    col_btns = st.columns(2)
    with col_btns[0]:
        if st.button("🚀 Simuler une Vente Shopify / TikTok Shop", use_container_width=True):
            import random
            clients_mock = ["Sylvie Petit", "Antoine Legrand", "Marc Moreau", "Chloé Roux", "Alexandre Simon", "Sarah Vidal"]
            villes_mock = ["Blois", "Tours", "Orléans", "Paris", "Lyon", "Marseille", "Bordeaux"]
            marques_mock = ["🚲 URBÆ™", "🧬 The Apex Protocol", "⚡ NOVA FUEL"]
            produits_mock = {
                "🚲 URBÆ™": ("Sacoche étanche cadre", 129.0),
                "🧬 The Apex Protocol": ("Lampe luminothérapie", 349.0),
                "⚡ NOVA FUEL": ("Gummies Focus + Sticks", 79.0)
            }
            
            sel_marque = random.choice(marques_mock)
            prod_name, prod_price = produits_mock[sel_marque]
            new_order = {
                "id": f"SMD-2026-{random.randint(100, 999)}",
                "client": random.choice(clients_mock),
                "ville": random.choice(villes_mock),
                "marque": sel_marque,
                "produit": prod_name,
                "prix": prod_price,
                "status": "Attente personnalisation",
                "tracking": "N/A"
            }
            st.session_state.simulated_orders.insert(0, new_order)
            st.success(f"Commande reçue ! Nouvelle vente pour {new_order['client']} ({new_order['prix']} €)")
            st.rerun()
            
    with col_btns[1]:
        if st.button("📦 Traiter la commande en attente", use_container_width=True):
            # Trouver la commande la plus ancienne non expédiée
            found = False
            for ord in reversed(st.session_state.simulated_orders):
                if ord["status"] == "Attente personnalisation":
                    ord["status"] = "Impression Colis"
                    st.info(f"Commande {ord['id']} : Lancement de l'impression du colis personnalisé.")
                    found = True
                    break
                elif ord["status"] == "Impression Colis":
                    ord["status"] = "En cours de préparation"
                    st.info(f"Commande {ord['id']} : Emballage et insertion de la carte de remerciement.")
                    found = True
                    break
                elif ord["status"] == "En cours de préparation":
                    ord["status"] = "Expédié"
                    import random
                    ord["tracking"] = f"DHL-{random.randint(100000000, 999999999)}"
                    st.success(f"Commande {ord['id']} expédiée via DHL ! Suivi : {ord['tracking']}")
                    found = True
                    break
            if not found:
                st.warning("Toutes les commandes sont déjà traitées et expédiées !")
            else:
                st.rerun()
                
    # Tableau des commandes
    df_orders = pd.DataFrame(st.session_state.simulated_orders)
    st.dataframe(df_orders, use_container_width=True)
    
    st.markdown("---")
    
    # Fournisseurs
    st.subheader("🔍 Annuaire des Fournisseurs Premium (Zéro MOQ)")
    st.markdown("Voici la liste des fournisseurs sélectionnés et vérifiés par SMD Global Consulting LLC pour le brandshipping.")
    
    sups = [
        {"Nom": "YunExpress Brandship Line", "Vitesse": "5-8 jours ouvrés", "MOQ": "1 unité", "Tarif Box": "1.80€ / unité", "Catégorie": "Électronique, Beauté", "Note": "⭐⭐⭐⭐⭐ 4.8/5"},
        {"Nom": "DHL Fastline Europe", "Vitesse": "3-5 jours ouvrés", "MOQ": "1 unité", "Tarif Box": "2.50€ / unité", "Catégorie": "Général, Premium", "Note": "⭐⭐⭐⭐⭐ 4.9/5"},
        {"Nom": "SMD Local Supply (Blois-Tours)", "Vitesse": "2-3 jours ouvrés", "MOQ": "1 unité", "Tarif Box": "3.00€ / unité (Éco-Conçu)", "Catégorie": "Sports, Mobilier", "Note": "⭐⭐⭐⭐⭐ 5.0/5"},
        {"Nom": "ZhiExpress Custom", "Vitesse": "7-12 jours ouvrés", "MOQ": "10 unités", "Tarif Box": "1.20€ / unité", "Catégorie": "Général", "Note": "⭐⭐⭐⭐ 4.5/5"}
    ]
    
    col_sups = st.columns(2)
    for index, s in enumerate(sups):
        col_target = col_sups[index % 2]
        with col_target:
            st.markdown(f"""
            <div class="glass-card">
                <h4 style="color:#00d4ff; margin:0; font-size:1.15rem; font-family:'Outfit';">{s['Nom']}</h4>
                <p style="margin:8px 0; font-size:0.85rem; color:#ccc; line-height:1.4;">
                    <b>⏱️ Délai :</b> {s['Vitesse']} | <b>📦 MOQ :</b> {s['MOQ']}<br>
                    <b>💵 Prix Colis Custom :</b> {s['Tarif Box']} <br>
                    <b>🏷️ Secteur :</b> {s['Catégorie']}
                </p>
                <div style="font-size:0.85rem; color:#FFE500;">{s['Note']}</div>
            </div>
            """, unsafe_allow_html=True)

# =============================================================================
# TAB 8 — 🏭 UGC FACTORY : PIPELINE IA COLLABORATIF
# =============================================================================
with tab8:
    st.subheader("🏭 UGC Factory — Pipeline IA Collaboratif")
    st.markdown("Production automatisée de vidéos UGC : **Brief → Script → Voix → Vidéo → Export**")

    # ── Indicateur pipeline ──────────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex; gap:8px; align-items:center; margin-bottom:20px; flex-wrap:wrap;">
        <span style="background:#1a1a3e; border:1px solid #00d4ff; border-radius:20px; padding:6px 14px; color:#00d4ff; font-size:0.8rem;">① Brief Client</span>
        <span style="color:#555;">→</span>
        <span style="background:#1a1a3e; border:1px solid #9B5DE5; border-radius:20px; padding:6px 14px; color:#9B5DE5; font-size:0.8rem;">② Agent Script (Mistral)</span>
        <span style="color:#555;">→</span>
        <span style="background:#1a1a3e; border:1px solid #51cf66; border-radius:20px; padding:6px 14px; color:#51cf66; font-size:0.8rem;">③ Voix Off (ElevenLabs)</span>
        <span style="color:#555;">→</span>
        <span style="background:#1a1a3e; border:1px solid #FF2A85; border-radius:20px; padding:6px 14px; color:#FF2A85; font-size:0.8rem;">④ Vidéo Avatar (HeyGen)</span>
        <span style="color:#555;">→</span>
        <span style="background:#1a1a3e; border:1px solid #ffd43b; border-radius:20px; padding:6px 14px; color:#ffd43b; font-size:0.8rem;">⑤ Export & Livraison</span>
    </div>
    """, unsafe_allow_html=True)

    # ── ÉTAPE 1 : BRIEF CLIENT ───────────────────────────────────────────────
    with st.expander("① Brief Client", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            ugc_marque = st.selectbox(
                "Marque",
                ["URBÆ™", "The Apex Protocol", "NOVA FUEL", "Client externe"],
                key="ugc_marque"
            )
            ugc_plateforme = st.selectbox(
                "Plateforme cible",
                ["TikTok", "Reels Instagram", "YouTube Shorts", "Toutes"],
                key="ugc_plateforme"
            )
            ugc_nb_scripts = st.slider("Nombre de scripts", 1, 10, 3, key="ugc_nb_scripts")

        with col2:
            ugc_type = st.multiselect(
                "Types de scripts",
                ["Hook données/stats", "Témoignage client", "Démonstration produit",
                 "FOMO/Urgence", "Routine quotidienne", "Test extrême", "Cross-sell SMD"],
                default=["Hook données/stats", "Témoignage client", "FOMO/Urgence"],
                key="ugc_type"
            )
            ugc_duree = st.selectbox(
                "Durée vidéo",
                ["15 secondes", "30 secondes", "45 secondes", "60 secondes"],
                key="ugc_duree"
            )

        ugc_angle = st.text_area(
            "Angle spécifique / Contexte brief",
            placeholder="Ex: Mettre en avant le gain de temps pour les vélotafeurs pressés. Ton humoristique mais crédible...",
            height=80,
            key="ugc_angle"
        )

        ugc_cta = st.text_input(
            "CTA & Code promo",
            placeholder="Ex: Code URBA20 pour -20% | Lien en bio | Stock limité",
            key="ugc_cta"
        )

    # ── ÉTAPE 2 : AGENT SCRIPT (MISTRAL) ────────────────────────────────────
    st.markdown("---")

    if st.button("🤖 ② Générer les scripts avec Mistral", type="primary",
                 use_container_width=True, key="btn_ugc_script"):

        types_str = ", ".join(ugc_type) if ugc_type else "variés"
        prompt_ugc = f"""
Marque : {ugc_marque}
Plateforme : {ugc_plateforme}
Nombre de scripts : {ugc_nb_scripts}
Types : {types_str}
Durée : {ugc_duree}
Angle / Brief : {ugc_angle or "Général - optimise selon la marque"}
CTA / Code promo : {ugc_cta or "Lien en bio"}

Produis exactement {ugc_nb_scripts} scripts UGC complets, prêts à tourner.
Chaque script doit avoir : Hook, Problème, Solution, CTA, Texte overlay, Voix off complète, Hashtags.
"""
        result = generate_with_cache("ugc_factory", prompt_ugc)
        if not result.startswith("❌"):
            st.session_state.results['ugc_scripts'] = result
            st.session_state['ugc_marque_sel'] = ugc_marque
        st.rerun()

    # Affichage des scripts générés
    if 'ugc_scripts' in st.session_state.results:
        with st.expander("📄 Scripts générés (prêts à utiliser)", expanded=True):
            st.markdown(st.session_state.results['ugc_scripts'])
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button(
                    "⬇️ Télécharger les scripts (.txt)",
                    data=st.session_state.results['ugc_scripts'],
                    file_name=f"scripts_ugc_{ugc_marque.replace('™','').replace(' ','_')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="dl_scripts"
                )

    # ── ÉTAPE 3 : VOIX OFF (ELEVENLABS) ─────────────────────────────────────
    st.markdown("---")
    with st.expander("③ Voix Off — ElevenLabs", expanded=False):
        st.markdown("**Convertissez la section 'VOIX OFF' de votre script en audio professionnel.**")

        eleven_key = st.text_input(
            "🔑 ElevenLabs API Key",
            type="password",
            placeholder="sk-... (obtenez-la sur elevenlabs.io)",
            key="eleven_key"
        )

        voix_off_texte = st.text_area(
            "Texte à convertir en voix",
            placeholder="Collez ici la section VOIX OFF de votre script généré...",
            height=120,
            key="voix_off_texte"
        )

        col1, col2 = st.columns(2)
        with col1:
            voice_id = st.selectbox(
                "Voix",
                ["Rachel (FR féminine, douce)", "Bella (FR féminine, énergique)",
                 "Antoni (FR masculin, confiant)", "Josh (FR masculin, jeune)"],
                key="voice_id"
            )
            voice_map = {
                "Rachel (FR féminine, douce)": "21m00Tcm4TlvDq8ikWAM",
                "Bella (FR féminine, énergique)": "EXAVITQu4vr4xnSDxMaL",
                "Antoni (FR masculin, confiant)": "ErXwobaYiN019PkySvjV",
                "Josh (FR masculin, jeune)": "TxGEqnHWrfWFTfGW9XjX"
            }
        with col2:
            stability = st.slider("Stabilité voix", 0.0, 1.0, 0.5, 0.05, key="stability")
            similarity = st.slider("Similarité", 0.0, 1.0, 0.75, 0.05, key="similarity")

        if st.button("🎙️ Générer la voix off", key="btn_voix", use_container_width=True):
            if not eleven_key:
                st.warning("⚠️ Entrez votre clé ElevenLabs API")
            elif not voix_off_texte:
                st.warning("⚠️ Entrez le texte à convertir")
            else:
                selected_voice = voice_map.get(voice_id, "21m00Tcm4TlvDq8ikWAM")
                with st.spinner("🎙️ Génération audio en cours..."):
                    try:
                        resp = requests.post(
                            f"https://api.elevenlabs.io/v1/text-to-speech/{selected_voice}",
                            headers={
                                "xi-api-key": eleven_key,
                                "Content-Type": "application/json"
                            },
                            json={
                                "text": voix_off_texte,
                                "model_id": "eleven_multilingual_v2",
                                "voice_settings": {
                                    "stability": stability,
                                    "similarity_boost": similarity
                                }
                            },
                            timeout=30
                        )
                        if resp.status_code == 200:
                            st.session_state['ugc_audio'] = resp.content
                            st.success("✅ Voix off générée !")
                        else:
                            st.error(f"❌ Erreur ElevenLabs ({resp.status_code}) : vérifiez votre clé API")
                    except Exception as e:
                        st.error(f"❌ Erreur : {e}")

        if 'ugc_audio' in st.session_state:
            st.audio(st.session_state['ugc_audio'], format="audio/mp3")
            st.download_button(
                "⬇️ Télécharger la voix off (.mp3)",
                data=st.session_state['ugc_audio'],
                file_name="voix_off_ugc.mp3",
                mime="audio/mpeg",
                use_container_width=True,
                key="dl_audio"
            )

    # ── ÉTAPE 4 : VIDÉO AVATAR (HEYGEN) ─────────────────────────────────────
    st.markdown("---")
    with st.expander("④ Vidéo Avatar — HeyGen", expanded=False):
        st.markdown("**Créez une vidéo avec un avatar IA qui lit votre script.**")

        heygen_key = st.text_input(
            "🔑 HeyGen API Key",
            type="password",
            placeholder="Obtenez-la sur app.heygen.com → Settings → API",
            key="heygen_key"
        )

        col1, col2 = st.columns(2)
        with col1:
            avatar_id = st.selectbox(
                "Avatar",
                ["Anna (femme, 25-30ans, style casual)", "Tyler (homme, 28-35ans, style pro)",
                 "Jade (femme, 20-25ans, style sportif)", "Marcus (homme, 30-40ans, style entrepreneur)"],
                key="avatar_id"
            )
            avatar_map = {
                "Anna (femme, 25-30ans, style casual)": "Anna_public_3_20240108",
                "Tyler (homme, 28-35ans, style pro)": "Tyler-incasualsuit-20220721",
                "Jade (femme, 20-25ans, style sportif)": "Jade_public_2_20231130",
                "Marcus (homme, 30-40ans, style entrepreneur)": "Marcus_public_3_20240108"
            }
        with col2:
            video_ratio = st.selectbox(
                "Format",
                ["9:16 (TikTok/Reels vertical)", "16:9 (YouTube horizontal)", "1:1 (Carré)"],
                key="video_ratio"
            )
            ratio_map = {"9:16 (TikTok/Reels vertical)": "9:16", "16:9 (YouTube horizontal)": "16:9", "1:1 (Carré)": "1:1"}

        script_video = st.text_area(
            "Script pour l'avatar (voix off complète)",
            placeholder="Collez ici la VOIX OFF de votre script généré à l'étape ②...",
            height=120,
            key="script_video"
        )

        if st.button("🎬 Générer la vidéo", key="btn_heygen", use_container_width=True):
            if not heygen_key:
                st.warning("⚠️ Entrez votre clé HeyGen API")
            elif not script_video:
                st.warning("⚠️ Entrez le script pour l'avatar")
            else:
                with st.spinner("🎬 Création de la vidéo en cours (1-3 min)..."):
                    try:
                        selected_avatar = avatar_map.get(avatar_id, "Anna_public_3_20240108")
                        selected_ratio = ratio_map.get(video_ratio, "9:16")
                        resp = requests.post(
                            "https://api.heygen.com/v2/video/generate",
                            headers={
                                "X-Api-Key": heygen_key,
                                "Content-Type": "application/json"
                            },
                            json={
                                "video_inputs": [{
                                    "character": {
                                        "type": "avatar",
                                        "avatar_id": selected_avatar,
                                        "avatar_style": "normal"
                                    },
                                    "voice": {
                                        "type": "text",
                                        "input_text": script_video,
                                        "voice_id": "fr-FR-DeniseNeural",
                                        "speed": 1.05
                                    }
                                }],
                                "dimension": {
                                    "width": 720 if selected_ratio == "16:9" else 405,
                                    "height": 405 if selected_ratio == "16:9" else 720
                                }
                            },
                            timeout=30
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            video_id = data.get("data", {}).get("video_id", "")
                            if video_id:
                                st.session_state['ugc_video_id'] = video_id
                                st.success(f"✅ Vidéo en cours de génération ! ID : `{video_id}`")
                                st.info("⏳ Revenez dans 2-3 minutes et collez l'ID ci-dessous pour récupérer la vidéo.")
                            else:
                                st.error("❌ Réponse HeyGen inattendue")
                        else:
                            st.error(f"❌ Erreur HeyGen ({resp.status_code}) : {resp.text[:200]}")
                    except Exception as e:
                        st.error(f"❌ Erreur : {e}")

        # Récupération vidéo par ID
        st.markdown("**Récupérer une vidéo générée :**")
        col_v1, col_v2 = st.columns([3, 1])
        with col_v1:
            video_id_input = st.text_input(
                "Video ID HeyGen",
                value=st.session_state.get('ugc_video_id', ''),
                placeholder="Collez ici le video_id reçu...",
                key="video_id_input"
            )
        with col_v2:
            if st.button("🔍 Vérifier statut", key="btn_check_video"):
                if video_id_input and heygen_key:
                    with st.spinner("Vérification..."):
                        try:
                            r = requests.get(
                                f"https://api.heygen.com/v1/video_status.get?video_id={video_id_input}",
                                headers={"X-Api-Key": heygen_key},
                                timeout=15
                            )
                            if r.status_code == 200:
                                vdata = r.json().get("data", {})
                                status = vdata.get("status", "unknown")
                                if status == "completed":
                                    video_url = vdata.get("video_url", "")
                                    st.success(f"✅ Vidéo prête !")
                                    st.video(video_url)
                                    st.markdown(f"🔗 [Télécharger la vidéo]({video_url})")
                                elif status == "processing":
                                    st.info("⏳ Encore en cours de génération, réessayez dans 1 min.")
                                else:
                                    st.warning(f"Statut : {status}")
                        except Exception as e:
                            st.error(f"❌ {e}")

    # ── ÉTAPE 5 : EXPORT & LIVRAISON ────────────────────────────────────────
    st.markdown("---")
    with st.expander("⑤ Export & Livraison Client", expanded=False):
        st.markdown("**Récapitulatif de la production UGC — prêt à livrer.**")

        if 'ugc_scripts' in st.session_state.results:
            nb_scripts = ugc_nb_scripts
            marque_sel = st.session_state.get('ugc_marque_sel', ugc_marque)

            # Tableau récapitulatif
            recap_data = {
                "Étape": ["① Brief", "② Scripts Mistral", "③ Voix ElevenLabs", "④ Vidéo HeyGen", "⑤ Export"],
                "Statut": [
                    "✅ Complété",
                    "✅ Complété" if 'ugc_scripts' in st.session_state.results else "⏳ En attente",
                    "✅ Complété" if 'ugc_audio' in st.session_state else "⏳ En attente",
                    "✅ Complété" if 'ugc_video_id' in st.session_state else "⏳ En attente",
                    "📦 Prêt"
                ],
                "Détail": [
                    f"{marque_sel} | {ugc_plateforme} | {nb_scripts} vidéos",
                    f"{nb_scripts} scripts générés",
                    "Audio MP3 disponible" if 'ugc_audio' in st.session_state else "Non généré",
                    f"ID: {st.session_state.get('ugc_video_id','Non généré')}",
                    "Téléchargement disponible"
                ]
            }
            st.dataframe(recap_data, use_container_width=True, hide_index=True)

            # Estimation ROI
            st.markdown("---")
            st.markdown("### 💰 Estimation ROI UGC Factory")
            col_r1, col_r2, col_r3 = st.columns(3)
            cout_prod_unitaire = 5.0
            prix_vente_unitaire = st.number_input("Prix de vente/vidéo (€)", value=150.0, step=10.0, key="prix_ugc")
            with col_r1:
                st.metric("Coût IA / vidéo", f"{cout_prod_unitaire:.2f} €")
            with col_r2:
                st.metric("Prix client / vidéo", f"{prix_vente_unitaire:.2f} €")
            with col_r3:
                marge_ugc = ((prix_vente_unitaire - cout_prod_unitaire) / prix_vente_unitaire * 100)
                st.metric("Marge UGC Factory", f"{marge_ugc:.1f}%", delta="Business sans stock")

            st.markdown(f"""
            > **Pack {nb_scripts} vidéos** → Revenue : **{nb_scripts * prix_vente_unitaire:,.0f} €**
            > | Coût IA : **{nb_scripts * cout_prod_unitaire:,.0f} €**
            > | Profit net : **{nb_scripts * (prix_vente_unitaire - cout_prod_unitaire):,.0f} €**
            """)

            # Bouton export complet
            export_content = f"""# 🏭 UGC FACTORY — RAPPORT DE PRODUCTION
## Marque : {marque_sel} | Plateforme : {ugc_plateforme}
## Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}
## Scripts produits : {nb_scripts}

---

{st.session_state.results.get('ugc_scripts', '')}

---
## 📊 MÉTRIQUES
- Coût production IA : {nb_scripts * cout_prod_unitaire:.2f} €
- Prix livraison client : {nb_scripts * prix_vente_unitaire:.2f} €
- Marge nette : {marge_ugc:.1f}%
- Audio généré : {'Oui' if 'ugc_audio' in st.session_state else 'Non'}
- Vidéo HeyGen ID : {st.session_state.get('ugc_video_id', 'Non généré')}
"""
            st.download_button(
                "📦 Exporter le rapport complet (.txt)",
                data=export_content,
                file_name=f"rapport_ugc_{marque_sel.replace('™','').replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True,
                key="dl_rapport"
            )
        else:
            st.info("💡 Lancez d'abord la génération des scripts à l'étape ②.")

    # Tarifs UGC Factory
    st.markdown("---")
    with st.expander("💼 Grille Tarifaire UGC Factory", expanded=False):
        tarifs = {
            "Pack": ["Starter (5 vidéos)", "Growth (15 vidéos)", "Scale (30 vidéos)", "White-label agence"],
            "Prix client": ["499 €", "999 €", "1 799 €", "300 €/mois + volume"],
            "Coût IA estimé": ["25 €", "75 €", "150 €", "~50 €/mois"],
            "Marge": ["95 %", "92 %", "91 %", "83 %+"],
            "Délai livraison": ["24h", "48h", "72h", "Continu"]
        }
        st.dataframe(tarifs, use_container_width=True, hide_index=True)
        st.caption("💡 Coût IA estimé : Mistral API (~0.5€/script) + ElevenLabs (~1€/audio) + HeyGen (~3€/vidéo)")

st.divider()
st.caption("SMD Global Consulting LLC | Brandshipping AI © 2026 | URBÆ™ · The Apex Protocol · NOVA FUEL | Propulsé par Mistral AI")
