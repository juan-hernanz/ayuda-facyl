import streamlit as st
import pandas as pd
import datetime
 
import os

from utils import load_data, asignar_situacion, get_unique_materias, filter_materias



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

def show_home():

    # Configuración de la página
    st.set_page_config(
        page_title="Buscador de Becas de Castilla y León",
        initial_sidebar_state="collapsed",
        layout="wide"
    )

    # Título
    st.title("**Ayuda Fá**cyl")
    st.subheader("""Encuentra la Subvención o Beca que se ajuste a ti.""")
    st.subheader("""Nosotros te ayudamos a entenderla""")


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
    .card:hover {
        box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2);
    }

    .card-title {
        font-size: 14px;
        font-weight: bold;
        color: #333;
    }
    .card-content {
        font-size: 14px;
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
    </style>
    """, unsafe_allow_html=True)

    # Cargar los datos
    df = load_data()

    # Asignar situaciones a las becas
    df_result = asignar_situacion(df)
    st.session_state.df_full = df_result

    col_izquierda, spacer, col_derecha = st.columns([1, 0.1, 1])

    # Columna derecha: Becas activas
    with col_derecha:
        st.header("Ayudas Activas")

        # Filtrar becas activas
        today = datetime.date.today()
        df_result['fecha_limite'] = pd.to_datetime(df_result['fecha_limite']).dt.date
        active_df = df_result[df_result['fecha_limite'] >= today]

        # Obtener el conteo de becas por situación
        situacion_counts = active_df['situacion'].value_counts()

        # Crear columnas para las tarjetas (ajusta el número según tus preferencias)
        cols = st.columns(2)

        # Iterar sobre las situaciones y crear una tarjeta para cada una
        for i, (situacion, count) in enumerate(situacion_counts.items()):
            with cols[i % 2]:
            #     st.markdown(f"""
            #     <div class="card">
            #         <div class="card-title">{situacion}</div>
            #         <div class="card-content">
            #             <span class="green-dot">●</span> Ayudas activas: {count}
            #         </div>
            #     </div>
            # """, unsafe_allow_html=True)
                st.markdown("""
                <style>
                button[kind="primary"] {
                    background: none!important;
                    border: none;
                    padding: 5px;
                    color: black !important;
                    background-color: #e8f5e9 !important;
                    text-decoration: none;
                    cursor: pointer;
                    border-radius: 15px;
                    box-shadow: 0px 0px 6px rgb(0, 163, 108, 0.8);
                    transition: all 0.3s ease;
                }
                button[kind="primary"]:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 2px 6px rgb(0, 163, 108, 0.8);
                }
                </style>
                """, unsafe_allow_html=True)

                if st.button(f"{situacion}: **{count}**", type="primary", key=situacion):
                    st.session_state['filtros'] = {
                        "grupo1": "",
                        "grupo2":"",
                        "situacion": f"{situacion}",

                    }
                    st.switch_page("pages/listado_ayudas.py")


        

    # Columna izquierda: Buscador
    with col_izquierda:
        st.header("Buscador de Ayudas personalizado")

        # Sección 1: Grupo
        st.subheader("¿A qué grupo pertecenes?")
        col1, col2 = st.columns(2)

        with col1:
            grupo1 = st.selectbox("Solicitante", ["Persona", "Entidad"])

        with col2:
            grupo2 = st.selectbox("Elige la más adecuada", (grupo_mapping.get(grupo1, []) if grupo1 else []), 
                                disabled=not grupo1)

        # Sección 2: Situación
        st.subheader("¿Qué tipo de ayuda buscas?")
        situacion = st.selectbox("Una ayuda ...", 
                                (situacion_mapping.get((grupo1, grupo2), []) if grupo1 and grupo2 else []), 
                                disabled=not (grupo1 and grupo2))

        # Aplicar filtros
        if grupo2:

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
            destinatarios_permitidos = destinatarios_mapping.get(grupo2, [])

            # Función para verificar si alguno de los destinatarios permitidos está en el campo 'destinatarios'
            def contiene_destinatario_permitido(destinatarios):

                if pd.isna(destinatarios):
                    return False
                return any(dest in destinatarios for dest in destinatarios_permitidos)

            # Aplica el filtro
            df_result = df_result[df_result['destinatarios'].apply(contiene_destinatario_permitido)]

        if situacion:
            df_result = df_result[df_result['situacion']==(situacion)]

            # Sección 3: Áreas de Interés
            st.subheader("Áreas de Interés")
            # Crear el multiselect
            selected_materias = st.multiselect(
                "Selecciona las materias:",
                options=get_unique_materias(df_result),
                default=[]
            )

        if selected_materias:
            df_result = filter_materias(df_result, selected_materias)



        # Mostrar resultados
        st.subheader("Resultados para ti:")
        st.session_state.df_filtered_start = df_result
        

        # Filtrar becas personalizadas
        today = datetime.date.today()
        df_result['fecha_limite'] = pd.to_datetime(df_result['fecha_limite']).dt.date
        active_df_personalised= df_result[df_result['fecha_limite'] >= today]
        expired_df_personalised = df_result[df_result['fecha_limite'] < today]

        st.session_state.df_active_personalised_requested = active_df_personalised
        st.session_state.df_expired_personalised_requested = expired_df_personalised

        # Crear columnas para las tarjetas
        col_active, col_expired = st.columns(2)  # Puedes ajustar el número de columnas según tus preferencias


        # Obtener el conteo de becas activas
        with col_active:
            if active_df_personalised.empty:
                st.warning("No hay ayudas activas para tu búsqueda.")
            else:
                active_counts = active_df_personalised.shape[0]
                st.markdown(f"""
                    <div class="status-bubble-active">
                        <span class="dot-active">●</span> Ayudas activas: {active_counts}
                    </div>
                """, unsafe_allow_html=True)

            # Obtener el conteo de becas activas
        with col_expired:
            if expired_df_personalised.empty:
                st.warning("No hay ayudas expiradas para tú búsqueda.")
            else:
                expired_counts = expired_df_personalised.shape[0]
                st.markdown(f"""
                    <div class="status-bubble-expired">
                        <span class="dot-expired">●</span> Ayudas expiradas: {expired_counts}
                    </div>
                """, unsafe_allow_html=True)

        if (~active_df_personalised.empty | ~expired_df_personalised.empty):
            if st.button("Ver resultados"):
                st.session_state.filtros = {
                    "grupo1": grupo1,
                    "grupo2": grupo2,
                    "situacion": situacion,
                    "selected_materias": selected_materias,
                }
                st.switch_page("pages/listado_ayudas.py")
                    
if __name__ == "__main__":
    show_home()

    

