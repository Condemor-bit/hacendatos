import streamlit as st
from google.cloud import bigquery
import pandas as pd
import plotly.express as px
from google.cloud import storage

#import seaborn as sns
#import matplotlib.pyplot as plt
from PIL import Image
import io

import os
#os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "GC-clave.json"

st.set_page_config(
    page_title="Hacendatos",
    page_icon="🍊",
    layout="wide",
    initial_sidebar_state="expanded"  # puede ser "expanded" o "collapsed"
)



page = st.sidebar.radio(
    "Selecciona análisis",
    ["Wordcloud", "Percepción Mercadona", "Categorías"]
)


if page == "Wordcloud":
    storage_client = storage.Client()
    bucket_name = ""
    bucket = storage_client.bucket(bucket_name)

    # Nombre del archivo 
    file_name = "Gold/graph/wordcloud.png"  
    # Obtener blob y descargar bytes
    blob = bucket.blob(file_name)
    image_bytes = blob.download_as_bytes()
    # Convertir bytes en imagen con PIL
    image = Image.open(io.BytesIO(image_bytes))

    # Mostrar en Streamlit
    st.image(image, caption="Hacendatos WorldCloud", use_container_width=True)

elif page == "Percepción Mercadona":
    #st.header("👁️ Imagen de Marca")
    # Configuración cliente BigQuery
    client = bigquery.Client()

    # Obtener fechas mín y máx desde BigQuery
    query_fechas = """
    SELECT
        MIN(DATE(fecha_captura)) as min_fecha,
        MAX(DATE(fecha_captura)) as max_fecha
    FROM ` .hacendatos.embeddings`
    """
    fechas = client.query(query_fechas).to_dataframe()
    min_fecha = fechas["min_fecha"].iloc[0]
    max_fecha = fechas["max_fecha"].iloc[0]

    # --- Sidebar con filtros ---
    st.sidebar.header("Filtros")

    # Slider de rango de fechas
    fecha_inicio, fecha_fin = st.sidebar.slider(
        "Selecciona rango de fechas",
        min_value=min_fecha,
        max_value=max_fecha,
        value=(min_fecha, max_fecha),   
        format="YYYY-MM-DD"
    )


    # Selector de sentimiento con opción "All"
    sentimiento = st.sidebar.selectbox(
        "Selecciona sentimiento",
        ["All", "positivo", "neutral", "negativo"]  # añade "All"
    )

    # --- Construcción dinámica del WHERE ---
    where_sentimiento = "" if sentimiento == "All" else f"AND sentimiento = '{sentimiento}'"


    # Obtener clusters distintos de la tabla
    query_clusters = """
    SELECT DISTINCT clusters_hdbscan
    FROM ` .hacendatos.embeddings`
    ORDER BY clusters_hdbscan
    """
    clusters = client.query(query_clusters).to_dataframe()["clusters_hdbscan"].tolist()

    cluster_sel = st.sidebar.multiselect(
        "Selecciona Tópico",
        ["All"] + clusters
    )

    if "All" in cluster_sel or len(cluster_sel) == 0:
        where_cluster = ""
    else:
        where_cluster = "AND clusters_hdbscan IN ({})".format(
            ",".join([f"'{c}'" for c in cluster_sel])
        )

    # --- Query dinámica ---
    query = f"""
    SELECT
        DATE(fecha_captura) AS fecha,
        tweets,
        sentimiento,
        UMAP_1,
        UMAP_2,
        UMAP_3,
        clusters_hdbscan as Topic
    FROM ` .hacendatos.embeddings`
    WHERE DATE(fecha_captura) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
    {where_sentimiento}
    {where_cluster}
    """
    # Ejecutar query
    df = client.query(query).to_dataframe()


    # --- Visualización ---
    #st.title("Dashboard de Sentimientos")

    # Crear una grilla 2x2
    col1, col2 = st.columns(2)  

    with col1:
        st.subheader(f"👁️ Tweets Imagen de Marca  {''.join(map(str, cluster_sel))}")
        if df.empty:
            st.warning("No hay datos para los filtros seleccionados.")
        else:
            fig = px.scatter_3d(
                df,
                x="UMAP_1",
                y="UMAP_2",
                z="UMAP_3",
                color="Topic",
                hover_data=["tweets", "sentimiento"],
                height=600,
                width=600,
                color_discrete_map={"Desconectado": "gray"}
            )

            # Actualizando trazas para los puntos
            fig.update_traces(marker=dict(size=2, opacity=0.5))

            # Apagando cluster Desconectado desde el inicio
            for trace in fig.data:
                if trace.name == "Desconectado":
                    trace.marker.color = "gray"
                    trace.marker.opacity = 0.05
                    trace.visible = "legendonly"

            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader(f"Sentimiento Imagen de Marca  {''.join(map(str, cluster_sel))} 💭")
        if df.empty:
            st.warning("No hay datos para los filtros seleccionados.")
        else:
            #preparamos los datos
            counts_sentimientos = df.sentimiento.value_counts() #contamos valores
            df_pie = counts_sentimientos.reset_index() #hacemos el df con los valores
            df_pie.columns = ["sentimiento", "proporcion"]
            color_discrete_map={
                    "positivo": "#66cc00", #"green",
                    "negativo":"#cc3333", # "red",
                    "neutral": "#cfcfcf",#"gray"
                }

            #grafic de tarta
            fig_pie = px.pie(
                df_pie,
                names="sentimiento",   
                values="proporcion",   
                color="sentimiento",
                color_discrete_map=color_discrete_map,
                height=600,
                width=600
                )
            fig_pie.update_traces(textposition='inside', textinfo='percent+value+label')
            fig_pie.update_layout(showlegend=False)

        

            st.plotly_chart(fig_pie, use_container_width=True)


    ### linea temporal
    if df.empty:
        st.warning("No hay datos para los filtros seleccionados.")
    else:
        df_line_sent = df.groupby(["fecha", "sentimiento"])["tweets"].count().reset_index()
        df_line_sent.columns = ["fecha", "sentimiento", "num_tweets"]
        df_line_sent["fecha"]  = pd.to_datetime(df_line_sent["fecha"])
        df_line_sent["fecha"] = df_line_sent["fecha"].dt.to_period('M').dt.to_timestamp()
        df_line_sent = df_line_sent.groupby(["fecha", "sentimiento"])["num_tweets"].count().reset_index()

        color_discrete_map={
                "positivo": "#66cc00", #"green",
                "negativo":"#cc3333", # "red",
                "neutral": "#cfcfcf",#"gray"
            }

        fig_line_sent = px.line(df_line_sent, x="fecha", y="num_tweets",
                    color='sentimiento',  color_discrete_map=color_discrete_map)
        fig_line_sent.update_layout(showlegend=False)
        st.plotly_chart(fig_line_sent, use_container_width=True)

elif page == "Categorías":
    client = bigquery.Client()

    # --- CONSULTA DE CATEGORÍAS ---
    query_categorias = """
    SELECT DISTINCT categoria
    FROM ` .hacendatos.categorias`
    ORDER BY categoria
    """
    categorias = client.query(query_categorias).to_dataframe()["categoria"].tolist()

    categoria_sel = st.sidebar.multiselect(
        "Selecciona Categoría",
        ["All"] + categorias
    )

    # Construir filtro para categorías
    if "All" in categoria_sel or len(categoria_sel) == 0:
        where_categoria = ""
    else:
        where_categoria = "AND categoria IN ({})".format(
            ",".join([f"'{c}'" for c in categoria_sel])
        )

    # --- CONSULTA DE SUBCATEGORÍAS FILTRADAS POR CATEGORÍA ---
    if "All" in categoria_sel or len(categoria_sel) == 0:
        query_subcategorias = """
        SELECT DISTINCT subcategoria
        FROM ` .hacendatos.categorias`
        ORDER BY subcategoria
        """
    else:
        query_subcategorias = """
        SELECT DISTINCT subcategoria
        FROM ` .hacendatos.categorias`
        WHERE categoria IN ({})
        ORDER BY subcategoria
        """.format(",".join([f"'{c}'" for c in categoria_sel]))

    subcategorias = client.query(query_subcategorias).to_dataframe()["subcategoria"].tolist()

    subcategoria_sel = st.sidebar.multiselect(
        "Selecciona Subcategoría",
        ["All"] + subcategorias
    )

    # Construir filtro para subcategorías
    if "All" in subcategoria_sel or len(subcategoria_sel) == 0:
        where_subcategoria = ""
    else:
        where_subcategoria = "AND subcategoria IN ({})".format(
            ",".join([f"'{c}'" for c in subcategoria_sel])
        )

     # Obtener fechas mín y máx desde BigQuery
    query_fechas = """
    SELECT
        MIN(DATE(fecha_captura)) as min_fecha,
        MAX(DATE(fecha_captura)) as max_fecha
    FROM ` .hacendatos.categorias`
    """

    fechas = client.query(query_fechas).to_dataframe()
    min_fecha = fechas["min_fecha"].iloc[0]
    max_fecha = fechas["max_fecha"].iloc[0]

    # --- Sidebar con filtros ---
    st.sidebar.header("Filtros")

    # Slider de rango de fechas
    fecha_inicio, fecha_fin = st.sidebar.slider(
        "Selecciona rango de fechas",
        min_value=min_fecha,
        max_value=max_fecha,
        value=(min_fecha, max_fecha),   
        format="YYYY-MM-DD"
    )


    # Selector de sentimiento con opción "All"
    sentimiento = st.sidebar.selectbox(
        "Selecciona sentimiento",
        ["All", "positivo", "neutral", "negativo"]  # añade "All"
    )

    # --- Construcción dinámica del WHERE ---
    where_sentimiento = "" if sentimiento == "All" else f"AND sentimiento = '{sentimiento}'"

    # --- Query dinámica ---
    query = f"""
    SELECT
        DATE(fecha_captura) AS fecha,
        sentimiento,
        categoria,
        subcategoria
        
    FROM ` .hacendatos.categorias`
    WHERE DATE(fecha_captura) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
    {where_sentimiento}
    {where_categoria}
    {where_subcategoria}
    """
    # Ejecutar query
    df = client.query(query).to_dataframe()


    ###query  valoracion sentimientos subcategorias
    valoracion_query_sub = f"""
    SELECT
        subcategoria,
        COUNT(*) AS total_sentimientos,
        COUNT(CASE WHEN sentimiento = 'positivo' THEN 1 END) AS positivos,
        COUNT(CASE WHEN sentimiento = 'negativo' THEN 1 END) AS negativos,
        COUNT(CASE WHEN sentimiento = 'neutral' THEN 1 END) AS neutrales,
        ROUND(100 * COUNT(CASE WHEN sentimiento = 'positivo' THEN 1 END) / COUNT(*), 2) AS pct_positivo,
        ROUND(100 * COUNT(CASE WHEN sentimiento = 'negativo' THEN 1 END) / COUNT(*), 2) AS pct_negativo,
        ROUND(100 * COUNT(CASE WHEN sentimiento = 'neutral' THEN 1 END) / COUNT(*), 2) AS pct_neutral
        FROM ` .hacendatos.categorias`
        WHERE DATE(fecha_captura) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
        {where_sentimiento}
        {where_categoria}
        {where_subcategoria}
        GROUP BY subcategoria
        ORDER BY total_sentimientos DESC
        LIMIT 5;
    """

    df_valoracion_sub = client.query(valoracion_query_sub).to_dataframe()

    ###query  valoracion sentimientos categorias
    valoracion_query = f"""
    SELECT
        categoria,
        COUNT(*) AS total_sentimientos,
        COUNT(CASE WHEN sentimiento = 'positivo' THEN 1 END) AS positivos,
        COUNT(CASE WHEN sentimiento = 'negativo' THEN 1 END) AS negativos,
        COUNT(CASE WHEN sentimiento = 'neutral' THEN 1 END) AS neutrales,
        ROUND(100 * COUNT(CASE WHEN sentimiento = 'positivo' THEN 1 END) / COUNT(*), 2) AS pct_positivo,
        ROUND(100 * COUNT(CASE WHEN sentimiento = 'negativo' THEN 1 END) / COUNT(*), 2) AS pct_negativo,
        ROUND(100 * COUNT(CASE WHEN sentimiento = 'neutral' THEN 1 END) / COUNT(*), 2) AS pct_neutral
        FROM ` .hacendatos.categorias`
        WHERE DATE(fecha_captura) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
        {where_sentimiento}
        {where_categoria}
        {where_subcategoria}
        GROUP BY categoria
        ORDER BY total_sentimientos ASC;
    """

    df_valoracion = client.query(valoracion_query).to_dataframe()
    total_valoraciones = df_valoracion['total_sentimientos'].sum()

    st.header(f"📊 Total de valoraciones: {total_valoraciones}")


    #crear grilla
    col1, col2, col3 = st.columns([2, 1, 2])


    with col2:
        #   st.subheader(f"Sentimiento {''.join(map(str, categoria_sel))}    {''.join(map(str,subcategoria_sel))}")
        if df.empty:
            st.warning("No hay datos para los filtros seleccionados.")
        else:
            #preparamos los datos
            counts_sentimientos = df.sentimiento.value_counts() #contamos valores
            df_pie = counts_sentimientos.reset_index() #hacemos el df con los valores
            df_pie.columns = ["sentimiento", "proporcion"]
            color_discrete_map={
                    "positivo": "#66cc00", #"green",
                    "negativo":"#cc3333", # "red",
                    "neutral": "#cfcfcf",#"gray"
                }
            fig_pie = px.pie(
                df_pie,
                names="sentimiento",   
                values="proporcion",   
                color="sentimiento",
                color_discrete_map=color_discrete_map,
                height=800,
                width=600
                )
            fig_pie.update_traces(textposition='inside', textinfo='percent+value+label')
            fig_pie.update_layout(showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)


    with col1:
        #Grafico categoria
        if ("All" in categoria_sel or len(categoria_sel) == 0) and (len(subcategoria_sel) == 0 or "All" in subcategoria_sel):
        #if "All" in categoria_sel or len(categoria_sel) == 0:
            fig_cate = px.bar(df_valoracion, y="categoria", 
                                x=["positivos", "negativos", "neutrales"],
                                color_discrete_sequence=["#66cc00", "#cc3333", "#cfcfcf"],
                                hover_data=["pct_positivo", "pct_negativo","pct_neutral"],
                                title="📉 Cantidad de reseñas por categorias",
                                labels={"value": "Número de valoraciones", "categoria": "Categoría"},
                                height=800,
                                width=600)
            fig_cate.update_layout(template="simple_white")
            #fig.update_layout(xaxis_tickangle=-45)
            fig_cate.update_layout(showlegend=False)
            fig_cate.update_layout(title_font=dict(size=28), title_x=0.25)
            st.plotly_chart(fig_cate, use_container_width=True)

        else:
            query_categoris_line = f"""
            SELECT
                DATE(fecha_captura) AS fecha,
                sentimiento,
                categoria,
                subcategoria
                
            FROM ` .hacendatos.categorias`
            WHERE DATE(fecha_captura) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
            {where_sentimiento}
            {where_categoria}
            """
            # Ejecutar query
            df_cat_line = client.query(query_categoris_line).to_dataframe()

            # --- Gráfico temporal por sentimientos ---
            df_time = (df_cat_line.groupby(["fecha", "sentimiento"]).size().reset_index(name="conteo"))

            df_time["fecha"] = pd.to_datetime(df_time["fecha"], errors='coerce')
            df_time["fecha"] = df_time["fecha"].dt.to_period('M').dt.to_timestamp()
            df_time = df_time.groupby(["fecha", "sentimiento"])["conteo"].sum().reset_index()
            
            color_discrete_map = {
                "positivo": "#66cc00",
                "negativo": "#cc3333",
                "neutral": "#cfcfcf"
            }

            fig_time = px.line(
                df_time,
                x="fecha",
                y="conteo",
                color="sentimiento",
                color_discrete_map=color_discrete_map,
                title=f"""📈 Evolución de valoraciónes en: {', '.join(df.categoria.head(1))}""",
                height=800
            )
            fig_time.update_layout(showlegend=False)
            fig_time.update_traces(opacity=0.90, line=dict(width=1))          
            fig_time.update_layout(
                template="simple_white",
                title_font=dict(size=24),
                title_x=0.0
            )
            st.plotly_chart(fig_time, use_container_width=True)

    with col3:
        #Grafico categoria
        if "All" in subcategoria_sel or len(subcategoria_sel) == 0:
            #grafico subcategoria
            fig_catesb = px.bar(df_valoracion_sub, y="subcategoria", 
                        x=["positivos", "negativos", "neutrales"],
                        color_discrete_sequence=["#66cc00", "#cc3333", "#cfcfcf"],
                        hover_data=["pct_positivo", "pct_negativo","pct_neutral"],
                        title="🏆 TOP 5 Subcategorias más valoradas",
                        labels={"value": "Número de valoraciones", "subcategoria": "Subcategoría"},
                        height=800)
            fig_catesb.update_layout(template="simple_white")
            fig_catesb.update_yaxes(autorange="reversed")
            #fig.update_layout(xaxis_tickangle=-45)
            fig_catesb.update_layout(showlegend=False)
            fig_catesb.update_layout(title_font=dict(size=28), title_x=0.22)

            st.plotly_chart(fig_catesb, use_container_width=True)


        else:
            
            # --- Gráfico temporal por sentimientos_subcat ---
            df_time_sc = (
                df.groupby(["fecha", "sentimiento"])
                .size()
                .reset_index(name="conteo")
            )

            df_time_sc["fecha"] = pd.to_datetime(df_time_sc["fecha"], errors='coerce')
            df_time_sc["fecha"] = df_time_sc["fecha"].dt.to_period('M').dt.to_timestamp()
            df_time_sc = df_time_sc.groupby(["fecha", "sentimiento"])["conteo"].sum().reset_index()

            color_discrete_map = {
                "positivo": "#66cc00",
                "negativo": "#cc3333",
                "neutral": "#cfcfcf"
            }

            fig_time_sc = px.line(
                df_time_sc ,
                x="fecha",
                y="conteo",
                color="sentimiento",
                color_discrete_map=color_discrete_map,
                title=f"""📈 Evolución de valoraciónes en: {', '.join(subcategoria_sel)}""",
                height=800
            )
            fig_time_sc.update_layout(showlegend=False)
            fig_time_sc.update_traces(opacity=0.90, line=dict(width=1))          
            fig_time_sc.update_layout(
                template="simple_white",
                title_font=dict(size=24),
                title_x=0.0
            )
            st.plotly_chart(fig_time_sc, use_container_width=True)


