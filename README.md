# 🔬 Scientific Article Aggregator

Una aplicación web moderna para buscar, guardar y visualizar artículos científicos de múltiples bases de datos, con exploración por palabras clave, integración de feeds RSS, visualización en tarjetas, panel de detalles, y grafo de conocimiento de artículos guardados. Pensada para facilitar la exploración y organización de literatura científica de forma sencilla y visual.

## ✨ Características

- **🔍 Búsqueda avanzada**: Busca artículos en arXiv, Europe PMC, Crossref, bioRxiv/medRxiv y RSS personalizados
- **🗂️ Guardado de artículos**: Marca y organiza artículos de interés
- **🕸️ Grafo de conocimiento**: Visualiza relaciones entre artículos guardados por temas, autores y fuentes
- **🎨 Interfaz moderna**: Diseño minimalista tipo Medium con Streamlit
- **📥 Exportación**: Descarga artículos guardados en formato Markdown, JSON o CSV
- **⚡ Automatización**: Ejecución diaria programada (opcional)

## 🚀 Despliegue en Streamlit Cloud

### Paso 1: Subir a GitHub

1. **Crear repositorio en GitHub**:
   ```bash
   # En tu máquina local, clona este proyecto
   git clone <URL_DE_ESTE_REPO>
   cd scientific-article-aggregator
   ```

2. **Configurar Git** (si es necesario):
   ```bash
   git config --global user.name "Tu Nombre"
   git config --global user.email "tu@email.com"
   ```

3. **Subir cambios**:
   ```bash
   git add .
   git commit -m "Initial commit: Scientific Article Aggregator"
   git push origin main
   ```

### Paso 2: Desplegar en Streamlit Cloud

1. **Ir a [share.streamlit.io](https://share.streamlit.io)**

2. **Conectar con GitHub**:
   - Haz clic en "New app"
   - Conecta tu cuenta de GitHub
   - Selecciona tu repositorio `scientific-article-aggregator`

3. **Configurar el despliegue**:
   - **Repository**: `tu-usuario/scientific-article-aggregator`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`

4. **Hacer clic en "Deploy!"**

### Paso 3: Configuración Adicional (Opcional)

Si necesitas variables de entorno o configuraciones especiales:

1. **Crear archivo `secrets.toml`** (local, no subir a GitHub):
   ```toml
   # .streamlit/secrets.toml
   [api_keys]
   # Agregar claves de API si las necesitas
   ```

2. **Configurar secrets en Streamlit Cloud**:
   - Ve a tu app desplegada
   - Haz clic en "Settings" → "Secrets"
   - Agrega las variables necesarias

## 🛠️ Instalación Local

```bash
# Clonar el repositorio
git clone <URL_DEL_REPO>
cd scientific-article-aggregator

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
streamlit run streamlit_app.py
```

## 📖 Navegación y Uso

### Páginas principales

1. **Buscar artículos**: Ingresa palabras clave, selecciona fuentes y explora resultados en tarjetas. Haz clic en una tarjeta para ver detalles y guardar artículos de interés.
2. **Artículos guardados**: Visualiza, elimina y exporta tus artículos favoritos.
3. **Grafo de conocimiento**: Explora visualmente las relaciones entre los artículos guardados por temas, autores y fuentes.
4. **Configuración**: Gestiona feeds RSS, temas de interés y preferencias de la app.

### Funciones principales

- **Buscar y filtrar artículos** por palabras clave y fuente
- **Agregar feeds RSS** personalizados
- **Guardar y eliminar artículos** de interés
- **Ver detalles completos** (abstract traducido, autores, fuente, fecha, DOI, URL)
- **Exportar artículos guardados** en Markdown, JSON o CSV
- **Visualizar el grafo de conocimiento** de tus artículos

## 🔧 Configuración

- Personaliza temas y fuentes en la sección de Configuración
- Agrega tus propios feeds RSS
- Configura claves API en `config/api_keys.yaml` si es necesario

## 🤝 Contribuir

1. Haz fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/NuevaFeature`)
3. Commit a tus cambios (`git commit -m 'Agrega NuevaFeature'`)
4. Push a la rama (`git push origin feature/NuevaFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 🆘 Soporte

- Verifica los logs en la carpeta `logs/` o en Streamlit Cloud
- Revisa `requirements.txt` y la estructura del proyecto
- Consulta la documentación de [Streamlit](https://docs.streamlit.io/)

## 🌟 Características Futuras

- [ ] Integración con más bases de datos científicas
- [ ] Análisis de sentimientos en artículos
- [ ] Recomendaciones personalizadas
- [ ] API REST para integración externa
- [ ] Notificaciones por email
- [ ] Exportación a diferentes formatos

---

**Desarrollado con ❤️ para la comunidad científica**

## 📁 Estructura del Proyecto

```
scientific-article-aggregator-complete/
├── streamlit_app.py              # Aplicación principal Streamlit
├── requirements.txt              # Dependencias
├── .streamlit/
│   └── config.toml               # Configuración de Streamlit
├── src/                          # Código fuente
│   ├── data_harvester/           # Recolección de datos (APIs, RSS)
│   ├── article_processor/        # Utilidades de texto y limpieza
│   ├── knowledge_graph/          # Grafo de conocimiento
│   ├── scheduler/                # Automatización (opcional)
│   └── utils/                    # Utilidades generales y base de datos
├── config/                       # Archivos de configuración y claves
├── data/                         # Base de datos SQLite
│   └── articles.db
├── outputs/                      # Exportaciones y posts generados
├── tests/                        # Pruebas unitarias y de integración
│   ├── test_harvesters.py
│   └── test_processor.py
├── logs/                         # (opcional) Archivos de log de la app
└── README.md
```

