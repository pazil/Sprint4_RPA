#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para processar todos os arquivos JSON extraídos em data/dados_extraidos/lote/
e gerar um único arquivo final com todos os produtos e seus reviews.

Ignora arquivos que começam com 'consolidado...'
Para cada par de arquivos (produtos.json + reviews.json), une os dados e adiciona
uma feature 'todos_reviews' em cada produto.
"""

import json
import pandas as pd
from datetime import datetime
import os
import glob
from typing import Dict, List, Any, Tuple
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def listar_arquivos_lote(diretorio_lote: str) -> Tuple[List[str], List[str]]:
    """
    Lista todos os arquivos JSON na pasta lote, separando produtos e reviews.
    Ignora arquivos que começam com 'consolidado...'
    
    Returns:
        Tuple com listas de arquivos de produtos e reviews
    """
    # Buscar todos os arquivos JSON
    arquivos_json = glob.glob(os.path.join(diretorio_lote, "*.json"))
    
    # Filtrar arquivos consolidado
    arquivos_json = [f for f in arquivos_json if not os.path.basename(f).startswith('consolidado')]
    
    # Separar produtos e reviews
    arquivos_produtos = []
    arquivos_reviews = []
    
    for arquivo in arquivos_json:
        nome_arquivo = os.path.basename(arquivo)
        if nome_arquivo.endswith('_reviews.json'):
            arquivos_reviews.append(arquivo)
        elif nome_arquivo.endswith('.json') and not nome_arquivo.endswith('_reviews.json'):
            arquivos_produtos.append(arquivo)
    
    logger.info(f"Encontrados {len(arquivos_produtos)} arquivos de produtos")
    logger.info(f"Encontrados {len(arquivos_reviews)} arquivos de reviews")
    
    return arquivos_produtos, arquivos_reviews

def encontrar_pares_arquivos(arquivos_produtos: List[str], arquivos_reviews: List[str]) -> List[Tuple[str, str]]:
    """
    Encontra pares de arquivos (produtos.json, reviews.json) baseado no nome.
    
    Returns:
        Lista de tuplas (arquivo_produtos, arquivo_reviews)
    """
    pares = []
    
    for arquivo_produtos in arquivos_produtos:
        nome_base = os.path.basename(arquivo_produtos).replace('.json', '')
        arquivo_reviews_correspondente = None
        
        # Procurar arquivo de reviews correspondente
        for arquivo_reviews in arquivos_reviews:
            nome_reviews = os.path.basename(arquivo_reviews).replace('_reviews.json', '')
            if nome_reviews == nome_base:
                arquivo_reviews_correspondente = arquivo_reviews
                break
        
        if arquivo_reviews_correspondente:
            pares.append((arquivo_produtos, arquivo_reviews_correspondente))
            logger.info(f"Par encontrado: {nome_base}")
        else:
            logger.warning(f"Nenhum arquivo de reviews encontrado para: {nome_base}")
    
    logger.info(f"Total de pares encontrados: {len(pares)}")
    return pares

def carregar_dados_arquivo(caminho_arquivo: str) -> Dict[str, Any]:
    """Carrega dados de um arquivo JSON."""
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        return dados
    except Exception as e:
        logger.error(f"Erro ao carregar arquivo {caminho_arquivo}: {e}")
        raise

def criar_indice_reviews_por_produto(reviews: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Cria um índice dos reviews agrupados por produto_id."""
    indice = {}
    
    for review in reviews:
        produto_id = review.get('produto_id')
        if produto_id:
            if produto_id not in indice:
                indice[produto_id] = []
            indice[produto_id].append(review)
    
    return indice

def processar_par_arquivos(arquivo_produtos: str, arquivo_reviews: str) -> List[Dict[str, Any]]:
    """
    Processa um par de arquivos (produtos + reviews) e retorna produtos com todos_reviews.
    """
    nome_base = os.path.basename(arquivo_produtos).replace('.json', '')
    logger.info(f"Processando: {nome_base}")
    
    # Carregar dados
    dados_produtos = carregar_dados_arquivo(arquivo_produtos)
    dados_reviews = carregar_dados_arquivo(arquivo_reviews)
    
    produtos = dados_produtos.get('produtos', [])
    reviews = dados_reviews.get('reviews', [])
    
    logger.info(f"  - {len(produtos)} produtos")
    logger.info(f"  - {len(reviews)} reviews")
    
    # Criar índice de reviews
    indice_reviews = criar_indice_reviews_por_produto(reviews)
    
    # Unir produtos com reviews
    produtos_unidos = []
    produtos_com_reviews = 0
    produtos_sem_reviews = 0
    
    for produto in produtos:
        produto_id = produto.get('id')
        
        if not produto_id:
            continue
        
        # Criar cópia do produto
        produto_unido = produto.copy()
        
        # Buscar reviews para este produto
        reviews_produto = indice_reviews.get(produto_id, [])
        
        if reviews_produto:
            produto_unido['todos_reviews'] = reviews_produto
            produtos_com_reviews += 1
        else:
            produto_unido['todos_reviews'] = []
            produtos_sem_reviews += 1
        
        produtos_unidos.append(produto_unido)
    
    logger.info(f"  - Produtos com reviews: {produtos_com_reviews}")
    logger.info(f"  - Produtos sem reviews: {produtos_sem_reviews}")
    
    return produtos_unidos

def processar_todos_arquivos(diretorio_lote: str) -> List[Dict[str, Any]]:
    """
    Processa todos os arquivos na pasta lote e retorna lista unificada de produtos.
    """
    logger.info("=" * 60)
    logger.info("INICIANDO PROCESSAMENTO DE TODOS OS ARQUIVOS")
    logger.info("=" * 60)
    
    # Listar arquivos
    arquivos_produtos, arquivos_reviews = listar_arquivos_lote(diretorio_lote)
    
    # Encontrar pares
    pares = encontrar_pares_arquivos(arquivos_produtos, arquivos_reviews)
    
    # Processar cada par
    todos_produtos = []
    total_produtos = 0
    total_reviews = 0
    
    for i, (arquivo_produtos, arquivo_reviews) in enumerate(pares):
        logger.info(f"\n--- Processando par {i+1}/{len(pares)} ---")
        
        try:
            produtos_unidos = processar_par_arquivos(arquivo_produtos, arquivo_reviews)
            todos_produtos.extend(produtos_unidos)
            
            # Contar reviews
            reviews_count = sum(len(p.get('todos_reviews', [])) for p in produtos_unidos)
            total_reviews += reviews_count
            total_produtos += len(produtos_unidos)
            
            logger.info(f"✓ Par {i+1} processado com sucesso")
            
        except Exception as e:
            logger.error(f"✗ Erro ao processar par {i+1}: {e}")
            continue
    
    logger.info("=" * 60)
    logger.info("PROCESSAMENTO CONCLUÍDO")
    logger.info("=" * 60)
    logger.info(f"Total de produtos processados: {total_produtos}")
    logger.info(f"Total de reviews processados: {total_reviews}")
    logger.info(f"Pares processados com sucesso: {len(todos_produtos)}")
    
    return todos_produtos

def salvar_dataset_final(todos_produtos: List[Dict[str, Any]], 
                        diretorio_saida: str = "data") -> Tuple[str, str]:
    """Salva o dataset final unificado."""
    
    # Criar diretório se não existir
    os.makedirs(diretorio_saida, exist_ok=True)
    
    # Timestamp atual
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Nome do arquivo
    nome_base = f"dataset_final_unificado_todos_tipos_{timestamp}"
    
    # Salvar como JSON
    arquivo_json = os.path.join(diretorio_saida, f"{nome_base}.json")
    dados_json = {
        "tipo_info": {
            "descricao": "Dataset final unificado com todos os tipos de produtos HP e seus reviews",
            "timestamp": timestamp,
            "total_produtos": len(todos_produtos),
            "produtos_com_reviews": len([p for p in todos_produtos if p.get('todos_reviews')]),
            "produtos_sem_reviews": len([p for p in todos_produtos if not p.get('todos_reviews')]),
            "total_reviews": sum(len(p.get('todos_reviews', [])) for p in todos_produtos)
        },
        "produtos": todos_produtos
    }
    
    with open(arquivo_json, 'w', encoding='utf-8') as f:
        json.dump(dados_json, f, ensure_ascii=False, indent=2)
    
    # Salvar como CSV (sem reviews para não ficar muito grande)
    arquivo_csv = os.path.join(diretorio_saida, f"{nome_base}.csv")
    
    produtos_para_csv = []
    for produto in todos_produtos:
        produto_csv = produto.copy()
        # Remover todos_reviews para CSV
        produto_csv.pop('todos_reviews', None)
        # Adicionar contagem de reviews
        produto_csv['total_reviews_encontrados'] = len(produto.get('todos_reviews', []))
        produtos_para_csv.append(produto_csv)
    
    df = pd.DataFrame(produtos_para_csv)
    df.to_csv(arquivo_csv, index=False, encoding='utf-8')
    
    logger.info(f"\nDataset final salvo:")
    logger.info(f"  JSON: {arquivo_json}")
    logger.info(f"  CSV: {arquivo_csv}")
    
    return arquivo_json, arquivo_csv

def main():
    """Função principal."""
    
    diretorio_lote = "data/dados_extraidos/lote"
    
    try:
        # Processar todos os arquivos
        todos_produtos = processar_todos_arquivos(diretorio_lote)
        
        # Salvar dataset final
        arquivo_json, arquivo_csv = salvar_dataset_final(todos_produtos)
        
        print(f"\n[SUCESSO] Processamento concluído!")
        print(f"[ARQUIVO] JSON: {arquivo_json}")
        print(f"[ARQUIVO] CSV: {arquivo_csv}")
        print(f"[TOTAL] {len(todos_produtos)} produtos processados")
        
    except Exception as e:
        logger.error(f"Erro durante o processamento: {e}")
        raise

if __name__ == "__main__":
    main()
