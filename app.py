import streamlit as st
import pandas as pd
import urllib.parse
import httpx
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
# 2. ORÍGENES, FACTOR DE CONECTIVIDAD Y CATÁLOGO MULTIDESTINO
# -----------------------------------------------------------------------------
ORIGENES_DISPONIBLES = {
    "Madrid": {"code": "MAD", "factor_precio": 1.0},
    "Barcelona": {"code": "BCN", "factor_precio": 0.95},
    "Valencia": {"code": "VLC", "factor_precio": 1.15},
    "Málaga": {"code": "AGP", "factor_precio": 1.10},
    "Sevilla": {"code": "SVQ", "factor_precio": 1.15},
    "Bilbao": {"code": "BIO", "factor_precio": 1.25}
}

ESCAPADAS_CATALOGO_AMPLIADO = [
    {
        "destino": "Sofía", "pais": "Bulgaria", "transporte": "Avión Directo", "code": "SOF",
        "duracion": "3 Días / 2 Noches", "hotel_base_noche": 35, 
        "actividad_defecto": "Tour Monasterios de Rila", "precio_actividad_base": 15, 
        "precio_transporte_persona_base": 155,
        "imagen": "https://images.unsplash.com/photo-1573843981267-be1999ff37cd?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Varsovia", "pais": "Polonia", "transporte": "Avión Directo", "code": "WAW",
        "duracion": "3 Días / 2 Noches", "hotel_base_noche": 38, 
        "actividad_defecto": "Concierto Chopin en Casco Antiguo", "precio_actividad_base": 14, 
        "precio_transporte_persona_base": 165,
        "imagen": "https://images.unsplash.com/photo-1519197924294-4ac978a3ef54?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Roma", "pais": "Italia", "transporte": "Avión Directo", "code": "FCO",
        "duracion": "3 Días / 2 Noches", "hotel_base_noche": 45, 
        "actividad_defecto": "Tour Coliseo y Foro Romano", "precio_actividad_base": 30, 
        "precio_transporte_persona_base": 120,
        "imagen": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Fez", "pais": "Marruecos", "transporte": "Avión Directo", "code": "FEZ",
        "duracion": "3 Días / 2 Noches", "hotel_base_noche": 25, 
        "actividad_defecto": "Visita Guiada por la Medina", "precio_actividad_base": 12, 
        "precio_transporte_persona_base": 65,
        "imagen": "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Lisboa", "pais": "Portugal", "transporte": "Avión Directo", "code": "LIS",
        "duracion": "3 Días / 2 Noches", "hotel_base_noche": 40, 
        "actividad_defecto": "Paseo en Barco por el Tajo", "precio_actividad_base": 18, 
        "precio_transporte_persona_base": 85,
        "imagen": "https://images.unsplash.com/photo-1585208798174-6cedd86e019a?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Oporto", "pais": "Portugal", "transporte": "Autobús Nocturno / Tren", "code": "OPO",
        "duracion": "3 Días / 2 Noches", "hotel_base_noche": 32, 
        "actividad_defecto": "Crucero de los 6 Puentes", "precio_actividad_base": 15, 
        "precio_transporte_persona_base": 30,
        "imagen": "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Praga", "pais": "República Checa", "transporte": "Avión Directo", "code": "PRG",
        "duracion": "3 Días / 2 Noches", "hotel_base_noche": 42, 
        "actividad_defecto": "Visita Guiada al Castillo de Praga", "precio_actividad_base": 20, 
        "precio_transporte_persona_base": 135,
        "imagen": "https://images.unsplash.com/photo-1541849546-216549ae216d?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Milán", "pais": "Italia", "transporte": "Avión Directo", "code": "MXP",
        "duracion": "3 Días / 2 Noches", "hotel_base_noche": 48, 
        "actividad_defecto": "Entrada a las Terrazas del Duomo", "precio_actividad_base": 22, 
        "precio_transporte_persona_base": 90,
        "imagen": "https://images.unsplash.com/photo-1513581166391-887a96ddeafd?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "París", "pais": "Francia", "transporte": "Avión Directo", "code": "CDG",
        "duracion": "3 Días / 2 Noches", "hotel_base_noche": 55, 
        "actividad_defecto": "Crucero por el Sena", "precio_actividad_base": 17, 
        "precio_transporte_persona_base": 115,
        "imagen": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Valencia", "pais": "España", "transporte": "Tren Alta Velocidad", "code": "VLC",
        "duracion": "3 Días / 2 Noches", "hotel_base_noche": 40, 
        "actividad_defecto": "Ciudad de las Artes y Ciencias", "precio_actividad_base": 24, 
        "precio_transporte_persona_base": 25,
        "imagen": "https://images.unsplash.com/photo-1590496793929-36417d3117de?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Sevilla", "pais": "España", "transporte": "Tren Alta Velocidad", "code": "SVQ",
        "duracion": "3 Días / 2 Noches", "hotel_base_noche": 42, 
        "actividad_defecto": "Show Flamenco en Triana", "precio_actividad_base": 20, 
        "precio_transporte_persona_base": 35,
        "imagen": "https://images.unsplash.com/photo-1561632669-6e0e99a2245b?auto=format&fit=crop&w=800&q=80"
    },
    {
        "destino": "Burdeos", "pais": "Francia", "transporte": "Autobús Nocturno / Tren", "code": "BOD",
        "duracion": "3 Días / 2 Noches", "hotel_base_noche": 38, 
        "actividad_defecto": "Cata de Vinos en Cité du Vin", "precio_actividad_base": 22, 
        "precio_transporte_persona_base": 45,
        "imagen": "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=800&q=80"
    }
]

# -----------------------------------------------------------------------------
# 3. MOTORES DE PRECIOS REALES EN LOTE (SIN RALENTIZAR LA APP)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=1800)
def obtener_mapa_vuelos_reales_origen(origen_code):
    """
    Descarga en una única llamada todas las tarifas reales de Ida y Vuelta 
    registradas en las últimas 48h desde el origen seleccionado.
    """
    tp_token = st.secrets.get("TRAVELPAYOUTS_KEY", None)
    mapa_precios = {}
    if not tp_token:
        return mapa_precios

    try:
        url = "https://api.travelpayouts.com/v2/prices/latest"
        headers = {"X-Access-Token": tp_token}
        params = {
            "origin": origen_code,
            "currency": "EUR",
            "period_type": "year",
            "one_way": "false",       # ÚNICAMENTE IDA Y VUELTA
            "sorting": "price",
            "limit": 100
        }
        resp = httpx.get(url, headers=headers, params=params, timeout=6.0)
        data = resp.json()

        if data.get("success") and "data" in data:
            for item in data["data"]:
                dest = item.get("destination")
                precio = float(item.get("value", 0))
                if dest and precio > 0:
                    # Guardamos la tarifa media si hay varias entradas para el mismo destino
                    if dest in mapa_precios:
                        mapa_precios[dest]["precios"].append(precio)
                    else:
                        mapa_precios[dest] = {
                            "precios": [precio],
                            "depart_date": item.get("depart_date", "")[:10],
                            "return_date": item.get("return_date", "")[:10]
                        }
    except Exception:
        pass
    return mapa_precios

@st.cache_data(ttl=3600)
def obtener_chollos_klook_live(destino_nombre):
    """Consulta la API de Klook para extraer la experiencia más económica por persona."""
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
        resp = httpx.get(url, headers=headers, params=params, timeout=4.0)
        data = resp.json()
        
        if "items" in data and len(data["items"]) > 0:
            items_validos = [i for i in data["items"] if "price" in i and float(i["price"]) > 0]
            if items_validos:
                item_chollo = min(items_validos, key=lambda x: float(x["price"]))
                return {
                    "actividad": item_chollo.get("title", f"Experiencia Top en {destino_nombre}"),
                    "precio_unitario": float(item_chollo.get("price")),
                    "url_directa": item_chollo.get("deep_link") or item_chollo.get("url")
                }
    except Exception:
        pass
    return None

def generar_enlaces_escapada(tipo_transporte, origen_nombre, destino_nombre, origen_code, destino_code, num_pasajeros, f_ida_api=None, f_vta_api=None, url_klook_actividad_api=None):
    """Genera URLs dinámicas directas sincronizadas con fechas y pasajeros."""
    def simplificar(t):
        r = {'á':'a', 'é':'e', 'í':'i', 'ó':'o', 'ú':'u', 'ñ':'n'}
        t = t.lower()
        for k, v in r.items():
            t = t.replace(k, v)
        return t.strip().replace(" ", "-")

    origen_slug = simplificar(origen_nombre)
    destino_slug = simplificar(destino_nombre)

    if f_ida_api and f_vta_api:
        try:
            dt_ida = datetime.strptime(f_ida_api, "%Y-%m-%d")
            dt_vta = datetime.strptime(f_vta_api, "%Y-%m-%d")
            # Asegurar que las fechas devueltas estén en el futuro
            if dt_ida < datetime.now():
                raise ValueError("Fecha pasada")
        except Exception:
            dt_ida = datetime.now() + timedelta(days=14)
            dt_vta = datetime.now() + timedelta(days=17)
    else:
        dt_ida = datetime.now() + timedelta(days=14)
        dt_vta = datetime.now() + timedelta(days=17)

    # 1. Enlace Transporte
    if "Avión" in tipo_transporte:
        dia_ida, mes_ida = dt_ida.strftime("%d"), dt_ida.strftime("%m")
        dia_vta, mes_vta = dt_vta.strftime("%d"), dt_vta.strftime("%m")
        url_trans = f"https://www.aviasales.com/search/{origen_code}{dia_ida}{mes_ida}{destino_code}{dia_vta}{mes_vta}{num_pasajeros}"
    elif "Tren" in tipo_transporte or "Autobús" in tipo_transporte:
        url_trans = f"https://www.omio.es/viajes/{origen_slug}/{destino_slug}"
    else:
        url_trans = f"https://www.blablacar.es/search?fn={urllib.parse.quote(origen_nombre)}&tn={urllib.parse.quote(destino_nombre)}"

    # 2. Enlace Alojamiento Klook
    url_hotel = f"https://www.klook.com/es/search/?query={urllib.parse.quote('hotel ' + destino_nombre)}"

    # 3. Enlace Experiencia Klook
    if url_klook_actividad_api and str(url_klook_actividad_api).startswith("http"):
        url_actividad = url_klook_actividad_api
    else:
        url_actividad = f"https://www.klook.com/es/search/?query={urllib.parse.quote('actividades ' + destino_nombre)}"

    return url_trans, url_hotel, url_actividad

# -----------------------------------------------------------------------------
# 4. BARRA LATERAL (CONTROLES)
# -----------------------------------------------------------------------------
st.sidebar.markdown("### CONFIGURACIÓN DEL VIAJE")
origen_seleccionado = st.sidebar.selectbox("Ciudad de Salida", list(ORIGENES_DISPONIBLES.keys()), index=0)
datos_origen = ORIGENES_DISPONIBLES[origen_seleccionado]
codigo_origen_actual = datos_origen["code"]
factor_origen = datos_origen["factor_precio"]

# Por defecto: 1 viajero
num_viajeros = st.sidebar.number_input("Número de Viajeros 👤", min_value=1, max_value=8, value=1, step=1)

st.sidebar.markdown("---")
presupuesto_total_pack = st.sidebar.slider(f"Presupuesto MÁXIMO Pack Total ({num_viajeros} p) (€)", 100, 2000, 650, step=25)

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
st.caption(f"Radar de Escapadas 'All-in-One' (Ida y Vuelta) desde {origen_seleccionado}")

tp_activa = "TRAVELPAYOUTS_KEY" in st.secrets

if tp_activa:
    st.success(f"🟢 API Travelpayouts Conectada: Sincronización de rutas desde {origen_seleccionado} ({codigo_origen_actual}) para {num_viajeros} viajero(s)")

st.write("")

# Obtener mapa de precios reales en una sola consulta rápida
mapa_vuelos_live = obtener_mapa_vuelos_reales_origen(codigo_origen_actual) if tp_activa else {}

escapadas_filtradas = []

for item in ESCAPADAS_CATALOGO_AMPLIADO:
    if item["destino"].lower() == origen_seleccionado.lower():
        continue
        
    if not any(t in item["transporte"] for t in filtro_transporte):
        continue

    # 1. Cálculo realista de vuelo Ida y Vuelta según origen
    precio_referencia_ajustado = item["precio_transporte_persona_base"] * factor_origen
    precio_persona_final = precio_referencia_ajustado
    es_dato_api = False
    f_ida_api = None
    f_vta_api = None

    if "Avión" in item["transporte"] and item["code"] in mapa_vuelos_live:
        info_ruta = mapa_vuelos_live[item["code"]]
        lista_precios = info_ruta["precios"]
        # Filtrar precios reales de ida y vuelta descartando errores de caché
        precios_validos = [
            p for p in lista_precios 
            if (precio_referencia_ajustado * 0.60) <= p <= (precio_referencia_ajustado * 1.65)
        ]
        if precios_validos:
            # Promedio de los precios reales encontrados para esa ruta
            precio_persona_final = sum(precios_validos) / len(precios_validos)
            es_dato_api = True
            f_ida_api = info_ruta["depart_date"]
            f_vta_api = info_ruta["return_date"]

    precio_transporte_total = int(round(precio_persona_final * num_viajeros))

    # 2. Experiencia Klook y URL directa
    nombre_actividad = item["actividad_defecto"]
    precio_actividad_unitario = item["precio_actividad_base"]
    url_klook_api = None

    if tp_activa:
        datos_klook = obtener_chollos_klook_live(item["destino"])
        if datos_klook:
            nombre_actividad = datos_klook["actividad"]
            precio_actividad_unitario = datos_klook["precio_unitario"]
            url_klook_api = datos_klook.get("url_directa")

    precio_actividad_total = int(round(precio_actividad_unitario * num_viajeros))

    # 3. Alojamiento (2 Noches)
    precio_alojamiento_total = int(item["hotel_base_noche"] * 2)

    # 4. Precio Pack Total
    precio_total_pack = int(precio_transporte_total + precio_alojamiento_total + precio_actividad_total)

    if precio_total_pack <= presupuesto_total_pack:
        url_trans, url_hotel, url_act = generar_enlaces_escapada(
            item["transporte"], origen_seleccionado, item["destino"], codigo_origen_actual, item["code"], num_viajeros, f_ida_api, f_vta_api, url_klook_api
        )

        escapadas_filtradas.append({
            "destino": item["destino"],
            "pais": item["pais"],
            "duracion": item["duracion"],
            "transporte": item["transporte"],
            "imagen": item["imagen"],
            "precio_transporte": precio_transporte_total,
            "precio_alojamiento": precio_alojamiento_total,
            "actividad_nombre": nombre_actividad,
            "precio_actividad": precio_actividad_total,
            "precio_total": precio_total_pack,
            "es_live": es_dato_api,
            "url_transporte": url_trans,
            "url_hotel": url_hotel,
            "url_actividad": url_act
        })

# Ordenar de menor a mayor precio total
escapadas_filtradas = sorted(escapadas_filtradas, key=lambda x: x["precio_total"])

if escapadas_filtradas:
    cols = st.columns(2)
    for idx, pack in enumerate(escapadas_filtradas):
        col = cols[idx % 2]
        with col:
            with st.container(border=True):
                st.image(pack["imagen"], use_container_width=True)
                
                etiqueta_origen = " • Tarifa Live Ruta" if pack["es_live"] else f" • Estimación desde {origen_seleccionado}"
                st.caption(f"{pack['duracion']} • {pack['transporte']} (Ida y Vuelta){etiqueta_origen}")
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
