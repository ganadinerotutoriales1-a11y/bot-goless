import requests
import asyncio
import os
from telegram import Bot

# ======================
# CONFIG
# ======================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))
API_KEY = os.getenv("API_KEY")

bot = Bot(token=BOT_TOKEN)

HEADERS = {
    "x-apisports-key": API_KEY
}

URL_LIVE = "https://v3.football.api-sports.io/fixtures?live=all"

# Ligas top (goles)
LIGAS_GOLEADORAS = [39, 140, 135, 78, 61, 88]

# Control
alertados = set()
historial_stats = {}

# ======================
# PARTIDOS
# ======================

def obtener_partidos():
    try:
        r = requests.get(URL_LIVE, headers=HEADERS, timeout=10)
        data = r.json()
        return data.get("response", [])
    except:
        return []

# ======================
# STATS
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
# CALCULO INTELIGENTE
# ======================

def calcular_presion(fixture, tiros, tiros_puerta, corners, ataques):
    clave = str(fixture)

    anterior = historial_stats.get(clave)

    score = 0

    # Presión actual
    if tiros >= 12:
        score += 2
    if tiros_puerta >= 5:
        score += 2
    if corners >= 4:
        score += 1
    if ataques >= 55:
        score += 2

    # Tendencia (subida)
    if anterior:
        if tiros > anterior[0]:
            score += 1
        if ataques > anterior[3]:
            score += 1

    # Guardar historial
    historial_stats[clave] = (tiros, tiros_puerta, corners, ataques)

    return score

# ======================
# ANALISIS ELITE
# ======================

async def analizar():

    print("🧠 Analizando ELITE...")

    partidos = obtener_partidos()

    for p in partidos:

        liga = p["league"]["id"]
        minuto = p["fixture"]["status"]["elapsed"]

        if liga not in LIGAS_GOLEADORAS:
            continue

        # SOLO MINUTOS PRO
        if not (minuto and 59 <= minuto <= 81):
            continue

        fixture = p["fixture"]["id"]

        if fixture in alertados:
            continue

        home = p["teams"]["home"]["name"]
        away = p["teams"]["away"]["name"]

        goles_home = p["goals"]["home"] or 0
        goles_away = p["goals"]["away"] or 0

        diferencia = abs(goles_home - goles_away)

        tiros, tiros_puerta, corners, ataques = obtener_estadisticas(fixture)

        # Score inteligente
        score = calcular_presion(fixture, tiros, tiros_puerta, corners, ataques)

        # FILTRO FINAL ELITE
        if score >= 6 and diferencia <= 1:

            mensaje = f"""
🔥 ALERTA ELITE (GOL PROBABLE)

{home} vs {away}
Minuto {minuto}

Marcador: {goles_home}-{goles_away}

📊 Presión:
- Tiros: {tiros}
- A puerta: {tiros_puerta}
- Corners: {corners}
- Ataques: {ataques}

🧠 Score: {score}/10
📈 Tendencia: EN SUBIDA

⚡ POSIBLE GOL EN BREVE
"""

            await bot.send_message(chat_id=CHAT_ID, text=mensaje)

            alertados.add(fixture)

# ======================
# LOOP
# ======================

async def main():
    while True:
        try:
            await analizar()
        except Exception as e:
            print("Error:", e)

        # 🔥 ULTRA OPTIMIZADO (menos consumo API)
        await asyncio.sleep(240)

asyncio.run(main())