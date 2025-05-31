
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO

st.set_page_config(layout="wide")
st.title("Analyse test all-out 30s (SmO2 + puissance)")

st.sidebar.header("Fichiers")
data_file = st.sidebar.file_uploader("Données SmO2 / Puissance", type=["csv", "xlsx"])
info_file = st.sidebar.file_uploader("Fiche coureur (.txt)", type=["txt"])
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

    st.sidebar.subheader("Délimitation des phases")
    t1 = st.sidebar.slider("Fin T1 (s)", 0, 10, 3)
    t2 = st.sidebar.slider("Fin T2 (s)", t1+1, 20, 10)
    t3 = st.sidebar.slider("Fin T3 (s)", t2+1, 35, 30)

    fig, ax1 = plt.subplots()
    ax1.set_title("Évolution SmO2 & Puissance pendant le test")
    ax1.set_xlabel("Temps (s)")
    ax1.set_ylabel("SmO2 (%)", color='blue')
    ax1.plot(df["Temps"], df["SmO2_1"], label="SmO2 capteur 1", color='blue')
    if "SmO2_2" in df:
        ax1.plot(df["Temps"], df["SmO2_2"], label="SmO2 capteur 2", color='cyan')
    ax1.tick_params(axis='y', labelcolor='blue')

    ax2 = ax1.twinx()
    ax2.set_ylabel("Puissance (W)", color='red')
    ax2.plot(df["Temps"], df["Puissance"], label="Puissance", color='red', linestyle='--')
    ax2.tick_params(axis='y', labelcolor='red')

    for t in [t1, t2, t3]:
        ax1.axvline(x=t, color='gray', linestyle=':')
    ax1.axvline(x=30, color='black', linestyle='--')

    fig.tight_layout()
    st.pyplot(fig)
