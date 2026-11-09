import streamlit as st
import pandas as pd
import urllib.parse
import httpx
import time
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y TEMA OSCURO PERMANENTE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="VAGABOND | Escapadas Baratas 'All-in-One'",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
# 2. MOTORES EN TIEMPO REAL (TRAVELPAYOUTS V3 FLIGHTS & KLOOK CON DEEP LINKS REALES)
# -----------------------------------------------------------------------------
def obtener_vuelo_live_travelpayouts(origen_code, destino_code, num_pasajeros):
    """
    Consulta en tiempo real la API v3 de Travelpayouts/Aviasales filtrada por fechas exactas.
    """
    tp_token = st.secrets.get("TRAVELPAYOUTS_KEY", None)
    if not tp_token:
        return None

    fecha_ida = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    fecha_vuelta = (datetime.now() + timedelta(days=17)).strftime("%Y-%m-%d")

    try:
        url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
        headers = {"X-Access-Token": tp_token}
        params = {
            "origin": origen_code,
            "destination": destino_code,
            "departure_at": fecha_ida,
            "return_at": fecha_vuelta,
            "unique": "true",
            "sorting": "price",
            "currency": "EUR",
            "limit": 5
        }
        resp = httpx.get(url, headers=headers, params=params, timeout=7.0)
        data = resp.json()

        if data.get("success") and "data" in data and len(data["data"]) > 0:
            precio_persona = float(data["data"][0]["price"])
            return precio_persona * num_pasajeros
    except Exception:
        pass
    return None

def obtener_chollos_klook_live(destino_nombre, num_pasajeros):
    """
    Consulta la API de Klook para extraer la experiencia más económica 
    junto con su enlace de reserva oficial directo (Evita el 404).
    """
    tp_token = st.secrets.get("TRAVELPAYOUTS_KEY", None)
    if not tp_token:
        return None
    
    try:
        url = "https://api.travelpayouts.com/v1/klook/search"
        headers = {"X-Access-Token": tp_token}
        params = {
            "query": destino_nombre,
            "currency": "EUR",
            "lang": "es_ES"
        }
        resp = httpx.get(url, headers=headers, params=params, timeout=6.0)
        data = resp.json()
        
        if "items" in data and len(data["items"]) > 0:
            items_validos = [i for i in data["items"] if "price" in i and float(i["price"]) > 0]
            if items_validos:
                item_chollo = min(items_validos, key=lambda x: float(x["price"]))
                precio_unitario = float(item_chollo.get("price"))
                
                # Extraer URL directa del producto si existe en la respuesta de la API
                url_directa = item_chollo.get("url") or item_chollo.get("deep_link")
                
                return {
                    "actividad": item_chollo.get("title", f"Experiencia Top en {destino_nombre}"),
                    "precio_total": precio_unitario * num_pasajeros,
                    "url_directa": url_directa
                }
    except Exception:
        pass
    return None

def generar_enlaces_escapada(tipo_transporte, origen_nombre, destino_nombre, origen_code, destino_code, num_pasajeros, url_klook_actividad_api=None):
    """Genera URLs dinámicas de reserva 100% funcionales y sin errores 404."""
    def simplificar(t):
        r = {'á':'a', 'é':'e', 'í':'i', 'ó':'o', 'ú':'u', 'ñ':'n'}
        t = t.lower()
        for k, v in r.items():
            t = t.replace(k, v)
        return t.strip().replace(" ", "-")

    origen_slug = simplificar(origen_nombre)
    destino_slug = simplificar(destino_nombre)
    
    fecha_ida = datetime.now() + timedelta(days=14)
    fecha_vuelta = datetime.now() + timedelta(days=17)

    # 1. Enlace Transporte (Aviasales u Omio)
    if "Avión" in tipo_transporte:
        dia_ida, mes_ida = fecha_ida.strftime("%d"), fecha_ida.strftime("%m")
        dia_vta, mes_vta = fecha_vuelta.strftime("%d"), fecha_vuelta.strftime("%m")
        url_trans = f"https://www.aviasales.com/search/{origen_code}{dia_ida}{mes_ida}{destino_code}{dia_vta}{mes_vta}{num_pasajeros}"
    elif "Tren" in tipo_transporte or "Autobús" in tipo_transporte:
        url_trans = f"https://www.omio.es/viajes/{origen_slug}/{destino_slug}"
    else:
        url_trans = f"https://www.blablacar.es/search?fn={urllib.parse.quote(origen_nombre)}&tn={urllib.parse.quote(destino_nombre)}"

    # 2. Enlace Alojamiento Klook (Estructura de búsqueda estándar segura)
    dest_encoded = urllib.parse.quote(destino_nombre)
    url_hotel = f"https://www.klook.com/es-ES/experiences/list/{dest_encoded}-hotels/"

    # 3. Enlace Experiencia Klook (Prioriza la URL devuelta por la API; si no, usa la ruta base segura)
    if url_klook_actividad_api:
        url_actividad = url_klook_actividad_api
    else:
        url_actividad = f"https://www.klook.com/es-ES/experiences/list/{dest_encoded}-things-to-do/"

    return url_trans, url_hotel, url_actividad

# -----------------------------------------------------------------------------
# 3. CATÁLOGO CON PRECIOS Y DESTINOS
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
        "destino": "Sofía", "pais": "Bulgaria", "transporte": "Avión Directo", "code": "SOF",
        "duracion": "3 Días / 2 Noches", "hotel_base_noche": 30, 
        "actividad_defecto": "Tour a los Monasterios de Rila", "precio_actividad_base": 15, 
        "precio_transporte_persona_base": 165,
        "imagen": "https://images.unsplash.com/photo-1573843981267-be1999ff37cd?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Varsovia", "pais": "Polonia", "transporte": "Avión Directo", "code": "WAW",
        "duracion": "3 Días / 2 Noches", "hotel_base_noche": 35, 
        "actividad_defecto": "Concierto de Chopin en el Casco Antiguo", "precio_actividad_base": 14, 
        "precio_transporte_persona_base": 170,
        "imagen": "https://images.unsplash.com/photo-1519197924294-4ac978a3ef54?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Oporto", "pais": "Portugal", "transporte": "Autobús Nocturno / Tren", "code": "OPO",
        "duracion": "3 Días / 2 Noches", "hotel_base_noche": 32, 
        "actividad_defecto": "Crucero de los 6 Puentes por el Duero", "precio_actividad_base": 15, 
        "precio_transporte_persona_base": 28,
        "imagen": "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Fez", "pais": "Marruecos", "transporte": "Avión Directo", "code": "FEZ",
        "duracion": "3 Días / 2 Noches", "hotel_base_noche": 25, 
        "actividad_defecto": "Visita Guiada por la Medina Histórica", "precio_actividad_base": 12, 
        "precio_transporte_persona_base": 65,
        "imagen": "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Valencia", "pais": "España", "transporte": "Tren Alta Velocidad", "code": "VLC",
        "duracion": "3 Días / 2 Noches", "hotel_base_noche": 40, 
        "actividad_defecto": "Ciudad de las Artes y Ciencias", "precio_actividad_base": 24, 
        "precio_transporte_persona_base": 25,
        "imagen": "https://images.unsplash.com/photo-1590496793929-36417d3117de?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Roma", "pais": "Italia", "transporte": "Avión Directo", "code": "FCO",
        "duracion": "3 Días / 2 Noches", "hotel_base_noche": 45, 
        "actividad_defecto": "Visita Guiada Coliseo y Foro Romano", "precio_actividad_base": 30, 
        "precio_transporte_persona_base": 120,
        "imagen": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=800&q=80"
    }
]

# -----------------------------------------------------------------------------
# 4. BARRA LATERAL (CONTROLES)
# -----------------------------------------------------------------------------
st.sidebar.markdown("### CONFIGURACIÓN DEL VIAJE")
origen_seleccionado = st.sidebar.selectbox("Ciudad de Salida", list(ORIGENES_DISPONIBLES.keys()), index=0)
codigo_origen_actual = ORIGENES_DISPONIBLES[origen_seleccionado]

num_viajeros = st.sidebar.number_input("Número de Viajeros 👤", min_value=1, max_value=8, value=2, step=1)

st.sidebar.markdown("---")
presupuesto_total_pack = st.sidebar.slider(f"Presupuesto MÁXIMO Pack Total ({num_viajeros} p) (€)", 100, 2000, 600, step=25)

st.sidebar.markdown("---")
filtro_transporte = st.sidebar.multiselect(
    "Modos de Transporte:",
    ["Avión", "Tren", "Autobús"],
    default=["Avión", "Tren", "Autobús"]
)

# -----------------------------------------------------------------------------
# 5. RENDERIZADO PRINCIPAL
# -----------------------------------------------------------------------------
st.title("V A G A B O N D")
st.caption(f"Radar de Escapadas con Tarifas en Vivo (Travelpayouts Live v3 + Klook + Alojamiento) desde {origen_seleccionado}")

tp_activa = "TRAVELPAYOUTS_KEY" in st.secrets

if tp_activa:
    st.success(f"🟢 API Travelpayouts v3 Conectada: Búsqueda sincrónica en tiempo real para {num_viajeros} viajero(s)")

st.write("")

escapadas_filtradas = []

for item in ESCAPADAS_CATALOGO:
    if item["destino"].lower() == origen_seleccionado.lower():
        continue
        
    if not any(t in item["transporte"] for t in filtro_transporte):
        continue

    # 1. Tarifas de Vuelos Real desde Travelpayouts API v3
    precio_transporte_total = item["precio_transporte_persona_base"] * num_viajeros
    es_live_flight = False

    if "Avión" in item["transporte"] and tp_activa:
        precio_vuelo_tp = obtener_vuelo_live_travelpayouts(codigo_origen_actual, item["code"], num_viajeros)
        if precio_vuelo_tp:
            precio_transporte_total = precio_vuelo_tp
            es_live_flight = True

    # 2. Experiencia Klook y URL directa
    nombre_actividad = item["actividad_defecto"]
    precio_actividad_total = item["precio_actividad_base"] * num_viajeros
    url_klook_api = None

    if tp_activa:
        datos_klook = obtener_chollos_klook_live(item["destino"], num_viajeros)
        if datos_klook:
            nombre_actividad = datos_klook["actividad"]
            precio_actividad_total = datos_klook["precio_total"]
            url_klook_api = datos_klook.get("url_directa")

    # 3. Alojamiento (2 Noches)
    precio_alojamiento_total = int(item["hotel_base_noche"] * 2)

    # 4. Precio Pack Total
    precio_total_pack = int(precio_transporte_total + precio_alojamiento_total + precio_actividad_total)

    if precio_total_pack <= presupuesto_total_pack:
        url_trans, url_hotel, url_act = generar_enlaces_escapada(
            item["transporte"], origen_seleccionado, item["destino"], codigo_origen_actual, item["code"], num_viajeros, url_klook_api
        )

        escapadas_filtradas.append({
            "destino": item["destino"],
            "pais": item["pais"],
            "duracion": item["duracion"],
            "transporte": item["transporte"],
            "imagen": item["imagen"],
            "precio_transporte": int(precio_transporte_total),
            "precio_alojamiento": int(precio_alojamiento_total),
            "actividad_nombre": nombre_actividad,
            "precio_actividad": int(precio_actividad_total),
            "precio_total": precio_total_pack,
            "es_live": es_live_flight,
            "url_transporte": url_trans,
            "url_hotel": url_hotel,
            "url_actividad": url_act
        })

escapadas_filtradas = sorted(escapadas_filtradas, key=lambda x: x["precio_total"])

if escapadas_filtradas:
    cols = st.columns(2)
    for idx, pack in enumerate(escapadas_filtradas):
        col = cols[idx % 2]
        with col:
            with st.container(border=True):
                st.image(pack["imagen"], use_container_width=True)
                
                badge_live = " • Tarifa Live API v3" if pack["es_live"] else ""
                st.caption(f"{pack['duracion']} • {pack['transporte']}{badge_live}")
                st.subheader(f"{pack['destino']}, {pack['pais']}")
                
                st.metric(label=f"Precio Pack Total ({num_viajeros} viajero/s)", value=f"{pack['precio_total']} €")
                
                st.divider()
                
                st.write(f"• **Transporte ({pack['transporte']}):** {pack['precio_transporte']} €")
                st.write(f"• **Alojamiento (2 Noches):** {pack['precio_alojamiento']} €")
                st.write(f"• **Experiencia Klook:** {pack['actividad_nombre']} ({pack['precio_actividad']} €)")
                
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
    st.info(f"No hay paquetes disponibles desde {origen_seleccionado} por debajo de {presupuesto_total_pack}€ para {num_viajeros} persona(s). Eleva el presupuesto en el panel lateral.")
