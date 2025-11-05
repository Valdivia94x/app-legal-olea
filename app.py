import os
import openai
import json
import time
import streamlit as st
from docx import Document
import io
import fitz

# --- 0. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Olea Asistente Legal", 
    layout="centered",
    page_icon="favicon.png"
)

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
NOMBRES_DE_ESTILOS = ['Titulo_1', 'Parrafo_Justificado', 'Lista_Numerada', 'Estilo_Firma', 'Lista_Manual']
TEMPLATE_FILE_GENERAL = 'template_maestro.docx'
TEMPLATE_FILE_PAGARE = 'template_pagare.docx'

# --- COMPONENTE 2: El "Extractor Universal" (V1.9) ---
@st.cache_data
def extraer_texto_del_documento(archivo_subido):
    """
    Extractor inteligente V1.9: Lee .docx y .pdf
    Toma un archivo subido por Streamlit (UploadedFile)
    y devuelve una sola cadena de texto.
    """
    try:
        # 1. Leer el archivo en memoria una sola vez
        file_bytes = archivo_subido.read()
        
        # 2. Decidir qué herramienta usar
        if archivo_subido.type == "application/pdf":
            # --- LÓGICA PARA PDF (NUEVO) ---
            st.write("Detectado: PDF. Usando PyMuPDF (fitz)...")
            texto_completo = []
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                for page in doc:
                    texto_completo.append(page.get_text())
            return '\n'.join(texto_completo)

        elif archivo_subido.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            # --- LÓGICA PARA DOCX (LA ANTIGUA) ---
            st.write("Detectado: DOCX. Usando python-docx...")
            doc = Document(io.BytesIO(file_bytes))
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
        
        else:
            st.error(f"Tipo de archivo no soportado: {archivo_subido.type}")
            return None
            
    except Exception as e:
        st.error(f"Error al leer el archivo ({archivo_subido.name}): {e}")
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
    - REGLAS DE LISTAS:
        - Para cláusulas largas que deben continuar (ej. 'CLÁUSULA PRIMERA', 'CLÁUSULA SEGUNDA'), usa el estilo 'Lista_Numerada'.
        - Para cualquier OTRA lista (ej. un Orden del Día, listas de requisitos, etc.) que deba empezar en '1.', usa el estilo 'Lista_Manual'.
        - IMPORTANTE: Cuando uses 'Lista_Manual', DEBES escribir tú mismo el número y un tabulador. Ejemplo: "1.\t[Texto del punto uno]", "2.\t[Texto del punto dos]", etc.
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
       - REGLAS DE LISTAS:
           - Para cláusulas largas que deben continuar (ej. 'CLÁUSULA PRIMERA'), usa el estilo 'Lista_Numerada'.
           - Para cualquier OTRA lista que deba empezar en '1.', usa el estilo 'Lista_Manual'.
           - IMPORTANTE: Cuando uses 'Lista_Manual', DEBES escribir tú mismo el número y un tabulador. Ejemplo: "1.\t[Texto del punto uno]", "2.\t[Texto del punto dos]", etc.
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

# --- ENSAMBLADOR 1.0 (GENERAL) - CORREGIDO V1.2 ---
def ensamblar_docx_general(json_data, archivo_template): # <--- CAMBIO 1: Acepta el 2do argumento
    """
    Toma el JSON de la IA y construye un .docx
    usando el template general.
    """
    try:
        # --- CAMBIO 2: Usamos la variable 'archivo_template' ---
        if not os.path.exists(archivo_template): 
            st.error(f"¡Error crítico! No se encuentra el archivo '{archivo_template}'.")
            return None
            
        doc = Document(archivo_template) # <--- CAMBIO 3: Usamos la variable
        # --- FIN DE CAMBIOS ---
        
        # (El resto del código ya estaba bien)
        datos = json.loads(json_data)
        
        for item in datos:
            texto = item.get('text', '')
            estilo = item.get('style', 'Parrafo_Justificado') 
            
            if estilo not in NOMBRES_DE_ESTILOS:
                # Usamos st.warning para que se vea en la app
                st.warning(f"Advertencia: La IA usó un estilo desconocido ('{estilo}'). Usando 'Parrafo_Justificado'.")
                estilo = 'Parrafo_Justificado'
            
            doc.add_paragraph(texto, style=estilo)
            
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer
        
    except json.JSONDecodeError:
        st.error(f"ERROR CRÍTICO: La IA no devolvió un JSON válido. No se puede ensamblar.")
        st.code(json_data) # Muestra el JSON roto
        return None
    except Exception as e:
        st.error(f"ERROR durante el ensamblaje del .docx: {e}")
        return None
    
# --- ENSAMBLADOR 2.0 (PAGARÉ) - CORREGIDO V1.7 (Crea la tabla) ---
def ensamblar_pagare_en_memoria(json_data, archivo_template):
    """
    Toma el JSON de pagaré (prosa y tabla) y construye un .docx EN MEMORIA.
    Esta versión CREA la tabla desde cero al final del documento.
    """
    try:
        if not os.path.exists(archivo_template):
            st.error(f"¡Error crítico! No se encuentra el archivo '{archivo_template}'.")
            return None
            
        # 1. Cargar el template (que ahora NO tiene tabla)
        doc = Document(archivo_template) 
        datos = json.loads(json_data)
        
        # --- 2. Ensamblar la Prosa PRIMERO ---
        st.write("Ensamblando prosa del pagaré...")
        prosa_items = datos.get("prosa", [])
        for item in prosa_items:
            texto = item.get('text', '')
            estilo = item.get('style', 'Parrafo_Justificado')
            if estilo not in NOMBRES_DE_ESTILOS:
                estilo = 'Parrafo_Justificado'
            doc.add_paragraph(texto, style=estilo)
            
        # --- 3. Ensamblar la Tabla de Amortización AL FINAL ---
        tabla_datos = datos.get("tabla_amortizacion", [])
        if tabla_datos:
            st.write("Creando y ensamblando tabla de amortización...")
            
            # ¡AQUÍ CREAMOS LA TABLA!
            # (Asumimos 4 columnas. Si necesitas más, cambia el 'cols=4')
            table = doc.add_table(rows=1, cols=4) 
            table.style = 'Table Grid' # Estilo básico de Word
            
            # Rellenar los encabezados (hardcodeados)
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = 'Pago No.'
            hdr_cells[1].text = 'Interés'
            hdr_cells[2].text = 'Capital'
            hdr_cells[3].text = 'Saldo Insoluto'
            
            # (Opcional: Poner encabezados en negrita)
            for cell in hdr_cells:
                cell.paragraphs[0].runs[0].font.bold = True

            # Rellenar las filas de datos
            for fila_data in tabla_datos:
                row_cells = table.add_row().cells # Añade una nueva fila
                
                valores = list(fila_data.values())
                
                try:
                    row_cells[0].text = str(valores[0]) # Pago No.
                    row_cells[1].text = f"{float(valores[1]):,.2f}" # Interés
                    row_cells[2].text = f"{float(valores[2]):,.2f}" # Capital
                    row_cells[3].text = f"{float(valores[3]):,.2f}" # Saldo
                except Exception as e:
                    st.warning(f"Error al procesar fila de tabla: {e}. Datos: {valores}")
                    row_cells[0].text = "ERROR"
            
            # Añadir un espacio después de la tabla
            doc.add_paragraph("") 
                
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

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Configuración de IA")
    modelo_seleccionado = st.sidebar.selectbox(
        "Elige el motor de IA:",
        ("gpt-5", "gpt-5-pro"),
        index=0, 
        help="GPT-5 es más rápido y barato. GPT-5-Pro es más lento, caro, pero más inteligente."
    )
    st.sidebar.caption(f"Usando: {modelo_seleccionado}")
    
    # Guardamos el modelo en la memoria para que el chat lo vea
    st.session_state['modelo_seleccionado'] = modelo_seleccionado

    st.title("🤖 Asistente Legal")

    tab_generador, tab_chatbot = st.tabs(
        ["Generador de Documentos", "Chatbot Legal (Demo)"]
    )

    with tab_generador:
        mostrar_pagina_generador(modelo_seleccionado)

    with tab_chatbot:
        mostrar_pagina_chatbot()

# --- 3. FUNCIONES DE WORKFLOW ---

def ejecutar_flujo_general(instruccion, ejemplo_subido, modelo_seleccionado):
    """
    Este es el flujo de trabajo que YA CONSTRUIMOS.
    """
    st.success("Iniciando flujo: Documento General")
    
    texto_de_ejemplo = "N/A"
    if ejemplo_subido:
        with st.spinner("Leyendo documento de ejemplo..."):
            texto_de_ejemplo = extraer_texto_del_documento(ejemplo_subido)
    
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

def mostrar_pagina_generador(modelo_seleccionado):
    st.markdown("Genera borradores de documentos legales usando IA.")

    st.markdown("### 1. Selecciona el tipo de documento")
    tipo_doc = st.selectbox(
        "Elige la plantilla que deseas usar:",
        ("Documento General", "Pagaré (con Tabla)")
    )

    st.markdown("---") # Una línea divisoria

    instruccion = st.text_area(
        "2. Escribe las instrucciones del documento que necesitas:",
        height=200,
        placeholder="Ej: Genera un Contrato de Arrendamiento simple para una casa. Arrendador: Juan Pérez. Arrendatario: María López..."
    )

    ejemplo_subido = st.file_uploader(
        "3. (Opcional) Sube un .docx o pfd de ejemplo para imitar el tono:",
        type=["docx", "pdf"]
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
                        texto_de_ejemplo = extraer_texto_del_documento(ejemplo_subido)
                
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

# --- ¡NUEVA FUNCIÓN PARA EL CHATBOT! ---

# --- CEREBRO DEL CHATBOT (SIMPLIFICADO) ---
def llamar_chat_ia(historial_mensajes, modelo_ia):
    """
    Función 'Cerebro' simple para el chatbot.
    Usa el endpoint v1/chat/completions (perfecto para gpt-4o-mini).
    """
    try:
        completion = client.chat.completions.create(
            model=modelo_ia, 
            messages=historial_mensajes
        )
        return completion.choices[0].message.content
    except Exception as e:
        st.error(f"Error al llamar a la API del chat: {e}")
        return None

# --- PÁGINA DEL CHATBOT (V 1.5 - ANALIZADOR DE DOCS) ---
def mostrar_pagina_chatbot():
    """
    Contiene la lógica para el chatbot simple,
    AHORA CON CAPACIDAD DE ANALIZAR DOCUMENTOS.
    """
    
    st.warning("⚠️ **Modo Demo:** Este chatbot es una IA generativa (gpt-4o-mini). Sus respuestas pueden ser imprecisas.")
    
    # --- ¡NUEVO! El File Uploader ---
    uploaded_doc = st.file_uploader(
        "Sube un .docx para analizarlo:",
        type=["docx", "pdf"],
        key="chatbot_file_uploader" # ¡Un 'key' único!
    )
    
    # --- ¡NUEVA! Lógica de carga de documento ---
    if uploaded_doc is not None:
        # Usamos un 'if' con una variable de sesión para evitar 
        # que se recargue y borre el chat con cada acción.
        if "documento_analizado" not in st.session_state or st.session_state.documento_analizado != uploaded_doc.name:
            with st.spinner(f"Analizando '{uploaded_doc.name}'..."):
                contexto_documento = extraer_texto_del_documento(uploaded_doc)
                if contexto_documento:
                    # ¡Iniciamos un NUEVO chat con el contexto!
                    st.session_state.chat_history = [
                        {
                            "role": "system",
                            "content": f"""
                            Eres un asistente legal experto. Te han pasado el siguiente documento como contexto.
                            Tu trabajo es responder a las preguntas del usuario basándote ÚNICA Y EXCLUSIVAMENTE en el texto de este documento.
                            Si la respuesta no está en el texto, debes decir "La respuesta no se encuentra en el documento."
                            No inventes información.
                            ---
                            CONTEXTO DEL DOCUMENTO (Nombre: {uploaded_doc.name}):
                            {contexto_documento}
                            ---
                            """
                        },
                        {
                            "role": "assistant",
                            "content": f"He leído el documento '{uploaded_doc.name}'. ¿Qué necesitas saber sobre él?"
                        }
                    ]
                    st.session_state.documento_analizado = uploaded_doc.name # Marcamos que ya lo analizamos
                    st.success("Documento analizado. ¡Puedes empezar a chatear con él!")
                else:
                    st.error("No se pudo extraer texto del documento.")
                    
    # --- Lógica de Chat (casi igual que antes) ---
    
    # Forzar el modelo rápido
    modelo_chatbot = "gpt-4o-mini"

    # Inicializar historial (si no se ha subido un doc)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Hola, soy el asistente legal. Sube un documento para analizar o hazme una pregunta general (sin contexto)."}
        ]

    # --- 1. PINTAR EL HISTORIAL ANTIGUO (CON FILTRO) ---
    for message in st.session_state.chat_history:
        
        # --- ¡EL ARREGLO ESTÁ AQUÍ! ---
        # Solo muestra los mensajes si NO son del "sistema"
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    # --- FIN DEL ARREGLO ---

    # --- 2. PEDIR NUEVO INPUT (Se pega al fondo) ---
    # (Esto PINTA la caja de texto en la parte inferior)
    if prompt := st.chat_input("Escribe tu pregunta aquí..."):
        
        # --- ¡INICIO DE CAMBIOS! ---
        
        # 1. Guardar mensaje del usuario en la memoria
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # (¡BORRAMOS EL 'with st.chat_message("user")' DE AQUÍ!)

        # 2. Generar respuesta de la IA (¡NO LA PINTAMOS AÚN!)
        with st.spinner("Pensando..."): # El spinner SÍ está bien aquí
            respuesta_ia = llamar_chat_ia(
                st.session_state.chat_history, 
                modelo_chatbot
            )
            
            if respuesta_ia:
                # 3. Guardar respuesta de la IA en la memoria
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": respuesta_ia}
                )
            else:
                st.error("No se pudo obtener respuesta de la IA.")
        
        # (¡BORRAMOS EL 'with st.chat_message("assistant")' DE AQUÍ!)
        
        # 4. Forzar un refresco de la página
        # Esto hace que el script se reinicie y el 'for' loop 
        # de arriba pinte los mensajes nuevos.
        st.rerun()
        
        # --- FIN DE CAMBIOS ---

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