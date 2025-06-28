# 🚀 Guía Completa de Despliegue

## Paso a Paso: GitHub + Streamlit Cloud

### 1. Preparar el Proyecto para GitHub

#### A. Verificar la estructura del proyecto
```
scientific-article-aggregator/
├── streamlit_app.py          ← Archivo principal (OBLIGATORIO)
├── requirements.txt          ← Dependencias (OBLIGATORIO)
├── .streamlit/config.toml   ← Configuración de Streamlit
├── README.md                ← Documentación
├── .gitignore              ← Archivos a ignorar
└── src/                    ← Código fuente
```

#### B. Limpiar archivos innecesarios
```bash
# Eliminar archivos temporales
rm -rf __pycache__/
rm -rf *.pyc
rm -rf .pytest_cache/
rm -rf data/*.db  # Base de datos local (se recreará)
```

### 2. Subir a GitHub

#### A. Crear repositorio en GitHub
1. Ve a [github.com](https://github.com)
2. Haz clic en "New repository"
3. Nombre: `scientific-article-aggregator`
4. Descripción: "Agregador automático de artículos científicos con interfaz web moderna"
5. Público o Privado (tu elección)
6. **NO** inicializar con README (ya tenemos uno)
7. Haz clic en "Create repository"

#### B. Subir el código
```bash
# En tu máquina local (o descarga el proyecto del sandbox)
cd scientific-article-aggregator

# Inicializar Git (si no está inicializado)
git init

# Agregar archivos
git add .

# Primer commit
git commit -m "Initial commit: Scientific Article Aggregator"

# Conectar con GitHub (reemplaza TU_USUARIO)
git remote add origin https://github.com/TU_USUARIO/scientific-article-aggregator.git

# Subir código
git branch -M main
git push -u origin main
```

### 3. Desplegar en Streamlit Cloud

#### A. Acceder a Streamlit Cloud
1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Haz clic en "Sign up" o "Sign in"
3. **Conecta con GitHub** (usa la misma cuenta donde subiste el repo)

#### B. Crear nueva app
1. Haz clic en "New app"
2. Selecciona "From existing repo"
3. Configurar:
   - **Repository**: `TU_USUARIO/scientific-article-aggregator`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`
   - **App URL**: `scientific-article-aggregator` (o el nombre que prefieras)

#### C. Desplegar
1. Haz clic en "Deploy!"
2. Espera 2-5 minutos mientras se instalan las dependencias
3. ¡Tu app estará lista!

### 4. URL Final

Tu aplicación estará disponible en:
```
https://TU_USUARIO-scientific-article-aggregator-streamlit-app-HASH.streamlit.app
```

O si personalizaste la URL:
```
https://scientific-article-aggregator.streamlit.app
```

## 🔧 Solución de Problemas Comunes

### Error: "Module not found"
**Problema**: Falta una dependencia en `requirements.txt`
**Solución**: 
1. Agregar la dependencia faltante a `requirements.txt`
2. Hacer commit y push
3. Streamlit Cloud se actualizará automáticamente

### Error: "File not found"
**Problema**: Rutas incorrectas o archivos faltantes
**Solución**:
1. Verificar que `streamlit_app.py` esté en la raíz
2. Verificar rutas relativas en el código
3. Asegurar que todos los archivos necesarios estén en GitHub

### Error: "App crashed"
**Problema**: Error en el código o configuración
**Solución**:
1. Ver logs en Streamlit Cloud (botón "Manage app" → "Logs")
2. Probar localmente: `streamlit run streamlit_app.py`
3. Corregir errores y hacer push

### Base de datos vacía
**Problema**: No hay datos al iniciar
**Solución**: 
1. La app creará automáticamente la base de datos
2. Usar los botones "Recolectar Artículos" y "Procesar Artículos"
3. Los datos se mantendrán mientras la app esté activa

## 🎨 Personalización de la Interfaz

### Cambiar colores y tema
Edita `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#FF6B6B"        # Color principal
backgroundColor = "#FFFFFF"     # Fondo
secondaryBackgroundColor = "#F0F2F6"  # Fondo secundario
textColor = "#262730"          # Color del texto
font = "serif"                 # Fuente: "sans serif", "serif", "monospace"
```

### Personalizar CSS
En `streamlit_app.py`, modifica la sección de CSS:
```python
st.markdown("""
<style>
    /* Tu CSS personalizado aquí */
    .main-title {
        color: #tu-color;
        font-size: 4rem;
    }
</style>
""", unsafe_allow_html=True)
```

## 🔄 Actualizaciones Automáticas

Streamlit Cloud se actualiza automáticamente cuando haces push a GitHub:

```bash
# Hacer cambios en el código
git add .
git commit -m "Descripción de los cambios"
git push origin main
```

La app se redesplegará automáticamente en 1-2 minutos.

## 📊 Monitoreo y Logs

### Ver logs de la aplicación
1. Ve a tu app en Streamlit Cloud
2. Haz clic en "Manage app"
3. Selecciona "Logs" para ver errores y debug info

### Métricas de uso
Streamlit Cloud proporciona métricas básicas:
- Número de visitantes
- Tiempo de actividad
- Uso de recursos

## 🔒 Configuración Avanzada

### Variables de entorno (secrets)
Si necesitas API keys u otras configuraciones sensibles:

1. **Crear archivo local** `.streamlit/secrets.toml`:
```toml
[api_keys]
openai_key = "tu-api-key"
other_key = "otro-valor"
```

2. **Configurar en Streamlit Cloud**:
   - Manage app → Settings → Secrets
   - Copiar el contenido del archivo secrets.toml

3. **Usar en el código**:
```python
import streamlit as st
api_key = st.secrets["api_keys"]["openai_key"]
```

### Dominio personalizado
Para usar tu propio dominio:
1. Upgrade a Streamlit Cloud Pro
2. Configurar DNS CNAME
3. Configurar en settings de la app

## 🎯 Optimización para Producción

### Performance
- Usar `@st.cache_data` para funciones costosas
- Limitar el número de artículos mostrados
- Implementar paginación para listas largas

### Seguridad
- No incluir API keys en el código
- Usar secrets para información sensible
- Validar inputs del usuario

### Escalabilidad
- Considerar base de datos externa para muchos usuarios
- Implementar rate limiting
- Usar CDN para assets estáticos

---

¡Tu aplicación estará lista para compartir con el mundo! 🌍

