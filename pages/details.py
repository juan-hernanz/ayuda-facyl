import streamlit as st
import pandas as pd
from huggingface_hub import InferenceClient
from utils import limpiar_html, calcular_dias_restantes, section_header
from pages.listado_ayudas import show_listado_ayudas

st.markdown("""
<style>
.status-bubble-active {
    background-color: #e8f5e9;
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
        beca_details = full_df[full_df['identificador'] == beca_id].iloc[0]

        # Determine status
        if beca_details['days_left']>=0:
            status = 'active'
            status_text = 'Activa'
            dias_text = 'Quedan '
        else:
            status = 'expired'
            status_text = 'Expirada'
            dias_text = 'Expiró hace '

        
        # Open the file and read the token
        # with open('api_token.txt', 'r') as file:
        #     api_token = file.read().strip()
        # client = InferenceClient(token=api_token)
        api_token = st.secrets["api_token"]
        client = InferenceClient(token=api_token)

        # Calls to genAI
        model = 'mistralai/Mistral-7B-Instruct-v0.3'

        # Mostrar Título
        st.subheader(f"{beca_details['titulo']}")

        # Crear columnas para detalles debajo del título
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
                <div class="days-left-{status}">{dias_text}{int(abs(beca_details['days_left']))} días</div>
            """, unsafe_allow_html=True)

            # Mostrar lugar presentación
            st.markdown(f"""
                <div class="burbuja">{decide_location(client,beca_details['lugar_presentacion'], model)}</div>
            """, unsafe_allow_html=True)

        with col_mid:
            # Mostrar fechas
            
            st.write(f"**Fecha publicación**: {beca_details['fecha_publicacion']}")
            st.write(f"**Fecha límite**: {beca_details['fecha_limite']}")
        
            # Enlace a la ayuda
            st.markdown(f"""

                <a href="{beca_details['enlace_contenido']}" 
                class="link-bubble" 
                title="Ir al portal oficial" 
                target="_blank">
                    🔗 Ver ayuda original
                </a>


            """, unsafe_allow_html=True)

        with col_right:
            # Mostrar materias
            st.markdown(f"""
                    {''.join([f'<span class="burbuja">{materia.strip()}</span>' for materia in beca_details['materia'].split(',')])}
                """,
                unsafe_allow_html=True)



        # Descripcion de la beca
        section_header("✨ Descripción comprensible")
        st.write(f"""{summarise_description(client,beca_details['descripcion'], model)}""")
        # st.write(f"""{beca_details['descripcion']}""")


        # Beneficiarios
        section_header("👥 ¿Quién puede solicitar la ayuda?")
        st.write(f"""{summarise_beneficiarios(client,beca_details['beneficiarios'], model)}""") 
        # st.write(f"""{beca_details['beneficiarios']}""")

        # Requisitos
        section_header("📋 Requisitos")
        st.markdown(f"""{summarise_requisitos(client,beca_details['requisitos'], model).replace("```html", "").replace("```", "").strip()}"""
        , unsafe_allow_html=True)
        # st.write(f"""{beca_details['requisitos']}""")

        # Cuantía
        section_header("💶 Cuantía")
        st.markdown(f"""
        {summarise_cuantia(client,beca_details['cuantia'], model).replace("```html", "").replace("```", "").strip()}
        """, unsafe_allow_html=True)
        # st.write(f"""{beca_details['cuantia']}""")

        # ¿Y luego qué?
        section_header("⏩  ¿Y luego qué?")
        st.markdown(f"""
        {summarise_after(client,beca_details['forma_resolucion'],beca_details['recursos'], model).replace("```html", "").replace("```", "").strip()}
        """, unsafe_allow_html=True)
        # st.write(f"""{beca_details['forma_resolucion']}""")
        # st.write(f"""{beca_details['recursos']}""")

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