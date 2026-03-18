import requests
import asyncio
import os
from telegram import Bot

# ======================
# CONFIG
# ======================

import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))
API_KEY = os.getenv("API_KEY")
print("TOKEN:", BOT_TOKEN)
print("CHAT_ID:", CHAT_ID)
print("API:", API_KEY)

bot = Bot(token=BOT_TOKEN)
HEADERS = {
    "x-apisports-key": API_KEY
}

URL_LIVE = "https://v3.football.api-sports.io/fixtures?live=all"

LIGAS_GOLEADORAS = [39, 140, 135, 78, 61, 88]

# ======================
# PARTIDOS EN VIVO
# ======================

def obtener_partidos():
    try:
        r = requests.get(URL_LIVE, headers=HEADERS, timeout=10)
        data = r.json()
        return data.get("response", [])
    except:
        return []

# ======================
# ESTADÍSTICAS
# ======================

def obtener_estadisticas(fixture):
    try:
        url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()

        tiros = tiros_puerta = corners = ataques = 0

        for team in data.get("response", []):
            for stat in team.get("statistics", []):

                valor = stat.get("value") or 0

                if isinstance(valor, str) and not valor.isdigit():
                    valor = 0

                valor = int(valor)

                if stat["type"] == "Total Shots":
                    tiros += valor
                elif stat["type"] == "Shots on Goal":
                    tiros_puerta += valor
                elif stat["type"] == "Corner Kicks":
                    corners += valor
                elif stat["type"] == "Dangerous Attacks":
                    ataques += valor

        return tiros, tiros_puerta, corners, ataques

    except:
        return 0, 0, 0, 0

# ======================
# ANALISIS
# ======================

async def analizar():

    print("Radar analizando...")

    partidos = obtener_partidos()
    candidatos = []

    for p in partidos:

        liga = p["league"]["id"]
        minuto = p["fixture"]["status"]["elapsed"]

        if liga not in LIGAS_GOLEADORAS:
            continue

        if minuto and 60 <= minuto <= 83:
            candidatos.append(p)

    for p in candidatos[:3]:

        fixture = p["fixture"]["id"]
        home = p["teams"]["home"]["name"]
        away = p["teams"]["away"]["name"]

        goles_home = p["goals"]["home"] or 0
        goles_away = p["goals"]["away"] or 0

        minuto = p["fixture"]["status"]["elapsed"]

        tiros, tiros_puerta, corners, ataques = obtener_estadisticas(fixture)

        diferencia = abs(goles_home - goles_away)

        if (
            tiros >= 11
            and tiros_puerta >= 5
            and corners >= 5
            and ataques >= 50
            and diferencia <= 1
        ):

            mensaje = f"""
🔥 ALERTA GOL DIAMANTE

{home} vs {away}
Minuto {minuto}

Marcador: {goles_home}-{goles_away}

Tiros: {tiros}
Tiros puerta: {tiros_puerta}
Corners: {corners}
Ataques peligrosos: {ataques}

🚨 Alta probabilidad de gol
"""

            await bot.send_message(chat_id=CHAT_ID, text=mensaje)

# ======================
# LOOP PRINCIPAL
# ======================

async def main():
    while True:
        try:
            await analizar()
        except Exception as e:
            print("Error:", e)

        await asyncio.sleep(300)

asyncio.run(main())