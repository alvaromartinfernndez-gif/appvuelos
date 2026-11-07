import html
import re
import urllib.parse
from datetime import datetime, timedelta

import httpx
import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y TEMA (CLARO / OSCURO)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Vagabond | Escapadas Globales",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.markdown("### Apariencia")
tema_elegido = st.sidebar.radio("Modo de pantalla", ["Claro ☀️", "Oscuro 🌙"], index=0)

if tema_elegido == "Oscuro 🌙":
    bg_app, bg_sidebar, text_main, text_sub = "#0F172A", "#1E293B", "#F8FAFC", "#94A3B8"
    card_bg, card_border = "#1E293B", "#334155"
    btn_bg, btn_text, btn_hover = "#38BDF8", "#0F172A", "#0284C7"
    price_color, hero_border, shadow = "#34D399", "#38BDF8", "rgba(0,0,0,.4)"
    input_bg, input_text = "#334155", "#F8FAFC"
else:
    bg_app, bg_sidebar, text_main, text_sub = "#F8FAFC", "#FFFFFF", "#0F172A", "#475569"
    card_bg, card_border = "#FFFFFF", "#CBD5E1"
    btn_bg, btn_text, btn_hover = "#0F172A", "#FFFFFF", "#047857"
    price_color, hero_border, shadow = "#047857", "#047857", "rgba(0,0,0,.06)"
    input_bg, input_text = "#FFFFFF", "#0F172A"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=Plus+Jakarta+Sans:wght@300;400;600&display=swap');
.stApp {{ background-color:{bg_app}!important; color:{text_main}!important; }}
html,body,[class*="css"],.stMarkdown,p,span,div,h1,h2,h3,h4,h5,h6 {{ font-family:'Plus Jakarta Sans',sans-serif!important; color:{text_main}!important; }}
section[data-testid="stSidebar"] {{ background-color:{bg_sidebar}!important; border-right:1px solid {card_border}!important; }}
section[data-testid="stSidebar"] * {{ color:{text_main}!important; }}
div[data-baseweb="select"]>div,div[data-baseweb="input"]>div,input {{ background-color:{input_bg}!important; color:{input_text}!important; border:1px solid {card_border}!important; border-radius:8px!important; }}
div[data-baseweb="popover"],div[data-baseweb="menu"],ul[role="listbox"],li[role="option"] {{ background-color:{input_bg}!important; color:{input_text}!important; }}
li[role="option"]:hover {{ background-color:{card_border}!important; }}
.brand-header {{ font-family:'Cinzel',serif!important; font-size:2.5rem; font-weight:700; letter-spacing:2px; color:{text_main}!important; margin-bottom:.2rem; text-transform:uppercase; }}
.brand-sub {{ font-size:.95rem; color:{text_sub}!important; margin-bottom:1.5rem; font-weight:300; letter-spacing:1px; }}
.hero-badge {{ background-color:{hero_border}; color:{btn_text}!important; font-size:.75rem; font-weight:700; padding:4px 10px; border-radius:6px; letter-spacing:1px; text-transform:uppercase; display:inline-block; margin-bottom:.5rem; }}
.destination-card {{ background-color:{card_bg}!important; border-radius:16px; overflow:hidden; border:1px solid {card_border}; box-shadow:0 4px 20px {shadow}; transition:transform .2s ease; margin-bottom:1.8rem; }}
.destination-card:hover {{ transform:translateY(-4px); }}
.card-image-container {{ width:100%; height:190px; background-size:cover; background-position:center; }}
.card-content {{ padding:1.25rem; background-color:{card_bg}!important; }}
.card-title {{ font-family:'Cinzel',serif!important; font-size:1.25rem; font-weight:700; color:{text_main}!important; margin:0; }}
.card-region {{ font-size:.8rem; text-transform:uppercase; letter-spacing:1px; color:{text_sub}!important; font-weight:600; margin-top:2px; }}
.price-tag {{ font-size:1.4rem; font-weight:700; color:{price_color}!important; }}
.booking-btn {{ display:block; width:100%; text-align:center; background-color:{btn_bg}!important; color:{btn_text}!important; padding:.65rem 1rem; border-radius:8px; text-decoration:none!important; font-weight:600; font-size:.85rem; letter-spacing:.5px; margin-top:1rem; }}
.booking-btn:hover {{ background-color:{btn_hover}!important; }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. SERVICIOS: GEOCODIFICACIÓN Y SERPAPI
# -----------------------------------------------------------------------------
@st.cache_data(ttl=86400)
def obtener_coordenadas_lugar(nombre_lugar):
    """Busca coordenadas con Nominatim; devuelve un valor de reserva si no encuentra."""
    try:
        response = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": nombre_lugar, "format": "json", "limit": 1},
            headers={"User-Agent": "VagabondApp/3.0 (travel search demo)"},
            timeout=6.0,
        )
        response.raise_for_status()
        results = response.json()
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        pass
    return 20.0, 0.0


def obtener_clave_serpapi():
    try:
        return st.secrets.get("SERPAPI_KEY")
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return None


@st.cache_data(ttl=300, show_spinner=False)
def buscar_vuelo_google_flights_real(origen, destino_code, outbound_date, return_date, api_key):
    """Consulta resultados de Google Flights a través del servicio externo SerpApi."""
    if not api_key or not re.fullmatch(r"[A-Z]{3}", str(origen)) or not re.fullmatch(r"[A-Z]{3}", str(destino_code)):
        return None
    try:
        response = httpx.get(
            "https://serpapi.com/search.json",
            params={
                "engine": "google_flights",
                "departure_id": origen,
                "arrival_id": destino_code,
                "outbound_date": outbound_date,
                "return_date": return_date,
                "currency": "EUR",
                "hl": "es",
                "api_key": api_key,
            },
            timeout=12.0,
        )
        response.raise_for_status()
        payload = response.json()
        flights = payload.get("best_flights") or payload.get("other_flights") or []
        if flights:
            return int(flights[0]["price"])
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return None
    return None

# -----------------------------------------------------------------------------
# 3. CATÁLOGO DE ORÍGENES Y DESTINOS
# -----------------------------------------------------------------------------
ORIGENES_GLOBALES = {
    "Europa": {
        "España": ["Madrid (MAD)", "Barcelona (BCN)", "Valencia (VLC)", "Málaga (AGP)", "Sevilla (SVQ)"],
        "Francia": ["París (CDG)", "Niza (NCE)", "Marsella (MRS)"],
        "Alemania": ["Fráncfort (FRA)", "Múnich (MUC)", "Berlín (BER)"],
        "Reino Unido": ["Londres (LHR)", "Mánchester (MAN)"],
        "Italia": ["Roma (FCO)", "Milán (MXP)", "Venecia (VCE)"],
    },
    "América": {
        "Estados Unidos": ["Nueva York (JFK)", "Los Ángeles (LAX)", "Miami (MIA)"],
        "México": ["Ciudad de México (MEX)", "Cancún (CUN)"],
        "Colombia": ["Bogotá (BOG)", "Medellín (MDE)"],
        "Argentina": ["Buenos Aires (EZE)"],
    },
    "Asia & Oriente": {
        "Japón": ["Tokio (HND)", "Osaka (KIX)"],
        "Emiratos Árabes": ["Dubái (DXB)"],
        "Tailandia": ["Bangkok (BKK)"],
    },
}

REGIONES_DESTINO = [
    "Cualquier rincón del mundo", "Caribe & Playas Tropicales", "Cáucaso & Daguestán",
    "Sudeste Asiático", "Capitales Europeas", "Oriente Medio & Desierto",
    "Nórdicos & Auroras Boreales", "Islas del Mediterráneo", "Búsqueda por destino exacto...",
]

DATA_DESTINOS_BASE = [
    {"destino":"Roma","region":"Capitales Europeas","pais":"Italia","precio_base":34,"duracion":"3 días","dias_num":3,"lat":41.9028,"lon":12.4964,"tipo":"Directo","code":"FCO","img":"https://images.unsplash.com/photo-1552832230-c0197dd311b5?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Oporto","region":"Capitales Europeas","pais":"Portugal","precio_base":22,"duracion":"3 días","dias_num":3,"lat":41.1579,"lon":-8.6291,"tipo":"Directo","code":"OPO","img":"https://images.unsplash.com/photo-1555881400-74d7acaacd8b?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Cancún","region":"Caribe & Playas Tropicales","pais":"México","precio_base":340,"duracion":"7 días","dias_num":7,"lat":21.1619,"lon":-86.8515,"tipo":"1 escala","code":"CUN","img":"https://images.unsplash.com/photo-1510097467424-192d713be8b2?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Majachkalá","region":"Cáucaso & Daguestán","pais":"Rusia / Cáucaso","precio_base":195,"duracion":"5 días","dias_num":5,"lat":42.9849,"lon":47.5046,"tipo":"1 escala","code":"MCX","img":"https://images.unsplash.com/photo-1516483638261-f4dbaf036963?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Bangkok","region":"Sudeste Asiático","pais":"Tailandia","precio_base":460,"duracion":"10 días","dias_num":10,"lat":13.7563,"lon":100.5018,"tipo":"1 escala","code":"BKK","img":"https://images.unsplash.com/photo-1508009603885-50cf7c579365?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Dubái","region":"Oriente Medio & Desierto","pais":"EAU","precio_base":220,"duracion":"4 días","dias_num":4,"lat":25.2048,"lon":55.2708,"tipo":"Directo","code":"DXB","img":"https://images.unsplash.com/photo-1512453979798-5ea266f8880c?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Reikiavik","region":"Nórdicos & Auroras Boreales","pais":"Islandia","precio_base":125,"duracion":"4 días","dias_num":4,"lat":64.1466,"lon":-21.9426,"tipo":"Directo","code":"KEF","img":"https://images.unsplash.com/photo-1504893524553-b855bce32c67?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Ibiza","region":"Islas del Mediterráneo","pais":"España","precio_base":19,"duracion":"3 días","dias_num":3,"lat":38.9067,"lon":1.4206,"tipo":"Directo","code":"IBZ","img":"https://images.unsplash.com/photo-1537996194471-e657df975ab4?q=80&w=800&auto=format&fit=crop"},
]

# -----------------------------------------------------------------------------
# 4. CONTROLES Y PREPARACIÓN DE BÚSQUEDA
# -----------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("### Configuración de búsqueda")
continente = st.sidebar.selectbox("Región de salida", list(ORIGENES_GLOBALES))
pais = st.sidebar.selectbox("País", list(ORIGENES_GLOBALES[continente]))
ciudad_origen = st.sidebar.selectbox("Aeropuerto", ORIGENES_GLOBALES[continente][pais])
codigo_iata = ciudad_origen.rsplit("(", 1)[-1].replace(")", "").strip() if "(" in ciudad_origen else "MAD"

st.sidebar.markdown("---")
region_filtro = st.sidebar.selectbox("Filtro de Destino", REGIONES_DESTINO)
destino_busqueda = ""
if region_filtro == "Búsqueda por destino exacto...":
    destino_busqueda = st.sidebar.text_input("Escribe cualquier ciudad o punto del planeta:", "Daguestán")

duracion_filtro = st.sidebar.selectbox(
    "Duración del viaje",
    ["Cualquier duración", "Escapada rápida (3-4 días)", "Semana completa (5-8 días)", "Gran viaje (+8 días)"],
)
presupuesto_max = st.sidebar.slider("Presupuesto máximo (€)", 10, 2000, 500, step=10)

fecha_ida = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
fecha_vuelta = (datetime.now() + timedelta(days=17)).strftime("%Y-%m-%d")
serpapi_key = obtener_clave_serpapi()

destinos_a_procesar = [item.copy() for item in DATA_DESTINOS_BASE]
if region_filtro == "Búsqueda por destino exacto..." and destino_busqueda.strip():
    lat_geo, lon_geo = obtener_coordenadas_lugar(destino_busqueda.strip())
    destinos_a_procesar.insert(0, {
        "destino": destino_busqueda.strip().title(), "region": "Búsqueda Personalizada", "pais": "Global",
        "precio_base": 150, "duracion": "5 días", "dias_num": 5, "lat": lat_geo, "lon": lon_geo,
        "tipo": "Consultar disponibilidad", "code": "",
        "img": "https://images.unsplash.com/photo-1488646953014-85cb44e25828?q=80&w=800&auto=format&fit=crop",
    })

# -----------------------------------------------------------------------------
# 5. BÚSQUEDA DE PRECIOS
# -----------------------------------------------------------------------------
st.markdown('<div class="brand-header">V A G A B O N D</div>', unsafe_allow_html=True)
st.markdown(f'<div class="brand-sub">Búsqueda desde <b>{html.escape(ciudad_origen)}</b> · tarifas sujetas a cambios</div>', unsafe_allow_html=True)
if serpapi_key:
    st.caption("SerpApi está configurada: se consultan resultados de Google Flights a través de SerpApi. Verifica la tarifa antes de reservar.")
else:
    st.caption("Sin SERPAPI_KEY: se muestran precios de referencia, no tarifas en tiempo real. Los enlaces abren búsquedas de Google Flights.")

vuelos_procesados = []
for item in destinos_a_procesar:
    item_copy = item.copy()
    precio_real = buscar_vuelo_google_flights_real(
        codigo_iata, item["code"], fecha_ida, fecha_vuelta, serpapi_key
    )
    if precio_real is not None:
        item_copy["precio"] = precio_real
        item_copy["fuente_precio"] = "Resultado de SerpApi / Google Flights"
    else:
        item_copy["precio"] = item["precio_base"]
        item_copy["fuente_precio"] = "Precio de referencia (no cotización)"
    query = f"Flights to {item['destino']} from {codigo_iata} on {fecha_ida} through {fecha_vuelta}"
    item_copy["url_reserva"] = "https://www.google.com/travel/flights?q=" + urllib.parse.quote(query)
    vuelos_procesados.append(item_copy)

df = pd.DataFrame(vuelos_procesados)
df_filtrado = df[df["precio"] <= presupuesto_max].copy()
if region_filtro != "Cualquier rincón del mundo":
    if region_filtro == "Búsqueda por destino exacto...":
        if destino_busqueda.strip():
            term = destino_busqueda.strip().lower()
            mask = (
                df_filtrado["destino"].str.lower().str.contains(term, na=False)
                | df_filtrado["region"].str.lower().str.contains(term, na=False)
                | df_filtrado["pais"].str.lower().str.contains(term, na=False)
            )
            df_filtrado = df_filtrado[mask]
    else:
        df_filtrado = df_filtrado[df_filtrado["region"] == region_filtro]

if duracion_filtro == "Escapada rápida (3-4 días)":
    df_filtrado = df_filtrado[df_filtrado["dias_num"].between(3, 4)]
elif duracion_filtro == "Semana completa (5-8 días)":
    df_filtrado = df_filtrado[df_filtrado["dias_num"].between(5, 8)]
elif duracion_filtro == "Gran viaje (+8 días)":
    df_filtrado = df_filtrado[df_filtrado["dias_num"] > 8]
df_filtrado = df_filtrado.sort_values(by="precio")

# -----------------------------------------------------------------------------
# 6. RESULTADOS
# -----------------------------------------------------------------------------
if not df_filtrado.empty:
    top = df_filtrado.iloc[0]
    st.markdown("### Oferta destacada")
    hero_image, hero_details = st.columns([1.2, 2])
    with hero_image:
        st.image(top["img"], use_container_width=True)
    with hero_details:
        st.markdown(f"""
        <div class="hero-badge">{html.escape(top['fuente_precio'])}</div>
        <h2 style="font-family:'Cinzel',serif;margin:0">{html.escape(top['destino'])} ({html.escape(top['pais'])})</h2>
        <p>Duración recomendada: {html.escape(top['duracion'])}</p>
        <div style="font-size:2rem;font-weight:700;color:{price_color};margin:10px 0">Desde {top['precio']} €</div>
        <a href="{html.escape(top['url_reserva'], quote=True)}" target="_blank" rel="noopener noreferrer" class="booking-btn">CONSULTAR EN GOOGLE FLIGHTS</a>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Escapadas encontradas")
    cols = st.columns(3)
    for index, (_, row) in enumerate(df_filtrado.iterrows()):
        with cols[index % 3]:
            st.markdown(f"""
            <div class="destination-card">
                <div class="card-image-container" style="background-image:url('{html.escape(row['img'], quote=True)}')"></div>
                <div class="card-content">
                    <div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px">
                        <h3 class="card-title">{html.escape(row['destino'])}</h3>
                        <span class="price-tag">{row['precio']} €</span>
                    </div>
                    <div class="card-region">{html.escape(row['pais'])} · {html.escape(row['duracion'])}</div>
                    <div style="font-size:.8rem;color:{text_sub};margin-top:6px">Vuelo {html.escape(row['tipo'])}</div>
                    <div style="font-size:.72rem;color:{text_sub};margin-top:6px">{html.escape(row['fuente_precio'])}</div>
                    <a href="{html.escape(row['url_reserva'], quote=True)}" target="_blank" rel="noopener noreferrer" class="booking-btn">VER EN GOOGLE FLIGHTS</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Mapa de rutas globales")
    st.map(df_filtrado[["lat", "lon"]], zoom=1)
else:
    st.info("No hay opciones que coincidan con los filtros. Incrementa el presupuesto o cambia la duración/destino.")
