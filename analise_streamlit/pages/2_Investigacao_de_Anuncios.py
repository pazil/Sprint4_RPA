# pages/2_Investigacao_de_Anuncios.py - Ferramenta de Investigação de Anúncios

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import load_data, load_ml_scores, get_risk_categories, get_logo_path

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="HP Anti-Fraude | Investigação de Anúncios",
    page_icon="🔬",
    layout="wide"
)

# --- CARREGAMENTO DOS DADOS ---
PATH_DATASET = "data/final_grafo/dataset_final_com_grafo.csv"
df = load_data(PATH_DATASET)
df_with_scores = load_ml_scores()

# Adicionar categorias de risco
df = get_risk_categories(df)

# --- TÍTULO E INTRODUÇÃO ---
st.title("🔬 Ferramenta de Investigação de Anúncios")
st.markdown("""
**Filtre e analise os anúncios suspeitos para ação direcionada.**
Use os filtros na barra lateral para investigar casos específicos e tomar decisões baseadas em dados.
""")

if df is None:
    st.stop()

# --- FILTROS INTERATIVOS NA BARRA LATERAL ---
# Logo HP no topo da sidebar (acima das abas de navegação) - Centralizado
col1, col2, col3 = st.sidebar.columns([1, 2, 1])
with col2:
    st.image(get_logo_path(), width=150)

st.sidebar.header("🔍 Filtros de Investigação")

# Filtro por Score de Suspeita
score_min, score_max = st.sidebar.slider(
    "Score de Suspeita:",
    min_value=float(df['score_de_suspeita'].min()),
    max_value=float(df['score_de_suspeita'].max()),
    value=(0.0, float(df['score_de_suspeita'].max())),
    step=0.1,
    help="Selecione o range de scores para investigar"
)

# Filtro por Categoria de Risco
risk_categories = ['Todas'] + list(df['risk_category'].unique())
selected_risk = st.sidebar.selectbox(
    "Categoria de Risco:",
    options=risk_categories,
    help="Filtrar por nível de risco"
)

# Filtro por Comunidade de Risco
comunidades_perigosas = df[df['grafo_taxa_suspeita_comunidade'] > 0.2]['grafo_comunidade_id'].unique()
comunidades_options = ['Todas'] + sorted([int(c) for c in comunidades_perigosas if not pd.isna(c)])
comunidade_selecionada = st.sidebar.selectbox(
    "Comunidade de Risco:",
    options=comunidades_options,
    help="Filtrar por comunidades com alta taxa de suspeita"
)

# Filtro por Status do Vendedor
status_options = ['Todos'] + sorted(df['power_seller_status'].unique().tolist())
status_selecionado = st.sidebar.selectbox(
    "Status do Vendedor:",
    options=status_options,
    help="Filtrar por nível do vendedor"
)

# Filtro por Faixa de Preço
if 'preco_atual' in df.columns:
    preco_min = float(df['preco_atual'].min())
    preco_max = float(df['preco_atual'].max())
    preco_range = st.sidebar.slider(
        "Faixa de Preço (R$):",
        min_value=preco_min,
        max_value=preco_max,
        value=(preco_min, preco_max),
        step=1.0,
        help="Filtrar por faixa de preço"
    )
else:
    preco_range = (0, 1000)

# Filtro por Flags de Fraude
st.sidebar.subheader("Flags de Fraude")
flags = [col for col in df.columns if col.startswith('flag_')]
selected_flags = []
for flag in flags:
    if st.sidebar.checkbox(flag.replace('flag_', '').replace('_', ' ').title(), value=False):
        selected_flags.append(flag)

# --- APLICAÇÃO DOS FILTROS ---
df_filtrado = df.copy()

# Aplicar filtros sequencialmente
df_filtrado = df_filtrado[
    (df_filtrado['score_de_suspeita'] >= score_min) & 
    (df_filtrado['score_de_suspeita'] <= score_max)
]

if selected_risk != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['risk_category'] == selected_risk]

if comunidade_selecionada != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['grafo_comunidade_id'] == comunidade_selecionada]

if status_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['power_seller_status'] == status_selecionado]

if 'preco_atual' in df.columns:
    df_filtrado = df_filtrado[
        (df_filtrado['preco_atual'] >= preco_range[0]) & 
        (df_filtrado['preco_atual'] <= preco_range[1])
    ]

# Aplicar filtros de flags
for flag in selected_flags:
    df_filtrado = df_filtrado[df_filtrado[flag] == 1]

# --- MÉTRICAS DOS FILTROS APLICADOS ---
st.header("📊 Resultados da Investigação")

col1, col2, col3, col4 = st.columns(4)

total_original = len(df)
total_filtrado = len(df_filtrado)
suspicious_filtrado = df_filtrado['is_fraud_suspect_v2'].sum()
suspicious_rate = (suspicious_filtrado / total_filtrado * 100) if total_filtrado > 0 else 0

col1.metric("Anúncios Filtrados", f"{total_filtrado:,}", f"{total_filtrado/total_original*100:.1f}% do total")
col2.metric("Suspeitos Encontrados", f"{suspicious_filtrado:,}", f"{suspicious_rate:.1f}% dos filtrados")
col3.metric("Taxa de Detecção", f"{suspicious_rate:.1f}%", "Eficiência dos filtros")
col4.metric("Redução de Dados", f"{total_original - total_filtrado:,}", "Anúncios excluídos")

# --- VISUALIZAÇÕES DOS DADOS FILTRADOS ---
if total_filtrado > 0:
    st.header("📈 Análise dos Anúncios Filtrados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribuição de Scores
        fig_hist = px.histogram(
            df_filtrado, 
            x='score_de_suspeita', 
            nbins=20,
            title="Distribuição de Scores (Filtrados)",
            color_discrete_sequence=['#FF6B35']
        )
        fig_hist.add_vline(x=3, line_dash="dash", line_color="red", annotation_text="Threshold")
        st.plotly_chart(fig_hist, width='stretch', config={'displayModeBar': False})
    
    with col2:
        # Distribuição por Categoria de Risco
        risk_dist = df_filtrado['risk_category'].value_counts()
        fig_pie = px.pie(
            values=risk_dist.values, 
            names=risk_dist.index,
            title="Distribuição por Categoria de Risco",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(fig_pie, width='stretch', config={'displayModeBar': False})
    
    # Análise de Preços (se disponível)
    if 'preco_atual' in df.columns and 'diferenca_preco_perc' in df.columns:
        st.subheader("💰 Análise de Preços dos Anúncios Filtrados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Scatter Plot: Preço vs Score
            fig_scatter = px.scatter(
                df_filtrado, 
                x='diferenca_preco_perc', 
                y='score_de_suspeita',
                color='is_fraud_suspect_v2',
                color_discrete_map={0: 'blue', 1: 'red'},
                hover_data=['vendedor_nome', 'preco_atual'],
                title="Score vs Desconto de Preço"
            )
            fig_scatter.update_layout(
                xaxis_title="Diferença Percentual de Preço",
                yaxis_title="Score de Suspeita",
                xaxis_tickformat=".0%"
            )
            st.plotly_chart(fig_scatter, width='stretch', config={'displayModeBar': False})
        
        with col2:
            # Box Plot: Preços por Status
            fig_box = px.box(
                df_filtrado, 
                x='is_fraud_suspect_v2', 
                y='preco_atual',
                color='is_fraud_suspect_v2',
                color_discrete_map={0: 'blue', 1: 'red'},
                title="Distribuição de Preços por Status"
            )
            fig_box.update_layout(showlegend=False)
            st.plotly_chart(fig_box, width='stretch', config={'displayModeBar': False})

# --- TABELA DE DADOS INTERATIVA ---
st.header("📋 Tabela de Anúncios Investigados")

if total_filtrado > 0:
    # Ordenar por score de suspeita (maior primeiro)
    df_display = df_filtrado.sort_values(by='score_de_suspeita', ascending=False)
    
    # Configurar colunas para exibição
    display_columns = [
        'id_anuncio', 'vendedor_nome', 'score_de_suspeita', 'risk_category',
        'is_fraud_suspect_v2', 'preco_atual', 'diferenca_preco_perc',
        'grafo_taxa_suspeita_comunidade', 'power_seller_status', 'link_anuncio'
    ]
    
    # Adicionar colunas de flags se existirem
    flags_display = [col for col in flags if col in df_display.columns]
    display_columns.extend(flags_display)
    
    # Filtrar apenas colunas que existem
    display_columns = [col for col in display_columns if col in df_display.columns]
    
    st.dataframe(
        df_display[display_columns],
        width='stretch',
        column_config={
            "id_anuncio": "ID Anúncio",
            "vendedor_nome": "Vendedor",
            "score_de_suspeita": st.column_config.NumberColumn("Score", format="%.2f"),
            "risk_category": "Categoria Risco",
            "is_fraud_suspect_v2": st.column_config.CheckboxColumn("Suspeito"),
            "preco_atual": st.column_config.NumberColumn("Preço (R$)", format="%.2f"),
            "diferenca_preco_perc": st.column_config.ProgressColumn("Desconto", format="%.1f%%", min_value=-1, max_value=0),
            "grafo_taxa_suspeita_comunidade": st.column_config.ProgressColumn("Risco Comunidade", format="%.1f%%", min_value=0, max_value=1),
            "power_seller_status": "Status Vendedor",
            "link_anuncio": st.column_config.LinkColumn("Link", display_text="🔗 Abrir", width="small"),
        },
        height=600
    )
    
    # --- AÇÕES EM LOTE ---
    st.header("⚡ Ações em Lote")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Gerar Relatório", type="primary"):
            st.success(f"Relatório gerado para {total_filtrado} anúncios filtrados!")
    
    with col2:
        if st.button("🚨 Marcar para Ação Legal"):
            st.warning(f"{suspicious_filtrado} anúncios suspeitos marcados para ação legal!")
    
    with col3:
        if st.button("📧 Notificar Vendedores"):
            vendedores_unicos = df_filtrado['seller_id'].nunique()
            st.info(f"Notificação enviada para {vendedores_unicos} vendedores únicos!")

else:
    st.warning("⚠️ Nenhum anúncio encontrado com os filtros aplicados. Tente ajustar os critérios de busca.")

# --- ANÁLISE DE PADRÕES ---
if total_filtrado > 5:  # Só mostrar se houver dados suficientes
    st.header("🔍 Análise de Padrões")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top Vendedores Suspeitos
        st.subheader("Top Vendedores Suspeitos (Filtrados)")
        top_sellers = df_filtrado.groupby('vendedor_nome').agg({
            'id_anuncio': 'count',
            'is_fraud_suspect_v2': 'sum',
            'score_de_suspeita': 'mean'
        }).rename(columns={
            'id_anuncio': 'total_anuncios',
            'is_fraud_suspect_v2': 'suspeitos',
            'score_de_suspeita': 'score_medio'
        }).sort_values('suspeitos', ascending=False).head(10)
        
        st.dataframe(top_sellers, width='stretch')
    
    with col2:
        # Análise de Flags
        st.subheader("Frequência de Flags (Filtrados)")
        if flags:
            flags_counts = df_filtrado[flags].sum().sort_values(ascending=False)
            fig_flags = px.bar(
                x=flags_counts.values,
                y=[f.replace('flag_', '').replace('_', ' ').title() for f in flags_counts.index],
                orientation='h',
                title="Flags Mais Comuns",
                color=flags_counts.values,
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig_flags, width='stretch', config={'displayModeBar': False})

# --- SIDEBAR ---
st.sidebar.success("🔬 Página de Investigação Ativa")
st.sidebar.info(f"""
**Filtros Aplicados:**
- Score: {score_min:.1f} - {score_max:.1f}
- Risco: {selected_risk}
- Comunidade: {comunidade_selecionada}
- Status: {status_selecionado}
- Preço: R$ {preco_range[0]:.0f} - R$ {preco_range[1]:.0f}
- Flags: {len(selected_flags)} selecionadas
""")

st.sidebar.metric("Resultados", f"{total_filtrado:,} anúncios", f"{suspicious_rate:.1f}% suspeitos")
