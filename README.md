# 🤖 Olea Asistente Legal (app-legal-olea) V1.2

Aplicación en Streamlit y Python que utiliza IA (OpenAI GPT-5 y GPT-4o-Mini) para asistir en tareas legales.

Este proyecto V1.6 incluye un sistema de login seguro y una interfaz de pestañas con dos herramientas principales:

1.  **Generador de Documentos:** Crea documentos "Generales" (basados en texto) o "Pagarés" (con tablas de amortización calculadas) usando plantillas de Word e IA para imitar el tono de un ejemplo.
2.  **Chatbot Analizador:** Un chatbot (GPT-4o-Mini) que puede "leer" un `.docx` subido por el usuario y responder preguntas específicas sobre su contenido.

## 🚀 Componentes del Proyecto

El sistema funciona con 5 archivos clave que deben estar en la misma carpeta:

1.  **`app.py`**: El código fuente principal de la aplicación Streamlit. Contiene toda la lógica de la UI, el login, las pestañas, los "Cerebros" (llamadas a la API) y los "Ensambladores" (lógica de `python-docx`).
2.  **`requirements.txt`**: La lista de dependencias de Python necesarias.
3.  **`template_maestro.docx`**: El molde de Word para el flujo de "Documento General".
4.  **`template_pagare.docx`**: El molde de Word para el flujo de "Pagaré" (contiene la tabla vacía).
5.  **`logo.png` / `favicon.png`**: Los archivos de imagen para la marca.

## ⚙️ Instalación (Local)

1.  Clona este repositorio o descarga los archivos.
2.  Asegúrate de tener Python 3.10+ instalado.
3.  Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```
4.  Configura tu variable de entorno de OpenAI:
    ```bash
    # En PowerShell
    $env:OPENAI_API_KEY = "sk-xxxxxxxxxxxxxx"
    ```

## ▶️ Ejecución (Local)

Para correr la aplicación web en tu máquina local, usa el siguiente comando en tu terminal:

```bash
streamlit run app.py
```

La app se abrirá automáticamente en tu navegador en `http://localhost:8501`.

## ☁️ Despliegue (Deploy)

Esta app está diseñada para desplegarse fácilmente en **Streamlit Community Cloud**.

1.  Conecta este repositorio de GitHub a Streamlit Cloud.
2.  Asegúrate de configurar el `OPENAI_API_KEY` en los **"Secrets"** de la app en Streamlit.