import streamlit as st
import pandas as pd

# Configuración visual de la página
st.set_page_config(page_title="Buscador de Escapadas", page_icon="✈️", layout="wide")

st.title("✈️ Buscador de Escapadas Económicas")
st.write("Encuentra viajes de fin de semana en tiempo real al mejor precio.")

# Sidebar (Menú lateral para filtros visuales)
st.sidebar.header("Tus Preferencias")
opcion = st.sidebar.radio("Modo de búsqueda:", ["Escapada por Presupuesto", "Buscar Destino Específico"])

# Datos de prueba (aquí conectarás la API en tiempo real)
datos_vuelos = pd.DataFrame([
    {"Destino": "Oporto", "Precio (€)": 32, "Días": 3, "lat": 41.1579, "lon": -8.6291},
    {"Destino": "Roma", "Precio (€)": 45, "Días": 3, "lat": 41.9028, "lon": 12.4964},
    {"Destino": "Londres", "Precio (€)": 55, "Días": 4, "lat": 51.5074, "lon": -0.1278},
    {"Destino": "París", "Precio (€)": 80, "Días": 3, "lat": 48.8566, "lon": 2.3522},
])

if opcion == "Escapada por Presupuesto":
    presupuesto = st.sidebar.slider("Presupuesto máximo (€)", 20, 200, 60, step=5)

    # Filtrar resultados
    resultados = datos_vuelos[datos_vuelos["Precio (€)"] <= presupuesto]

    st.subheader(f"Destinos disponibles por menos de {presupuesto}€")

    if not resultados.empty:
        # Métricas visuales
        col1, col2 = st.columns(2)
        mejor_opcion = resultados.loc[resultados["Precio (€)"].idxmin()]
        col1.metric(label="Opción más barata", value=f"{mejor_opcion['Destino']}", delta=f"{mejor_opcion['Precio (€)']} €")

        # Tabla interactiva y Mapa
        st.dataframe(resultados[["Destino", "Precio (€)", "Días"]], use_container_width=True)
        st.map(resultados, latitude="lat", longitude="lon")
    else:
        st.warning("No hay escapadas disponibles por debajo de ese presupuesto.")

elif opcion == "Buscar Destino Específico":
    ciudad = st.text_input("Introduce la ciudad a la que quieres viajar:", "Roma")
    coincidencia = datos_vuelos[datos_vuelos["Destino"].str.lower() == ciudad.lower()]

    if not coincidencia.empty:
        precio = coincidencia.iloc[0]["Precio (€)"]
        st.success(f"¡Encontrado! El mejor precio a **{ciudad.capitalize()}** es de **{precio}€**.")
    else:
        st.error(f"No encontramos vuelos directos económicos a {ciudad}.")
