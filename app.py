import html
import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE LA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Global Flight Escape | Buscador de Escapadas",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS personalizados para una interfaz moderna
st.markdown(
    """
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
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 2. BASE DE DATOS MUNDIAL DE ORÍGENES Y REGIONES DE DESTINO
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
        "Canadá": ["Toronto (YYZ)", "Vancouver (YVR)", "Montreal (YUL)"],
    },
    "América del Sur 🌎": {
        "Colombia": ["Bogotá (BOG)", "Medellín (MDE)", "Cartagena (CTG)"],
        "Argentina": ["Buenos Aires (EZE)", "Mendoza (MDZ)", "Córdoba (COR)"],
        "Brasil": ["São Paulo (GRU)", "Río de Janeiro (GIG)"],
        "Chile": ["Santiago (SCL)"],
        "Perú": ["Lima (LIM)"],
    },
    "Asia y Cáucaso 🌏": {
        "Japón": ["Tokio (HND)", "Osaka (KIX)"],
        "Rusia / Cáucaso": ["Moscú (SVO)", "Majachkalá / Daguestán (MCX)", "Sochi (AER)"],
        "Tailandia": ["Bangkok (BKK)", "Phuket (HKT)"],
        "EAU": ["Dubái (DXB)", "Abu Dabi (AUH)"],
    },
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
    "🔍 Buscar destino / ciudad específica...",
]

# -----------------------------------------------------------------------------
# 3. DATOS DE EJEMPLO (NO SON PRECIOS EN TIEMPO REAL)
# -----------------------------------------------------------------------------
DATA_SIMULADA = [
    {"destino": "Roma", "region": "🏰 Europa de Escapada", "pais": "Italia", "precio": 35, "duracion": "3 días", "lat": 41.9028, "lon": 12.4964, "tipo": "Directo"},
    {"destino": "Oporto", "region": "🏰 Europa de Escapada", "pais": "Portugal", "precio": 24, "duracion": "3 días", "lat": 41.1579, "lon": -8.6291, "tipo": "Directo"},
    {"destino": "Cancún / El Caribe", "region": "🏝️ El Caribe (Cancún, Punta Cana, La Habana, San Andrés...)", "pais": "México", "precio": 320, "duracion": "7 días", "lat": 21.1619, "lon": -86.8515, "tipo": "1 Escala"},
    {"destino": "Punta Cana / El Caribe", "region": "🏝️ El Caribe (Cancún, Punta Cana, La Habana, San Andrés...)", "pais": "Rep. Dominicana", "precio": 380, "duracion": "8 días", "lat": 18.5601, "lon": -68.3725, "tipo": "1 Escala"},
    {"destino": "Majachkalá / Daguestán", "region": "⛰️ Daguestán y Cáucaso (Majachkalá, Derbent, Tblisi...)", "pais": "Rusia", "precio": 190, "duracion": "5 días", "lat": 42.9849, "lon": 47.5046, "tipo": "1 Escala"},
    {"destino": "Derbent / Daguestán", "region": "⛰️ Daguestán y Cáucaso (Majachkalá, Derbent, Tblisi...)", "pais": "Rusia", "precio": 210, "duracion": "6 días", "lat": 42.0678, "lon": 48.2899, "tipo": "1 Escala"},
    {"destino": "Bangkok", "region": "🌴 Sudeste Asiático (Bangkok, Bali, Phuket, Vietnam...)", "pais": "Tailandia", "precio": 450, "duracion": "10 días", "lat": 13.7563, "lon": 100.5018, "tipo": "1 Escala"},
    {"destino": "Bali", "region": "🌴 Sudeste Asiático (Bangkok, Bali, Phuket, Vietnam...)", "pais": "Indonesia", "precio": 520, "duracion": "12 días", "lat": -8.4095, "lon": 115.1889, "tipo": "1 Escala"},
    {"destino": "Dubái", "region": "🏜️ Medio Oriente y Desiertos (Dubái, Petra, El Cairo...)", "pais": "EAU", "precio": 210, "duracion": "4 días", "lat": 25.2048, "lon": 55.2708, "tipo": "Directo"},
    {"destino": "Reikiavik", "region": "❄️ Nórdicos y Auroras (Reikiavik, Oslo, Rovaniemi...)", "pais": "Islandia", "precio": 115, "duracion": "4 días", "lat": 64.1466, "lon": -21.9426, "tipo": "Directo"},
    {"destino": "Ibiza", "region": "🏖️ Islas Mediterráneas (Ibiza, Mikonos, Cerdeña, Malta...)", "pais": "España", "precio": 18, "duracion": "3 días", "lat": 38.9067, "lon": 1.4206, "tipo": "Directo"},
    {"destino": "Bora Bora", "region": "🌺 Polinesia e Islas del Pacífico (Fiyi, Tahití...)", "pais": "Polinesia Fr.", "precio": 980, "duracion": "10 días", "lat": -16.5004, "lon": -151.7415, "tipo": "2 Escalas"},
]

# -----------------------------------------------------------------------------
# 4. BARRA LATERAL (FILTROS DE ORIGEN Y DESTINO)
# -----------------------------------------------------------------------------
st.sidebar.title("✈️ Configura tu Viaje")

st.sidebar.subheader("1. Origen (Cualquier lugar)")
continente_sel = st.sidebar.selectbox("Continente de salida:", list(ORIGENES_GLOBALL.keys()))
pais_sel = st.sidebar.selectbox("País de salida:", list(ORIGENES_GLOBALL[continente_sel].keys()))
ciudad_origen_sel = st.sidebar.selectbox(
    "Aeropuerto / Ciudad de origen:", ORIGENES_GLOBALL[continente_sel][pais_sel]
)

origen_manual = st.sidebar.checkbox("¿No está tu ciudad? Escribir origen manual")
if origen_manual:
    ciudad_origen_final = st.sidebar.text_input("Escribe tu ciudad u origen:", "Málaga (AGP)")
else:
    ciudad_origen_final = ciudad_origen_sel

st.sidebar.markdown("---")
st.sidebar.subheader("2. Destino o Región Específica")
region_seleccionada = st.sidebar.selectbox("Selecciona región objetivo:", REGIONES_DESTINO)

destino_especifico_texto = ""
if region_seleccionada == "🔍 Buscar destino / ciudad específica...":
    destino_especifico_texto = st.sidebar.text_input(
        "Introduce ciudad, región o país exacto (ej. Daguestán, San Andrés):", "Daguestán"
    )

st.sidebar.markdown("---")
presupuesto_max = st.sidebar.slider("Presupuesto máximo por vuelo (€):", 10, 1000, 300, step=10)

# -----------------------------------------------------------------------------
# 5. FILTRADO Y PRESENTACIÓN DE RESULTADOS
# -----------------------------------------------------------------------------
st.markdown('<div class="main-title">🌍 Buscador Global de Escapadas</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="sub-title">Buscando ofertas con salida desde <b>{html.escape(ciudad_origen_final)}</b></div>',
    unsafe_allow_html=True,
)

try:
    amadeus_key = st.secrets.get("AMADEUS_CLIENT_ID")
except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
    amadeus_key = None

if amadeus_key:
    st.info("🔑 Credencial de Amadeus configurada. La búsqueda sigue usando datos de ejemplo; aún no está conectada a la API.")
else:
    st.caption("ℹ️ Modo de demostración: los precios y destinos mostrados son datos de ejemplo, no ofertas en tiempo real.")

# Filtrar datos de ejemplo
_df = pd.DataFrame(DATA_SIMULADA)
df_filtrado = _df[_df["precio"] <= presupuesto_max]

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
        # La etiqueta visible incluye ejemplos entre paréntesis; buscar por el nombre
        # de la región permite encontrar los datos de ejemplo asociados.
        region_clave = region_seleccionada.split(" (")[0]
        df_filtrado = df_filtrado[df_filtrado["region"].str.startswith(region_clave)]

df_filtrado = df_filtrado.sort_values(by="precio")

# -----------------------------------------------------------------------------
# 6. RESULTADOS VISUALES
# -----------------------------------------------------------------------------
if not df_filtrado.empty:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🔥 Escapadas encontradas")
        for _, row in df_filtrado.iterrows():
            st.markdown(
                f"""
            <div class="card-dest">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin:0; color:#0F172A;">✈️ {html.escape(row['destino'])} ({html.escape(row['pais'])})</h3>
                    <span class="badge-price">{row['precio']} €</span>
                </div>
                <p style="margin: 6px 0 0 0; color:#64748B;">
                    📍 <b>Región:</b> {html.escape(row['region'])}<br>
                    ⏱️ <b>Duración aconsejada:</b> {html.escape(row['duracion'])} | <b>Vuelo:</b> {html.escape(row['tipo'])}
                </p>
            </div>
            """,
                unsafe_allow_html=True,
            )

    with col2:
        st.subheader("🗺️ Mapa Interactivo de Opciones")
        st.map(df_filtrado[["lat", "lon"]], zoom=1)

        st.subheader("📊 Tabla Comparativa")
        st.dataframe(
            df_filtrado[["destino", "pais", "precio", "duracion", "tipo"]],
            use_container_width=True,
            hide_index=True,
        )
else:
    st.warning(
        f"No se encontraron escapadas por menos de {presupuesto_max}€ para el filtro seleccionado. "
        "Prueba a subir el presupuesto en el menú lateral."
    )
