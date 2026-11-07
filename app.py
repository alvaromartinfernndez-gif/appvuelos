import random
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
    price_color, hero_bg, hero_border, shadow = "#34D399", "#1E293B", "#38BDF8", "rgba(0,0,0,.4)"
    input_bg, input_text = "#334155", "#F8FAFC"
else:
    bg_app, bg_sidebar, text_main, text_sub = "#F8FAFC", "#FFFFFF", "#0F172A", "#475569"
    card_bg, card_border = "#FFFFFF", "#CBD5E1"
    btn_bg, btn_text, btn_hover = "#0F172A", "#FFFFFF", "#047857"
    price_color, hero_bg, hero_border, shadow = "#047857", "#FFFFFF", "#047857", "rgba(0,0,0,.06)"
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
.hero-card {{ background-color:{hero_bg}!important; border-radius:16px; border:2px solid {hero_border}; padding:1.5rem; box-shadow:0 8px 30px {shadow}; margin-bottom:2rem; }}
.hero-badge {{ background-color:{hero_border}; color:{btn_text}!important; font-size:.75rem; font-weight:700; padding:4px 10px; border-radius:6px; letter-spacing:1px; text-transform:uppercase; display:inline-block; margin-bottom:.5rem; }}
.destination-card {{ background-color:{card_bg}!important; border-radius:16px; overflow:hidden; border:1px solid {card_border}; box-shadow:0 4px 20px {shadow}; margin-bottom:1.8rem; }}
.destination-card:hover {{ transform:translateY(-4px); }}
.card-image-container {{ width:100%; height:190px; background-size:cover; background-position:center; }}
.card-content {{ padding:1.25rem; background-color:{card_bg}!important; }}
.card-title {{ font-family:'Cinzel',serif!important; font-size:1.25rem; font-weight:700; color:{text_main}!important; margin:0; }}
.card-region {{ font-size:.8rem; text-transform:uppercase; letter-spacing:1px; color:{text_sub}!important; font-weight:600; margin-top:2px; }}
.price-tag {{ font-size:1.4rem; font-weight:700; color:{price_color}!important; }}
.booking-btn {{ display:block; width:100%; text-align:center; background-color:{btn_bg}!important; color:{btn_text}!important; padding:.65rem 1rem; border-radius:8px; text-decoration:none!important; font-weight:600; font-size:.85rem; letter-spacing:.5px; margin-top:1rem; }}
.booking-btn:hover {{ background-color:{btn_hover}!important; }}
.live-indicator {{ display:inline-flex; align-items:center; gap:6px; font-size:.75rem; color:{price_color}!important; font-weight:600; letter-spacing:.5px; }}
.dot {{ width:8px; height:8px; background-color:#10B981; border-radius:50%; }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. GEOCODIFICACIÓN Y TENDENCIA ILUSTRATIVA DE PRECIOS
# -----------------------------------------------------------------------------
@st.cache_data(ttl=86400)
def obtener_coordenadas_lugar(nombre_lugar):
    """Busca coordenadas mediante Nominatim; usa coordenadas neutrales si falla."""
    try:
        response = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": nombre_lugar, "format": "json", "limit": 1},
            headers={"User-Agent": "VagabondFlightAppGlobal/2.0"},
            timeout=6.0,
        )
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        pass
    return 20.0, 0.0


@st.cache_data(ttl=300)
def calcular_historico_precios_reales(precio_actual, codigo_destino):
    """Crea una tendencia aleatoria ilustrativa, no un histórico real de tarifas."""
    fechas, precios = [], []
    hoy = datetime.now()
    seed = sum(ord(char) for char in codigo_destino) + int(precio_actual)
    rng = random.Random(seed)
    for i in range(14):
        dia = hoy + timedelta(days=i)
        factor = 1.30 if dia.weekday() in (4, 5, 6) else 0.88
        precio = max(18, int((precio_actual + rng.randint(-12, 18)) * factor))
        fechas.append(dia.strftime("%d %b (%a)"))
        precios.append(precio)
    return pd.DataFrame({"Día": fechas, "Precio (€)": precios}).set_index("Día")

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
# 4. BÚSQUEDA DE VUELOS
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300)
def consultar_vuelos_tiempo_real(origen_code, lista_destinos):
    """Intenta fast-flights; los precios de catálogo son referencias, no cotizaciones."""
    fecha_ida = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    fecha_vuelta = (datetime.now() + timedelta(days=17)).strftime("%Y-%m-%d")
    try:
        from fast_flights import FlightData, Passengers, search_airline
    except ImportError:
        FlightData = Passengers = search_airline = None

    vuelos = []
    for item in lista_destinos:
        data = item.copy()
        data["fuente_precio"] = "Precio de referencia (no cotización)"
        # A destination typed by the user is a name, not a valid IATA code.
        if search_airline is not None and len(item["code"]) == 3:
            try:
                resultado = search_airline(
                    flight_data=[FlightData(date=fecha_ida, from_airport=origen_code, to_airport=item["code"])],
                    trip="one-way", passengers=Passengers(adults=1), currency="EUR",
                )
                precios = [int(f.price) for f in (resultado.flights or []) if getattr(f, "price", None) is not None]
                data["precio"] = min(precios) if precios else item["precio_base"]
                if precios:
                    data["fuente_precio"] = "Resultado fast-flights; confirma precio y disponibilidad"
            except Exception:
                data["precio"] = item["precio_base"]
        else:
            data["precio"] = item["precio_base"]

        consulta = f"Flights to {item['destino']} from {origen_code} on {fecha_ida} through {fecha_vuelta}"
        data["url_reserva"] = "https://www.google.com/travel/flights?q=" + urllib.parse.quote(consulta)
        vuelos.append(data)
    return vuelos

# -----------------------------------------------------------------------------
# 5. CONTROLES DE BÚSQUEDA
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
presupuesto_max = st.sidebar.slider("Presupuesto máximo (€)", 10, 2000, 450, step=10)

# -----------------------------------------------------------------------------
# 6. DESTINO PERSONALIZADO Y RESULTADOS
# -----------------------------------------------------------------------------
destinos_a_procesar = DATA_DESTINOS_BASE.copy()
if region_filtro == "Búsqueda por destino exacto..." and destino_busqueda.strip():
    lat_geo, lon_geo = obtener_coordenadas_lugar(destino_busqueda.strip())
    destinos_a_procesar.insert(0, {
        "destino": destino_busqueda.strip().title(), "region": "Búsqueda Personalizada", "pais": "Global",
        "precio_base": 150, "duracion": "5 días", "dias_num": 5, "lat": lat_geo, "lon": lon_geo,
        "tipo": "Consultar disponibilidad", "code": "",
        "img": "https://images.unsplash.com/photo-1488646953014-85cb44e25828?q=80&w=800&auto=format&fit=crop",
    })

st.markdown('<div class="brand-header">V A G A B O N D</div>', unsafe_allow_html=True)
st.markdown(f'<div class="brand-sub">Escapadas desde <b>{ciudad_origen}</b> · precios orientativos sujetos a disponibilidad</div>', unsafe_allow_html=True)
st.caption("El gráfico de tendencia es una simulación, no un histórico de tarifas. Confirma los precios con la aerolínea o el proveedor.")

vuelos = consultar_vuelos_tiempo_real(codigo_iata, destinos_a_procesar)
df = pd.DataFrame(vuelos)
df_filtrado = df[df["precio"] <= presupuesto_max].copy()

if region_filtro != "Cualquier rincón del mundo":
    if region_filtro == "Búsqueda por destino exacto...":
        if destino_busqueda:
            term = destino_busqueda.strip().lower()
            mask = (df_filtrado["destino"].str.lower().str.contains(term, na=False)
                    | df_filtrado["region"].str.lower().str.contains(term, na=False)
                    | df_filtrado["pais"].str.lower().str.contains(term, na=False))
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

if not df_filtrado.empty:
    top = df_filtrado.iloc[0]
    st.markdown("### Oferta destacada · menor precio mostrado")
    col_hero1, col_hero2 = st.columns([1.2, 2])
    with col_hero1:
        st.image(top["img"], use_container_width=True)
    with col_hero2:
        st.markdown(f"""
        <div class="hero-badge">Precio mostrado · confirma disponibilidad</div>
        <h2 style="font-family:'Cinzel',serif;margin:0">{top['destino']} ({top['pais']})</h2>
        <p>Salida desde {ciudad_origen} · {top['duracion']}</p>
        <div style="font-size:2rem;font-weight:700;color:{price_color};margin:10px 0">{top['precio']} €</div>
        <a href="{top['url_reserva']}" target="_blank" class="booking-btn">CONSULTAR EN GOOGLE FLIGHTS</a>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"### 📊 Tendencia ilustrativa de precios para {top['destino']}")
    st.caption("Valores generados aleatoriamente a partir del precio mostrado; no son cotizaciones para fechas concretas.")
    trend = calcular_historico_precios_reales(top["precio"], top["code"])
    chart_col, info_col = st.columns([2.5, 1])
    with chart_col:
        st.bar_chart(trend, y="Precio (€)", height=280)
    with info_col:
        dia_min = trend["Precio (€)"].idxmin()
        precio_min = int(trend["Precio (€)"].min())
        promedio = int(trend["Precio (€)"].mean())
        st.metric("Día más bajo (simulado)", dia_min, f"{precio_min} €")
        st.metric("Promedio simulado", f"{promedio} €")

    st.markdown("---")
    st.markdown("### Todas las opciones disponibles")
    cols = st.columns(3)
    for idx, (_, row) in enumerate(df_filtrado.iterrows()):
        with cols[idx % 3]:
            st.markdown(f"""
            <div class="destination-card">
                <div class="card-image-container" style="background-image:url('{row['img']}')"></div>
                <div class="card-content">
                    <div style="display:flex;justify-content:space-between;align-items:baseline">
                        <h3 class="card-title">{row['destino']}</h3><span class="price-tag">{row['precio']} €</span>
                    </div>
                    <div class="card-region">{row['pais']} · {row['duracion']}</div>
                    <div style="font-size:.8rem;color:{text_sub};margin-top:6px">Vuelo {row['tipo']}</div>
                    <div style="font-size:.72rem;color:{text_sub};margin-top:6px">{row['fuente_precio']}</div>
                    <a href="{row['url_reserva']}" target="_blank" class="booking-btn">CONSULTAR EN GOOGLE FLIGHTS</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Ubicación global en el mapa")
    st.map(df_filtrado[["lat", "lon"]], zoom=1)
else:
    st.info("No hay rutas disponibles para los filtros seleccionados. Ajusta el presupuesto o cambia el destino.")
