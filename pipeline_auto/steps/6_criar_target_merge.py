#!/usr/bin/env python3
"""
SCRIPT 6: CRIAR TARGET E MERGE FINAL
=====================================
Cria a variável target is_fraud_suspect_v2 e faz o merge de todas as features.

INPUT:
- data/script_3_features_basicas/dataset_com_features_basicas_*.csv
- data/script_4_nlp/reviews_com_nlp_*.csv
- data/script_5_imagens/hashes_imagens.csv

OUTPUT:
- data/script_6_grafo/dataset_final_para_modelo.csv (PRONTO PARA ML)
"""

import pandas as pd
import numpy as np
import os
import json

# --- CONFIGURAÇÃO ---
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))
from _config import *

# Usar os arquivos mais recentes de cada script
PATH_FEATURES_BASICAS = max(SCRIPT_3_DIR.glob("*.csv"), key=lambda x: x.stat().st_mtime)
PATH_REVIEWS_NLP = max(SCRIPT_4_DIR.glob("*.csv"), key=lambda x: x.stat().st_mtime)
PATH_HASHES_IMAGENS = SCRIPT_5_DIR / "hashes_imagens.csv"
PATH_OUTPUT = SCRIPT_6_DIR / "dataset_final_para_modelo.csv"

# Criar diretório de saída se não existir
SCRIPT_6_DIR.mkdir(parents=True, exist_ok=True)

def criar_is_fraud_suspect_v2(df):
    """
    Cria variável target is_fraud_suspect_v2 (versão melhorada)
    
    CRITÉRIOS DE SUSPEITA (11 critérios):
    ======================================
    
    🔴 CRITÉRIOS FORTES (2 pontos cada):
    1. Preço MUITO abaixo do mercado (< -30%)
    2. Imagem reutilizada em MUITOS produtos (>10x)
    3. Vendedor com reputação MUITO RUIM (1_red)
    4. Alta % de reviews negativas (>30%)
    
    🟠 CRITÉRIOS MÉDIOS (1 ponto cada):
    5. Preço moderadamente abaixo (-15% a -30%)
    6. Imagem reutilizada moderadamente (3-10x)
    7. Vendedor com reputação RUIM (2_orange)
    8. Inconsistência XL no título
    9. Vendedor NOVO com poucos produtos (<50 transações)
    
    🟡 CRITÉRIOS FRACOS (0.5 ponto cada):
    10. Preço ligeiramente abaixo (-5% a -15%)
    11. Reviews negativas moderadas (15-30%)
    
    ⭐ PENALIDADE ESPECIAL:
    - Loja Oficial com múltiplos critérios suspeitos (+1 ponto)
      (Para detectar o caso da loja oficial fraudulenta da HP)
    
    THRESHOLD: score >= 3.0 → SUSPEITO
    """
    
    print("\n" + "="*80)
    print("🎯 CRIANDO VARIÁVEL TARGET: is_fraud_suspect_v2")
    print("="*80)
    
    # Inicializar score e flags individuais
    df['score_de_suspeita'] = 0.0
    
    # Flags individuais para rastrear cada critério
    df['flag_preco_muito_baixo'] = 0  # < -30%
    df['flag_preco_medio_baixo'] = 0  # -15% a -30%
    df['flag_preco_ligeiramente_baixo'] = 0  # -5% a -15%
    df['flag_imagem_muito_reutilizada'] = 0  # >10x
    df['flag_imagem_reutilizada'] = 0  # 3-10x
    df['flag_reputacao_muito_ruim'] = 0  # <= 1
    df['flag_reputacao_ruim'] = 0  # <= 2
    df['flag_reviews_muito_negativas'] = 0  # >30%
    df['flag_reviews_negativas'] = 0  # 15-30%
    df['flag_inconsistencia_xl'] = 0  # Inconsistência XL
    df['flag_vendedor_novo'] = 0  # <50 transações
    df['flag_loja_oficial_suspeita'] = 0  # Loja oficial com múltiplos critérios
    df['flag_fraude_instantanea'] = 0  # Preço < -30% (regra especial)
    
    # --- 1. ANÁLISE DE PREÇO ---
    print("\n📊 CRITÉRIO 1-3: ANÁLISE DE PREÇO")
    
    # Preço MUITO abaixo (-30% ou mais)
    mask_preco_muito_baixo = df['diferenca_preco_perc'] < -0.30
    df.loc[mask_preco_muito_baixo, 'score_de_suspeita'] += 2.0
    df.loc[mask_preco_muito_baixo, 'flag_preco_muito_baixo'] = 1
    print(f"   🔴 Preço < -30%: {mask_preco_muito_baixo.sum()} produtos (+2.0 pontos)")
    
    # Preço moderadamente abaixo (-15% a -30%)
    mask_preco_medio = (df['diferenca_preco_perc'] >= -0.30) & (df['diferenca_preco_perc'] < -0.15)
    df.loc[mask_preco_medio, 'score_de_suspeita'] += 1.0
    df.loc[mask_preco_medio, 'flag_preco_medio_baixo'] = 1
    print(f"   🟠 Preço -15% a -30%: {mask_preco_medio.sum()} produtos (+1.0 ponto)")
    
    # Preço ligeiramente abaixo (-5% a -15%)
    mask_preco_leve = (df['diferenca_preco_perc'] >= -0.15) & (df['diferenca_preco_perc'] < -0.05)
    df.loc[mask_preco_leve, 'score_de_suspeita'] += 0.5
    df.loc[mask_preco_leve, 'flag_preco_ligeiramente_baixo'] = 1
    print(f"   🟡 Preço -5% a -15%: {mask_preco_leve.sum()} produtos (+0.5 ponto)")
    
    # --- 2. ANÁLISE DE IMAGEM (se disponível) ---
    print("\n🖼️ CRITÉRIO 4-5: ANÁLISE DE REUSO DE IMAGEM")
    
    if 'contagem_reuso_imagem' in df.columns:
        # Reuso MUITO alto (>10x)
        mask_reuso_alto = df['contagem_reuso_imagem'] > 10
        df.loc[mask_reuso_alto, 'score_de_suspeita'] += 2.0
        print(f"   🔴 Reuso > 10x: {mask_reuso_alto.sum()} produtos (+2.0 pontos)")
        
        # Reuso moderado (3-10x)
        mask_reuso_medio = (df['contagem_reuso_imagem'] >= 3) & (df['contagem_reuso_imagem'] <= 10)
        df.loc[mask_reuso_medio, 'score_de_suspeita'] += 1.0
        print(f"   🟠 Reuso 3-10x: {mask_reuso_medio.sum()} produtos (+1.0 ponto)")
    else:
        print("   ⚠️ Coluna 'contagem_reuso_imagem' não encontrada. Pulando...")
    
    # --- 3. ANÁLISE DE REPUTAÇÃO ---
    print("\n⭐ CRITÉRIO 6-7: REPUTAÇÃO DO VENDEDOR")
    
    # Reputação MUITO RUIM (1_red)
    mask_rep_ruim = df['vendedor_reputacao_num'] == 1
    df.loc[mask_rep_ruim, 'score_de_suspeita'] += 2.0
    print(f"   🔴 Reputação 1_red: {mask_rep_ruim.sum()} produtos (+2.0 pontos)")
    
    # Reputação RUIM (2_orange)
    mask_rep_regular = df['vendedor_reputacao_num'] == 2
    df.loc[mask_rep_regular, 'score_de_suspeita'] += 1.0
    print(f"   🟠 Reputação 2_orange: {mask_rep_regular.sum()} produtos (+1.0 ponto)")
    
    # --- 4. ANÁLISE DE REVIEWS ---
    print("\n💬 CRITÉRIO 8-9: REVIEWS NEGATIVAS")
    
    # Reviews negativas ALTAS (>30%)
    mask_reviews_alta = df['perc_reviews_negativas'] > 0.30
    df.loc[mask_reviews_alta, 'score_de_suspeita'] += 2.0
    print(f"   🔴 Reviews negativas > 30%: {mask_reviews_alta.sum()} produtos (+2.0 pontos)")
    
    # Reviews negativas moderadas (15-30%)
    mask_reviews_media = (df['perc_reviews_negativas'] >= 0.15) & (df['perc_reviews_negativas'] <= 0.30)
    df.loc[mask_reviews_media, 'score_de_suspeita'] += 0.5
    print(f"   🟡 Reviews negativas 15-30%: {mask_reviews_media.sum()} produtos (+0.5 ponto)")
    
    # --- 5. INCONSISTÊNCIA XL ---
    print("\n🔤 CRITÉRIO 10: INCONSISTÊNCIA XL")
    
    mask_xl = df['flag_inconsistencia_xl'] == 1
    df.loc[mask_xl, 'score_de_suspeita'] += 1.0
    print(f"   🟠 Inconsistência XL: {mask_xl.sum()} produtos (+1.0 ponto)")
    
    # --- 6. VENDEDOR NOVO ---
    print("\n🆕 CRITÉRIO 11: VENDEDOR NOVO")
    
    mask_novo = df['vendedor_total_transacoes'] < 50
    df.loc[mask_novo, 'score_de_suspeita'] += 1.0
    print(f"   🟠 Vendedor novo (<50 transações): {mask_novo.sum()} produtos (+1.0 ponto)")
    
    # --- 7. PENALIDADE ESPECIAL: LOJA OFICIAL SUSPEITA ---
    print("\n⭐ PENALIDADE ESPECIAL: LOJA OFICIAL COM MÚLTIPLOS CRITÉRIOS")
    
    # Loja oficial com score >= 2.0 (já tem múltiplos critérios suspeitos)
    mask_loja_oficial_suspeita = (df['e_loja_oficial'] == 1) & (df['score_de_suspeita'] >= 2.0)
    df.loc[mask_loja_oficial_suspeita, 'score_de_suspeita'] += 1.0
    print(f"   🔴 Loja oficial com múltiplos critérios: {mask_loja_oficial_suspeita.sum()} produtos (+1.0 ponto)")
    print("   💡 Detecta casos como a loja oficial fraudulenta mencionada pela HP")
    
    # =============================================================================
    # REGRA DE FRAUDE INSTANTÂNEA (MANTENDO OUTROS CRITÉRIOS)
    # =============================================================================
    print("\n🚨 APLICANDO REGRA DE FRAUDE INSTANTÂNEA...")
    
    # A máscara mask_preco_muito_baixo já foi definida na seção de análise de preço
    SCORE_INSTANTANEO = 10.0
    
    # CORREÇÃO: Somar em vez de sobrescrever para manter outros critérios
    # Primeiro, remover os 2 pontos já adicionados pelo critério de preço
    df.loc[mask_preco_muito_baixo, 'score_de_suspeita'] -= 2.0
    # Depois, adicionar o score instantâneo
    df.loc[mask_preco_muito_baixo, 'score_de_suspeita'] += SCORE_INSTANTANEO
    # Marcar a flag de fraude instantânea
    df.loc[mask_preco_muito_baixo, 'flag_fraude_instantanea'] = 1
    
    print(f"   ✅ {mask_preco_muito_baixo.sum()} produtos com preço < -30% tiveram seu score ajustado para {SCORE_INSTANTANEO}")
    print("   💡 Outros critérios (imagem, reputação, etc.) foram mantidos no score final")
    # =============================================================================
    
    # --- 8. CRIAR TARGET BINÁRIO ---
    print("\n" + "="*80)
    print("🎯 DEFININDO THRESHOLD E CRIANDO TARGET")
    print("="*80)
    
    THRESHOLD = 3.0
    df['is_fraud_suspect_v2'] = (df['score_de_suspeita'] >= THRESHOLD).astype(int)
    
    print(f"\n📊 THRESHOLD: {THRESHOLD} pontos")
    print(f"   ✅ Produtos NÃO SUSPEITOS (score < {THRESHOLD}): {(df['is_fraud_suspect_v2'] == 0).sum()}")
    print(f"   ⚠️ Produtos SUSPEITOS (score >= {THRESHOLD}): {(df['is_fraud_suspect_v2'] == 1).sum()}")
    print(f"   📈 Taxa de suspeitos: {(df['is_fraud_suspect_v2'] == 1).sum() / len(df) * 100:.1f}%")
    
    # --- 9. ANÁLISE DE DISTRIBUIÇÃO DE SCORES ---
    print("\n📊 DISTRIBUIÇÃO DE SCORES:")
    print("-"*80)
    
    bins = [0, 1, 2, 3, 4, 5, 100]
    labels = ['0-1', '1-2', '2-3', '3-4', '4-5', '5+']
    df['score_faixa'] = pd.cut(df['score_de_suspeita'], bins=bins, labels=labels, include_lowest=True)
    
    distribuicao = df.groupby('score_faixa', observed=True).agg({
        'id_anuncio': 'count',
        'is_fraud_suspect_v2': 'sum'
    }).rename(columns={'id_anuncio': 'total_produtos', 'is_fraud_suspect_v2': 'num_suspeitos'})
    
    for faixa, row in distribuicao.iterrows():
        simbolo = "✅" if faixa in ['0-1', '1-2', '2-3'] else "⚠️"
        print(f"   {simbolo} Score {faixa}: {row['total_produtos']:>3} produtos ({row['num_suspeitos']:>2} suspeitos)")
    
    df.drop(columns=['score_faixa'], inplace=True)
    
    print("\n✅ Target 'is_fraud_suspect_v2' criado com sucesso!")
    
    return df

def merge_all_features():
    """Faz merge de todas as features"""
    
    print("\n" + "="*80)
    print("🔗 MERGE DE TODAS AS FEATURES")
    print("="*80)
    
    # 1. Carregar Features Básicas
    print("\n📂 1. Carregando Features Básicas...")
    df_base = pd.read_csv(PATH_FEATURES_BASICAS)
    print(f"   ✅ {len(df_base)} produtos, {len(df_base.columns)} colunas")
    
    # 2. Carregar Reviews NLP
    print("\n📂 2. Carregando Reviews NLP...")
    try:
        df_nlp = pd.read_csv(PATH_REVIEWS_NLP)
        print(f"   ✅ {len(df_nlp)} produtos com reviews, {len(df_nlp.columns)} colunas NLP")
        
        # Merge
        df_merged = pd.merge(df_base, df_nlp, on='id_anuncio', how='left')
        print(f"   ✅ Merge realizado: {len(df_merged)} produtos")
        
        # Preencher NaN para produtos sem reviews
        nlp_cols = [col for col in df_nlp.columns if col != 'id_anuncio']
        for col in nlp_cols:
            if col in df_merged.columns:
                if col.startswith('review_embedding_'):
                    df_merged[col] = df_merged[col].fillna(0.0)
                elif col == 'sentimento_medio_reviews':
                    df_merged[col] = df_merged[col].fillna(0.0)
                else:
                    df_merged[col] = df_merged[col].fillna(0)
        
        print(f"   ✅ NaN preenchidos para produtos sem reviews")
    except FileNotFoundError:
        print("   ⚠️ Arquivo reviews_com_nlp.csv não encontrado. Pulando NLP...")
        df_merged = df_base.copy()
    
    # 3. Carregar Hashes de Imagem
    print("\n📂 3. Carregando Hashes de Imagem...")
    
    # Tentar carregar hashes_imagens_COMPLETO.csv primeiro (múltiplas imagens)
    hash_file_used = None
    if False:  # PATH_HASHES_COMPLETO não existe mais
        print("   🔍 Detectado: hashes_imagens_COMPLETO.csv (múltiplas imagens)")
        df_hashes = pd.read_csv(PATH_HASHES_COMPLETO)
        hash_file_used = 'COMPLETO'
        
        # Agregar: pegar a contagem MÁXIMA de reuso entre todas as imagens do produto
        print("   📊 Agregando múltiplas imagens por produto (MAX reuso)...")
        df_hashes_agg = df_hashes.groupby('id_anuncio').agg({
            'contagem_reuso_imagem': 'max',  # Máximo reuso entre as imagens
            'phash': 'count'  # Número de imagens
        }).reset_index()
        df_hashes_agg.rename(columns={
            'contagem_reuso_imagem': 'contagem_reuso_imagem',
            'phash': 'num_imagens_produto'
        }, inplace=True)
        
        print(f"   ✅ {len(df_hashes_agg)} produtos com imagens")
        print(f"   📊 Média de imagens por produto: {df_hashes['id_anuncio'].value_counts().mean():.1f}")
        
    elif os.path.exists(PATH_HASHES_IMAGENS):
        print("   🔍 Detectado: hashes_imagens.csv (imagem principal)")
        df_hashes_agg = pd.read_csv(PATH_HASHES_IMAGENS)
        hash_file_used = 'SIMPLES'
        df_hashes_agg['num_imagens_produto'] = 1  # Apenas 1 imagem
        print(f"   ✅ {len(df_hashes_agg)} produtos com hash")
    else:
        print("   ⚠️ Nenhum arquivo de hash encontrado. Criando placeholder...")
        df_hashes_agg = pd.DataFrame({
            'id_anuncio': df_merged['id_anuncio'],
            'contagem_reuso_imagem': 1,
            'num_imagens_produto': 0
        })
        hash_file_used = 'PLACEHOLDER'
    
    # Merge hashes
    df_final = pd.merge(df_merged, df_hashes_agg[['id_anuncio', 'contagem_reuso_imagem', 'num_imagens_produto']], 
                        on='id_anuncio', how='left')
    df_final['contagem_reuso_imagem'] = df_final['contagem_reuso_imagem'].fillna(1)
    df_final['num_imagens_produto'] = df_final['num_imagens_produto'].fillna(0)
    
    print(f"   ✅ Merge realizado: {len(df_final)} produtos")
    
    print("\n" + "="*80)
    print("📊 RESUMO DO DATASET MERGED")
    print("="*80)
    print(f"   Total de produtos: {len(df_final)}")
    print(f"   Total de features: {len(df_final.columns)}")
    print(f"   Arquivo de hash usado: {hash_file_used}")
    
    return df_final

def main():
    print("="*80)
    print("🎯 SCRIPT 6: CRIAR TARGET E MERGE FINAL")
    print("="*80)
    
    # 1. Merge de todas as features
    df = merge_all_features()
    
    # 2. Criar target
    df = criar_is_fraud_suspect_v2(df)
    
    # 3. Salvar dataset final
    print("\n" + "="*80)
    print("💾 SALVANDO DATASET FINAL")
    print("="*80)
    
    df.to_csv(PATH_OUTPUT, index=False)
    print(f"✅ Salvo: {os.path.abspath(PATH_OUTPUT)}")
    print(f"📊 Shape: ({len(df)}, {len(df.columns)})")
    
    # 4. Resumo final
    print("\n" + "="*80)
    print("📈 RESUMO FINAL DO DATASET")
    print("="*80)
    
    print(f"\n📦 TOTAL: {len(df)} produtos")
    print(f"📊 FEATURES: {len(df.columns)} colunas")
    print(f"\n🎯 TARGET:")
    print(f"   ✅ NÃO SUSPEITOS: {(df['is_fraud_suspect_v2'] == 0).sum()} ({(df['is_fraud_suspect_v2'] == 0).sum() / len(df) * 100:.1f}%)")
    print(f"   ⚠️ SUSPEITOS: {(df['is_fraud_suspect_v2'] == 1).sum()} ({(df['is_fraud_suspect_v2'] == 1).sum() / len(df) * 100:.1f}%)")
    
    print(f"\n📊 SCORE DE SUSPEITA:")
    print(f"   Mínimo: {df['score_de_suspeita'].min():.1f}")
    print(f"   Máximo: {df['score_de_suspeita'].max():.1f}")
    print(f"   Média: {df['score_de_suspeita'].mean():.1f}")
    print(f"   Mediana: {df['score_de_suspeita'].median():.1f}")
    
    # Lista de features por categoria
    print(f"\n📋 CATEGORIAS DE FEATURES:")
    
    feature_categories = {
        '🔴 IDENTIFICADORES': [col for col in df.columns if col in ['id_anuncio', 'titulo', 'link_anuncio', 'seller_id', 'vendedor_nome']],
        '🟠 PREÇO': [col for col in df.columns if 'preco' in col.lower() or 'diferenca' in col.lower()],
        '🟡 VENDEDOR': [col for col in df.columns if 'vendedor' in col.lower() and col not in ['vendedor_id', 'vendedor_nome']],
        '🟢 REVIEWS': [col for col in df.columns if 'review' in col.lower() or 'rating' in col.lower()],
        '🔵 PRODUTO': [col for col in df.columns if col in ['tipo_cartucho', 'unidades_por_anuncio', 'cores_detalhadas', 'flag_inconsistencia_xl']],
        '🟣 NLP': [col for col in df.columns if 'sentimento' in col.lower() or 'contagem_' in col.lower() or 'embedding' in col.lower()],
        '🟤 IMAGEM': [col for col in df.columns if 'imagem' in col.lower() or 'phash' in col.lower()],
        '⚫ TARGET': [col for col in df.columns if 'fraud' in col.lower() or 'suspeita' in col.lower()]
    }
    
    for categoria, features in feature_categories.items():
        if features:
            print(f"   {categoria}: {len(features)} features")
    
    print("\n" + "="*80)
    print("✅ SCRIPT 4 CONCLUÍDO COM SUCESSO!")
    print("="*80)
    print(f"\n📁 Próximo passo: Treinar o modelo com {PATH_OUTPUT}")

if __name__ == "__main__":
    main()


