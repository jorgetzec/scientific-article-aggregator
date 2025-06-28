"""
Scientific Article Aggregator - Aplicación Streamlit
Interfaz web minimalista y moderna al estilo de Medium
"""

import streamlit as st
import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import networkx as nx

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.database import db_manager
from src.data_harvester.harvester_manager import harvester_manager
from src.article_processor.processor_manager import processor_manager
from src.knowledge_graph.graph_builder import graph_builder

# Configuración de la página
st.set_page_config(
    page_title="Scientific Article Aggregator",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para estilo Medium
st.markdown("""
<style>
    /* Estilo general */
    .main {
        padding-top: 2rem;
    }
    
    /* Título principal */
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        color: #1a1a1a;
        text-align: center;
        margin-bottom: 0.5rem;
        font-family: 'Georgia', serif;
    }
    
    .main-subtitle {
        font-size: 1.2rem;
        color: #6b7280;
        text-align: center;
        margin-bottom: 3rem;
        font-style: italic;
    }
    
    /* Cards estilo Medium */
    .article-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #3b82f6;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .article-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    
    .article-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 0.5rem;
        line-height: 1.4;
    }
    
    .article-meta {
        font-size: 0.9rem;
        color: #6b7280;
        margin-bottom: 1rem;
    }
    
    .article-summary {
        font-size: 1rem;
        color: #374151;
        line-height: 1.6;
        margin-bottom: 1rem;
    }
    
    /* Botones estilo Medium */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }
    
    /* Sidebar */
    .sidebar .sidebar-content {
        background: #f8fafc;
    }
    
    /* Métricas */
    .metric-card {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* Gráficos */
    .chart-container {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    
    /* Texto de carga */
    .loading-text {
        text-align: center;
        color: #6b7280;
        font-style: italic;
        padding: 2rem;
    }
    
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def main():
    """Función principal de la aplicación."""
    
    # Título principal
    st.markdown('<h1 class="main-title">🔬 Scientific Article Aggregator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="main-subtitle">Tu fuente diaria de descubrimientos científicos, simplificados y accesibles</p>', unsafe_allow_html=True)
    
    # Sidebar para navegación
    with st.sidebar:
        st.markdown("### 📋 Navegación")
        page = st.selectbox(
            "Selecciona una página:",
            ["🏠 Dashboard", "📚 Artículos", "🔍 Explorar", "⚙️ Configuración", "📊 Analytics"]
        )
        
        st.markdown("---")
        
        # Estadísticas rápidas
        st.markdown("### 📈 Estadísticas")
        try:
            total_articles = len(db_manager.get_recent_articles(days=365, limit=1000))
            recent_articles = len(db_manager.get_recent_articles(days=7, limit=100))
            
            st.metric("Total Artículos", total_articles)
            st.metric("Esta Semana", recent_articles)
        except Exception as e:
            st.error(f"Error cargando estadísticas: {e}")
    
    # Contenido principal basado en la página seleccionada
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "📚 Artículos":
        show_articles()
    elif page == "🔍 Explorar":
        show_explorer()
    elif page == "⚙️ Configuración":
        show_settings()
    elif page == "📊 Analytics":
        show_analytics()

def show_dashboard():
    """Muestra el dashboard principal."""
    st.markdown("## 🏠 Dashboard")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        # Obtener estadísticas
        total_articles = len(db_manager.get_recent_articles(days=365, limit=1000))
        recent_articles = len(db_manager.get_recent_articles(days=7, limit=100))
        processed_articles = len([a for a in db_manager.get_recent_articles(days=30, limit=100) if a.summary])
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>📚</h3>
                <h2>{}</h2>
                <p>Total Artículos</p>
            </div>
            """.format(total_articles), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3>🆕</h3>
                <h2>{}</h2>
                <p>Esta Semana</p>
            </div>
            """.format(recent_articles), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h3>✅</h3>
                <h2>{}</h2>
                <p>Procesados</p>
            </div>
            """.format(processed_articles), unsafe_allow_html=True)
        
        with col4:
            processing_rate = (processed_articles / max(total_articles, 1)) * 100
            st.markdown("""
            <div class="metric-card">
                <h3>📊</h3>
                <h2>{:.1f}%</h2>
                <p>Tasa Procesamiento</p>
            </div>
            """.format(processing_rate), unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Artículos recientes
        st.markdown("### 📰 Artículos Recientes")
        
        recent_articles_data = db_manager.get_recent_articles(days=7, limit=5)
        
        if recent_articles_data:
            for article in recent_articles_data:
                show_article_card(article)
        else:
            st.info("No hay artículos recientes. Ejecuta la recolección para obtener nuevos artículos.")
        
        # Botones de acción
        st.markdown("### 🚀 Acciones Rápidas")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Recolectar Artículos", use_container_width=True):
                with st.spinner("Recolectando artículos..."):
                    try:
                        topics = ["bioinformatics", "computational biology", "machine learning"]
                        stats = harvester_manager.harvest_all_sources(topics=topics, max_articles_per_source=5)
                        total_articles = sum(len(articles) for articles in stats.values())
                        st.success(f"✅ Recolectados {total_articles} artículos")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error en recolección: {e}")
        
        with col2:
            if st.button("📝 Procesar Artículos", use_container_width=True):
                with st.spinner("Procesando artículos..."):
                    try:
                        stats = processor_manager.process_articles(max_articles=5)
                        st.success(f"✅ Procesados {stats.get('processed', 0)} artículos")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error en procesamiento: {e}")
        
        with col3:
            if st.button("🕸️ Actualizar Grafo", use_container_width=True):
                with st.spinner("Actualizando knowledge graph..."):
                    try:
                        articles = db_manager.get_recent_articles(days=30, limit=50)
                        graph_builder.build_graph(articles)
                        st.success("✅ Knowledge graph actualizado")
                    except Exception as e:
                        st.error(f"Error actualizando grafo: {e}")
        
    except Exception as e:
        st.error(f"Error cargando dashboard: {e}")

def show_articles():
    """Muestra la página de artículos."""
    st.markdown("## 📚 Artículos")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        days_filter = st.selectbox("Período", [7, 14, 30, 90, 365], index=2)
    
    with col2:
        source_filter = st.selectbox("Fuente", ["Todas", "arxiv", "europepmc", "crossref", "biorxiv"])
    
    with col3:
        limit_filter = st.selectbox("Límite", [10, 20, 50, 100], index=1)
    
    # Obtener artículos
    try:
        articles = db_manager.get_recent_articles(days=days_filter, limit=limit_filter)
        
        if source_filter != "Todas":
            articles = [a for a in articles if a.source == source_filter]
        
        st.markdown(f"### Mostrando {len(articles)} artículos")
        
        if articles:
            for article in articles:
                show_article_card(article, show_full=True)
        else:
            st.info("No se encontraron artículos con los filtros seleccionados.")
    
    except Exception as e:
        st.error(f"Error cargando artículos: {e}")

def show_explorer():
    """Muestra la página de exploración con knowledge graph."""
    st.markdown("## 🔍 Explorar Knowledge Graph")
    
    try:
        # Construir grafo si no existe
        articles = db_manager.get_recent_articles(days=30, limit=50)
        if articles:
            graph = graph_builder.build_graph(articles)
            
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
                
                # Visualización simple del grafo
                st.markdown("### 🕸️ Visualización del Grafo")
                
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
                        title="Knowledge Graph de Artículos Científicos",
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        annotations=[
                            dict(
                                text="Cada nodo representa un artículo. Las conexiones muestran relaciones por temas, autores o fuente.",
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
                    st.markdown("### 🌟 Artículos Más Conectados")
                    
                    for i, article_info in enumerate(stats['top_connected_articles'][:3], 1):
                        st.markdown(f"""
                        **{i}. {article_info['title']}**  
                        *{article_info['connections']} conexiones | Fuente: {article_info['source']}*
                        """)
            else:
                st.info("No hay suficientes artículos para generar el knowledge graph.")
        else:
            st.info("No hay artículos disponibles. Ejecuta la recolección primero.")
    
    except Exception as e:
        st.error(f"Error en exploración: {e}")

def show_settings():
    """Muestra la página de configuración."""
    st.markdown("## ⚙️ Configuración")
    
    # Configuración de temas
    st.markdown("### 🏷️ Temas de Interés")
    
    current_topics = st.text_area(
        "Temas para recolección (uno por línea):",
        value="bioinformatics\ncomputational biology\nmachine learning\ndata analysis\nplant microbe interaction\nscientific education",
        height=150
    )
    
    # Configuración de fuentes
    st.markdown("### 📡 Fuentes de Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        arxiv_enabled = st.checkbox("arXiv", value=True)
        europepmc_enabled = st.checkbox("Europe PMC", value=True)
        crossref_enabled = st.checkbox("Crossref", value=True)
    
    with col2:
        biorxiv_enabled = st.checkbox("bioRxiv/medRxiv", value=True)
        max_articles = st.number_input("Máx. artículos por fuente", min_value=1, max_value=50, value=10)
    
    # Configuración de procesamiento
    st.markdown("### 📝 Procesamiento")
    
    auto_process = st.checkbox("Procesamiento automático", value=True)
    max_summary_length = st.slider("Longitud máxima del resumen (palabras)", 100, 500, 300)
    
    if st.button("💾 Guardar Configuración", use_container_width=True):
        st.success("✅ Configuración guardada")

def show_analytics():
    """Muestra la página de analytics."""
    st.markdown("## 📊 Analytics")
    
    try:
        # Obtener datos para analytics
        articles = db_manager.get_recent_articles(days=30, limit=100)
        
        if articles:
            # Gráfico de artículos por fuente
            st.markdown("### 📈 Artículos por Fuente")
            
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
            st.markdown("### 📅 Tendencia Temporal")
            
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
            st.markdown("### 🔄 Estado de Procesamiento")
            
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

def show_article_card(article, show_full=False):
    """Muestra una tarjeta de artículo."""
    # Determinar el emoji basado en la fuente
    source_emojis = {
        'arxiv': '📄',
        'europepmc': '🏥',
        'crossref': '🔗',
        'biorxiv': '🧬',
        'medrxiv': '💊'
    }
    
    emoji = source_emojis.get(article.source, '📚')
    
    # Formatear fecha
    date_str = "Fecha no disponible"
    if hasattr(article, 'publication_date') and article.publication_date:
        date_str = article.publication_date.strftime('%d %B %Y')
    
    # Crear la tarjeta
    card_html = f"""
    <div class="article-card">
        <div class="article-title">{emoji} {article.title}</div>
        <div class="article-meta">
            <strong>Fuente:</strong> {article.source} | 
            <strong>Fecha:</strong> {date_str}
            {f' | <strong>Autores:</strong> {", ".join(article.authors[:2])}{"..." if len(article.authors) > 2 else ""}' if article.authors else ''}
        </div>
    """
    
    if article.summary and show_full:
        card_html += f'<div class="article-summary">{article.summary}</div>'
    elif article.abstract:
        abstract_preview = article.abstract[:200] + "..." if len(article.abstract) > 200 else article.abstract
        card_html += f'<div class="article-summary">{abstract_preview}</div>'
    
    card_html += "</div>"
    
    st.markdown(card_html, unsafe_allow_html=True)
    
    # Botón para ver detalles
    if show_full and st.button(f"Ver Post Completo", key=f"view_{article.id}"):
        if article.post_content:
            st.markdown("---")
            st.markdown(article.post_content)
            st.markdown("---")
        else:
            st.info("Este artículo aún no ha sido procesado para generar un post.")

if __name__ == "__main__":
    main()

