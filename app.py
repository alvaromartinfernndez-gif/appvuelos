import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

try:
    from fast_flights import FlightQuery, Passengers, create_query, get_flights
except ImportError:
    FlightQuery = None
    Passengers = None
    create_query = None
    get_flights = None

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE LA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Global Flight Escape | Buscador de Escapadas",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para una interfaz moderna
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .card-dest {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .badge-price {
        background-color: #059669;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 1.1rem;
    }
    .badge-status {
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. BASE DE DATOS MUNDIAL DE ORIGENES Y REGIONES DE DESTINO
# -----------------------------------------------------------------------------
ORIGENES_GLOBALL = {
    "Europa 🇪🇺": {
        "España": ["Madrid (MAD)", "Barcelona (BCN)", "Valencia (VLC)", "Málaga (AGP)", "Sevilla (SVQ)", "Bilbao (BIO)"],
        "Francia": ["París (CDG)", "Niza (NCE)", "Lyon (LYS)", "Marsella (MRS)"],
        "Alemania": ["Fráncfort (FRA)", "Múnich (MUC)", "Berlín (BER)"],
        "Reino Unido": ["Londres (LHR)", "Mánchester (MAN)", "Edimburgo (EDI)"],
        "Italia": ["Roma (FCO)", "Milán (MXP)", "Venecia (VCE)"],
    },
    "América del Norte 🌎": {
        "Estados Unidos": ["Nueva York (JFK)", "Los Ángeles (LAX)", "Miami (MIA)", "Chicago (ORD)"],
        "México": ["Ciudad de México (MEX)", "Cancún (CUN)", "Guadalajara (GDL)"],
        "Canadá": ["Toronto (YYZ)", "Vancouver (YVR)", "Montreal (YUL)"]
    },
    "América del Sur 🌎": {
        "Colombia": ["Bogotá (BOG)", "Medellín (MDE)", "Cartagena (CTG)"],
        "Argentina": ["Buenos Aires (EZE)", "Mendoza (MDZ)", "Córdoba (COR)"],
        "Brasil": ["São Paulo (GRU)", "Río de Janeiro (GIG)"],
        "Chile": ["Santiago (SCL)"],
        "Perú": ["Lima (LIM)"]
    },
    "Asia y Cáucaso 🌏": {
        "Japón": ["Tokio (HND)", "Osaka (KIX)"],
        "Rusia / Cáucaso": ["Moscú (SVO)", "Majachkalá / Daguestán (MCX)", "Sochi (AER)"],
        "Tailandia": ["Bangkok (BKK)", "Phuket (HKT)"],
        "EAU": ["Dubái (DXB)", "Abu Dabi (AUH)"]
    }
}

REGIONES_DESTINO = [
    "🔥 Ver todo (Cualquier rincón del planeta)",
    "🏝️ El Caribe (Cancún, Punta Cana, La Habana, San Andrés...)",
    "⛰️ Daguestán y Cáucaso (Majachkalá, Derbent, Tblisi...)",
    "🌴 Sudeste Asiático (Bangkok, Bali, Phuket, Vietnam...)",
    "🏰 Europa de Escapada (Roma, París, Londres, Oporto...)",
    "🏜️ Medio Oriente y Desiertos (Dubái, Petra, El Cairo...)",
    "❄️ Nórdicos y Auroras (Reikiavik, Oslo, Rovaniemi...)",
    "🏖️ Islas Mediterráneas (Ibiza, Mikonos, Cerdeña, Malta...)",
    "🌺 Polinesia e Islas del Pacífico (Fiyi, Tahití...)",
    "🔍 Buscar destino / ciudad específica..."
]

DATA_BASE_DESTINOS = [
    {"destino": "Roma", "region": "🏰 Europa de Escapada", "pais": "Italia", "precio_base": 35, "duracion": "3 días", "lat": 41.9028, "lon": 12.4964, "tipo": "Directo", "code": "FCO"},
    {"destino": "Oporto", "region": "🏰 Europa de Escapada", "pais": "Portugal", "precio_base": 24, "duracion": "3 días", "lat": 41.1579, "lon": -8.6291, "tipo": "Directo", "code": "OPO"},
    {"destino": "Cancún / El Caribe", "region": "🏝️ El Caribe (Cancún, Punta Cana, La Habana, San Andrés...)", "pais": "México", "precio_base": 320, "duracion": "7 días", "lat": 21.1619, "lon": -86.8515, "tipo": "1 Escala", "code": "CUN"},
    {"destino": "Punta Cana / El Caribe", "region": "🏝️ El Caribe (Cancún, Punta Cana, La Habana, San Andrés...)", "pais": "Rep. Dominicana", "precio_base": 380, "duracion": "8 días", "lat": 18.5601, "lon": -68.3725, "tipo": "1 Escala", "code": "PUJ"},
    {"destino": "Majachkalá / Daguestán", "region": "⛰️ Daguestán y Cáucaso (Majachkalá, Derbent, Tblisi...)", "pais": "Rusia", "precio_base": 190, "duracion": "5 días", "lat": 42.9849, "lon": 47.5046, "tipo": "1 Escala", "code": "MCX"},
    {"destino": "Derbent / Daguestán", "region": "⛰️ Daguestán y Cáucaso (Majachkalá, Derbent, Tblisi...)", "pais": "Rusia", "precio_base": 210, "duracion": "6 días", "lat": 42.0678, "lon": 48.2899, "tipo": "1 Escala", "code": "MCX"},
    {"destino": "Bangkok", "region": "🌴 Sudeste Asiático (Bangkok, Bali, Phuket, Vietnam...)", "pais": "Tailandia", "precio_base": 450, "duracion": "10 días", "lat": 13.7563, "lon": 100.5018, "tipo": "1 Escala", "code": "BKK"},
    {"destino": "Bali", "region": "🌴 Sudeste Asiático (Bangkok, Bali, Phuket, Vietnam...)", "pais": "Indonesia", "precio_base": 520, "duracion": "12 días", "lat": -8.4095, "lon": 115.1889, "tipo": "1 Escala", "code": "DPS"},
    {"destino": "Dubái", "region": "🏜️ Medio Oriente y Desiertos (Dubái, Petra, El Cairo...)", "pais": "EAU", "precio_base": 210, "duracion": "4 días", "lat": 25.2048, "lon": 55.2708, "tipo": "Directo", "code": "DXB"},
    {"destino": "Reikiavik", "region": "❄️ Nórdicos y Auroras (Reikiavik, Oslo, Rovaniemi...)", "pais": "Islandia", "precio_base": 115, "duracion": "4 días", "lat": 64.1466, "lon": -21.9426, "tipo": "Directo", "code": "KEF"},
    {"destino": "Ibiza", "region": "🏖️ Islas Mediterráneas (Ibiza, Mikonos, Cerdeña, Malta...)", "pais": "España", "precio_base": 18, "duracion": "3 días", "lat": 38.9067, "lon": 1.4206, "tipo": "Directo", "code": "IBZ"},
    {"destino": "Bora Bora", "region": "🌺 Polinesia e Islas del Pacífico (Fiyi, Tahití...)", "pais": "Polinesia Fr.", "precio_base": 980, "duracion": "10 días", "lat": -16.5004, "lon": -151.7415, "tipo": "2 Escalas", "code": "BOB"}
]

# -----------------------------------------------------------------------------
# 3. MOTOR DE BÚSQUEDA DUAL (fast-flights + fallback)
# -----------------------------------------------------------------------------
def extract_price(raw_result):
    """Extrae el precio de una respuesta de fast-flights o de un dict."""
    if raw_result is None:
        return None

    if isinstance(raw_result, dict):
        if "price" in raw_result:
            return raw_result["price"]
        if "price_amount" in raw_result:
            return raw_result["price_amount"]
        if "total" in raw_result:
            return raw_result["total"]
        if "amount" in raw_result:
            return raw_result["amount"]
        return None

    if hasattr(raw_result, "price"):
        return raw_result.price

    if hasattr(raw_result, "amount"):
        return raw_result.amount

    if isinstance(raw_result, (list, tuple)) and raw_result:
        return extract_price(raw_result[0])

    return None


def obtener_vuelos_tiempo_real(origen_code):
    """
    Intenta obtener vuelos con fast-flights usando la API oficial.
    Si falla, usa una estimación de demostración.
    """
    vuelos_resultado = []
    fecha_proxima = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

    if FlightQuery is not None and create_query is not None and get_flights is not None:
        try:
            for item in DATA_BASE_DESTINOS[:6]:
                query = create_query(
                    flights=[
                        FlightQuery(
                            date=fecha_proxima,
                            from_airport=origen_code,
                            to_airport=item["code"],
                        )
                    ],
                    seat="economy",
                    trip="one-way",
                    passengers=Passengers(adults=1),
                    language="en-US",
                    currency="EUR",
                )

                raw = get_flights(query)
                resultados = []

                if hasattr(raw, "flights"):
                    resultados = raw.flights
                elif isinstance(raw, dict) and "flights" in raw:
                    resultados = raw["flights"]
                elif isinstance(raw, list):
                    resultados = raw

                if resultados:
                    precio = extract_price(resultados[0])
                    if precio is not None:
                        item_copy = item.copy()
                        item_copy["precio"] = int(precio)
                        item_copy["proveedor"] = "fast-flights (Google Flights)"
                        vuelos_resultado.append(item_copy)
                        continue

                item_copy = item.copy()
                item_copy["precio"] = max(15, int(item["precio_base"]))
                item_copy["proveedor"] = "fast-flights (sin datos reales)"
                vuelos_resultado.append(item_copy)

            if vuelos_resultado:
                return vuelos_resultado, "🟢 fast-flights activo"

        except Exception:
            pass

    # Fallback seguro
    for item in DATA_BASE_DESTINOS:
        item_copy = item.copy()
        variacion = random.randint(-8, 12)
        item_copy["precio"] = max(15, item_copy["precio_base"] + variacion)
        item_copy["proveedor"] = "Fallback de demostración"
        vuelos_resultado.append(item_copy)

    return vuelos_resultado, "🟡 Datos de demostración activos" 

# -----------------------------------------------------------------------------
# 4. BARRA LATERAL (FILTROS DE ORIGEN Y DESTINO GLOBAL)
# -----------------------------------------------------------------------------
st.sidebar.title("✈️ Configura tu Viaje")

st.sidebar.subheader("1. Origen (Cualquier lugar)")
continente_sel = st.sidebar.selectbox("Continente de salida:", list(ORIGENES_GLOBALL.keys()))
pais_sel = st.sidebar.selectbox("País de salida:", list(ORIGENES_GLOBALL[continente_sel].keys()))
ciudad_origen_sel = st.sidebar.selectbox("Aeropuerto / Ciudad de origen:", ORIGENES_GLOBALL[continente_sel][pais_sel])

origen_manual = st.sidebar.checkbox("¿No está tu ciudad? Escribir origen manual")
if origen_manual:
    ciudad_origen_final = st.sidebar.text_input("Escribe tu ciudad u origen:", "Málaga (AGP)")
else:
    ciudad_origen_final = ciudad_origen_sel

if "(" in ciudad_origen_final and ")" in ciudad_origen_final:
    codigo_origen_iata = ciudad_origen_final.split("(")[-1].replace(")", "").strip()
else:
    codigo_origen_iata = "MAD"

st.sidebar.markdown("---")
st.sidebar.subheader("2. Destino o Región Específica")
region_seleccionada = st.sidebar.selectbox("Selecciona región objetivo:", REGIONES_DESTINO)

destino_especifico_texto = ""
if region_seleccionada == "🔍 Buscar destino / ciudad específica...":
    destino_especifico_texto = st.sidebar.text_input("Introduce ciudad, región o país exacto:", "Daguestán")

st.sidebar.markdown("---")
presupuesto_max = st.sidebar.slider("Presupuesto máximo por vuelo (€):", 10, 1000, 300, step=10)

# -----------------------------------------------------------------------------
# 5. EJECUCIÓN Y MOSTRADO DE RESULTADOS
# -----------------------------------------------------------------------------
st.markdown('<div class="main-title">🌍 Buscador Global de Escapadas</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">Buscando las mejores ofertas con salida desde <b>{ciudad_origen_final}</b></div>', unsafe_allow_html=True)

lista_vuelos, estado_motor = obtener_vuelos_tiempo_real(codigo_origen_iata)
st.caption(estado_motor)

df = pd.DataFrame(lista_vuelos)
if not df.empty:
    df_filtrado = df[df["precio"] <= presupuesto_max].copy()
else:
    df_filtrado = df.copy()

if region_seleccionada != "🔥 Ver todo (Cualquier rincón del planeta)":
    if region_seleccionada == "🔍 Buscar destino / ciudad específica...":
        if destino_especifico_texto:
            consulta = destino_especifico_texto.strip().lower()
            df_filtrado = df_filtrado[
                df_filtrado["destino"].str.lower().str.contains(consulta, na=False)
                | df_filtrado["region"].str.lower().str.contains(consulta, na=False)
                | df_filtrado["pais"].str.lower().str.contains(consulta, na=False)
            ]
    else:
        region_clave = region_seleccionada.split(" (")[0]
        df_filtrado = df_filtrado[df_filtrado["region"].str.startswith(region_clave)]

if not df_filtrado.empty:
    df_filtrado = df_filtrado.sort_values(by="precio")

# -----------------------------------------------------------------------------
# 6. COMPONENTES VISUALES Y MAPA
# -----------------------------------------------------------------------------
if not df_filtrado.empty:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🔥 Escapadas encontradas")
        for _, row in df_filtrado.iterrows():
            st.markdown(f"""
            <div class="card-dest">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin:0; color:#0F172A;">✈️ {row['destino']} ({row['pais']})</h3>
                    <span class="badge-price">{row['precio']} €</span>
                </div>
                <p style="margin: 6px 0 0 0; color:#64748B;">
                    📍 <b>Región:</b> {row['region']}<br>
                    ⏱️ <b>Duración aconsejada:</b> {row['duracion']} | <b>Vuelo:</b> {row['tipo']}
                </p>
                <div style="margin-top: 8px;">
                    <span class="badge-status">{row.get('proveedor', 'Tiempo Real')}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.subheader("🗺️ Mapa Interactivo de Opciones")
        st.map(df_filtrado[["lat", "lon"]], zoom=1)

        st.subheader("📊 Tabla Comparativa")
        st.dataframe(
            df_filtrado[["destino", "pais", "precio", "duracion", "tipo"]],
            use_container_width=True,
            hide_index=True
        )
else:
    st.warning(f"No se encontraron escapadas por menos de {presupuesto_max}€ para el filtro seleccionado. Prueba a subir el presupuesto en el menú lateral.")
