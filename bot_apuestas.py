import requests
import asyncio
from telegram import Bot

# ======================
# CONFIG
# ======================

BOT_TOKEN = os.getenv("8604694183:AAHUD6HzThdqv4stBwVEPeMz")
CHAT_ID = os.getenv("8649081602")
API_KEY = os.getenv("2092fe315fdefbc8cd7f65767ba2ce26")

bot = Bot(token=BOT_TOKEN)

HEADERS = {
    "x-apisports-key": API_KEY
}

URL_LIVE = "https://v3.football.api-sports.io/fixtures?live=all"

# ligas con más goles
LIGAS_GOLEADORAS = [39,140,135,78,61,88]

# ======================
# PARTIDOS EN VIVO
# ======================

def obtener_partidos():

    r = requests.get(URL_LIVE, headers=HEADERS)
    data = r.json()

    if "response" not in data:
        return []

    return data["response"]

# ======================
# ESTADÍSTICAS
# ======================

def obtener_estadisticas(fixture):

    url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture}"

    r = requests.get(url, headers=HEADERS)

    data = r.json()

    tiros = 0
    tiros_puerta = 0
    corners = 0
    ataques = 0

    if "response" not in data:
        return tiros, tiros_puerta, corners, ataques

    for team in data["response"]:

        for stat in team["statistics"]:

            if stat["type"] == "Total Shots":
                tiros += int(stat["value"] or 0)

            if stat["type"] == "Shots on Goal":
                tiros_puerta += int(stat["value"] or 0)

            if stat["type"] == "Corner Kicks":
                corners += int(stat["value"] or 0)

            if stat["type"] == "Dangerous Attacks":
                ataques += int(stat["value"] or 0)

    return tiros, tiros_puerta, corners, ataques

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

    candidatos = candidatos[:3]

    for p in candidatos:

        fixture = p["fixture"]["id"]

        home = p["teams"]["home"]["name"]
        away = p["teams"]["away"]["name"]

        goles_home = p["goals"]["home"]
        goles_away = p["goals"]["away"]

        minuto = p["fixture"]["status"]["elapsed"]

        tiros, tiros_puerta, corners, ataques = obtener_estadisticas(fixture)

        diferencia = abs((goles_home or 0) - (goles_away or 0))

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

Marcador
{goles_home}-{goles_away}

Tiros: {tiros}
Tiros puerta: {tiros_puerta}
Corners: {corners}
Ataques peligrosos: {ataques}

Probabilidad alta de gol
"""

            await bot.send_message(chat_id=CHAT_ID, text=mensaje)

# ======================
# LOOP
# ======================

async def main():

    while True:
    bot.send_message(chat_id=CHAT_ID, text="🔥 PRUEBA DIRECTA BOT ACTIVO")
        try:

            await analizar()

        except Exception as e:

            print("Error:", e)

        await asyncio.sleep(300)

asyncio.run(main())