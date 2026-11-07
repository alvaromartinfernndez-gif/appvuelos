import html
import re
import urllib.parse
from datetime import datetime, timedelta

import httpx
import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y TEMA (AESTHETIC & MINIMALISTA)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="VAGABOND | Engine Global de Vuelos",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.markdown("### APARIENCIA")
tema_elegido = st.sidebar.radio("Modo de interfaz", ["Modo Claro", "Modo Oscuro"], index=0)

if tema_elegido == "Modo Oscuro":
    bg_app, bg_sidebar = "#090D16", "#111827"
    text_main, text_sub = "#F1F5F9", "#94A3B8"
    card_bg, card_border = "#111827", "#1E293B"
    btn_bg, btn_text, btn_hover = "#F1F5F9", "#090D16", "#CBD5E1"
    price_color, input_bg, input_text = "#34D399", "#1E293B", "#F1F5F9"
    badge_bg = "rgba(52, 211, 153, 0.1)"
else:
    bg_app, bg_sidebar = "#FAFAFA", "#FFFFFF"
    text_main, text_sub = "#0F172A", "#64748B"
    card_bg, card_border = "#FFFFFF", "#E2E8F0"
    btn_bg, btn_text, btn_hover = "#0F172A", "#FFFFFF", "#334155"
    price_color, input_bg, input_text = "#047857", "#FFFFFF", "#0F172A"
    badge_bg = "rgba(4, 120, 87, 0.08)"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap');
.stApp {{ background:{bg_app}!important; color:{text_main}!important; }}
html,body,[class*="css"],.stMarkdown,p,span,div,h1,h2,h3,h4,h5,h6 {{ font-family:'Plus Jakarta Sans',sans-serif!important; color:{text_main}!important; }}
section[data-testid="stSidebar"] {{ background:{bg_sidebar}!important; border-right:1px solid {card_border}!important; }}
section[data-testid="stSidebar"] * {{ color:{text_main}!important; }}
div[data-baseweb="select"]>div,div[data-baseweb="input"]>div,input {{ background:{input_bg}!important; color:{input_text}!important; border:1px solid {card_border}!important; border-radius:6px!important; }}
.brand-header {{ font-family:'Cinzel',serif!important; font-size:2.2rem; font-weight:600; letter-spacing:6px; margin-bottom:.2rem; text-transform:uppercase; }}
.brand-sub {{ font-size:.85rem; color:{text_sub}!important; margin-bottom:2rem; font-weight:300; letter-spacing:2px; text-transform:uppercase; }}
.section-title {{ font-family:'Cinzel',serif!important; font-size:1.25rem; font-weight:600; letter-spacing:2px; margin:1rem 0; text-transform:uppercase; }}
.destination-card {{ background:{card_bg}!important; border:1px solid {card_border}; border-radius:12px; overflow:hidden; box-shadow:0 2px 12px rgba(0,0,0,.03); transition:transform .2s,border-color .2s; margin-bottom:1.5rem; }}
.destination-card:hover {{ transform:translateY(-3px); border-color:{text_sub}; }}
.card-image-container {{ width:100%; height:170px; background-size:cover; background-position:center; }}
.card-content {{ padding:1.2rem; background:{card_bg}!important; }}
.card-title {{ font-family:'Cinzel',serif!important; font-size:1.15rem; font-weight:600; margin:0; }}
.card-region {{ font-size:.75rem; text-transform:uppercase; letter-spacing:1.5px; color:{text_sub}!important; font-weight:500; margin-top:4px; }}
.price-tag {{ font-size:1.3rem; font-weight:600; color:{price_color}!important; }}
.badge-cp {{ display:inline-block; background:{badge_bg}; color:{price_color}!important; font-size:.7rem; font-weight:600; padding:2px 8px; border-radius:4px; letter-spacing:1px; text-transform:uppercase; margin-top:6px; }}
.booking-btn {{ display:block; width:100%; text-align:center; background:{btn_bg}!important; color:{btn_text}!important; padding:.6rem 1rem; border-radius:6px; text-decoration:none!important; font-weight:500; font-size:.8rem; letter-spacing:1px; text-transform:uppercase; margin-top:1rem; transition:background-color .2s; }}
.booking-btn:hover {{ background:{btn_hover}!important; }}
.status-dot {{ display:inline-flex; align-items:center; gap:8px; font-size:.75rem; color:{text_sub}!important; letter-spacing:1px; text-transform:uppercase; }}
.dot {{ width:6px; height:6px; background:{price_color}; border-radius:50%; }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. AEROPUERTOS DE ORIGEN Y CATÁLOGO GLOBAL DE SUGERENCIAS
# -----------------------------------------------------------------------------
ORIGENES_MUNDIALES = {
    "España": ["Madrid (MAD)", "Barcelona (BCN)", "Valencia (VLC)", "Málaga (AGP)", "Sevilla (SVQ)"],
    "Europa": ["París (CDG)", "Londres (LHR)", "Fráncfort (FRA)", "Roma (FCO)", "Ámsterdam (AMS)"],
    "América": ["Nueva York (JFK)", "Miami (MIA)", "Los Ángeles (LAX)", "Ciudad de México (MEX)", "Bogotá (BOG)", "Buenos Aires (EZE)"],
    "Asia & Oriente": ["Dubái (DXB)", "Tokio (HND)", "Bangkok (BKK)", "Singapur (SIN)"],
}

CATALOGO_SEMILLA = [
    {"destino":"Roma","pais":"Italia","continente":"Europa","code":"FCO","precio_base":34,"duracion":"3 días","dias_num":3,"tipo":"Directo","rating":9.5,"img":"https://images.unsplash.com/photo-1552832230-c0197dd311b5?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Oporto","pais":"Portugal","continente":"Europa","code":"OPO","precio_base":22,"duracion":"3 días","dias_num":3,"tipo":"Directo","rating":9.2,"img":"https://images.unsplash.com/photo-1555881400-74d7acaacd8b?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Cancún","pais":"México","continente":"América","code":"CUN","precio_base":320,"duracion":"7 días","dias_num":7,"tipo":"1 escala","rating":8.9,"img":"https://images.unsplash.com/photo-1510097467424-192d713be8b2?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Nueva York","pais":"EE.UU.","continente":"América","code":"JFK","precio_base":280,"duracion":"6 días","dias_num":6,"tipo":"Directo","rating":9.7,"img":"https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Tokio","pais":"Japón","continente":"Asia","code":"HND","precio_base":540,"duracion":"10 días","dias_num":10,"tipo":"1 escala","rating":9.9,"img":"https://images.unsplash.com/photo-1503899036084-c55cdd92da26?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Bangkok","pais":"Tailandia","continente":"Asia","code":"BKK","precio_base":440,"duracion":"10 días","dias_num":10,"tipo":"1 escala","rating":9.5,"img":"https://images.unsplash.com/photo-1508009603885-50cf7c579365?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Dubái","pais":"EAU","continente":"Asia","code":"DXB","precio_base":210,"duracion":"4 días","dias_num":4,"tipo":"Directo","rating":8.8,"img":"https://images.unsplash.com/photo-1512453979798-5ea266f8880c?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Ciudad del Cabo","pais":"Sudáfrica","continente":"África","code":"CPT","precio_base":460,"duracion":"9 días","dias_num":9,"tipo":"1 escala","rating":9.4,"img":"https://images.unsplash.com/photo-1580618672591-eb180b1a973f?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Sídney","pais":"Australia","continente":"Oceanía","code":"SYD","precio_base":820,"duracion":"12 días","dias_num":12,"tipo":"2 escalas","rating":9.3,"img":"https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?q=80&w=800&auto=format&fit=crop"},
]

# -----------------------------------------------------------------------------
# 3. SERVICIOS: GEOCODIFICACIÓN Y TARIFAS SERPAPI
# -----------------------------------------------------------------------------
def obtener_clave_serpapi():
    try:
        return st.secrets.get("SERPAPI_KEY")
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return None


@st.cache_data(ttl=86400, show_spinner=False)
def buscar_aeropuerto_global(busqueda_usuario):
    """Resuelve el nombre de un lugar con Nominatim; no inventa códigos IATA."""
    try:
        response = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": busqueda_usuario, "format": "json", "addressdetails": 1, "limit": 1},
            headers={"User-Agent": "VagabondGlobalEngine/10.0"},
            timeout=6.0,
        )
        response.raise_for_status()
        results = response.json()
        if not results:
            return None
        address = results[0].get("address", {})
        city = address.get("city") or address.get("town") or address.get("village") or address.get("state") or busqueda_usuario
        return {"destino": city, "pais": address.get("country", "Mundo")}
    except (httpx.HTTPError, ValueError, TypeError):
        return None


@st.cache_data(ttl=300, show_spinner=False)
def obtener_tarifa_google_flights(origen_code, destino_code, fecha_ida, fecha_vuelta, api_key):
    if not api_key or not re.fullmatch(r"[A-Z]{3}", str(origen_code)) or not re.fullmatch(r"[A-Z]{3}", str(destino_code)):
        return None
    try:
        response = httpx.get(
            "https://serpapi.com/search.json",
            params={
                "engine": "google_flights",
                "departure_id": origen_code,
                "arrival_id": destino_code,
                "outbound_date": fecha_ida,
                "return_date": fecha_vuelta,
                "currency": "EUR",
                "hl": "es",
                "api_key": api_key,
            },
            timeout=8.0,
        )
        response.raise_for_status()
        flights = response.json().get("best_flights") or []
        return int(flights[0]["price"]) if flights else None
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return None


def crear_url_google_flights(destination, origin, outbound, inbound):
    query = f"Flights to {destination} from {origin} on {outbound} through {inbound}"
    return "https://www.google.com/travel/flights?q=" + urllib.parse.quote(query)


def render_cards(frame, value_badge=False):
    columns = st.columns(3)
    for index, (_, row) in enumerate(frame.iterrows()):
        with columns[index % 3]:
            badge = '<div class="badge-cp">Ratio Óptimo</div>' if value_badge else ""
            st.markdown(
                f"""
                <div class="destination-card">
                    <div class="card-image-container" style="background-image:url('{html.escape(str(row['img']), quote=True)}')"></div>
                    <div class="card-content">
                        <div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px">
                            <h3 class="card-title">{html.escape(str(row['destino']))}</h3>
                            <span class="price-tag">{row['precio']} €</span>
                        </div>
                        <div class="card-region">{html.escape(str(row['pais']))} · {html.escape(str(row['duracion']))}</div>
                        <div style="font-size:.75rem;color:{text_sub}!important;margin-top:6px">Vuelo {html.escape(str(row['tipo']))}</div>
                        {badge}
                        <a href="{html.escape(row['url_reserva'], quote=True)}" target="_blank" rel="noopener noreferrer" class="booking-btn">Reservar en Google Flights</a>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# -----------------------------------------------------------------------------
# 4. BARRA LATERAL: BÚSQUEDA GLOBAL
# -----------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("### ORIGEN DEL VIAJE")
region_salida = st.sidebar.selectbox("Región", list(ORIGENES_MUNDIALES))
ciudad_origen = st.sidebar.selectbox("Aeropuerto", ORIGENES_MUNDIALES[region_salida])
codigo_origen = ciudad_origen.rsplit("(", 1)[-1].replace(")", "").strip()

st.sidebar.markdown("---")
st.sidebar.markdown("### BÚSQUEDA MUNDIAL")
busqueda_libre = st.sidebar.text_input(
    "Buscar cualquier rincón del planeta:",
    "",
    placeholder="Ej: Bora Bora, Katmandú, Reikiavik, Zanzíbar...",
)
solo_directos = st.sidebar.checkbox("Mostrar solo vuelos directos", value=False)
presupuesto_max = st.sidebar.slider("Presupuesto máximo (€)", 10, 4000, 1000, step=50)

# -----------------------------------------------------------------------------
# 5. HEADER Y PROCESAMIENTO DE CONSULTAS
# -----------------------------------------------------------------------------
st.markdown('<div class="brand-header">V A G A B O N D</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="brand-sub">Buscador global conectado con Google Flights desde <b>{html.escape(ciudad_origen)}</b></div>',
    unsafe_allow_html=True,
)
serpapi_key = obtener_clave_serpapi()
if serpapi_key:
    st.markdown('<div class="status-dot"><div class="dot"></div> API Google Flights vía SerpApi activa</div>', unsafe_allow_html=True)
else:
    st.caption("Sin SERPAPI_KEY se muestran precios de referencia; confirma las tarifas en Google Flights.")
st.write("")

fecha_ida = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
fecha_vuelta = (datetime.now() + timedelta(days=21)).strftime("%Y-%m-%d")
catalogo_activo = [item.copy() for item in CATALOGO_SEMILLA]
resultado_global = None

if busqueda_libre.strip():
    resultado_global = buscar_aeropuerto_global(busqueda_libre.strip())
    if resultado_global:
        catalogo_activo.insert(0, {
            "destino": resultado_global["destino"],
            "pais": resultado_global["pais"],
            "continente": "Personalizado",
            "code": "",
            "precio_base": 150,
            "duracion": "Flexible (7 días)",
            "dias_num": 7,
            "tipo": "Consultar disponibilidad",
            "rating": 9.2,
            "img": "https://images.unsplash.com/photo-1488646953014-85cb44e25828?q=80&w=800&auto=format&fit=crop",
        })
    else:
        st.warning("No se pudo localizar ese destino. Prueba con otra ciudad, isla o país.")

vuelos_procesados = []
for item in catalogo_activo:
    precio_google = obtener_tarifa_google_flights(
        codigo_origen, item["code"], fecha_ida, fecha_vuelta, serpapi_key
    )
    precio_final = precio_google if precio_google is not None else item["precio_base"]
    factor_directo = 1.25 if item["tipo"] == "Directo" else 1.0
    item["precio"] = precio_final
    item["score_cp"] = round((item["rating"] * 10 * factor_directo) / max(precio_final, 1), 3)
    item["url_reserva"] = crear_url_google_flights(item["destino"], codigo_origen, fecha_ida, fecha_vuelta)
    vuelos_procesados.append(item)

df = pd.DataFrame(vuelos_procesados)
df_filtrado = df[df["precio"] <= presupuesto_max].copy()

if solo_directos:
    df_filtrado = df_filtrado[df_filtrado["tipo"].str.contains("Directo", na=False)]

if busqueda_libre.strip():
    query = busqueda_libre.strip().casefold()
    matches = (
        df_filtrado["destino"].str.casefold().str.contains(query, regex=False, na=False)
        | df_filtrado["pais"].str.casefold().str.contains(query, regex=False, na=False)
    )
    # Keep a successfully geocoded custom destination in results even if its display name differs from the query.
    if resultado_global is not None:
        matches |= df_filtrado["continente"].eq("Personalizado")
    df_filtrado = df_filtrado[matches]

# -----------------------------------------------------------------------------
# 6. PRESENTACIÓN: VUELOS MÁS BARATOS Y MEJORES CALIDAD-PRECIO
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title">Los 6 viajes más baratos del mundo</div>', unsafe_allow_html=True)
if not df_filtrado.empty:
    render_cards(df_filtrado.sort_values(by="precio").head(6))
else:
    st.info("No hay rutas dentro de este presupuesto y filtros. Ajusta las opciones en la barra lateral.")

st.markdown("---")
st.markdown('<div class="section-title">Los 6 mejores en calidad - precio</div>', unsafe_allow_html=True)
if not df_filtrado.empty:
    render_cards(df_filtrado.sort_values(by="score_cp", ascending=False).head(6), value_badge=True)
else:
    st.info("No se encontraron resultados para calcular la relación calidad-precio.")
