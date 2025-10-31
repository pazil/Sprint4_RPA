#!/usr/bin/env python3
"""
=============================================================================
SCRIPT 0: UNIFICAR DADOS BRUTOS
=============================================================================
Unifica todos os JSONs dos diferentes datasets (662, 667, 668) em arquivos
consolidados únicos.

INPUT:
- dados_brutos/662/dados_extraidos_ia_gpt4o.json
- dados_brutos/667 e 668/dados_extraidos_ia_gpt4o_COMPLETO.json
- dados_brutos/662/reviews_extraidos_20251005_205046.json
- dados_brutos/667 e 668/664_reviews.json
- dados_brutos/667 e 668/667_reviews.json
- dados_brutos/662/dados_vendedores_20251005_184451.json
- dados_brutos/667 e 668/664_vendedores.json
- dados_brutos/667 e 668/667_vendedores.json

OUTPUT:
- dados_brutos/dados_extraidos_ia_unificado.json
- dados_brutos/reviews_unificado.json
- dados_brutos/vendedores_unificado.json
- dados_brutos/dados_completos_unificado.csv

ESTRUTURA DE UNIFICAÇÃO:
- dataset_javascript: product_id (MLB...)
- reviews: product_id (MLB...)
- vendedores: id (numérico) -> vendedor_id no dataset
"""

import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime

# --- CONFIGURAÇÃO ---
BASE_DIR = Path(__file__).parent.parent
DADOS_BRUTOS_DIR = BASE_DIR / "dados_brutos"
DATA_DIR = BASE_DIR / "data"
SCRIPT_0_DIR = DATA_DIR / "script_0_unificar_dados"

def carregar_json(caminho):
    """Carrega um arquivo JSON de forma segura"""
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"   ⚠️ Erro ao carregar {caminho}: {e}")
        return None

def salvar_json(dados, caminho):
    """Salva dados em formato JSON"""
    try:
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"   ❌ Erro ao salvar {caminho}: {e}")
        return False

def limpar_texto_para_csv(texto):
    """Limpa texto para evitar problemas no CSV"""
    if texto is None:
        return ""
    
    # Converter para string se não for
    texto = str(texto)
    
    # Remover quebras de linha e caracteres problemáticos
    texto = texto.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    
    # Remover múltiplos espaços
    import re
    texto = re.sub(r'\s+', ' ', texto)
    
    # Limitar tamanho para evitar campos muito grandes
    if len(texto) > 1000:
        texto = texto[:1000] + "..."
    
    return texto.strip()

def salvar_csv_seguro(dados, caminho):
    """Salva dados em formato CSV de forma segura, tratando textos"""
    import csv
    
    if not dados:
        print(f"   ⚠️ Nenhum dado para salvar em CSV")
        return False
    
    # Obter todas as chaves únicas de todos os produtos
    todas_chaves = set()
    for produto in dados:
        todas_chaves.update(produto.keys())
    
    # Ordenar chaves para consistência
    chaves_ordenadas = sorted(todas_chaves)
    
    try:
        with open(caminho, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=chaves_ordenadas)
            writer.writeheader()
            
            for produto in dados:
                # Limpar dados de texto para cada produto
                produto_limpo = {}
                for chave, valor in produto.items():
                    if isinstance(valor, str):
                        produto_limpo[chave] = limpar_texto_para_csv(valor)
                    else:
                        produto_limpo[chave] = valor
                
                writer.writerow(produto_limpo)
        
        return True
    except Exception as e:
        print(f"   ❌ Erro ao salvar CSV {caminho}: {e}")
        return False

def unificar_datasets_ia():
    """Unifica apenas os datasets JavaScript da pasta 667 e 668"""
    print("\n📊 UNIFICANDO DATASETS JAVASCRIPT (667 e 668)...")
    print("-"*80)
    
    datasets_ia = []
    
    # Dataset 664
    caminho_664 = DADOS_BRUTOS_DIR / "667 e 668" / "664_dataset_javascript_sem_reviews_20250930_012112.json"
    if caminho_664.exists():
        dados_664 = carregar_json(caminho_664)
        if dados_664 and 'produtos' in dados_664:
            # Adicionar tipo de cartucho
            for produto in dados_664['produtos']:
                produto['tipo_cartucho'] = '664'
                produto['id_produto'] = produto.get('id')  # Padronizar nome do campo
            datasets_ia.extend(dados_664['produtos'])
            print(f"   ✅ Dataset 664: {len(dados_664['produtos'])} produtos")
    else:
        print(f"   ❌ Arquivo não encontrado: {caminho_664}")
    
    # Dataset 667
    caminho_667 = DADOS_BRUTOS_DIR / "667 e 668" / "667_dataset_javascript_sem_reviews_20250930_002906.json"
    if caminho_667.exists():
        dados_667 = carregar_json(caminho_667)
        if dados_667 and 'produtos' in dados_667:
            # Adicionar tipo de cartucho
            for produto in dados_667['produtos']:
                produto['tipo_cartucho'] = '667'
                produto['id_produto'] = produto.get('id')  # Padronizar nome do campo
            datasets_ia.extend(dados_667['produtos'])
            print(f"   ✅ Dataset 667: {len(dados_667['produtos'])} produtos")
    else:
        print(f"   ❌ Arquivo não encontrado: {caminho_667}")
    
    print(f"   📊 Total unificado: {len(datasets_ia)} produtos")
    
    # Criar pasta específica do Script 0 se não existir
    SCRIPT_0_DIR.mkdir(parents=True, exist_ok=True)
    
    return datasets_ia

def unificar_reviews():
    """Unifica apenas os arquivos de reviews da pasta 667 e 668"""
    print("\n💬 UNIFICANDO REVIEWS (667 e 668)...")
    print("-"*80)
    
    reviews_unificadas = []
    
    # Reviews 664
    caminho_664 = DADOS_BRUTOS_DIR / "667 e 668" / "664_reviews.json"
    if caminho_664.exists():
        reviews_664 = carregar_json(caminho_664)
        if reviews_664:
            reviews_unificadas.extend(reviews_664)
            print(f"   ✅ Reviews 664: {len(reviews_664)} produtos")
    else:
        print(f"   ❌ Arquivo não encontrado: {caminho_664}")
    
    # Reviews 667
    caminho_667 = DADOS_BRUTOS_DIR / "667 e 668" / "667_reviews.json"
    if caminho_667.exists():
        reviews_667 = carregar_json(caminho_667)
        if reviews_667:
            reviews_unificadas.extend(reviews_667)
            print(f"   ✅ Reviews 667: {len(reviews_667)} produtos")
    else:
        print(f"   ❌ Arquivo não encontrado: {caminho_667}")
    
    print(f"   📊 Total unificado: {len(reviews_unificadas)} produtos")
    
    # Salvar unificado
    caminho_saida = DATA_DIR / "reviews_unificado.json"
    if salvar_json(reviews_unificadas, caminho_saida):
        print(f"   ✅ Salvo em: {caminho_saida}")
    
    return reviews_unificadas

def unificar_vendedores():
    """Unifica apenas os arquivos de vendedores da pasta 667 e 668"""
    print("\n👥 UNIFICANDO VENDEDORES (667 e 668)...")
    print("-"*80)
    
    vendedores_unificados = []
    
    # Vendedores 664
    caminho_664 = DADOS_BRUTOS_DIR / "667 e 668" / "664_vendedores.json"
    if caminho_664.exists():
        vendedores_664 = carregar_json(caminho_664)
        if vendedores_664 and 'dados_vendedores' in vendedores_664:
            vendedores_unificados.extend(vendedores_664['dados_vendedores'])
            print(f"   ✅ Vendedores 664: {len(vendedores_664['dados_vendedores'])} vendedores")
    else:
        print(f"   ❌ Arquivo não encontrado: {caminho_664}")
    
    # Vendedores 667
    caminho_667 = DADOS_BRUTOS_DIR / "667 e 668" / "667_vendedores.json"
    if caminho_667.exists():
        vendedores_667 = carregar_json(caminho_667)
        if vendedores_667 and 'dados_vendedores' in vendedores_667:
            vendedores_unificados.extend(vendedores_667['dados_vendedores'])
            print(f"   ✅ Vendedores 667: {len(vendedores_667['dados_vendedores'])} vendedores")
    else:
        print(f"   ❌ Arquivo não encontrado: {caminho_667}")
    
    # Remover duplicatas baseado no ID
    vendedores_unicos = {}
    for vendedor in vendedores_unificados:
        vendedor_id = vendedor.get('id')
        if vendedor_id and vendedor_id not in vendedores_unicos:
            vendedores_unicos[vendedor_id] = vendedor
    
    vendedores_finais = list(vendedores_unicos.values())
    print(f"   📊 Total unificado (sem duplicatas): {len(vendedores_finais)} vendedores")
    
    return vendedores_finais

def criar_dataset_completo_json(datasets_ia, reviews_unificadas, vendedores_finais):
    """Cria um único JSON completo com todos os dados unificados"""
    print("\n📊 CRIANDO DATASET COMPLETO JSON...")
    print("-"*80)
    
    # Criar dicionário de vendedores para lookup rápido
    vendedores_dict = {}
    for vendedor in vendedores_finais:
        vendedor_id = vendedor.get('id')
        if vendedor_id:
            vendedores_dict[vendedor_id] = vendedor
    
    # Criar dicionário de reviews para lookup rápido
    reviews_dict = {}
    for produto_reviews in reviews_unificadas:
        product_id = produto_reviews.get('product_id')
        if product_id:
            reviews_dict[product_id] = produto_reviews
    
    # Expandir dados de vendedores e reviews para cada produto
    produtos_completos = []
    
    for produto in datasets_ia:
        produto_id = produto.get('id_produto')  # "MLB36751629"
        vendedor_id = produto.get('seller_id')  # "1737442603" (string)
        
        # Dados básicos do produto
        produto_completo = produto.copy()
        
        # Adicionar dados do vendedor
        # Converter seller_id (string) para int para buscar no dicionário de vendedores
        # Usar int64 para evitar overflow com IDs grandes
        try:
            vendedor_id_int = int(vendedor_id) if vendedor_id and vendedor_id.isdigit() else None
        except (ValueError, OverflowError):
            vendedor_id_int = None
        if vendedor_id_int and vendedor_id_int in vendedores_dict:
            vendedor = vendedores_dict[vendedor_id_int]
            produto_completo.update({
                'vendedor_nome': vendedor.get('nickname', ''),
                'vendedor_estado': vendedor.get('address', {}).get('state', ''),
                'vendedor_cidade': vendedor.get('address', {}).get('city', ''),
                'vendedor_tipo': vendedor.get('user_type', ''),
                'vendedor_reputation_level': vendedor.get('seller_reputation', {}).get('level_id', ''),
                'vendedor_power_seller_status': vendedor.get('seller_reputation', {}).get('power_seller_status', ''),
                'vendedor_total_transacoes': vendedor.get('seller_reputation', {}).get('transactions', {}).get('total', 0),
                'vendedor_status': vendedor.get('status', {}).get('site_status', '')
            })
        
        # Adicionar dados de reviews
        if produto_id in reviews_dict:
            reviews_data = reviews_dict[produto_id]
            produto_completo.update({
                'rating_medio': reviews_data.get('general_data', {}).get('average_rating', 0),
                'total_reviews': reviews_data.get('general_data', {}).get('total_reviews', 0),
                'ai_summary': reviews_data.get('ai_summary', {}).get('summary', ''),
                'reviews_com_texto': len([r for r in reviews_data.get('reviews', []) if r.get('text', '').strip()]),
                'reviews_com_imagens': len([r for r in reviews_data.get('reviews', []) if r.get('has_images', False)])
            })
            
            # Adicionar distribuição de ratings
            reviews_list = reviews_data.get('reviews', [])
            rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for review in reviews_list:
                rating = review.get('rating')
                if rating in rating_counts:
                    rating_counts[rating] += 1
            
            produto_completo.update({
                'rating_1_estrela': rating_counts[1],
                'rating_2_estrelas': rating_counts[2],
                'rating_3_estrelas': rating_counts[3],
                'rating_4_estrelas': rating_counts[4],
                'rating_5_estrelas': rating_counts[5]
            })
        else:
            # Valores padrão para produtos sem reviews
            produto_completo.update({
                'rating_medio': 0,
                'total_reviews': 0,
                'ai_summary': '',
                'reviews_com_texto': 0,
                'reviews_com_imagens': 0,
                'rating_1_estrela': 0,
                'rating_2_estrelas': 0,
                'rating_3_estrelas': 0,
                'rating_4_estrelas': 0,
                'rating_5_estrelas': 0
            })
        
        produtos_completos.append(produto_completo)
    
    # Salvar JSON único
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho_json = SCRIPT_0_DIR / f"dataset_completo_unificado_{timestamp}.json"
    
    try:
        if salvar_json(produtos_completos, caminho_json):
            print(f"   ✅ JSON salvo em: {caminho_json}")
            print(f"   📊 Total de produtos: {len(produtos_completos)}")
    except Exception as e:
        print(f"   ❌ Erro ao salvar JSON: {e}")
    
    # Salvar CSV também
    caminho_csv = SCRIPT_0_DIR / f"dataset_completo_unificado_{timestamp}.csv"
    try:
        salvar_csv_seguro(produtos_completos, caminho_csv)
        print(f"   ✅ CSV salvo em: {caminho_csv}")
    except Exception as e:
        print(f"   ❌ Erro ao salvar CSV: {e}")
    
    return produtos_completos

def main():
    print("="*80)
    print("🔄 SCRIPT 0: UNIFICAR DADOS BRUTOS")
    print("="*80)
    
    # Verificar se a pasta de dados brutos existe
    if not DADOS_BRUTOS_DIR.exists():
        print(f"❌ ERRO: Pasta {DADOS_BRUTOS_DIR} não encontrada!")
        return
    
    print(f"📂 Pasta de dados brutos: {DADOS_BRUTOS_DIR}")
    print(f"📂 Pasta de saída (data): {DATA_DIR}")
    
    # 1. Unificar datasets de IA
    datasets_ia = unificar_datasets_ia()
    
    # 2. Unificar reviews
    reviews_unificadas = unificar_reviews()
    
    # 3. Unificar vendedores
    vendedores_finais = unificar_vendedores()
    
    # 4. Criar dataset completo JSON único
    produtos_completos = criar_dataset_completo_json(datasets_ia, reviews_unificadas, vendedores_finais)
    
    # 5. Resumo final
    print("\n" + "="*80)
    print("📈 RESUMO FINAL")
    print("="*80)
    
    print(f"\n✅ ARQUIVOS CRIADOS:")
    print(f"   📊 dataset_completo_unificado_*.json: {len(produtos_completos)} produtos completos")
    print(f"   📋 dataset_completo_unificado_*.csv: {len(produtos_completos)} produtos completos")
    
    print(f"\n📊 ESTATÍSTICAS DO DATASET FINAL:")
    print(f"   Total de produtos: {len(produtos_completos)}")
    
    # Estatísticas por tipo de cartucho
    tipos_cartucho = {}
    for produto in produtos_completos:
        tipo = produto.get('tipo_cartucho', 'desconhecido')
        tipos_cartucho[tipo] = tipos_cartucho.get(tipo, 0) + 1
    
    if tipos_cartucho:
        print(f"\n📦 DISTRIBUIÇÃO POR TIPO DE CARTUCHO:")
        for tipo, count in tipos_cartucho.items():
            print(f"   {tipo}: {count} produtos")
    
    # Estatísticas de reviews
    produtos_com_reviews = len([p for p in produtos_completos if (p.get('total_reviews') or 0) > 0])
    total_reviews = sum(p.get('total_reviews') or 0 for p in produtos_completos)
    print(f"\n💬 REVIEWS:")
    print(f"   Produtos com reviews: {produtos_com_reviews} ({produtos_com_reviews/len(produtos_completos)*100:.1f}%)")
    print(f"   Total de reviews: {total_reviews}")
    
    # Estatísticas de vendedores
    vendedores_unicos = len(set(p.get('vendedor_id') for p in produtos_completos if p.get('vendedor_id')))
    print(f"\n👥 VENDEDORES:")
    print(f"   Vendedores únicos: {vendedores_unicos}")
    
    print("\n" + "="*80)
    print("✅ SCRIPT 0 CONCLUÍDO COM SUCESSO!")
    print("="*80)
    print(f"\n📁 Próximo passo: python 1_processar_features_basicas.py")
    print("   (usando o arquivo JSON unificado como entrada)")

if __name__ == "__main__":
    main()
