# utils.py - Funções compartilhadas para o dashboard multi-página

import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path

# Determinar o diretório base do projeto (Sprint4RPA/analise_streamlit)
BASE_DIR = Path(__file__).resolve().parent

def resolve_data_path(relative_path: str) -> Path:
    """
    Resolve caminhos relativos para caminhos absolutos baseados na localização do utils.py
    Isso garante que os caminhos funcionem independentemente do diretório de trabalho do Streamlit
    """
    return BASE_DIR / relative_path

def get_logo_path() -> str:
    """
    Retorna o caminho absoluto do logo HP
    """
    logo_path = BASE_DIR / "logo" / "480px-HP_logo_2012.svg.png"
    return str(logo_path)

@st.cache_data
def load_data(path):
    """Carrega e processa os dados com cache para performance"""
    try:
        # Resolver caminho absoluto se for relativo
        path_obj = Path(path)
        if not path_obj.is_absolute():
            path_obj = resolve_data_path(path)
        
        # Converter para string para pandas
        path_str = str(path_obj)
        
        # Verificar se o arquivo existe antes de tentar ler
        if not path_obj.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {path_str}")
        
        df = pd.read_csv(path_str)
        df.drop_duplicates(subset=['id_anuncio'], keep='first', inplace=True)
        df.dropna(subset=['seller_id'], inplace=True)
        df['seller_id'] = df['seller_id'].astype(int)
        
        # Filtrar produtos usados/seminovos se a coluna existir
        if 'usado_seminovo' in df.columns:
            df = df[df['usado_seminovo'] != True].copy()
        
        return df
    except FileNotFoundError as e:
        path_resolvido = resolve_data_path(path) if not Path(path).is_absolute() else Path(path)
        st.warning(f"⚠️ Dataset não encontrado em '{path}'")
        st.info(f"💡 Caminho resolvido: {path_resolvido.absolute()}")
        if not path_resolvido.exists():
            st.error(f"❌ O arquivo realmente não existe em: {path_resolvido.absolute()}")
        st.info("📊 Carregando dados de exemplo...")
        return create_sample_data()
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {str(e)}")
        return create_sample_data()

@st.cache_data
def create_sample_data():
    """Cria dados de exemplo para demonstração"""
    np.random.seed(42)
    n_samples = 200
    
    df = pd.DataFrame({
        'id_anuncio': [f'MLB{i:06d}' for i in range(1, n_samples + 1)],
        'seller_id': np.random.randint(1, 30, n_samples),
        'vendedor_nome': [f'Vendedor_{i}' for i in np.random.randint(1, 30, n_samples)],
        'score_de_suspeita': np.random.uniform(0, 10, n_samples),
        'is_fraud_suspect_v2': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
        'preco_atual': np.random.uniform(50, 500, n_samples),
        'preco_sugerido_hp': np.random.uniform(100, 600, n_samples),
        'diferenca_preco_perc': np.random.uniform(-0.5, 0.2, n_samples),
        'vendedor_total_transacoes': np.random.randint(10, 1000, n_samples),
        'grafo_comunidade_id': np.random.randint(1, 15, n_samples),
        'grafo_taxa_suspeita_comunidade': np.random.uniform(0, 1, n_samples),
        'power_seller_status': np.random.choice(['Bronze', 'Silver', 'Gold', 'Platinum'], n_samples, p=[0.4, 0.3, 0.2, 0.1]),
        'link_anuncio': [f'https://produto.mercadolivre.com.br/MLB{i:06d}' for i in range(1, n_samples + 1)],
        'flag_fraude_instantanea': np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
        'flag_vendedor_novo': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
        'flag_imagem_reutilizada': np.random.choice([0, 1], n_samples, p=[0.6, 0.4]),
        'flag_reputacao_muito_ruim': np.random.choice([0, 1], n_samples, p=[0.9, 0.1]),
        'flag_preco_muito_baixo': np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
        'flag_imagem_muito_reutilizada': np.random.choice([0, 1], n_samples, p=[0.9, 0.1]),
        'vendedor_total_vendas': np.random.randint(5, 500, n_samples),
        'vendedor_total_cancelamentos': np.random.randint(0, 50, n_samples),
        'vendedor_taxa_cancelamento': np.random.uniform(0, 0.3, n_samples),
        'vendedor_media_avaliacao': np.random.uniform(3, 5, n_samples),
        'vendedor_num_avaliacoes': np.random.randint(0, 100, n_samples),
        'contagem_reuso_imagem': np.random.randint(0, 20, n_samples),
        'titulo': [f'Cartucho HP {np.random.choice(["Original", "Compatível", "Remanufaturado"])} {np.random.choice(["Preto", "Colorido"])}' for _ in range(n_samples)],
        'descricao': [f'Descrição do produto {i}' for i in range(1, n_samples + 1)]
    })
    
    return df

@st.cache_data
def load_ml_scores():
    """Carrega dados com scores de ML se disponível"""
    try:
        # Priorizar dataset sem preço (conforme solicitado)
        path = resolve_data_path("data/datasets_scores/dataset_com_scores_hibridos.csv")
        df_with_scores = pd.read_csv(path)
        return df_with_scores
    except FileNotFoundError:
        try:
            # Fallback para dataset com preço
            path = resolve_data_path("data/datasets_scores/dataset_com_scores_hibridos_com_preco.csv")
            df_with_scores = pd.read_csv(path)
            return df_with_scores
        except FileNotFoundError:
            return None

def get_risk_categories(df):
    """Categoriza anúncios por nível de risco"""
    df['risk_category'] = pd.cut(
        df['score_de_suspeita'], 
        bins=[0, 3, 6, 8, 10], 
        labels=['Baixo', 'Médio', 'Alto', 'Crítico'],
        include_lowest=True
        # Nota: 'observed' não é um parâmetro válido para pd.cut(), apenas para pd.groupby()
    )
    return df

def get_seller_metrics(df):
    """Calcula métricas agregadas por vendedor"""
    # Verificar quais colunas existem no dataset
    available_cols = df.columns.tolist()
    
    # Definir agregações baseadas nas colunas disponíveis
    agg_dict = {
        'id_anuncio': 'count',
        'is_fraud_suspect_v2': 'sum',
        'score_de_suspeita': 'mean'
    }
    
    # Adicionar colunas opcionais se existirem
    if 'preco_atual' in available_cols:
        agg_dict['preco_atual'] = 'mean'
    if 'diferenca_preco_perc' in available_cols:
        agg_dict['diferenca_preco_perc'] = 'mean'
    if 'grafo_taxa_suspeita_comunidade' in available_cols:
        agg_dict['grafo_taxa_suspeita_comunidade'] = 'mean'
    if 'vendedor_total_transacoes' in available_cols:
        agg_dict['vendedor_total_transacoes'] = 'first'
    if 'power_seller_status' in available_cols:
        agg_dict['power_seller_status'] = 'first'
    if 'e_loja_oficial' in available_cols:
        agg_dict['e_loja_oficial'] = 'first'
    if 'reputation_level' in available_cols:
        agg_dict['reputation_level'] = 'first'
    
    seller_metrics = df.groupby(['seller_id', 'vendedor_nome']).agg(agg_dict).reset_index()
    
    # Renomear colunas
    rename_dict = {
        'id_anuncio': 'total_anuncios',
        'is_fraud_suspect_v2': 'anuncios_suspeitos',
        'score_de_suspeita': 'score_medio'
    }
    
    if 'preco_atual' in seller_metrics.columns:
        rename_dict['preco_atual'] = 'preco_medio'
    if 'diferenca_preco_perc' in seller_metrics.columns:
        rename_dict['diferenca_preco_perc'] = 'desconto_medio'
    if 'grafo_taxa_suspeita_comunidade' in seller_metrics.columns:
        rename_dict['grafo_taxa_suspeita_comunidade'] = 'risco_comunidade_medio'
    if 'vendedor_total_transacoes' in seller_metrics.columns:
        rename_dict['vendedor_total_transacoes'] = 'total_transacoes'
    if 'power_seller_status' in seller_metrics.columns:
        rename_dict['power_seller_status'] = 'status'
    if 'e_loja_oficial' in seller_metrics.columns:
        rename_dict['e_loja_oficial'] = 'loja_oficial'
    if 'reputation_level' in seller_metrics.columns:
        rename_dict['reputation_level'] = 'reputacao'
    
    seller_metrics = seller_metrics.rename(columns=rename_dict)
    
    # Calcular taxa de suspeita
    seller_metrics['taxa_suspeita'] = (seller_metrics['anuncios_suspeitos'] / seller_metrics['total_anuncios'] * 100).round(1)
    
    return seller_metrics.sort_values('anuncios_suspeitos', ascending=False)

def get_community_metrics(df):
    """Calcula métricas por comunidade"""
    # Filtrar apenas comunidades válidas (não NaN)
    df_communities = df[df['grafo_comunidade_id'].notna()].copy()
    
    if len(df_communities) == 0:
        return pd.DataFrame(columns=['grafo_comunidade_id', 'total_anuncios', 'anuncios_suspeitos', 'score_medio', 'vendedores_unicos', 'taxa_suspeita'])
    
    community_metrics = df_communities.groupby('grafo_comunidade_id').agg({
        'id_anuncio': 'count',
        'is_fraud_suspect_v2': 'sum',
        'score_de_suspeita': 'mean',
        'seller_id': 'nunique'
    }).rename(columns={
        'id_anuncio': 'total_anuncios',
        'is_fraud_suspect_v2': 'anuncios_suspeitos',
        'score_de_suspeita': 'score_medio',
        'seller_id': 'vendedores_unicos'
    }).reset_index()
    
    # Calcular taxa de suspeita
    community_metrics['taxa_suspeita'] = (community_metrics['anuncios_suspeitos'] / community_metrics['total_anuncios'] * 100).round(1)
    
    # Adicionar coluna de score médio (se não existir)
    if 'score_medio' not in community_metrics.columns:
        community_metrics['score_medio'] = 0
    
    return community_metrics.sort_values('taxa_suspeita', ascending=False)


def append_to_dataset(novo_registro: pd.DataFrame, dataset_path: str, backup: bool = True) -> bool:
    """
    Adiciona ou atualiza um registro no dataset CSV
    
    Args:
        novo_registro: DataFrame com o novo registro (deve ter coluna 'id_anuncio')
        dataset_path: Caminho do arquivo CSV do dataset
        backup: Se True, cria backup antes de modificar
    
    Returns:
        True se sucesso, False caso contrário
    """
    try:
        from pathlib import Path
        from datetime import datetime
        import shutil
        
        dataset_file = Path(dataset_path)
        
        if not dataset_file.exists():
            # Se o arquivo não existe, criar novo
            novo_registro.to_csv(dataset_file, index=False, encoding='utf-8')
            return True
        
        # Criar backup se solicitado
        if backup:
            backup_path = dataset_file.parent / f"{dataset_file.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            shutil.copy2(dataset_file, backup_path)
        
        # Carregar dataset existente
        df_existente = pd.read_csv(dataset_file)
        
        # Verificar se já existe registro com mesmo id_anuncio
        id_col = 'id_anuncio'
        if id_col not in novo_registro.columns:
            raise ValueError(f"Coluna '{id_col}' não encontrada no novo registro")
        
        id_novo = novo_registro[id_col].iloc[0]
        
        # Remover registro existente se houver
        df_existente = df_existente[df_existente[id_col] != id_novo]
        
        # Adicionar novo registro
        df_final = pd.concat([df_existente, novo_registro], ignore_index=True)
        
        # Salvar dataset atualizado
        df_final.to_csv(dataset_file, index=False, encoding='utf-8')
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao atualizar dataset: {e}")
        return False


def clear_streamlit_cache():
    """Limpa o cache do Streamlit"""
    try:
        # Limpar cache de todas as funções decoradas com @st.cache_data
        st.cache_data.clear()
        return True
    except Exception as e:
        print(f"⚠️ Erro ao limpar cache: {e}")
        return False


def get_anuncio_by_id(id_anuncio: str, dataset_path: str) -> pd.DataFrame:
    """
    Busca um anúncio específico no dataset pelo ID
    
    Args:
        id_anuncio: ID do anúncio a buscar
        dataset_path: Caminho do arquivo CSV do dataset
    
    Returns:
        DataFrame com o registro encontrado ou DataFrame vazio
    """
    try:
        # Resolver caminho absoluto se for relativo
        if not Path(dataset_path).is_absolute():
            dataset_path = resolve_data_path(dataset_path)
        df = pd.read_csv(dataset_path)
        resultado = df[df['id_anuncio'] == id_anuncio]
        return resultado
    except Exception as e:
        print(f"❌ Erro ao buscar anúncio: {e}")
        return pd.DataFrame()
