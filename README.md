# 🔬 Scientific Article Aggregator

Una aplicación web moderna que automatiza la recolección, procesamiento y visualización de artículos científicos de múltiples bases de datos, generando resúmenes accesibles y posts divulgativos al estilo Medium.

## ✨ Características

- **🔍 Recolección Automatizada**: Escanea múltiples bases de datos científicas (arXiv, Europe PMC, Crossref, bioRxiv/medRxiv)
- **📝 Procesamiento Inteligente**: Genera resúmenes sin tecnicismos y posts divulgativos
- **🕸️ Knowledge Graph**: Visualiza relaciones entre artículos por temas, autores y fuentes
- **🎨 Interfaz Moderna**: Diseño minimalista al estilo Medium con Streamlit
- **⚡ Automatización**: Ejecución diaria programada para mantenerse actualizado
- **💾 Exportación**: Guarda contenido en formato Markdown

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

## 📖 Uso

### Interfaz Web

1. **Dashboard**: Vista general con métricas y artículos recientes
2. **Artículos**: Explorar y filtrar artículos recolectados
3. **Explorar**: Visualizar el knowledge graph de relaciones
4. **Configuración**: Personalizar temas y fuentes
5. **Analytics**: Estadísticas y tendencias

### Funciones Principales

- **Recolectar Artículos**: Busca nuevos artículos en las bases de datos configuradas
- **Procesar Artículos**: Genera resúmenes y posts divulgativos
- **Actualizar Grafo**: Reconstruye el knowledge graph con nuevas relaciones
- **Exportar Contenido**: Descarga posts en formato Markdown

## 🔧 Configuración

### Temas de Interés

Personaliza los temas en la sección de Configuración:
- Bioinformática
- Programación en biología
- Análisis de datos biológicos
- Interacción planta-microorganismos
- Educación científica
- Investigación en divulgación

### Fuentes de Datos

- **arXiv**: Artículos de preprint en ciencias
- **Europe PMC**: Base de datos biomédica europea
- **Crossref**: Metadatos de publicaciones académicas
- **bioRxiv/medRxiv**: Preprints en biología y medicina

## 📁 Estructura del Proyecto

```
scientific-article-aggregator/
├── streamlit_app.py              # Aplicación principal
├── requirements.txt              # Dependencias
├── .streamlit/config.toml       # Configuración de Streamlit
├── src/                         # Código fuente
│   ├── data_harvester/          # Recolección de datos
│   ├── article_processor/       # Procesamiento de artículos
│   ├── knowledge_graph/         # Grafo de conocimiento
│   ├── scheduler/               # Automatización
│   └── utils/                   # Utilidades
├── config/                      # Archivos de configuración
├── data/                        # Base de datos SQLite
├── outputs/                     # Posts generados
└── tests/                       # Pruebas
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 🆘 Soporte

Si tienes problemas con el despliegue:

1. **Verifica los logs** en Streamlit Cloud
2. **Revisa requirements.txt** - asegúrate de que todas las dependencias estén listadas
3. **Comprueba la estructura** - `streamlit_app.py` debe estar en la raíz
4. **Consulta la documentación** de [Streamlit Cloud](https://docs.streamlit.io/streamlit-cloud)

## 🌟 Características Futuras

- [ ] Integración con más bases de datos científicas
- [ ] Análisis de sentimientos en artículos
- [ ] Recomendaciones personalizadas
- [ ] API REST para integración externa
- [ ] Notificaciones por email
- [ ] Exportación a diferentes formatos

---

**Desarrollado con ❤️ para la comunidad científica**

