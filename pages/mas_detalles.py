import streamlit as st
import pandas as pd
from huggingface_hub import InferenceClient
from utils import limpiar_html, calcular_dias_restantes, section_header
from pages.listado_ayudas import show_listado_ayudas
from utils import limpiar_html
from streamlit_gsheets import GSheetsConnection
from datetime import datetime


st.markdown("""
<style>
.status-bubble-active {
    background-color: #e8f5e9;
    color: #4CAF50;
    border-radius: 20px;
    padding: 5px 10px;
    margin: 5px;
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
    color: gray;
    border-radius: 20px;
    padding: 5px 10px;
    margin: 5px;
    display: inline-flex;
    align-items: center;
    font-weight: bold;
}
.dot-expired {
    color: gray;
    margin-right: 5px;
}
.burbuja {
    background-color: #f0f0f0;
    color: #333;
    border-radius: 20px;
    padding: 5px 10px;
    margin: 5px;
    display: inline-block;
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

.fecha-limite {
    margin-bottom: 10px; 
}

.link-bubble {
    background-color: #f0f0f0;
    border-radius: 20px;
    padding: 8px 15px;
    text-decoration: none;
    color: #ff4500;
    font-weight: bold;
    display: inline-block;
    transition: background-color 0.3s, transform 0.3s;
}
.link-bubble:hover {
    background-color: #e0e0e0;
    transform: scale(1.05);
    text-decoration: none;
}


</style>
""", unsafe_allow_html=True)


def show_details():

    # Check and initialise session state variables
    if 'beca_id' not in st.session_state:
        show_listado_ayudas()
    
    # Add Frame for container
    container = st.container(border=True)


    with container:

        # Find beca details
        full_df = st.session_state.df_full 
        beca_id= st.session_state.beca_id

        # Add days-left column
        full_df = calcular_dias_restantes(full_df)

        # Fetch the details of the selected beca from your dataframe
        ayuda_details = full_df[full_df['identificador'] == beca_id].iloc[0]

                # 1. Mostrar Título
        st.subheader(f"{ayuda_details['titulo']}")

        # Determine status
        if ayuda_details['days_left']>=0:
            status = 'active'
            status_text = 'Activa'
            dias_text = 'Quedan '
        else:
            status = 'expired'
            status_text = 'Expirada'
            dias_text = 'Expiró hace '

        # Check if beca_id has been processed by ai
        status_ai, ayuda_ai_df = generando_datos_ayuda(ayuda_details)
        
        # ai data is available
        if status_ai:
            # Convert ai results from df to dictionary
            ayuda_ai = ayuda_ai_df.to_dict('records')[0]

             # 2. Crear columnas para detalles debajo del título
            col_left, col_mid, col_right= st.columns([0.27,0.35,0.38]) 


            with col_left:
                # Mostrar estado
                st.markdown(f"""
                <div class="status-bubble-{status}">
                    <span class="dot-{status}">●</span>
                    {status_text}
                </div>
                """, unsafe_allow_html=True)

                # Mostrar días restantes
                st.markdown(f"""
                    <div class="days-left-{status}">{dias_text}{int(abs(ayuda_details['days_left']))} días</div>
                """, unsafe_allow_html=True)

                # Mostrar lugar presentación
                st.markdown(f"""
                    <div class="burbuja">{ayuda_ai['ai_lugar']}</div>
                """, unsafe_allow_html=True)

            with col_mid:
                # Mostrar fechas
                
                st.write(f"**Fecha publicación**: {ayuda_details['fecha_publicacion']}")
                st.write(f"**Fecha límite**: {ayuda_details['fecha_limite']}")
            
                # Enlace a la ayuda
                st.markdown(f"""

                    <a href="{ayuda_details['enlace_contenido']}" 
                    class="link-bubble" 
                    title="Ir al portal oficial" 
                    target="_blank">
                        🔗 Ver ayuda original
                    </a>
                    """, unsafe_allow_html=True)

            with col_right:
                # Mostrar materias
                st.markdown(f"""
                        {''.join([f'<span class="burbuja">{materia.strip()}</span>' for materia in ayuda_details['materia'].split(',')])}
                    """,
                    unsafe_allow_html=True)

            # Descripcion de la beca
            section_header("✨ Descripción comprensible")
            st.write(f"""{ayuda_ai['ai_descripcion']}""")


            # Beneficiarios
            section_header("👥 ¿Quién puede solicitar la ayuda?")
            st.write(f"""{ayuda_ai['ai_beneficiarios']}""") 

            # Requisitos
            section_header("📋 Requisitos")
            st.markdown(f"""
            {ayuda_ai['ai_requisitos']}
            """, unsafe_allow_html=True)

            # Cuantía
            section_header("💶 Cuantía")
            st.markdown(f"""
            {ayuda_ai['ai_cuantia']}
            """, unsafe_allow_html=True)

            # ¿Y luego qué?
            section_header("⏩  ¿Y luego qué?")
            st.markdown(f"""
            {ayuda_ai['ai_despues']}
            """, unsafe_allow_html=True)

        # ai data is available and too many requests
        else:
            # 2. Crear columnas para detalles debajo del título
            col_left, col_mid, col_right= st.columns([0.27,0.35,0.38]) 


            with col_left:
                # Mostrar estado
                st.markdown(f"""
                <div class="status-bubble-{status}">
                    <span class="dot-{status}">●</span>
                    {status_text}
                </div>
                """, unsafe_allow_html=True)

                # Mostrar días restantes
                st.markdown(f"""
                    <div class="days-left-{status}">{dias_text}{int(abs(ayuda_details['days_left']))} días</div>
                """, unsafe_allow_html=True)


            with col_mid:
                # Mostrar fechas
                
                st.write(f"**Fecha publicación**: {ayuda_details['fecha_publicacion']}")
                st.write(f"**Fecha límite**: {ayuda_details['fecha_limite']}")
            
                # Enlace a la ayuda
                st.markdown(f"""

                    <a href="{ayuda_details['enlace_contenido']}" 
                    class="link-bubble" 
                    title="Ir al portal oficial" 
                    target="_blank">
                        🔗 Ver ayuda original
                    </a>
                    """, unsafe_allow_html=True)

            with col_right:
                # Mostrar materias
                st.markdown(f"""
                        {''.join([f'<span class="burbuja">{materia.strip()}</span>' for materia in ayuda_details['materia'].split(',')])}
                    """,
                    unsafe_allow_html=True)

            st.warning("""
                        👀 Mucha gente está usando nuestra página y estamos dando prioridad a las **ayudas activas**.  
                        ✅ Te recomendamos esperar un poco y explorar la ayuda orginal pinchando en el link.
                        """)
        
        



       

@st.cache_data(ttl=0)
def generando_datos_ayuda(ayuda_row):

    ayuda_id = ayuda_row['identificador']
    print(ayuda_id)

    # Read the database
    st.cache_data.clear()
    gs_conn = st.connection("gsheets", type=GSheetsConnection)
    gs_db = gs_conn.read()
    gs_df  = pd.DataFrame(gs_db)
    gs_df['ayuda_id'] = gs_df['ayuda_id'].astype(int)

    # print(gs_df[gs_df['ayuda_id']==ayuda_id])

    # Check if ayuda_id has been processed
    if ayuda_id in gs_df['ayuda_id'].values:

        ai_row_df = gs_df[gs_df['ayuda_id']==ayuda_id]

        return True, ai_row_df

    else:
        # Try to generate ai responses
        try:
            ai_row = process_ayuda_with_ai(ayuda_row)
            #convert dict to pandas dataframe
            ai_row_series = pd.Series(ai_row)
            ai_row_df = ai_row_series.to_frame()
            ai_row_df = ai_row_df.T


            # # Update database
            gs_df_updated = pd.concat([gs_df,ai_row_df],ignore_index=True)
            gs_conn.update(worksheet='db',data=gs_df_updated)

            return True, ai_row_df

        except:

            return False, []
        

    

def process_ayuda_with_ai(ayuda_row):

    # Open the file and read the token
    api_token = st.secrets["api_token"]
    client = InferenceClient(token=api_token)

    # Calls to genAI
    model = 'mistralai/Mistral-7B-Instruct-v0.3'

    ai_descripcion = summarise_description(client,ayuda_row['descripcion'], model)
    ai_beneficiarios = summarise_beneficiarios(client,ayuda_row['beneficiarios'], model)
    ai_requisitos = summarise_requisitos(client,ayuda_row['requisitos'], model).replace("```html", "").replace("```", "").strip()
    ai_cuantia = summarise_cuantia(client,ayuda_row['cuantia'], model).replace("```html", "").replace("```", "").strip()
    ai_despues = summarise_after(client,ayuda_row['forma_resolucion'],ayuda_row['recursos'], model).replace("```html", "").replace("```", "").strip()
    ai_lugar = decide_location(client,ayuda_row['lugar_presentacion'], model)

    # Timestamp
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

    # Create a dictionary with your variables
    new_row = {
        "ayuda_id":int(ayuda_row['identificador']),
        "ai_descripcion": ai_descripcion,
        "ai_beneficiarios": ai_beneficiarios,
        "ai_requisitos": ai_requisitos,
        "ai_cuantia": ai_cuantia,
        "ai_despues": ai_despues,
        "ai_lugar": ai_lugar,
        "ai_created_at": formatted_datetime
    }


    return new_row

def summarise_description(client,text, model):

    cleaned_text = limpiar_html(text)

    # Vas a recibir la descripción de una beca de Castilla y León.
    # Resume el texto de manera sencilla de entender para un ciudadano y en tercera persona:

    # {cleaned_text}

    # Resumen conciso (máximo 50 palabras): 

    prompt = f"""
    Vas a recibir la descripción de una beca de Castilla y León.
    Proporciona un resumen del siguiente texto de manera sencilla de entender y en tercera persona:

    {cleaned_text}

    Resumen conciso (máximo 50 palabras):

    """

    response = client.text_generation(
        prompt,
        model=model,
        max_new_tokens=150,
        temperature=0.001,
        top_k=50,
        top_p=0.95,
        repetition_penalty=1.2
    )

    return response

def summarise_beneficiarios(client,text, model):
    
    # cleaned_text = limpiar_html(text)

    # prompt = f"""
    # Vas a recibir la lista de beneficiarios de una beca de Castilla y León.
    # Realiza un resumen de la siguiente lista que pueda ser de interés para un posible solicitante:

    # {text}
    # No incluyas mensajes apelando al solicitante.
    # Lista resumida: """
    
    prompt = f"""
    Vas a recibir los posibles beneficiarios de una beca de Castilla y León.
    Proporciona un resumen del siguiente texto de manera sencilla de entender y en tercera persona:

    {text}

    Resumen conciso (máximo 50 palabras) y neutro: 
    """
    
    response = client.text_generation(
        prompt,
        model=model,
        max_new_tokens=1000,
        temperature=0.001,
        top_k=50,
        top_p=0.95,
        repetition_penalty=1.2
    )
    
    return response

def summarise_requisitos(client, requisitos, model):
    
    # cleaned_text = limpiar_html(requisitos)
    # Resumen de requisitos en tercera persona

    prompt = f"""
    Proporciona un resumen conciso en HTML sin títulos del los siguientes requisitos:

    {requisitos}

    Resumen conciso (máximo 50 palabras) en HTML: 
    """
    
    response = client.text_generation(
        prompt,
        model=model,
        max_new_tokens=1000,
        temperature=0.001,
        top_k=50,
        top_p=0.95,
        repetition_penalty=1.2
    )
    
    return response

def summarise_cuantia(client,cuantia, model):
    #cleaned_text = limpiar_html(text)

    prompt = f"""
    Proporciona un texto en forma de lista que resuma los detalles de la siguientes cantidades:

    {cuantia}

    Presenta la información en una lista de HTML resaltando en negrita lo importante.
    Respuesta en HTML:
"""
    
    response = client.text_generation(
        prompt,
        model=model,
        max_new_tokens=1000,
        temperature=0.001,
        top_k=50,
        top_p=0.95,
        repetition_penalty=1.2
    )
    
    return response

def summarise_after(client,resolucion, recursos,model):
    #cleaned_text = limpiar_html(text)

    prompt = f"""
    Proporcionar una lista en HTML con la siguiente información de una ayuda de Castilla y León:
    - El plazo máximo de resolución.
    - El sentido del silencio explicado para un ciudadano sin conocimientos
    - Los recursos que se admiten explicandos para un ciudadano sin conocimientos.

    Para ello, este es el Plazo máximo de resolución y el sentido del silencio de la convocatoria en el siguiente texto:
    {resolucion}.

    Además, los recursos que admite la convocatoria son los siguientes:
    {recursos}


    Presenta la información en una lista de HTML resaltando en negrita lo importante.
    Respuesta en HTML:

    """
    
    response = client.text_generation(
        prompt,
        model=model,
        max_new_tokens=1000,
        temperature=0.001,
        top_k=50,
        top_p=0.95,
        repetition_penalty=1.2
    )
    
    return response

def decide_location(client,lugar_presentacion,model):
    #cleaned_text = limpiar_html(text)

    prompt = f"""
    Vas a recibir información sobre el lugar de presentación de la documentación de una beca.
    {lugar_presentacion}.

    Analiza el texto y proporciona uno los siguientes formatos de presentación:
    - PRESENCIAL
    - ELECTRÓNICO
    - PPRESENCIAL O ELECTRÓNICO


    Forma de presentación: """
    
    response = client.text_generation(
        prompt,
        model=model,
        max_new_tokens=1000,
        temperature=0.001,
        top_k=50,
        top_p=0.95,
        repetition_penalty=1.2
    )
    
    return response


if __name__ == "__main__":
    show_details()