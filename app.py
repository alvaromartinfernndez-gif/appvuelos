import streamlit as st
import pandas as pd
import urllib.parse
import httpx
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y TEMA MINIMALISTA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="VAGABOND | Escapadas Baratas 'All-in-One'",
    page_icon="✈️",
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

    .escapada-card {{
        background-color: {card_bg} !important;
        border-radius: 12px;
        border: 1px solid {card_border};
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        transition: transform 0.2s ease;
    }}

    .escapada-card:hover {{
        transform: translateY(-2px);
        border-color: {alert_color};
    }}

    .badge-tag {{
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

    .total-price {{
        font-size: 2rem;
        font-weight: 700;
        color: {alert_color} !important;
    }}

    .action-btn {{
        display: block;
        width: 100%;
        text-align: center;
        background-color: {btn_bg} !important;
        color: {btn_text} !important;
        padding: 0.5rem 0.8rem;
        border-radius: 6px;
        text-decoration: none !important;
        font-weight: 600;
        font-size: 0.75rem;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-top: 0.5rem;
    }}

    .action-btn-sec {{
        display: block;
        width: 100%;
        text-align: center;
        background-color: transparent !important;
        color: {text_main} !important;
        border: 1px solid {card_border};
        padding: 0.5rem 0.8rem;
        border-radius: 6px;
        text-decoration: none !important;
        font-weight: 600;
        font-size: 0.75rem;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-top: 0.5rem;
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

    .pack-breakdown {{
        font-size: 0.85rem;
        color: {text_sub};
        margin-top: 0.5rem;
        margin-bottom: 1rem;
        line-height: 1.6;
    }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. MOTORES API (KLOOK ACTIVIDADES/ALOJAMIENTO & GOOGLE FLIGHTS)
# -----------------------------------------------------------------------------
def obtener_klook_datos(destino_nombre):
    """Consulta actividades y tours recomendados en tiempo real en Klook."""
    tp_token = st.secrets.get("TRAVELPAYOUTS_KEY", None)
    if not tp_token:
        return None
    
    try:
        url = "https://api.travelpayouts.com/v1/klook/search"
        headers = {"X-Access-Token": tp_token}
        params = {
            "query": f"actividades en {destino_nombre}",
            "currency": "EUR",
            "lang": "es_ES"
        }
        resp = httpx.get(url, headers=headers, params=params, timeout=6.0)
        data = resp.json()
        
        if "items" in data and len(data["items"]) > 0:
            top_item = data["items"][0]
            return {
                "actividad": top_item.get("title", f"Tour imprescindible por {destino_nombre}"),
                "precio": float(top_item.get("price", 25))
            }
    except Exception:
        pass
    return None

def obtener_vuelo_google_real(origen_code, destino_code):
    """Consulta la API de Google Flights mediante SerpApi."""
    serpapi_key = st.secrets.get("SERPAPI_KEY", None)
    if not serpapi_key:
        return None
    
    fecha_ida = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    fecha_vuelta = (datetime.now() + timedelta(days=16)).strftime("%Y-%m-%d")
    
    try:
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_flights",
            "departure_id": origen_code,
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

def generar_enlaces_escapada(tipo_transporte, origen_nombre, destino_nombre, nombre_actividad):
    """Genera las URLs dinámicas de reserva para Transporte, Alojamiento y Actividad Klook."""
    def simplificar(t):
        r = {'á':'a', 'é':'e', 'í':'i', 'ó':'o', 'ú':'u', 'ñ':'n'}
        t = t.lower()
        for k, v in r.items():
            t = t.replace(k, v)
        return t.strip().replace(" ", "-")

    origen_slug = simplificar(origen_nombre)
    destino_slug = simplificar(destino_nombre)
    
    fecha_ida = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    fecha_vuelta = (datetime.now() + timedelta(days=16)).strftime("%Y-%m-%d")

    # Enlace Transporte
    if "Avión" in tipo_transporte:
        query_vuelo = f"Vuelos de {origen_nombre} a {destino_nombre} del {fecha_ida} al {fecha_vuelta}"
        url_transporte = f"https://www.google.com/travel/flights?q={urllib.parse.quote(query_vuelo)}"
    elif "Tren" in tipo_transporte or "Autobús" in tipo_transporte:
        url_transporte = f"https://www.omio.es/viajes/{origen_slug}/{destino_slug}"
    else:
        url_transporte = f"https://www.blablacar.es/search?fn={urllib.parse.quote(origen_nombre)}&tn={urllib.parse.quote(destino_nombre)}"

    # Enlace Alojamiento Klook/Booking
    url_hotel = f"https://www.klook.com/es/hotels/search/?city={urllib.parse.quote(destino_nombre)}&checkIn={fecha_ida}&checkOut={fecha_vuelta}"

    # Enlace Actividades Klook
    url_klook_actividad = f"https://www.klook.com/es/search?query={urllib.parse.quote(destino_nombre)}"

    return url_transporte, url_hotel, url_klook_actividad

# -----------------------------------------------------------------------------
# 3. CATÁLOGO BASE DE ESCAPADAS COMPLETAS (Weekend Packs)
# -----------------------------------------------------------------------------
ORIGENES_DISPONIBLES = {
    "Madrid": "MAD",
    "Barcelona": "BCN",
    "Valencia": "VLC",
    "Málaga": "AGP",
    "Sevilla": "SVQ",
    "Bilbao": "BIO"
}

ESCAPADAS_CATALOGO = [
    {
        "destino": "Valencia", "pais": "España", "transporte": "Tren Alta Velocidad", "code": "VLC",
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 35, "actividad_defecto": "Entrada Hemisfèric + Oceanogràfic",
        "precio_actividad_defecto": 28, "precio_transporte_base": 19
    },
    {
        "destino": "Roma", "pais": "Italia", "transporte": "Avión Directo", "code": "FCO",
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 45, "actividad_defecto": "Visita Guiada Coliseo y Foro Romano",
        "precio_actividad_defecto": 35, "precio_transporte_base": 38
    },
    {
        "destino": "París", "pais": "Francia", "transporte": "Autobús Larga Distancia", "code": "PAR",
        "duracion": "4 Días / 3 Noches", "hotel_estimado_noche": 50, "actividad_defecto": "Crucero por el Sena al Atardecer",
        "precio_actividad_defecto": 18, "precio_transporte_base": 39
    },
    {
        "destino": "Oporto", "pais": "Portugal", "transporte": "Autobús Nocturno", "code": "OPO",
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 30, "actividad_defecto": "Catamarán por el Duero + Catas de Vino",
        "precio_actividad_defecto": 22, "precio_transporte_base": 29
    },
    {
        "destino": "Londres", "pais": "Reino Unido", "transporte": "Avión Directo", "code": "STN",
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 55, "actividad_defecto": "Entrada Combinada London Eye + Tour",
        "precio_actividad_defecto": 38, "precio_transporte_base": 32
    }
]

# -----------------------------------------------------------------------------
# 4. BARRA LATERAL (ORIGEN Y PRESUPUESTO DEL PACK COMPLETO)
# -----------------------------------------------------------------------------
st.sidebar.markdown("### ORIGEN DE LA ESCAPADA")
origen_seleccionado = st.sidebar.selectbox("Ciudad de Salida", list(ORIGENES_DISPONIBLES.keys()), index=0)
codigo_origen_actual = ORIGENES_DISPONIBLES[origen_seleccionado]

st.sidebar.markdown("---")
presupuesto_total_pack = st.sidebar.slider("Presupuesto MÁXIMO Pack Completo (€)", 50, 600, 200, step=10)

st.sidebar.markdown("---")
filtro_transporte = st.sidebar.multiselect(
    "Medios de Transporte Permitidos:",
    ["Avión", "Tren", "Autobús"],
    default=["Avión", "Tren", "Autobús"]
)

# -----------------------------------------------------------------------------
# 5. RENDERIZADO PRINCIPAL (ESCAPADAS TODO INCLUIDO)
# -----------------------------------------------------------------------------
st.markdown('<div class="brand-header">V A G A B O N D</div>', unsafe_allow_html=True)
st.markdown(f'<div class="brand-sub">Radar de Escapadas Baratas con <b>Todo Incluido (Viaje + Hotel + Actividad Klook)</b> desde {origen_seleccionado}</div>', unsafe_allow_html=True)

serp_activa = "SERPAPI_KEY" in st.secrets
klook_activa = "TRAVELPAYOUTS_KEY" in st.secrets

if serp_activa or klook_activa:
    st.markdown('<div class="status-live"><div class="pulse-dot"></div> Conexión activa con Klook API + Google Flights</div>', unsafe_allow_html=True)

st.write("")
st.markdown(f"### 🧳 Escapadas Disponibles desde {origen_seleccionado}")

escapadas_filtradas = []

for item in ESCAPADAS_CATALOGO:
    if item["destino"].lower() == origen_seleccionado.lower():
        continue
        
    if not any(t in item["transporte"] for t in filtro_transporte):
        continue

    # 1. Calcular Transporte
    precio_transporte = item["precio_transporte_base"]
    if "Avión" in item["transporte"] and serp_activa:
        p_vuelo = obtener_vuelo_google_real(codigo_origen_actual, item["code"])
        if p_vuelo:
            precio_transporte = p_vuelo

    # 2. Calcular Actividad Klook
    nombre_actividad = item["actividad_defecto"]
    precio_actividad = item["precio_actividad_defecto"]
    if klook_activa:
        datos_klook = obtener_klook_datos(item["destino"])
        if datos_klook:
            nombre_actividad = datos_klook["actividad"]
            precio_actividad = datos_klook["precio"]

    # 3. Calcular Alojamiento (2 Noches Estándar)
    noches = 2
    precio_alojamiento_total = item["hotel_estimado_noche"] * noches

    # 4. PRECIO TOTAL PACK
    precio_total_pack = int(precio_transporte + precio_alojamiento_total + precio_actividad)

    if precio_total_pack <= presupuesto_total_pack:
        url_trans, url_hotel, url_act = generar_enlaces_escapada(
            item["transporte"], origen_seleccionado, item["destino"], nombre_actividad
        )

        escapadas_filtradas.append({
            "destino": item["destino"],
            "pais": item["pais"],
            "duracion": item["duracion"],
            "transporte": item["transporte"],
            "precio_transporte": int(precio_transporte),
            "precio_alojamiento": int(precio_alojamiento_total),
            "actividad_nombre": nombre_actividad,
            "precio_actividad": int(precio_actividad),
            "precio_total": precio_total_pack,
            "url_transporte": url_trans,
            "url_hotel": url_hotel,
            "url_actividad": url_act
        })

if escapadas_filtradas:
    cols = st.columns(2)
    for idx, pack in enumerate(escapadas_filtradas):
        col = cols[idx % 2]
        with col:
            st.markdown(f"""
            <div class="escapada-card">
                <div class="badge-tag">{pack['duracion']} • {pack['transporte']}</div>
                <h3 style="margin: 0; font-family: 'Cinzel', serif;">{pack['destino']} ({pack['pais']})</h3>
                
                <div style="margin-top: 10px;">
                    <span class="total-price">{pack['precio_total']} €</span>
                    <span style="font-size: 0.8rem; color: {text_sub};"> / pack completo estimado</span>
                </div>

                <div class="pack-breakdown">
                    🚆 <b>Viaje (Ida/Vuelta):</b> {pack['precio_transporte']} €<br>
                    🏨 <b>Hotel (2 noches):</b> {pack['precio_alojamiento']} €<br>
                    🎟️ <b>Klook Exp:</b> {pack['actividad_nombre']} ({pack['precio_actividad']} €)
                </div>

                <a href="{pack['url_transporte']}" target="_blank" class="action-btn">1. Reservar Transporte ({pack['precio_transporte']}€)</a>
                <a href="{pack['url_hotel']}" target="_blank" class="action-btn-sec">2. Ver Alojamiento ({pack['precio_alojamiento']}€)</a>
                <a href="{pack['url_actividad']}" target="_blank" class="action-btn-sec">3. Reservar Experiencia Klook ({pack['precio_actividad']}€)</a>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info(f"No hay escapadas completas disponibles desde {origen_seleccionado} por debajo de {presupuesto_total_pack}€. Aumenta el presupuesto máximo en la barra lateral.")
