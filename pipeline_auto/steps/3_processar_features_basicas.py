"""
=============================================================================
SCRIPT 3: PROCESSAR FEATURES BÁSICAS (VERSÃO MELHORADA)
=============================================================================
Calcula todas as features derivadas básicas a partir dos dados filtrados.

INPUT:
- data/script_1_filtrar_campos/dataset_campos_essenciais_*.csv
- data/script_2_ia/dados_extraidos_ia_*.csv
- Tabela de Preços Sugeridos.csv

OUTPUT:
- data/script_3_features_basicas/dataset_com_features_basicas_*.csv

FEATURES CALCULADAS:
- diferenca_preco_perc (preço vs HP)
- perc_reviews_negativas
- rating_ponderado
- vendedor_reputacao_num
- e_loja_oficial
- flag_inconsistencia_xl
"""

import pandas as pd
import numpy as np
import json
import ast
from pathlib import Path
import sys
from datetime import datetime

# Importar configurações
from _config import *

print("="*80)
print("🔧 SCRIPT 3: PROCESSAR FEATURES BÁSICAS (VERSÃO MELHORADA)")
print("="*80)

# =============================================================================
# 1. CARREGAR DADOS (VERSÃO CORRIGIDA)
# =============================================================================

print("\n📂 CARREGANDO DADOS...")
print("-"*80)

# MUDANÇA: Carregar o dataset JÁ FILTRADO do passo anterior
ARQUIVO_ESSENCIAIS = max(SCRIPT_1_DIR.glob("*.csv"), key=lambda x: x.stat().st_mtime)
print(f"Carregando: {ARQUIVO_ESSENCIAIS.name}")
df = pd.read_csv(ARQUIVO_ESSENCIAIS)
print(f"   ✅ {len(df)} produtos com campos essenciais carregados")

# Dados extraídos com IA (usando arquivo mais recente com IDs corretos)
ARQUIVO_IA = max(SCRIPT_2_DIR.glob("*.csv"), key=lambda x: x.stat().st_mtime)
print(f"\nCarregando: {ARQUIVO_IA.name}")
df_ia = pd.read_csv(ARQUIVO_IA, encoding='utf-8-sig')
print(f"   ✅ {len(df_ia)} produtos com IA")

# Tabela de preços HP
print(f"\nCarregando: Tabela de Preços Sugeridos HP")
try:
    df_precos_hp = pd.read_csv(
        "../fornecidos_pela_hp/Tabela de Preços Sugeridos.csv", 
        sep=';',          # MUDANÇA: Usar ponto e vírgula como separador
        decimal=','       # MUDANÇA: Usar vírgula como separador decimal
    )
    # MUDANÇA: Limpar e converter a coluna de preço
    df_precos_hp['Preco Sugerido'] = pd.to_numeric(df_precos_hp['Preco Sugerido'], errors='coerce')
    df_precos_hp = df_precos_hp.dropna(subset=['Preco Sugerido']) # Remover linhas sem preço
    print(f"   ✅ {len(df_precos_hp)} preços HP carregados e limpos")
except Exception as e:
    print(f"   ⚠️ Não foi possível carregar tabela HP: {e}")
    print(f"   Continuando sem preços HP...")
    df_precos_hp = None

# =============================================================================
# 2. MERGE DOS DADOS (VERSÃO CORRIGIDA)
# =============================================================================

print("\n🔗 FAZENDO MERGE DOS DADOS...")
print("-"*80)

# MUDANÇA: Fazer o merge usando a chave padronizada (id_anuncio)
# Garanta que ambos os CSVs usem o mesmo nome para a coluna de ID
df_merged = pd.merge(df, df_ia, on='id_anuncio', how='left')
print(f"   ✅ Merge realizado: {len(df_merged)} produtos")

# === BLOCO DE DEPURAÇÃO (ADICIONE ISSO) ===
print("\n🔍 DEPURANDO O MERGE...")
print("-"*80)
print(f"   Tipos de dados de 'id_anuncio' em df: {df['id_anuncio'].dtype}")
print(f"   Tipos de dados de 'id_anuncio' em df_ia: {df_ia['id_anuncio'].dtype}")

# Converter ambos para string para garantir a correspondência
df['id_anuncio'] = df['id_anuncio'].astype(str)
df_ia['id_anuncio'] = df_ia['id_anuncio'].astype(str)
print("   -> IDs convertidos para string para garantir a correspondência.")

# Refazer o merge com tipos consistentes
df_merged = pd.merge(df, df_ia, on='id_anuncio', how='left')
print(f"   ✅ Merge refeito: {len(df_merged)} produtos")

# Verificar quantos merges foram bem-sucedidos
sucessos_merge = df_merged['tipo_cartucho'].notna().sum()
print(f"   ✅ {sucessos_merge} de {len(df)} produtos foram enriquecidos com dados da IA.")
if sucessos_merge == 0:
    print("   ❌ ALERTA CRÍTICO: Nenhum produto correspondeu! Verifique se os arquivos de entrada são compatíveis.")
# === FIM DO BLOCO DE DEPURAÇÃO ===

# Verificar produtos sem IA
sem_ia = df_merged[df_merged['tipo_cartucho'].isna()]
if len(sem_ia) > 0:
    print(f"   ⚠️ {len(sem_ia)} produtos sem dados de IA")

# =============================================================================
# 3. FEATURE: vendedor_reputacao_num
# =============================================================================

print("\n⚙️ CALCULANDO: vendedor_reputacao_num")
print("-"*80)

# Mapear reputação para número
df_merged['vendedor_reputacao_num'] = df_merged['reputation_level'].map(REPUTACAO_MAP).fillna(0)
print(f"   ✅ Reputação mapeada")
print(f"      Valores únicos: {sorted(df_merged['vendedor_reputacao_num'].unique())}")

# =============================================================================
# 4. FEATURE: e_loja_oficial
# =============================================================================

print("\n⚙️ CALCULANDO: e_loja_oficial")
print("-"*80)

# Se vendedor_tipo == 'brand', é loja oficial
df_merged['e_loja_oficial'] = (df_merged['official_store_id'].notna()).astype(int)
print(f"   ✅ Lojas oficiais identificadas: {df_merged['e_loja_oficial'].sum()}")

# =============================================================================
# 5. FEATURE: vendedor_lider
# =============================================================================

print("\n⚙️ CALCULANDO: vendedor_lider")
print("-"*80)

# Se tem power_seller_status, é líder
df_merged['vendedor_lider'] = df_merged['power_seller_status'].notna().astype(int)
print(f"   ✅ Vendedores líderes identificados: {df_merged['vendedor_lider'].sum()}")

# =============================================================================
# 6. FEATURE: perc_reviews_negativas (LÓGICA CORRIGIDA E PRECISA)
# =============================================================================
print("\n⚙️ CALCULANDO: perc_reviews_negativas")
print("-"*80)

# ANOTAÇÃO: Esta lógica assume que seu CSV de entrada tem as colunas 'distribuicao_estrelas' e 'total_reviews_produto'
# Primeiro, converter a string de dicionário para um dicionário real
df_merged['distribuicao_estrelas'] = df_merged['distribuicao_estrelas'].apply(
    lambda x: ast.literal_eval(x) if pd.notna(x) and isinstance(x, str) else {}
)

# Extrair contagens de 1 e 2 estrelas
reviews_1_estrela = df_merged['distribuicao_estrelas'].apply(lambda d: d.get('1_estrelas', 0))
reviews_2_estrelas = df_merged['distribuicao_estrelas'].apply(lambda d: d.get('2_estrelas', 0))
reviews_negativas = reviews_1_estrela + reviews_2_estrelas
total_reviews = df_merged['total_reviews_produto'].fillna(0)

# Calcular porcentagem
df_merged['perc_reviews_negativas'] = np.where(
    total_reviews > 0,
    reviews_negativas / total_reviews,
    0
)
print(f"   ✅ Porcentagem calculada com base na distribuição de estrelas.")
print(f"      Média: {df_merged['perc_reviews_negativas'].mean():.2%}")
print(f"      Máxima: {df_merged['perc_reviews_negativas'].max():.2%}")

# =============================================================================
# 7. FEATURE: rating_ponderado
# =============================================================================

print("\n⚙️ CALCULANDO: rating_ponderado")
print("-"*80)

# Rating ponderado pelo log do número de reviews
df_merged['rating_ponderado'] = (
    df_merged['rating_medio_produto'].fillna(0) * 
    np.log(df_merged['total_reviews_produto'].fillna(0) + 1)
)
print(f"   ✅ Rating ponderado calculado")
print(f"      Média: {df_merged['rating_ponderado'].mean():.2f}")
print(f"      Máximo: {df_merged['rating_ponderado'].max():.2f}")

# =============================================================================
# 8. FEATURE: flag_inconsistencia_xl
# =============================================================================

print("\n⚙️ CALCULANDO: flag_inconsistencia_xl")
print("-"*80)

# Verificar se título menciona XL mas tipo não tem XL (ou vice-versa)
titulo_tem_xl = df_merged['titulo'].str.lower().str.contains('xl', na=False)
tipo_tem_xl = df_merged['tipo_cartucho'].str.lower().str.contains('xl', na=False)

df_merged['flag_inconsistencia_xl'] = (titulo_tem_xl != tipo_tem_xl).astype(int)

inconsistencias = df_merged['flag_inconsistencia_xl'].sum()
print(f"   ✅ Inconsistências XL detectadas: {inconsistencias}")
if inconsistencias > 0:
    print(f"      ({inconsistencias/len(df_merged)*100:.1f}% dos produtos)")


# =============================================================================
# 9. FEATURE: diferenca_preco_perc (com tabela HP) - VERSÃO MELHORADA
# =============================================================================

print("\n⚙️ CALCULANDO: diferenca_preco_perc")
print("-"*80)

if df_precos_hp is not None:
    # --- PASSO 1: Pré-processar tabela HP para busca rápida ---
    
    def criar_chave_lookup(row):
        produto_str = str(row['Produto']).lower()
        familia_str = str(row['Familia']).lower()
        
        # Extrair modelo base (ex: 664)
        modelo_base = familia_str.replace('hp', '').strip()
        
        # Verificar se é XL
        is_xl = 'xl' in produto_str
        
        # Determinar cor
        cor = 'preto' if 'preto' in produto_str else 'colorido'
        
        # Montar chave: ex: "664xl_preto"
        return f"{modelo_base}{'xl' if is_xl else ''}_{cor}"

    df_precos_hp['lookup_key'] = df_precos_hp.apply(criar_chave_lookup, axis=1)
    
    # Criar um dicionário para busca instantânea: {chave: preco}
    preco_lookup_dict = pd.Series(df_precos_hp['Preco Sugerido'].values, index=df_precos_hp['lookup_key']).to_dict()
    print("   ✅ Dicionário de preços HP criado para busca rápida.")

    # --- PASSO 2: Função para buscar o preço sugerido total do anúncio ---
    
    def buscar_preco_hp_total(row):
        tipo_ia = str(row['tipo_cartucho']).lower().strip()
        cores_ia = row['cores_detalhadas']
        unidades_ia = int(row['quantidade_por_anuncio']) if pd.notna(row['quantidade_por_anuncio']) else 1
        
        # Tratar o caso de 'cores_detalhadas' ser uma string
        if isinstance(cores_ia, str):
            try:
                cores_ia = json.loads(cores_ia.replace("'", "\""))
            except:
                return np.nan # Não foi possível parsear

        if not isinstance(cores_ia, dict):
             return np.nan
        
        tem_preto = cores_ia.get('preto', 0) == 1
        tem_colorido = cores_ia.get('colorido', 0) == 1
        
        preco_total_sugerido = 0.0

        if unidades_ia == 1:
            cor_str = 'preto' if tem_preto else 'colorido'
            chave = f"{tipo_ia}_{cor_str}"
            preco_total_sugerido = preco_lookup_dict.get(chave, np.nan)

        elif unidades_ia == 2 and tem_preto and tem_colorido:
            # Kit com 1 preto + 1 colorido
            chave_preto = f"{tipo_ia}_preto"
            chave_color = f"{tipo_ia}_colorido"
            preco_preto = preco_lookup_dict.get(chave_preto)
            preco_color = preco_lookup_dict.get(chave_color)
            
            if preco_preto and preco_color:
                preco_total_sugerido = preco_preto + preco_color
            else:
                preco_total_sugerido = np.nan
        
        elif unidades_ia > 1 and tem_preto and not tem_colorido:
            # Kit com múltiplos cartuchos pretos
            chave = f"{tipo_ia}_preto"
            preco_unitario = preco_lookup_dict.get(chave)
            preco_total_sugerido = preco_unitario * unidades_ia if preco_unitario else np.nan
            
        elif unidades_ia > 1 and not tem_preto and tem_colorido:
            # Kit com múltiplos cartuchos coloridos
            chave = f"{tipo_ia}_colorido"
            preco_unitario = preco_lookup_dict.get(chave)
            preco_total_sugerido = preco_unitario * unidades_ia if preco_unitario else np.nan
        
        else:
            # Kits mais complexos (ex: 3 pretos + 2 coloridos) não são tratados
            preco_total_sugerido = np.nan
            
        return preco_total_sugerido

    # --- PASSO 3: Aplicar a função e calcular a diferença ---

    df_merged['preco_sugerido_hp'] = df_merged.apply(buscar_preco_hp_total, axis=1)
    
    df_merged['diferenca_preco_perc'] = np.where(
        df_merged['preco_sugerido_hp'].notna() & (df_merged['preco_sugerido_hp'] > 0),
        (df_merged['preco_atual'] - df_merged['preco_sugerido_hp']) / df_merged['preco_sugerido_hp'],
        np.nan
    )
    
    tem_preco = df_merged['diferenca_preco_perc'].notna().sum()
    print(f"   ✅ Diferença de preço calculada para {tem_preco} de {len(df_merged)} produtos")
    if tem_preco > 0:
        # Filtrar valores extremos (outliers) para uma média mais realista
        diferenca_filtrada = df_merged['diferenca_preco_perc'].dropna()
        diferenca_filtrada = diferenca_filtrada[diferenca_filtrada.between(-1, 2)] # Ex: ignora descontos > 100% ou ágios > 200%
        print(f"      Média (sem outliers): {diferenca_filtrada.mean():.2%}")

else:
    print("   ⚠️ Pulando (tabela HP não carregada)")
    df_merged['diferenca_preco_perc'] = np.nan
    df_merged['preco_sugerido_hp'] = np.nan


# =============================================================================
# 11. SELECIONAR COLUNAS FINAIS
# =============================================================================

print("\n📊 SELECIONANDO COLUNAS FINAIS...")
print("-"*80)

# Colunas que queremos manter
colunas_manter = [
    # Identificadores
    'id_anuncio', 'seller_id', 'catalog_product_id', 'titulo', 'link_anuncio', 'imagem_url_principal', 'descricao',

    # Features da IA
    'tipo_cartucho', 'quantidade_por_anuncio', 'cores_detalhadas', 'usado_seminovo',

    # Features do Vendedor (Originais + Novas)
    'vendedor_nome', 'vendedor_total_transacoes', 'power_seller_status', 'official_store_id', 'reputation_level',
    'vendedor_reputacao_num', 'vendedor_lider', 'e_loja_oficial',

    # Features de Preço (Originais + Novas)
    'preco_atual', 'preco_sugerido_hp', 'diferenca_preco_perc',

    # Features de Reviews (Originais + Novas)
    'rating_medio_produto', 'total_reviews_produto', 'distribuicao_estrelas',
    'perc_reviews_negativas', 'rating_ponderado',

    # Flags de Inconsistência (Novas)
    'flag_inconsistencia_xl',
    
    # Outras Features Originais
    'condicao', 'logistic_type', 'origem_envio', 'conexoes_vendedores_alt', 'marca', 'modelo'
]

# Verificar quais colunas existem
colunas_existentes = [col for col in colunas_manter if col in df_merged.columns]
colunas_faltando = [col for col in colunas_manter if col not in df_merged.columns]

if colunas_faltando:
    print(f"   ⚠️ Colunas faltando: {colunas_faltando}")

df_final = df_merged[colunas_existentes].copy()
print(f"   ✅ {len(colunas_existentes)} colunas selecionadas")

# =============================================================================
# 12. SALVAR DATASET
# =============================================================================

print("\n💾 SALVANDO DATASET...")
print("-"*80)

# Salvar na pasta correta
SCRIPT_3_DIR.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
arquivo_saida = SCRIPT_3_DIR / f"dataset_com_features_basicas_{timestamp}.csv"
df_final.to_csv(arquivo_saida, index=False)
print(f"   ✅ Salvo em: {arquivo_saida}")
print(f"   📊 Shape: {df_final.shape}")

# =============================================================================
# 13. RESUMO FINAL
# =============================================================================

print("\n" + "="*80)
print("📈 RESUMO DAS FEATURES CRIADAS")
print("="*80)

features_criadas = [
    'vendedor_reputacao_num',
    'e_loja_oficial',
    'vendedor_lider',
    'perc_reviews_negativas',
    'rating_ponderado',
    'flag_inconsistencia_xl',
    'diferenca_preco_perc'
]

print("\n✅ Features calculadas:")
for feature in features_criadas:
    if feature in df_final.columns:
        print(f"   ✅ {feature}")
    else:
        print(f"   ❌ {feature} (não calculada)")

print(f"\n📊 ESTATÍSTICAS:")
print(f"   Total de produtos: {len(df_final)}")
print(f"   Total de colunas: {len(df_final.columns)}")
print(f"   Lojas oficiais: {df_final['e_loja_oficial'].sum()}")
print(f"   Vendedores líderes: {df_final['vendedor_lider'].sum()}")
print(f"   Inconsistências XL: {df_final['flag_inconsistencia_xl'].sum()}")

print("\n" + "="*80)
print("✅ SCRIPT 3 CONCLUÍDO COM SUCESSO!")
print("="*80)
print(f"\n📁 Próximo passo: python 4_processar_reviews_nlp.py")


