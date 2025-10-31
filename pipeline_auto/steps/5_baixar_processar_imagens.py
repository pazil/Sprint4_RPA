"""
=============================================================================
SCRIPT 5: BAIXAR E PROCESSAR IMAGENS
=============================================================================
Baixa imagens dos produtos e calcula pHash (perceptual hash) para detectar
imagens duplicadas/reutilizadas.

INPUT:
- data/script_3_features_basicas/dataset_com_features_basicas_*.csv (coluna: imagem_url_principal)

OUTPUT:
- data/script_5_imagens/imagens_baixadas/ (pasta com imagens baixadas)
- data/script_5_imagens/hashes_imagens.csv (id_anuncio, phash, contagem_reuso_imagem)
"""

import pandas as pd
import numpy as np
import requests
import os
from PIL import Image
import imagehash
from pathlib import Path
from tqdm import tqdm
import time
import warnings
warnings.filterwarnings('ignore')

# Importar configurações
import sys
sys.path.append(str(Path(__file__).parent))
from _config import *

print("="*80)
print("🖼️ SCRIPT 5: BAIXAR E PROCESSAR IMAGENS")
print("="*80)

# =============================================================================
# 1. VERIFICAR DEPENDÊNCIAS
# =============================================================================

print("\n📦 VERIFICANDO DEPENDÊNCIAS...")
print("-"*80)

try:
    from PIL import Image
    print("   ✅ Pillow instalado")
except ImportError:
    print("   ❌ Pillow não encontrado!")
    print("   Execute: pip install Pillow")
    sys.exit(1)

try:
    import imagehash
    print("   ✅ imagehash instalado")
except ImportError:
    print("   ❌ imagehash não encontrado!")
    print("   Execute: pip install imagehash")
    sys.exit(1)

try:
    import requests
    print("   ✅ requests instalado")
except ImportError:
    print("   ❌ requests não encontrado!")
    print("   Execute: pip install requests")
    sys.exit(1)

# =============================================================================
# 2. CARREGAR DADOS
# =============================================================================

print("\n📂 CARREGANDO DADOS...")
print("-"*80)

# Usar o arquivo mais recente do Script 3
DATASET_FEATURES_BASICAS = max(SCRIPT_3_DIR.glob("*.csv"), key=lambda x: x.stat().st_mtime)
print(f"Carregando: {DATASET_FEATURES_BASICAS.name}")
df = pd.read_csv(DATASET_FEATURES_BASICAS)
print(f"   ✅ {len(df)} produtos carregados")

# Verificar se tem coluna de URL de imagem
if 'imagem_url_principal' not in df.columns:
    print("   ❌ Coluna 'imagem_url_principal' não encontrada!")
    sys.exit(1)

produtos_com_url = df['imagem_url_principal'].notna().sum()
print(f"   ✅ {produtos_com_url} produtos com URL de imagem")

# =============================================================================
# 3. CRIAR PASTA DE IMAGENS
# =============================================================================

print(f"\n📁 CRIANDO PASTA DE IMAGENS...")
print("-"*80)

# Usar SCRIPT_5_DIR para manter consistência com a nova estrutura
SCRIPT_5_DIR.mkdir(parents=True, exist_ok=True)
IMAGENS_DIR = SCRIPT_5_DIR / "imagens_baixadas"
IMAGENS_DIR.mkdir(parents=True, exist_ok=True)
print(f"   ✅ Pasta criada: {IMAGENS_DIR}")

# =============================================================================
# 4. BAIXAR IMAGENS
# =============================================================================

print(f"\n⬇️ BAIXANDO IMAGENS...")
print("-"*80)
print(f"   ⏳ Isso pode levar alguns minutos...")
print(f"   Timeout: {IMAGE_DOWNLOAD_TIMEOUT}s por imagem")

# Contadores
sucessos = 0
erros = 0
ja_existiam = 0
sem_url = 0

# Headers para simular navegador
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Baixar cada imagem
for index, row in tqdm(df.iterrows(), total=len(df), desc="Baixando"):
    id_produto = row['id_anuncio']
    url = row['imagem_url_principal']
    
    # Pular se não tem URL
    if pd.isna(url) or not url:
        sem_url += 1
        continue
    
    # Nome do arquivo (extensão baseada na URL ou .jpg padrão)
    try:
        ext = '.jpg'  # Mercado Livre geralmente usa .jpg ou .webp
        if 'webp' in url.lower():
            ext = '.webp'
        elif 'png' in url.lower():
            ext = '.png'
    except:
        ext = '.jpg'
    
    nome_arquivo = f"{id_produto}{ext}"
    caminho_arquivo = IMAGENS_DIR / nome_arquivo
    
    # Pular se já existe
    if caminho_arquivo.exists():
        ja_existiam += 1
        continue
    
    # Baixar
    try:
        response = requests.get(
            url,
            stream=True,
            timeout=IMAGE_DOWNLOAD_TIMEOUT,
            headers=headers
        )
        response.raise_for_status()
        
        # Salvar
        with open(caminho_arquivo, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        sucessos += 1
        
        # Delay para não sobrecarregar servidor
        time.sleep(0.5)
        
    except Exception as e:
        # print(f"   ⚠️ Erro em {id_produto}: {e}")
        erros += 1

print(f"\n   📊 RELATÓRIO DE DOWNLOAD:")
print(f"      ✅ Baixadas com sucesso: {sucessos}")
print(f"      ⏩ Já existiam (puladas): {ja_existiam}")
print(f"      ❌ Sem URL: {sem_url}")
print(f"      ⚠️ Erros de download: {erros}")

# =============================================================================
# 5. CALCULAR pHASH
# =============================================================================

print(f"\n🔢 CALCULANDO pHASH DAS IMAGENS...")
print("-"*80)

dados_hashes = []
hash_calculados = 0
hash_erros = 0

# Listar arquivos de imagem
arquivos_imagem = list(IMAGENS_DIR.glob('*'))
print(f"   Total de arquivos encontrados: {len(arquivos_imagem)}")

for arquivo in tqdm(arquivos_imagem, desc="Calculando pHash"):
    if arquivo.is_file():
        # Extrair ID do produto do nome do arquivo
        id_produto = arquivo.stem
        
        try:
            # Calcular pHash
            img = Image.open(arquivo)
            phash = str(imagehash.phash(img))
            
            dados_hashes.append({
                'id_anuncio': id_produto,
                'nome_arquivo': arquivo.name,
                'phash': phash
            })
            hash_calculados += 1
            
        except Exception as e:
            # print(f"   ⚠️ Erro ao calcular hash de {arquivo.name}: {e}")
            dados_hashes.append({
                'id_anuncio': id_produto,
                'nome_arquivo': arquivo.name,
                'phash': 'ERRO'
            })
            hash_erros += 1

print(f"\n   📊 RELATÓRIO DE pHASH:")
print(f"      ✅ Hashes calculados: {hash_calculados}")
print(f"      ⚠️ Erros: {hash_erros}")

# =============================================================================
# 6. CONTAR REUSO DE IMAGENS
# =============================================================================

print(f"\n🔍 DETECTANDO IMAGENS REUTILIZADAS...")
print("-"*80)

df_hashes = pd.DataFrame(dados_hashes)

# Contar quantos produtos usam cada hash
hash_counts = df_hashes[df_hashes['phash'] != 'ERRO']['phash'].value_counts()

# Adicionar contagem de reuso
df_hashes['contagem_reuso_imagem'] = df_hashes['phash'].map(hash_counts).fillna(0).astype(int)

# Para hashes com erro, usar 0
df_hashes.loc[df_hashes['phash'] == 'ERRO', 'contagem_reuso_imagem'] = 0

# Estatísticas
imagens_unicas = len(hash_counts)
imagens_reutilizadas = (hash_counts > 1).sum()
max_reuso = hash_counts.max() if len(hash_counts) > 0 else 0

print(f"   ✅ Imagens únicas: {imagens_unicas}")
print(f"   ⚠️ Imagens reutilizadas (>1 produto): {imagens_reutilizadas}")
print(f"   📊 Máximo de reuso: {max_reuso}x")

if imagens_reutilizadas > 0:
    print(f"\n   🔝 TOP 5 IMAGENS MAIS REUTILIZADAS:")
    for i, (phash_val, count) in enumerate(hash_counts.head(5).items(), 1):
        # Pegar IDs dos produtos que usam este hash
        produtos = df_hashes[df_hashes['phash'] == phash_val]['id_anuncio'].tolist()
        print(f"      {i}. Hash: {phash_val[:16]}... | Usado {count}x")
        print(f"         Produtos: {', '.join(map(str, produtos[:3]))}{'...' if len(produtos) > 3 else ''}")

# =============================================================================
# 7. SALVAR RESULTADO
# =============================================================================

print(f"\n💾 SALVANDO RESULTADO...")
print("-"*80)

# Salvar CSV de hashes na pasta do Script 5
HASHES_IMAGENS_CSV = SCRIPT_5_DIR / "hashes_imagens.csv"
df_hashes.to_csv(HASHES_IMAGENS_CSV, index=False)
print(f"   ✅ Salvo em: {HASHES_IMAGENS_CSV}")
print(f"   📊 Shape: {df_hashes.shape}")

# =============================================================================
# 8. RESUMO FINAL
# =============================================================================

print("\n" + "="*80)
print("📈 RESUMO DO PROCESSAMENTO DE IMAGENS")
print("="*80)

print(f"\n✅ DOWNLOAD:")
print(f"   Baixadas: {sucessos}")
print(f"   Já existiam: {ja_existiam}")
print(f"   Erros: {erros}")
print(f"   Sem URL: {sem_url}")

print(f"\n✅ pHASH:")
print(f"   Calculados: {hash_calculados}")
print(f"   Erros: {hash_erros}")

print(f"\n✅ ANÁLISE DE REUSO:")
print(f"   Imagens únicas: {imagens_unicas}")
print(f"   Imagens reutilizadas: {imagens_reutilizadas}")
print(f"   Máximo de reuso: {max_reuso}x")

print(f"\n📊 DISTRIBUIÇÃO DE REUSO:")
reuso_0 = (df_hashes['contagem_reuso_imagem'] == 0).sum()
reuso_1 = (df_hashes['contagem_reuso_imagem'] == 1).sum()
reuso_2_5 = ((df_hashes['contagem_reuso_imagem'] >= 2) & (df_hashes['contagem_reuso_imagem'] <= 5)).sum()
reuso_6_10 = ((df_hashes['contagem_reuso_imagem'] >= 6) & (df_hashes['contagem_reuso_imagem'] <= 10)).sum()
reuso_10_plus = (df_hashes['contagem_reuso_imagem'] > 10).sum()

print(f"   Sem hash (erro): {reuso_0}")
print(f"   Única (1x): {reuso_1}")
print(f"   Baixo reuso (2-5x): {reuso_2_5}")
print(f"   Médio reuso (6-10x): {reuso_6_10}")
print(f"   Alto reuso (>10x): {reuso_10_plus} ⚠️")

print("\n" + "="*80)
print("✅ SCRIPT 3 CONCLUÍDO COM SUCESSO!")
print("="*80)
print(f"\n📁 Próximo passo: python 4_criar_target_merge.py")


