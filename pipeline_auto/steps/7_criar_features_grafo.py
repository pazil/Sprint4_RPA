#!/usr/bin/env python3
"""
SCRIPT 7: CRIAR FEATURES DE GRAFO COM SIMILARIDADE SEMÂNTICA
============================================================
Constrói o grafo de vendedores com 4 camadas de conexões e calcula 12 métricas de grafo.

CAMADAS DE CONEXÃO:
1. Mesmo produto de catálogo (peso: 5.0)
2. Vendedores alternativos (peso: 2.0)  
3. Imagens compartilhadas (peso: 1.0)
4. Similaridade semântica (peso: 0.5)

INPUT:
- data/script_6_grafo/dataset_final_para_modelo.csv (Script 6)
- data/script_5_imagens/hashes_imagens.csv (Script 5)

OUTPUT:
- data/script_7_grafo/dataset_final_com_grafo.csv (DATASET COMPLETO COM FEATURES DE GRAFO)
"""

import pandas as pd
import numpy as np
import os
import networkx as nx
from community import community_louvain
import ast  # Para converter strings de listas de forma segura

# --- CONFIGURAÇÃO ---
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))
from _config import *

# Usar os arquivos mais recentes de cada script
PATH_DATASET = SCRIPT_6_DIR / "dataset_final_para_modelo.csv"
PATH_HASHES = SCRIPT_5_DIR / "hashes_imagens.csv"
PATH_OUTPUT = SCRIPT_7_DIR / "dataset_final_com_grafo.csv"

# Criar diretório de saída se não existir
SCRIPT_7_DIR.mkdir(parents=True, exist_ok=True)

# Verificar se o arquivo existe, se não, procurar em script_6_target_merge
if not PATH_DATASET.exists():
    SCRIPT_6_TARGET_DIR = DATA_DIR / "script_6_target_merge"
    if SCRIPT_6_TARGET_DIR.exists():
        PATH_DATASET = max(SCRIPT_6_TARGET_DIR.glob("*.csv"), key=lambda x: x.stat().st_mtime)
        print(f"   📂 Usando arquivo de: {PATH_DATASET}")

def main():
    print("="*80)
    print("🕸️ SCRIPT 7: CRIAR FEATURES DE GRAFO COM SIMILARIDADE SEMÂNTICA")
    print("="*80)
    
    # 1. Carregar dados
    print("\n📂 CARREGANDO DADOS...")
    print("-"*80)
    
    df = pd.read_csv(PATH_DATASET)
    df_hashes = pd.read_csv(PATH_HASHES)
    
    print(f"   ✅ Dataset principal: {len(df)} produtos")
    print(f"   ✅ Hashes de imagens: {len(df_hashes)} imagens")
    
    # =============================================================================
    # 2. LIMPEZA DE DADOS (NAN E DUPLICATAS)
    # =============================================================================
    print(f"\n🧹 LIMPANDO DADOS (NAN E DUPLICATAS)...")
    print("-"*80)
    
    # Verificar e remover linhas sem seller_id
    seller_id_nulos = df['seller_id'].isna().sum()
    if seller_id_nulos > 0:
        print(f"   🚨 Removendo {seller_id_nulos} linhas sem seller_id")
        df = df.dropna(subset=['seller_id']).copy()
    
    # Converter seller_id para int64 para evitar overflow
    df['seller_id'] = df['seller_id'].astype('int64')
    
    # Verificar e remover duplicatas por id_anuncio
    num_duplicatas = df.duplicated(subset=['id_anuncio']).sum()
    if num_duplicatas > 0:
        print(f"   🚨 Removendo {num_duplicatas} anúncios duplicados")
        df = df.drop_duplicates(subset=['id_anuncio'], keep='first').copy()
    
    # Preencher valores nulos em campos importantes (apenas os necessários)
    if 'grafo_comunidade_id' in df.columns:
        df['grafo_comunidade_id'] = df['grafo_comunidade_id'].fillna(-1)
    if 'is_fraud_suspect_v2' in df.columns:
        df['is_fraud_suspect_v2'] = df['is_fraud_suspect_v2'].fillna(0)
    
    print(f"   ✅ Dataset limpo: {len(df)} produtos únicos")
    print(f"   ✅ Vendedores únicos: {df['seller_id'].nunique()}")
    
    # =============================================================================
    # 3. CALCULAR SIMILARIDADE SEMÂNTICA (TÍTULO, DESCRIÇÃO, REVIEWS)
    # =============================================================================
    print(f"\n🧠 CALCULANDO SIMILARIDADE SEMÂNTICA...")
    print("-"*80)
    
    import json
    from sklearn.metrics.pairwise import cosine_similarity
    
    # Verificar se temos as colunas de embedding separadas
    embedding_cols = ['embedding_titulo', 'embedding_descricao', 'embedding_reviews']
    available_embeddings = [col for col in embedding_cols if col in df.columns]
    
    if available_embeddings:
        print(f"   ✅ Colunas de embedding encontradas: {available_embeddings}")
        
        # Processar cada tipo de embedding separadamente
        similarity_matrices = {}
        SIMILARITY_THRESHOLD = 0.85
        
        for embedding_type in available_embeddings:
            print(f"   📐 Processando {embedding_type}...")
            
            # Extrair embeddings válidos (não nulos)
            valid_indices = df[embedding_type].notna()
            valid_df = df[valid_indices].copy()
            
            if len(valid_df) == 0:
                print(f"      ⚠️ Nenhum embedding válido para {embedding_type}")
                continue
            
            # Converter strings JSON para arrays NumPy
            embeddings_list = []
            for idx, row in valid_df.iterrows():
                try:
                    embedding = json.loads(row[embedding_type])
                    # Garantir que o embedding tem exatamente 1536 dimensões
                    if len(embedding) == 1536:
                        embeddings_list.append(embedding)
                    else:
                        # Se não tem 1536 dimensões, usar zeros
                        embeddings_list.append([0.0] * 1536)
                except (json.JSONDecodeError, TypeError):
                    # Se não conseguir fazer parse, usar zeros
                    embeddings_list.append([0.0] * 1536)
            
            # Verificar se todos os embeddings têm o mesmo tamanho
            if embeddings_list:
                embedding_lengths = [len(emb) for emb in embeddings_list]
                if len(set(embedding_lengths)) > 1:
                    print(f"      ⚠️ Embeddings com tamanhos diferentes: {set(embedding_lengths)}")
                    # Padronizar para 1536 dimensões
                    embeddings_list = [emb[:1536] + [0.0] * max(0, 1536 - len(emb)) for emb in embeddings_list]
            
            embeddings_matrix = np.array(embeddings_list)
            print(f"      ✅ Matriz de {embedding_type}: {embeddings_matrix.shape}")
            
            # Calcular similaridade de cosseno
            cosine_sim = cosine_similarity(embeddings_matrix)
            similarity_matrices[embedding_type] = {
                'matrix': cosine_sim,
                'indices': valid_df.index.tolist()
            }
            
            # Estatísticas
            similaridades_altas = (cosine_sim > SIMILARITY_THRESHOLD).sum()
            print(f"      📊 Pares com similaridade > {SIMILARITY_THRESHOLD:.0%}: {similaridades_altas}")
        
        print(f"   ✅ {len(similarity_matrices)} tipos de similaridade calculados")
    else:
        print(f"   ⚠️ Nenhuma coluna de embedding encontrada. Pulando similaridade semântica.")
        similarity_matrices = {}
        SIMILARITY_THRESHOLD = 0.85
    
    # =============================================================================
    # 4. Construir o grafo (VERSÃO MELHORADA COM MÚLTIPLAS ARESTAS)
    # =============================================================================
    print("\n🔨 CONSTRUINDO GRAFO DE VENDEDORES...")
    print("-"*80)

    G = nx.Graph()

    # --- 4.1 Adicionar nós (vendedores) ---
    print("   📍 Adicionando nós (vendedores)...")
    vendedores_unicos = df['seller_id'].unique()
    
    for seller_id in vendedores_unicos:
        # Pegar produtos desse vendedor
        produtos_vendedor = df[df['seller_id'] == seller_id]
        
        if len(produtos_vendedor) == 0:
            continue
        
        # Atributos do vendedor
        G.add_node(
            seller_id,
            tipo='vendedor',
            total_transacoes=produtos_vendedor['vendedor_total_transacoes'].iloc[0],
            reputacao=produtos_vendedor['vendedor_reputacao_num'].iloc[0],
            e_loja_oficial=produtos_vendedor['e_loja_oficial'].iloc[0],
            num_produtos=len(produtos_vendedor),
            num_produtos_suspeitos=produtos_vendedor['is_fraud_suspect_v2'].sum(),
            taxa_suspeita=produtos_vendedor['is_fraud_suspect_v2'].mean()
        )
    print(f"   ✅ {len(G.nodes)} vendedores adicionados como nós.")

    # --- 4.2 Adicionar arestas (conexões) em camadas ---
    print("\n   🔗 Adicionando conexões em camadas (arestas)...")

    # --- CAMADA 1: MESMO PRODUTO DE CATÁLOGO (Conexão mais forte) ---
    print("      - Camada 1: Vendedores do mesmo produto de catálogo...")
    conexoes_catalogo = 0
    df_cat = df.dropna(subset=['catalog_product_id'])
    for _, grupo in df_cat.groupby('catalog_product_id'):
        vendedores = grupo['seller_id'].unique()
        if len(vendedores) > 1:
            for i, v1 in enumerate(vendedores):
                for v2 in vendedores[i+1:]:
                    if G.has_edge(v1, v2):
                        G[v1][v2]['weight'] += 5.0  # Aumenta o peso se já conectado
                    else:
                        G.add_edge(v1, v2, weight=5.0, tipo='mesmo_catalogo')
                        conexoes_catalogo += 1
    print(f"         -> {conexoes_catalogo} novas conexões criadas (peso: 5.0)")

    # --- CAMADA 2: VENDEDORES ALTERNATIVOS (Conexão forte) ---
    print("      - Camada 2: Vendedores listados como alternativas de compra...")
    conexoes_alt = 0
    df_alt = df.dropna(subset=['conexoes_vendedores_alt'])
    for _, row in df_alt.iterrows():
        vendedor_principal = row['seller_id']
        try:
            # Usar ast.literal_eval para converter string de lista para lista
            vendedores_alternativos = ast.literal_eval(row['conexoes_vendedores_alt'])
            if not isinstance(vendedores_alternativos, list): continue
                
            for vendedor_alt in vendedores_alternativos:
                # Garantir que o nó alternativo existe no grafo antes de conectar
                if G.has_node(vendedor_principal) and G.has_node(int(vendedor_alt)):
                    if G.has_edge(vendedor_principal, int(vendedor_alt)):
                        G[vendedor_principal][int(vendedor_alt)]['weight'] += 2.0
                    else:
                        G.add_edge(vendedor_principal, int(vendedor_alt), weight=2.0, tipo='alternativa_compra')
                        conexoes_alt += 1
        except (ValueError, SyntaxError):
            continue # Ignora se a string não for uma lista válida
    print(f"         -> {conexoes_alt} novas conexões criadas (peso: 2.0)")

    # --- CAMADA 3: IMAGENS COMPARTILHADAS (Conexão contextual) ---
    print("      - Camada 3: Vendedores que compartilham a mesma imagem...")
    conexoes_imagem = 0
    # Unir df_hashes com df para obter o seller_id para cada imagem
    df_hashes_com_vendedor = pd.merge(df_hashes, df[['id_anuncio', 'seller_id']], on='id_anuncio', how='inner')

    for _, grupo in df_hashes_com_vendedor.groupby('phash'):
        vendedores = grupo['seller_id'].unique()
        if len(vendedores) > 1:
            for i, v1 in enumerate(vendedores):
                for v2 in vendedores[i+1:]:
                    if G.has_edge(v1, v2):
                        G[v1][v2]['weight'] += 1.0
                    else:
                        G.add_edge(v1, v2, weight=1.0, tipo='imagem_compartilhada')
                        conexoes_imagem += 1
    print(f"         -> {conexoes_imagem} novas conexões criadas (peso: 1.0)")

    # --- CAMADA 4: CONEXÕES SEMÂNTICAS (Conexão baseada em similaridade) ---
    if similarity_matrices:
        print("      - Camada 4: Vendedores com produtos semanticamente similares...")
        conexoes_semanticas = 0
        
        # Processar cada tipo de similaridade
        for embedding_type, sim_data in similarity_matrices.items():
            print(f"         Processando similaridade de {embedding_type}...")
            cosine_sim = sim_data['matrix']
            indices = sim_data['indices']
            
            # Mapear índices do DataFrame para posições na matriz de similaridade
            idx_to_pos = {idx: pos for pos, idx in enumerate(indices)}
            
            conexoes_tipo = 0
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    if cosine_sim[i, j] > SIMILARITY_THRESHOLD:
                        # Obter os índices originais do DataFrame
                        idx1 = indices[i]
                        idx2 = indices[j]
                        
                        vendedor1 = df.loc[idx1, 'seller_id']
                        vendedor2 = df.loc[idx2, 'seller_id']
                        
                        # Não conectar um vendedor a ele mesmo
                        if vendedor1 != vendedor2 and G.has_node(vendedor1) and G.has_node(vendedor2):
                            peso = 0.5  # Peso base para similaridade semântica
                            
                            if G.has_edge(vendedor1, vendedor2):
                                G[vendedor1][vendedor2]['weight'] += peso
                            else:
                                G.add_edge(vendedor1, vendedor2, weight=peso, tipo=f'similaridade_{embedding_type}')
                                conexoes_semanticas += 1
                                conexoes_tipo += 1
            
            print(f"            -> {conexoes_tipo} conexões de {embedding_type}")
        
        print(f"         -> {conexoes_semanticas} novas conexões semânticas criadas (peso: 0.5)")
    else:
        print("      - Camada 4: Pulada (sem embeddings disponíveis)")

    # --- 4.3 Estatísticas Finais do Grafo ---
    print(f"\n📊 ESTATÍSTICAS FINAIS DO GRAFO CONSTRUÍDO:")
    print(f"   Nós (vendedores): {len(G.nodes)}")
    print(f"   Arestas (conexões): {len(G.edges)}")
    print(f"   Vendedores conectados: {len([n for n in G.nodes if G.degree(n) > 0])}")
    print(f"   Vendedores isolados: {len([n for n in G.nodes if G.degree(n) == 0])}")
    
    # Calcular peso médio das arestas
    if len(G.edges) > 0:
        pesos = [G[u][v]['weight'] for u, v in G.edges()]
        print(f"   Peso médio das conexões: {np.mean(pesos):.2f}")
        print(f"   Peso máximo das conexões: {np.max(pesos):.2f}")
        print(f"   Peso mínimo das conexões: {np.min(pesos):.2f}")
    
    # 5. Detectar comunidades
    print("\n🔍 DETECTANDO COMUNIDADES...")
    print("-"*80)
    
    # Criar subgrafo apenas com nós conectados
    G_conectado = G.subgraph([n for n in G.nodes if G.degree(n) > 0]).copy()
    
    if len(G_conectado.nodes) > 0:
        comunidades = community_louvain.best_partition(G_conectado)
        
        # Adicionar comunidade aos nós
        for node, comunidade_id in comunidades.items():
            G.nodes[node]['comunidade'] = comunidade_id
        
        # Nós isolados recebem comunidade -1
        for node in G.nodes:
            if 'comunidade' not in G.nodes[node]:
                G.nodes[node]['comunidade'] = -1
        
        print(f"   ✅ {len(set(comunidades.values()))} comunidades detectadas")
    else:
        print("   ⚠️ Nenhum vendedor conectado. Pulando detecção de comunidades.")
        for node in G.nodes:
            G.nodes[node]['comunidade'] = -1
    
    # 6. Extrair features básicas do grafo
    print("\n📊 EXTRAINDO FEATURES BÁSICAS DO GRAFO...")
    print("-"*80)
    
    grafo_features = []
    
    for seller_id in G.nodes:
        features = {
            'seller_id': seller_id,
            'grafo_num_conexoes': G.degree(seller_id),
            'grafo_comunidade_id': G.nodes[seller_id].get('comunidade', -1),
            'grafo_num_produtos': G.nodes[seller_id].get('num_produtos', 0),
            'grafo_num_suspeitos': G.nodes[seller_id].get('num_produtos_suspeitos', 0),
            'grafo_taxa_suspeita_vendedor': G.nodes[seller_id].get('taxa_suspeita', 0)
        }
        grafo_features.append(features)
    
    df_grafo_features = pd.DataFrame(grafo_features)
    print(f"   ✅ Features básicas extraídas: {len(df_grafo_features)} vendedores")
    
    # 7. Calcular features de comunidade
    print("\n📊 CALCULANDO FEATURES DE COMUNIDADE...")
    print("-"*80)
    
    comunidade_stats = df_grafo_features.groupby('grafo_comunidade_id').agg({
        'seller_id': 'count',  # Tamanho da comunidade
        'grafo_num_suspeitos': 'sum',  # Total de suspeitos na comunidade
        'grafo_num_produtos': 'sum',  # Total de produtos na comunidade
    }).rename(columns={
        'seller_id': 'grafo_tamanho_comunidade',
        'grafo_num_suspeitos': 'grafo_total_suspeitos_comunidade',
        'grafo_num_produtos': 'grafo_total_produtos_comunidade'
    })
    
    # Taxa de suspeita da comunidade
    comunidade_stats['grafo_taxa_suspeita_comunidade'] = (
        comunidade_stats['grafo_total_suspeitos_comunidade'] / 
        comunidade_stats['grafo_total_produtos_comunidade']
    ).fillna(0)
    
    # Merge com features do grafo
    df_grafo_features = df_grafo_features.merge(
        comunidade_stats, 
        on='grafo_comunidade_id', 
        how='left'
    )
    
    # Preencher NaN para vendedores isolados (comunidade -1)
    df_grafo_features['grafo_tamanho_comunidade'] = df_grafo_features['grafo_tamanho_comunidade'].fillna(0)
    df_grafo_features['grafo_total_suspeitos_comunidade'] = df_grafo_features['grafo_total_suspeitos_comunidade'].fillna(0)
    df_grafo_features['grafo_total_produtos_comunidade'] = df_grafo_features['grafo_total_produtos_comunidade'].fillna(0)
    df_grafo_features['grafo_taxa_suspeita_comunidade'] = df_grafo_features['grafo_taxa_suspeita_comunidade'].fillna(0)
    
    print(f"   ✅ Features de comunidade calculadas")
    
    # 8. Calcular features de vizinhança
    print("\n📊 CALCULANDO FEATURES DE VIZINHANÇA...")
    print("-"*80)
    
    df_vizinhanca = []
    
    for seller_id in G.nodes:
        vizinhos = list(G.neighbors(seller_id))
        
        if len(vizinhos) > 0:
            # Contar produtos suspeitos dos vizinhos
            vizinhos_suspeitos = sum([G.nodes[v].get('num_produtos_suspeitos', 0) for v in vizinhos])
            vizinhos_produtos_total = sum([G.nodes[v].get('num_produtos', 0) for v in vizinhos])
            taxa_suspeita_vizinhos = vizinhos_suspeitos / vizinhos_produtos_total if vizinhos_produtos_total > 0 else 0
            
            # Peso total e médio das conexões
            peso_total = sum([G[seller_id][v]['weight'] for v in vizinhos])
            
            df_vizinhanca.append({
                'seller_id': seller_id,
                'grafo_num_vizinhos': len(vizinhos),
                'grafo_vizinhos_suspeitos': vizinhos_suspeitos,
                'grafo_taxa_suspeita_vizinhos': taxa_suspeita_vizinhos,
                'grafo_peso_total_conexoes': peso_total,
                'grafo_peso_medio_conexoes': peso_total / len(vizinhos)
            })
        else:
            df_vizinhanca.append({
                'seller_id': seller_id,
                'grafo_num_vizinhos': 0,
                'grafo_vizinhos_suspeitos': 0,
                'grafo_taxa_suspeita_vizinhos': 0,
                'grafo_peso_total_conexoes': 0,
                'grafo_peso_medio_conexoes': 0
            })
    
    df_vizinhanca = pd.DataFrame(df_vizinhanca)
    df_grafo_features = df_grafo_features.merge(df_vizinhanca, on='seller_id', how='left')
    
    print(f"   ✅ Features de vizinhança calculadas")
    
    # 9. Calcular métricas de centralidade
    print("\n📊 CALCULANDO MÉTRICAS DE CENTRALIDADE...")
    print("-"*80)
    
    if len(G_conectado.nodes) > 0:
        print("   🔢 Calculando betweenness centrality...")
        betweenness = nx.betweenness_centrality(G_conectado)
        
        print("   🔢 Calculando closeness centrality...")
        closeness = nx.closeness_centrality(G_conectado)
        
        print("   🔢 Calculando PageRank...")
        pagerank = nx.pagerank(G_conectado)
        
        df_centralidade = []
        for seller_id in G.nodes:
            if seller_id in betweenness:
                df_centralidade.append({
                    'seller_id': seller_id,
                    'grafo_betweenness': betweenness[seller_id],
                    'grafo_closeness': closeness[seller_id],
                    'grafo_pagerank': pagerank[seller_id]
                })
            else:
                # Vendedor isolado
                df_centralidade.append({
                    'seller_id': seller_id,
                    'grafo_betweenness': 0,
                    'grafo_closeness': 0,
                    'grafo_pagerank': 0
                })
        
        df_centralidade = pd.DataFrame(df_centralidade)
        df_grafo_features = df_grafo_features.merge(df_centralidade, on='seller_id', how='left')
        
        print(f"   ✅ Métricas de centralidade calculadas")
    else:
        print("   ⚠️ Nenhum vendedor conectado. Usando valores padrão (0) para centralidade.")
        df_grafo_features['grafo_betweenness'] = 0
        df_grafo_features['grafo_closeness'] = 0
        df_grafo_features['grafo_pagerank'] = 0
    
    # 10. Fazer merge com dataset principal
    print("\n🔗 FAZENDO MERGE COM DATASET PRINCIPAL...")
    print("-"*80)
    
    # Merge por seller_id (vai replicar para todos os produtos do mesmo vendedor)
    df_final = df.merge(df_grafo_features, on='seller_id', how='left')
    
    # Preencher NaN para produtos sem features de grafo (se houver)
    grafo_cols = [col for col in df_final.columns if col.startswith('grafo_')]
    for col in grafo_cols:
        df_final[col] = df_final[col].fillna(0)
    
    print(f"   ✅ Merge realizado: {len(df_final)} produtos")
    print(f"   ✅ Total de colunas: {len(df_final.columns)}")
    
    # 11. Salvar dataset final
    print("\n💾 SALVANDO DATASET FINAL...")
    print("-"*80)
    
    df_final.to_csv(PATH_OUTPUT, index=False)
    
    print(f"   ✅ Salvo: {os.path.abspath(PATH_OUTPUT)}")
    print(f"   📊 Shape: ({len(df_final)}, {len(df_final.columns)})")
    
    # 10. Resumo final
    print("\n" + "="*80)
    print("📈 RESUMO FINAL")
    print("="*80)
    
    print(f"\n📦 DATASET FINAL:")
    print(f"   Total de produtos: {len(df_final)}")
    print(f"   Total de features: {len(df_final.columns)}")
    
    print(f"\n🕸️ FEATURES DE GRAFO CRIADAS (12 features):")
    grafo_features_list = [
        ('grafo_num_conexoes', 'Número de conexões do vendedor'),
        ('grafo_comunidade_id', 'ID da comunidade do vendedor'),
        ('grafo_tamanho_comunidade', 'Tamanho da comunidade'),
        ('grafo_taxa_suspeita_comunidade', 'Taxa de suspeita da comunidade'),
        ('grafo_num_vizinhos', 'Número de vizinhos diretos'),
        ('grafo_vizinhos_suspeitos', 'Número de produtos suspeitos dos vizinhos'),
        ('grafo_taxa_suspeita_vizinhos', 'Taxa de suspeita dos vizinhos'),
        ('grafo_peso_total_conexoes', 'Peso total das conexões'),
        ('grafo_peso_medio_conexoes', 'Peso médio das conexões'),
        ('grafo_betweenness', 'Centralidade de intermediação'),
        ('grafo_closeness', 'Centralidade de proximidade'),
        ('grafo_pagerank', 'Importância (PageRank)')
    ]
    
    for idx, (feature, descricao) in enumerate(grafo_features_list, 1):
        print(f"   {idx:2d}. {feature:<35} - {descricao}")
    
    # Estatísticas das features de grafo
    print(f"\n📊 ESTATÍSTICAS DAS FEATURES DE GRAFO:")
    print("-"*80)
    
    grafo_numeric_cols = [col for col in grafo_cols if df_final[col].dtype in ['int64', 'float64']]
    stats = df_final[grafo_numeric_cols].describe().round(3)
    print(stats.to_string())
    
    # Correlação com target
    print(f"\n🎯 CORRELAÇÃO COM is_fraud_suspect_v2:")
    print("-"*80)
    
    correlacoes = df_final[grafo_numeric_cols + ['is_fraud_suspect_v2']].corr()['is_fraud_suspect_v2'].sort_values(ascending=False)
    
    print("\nTop 10 features de grafo mais correlacionadas:")
    for idx, (feature, corr) in enumerate(correlacoes[1:11].items(), 1):
        sinal = "+" if corr >= 0 else ""
        print(f"   {idx:2d}. {feature:<35} | Correlação: {sinal}{corr:.4f}")
    
    print("\n" + "="*80)
    print("✅ SCRIPT 5 CONCLUÍDO COM SUCESSO!")
    print("="*80)
    
    print(f"\n📁 Próximo passo: Usar o modelo treinado com {PATH_OUTPUT}")
    print(f"   Total de features: {len(df_final.columns)} (incluindo 12 de grafo)")

if __name__ == "__main__":
    main()

