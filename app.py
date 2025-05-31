import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO

st.set_page_config(layout="wide")
st.title("Analyse test all-out 30" (SmO2 + puissance)")

# --- Chargement des fichiers ---
st.sidebar.header("Fichiers")
data_file = st.sidebar.file_uploader("Données SmO2 / Puissance", type=["csv", "xlsx"])
info_file = st.sidebar.file_uploader("Fiche coureur (.txt)", type=["txt"])
logo = "logo_TZP.jpg"  # Assure-toi que ce fichier est dans le repo

# --- Lecture des données coureur ---
def parse_info_file(uploaded_txt):
    info = {}
    lines = uploaded_txt.read().decode("utf-8").splitlines()
    for line in lines:
        if ":" in line:
            key, val = line.split(":", 1)
            info[key.strip()] = val.strip()
    return info

# --- Lecture du fichier de données ---
if data_file:
    if data_file.name.endswith(".csv"):
        df = pd.read_csv(data_file)
    else:
        df = pd.read_excel(data_file)

    st.subheader("Visualisation des données")
    st.write(df.head())

    time_col = st.selectbox("Colonne Temps", df.columns)
    smo2_col_1 = st.selectbox("SmO2 Capteur 1", df.columns)
    smo2_col_2 = st.selectbox("SmO2 Capteur 2 (optionnel)", ["Aucun"] + list(df.columns))
    power_col = st.selectbox("Puissance (W)", df.columns)

    df["Temps"] = pd.to_numeric(df[time_col], errors='coerce')
    df["SmO2_1"] = pd.to_numeric(df[smo2_col_1], errors='coerce')
    df["Puissance"] = pd.to_numeric(df[power_col], errors='coerce')
    if smo2_col_2 != "Aucun":
        df["SmO2_2"] = pd.to_numeric(df[smo2_col_2], errors='coerce')

    # --- Curseurs pour délimitation T1-T4 ---
    st.sidebar.subheader("Délimitation des phases")
    t1 = st.sidebar.slider("Fin T1 (s)", 0, 10, 3)
    t2 = st.sidebar.slider("Fin T2 (s)", t1+1, 20, 10)
    t3 = st.sidebar.slider("Fin T3 (s)", t2+1, 35, 30)

    # --- Graphique SmO2 + Puissance ---
    fig, ax1 = plt.subplots()
    ax1.plot(df["Temps"], df["SmO2_1"], label="SmO2 capteur 1", color='blue')
    if "SmO2_2" in df:
        ax1.plot(df["Temps"], df["SmO2_2"], label="SmO2 capteur 2", color='cyan')
    ax1.set_ylabel("SmO2 (%)")
    ax2 = ax1.twinx()
    ax2.plot(df["Temps"], df["Puissance"], label="Puissance", color='red', linestyle='--')
    ax2.set_ylabel("Puissance (W)")
    fig.legend(loc="upper right")
    st.pyplot(fig)

    # --- Analyse puissance ---
    zone_test = df[(df["Temps"] >= 0) & (df["Temps"] <= 30)]
    mean_p = zone_test["Puissance"].mean()
    p10 = [zone_test[(zone_test["Temps"] >= i) & (zone_test["Temps"] < i+10)]["Puissance"].mean() for i in [0, 10, 20]]
    p_max = zone_test["Puissance"].max()
    p_min = zone_test["Puissance"].min()
    delta_p = p_max - p_min
    fatigue_index = 100 * (p_max - p_min) / p_max if p_max > 0 else None
    loss_time = zone_test[zone_test["Puissance"] < 0.8 * p_max]["Temps"].min()

    # --- Analyse SmO2 ---
    t4 = df["Temps"].max()
    def slope(start, end, var):
        sub = df[(df["Temps"] >= start) & (df["Temps"] <= end)]
        return (sub[var].iloc[-1] - sub[var].iloc[0]) / (end - start)

    slope_T2 = slope(t1, t2, "SmO2_1")
    slope_T4 = slope(t3, t4, "SmO2_1")
    sm_min = zone_test["SmO2_1"].min()
    sm_start = zone_test["SmO2_1"].iloc[0]
    sm_end = df[df["Temps"] > t3]["SmO2_1"].iloc[0]
    recovery_half = sm_start + 0.5 * (sm_min - sm_start)
    rec_half_time = df[(df["Temps"] > t3) & (df["SmO2_1"] >= recovery_half)]["Temps"].min()

    # --- Synthèse ---
    st.subheader("Résultats")
    st.write({
        "Puissance moyenne 30s": round(mean_p,1),
        "0-10s": round(p10[0],1), "10-20s": round(p10[1],1), "20-30s": round(p10[2],1),
        "Pmax": round(p_max,1), "Pmin": round(p_min,1), "ΔP": round(delta_p,1),
        "Fatigue Index (%)": round(fatigue_index,1),
        "Temps perte puissance (s)": round(loss_time,1) if not pd.isna(loss_time) else "Non détecté",
        "SmO2 min": round(sm_min,1), "Pente T2 SmO2 (%/s)": round(slope_T2,3),
        "Pente T4 SmO2 (%/s)": round(slope_T4,3),
        "T½ Réoxygénation": round(rec_half_time - t3,1) if not pd.isna(rec_half_time) else "Non atteint"
    })

    # --- Rapport PDF ---
    if st.button("Générer rapport PDF") and info_file:
        info = parse_info_file(info_file)
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Logo + en-tête
        c.drawImage(logo, 40, height - 100, width=80, preserveAspectRatio=True)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(140, height - 60, "Rapport de test all-out 30" - TZP")

        # Identité
        c.setFont("Helvetica", 12)
        y = height - 130
        for k, v in info.items():
            c.drawString(40, y, f"{k}: {v}")
            y -= 15

        # Résultats principaux
        y -= 15
        c.drawString(40, y, "--- Résultats principaux ---")
        y -= 15
        metrics = [
            ("Puissance moyenne 30s", mean_p),
            ("Fatigue Index", fatigue_index),
            ("SmO2 min", sm_min),
            ("Pente T2 SmO2", slope_T2),
            ("Pente T4 SmO2", slope_T4)
        ]
        for label, val in metrics:
            c.drawString(40, y, f"{label}: {round(val, 2)}")
            y -= 15

        c.showPage()
        c.save()
        st.download_button("Télécharger le rapport PDF", data=buffer.getvalue(), file_name="rapport_test_TZP.pdf")
