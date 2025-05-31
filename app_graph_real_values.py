
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("Analyse graphique SmO2 + Puissance (réelle)")

st.sidebar.header("Chargement des données")
data_file = st.sidebar.file_uploader("Fichier .xlsx ou .csv", type=["xlsx", "csv"])

if data_file:
    if data_file.name.endswith(".csv"):
        df = pd.read_csv(data_file)
    else:
        df = pd.read_excel(data_file)

    st.subheader("Aperçu brut des données")
    st.write(df.head())

    time_col = st.selectbox("Colonne Temps", df.columns)
    smo2_col = st.selectbox("Colonne SmO2", df.columns)
    power_col = st.selectbox("Colonne Puissance", df.columns)

    # Nettoyage
    df["Temps"] = pd.to_numeric(df[time_col], errors="coerce")
    df["SmO2"] = pd.to_numeric(df[smo2_col], errors="coerce")
    df["Puissance"] = pd.to_numeric(df[power_col], errors="coerce")

    df = df.dropna(subset=["Temps", "SmO2", "Puissance"])

    if df.empty:
        st.error("Aucune donnée exploitable après nettoyage.")
    else:
        st.subheader("Statistiques descriptives")
        desc_df = df[["SmO2", "Puissance"]].describe()
        st.write(desc_df)

        st.subheader("Graphique SmO2 & Puissance")
        fig, ax1 = plt.subplots()
        ax1.set_title("SmO2 & Puissance réelles pendant l'effort")
        ax1.set_xlabel("Temps (s)")
        ax1.set_ylabel("SmO2 (%)", color='blue')
        ax1.plot(df["Temps"], df["SmO2"], color='blue', label="SmO2")
        ax1.tick_params(axis='y', labelcolor='blue')

        ax2 = ax1.twinx()
        ax2.set_ylabel("Puissance (W)", color='red')
        ax2.plot(df["Temps"], df["Puissance"], color='red', linestyle='--', label="Puissance")
        ax2.tick_params(axis='y', labelcolor='red')

        fig.tight_layout()
        st.pyplot(fig)
