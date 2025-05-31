
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO

st.set_page_config(layout="wide")
st.title("Analyse all-out 30s avec graphique SmO2 + Puissance")

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

    st.subheader("Aperçu des données")
    st.write(df.head())

    time_col = st.selectbox("Colonne Temps", df.columns)
    smo2_col = st.selectbox("Colonne SmO2", df.columns)
    power_col = st.selectbox("Colonne Puissance", df.columns)

    df["Temps"] = pd.to_numeric(df[time_col], errors="coerce")
    df["SmO2"] = pd.to_numeric(df[smo2_col], errors="coerce")
    df["Puissance"] = pd.to_numeric(df[power_col], errors="coerce")
    df = df.dropna(subset=["Temps", "SmO2", "Puissance"])

    if df.empty:
        st.error("Données invalides après nettoyage.")
    else:
        st.sidebar.header("2. Délimitation des phases")
        t1 = st.sidebar.slider("Fin T1 (s)", 0, 10, 3)
        t2 = st.sidebar.slider("Fin T2 (s)", t1 + 1, 20, 10)
        t3 = st.sidebar.slider("Fin T3 (s)", t2 + 1, 35, 30)

        st.subheader("Graphique SmO2 / Puissance")
        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax1.set_title("Évolution SmO2 et Puissance pendant le test")
        ax1.set_xlabel("Temps (s)")
        ax1.set_ylabel("SmO2 (%)", color="blue")
        ax1.plot(df["Temps"], df["SmO2"], color="blue", label="SmO2")
        ax1.tick_params(axis='y', labelcolor='blue')

        ax2 = ax1.twinx()
        ax2.set_ylabel("Puissance (W)", color="red")
        ax2.plot(df["Temps"], df["Puissance"], color="red", linestyle='--', label="Puissance")
        ax2.tick_params(axis='y', labelcolor='red')

        for t in [t1, t2, t3]:
            ax1.axvline(x=t, color='gray', linestyle=':')
        ax1.axvline(x=30, color='black', linestyle='--')

        fig.tight_layout()
        st.pyplot(fig)

        # Analyse
        zone = df[(df["Temps"] >= 0) & (df["Temps"] <= 30)]
        mean_p = zone["Puissance"].mean()
        p10 = [zone[(zone["Temps"] >= i) & (zone["Temps"] < i + 10)]["Puissance"].mean() for i in [0, 10, 20]]
        p_max = zone["Puissance"].max()
        p_min = zone["Puissance"].min()
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
        rec_half = sm_start + 0.5 * (sm_min - sm_start)
        rec_half_time = df[(df["Temps"] > t3) & (df["SmO2"] >= rec_half)]["Temps"].min()

        st.subheader("3. Résultats du test")
        results = pd.DataFrame({
            "Mesure": [
                "Puissance moyenne 30s", "0-10s", "10-20s", "20-30s",
                "Pmax", "Pmin", "ΔP", "Fatigue Index (%)",
                "Temps perte puissance", "SmO2 min", "Pente T2", "Pente T4", "T½ Réoxygénation"
            ],
            "Valeur": [
                round(mean_p, 1), round(p10[0], 1), round(p10[1], 1), round(p10[2], 1),
                int(p_max), int(p_min), int(delta_p), round(fi, 1),
                float(loss_time) if not pd.isna(loss_time) else "Non détecté",
                round(sm_min, 1), round(slope_T2, 3), round(slope_T4, 3),
                round(rec_half_time - t3, 1) if not pd.isna(rec_half_time) else "Non atteint"
            ]
        })
        st.dataframe(results)

        # PDF
        st.sidebar.header("4. Rapport PDF")
        if st.sidebar.button("Télécharger le rapport PDF") and info_file:
            info = parse_info_file(info_file)
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            try:
                c.drawImage(logo, 40, height - 100, width=80, preserveAspectRatio=True)
            except:
                pass
            c.setFont("Courier-Bold", 16)
            c.drawString(140, height - 60, "Rapport de test all-out 30s - TZP")
            c.setFont("Courier", 12)
            y = height - 130
            for k, v in info.items():
                c.drawString(40, y, f"{k}: {v}")
                y -= 15
            y -= 10
            c.drawString(40, y, "--- Résultats ---")
            y -= 15
            for index, row in results.iterrows():
                c.drawString(40, y, f"{row['Mesure']}: {row['Valeur']}")
                y -= 15
            c.showPage()
            c.save()
            st.success("PDF généré")
            st.download_button("Télécharger le PDF", data=buffer.getvalue(), file_name="rapport_test_TZP.pdf")
