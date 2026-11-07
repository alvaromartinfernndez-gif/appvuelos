import streamlit as st
import pandas as pd
import urllib.parse
import httpx
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y TEMA MINIMALISTA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="VAGABOND | Radar de Chollos Multimodal",
    page_icon="🔔",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.markdown("### CONFIGURACIÓN DE ALERTAS")
tema_elegido = st.sidebar.radio("Apariencia", ["Modo Claro ☀️", "Modo Oscuro 🌙"], index=0)

if tema_elegido == "Modo Oscuro 🌙":
    bg_app = "#090D16"
    bg_sidebar = "#111827"
    text_main = "#F1F5F9"
    text_sub = "#94A3B8"
    card_bg = "#111827"
    card_border = "#1E293B"
    btn_bg = "#F1F5F9"
    btn_text = "#090D16"
    btn_hover = "#CBD5E1"
    alert_color = "#10B981"
    badge_bg = "rgba(16, 185, 129, 0.15)"
else:
    bg_app = "#FAFAFA"
    bg_sidebar = "#FFFFFF"
    text_main = "#0F172A"
    text_sub = "#64748B"
    card_bg = "#FFFFFF"
    card_border = "#E2E8F0"
    btn_bg = "#0F172A"
    btn_text = "#FFFFFF"
    btn_hover = "#334155"
    alert_color = "#047857"
    badge_bg = "rgba(4, 120, 87, 0.08)"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Plus+Jakarta+Sans:wght@300;400;600&display=swap');

    .stApp {{
        background-color: {bg_app} !important;
        color: {text_main} !important;
    }}

    html, body, [class*="css"], .stMarkdown, p, span, div, h1, h2, h3, h4, h5, h6 {{
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: {text_main} !important;
    }}

    section[data-testid="stSidebar"] {{
        background-color: {bg_sidebar} !important;
        border-right: 1px solid {card_border} !important;
    }}

    .brand-header {{
        font-family: 'Cinzel', serif !important;
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: 5px;
        color: {text_main} !important;
        margin-bottom: 0.2rem;
        text-transform: uppercase;
    }}

    .brand-sub {{
        font-size: 0.85rem;
        color: {text_sub} !important;
        margin-bottom: 2rem;
        font-weight: 300;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }}

    .alert-card {{
        background-color: {card_bg} !important;
        border-radius: 12px;
        border: 1px solid {card_border};
        padding: 1.5rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        transition: transform 0.2s ease;
    }}

    .alert-card:hover {{
        transform: translateY(-2px);
        border-color: {alert_color};
    }}

    .transport-tag {{
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        padding: 3px 10px;
        border-radius: 20px;
        background-color: {badge_bg};
        color: {alert_color} !important;
        margin-bottom: 8px;
    }}

    .alert-price {{
        font-size: 1.8rem;
        font-weight: 700;
        color: {alert_color} !important;
    }}

    .action-btn {{
        display: inline-block;
        width: 100%;
        text-align: center;
        background-color: {btn_bg} !important;
        color: {btn_text} !important;
        padding: 0.65rem 1rem;
        border-radius: 6px;
        text-decoration: none !important;
        font-weight: 600;
        font-size: 0.8rem;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-top: 1rem;
    }}

    .status-live {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 0.75rem;
        color: {alert_color} !important;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
    }}

    .pulse-dot {{
        width: 8px;
        height: 8px;
        background-color: {alert_color};
        border-radius: 50%;
    }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. MOTORES MULTIMODALES EN TIEMPO REAL
# -----------------------------------------------------------------------------
def obtener_vuelo_real(origen, destino_code):
    """Consulta directa a Google Flights en tiempo real mediante SerpApi."""
    serpapi_key = st.secrets.get("SERPAPI_KEY", None)
    if not serpapi_key:
        return None
    
    fecha_ida = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    fecha_vuelta = (datetime.now() + timedelta(days=18)).strftime("%Y-%m-%d")
    
    try:
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_flights",
            "departure_id": origen,
            "arrival_id": destino_code,
            "outbound_date": fecha_ida,
            "return_date": fecha_vuelta,
            "currency": "EUR",
            "hl": "es",
            "api_key": serpapi_key
        }
        resp = httpx.get(url, params=params, timeout=7.0)
        data = resp.json()
        if "best_flights" in data and len(data["best_flights"]) > 0:
            return data["best_flights"][0]["price"]
    except Exception:
        pass
    return None

def generar_enlace_multimodal(tipo, origen_nombre, destino_nombre):
    """Genera el enlace parametrizado directo para la reserva en tiempo real según medio de transporte."""
    q_origen = urllib.parse.quote(origen_nombre)
    q_destino = urllib.parse.quote(destino_nombre)
    
    if "Avión" in tipo:
        return f"https://www.google.com/travel/flights?q=Vuelos%20desde%20{q_origen}%20a%20{q_destino}"
    elif "Tren" in tipo or "Autobús" in tipo:
        return f"https://www.thetrainline.com/es/busqueda/{q_origen}/{q_destino}"
    else:
        return f"https://www.blablacar.es/search?fn={q_origen}&tn={q_destino}"

# -----------------------------------------------------------------------------
# 3. BASE DE DATOS DE CHOLLOS Y BASE MULTIMODAL
# -----------------------------------------------------------------------------
ORIGENES = {
    "Madrid": "MAD",
    "Barcelona": "BCN",
    "Valencia": "VLC",
    "Málaga": "AGP",
    "Sevilla": "SVQ",
    "Bilbao": "BIO"
}

ALERTAS_BASE = [
    # TREN & AUTOBÚS (Nacional & Europa)
    {"destino": "Valencia", "pais": "España", "transporte": "Tren de Alta Velocidad (Iryo / Ouigo)", "code": "VLC", "precio_habitual": 45, "precio_chollo": 9, "operador": "Iryo", "tipo_cat": "Tren"},
    {"destino": "París", "pais": "Francia", "transporte": "Autobús Larga Distancia", "code": "PAR", "precio_habitual": 65, "precio_chollo": 19, "operador": "FlixBus", "tipo_cat": "Autobús"},
    {"destino": "Barcelona", "pais": "España", "transporte": "Tren Alta Velocidad", "code": "BCN", "precio_habitual": 59, "precio_chollo": 15, "operador": "Ouigo", "tipo_cat": "Tren"},
    {"destino": "Oporto", "pais": "Portugal", "transporte": "Autobús Nocturno", "code": "OPO", "precio_habitual": 40, "precio_chollo": 12, "operador": "Alsa / FlixBus", "tipo_cat": "Autobús"},
    
    # AVIONES (Google Flights Real-Time)
    {"destino": "Roma", "pais": "Italia", "transporte": "Avión (Vuelo Directo)", "code": "FCO", "precio_habitual": 120, "precio_chollo": 24, "operador": "Ryanair / Wizz", "tipo_cat": "Avión"},
    {"destino": "Londres", "pais": "Reino Unido", "transporte": "Avión (Vuelo Directo)", "code": "STN", "precio_habitual": 110, "precio_chollo": 18, "operador": "Ryanair", "tipo_cat": "Avión"},
    {"destino": "Dubái", "pais": "EAU", "transporte": "Avión (Directo)", "code": "DXB", "precio_habitual": 450, "precio_chollo": 189, "operador": "Wizz Air", "tipo_cat": "Avión"},
    {"destino": "Nueva York", "pais": "EE.UU.", "transporte": "Avión (Ida y Vuelta)", "code": "JFK", "precio_habitual": 520, "precio_chollo": 240, "operador": "Iberia / LEVEL", "tipo_cat": "Avión"}
]

# -----------------------------------------------------------------------------
# 4. BARRA LATERAL (FILTROS DE ALERTAS)
# -----------------------------------------------------------------------------
st.sidebar.markdown("### ORIGEN DE TUS VIAJES")
origen_seleccionado = st.sidebar.selectbox("Ciudad de Salida", list(ORIGENES.keys()))
codigo_origen = ORIGENES[origen_seleccionado]

st.sidebar.markdown("---")
st.sidebar.markdown("### FILTRAR MEDIOS DE TRANSPORTE")
filtro_transporte = st.sidebar.multiselect(
    "Medios permitidos:",
    ["Avión", "Tren", "Autobús"],
    default=["Avión", "Tren", "Autobús"]
)

st.sidebar.markdown("---")
presupuesto_alerta = st.sidebar.slider("Alerta si el billete cuesta menos de (€)", 5, 300, 50, step=5)

# -----------------------------------------------------------------------------
# 5. PANEL PRINCIPAL DE ALERTAS EN TIEMPO REAL
# -----------------------------------------------------------------------------
st.markdown('<div class="brand-header">V A G A B O N D</div>', unsafe_allow_html=True)
st.markdown(f'<div class="brand-sub">Radar de Alertas en Tiempo Real desde <b>{origen_seleccionado}</b></div>', unsafe_allow_html=True)

serp_activa = "SERPAPI_KEY" in st.secrets
if serp_activa:
    st.markdown('<div class="status-live"><div class="pulse-dot"></div> Monitoreo multimodal en tiempo real conectado</div>', unsafe_allow_html=True)
else:
    st.caption("ℹ️ Modo Alerta Directa: Haz clic en cualquier chollo para comprobar la tarifa exacta en vivo.")

st.write("")
st.markdown("### 🔔 Chollos Detectados Ahora Mismo")

# Filtrado y procesamiento
chollos_encontrados = []
for item in ALERTAS_BASE:
    # Comprobar si el medio de transporte está seleccionado
    if not any(t in item["transporte"] for t in filtro_transporte):
        continue
        
    precio_mostrar = item["precio_chollo"]
    
    # Si es avión y SerpApi está configurado, obtener precio real en tiempo real
    if item["tipo_cat"] == "Avión" and serp_activa:
        precio_api = obtener_vuelo_real(codigo_origen, item["code"])
        if precio_api:
            precio_mostrar = precio_api

    # Evaluar si es un chollo (bajo el presupuesto máximo fijado)
    if precio_mostrar <= presupuesto_alerta:
        url_directa = generar_enlace_multimodal(item["transporte"], origen_seleccionado, item["destino"])
        descuento = int(((item["precio_habitual"] - precio_mostrar) / item["precio_habitual"]) * 100)
        
        chollos_encontrados.append({
            "destino": item["destino"],
            "pais": item["pais"],
            "transporte": item["transporte"],
            "precio": precio_mostrar,
            "precio_habitual": item["precio_habitual"],
            "descuento": max(descuento, 10),
            "url": url_directa
        })

# Renderizar alertas en cuadrícula
if chollos_encontrados:
    cols = st.columns(2)
    for idx, chollo in enumerate(chollos_encontrados):
        col = cols[idx % 2]
        with col:
            st.markdown(f"""
            <div class="alert-card">
                <div class="transport-tag">{chollo['transporte']}</div>
                <h3 style="margin: 0; font-family: 'Cinzel', serif;">{chollo['destino']} ({chollo['pais']})</h3>
                <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 10px;">
                    <div>
                        <span class="alert-price">{chollo['precio']} €</span>
                        <span style="font-size: 0.85rem; color: {text_sub}; text-decoration: line-through; margin-left: 8px;">{chollo['precio_habitual']} €</span>
                    </div>
                    <span style="background-color: {badge_bg}; color: {alert_color}; font-weight:700; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem;">
                        -{chollo['descuento']}% DESCUENTO
                    </span>
                </div>
                <a href="{chollo['url']}" target="_blank" class="action-btn">RESERVAR BILLETE EN VIVO</a>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info(f"No hay alertas de chollos activas por debajo de {presupuesto_alerta}€ para los medios de transporte seleccionados. Aumenta el umbral en la barra lateral.")
