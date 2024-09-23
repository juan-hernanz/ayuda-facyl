import streamlit as st
import pandas as pd
import datetime
from utils import load_data,get_unique_materias, filter_materias, update_filtros, mostrar_tarjetas_personalizadas



# Datos de mapeo
grupo_mapping = {
    "Persona": ["Ciudadano","Estudiante", "En situación vulnerable"],
    "Entidad": ["Empresa o Autónomo", "Asociación", "Entidad Local o Empleado Público", 
                "Universidad", "Fundación", "Colegio Profesional", "Otra Entidad"]
}

situacion_mapping = {
    ("Persona", "Estudiante"): ["Para estudiar y formarse", "Para empresas y autónomos", "Para trabajar", 
                                "Para mejorar situaciones sociales", "Para acceso a vivienda", 
                                "Para deporte y ocio", "Para Asociaciones"],
    ("Persona", "En situación vulnerable"): ["Para empresas y autónomos", "Para trabajar", 
                                             "Para mejorar situaciones sociales", "Para deporte y ocio"],
    ("Persona", "Ciudadano"): ["Para estudiar y formarse", "Para empresas y autónomos", "Para trabajar", 
                               "Para mejorar situaciones sociales", "Para acceso a vivienda", 
                               "Para crear una empresa", "Para deporte y ocio", "Para familias", 
                               "Para acceder a servicios sanitarios", "Para Asociaciones", 
                               "Para Entidades Locales", "Para Cultura y Patrimonio", "Otras ayudas"],
    ("Entidad", "Empresa o Autónomo"): ["Para estudiar y formarse", "Para empresas y autónomos", 
                                        "Para trabajar", "Para mejorar situaciones sociales", 
                                        "Para crear una empresa"],
    ("Entidad", "Asociación"): ["Para estudiar y formarse", "Para empresas y autónomos", "Para trabajar", 
                                "Para mejorar situaciones sociales", "Para deporte y ocio", 
                                "Para Asociaciones"],
    ("Entidad", "Entidad Local o Empleado Público"): ["Para estudiar y formarse", "Para trabajar", 
                                                      "Para Asociaciones", "Para Entidades Locales"],
    ("Entidad", "Universidad"): ["Para estudiar y formarse", "Para Asociaciones", "Para Cultura y Patrimonio"],
    ("Entidad", "Fundación"): ["Para estudiar y formarse", "Para Asociaciones"],
    ("Entidad", "Colegio Profesional"): ["Para Asociaciones"],
    ("Entidad", "Otra Entidad"): ["Para estudiar y formarse", "Para empresas y autónomos", "Para trabajar", 
                                  "Para mejorar situaciones sociales", "Para acceso a vivienda", 
                                  "Para crear una empresa", "Para deporte y ocio", "Para familias", 
                                  "Para acceder a servicios sanitarios", "Para Asociaciones", 
                                  "Para Entidades Locales", "Para Cultura y Patrimonio", "Otras ayudas"]
}

def show_listado_ayudas():
    st.title("Listado de Ayudas")

    # Estilos CSS personalizados
    st.markdown("""
    <style>
    .status-bubble-active {
        background-color: #e8f5e9;
        color: #4CAF50;
        border-radius: 20px;
        padding: 5px 10px;
        font-weight: bold;
        display: inline-block;
        margin-bottom:5px;
    }
    .dot-active {
        color: #4CAF50;
        margin-right: 5px;
    }
    .status-bubble-expired {
        background-color: #f0f0f0;
        color: gray;
        border-radius: 20px;
        padding: 5px 10px;
        font-weight: bold;
        display: inline-block;
    }
    .dot-expired {
        color: gray;
        margin-right: 5px;
    }

    .stButton > button {
        width: 100%;
        margin-top: 10px;
    }

    .green-dot {
        color: green;
        font-weight: bold;
        margin-right: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Check and initialise session state variables
    if 'df_full' not in st.session_state:
        df_result = load_data()
        st.session_state['df_full'] = df_result

    else:
        df_result = st.session_state.df_full

    if 'filtros' not in st.session_state:
        st.session_state['filtros'] = {
                    "grupo1": "Persona",
                    "grupo2": "Ciudadano",
                    "situacion": "Para estudiar y formarse"
                }


    
    # # Crear un expander para los filtros
    with st.expander("Modificar filtros"):


        col_grupo, col_situacion, col_materias, col_button = st.columns([3, 2, 2,1])

        # Sección 1: Grupo
        with col_grupo:
            # st.write("¿A qué grupo pertecenes?")
            col_grupo1, col_grupo2 = st.columns(2)

            with col_grupo1:
                grupo1 = st.selectbox("Solicitante", ["Persona", "Entidad"],
                                    key="sb_grupo1",
                                    index=["Persona", "Entidad"].index(st.session_state.filtros["grupo1"]) if st.session_state.filtros["grupo1"] else 0
                                    )
            with col_grupo2:
                grupo2 = st.selectbox("Elige la más adecuada", 
                                    (grupo_mapping.get(grupo1, []) if grupo1 else []),
                                    key="sb_grupo2",
                                    index=grupo_mapping.get(grupo1, []).index(st.session_state.filtros["grupo2"]) if st.session_state.filtros["grupo2"] in grupo_mapping.get(grupo1, []) else 0,
                                    disabled=not grupo1)

        # Sección 2: Situación
        with col_situacion:
            
            # st.write("¿Qué tipo de ayuda buscas?")
            situacion = st.selectbox("Una ayuda ...", 
                                    (situacion_mapping.get((grupo1, grupo2), []) if grupo1 and grupo2 else []), 
                                    key="sb_situacion",
                                    index=situacion_mapping.get((grupo1, grupo2), []).index(st.session_state.filtros["situacion"]) if st.session_state.filtros["situacion"] in situacion_mapping.get((grupo1, grupo2), []) else 0,
                                    disabled=not (grupo1 and grupo2))


        # Aplicar filtros y mostrar resultados
        if st.session_state.sb_grupo2:
            # Define el mapeo de grupo2 a destinatarios
            destinatarios_mapping = {
                "Estudiante": ["Jóvenes", "Menores"],
                "En situación vulnerable": ["Mujer", "Personas con discapacidad", "Mayores"],
                "Ciudadano": ["Otros destinatarios", "Ciudadanos", "Jóvenes", "Mujer", "Personas con discapacidad", "Menores", "Mayores", "Empleados públicos"],
                "Empresa o Autónomo": ["Empresas y autónomos"],
                "Asociación": ["Asociaciones"],
                "Entidad Local o Empleado Público": ["Empleados públicos", "Entidades Locales"],
                "Universidad": ["Universidades"],
                "Fundación": ["Fundaciones"],
                "Colegio Profesional": ["Colegios Profesionales"],
                "Otra Entidad": ["Otros destinatarios", "Ciudadanos"]
            }

            # Obtén los destinatarios permitidos para el grupo2 seleccionado
            destinatarios_permitidos = destinatarios_mapping.get(st.session_state.sb_grupo2, [])

            # Función para verificar si alguno de los destinatarios permitidos está en el campo 'destinatarios'
            def contiene_destinatario_permitido(destinatarios):

                if pd.isna(destinatarios):
                    return False
                return any(dest in destinatarios for dest in destinatarios_permitidos)

            # Aplica el filtro
            df_result = df_result[df_result['destinatarios'].apply(contiene_destinatario_permitido)]

        if st.session_state.sb_situacion:
            
            df_result = df_result[df_result['situacion'] == st.session_state.sb_situacion]


            option_materias = get_unique_materias(df_result)

            # Determinar los valores por defecto
            default_materias = []
            if 'filtros' in st.session_state and 'selected_materias' in st.session_state.filtros:
                # Filtrar solo las materias que existen en las opciones actuales
                default_materias = [m for m in st.session_state.filtros['selected_materias'] if m in option_materias]


            # Sección 3: Áreas de Interés
            with col_materias:
                # st.write("Áreas de Interés")
                selected_materias = st.multiselect(
                    "Selecciona las materias:",
                    options=option_materias,
                    default = default_materias ,
                    key="ms_materias"
                )

        if selected_materias:
            df_result= filter_materias(df_result, selected_materias)

    
    # Mostrar conteos
    # Filtrar becas personalizadas
    today = datetime.date.today()
    df_result['fecha_limite'] = pd.to_datetime(df_result['fecha_limite']).dt.date
    active_df_personalised= df_result[df_result['fecha_limite'] >= today]
    expired_df_personalised = df_result[df_result['fecha_limite'] < today]

    # Crear columnas para las tarjetas
    # col_active, col_expired = st.columns(2)  # Puedes ajustar el número de columnas según tus preferencias


    # Obtener el conteo de becas activas
    # with col_active:
    if active_df_personalised.empty:
        st.warning("No hay ayudas activas para tu búsqueda.")
    else:
        active_counts = active_df_personalised.shape[0]
        st.markdown(f"""
        <div class="status-bubble-active">
            <span class="dot-active">●</span> Ayudas activas: {active_counts}
        </div>
        """, unsafe_allow_html=True)

    # Obtener el conteo de becas expiradas
    # with col_expired:
    if expired_df_personalised.empty:
        st.warning("No hay ayudas expiradas para tú búsqueda.")
    else:
        expired_counts = expired_df_personalised.shape[0]
        st.markdown(f"""
        <div class="status-bubble-expired">
            <span class="dot-expired">●</span> Ayudas expiradas: {expired_counts}
        </div>
    """, unsafe_allow_html=True)

    # Botón para actualizar la búsqueda
    if (~df_result.empty):
        with col_button:
            if st.button("Ver resultados"):
                st.session_state.filtros = {
                    "grupo1": grupo1,
                    "grupo2": grupo2,
                    "situacion": situacion,
                    "selected_materias": selected_materias,
                }

                # st.session_state.df_personalised_requested = df_result
                
                st.session_state.df_active_personalised_requested= df_result[df_result['fecha_limite'] >= today]
                st.session_state.df_expired_personalised_requested = df_result[df_result['fecha_limite'] < today]

    
    # Listado de becas activas
    st.subheader("Ayudas activas:")

    if st.session_state.df_active_personalised_requested.empty:
        st.warning("No hay becas activas para tu búsqueda.")

    else:
        mostrar_tarjetas_personalizadas(st.session_state.df_active_personalised_requested, status="active")
        

    # Listado de becas expiradas
    st.subheader("Ayudas pasadas:")
    if st.session_state.df_expired_personalised_requested.empty:
        st.warning("No hay becas expiradas para tu búsqueda.")

    else:
        mostrar_tarjetas_personalizadas(st.session_state.df_expired_personalised_requested, status="expired")

          
   

    # # Buscador por keyword
    # keyword = st.text_input("Buscar por título:")
    # if keyword:
    #     df_resultado_keyword = df_becas[df_becas["titulo"].str.contains(keyword, case=False)]
    #     # Mostrar resultados
    #     st.write(f"Se encontraron {len(df_resultado_keyword)} becas:")
    #     st.dataframe(df_resultado_keyword)



#     return df_filtered

if __name__ == "__main__":
    show_listado_ayudas()