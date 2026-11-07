import html
import re
import urllib.parse
from datetime import datetime, timedelta

import httpx
import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# Page setup and theme
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="VAGABOND | Engine Global de Vuelos",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.markdown("### APARIENCIA")
theme = st.sidebar.radio("Modo de interfaz", ["Modo Claro", "Modo Oscuro"], index=0)

if theme == "Modo Oscuro":
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
.booking-btn {{ display:block; width:100%; text-align:center; background:{btn_bg}!important; color:{btn_text}!important; padding:.6rem 1rem; border-radius:6px; text-decoration:none!important; font-weight:500; font-size:.8rem; letter-spacing:1px; text-transform:uppercase; margin-top:1rem; }}
.booking-btn:hover {{ background:{btn_hover}!important; }}
.status-dot {{ display:inline-flex; align-items:center; gap:8px; font-size:.75rem; color:{text_sub}!important; letter-spacing:1px; text-transform:uppercase; }}
.dot {{ width:6px; height:6px; background:{price_color}; border-radius:50%; }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Global origin and destination catalog
# -----------------------------------------------------------------------------
ORIGENES_GLOBALES = {
    "Europa": {
        "España": ["Madrid (MAD)", "Barcelona (BCN)", "Valencia (VLC)", "Málaga (AGP)", "Sevilla (SVQ)"],
        "Francia": ["París (CDG)", "Niza (NCE)"],
        "Alemania": ["Fráncfort (FRA)", "Berlín (BER)"],
        "Reino Unido": ["Londres (LHR)", "Mánchester (MAN)"],
        "Italia": ["Roma (FCO)", "Milán (MXP)"],
    },
    "América": {
        "Estados Unidos": ["Nueva York (JFK)", "Los Ángeles (LAX)", "Miami (MIA)"],
        "México": ["Ciudad de México (MEX)", "Cancún (CUN)"],
        "Colombia": ["Bogotá (BOG)"],
        "Argentina": ["Buenos Aires (EZE)"],
    },
    "Asia & África": {
        "Japón": ["Tokio (HND)"],
        "Emiratos Árabes": ["Dubái (DXB)"],
        "Tailandia": ["Bangkok (BKK)"],
        "Sudáfrica": ["Ciudad del Cabo (CPT)"],
    },
}

CATALOGO_GLOBAL_MUNDIAL = [
    {"destino":"Roma","pais":"Italia","continente":"Europa","precio_base":34,"duracion":"3 días","dias_num":3,"tipo":"Directo","code":"FCO","rating":9.5,"img":"https://images.unsplash.com/photo-1552832230-c0197dd311b5?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Oporto","pais":"Portugal","continente":"Europa","precio_base":22,"duracion":"3 días","dias_num":3,"tipo":"Directo","code":"OPO","rating":9.2,"img":"https://images.unsplash.com/photo-1555881400-74d7acaacd8b?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Atenas","pais":"Grecia","continente":"Europa","precio_base":48,"duracion":"4 días","dias_num":4,"tipo":"Directo","code":"ATH","rating":9.3,"img":"https://images.unsplash.com/photo-1533105079780-92b9be482077?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Reikiavik","pais":"Islandia","continente":"Europa","precio_base":115,"duracion":"4 días","dias_num":4,"tipo":"Directo","code":"KEF","rating":9.6,"img":"https://images.unsplash.com/photo-1504893524553-b855bce32c67?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Ibiza","pais":"España","continente":"Europa","precio_base":19,"duracion":"3 días","dias_num":3,"tipo":"Directo","code":"IBZ","rating":8.7,"img":"https://images.unsplash.com/photo-1537996194471-e657df975ab4?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Praga","pais":"República Checa","continente":"Europa","precio_base":39,"duracion":"3 días","dias_num":3,"tipo":"Directo","code":"PRG","rating":9.4,"img":"https://images.unsplash.com/photo-1541849546-216549ae216d?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Cancún","pais":"México","continente":"América","precio_base":320,"duracion":"7 días","dias_num":7,"tipo":"1 escala","code":"CUN","rating":8.9,"img":"https://images.unsplash.com/photo-1510097467424-192d713be8b2?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Nueva York","pais":"Estados Unidos","continente":"América","precio_base":280,"duracion":"6 días","dias_num":6,"tipo":"Directo","code":"JFK","rating":9.7,"img":"https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Río de Janeiro","pais":"Brasil","continente":"América","precio_base":490,"duracion":"8 días","dias_num":8,"tipo":"1 escala","code":"GIG","rating":9.0,"img":"https://images.unsplash.com/photo-1483729558449-99ef09a8c325?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Buenos Aires","pais":"Argentina","continente":"América","precio_base":510,"duracion":"9 días","dias_num":9,"tipo":"Directo","code":"EZE","rating":9.2,"img":"https://images.unsplash.com/photo-1589909202802-8f4aadce1849?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Bangkok","pais":"Tailandia","continente":"Asia","precio_base":440,"duracion":"10 días","dias_num":10,"tipo":"1 escala","code":"BKK","rating":9.5,"img":"https://images.unsplash.com/photo-1508009603885-50cf7c579365?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Tokio","pais":"Japón","continente":"Asia","precio_base":540,"duracion":"10 días","dias_num":10,"tipo":"1 escala","code":"HND","rating":9.9,"img":"https://images.unsplash.com/photo-1503899036084-c55cdd92da26?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Dubái","pais":"EAU","continente":"Asia","precio_base":210,"duracion":"4 días","dias_num":4,"tipo":"Directo","code":"DXB","rating":8.8,"img":"https://images.unsplash.com/photo-1512453979798-5ea266f8880c?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Bali","pais":"Indonesia","continente":"Asia","precio_base":495,"duracion":"10 días","dias_num":10,"tipo":"1 escala","code":"DPS","rating":9.6,"img":"https://images.unsplash.com/photo-1537996194471-e657df975ab4?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Majachkalá","pais":"Rusia / Cáucaso","continente":"Cáucaso","precio_base":195,"duracion":"5 días","dias_num":5,"tipo":"1 escala","code":"MCX","rating":8.9,"img":"https://images.unsplash.com/photo-1516483638261-f4dbaf036963?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Ciudad del Cabo","pais":"Sudáfrica","continente":"África","precio_base":460,"duracion":"9 días","dias_num":9,"tipo":"1 escala","code":"CPT","rating":9.4,"img":"https://images.unsplash.com/photo-1580618672591-eb180b1a973f?q=80&w=800&auto=format&fit=crop"},
    {"destino":"El Cairo","pais":"Egipto","continente":"África","precio_base":190,"duracion":"5 días","dias_num":5,"tipo":"Directo","code":"CAI","rating":9.1,"img":"https://images.unsplash.com/photo-1572252009286-268acec5ca0a?q=80&w=800&auto=format&fit=crop"},
    {"destino":"Sídney","pais":"Australia","continente":"Oceanía","precio_base":820,"duracion":"12 días","dias_num":12,"tipo":"2 escalas","code":"SYD","rating":9.3,"img":"https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?q=80&w=800&auto=format&fit=crop"},
]

# -----------------------------------------------------------------------------
# Search helpers
# -----------------------------------------------------------------------------
def get_serpapi_key():
    try:
        return st.secrets.get("SERPAPI_KEY")
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return None


@st.cache_data(ttl=86400, show_spinner=False)
def buscar_aeropuerto_global(query):
    """Resolve a user-entered place with Nominatim; do not invent an IATA code."""
    try:
        response = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json", "addressdetails": 1, "limit": 1},
            headers={"User-Agent": "VagabondGlobalEngine/10.0"},
            timeout=6.0,
        )
        response.raise_for_status()
        results = response.json()
        if not results:
            return None
        address = results[0].get("address", {})
        city = address.get("city") or address.get("town") or address.get("village") or address.get("state") or query
        return {"destino": city, "pais": address.get("country", "Mundo")}
    except (httpx.HTTPError, ValueError, TypeError):
        return None


@st.cache_data(ttl=300, show_spinner=False)
def obtener_tarifa_google_flights(origen, destino, fecha_ida, fecha_vuelta, api_key):
    if not api_key or not re.fullmatch(r"[A-Z]{3}", str(origen)) or not re.fullmatch(r"[A-Z]{3}", str(destino)):
        return None
    try:
        response = httpx.get(
            "https://serpapi.com/search.json",
            params={
                "engine": "google_flights",
                "departure_id": origen,
                "arrival_id": destino,
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


def flight_url(destination, origin, outbound, inbound):
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
                    <div class="card-image-container" style="background-image:url('{html.escape(row['img'], quote=True)}')"></div>
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
# Sidebar filters
# -----------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("### CONFIGURACIÓN DE BÚSQUEDA")
origin_region = st.sidebar.selectbox("Región de salida", list(ORIGENES_GLOBALES))
origin_country = st.sidebar.selectbox("País de salida", list(ORIGENES_GLOBALES[origin_region]))
origin_city = st.sidebar.selectbox("Aeropuerto de salida", ORIGENES_GLOBALES[origin_region][origin_country])
origin_code = origin_city.rsplit("(", 1)[-1].replace(")", "").strip()

st.sidebar.markdown("---")
destination_continent = st.sidebar.selectbox(
    "Filtrar continente de destino",
    ["Todos los continentes", "Europa", "América", "Asia", "África", "Cáucaso", "Oceanía"],
)
duration_filter = st.sidebar.selectbox(
    "Duración del viaje",
    ["Cualquier duración", "Escapada (3-4 días)", "Semana (5-8 días)", "Larga estancia (+8 días)"],
)
search_text = st.sidebar.text_input(
    "Buscar cualquier rincón del planeta:",
    placeholder="Ej: Bora Bora, Katmandú, Reikiavik, Zanzíbar...",
)
only_direct = st.sidebar.checkbox("Mostrar solo vuelos directos", value=False)
budget = st.sidebar.slider("Presupuesto máximo (€)", 10, 4000, 1000, step=50)

# -----------------------------------------------------------------------------
# Header and flight processing
# -----------------------------------------------------------------------------
st.markdown('<div class="brand-header">V A G A B O N D</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="brand-sub">Buscador global conectado con Google Flights desde <b>{html.escape(origin_city)}</b></div>',
    unsafe_allow_html=True,
)
api_key = get_serpapi_key()
if api_key:
    st.markdown('<div class="status-dot"><div class="dot"></div> Feed directo Google Flights activo</div>', unsafe_allow_html=True)
else:
    st.caption("Sin SERPAPI_KEY se muestran precios de referencia; confirma las tarifas en Google Flights.")
st.write("")

outbound_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
return_date = (datetime.now() + timedelta(days=21)).strftime("%Y-%m-%d")
active_catalog = [item.copy() for item in CATALOGO_GLOBAL_MUNDIAL]

if search_text.strip():
    resolved_place = buscar_aeropuerto_global(search_text.strip())
    if resolved_place:
        active_catalog.insert(0, {
            "destino": resolved_place["destino"],
            "pais": resolved_place["pais"],
            "continente": "Personalizado",
            "precio_base": 150,
            "duracion": "Flexible (7 días)",
            "dias_num": 7,
            "tipo": "Consultar disponibilidad",
            "code": "",
            "rating": 9.2,
            "img": "https://images.unsplash.com/photo-1488646953014-85cb44e25828?q=80&w=800&auto=format&fit=crop",
        })
    elif search_text.strip():
        st.warning("No se pudo localizar ese destino. Prueba con otra ciudad, isla o país.")

processed = []
for item in active_catalog:
    live_price = obtener_tarifa_google_flights(
        origin_code, item["code"], outbound_date, return_date, api_key
    )
    price = live_price if live_price is not None else item["precio_base"]
    direct_factor = 1.25 if item["tipo"] == "Directo" else 1.0
    item["precio"] = price
    item["score_cp"] = round((item["rating"] * 10 * direct_factor) / max(price, 1), 3)
    item["url_reserva"] = flight_url(item["destino"], origin_code, outbound_date, return_date)
    processed.append(item)

df = pd.DataFrame(processed)
filtered = df[df["precio"] <= budget].copy()
if destination_continent != "Todos los continentes":
    filtered = filtered[filtered["continente"] == destination_continent]
if duration_filter == "Escapada (3-4 días)":
    filtered = filtered[filtered["dias_num"].between(3, 4)]
elif duration_filter == "Semana (5-8 días)":
    filtered = filtered[filtered["dias_num"].between(5, 8)]
elif duration_filter == "Larga estancia (+8 días)":
    filtered = filtered[filtered["dias_num"] > 8]
if only_direct:
    filtered = filtered[filtered["tipo"].str.contains("Directo", na=False)]
if search_text.strip():
    query = search_text.strip().casefold()
    matches = (
        filtered["destino"].str.casefold().str.contains(query, regex=False, na=False)
        | filtered["pais"].str.casefold().str.contains(query, regex=False, na=False)
    )
    # Keep the geocoded custom destination, rather than filtering it out by its resolved display name.
    if active_catalog and resolved_place:
        matches |= filtered["continente"].eq("Personalizado")
    filtered = filtered[matches]

# -----------------------------------------------------------------------------
# Cheapest and best-value flight recommendations
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title">Los 6 viajes más baratos del mundo</div>', unsafe_allow_html=True)
if not filtered.empty:
    render_cards(filtered.sort_values("precio").head(6))
else:
    st.info("No hay rutas dentro de este presupuesto y filtros. Ajusta las opciones de la barra lateral.")

st.markdown("---")
st.markdown('<div class="section-title">Los 6 mejores en calidad - precio</div>', unsafe_allow_html=True)
if not filtered.empty:
    render_cards(filtered.sort_values("score_cp", ascending=False).head(6), value_badge=True)
else:
    st.info("No se encontraron resultados para calcular la relación calidad-precio.")
