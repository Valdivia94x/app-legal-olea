import os
import openai
import json
import time
import streamlit as st
from docx import Document
import io

# --- 0. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Olea Asistente Legal", layout="centered")

# --- 1. CONFIGURACIÓN DE USUARIO Y CONTRASEÑA ---
# ¡IMPORTANTE! Cámbialos por algo seguro
USUARIO_CORRECTO = "admin"
PASSWORD_CORRECTO = "1234"

# --- 2. CONFIGURACIÓN GLOBAL Y COMPONENTES 1, 2, 3, 4 ---
# (Todo nuestro código de "motor" va aquí, definido como funciones)

# Conectar a OpenAI
try:
    client = openai.OpenAI()
except Exception as e:
    # Esto pasará si la API key no está configurada
    st.error(f"Error al conectar con OpenAI. ¿Configuraste la variable OPENAI_API_KEY?")
    st.stop() # Detiene la app si no hay API key

# Constantes del Template
NOMBRES_DE_ESTILOS = ['Titulo_1', 'Parrafo_Justificado', 'Lista_Numerada', 'Estilo_Firma']
TEMPLATE_FILE_GENERAL = 'template_maestro.docx'
TEMPLATE_FILE_PAGARE = 'template_pagare.docx'

@st.cache_data
def extraer_texto_de_docx(archivo_subido):
    try:
        doc = Document(io.BytesIO(archivo_subido.read()))
        texto_completo = []
        for parrafo in doc.paragraphs:
            if parrafo.text.strip():
                texto_completo.append(parrafo.text)
        for tabla in doc.tables:
            for fila in tabla.rows:
                for celda in fila.cells:
                    if celda.text.strip():
                        texto_completo.append(celda.text)
        return '\n'.join(texto_completo)
    except Exception as e:
        st.error(f"Error al leer el archivo DOCX: {e}")
        return None

@st.cache_data
def generar_documento_ia_general(instruccion_usuario, texto_de_ejemplo, modelo_ia):
    st.info(f"Conectando con la IA ({modelo_ia})... Esto puede tardar varios minutos.")
    lista_estilos_str = ", ".join([f"'{s}'" for s in NOMBRES_DE_ESTILOS])
    prompt_final = f"""
    PRIORIDAD ABSOLUTA: Tu única y exclusiva respuesta debe ser un objeto JSON válido.
    Tu respuesta debe comenzar con un corchete de apertura [ y terminar con un corchete de cierre ].
    No escribas NADA antes del [ ni NADA después del ].
    Eres un abogado senior 'todoterreno' en México.
    FORMATO DE SALIDA OBLIGATORIO:
    Una lista de objetos JSON: [{{"style": "...", "text": "..."}}]
    REGLAS DE ESTILO OBLIGATORIAS:
    - Los únicos valores permitidos para "style" son: {lista_estilos_str}.
    - Usa 'Titulo_1' para todos los títulos.
    - Usa 'Parrafo_Justificado' para el texto principal.
    - Usa 'Lista_Numerada' para listas.
    - Usa 'Estilo_Firma' para las firmas.
    EJEMPLOS DE TONO (PARA IMITAR):
    ---
    {texto_de_ejemplo}
    ---
    [TAREA DEL USUARIO]:
    {instruccion_usuario}
    Recuerda: Tu respuesta debe ser solo el JSON, empezando con [ y terminando con ].
    """
    try:
        start_time = time.time()
        completion = client.responses.create(
            model=modelo_ia, # Usamos el modelo seleccionado
            input=prompt_final,
            max_output_tokens=20000
        )
        end_time = time.time()
        st.info(f"Respuesta recibida de la IA en {end_time - start_time:.2f} segundos.")
        
        respuesta_cruda = completion.output_text
        start_index = respuesta_cruda.find('[')
        end_index = respuesta_cruda.rfind(']')
        
        if start_index == -1 or end_index == -1:
            st.error("Error: La IA no devolvió un JSON válido. Respuesta cruda:")
            st.code(respuesta_cruda)
            return None
            
        json_limpio = respuesta_cruda[start_index : end_index + 1]
        return json_limpio
        
    except Exception as e:
        st.error(f"ERROR INESPERADO DE API: {e}")
        return None
    
# --- CEREBRO 2.0: Generador de Pagarés (con Tabla) ---
@st.cache_data
def generar_pagare_ia(instruccion_usuario, texto_de_ejemplo, modelo_ia):
    st.info(f"Conectando con la IA ({modelo_ia}) para el Pagaré... Esto puede tardar varios minutos.")
    
    lista_estilos_str = ", ".join([f"'{s}'" for s in NOMBRES_DE_ESTILOS])
    
    # --- ¡EL PROMPT CLAVE para JSON anidado y cálculos! ---
    prompt_final = f"""
    PRIORIDAD ABSOLUTA: Tu única y exclusiva respuesta debe ser un objeto JSON válido.
    Tu respuesta debe comenzar con un corchete de apertura {{ y terminar con un corchete de cierre }}.
    No escribas NADA antes del {{ ni NADA después del }}.

    Eres un abogado senior 'todoterreno' en México, experto en documentos mercantiles.
    
    FORMATO DE SALIDA OBLIGATORIO:
    Un objeto JSON con dos claves principales: "prosa" y "tabla_amortizacion".

    1. CLAVE "prosa":
       Una lista de objetos JSON para el texto principal del pagaré:
       "prosa": [{{"style": "...", "text": "..."}}]
       REGLAS DE ESTILO OBLIGATORIAS PARA "prosa":
       - Los únicos valores permitidos para "style" son: {lista_estilos_str}.
       - Usa 'Titulo_1' para todos los títulos.
       - Usa 'Parrafo_Justificado' para el texto principal.
       - Usa 'Estilo_Firma' para las firmas.
       - Incluye en la prosa los montos calculados (intereses, total).

    2. CLAVE "tabla_amortizacion":
       Una lista de objetos JSON con los datos de cada pago de la tabla de amortización:
       "tabla_amortizacion": [
         {{"Pago No.": 1, "Interés": 100.00, "Capital": 900.00, "Saldo Insoluto": 9900.00}},
         {{"Pago No.": 2, "Interés": 99.00, "Capital": 901.00, "Saldo Insoluto": 8999.00}}
         // ...y así sucesivamente por cada pago
       ]
       REGLAS DE FORMATO PARA "tabla_amortizacion":
       - Las claves de cada objeto deben coincidir exactamente con los encabezados de la tabla: "Pago No.", "Interés", "Capital", "Saldo Insoluto".
       - Los valores deben ser números (float para Interés, Capital, Saldo).
       - No incluyas la fila de encabezados en este JSON, solo los datos.

    EJEMPLOS DE TONO (PARA IMITAR):
    ---
    {texto_de_ejemplo}
    ---
    
    [TAREA DEL USUARIO]:
    {instruccion_usuario}
    
    Recuerda: Tu respuesta debe ser solo el JSON, empezando con {{ y terminando con }}.
    """
    try:
        start_time = time.time()
        completion = client.responses.create(
            model=modelo_ia, 
            input=prompt_final,
            max_output_tokens=20000
        )
        end_time = time.time()
        st.info(f"Respuesta recibida de la IA en {end_time - start_time:.2f} segundos.")
        
        # OJO: Ahora busca { y } porque es un objeto JSON, no una lista.
        respuesta_cruda = completion.output_text
        start_index = respuesta_cruda.find('{')
        end_index = respuesta_cruda.rfind('}')
        
        if start_index == -1 or end_index == -1:
            st.error("Error: La IA no devolvió un JSON de pagaré válido. Respuesta cruda:")
            st.code(respuesta_cruda)
            return None
            
        json_limpio = respuesta_cruda[start_index : end_index + 1]
        return json_limpio
        
    except Exception as e:
        st.error(f"ERROR INESPERADO DE API: {e}")
        return None

def ensamblar_docx_general(json_data):
    try:
        if not os.path.exists(TEMPLATE_FILE_GENERAL):
            st.error(f"¡Error crítico! No se encuentra el archivo '{TEMPLATE_FILE_GENERAL}'.")
            return None
            
        doc = Document(TEMPLATE_FILE_GENERAL)
        datos = json.loads(json_data)
        
        for item in datos:
            texto = item.get('text', '')
            estilo = item.get('style', 'Parrafo_Justificado')
            
            if estilo not in NOMBRES_DE_ESTILOS:
                estilo = 'Parrafo_Justificado'
            
            doc.add_paragraph(texto, style=estilo)
            
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        st.error(f"Error durante el ensamblaje del .docx: {e}")
        return None
    
# --- ENSAMBLADOR 2.0: Constructor de Pagarés (con Tabla) ---
def ensamblar_pagare_en_memoria(json_data, archivo_template):
    """
    Toma el JSON de pagaré (prosa y tabla) y construye un .docx EN MEMORIA.
    """
    try:
        if not os.path.exists(archivo_template):
            st.error(f"¡Error crítico! No se encuentra el archivo '{archivo_template}'.")
            return None
            
        doc = Document(archivo_template)
        datos = json.loads(json_data)
        
        # --- 1. Ensamblar la Prosa ---
        st.write("Ensamblando prosa del pagaré...")
        prosa_items = datos.get("prosa", [])
        for item in prosa_items:
            texto = item.get('text', '')
            estilo = item.get('style', 'Parrafo_Justificado')
            if estilo not in NOMBRES_DE_ESTILOS:
                estilo = 'Parrafo_Justificado'
            doc.add_paragraph(texto, style=estilo)
            
        # --- 2. Ensamblar la Tabla de Amortización ---
        tabla_datos = datos.get("tabla_amortizacion", [])
        if tabla_datos:
            st.write("Ensamblando tabla de amortización...")
            
            if not doc.tables:
                st.error("Error: El template del pagaré no contiene una tabla. No se puede generar la amortización.")
                return None
            
            table = doc.tables[0] # Asumimos que la primera tabla es la de amortización
            
            # Obtener encabezados (si se necesitan, para validar)
            # headers = [cell.text for cell in table.rows[0].cells] 
            
            # ---- NUEVO CÓDIGO V 1.1 ---
            for fila_data in tabla_datos:
                row_cells = table.add_row().cells

                # Convertimos el objeto JSON (ej. {"Pago No.": 1, "Interés": 921})
                # en una simple lista de sus valores (ej. [1, 921, ...])
                valores = list(fila_data.values())

                # Asignamos los valores por ORDEN, no por nombre.
                # Esto asume que la IA, aunque falle en los nombres,
                # al menos respetará el orden de los datos.
                try:
                    row_cells[0].text = str(valores[0]) # Pago No.
                    row_cells[1].text = f"{float(valores[1]):,.2f}" # Interés
                    row_cells[2].text = f"{float(valores[2]):,.2f}" # Capital
                    row_cells[3].text = f"{float(valores[3]):,.2f}" # Saldo
                except Exception as e:
                    # Si algo falla (ej. la IA mandó texto en lugar de números)
                    # ponemos un error en la fila.
                    st.warning(f"Error al procesar fila de tabla: {e}. Datos: {valores}")
                    row_cells[0].text = "ERROR"
            # ---- FIN DE NUEVO CÓDIGO ---
                
        # Guardar el documento en un buffer de memoria
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        st.error(f"Error durante el ensamblaje del pagaré .docx: {e}")
        return None

# --- 3. FUNCIÓN PARA MOSTRAR LA APP PRINCIPAL ---
# (Todo nuestro Componente 5 va aquí adentro)
def mostrar_app_principal():
    
    # Botón de Cerrar Sesión (¡Nuevo!)
    st.sidebar.button("Cerrar Sesión", on_click=logout)

    # Logo
    st.sidebar.image("logo.png")

    st.title("🤖 Asistente Legal")

    st.markdown("Genera borradores de documentos legales usando IA.")

    st.markdown("### 1. Selecciona el tipo de documento")
    tipo_doc = st.selectbox(
        "Elige la plantilla que deseas usar:",
        ("Documento General", "Pagaré (con Tabla)")
    )

    st.markdown("---") # Una línea divisoria
    
    # Selector de modelo
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Configuración de IA")
    modelo_seleccionado = st.sidebar.selectbox(
        "Elige el motor de IA:",
        ("gpt-5", "gpt-5-pro"),
        index=0, # Por defecto usa gpt-5 (el barato)
        help="GPT-5 es más rápido y barato. GPT-5-Pro es más lento, caro, pero más inteligente."
    )
    st.sidebar.caption(f"Usando: {modelo_seleccionado}")

    instruccion = st.text_area(
        "2. Escribe las instrucciones del documento que necesitas:",
        height=200,
        placeholder="Ej: Genera un Contrato de Arrendamiento simple para una casa. Arrendador: Juan Pérez. Arrendatario: María López..."
    )

    ejemplo_subido = st.file_uploader(
        "3. (Opcional) Sube un .docx de ejemplo para imitar el tono:",
        type="docx"
    )

    if st.button("🚀 Generar Documento"):
        if not instruccion:
            st.warning("Por favor, escribe las instrucciones del documento.")
        else:
            # --- IF para decidir qué flujo usar ---
            if tipo_doc == "Documento General":
                ejecutar_flujo_general(instruccion, ejemplo_subido, modelo_seleccionado)
            
            elif tipo_doc == "Pagaré (con Tabla)":
                st.success("Iniciando flujo: Pagaré (con Tabla)")
                texto_de_ejemplo = "N/A"
                if ejemplo_subido:
                    with st.spinner("Leyendo documento de ejemplo..."):
                        texto_de_ejemplo = extraer_texto_de_docx(ejemplo_subido)
                
                if texto_de_ejemplo is not None:
                    with st.spinner(f"🧠✨ La IA ({modelo_seleccionado}) está redactando y calculando..."):
                        # Usamos la nueva función del cerebro para pagarés
                        json_respuesta_pagare = generar_pagare_ia(instruccion, texto_de_ejemplo, modelo_seleccionado)
                    
                    if json_respuesta_pagare:
                        with st.spinner("🛠️ Ensamblando el archivo .docx del pagaré..."):
                            # Usamos la nueva función del ensamblador para pagarés
                            buffer_docx_pagare = ensamblar_pagare_en_memoria(json_respuesta_pagare, TEMPLATE_FILE_PAGARE)
                        
                        if buffer_docx_pagare:
                            st.success("¡Tu Pagaré con Tabla está listo para descargar!")
                            st.download_button(
                                label="📥 Descargar Pagaré Generado",
                                data=buffer_docx_pagare,
                                file_name="PAGARE_GENERADO.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )

# --- 3. FUNCIONES DE WORKFLOW ---

def ejecutar_flujo_general(instruccion, ejemplo_subido, modelo_seleccionado):
    """
    Este es el flujo de trabajo que YA CONSTRUIMOS.
    """
    st.success("Iniciando flujo: Documento General")
    
    texto_de_ejemplo = "N/A"
    if ejemplo_subido:
        with st.spinner("Leyendo documento de ejemplo..."):
            texto_de_ejemplo = extraer_texto_de_docx(ejemplo_subido)
    
    if texto_de_ejemplo is not None:
        with st.spinner(f"🧠✨ La IA ({modelo_seleccionado}) está redactando... Esto puede tardar varios minutos."):
            # ¡IMPORTANTE! Tenemos que definir qué prompt usar.
            # Por ahora, solo tenemos uno.
            json_respuesta = generar_documento_ia_general(instruccion, texto_de_ejemplo, modelo_seleccionado)
        
        if json_respuesta:
            with st.spinner("🛠️ Ensamblando el archivo .docx..."):
                # ¡IMPORTANTE! Le decimos qué template usar
                buffer_docx = ensamblar_docx_general(json_respuesta, TEMPLATE_FILE_GENERAL)
            
            if buffer_docx:
                st.success("¡Tu documento está listo para descargar!")
                st.download_button(
                    label="📥 Descargar Documento Generado",
                    data=buffer_docx,
                    file_name="DOCUMENTO_GENERADO.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

# --- 4. FUNCIONES DE LOGIN Y LOGOUT ---
def mostrar_login():
    col1, col2, col3 = st.columns([1, 2, 1]) 
    with col2:
        st.image("logoOscuro.png") 
    
    st.title("Asistente Legal")

    st.markdown("Por favor, inicia sesión para continuar.")

    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Iniciar Sesión")

        if submitted:
            if username == USUARIO_CORRECTO and password == PASSWORD_CORRECTO:
                st.session_state['authenticated'] = True
                st.rerun() 
            else:
                st.error("Usuario o contraseña incorrectos.")

def logout():
    st.session_state['authenticated'] = False

# --- 5. LÓGICA PRINCIPAL (EL "SWITCH") ---

# Inicializar el estado de sesión
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

# Mostrar la página correspondiente
if st.session_state['authenticated']:
    # Renombramos la función original
    mostrar_app_principal() 
else:
    mostrar_login()