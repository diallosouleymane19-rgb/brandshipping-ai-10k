import os
st_files = []
for root, dirs, files in os.walk("/mount/src/brandshipping-ai-10k"):
    for f in files:
        st_files.append(os.path.join(root, f))
import json
import requests
import streamlit as st
from dotenv import load_dotenv
from utils.prompts import SYSTEM_PROMPTS
from utils.financial_model import calculer_projection, get_metrics_cibles

load_dotenv()

st.set_page_config(page_title="Brandshipping AI - Agent 10K", page_icon="🚀", layout="wide")
st.title("🚀 Brandshipping AI - Agent 10K")
st.caption("Produit · Offre · Créatives · Acquisition | Objectif : 10K€ net/mois")

# =============================================================================
# FONCTION D'APPEL API MISTRAL (SANS SDK)
# =============================================================================
def call_mistral_api(system_prompt: str, user_prompt: str) -> str:
    """Appelle l'API REST Mistral directement via requests."""
    api_key = st.secrets.get("MISTRAL_API_KEY") or os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return "❌ Clé MISTRAL_API_KEY manquante dans Settings > Secrets"
    
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "mistral-large-latest",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"❌ Erreur API Mistral : {e}"
    except (KeyError, IndexError) as e:
        return f"❌ Format de réponse inattendu : {e}"

# =============================================================================
# COCKPIT IA (SIDEBAR)
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
    ca_test = st.number_input("CA mensuel estimé (€)", value=15930, step=500)
    proj = calculer_projection(ca_test, metrics['marge_pct']/100, ca_test * ads_pct)

    col1, col2 = st.columns(2)
    col1.metric("Résultat Net", f"{proj['resultat_net']:,.0f} €")
    col2.metric("Progression 10K", f"{proj['progression_10k']}%")
    st.progress(min(proj['progression_10k'] / 100, 1.0))

# =============================================================================
# MODULES IA (ONGLETS)
# =============================================================================
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Stratégie", "🎁 Offre", "🎬 Créatives", "📢 Acquisition"])

with tab1:
    st.subheader("Trouver 3 produits à marge x3")
    niche = st.text_input("Niche ou passion ?", placeholder="Ex: Accessoires yoga éco-responsables")
    if st.button("Générer la stratégie", type="primary"):
        if niche:
            with st.spinner("Analyse de niche en cours..."):
                result = call_mistral_api(SYSTEM_PROMPTS["strategie"], f"Niche: {niche}. Propose 3 produits concrets avec analyse marge x3.")
            st.markdown(result)
        else:
            st.warning("Renseignez une niche.")

with tab2:
    st.subheader("Créer une offre Bundle Premium")
    produit = st.text_input("Produit sélectionné", placeholder="Ex: Tapis liège + Gourde inox")
    if st.button("Générer l'offre", type="primary"):
        if produit:
            with st.spinner("Création de l'offre..."):
                result = call_mistral_api(SYSTEM_PROMPTS["offre"], f"Produit: {produit}. Crée un bundle premium irrésistible.")
            st.markdown(result)
        else:
            st.warning("Renseignez un produit.")

with tab3:
    st.subheader("5 Scripts Vidéo UGC (15-30s)")
    produit_video = st.text_input("Produit pour vidéos", placeholder="Ex: Correcteur de posture")
    if st.button("Générer les scripts", type="primary"):
        if produit_video:
            with st.spinner("Génération des scripts..."):
                result = call_mistral_api(SYSTEM_PROMPTS["creatives"], f"Produit: {produit_video}. Génère 5 scripts UGC format Hook+Problème+Solution+CTA.")
            st.markdown(result)
        else:
            st.warning("Renseignez un produit.")

with tab4:
    st.subheader("Plan d'Acquisition & 20 Angles Pub")
    contexte = st.text_area("Contexte (cible, budget, canal)", placeholder="Femmes 25-35 ans, 50€/jour, TikTok Shop")
    if st.button("Générer le plan média", type="primary"):
        if contexte:
            with st.spinner("Élaboration du plan média..."):
                result = call_mistral_api(SYSTEM_PROMPTS["acquisition"], f"Contexte: {contexte}. Plan test 7j + 20 angles pub.")
            st.markdown(result)
        else:
            st.warning("Renseignez le contexte.")

st.divider()
st.caption("Brandshipping AI - Agent 10K © 2026 | Propulsé par Mistral AI (API REST)")
