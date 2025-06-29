
import streamlit as st
import requests
from datetime import datetime

API_KEY_RAPIDAPI = "0053fc492dmsh0aa885662e3df2cp1fbaa2jsnde9ef0e4e8a2"
BASE_URL_LIVE = "https://api-football-v1.p.rapidapi.com/v3/fixtures"

HEADERS = {
    "X-RapidAPI-Key": API_KEY_RAPIDAPI,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}

# 📌 Récupère toutes les ligues avec matchs en live
def get_live_leagues():
    url = BASE_URL_LIVE + "?live=all"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        return []
    data = res.json().get("response", [])
    leagues = {}
    for match in data:
        league = match["league"]
        leagues[league["id"]] = f"{league['name']} ({league['country']})"
    return leagues

# 📌 Récupère les matchs en live d’une ligue
def get_live_matches_by_league(league_id):
    url = BASE_URL_LIVE + "?live=all"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        return []
    data = res.json().get("response", [])
    return [match for match in data if match["league"]["id"] == league_id and match["status"]["elapsed"] >= 60]

# 📊 Méthode simplifiée de calcul de probabilité (améliorable)
def proba_estimee(cote):
    if cote <= 1.01:
        return 0.99
    return round(1 / cote, 2)

def mise_kelly(bankroll, cote, proba, fraction=0.25):
    kelly = ((cote * proba) - 1) / (cote - 1)
    return round(bankroll * max(kelly, 0) * fraction, 0)

# Interface
st.set_page_config(page_title="SmartBet Live 🔴", layout="centered")
st.title("🔴 Analyse des matchs en live (après 60 minutes)")

bankroll = st.number_input("💼 Entrez votre bankroll (FCFA)", min_value=1000, value=50000, step=1000)

# Choix de la ligue
leagues = get_live_leagues()
if leagues:
    league_id = st.selectbox("📍 Choisis une ligue en live :", options=list(leagues.keys()), format_func=lambda x: leagues[x])
    if st.button("🔎 Analyser les matchs en cours (60min+)"):
        matches = get_live_matches_by_league(league_id)
        if not matches:
            st.warning("Aucun match live trouvé après 60 minutes pour cette ligue.")
        for m in matches:
            team_home = m["teams"]["home"]["name"]
            team_away = m["teams"]["away"]["name"]
            minute = m["status"]["elapsed"]

            cote_home = m["odds"]["betting"]["1"] if m["odds"] else 2.0
            proba_home = proba_estimee(cote_home)
            mise = mise_kelly(bankroll, cote_home, proba_home)

            st.markdown(f"### ⚽ {team_home} vs {team_away} – {minute}′")
            st.write(f"🔹 Cote Victoire {team_home} : {cote_home}")
            st.write(f"📊 Probabilité estimée : {int(proba_home * 100)}%")
            st.write(f"💸 Mise Kelly conseillée : **{mise} FCFA**")

            if proba_home >= 0.70:
                st.success("🎯 Opportunité détectée !")
                st.balloons()
            st.divider()
else:
    st.warning("Aucune ligue avec matchs live détectée.")
