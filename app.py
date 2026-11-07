import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y TIPOGRAFÍAS ELEGANTES
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Vagabond | Escapadas Globales",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de fuentes tipográficas y diseño sobrio mediante CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=Plus+Jakarta+Sans:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #1E293B;
    }

    .brand-header {
        font-family: 'Cinzel', serif;
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: 2px;
        color: #0F172A;
        margin-bottom: 0.2rem;
        text-transform: uppercase;
    }

    .brand-sub {
        font-size: 0.95rem;
        color: #64748B;
        margin-bottom: 2rem;
        font-weight: 300;
        letter-spacing: 1px;
    }

    .destination-card {
        background-color: #FFFFFF;
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 1.8rem;
    }

    .destination-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.08);
    }

    .card-image-container {
        width: 100%;
        height: 190px;
        background-size: cover;
        background-position: center;
        position: relative;
    }

    .card-content {
        padding: 1.25rem;
    }

    .card-title {
        font-family: 'Cinzel', serif;
        font-size: 1.25rem;
        font-weight: 700;
        color: #0F172A;
        margin: 0;
    }

    .card-region {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #64748B;
        font-weight: 600;
        margin-top: 2px;
    }

    .price-tag {
        font-size: 1.4rem;
        font-weight: 700;
        color: #047857;
    }

    .booking-btn {
        display: block;
        width: 100%;
        text-align: center;
        background-color: #0F172A;
        color: #FFFFFF !important;
        padding: 0.65rem 1rem;
        border-radius: 8px;
        text-decoration: none !important;
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.5px;
        margin-top: 1rem;
        transition: background-color 0.2s;
    }

    .booking-btn:hover {
        background-color: #047857;
    }

    .live-indicator {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.75rem;
        color: #047857;
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    .dot {
        width: 8px;
        height: 8px;
        background-color: #10B981;
        border-radius: 50%;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. CATÁLOGO GLOBAL Y FOTOGRAFÍAS PAISAJÍSTICAS DE ALTA RESOLUCIÓN
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
        "precio_base": 34, "duracion": "3 días", "lat": 41.9028, "lon": 12.4964, "tipo": "Directo", "code": "FCO",
        "img": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?q=80&w=800&auto=format&fit=crop"
    },
    {
        "destino": "Oporto", "region": "Capitales Europeas", "pais": "Portugal",
        "precio_base": 22, "duracion": "3 días", "lat": 41.1579, "lon": -8.6291, "tipo": "Directo", "code": "OPO",
        "img": "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?q=80&w=800&auto=format&fit=crop"
    },
    {
        "destino": "Cancún", "region": "Caribe & Playas Tropicales", "pais": "México",
        "precio_base": 340, "duracion": "7 días", "lat": 21.1619, "lon": -86.8515, "tipo": "1 escala", "code": "CUN",
        "img": "https://images.unsplash.com/photo-1510097467424-192d713be8b2?q=80&w=800&auto=format&fit=crop"
    },
    {
        "destino": "Majachkalá", "region": "Cáucaso & Daguestán", "pais": "Rusia / Cáucaso",
        "precio_base": 195, "duracion": "5 días", "lat": 42.9849, "lon": 47.5046, "tipo": "1 escala", "code": "MCX",
        "img": "https://images.unsplash.com/photo-1516483638261-f4dbaf036963?q=80&w=800&auto=format&fit=crop"
    },
    {
        "destino": "Bangkok", "region": "Sudeste Asiático", "pais": "Tailandia",
        "precio_base": 460, "duracion": "10 días", "lat": 13.7563, "lon": 100.5018, "tipo": "1 escala", "code": "BKK",
        "img": "https://images.unsplash.com/photo-1508009603885-50cf7c579365?q=80&w=800&auto=format&fit=crop"
    },
    {
        "destino": "Dubái", "region": "Oriente Medio & Desierto", "pais": "EAU",
        "precio_base": 220, "duracion": "4 días", "lat": 25.2048, "lon": 55.2708, "tipo": "Directo", "code": "DXB",
        "img": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?q=80&w=800&auto=format&fit=crop"
    },
    {
        "destino": "Reikiavik", "region": "Nórdicos & Auroras Boreales", "pais": "Islandia",
        "precio_base": 125, "duracion": "4 días", "lat": 64.1466, "lon": -21.9426, "tipo": "Directo", "code": "KEF",
        "img": "https://images.unsplash.com/photo-1504893524553-b855bce32c67?q=80&w=800&auto=format&fit=crop"
    },
    {
        "destino": "Ibiza", "region": "Islas del Mediterráneo", "pais": "España",
        "precio_base": 19, "duracion": "3 días", "lat": 38.9067, "lon": 1.4206, "tipo": "Directo", "code": "IBZ",
        "img": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?q=80&w=800&auto=format&fit=crop"
    }
]

# -----------------------------------------------------------------------------
# 3. MOTOR DE BÚSQUEDA CON ENLACES DE RESERVA
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300)
def consultar_vuelos_tiempo_real(origen_code):
    """Consulta precios con fast-flights cuando está disponible.

    Los precios de catálogo se usan como fallback y no son cotizaciones reales.
    """
    vuelos_procesados = []
    fecha_ida = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    fecha_vuelta = (datetime.now() + timedelta(days=17)).strftime("%Y-%m-%d")

    try:
        from fast_flights import FlightQuery, Passengers, create_query, get_flights

        for item in DATA_DESTINOS:
            item_data = item.copy()
            try:
                query = create_query(
                    flights=[FlightQuery(
                        date=fecha_ida,
                        from_airport=origen_code,
                        to_airport=item["code"],
                    )],
                    seat="economy",
                    trip="one-way",
                    passengers=Passengers(adults=1),
                    currency="EUR",
                )
                result = get_flights(query)
                found_flights = getattr(result, "flights", [])
                if found_flights:
                    item_data["precio"] = int(found_flights[0].price)
                    item_data["fuente_precio"] = "fast-flights / Google Flights"
                else:
                    item_data["precio"] = item["precio_base"]
                    item_data["fuente_precio"] = "Precio de referencia (no cotización)"
            except Exception:
                item_data["precio"] = item["precio_base"]
                item_data["fuente_precio"] = "Precio de referencia (no cotización)"

            query_text = (
                f"Flights to {item['destino']} from {origen_code} "
                f"on {fecha_ida} through {fecha_vuelta}"
            )
            item_data["url_reserva"] = (
                "https://www.google.com/travel/flights?q="
                + urllib.parse.quote(query_text)
            )
            vuelos_procesados.append(item_data)

    except (ImportError, Exception):
        for item in DATA_DESTINOS:
            item_data = item.copy()
            item_data["precio"] = item["precio_base"]
            item_data["fuente_precio"] = "Precio de referencia (no cotización)"
            query_text = (
                f"Flights to {item['destino']} from {origen_code} "
                f"on {fecha_ida} through {fecha_vuelta}"
            )
            item_data["url_reserva"] = (
                "https://www.google.com/travel/flights?q="
                + urllib.parse.quote(query_text)
            )
            vuelos_procesados.append(item_data)

    return vuelos_procesados

# -----------------------------------------------------------------------------
# 4. CONTROLES Y FILTROS
# -----------------------------------------------------------------------------
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

st.sidebar.markdown("---")
presupuesto_max = st.sidebar.slider("Presupuesto máximo (€)", 10, 1000, 350, step=10)

# -----------------------------------------------------------------------------
# 5. PRESENTACIÓN VISUAL
# -----------------------------------------------------------------------------
st.markdown('<div class="brand-header">V A G A B O N D</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="brand-sub">Escapadas seleccionadas desde <b>{ciudad_origen}</b></div>',
    unsafe_allow_html=True,
)

st.markdown("""
<div class="live-indicator">
    <div class="dot"></div> Consulta de precios; pueden ser estimados y deben confirmarse con el proveedor
</div>
""", unsafe_allow_html=True)
st.write("")

vuelos = consultar_vuelos_tiempo_real(codigo_iata)
df = pd.DataFrame(vuelos)
df_filtrado = df[df["precio"] <= presupuesto_max].copy()

if region_filtro != "Cualquier rincón del mundo":
    if region_filtro == "Búsqueda por destino exacto...":
        if destino_busqueda:
            consulta = destino_busqueda.strip().lower()
            df_filtrado = df_filtrado[
                df_filtrado["destino"].str.lower().str.contains(consulta, na=False)
                | df_filtrado["region"].str.lower().str.contains(consulta, na=False)
                | df_filtrado["pais"].str.lower().str.contains(consulta, na=False)
            ]
    else:
        df_filtrado = df_filtrado[df_filtrado["region"] == region_filtro]

df_filtrado = df_filtrado.sort_values(by="precio")

# Grid visual de 3 columnas
if not df_filtrado.empty:
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
                    <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 6px;">Vuelo {row['tipo']}</div>
                    <div style="font-size: 0.75rem; color: #64748B; margin-top: 6px;">{row['fuente_precio']}</div>
                    <a href="{row['url_reserva']}" target="_blank" class="booking-btn">CONSULTAR EN GOOGLE FLIGHTS</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Cobertura de rutas en mapa")
    st.map(df_filtrado[["lat", "lon"]], zoom=1)
else:
    st.info("No hay rutas disponibles que coincidan exactamente con el presupuesto fijado. Aumenta el margen en el panel lateral.")
