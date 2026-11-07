import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y SELECTOR DE TEMA (CLARO / OSCURO)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Vagabond | Escapadas Globales",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Selector de tema en el sidebar
st.sidebar.markdown("### Apariencia")
tema_elegido = st.sidebar.radio("Modo de pantalla", ["Claro ☀️", "Oscuro 🌙"], index=0)

# -----------------------------------------------------------------------------
# 2. DEFINICIÓN DE ESTILOS CSS SEGÚN TEMA SELECCIONADO
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
    hero_bg = "#1E293B"
    hero_border = "#38BDF8"
    shadow = "rgba(0, 0, 0, 0.4)"
else:
    bg_app = "#F8FAFC"
    bg_sidebar = "#FFFFFF"
    text_main = "#0F172A"
    text_sub = "#475569"
    card_bg = "#FFFFFF"
    card_border = "#E2E8F0"
    btn_bg = "#0F172A"
    btn_text = "#FFFFFF"
    btn_hover = "#047857"
    price_color = "#047857"
    hero_bg = "#FFFFFF"
    hero_border = "#047857"
    shadow = "rgba(0, 0, 0, 0.06)"

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

    .hero-card {{
        background-color: {hero_bg} !important;
        border-radius: 16px;
        border: 2px solid {hero_border};
        padding: 1.5rem;
        box-shadow: 0 8px 30px {shadow};
        margin-bottom: 2rem;
        display: flex;
        gap: 1.5rem;
        align-items: center;
    }}

    .hero-badge {{
        background-color: {hero_border};
        color: {btn_text} !important;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 6px;
        letter-spacing: 1px;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 0.5rem;
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
        height: 190px;
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
        font-size: 1.25rem;
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
# 3. CATÁLOGO GLOBAL Y FOTOGRAFÍAS PAISAJÍSTICAS
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

DATA_DESTINOS = [
    {
        "destino": "Roma", "region": "Capitales Europeas", "pais": "Italia",
        "precio_base": 34, "duracion": "3 días", "dias_num": 3, "lat": 41.9028, "lon": 12.4964, "tipo": "Directo", "code": "FCO",
        "img": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?q=80&w=800&auto=format&fit=crop"
    },
    {
        "destino": "Oporto", "region": "Capitales Europeas", "pais": "Portugal",
        "precio_base": 22, "duracion": "3 días", "dias_num": 3, "lat": 41.1579, "lon": -8.6291, "tipo": "Directo", "code": "OPO",
        "img": "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?q=80&w=800&auto=format&fit=crop"
    },
    {
        "destino": "Cancún", "region": "Caribe & Playas Tropicales", "pais": "México",
        "precio_base": 340, "duracion": "7 días", "dias_num": 7, "lat": 21.1619, "lon": -86.8515, "tipo": "1 escala", "code": "CUN",
        "img": "https://images.unsplash.com/photo-1510097467424-192d713be8b2?q=80&w=800&auto=format&fit=crop"
    },
    {
        "destino": "Majachkalá", "region": "Cáucaso & Daguestán", "pais": "Rusia / Cáucaso",
        "precio_base": 195, "duracion": "5 días", "dias_num": 5, "lat": 42.9849, "lon": 47.5046, "tipo": "1 escala", "code": "MCX",
        "img": "https://images.unsplash.com/photo-1516483638261-f4dbaf036963?q=80&w=800&auto=format&fit=crop"
    },
    {
        "destino": "Bangkok", "region": "Sudeste Asiático", "pais": "Tailandia",
        "precio_base": 460, "duracion": "10 días", "dias_num": 10, "lat": 13.7563, "lon": 100.5018, "tipo": "1 escala", "code": "BKK",
        "img": "https://images.unsplash.com/photo-1508009603885-50cf7c579365?q=80&w=800&auto=format&fit=crop"
    },
    {
        "destino": "Dubái", "region": "Oriente Medio & Desierto", "pais": "EAU",
        "precio_base": 220, "duracion": "4 días", "dias_num": 4, "lat": 25.2048, "lon": 55.2708, "tipo": "Directo", "code": "DXB",
        "img": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?q=80&w=800&auto=format&fit=crop"
    },
    {
        "destino": "Reikiavik", "region": "Nórdicos & Auroras Boreales", "pais": "Islandia",
        "precio_base": 125, "duracion": "4 días", "dias_num": 4, "lat": 64.1466, "lon": -21.9426, "tipo": "Directo", "code": "KEF",
        "img": "https://images.unsplash.com/photo-1504893524553-b855bce32c67?q=80&w=800&auto=format&fit=crop"
    },
    {
        "destino": "Ibiza", "region": "Islas del Mediterráneo", "pais": "España",
        "precio_base": 19, "duracion": "3 días", "dias_num": 3, "lat": 38.9067, "lon": 1.4206, "tipo": "Directo", "code": "IBZ",
        "img": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?q=80&w=800&auto=format&fit=crop"
    }
]

# -----------------------------------------------------------------------------
# 4. MOTOR DE BÚSQUEDA EN TIEMPO REAL CON ENLACES DE RESERVA
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300)
def consultar_vuelos_tiempo_real(origen_code):
    vuelos_procesados = []
    fecha_ida = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    fecha_vuelta = (datetime.now() + timedelta(days=17)).strftime("%Y-%m-%d")

    try:
        from fast_flights import FlightData, Passengers, search_airline

        for item in DATA_DESTINOS:
            item_data = item.copy()
            try:
                res = search_airline(
                    flight_data=[FlightData(date=fecha_ida, from_airport=origen_code, to_airport=item["code"])],
                    trip="one-way",
                    passengers=Passengers(adults=1),
                    currency="EUR"
                )
                if res and res.flights:
                    item_data["precio"] = int(res.flights[0].price)
                else:
                    item_data["precio"] = item["precio_base"]
            except Exception:
                item_data["precio"] = item["precio_base"]

            link_google = f"https://www.google.com/travel/flights?q=Flights%20to%20{urllib.parse.quote(item['destino'])}%20from%20{origen_code}%20on%20{fecha_ida}%20through%20{fecha_vuelta}"
            item_data["url_reserva"] = link_google
            vuelos_procesados.append(item_data)

        return vuelos_procesados

    except Exception:
        for item in DATA_DESTINOS:
            item_data = item.copy()
            item_data["precio"] = item["precio_base"]
            link_google = f"https://www.google.com/travel/flights?q=Flights%20to%20{urllib.parse.quote(item['destino'])}%20from%20{origen_code}%20on%20{fecha_ida}%20through%20{fecha_vuelta}"
            item_data["url_reserva"] = link_google
            vuelos_procesados.append(item_data)

        return vuelos_procesados

# -----------------------------------------------------------------------------
# 5. CONTROLES Y FILTROS EN BARRA LATERAL
# -----------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("### Configuración de búsqueda")

continente = st.sidebar.selectbox("Región de salida", list(ORIGENES_GLOBALES.keys()))
pais = st.sidebar.selectbox("País", list(ORIGENES_GLOBALES[continente].keys()))
ciudad_origen = st.sidebar.selectbox("Aeropuerto", ORIGENES_GLOBALES[continente][pais])

if "(" in ciudad_origen and ")" in ciudad_origen:
    codigo_iata = ciudad_origen.split("(")[-1].replace(")", "").strip()
else:
    codigo_iata = "MAD"

st.sidebar.markdown("---")
region_filtro = st.sidebar.selectbox("Filtro de Destino", REGIONES_DESTINO)

destino_busqueda = ""
if region_filtro == "Búsqueda por destino exacto...":
    destino_busqueda = st.sidebar.text_input("Escribe la ciudad o territorio:", "Daguestán")

# NUEVO FILTRO POR DURACIÓN DEL VIAJE
st.sidebar.markdown("---")
duracion_filtro = st.sidebar.selectbox(
    "Duración del viaje",
    ["Cualquier duración", "Escapada rápida (3-4 días)", "Semana completa (5-8 días)", "Gran viaje (+8 días)"]
)

st.sidebar.markdown("---")
presupuesto_max = st.sidebar.slider("Presupuesto máximo (€)", 10, 1000, 350, step=10)

# -----------------------------------------------------------------------------
# 6. PRESENTACIÓN VISUAL DE RESULTADOS
# -----------------------------------------------------------------------------
st.markdown('<div class="brand-header">V A G A B O N D</div>', unsafe_allow_html=True)
st.markdown(f'<div class="brand-sub">Escapadas seleccionadas en tiempo real desde <b>{ciudad_origen}</b></div>', unsafe_allow_html=True)

st.markdown("""
<div class="live-indicator">
    <div class="dot"></div> Feed de datos actualizado en tiempo real
</div>
""", unsafe_allow_html=True)

st.write("")

vuelos = consultar_vuelos_tiempo_real(codigo_iata)
df = pd.DataFrame(vuelos)

# Filtrado por presupuesto
df_filtrado = df[df["precio"] <= presupuesto_max]

# Filtrado por región / destino exacto
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

# Filtrado por duración
if duracion_filtro == "Escapada rápida (3-4 días)":
    df_filtrado = df_filtrado[df_filtrado["dias_num"].between(3, 4)]
elif duracion_filtro == "Semana completa (5-8 días)":
    df_filtrado = df_filtrado[df_filtrado["dias_num"].between(5, 8)]
elif duracion_filtro == "Gran viaje (+8 días)":
    df_filtrado = df_filtrado[df_filtrado["dias_num"] > 8]

df_filtrado = df_filtrado.sort_values(by="precio")

if not df_filtrado.empty:
    # NUEVA SECCIÓN: OFERTA ESTRELLA DEL DÍA (El vuelo más barato)
    top_deal = df_filtrado.iloc[0]

    st.markdown("### Oferta Estrella del Día")
    col_hero1, col_hero2 = st.columns([1.2, 2])
    with col_hero1:
        st.image(top_deal["img"], use_container_width=True)
    with col_hero2:
        st.markdown(f"""
        <div class="hero-badge">Mejor tarifa en tiempo real</div>
        <h2 style="font-family: 'Cinzel', serif; margin:0;">{top_deal['destino']} ({top_deal['pais']})</h2>
        <p style="color:{text_sub}; margin-top:4px;">Ruta directa/escala desde {ciudad_origen} · {top_deal['duracion']}</p>
        <div style="font-size: 2rem; font-weight: 700; color:{price_color}; margin: 10px 0;">{top_deal['precio']} €</div>
        <a href="{top_deal['url_reserva']}" target="_blank" class="booking-btn" style="max-width: 250px;">RESERVAR MEJOR CHOLLO</a>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Todas las escapadas encontradas")

    cols = st.columns(3)
    for idx, (_, row) in enumerate(df_filtrado.iterrows()):
        col = cols[idx % 3]
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

    st.markdown("---")
    st.markdown("### Cobertura de rutas en mapa")
    st.map(df_filtrado[["lat", "lon"]], zoom=1)
else:
    st.info("No hay rutas disponibles que coincidan exactamente con los filtros seleccionados. Aumenta el margen de presupuesto o cambia la duración en el panel lateral.")
