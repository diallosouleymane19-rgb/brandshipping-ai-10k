# app.py
import subprocess
import sys
import os

# =============================================================================
# INSTALLATION DE SECOURS (si requirements.txt échoue sur Streamlit Cloud)
# =============================================================================
try:
    from mistralai import Mistral
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mistralai==1.6.0"])
    from mistralai import Mistral

try:
    import streamlit as st
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit==1.45.0"])
    import streamlit as st

try:
    import pandas as pd
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas==2.2.3"])
    import pandas as pd

try:
    from dotenv import load_dotenv
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv==1.1.0"])
    from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Imports locaux (doivent être après l'installation de secours)
from utils.prompts import SYSTEM_PROMPTS
from utils.financial_model import calculer_projection, get_metrics_cibles

# =============================================================================
# CONFIGURATION PAGE
# =============================================================================
st.set_page_config(
    page_title="Brandshipping AI - Agent 10K",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 Brandshipping AI - Agent 10K")
st.caption("Produit · Offre · Créatives · Acquisition | Objectif : 10K€ net/mois")

# =============================================================================
# INITIALISATION MISTRAL
# =============================================================================
@st.cache_resource
def init_mistral():
    # Priorité aux Secrets Streamlit Cloud, puis .env local
    api_key = st.secrets.get("MISTRAL_API_KEY") or os.getenv("MISTRAL_API_KEY")
    if not api_key:
        st.error("❌ Clé MISTRAL_API_KEY manquante. Ajoutez-la dans Settings > Secrets sur Streamlit Cloud ou dans un fichier .env en local.")
        return None
    try:
        return Mistral(api_key=api_key)
    except Exception as e:
        st.error(f"❌ Erreur initialisation Mistral : {e}")
        return None

client = init_mistral()

# =============================================================================
# SIDEBAR : COCKPIT IA
# =============================================================================
with st.sidebar:
    st.header("📊 Cockpit IA")

    prix = st.number_input("Prix de vente (€)", value=89.0, step=5.0, min_value=1.0)
    cout = st.number_input("Coût produit (€)", value=34.0, step=1.0, min_value=0.0)
    ads_pct = st.slider("Budget Ads (% du CA)", 10, 50, 22) / 100

    metrics = get_metrics_cibles(prix, cout)

    st.metric("Marge Brute", f"{metrics['marge_pct']}%")
    st.metric("CA nécessaire / mois", f"{metrics['ca_necessaire']:,.0f} €")
    st.metric("Commandes / jour", f"{metrics['commandes_jour']:.1f}")

    st.divider()
    st.subheader("Projection Actuelle")

    ca_test = st.number_input(
        "CA mensuel estimé (€)",
        value=15930,
        step=500,
        min_value=0
    )

    proj = calculer_projection(ca_test, metrics['marge_pct'] / 100, ca_test * ads_pct)

    col1, col2 = st.columns(2)
    col1.metric("Résultat Net", f"{proj['resultat_net']:,.0f} €")
    col2.metric("Progression 10K", f"{proj['progression_10k']}%")
    st.progress(min(proj['progression_10k'] / 100, 1.0))

    st.divider()
    st.caption("Agent 10K — Plan itératif, pas une garantie.")

# =============================================================================
# FONCTION DE GÉNÉRATION IA
# =============================================================================
def generate_content(module_key: str, user_prompt: str) -> str:
    """Appelle Mistral avec le prompt système correspondant au module."""
    try:
        response = client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPTS[module_key]},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Erreur lors de la génération : {e}"

# =============================================================================
# ONGLETS MODULES IA
# =============================================================================
if client:
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Stratégie & Niche",
        "🎁 Offre Bundle",
        "🎬 Créatives UGC",
        "📢 Acquisition"
    ])

    # ── TAB 1 : STRATÉGIE ────────────────────────────────────────────────
    with tab1:
        st.subheader("Trouver 3 produits à marge x3")
        niche = st.text_input(
            "Quelle est votre niche ou passion ?",
            placeholder="Ex: Accessoires yoga éco-responsables",
            key="niche_input"
        )
        if st.button("Générer la stratégie", type="primary", key="btn_strat"):
            if niche:
                result = generate_content(
                    "strategie",
                    f"Niche: {niche}. Propose 3 produits concrets avec analyse marge x3, fournisseurs potentiels et justification."
                )
                st.markdown(result)
            else:
                st.warning("⚠️ Veuillez renseigner une niche.")

    # ── TAB 2 : OFFRE BUNDLE ─────────────────────────────────────────────
    with tab2:
        st.subheader("Créer une offre Bundle Premium")
        produit = st.text_input(
            "Produit sélectionné",
            placeholder="Ex: Tapis de liège + Gourde inox",
            key="offre_produit"
        )
        if st.button("Générer l'offre", type="primary", key="btn_offre"):
            if produit:
                result = generate_content(
                    "offre",
                    f"Produit: {produit}. Crée un bundle premium irrésistible avec pricing psychologique, bonus perçus et argumentaire."
                )
                st.markdown(result)
            else:
                st.warning("⚠️ Veuillez renseigner un produit.")

    # ── TAB 3 : CRÉATIVES UGC ────────────────────────────────────────────
    with tab3:
        st.subheader("5 Scripts Vidéo UGC (15-30s)")
        produit_video = st.text_input(
            "Produit pour les vidéos",
            placeholder="Ex: Correcteur de posture",
            key="crea_produit"
        )
        if st.button("Générer les scripts", type="primary", key="btn_crea"):
            if produit_video:
                result = generate_content(
                    "creatives",
                    f"Produit: {produit_video}. Génère 5 scripts UGC format Hook+Problème+Solution+CTA."
                )
                st.markdown(result)
            else:
                st.warning("⚠️ Veuillez renseigner un produit.")

    # ── TAB 4 : ACQUISITION ──────────────────────────────────────────────
    with tab4:
        st.subheader("Plan d'Acquisition & 20 Angles Pub")
        contexte = st.text_area(
            "Contexte (cible, budget, canal prioritaire)",
            placeholder="Femmes 25-35 ans, 50€/jour, TikTok Shop",
            key="acq_contexte"
        )
        if st.button("Générer le plan média", type="primary", key="btn_acq"):
            if contexte:
                result = generate_content(
                    "acquisition",
                    f"Contexte: {contexte}. Élabore un plan de test 7 jours avec structure campagne, audiences, KPIs et 20 angles publicitaires."
                )
                st.markdown(result)
            else:
                st.warning("⚠️ Veuillez renseigner le contexte.")

else:
    st.info("⏳ En attente de la clé API Mistral pour activer l'agent...")
    st.caption("Ajoutez MISTRAL_API_KEY dans Settings > Secrets de votre app Streamlit Cloud.")

# =============================================================================
# FOOTER
# =============================================================================
st.divider()
st.caption("Brandshipping AI - Agent 10K © 2026 | Propulsé par Mistral AI & Streamlit")
