# app.py
import streamlit as st
import os
from dotenv import load_dotenv
from mistralai import Mistral
from utils.prompts import SYSTEM_PROMPTS
from utils.financial_model import calculer_projection, get_metrics_cibles

load_dotenv()

st.set_page_config(page_title="Brandshipping AI - Agent 10K", page_icon="🚀", layout="wide")
st.title("🚀 Brandshipping AI - Agent 10K")
st.caption("Produit · Offre · Créatives · Acquisition | Objectif : 10K€ net/mois")

# Initialisation Mistral
@st.cache_resource
def init_mistral():
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        st.error("❌ Clé MISTRAL_API_KEY manquante dans .env")
        return None
    return Mistral(api_key=api_key)

client = init_mistral()

# --- SIDEBAR : COCKPIT IA ---
with st.sidebar:
    st.header("📊 Cockpit IA")
    prix = st.number_input("Prix de vente (€)", value=89.0, step=5.0)
    cout = st.number_input("Coût produit (€)", value=34.0, step=1.0)
    ads_pct = st.slider("Budget Ads (% du CA)", 10, 50, 22) / 100
    
    metrics = get_metrics_cibles(prix, cout)
    st.metric("Marge Brute", f"{metrics['marge_pct']}%")
    st.metric("CA nécessaire / mois", f"{metrics['ca_necessaire']:,.0f} €")
    st.metric("Commandes / jour", f"{metrics['commandes_jour']:.1f}")
    
    st.divider()
    st.subheader("Projection Actuelle")
    ca_test = st.number_input("CA mensuel estimé (€)", value=15930, step=500)
    proj = calculer_projection(ca_test, metrics['marge_pct']/100, ca_test * ads_pct)
    
    col1, col2 = st.columns(2)
    col1.metric("Résultat Net", f"{proj['resultat_net']:,.0f} €")
    col2.metric("Progression 10K", f"{proj['progression_10k']}%")
    st.progress(proj['progression_10k'] / 100)

# --- MODULES IA ---
if client:
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Stratégie & Niche", "🎁 Offre Bundle", "🎬 Créatives UGC", "📢 Acquisition"])
    
    def generate_content(module_key: str, user_prompt: str):
        with st.spinner(f"L'Agent 10K travaille sur {module_key}..."):
            response = client.chat.complete(
                model="mistral-large-latest",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPTS[module_key]},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.choices[0].message.content

    with tab1:
        st.subheader("Trouver 3 produits à marge x3")
        niche = st.text_input("Quelle est votre niche ou passion ?", placeholder="Ex: Accessoires yoga éco-responsables")
        if st.button("Générer la stratégie", key="btn_strat"):
            if niche:
                result = generate_content("strategie", f"Niche: {niche}. Propose 3 produits concrets avec analyse marge x3.")
                st.markdown(result)
            else:
                st.warning("Veuillez renseigner une niche.")

    with tab2:
        st.subheader("Créer une offre Bundle Premium")
        produit = st.text_input("Produit sélectionné", placeholder="Ex: Tapis de liège + Gourde inox")
        if st.button("Générer l'offre", key="btn_offre"):
            if produit:
                result = generate_content("offre", f"Produit: {produit}. Crée un bundle premium irrésistible.")
                st.markdown(result)
            else:
                st.warning("Veuillez renseigner un produit.")

    with tab3:
        st.subheader("5 Scripts Vidéo UGC")
        produit_video = st.text_input("Produit pour les vidéos", placeholder="Ex: Correcteur de posture")
        if st.button("Générer les scripts", key="btn_crea"):
            if produit_video:
                result = generate_content("creatives", f"Produit: {produit_video}. Génère 5 scripts UGC 15-30s.")
                st.markdown(result)
            else:
                st.warning("Veuillez renseigner un produit.")

    with tab4:
        st.subheader("Plan d'Acquisition & 20 Angles Pub")
        contexte = st.text_area("Contexte (cible, budget, canal prioritaire)", placeholder="Femmes 25-35 ans, 50€/jour, TikTok Shop")
        if st.button("Générer le plan média", key="btn_acq"):
            if contexte:
                result = generate_content("acquisition", f"Contexte: {contexte}. Plan de test 7j + 20 angles pub.")
                st.markdown(result)
            else:
                st.warning("Veuillez renseigner le contexte.")
else:
    st.info("⏳ En attente de la clé API Mistral pour activer l'agent...")
