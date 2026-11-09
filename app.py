import streamlit as st
import pandas as pd
import urllib.parse
import httpx
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y TEMA OSCURO FIJO
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="VAGABOND | Escapadas Baratas 'All-in-One'",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo Oscuro Fijo Permanente
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');

    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #090D16 !important;
        color: #F8FAFC !important;
    }
    
    section[data-testid="stSidebar"], [data-testid="stSidebarContent"] {
        background-color: #111827 !important;
        border-right: 1px solid #1E293B !important;
    }

    p, span, label, h1, h2, h3, h4, div, .stMarkdown {
        color: #F8FAFC !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #111827 !important;
        border: 1px solid #1E293B !important;
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. MOTOR DE EVALUACIÓN MULTIMODAL EN TIEMPO REAL
# -----------------------------------------------------------------------------
def obtener_vuelo_live_google(origen_code, destino_code):
    """
    Obtiene la tarifa REAL de vuelo de ida y vuelta más económica en vivo vía Google Flights (SerpApi).
    """
    serpapi_key = st.secrets.get("SERPAPI_KEY", None)
    if not serpapi_key:
        return None
    
    fecha_ida = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    fecha_vuelta = (datetime.now() + timedelta(days=17)).strftime("%Y-%m-%d")
    
    try:
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_flights",
            "departure_id": origen_code,
            "arrival_id": destino_code,
            "outbound_date": fecha_ida,
            "return_date": fecha_vuelta,
            "type": "2",  # 2 = Round trip (Ida y vuelta)
            "travel_class": "1", # Turista
            "currency": "EUR",
            "hl": "es",
            "api_key": serpapi_key
        }
        resp = httpx.get(url, params=params, timeout=7.0)
        data = resp.json()
        
        precios = []
        if "best_flights" in data:
            precios.extend([f["price"] for f in data["best_flights"] if "price" in f])
        if "other_flights" in data:
            precios.extend([f["price"] for f in data["other_flights"] if "price" in f])
            
        if precios:
            return min(precios)
    except Exception:
        pass
    return None

def evaluar_transporte_multimodal(origen_nombre, origen_code, destino_item):
    """
    Compara en tiempo real todas las opciones de transporte (Vuelo vs Autobús/Ferry/Tren)
    y devuelve la alternativa con el menor precio absoluto.
    """
    opciones = []
    
    # Option A: Vuelo Directo en tiempo real
    precio_vuelo = obtener_vuelo_live_google(origen_code, destino_item["code"])
    if precio_vuelo:
        opciones.append({
            "tipo": "Avión (Ida y Vuelta)",
            "precio": precio_vuelo,
            "modo_link": "avion"
        })
    elif "precio_base_vuelo" in destino_item:
        opciones.append({
            "tipo": "Avión (Estimación Ida/Vuelta)",
            "precio": destino_item["precio_base_vuelo"],
            "modo_link": "avion"
        })

    # Option B: Autobús / Ferry / Tren
    if "precio_base_terrestre" in destino_item:
        tipo_terrestre = destino_item.get("tipo_terrestre", "Autobús / Tren")
        opciones.append({
            "tipo": tipo_terrestre,
            "precio": destino_item["precio_base_terrestre"],
            "modo_link": "terrestre"
        })

    if opciones:
        # Devuelve la opción más barata tras comparar avión vs bus/ferry/tren
        ganador = min(opciones, key=lambda x: x["precio"])
        return ganador
    
    return {
        "tipo": "Transporte Estándar",
        "precio": 40,
        "modo_link": "terrestre"
    }

def obtener_chollos_klook(destino_nombre):
    """Escanea en vivo la actividad de menor precio en Klook."""
    tp_token = st.secrets.get("TRAVELPAYOUTS_KEY", None)
    if not tp_token:
        return None
    
    try:
        url = "https://api.travelpayouts.com/v1/klook/search"
        headers = {"X-Access-Token": tp_token}
        params = {
            "query": f"actividades {destino_nombre}",
            "currency": "EUR",
            "lang": "es_ES"
        }
        resp = httpx.get(url, headers=headers, params=params, timeout=6.0)
        data = resp.json()
        
        if "items" in data and len(data["items"]) > 0:
            items_validos = [i for i in data["items"] if "price" in i and float(i["price"]) > 0]
            if items_validos:
                item_chollo = min(items_validos, key=lambda x: float(x["price"]))
                return {
                    "actividad": item_chollo.get("title", f"Experiencia Top en {destino_nombre}"),
                    "precio": float(item_chollo.get("price"))
                }
    except Exception:
        pass
    return None

def generar_enlaces_escapada(modo_transporte, origen_nombre, destino_nombre):
    """Genera hipervínculos dinámicos a las plataformas de reserva correspondientes."""
    def simplificar(t):
        r = {'á':'a', 'é':'e', 'í':'i', 'ó':'o', 'ú':'u', 'ñ':'n'}
        t = t.lower()
        for k, v in r.items():
            t = t.replace(k, v)
        return t.strip().replace(" ", "-")

    origen_slug = simplificar(origen_nombre)
    destino_slug = simplificar(destino_nombre)
    
    fecha_ida = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    fecha_vuelta = (datetime.now() + timedelta(days=17)).strftime("%Y-%m-%d")

    # Enlace Transporte según la opción ganadora
    if modo_transporte == "avion":
        query_vuelo = f"Vuelos de {origen_nombre} a {destino_nombre} del {fecha_ida} al {fecha_vuelta}"
        url_trans = f"https://www.google.com/travel/flights?q={urllib.parse.quote(query_vuelo)}"
    else:
        url_trans = f"https://www.omio.es/viajes/{origen_slug}/{destino_slug}"

    url_hotel = f"https://www.klook.com/es/hotels/search/?city={urllib.parse.quote(destino_nombre)}&checkIn={fecha_ida}&checkOut={fecha_vuelta}"
    url_actividad = f"https://www.klook.com/es/search?query={urllib.parse.quote(destino_nombre)}"

    return url_trans, url_hotel, url_actividad

# -----------------------------------------------------------------------------
# 3. CATÁLOGO CON EVALUACIÓN DUAL (VUELO VS. TERRESTRE/FERRY)
# -----------------------------------------------------------------------------
ORIGENES_DISPONIBLES = {
    "Madrid": "MAD",
    "Barcelona": "BCN",
    "Valencia": "VLC",
    "Málaga": "AGP",
    "Sevilla": "SVQ",
    "Bilbao": "BIO"
}

ESCAPADAS_CATALOGO = [
    {
        "destino": "Tánger / Fez", "pais": "Marruecos", "code": "TNG",
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 22, 
        "precio_base_vuelo": 38, "precio_base_terrestre": 29, "tipo_terrestre": "Autobús + Ferry",
        "actividad_defecto": "Visita Guiada Medina y Zoco", "precio_actividad_defecto": 12,
        "imagen": "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Oporto", "pais": "Portugal", "code": "OPO",
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 28, 
        "precio_base_vuelo": 45, "precio_base_terrestre": 24, "tipo_terrestre": "Autobús Nocturno / Tren",
        "actividad_defecto": "Crucero de los 6 Puentes por el Duero", "precio_actividad_defecto": 15,
        "imagen": "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Valencia", "pais": "España", "code": "VLC",
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 35, 
        "precio_base_vuelo": 55, "precio_base_terrestre": 19, "tipo_terrestre": "Tren Alta Velocidad (Ouigo/Iryo)",
        "actividad_defecto": "Ciudad de las Artes y Ciencias", "precio_actividad_defecto": 24,
        "imagen": "https://images.unsplash.com/photo-1590496793929-36417d3117de?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Sofía", "pais": "Bulgaria", "code": "SOF",
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 24, 
        "precio_base_vuelo": 39, "precio_base_terrestre": 85, "tipo_terrestre": "Autobús Larga Distancia",
        "actividad_defecto": "Tour a los Monasterios de Rila", "precio_actividad_defecto": 15,
        "imagen": "https://images.unsplash.com/photo-1573843981267-be1999ff37cd?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Palma de Mallorca", "pais": "España", "code": "PMI",
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 35, 
        "precio_base_vuelo": 28, "precio_base_terrestre": 45, "tipo_terrestre": "Ferry Express",
        "actividad_defecto": "Paseo en Barco y Snorkel", "precio_actividad_defecto": 25,
        "imagen": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Roma", "pais": "Italia", "code": "FCO",
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 42, 
        "precio_base_vuelo": 48, "precio_base_terrestre": 110, "tipo_terrestre": "Autobús / Tren",
        "actividad_defecto": "Visita Guiada Coliseo y Foro Romano", "precio_actividad_defecto": 30,
        "imagen": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "París", "pais": "Francia", "code": "PAR",
        "duracion": "4 Días / 3 Noches", "hotel_estimado_noche": 48, 
        "precio_base_vuelo": 65, "precio_base_terrestre": 39, "tipo_terrestre": "Autobús Larga Distancia (FlixBus)",
        "actividad_defecto": "Crucero por el Sena al Atardecer", "precio_actividad_defecto": 16,
        "imagen": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=800&q=80"
    }
]

# -----------------------------------------------------------------------------
# 4. BARRA LATERAL (CONTROLES)
# -----------------------------------------------------------------------------
st.sidebar.markdown("### ORIGEN DE LA ESCAPADA")
origen_seleccionado = st.sidebar.selectbox("Ciudad de Salida", list(ORIGENES_DISPONIBLES.keys()), index=0)
codigo_origen_actual = ORIGENES_DISPONIBLES[origen_seleccionado]

st.sidebar.markdown("---")
presupuesto_total_pack = st.sidebar.slider("Presupuesto MÁXIMO Pack (€)", 50, 600, 220, step=10)

# -----------------------------------------------------------------------------
# 5. RENDERIZADO
# -----------------------------------------------------------------------------
st.title("V A G A B O N D")
st.caption(f"Comparador Multimodal en Tiempo Real (Vuelo vs. Bus/Ferry + Hotel + Chollo Klook) desde {origen_seleccionado}")

serp_activa = "SERPAPI_KEY" in st.secrets
klook_activa = "TRAVELPAYOUTS_KEY" in st.secrets

if serp_activa:
    st.success("🟢 Peticiones Google Flights (Ida/Vuelta en Vivo) + Klook API activas")

st.write("")

escapadas_filtradas = []

for item in ESCAPADAS_CATALOGO:
    if item["destino"].lower() == origen_seleccionado.lower():
        continue

    # 1. Comparación Multimodal en Tiempo Real (Selecciona lo más barato entre Avión y Bus/Ferry)
    transporte_ganador = evaluar_transporte_multimodal(origen_seleccionado, codigo_origen_actual, item)
    precio_transporte = transporte_ganador["precio"]
    tipo_transporte_nombre = transporte_ganador["tipo"]

    # 2. Chollo Klook
    nombre_actividad = item["actividad_defecto"]
    precio_actividad = item["precio_actividad_defecto"]
    if klook_activa:
        datos_klook = obtener_chollos_klook(item["destino"])
        if datos_klook:
            nombre_actividad = datos_klook["actividad"]
            precio_actividad = datos_klook["precio"]

    # 3. Alojamiento (2 Noches)
    precio_alojamiento_total = item["hotel_estimado_noche"] * 2

    # 4. Precio Total Pack
    precio_total_pack = int(precio_transporte + precio_alojamiento_total + precio_actividad)

    if precio_total_pack <= presupuesto_total_pack:
        url_trans, url_hotel, url_act = generar_enlaces_escapada(
            transporte_ganador["modo_link"], origen_seleccionado, item["destino"]
        )

        escapadas_filtradas.append({
            "destino": item["destino"],
            "pais": item["pais"],
            "duracion": item["duracion"],
            "transporte": tipo_transporte_nombre,
            "imagen": item["imagen"],
            "precio_transporte": int(precio_transporte),
            "precio_alojamiento": int(precio_alojamiento_total),
            "actividad_nombre": nombre_actividad,
            "precio_actividad": int(precio_actividad),
            "precio_total": precio_total_pack,
            "url_transporte": url_trans,
            "url_hotel": url_hotel,
            "url_actividad": url_act
        })

# Ordenar por precio total de menor a mayor
escapadas_filtradas = sorted(escapadas_filtradas, key=lambda x: x["precio_total"])

# Renderizado mediante tarjetas nativas
if escapadas_filtradas:
    cols = st.columns(2)
    for idx, pack in enumerate(escapadas_filtradas):
        col = cols[idx % 2]
        with col:
            with st.container(border=True):
                st.image(pack["imagen"], use_container_width=True)
                
                st.caption(f"{pack['duracion']} • Opcion más barata: {pack['transporte']}")
                st.subheader(f"{pack['destino']}, {pack['pais']}")
                
                st.metric(label="Precio Pack Completo Estimado", value=f"{pack['precio_total']} €")
                
                st.divider()
                
                st.write(f"• **Transporte ({pack['transporte']}):** {pack['precio_transporte']} €")
                st.write(f"• **Alojamiento (2 Noches):** {pack['precio_alojamiento']} €")
                st.write(f"• **Chollo Klook:** {pack['actividad_nombre']} ({pack['precio_actividad']} €)")
                
                st.divider()

                st.link_button(
                    f"1. Reservar {pack['transporte']} ({pack['precio_transporte']}€)", 
                    pack["url_transporte"], 
                    type="primary", 
                    use_container_width=True
                )
                st.link_button(
                    f"2. Ver Hotel en Klook ({pack['precio_alojamiento']}€)", 
                    pack["url_hotel"], 
                    use_container_width=True
                )
                st.link_button(
                    f"3. Experiencia Klook ({pack['precio_actividad']}€)", 
                    pack["url_actividad"], 
                    use_container_width=True
                )
else:
    st.info(f"No hay paquetes disponibles desde {origen_seleccionado} por debajo de {presupuesto_total_pack}€. Eleva el presupuesto en el panel lateral.")
