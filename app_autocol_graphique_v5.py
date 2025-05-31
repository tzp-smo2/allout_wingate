
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO

st.set_page_config(layout="wide")
st.title("Analyse all-out 30s (SmO2 + Puissance) - v2")

st.sidebar.header("1. Charger les fichiers")
data_file = st.sidebar.file_uploader("Fichier de données (.xlsx ou .csv)", type=["xlsx", "csv"])
info_file = st.sidebar.file_uploader("Fiche athlète (.txt)", type=["txt"])
logo = "logo_TZP.jpg"

def parse_info_file(uploaded_txt):
    info = {}
    lines = uploaded_txt.read().decode("utf-8").splitlines()
    for line in lines:
        if ":" in line:
            key, val = line.split(":", 1)
            info[key.strip()] = val.strip()
    return info

if data_file:
    if data_file.name.endswith(".csv"):
        df = pd.read_csv(data_file)
    else:
        df = pd.read_excel(data_file)

    time_col = next((c for c in df.columns if "Time[s]" in c or "Temps" in c), None)
    smo2_col = next((c for c in df.columns if "SmO2[%]" in c), None)
    smo2_col_2 = next((c for c in df.columns if "SmO2 - 2[%]" in c), None)
    power_col = next((c for c in df.columns if "Power" in c or "Target" in c), None)

    if not all([time_col, smo2_col, power_col]):
        st.error("Colonnes manquantes.")
        st.write("Colonnes trouvées :", list(df.columns))
    else:
        df = df.rename(columns={time_col: "Temps", smo2_col: "SmO2", power_col: "Puissance"})
        if smo2_col_2:
            df = df.rename(columns={smo2_col_2: "SmO2_2"})

        df["Temps"] = pd.to_numeric(df["Temps"], errors="coerce")
        df["SmO2"] = pd.to_numeric(df["SmO2"], errors="coerce")
        df["Puissance"] = pd.to_numeric(df["Puissance"], errors="coerce")
        if "SmO2_2" in df:
            df["SmO2_2"] = pd.to_numeric(df["SmO2_2"], errors="coerce")

        df = df.dropna(subset=["Temps", "SmO2", "Puissance"])

        st.subheader("Aperçu des données")
        st.write(df.head())

        st.sidebar.header("2. Délimitation des phases")
        t1 = st.sidebar.slider("Fin T1 (s)", 0, 10, 3)
        t3 = st.sidebar.slider("Fin T3 (s)", t1 + 1, 35, 30)
        t2 = 30  # Phase T2 fixée à 30s

        st.subheader("Graphique SmO2 / Puissance")
        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax1.set_title("SmO2 et Puissance pendant le test")
        ax1.set_xlabel("Temps (s)")
        ax1.set_ylabel("SmO2 (%)", color="blue")
        ax1.plot(df["Temps"], df["SmO2"], color="blue", label="SmO2 capteur 1")
        if "SmO2_2" in df:
            ax1.plot(df["Temps"], df["SmO2_2"], color="cyan", linestyle=':', label="SmO2 capteur 2")
        ax1.tick_params(axis='y', labelcolor='blue')

        ax2 = ax1.twinx()
        ax2.set_ylabel("Puissance (W)", color="red")
        ax2.plot(df["Temps"], df["Puissance"], color="red", linestyle='--', label="Puissance")
        ax2.tick_params(axis='y', labelcolor='red')

        for t in [t1, t2, t3]:
            ax1.axvline(x=t, color='gray', linestyle=':')
        ax1.axvline(x=30, color='black', linestyle='--')

        
        # Zones colorées
        ax1.axvspan(0, t1, color='lightgreen', alpha=0.3)
        ax1.axvspan(t1, t2, color='khaki', alpha=0.3)
        ax1.axvspan(t2, 30, color='lightcoral', alpha=0.3)
        ax1.axvspan(30, max_time, color='lightblue', alpha=0.3)

        # Point bleu SmO2 max
        ax1.plot(max_time, sm_max, 'o', color='blue', label="SmO2 max")

        fig.tight_layout()
        st.pyplot(fig)

        
        # Calcul SmO2 max et temps correspondant avant affichage
        smo2_rec = df[df["Temps"] > 30]
        sm_max = smo2_rec["SmO2"].max()
        max_time = smo2_rec[smo2_rec["SmO2"] == sm_max]["Temps"].iloc[0] if not smo2_rec.empty else 30


        # Analyse
        smo2_rec = df[df["Temps"] > 30]
        sm_max = smo2_rec["SmO2"].max()
        max_time = smo2_rec[smo2_rec["SmO2"] == sm_max]["Temps"].iloc[0]
        zone = df[(df["Temps"] >= 0) & (df["Temps"] <= 30)]
        mean_p = zone["Puissance"].mean()
        p10 = [zone[(zone["Temps"] >= i) & (zone["Temps"] < i + 10)]["Puissance"].mean() for i in [0, 10, 20]]
        p_max = zone["Puissance"].max()
        p_min = df[(df["Temps"] >= 5) & (df["Temps"] <= 30)]["Puissance"].min()  # Corrigé ici
        delta_p = p_max - p_min
        fi = 100 * delta_p / p_max if p_max > 0 else None
        loss_time = zone[zone["Puissance"] < 0.8 * p_max]["Temps"].min()

        def slope(start, end, var):
            sub = df[(df["Temps"] >= start) & (df["Temps"] <= end)]
            return (sub[var].iloc[-1] - sub[var].iloc[0]) / (end - start)

        slope_T2 = slope(t1, t2, "SmO2")
        slope_T4 = slope(t3, df["Temps"].max(), "SmO2")
        sm_min = zone["SmO2"].min()
        sm_start = zone["SmO2"].iloc[0]
        rec_half = sm_min + 0.5 * (sm_max - sm_min)
        rec_half_time = df[(df["Temps"] > t3) & (df["SmO2"] >= rec_half)]["Temps"].min()

        st.subheader("Résultats du test")
        results = pd.DataFrame({
            "Mesure": [
                "Puissance moyenne 30s", "0-10s", "10-20s", "20-30s",
                "Pmax", "Pmin (5-30s)", "ΔP", "Fatigue Index (%)",
                "Temps perte puissance", "SmO2 min", "Pente T2", "Pente T4", "SmO2 max", "T½ Réoxygénation"
            ],
            "Valeur": [
                round(mean_p, 1), round(p10[0], 1), round(p10[1], 1), round(p10[2], 1),
                int(p_max), int(p_min), int(delta_p), round(fi, 1),
                float(loss_time) if not pd.isna(loss_time) else "Non détecté",
                round(sm_min, 1), round(slope_T2, 3), round(slope_T4, 3),
                round(sm_max, 1), round(rec_half_time - 30, 1) if not pd.isna(rec_half_time) else "Non atteint"
            ]
        })
        st.dataframe(results)
