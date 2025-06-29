"""
Scientific Article Aggregator - Aplicación Streamlit
Interfaz web minimalista y moderna al estilo de Medium
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from datetime import datetime, timedelta
import yaml
import os
import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent / "src"))

from src.utils.database import db_manager
from src.data_harvester.harvester_manager import harvester_manager
from src.article_processor.processor_manager import processor_manager
from src.knowledge_graph.graph_builder import graph_builder
from src.data_harvester.rss_harvester import rss_harvester

# Función para traducir texto al español
def translate_to_spanish(text, max_length=2000):
    """
    Traduce texto al español usando deep-translator.
    
    Args:
        text: Texto a traducir
        max_length: Longitud máxima del texto a traducir
        
    Returns:
        Texto traducido o None si hay error
    """
    try:
        from deep_translator import GoogleTranslator
        import re
        
        # Limpiar etiquetas HTML/XML
        if text:
            # Remover etiquetas JATS y HTML
            text = re.sub(r'<[^>]+>', '', text)
            # Remover espacios múltiples
            text = re.sub(r'\s+', ' ', text)
            # Limpiar caracteres especiales
            text = text.strip()
        
        # Verificar que el texto no esté vacío después de la limpieza
        if not text or len(text.strip()) < 10:
            return None
        
        # Para abstracts largos, dividir en chunks para traducción
        if len(text) > max_length:
            # Dividir en oraciones para mantener coherencia
            sentences = re.split(r'[.!?]+', text)
            translated_parts = []
            current_chunk = ""
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                if len(current_chunk + sentence) < max_length:
                    current_chunk += sentence + ". "
                else:
                    if current_chunk:
                        translator = GoogleTranslator(source='auto', target='es')
                        translation = translator.translate(current_chunk)
                        translated_parts.append(translation)
                    current_chunk = sentence + ". "
            
            # Traducir el último chunk
            if current_chunk:
                translator = GoogleTranslator(source='auto', target='es')
                translation = translator.translate(current_chunk)
                translated_parts.append(translation)
            
            return " ".join(translated_parts)
        else:
            # Traducir texto completo
            translator = GoogleTranslator(source='auto', target='es')
            translation = translator.translate(text)
            return translation
            
    except Exception as e:
        st.error(f"Error en traducción: {e}")
        return None

# Configuración de la página
st.set_page_config(
    page_title="Scientific Article Aggregator",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para estilo Medium
st.markdown("""
<style>
    /* Tipografía global */
    * {
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif !important;
    }
    
    /* Títulos principales */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif !important;
        font-weight: 500 !important;
    }
    
    /* Títulos de páginas principales en negritas */
    .page-title {
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif !important;
        font-weight: 700 !important;
        font-size: 2rem !important;
        color: #1f2937 !important;
        margin-bottom: 1rem !important;
    }
    
    /* Subtítulos con tipografía diferente */
    .section-title {
        font-family: 'Georgia', 'Times New Roman', serif !important;
        font-weight: 600 !important;
        font-size: 1.3rem !important;
        color: #374151 !important;
        margin-bottom: 0.8rem !important;
        font-style: italic !important;
    }
    
    /* Título principal */
    .main-title {
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif !important;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: #1f2937 !important;
        margin-bottom: 0.5rem !important;
        text-align: center !important;
    }
    
    /* Subtítulo */
    .main-subtitle {
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif !important;
        font-size: 1.1rem !important;
        font-weight: 400 !important;
        color: #6b7280 !important;
        text-align: center !important;
        margin-bottom: 2rem !important;
    }
    
    /* Texto de lectura */
    p, div, span, label {
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif !important;
        font-weight: 400 !important;
    }
    
    /* Sidebar */
    .css-1d391kg {
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif !important;
    }
    
    /* Botones */
    .stButton > button {
        background: #f5f5f5;
        color: #222;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 0.45rem 1.2rem;
        font-weight: 500;
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif;
        transition: background 0.2s, color 0.2s, border 0.2s;
        box-shadow: none;
    }
    .stButton > button:hover {
        background: #eaeaea;
        color: #111;
        border: 1px solid #bdbdbd;
    }
    .sidebar .sidebar-content {
        background: #f7f8fa;
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif;
    }
    .sidebar h3 {
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif;
        font-weight: 600;
        color: #222;
    }
    .sidebar p {
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif;
    }
    .sidebar .stSelectbox {
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif;
    }
    .sidebar .stButton > button {
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif;
    }
    .metric-card {
        background: #f7f8fa;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        margin-bottom: 1rem;
        border: 1px solid #ececec;
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif;
    }
    .metric-card h2 {
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif;
        font-weight: 700;
        color: #222;
    }
    .metric-card h3 {
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif;
        font-weight: 600;
        color: #666;
        margin-bottom: 0.5rem;
    }
    .metric-card p {
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif;
        color: #888;
        margin-top: 0.5rem;
    }
    .chart-container {
        background: #fff;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(30,34,40,0.06);
        margin-bottom: 2rem;
        border: 1px solid #ececec;
    }
    .loading-text {
        text-align: center;
        color: #888;
        font-style: italic;
        padding: 2rem;
    }
    /* Estilo para página activa en sidebar */
    .sidebar .stSelectbox > div > div > div > div {
        background-color: #3b82f6 !important;
        color: white !important;
    }
    /* Estilo para botones de acción */
    .action-button {
        background: #3b82f6 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 500 !important;
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif !important;
        transition: all 0.2s ease !important;
    }
    .action-button:hover {
        background: #2563eb !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
    }
    /* Estilo para botón de limpiar BD */
    .danger-button {
        background: #ef4444 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 500 !important;
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif !important;
        transition: all 0.2s ease !important;
    }
    .danger-button:hover {
        background: #dc2626 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3) !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    /* Estilo para textarea de palabras clave */
    .stTextArea > div > div > textarea {
        border: 2px solid #e0e0e0 !important;
        border-radius: 8px !important;
        padding: 12px !important;
        font-family: 'Roboto', 'Segoe UI', 'Arial', sans-serif !important;
        transition: border-color 0.2s ease !important;
    }
    .stTextArea > div > div > textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }
    /* Panel de detalles en el lado derecho */
    .details-panel {
        position: fixed;
        top: 0;
        right: 0;
        width: 400px;
        height: 100vh;
        background: white;
        border-left: 1px solid #e0e0e0;
        box-shadow: -2px 0 8px rgba(0,0,0,0.1);
        z-index: 1000;
        overflow-y: auto;
        padding: 20px;
        transform: translateX(100%);
        transition: transform 0.3s ease;
    }
    .details-panel.open {
        transform: translateX(0);
    }
    /* Overlay para el panel */
    .details-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0,0,0,0.3);
        z-index: 999;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
    }
    .details-overlay.open {
        opacity: 1;
        visibility: visible;
    }
    /* Panel lateral derecho */
    .right-panel {
        position: fixed;
        top: 0;
        right: -400px;
        width: 400px;
        height: 100vh;
        background: white;
        border-left: 1px solid #e0e0e0;
        box-shadow: -2px 0 8px rgba(0,0,0,0.1);
        z-index: 1000;
        overflow-y: auto;
        padding: 20px;
        transition: right 0.3s ease;
    }
    .right-panel.open {
        right: 0;
    }
    /* Overlay para el panel */
    .panel-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0,0,0,0.3);
        z-index: 999;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
    }
    .panel-overlay.open {
        opacity: 1;
        visibility: visible;
    }
    /* Botón para cerrar panel */
    .close-panel-btn {
        position: absolute;
        top: 10px;
        right: 10px;
        background: #f5f5f5;
        border: 1px solid #e0e0e0;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 16px;
        color: #666;
    }
    .close-panel-btn:hover {
        background: #e0e0e0;
    }
    /* Contenido del panel */
    .panel-content {
        margin-top: 40px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Función principal de la aplicación."""
    
    # Título principal
    st.markdown('<h1 class="main-title">Scientific Article Aggregator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="main-subtitle">Tu fuente diaria de descubrimientos científicos, simplificados y accesibles</p>', unsafe_allow_html=True)
    
    # Sidebar para navegación
    with st.sidebar:
        st.markdown("### Navegación")
        page = st.selectbox(
            "Selecciona una página:",
            ["Búsqueda", "Artículos", "Estadísticas"]
        )
        
        # Subpáginas para Artículos
        if page == "Artículos":
            subpage = st.selectbox(
                "Selecciona una sección:",
                ["Listado", "Grafo", "Exportar"]
            )
        else:
            subpage = None
        
        st.markdown("---")
        
        # Métricas de búsqueda
        if page == "Búsqueda":
            st.markdown("### Métricas")
            
            try:
                # Obtener estadísticas con mejor manejo de errores
                try:
                    all_articles = db_manager.get_recent_articles(days=365, limit=1000)
                    total_found = len(all_articles)  # Total de artículos encontrados
                    saved_articles = len([a for a in all_articles if hasattr(a, 'saved') and a.saved])
        except Exception as e:
                    st.error(f"Error obteniendo artículos totales: {e}")
                    total_found = 0
                    saved_articles = 0
                
                try:
                    # Artículos guardados en los últimos 7 días
                    recent_saved = len([a for a in db_manager.get_recent_articles(days=7, limit=1000) 
                                      if hasattr(a, 'saved') and a.saved])
                except Exception as e:
                    st.error(f"Error obteniendo artículos recientes: {e}")
                    recent_saved = 0
                
                # Métricas en el sidebar
                col1, col2 = st.columns(2)
        
        with col1:
                    st.metric("Total Encontrados", total_found)
                    st.metric("Guardados", saved_articles)
        
        with col2:
                    st.metric("Nuevos (7 días)", recent_saved)
                    if total_found > 0:
                        save_rate = (saved_articles / total_found) * 100
                        st.metric("Tasa Guardado", f"{save_rate:.1f}%")
                    else:
                        st.metric("Tasa Guardado", "0%")
                
            except Exception as e:
                st.error(f"Error cargando métricas: {e}")
            
            st.markdown("---")
            
            # Fuentes de datos en el sidebar
            st.markdown("### Fuentes de Datos")
            arxiv_enabled = st.checkbox("arXiv", value=True, key="arxiv_sidebar")
            europepmc_enabled = st.checkbox("Europe PMC (incluye PubMed)", value=True, key="europepmc_sidebar")
            crossref_enabled = st.checkbox("Crossref", value=True, key="crossref_sidebar")
            biorxiv_enabled = st.checkbox("bioRxiv/medRxiv", value=True, key="biorxiv_sidebar")
            
            # Guardar configuración en session state
            st.session_state.enabled_sources = {
                'arxiv': arxiv_enabled,
                'europepmc': europepmc_enabled,
                'crossref': crossref_enabled,
                'biorxiv': biorxiv_enabled
            }
        
        st.markdown("---")
        
        # Gestión de RSS feeds
        st.markdown("### 📡 Gestión RSS")
        
        if st.button("Gestionar RSS Feeds", key="manage_rss", use_container_width=True):
            st.session_state.show_rss_manager = True
        
        # Inicializar lista de RSS feeds en session state
        if 'rss_feeds' not in st.session_state:
            st.session_state.rss_feeds = []
        
        # Mostrar RSS feeds guardados
        if st.session_state.rss_feeds:
            st.markdown("**RSS Feeds guardados:**")
            for i, feed in enumerate(st.session_state.rss_feeds):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(feed[:50] + "..." if len(feed) > 50 else feed)
                with col2:
                    if st.button("❌", key=f"remove_rss_{i}"):
                        st.session_state.rss_feeds.pop(i)
                        st.rerun()
        
        # Gestor de RSS feeds
        if hasattr(st.session_state, 'show_rss_manager') and st.session_state.show_rss_manager:
            st.markdown("#### Agregar RSS Feed")
            new_rss = st.text_input("URL del RSS feed:", placeholder="https://ejemplo.com/rss")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Agregar RSS"):
                    if new_rss and new_rss not in st.session_state.rss_feeds:
                        if rss_harvester.validate_rss_url(new_rss):
                            st.session_state.rss_feeds.append(new_rss)
                            st.success("✅ RSS agregado")
                            st.rerun()
        else:
                            st.error("❌ URL de RSS inválida")
                    elif new_rss in st.session_state.rss_feeds:
                        st.warning("⚠️ Este RSS ya está en la lista")
            
            with col2:
                if st.button("Cerrar"):
                    st.session_state.show_rss_manager = False
                    st.rerun()
        
        st.markdown("---")
        
        # Botón para limpiar base de datos
        st.markdown("### Administración")
        
        # Mostrar confirmación antes de limpiar
        if 'show_clear_confirm' not in st.session_state:
            st.session_state.show_clear_confirm = False
        
        if not st.session_state.show_clear_confirm:
            col1, col2 = st.columns(2)
        with col1:
                if st.button("Limpiar Base de Datos", key="clear_db", use_container_width=True):
                    st.session_state.show_clear_confirm = True
                    st.rerun()
            with col2:
                if st.button("Limpiar Fechas Inválidas", key="clean_dates", use_container_width=True):
                    with st.spinner("Limpiando fechas inválidas..."):
                        try:
                            corrected_count = db_manager.clean_invalid_dates()
                            if corrected_count > 0:
                                st.success(f"✅ {corrected_count} fechas inválidas corregidas")
                            else:
                                st.info("✅ No se encontraron fechas inválidas")
                        st.rerun()
                    except Exception as e:
                            st.error(f"Error limpiando fechas: {e}")
        else:
            st.warning("⚠️ ¿Estás seguro de que quieres limpiar completamente la base de datos? Esta acción no se puede deshacer.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Sí, limpiar", key="confirm_clear", use_container_width=True):
                    with st.spinner("Limpiando base de datos..."):
                        try:
                            success = db_manager.clear_database()
                            if success:
                                st.success("Base de datos limpiada exitosamente")
                            else:
                                st.error("Error al limpiar la base de datos")
                            st.session_state.show_clear_confirm = False
                        st.rerun()
                    except Exception as e:
                            st.error(f"Error limpiando base de datos: {e}")
                            st.session_state.show_clear_confirm = False
            with col2:
                if st.button("Cancelar", key="cancel_clear", use_container_width=True):
                    st.session_state.show_clear_confirm = False
                    st.rerun()
    
    # Contenido principal basado en la página seleccionada
    if page == "Búsqueda":
        show_dashboard()
    elif page == "Artículos":
        if subpage == "Listado":
            show_saved_articles()
        elif subpage == "Grafo":
            show_articles_graph()
        elif subpage == "Exportar":
            show_export_articles()
    elif page == "Estadísticas":
        show_analytics()

def perform_search(keywords_input, max_articles):
    """Realiza la búsqueda de artículos."""
    try:
        # Convertir palabras clave a lista
        keywords = [kw.strip() for kw in keywords_input.split('\n') if kw.strip()]
        
        # Configurar fuentes habilitadas desde el sidebar
        enabled_sources = []
        if hasattr(st.session_state, 'enabled_sources'):
            for source, enabled in st.session_state.enabled_sources.items():
                if enabled:
                    enabled_sources.append(source)
        else:
            # Default si no hay configuración
            enabled_sources = ["arxiv", "europepmc", "crossref", "biorxiv"]
        
        # Realizar búsqueda
        stats = harvester_manager.harvest_all_sources(
            topics=keywords, 
            max_articles_per_source=max_articles,
            sources=enabled_sources
        )
        
        # Agregar RSS feeds guardados
        if hasattr(st.session_state, 'rss_feeds') and st.session_state.rss_feeds:
            for i, rss_url in enumerate(st.session_state.rss_feeds):
                try:
                    rss_articles = rss_harvester.harvest(rss_url, max_articles)
                    if rss_articles:
                        stats[f"rss_{i}"] = rss_articles
                        st.info(f"📡 RSS {i+1}: {len(rss_articles)} artículos encontrados")
                    except Exception as e:
                    st.warning(f"Error con RSS {i+1}: {e}")
        
        total_found = sum(len(articles) for articles in stats.values())
        st.success(f"✅ Encontrados {total_found} artículos")
        
        # Guardar resultados en session state
        st.session_state.search_results = []
        for source, articles in stats.items():
            st.session_state.search_results.extend(articles)
        
        # No hacer st.rerun() aquí para evitar bucles infinitos
        
    except Exception as e:
        st.error(f"Error en búsqueda: {e}")

def show_dashboard():
    """Muestra la página de búsqueda principal con configuración."""
    st.markdown('<h1 class="page-title">Búsqueda</h1>', unsafe_allow_html=True)
    
    # Configuración de búsqueda
    st.markdown("### Configuración de Búsqueda")
    
    # Inicializar palabras clave en session state
    if 'default_keywords' not in st.session_state:
        st.session_state.default_keywords = "bioinformatics\ncomputational biology\nmachine learning\ndata analysis"
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Palabras Clave")
        keywords_input = st.text_area(
            "Escribre una palabra clave por línea",
            value=st.session_state.default_keywords,
            height=150,
            key="keywords_dash"
        )
        
        # Guardar palabras clave cuando cambien
        if keywords_input != st.session_state.default_keywords:
            st.session_state.default_keywords = keywords_input
            st.session_state.keywords_changed = True
    
    with col2:
        max_articles = st.number_input("Máx. artículos por fuente", min_value=1, max_value=50, value=10, key="max_articles_dash")
    
    # Botón de búsqueda
    st.markdown("---")
    if st.button("🔍 Buscar Artículos", use_container_width=True, key="search_btn"):
        with st.spinner("Buscando artículos..."):
            perform_search(keywords_input, max_articles)
    
    # Mostrar resultados de búsqueda
    if hasattr(st.session_state, 'search_results') and st.session_state.search_results:
        st.markdown("---")
        st.markdown(f'<h3 class="section-title">Resultados de Búsqueda ({len(st.session_state.search_results)} artículos)</h3>', unsafe_allow_html=True)
        
        # Filtros para resultados
        col1, col2 = st.columns(2)
        with col1:
            source_filter = st.selectbox("Filtrar por fuente:", ["Todas"] + list(set([a.source for a in st.session_state.search_results])))
        with col2:
            sort_by = st.selectbox("Ordenar por:", ["Fecha", "Título", "Fuente"])
        
        # Aplicar filtros
        filtered_results = st.session_state.search_results
        if source_filter != "Todas":
            if source_filter == "europepmc (incluye PubMed)":
                filtered_results = [a for a in filtered_results if a.source == "europepmc"]
            else:
                filtered_results = [a for a in filtered_results if a.source == source_filter]
        
        # Ordenar resultados
        if sort_by == "Fecha":
            filtered_results.sort(key=lambda x: x.publication_date or datetime.min, reverse=True)
        elif sort_by == "Título":
            filtered_results.sort(key=lambda x: x.title.lower())
        elif sort_by == "Fuente":
            filtered_results.sort(key=lambda x: x.source)
        
        # Mostrar artículos en cards
        for i, article in enumerate(filtered_results):
            show_search_result_card(article, i)
    
    # Búsqueda automática solo una vez al cargar la página
    if 'auto_search_done' not in st.session_state:
        st.session_state.auto_search_done = False
    
    # Solo hacer búsqueda automática si no se ha hecho antes
    if not st.session_state.auto_search_done:
        st.info("💡 Haz clic en 'Buscar Artículos' para comenzar a buscar")
        st.session_state.auto_search_done = True
    
    # Artículos guardados recientemente
    st.markdown("---")
    st.markdown('<h3 class="section-title">Artículos Guardados Recientemente</h3>', unsafe_allow_html=True)
    
    saved_articles_data = [a for a in db_manager.get_recent_articles(days=30, limit=10) if hasattr(a, 'saved') and a.saved]
    
    if saved_articles_data:
        for article in saved_articles_data:
            show_article_card(article)
    else:
        st.info("No hay artículos guardados. Busca artículos y guárdalos para verlos aquí.")

def show_saved_articles():
    """Muestra la lista de artículos guardados."""
    st.markdown('<h1 class="page-title">Artículos Guardados</h1>', unsafe_allow_html=True)
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        days_filter = st.selectbox("Período", [7, 14, 30, 90, 365], index=2, key="saved_days")
    
    with col2:
        source_filter = st.selectbox("Fuente", ["Todas", "arxiv", "europepmc (incluye PubMed)", "crossref", "biorxiv"], key="saved_source")
    
    with col3:
        limit_filter = st.selectbox("Límite", [10, 20, 50, 100], index=1, key="saved_limit")
    
    # Obtener artículos guardados
    try:
        all_articles = db_manager.get_recent_articles(days=days_filter, limit=limit_filter)
        saved_articles = [a for a in all_articles if hasattr(a, 'saved') and a.saved]
        
        if source_filter != "Todas":
            if source_filter == "europepmc (incluye PubMed)":
                saved_articles = [a for a in saved_articles if a.source == "europepmc"]
            else:
                saved_articles = [a for a in saved_articles if a.source == source_filter]
        
        st.markdown(f'<h3 class="section-title">Mostrando {len(saved_articles)} artículos guardados</h3>', unsafe_allow_html=True)
        
        if saved_articles:
            for article in saved_articles:
                show_article_card(article, show_full=True)
        else:
            st.info("No hay artículos guardados con los filtros seleccionados.")
    
    except Exception as e:
        st.error(f"Error cargando artículos guardados: {e}")

def show_articles_graph():
    """Muestra el grafo de artículos guardados."""
    st.markdown('<h1 class="page-title">Grafo de Artículos Guardados</h1>', unsafe_allow_html=True)
    
    try:
        # Obtener artículos guardados para el grafo
        all_articles = db_manager.get_recent_articles(days=365, limit=100)
        saved_articles = [a for a in all_articles if hasattr(a, 'saved') and a.saved]
        
        if saved_articles:
            graph = graph_builder.build_graph(saved_articles)
            
            if graph.nodes:
                # Estadísticas del grafo
                stats = graph_builder.get_graph_statistics()
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Nodos (Artículos)", stats['nodes'])
                
                with col2:
                    st.metric("Conexiones", stats['edges'])
                
                with col3:
                    st.metric("Componentes", stats['components'])
                
                # Visualización del grafo
                st.markdown('<h3 class="section-title">Visualización del Grafo</h3>', unsafe_allow_html=True)
                
                if stats['nodes'] > 0:
                    # Crear visualización con plotly
                    pos = nx.spring_layout(graph, k=1, iterations=50)
                    
                    # Preparar datos para plotly
                    edge_x = []
                    edge_y = []
                    for edge in graph.edges():
                        x0, y0 = pos[edge[0]]
                        x1, y1 = pos[edge[1]]
                        edge_x.extend([x0, x1, None])
                        edge_y.extend([y0, y1, None])
                    
                    node_x = []
                    node_y = []
                    node_text = []
                    node_size = []
                    
                    for node in graph.nodes():
                        x, y = pos[node]
                        node_x.append(x)
                        node_y.append(y)
                        
                        node_data = graph.nodes[node]
                        title = node_data.get('title', 'Unknown')[:50] + "..."
                        source = node_data.get('source', 'Unknown')
                        node_text.append(f"{title}<br>Fuente: {source}")
                        node_size.append(node_data.get('node_size', 10))
                    
                    # Crear figura
                    fig = go.Figure()
                    
                    # Agregar edges
                    fig.add_trace(go.Scatter(
                        x=edge_x, y=edge_y,
                        line=dict(width=0.5, color='#888'),
                        hoverinfo='none',
                        mode='lines'
                    ))
                    
                    # Agregar nodes
                    fig.add_trace(go.Scatter(
                        x=node_x, y=node_y,
                        mode='markers',
                        hoverinfo='text',
                        text=node_text,
                        marker=dict(
                            size=node_size,
                            color='#3b82f6',
                            line=dict(width=2, color='white')
                        )
                    ))
                    
                    fig.update_layout(
                        title="Knowledge Graph de Artículos Guardados",
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        annotations=[
                            dict(
                                text="Cada nodo representa un artículo guardado. Las conexiones muestran relaciones por temas, autores o fuente.",
                                showarrow=False,
                                xref="paper", yref="paper",
                                x=0.005, y=-0.002,
                                xanchor='left', yanchor='bottom',
                                font=dict(color='#6b7280', size=12)
                            )
                        ],
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        height=600
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Artículos más conectados
                if stats.get('top_connected_articles'):
                    st.markdown("### Artículos Más Conectados")
                    
                    for i, article_info in enumerate(stats['top_connected_articles'][:5], 1):
                        st.markdown(f"""
                        **{i}. {article_info['title']}**  
                        *{article_info['connections']} conexiones | Fuente: {article_info['source']}*
                        """)
            else:
                st.info("No hay suficientes artículos guardados para generar el knowledge graph.")
        else:
            st.info("No hay artículos guardados. Guarda algunos artículos para generar el grafo.")
    
    except Exception as e:
        st.error(f"Error en grafo: {e}")

def show_export_articles():
    """Muestra la página de exportación de artículos."""
    st.markdown("## Exportar Artículos")
    
    try:
        # Obtener artículos guardados
        all_articles = db_manager.get_recent_articles(days=365, limit=1000)
        saved_articles = [a for a in all_articles if hasattr(a, 'saved') and a.saved]
        
        if not saved_articles:
            st.info("No hay artículos guardados para exportar.")
            return
        
        st.markdown(f"### Seleccionar Artículos para Exportar ({len(saved_articles)} disponibles)")
        
        # Filtros para selección
    col1, col2 = st.columns(2)
        with col1:
            source_filter = st.selectbox("Filtrar por fuente:", ["Todas"] + list(set([a.source for a in saved_articles])), key="export_source")
        with col2:
            date_filter = st.selectbox("Filtrar por fecha:", ["Todos", "Última semana", "Último mes", "Último año"], key="export_date")
        
        # Aplicar filtros
        filtered_articles = saved_articles
        if source_filter != "Todas":
            filtered_articles = [a for a in filtered_articles if a.source == source_filter]
        
        if date_filter != "Todos":
            from datetime import timedelta
            if date_filter == "Última semana":
                cutoff_date = datetime.now() - timedelta(days=7)
            elif date_filter == "Último mes":
                cutoff_date = datetime.now() - timedelta(days=30)
            elif date_filter == "Último año":
                cutoff_date = datetime.now() - timedelta(days=365)
            
            filtered_articles = [a for a in filtered_articles if a.publication_date and a.publication_date >= cutoff_date]
        
        st.markdown(f"**Artículos filtrados: {len(filtered_articles)}**")
        
        # Selección múltiple de artículos
        article_titles = [f"{a.title[:60]}... ({a.source})" for a in filtered_articles]
        selected_indices = st.multiselect(
            "Selecciona artículos para exportar:",
            options=range(len(filtered_articles)),
            format_func=lambda x: article_titles[x],
            key="export_selection"
        )
        
        if selected_indices:
            selected_articles = [filtered_articles[i] for i in selected_indices]
            
            # Opciones de exportación
            st.markdown("### Opciones de Exportación")
            export_format = st.selectbox("Formato:", ["Markdown", "JSON", "CSV"])
            include_abstract = st.checkbox("Incluir abstract", value=True)
            include_metadata = st.checkbox("Incluir metadatos", value=True)
            
            if st.button("📄 Exportar Artículos Seleccionados", use_container_width=True):
                try:
                    if export_format == "Markdown":
                        markdown_content = generate_markdown_export(selected_articles, include_abstract, include_metadata)
                        st.download_button(
                            label="📥 Descargar Markdown",
                            data=markdown_content,
                            file_name=f"articulos_exportados_{datetime.now().strftime('%Y%m%d')}.md",
                            mime="text/markdown"
                        )
                        st.text_area("Vista previa:", markdown_content[:1000] + "...", height=200)
                    
                    elif export_format == "JSON":
                        import json
                        json_data = [article_to_dict(a, include_abstract, include_metadata) for a in selected_articles]
                        st.download_button(
                            label="📥 Descargar JSON",
                            data=json.dumps(json_data, indent=2, ensure_ascii=False),
                            file_name=f"articulos_exportados_{datetime.now().strftime('%Y%m%d')}.json",
                            mime="application/json"
                        )
                    
                    elif export_format == "CSV":
                        import pandas as pd
                        csv_data = [article_to_dict(a, include_abstract, include_metadata) for a in selected_articles]
                        df = pd.DataFrame(csv_data)
                        csv_content = df.to_csv(index=False, encoding='utf-8')
                        st.download_button(
                            label="📥 Descargar CSV",
                            data=csv_content,
                            file_name=f"articulos_exportados_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    
                    st.success(f"✅ Exportación preparada para {len(selected_articles)} artículos")
                
                except Exception as e:
                    st.error(f"Error en exportación: {e}")
        else:
            st.info("Selecciona al menos un artículo para exportar.")
    
    except Exception as e:
        st.error(f"Error cargando exportación: {e}")

def show_search_result_card(article, index):
    """Muestra una tarjeta de resultado de búsqueda expandible."""
    date_str = "Fecha no disponible"
    if hasattr(article, 'publication_date') and article.publication_date:
        date_str = article.publication_date.strftime('%d %B %Y')
    
    # Verificar si el artículo ya está guardado
    is_saved = hasattr(article, 'saved') and article.saved
    
    # Crear la tarjeta expandible
    with st.expander(f"📄 {article.title[:60]}...", expanded=False):
        # Título completo
        st.markdown(f"**{article.title}**")
        
        # Información básica
        st.markdown(f"**Fuente:** {article.source} | **Fecha:** {date_str}")
        if article.authors:
            st.markdown(f"**Autores:** {', '.join(article.authors[:3])}{'...' if len(article.authors) > 3 else ''}")
        
        # Abstract traducido
        if article.abstract:
            try:
                translated_abstract = translate_to_spanish(article.abstract)
                st.markdown("**Abstract:**")
                st.write(translated_abstract)
            except Exception as e:
                st.markdown("**Abstract (Original):**")
                st.write(article.abstract)
                st.error(f"Error en traducción: {e}")
        
        # Botón de guardar/desguardar
        col1, col2 = st.columns([1, 3])
    with col1:
            if is_saved:
                if st.button("💾 Quitar de Guardados", key=f"unsave_{index}"):
                    try:
                        success = db_manager.unmark_article_as_saved(article.id)
                        if success:
                            st.success("✅ Artículo removido de guardados")
                            article.saved = False
                            article.saved_at = None
                            st.rerun()
                        else:
                            st.error("❌ Error al remover el artículo")
                    except Exception as e:
                        st.error(f"Error removiendo artículo: {e}")
            else:
                if st.button("💾 Guardar Artículo", key=f"save_{index}"):
                    try:
                        # Verificar que el artículo tenga un ID válido
                        if not article.id or article.id.strip() == "":
                            st.error("❌ Error: El artículo no tiene un ID válido")
                            return
                        
                        # Primero guardar el artículo en la base de datos si no existe
                        existing_article = db_manager.get_article(article.id)
                        if not existing_article:
                            save_success = db_manager.save_article(article)
                            if not save_success:
                                st.error("❌ Error al guardar el artículo en la base de datos")
                                return
                        
                        # Luego marcarlo como guardado
                        success = db_manager.mark_article_as_saved(article.id)
                        if success:
                            st.success("✅ Artículo guardado exitosamente")
                            article.saved = True
                            article.saved_at = datetime.now()
                            st.rerun()
                        else:
                            st.error("❌ Error al marcar el artículo como guardado")
                    except Exception as e:
                        st.error(f"Error guardando artículo: {e}")
    
    with col2:
            if article.url:
                st.markdown(f"[🔗 Ver artículo original]({article.url})")

def generate_markdown_export(articles, include_abstract=True, include_metadata=True):
    """Genera contenido markdown para exportación."""
    content = [f"# Artículos Exportados - {datetime.now().strftime('%d/%m/%Y')}", ""]
    
    for i, article in enumerate(articles, 1):
        content.append(f"## {i}. {article.title}")
        content.append("")
        
        if include_metadata:
            content.append(f"**Fuente:** {article.source}")
            if article.publication_date:
                content.append(f"**Fecha:** {article.publication_date.strftime('%d/%m/%Y')}")
            if article.authors:
                content.append(f"**Autores:** {', '.join(article.authors)}")
            if article.doi:
                content.append(f"**DOI:** {article.doi}")
            if article.url:
                content.append(f"**URL:** {article.url}")
            content.append("")
        
        if include_abstract and article.abstract:
            content.append("**Abstract:**")
            content.append(article.abstract)
            content.append("")
        
        content.append("---")
        content.append("")
    
    return "\n".join(content)

def article_to_dict(article, include_abstract=True, include_metadata=True):
    """Convierte un artículo a diccionario para exportación."""
    data = {
        "title": article.title,
        "source": article.source
    }
    
    if include_metadata:
        data.update({
            "publication_date": article.publication_date.isoformat() if article.publication_date else None,
            "authors": article.authors,
            "doi": article.doi,
            "url": article.url,
            "topics": article.topics
        })
    
    if include_abstract:
        data["abstract"] = article.abstract
    
    return data

def show_article_card(article, show_full=False):
    """Muestra una tarjeta de artículo con estilo minimalista tipo Medium."""
    date_str = "Fecha no disponible"
    if hasattr(article, 'publication_date') and article.publication_date:
        date_str = article.publication_date.strftime('%d %B %Y')
    
    # Crear la tarjeta expandible
    with st.expander(f"📄 {article.title[:60]}...", expanded=False):
        # Título completo
        st.markdown(f"**{article.title}**")
        
        # Información básica
        st.markdown(f"**Fuente:** {article.source} | **Fecha:** {date_str}")
        if article.authors:
            st.markdown(f"**Autores:** {', '.join(article.authors[:3])}{'...' if len(article.authors) > 3 else ''}")
        
        # Abstract traducido completo
        if article.abstract:
            try:
                translated_abstract = translate_to_spanish(article.abstract)
                st.markdown("**Abstract:**")
                st.write(translated_abstract)
            except Exception as e:
                st.markdown("**Abstract (Original):**")
                st.write(article.abstract)
                st.error(f"Error en traducción: {e}")
        
        # Información adicional
        if article.doi:
            st.markdown(f"**DOI:** {article.doi}")
        
        if article.url:
            st.markdown(f"**URL:** [{article.url}]({article.url})")
        
        if article.topics:
            st.markdown(f"**Temas:** {', '.join(article.topics)}")
        
        # Resumen procesado si existe
        if article.summary:
            st.markdown("---")
            st.markdown("**Resumen procesado:**")
            st.markdown(article.summary)
        
        # Contenido del post si existe
        if article.post_content:
            st.markdown("---")
            st.markdown("**Contenido del post:**")
            st.markdown(article.post_content)
        
        # Botón para eliminar de guardados (solo si está guardado)
        if hasattr(article, 'saved') and article.saved:
            st.markdown("---")
            if st.button("🗑️ Eliminar de Guardados", key=f"delete_{article.id}", use_container_width=True):
                try:
                    success = db_manager.unmark_article_as_saved(article.id)
                    if success:
                        st.success("✅ Artículo eliminado de guardados")
                        article.saved = False
                        article.saved_at = None
                        st.rerun()
                    else:
                        st.error("❌ Error al eliminar el artículo")
                except Exception as e:
                    st.error(f"Error eliminando artículo: {e}")

def show_analytics():
    """Muestra la página de estadísticas."""
    st.markdown('<h1 class="page-title">Estadísticas</h1>', unsafe_allow_html=True)
    
    try:
        # Obtener datos para analytics
        articles = db_manager.get_recent_articles(days=30, limit=100)
        
        if articles:
            # Gráfico de artículos por fuente
            st.markdown('<h3 class="section-title">Artículos por Fuente</h3>', unsafe_allow_html=True)
            
            source_counts = {}
            for article in articles:
                source_counts[article.source] = source_counts.get(article.source, 0) + 1
            
            if source_counts:
                fig_sources = px.pie(
                    values=list(source_counts.values()),
                    names=list(source_counts.keys()),
                    title="Distribución por Fuente"
                )
                fig_sources.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_sources, use_container_width=True)
            
            # Gráfico temporal
            st.markdown('<h3 class="section-title">Tendencia Temporal</h3>', unsafe_allow_html=True)
            
            # Agrupar por fecha
            date_counts = {}
            for article in articles:
                if hasattr(article, 'publication_date') and article.publication_date:
                    date_str = article.publication_date.strftime('%Y-%m-%d')
                    date_counts[date_str] = date_counts.get(date_str, 0) + 1
            
            if date_counts:
                dates = list(date_counts.keys())
                counts = list(date_counts.values())
                
                fig_timeline = px.line(
                    x=dates, y=counts,
                    title="Artículos por Día",
                    labels={'x': 'Fecha', 'y': 'Número de Artículos'}
                )
                st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Estadísticas de procesamiento
            st.markdown('<h3 class="section-title">Estado de Procesamiento</h3>', unsafe_allow_html=True)
            
            processed_count = len([a for a in articles if a.summary])
            unprocessed_count = len(articles) - processed_count
            
            fig_processing = px.bar(
                x=['Procesados', 'Sin Procesar'],
                y=[processed_count, unprocessed_count],
                title="Estado de Procesamiento",
                color=['Procesados', 'Sin Procesar'],
                color_discrete_map={'Procesados': '#10b981', 'Sin Procesar': '#f59e0b'}
            )
            st.plotly_chart(fig_processing, use_container_width=True)
        
        else:
            st.info("No hay datos suficientes para mostrar analytics.")
    
    except Exception as e:
        st.error(f"Error cargando analytics: {e}")

def handle_article_save(article_id):
    """Maneja el guardado de un artículo desde el panel lateral."""
    try:
        success = db_manager.mark_article_as_saved(article_id)
        if success:
            st.success("✅ Artículo guardado exitosamente")
        else:
            st.error("❌ Error al guardar el artículo")
        return success
    except Exception as e:
        st.error(f"Error guardando artículo: {e}")
        return False

if __name__ == "__main__":
    main()

