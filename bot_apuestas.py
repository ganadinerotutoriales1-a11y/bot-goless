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

# Ligas más goleadoras
LIGAS_GOLEADORAS = [39, 140, 135, 78, 61, 88]

# Control para no repetir alertas
alertados = set()

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
# ANALISIS PRO
# ======================

async def analizar():

    print("🔎 Analizando partidos...")

    partidos = obtener_partidos()

    for p in partidos:

        liga = p["league"]["id"]
        minuto = p["fixture"]["status"]["elapsed"]

        if liga not in LIGAS_GOLEADORAS:
            continue

        # 🔥 SOLO MINUTOS PRO
        if not (minuto and 59 <= minuto <= 81):
            continue

        fixture = p["fixture"]["id"]

        # ❌ Evitar repetir alertas
        if fixture in alertados:
            continue

        home = p["teams"]["home"]["name"]
        away = p["teams"]["away"]["name"]

        goles_home = p["goals"]["home"] or 0
        goles_away = p["goals"]["away"] or 0

        tiros, tiros_puerta, corners, ataques = obtener_estadisticas(fixture)

        diferencia = abs(goles_home - goles_away)

        # 🔥 FILTRO PRO (más preciso)
        if (
            tiros >= 12
            and tiros_puerta >= 5
            and corners >= 4
            and ataques >= 55
            and diferencia <= 1
        ):

            mensaje = f"""
🔥 ALERTA GOL PRO

{home} vs {away}
Minuto {minuto}

Marcador: {goles_home}-{goles_away}

📊 Datos:
- Tiros: {tiros}
- Tiros puerta: {tiros_puerta}
- Corners: {corners}
- Ataques peligrosos: {ataques}

🚨 PRESIÓN ALTA → POSIBLE GOL
"""

            await bot.send_message(chat_id=CHAT_ID, text=mensaje)

            # Guardar como ya alertado
            alertados.add(fixture)

# ======================
# LOOP PRINCIPAL
# ======================

async def main():
    while True:
        try:
            await analizar()
        except Exception as e:
            print("Error:", e)

        # ⏱️ Optimizado (menos consumo API)
        await asyncio.sleep(240)

asyncio.run(main())