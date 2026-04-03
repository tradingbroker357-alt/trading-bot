
from iqoptionapi.stable_api import IQ_Option
import pandas as pd
import time
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

EMAIL    = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

ACTIVOS = [
    "AUDCAD-OTC",
    "EURGBP-OTC",
    "EURJPY-OTC",
    "EURUSD-OTC",
    "GBPJPY-OTC",
    "GBPUSD-OTC",
    "NZDUSD-OTC",
    "USDCHF-OTC",
    "USDJPY-OTC"
]

VELAS_INICIALES = 100
VELAS_NUEVAS    = 5
INTERVALO       = 60  # segundos (velas de 1 minuto)
DATA_DIR        = "data"

os.makedirs(DATA_DIR, exist_ok=True)

# =========================
# CONECTAR
# =========================
def conectar():
    print("🔄 Conectando a IQ Option...")
    iq = IQ_Option(EMAIL, PASSWORD)
    iq.connect()
    if not iq.check_connect():
        print("❌ Error de conexión")
        exit()
    print("✅ Conectado")
    return iq

# =========================
# GUARDAR VELAS SIN MEZCLAR
# =========================
def guardar_velas(activo, velas_nuevas):
    ruta = os.path.join(DATA_DIR, f"{activo}.csv")

    df_nuevo = pd.DataFrame(velas_nuevas)
    df_nuevo = df_nuevo.sort_values("from")
    df_nuevo = df_nuevo[["from", "open", "max", "min", "close"]]
    df_nuevo.columns = ["timestamp", "open", "high", "low", "close"]

    if os.path.exists(ruta):
        df_existente = pd.read_csv(ruta)
        df_total = pd.concat([df_existente, df_nuevo])
        # elimina duplicados por timestamp
        df_total = df_total.drop_duplicates(subset="timestamp")
        df_total = df_total.sort_values("timestamp")
    else:
        df_total = df_nuevo

    df_total.to_csv(ruta, index=False)
    return len(df_total)

# =========================
# DESCARGA INICIAL
# =========================
def descarga_inicial(iq):
    print("\n📥 Descarga inicial (100 velas por activo)...\n")
    for activo in ACTIVOS:
        try:
            velas = iq.get_candles(activo, INTERVALO, VELAS_INICIALES, time.time())
            total = guardar_velas(activo, velas)
            print(f"💾 {activo} — {total} velas guardadas")
        except Exception as e:
            print(f"⚠️ Error en {activo}: {e}")

# =========================
# ESPERAR CIERRE DE VELA
# =========================
def esperar_cierre():
    while True:
        ahora = datetime.now()
        if ahora.second == 0:
            print(f"\n⏰ Cierre detectado: {ahora.strftime('%H:%M:%S')}")
            return
        time.sleep(0.2)

# =========================
# LOOP PRINCIPAL
# =========================
def loop_continuo(iq):
    print("\n🔁 Iniciando loop continuo...\n")
    while True:
        esperar_cierre()
        for activo in ACTIVOS:
            try:
                velas = iq.get_ca
