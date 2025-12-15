# 🤖 Olea Asistente Legal (app-legal-olea) V2.4

Aplicación en Streamlit y Python que utiliza una arquitectura híbrida de IA (OpenAI + Azure) y una base de datos de usuarios (Supabase) para asistir en tareas legales.

Este proyecto **V2.4** incluye:
* **Sistema de Login Multi-Usuario** (vía Supabase Auth).
* **Panel de Administración (CRUD)** para crear/borrar/listar usuarios.
* **Motor Híbrido de Lectura de Documentos:**
    * **Digitales (.docx / .pdf):** Procesamiento nativo instantáneo (Costo $0).
    * **Escaneados / Imágenes:** Integración con **Microsoft Azure AI Document Intelligence** para leer firmas manuscritas, tablas complejas y documentos antiguos sin filtros de censura.
* **Generador de Documentos:**
    * Flujo "General" (con listas `Lista_Manual` V1.8).
    * Flujo "Pagaré" (con tablas V2.1 que incluyen **cálculos de IVA**).
* **Chatbot Analizador:**
    * Usa `gpt-4o` para **razonar** sobre el contenido extraído.
    * Algoritmo de **"Chunking" (segmentación)** para procesar archivos escaneados pesados (>4MB) dividiéndolos automáticamente.

## 🚀 Componentes del Proyecto

El sistema funciona con varios archivos y carpetas clave:

1.  **`app.py`**: El código fuente principal (V2.4 con lógica de Azure).
2.  **`requirements.txt`**: Lista de dependencias actualizada (`streamlit`, `openai`, `azure-ai-formrecognizer`, `PyMuPDF`, `supabase`).
3.  **`template_maestro.docx`**: Molde para el "Documento General".
4.  **`template_pagare.docx`**: Molde para el "Pagaré".
5.  **`.streamlit/`**: Carpeta de configuración.
    * **`config.toml`**: Forza el modo oscuro (`base = "dark"`).
    * **`secrets.toml`**: (SOLO LOCAL) Contiene las **7 llaves** necesarias.
6.  **`.gitignore`**: Asegura que `secrets.toml` **NUNCA** se suba a GitHub.
7.  **Imágenes**: `logo.png` / `favicon.png`.

## ⚙️ Instalación (Local)

1.  Clona el repositorio.
2.  Instala las dependencias (¡Actualizado!):
    ```bash
    pip install -r requirements.txt
    ```
3.  Crea la carpeta y archivo de secretos locales: `.streamlit/secrets.toml`.
4.  Pega tus **7 llaves** (OpenAI, Supabase x3, Azure x2) en `secrets.toml`.

## ▶️ Ejecución (Local)

```bash
streamlit run app.py --server.port 8080

```

(O el puerto que el equipo de IT designe).