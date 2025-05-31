# TZP All-out Test Analyzer

Cette application Streamlit permet d’analyser un test all-out de 30 secondes (type Wingate) à partir des données SmO₂ et de puissance. Elle inclut :

- Courbes SmO₂ et puissance synchronisées
- Segmentation interactive des phases T1 à T4
- Analyse de la récupération musculaire (T½, pente, plancher)
- Calcul de la puissance moyenne, max, min, et indice de fatigue
- Détection du moment de chute de puissance
- Rapport PDF personnalisé généré à partir d'un fichier .txt

## Utilisation

1. Téléversez vos fichiers de test (`.csv` ou `.xlsx`) et la fiche athlète (`.txt`)
2. Ajustez les curseurs pour délimiter les phases
3. Visualisez les résultats et téléchargez un rapport PDF

## Installation locale

```
pip install -r requirements.txt
streamlit run app.py
```

---

Développé par Training Zone Performance.
