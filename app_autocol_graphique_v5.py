
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Analyse All-Out 30s : SmO2 + Puissance")

data_file = st.file_uploader("Charger votre fichier .xlsx", type=["xlsx"])
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

    smo2_rec = df[df["Temps"] > 30]
    sm_max = smo2_rec["SmO2"].max()
    try:
        max_time = float(smo2_rec[smo2_rec["SmO2"] == sm_max]["Temps"].values[0])
    except:
        max_time = 31.0

    t1, t2 = 3, 10

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(df["Temps"], df["SmO2"], label="SmO2", color='blue')
    ax2 = ax1.twinx()
    ax2.plot(df["Temps"], df["Puissance"], label="Puissance", color='red', linestyle='--')

    ax1.axvspan(0, t1, color='lightgreen', alpha=0.3)
    ax1.axvspan(t1, t2, color='khaki', alpha=0.3)
    ax1.axvspan(t2, 30, color='lightcoral', alpha=0.3)
    ax1.axvspan(30, max_time, color='lightblue', alpha=0.3)
    ax1.plot(max_time, sm_max, 'o', color='blue', label="SmO2 max")

    fig.tight_layout()
    st.pyplot(fig)
