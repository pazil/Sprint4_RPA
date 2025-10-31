#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script 1: Filtrar Campos Essenciais
===================================

Este script filtra o dataset unificado mantendo apenas os campos essenciais
para análise de fraude, conforme especificado na lista definitiva.

Entrada: dataset_completo_unificado_*.json
Saída: dataset_campos_essenciais_*.json + *.csv
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Importar configurações
from _config import DATA_DIR, BASE_DIR

# Pasta específica para Script 1
SCRIPT_1_DIR = DATA_DIR / "script_1_filtrar_campos"

def carregar_json(caminho: Path) -> Optional[Any]:
    """Carrega dados de um arquivo JSON"""
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"   ⚠️ Erro ao carregar {caminho}: {e}")
        return None

def salvar_json(dados: Any, caminho: Path) -> bool:
    """Salva dados em formato JSON"""
    try:
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"   ❌ Erro ao salvar {caminho}: {e}")
        return False

def extrair_campo_aninhado(dados: Dict, caminho: str, default: Any = None) -> Any:
    """
    Extrai campo de um dicionário aninhado usando notação de ponto
    Ex: 'dados_brutos.melidata.catalog_product_id'
    """
    try:
        keys = caminho.split('.')
        valor = dados
        for key in keys:
            if isinstance(valor, dict) and key in valor:
                valor = valor[key]
            else:
                return default
        return valor
    except Exception:
        return default

# Função removida - reviews_texto_lista não será mais extraído

def extrair_conexoes_vendedores(dados_brutos: Dict) -> List[str]:
    """Extrai lista de seller_ids de vendedores alternativos"""
    try:
        alternativas = extrair_campo_aninhado(dados_brutos, 'melidata.alternative_buying_options', [])
        if not isinstance(alternativas, list):
            return []
        
        seller_ids = []
        for alt in alternativas:
            if isinstance(alt, dict) and 'seller_id' in alt:
                seller_id = str(alt['seller_id'])
                if seller_id:
                    seller_ids.append(seller_id)
        return seller_ids
    except Exception:
        return []

def extrair_origem_envio(dados_brutos: Dict) -> Optional[str]:
    """Extrai origem de envio do shipping_promise"""
    try:
        origins = extrair_campo_aninhado(dados_brutos, 'melidata.shipping_promise.address_options', [])
        if isinstance(origins, list) and len(origins) > 0:
            first_origin = origins[0]
            if isinstance(first_origin, dict) and 'origins' in first_origin:
                origins_list = first_origin['origins']
                if isinstance(origins_list, list) and len(origins_list) > 0:
                    return origins_list[0].get('value')
        return None
    except Exception:
        return None

def filtrar_campos_essenciais(produto: Dict) -> Dict:
    """
    Filtra e extrai apenas os campos essenciais de um produto
    """
    dados_brutos = produto.get('dados_brutos', {})
    
    # Identificadores Essenciais
    id_anuncio = produto.get('id', '')
    catalog_product_id = extrair_campo_aninhado(dados_brutos, 'melidata.catalog_product_id', '')
    seller_id = produto.get('seller_id', '')
    link_anuncio = produto.get('link', '')
    
    # Features do Produto e Anúncio
    titulo = produto.get('titulo', '')
    preco_atual = produto.get('preco', '')
    imagem_url_principal = produto.get('imagem_url', '')
    descricao = produto.get('descricao', '')
    condicao = produto.get('condicao', '')
    marca = produto.get('marca', '')
    modelo = produto.get('modelo', '')
    
    # Features do Vendedor
    vendedor_nome = produto.get('vendedor_nome', None)
    if vendedor_nome == '' or vendedor_nome is None:
        # Se não há nome do vendedor, usar um padrão baseado no seller_id
        seller_id = produto.get('seller_id', '')
        vendedor_nome = f'Vendedor_{seller_id}' if seller_id else 'Vendedor_Desconhecido'
    reputation_level = produto.get('reputation_level', '')
    power_seller_status = produto.get('power_seller_status', '')
    vendedor_total_transacoes = produto.get('vendedor_total_transacoes', 0)
    official_store_id = extrair_campo_aninhado(dados_brutos, 'melidata.official_store_id', '')
    
    # Features de Review
    rating_medio_produto = extrair_campo_aninhado(dados_brutos, 'melidata.reviews.rate', None)
    if rating_medio_produto is None:
        rating_medio_produto = produto.get('rating_estrelas', None)
    
    total_reviews_produto = extrair_campo_aninhado(dados_brutos, 'melidata.reviews.count', 0)
    distribuicao_estrelas = produto.get('distribuicao_estrelas', '')
    
    # Features para o Grafo e Heurísticas
    conexoes_vendedores_alt = extrair_conexoes_vendedores(dados_brutos)
    logistic_type = extrair_campo_aninhado(dados_brutos, 'melidata.logistic_type', '')
    origem_envio = extrair_origem_envio(dados_brutos)
    
    # Montar produto filtrado
    produto_filtrado = {
        # Identificadores Essenciais
        'id_anuncio': id_anuncio,
        'catalog_product_id': catalog_product_id,
        'seller_id': seller_id,
        'link_anuncio': link_anuncio,
        
        # Features do Produto e Anúncio
        'titulo': titulo,
        'preco_atual': preco_atual,
        'imagem_url_principal': imagem_url_principal,
        'descricao': descricao,
        'condicao': condicao,
        'marca': marca,
        'modelo': modelo,
        
        # Features do Vendedor
        'vendedor_nome': vendedor_nome,
        'reputation_level': reputation_level,
        'power_seller_status': power_seller_status,
        'vendedor_total_transacoes': vendedor_total_transacoes,
        'official_store_id': official_store_id,
        
        # Features de Review
        'rating_medio_produto': rating_medio_produto,
        'total_reviews_produto': total_reviews_produto,
        'distribuicao_estrelas': distribuicao_estrelas,
        
        # Features para o Grafo e Heurísticas
        'conexoes_vendedores_alt': conexoes_vendedores_alt,
        'logistic_type': logistic_type,
        'origem_envio': origem_envio
    }
    
    return produto_filtrado

def processar_dataset_essencial():
    """Processa o dataset unificado e extrai apenas os campos essenciais"""
    print("="*80)
    print("🔍 SCRIPT 1: FILTRAR CAMPOS ESSENCIAIS")
    print("="*80)
    
    # Encontrar arquivo unificado mais recente do Script 0
    pattern = str(DATA_DIR / "script_0_unificar_dados" / "dataset_completo_unificado_*.json")
    import glob
    arquivos_json = glob.glob(pattern)
    
    if not arquivos_json:
        print(f"❌ ERRO: Nenhum arquivo dataset_completo_unificado_*.json encontrado em {DATA_DIR}/script_0_unificar_dados")
        return
    
    # Pegar o mais recente
    arquivo_mais_recente = max(arquivos_json, key=os.path.getctime)
    print(f"📂 Arquivo de entrada: {arquivo_mais_recente}")
    
    # Carregar dataset unificado
    print("\n📊 CARREGANDO DATASET UNIFICADO...")
    dataset_unificado = carregar_json(Path(arquivo_mais_recente))
    
    if not dataset_unificado:
        print("❌ ERRO: Não foi possível carregar o dataset unificado")
        return
    
    print(f"   ✅ Dataset carregado: {len(dataset_unificado)} produtos")
    
    # Processar cada produto
    print("\n🔍 FILTRANDO CAMPOS ESSENCIAIS...")
    print("-"*80)
    
    produtos_essenciais = []
    produtos_com_erro = 0
    
    for i, produto in enumerate(dataset_unificado):
        try:
            produto_filtrado = filtrar_campos_essenciais(produto)
            produtos_essenciais.append(produto_filtrado)
            
            if (i + 1) % 50 == 0:
                print(f"   📊 Processados: {i + 1}/{len(dataset_unificado)} produtos")
                
        except Exception as e:
            produtos_com_erro += 1
            print(f"   ⚠️ Erro no produto {i + 1}: {e}")
    
    print(f"\n✅ Processamento concluído:")
    print(f"   📊 Produtos processados: {len(produtos_essenciais)}")
    print(f"   ⚠️ Produtos com erro: {produtos_com_erro}")
    
    # Criar pasta específica do Script 1 se não existir
    SCRIPT_1_DIR.mkdir(parents=True, exist_ok=True)
    
    # Salvar JSON essencial
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo_json = SCRIPT_1_DIR / f"dataset_campos_essenciais_{timestamp}.json"
    
    print(f"\n💾 SALVANDO ARQUIVOS...")
    print("-"*80)
    
    if salvar_json(produtos_essenciais, arquivo_json):
        print(f"   ✅ JSON salvo: {arquivo_json}")
    
    # Salvar CSV essencial
    arquivo_csv = SCRIPT_1_DIR / f"dataset_campos_essenciais_{timestamp}.csv"
    if salvar_csv_essencial(produtos_essenciais, arquivo_csv):
        print(f"   ✅ CSV salvo: {arquivo_csv}")
    
    # Estatísticas finais
    print(f"\n📈 ESTATÍSTICAS FINAIS:")
    print("-"*80)
    
    # Contar campos preenchidos
    campos_stats = {}
    for produto in produtos_essenciais:
        for campo, valor in produto.items():
            if campo not in campos_stats:
                campos_stats[campo] = {'preenchido': 0, 'total': 0}
            
            campos_stats[campo]['total'] += 1
            if valor is not None and valor != '' and valor != []:
                campos_stats[campo]['preenchido'] += 1
    
    print(f"\n📊 COBERTURA DOS CAMPOS:")
    for campo, stats in campos_stats.items():
        percentual = (stats['preenchido'] / stats['total']) * 100
        print(f"   {campo}: {stats['preenchido']}/{stats['total']} ({percentual:.1f}%)")
    
    # Estatísticas específicas
    produtos_com_conexoes = len([p for p in produtos_essenciais if p.get('conexoes_vendedores_alt')])
    produtos_fulfillment = len([p for p in produtos_essenciais if p.get('logistic_type') == 'fulfillment'])
    
    print(f"\n📊 ESTATÍSTICAS ESPECÍFICAS:")
    print(f"   Produtos com conexões de vendedores: {produtos_com_conexoes} ({produtos_com_conexoes/len(produtos_essenciais)*100:.1f}%)")
    print(f"   Produtos fulfillment: {produtos_fulfillment} ({produtos_fulfillment/len(produtos_essenciais)*100:.1f}%)")
    
    print("\n" + "="*80)
    print("✅ SCRIPT 1 CONCLUÍDO COM SUCESSO!")
    print("="*80)
    
    return produtos_essenciais

def salvar_csv_essencial(dados: List[Dict], caminho: Path) -> bool:
    """Salva dados essenciais em formato CSV com tratamento correto de listas e dicionários"""
    import csv
    import json
    
    if not dados:
        print(f"   ⚠️ Nenhum dado para salvar em CSV")
        return False
    
    # Obter todas as chaves únicas
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
                # Limpar dados de texto para CSV
                produto_limpo = {}
                for chave, valor in produto.items():
                    if isinstance(valor, str):
                        # Limpar quebras de linha e caracteres problemáticos
                        valor_limpo = valor.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                        # Limitar tamanho
                        if len(valor_limpo) > 1000:
                            valor_limpo = valor_limpo[:1000] + "..."
                        produto_limpo[chave] = valor_limpo
                    elif isinstance(valor, list):
                        # Converter lista para string JSON
                        produto_limpo[chave] = json.dumps(valor, ensure_ascii=False)
                    elif isinstance(valor, dict):
                        # Converter dicionário para string JSON
                        produto_limpo[chave] = json.dumps(valor, ensure_ascii=False)
                    else:
                        produto_limpo[chave] = valor
                
                writer.writerow(produto_limpo)
        
        return True
    except Exception as e:
        print(f"   ❌ Erro ao salvar CSV {caminho}: {e}")
        return False

if __name__ == "__main__":
    processar_dataset_essencial()
