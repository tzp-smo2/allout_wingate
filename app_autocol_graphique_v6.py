
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("Analyse all-out 30s (SmO2 + Puissance) - v6")

st.sidebar.header("1. Charger les fichiers")
data_file = st.sidebar.file_uploader("Fichier de données (.xlsx ou .csv)", type=["xlsx", "csv"])
info_file = st.sidebar.file_uploader("Fiche athlète (.txt)", type=["txt"])

if data_file:
    df = pd.read_excel(data_file)
    df = df.rename(columns={
        "Time[s]": "Temps",
        "SmO2[%]": "SmO2",
        "Power -  2[W]": "Puissance"
    })

    df["Temps"] = pd.to_numeric(df["Temps"], errors="coerce")
    df["SmO2"] = pd.to_numeric(df["SmO2"], errors="coerce")
    df["Puissance"] = pd.to_numeric(df["Puissance"], errors="coerce")
    df = df.dropna(subset=["Temps", "SmO2", "Puissance"])

    st.subheader("Aperçu des données")
    st.write(df.head())

    st.sidebar.header("2. Délimitation des phases")
    t1 = st.sidebar.slider("Fin T1 (s)", 0, 10, 3)
    t2 = st.sidebar.slider("Fin T2 (s)", t1 + 1, 30, 10)
    t3 = 30  # Fixe

    # Détection SmO2 max après 30s
    smo2_rec = df[df["Temps"] > 30]
    sm_max = smo2_rec["SmO2"].max()
    try:
        max_time = float(smo2_rec[smo2_rec["SmO2"] == sm_max]["Temps"].values[0])
    except:
        max_time = 31.0

    st.subheader("Graphique SmO2 / Puissance")
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.set_title("Évolution SmO2 & Puissance pendant le test")
    ax1.set_xlabel("Temps (s)")
    ax1.set_ylabel("SmO2 (%)", color='blue')
    ax1.plot(df["Temps"], df["SmO2"], color='blue', label='SmO2')
    ax1.tick_params(axis='y', labelcolor='blue')

    ax2 = ax1.twinx()
    ax2.set_ylabel("Puissance (W)", color='red')
    ax2.plot(df["Temps"], df["Puissance"], color='red', linestyle='--', label='Puissance')
    ax2.tick_params(axis='y', labelcolor='red')

    # Zones colorées
    ax1.axvspan(0, t1, color='lightgreen', alpha=0.3)
    ax1.axvspan(t1, t2, color='khaki', alpha=0.3)
    ax1.axvspan(t2, 30, color='lightcoral', alpha=0.3)
    ax1.axvspan(30, max_time, color='lightblue', alpha=0.3)

    # SmO2 max point
    ax1.plot(max_time, sm_max, 'o', color='blue', label='SmO2 max')

    fig.tight_layout()
    st.pyplot(fig)

    # ANALYSE
    zone = df[(df["Temps"] >= 0) & (df["Temps"] <= 30)]
    mean_p = zone["Puissance"].mean()
    p10 = [zone[(zone["Temps"] >= i) & (zone["Temps"] < i + 10)]["Puissance"].mean() for i in [0, 10, 20]]
    p_max = zone["Puissance"].max()
    p_min = df[(df["Temps"] >= 5) & (df["Temps"] <= 30)]["Puissance"].min()
    delta_p = p_max - p_min
    fi = 100 * delta_p / p_max if p_max > 0 else None
    loss_time = zone[zone["Puissance"] < 0.8 * p_max]["Temps"].min()

    def slope(start, end, var):
        sub = df[(df["Temps"] >= start) & (df["Temps"] <= end)]
        return (sub[var].iloc[-1] - sub[var].iloc[0]) / (end - start)

    slope_T2 = slope(t1, t2, "SmO2")
    slope_T4 = slope(30, df["Temps"].max(), "SmO2")
    sm_min = zone["SmO2"].min()
    rec_half = sm_min + 0.5 * (sm_max - sm_min)
    rec_half_time = df[(df["Temps"] > 30) & (df["SmO2"] >= rec_half)]["Temps"].min()

    st.subheader("Résultats du test")
    results = pd.DataFrame({
        "Mesure": [
            "Puissance moyenne 30s", "0-10s", "10-20s", "20-30s",
            "Pmax", "Pmin (5-30s)", "ΔP", "Fatigue Index (%)",
            "Temps perte puissance", "SmO2 min", "SmO2 max", "Pente T2", "Pente T4", "T½ Réoxygénation"
        ],
        "Valeur": [
            round(mean_p, 1), round(p10[0], 1), round(p10[1], 1), round(p10[2], 1),
            int(p_max), int(p_min), int(delta_p), round(fi, 1),
            float(loss_time) if not pd.isna(loss_time) else "Non détecté",
            round(sm_min, 1), round(sm_max, 1), round(slope_T2, 3), round(slope_T4, 3),
            round(rec_half_time - 30, 1) if not pd.isna(rec_half_time) else "Non atteint"
        ]
    })
    st.dataframe(results)
