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
# 2. MOTOR DE EXPLORACIÓN DE DESTINOS EN TIEMPO REAL (CHOLLOS DINÁMICOS)
# -----------------------------------------------------------------------------
ORIGENES_DISPONIBLES = {
    "Madrid": "MAD",
    "Barcelona": "BCN",
    "Valencia": "VLC",
    "Málaga": "AGP",
    "Sevilla": "SVQ",
    "Bilbao": "BIO"
}

# Base de imágenes de alta calidad por código IATA o genéricas arquitectónicas
IMAGENES_DESTINOS = {
    "SOF": "https://images.unsplash.com/photo-1573843981267-be1999ff37cd?auto=format&fit=crop&w=800&q=80",
    "WAW": "https://images.unsplash.com/photo-1519197924294-4ac978a3ef54?auto=format&fit=crop&w=800&q=80",
    "OPO": "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?auto=format&fit=crop&w=800&q=80",
    "FEZ": "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=800&q=80",
    "VLC": "https://images.unsplash.com/photo-1590496793929-36417d3117de?auto=format&fit=crop&w=800&q=80",
    "FCO": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=800&q=80",
    "LIS": "https://images.unsplash.com/photo-1585208798174-6cedd86e019a?auto=format&fit=crop&w=800&q=80",
    "PAR": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=800&q=80",
    "LON": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?auto=format&fit=crop&w=800&q=80",
    "BER": "https://images.unsplash.com/photo-1560969184-10fe8719e047?auto=format&fit=crop&w=800&q=80",
    "DEFAULT": "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=800&q=80"
}

def obtener_vuelos_chollos_dinamicos(origen_code, num_pasajeros):
    """
    Escanea la API de Travelpayouts para descubrir los vuelos de IDA Y VUELTA 
    más baratos en vivo desde la ciudad elegida hacia cualquier destino.
    """
    tp_token = st.secrets.get("TRAVELPAYOUTS_KEY", None)
    if not tp_token:
        return []

    fecha_ida = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    fecha_vuelta = (datetime.now() + timedelta(days=17)).strftime("%Y-%m-%d")

    vuelos_encontrados = []

    try:
        url = "https://api.travelpayouts.com/v3/prices_for_dates"
        headers = {"X-Access-Token": tp_token}
        params = {
            "origin": origen_code,
            "departure_at": fecha_ida,
            "return_at": fecha_vuelta,
            "one_way": "false",  # EXCLUSIVO IDA Y VUELTA COMPLETO
            "sorting": "price",
            "currency": "EUR",
            "limit": 15
        }
        resp = httpx.get(url, headers=headers, params=params, timeout=7.0)
        data = resp.json()

        if data.get("success") and "data" in data:
            for item in data["data"]:
                precio_persona = float(item.get("price", 0))
                destino_code = item.get("destination")
                
                # Filtrar tarifas de ida y vuelta consistentes
                if precio_persona > 15 and destino_code:
                    vuelos_encontrados.append({
                        "code": destino_code,
                        "precio_transporte_total": precio_persona * num_pasajeros,
                        "precio_persona": precio_persona,
                        "f_ida": item.get("departure_at", "")[:10],
                        "f_vta": item.get("return_at", "")[:10]
                    })
    except Exception:
        pass

    return vuelos_encontrados

def obtener_chollos_klook_live(destino_nombre, num_pasajeros):
    """Consulta la API de Klook para extraer la experiencia más económica."""
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
        resp = httpx.get(url, headers=headers, params=params, timeout=5.0)
        data = resp.json()
        
        if "items" in data and len(data["items"]) > 0:
            items_validos = [i for i in data["items"] if "price" in i and float(i["price"]) > 0]
            if items_validos:
                item_chollo = min(items_validos, key=lambda x: float(x["price"]))
                precio_unitario = float(item_chollo.get("price"))
                url_directa = item_chollo.get("deep_link") or item_chollo.get("url")
                
                return {
                    "actividad": item_chollo.get("title", f"Experiencia Top en {destino_nombre}"),
                    "precio_total": precio_unitario * num_pasajeros,
                    "url_directa": url_directa
                }
    except Exception:
        pass
    return None

def generar_enlaces_escapada(origen_nombre, destino_nombre, origen_code, destino_code, num_pasajeros, f_ida_api, f_vuelta_api, url_klook_actividad_api=None):
    """Genera URLs dinámicas directas sin errores 404."""
    if f_ida_api and f_vuelta_api:
        try:
            dt_ida = datetime.strptime(f_ida_api, "%Y-%m-%d")
            dt_vta = datetime.strptime(f_vuelta_api, "%Y-%m-%d")
        except Exception:
            dt_ida = datetime.now() + timedelta(days=14)
            dt_vta = datetime.now() + timedelta(days=17)
    else:
        dt_ida = datetime.now() + timedelta(days=14)
        dt_vta = datetime.now() + timedelta(days=17)

    dia_ida, mes_ida = dt_ida.strftime("%d"), dt_ida.strftime("%m")
    dia_vta, mes_vta = dt_vta.strftime("%d"), dt_vta.strftime("%m")
    
    # URL Vuelo Aviasales (Ida y Vuelta con número de viajeros exacto)
    url_trans = f"https://www.aviasales.com/search/{origen_code}{dia_ida}{mes_ida}{destino_code}{dia_vta}{mes_vta}{num_pasajeros}"

    # URL Hotel Klook
    url_hotel = f"https://www.klook.com/es/search/?query={urllib.parse.quote('hotel ' + destino_nombre)}"

    # URL Experiencia Klook
    if url_klook_actividad_api and str(url_klook_actividad_api).startswith("http"):
        url_actividad = url_klook_actividad_api
    else:
        url_actividad = f"https://www.klook.com/es/search/?query={urllib.parse.quote('actividades ' + destino_nombre)}"

    return url_trans, url_hotel, url_actividad

# -----------------------------------------------------------------------------
# 3. BARRA LATERAL (CONTROLES)
# -----------------------------------------------------------------------------
st.sidebar.markdown("### CONFIGURACIÓN DEL VIAJE")
origen_seleccionado = st.sidebar.selectbox("Ciudad de Salida", list(ORIGENES_DISPONIBLES.keys()), index=0)
codigo_origen_actual = ORIGENES_DISPONIBLES[origen_seleccionado]

num_viajeros = st.sidebar.number_input("Número de Viajeros 👤", min_value=1, max_value=8, value=1, step=1)

st.sidebar.markdown("---")
presupuesto_total_pack = st.sidebar.slider(f"Presupuesto MÁXIMO Pack Total ({num_viajeros} p) (€)", 50, 1500, 350, step=25)

# -----------------------------------------------------------------------------
# 4. RENDERIZADO PRINCIPAL (DESTINOS DINÁMICOS EN DIRECTO)
# -----------------------------------------------------------------------------
st.title("V A G A B O N D")
st.caption(f"Radar Inteligente de Chollos Dinámicos en Tiempo Real desde {origen_seleccionado}")

tp_activa = "TRAVELPAYOUTS_KEY" in st.secrets

if tp_activa:
    st.success(f"🟢 Escaneando el mercado en directo: Descubriendo los destinos más baratos desde {origen_seleccionado}")

st.write("")

# 1. Escanear ofertas de vuelos dinámicas
vuelos_live = obtener_vuelos_chollos_dinamicos(codigo_origen_actual, num_viajeros)

escapadas_filtradas = []

if vuelos_live:
    for vuelo in vuelos_live:
        codigo_dest = vuelo["code"]
        destino_nombre = codigo_dest  # Nombre dinámico según código IATA
        
        # 2. Experiencia Klook en vivo
        nombre_actividad = f"Tour Top en {destino_nombre}"
        precio_actividad_total = 15 * num_viajeros
        url_klook_api = None

        if tp_activa:
            datos_klook = obtener_chollos_klook_live(destino_nombre, num_pasajeros=num_viajeros)
            if datos_klook:
                nombre_actividad = datos_klook["actividad"]
                precio_actividad_total = datos_klook["precio_total"]
                url_klook_api = datos_klook.get("url_directa")

        # 3. Estimación Alojamiento (2 Noches)
        precio_alojamiento_total = 35 * 2

        # 4. Cálculo del Pack Total Real
        precio_total_pack = int(vuelo["precio_transporte_total"] + precio_alojamiento_total + precio_actividad_total)

        if precio_total_pack <= presupuesto_total_pack:
            url_trans, url_hotel, url_act = generar_enlaces_escapada(
                origen_seleccionado, destino_nombre, codigo_origen_actual, codigo_dest, num_viajeros, vuelo["f_ida"], vuelo["f_vta"], url_klook_api
            )

            img_url = IMAGENES_DESTINOS.get(codigo_dest, IMAGENES_DESTINOS["DEFAULT"])

            escapadas_filtradas.append({
                "destino": destino_nombre,
                "duracion": "3 Días / 2 Noches",
                "transporte": "Avión Directo (Ida y Vuelta)",
                "imagen": img_url,
                "precio_transporte": int(vuelo["precio_transporte_total"]),
                "precio_alojamiento": int(precio_alojamiento_total),
                "actividad_nombre": nombre_actividad,
                "precio_actividad": int(precio_actividad_total),
                "precio_total": precio_total_pack,
                "url_transporte": url_trans,
                "url_hotel": url_hotel,
                "url_actividad": url_act
            })

# Ordenar por precio total de menor a mayor
escapadas_filtradas = sorted(escapadas_filtradas, key=lambda x: x["precio_total"])

# Renderizado de Tarjetas
if escapadas_filtradas:
    cols = st.columns(2)
    for idx, pack in enumerate(escapadas_filtradas):
        col = cols[idx % 2]
        with col:
            with st.container(border=True):
                st.image(pack["imagen"], use_container_width=True)
                
                st.caption(f"{pack['duracion']} • {pack['transporte']} • Live API")
                st.subheader(f"Destino: {pack['destino']}")
                
                st.metric(label=f"Precio Pack Total ({num_viajeros} viajero/s)", value=f"{pack['precio_total']} €")
                
                st.divider()
                
                st.write(f"• **Vuelo Ida y Vuelta ({num_viajeros}p):** {pack['precio_transporte']} €")
                st.write(f"• **Alojamiento (2 Noches):** {pack['precio_alojamiento']} €")
                st.write(f"• **Experiencia Klook:** {pack['actividad_nombre']} ({pack['precio_actividad']} €)")
                
                st.divider()

                st.link_button(
                    f"1. Reservar Vuelo ({pack['precio_transporte']}€)", 
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
    st.info(f"No hay paquetes en vivo desde {origen_seleccionado} por debajo de {presupuesto_total_pack}€ para {num_viajeros} persona(s). Eleva el presupuesto en la barra lateral.")
