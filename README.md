# 🤖 Olea Asistente Legal (app-legal-olea) V2.3

Aplicación en Streamlit y Python que utiliza IA (OpenAI) y una base de datos de usuarios (Supabase) para asistir en tareas legales.

Este proyecto V2.3 incluye:
* Sistema de **Login Multi-Usuario** (vía Supabase Auth).
* Un **Panel de Administración (CRUD)** para crear/borrar/listar usuarios.
* Interfaz de pestañas (Generador y Chatbot).
* **Generador de Documentos:**
    * Flujo "General" (con listas `Lista_Manual` V1.8).
    * Flujo "Pagaré" (con tablas V2.1 que incluyen **cálculos de IVA**).
* **Chatbot Analizador:**
    * Lee **.docx** y **.pdf** (V1.9).
    * Usa `gpt-4o` para **razonar** sobre el contenido (V1.7).
* Fix de Modo Oscuro (`config.toml`) y fix de vista previa de link (`ngrok`).

## 🚀 Componentes del Proyecto

El sistema funciona con varios archivos y carpetas clave:

1.  **`app.py`**: El código fuente principal (V2.3 agnóstico).
2.  **`requirements.txt`**: La lista de dependencias (`streamlit`, `openai`, `python-docx`, `PyMuPDF`, `supabase`).
3.  **`template_maestro.docx`**: Molde para el "Documento General".
4.  **`template_pagare.docx`**: Molde para el "Pagaré" (V1.7, sin tabla).
5.  **`.streamlit/`**: Carpeta de configuración.
    * **`config.toml`**: Forza el modo oscuro (`base = "dark"`).
    * **`secrets.toml`**: (SOLO LOCAL) Contiene las 5 llaves para pruebas.
6.  **`.gitignore`**: Asegura que `secrets.toml` **NUNCA** se suba a GitHub.
7.  **Imágenes**: `logo.png` / `favicon.png`.

## ⚙️ Instalación (Local)

1.  Clona el repositorio.
2.  Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```
3.  Crea la carpeta y archivo de secretos locales: `.streamlit/secrets.toml`.
4.  Pega tus 5 llaves (OpenAI, Supabase URL, Key, Service_Key) en `secrets.toml`.

## ▶️ Ejecución (Local)

```bash
streamlit run app.py
```

La app leerá las llaves desde .streamlit/secrets.toml y se abrirá en http://localhost:8501.

## ☁️ Despliegue (Deploy)
Esta app es 100% "agnóstica" y está lista para el despliegue en el servidor de Neurya.

1.  **Dependencias del Servidor (Windows):**
    * Asegúrate de que Python esté instalado.
    * Instala las librerías: `pip install -r requirements.txt`.
    * ¡Crítico! Instala el **Microsoft Visual C++ Redistributable (x64)** para que `PyMuPDF` (lector de PDF) funcione.

2.  **Variables de Entorno (Las "Llaves"):** El `app.py` está programado para leer sus secretos desde las Variables de Entorno del Sistema. El equipo de IT debe configurar estas **4** variables:
    * `OPENAI_API_KEY`
    * `SUPABASE_URL`
    * `SUPABASE_KEY` (la 'anon', 'public' key)
    * `SUPABASE_SERVICE_KEY` (la 'service_role' key para el Admin)

3. Ejecución (Servidor):
```bash
streamlit run app.py --server.port 8080
```
(O el puerto que el equipo de IT designe).