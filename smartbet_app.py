
import streamlit as st
import requests
from datetime import datetime

API_KEY = "e466a37640c044bfbeaceaef804ff773"
BASE_URL = "https://api.football-data.org/v4/matches"

def get_real_matches():
    headers = {"X-Auth-Token": API_KEY}
    today = datetime.today().strftime('%Y-%m-%d')
    response = requests.get(f"{BASE_URL}?dateFrom={today}&dateTo={today}", headers=headers)
    if response.status_code != 200:
        return []
    return response.json().get("matches", [])

def get_live_matches():
    headers = {"X-Auth-Token": API_KEY}
    params = {"status": "LIVE"}
    response = requests.get(BASE_URL, headers=headers, params=params)
    if response.status_code != 200:
        return []
    return response.json().get("matches", [])

def analyse_match_avance(home, away):
    data_forme = {
        "PSG": 5, "Marseille": 2, "Lyon": 4, "Nice": 3, "Monaco": 4,
        "Rennes": 3, "Brest": 2, "Lens": 3, "Auxerre": 1, "Toulouse": 3
    }
    forme_home = data_forme.get(home, 2)
    forme_away = data_forme.get(away, 2)
    delta = forme_home - forme_away
    proba = 0.55 + (0.05 * delta)
    proba = max(0.50, min(proba, 0.80))
    if delta > 1:
        cote = 1.60
    elif delta == 0:
        cote = 2.20
    else:
        cote = 2.80
    return {"home": home, "away": away, "proba": proba, "cote": cote}

def mise_kelly(bankroll, cote, proba, fraction=0.25):
    kelly = ((cote * proba) - 1) / (cote - 1)
    return round(bankroll * max(kelly, 0) * fraction, 0)

def analyse_live_match_avec_alerte(match):
    home = match["homeTeam"]["name"]
    away = match["awayTeam"]["name"]
    score_home = match["score"]["fullTime"]["home"] or 0
    score_away = match["score"]["fullTime"]["away"] or 0
    utc = match["utcDate"]
    heure_match = utc[11:16]
    minute_simulee = datetime.utcnow().minute
    score = f"{score_home} - {score_away}"
    alerte, animation = "", None

    if score_home == 0 and score_away == 0 and minute_simulee > 30:
        alerte = "0-0 après 30' → Over 0.5"
        animation = "balloons"
    elif score_home == 1 and score_away == 1 and 45 < minute_simulee < 75:
        alerte = "1-1 entre 45'-75' → BTTS + Over 2.5"
        animation = "balloons"
    elif abs(score_home - score_away) >= 2 and minute_simulee >= 60:
        alerte = "2 buts d’écart → Over ou Handicap"
        animation = "snow"
    else:
        alerte = "Pas de signal fort"

    return {
        "match": f"{home} vs {away}",
        "score": score,
        "minute": heure_match,
        "alerte": alerte,
        "animation": animation
    }

st.set_page_config(page_title="SmartBet Bot", layout="wide")
menu = st.sidebar.selectbox("Menu", ["Matchs du jour", "Live + Alertes"])

if menu == "Matchs du jour":
    st.title("⚽ Analyse poussée des matchs du jour")
    bankroll = st.number_input("💼 Bankroll actuelle (FCFA)", min_value=1000, value=50000, step=1000)

    if st.button("Analyser les meilleurs matchs"):
        matchs = get_real_matches()
        recommandations = []

        for m in matchs:
            home = m["homeTeam"]["name"]
            away = m["awayTeam"]["name"]
            analyse = analyse_match_avance(home, away)
            proba = analyse["proba"]
            cote = analyse["cote"]
            mise = mise_kelly(bankroll, cote, proba)
            if mise > 0 and proba > (1 / cote):
                recommandations.append({"match": f"{home} vs {away}", "proba": proba, "cote": cote, "mise": mise})

        if recommandations:
            for r in recommandations:
                st.subheader(r["match"])
                st.write(f"Cote : {r['cote']} | Probabilité : {int(r['proba']*100)}%")
                st.success(f"Mise conseillée : {r['mise']} FCFA")
                st.divider()
        else:
            st.warning("Aucun match à value aujourd'hui.")

elif menu == "Live + Alertes":
    st.title("🔴 Analyse en live avec alertes ✨")
    if st.button("Scanner les matchs en direct"):
        matchs = get_live_matches()
        if matchs:
            for match in matchs:
                res = analyse_live_match_avec_alerte(match)
                st.subheader(res['match'])
                st.write(f"Heure : {res['minute']} | Score : {res['score']}")
                st.success(f"Alerte : {res['alerte']}")
                if res['animation'] == "balloons":
                    st.balloons()
                elif res['animation'] == "snow":
                    st.snow()
                st.divider()
        else:
            st.warning("Aucun match en direct trouvé.")
