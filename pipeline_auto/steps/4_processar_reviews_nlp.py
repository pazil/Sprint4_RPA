"""
=============================================================================
SCRIPT 2: PROCESSAR REVIEWS COM NLP (VERSÃO REVISADA)
=============================================================================
Analisa reviews, título e descrição dos produtos usando técnicas de NLP e gera embeddings.

INPUT:
- data/script_3_features_basicas/dataset_com_features_basicas_*.csv
- data/reviews_unificado.json

OUTPUT:
- data/script_4_nlp/reviews_com_nlp_*.csv

FEATURES GERADAS:
- sentimento_medio_reviews (VADER)
- contagem_alegacao_fraude (palavras-chave)
- contagem_performance_negativa (palavras-chave)
- possui_reviews_texto (flag)
- embedding_titulo (OpenAI - 1536 dimensões do título)
- embedding_descricao (OpenAI - 1536 dimensões da descrição)
- embedding_reviews (OpenAI - 1536 dimensões das reviews)

MELHORIAS DA VERSÃO:
- Adaptado para usar o dataset limpo e centralizado, eliminando merges.
- Mais rápido e com menos dependências de arquivos.
- Usa nomes de colunas atualizados (id_anuncio, titulo, descricao).
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
import os
from dotenv import load_dotenv
import time

# Importar configurações
import sys
sys.path.append(str(Path(__file__).parent))
from _config import *

# Carregar variáveis de ambiente
load_dotenv()

print("="*80)
print("🧠 SCRIPT 4: PROCESSAR REVIEWS COM NLP (VERSÃO REVISADA)")
print("="*80)

# =============================================================================
# 1. VERIFICAR DEPENDÊNCIAS
# =============================================================================

print("\n📦 VERIFICANDO DEPENDÊNCIAS...")
print("-"*80)

# Verificar vaderSentiment
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    print("   ✅ vaderSentiment instalado")
except ImportError:
    print("   ❌ vaderSentiment não encontrado!")
    print("   Execute: pip install vaderSentiment")
    sys.exit(1)

# Verificar OpenAI
try:
    from openai import OpenAI
    print("   ✅ openai instalado")
except ImportError:
    print("   ❌ openai não encontrado!")
    print("   Execute: pip install openai")
    sys.exit(1)

# Verificar API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("   ❌ OPENAI_API_KEY não encontrada no .env!")
    print("   Crie um arquivo .env com: OPENAI_API_KEY=sk-...")
    sys.exit(1)
else:
    print(f"   ✅ API Key OpenAI configurada")

client = OpenAI(api_key=OPENAI_API_KEY)

# =============================================================================
# 2. CONFIGURAR ARQUIVOS DE ENTRADA E SAÍDA
# =============================================================================

# MUDANÇA: Apontar para os novos arquivos de entrada.

# Arquivo com features básicas (inclui título, descrição e features calculadas)
DATASET_FEATURES_CSV = max(Path("../data/script_3_features_basicas").glob("*.csv"), key=lambda x: x.stat().st_mtime)

# Arquivo JSON unificado com os reviews
REVIEWS_UNIFICADO_JSON = Path("../data/reviews_unificado.json")

# Arquivo de saída para as features de NLP
OUTPUT_DIR = Path("../data/script_4_nlp")
OUTPUT_DIR.mkdir(exist_ok=True)
REVIEWS_NLP_CSV = OUTPUT_DIR / f"reviews_com_nlp_{time.strftime('%Y%m%d_%H%M%S')}.csv"

# =============================================================================
# 3. CARREGAR DADOS (MUITO SIMPLIFICADO)
# =============================================================================

print("\n📂 CARREGANDO DADOS...")
print("-"*80)

# MUDANÇA: Carregar o dataset com features básicas que já contém tudo.
print(f"Carregando: {DATASET_FEATURES_CSV.name}")
df_produtos = pd.read_csv(DATASET_FEATURES_CSV)
print(f"   ✅ {len(df_produtos)} produtos carregados com título e descrição")

# MUDANÇA: Carregar o novo JSON de reviews.
print(f"\nCarregando: {REVIEWS_UNIFICADO_JSON.name}")
with open(REVIEWS_UNIFICADO_JSON, 'r', encoding='utf-8') as f:
    reviews_data = json.load(f)
print(f"   ✅ Reviews de {len(reviews_data)} produtos carregados")

# =============================================================================
# 4. ORGANIZAR REVIEWS POR PRODUTO (Sem alterações na lógica)
# =============================================================================

print("\n🔗 ORGANIZANDO REVIEWS POR PRODUTO...")
print("-"*80)

reviews_por_produto = {}
for produto in reviews_data:
    # ANOTAÇÃO: A chave no JSON é 'product_id', que corresponde a 'id_anuncio' no CSV.
    produto_id = produto.get('product_id')
    reviews_list = produto.get('reviews', [])
    
    if produto_id and reviews_list:
        textos_reviews = [
            review.get('text', '').strip() 
            for review in reviews_list 
            if review.get('text') and len(review.get('text').strip()) > 5
        ]
        if textos_reviews:
            reviews_por_produto[produto_id] = textos_reviews

print(f"   ✅ {len(reviews_por_produto)} produtos com reviews textuais válidos")

# =============================================================================
# 5. ANÁLISE DE SENTIMENTO E PALAVRAS-CHAVE (VADER)
# =============================================================================

print("\n😊 ANALISANDO SENTIMENTO (VADER)...")
print("-"*80)

analyzer = SentimentIntensityAnalyzer()
resultados_nlp = []

# MUDANÇA: Iterar sobre a coluna correta 'id_anuncio'.
for produto_id in df_produtos['id_anuncio']:
    reviews = reviews_por_produto.get(produto_id, [])
    
    resultado = {
        'id_anuncio': produto_id,
        'possui_reviews_texto': 1 if reviews else 0,
        'num_reviews_analisadas': len(reviews),
        'sentimento_medio_reviews': 0,
        'contagem_alegacao_fraude': 0,
        'contagem_performance_negativa': 0
    }
    
    if reviews:
        texto_completo = ' '.join(reviews).lower()
        sentimentos = [analyzer.polarity_scores(review)['compound'] for review in reviews]
        resultado['sentimento_medio_reviews'] = np.mean(sentimentos)
        resultado['contagem_alegacao_fraude'] = sum(texto_completo.count(p) for p in PALAVRAS_FRAUDE)
        resultado['contagem_performance_negativa'] = sum(texto_completo.count(p) for p in PALAVRAS_PERFORMANCE)
    
    resultados_nlp.append(resultado)

print(f"   ✅ Sentimento calculado para {len(resultados_nlp)} produtos")

# =============================================================================
# 6. GERAR EMBEDDINGS (OpenAI)
# =============================================================================

print(f"\n🤖 GERANDO EMBEDDINGS SEPARADOS COM OpenAI...")
print("-"*80)

embeddings_lista = []

# MUDANÇA: Iterar sobre o novo DataFrame e gerar embeddings separados
for index, row in df_produtos.iterrows():
    produto_id = row['id_anuncio']
    reviews = reviews_por_produto.get(produto_id, [])
    
    # Inicializar embeddings
    embedding_titulo = None
    embedding_descricao = None
    embedding_reviews = None
    
    # 1. Embedding do TÍTULO
    if pd.notna(row.get('titulo')) and row['titulo'].strip():
        try:
            response = client.embeddings.create(
                model=OPENAI_MODEL_EMBEDDING, 
                input=row['titulo'].strip()[:8000]
            )
            embedding_titulo = response.data[0].embedding
        except Exception as e:
            print(f"      ⚠️ Erro no título {produto_id}: {e}")
            embedding_titulo = [0.0] * 1536
    
    # 2. Embedding da DESCRIÇÃO
    if pd.notna(row.get('descricao')) and row['descricao'].strip():
        try:
            descricao = row['descricao'].strip()[:8000]
            response = client.embeddings.create(
                model=OPENAI_MODEL_EMBEDDING, 
                input=descricao
            )
            embedding_descricao = response.data[0].embedding
        except Exception as e:
            print(f"      ⚠️ Erro na descrição {produto_id}: {e}")
            embedding_descricao = [0.0] * 1536
    
    # 3. Embedding das REVIEWS
    if reviews:
        try:
            reviews_texto = ' '.join(reviews)[:8000]
            response = client.embeddings.create(
                model=OPENAI_MODEL_EMBEDDING, 
                input=reviews_texto
            )
            embedding_reviews = response.data[0].embedding
        except Exception as e:
            print(f"      ⚠️ Erro nas reviews {produto_id}: {e}")
            embedding_reviews = [0.0] * 1536
    
    # Adicionar à lista (usar None se não houver texto)
    embeddings_lista.append({
        'id_anuncio': produto_id,
        'embedding_titulo': embedding_titulo,
        'embedding_descricao': embedding_descricao,
        'embedding_reviews': embedding_reviews
    })

    if (index + 1) % 50 == 0:
        print(f"      ✅ {index + 1}/{len(df_produtos)} produtos processados para embeddings...")

print(f"\n   ✅ Embeddings separados gerados para {len(embeddings_lista)} produtos")

# =============================================================================
# 7. MERGE FINAL E SALVAR
# =============================================================================

print(f"\n🔗 FAZENDO MERGE FINAL E SALVANDO...")
print("-"*80)

df_nlp = pd.DataFrame(resultados_nlp)

# Criar DataFrame com embeddings separados
df_embeddings = pd.DataFrame(embeddings_lista)

# Converter embeddings de lista para string JSON para salvar no CSV
for col in ['embedding_titulo', 'embedding_descricao', 'embedding_reviews']:
    df_embeddings[col] = df_embeddings[col].apply(
        lambda x: json.dumps(x) if x is not None else None
    )

# MUDANÇA: Fazer o merge usando 'id_anuncio'.
df_nlp_completo = pd.merge(df_nlp, df_embeddings, on='id_anuncio', how='left')

# Remover duplicatas por id_anuncio (manter primeira ocorrência)
duplicatas_antes = df_nlp_completo.duplicated(subset=['id_anuncio']).sum()
if duplicatas_antes > 0:
    print(f"   🚨 Removendo {duplicatas_antes} duplicatas por id_anuncio")
    df_nlp_completo = df_nlp_completo.drop_duplicates(subset=['id_anuncio'], keep='first').copy()

df_nlp_completo.to_csv(REVIEWS_NLP_CSV, index=False)
print(f"   ✅ Arquivo final salvo em: {REVIEWS_NLP_CSV.name}")
print(f"   📊 Shape final: {df_nlp_completo.shape}")

print("\n" + "="*80)
print("✅ SCRIPT 2 CONCLUÍDO COM SUCESSO!")
print("="*80)

