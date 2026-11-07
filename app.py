import streamlit as st
import pandas as pd
import urllib.parse
import httpx
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y TEMA (CLARO / OSCURO)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Vagabond | Escapadas Globales",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.markdown("### Apariencia")
tema_elegido = st.sidebar.radio("Modo de pantalla", ["Claro ☀️", "Oscuro 🌙"], index=0)

# -----------------------------------------------------------------------------
# 2. DEFINICIÓN DE ESTILOS CSS SEGÚN TEMA
# -----------------------------------------------------------------------------
if tema_elegido == "Oscuro 🌙":
    bg_app = "#0F172A"
    bg_sidebar = "#1E293B"
    text_main = "#F8FAFC"
    text_sub = "#94A3B8"
    card_bg = "#1E293B"
    card_border = "#334155"
    btn_bg = "#38BDF8"
    btn_text = "#0F172A"
    btn_hover = "#0284C7"
    price_color = "#34D399"
    shadow = "rgba(0, 0, 0, 0.4)"
    input_bg = "#334155"
    input_text = "#F8FAFC"
else:
    bg_app = "#F8FAFC"
    bg_sidebar = "#FFFFFF"
    text_main = "#0F172A"
    text_sub = "#475569"
    card_bg = "#FFFFFF"
    card_border = "#CBD5E1"
    btn_bg = "#0F172A"
    btn_text = "#FFFFFF"
    btn_hover = "#047857"
    price_color = "#047857"
    shadow = "rgba(0, 0, 0, 0.06)"
    input_bg = "#FFFFFF"
    input_text = "#0F172A"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=Plus+Jakarta+Sans:wght@300;400;600&display=swap');

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
    
    section[data-testid="stSidebar"] * {{
        color: {text_main} !important;
    }}

    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, input {{
        background-color: {input_bg} !important;
        color: {input_text} !important;
        border: 1px solid {card_border} !important;
        border-radius: 8px !important;
    }}

    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {{
        background-color: {input_bg} !important;
        color: {input_text} !important;
    }}

    li[role="option"] {{
        background-color: {input_bg} !important;
        color: {input_text} !important;
    }}

    li[role="option"]:hover {{
        background-color: {card_border} !important;
    }}

    .brand-header {{
        font-family: 'Cinzel', serif !important;
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: 2px;
        color: {text_main} !important;
        margin-bottom: 0.2rem;
        text-transform: uppercase;
    }}

    .brand-sub {{
        font-size: 0.95rem;
        color: {text_sub} !important;
        margin-bottom: 1.5rem;
        font-weight: 300;
        letter-spacing: 1px;
    }}

    .destination-card {{
        background-color: {card_bg} !important;
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid {card_border};
        box-shadow: 0 4px 20px {shadow};
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 1.8rem;
    }}

    .destination-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 12px 30px {shadow};
    }}

    .card-image-container {{
        width: 100%;
        height: 180px;
        background-size: cover;
        background-position: center;
        position: relative;
    }}

    .card-content {{
        padding: 1.25rem;
        background-color: {card_bg} !important;
    }}

    .card-title {{
        font-family: 'Cinzel', serif !important;
        font-size: 1.2rem;
        font-weight: 700;
        color: {text_main} !important;
        margin: 0;
    }}

    .card-region {{
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: {text_sub} !important;
        font-weight: 600;
        margin-top: 2px;
    }}

    .price-tag {{
        font-size: 1.4rem;
        font-weight: 700;
        color: {price_color} !important;
    }}

    .booking-btn {{
        display: block;
        width: 100%;
        text-align: center;
        background-color: {btn_bg} !important;
        color: {btn_text} !important;
        padding: 0.65rem 1rem;
        border-radius: 8px;
        text-decoration: none !important;
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.5px;
        margin-top: 1rem;
        transition: background-color 0.2s;
    }}

    .booking-btn:hover {{
        background-color: {btn_hover} !important;
    }}

    .live-indicator {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.75rem;
        color: {price_color} !important;
        font-weight: 600;
        letter-spacing: 0.5px;
    }}

    .dot {{
        width: 8px;
        height: 8px;
        background-color: #10B981;
        border-radius: 50%;
    }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. BASE DE DATOS MUNDIAL COMPLETA
# -----------------------------------------------------------------------------
ORIGENES_GLOBALES = {
    "Europa": {
        "España": ["Madrid (MAD)", "Barcelona (BCN)", "Valencia (VLC)", "Málaga (AGP)", "Sevilla (SVQ)"],
        "Francia": ["París (CDG)", "Niza (NCE)", "Marsella (MRS)"],
        "Alemania": ["Fráncfort (FRA)", "Múnich (MUC)", "Berlín (BER)"],
        "Reino Unido": ["Londres (LHR)", "Mánchester (MAN)"],
        "Italia": ["Roma (FCO)", "Milán (MXP)", "Venecia (VCE)"]
    },
    "América": {
        "Estados Unidos": ["Nueva York (JFK)", "Los Ángeles (LAX)", "Miami (MIA)"],
        "México": ["Ciudad de México (MEX)", "Cancún (CUN)"],
        "Colombia": ["Bogotá (BOG)", "Medellín (MDE)"],
        "Argentina": ["Buenos Aires (EZE)"]
    },
    "Asia & Oriente": {
        "Japón": ["Tokio (HND)", "Osaka (KIX)"],
        "Emiratos Árabes": ["Dubái (DXB)"],
        "Tailandia": ["Bangkok (BKK)"]
    }
}

REGIONES_DESTINO = [
    "Cualquier rincón del mundo",
    "Caribe & Playas Tropicales",
    "Cáucaso & Daguestán",
    "Sudeste Asiático",
    "Capitales Europeas",
    "Oriente Medio & Desierto",
    "Nórdicos & Auroras Boreales",
    "Islas del Mediterráneo",
    "Búsqueda por destino exacto..."
]

DATA_DESTINOS_BASE = [
    {"destino": "Roma", "region": "Capitales Europeas", "pais": "Italia", "precio_base": 34, "duracion": "3 días", "dias_num": 3, "lat": 41.9028, "lon": 12.4964, "tipo": "Directo", "code": "FCO", "rating": 9.5, "img": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Oporto", "region": "Capitales Europeas", "pais": "Portugal", "precio_base": 22, "duracion": "3 días", "dias_num": 3, "lat": 41.1579, "lon": -8.6291, "tipo": "Directo", "code": "OPO", "rating": 9.2, "img": "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Cancún", "region": "Caribe & Playas Tropicales", "pais": "México", "precio_base": 340, "duracion": "7 días", "dias_num": 7, "lat": 21.1619, "lon": -86.8515, "tipo": "1 escala", "code": "CUN", "rating": 8.8, "img": "https://images.unsplash.com/photo-1510097467424-192d713be8b2?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Majachkalá", "region": "Cáucaso & Daguestán", "pais": "Rusia / Cáucaso", "precio_base": 195, "duracion": "5 días", "dias_num": 5, "lat": 42.9849, "lon": 47.5046, "tipo": "1 escala", "code": "MCX", "rating": 8.9, "img": "https://images.unsplash.com/photo-1516483638261-f4dbaf036963?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Bangkok", "region": "Sudeste Asiático", "pais": "Tailandia", "precio_base": 460, "duracion": "10 días", "dias_num": 10, "lat": 13.7563, "lon": 100.5018, "tipo": "1 escala", "code": "BKK", "rating": 9.6, "img": "https://images.unsplash.com/photo-1508009603885-50cf7c579365?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Dubái", "region": "Oriente Medio & Desierto", "pais": "EAU", "precio_base": 220, "duracion": "4 días", "dias_num": 4, "lat": 25.2048, "lon": 55.2708, "tipo": "Directo", "code": "DXB", "rating": 8.7, "img": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Reikiavik", "region": "Nórdicos & Auroras Boreales", "pais": "Islandia", "precio_base": 125, "duracion": "4 días", "dias_num": 4, "lat": 64.1466, "lon": -21.9426, "tipo": "Directo", "code": "KEF", "rating": 9.4, "img": "https://images.unsplash.com/photo-1504893524553-b855bce32c67?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Ibiza", "region": "Islas del Mediterráneo", "pais": "España", "precio_base": 19, "duracion": "3 días", "dias_num": 3, "lat": 38.9067, "lon": 1.4206, "tipo": "Directo", "code": "IBZ", "rating": 8.5, "img": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Tokio", "region": "Sudeste Asiático", "pais": "Japón", "precio_base": 580, "duracion": "10 días", "dias_num": 10, "lat": 35.6762, "lon": 139.6503, "tipo": "1 escala", "code": "HND", "rating": 9.8, "img": "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Ciudad del Cabo", "region": "Cualquier rincón del mundo", "pais": "Sudáfrica", "precio_base": 490, "duracion": "9 días", "dias_num": 9, "lat": -33.9249, "lon": 18.4241, "tipo": "1 escala", "code": "CPT", "rating": 9.3, "img": "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Sídney", "region": "Cualquier rincón del mundo", "pais": "Australia", "precio_base": 890, "duracion": "12 días", "dias_num": 12, "lat": -33.8688, "lon": 151.2093, "tipo": "2 escalas", "code": "SYD", "rating": 9.1, "img": "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Río de Janeiro", "region": "Caribe & Playas Tropicales", "pais": "Brasil", "precio_base": 510, "duracion": "8 días", "dias_num": 8, "lat": -22.9068, "lon": -43.1729, "tipo": "1 escala", "code": "GIG", "rating": 8.9, "img": "https://images.unsplash.com/photo-1483729558449-99ef09a8c325?q=80&w=800&auto=format&fit=crop"}
]

# -----------------------------------------------------------------------------
# 4. GEOCODIFICACIÓN & BÚSQUEDA EN TIEMPO REAL
# -----------------------------------------------------------------------------
@st.cache_data(ttl=86400)
def obtener_coordenadas_lugar(nombre_lugar):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(nombre_lugar)}&format=json&limit=1"
        headers = {"User-Agent": "VagabondApp/5.0"}
        response = httpx.get(url, headers=headers, timeout=6.0)
        data = response.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return 20.0, 0.0


def buscar_vuelo_google_flights_real(origen, destino_code):
    serpapi_key = st.secrets.get("SERPAPI_KEY", None)
    if not serpapi_key:
        return None
    
    fecha_ida = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    fecha_vuelta = (datetime.now() + timedelta(days=17)).strftime("%Y-%m-%d")
    
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
        resp = httpx.get(url, params=params, timeout=8.0)
        datos = resp.json()
        if "best_flights" in datos and len(datos["best_flights"]) > 0:
            return datos["best_flights"][0]["price"]
    except Exception:
        pass
    return None

# -----------------------------------------------------------------------------
# 5. CONTROLES DE BARRA LATERAL
# -----------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("### Configuración de búsqueda")

continente = st.sidebar.selectbox("Región de salida", list(ORIGENES_GLOBALES.keys()))
pais = st.sidebar.selectbox("País", list(ORIGENES_GLOBALES[continente].keys()))
ciudad_origen = st.sidebar.selectbox("Aeropuerto", ORIGENES_GLOBALES[continente][pais])

codigo_iata = ciudad_origen.split("(")[-1].replace(")", "").strip() if "(" in ciudad_origen else "MAD"

st.sidebar.markdown("---")
region_filtro = st.sidebar.selectbox("Filtro de Destino", REGIONES_DESTINO)

destino_busqueda = ""
if region_filtro == "Búsqueda por destino exacto...":
    destino_busqueda = st.sidebar.text_input("Escribe cualquier ciudad o territorio mundial:", "Daguestán")

st.sidebar.markdown("---")
duracion_filtro = st.sidebar.selectbox(
    "Duración del viaje",
    ["Cualquier duración", "Escapada rápida (3-4 días)", "Semana completa (5-8 días)", "Gran viaje (+8 días)"]
)

st.sidebar.markdown("---")
presupuesto_max = st.sidebar.slider("Presupuesto máximo (€)", 10, 3000, 650, step=20)

# -----------------------------------------------------------------------------
# 6. PROCESAMIENTO GENERAL
# -----------------------------------------------------------------------------
destinos_a_procesar = DATA_DESTINOS_BASE.copy()

if region_filtro == "Búsqueda por destino exacto..." and destino_busqueda.strip():
    lat_geo, lon_geo = obtener_coordenadas_lugar(destino_busqueda)
    destino_personalizado = {
        "destino": destino_busqueda.capitalize(),
        "region": "Búsqueda Personalizada",
        "pais": "Global",
        "precio_base": 180,
        "duracion": "5 días",
        "dias_num": 5,
        "lat": lat_geo,
        "lon": lon_geo,
        "tipo": "Directo / 1 escala",
        "code": destino_busqueda.upper()[:3],
        "rating": 9.0,
        "img": "https://images.unsplash.com/photo-1488646953014-85cb44e25828?q=80&w=800&auto=format&fit=crop"
    }
    destinos_a_procesar.insert(0, destino_personalizado)

# Header
st.markdown('<div class="brand-header">V A G A B O N D</div>', unsafe_allow_html=True)
st.markdown(f'<div class="brand-sub">Explorador Global de Vuelos desde <b>{ciudad_origen}</b></div>', unsafe_allow_html=True)

if "SERPAPI_KEY" in st.secrets:
    st.markdown('<div class="live-indicator"><div class="dot"></div> Datos en vivo conectados a Google Flights API</div>', unsafe_allow_html=True)

st.write("")

# Calcular precios y ratios de calidad-precio
fecha_ida = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
fecha_vuelta = (datetime.now() + timedelta(days=17)).strftime("%Y-%m-%d")

vuelos_procesados = []
for item in destinos_a_procesar:
    item_copy = item.copy()
    precio_real = buscar_vuelo_google_flights_real(codigo_iata, item["code"])
    precio_final = precio_real if precio_real else item["precio_base"]
    item_copy["precio"] = precio_final
    
    # Algoritmo de Calidad-Precio (Rating sobre precio ajustado por escalas)
    mult_directo = 1.25 if item["tipo"] == "Directo" else 1.0
    item_copy["score_cp"] = round(((item["rating"] * 100) * mult_directo) / precio_final, 2)
    
    item_copy["url_reserva"] = f"https://www.google.com/travel/flights?q=Flights%20to%20{urllib.parse.quote(item['destino'])}%20from%20{codigo_iata}%20on%20{fecha_ida}%20through%20{fecha_vuelta}"
    vuelos_procesados.append(item_copy)

df = pd.DataFrame(vuelos_procesados)

# Aplicar Filtros
df_filtrado = df[df["precio"] <= presupuesto_max]

if region_filtro != "Cualquier rincón del mundo":
    if region_filtro == "Búsqueda por destino exacto...":
        if destino_busqueda:
            df_filtrado = df_filtrado[
                df_filtrado["destino"].str.lower().str.contains(destino_busqueda.lower()) |
                df_filtrado["region"].str.lower().str.contains(destino_busqueda.lower()) |
                df_filtrado["pais"].str.lower().str.contains(destino_busqueda.lower())
            ]
    else:
        df_filtrado = df_filtrado[df_filtrado["region"] == region_filtro]

if duracion_filtro == "Escapada rápida (3-4 días)":
    df_filtrado = df_filtrado[df_filtrado["dias_num"].between(3, 4)]
elif duracion_filtro == "Semana completa (5-8 días)":
    df_filtrado = df_filtrado[df_filtrado["dias_num"].between(5, 8)]
elif duracion_filtro == "Gran viaje (+8 días)":
    df_filtrado = df_filtrado[df_filtrado["dias_num"] > 8]

# -----------------------------------------------------------------------------
# 7. MAPA GLOBAL ESTABLE (ST.MAP)
# -----------------------------------------------------------------------------
st.markdown("### 🗺️ Cobertura Global de Rutas")
if not df_filtrado.empty:
    st.map(df_filtrado[["lat", "lon"]], zoom=1)

st.markdown("---")

# -----------------------------------------------------------------------------
# 8. PANEL 1: LOS 6 VUELOS MÁS BARATOS
# -----------------------------------------------------------------------------
st.markdown("## 📉 Los 6 Vuelos Más Baratos")

if not df_filtrado.empty:
    top_6_baratos = df_filtrado.sort_values(by="precio").head(6)
    cols_baratos = st.columns(3)
    for idx, (_, row) in enumerate(top_6_baratos.iterrows()):
        col = cols_baratos[idx % 3]
        with col:
            st.markdown(f"""
            <div class="destination-card">
                <div class="card-image-container" style="background-image: url('{row['img']}');"></div>
                <div class="card-content">
                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                        <h3 class="card-title">{row['destino']}</h3>
                        <span class="price-tag">{row['precio']} €</span>
                    </div>
                    <div class="card-region">{row['pais']} · {row['duracion']}</div>
                    <div style="font-size: 0.8rem; color: {text_sub} !important; margin-top: 6px;">Vuelo {row['tipo']}</div>
                    <a href="{row['url_reserva']}" target="_blank" class="booking-btn">RESERVAR EN GOOGLE FLIGHTS</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("No hay rutas en este rango de precios.")

st.markdown("---")

# -----------------------------------------------------------------------------
# 9. PANEL 2: LOS 6 MEJORES CALIDAD-PRECIO
# -----------------------------------------------------------------------------
st.markdown("## ✨ Los 6 Mejores en Calidad-Precio")

if not df_filtrado.empty:
    top_6_calidad = df_filtrado.sort_values(by="score_cp", ascending=False).head(6)
    cols_calidad = st.columns(3)
    for idx, (_, row) in enumerate(top_6_calidad.iterrows()):
        col = cols_calidad[idx % 3]
        with col:
            st.markdown(f"""
            <div class="destination-card">
                <div class="card-image-container" style="background-image: url('{row['img']}');"></div>
                <div class="card-content">
                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                        <h3 class="card-title">{row['destino']}</h3>
                        <span class="price-tag">{row['precio']} €</span>
                    </div>
                    <div class="card-region">{row['pais']} · Valoración {row['rating']}/10</div>
                    <div style="font-size: 0.8rem; color: {text_sub} !important; margin-top: 6px;">Vuelo {row['tipo']} ({row['duracion']})</div>
                    <a href="{row['url_reserva']}" target="_blank" class="booking-btn">RESERVAR EN GOOGLE FLIGHTS</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("Ajusta el margen de presupuesto en la barra lateral para calcular ofertas de calidad-precio.")
