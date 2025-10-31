# pages/4_Rede_de_Fraude.py - Análise de Rede de Fraude

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from utils import load_data, get_community_metrics, get_logo_path

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="HP Anti-Fraude | Rede de Fraude",
    page_icon="🕸️",
    layout="wide"
)

# --- CARREGAMENTO DOS DADOS ---
PATH_DATASET = "data/final_grafo/dataset_final_com_grafo.csv"
df = load_data(PATH_DATASET)

# --- TÍTULO E INTRODUÇÃO ---
st.title("🕸️ Análise de Rede de Fraude")
st.markdown("""
**Visualização e análise da rede de vendedores e suas conexões suspeitas.**
Identifique clusters de fraude, vendedores centrais e padrões de comportamento em rede.
""")

if df is None:
    st.stop()

# --- MÉTRICAS DA REDE ---
st.header("📊 Métricas da Rede")

# Calcular métricas da rede
community_metrics = get_community_metrics(df)
total_communities = len(community_metrics)
communities_suspeitas = len(community_metrics[community_metrics['taxa_suspeita'] > 50])
total_vendedores = df['seller_id'].nunique()
vendedores_em_comunidades = df[df['grafo_comunidade_id'].notna()]['seller_id'].nunique()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Comunidades", f"{total_communities:,}")
col2.metric("Comunidades Suspeitas", f"{communities_suspeitas:,}", f"{communities_suspeitas/total_communities*100:.1f}%")
col3.metric("Vendedores na Rede", f"{vendedores_em_comunidades:,}", f"{vendedores_em_comunidades/total_vendedores*100:.1f}%")
col4.metric("Densidade Média", f"{community_metrics['vendedores_unicos'].mean():.1f}", "Vendedores/comunidade")

# --- ANÁLISE DE COMUNIDADES ---
st.header("🔍 Análise de Comunidades")

# Filtros para análise de comunidades
col1, col2, col3 = st.columns(3)

with col1:
    min_taxa_suspeita = st.slider("Taxa Mín. Suspeita (%):", 0, 100, 0, help="Filtrar comunidades por taxa mínima de suspeita")

with col2:
    min_vendedores = st.slider("Mín. Vendedores:", 1, 50, 2, help="Filtrar comunidades com pelo menos X vendedores")

with col3:
    min_anuncios = st.slider("Mín. Anúncios:", 1, 100, 5, help="Filtrar comunidades com pelo menos X anúncios")

# Aplicar filtros
communities_filtered = community_metrics[
    (community_metrics['taxa_suspeita'] >= min_taxa_suspeita) &
    (community_metrics['vendedores_unicos'] >= min_vendedores) &
    (community_metrics['total_anuncios'] >= min_anuncios)
]

# Debug: Mostrar informações dos filtros
st.info(f"**Filtros aplicados:** Taxa ≥ {min_taxa_suspeita}% | Vendedores ≥ {min_vendedores} | Anúncios ≥ {min_anuncios} | **{len(communities_filtered)} comunidades encontradas**")

# Mostrar estatísticas antes e depois dos filtros
col_debug1, col_debug2 = st.columns(2)
with col_debug1:
    st.metric("Total Comunidades (antes)", len(community_metrics))
with col_debug2:
    st.metric("Comunidades Filtradas", len(communities_filtered))

# --- VISUALIZAÇÕES DE COMUNIDADES ---
col1, col2 = st.columns(2)

with col1:
    # Scatter Plot: Taxa de Suspeita vs Tamanho
    st.subheader("Taxa de Suspeita vs Tamanho da Comunidade")
    fig_scatter = px.scatter(
        communities_filtered, 
        x='vendedores_unicos', 
        y='taxa_suspeita',
        size='total_anuncios',
        color='score_medio',
        hover_data=['grafo_comunidade_id'],
        title="Comunidades: Tamanho vs Taxa de Suspeita",
        labels={'vendedores_unicos': 'Nº de Vendedores', 'taxa_suspeita': 'Taxa de Suspeita (%)'},
        color_continuous_scale='Reds'
    )
    fig_scatter.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="Threshold 50%")
    st.plotly_chart(fig_scatter, width='stretch', config={'displayModeBar': False})

with col2:
    # Distribuição de Tamanhos
    st.subheader("Distribuição do Tamanho das Comunidades")
    fig_hist = px.histogram(
        communities_filtered, 
        x='vendedores_unicos', 
        nbins=15,
        title="Distribuição do Número de Vendedores por Comunidade",
        color_discrete_sequence=['#2E8B57']
    )
    st.plotly_chart(fig_hist, width='stretch', config={'displayModeBar': False})

# --- RANKING DE COMUNIDADES ---
st.header("🏆 Ranking de Comunidades")

# Ordenar por diferentes critérios
sort_options = {
    'Taxa de Suspeita': 'taxa_suspeita',
    'Número de Vendedores': 'vendedores_unicos',
    'Total de Anúncios': 'total_anuncios',
    'Score Médio': 'score_medio'
}

col1, col2 = st.columns(2)

with col1:
    sort_by = st.selectbox("Ordenar por:", list(sort_options.keys()))

with col2:
    ascending = st.checkbox("Ordem Crescente", value=False)

# Aplicar ordenação
communities_sorted = communities_filtered.sort_values(sort_options[sort_by], ascending=ascending)

st.subheader(f"Top {min(15, len(communities_sorted))} Comunidades ({sort_by})")

if len(communities_sorted) > 0:
    # Adicionar classificação de risco
    def classify_community_risk(taxa):
        if taxa >= 80:
            return "🔴 Crítico"
        elif taxa >= 60:
            return "🟠 Alto"
        elif taxa >= 30:
            return "🟡 Médio"
        else:
            return "🟢 Baixo"
    
    communities_display = communities_sorted.copy()
    communities_display['classificacao_risco'] = communities_display['taxa_suspeita'].apply(classify_community_risk)
    
    st.dataframe(
        communities_display[['grafo_comunidade_id', 'vendedores_unicos', 'total_anuncios', 'anuncios_suspeitos', 'taxa_suspeita', 'score_medio', 'classificacao_risco']].head(15),
        width='stretch',
        column_config={
            "grafo_comunidade_id": "ID Comunidade",
            "vendedores_unicos": "Vendedores",
            "total_anuncios": "Total Anúncios",
            "anuncios_suspeitos": "Anúncios Suspeitos",
            "taxa_suspeita": st.column_config.ProgressColumn("Taxa Suspeita", format="%.1f%%", min_value=0, max_value=100),
            "score_medio": st.column_config.NumberColumn("Score Médio", format="%.2f"),
            "classificacao_risco": "Classificação"
        }
    )
else:
    st.warning("Nenhuma comunidade encontrada com os filtros aplicados.")

# --- ANÁLISE DE VENDEDORES POR COMUNIDADE ---
st.header("👥 Análise de Vendedores por Comunidade")

# Seleção de comunidade para análise detalhada
if len(communities_filtered) > 0:
    comunidade_options = ['Selecionar comunidade...'] + sorted(communities_filtered['grafo_comunidade_id'].tolist())
    comunidade_selecionada = st.selectbox("Escolha uma comunidade para análise detalhada:", comunidade_options)
    
    if comunidade_selecionada != 'Selecionar comunidade...':
        # Dados da comunidade selecionada
        comunidade_data = communities_filtered[communities_filtered['grafo_comunidade_id'] == comunidade_selecionada].iloc[0]
        vendedores_comunidade = df[df['grafo_comunidade_id'] == comunidade_selecionada]
        
        # Métricas da comunidade
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("Vendedores Únicos", f"{comunidade_data['vendedores_unicos']:,}")
        col2.metric("Total Anúncios", f"{comunidade_data['total_anuncios']:,}")
        col3.metric("Taxa de Suspeita", f"{comunidade_data['taxa_suspeita']:.1f}%")
        col4.metric("Score Médio", f"{comunidade_data['score_medio']:.2f}")
        
        # Análise de vendedores na comunidade
        st.subheader("Vendedores na Comunidade")
        vendedores_analysis = vendedores_comunidade.groupby(['seller_id', 'vendedor_nome']).agg({
            'id_anuncio': 'count',
            'is_fraud_suspect_v2': 'sum',
            'score_de_suspeita': 'mean',
            'preco_atual': 'mean'
        }).rename(columns={
            'id_anuncio': 'total_anuncios',
            'is_fraud_suspect_v2': 'anuncios_suspeitos',
            'score_de_suspeita': 'score_medio',
            'preco_atual': 'preco_medio'
        }).reset_index()
        
        vendedores_analysis['taxa_suspeita'] = (vendedores_analysis['anuncios_suspeitos'] / vendedores_analysis['total_anuncios'] * 100).round(1)
        vendedores_analysis = vendedores_analysis.sort_values('anuncios_suspeitos', ascending=False)
        
        st.dataframe(
            vendedores_analysis[['vendedor_nome', 'total_anuncios', 'anuncios_suspeitos', 'taxa_suspeita', 'score_medio', 'preco_medio']],
            width='stretch',
            column_config={
                "vendedor_nome": "Vendedor",
                "total_anuncios": "Total Anúncios",
                "anuncios_suspeitos": "Anúncios Suspeitos",
                "taxa_suspeita": st.column_config.ProgressColumn("Taxa Suspeita", format="%.1f%%", min_value=0, max_value=100),
                "score_medio": st.column_config.NumberColumn("Score Médio", format="%.2f"),
                "preco_medio": st.column_config.NumberColumn("Preço Médio (R$)", format="%.2f")
            }
        )
        
        # Análise de anúncios da comunidade
        st.subheader("Anúncios da Comunidade")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribuição de scores
            fig_score = px.histogram(
                vendedores_comunidade, 
                x='score_de_suspeita', 
                nbins=20,
                title="Distribuição de Scores na Comunidade",
                color_discrete_sequence=['#FF6B35']
            )
            fig_score.add_vline(x=3, line_dash="dash", line_color="red", annotation_text="Threshold")
            st.plotly_chart(fig_score, width='stretch', config={'displayModeBar': False})
        
        with col2:
            # Análise de preços (se disponível)
            if 'preco_atual' in vendedores_comunidade.columns and 'diferenca_preco_perc' in vendedores_comunidade.columns:
                fig_preco = px.scatter(
                    vendedores_comunidade, 
                    x='diferenca_preco_perc', 
                    y='score_de_suspeita',
                    color='is_fraud_suspect_v2',
                    color_discrete_map={0: 'blue', 1: 'red'},
                    title="Score vs Desconto na Comunidade"
                )
                fig_preco.update_layout(
                    xaxis_title="Diferença Percentual de Preço",
                    yaxis_title="Score de Suspeita",
                    xaxis_tickformat=".0%"
                )
                st.plotly_chart(fig_preco, width='stretch', config={'displayModeBar': False})

# --- SIMULAÇÃO DE GRAFO DE REDE ---
st.header("🕸️ Visualização da Rede")

# Nota sobre visualização de grafo
st.info("""
**Nota:** Para uma visualização completa do grafo de rede, seria necessário instalar bibliotecas como `pyvis` ou `plotly.graph_objects`.
Aqui apresentamos uma representação simplificada baseada nos dados de comunidade.
""")

# Criar um grafo simplificado usando NetworkX
try:
    import networkx as nx
    
    # Criar grafo
    G = nx.Graph()
    
    # Adicionar nós (vendedores) e arestas (conexões por comunidade)
    for _, row in df.iterrows():
        if pd.notna(row['grafo_comunidade_id']):
            G.add_node(row['seller_id'], 
                      name=row['vendedor_nome'],
                      community=row['grafo_comunidade_id'],
                      suspicious=row['is_fraud_suspect_v2'])
    
    # Adicionar arestas entre vendedores da mesma comunidade
    for community_id in df['grafo_comunidade_id'].dropna().unique():
        vendedores_comunidade = df[df['grafo_comunidade_id'] == community_id]['seller_id'].unique()
        for i, v1 in enumerate(vendedores_comunidade):
            for v2 in vendedores_comunidade[i+1:]:
                G.add_edge(v1, v2)
    
    # Calcular métricas do grafo
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    density = nx.density(G)
    
    # Componentes conectados
    components = list(nx.connected_components(G))
    largest_component = max(components, key=len) if components else set()
    
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Nós (Vendedores)", f"{num_nodes:,}")
    col2.metric("Arestas (Conexões)", f"{num_edges:,}")
    col3.metric("Densidade", f"{density:.3f}")
    col4.metric("Componentes", f"{len(components):,}")
    
    # Análise de centralidade (se o grafo não for muito grande)
    if num_nodes <= 1000:  # Limitar para performance
        try:
            # Calcular centralidade
            centrality = nx.degree_centrality(G)
            betweenness = nx.betweenness_centrality(G, k=min(100, num_nodes))
            
            # Top vendedores por centralidade
            top_central = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]
            top_between = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Top Vendedores por Centralidade de Grau")
                df_central = pd.DataFrame(top_central, columns=['seller_id', 'centralidade'])
                df_central['vendedor_nome'] = df_central['seller_id'].map(
                    df.set_index('seller_id')['vendedor_nome'].to_dict()
                )
                st.dataframe(df_central[['vendedor_nome', 'centralidade']], width='stretch')
            
            with col2:
                st.subheader("Top Vendedores por Centralidade de Intermediação")
                df_between = pd.DataFrame(top_between, columns=['seller_id', 'intermediacao'])
                df_between['vendedor_nome'] = df_between['seller_id'].map(
                    df.set_index('seller_id')['vendedor_nome'].to_dict()
                )
                st.dataframe(df_between[['vendedor_nome', 'intermediacao']], width='stretch')
        
        except Exception as e:
            st.warning(f"Erro ao calcular centralidade: {str(e)}")
    
    else:
        st.warning("Grafo muito grande para análise de centralidade. Use filtros para reduzir o tamanho.")

except ImportError:
    st.warning("NetworkX não está instalado. Instale com: `pip install networkx`")
except Exception as e:
    st.error(f"Erro ao criar grafo: {str(e)}")

# --- PADRÕES DE FRAUDE EM REDE ---
st.header("🔍 Padrões de Fraude em Rede")

# Análise de clusters suspeitos
if len(communities_filtered) > 0:
    st.subheader("Análise de Clusters Suspeitos")
    
    # Identificar padrões
    clusters_criticos = communities_filtered[communities_filtered['taxa_suspeita'] >= 80]
    clusters_alto_risco = communities_filtered[(communities_filtered['taxa_suspeita'] >= 50) & (communities_filtered['taxa_suspeita'] < 80)]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Clusters Críticos", len(clusters_criticos), "Taxa ≥ 80%")
        if len(clusters_criticos) > 0:
            if st.button("🚨 Ação Imediata"):
                st.error(f"Ação imediata recomendada para {len(clusters_criticos)} clusters!")
    
    with col2:
        st.metric("Alto Risco", len(clusters_alto_risco), "Taxa 50-80%")
        if len(clusters_alto_risco) > 0:
            if st.button("🔍 Investigar"):
                st.warning(f"Investigação recomendada para {len(clusters_alto_risco)} clusters!")
    
    with col3:
        total_anuncios_suspeitos = communities_filtered['anuncios_suspeitos'].sum()
        st.metric("Anúncios Suspeitos", total_anuncios_suspeitos, "Total em clusters")
        if st.button("📊 Relatório Completo"):
            st.success("Relatório de clusters gerado!")

# --- RECOMENDAÇÕES ESTRATÉGICAS ---
st.header("💡 Recomendações Estratégicas")

# Análise de recomendações
if len(communities_filtered) > 0:
    # Identificar comunidades problemáticas
    comunidades_problematicas = communities_filtered[communities_filtered['taxa_suspeita'] > 30]
    
    if len(comunidades_problematicas) > 0:
        st.subheader("🎯 Ações Recomendadas")
        
        # Recomendações baseadas nos dados
        recomendacoes = []
        
        if len(clusters_criticos) > 0:
            recomendacoes.append(f"🚨 **Ação Imediata**: {len(clusters_criticos)} clusters críticos identificados")
        
        if len(clusters_alto_risco) > 0:
            recomendacoes.append(f"🔍 **Investigação Prioritária**: {len(clusters_alto_risco)} clusters de alto risco")
        
        if communities_filtered['vendedores_unicos'].max() > 20:
            recomendacoes.append("⚠️ **Monitoramento**: Clusters muito grandes podem indicar coordenação")
        
        if communities_filtered['taxa_suspeita'].mean() > 50:
            recomendacoes.append("📈 **Análise Sistêmica**: Taxa média alta sugere problema sistêmico")
        
        for rec in recomendacoes:
            st.markdown(rec)
    
    else:
        st.success("✅ Nenhuma comunidade problemática identificada com os filtros atuais.")

# --- SIDEBAR ---
# Logo HP no topo da sidebar (acima das abas de navegação) - Centralizado
col1, col2, col3 = st.sidebar.columns([1, 2, 1])
with col2:
    st.image(get_logo_path(), width=150)

st.sidebar.success("🕸️ Página de Rede de Fraude")
st.sidebar.info(f"""
**Resumo da Rede:**
- Comunidades: {total_communities:,}
- Suspeitas: {communities_suspeitas:,}
- Vendedores: {vendedores_em_comunidades:,}
- Densidade: {community_metrics['vendedores_unicos'].mean():.1f}
""")

st.sidebar.metric("Taxa Média Suspeita", f"{community_metrics['taxa_suspeita'].mean():.1f}%", "Comunidades")
