import streamlit as st
import pandas as pd
import urllib.parse
import httpx
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y TEMA DINÁMICO BLINDADO
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="VAGABOND | Radar de Escapadas Baratas",
    page_icon="🧳",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.markdown("### CONFIGURACIÓN DE ALERTAS")
tema_elegido = st.sidebar.radio("Apariencia", ["Modo Claro ☀️", "Modo Oscuro 🌙"], index=0)

# Inyección de estilos globales forzados según la opción elegida
if tema_elegido == "Modo Oscuro 🌙":
    bg_app = "#090D16"
    bg_sidebar = "#111827"
    text_color = "#F1F5F9"
    sub_color = "#94A3B8"
    card_bg = "#111827"
    card_border = "#1E293B"
    metric_bg = "#1E293B"
else:
    bg_app = "#FAFAFA"
    bg_sidebar = "#FFFFFF"
    text_color = "#0F172A"
    sub_color = "#64748B"
    card_bg = "#FFFFFF"
    card_border = "#E2E8F0"
    metric_bg = "#F1F5F9"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');

    /* Forzar fondo global y texto */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background-color: {bg_app} !important;
        color: {text_color} !important;
    }}

    /* Forzar fondo de la barra lateral */
    section[data-testid="stSidebar"], [data-testid="stSidebarContent"] {{
        background-color: {bg_sidebar} !important;
        border-right: 1px solid {card_border} !important;
    }}

    /* Ajuste de todos los textos generales */
    p, span, div, label, h1, h2, h3, h4, h5, h6, .stMarkdown {{
        color: {text_color} !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }}

    /* Títulos */
    .brand-title {{
        font-family: 'Cinzel', serif !important;
        font-size: 2.3rem;
        font-weight: 700;
        letter-spacing: 4px;
        color: {text_color} !important;
        margin-bottom: 0.1rem;
    }}
    .brand-subtitle {{
        font-size: 0.9rem;
        color: {sub_color} !important;
        margin-bottom: 1.5rem;
    }}

    /* Forzar tarjetas y contenedores nativos */
    [data-testid="stVerticalBlockBorderWrapper"] > div {{
        background-color: {card_bg} !important;
        border: 1px solid {card_border} !important;
        border-radius: 12px !important;
    }}

    /* Botones de acción */
    .stButton>button, a[data-testid="stLinkButton"] {{
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
    }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. MOTOR DE ALGORITMO Y BÚSQUEDA DE CHOLLOS EN TIEMPO REAL
# -----------------------------------------------------------------------------
def obtener_chollos_klook(destino_nombre):
    """Escanea múltiples actividades en Klook y selecciona la opción de menor precio."""
    tp_token = st.secrets.get("TRAVELPAYOUTS_KEY", None)
    if not tp_token:
        return None
    
    try:
        url = "https://api.travelpayouts.com/v1/klook/search"
        headers = {"X-Access-Token": tp_token}
        params = {
            "query": f"actividades {destino_nombre}",
            "currency": "EUR",
            "lang": "es_ES"
        }
        resp = httpx.get(url, headers=headers, params=params, timeout=6.0)
        data = resp.json()
        
        if "items" in data and len(data["items"]) > 0:
            items_validos = [i for i in data["items"] if "price" in i and float(i["price"]) > 0]
            if items_validos:
                item_chollo = min(items_validos, key=lambda x: float(x["price"]))
                return {
                    "actividad": item_chollo.get("title", f"Experiencia Top en {destino_nombre}"),
                    "precio": float(item_chollo.get("price"))
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

def generar_enlaces_escapada(tipo_transporte, origen_nombre, destino_nombre):
    """Genera URLs dinámicas directas."""
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

    if "Avión" in tipo_transporte:
        query_vuelo = f"Vuelos de {origen_nombre} a {destino_nombre} del {fecha_ida} al {fecha_vuelta}"
        url_trans = f"https://www.google.com/travel/flights?q={urllib.parse.quote(query_vuelo)}"
    elif "Tren" in tipo_transporte or "Autobús" in tipo_transporte:
        url_trans = f"https://www.omio.es/viajes/{origen_slug}/{destino_slug}"
    else:
        url_trans = f"https://www.blablacar.es/search?fn={urllib.parse.quote(origen_nombre)}&tn={urllib.parse.quote(destino_nombre)}"

    url_hotel = f"https://www.klook.com/es/hotels/search/?city={urllib.parse.quote(destino_nombre)}&checkIn={fecha_ida}&checkOut={fecha_vuelta}"
    url_actividad = f"https://www.klook.com/es/search?query={urllib.parse.quote(destino_nombre)}"

    return url_trans, url_hotel, url_actividad

# -----------------------------------------------------------------------------
# 3. BASE DE DATOS DE DESTINOS PARA ESCAPADAS
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
        "precio_actividad_defecto": 24, "precio_transporte_base": 19
    },
    {
        "destino": "Roma", "pais": "Italia", "transporte": "Avión Directo", "code": "FCO",
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 40, "actividad_defecto": "Visita Guiada Coliseo y Foro Romano",
        "precio_actividad_defecto": 30, "precio_transporte_base": 38
    },
    {
        "destino": "París", "pais": "Francia", "transporte": "Autobús Larga Distancia", "code": "PAR",
        "duracion": "4 Días / 3 Noches", "hotel_estimado_noche": 45, "actividad_defecto": "Crucero por el Sena al Atardecer",
        "precio_actividad_defecto": 16, "precio_transporte_base": 39
    },
    {
        "destino": "Oporto", "pais": "Portugal", "transporte": "Autobús Nocturno", "code": "OPO",
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 28, "actividad_defecto": "Catamarán por el Duero + Catas de Vino",
        "precio_actividad_defecto": 18, "precio_transporte_base": 29
    },
    {
        "destino": "Londres", "pais": "Reino Unido", "transporte": "Avión Directo", "code": "STN",
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 50, "actividad_defecto": "Entrada Combinada London Eye + Tour",
        "precio_actividad_defecto": 32, "precio_transporte_base": 32
    }
]

# -----------------------------------------------------------------------------
# 4. BARRA LATERAL (CONTROLES)
# -----------------------------------------------------------------------------
st.sidebar.markdown("### ORIGEN DE LA ESCAPADA")
origen_seleccionado = st.sidebar.selectbox("Ciudad de Salida", list(ORIGENES_DISPONIBLES.keys()), index=0)
codigo_origen_actual = ORIGENES_DISPONIBLES[origen_seleccionado]

st.sidebar.markdown("---")
presupuesto_total_pack = st.sidebar.slider("Presupuesto MÁXIMO Pack Completo (€)", 50, 600, 220, step=10)

st.sidebar.markdown("---")
filtro_transporte = st.sidebar.multiselect(
    "Medios de Transporte Permitidos:",
    ["Avión", "Tren", "Autobús"],
    default=["Avión", "Tren", "Autobús"]
)

# -----------------------------------------------------------------------------
# 5. RENDERIZADO VISUAL CON CAMBIO DE TEMA REAL
# -----------------------------------------------------------------------------
st.markdown('<div class="brand-title">V A G A B O N D</div>', unsafe_allow_html=True)
st.markdown(f'<div class="brand-subtitle">Radar de Chollos en Escapadas Completas (<b>Viaje + Hotel + Experiencia Klook</b>) desde {origen_seleccionado}</div>', unsafe_allow_html=True)

serp_activa = "SERPAPI_KEY" in st.secrets
klook_activa = "TRAVELPAYOUTS_KEY" in st.secrets

if serp_activa or klook_activa:
    st.success("🟢 API Klook (Chollos Actividades) & Google Flights activas en tiempo real")

st.write("")

escapadas_filtradas = []

for item in ESCAPADAS_CATALOGO:
    if item["destino"].lower() == origen_seleccionado.lower():
        continue
        
    if not any(t in item["transporte"] for t in filtro_transporte):
        continue

    # 1. Transporte real
    precio_transporte = item["precio_transporte_base"]
    if "Avión" in item["transporte"] and serp_activa:
        p_vuelo = obtener_vuelo_google_real(codigo_origen_actual, item["code"])
        if p_vuelo:
            precio_transporte = p_vuelo

    # 2. Chollo Klook Actividades
    nombre_actividad = item["actividad_defecto"]
    precio_actividad = item["precio_actividad_defecto"]
    if klook_activa:
        datos_klook = obtener_chollos_klook(item["destino"])
        if datos_klook:
            nombre_actividad = datos_klook["actividad"]
            precio_actividad = datos_klook["precio"]

    # 3. Alojamiento (2 Noches)
    precio_alojamiento_total = item["hotel_estimado_noche"] * 2

    # 4. Total del Pack
    precio_total_pack = int(precio_transporte + precio_alojamiento_total + precio_actividad)

    if precio_total_pack <= presupuesto_total_pack:
        url_trans, url_hotel, url_act = generar_enlaces_escapada(
            item["transporte"], origen_seleccionado, item["destino"]
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

# Renderizado con tarjetas completamente adaptables al tema
if escapadas_filtradas:
    cols = st.columns(2)
    for idx, pack in enumerate(escapadas_filtradas):
        col = cols[idx % 2]
        with col:
            with st.container(border=True):
                st.caption(f"🗓️ {pack['duracion']} • 🚆 {pack['transporte']}")
                st.subheader(f"{pack['destino']} ({pack['pais']})")
                
                st.metric(label="Precio Total Pack Completo", value=f"{pack['precio_total']} €")
                
                st.markdown("---")
                st.markdown(f"• **Transporte (Ida/Vuelta):** {pack['precio_transporte']} €")
                st.markdown(f"• **Hotel (2 noches):** {pack['precio_alojamiento']} €")
                st.markdown(f"• **Chollo Klook:** {pack['actividad_nombre']} (**{pack['precio_actividad']} €**)")
                st.markdown("---")

                st.link_button(f"1. Reservar Transporte ({pack['precio_transporte']}€)", pack['url_transporte'], type="primary", use_container_width=True)
                st.link_button(f"2. Ver Hotel en Klook ({pack['precio_alojamiento']}€)", pack['url_hotel'], use_container_width=True)
                st.link_button(f"3. Reservar Experiencia ({pack['precio_actividad']}€)", pack['url_actividad'], use_container_width=True)
else:
    st.info(f"No se encontraron paquetes completos por debajo de {presupuesto_total_pack}€ desde {origen_seleccionado}. Ajusta el presupuesto en el panel lateral.")
