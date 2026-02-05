from fastapi import FastAPI
import requests
from scipy.stats import poisson
import datetime

API_KEY = "PUNE_API_KEY_TAU_AICI"

app = FastAPI()

BASE = "https://api-football-v1.p.rapidapi.com/v3"

headers = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}

def prob_over(h, a, goals):
    p = 0
    for i in range(goals):
        for j in range(goals - i):
            p += poisson(h).pmf(i) * poisson(a).pmf(j)
    return 1 - p

def last5(team):
    r = requests.get(f"{BASE}/fixtures?team={team}&last=5", headers=headers).json()
    scored = conceded = wins = draws = 0

    for m in r["response"]:
        hg = m["goals"]["home"]
        ag = m["goals"]["away"]

        if m["teams"]["home"]["id"] == team:
            scored += hg
            conceded += ag
            if hg > ag: wins += 1
            if hg == ag: draws += 1
        else:
            scored += ag
            conceded += hg
            if ag > hg: wins += 1
            if ag == hg: draws += 1

    return scored / 5, conceded / 5, wins, draws

@app.get("/daily")
def daily():
    today = datetime.date.today().isoformat()
    fixtures = requests.get(f"{BASE}/fixtures?date={today}", headers=headers).json()["response"]

    picks = []

    for f in fixtures:
        home = f["teams"]["home"]["id"]
        away = f["teams"]["away"]["id"]

        hs, hc, hw, hd = last5(home)
        as_, ac, aw, ad = last5(away)

        eh = (hs + ac) / 2
        ea = (as_ + hc) / 2

        over15 = prob_over(eh, ea, 2) * 100
        dc1x = (hw + hd) / 5 * 100

        name = f["teams"]["home"]["name"] + " - " + f["teams"]["away"]["name"]

        if over15 >= 75:
            picks.append({"match": name, "pick": "Over 1.5", "prob": round(over15, 1)})

        if dc1x >= 75:
            picks.append({"match": name, "pick": "1X", "prob": round(dc1x, 1)})

    picks = sorted(picks, key=lambda x: x["prob"], reverse=True)

    return picks[:5]
