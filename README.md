# Simulador educativo de CO₂

Adaptación a Streamlit del simulador de CO₂ y radiación infrarroja del proyecto PAPIME PE101026. Conserva el motor físico conceptual en Python e incorpora controles y explicaciones didácticas.

## Ejecución local

Se probó con Python 3.13 y Streamlit 1.66. Desde esta carpeta:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

## Publicación en Streamlit Community Cloud

1. Sube los archivos de esta carpeta a la raíz de un repositorio GitHub. No subas una carpeta `.venv` ni un ZIP como archivo de la aplicación.
2. En https://share.streamlit.io, crea una aplicación a partir de ese repositorio. Indica la rama `main` y el archivo principal `app.py`.
3. En ajustes avanzados elige Python 3.13, la versión utilizada en las pruebas.
4. Publica y prueba la dirección `*.streamlit.app` generada.

`requirements.txt` está junto a `app.py`, de modo que Community Cloud pueda instalar las dependencias. La aplicación no requiere secretos ni base de datos.

## Alcance

El modelo es bidimensional, ilustrativo y no calcula predicciones climáticas. Las bandas, velocidades, tiempos y probabilidades son aproximaciones pedagógicas. La fluidez con muchos estudiantes simultáneos debe verificarse en el entorno de publicación.
