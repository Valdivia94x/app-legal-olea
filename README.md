# 🤖 Asistente Legal Rápido (app-legal-olea) V1.1

Aplicación en Streamlit y Python que utiliza IA (OpenAI GPT-5) para redactar borradores de documentos legales.

Este proyecto es el MVP V1.1, que incluye un sistema de login, la capacidad de generar documentos "Generales" (basados en texto) y documentos "Pagaré" (con tablas de amortización calculadas).

## 🚀 Componentes del Proyecto

El sistema funciona con 4 archivos clave que deben estar en la misma carpeta:

1.  **`app.py`**: El código fuente principal de la aplicación Streamlit. Contiene toda la lógica de la UI, el "Cerebro" (llamadas a la API) y el "Ensamblador" (lógica de `python-docx`).
2.  **`requirements.txt`**: La lista de dependencias de Python necesarias.
3.  **`template_maestro.docx`**: El molde de Word para el flujo de "Documento General". Contiene los estilos (`Titulo_1`, `Parrafo_Justificado`, etc.).
4.  **`template_pagare.docx`**: El molde de Word para el flujo de "Pagaré". Contiene los estilos Y la tabla vacía de amortización (solo encabezados).

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

La app se abrirá automáticamente en tu navegador en `http://localhost:8501`.

## ☁️ Despliegue (Deploy)

Esta app está diseñada para desplegarse fácilmente en **Streamlit Community Cloud**.

1.  Conecta este repositorio de GitHub a Streamlit Cloud.
2.  Asegúrate de configurar el `OPENAI_API_KEY` en los **"Secrets"** de la app en Streamlit.