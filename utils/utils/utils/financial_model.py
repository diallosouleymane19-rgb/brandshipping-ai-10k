# utils/financial_model.py

def calculer_projection(ca_mensuel: float, marge_pct: float, cout_ads: float) -> dict:
    """Calcule la projection financière vers l'objectif 10K€ net."""
    marge_brute = ca_mensuel * marge_pct
    resultat_net = marge_brute - cout_ads
    progression = min((resultat_net / 10000) * 100, 100)
    
    return {
        "ca_mensuel": round(ca_mensuel, 2),
        "marge_brute": round(marge_brute, 2),
        "cout_ads": round(cout_ads, 2),
        "resultat_net": round(resultat_net, 2),
        "progression_10k": round(progression, 1)
    }

def get_metrics_cibles(prix_vente: float, cout_produit: float) -> dict:
    """Calcule les métriques nécessaires pour atteindre 10K€ net."""
    marge_unitaire = prix_vente - cout_produit
    marge_pct = marge_unitaire / prix_vente if prix_vente > 0 else 0
    
    # Pour 10K net avec 62% de marge et ads estimées à 35% du CA
    ca_necessaire = 10000 / (marge_pct - 0.35) if (marge_pct - 0.35) > 0 else float('inf')
    commandes_jour = (ca_necessaire / prix_vente) / 30 if prix_vente > 0 else 0
    
    return {
        "marge_pct": round(marge_pct * 100, 1),
        "ca_necessaire": round(ca_necessaire, 2),
        "commandes_jour": round(commandes_jour, 1)
    }
