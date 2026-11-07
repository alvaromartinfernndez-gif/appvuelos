import streamlit as st
import pandas as pd
import urllib.parse
import httpx
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN Y ESTILOS (AESTHETIC / MINIMAL)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="VAGABOND | Global Engine",
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
        height: 180px;
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
# 2. RESOLUCIÓN DE DESTINOS Y TARIFAS EN TIEMPO REAL
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def resolver_destino_mundial(query_texto):
    """Obtiene el nombre oficial, país y coordenadas de cualquier lugar del planeta."""
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query_texto)}&format=json&addressdetails=1&limit=1"
        headers = {"User-Agent": "VagabondUniversalEngine/11.0"}
        resp = httpx.get(url, headers=headers, timeout=5.0)
        datos = resp.json()
        if datos:
            addr = datos[0].get("address", {})
            lugar = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("state") or query_texto
            pais = addr.get("country", "Mundo")
            return lugar.capitalize(), pais
    except Exception:
        pass
    return query_texto.capitalize(), "Mundo"

def consultar_precio_real_google(origen, destino_query):
    """Consulta la API de SerpApi para obtener el precio real mínimo en vivo."""
    serpapi_key = st.secrets.get("SERPAPI_KEY", None)
    if not serpapi_key:
        return None
    
    fecha_ida = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    fecha_vuelta = (datetime.now() + timedelta(days=21)).strftime("%Y-%m-%d")
    
    try:
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_flights",
            "departure_id": origen,
            "arrival_id": destino_query,
            "outbound_date": fecha_ida,
            "return_date": fecha_vuelta,
            "currency": "EUR",
            "hl": "es",
            "api_key": serpapi_key
        }
        resp = httpx.get(url, params=params, timeout=8.0)
        data = resp.json()
        
        # Extraer el precio más bajo real
        if "best_flights" in data and len(data["best_flights"]) > 0:
            return data["best_flights"][0]["price"]
        elif "other_flights" in data and len(data["other_flights"]) > 0:
            return data["other_flights"][0]["price"]
    except Exception:
        pass
    return None

# -----------------------------------------------------------------------------
# 3. BASE DE DATOS LOCAL Y CONTROLES DEL SIDEBAR
# -----------------------------------------------------------------------------
ORIGENES_MUNDIALES = {
    "España": ["Madrid (MAD)", "Barcelona (BCN)", "Valencia (VLC)", "Málaga (AGP)", "Sevilla (SVQ)"],
    "Europa": ["París (CDG)", "Londres (LHR)", "Fráncfort (FRA)", "Roma (FCO)", "Ámsterdam (AMS)"],
    "América": ["Nueva York (JFK)", "Miami (MIA)", "Los Ángeles (LAX)", "Ciudad de México (MEX)", "Bogotá (BOG)", "Buenos Aires (EZE)"],
    "Asia & Oriente": ["Dubái (DXB)", "Tokio (HND)", "Bangkok (BKK)", "Singapur (SIN)"]
}

CATALOGO_RECOMENDADO = [
    {"destino": "Roma", "pais": "Italia", "code": "FCO", "precio_ref": 34, "duracion": "3 días", "dias_num": 3, "tipo": "Directo", "rating": 9.5, "img": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Oporto", "pais": "Portugal", "code": "OPO", "precio_ref": 22, "duracion": "3 días", "dias_num": 3, "tipo": "Directo", "rating": 9.2, "img": "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Cancún", "pais": "México", "code": "CUN", "precio_ref": 320, "duracion": "7 días", "dias_num": 7, "tipo": "1 escala", "rating": 8.9, "img": "https://images.unsplash.com/photo-1510097467424-192d713be8b2?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Nueva York", "pais": "EE.UU.", "code": "JFK", "precio_ref": 280, "duracion": "6 días", "dias_num": 6, "tipo": "Directo", "rating": 9.7, "img": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Tokio", "pais": "Japón", "code": "HND", "precio_ref": 540, "duracion": "10 días", "dias_num": 10, "tipo": "1 escala", "rating": 9.9, "img": "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Bangkok", "pais": "Tailandia", "code": "BKK", "precio_ref": 440, "duracion": "10 días", "dias_num": 10, "tipo": "1 escala", "rating": 9.5, "img": "https://images.unsplash.com/photo-1508009603885-50cf7c579365?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Dubái", "pais": "EAU", "code": "DXB", "precio_ref": 210, "duracion": "4 días", "dias_num": 4, "tipo": "Directo", "rating": 8.8, "img": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Ciudad del Cabo", "pais": "Sudáfrica", "code": "CPT", "precio_ref": 460, "duracion": "9 días", "dias_num": 9, "tipo": "1 escala", "rating": 9.4, "img": "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?q=80&w=800&auto=format&fit=crop"},
    {"destino": "Sídney", "pais": "Australia", "code": "SYD", "precio_ref": 820, "duracion": "12 días", "dias_num": 12, "tipo": "2 escalas", "rating": 9.3, "img": "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?q=80&w=800&auto=format&fit=crop"}
]

st.sidebar.markdown("---")
st.sidebar.markdown("### ORIGEN DEL VIAJE")
region_salida = st.sidebar.selectbox("Región", list(ORIGENES_MUNDIALES.keys()))
ciudad_origen = st.sidebar.selectbox("Aeropuerto", ORIGENES_MUNDIALES[region_salida])
codigo_origen = ciudad_origen.split("(")[-1].replace(")", "").strip() if "(" in ciudad_origen else "MAD"

st.sidebar.markdown("---")
st.sidebar.markdown("### BÚSQUEDA DIRECTA MUNDIAL")
busqueda_libre = st.sidebar.text_input("Escribe cualquier ciudad o país:", "", placeholder="Ej: Zanzíbar, Kioto, Bora Bora, Bali...")
solo_directos = st.sidebar.checkbox("Mostrar solo vuelos directos", value=False)
presupuesto_max = st.sidebar.slider("Presupuesto máximo (€)", 10, 4000, 1000, step=50)

# -----------------------------------------------------------------------------
# 4. ENCABEZADO Y RENDERING
# -----------------------------------------------------------------------------
st.markdown('<div class="brand-header">V A G A B O N D</div>', unsafe_allow_html=True)
st.markdown(f'<div class="brand-sub">Consulta en vivo desde <b>{ciudad_origen}</b></div>', unsafe_allow_html=True)

if "SERPAPI_KEY" in st.secrets:
    st.markdown('<div class="status-dot"><div class="dot"></div> API Oficial Google Flights Conectada</div>', unsafe_allow_html=True)

st.write("")

fecha_ida_str = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
fecha_vuelta_str = (datetime.now() + timedelta(days=21)).strftime("%Y-%m-%d")

# -----------------------------------------------------------------------------
# CASO A: SI EL USUARIO ESCRIBE UN DESTINO ESPECÍFICO (VISTA ÚNICA EN TIEMPO REAL)
# -----------------------------------------------------------------------------
if busqueda_libre.strip():
    nombre_lugar, pais_lugar = resolver_destino_mundial(busqueda_libre.strip())
    precio_real = consultar_precio_real_google(codigo_origen, nombre_lugar)
    
    url_google_flights = f"https://www.google.com/travel/flights?q=Vuelos%20a%20{urllib.parse.quote(nombre_lugar)}%20desde%20{codigo_origen}"
    
    st.markdown(f'<div class="section-title">Resultado en tiempo real para "{nombre_lugar}"</div>', unsafe_allow_html=True)
    
    col_busq1, col_busq2 = st.columns([1, 2])
    with col_busq1:
        st.image("https://images.unsplash.com/photo-1488646953014-85cb44e25828?q=80&w=800&auto=format&fit=crop", use_container_width=True)
    with col_busq2:
        st.markdown(f"""
        <h2 style="font-family: 'Cinzel', serif; margin:0;">{nombre_lugar}</h2>
        <p style="color: {text_sub}; text-transform: uppercase; letter-spacing: 1px; font-size: 0.85rem;">{pais_lugar}</p>
        """, unsafe_allow_html=True)
        
        if precio_real:
            st.markdown(f'<div class="price-tag" style="font-size: 2.2rem; margin: 15px 0;">{precio_real} € <span style="font-size: 0.8rem; color:{text_sub}; font-weight: 300;">(Tarifa exacta en vivo)</span></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="font-size: 1.1rem; color:{text_sub}; margin: 15px 0;">Consulta el calendario de precios mínimos directamente en Google Flights.</div>', unsafe_allow_html=True)
            
        st.markdown(f'<a href="{url_google_flights}" target="_blank" class="booking-btn" style="max-width: 320px;">VER CALENDARIO COMPLETO EN GOOGLE FLIGHTS</a>', unsafe_allow_html=True)

    st.markdown("---")

# -----------------------------------------------------------------------------
# CASO B: CATÁLOGO DE INSPIRACIÓN MUNDIAL (6 BARATOS Y 6 CALIDAD-PRECIO)
# -----------------------------------------------------------------------------
vuelos_procesados = []
for item in CATALOGO_RECOMENDADO:
    item_copy = item.copy()
    precio_api = consultar_precio_real_google(codigo_origen, item["code"])
    precio_final = precio_api if precio_api else item["precio_ref"]
    
    item_copy["precio"] = precio_final
    factor_directo = 1.25 if "Directo" in item["tipo"] else 1.0
    item_copy["score_cp"] = round(((item["rating"] * 10) * factor_directo) / precio_final, 3)
    
    url_g = f"https://www.google.com/travel/flights?q=Flights%20to%20{urllib.parse.quote(item['destino'])}%20from%20{codigo_origen}%20on%20{fecha_ida_str}%20through%20{fecha_vuelta_str}"
    item_copy["url_reserva"] = url_g
    vuelos_procesados.append(item_copy)

df = pd.DataFrame(vuelos_procesados)
df_filtrado = df[df["precio"] <= presupuesto_max]

if solo_directos:
    df_filtrado = df_filtrado[df_filtrado["tipo"].str.contains("Directo")]

st.markdown('<div class="section-title">Los 6 viajes más baratos del mundo</div>', unsafe_allow_html=True)
if not df_filtrado.empty:
    top_baratos = df_filtrado.sort_values(by="precio").head(6)
    cols_b = st.columns(3)
    for idx, (_, row) in enumerate(top_baratos.iterrows()):
        col = cols_b[idx % 3]
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
                    <a href="{row['url_reserva']}" target="_blank" class="booking-btn">CONSULTAR EN GOOGLE FLIGHTS</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

st.markdown('<div class="section-title">Los 6 mejores en calidad - precio</div>', unsafe_allow_html=True)
if not df_filtrado.empty:
    top_calidad = df_filtrado.sort_values(by="score_cp", ascending=False).head(6)
    cols_c = st.columns(3)
    for idx, (_, row) in enumerate(top_calidad.iterrows()):
        col = cols_c[idx % 3]
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
                    <a href="{row['url_reserva']}" target="_blank" class="booking-btn">CONSULTAR EN GOOGLE FLIGHTS</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
