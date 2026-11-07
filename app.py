import streamlit as st
import pandas as pd
import urllib.parse
import httpx
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y TEMAS (MINIMALISTA / AESTHETIC)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="VAGABOND | Global Flight Finder",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.markdown("### APARIENCIA")
tema_elegido = st.sidebar.radio("Modo de interfaz", ["Modo Claro", "Modo Oscuro"], index=0)

if tema_elegido == "Modo Oscuro":
    bg_app = "#090D16"
    bg_sidebar = "#111827"
    text_main = "#F1F5F9"
    text_sub = "#94A3B8"
    card_bg = "#111827"
    card_border = "#1E293B"
    btn_bg = "#F1F5F9"
    btn_text = "#090D16"
    btn_hover = "#CBD5E1"
    price_color = "#34D399"
    input_bg = "#1E293B"
    input_text = "#F1F5F9"
    badge_bg = "rgba(52, 211, 153, 0.1)"
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
    price_color = "#047857"
    input_bg = "#FFFFFF"
    input_text = "#0F172A"
    badge_bg = "rgba(4, 120, 87, 0.08)"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap');

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
        border-radius: 6px !important;
    }}

    .brand-header {{
        font-family: 'Cinzel', serif !important;
        font-size: 2.2rem;
        font-weight: 600;
        letter-spacing: 6px;
        color: {text_main} !important;
        margin-bottom: 0.2rem;
        text-transform: uppercase;
    }}

    .brand-sub {{
        font-size: 0.85rem;
        color: {text_sub} !important;
        margin-bottom: 2rem;
        font-weight: 300;
        letter-spacing: 2px;
        text-transform: uppercase;
    }}

    .section-title {{
        font-family: 'Cinzel', serif !important;
        font-size: 1.25rem;
        font-weight: 600;
        letter-spacing: 2px;
        color: {text_main} !important;
        margin-top: 1rem;
        margin-bottom: 1rem;
        text-transform: uppercase;
    }}

    .destination-card {{
        background-color: {card_bg} !important;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid {card_border};
        box-shadow: 0 2px 12px rgba(0,0,0,0.03);
        transition: transform 0.2s ease, border-color 0.2s ease;
        margin-bottom: 1.5rem;
    }}

    .destination-card:hover {{
        transform: translateY(-3px);
        border-color: {text_sub};
    }}

    .card-image-container {{
        width: 100%;
        height: 170px;
        background-size: cover;
        background-position: center;
    }}

    .card-content {{
        padding: 1.2rem;
        background-color: {card_bg} !important;
    }}

    .card-title {{
        font-family: 'Cinzel', serif !important;
        font-size: 1.15rem;
        font-weight: 600;
        color: {text_main} !important;
        margin: 0;
    }}

    .card-region {{
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: {text_sub} !important;
        font-weight: 500;
        margin-top: 4px;
    }}

    .price-tag {{
        font-size: 1.3rem;
        font-weight: 600;
        color: {price_color} !important;
    }}

    .badge-cp {{
        display: inline-block;
        background-color: {badge_bg};
        color: {price_color} !important;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-top: 6px;
    }}

    .booking-btn {{
        display: block;
        width: 100%;
        text-align: center;
        background-color: {btn_bg} !important;
        color: {btn_text} !important;
        padding: 0.6rem 1rem;
        border-radius: 6px;
        text-decoration: none !important;
        font-weight: 500;
        font-size: 0.8rem;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-top: 1rem;
        transition: background-color 0.2s;
    }}

    .booking-btn:hover {{
        background-color: {btn_hover} !important;
    }}

    .status-dot {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 0.75rem;
        color: {text_sub} !important;
        letter-spacing: 1px;
        text-transform: uppercase;
    }}

    .dot {{
        width: 6px;
        height: 6px;
        background-color: {price_color};
        border-radius: 50%;
    }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. BASE DE DATOS GLOBAL DE DESTINOS
# -----------------------------------------------------------------------------
ORIGENES_GLOBALES = {
    "Europa": {
        "España": ["Madrid (MAD)", "Barcelona (BCN)", "Valencia (VLC)", "Málaga (AGP)", "Sevilla (SVQ)"],
        "Francia": ["París (CDG)", "Niza (NCE)"],
        "Alemania": ["Fráncfort (FRA)", "Berlín (BER)"],
        "Reino Unido": ["Londres (LHR)", "Mánchester (MAN)"],
        "Italia": ["Roma (FCO)", "Milán (MXP)"]
    },
    "América": {
        "Estados Unidos": ["Nueva York (JFK)", "Los Ángeles (LAX)", "Miami (MIA)"],
        "México": ["Ciudad de México (MEX)", "Cancún (CUN)"],
        "Colombia": ["Bogotá (BOG)"],
        "Argentina": ["Buenos Aires (EZE)"]
    },
    "Asia & África": {
        "Japón": ["Tokio (HND)"],
        "Emiratos Árabes": ["Dubái (DXB)"],
        "Tailandia": ["Bangkok (BKK)"],
        "Sudáfrica": ["Ciudad del Cabo (CPT)"]
    }
}

CATALOGO_GLOBAL = [
    {"destino": "Roma", "pais": "Italia", "continente": "Europa", "precio_base": 34, "duracion": "3 días", "dias_num": 3, "lat": 41.9028, "lon": 12.4964, "tipo": "Directo", "code": "FCO", "rating": 9.5, "img": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Oporto", "pais": "Portugal", "continente": "Europa", "precio_base": 22, "duracion": "3 días", "dias_num": 3, "lat": 41.1579, "lon": -8.6291, "tipo": "Directo", "code": "OPO", "rating": 9.2, "img": "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Atenas", "pais": "Grecia", "continente": "Europa", "precio_base": 48, "duracion": "4 días", "dias_num": 4, "lat": 37.9838, "lon": 23.7275, "tipo": "Directo", "code": "ATH", "rating": 9.3, "img": "https://images.unsplash.com/photo-1533105079780-92b9be482077?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Reikiavik", "pais": "Islandia", "continente": "Europa", "precio_base": 115, "duracion": "4 días", "dias_num": 4, "lat": 64.1466, "lon": -21.9426, "tipo": "Directo", "code": "KEF", "rating": 9.6, "img": "https://images.unsplash.com/photo-1504893524553-b855bce32c67?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Cancún", "pais": "México", "continente": "América", "precio_base": 320, "duracion": "7 días", "dias_num": 7, "lat": 21.1619, "lon": -86.8515, "tipo": "1 escala", "code": "CUN", "rating": 8.9, "img": "https://images.unsplash.com/photo-1510097467424-192d713be8b2?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Nueva York", "pais": "Estados Unidos", "continente": "América", "precio_base": 280, "duracion": "6 días", "dias_num": 6, "lat": 40.7128, "lon": -74.0060, "tipo": "Directo", "code": "JFK", "rating": 9.7, "img": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Río de Janeiro", "pais": "Brasil", "continente": "América", "precio_base": 490, "duracion": "8 días", "dias_num": 8, "lat": -22.9068, "lon": -43.1729, "tipo": "1 escala", "code": "GIG", "rating": 9.0, "img": "https://images.unsplash.com/photo-1483729558449-99ef09a8c325?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Bangkok", "pais": "Tailandia", "continente": "Asia", "precio_base": 440, "duracion": "10 días", "dias_num": 10, "lat": 13.7563, "lon": 100.5018, "tipo": "1 escala", "code": "BKK", "rating": 9.5, "img": "https://images.unsplash.com/photo-1508009603885-50cf7c579365?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Tokio", "pais": "Japón", "continente": "Asia", "precio_base": 540, "duracion": "10 días", "dias_num": 10, "lat": 35.6762, "lon": 139.6503, "tipo": "1 escala", "code": "HND", "rating": 9.9, "img": "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Dubái", "pais": "EAU", "continente": "Asia", "precio_base": 210, "duracion": "4 días", "dias_num": 4, "lat": 25.2048, "lon": 55.2708, "tipo": "Directo", "code": "DXB", "rating": 8.8, "img": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Ciudad del Cabo", "pais": "Sudáfrica", "continente": "África", "precio_base": 460, "duracion": "9 días", "dias_num": 9, "lat": -33.9249, "lon": 18.4241, "tipo": "1 escala", "code": "CPT", "rating": 9.4, "img": "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?q=80&w=800&auto=format&fit=crop"},
    {"destino": "El Cairo", "pais": "Egipto", "continente": "África", "precio_base": 190, "duracion": "5 días", "dias_num": 5, "lat": 30.0444, "lon": 31.2357, "tipo": "Directo", "code": "CAI", "rating": 9.1, "img": "https://images.unsplash.com/photo-1572252009286-268acec5ca0a?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Sídney", "pais": "Australia", "continente": "Oceanía", "precio_base": 820, "duracion": "12 días", "dias_num": 12, "lat": -33.8688, "lon": 151.2093, "tipo": "2 escalas", "code": "SYD", "rating": 9.3, "img": "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?q=80&w=800&auto=format&fit=crop"}
]

# -----------------------------------------------------------------------------
# 3. MOTOR DE BÚSQUEDA EN TIEMPO REAL CON SERPAPI / FALLBACK
# -----------------------------------------------------------------------------
@st.cache_data(ttl=86400)
def obtener_coordenadas_lugar(nombre_lugar):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(nombre_lugar)}&format=json&limit=1"
        headers = {"User-Agent": "VagabondAppAesthetic/7.0"}
        response = httpx.get(url, headers=headers, timeout=5.0)
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
# 4. BARRA LATERAL (FILTROS INDEPENDIENTES)
# -----------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("### CONFIGURACIÓN")

continente_salida = st.sidebar.selectbox("Región de salida", list(ORIGENES_GLOBALES.keys()))
pais_salida = st.sidebar.selectbox("País de salida", list(ORIGENES_GLOBALES[continente_salida].keys()))
ciudad_origen = st.sidebar.selectbox("Aeropuerto de salida", ORIGENES_GLOBALES[continente_salida][pais_salida])

codigo_iata = ciudad_origen.split("(")[-1].replace(")", "").strip() if "(" in ciudad_origen else "MAD"

st.sidebar.markdown("---")
filtro_continente = st.sidebar.selectbox("Filtrar continente de destino", ["Todos los continentes", "Europa", "América", "Asia", "África", "Oceanía"])

duracion_filtro = st.sidebar.selectbox(
    "Duración del viaje",
    ["Cualquier duración", "Escapada (3-4 días)", "Semana (5-8 días)", "Larga estancia (+8 días)"]
)

st.sidebar.markdown("---")
presupuesto_max = st.sidebar.slider("Presupuesto máximo (€)", 10, 2000, 750, step=20)

# -----------------------------------------------------------------------------
# 5. HEADER PRINCIPAL
# -----------------------------------------------------------------------------
st.markdown('<div class="brand-header">V A G A B O N D</div>', unsafe_allow_html=True)
st.markdown(f'<div class="brand-sub">Curaduría global de vuelos en tiempo real desde {ciudad_origen}</div>', unsafe_allow_html=True)

if "SERPAPI_KEY" in st.secrets:
    st.markdown('<div class="status-dot"><div class="dot"></div> Feed directo Google Flights activo</div>', unsafe_allow_html=True)

st.write("")

# -----------------------------------------------------------------------------
# 6. PROCESAMIENTO GLOBAL DE DATOS
# -----------------------------------------------------------------------------
fecha_ida = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
fecha_vuelta = (datetime.now() + timedelta(days=17)).strftime("%Y-%m-%d")

vuelos_procesados = []
for item in CATALOGO_GLOBAL:
    item_copy = item.copy()
    precio_real = buscar_vuelo_google_flights_real(codigo_iata, item["code"])
    precio_final = precio_real if precio_real else item["precio_base"]
    item_copy["precio"] = precio_final
    
    # Scoring Calidad-Precio (Rating ponderado por tipo de vuelo sobre tarifa)
    factor_directo = 1.2 if item["tipo"] == "Directo" else 1.0
    item_copy["score_cp"] = round(((item["rating"] * 10) * factor_directo) / precio_final, 3)
    
    item_copy["url_reserva"] = f"https://www.google.com/travel/flights?q=Flights%20to%20{urllib.parse.quote(item['destino'])}%20from%20{codigo_iata}%20on%20{fecha_ida}%20through%20{fecha_vuelta}"
    vuelos_procesados.append(item_copy)

df = pd.DataFrame(vuelos_procesados)

# Aplicar filtros globales
df_filtrado = df[df["precio"] <= presupuesto_max]

if filtro_continente != "Todos los continentes":
    df_filtrado = df_filtrado[df_filtrado["continente"] == filtro_continente]

if duracion_filtro == "Escapada (3-4 días)":
    df_filtrado = df_filtrado[df_filtrado["dias_num"].between(3, 4)]
elif duracion_filtro == "Semana (5-8 días)":
    df_filtrado = df_filtrado[df_filtrado["dias_num"].between(5, 8)]
elif duracion_filtro == "Larga estancia (+8 días)":
    df_filtrado = df_filtrado[df_filtrado["dias_num"] > 8]

# -----------------------------------------------------------------------------
# 7. SECCIÓN 1: LOS 6 VIAJES MÁS BARATOS
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title">Los 6 viajes más baratos</div>', unsafe_allow_html=True)

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
                    <div style="font-size: 0.75rem; color: {text_sub} !important; margin-top: 6px;">Vuelo {row['tipo']}</div>
                    <a href="{row['url_reserva']}" target="_blank" class="booking-btn">Reservar en Google Flights</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("No hay destinos disponibles dentro del presupuesto asignado. Ajusta el límite en el panel lateral.")

st.markdown("---")

# -----------------------------------------------------------------------------
# 8. SECCIÓN 2: LOS 6 MEJORES CALIDAD-PRECIO
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title">Los 6 mejores en calidad - precio</div>', unsafe_allow_html=True)

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
                    <div class="card-region">{row['pais']} · Valoración {row['rating']:.1f}/10</div>
                    <div class="badge-cp">Ratio Óptimo</div>
                    <a href="{row['url_reserva']}" target="_blank" class="booking-btn">Reservar en Google Flights</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("No hay rutas disponibles para calcular la relación calidad-precio.")

st.markdown("---")

# -----------------------------------------------------------------------------
# 9. SECCIÓN COMPLEMENTARIA: MAPA MUNDIAL DE COBERTURA (SECUNDARIO)
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title">Distribución geográfica de opciones</div>', unsafe_allow_html=True)
st.caption("Vista de cobertura de las rutas encontradas en el catálogo actual.")

if not df_filtrado.empty:
    st.map(df_filtrado[["lat", "lon"]], zoom=1)
