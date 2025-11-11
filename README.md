# 🤖 Asistente Legal Rápido (app-legal-olea) V2.1

Aplicación en Streamlit y Python que utiliza IA (OpenAI GPT-5/Pro y GPT-4o) para asistir en tareas legales.

Este proyecto V2.1 (final) incluye:
* Sistema de login seguro (agnóstico: `st.secrets` u `os.environ`).
* Interfaz de pestañas (Generador y Chatbot).
* **Generador de Documentos:** Crea documentos "Generales" (con listas V1.8) o "Pagarés" (con tablas V2.1 que incluyen **cálculos de IVA**).
* **Chatbot Analizador:** Un chatbot V1.7 (GPT-4o) que puede leer y **razonar** sobre el contenido de archivos `.docx` y `.pdf`.

## 🚀 Componentes del Proyecto

El sistema funciona con 5 archivos clave que deben estar en la misma carpeta:

1.  **`app.py`**: El código fuente principal (V2.1 agnóstico).
2.  **`requirements.txt`**: La lista de dependencias (`streamlit`, `openai`, `python-docx`, `PyMuPDF`).
3.  **`template_maestro.docx`**: El molde de Word para el flujo General (con estilo `Lista_Manual` V1.8).
4.  **`template_pagare.docx`**: El molde de Word para el flujo Pagaré (V1.7, sin tabla).
5.  **`.streamlit/config.toml`**: (Opcional, para forzar el modo oscuro).
6.  **`logo.png` / `favicon.png`**: Imágenes de marca.

## ⚙️ Instalación (Local)

1.  Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```
2.  Crea la carpeta de secretos locales: `.streamlit/secrets.toml` (asegúrate de que esté en `.gitignore`).

## ▶️ Ejecución (Local)

```bash
streamlit run app.py
```

## ☁️ Despliegue (Deploy)
Esta app está diseñada para desplegarse en cualquier servidor (Streamlit Cloud, Azure, AWS, On-Premise) ya que lee las credenciales desde st.secrets o (como fallback) desde os.environ.