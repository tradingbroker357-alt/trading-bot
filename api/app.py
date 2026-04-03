
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import pandas as pd
import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

app = FastAPI()

# =========================
# LEER PREDICCIONES
# =========================
def leer_predicciones(n=50):
    ruta = "predictions.csv"
    if not os.path.exists(ruta):
        return []
    df = pd.read_csv(ruta)
    return df.tail(n).to_dict(orient="records")

# =========================
# ENVIAR ALERTA TELEGRAM
# =========================
async def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url  = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "HTML"}
    async with httpx.AsyncClient() as client:
        await client.post(url, data=data)

# =========================
# DASHBOARD HTML
# =========================
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    predicciones = leer_predicciones()
    filas = ""
    for p in reversed(predicciones):
        color = "#2ecc71" if "SUBE" in str(p.get("direccion", "")) else "#e74c3c"
        filas += f"""
        <tr>
            <td>{p.get('hora', '')}</td>
            <td><b>{p.get('activo', '')}</b></td>
            <td>{p.get('ultimo_close', '')}</td>
            <td>{p.get('prediccion', '')}</td>
            <td style='color:{color};font-weight:bold'>{p.get('direccion', '')}</td>
        </tr>"""

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Trading Bot</title>
        <meta http-equiv='refresh' content='30'>
        <style>
            body {{ font-family: monospace; background: #0d1117; color: #c9d1d9; padding: 20px; }}
            h1   {{ color: #58a6ff; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th   {{ background: #161b22; color: #58a6ff; padding: 10px; text-align: left; }}
            td   {{ padding: 8px 10px; border-bottom: 1px solid #21262d; }}
            tr:hover {{ background: #161b22; }}
        </style>
    </head>
    <body>
        <h1>🤖 Trading Bot — Predicciones en vivo</h1>
        <p>Actualiza cada 30 segundos</p>
        <table>
            <tr>
                <th>Hora</th>
                <th>Activo</th>
                <th>Close actual</th>
                <th>Predicción</th>
                <th>Dirección</th>
            </tr>
            {filas}
        </table>
    </body>
    </html>
    """
    return html

# =========================
# ENDPOINT PREDICCIONES JSON
# =========================
@app.get("/predicciones")
async def get_predicciones():
    return leer_predicciones()

# =========================
# ALERTAS AUTOMATICAS
# =========================
@app.on_event("startup")
async def iniciar_alertas():
    asyncio.create_task(loop_alertas())

async def loop_alertas():
    enviadas = set()
    while True:
        predicciones = leer_predicciones(9)
        for p in predicciones:
            clave = f"{p.get('activo')}_{p.get('hora')}"
            if clave not in enviadas:
                msg = (
                    f"🤖 <b>{p.get('activo')}</b>\n"
                    f"🕐 {p.get('hora')}\n"
                    f"📈 Close actual: {p.get('ultimo_close')}\n"
                    f"🎯 Predicción:   {p.get('prediccion')}\n"
                    f"{'🟢' if 'SUBE' in str(p.get('direccion','')) else '🔴'} {p.get('direccion')}"
                )
                await enviar_telegram(msg)
                enviadas.add(clave)
        await asyncio.sleep(60)
