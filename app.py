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

# Estilo Oscuro Fijo Permanente (Imposible que falle en ningún dispositivo)
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

    /* Ajuste de contenedores con borde en Modo Oscuro */
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #111827 !important;
        border: 1px solid #1E293B !important;
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. MOTORES API (ALGORITMO BÚSQUEDA DINÁMICA DE CHOLLOS EN TIEMPO REAL)
# -----------------------------------------------------------------------------
def obtener_chollos_klook(destino_nombre):
    """
    Escanea múltiples actividades en Klook en tiempo real y extrae la más barata.
    """
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

def obtener_vuelo_google_real(origen_code, destino_code):
    """
    Consulta la API de Google Flights dinámicamente buscando la tarifa real más baja a 2 semanas vista.
    """
    serpapi_key = st.secrets.get("SERPAPI_KEY", None)
    if not serpapi_key:
        return None
    
    # Cálculo dinámico de fechas futuras (Ida en 14 días, vuelta en 17 días)
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

def generar_enlaces_escapada(tipo_transporte, origen_nombre, destino_nombre):
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

    # Enlace Transporte
    if "Avión" in tipo_transporte:
        query_vuelo = f"Vuelos de {origen_nombre} a {destino_nombre} del {fecha_ida} al {fecha_vuelta}"
        url_trans = f"https://www.google.com/travel/flights?q={urllib.parse.quote(query_vuelo)}"
    elif "Tren" in tipo_transporte or "Autobús" in tipo_transporte:
        url_trans = f"https://www.omio.es/viajes/{origen_slug}/{destino_slug}"
    else:
        url_trans = f"https://www.blablacar.es/search?fn={urllib.parse.quote(origen_nombre)}&tn={urllib.parse.quote(destino_nombre)}"

    # Enlace Alojamiento Klook
    url_hotel = f"https://www.klook.com/es/hotels/search/?city={urllib.parse.quote(destino_nombre)}&checkIn={fecha_ida}&checkOut={fecha_vuelta}"

    # Enlace Experiencia Klook
    url_actividad = f"https://www.klook.com/es/search?query={urllib.parse.quote(destino_nombre)}"

    return url_trans, url_hotel, url_actividad

# -----------------------------------------------------------------------------
# 3. CATÁLOGO AMPLIADO (PRINCIPALES + DESTINOS ALTERNATIVOS HIPER-BARATOS)
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
    # CHIPRE / DESTINOS ALTERNATIVOS DE BAJO COSTE
    {
        "destino": "Sofía", "pais": "Bulgaria", "transporte": "Avión Directo", "code": "SOF",
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 22, "actividad_defecto": "Tour a los Monasterios de Rila",
        "precio_actividad_defecto": 15, "precio_transporte_base": 24,
        "imagen": "https://images.unsplash.com/photo-1573843981267-be1999ff37cd?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Oporto", "pais": "Portugal", "transporte": "Autobús Nocturno", "code": "OPO",
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 28, "actividad_defecto": "Crucero de los 6 Puentes por el Duero",
        "precio_actividad_defecto": 15, "precio_transporte_base": 19,
        "imagen": "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Fez", "pais": "Marruecos", "transporte": "Avión Directo", "code": "FEZ",
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 20, "actividad_defecto": "Visita Guiada por la Medina Histórica",
        "precio_actividad_defecto": 12, "precio_transporte_base": 18,
        "imagen": "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Varsovia", "pais": "Polonia", "transporte": "Avión Directo", "code": "WAW",
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 25, "actividad_defecto": "Concierto de Chopin en el Casco Antiguo",
        "precio_actividad_defecto": 14, "precio_transporte_base": 28,
        "imagen": "https://images.unsplash.com/photo-1519197924294-4ac978a3ef54?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Valencia", "pais": "España", "transporte": "Tren Alta Velocidad", "code": "VLC",
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 35, "actividad_defecto": "Ciudad de las Artes y Ciencias",
        "precio_actividad_defecto": 24, "precio_transporte_base": 15,
        "imagen": "https://images.unsplash.com/photo-1590496793929-36417d3117de?auto=format&fit=crop&w=800&q=80"
    },
    # CAPITALES TRADICIONALES
    {
        "destino": "Roma", "pais": "Italia", "transporte": "Avión Directo", "code": "FCO",
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 40, "actividad_defecto": "Visita Guiada Coliseo y Foro Romano",
        "precio_actividad_defecto": 30, "precio_transporte_base": 34,
        "imagen": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "París", "pais": "Francia", "transporte": "Autobús Larga Distancia", "code": "PAR",
        "duracion": "4 Días / 3 Noches", "hotel_estimado_noche": 45, "actividad_defecto": "Crucero por el Sena al Atardecer",
        "precio_actividad_defecto": 16, "precio_transporte_base": 35,
        "imagen": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Londres", "pais": "Reino Unido", "transporte": "Avión Directo", "code": "STN",
        "duracion": "3 Días / 2 Noches", "hotel_estimado_noche": 50, "actividad_defecto": "Entrada Combinada London Eye",
        "precio_actividad_defecto": 32, "precio_transporte_base": 29,
        "imagen": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?auto=format&fit=crop&w=800&q=80"
    }
]

# -----------------------------------------------------------------------------
# 4. BARRA LATERAL (CONTROLES)
# -----------------------------------------------------------------------------
st.sidebar.markdown("### ORIGEN DE LA ESCAPADA")
origen_seleccionado = st.sidebar.selectbox("Ciudad de Salida", list(ORIGENES_DISPONIBLES.keys()), index=0)
codigo_origen_actual = ORIGENES_DISPONIBLES[origen_seleccionado]

st.sidebar.markdown("---")
presupuesto_total_pack = st.sidebar.slider("Presupuesto MÁXIMO Pack (€)", 50, 600, 180, step=10)

st.sidebar.markdown("---")
filtro_transporte = st.sidebar.multiselect(
    "Modos de Transporte:",
    ["Avión", "Tren", "Autobús"],
    default=["Avión", "Tren", "Autobús"]
)

# -----------------------------------------------------------------------------
# 5. RENDERIZADO CON TARJETAS NATIVAS OFICIALES
# -----------------------------------------------------------------------------
st.title("V A G A B O N D")
st.caption(f"Radar de Escapadas Baratas en Tiempo Real desde {origen_seleccionado} (Transporte + Hotel + Experiencia Klook)")

serp_activa = "SERPAPI_KEY" in st.secrets
klook_activa = "TRAVELPAYOUTS_KEY" in st.secrets

if serp_activa or klook_activa:
    st.success("🟢 Peticiones en tiempo real activas: Buscando las combinaciones de menor coste en directo")

st.write("")

escapadas_filtradas = []

for item in ESCAPADAS_CATALOGO:
    if item["destino"].lower() == origen_seleccionado.lower():
        continue
        
    if not any(t in item["transporte"] for t in filtro_transporte):
        continue

    # 1. Obtener la tarifa más baja de transporte
    precio_transporte = item["precio_transporte_base"]
    if "Avión" in item["transporte"] and serp_activa:
        p_vuelo = obtener_vuelo_google_real(codigo_origen_actual, item["code"])
        if p_vuelo:
            precio_transporte = p_vuelo

    # 2. Obtener el chollo más barato en Klook
    nombre_actividad = item["actividad_defecto"]
    precio_actividad = item["precio_actividad_defecto"]
    if klook_activa:
        datos_klook = obtener_chollos_klook(item["destino"])
        if datos_klook:
            nombre_actividad = datos_klook["actividad"]
            precio_actividad = datos_klook["precio"]

    # 3. Alojamiento (2 Noches)
    precio_alojamiento_total = item["hotel_estimado_noche"] * 2

    # 4. Precio Total
    precio_total_pack = int(precio_transporte + precio_alojamiento_total + precio_actividad)

    if precio_total_pack <= presupuesto_total_pack:
        url_trans, url_hotel, url_act = generar_enlaces_escapada(
            item["transporte"], origen_seleccionado, item["destino"]
        )

        escapadas_filtradas.append({
            "destino": item["destino"],
            "pais": item["pais"],
            "duracion": item["duracion"],
            "transporte": item["transporte"],
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

# Ordenar las escapadas de la más barata a la más cara automáticamente
escapadas_filtradas = sorted(escapadas_filtradas, key=lambda x: x["precio_total"])

# Renderizado mediante st.container(border=True) y st.link_button()
if escapadas_filtradas:
    cols = st.columns(2)
    for idx, pack in enumerate(escapadas_filtradas):
        col = cols[idx % 2]
        with col:
            with st.container(border=True):
                # Fotografía de arquitectura realista
                st.image(pack["imagen"], use_container_width=True)
                
                # Encabezados
                st.caption(f"{pack['duracion']} • {pack['transporte']}")
                st.subheader(f"{pack['destino']}, {pack['pais']}")
                
                # Métrica de Precio Total
                st.metric(label="Precio Pack Completo Estimado", value=f"{pack['precio_total']} €")
                
                st.divider()
                
                # Desglose de costes
                st.write(f"• **Transporte (Ida/Vuelta):** {pack['precio_transporte']} €")
                st.write(f"• **Alojamiento (2 Noches):** {pack['precio_alojamiento']} €")
                st.write(f"• **Experiencia Klook:** {pack['actividad_nombre']} ({pack['precio_actividad']} €)")
                
                st.divider()

                # BOTONES DIRECTOS REALES
                st.link_button(
                    f"1. Reservar Transporte ({pack['precio_transporte']}€)", 
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
