import streamlit as st
import pandas as pd
import urllib.parse
import httpx
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y TEMAS VISUALES ADAPTATIVOS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="VAGABOND | Escapadas Baratas",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.markdown("### CONFIGURACIÓN DE ALERTAS")
tema_elegido = st.sidebar.radio("Apariencia", ["Modo Claro ☀️", "Modo Oscuro 🌙"], index=0)

if tema_elegido == "Modo Oscuro 🌙":
    bg_app = "#090D16"
    bg_sidebar = "#111827"
    text_color = "#F8FAFC"
    sub_color = "#94A3B8"
    card_bg = "#111827"
    card_border = "#1E293B"
    btn_bg = "#F8FAFC"
    btn_text = "#090D16"
    btn_sec_bg = "#1E293B"
    btn_sec_text = "#F8FAFC"
    badge_bg = "rgba(16, 185, 129, 0.15)"
    accent_color = "#10B981"
else:
    bg_app = "#FAFAFA"
    bg_sidebar = "#FFFFFF"
    text_color = "#0F172A"
    sub_color = "#475569"
    card_bg = "#FFFFFF"
    card_border = "#E2E8F0"
    btn_bg = "#0F172A"
    btn_text = "#FFFFFF"
    btn_sec_bg = "#F1F5F9"
    btn_sec_text = "#0F172A"
    badge_bg = "rgba(4, 120, 87, 0.08)"
    accent_color = "#047857"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');

    /* Forzado absoluto de fondo de aplicación */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background-color: {bg_app} !important;
        color: {text_color} !important;
    }}

    /* Barra lateral */
    section[data-testid="stSidebar"], [data-testid="stSidebarContent"] {{
        background-color: {bg_sidebar} !important;
        border-right: 1px solid {card_border} !important;
    }}

    /* Tipografías globales */
    p, span, div, label, h1, h2, h3, h4, h5, h6, .stMarkdown {{
        color: {text_color} !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }}

    .brand-title {{
        font-family: 'Playfair Display', serif !important;
        font-size: 2.8rem;
        font-weight: 700;
        letter-spacing: 6px;
        color: {text_color} !important;
        margin-bottom: 0.2rem;
        text-transform: uppercase;
    }}

    .brand-subtitle {{
        font-size: 0.85rem;
        color: {sub_color} !important;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 2rem;
    }}

    /* Tarjeta fotográfica de destino */
    .card-container {{
        background-color: {card_bg};
        border: 1px solid {card_border};
        border-radius: 12px;
        overflow: hidden;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.04);
    }}

    .card-hero-img {{
        width: 100%;
        height: 180px;
        object-fit: cover;
    }}

    .card-body {{
        padding: 1.5rem;
    }}

    .card-title {{
        font-family: 'Playfair Display', serif !important;
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0;
        color: {text_color} !important;
    }}

    .card-price {{
        font-size: 2.2rem;
        font-weight: 700;
        color: {accent_color} !important;
    }}

    .card-tag {{
        display: inline-block;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        padding: 4px 10px;
        border-radius: 4px;
        background-color: {badge_bg};
        color: {accent_color} !important;
        margin-bottom: 8px;
    }}

    /* Botones de acción real adaptados al tema elegido */
    .btn-link-primary {{
        display: block;
        width: 100%;
        text-align: center;
        background-color: {btn_bg} !important;
        color: {btn_text} !important;
        padding: 0.75rem 1rem;
        border-radius: 6px;
        text-decoration: none !important;
        font-weight: 700;
        font-size: 0.75rem;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-top: 0.8rem;
        box-sizing: border-box;
    }}

    .btn-link-secondary {{
        display: block;
        width: 100%;
        text-align: center;
        background-color: {btn_sec_bg} !important;
        color: {btn_sec_text} !important;
        border: 1px solid {card_border};
        padding: 0.65rem 1rem;
        border-radius: 6px;
        text-decoration: none !important;
        font-weight: 600;
        font-size: 0.75rem;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-top: 0.5rem;
        box-sizing: border-box;
    }}

    /* Desglose de costes */
    .cost-item {{
        display: flex;
        justify-content: space-between;
        font-size: 0.85rem;
        color: {sub_color} !important;
        padding: 6px 0;
        border-bottom: 1px dashed {card_border};
    }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. MOTORES API (KLOOK ACTIVIDADES/ALOJAMIENTO & GOOGLE FLIGHTS)
# -----------------------------------------------------------------------------
def obtener_chollos_klook(destino_nombre):
    """Consulta la API de Klook para encontrar la experiencia más económica en la ciudad."""
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
                    "actividad": item_chollo.get("title", f"Experiencia en {destino_nombre}"),
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
    """Genera las URLs directas para la reserva."""
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
# 3. CATÁLOGO CON FOTOGRAFÍA REALISTA DE ARTE DE VIAJE (UNSPLASH ARCHITECTURE)
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
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 35, "actividad_defecto": "Ciudad de las Artes y Ciencias",
        "precio_actividad_defecto": 24, "precio_transporte_base": 19,
        "imagen": "https://images.unsplash.com/photo-1590496793929-36417d3117de?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Roma", "pais": "Italia", "transporte": "Avión Directo", "code": "FCO",
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 40, "actividad_defecto": "Visita Guiada Coliseo y Foro Romano",
        "precio_actividad_defecto": 30, "precio_transporte_base": 38,
        "imagen": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "París", "pais": "Francia", "transporte": "Autobús Larga Distancia", "code": "PAR",
        "duracion": "4 Días / 3 Noches", "hotel_estimado_noche": 45, "actividad_defecto": "Crucero por el Sena al Atardecer",
        "precio_actividad_defecto": 16, "precio_transporte_base": 39,
        "imagen": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Oporto", "pais": "Portugal", "transporte": "Autobús Nocturno", "code": "OPO",
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 28, "actividad_defecto": "Catamarán por el Duero y Catas de Vino",
        "precio_actividad_defecto": 18, "precio_transporte_base": 29,
        "imagen": "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Londres", "pais": "Reino Unido", "transporte": "Avión Directo", "code": "STN",
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 50, "actividad_defecto": "Entrada Combinada London Eye",
        "precio_actividad_defecto": 32, "precio_transporte_base": 32,
        "imagen": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?auto=format&fit=crop&w=800&q=80"
    }
]

# -----------------------------------------------------------------------------
# 4. PANEL LATERAL DE NAVEGACIÓN
# -----------------------------------------------------------------------------
st.sidebar.markdown("### ORIGEN DE LA ESCAPADA")
origen_seleccionado = st.sidebar.selectbox("Ciudad de Salida", list(ORIGENES_DISPONIBLES.keys()), index=0)
codigo_origen_actual = ORIGENES_DISPONIBLES[origen_seleccionado]

st.sidebar.markdown("---")
presupuesto_total_pack = st.sidebar.slider("Presupuesto MÁXIMO Pack (€)", 50, 600, 220, step=10)

st.sidebar.markdown("---")
filtro_transporte = st.sidebar.multiselect(
    "Modos de Transporte:",
    ["Avión", "Tren", "Autobús"],
    default=["Avión", "Tren", "Autobús"]
)

# -----------------------------------------------------------------------------
# 5. RENDERIZADO EDITORIAL DE TARJETAS DE ESCAPADA
# -----------------------------------------------------------------------------
st.markdown('<div class="brand-title">V A G A B O N D</div>', unsafe_allow_html=True)
st.markdown(f'<div class="brand-subtitle">Colección de Escapadas Completas desde <b>{origen_seleccionado}</b></div>', unsafe_allow_html=True)

serp_activa = "SERPAPI_KEY" in st.secrets
klook_activa = "TRAVELPAYOUTS_KEY" in st.secrets

escapadas_filtradas = []

for item in ESCAPADAS_CATALOGO:
    if item["destino"].lower() == origen_seleccionado.lower():
        continue
        
    if not any(t in item["transporte"] for t in filtro_transporte):
        continue

    # 1. Transporte
    precio_transporte = item["precio_transporte_base"]
    if "Avión" in item["transporte"] and serp_activa:
        p_vuelo = obtener_vuelo_google_real(codigo_origen_actual, item["code"])
        if p_vuelo:
            precio_transporte = p_vuelo

    # 2. Experiencia Klook
    nombre_actividad = item["actividad_defecto"]
    precio_actividad = item["precio_actividad_defecto"]
    if klook_activa:
        datos_klook = obtener_chollos_klook(item["destino"])
        if datos_klook:
            nombre_actividad = datos_klook["actividad"]
            precio_actividad = datos_klook["precio"]

    # 3. Alojamiento
    precio_alojamiento_total = item["hotel_estimado_noche"] * 2

    # 4. Precio Total
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
            "imagen": item["imagen"],
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
            <div class="card-container">
                <img src="{pack['imagen']}" class="card-hero-img" alt="{pack['destino']}">
                <div class="card-body">
                    <div class="card-tag">{pack['duracion']} • {pack['transporte']}</div>
                    <div class="card-title">{pack['destino']}, {pack['pais']}</div>
                    
                    <div style="margin-top: 12px; margin-bottom: 15px;">
                        <span class="card-price">{pack['precio_total']} €</span>
                        <span style="font-size: 0.8rem; color: {sub_color};"> / PACK COMPLETO</span>
                    </div>

                    <div class="cost-item">
                        <span>Billete de Transporte (Ida / Vuelta)</span>
                        <b>{pack['precio_transporte']} €</b>
                    </div>
                    <div class="cost-item">
                        <span>Alojamiento (2 Noches)</span>
                        <b>{pack['precio_alojamiento']} €</b>
                    </div>
                    <div class="cost-item" style="border-bottom: none;">
                        <span>Experiencia Klook: {pack['actividad_nombre']}</span>
                        <b>{pack['precio_actividad']} €</b>
                    </div>

                    <a href="{pack['url_transporte']}" target="_blank" class="btn-link-primary">1. RESERVAR TRANSPORTE ({pack['precio_transporte']}€)</a>
                    <a href="{pack['url_hotel']}" target="_blank" class="btn-link-secondary">2. HOTEL EN KLOOK ({pack['precio_alojamiento']}€)</a>
                    <a href="{pack['url_actividad']}" target="_blank" class="btn-link-secondary">3. RESERVAR EXPERIENCIA ({pack['precio_actividad']}€)</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info(f"No hay paquetes disponibles desde {origen_seleccionado} por debajo de {presupuesto_total_pack}€. Eleva el presupuesto en el panel lateral.")
