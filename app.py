import os
import streamlit as st
from mistralai import Mistral
from dotenv import load_dotenv
from utils.prompts import SYSTEM_PROMPTS
from utils.financial_model import calculer_projection, get_metrics_cibles

load_dotenv()

st.set_page_config(page_title="Brandshipping AI - Agent 10K", page_icon="🚀", layout="wide")
st.title("🚀 Brandshipping AI - Agent 10K")
st.caption("Produit · Offre · Créatives · Acquisition | Objectif : 10K€ net/mois")

@st.cache_resource
def init_mistral():
    api_key = st.secrets.get("MISTRAL_API_KEY") or os.getenv("MISTRAL_API_KEY")
    if not api_key:
        st.error("❌ Clé MISTRAL_API_KEY manquante dans Settings > Secrets")
        return None
    return Mistral(api_key=api_key)

client = init_mistral()

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
    ca_test = st.number_input("CA mensuel estimé (€)", value=15930, step=500)
    proj = calculer_projection(ca_test, metrics['marge_pct']/100, ca_test * ads_pct)
    
    col1, col2 = st.columns(2)
    col1.metric("Résultat Net", f"{proj['resultat_net']:,.0f} €")
    col2.metric("Progression 10K", f"{proj['progression_10k']}%")
    st.progress(min(proj['progression_10k'] / 100, 1.0))

def generate_content(module_key, user_prompt):
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
        return f"❌ Erreur : {e}"

if client:
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Stratégie", "🎁 Offre", "🎬 Créatives", "📢 Acquisition"])
    
    with tab1:
        niche = st.text_input("Niche ou passion ?", placeholder="Ex: Accessoires yoga éco-responsables")
        if st.button("Générer la stratégie", type="primary"):
            if niche:
                st.markdown(generate_content("strategie", f"Niche: {niche}. Propose 3 produits marge x3."))
            else:
                st.warning("Renseignez une niche.")
    
    with tab2:
        produit = st.text_input("Produit sélectionné", placeholder="Ex: Tapis liège + Gourde inox")
        if st.button("Générer l'offre", type="primary"):
            if produit:
                st.markdown(generate_content("offre", f"Produit: {produit}. Crée un bundle premium irrésistible."))
            else:
                st.warning("Renseignez un produit.")
    
    with tab3:
        produit_video = st.text_input("Produit pour vidéos", placeholder="Ex: Correcteur de posture")
        if st.button("Générer les scripts", type="primary"):
            if produit_video:
                st.markdown(generate_content("creatives", f"Produit: {produit_video}. 5 scripts UGC 15-30s."))
            else:
                st.warning("Renseignez un produit.")
    
    with tab4:
        contexte = st.text_area("Contexte (cible, budget, canal)", placeholder="Femmes 25-35 ans, 50€/jour, TikTok")
        if st.button("Générer le plan média", type="primary"):
            if contexte:
                st.markdown(generate_content("acquisition", f"Contexte: {contexte}. Plan test 7j + 20 angles pub."))
            else:
                st.warning("Renseignez le contexte.")
else:
    st.info("⏳ Ajoutez MISTRAL_API_KEY dans Settings > Secrets pour activer l'agent.")

st.divider()
st.caption("Brandshipping AI - Agent 10K © 2026 | Propulsé par Mistral AI")
