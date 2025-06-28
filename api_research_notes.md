## Notas de Investigación de APIs

### The Lens
- Documentación de API disponible: `https://docs.api.lens.org/`
- Menciona API Scholarly, Patent API, PatSeq Bulk Downloads.
- Requiere solicitud de acceso y tokens.
- Utiliza GraphQL, lo que puede ser beneficioso para consultas flexibles.

### BioOne
- No se encontró una API pública clara para la búsqueda de contenido.
- Los resultados de búsqueda mencionan 'COUNTER API credentials' para instituciones, lo que sugiere un acceso limitado o para fines de uso de estadísticas.
- Posiblemente se necesite web scraping si no hay una API pública para el contenido.

### ResearchGate
- No parece tener una API pública para la búsqueda y extracción de contenido de artículos.
- Los resultados sugieren que no hay una API oficial para extraer datos de publicaciones o autores.
- Se mencionan soluciones de web scraping (SerpApi), pero no es lo ideal.
- Se menciona Crossref API como alternativa para buscar publicaciones.

### IEEE Xplore
- Portal de API disponible: `https://ieeexplore.ieee.org/Xplorehelp/administrators-and-librarians/api-portal`
- Proporciona acceso a metadatos de más de 6 millones de documentos.
- Requiere registro de cuenta de usuario y una clave API.

### arXiv API
- Acceso a la API: `https://info.arxiv.org/help/api/index.html`
- Permite acceso programático al contenido y metadatos de e-prints.
- No requiere clave API.
- Soporta búsqueda y recuperación de resúmenes y documentos.

### Europe PMC
- RESTful Web Service disponible: `https://europepmc.org/RestfulWebService`
- Acceso a publicaciones e información relacionada en la base de datos Europe PMC.
- También tiene API de anotaciones y API de subvenciones.

### DOAJ API
- Documentación de API disponible: `https://doaj.org/docs/faq/` y `https://doaj.org/api/v1/docs`
- Permite descargar metadatos de revistas y artículos.
- API pública para búsqueda.

### bioRxiv/medRxiv REST API
- API disponible: `https://api.biorxiv.org/` y `https://api.medrxiv.org/`
- Permite acceder a preprints y metadatos.
- La documentación de ayuda está en `https://api.biorxiv.org/pubs/help`.

### Crossref Metadata API
- REST API disponible: `https://www.crossref.org/documentation/retrieve-metadata/rest-api/`
- Permite buscar, facetar, filtrar o muestrear metadatos de miles de miembros.
- Los resultados se devuelven en JSON.
- No requiere clave API para la mayoría de las búsquedas públicas.



## Evaluación de APIs y Arquitectura Propuesta

### APIs para Integración Directa (Prioritarias)

Las siguientes APIs son candidatas principales para la integración directa debido a su disponibilidad, documentación y aparente facilidad de uso para la extracción de metadatos y, en algunos casos, contenido completo o resúmenes:

1.  **The Lens API:** Su uso de GraphQL es una ventaja para consultas flexibles. Necesita solicitud de acceso y tokens, lo que implica un paso de configuración inicial.
2.  **IEEE Xplore API:** Permite acceso a metadatos de una gran cantidad de documentos. Requiere registro y una clave API.
3.  **arXiv API:** Acceso programático a e-prints y metadatos sin necesidad de clave API, lo que la hace muy accesible.
4.  **Europe PMC RESTful Web Service:** Ofrece acceso a publicaciones e información relacionada, incluyendo la posibilidad de acceder a textos completos de acceso abierto. Muy prometedora para el contenido.
5.  **DOAJ API:** Permite la descarga de metadatos de revistas y artículos de acceso abierto. Útil para identificar fuentes.
6.  **bioRxiv/medRxiv REST API:** Acceso directo a preprints y sus metadatos, ideal para investigación reciente en biología y medicina.
7.  **Crossref Metadata API:** Excelente para buscar metadatos de publicaciones y, en algunos casos, enlaces a textos completos. No requiere clave API para búsquedas públicas, lo que la hace fundamental.

### APIs con Desafíos o Integración Indirecta

-   **BioOne:** No se encontró una API pública clara para la extracción de contenido. Es probable que su contenido deba ser accedido a través de otras APIs (como Crossref o Europe PMC si indexan su contenido) o considerar si es indispensable para el MVP.
-   **ResearchGate:** No ofrece una API pública para la extracción de contenido. Se desaconseja el web scraping por su fragilidad y posibles problemas legales. Se buscará si su contenido es indexado por otras APIs mencionadas.

### Arquitectura Propuesta (Alto Nivel)

La aplicación se estructurará en varios componentes clave para asegurar modularidad y escalabilidad:

1.  **Módulo de Recolección de Datos (Data Harvester):**
    *   Responsable de interactuar con las diversas APIs (The Lens, IEEE Xplore, arXiv, Europe PMC, DOAJ, bioRxiv/medRxiv, Crossref).
    *   Implementará la lógica para construir consultas basadas en los temas de interés del usuario.
    *   Manejará la paginación, límites de tasa y errores de las APIs.
    *   Almacenará los metadatos y, si es posible, el texto completo de los artículos en una base de datos temporal o archivos intermedios.

2.  **Módulo de Procesamiento de Artículos (Article Processor):**
    *   **Extracción de Texto:** Si la API no proporciona el texto completo, se intentará acceder a los PDFs o HTMLs de acceso abierto para extraer el contenido relevante.
    *   **Resumidor (Summarizer):** Utilizará modelos de procesamiento de lenguaje natural (NLP) para generar resúmenes concisos y sin tecnicismos de los artículos identificados.
    *   **Generador de Posts Divulgativos (Post Generator):** Creará posts más desarrollados, en un tono casual, resaltando hallazgos clave y procedimientos, similar al estilo de Medium.

3.  **Módulo de Knowledge Graph (KG Builder):**
    *   Analizará los artículos y sus resúmenes/posts para identificar entidades (autores, instituciones, conceptos clave, genes, proteínas, etc.) y relaciones entre ellas.
    *   Construirá un grafo de conocimiento que represente estas conexiones.
    *   Se encargará de la visualización del grafo (posiblemente usando bibliotecas JS como D3.js o NetworkX en Python con una interfaz web).

4.  **Base de Datos/Almacenamiento:**
    *   Se utilizará una base de datos ligera (e.g., SQLite) para almacenar metadatos de artículos, resúmenes, posts generados y el grafo de conocimiento.
    *   Los posts finales se guardarán en formato Markdown (`.md`) en el sistema de archivos.

5.  **Interfaz de Usuario (UI - Streamlit):**
    *   Permitirá al usuario configurar temas de interés, ver los artículos recolectados, leer resúmenes y posts, y visualizar el Knowledge Graph.
    *   Ofrecerá la opción de guardar posts en `.md`.

6.  **Módulo de Programación de Tareas (Scheduler):**
    *   Utilizará una biblioteca de Python (e.g., `APScheduler` o `Celery` para tareas más robustas) para automatizar la ejecución diaria del proceso de recolección y procesamiento de artículos.

### Desafíos Técnicos y Soluciones Potenciales

-   **Acceso a Texto Completo:** Muchas APIs solo proporcionan metadatos. Se necesitará lógica para descargar y parsear PDFs o HTMLs de acceso abierto, lo cual puede ser complejo y propenso a errores debido a la variabilidad de formatos.
    *   **Solución:** Priorizar APIs que ofrezcan texto completo o enlaces directos a OA. Para PDFs, usar bibliotecas como `PyPDF2` o `pdfminer.six`. Para HTML, `BeautifulSoup`.
-   **Procesamiento de Lenguaje Natural (NLP):** La generación de resúmenes y posts de alta calidad requiere modelos de NLP avanzados.
    *   **Solución:** Utilizar bibliotecas como `Hugging Face Transformers` con modelos pre-entrenados (e.g., T5, BART para resúmenes) y ajustarlos si es necesario. Para la extracción de entidades, `spaCy` o `NLTK`.
-   **Construcción y Visualización del Knowledge Graph:** Identificar relaciones significativas y visualizarlas de manera interactiva puede ser un desafío.
    *   **Solución:** Usar `NetworkX` para la construcción del grafo en Python. Para la visualización en Streamlit, se puede integrar con componentes de Streamlit que permitan gráficos interactivos (e.g., `streamlit-agraph`, o generar JSON para una visualización basada en JS).
-   **Gestión de APIs:** Manejar diferentes esquemas de API, límites de tasa y autenticación.
    *   **Solución:** Crear clases o funciones adaptadoras para cada API, encapsulando su lógica específica. Implementar reintentos y esperas exponenciales para los límites de tasa.
-   **Automatización y Despliegue:** Asegurar que la tarea diaria se ejecute de manera confiable y que la aplicación sea desplegable en plataformas como Streamlit Cloud o un servidor.
    *   **Solución:** Usar `APScheduler` para la programación. Para el despliegue, seguir las mejores prácticas de Streamlit y Dockerizar la aplicación si es necesario para un despliegue más robusto.

### Tecnologías Principales

-   **Lenguaje de Programación:** Python
-   **Framework Web:** Streamlit
-   **NLP:** Hugging Face Transformers, spaCy, NLTK
-   **Procesamiento de PDF/HTML:** PyPDF2, pdfminer.six, BeautifulSoup
-   **Knowledge Graph:** NetworkX
-   **Base de Datos:** SQLite (para datos locales y persistencia)
-   **Programación de Tareas:** APScheduler
-   **Control de Versiones:** Git/GitHub

Esta planificación sienta las bases para la implementación de la aplicación, abordando los requisitos del usuario y los desafíos técnicos anticipados. El siguiente paso será establecer la estructura del proyecto y comenzar con la implementación de los conectores de API.

