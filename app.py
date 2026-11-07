import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y ELEGANCIA VISUAL
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Vagabond | Escapadas Globales",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS visual premium
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
        color: #0f172a;
    }

    .brand-header {
        font-family: 'Cinzel', serif;
        font-size: 2.6rem;
        letter-spacing: 0.16em;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.2rem;
        text-transform: uppercase;
    }

    .brand-sub {
        font-size: 0.9rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #64748b;
        margin-bottom: 2rem;
    }

    .destination-card {
        background: rgba(255,255,255,0.92);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 18px;
        overflow: hidden;
        box-shadow: 0 20px 40px rgba(15, 23, 42, 0.06);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 1.5rem;
    }

    .destination-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 24px 50px rgba(15, 23, 42, 0.12);
    }

    .card-image {
        height: 200px;
        background-size: cover;
        background-position: center;
    }

    .card-body {
        padding: 1.1rem 1rem 1.2rem;
    }

    .card-title {
        font-family: 'Cinzel', serif;
        font-size: 1.35rem;
        margin: 0;
        color: #0f172a;
    }

    .card-meta {
        font-size: 0.75rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #64748b;
        margin-top: 0.35rem;
        margin-bottom: 0.9rem;
    }

    .price-tag {
        font-size: 1.7rem;
        font-weight: 700;
        color: #047857;
    }

    .pill {
        font-size: 0.7rem;
        font-weight: 600;
        background: #ecfeff;
        color: #0f766e;
        border-radius: 999px;
        padding: 0.35rem 0.6rem;
        display: inline-block;
        margin-top: 0.5rem;
    }

    .booking-btn {
        display: block;
        text-align: center;
        background: #111827;
        color: white !important;
        text-decoration: none !important;
        border-radius: 10px;
        padding: 0.7rem 1rem;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-top: 1rem;
    }

    .booking-btn:hover {
        background: #047857;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. ORÍGENES Y DESTINOS GLOBALIZADOS
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
    """Consulta precios con fast-flights si está disponible. Si no, usa precios de referencia."""
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
                    item_data["fuente_precio"] = "Precio de referencia"
            except Exception:
                item_data["precio"] = item["precio_base"]
                item_data["fuente_precio"] = "Precio de referencia"

            query_text = f"Flights to {item['destino']} from {origen_code} on {fecha_ida} through {fecha_vuelta}"
            item_data["url_reserva"] = "https://www.google.com/travel/flights?q=" + urllib.parse.quote(query_text)
            vuelos_procesados.append(item_data)

    except Exception:
        for item in DATA_DESTINOS:
            item_data = item.copy()
            item_data["precio"] = item["precio_base"]
            item_data["fuente_precio"] = "Precio de referencia"
            query_text = f"Flights to {item['destino']} from {origen_code} on {fecha_ida} through {fecha_vuelta}"
            item_data["url_reserva"] = "https://www.google.com/travel/flights?q=" + urllib.parse.quote(query_text)
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
st.markdown(f'<div class="brand-sub">Escapadas seleccionadas desde <b>{ciudad_origen}</b></div>', unsafe_allow_html=True)

st.markdown("""
<div class="pill">Consulta de precios • puede requerir confirmación con el proveedor</div>
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

# Visual cards
if not df_filtrado.empty:
    cols = st.columns(3)
    for idx, (_, row) in enumerate(df_filtrado.iterrows()):
        col = cols[idx % 3]
        with col:
            st.markdown(f"""
            <div class="destination-card">
                <div class="card-image" style="background-image: url('{row['img']}');"></div>
                <div class="card-body">
                    <div style="display: flex; justify-content: space-between; align-items: baseline; gap: 12px;">
                        <h3 class="card-title">{row['destino']}</h3>
                        <span class="price-tag">{row['precio']} €</span>
                    </div>
                    <div class="card-meta">{row['pais']} · {row['duracion']}</div>
                    <div style="font-size: 0.8rem; color: #64748b;">Vuelo {row['tipo']}</div>
                    <div class="pill">{row['fuente_precio']}</div>
                    <a href="{row['url_reserva']}" target="_blank" class="booking-btn">Consultar vuelo</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Cobertura de rutas")
    st.map(df_filtrado[["lat", "lon"]], zoom=1)
else:
    st.info("No hay rutas disponibles que coincidan con este presupuesto. Intenta subir el límite en el panel lateral.")
