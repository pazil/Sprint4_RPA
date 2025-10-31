# 1_Dashboard_Geral.py - Página Principal do Dashboard HP Anti-Fraude

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import load_data, load_ml_scores, get_risk_categories, get_seller_metrics, get_community_metrics, get_logo_path

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="HP Anti-Fraude | Dashboard Geral",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CARREGAMENTO DOS DADOS ---
PATH_DATASET = "data/final_grafo/dataset_final_com_grafo.csv"
df = load_data(PATH_DATASET)
df_with_scores = load_ml_scores()

# Adicionar categorias de risco
df = get_risk_categories(df)

# --- TÍTULO E INTRODUÇÃO ---
st.title("🛡️ Dashboard Estratégico Anti-Fraude HP")
st.markdown("""
**Visão geral do ecossistema de anúncios e detecção de atividades suspeitas no Mercado Livre.**
Este dashboard apresenta análises em tempo real para identificação proativa de fraudes em cartuchos HP.
""")

if df is None:
    st.stop()

# --- MÉTRICAS DE VOLUME E ABRANGÊNCIA ---
st.header("📊 Panorama Geral")

# Calcular métricas principais
total_anuncios = len(df)
anuncios_suspeitos = df['is_fraud_suspect_v2'].sum()
vendedores_unicos = df['seller_id'].nunique()
vendedores_suspeitos = df[df['is_fraud_suspect_v2'] == 1]['seller_id'].nunique()

# Volume financeiro em risco
if 'preco_atual' in df.columns:
    volume_financeiro_risco = df[df['is_fraud_suspect_v2'] == 1]['preco_atual'].sum()
else:
    volume_financeiro_risco = 0

# Taxa de detecção
taxa_deteccao = (anuncios_suspeitos / total_anuncios * 100) if total_anuncios > 0 else 0

# Layout das métricas
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="Anúncios Analisados", 
        value=f"{total_anuncios:,}",
        delta=f"Base total"
    )

with col2:
    st.metric(
        label="Anúncios Suspeitos", 
        value=f"{anuncios_suspeitos:,}",
        delta=f"{taxa_deteccao:.1f}% do total"
    )

with col3:
    st.metric(
        label="Vendedores Suspeitos", 
        value=f"{vendedores_suspeitos:,}",
        delta=f"{vendedores_suspeitos/vendedores_unicos*100:.1f}% dos vendedores"
    )

with col4:
    st.metric(
        label="Valor em Risco", 
        value=f"R$ {volume_financeiro_risco:,.0f}",
        delta=f"R$ {volume_financeiro_risco/total_anuncios:,.0f} por anúncio"
    )

with col5:
    st.metric(
        label="Taxa de Detecção", 
        value=f"{taxa_deteccao:.1f}%",
        delta="Eficiência do sistema"
    )

# --- ANÁLISE DE RISCOS POR CATEGORIA ---
st.header("🎯 Análise de Riscos por Categoria")

col1, col2 = st.columns(2)

with col1:
    # Distribuição por categoria de risco
    risk_dist = df['risk_category'].value_counts()
    
    fig_risk = px.pie(
        values=risk_dist.values, 
        names=risk_dist.index,
        title="Distribuição por Nível de Risco",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_risk.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_risk, use_container_width=True, config={'displayModeBar': False})

with col2:
    # Score médio por categoria
    score_by_risk = df.groupby('risk_category', observed=True)['score_de_suspeita'].mean().sort_values(ascending=False)
    
    fig_score = px.bar(
        x=score_by_risk.index, 
        y=score_by_risk.values,
        title="Score Médio por Categoria de Risco",
        labels={'x': 'Categoria de Risco', 'y': 'Score Médio'},
        color=score_by_risk.values,
        color_continuous_scale='Reds'
    )
    fig_score.update_layout(showlegend=False)
    st.plotly_chart(fig_score, use_container_width=True, config={'displayModeBar': False})

# --- ANÁLISE DOS SINAIS DE FRAUDE ---
st.header("🔍 Análise dos Sinais de Fraude")

col1, col2 = st.columns(2)

with col1:
    # Distribuição do Score de Suspeita
    st.subheader("Distribuição do Score de Suspeita")
    fig_hist = px.histogram(
        df, 
        x="score_de_suspeita", 
        nbins=20, 
        title="Frequência dos Scores de Risco",
        color_discrete_sequence=['#FF6B35']
    )
    fig_hist.update_layout(
        yaxis_title="Nº de Anúncios",
        xaxis_title="Score de Suspeita"
    )
    fig_hist.add_vline(x=3, line_dash="dash", line_color="red", annotation_text="Threshold")
    st.plotly_chart(fig_hist, use_container_width=True, config={'displayModeBar': False})

with col2:
    # Fatores de Risco Mais Comuns
    st.subheader("Fatores de Risco Mais Comuns")
    flags = [col for col in df.columns if col.startswith('flag_')]
    if flags:
        flags_counts = df[flags].sum().sort_values(ascending=False)
        df_flags = pd.DataFrame(flags_counts, columns=['Ocorrências']).reset_index().rename(columns={'index': 'Fator de Risco'})
        
        fig_bar = px.bar(
            df_flags.head(7), 
            x='Ocorrências', 
            y='Fator de Risco', 
            orientation='h', 
            title="Top 7 Sinais de Alerta",
            color='Ocorrências',
            color_continuous_scale='Reds'
        )
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("Flags de fraude não encontradas no dataset atual.")

# --- ANÁLISE DE PREÇOS ---
if 'diferenca_preco_perc' in df.columns and 'preco_atual' in df.columns:
    st.header("💰 Análise de Preços e Suspeita")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Relação entre Preço e Suspeita
        st.subheader("Relação entre Preço e Suspeita de Fraude")
        fig_scatter = px.scatter(
            df, 
            x='diferenca_preco_perc', 
            y='score_de_suspeita',
            color=df['is_fraud_suspect_v2'].map({0: 'Legítimo', 1: 'Suspeito'}),
            color_discrete_map={'Legítimo': 'blue', 'Suspeito': 'red'},
            hover_data=['vendedor_nome', 'preco_atual'],
            title="Score de Suspeita vs. Desconto sobre o Preço Sugerido"
        )
        fig_scatter.update_layout(
            xaxis_title="Diferença Percentual de Preço",
            yaxis_title="Score de Suspeita",
            xaxis_tickformat=".0%"
        )
        st.plotly_chart(fig_scatter, use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        # Distribuição de Preços por Status
        st.subheader("Distribuição de Preços por Status")
        fig_box = px.box(
            df, 
            x='is_fraud_suspect_v2', 
            y='preco_atual',
            color='is_fraud_suspect_v2',
            color_discrete_map={0: 'blue', 1: 'red'},
            title="Distribuição de Preços: Legítimo vs Suspeito",
            labels={'is_fraud_suspect_v2': 'Status', 'preco_atual': 'Preço (R$)'}
        )
        fig_box.update_layout(showlegend=False)
        st.plotly_chart(fig_box, use_container_width=True, config={'displayModeBar': False})

# --- ANÁLISE DE VENDEDORES ---
st.header("👥 Análise de Vendedores")

# Top vendedores suspeitos
seller_metrics = get_seller_metrics(df)
top_sellers = seller_metrics.head(10)

st.subheader("Top 10 Vendedores com Mais Anúncios Suspeitos")
st.dataframe(
    top_sellers[['vendedor_nome', 'total_anuncios', 'anuncios_suspeitos', 'taxa_suspeita', 'score_medio', 'status']],
    use_container_width=True,
    column_config={
        "vendedor_nome": "Vendedor",
        "total_anuncios": "Total Anúncios",
        "anuncios_suspeitos": "Anúncios Suspeitos",
        "taxa_suspeita": st.column_config.ProgressColumn("Taxa Suspeita", format="%.1f%%", min_value=0, max_value=100),
        "score_medio": st.column_config.NumberColumn("Score Médio", format="%.2f"),
        "status": "Status"
    }
)

# --- ANÁLISE COM MACHINE LEARNING (se disponível) ---
if df_with_scores is not None:
    st.header("🤖 Análise com Machine Learning & Score Híbrido")
    
    # Verificar se a coluna score_hibrido existe
    has_hybrid_score = 'score_hibrido' in df_with_scores.columns
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribuição dos Scores ML")
        fig_ml_hist = px.histogram(
            df_with_scores, 
            x='ml_score', 
            nbins=30,
            title="Distribuição do ML Score",
            color_discrete_sequence=['#2E8B57']
        )
        fig_ml_hist.add_vline(x=0.5, line_dash="dash", line_color="red", annotation_text="Threshold ML")
        st.plotly_chart(fig_ml_hist, use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        if has_hybrid_score:
            st.subheader("Distribuição do Score Híbrido")
            fig_hybrid_hist = px.histogram(
                df_with_scores, 
                x='score_hibrido', 
                nbins=30,
                title="Distribuição do Score Híbrido (Heurística + ML)",
                color_discrete_sequence=['#FF6B35']
            )
            fig_hybrid_hist.add_vline(x=df_with_scores['score_hibrido'].median(), line_dash="dash", line_color="blue", annotation_text="Mediana")
            st.plotly_chart(fig_hybrid_hist, use_container_width=True, config={'displayModeBar': False})
        else:
            st.subheader("ML Score vs Heurística")
            fig_scatter = px.scatter(
                df_with_scores, 
                x='score_de_suspeita', 
                y='ml_score',
                color='is_fraud_suspect_v2',
                color_discrete_map={0: 'blue', 1: 'red'},
                title="Heurística vs ML Score",
                labels={'score_de_suspeita': 'Score Heurística', 'ml_score': 'ML Score'}
            )
            fig_scatter.add_hline(y=0.5, line_dash="dash", line_color="red")
            fig_scatter.add_vline(x=3, line_dash="dash", line_color="blue")
            st.plotly_chart(fig_scatter, use_container_width=True, config={'displayModeBar': False})
    
    # Nova seção: Comparação dos 3 scores
    if has_hybrid_score:
        st.subheader("📊 Comparação: Heurística vs ML vs Híbrido")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            # Scatter plot: Heurística vs ML Score
            fig_comparison = px.scatter(
                df_with_scores, 
                x='score_de_suspeita', 
                y='ml_score',
                color='is_fraud_suspect_v2',
                color_discrete_map={0: 'blue', 1: 'red'},
                title="Heurística vs ML Score",
                labels={'score_de_suspeita': 'Score Heurística', 'ml_score': 'ML Score'},
                hover_data=['score_hibrido']
            )
            fig_comparison.add_hline(y=0.5, line_dash="dash", line_color="red", annotation_text="Threshold ML")
            fig_comparison.add_vline(x=3, line_dash="dash", line_color="blue", annotation_text="Threshold Heurística")
            st.plotly_chart(fig_comparison, use_container_width=True, config={'displayModeBar': False})
        
        with col_b:
            # Scatter plot: Score Híbrido vs Heurística
            fig_hybrid_comp = px.scatter(
                df_with_scores, 
                x='score_de_suspeita', 
                y='score_hibrido',
                color='is_fraud_suspect_v2',
                color_discrete_map={0: 'green', 1: 'orange'},
                title="Score Híbrido vs Heurística",
                labels={'score_de_suspeita': 'Score Heurística', 'score_hibrido': 'Score Híbrido'},
                hover_data=['ml_score']
            )
            fig_hybrid_comp.add_vline(x=3, line_dash="dash", line_color="blue", annotation_text="Threshold Heurística")
            st.plotly_chart(fig_hybrid_comp, use_container_width=True, config={'displayModeBar': False})
        
        # Estatísticas dos scores
        st.subheader("📈 Estatísticas Comparativas")
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        
        with col_stat1:
            st.metric(
                "Média Score Heurística", 
                f"{df_with_scores['score_de_suspeita'].mean():.2f}",
                f"Desvio: {df_with_scores['score_de_suspeita'].std():.2f}"
            )
        
        with col_stat2:
            st.metric(
                "Média ML Score", 
                f"{df_with_scores['ml_score'].mean():.3f}",
                f"Desvio: {df_with_scores['ml_score'].std():.3f}"
            )
        
        with col_stat3:
            st.metric(
                "Média Score Híbrido", 
                f"{df_with_scores['score_hibrido'].mean():.3f}",
                f"Desvio: {df_with_scores['score_hibrido'].std():.3f}"
            )
        
        # Tabela com top anúncios por score híbrido
        st.subheader("🎯 Top 20 Anúncios por Score Híbrido")
        top_hybrid = df_with_scores.nlargest(20, 'score_hibrido')[
            ['id_anuncio', 'vendedor_nome', 'score_de_suspeita', 'ml_score', 'score_hibrido', 'is_fraud_suspect_v2', 'preco_atual', 'link_anuncio']
        ].copy()
        
        # Adicionar coluna de classificação
        top_hybrid['classificacao'] = top_hybrid['is_fraud_suspect_v2'].map({0: 'Legítimo', 1: 'Suspeito'})
        
        st.dataframe(
            top_hybrid[['id_anuncio', 'vendedor_nome', 'score_de_suspeita', 'ml_score', 'score_hibrido', 'classificacao', 'preco_atual', 'link_anuncio']],
            use_container_width=True,
            column_config={
                "id_anuncio": "ID Anúncio",
                "vendedor_nome": "Vendedor",
                "score_de_suspeita": st.column_config.NumberColumn("Score Heurística", format="%.2f"),
                "ml_score": st.column_config.NumberColumn("ML Score", format="%.4f"),
                "score_hibrido": st.column_config.NumberColumn("Score Híbrido", format="%.4f", help="Combinação ponderada de Heurística + ML"),
                "classificacao": "Classificação",
                "preco_atual": st.column_config.NumberColumn("Preço (R$)", format="R$ %.2f"),
                "link_anuncio": st.column_config.LinkColumn("Link", display_text="Abrir", width="small")
            },
            hide_index=True,
            height=400
        )
        
        # Info sobre o cálculo do score híbrido
        with st.expander("ℹ️ Como é calculado o Score Híbrido?"):
            st.markdown("""
            **Score Híbrido** é uma combinação ponderada do Score Heurístico e do ML Score:
            
            - **Score Heurístico**: Baseado em regras de negócio e flags de fraude (50%)
            - **ML Score**: Predição do modelo de Machine Learning (50%)
            
            Fórmula:
            ```
            score_hibrido = (score_de_suspeita_normalizado * 0.5) + (ml_score * 0.5)
            ```
            
            Onde:
            - `score_de_suspeita_normalizado` = score_de_suspeita / 10 (normalizado para 0-1)
            - `ml_score` = probabilidade do modelo (já está em 0-1)
            
            **Vantagens do Score Híbrido:**
            - Combina conhecimento especialista (heurística) com aprendizado de padrões (ML)
            - Reduz falsos positivos e falsos negativos
            - Mais robusto que usar apenas um método
            """)
        
        # Seção de Thresholds Configuráveis
        st.subheader("⚙️ Configuração de Thresholds")
        col_thresh1, col_thresh2, col_thresh3 = st.columns(3)
        
        with col_thresh1:
            threshold_heuristica = st.slider(
                "Threshold Heurística:",
                min_value=0.0,
                max_value=10.0,
                value=3.0,
                step=0.5,
                help="Score mínimo para considerar suspeito via heurística"
            )
        
        with col_thresh2:
            threshold_ml = st.slider(
                "Threshold ML:",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.05,
                help="Probabilidade mínima para considerar suspeito via ML"
            )
        
        with col_thresh3:
            threshold_hibrido = st.slider(
                "Threshold Híbrido:",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.05,
                help="Score híbrido mínimo para considerar suspeito"
            )
        
        # Aplicar thresholds aos gráficos
        st.subheader("📊 Análise com Thresholds Configurados")
        
        col_vis1, col_vis2 = st.columns(2)
        
        with col_vis1:
            # Gráfico com thresholds aplicados
            fig_thresholds = px.scatter(
                df_with_scores, 
                x='score_de_suspeita', 
                y='ml_score',
                color='is_fraud_suspect_v2',
                color_discrete_map={0: 'blue', 1: 'red'},
                title=f"Análise com Thresholds (H:{threshold_heuristica}, ML:{threshold_ml})",
                labels={'score_de_suspeita': 'Score Heurística', 'ml_score': 'ML Score'}
            )
            fig_thresholds.add_hline(y=threshold_ml, line_dash="dash", line_color="red", annotation_text=f"ML: {threshold_ml}")
            fig_thresholds.add_vline(x=threshold_heuristica, line_dash="dash", line_color="blue", annotation_text=f"Heurística: {threshold_heuristica}")
            st.plotly_chart(fig_thresholds, use_container_width=True, config={'displayModeBar': False})
        
        with col_vis2:
            # Distribuição do score híbrido com threshold
            fig_hybrid_thresh = px.histogram(
                df_with_scores, 
                x='score_hibrido', 
                nbins=30,
                title=f"Distribuição Score Híbrido (Threshold: {threshold_hibrido})",
                color_discrete_sequence=['#FF6B35']
            )
            fig_hybrid_thresh.add_vline(x=threshold_hibrido, line_dash="dash", line_color="red", annotation_text=f"Threshold: {threshold_hibrido}")
            st.plotly_chart(fig_hybrid_thresh, use_container_width=True, config={'displayModeBar': False})
        
        # Estatísticas com thresholds aplicados
        anuncios_heuristica = (df_with_scores['score_de_suspeita'] >= threshold_heuristica).sum()
        anuncios_ml = (df_with_scores['ml_score'] >= threshold_ml).sum()
        anuncios_hibrido = (df_with_scores['score_hibrido'] >= threshold_hibrido).sum()
        
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        with col_stat1:
            st.metric("Anúncios Heurística", f"{anuncios_heuristica}", f"{anuncios_heuristica/len(df_with_scores)*100:.1f}%")
        with col_stat2:
            st.metric("Anúncios ML", f"{anuncios_ml}", f"{anuncios_ml/len(df_with_scores)*100:.1f}%")
        with col_stat3:
            st.metric("Anúncios Híbrido", f"{anuncios_hibrido}", f"{anuncios_hibrido/len(df_with_scores)*100:.1f}%")
        
        # Explicação do Score Heurístico
        with st.expander("🔍 Como é calculado o Score Heurístico?"):
            st.markdown("""
            **Score Heurístico** é baseado em regras de negócio e flags de fraude:
            
            **Flags de Fraude (peso 1.0 cada):**
            - `flag_fraude_instantanea`: Detecção imediata de fraude
            - `flag_preco_muito_baixo`: Preço suspeitamente baixo
            - `flag_vendedor_novo`: Vendedor com pouca experiência
            - `flag_imagem_muito_reutilizada`: Reutilização excessiva de imagens
            - `flag_reputacao_muito_ruim`: Reputação muito baixa
            - `flag_reviews_muito_negativas`: Reviews muito negativas
            - `flag_loja_oficial_suspeita`: Loja oficial com comportamento suspeito
            
            **Flags de Preço (peso 0.5 cada):**
            - `flag_preco_medio_baixo`: Preço médio-baixo
            - `flag_preco_ligeiramente_baixo`: Preço ligeiramente baixo
            
            **Flags de Reputação (peso 0.3 cada):**
            - `flag_reputacao_ruim`: Reputação ruim
            - `flag_reviews_negativas`: Reviews negativas
            
            **Flags de Imagem (peso 0.2 cada):**
            - `flag_imagem_reutilizada`: Reutilização moderada de imagens
            
            **Fórmula:**
            ```
            score_de_suspeita = Σ(flag_fraude * 1.0) + Σ(flag_preco * 0.5) + 
                               Σ(flag_reputacao * 0.3) + Σ(flag_imagem * 0.2)
            ```
            
            **Vantagens:**
            - Baseado em conhecimento especialista
            - Interpretável e explicável
            - Captura padrões conhecidos de fraude
            """)
        
        # Feature Importance do ML
        with st.expander("🤖 Feature Importance do Modelo ML (sem preço)"):
            try:
                # Carregar feature importance
                feature_importance = pd.read_csv("data/features/feature_importance_ridge_classifier.csv")
                
                # Top 15 features mais importantes (por valor absoluto)
                top_features = feature_importance.head(15)
                
                # Criar gráfico com valores positivos e negativos
                fig_importance = px.bar(
                    top_features,
                    x='Coefficient',
                    y='Feature',
                    orientation='h',
                    title="Top 15 Features Mais Importantes (Ridge Classifier)",
                    color='Coefficient',
                    color_continuous_scale='RdBu_r',  # Escala que vai do vermelho ao azul
                    range_color=[-max(abs(top_features['Coefficient'])), max(abs(top_features['Coefficient']))]
                )
                fig_importance.update_layout(
                    yaxis={'categoryorder':'total ascending'},
                    xaxis_title="Coeficiente (Positivo = Aumenta Fraude, Negativo = Diminui Fraude)"
                )
                # Adicionar linha vertical em x=0
                fig_importance.add_vline(x=0, line_dash="dash", line_color="black", annotation_text="Neutro")
                st.plotly_chart(fig_importance, use_container_width=True, config={'displayModeBar': False})
                
                # Tabela com valores exatos dos coeficientes
                st.subheader("📊 Valores Exatos dos Coeficientes")
                top_features_display = top_features[['Feature', 'Coefficient', 'Abs_Coefficient']].copy()
                top_features_display['Efeito'] = top_features_display['Coefficient'].apply(
                    lambda x: '🔴 Aumenta Fraude' if x > 0 else '🔵 Diminui Fraude' if x < 0 else '⚪ Neutro'
                )
                top_features_display['Coeficiente'] = top_features_display['Coefficient'].round(4)
                top_features_display['Importância'] = top_features_display['Abs_Coefficient'].round(4)
                
                st.dataframe(
                    top_features_display[['Feature', 'Coeficiente', 'Efeito', 'Importância']],
                    use_container_width=True,
                    hide_index=True
                )
                
                st.markdown("""
                **Interpretação dos Coeficientes:**
                - **🔴 Valores Positivos**: Aumentam a probabilidade de fraude
                - **🔵 Valores Negativos**: Diminuem a probabilidade de fraude
                - **Importância**: Valor absoluto do coeficiente (quanto maior, mais importante)
                
                **Análise das Top Features:**
                - **flag_fraude_instantanea**: Flag de detecção imediata (maior impacto positivo)
                - **grafo_taxa_suspeita_vendedor**: Taxa de suspeita do vendedor no grafo
                - **grafo_pagerank**: Centralidade do vendedor na rede (pode ser negativo se vendedores centrais são confiáveis)
                - **grafo_peso_medio_conexoes**: Peso médio das conexões
                - **grafo_closeness**: Proximidade na rede de vendedores
                """)
                
            except FileNotFoundError:
                st.warning("Arquivo de feature importance não encontrado.")
        
        # Explicação do Grafo
        with st.expander("🕸️ Como foi construído o Grafo de Fraude?"):
            st.markdown("""
            ### **Construção do Grafo de Vendedores:**
            
            Para entender as relações ocultas entre os vendedores, construímos uma rede social (grafo) que nos permite aplicar análises de rede avançadas.
            
            **1. Nós (Vendedores):**
            - Cada vendedor (`seller_id`) é um ponto (nó) no nosso mapa da rede
            - Cada nó carrega atributos importantes, como sua reputação, volume de vendas e o `score_de_suspeita` que calculamos anteriormente
            
            **2. Arestas (Conexões Ponderadas):**
            - As conexões entre os vendedores são criadas com base em evidências concretas, e cada tipo de evidência tem um peso diferente que reflete a força do laço:
              - **Conexão Forte (Peso 5.0):** Vendedores que anunciam o mesmo produto de catálogo oficial (`catalog_product_id`)
              - **Conexão Média (Peso 2.0):** Vendedores que a plataforma sugere como alternativas de compra
              - **Conexão Contextual (Peso 1.0):** Vendedores que usam a mesma imagem de produto
              - **Conexão Semântica (Peso 0.5):** Vendedores cujos textos de anúncio são muito similares em significado
            
            **3. Algoritmos Utilizados e Features Geradas:**
            
            Uma vez que o mapa da rede está construído, aplicamos algoritmos consagrados da teoria dos grafos para extrair inteligência:
            
            *   **Detecção de Comunidades (Método de Louvain):** Este algoritmo identifica automaticamente "bairros" ou "panelinhas" de vendedores que estão mais conectados entre si do que com o resto da rede. O resultado são as features:
                - `grafo_comunidade_id`: O ID do "bairro" do vendedor
                - `grafo_taxa_suspeita_comunidade`: A "toxicidade" do bairro, ou seja, a porcentagem de produtos suspeitos dentro daquela comunidade
            
            *   **Análise de Centralidade (Identificando Atores Chave):** Usamos diferentes métricas para medir a importância de um vendedor na rede:
                - **`grafo_pagerank`:** O famoso algoritmo do Google, aqui adaptado para medir a **influência** de um vendedor. Um vendedor é influente se ele está conectado a outros vendedores que também são influentes. Ajuda a encontrar os "centros gravitacionais" da rede
                - **`grafo_betweenness`:** Mede a importância de um vendedor como uma **"ponte"** entre diferentes grupos. Vendedores com `betweenness` alta podem ser distribuidores que conectam diferentes células de fraude
                - **`grafo_closeness`:** Mede a **proximidade** de um vendedor a todos os outros. Um valor alto indica que o vendedor pode espalhar informações (ou produtos fraudulentos) rapidamente pela rede
            
            **4. Lógica de Detecção:**
            
            - O sistema sinaliza vendedores que, mesmo parecendo legítimos individualmente, pertencem a comunidades com alta taxa de suspeita
            - Ele prioriza a investigação de vendedores com alta centralidade (alto PageRank ou Betweenness) que também exibem comportamento suspeito
            - Os padrões revelados pelo grafo nos permitem identificar operações coordenadas que seriam invisíveis em uma análise anúncio por anúncio
            
            **Vantagens:**
            
            - Detecta fraudes coordenadas e em rede
            - Identifica os vendedores "chefes" ou "distribuidores" de uma operação
            - Complementa a análise individual com o poderoso contexto da rede social do vendedor
            """)

# --- RESUMO EXECUTIVO ---
st.header("📋 Resumo Executivo")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Anúncios de Alto Risco", f"{(df['risk_category'] == 'Crítico').sum()}", "Crítico")
    st.metric("Anúncios de Risco Alto", f"{(df['risk_category'] == 'Alto').sum()}", "Alto")

with col2:
    st.metric("Vendedores com 100% Suspeitos", f"{(seller_metrics['taxa_suspeita'] == 100).sum()}", "Crítico")
    st.metric("Vendedores com >50% Suspeitos", f"{(seller_metrics['taxa_suspeita'] > 50).sum()}", "Alto")

with col3:
    if 'preco_atual' in df.columns:
        preco_medio_suspeitos = df[df['is_fraud_suspect_v2'] == 1]['preco_atual'].mean()
        preco_medio_legitimos = df[df['is_fraud_suspect_v2'] == 0]['preco_atual'].mean()
        st.metric("Preço Médio Suspeitos", f"R$ {preco_medio_suspeitos:.0f}")
        st.metric("Preço Médio Legítimos", f"R$ {preco_medio_legitimos:.0f}")

# --- SIDEBAR ---
# Logo HP no topo da sidebar (acima das abas de navegação) - Centralizado
col1, col2, col3 = st.sidebar.columns([1, 2, 1])
with col2:
    st.image(get_logo_path(), width=150)

st.sidebar.success("🎯 Você está na página Dashboard Geral")
st.sidebar.info("""
**Navegação:**
- 📊 Dashboard Geral (atual)
- 🔬 Investigação de Anúncios
- 👥 Análise de Vendedores
- 🕸️ Rede de Fraude
- 🔍 Extrair e Analisar Anúncio
""")

st.sidebar.metric("Última Atualização", "Agora", "Tempo real")
