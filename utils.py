import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import re

# Función para cargar los datos
@st.cache_data
def load_data():
    url = "https://analisis.datosabiertos.jcyl.es/api/records/1.0/search/?dataset=ayudas-y-subvenciones&q=&rows=10000&sort=-fecha_publicacion"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame([record['fields'] for record in data['records']])

    # Drop duplicates
    df.drop_duplicates(subset='identificador',inplace=True)

    return df

# Logic to remove HTML tags
def limpiar_html(texto):
    # Patrón para coincidir con cualquier tag HTML
    patron = re.compile('<.*?>')
    
    # Reemplazar todos los tags encontrados con una cadena vacía
    texto_limpio = re.sub(patron, '', texto)
    
    return texto_limpio

# Logic to apply prompt to summarise description
def summarize_spanish(text):

    cleaned_text = limpiar_html(text)

    prompt = f"""
    ### Instrucciones ###
    Vas a recibir la descripción de una beca de Castilla y León.
    Resume el texto en español de manera sencilla de entender y en tercera persona:

    {cleaned_text}

     Resumen conciso (máximo 50 palabras): """
    
    response = client.text_generation(
        prompt,
        # model=model,
        max_new_tokens=150,
        temperature=0.01,
        top_k=50,
        top_p=0.95,
        repetition_penalty=1.2
    )
    
    return response

# Logic to assign situacion depending on etapa_vital, destinatarios, materia
def asignar_situacion(df):
    # Crear una copia del DataFrame para no modificar el original
    df_result = df.copy()
    
   # a) Mapear 'etapa_vital' a 'situacion' según el mapeado proporcionado
    mapeado = {
        'Para estudiar y formarse': 'Para estudiar y formarse',
        'Para ayudas a las empresas': 'Para empresas y autónomos',
        'Para trabajar en Castilla y León': 'Para trabajar',
        'En algunas situaciones sociales': 'Para mejorar situaciones sociales',
        'Para acceder y mantener una vivienda': 'Para acceso a vivienda',
        'Para el establecimiento de una empresa': 'Para crear una empresa',
        'Para disfrutar en Castilla y León': 'Para deporte y ocio',
        'Para las familias en Castilla y León': 'Para familias',
        'Para acceder a servicios sanitarios': 'Para acceder a servicios sanitarios'
    }
    
    df_result['situacion'] = df_result['etapa_vital'].map(mapeado)
    
    # b) Aplicar lógicas secuencialmente a las filas donde 'situacion' es nula
    mask_nan = df_result['situacion'].isnull()
    
    # (1) Si Destinatarios contiene Empresas
    mask = mask_nan & df_result['destinatarios'].str.contains('Empresas', na=False)
    df_result.loc[mask, 'situacion'] = 'Para empresas y autónomos'
    mask_nan = df_result['situacion'].isnull()
    
    # (2) Destinatarios sólo contiene Asociaciones
    mask = mask_nan & (df_result['destinatarios'] == 'Asociaciones')
    df_result.loc[mask, 'situacion'] = 'Para Asociaciones'
    mask_nan = df_result['situacion'].isnull()
    
    # (3) Destinatario contiene Asociaciones y otros (menos Empresa)
    mask = mask_nan & df_result['destinatarios'].str.contains('Asociaciones', na=False) & ~df_result['destinatarios'].str.contains('Empresas', na=False)
    df_result.loc[mask, 'situacion'] = 'Para Asociaciones'
    mask_nan = df_result['situacion'].isnull()
    
    # (4) Destinatarios contiene Entidades Locales
    mask = mask_nan & df_result['destinatarios'].str.contains('Entidades Locales', na=False)
    df_result.loc[mask, 'situacion'] = 'Para Entidades Locales'
    mask_nan = df_result['situacion'].isnull()
    
    # (5) Destinatarios solo contiene Ciudadanos
    mask = mask_nan & (df_result['destinatarios'] == 'Ciudadanos')
    df_result.loc[mask, 'situacion'] = 'Para familias'
    mask_nan = df_result['situacion'].isnull()
    
    # (6) Materia contiene Cultura y Patrimonio
    mask = mask_nan & df_result['materia'].str.contains('Cultura y Patrimonio', na=False)
    df_result.loc[mask, 'situacion'] = 'Para Cultura y Patrimonio'
    mask_nan = df_result['situacion'].isnull()
    
    # (7) Destinatarios solo contiene Jóvenes
    mask = mask_nan & (df_result['destinatarios'] == 'Jóvenes')
    df_result.loc[mask, 'situacion'] = 'Para estudiar y formarse'
    mask_nan = df_result['situacion'].isnull()
    
    # (8) Materia contiene Mujer
    mask = mask_nan & df_result['materia'].str.contains('Mujer', na=False)
    df_result.loc[mask, 'situacion'] = 'Para mejorar situaciones sociales'
    mask_nan = df_result['situacion'].isnull()
    
    # (9) Materia contiene Deportes
    mask = mask_nan & df_result['materia'].str.contains('Deportes', na=False)
    df_result.loc[mask, 'situacion'] = 'Para deporte y ocio'
    mask_nan = df_result['situacion'].isnull()
    
    # (10) Materia contiene Empleo
    mask = mask_nan & df_result['materia'].str.contains('Empleo', na=False)
    df_result.loc[mask, 'situacion'] = 'Para trabajar'
    mask_nan = df_result['situacion'].isnull()
    
    # (11) El resto en blanco
    df_result.loc[mask_nan, 'situacion'] = 'Otras ayudas'
    
    return df_result

# Función para obtener valores únicos de la columna 'materias'
def get_unique_materias(df):
    all_materias = set()
    for materias in df['materia'].dropna():
        all_materias.update(materia.strip() for materia in materias.split(','))
    return sorted(all_materias)

# Función para filtrar el DataFrame por materias
def filter_materias(df, selected):
    if not selected:
        return df
    return df[df['materia'].apply(lambda x: any(materia.strip() in selected for materia in str(x).split(',')))]

# Callback function to update session state
def update_filtros(nuevos_filtros):
    st.session_state.filtros["grupo1"] = nuevos_filtros["grupo1"]
    st.session_state.filtros["grupo2"] = nuevos_filtros["grupo2"]
    st.session_state.filtros["situacion"] = nuevos_filtros["situacion"]
    st.session_state.filtros["selected_materias"] = nuevos_filtros["selected_materias"]

def calcular_dias_restantes(df):
    # Asegúrate de que la columna 'Fecha límite' sea de tipo datetime
    df['fecha_limite_date'] = pd.to_datetime(df['fecha_limite'], errors='coerce')
    
    # Obtén la fecha actual
    hoy = datetime.now().date()
    
    # Calcula la diferencia en días
    df['days_left'] = (df['fecha_limite_date'].dt.date - hoy).dt.days



    # Si quieres que los días negativos (fechas pasadas) se muestren como 0, puedes usar:
    # df['days_left'] = (df['Fecha límite'].dt.date - hoy).dt.days.clip(lower=0)
    
    return df

def mostrar_tarjetas_personalizadas(df_to_show, status):

    # Calcular diferencia de días
    df_to_show =  calcular_dias_restantes(df_to_show)

    # Estilos CSS personalizados
    st.markdown("""
    <style>
    .card {
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
        transition: 0.3s;
        border-radius: 5px;
        border: 2px solid #4CAF50;
        padding: 10px;
        background-color: white;
        margin-bottom: 10px;
    }
    .stContainer {
        border: 2px solid #4CAF50;
        border-radius: 10px;
        padding: 20px;
    }
    .days-left-active {
        background-color: #ffebee;
        border-radius: 20px;
        padding: 5px 10px;
        margin: 5px;
        display: inline-block;
        font-weight: bold;
        color: #ff4500;  /* Color rojo-naranja para urgencia */
    }
    .days-left-expired {
        background-color: #f0f0f0;
        border-radius: 20px;
        padding: 5px 10px;
        margin: 5px;
        display: inline-block;
        font-weight: bold;
        color: gray;  /* Color gris */
    }
    .card-title {
        font-size: 14px;
        font-weight: bold;
        color: #333;
    }
    .stButton > button {
        width: 100%;
        margin-top: 10px;
    }
    .fecha-limite {
        margin-bottom: 10px; 
    }
    .burbuja {
        display: inline-block;
        background-color: #f0f0f0;
        border-radius: 15px;
        padding: 5px 10px;
        margin-right: 5px;
        margin-bottom: 10px;
        font-size: 12px;
    }
    .status-bubble-active {
        background-color: #e8f5e9;
        border-radius: 20px;
        padding: 5px 10px;
        display: inline-flex;
        align-items: center;
        font-weight: bold;
    }
    .dot-active {
        color: #4CAF50;
        margin-right: 5px;
    }
    .status-bubble-expired {
        background-color: #f0f0f0;
        border-radius: 20px;
        padding: 5px 10px;
        display: inline-flex;
        align-items: center;
        font-weight: bold;
    }
    .dot-expired {
        color: gray;
        margin-right: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
        

    if status == "active":
        status_beca = "Activa"
        # Las más cercanas primero
        df_to_show = df_to_show.sort_values(by='days_left')
        days_text = "Quedan "
        
    else:
        status_beca = "Expirada"
        # Las más cercanas primero
        df_to_show = df_to_show.sort_values(by='days_left', ascending=False)
        days_text = "Expiró hace "
        # Convert Negatives to Positives
        df_to_show['days_left'] = df_to_show['days_left'].abs()
        

    # st.dataframe(df_to_show[['titulo','etapa_vital','destinatarios','materia','situacion']])  
    df_to_show.reset_index(drop=True, inplace=True)
    
    # Crear columnas para las tarjetas 
    cols = st.columns(2)

    # Iterar sobre las situaciones y crear una tarjeta para cada una
    for index, row in df_to_show.iterrows():
        
        beca_id = row['identificador']

        with cols[index % 2]:
            with st.container(border=True):
                st.markdown(f"""
                
                    <div class="card-title">{row['titulo']}</div>
                    <div class="card-content">
                        <div class="status-bubble-{status}">
                            <span class="dot-{status}">●</span>
                            {status_beca}
                        </div>
                        <div class="days-left-{status}">{days_text}{row['days_left']} días</div>
                        <br>Materias</br>
                        <div>
                            {''.join([f'<span class="burbuja">{materia.strip()}</span>' for materia in row['materia'].split(',')])}
                        </div>
                    </div>
                

                """, unsafe_allow_html=True)

                button_key = f"button-{beca_id}"
                if st.button("Ver más", key=button_key):
                    # Handle button click
                    st.session_state.beca_id = beca_id
                    st.switch_page("pages/details.py")

def limpiar_html(texto):
    # Patrón para coincidir con cualquier tag HTML
    patron = re.compile('<.*?>')
    
    # Reemplazar todos los tags encontrados con una cadena vacía
    texto_limpio = re.sub(patron, '', texto)
    
    return texto_limpio


def section_header(title):
    st.markdown("""
    <style>
    .section-header {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .section-header h4 {
        color: #262730;
        font-weight: bold;
        margin-bottom: 0;
        padding-bottom: 10px;
        border-bottom: 1px solid rgba(128, 128, 128, 0.5);
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="section-header">
        <h4>{title}</h4>
    </div>
    """, unsafe_allow_html=True)