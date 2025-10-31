# pages/3_Analise_de_Vendedores.py - Análise de Vendedores

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import load_data, get_seller_metrics, get_community_metrics, get_logo_path

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="HP Anti-Fraude | Análise de Vendedores",
    page_icon="👥",
    layout="wide"
)

# --- CARREGAMENTO DOS DADOS ---
PATH_DATASET = "data/final_grafo/dataset_final_com_grafo.csv"
df = load_data(PATH_DATASET)

# --- TÍTULO E INTRODUÇÃO ---
st.title("👥 Análise de Vendedores")
st.markdown("""
**Análise comportamental e de risco dos vendedores no ecossistema HP.**
Identifique padrões suspeitos, vendedores de alto risco e estratégias de mitigação.
""")

if df is None:
    st.stop()

# --- MÉTRICAS GERAIS DE VENDEDORES ---
st.header("📊 Panorama dos Vendedores")

# Calcular métricas de vendedores
seller_metrics = get_seller_metrics(df)
community_metrics = get_community_metrics(df)

total_vendedores = df['seller_id'].nunique()
vendedores_suspeitos = df[df['is_fraud_suspect_v2'] == 1]['seller_id'].nunique()
vendedores_100_suspeitos = (seller_metrics['taxa_suspeita'] == 100).sum()
vendedores_alto_risco = (seller_metrics['taxa_suspeita'] > 50).sum()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total de Vendedores", f"{total_vendedores:,}")
col2.metric("Vendedores Suspeitos", f"{vendedores_suspeitos:,}", f"{vendedores_suspeitos/total_vendedores*100:.1f}%")
col3.metric("100% Suspeitos", f"{vendedores_100_suspeitos:,}", "Crítico")
col4.metric("Alto Risco (>50%)", f"{vendedores_alto_risco:,}", "Atenção")

# --- RANKING DE VENDEDORES SUSPEITOS ---
st.header("🚨 Ranking de Vendedores Suspeitos")

# Filtros para o ranking
col1, col2, col3 = st.columns(3)

with col1:
    min_anuncios = st.slider("Mín. Anúncios:", 1, 50, 5, help="Filtrar vendedores com pelo menos X anúncios")

with col2:
    min_taxa_suspeita = st.slider("Mín. Taxa Suspeita (%):", 0, 100, 0, help="Filtrar por taxa mínima de suspeita")

with col3:
    status_filter = st.selectbox("Status do Vendedor:", ['Todos'] + sorted(df['power_seller_status'].unique().tolist()))

# Aplicar filtros
seller_filtered = seller_metrics[
    (seller_metrics['total_anuncios'] >= min_anuncios) &
    (seller_metrics['taxa_suspeita'] >= min_taxa_suspeita)
]

if status_filter != 'Todos':
    seller_filtered = seller_filtered[seller_filtered['status'] == status_filter]

# Exibir ranking
st.subheader(f"Top {min(20, len(seller_filtered))} Vendedores Filtrados")

if len(seller_filtered) > 0:
    # Adicionar coluna de classificação de risco
    def classify_risk(taxa):
        if taxa == 100:
            return "🔴 Crítico"
        elif taxa >= 70:
            return "🟠 Alto"
        elif taxa >= 30:
            return "🟡 Médio"
        else:
            return "🟢 Baixo"
    
    seller_display = seller_filtered.copy()
    seller_display['classificacao_risco'] = seller_display['taxa_suspeita'].apply(classify_risk)
    
    st.dataframe(
        seller_display[['vendedor_nome', 'total_anuncios', 'anuncios_suspeitos', 'taxa_suspeita', 'score_medio', 'classificacao_risco', 'status']].head(20),
        width='stretch',
        column_config={
            "vendedor_nome": "Vendedor",
            "total_anuncios": "Total Anúncios",
            "anuncios_suspeitos": "Anúncios Suspeitos",
            "taxa_suspeita": st.column_config.ProgressColumn("Taxa Suspeita", format="%.1f%%", min_value=0, max_value=100),
            "score_medio": st.column_config.NumberColumn("Score Médio", format="%.2f"),
            "classificacao_risco": "Classificação",
            "status": "Status"
        }
    )
else:
    st.warning("Nenhum vendedor encontrado com os filtros aplicados.")

# --- ANÁLISE COMPORTAMENTAL ---
st.header("🔍 Análise Comportamental")

col1, col2 = st.columns(2)

with col1:
    # Distribuição de Taxa de Suspeita
    st.subheader("Distribuição da Taxa de Suspeita")
    fig_hist = px.histogram(
        seller_metrics, 
        x='taxa_suspeita', 
        nbins=20,
        title="Frequência de Taxa de Suspeita por Vendedor",
        color_discrete_sequence=['#FF6B35']
    )
    fig_hist.add_vline(x=50, line_dash="dash", line_color="red", annotation_text="Threshold 50%")
    fig_hist.add_vline(x=100, line_dash="dash", line_color="darkred", annotation_text="100% Suspeito")
    st.plotly_chart(fig_hist, width='stretch', config={'displayModeBar': False})

with col2:
    # Score Médio vs Taxa de Suspeita
    st.subheader("Score Médio vs Taxa de Suspeita")
    fig_scatter = px.scatter(
        seller_metrics, 
        x='taxa_suspeita', 
        y='score_medio',
        size='total_anuncios',
        color='status',
        hover_data=['vendedor_nome'],
        title="Correlação: Taxa de Suspeita vs Score Médio",
        labels={'taxa_suspeita': 'Taxa de Suspeita (%)', 'score_medio': 'Score Médio'}
    )
    fig_scatter.add_hline(y=3, line_dash="dash", line_color="red", annotation_text="Threshold Score")
    fig_scatter.add_vline(x=50, line_dash="dash", line_color="red", annotation_text="Threshold Taxa")
    st.plotly_chart(fig_scatter, width='stretch', config={'displayModeBar': False})

# --- ANÁLISE POR STATUS DO VENDEDOR ---
st.header("🏆 Análise por Status do Vendedor")

status_analysis = seller_metrics.groupby('status').agg({
    'total_anuncios': 'sum',
    'anuncios_suspeitos': 'sum',
    'taxa_suspeita': 'mean',
    'score_medio': 'mean',
    'vendedor_nome': 'count'
}).rename(columns={'vendedor_nome': 'total_vendedores'})

status_analysis['taxa_suspeita_media'] = status_analysis['taxa_suspeita'].round(1)
status_analysis['score_medio'] = status_analysis['score_medio'].round(2)

col1, col2 = st.columns(2)

with col1:
    # Taxa de Suspeita por Status
    st.subheader("Taxa Média de Suspeita por Status")
    fig_bar = px.bar(
        status_analysis.reset_index(), 
        x='status', 
        y='taxa_suspeita_media',
        title="Taxa Média de Suspeita por Status do Vendedor",
        color='taxa_suspeita_media',
        color_continuous_scale='Reds'
    )
    fig_bar.update_layout(showlegend=False)
    st.plotly_chart(fig_bar, width='stretch', config={'displayModeBar': False})

with col2:
    # Volume de Anúncios por Status
    st.subheader("Volume de Anúncios por Status")
    fig_pie = px.pie(
        status_analysis.reset_index(), 
        values='total_anuncios', 
        names='status',
        title="Distribuição de Anúncios por Status"
    )
    st.plotly_chart(fig_pie, width='stretch', config={'displayModeBar': False})

# Tabela de análise por status
st.subheader("Resumo por Status do Vendedor")
st.dataframe(
    status_analysis[['total_vendedores', 'total_anuncios', 'anuncios_suspeitos', 'taxa_suspeita_media', 'score_medio']],
    width='stretch',
    column_config={
        "total_vendedores": "Vendedores",
        "total_anuncios": "Total Anúncios",
        "anuncios_suspeitos": "Anúncios Suspeitos",
        "taxa_suspeita_media": st.column_config.ProgressColumn("Taxa Media", format="%.1f%%", min_value=0, max_value=100),
        "score_medio": st.column_config.NumberColumn("Score Médio", format="%.2f")
    }
)

# --- ANÁLISE DE COMUNIDADES ---
st.header("🕸️ Análise de Comunidades de Vendedores")

if len(community_metrics) > 0:
    col1, col2 = st.columns(2)
    
    with col1:
        # Top Comunidades Suspeitas
        st.subheader("Top Comunidades por Taxa de Suspeita")
        top_communities = community_metrics.head(10)
        
        fig_comm = px.bar(
            top_communities, 
            x='taxa_suspeita', 
            y='grafo_comunidade_id',
            orientation='h',
            title="Top 10 Comunidades Mais Suspeitas",
            color='taxa_suspeita',
            color_continuous_scale='Reds'
        )
        fig_comm.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_comm, width='stretch', config={'displayModeBar': False})
    
    with col2:
        # Distribuição de Tamanho das Comunidades
        st.subheader("Distribuição do Tamanho das Comunidades")
        fig_size = px.histogram(
            community_metrics, 
            x='total_anuncios', 
            nbins=15,
            title="Distribuição do Número de Anúncios por Comunidade",
            color_discrete_sequence=['#2E8B57']
        )
        st.plotly_chart(fig_size, width='stretch', config={'displayModeBar': False})
    
    # Tabela de comunidades
    st.subheader("Detalhes das Comunidades")
    st.dataframe(
        community_metrics[['grafo_comunidade_id', 'total_anuncios', 'anuncios_suspeitos', 'taxa_suspeita', 'vendedores_unicos', 'score_medio']].head(15),
        width='stretch',
        column_config={
            "grafo_comunidade_id": "ID Comunidade",
            "total_anuncios": "Total Anúncios",
            "anuncios_suspeitos": "Anúncios Suspeitos",
            "taxa_suspeita": st.column_config.ProgressColumn("Taxa Suspeita", format="%.1f%%", min_value=0, max_value=100),
            "vendedores_unicos": "Vendedores Únicos",
            "score_medio": st.column_config.NumberColumn("Score Médio", format="%.2f")
        }
    )

# --- INVESTIGAÇÃO DE VENDEDOR ESPECÍFICO ---
st.header("🔍 Investigação de Vendedor Específico")

# Filtros de Investigação
st.subheader("Filtros de Investigação")
col_filtro1, col_filtro2, col_filtro3 = st.columns(3)

with col_filtro1:
    filtro_suspeita = st.selectbox(
        "Filtrar por Nível de Suspeita:",
        options=['Todos', 'Críticos (100%)', 'Alto Risco (>50%)', 'Médio Risco (25-50%)', 'Baixo Risco (<25%)'],
        help="Filtre vendedores por sua taxa de anúncios suspeitos"
    )

with col_filtro2:
    filtro_min_anuncios = st.slider(
        "Mínimo de Anúncios:",
        min_value=1,
        max_value=int(seller_metrics['total_anuncios'].max()),
        value=1,
        help="Filtre vendedores com pelo menos X anúncios"
    )

with col_filtro3:
    filtro_status = st.multiselect(
        "Status do Vendedor:",
        options=['bronze', 'silver', 'gold', 'platinum'],
        default=['bronze', 'silver', 'gold', 'platinum'],
        help="Selecione os status de vendedor para incluir"
    )

# Filtros adicionais em nova linha
col_filtro4, col_filtro5, col_filtro6 = st.columns(3)

with col_filtro4:
    filtro_oficial = st.selectbox(
        "Loja Oficial:",
        options=['Todos', 'Apenas Oficiais', 'Apenas Não-Oficiais'],
        help="Filtrar por status de loja oficial"
    )

with col_filtro5:
    filtro_reputacao = st.selectbox(
        "Nível de Reputação:",
        options=['Todos', 'Muito Ruim', 'Ruim', 'Regular', 'Boa', 'Muito Boa'],
        help="Filtrar por nível de reputação do vendedor"
    )

with col_filtro6:
    filtro_score_min = st.slider(
        "Score Mínimo:",
        min_value=0.0,
        max_value=10.0,
        value=0.0,
        step=0.5,
        help="Score de suspeita mínimo"
    )

# Aplicar filtros
seller_metrics_filtrado = seller_metrics.copy()

# Filtro por suspeita
if filtro_suspeita == 'Críticos (100%)':
    seller_metrics_filtrado = seller_metrics_filtrado[seller_metrics_filtrado['taxa_suspeita'] == 100]
elif filtro_suspeita == 'Alto Risco (>50%)':
    seller_metrics_filtrado = seller_metrics_filtrado[seller_metrics_filtrado['taxa_suspeita'] > 50]
elif filtro_suspeita == 'Médio Risco (25-50%)':
    seller_metrics_filtrado = seller_metrics_filtrado[(seller_metrics_filtrado['taxa_suspeita'] >= 25) & (seller_metrics_filtrado['taxa_suspeita'] <= 50)]
elif filtro_suspeita == 'Baixo Risco (<25%)':
    seller_metrics_filtrado = seller_metrics_filtrado[seller_metrics_filtrado['taxa_suspeita'] < 25]

# Filtro por número mínimo de anúncios
seller_metrics_filtrado = seller_metrics_filtrado[seller_metrics_filtrado['total_anuncios'] >= filtro_min_anuncios]

# Filtro por status do vendedor
if filtro_status and 'status' in seller_metrics_filtrado.columns:
    seller_metrics_filtrado = seller_metrics_filtrado[seller_metrics_filtrado['status'].isin(filtro_status)]

# Filtro por loja oficial
if filtro_oficial == 'Apenas Oficiais':
    if 'loja_oficial' in seller_metrics_filtrado.columns:
        seller_metrics_filtrado = seller_metrics_filtrado[seller_metrics_filtrado['loja_oficial'] == True]
elif filtro_oficial == 'Apenas Não-Oficiais':
    if 'loja_oficial' in seller_metrics_filtrado.columns:
        seller_metrics_filtrado = seller_metrics_filtrado[seller_metrics_filtrado['loja_oficial'] == False]

# Filtro por reputação
if filtro_reputacao != 'Todos' and 'reputacao' in seller_metrics_filtrado.columns:
    if filtro_reputacao == 'Muito Ruim':
        seller_metrics_filtrado = seller_metrics_filtrado[seller_metrics_filtrado['reputacao'] <= 1]
    elif filtro_reputacao == 'Ruim':
        seller_metrics_filtrado = seller_metrics_filtrado[(seller_metrics_filtrado['reputacao'] > 1) & (seller_metrics_filtrado['reputacao'] <= 2)]
    elif filtro_reputacao == 'Regular':
        seller_metrics_filtrado = seller_metrics_filtrado[(seller_metrics_filtrado['reputacao'] > 2) & (seller_metrics_filtrado['reputacao'] <= 3)]
    elif filtro_reputacao == 'Boa':
        seller_metrics_filtrado = seller_metrics_filtrado[(seller_metrics_filtrado['reputacao'] > 3) & (seller_metrics_filtrado['reputacao'] <= 4)]
    elif filtro_reputacao == 'Muito Boa':
        seller_metrics_filtrado = seller_metrics_filtrado[seller_metrics_filtrado['reputacao'] > 4]

# Filtro por score mínimo
seller_metrics_filtrado = seller_metrics_filtrado[seller_metrics_filtrado['score_medio'] >= filtro_score_min]

# Mostrar estatísticas dos filtros
filtros_aplicados = []
if filtro_suspeita != 'Todos':
    filtros_aplicados.append(f"Suspeita: {filtro_suspeita}")
if filtro_min_anuncios > 1:
    filtros_aplicados.append(f"Mín. {filtro_min_anuncios} anúncios")
if filtro_status and len(filtro_status) < 4:
    filtros_aplicados.append(f"Status: {', '.join(filtro_status)}")
if filtro_oficial != 'Todos':
    filtros_aplicados.append(f"Oficial: {filtro_oficial}")
if filtro_reputacao != 'Todos':
    filtros_aplicados.append(f"Reputação: {filtro_reputacao}")
if filtro_score_min > 0:
    filtros_aplicados.append(f"Score ≥ {filtro_score_min}")

filtros_texto = " | ".join(filtros_aplicados) if filtros_aplicados else "Nenhum filtro aplicado"

st.info(f"**Filtros aplicados:** {filtros_texto} | **{len(seller_metrics_filtrado)} vendedores encontrados**")

# Seleção de vendedor (após filtros)
vendedor_options = ['Selecionar vendedor...'] + sorted(seller_metrics_filtrado['vendedor_nome'].tolist())
vendedor_selecionado = st.selectbox("Escolha um vendedor para investigar:", vendedor_options)

if vendedor_selecionado != 'Selecionar vendedor...':
    # Dados do vendedor selecionado
    vendedor_data = seller_metrics[seller_metrics['vendedor_nome'] == vendedor_selecionado].iloc[0]
    vendedor_anuncios = df[df['vendedor_nome'] == vendedor_selecionado]
    
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Total Anúncios", f"{vendedor_data['total_anuncios']:,}")
    col2.metric("Anúncios Suspeitos", f"{vendedor_data['anuncios_suspeitos']:,}")
    col3.metric("Taxa de Suspeita", f"{vendedor_data['taxa_suspeita']:.1f}%")
    col4.metric("Score Médio", f"{vendedor_data['score_medio']:.2f}")
    
    # Análise temporal (se houver dados de data)
    st.subheader("Anúncios do Vendedor")
    
    # Mostrar anúncios suspeitos primeiro
    anuncios_suspeitos = vendedor_anuncios[vendedor_anuncios['is_fraud_suspect_v2'] == 1].sort_values('score_de_suspeita', ascending=False)
    anuncios_legitimos = vendedor_anuncios[vendedor_anuncios['is_fraud_suspect_v2'] == 0].sort_values('score_de_suspeita', ascending=False)
    
    if len(anuncios_suspeitos) > 0:
        st.subheader("🚨 Anúncios Suspeitos")
        st.dataframe(
            anuncios_suspeitos[['id_anuncio', 'score_de_suspeita', 'preco_atual', 'diferenca_preco_perc', 'link_anuncio']],
            width='stretch',
            column_config={
                "id_anuncio": "ID Anúncio",
                "score_de_suspeita": st.column_config.NumberColumn("Score", format="%.2f"),
                "preco_atual": st.column_config.NumberColumn("Preço (R$)", format="%.2f"),
                "diferenca_preco_perc": st.column_config.ProgressColumn("Desconto", format="%.1f%%", min_value=-1, max_value=0),
                "link_anuncio": st.column_config.LinkColumn("Link", display_text="🔗 Abrir")
            }
        )
    
    if len(anuncios_legitimos) > 0:
        st.subheader("✅ Anúncios Legítimos")
        st.dataframe(
            anuncios_legitimos[['id_anuncio', 'score_de_suspeita', 'preco_atual', 'diferenca_preco_perc', 'link_anuncio']].head(10),
            width='stretch',
            column_config={
                "id_anuncio": "ID Anúncio",
                "score_de_suspeita": st.column_config.NumberColumn("Score", format="%.2f"),
                "preco_atual": st.column_config.NumberColumn("Preço (R$)", format="%.2f"),
                "diferenca_preco_perc": st.column_config.ProgressColumn("Desconto", format="%.1f%%", min_value=-1, max_value=0),
                "link_anuncio": st.column_config.LinkColumn("Link", display_text="🔗 Abrir")
            }
        )

# --- AÇÕES RECOMENDADAS ---
st.header("⚡ Ações Recomendadas")

# Identificar vendedores críticos
vendedores_criticos = seller_metrics[seller_metrics['taxa_suspeita'] == 100]
vendedores_alto_risco = seller_metrics[(seller_metrics['taxa_suspeita'] > 50) & (seller_metrics['taxa_suspeita'] < 100)]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Vendedores Críticos", len(vendedores_criticos), "Ação Imediata")
    if len(vendedores_criticos) > 0:
        if st.button("🚨 Bloquear Vendedores Críticos"):
            st.error(f"Bloqueio recomendado para {len(vendedores_criticos)} vendedores!")

with col2:
    st.metric("Alto Risco", len(vendedores_alto_risco), "Investigação")
    if len(vendedores_alto_risco) > 0:
        if st.button("🔍 Investigar Alto Risco"):
            st.warning(f"Investigação recomendada para {len(vendedores_alto_risco)} vendedores!")

with col3:
    total_anuncios_suspeitos = seller_metrics['anuncios_suspeitos'].sum()
    st.metric("Anúncios Suspeitos", total_anuncios_suspeitos, "Total")
    if st.button("📊 Gerar Relatório Completo"):
        st.success("Relatório de vendedores gerado com sucesso!")

# --- SIDEBAR ---
# Logo HP no topo da sidebar (acima das abas de navegação) - Centralizado
col1, col2, col3 = st.sidebar.columns([1, 2, 1])
with col2:
    st.image(get_logo_path(), width=150)

st.sidebar.success("👥 Página de Análise de Vendedores")
st.sidebar.info(f"""
**Resumo:**
- Total Vendedores: {total_vendedores}
- Suspeitos: {vendedores_suspeitos}
- Críticos: {vendedores_100_suspeitos}
- Alto Risco: {vendedores_alto_risco}
""")

st.sidebar.metric("Taxa Geral Suspeita", f"{seller_metrics['taxa_suspeita'].mean():.1f}%", "Média")
