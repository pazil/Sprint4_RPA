#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de Processamento de Anúncio
Integra extração Selenium + pipeline + merge ao dataset final
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Callable, Tuple
import pandas as pd

# Adicionar caminhos necessários
BASE_DIR = Path(__file__).resolve().parents[1]  # Sprint4RPA
SELENIUM_DIR = BASE_DIR / "Selenium"
PIPELINE_DIR = BASE_DIR / "pipeline_auto"

# Adicionar ao path para imports
sys.path.insert(0, str(SELENIUM_DIR))
sys.path.insert(0, str(BASE_DIR))

# Importar funções do extrator Selenium
try:
    from extrator_completo_integrado import (
        extract_javascript_data_advanced,
        extract_product_code,
        clean_for_json,
        criar_pasta_dados
    )
except ImportError as e:
    print(f"⚠️ Erro ao importar módulo Selenium: {e}")
    extract_javascript_data_advanced = None


def validar_url(url: str) -> Tuple[bool, str]:
    """Valida se a URL é do MercadoLivre"""
    if not url or not isinstance(url, str):
        return False, "URL vazia ou inválida"
    
    url_lower = url.lower().strip()
    if 'mercadolivre.com.br' not in url_lower:
        return False, "URL deve ser do Mercado Livre (mercadolivre.com.br)"
    
    if not url_lower.startswith('http'):
        return False, "URL deve começar com http:// ou https://"
    
    return True, "URL válida"


def extrair_dados_selenium(url: str, driver, progress_callback: Optional[Callable] = None) -> Optional[Dict]:
    """
    Extrai dados de um anúncio usando o extrator Selenium
    
    Args:
        url: URL do produto no Mercado Livre
        driver: Instância do WebDriver do Selenium
        progress_callback: Função callback para reportar progresso (recebe progresso 0-1 e mensagem)
    
    Returns:
        Dicionário com dados do produto ou None em caso de erro
    """
    if extract_javascript_data_advanced is None:
        raise ImportError("Módulo de extração Selenium não disponível")
    
    try:
        if progress_callback:
            progress_callback(0.1, "Iniciando extração de dados...")
        
        # Extrair dados usando função do extrator
        produto = extract_javascript_data_advanced(driver, url)
        
        if progress_callback:
            progress_callback(0.9, "Extração concluída!")
        
        if not produto:
            return None
        
        # Limpar dados para serialização JSON
        produto_limpo = clean_for_json(produto)
        
        return produto_limpo
        
    except Exception as e:
        print(f"❌ Erro ao extrair dados: {e}")
        return None


def salvar_produto_extraido(produto: Dict, progress_callback: Optional[Callable] = None) -> Path:
    """
    Salva produto extraído no formato esperado pelo pipeline
    
    Args:
        produto: Dicionário com dados do produto
        progress_callback: Função callback para reportar progresso
    
    Returns:
        Path do arquivo JSON salvo
    """
    try:
        if progress_callback:
            progress_callback(0.5, "Salvando dados extraídos...")
        
        # Criar estrutura de pastas
        dados_path = criar_pasta_dados()
        pasta_produto = Path(dados_path) / 'produto_especifico'
        pasta_produto.mkdir(parents=True, exist_ok=True)
        
        # Criar timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Extrair ID do produto
        product_id = produto.get('id') or produto.get('product_code') or 'UNKNOWN'
        reviews_count = len(produto.get('todos_reviews', []))
        
        # Estrutura de dados final (compatível com formato esperado)
        dataset_final = {
            "busca_info": {
                "modo": "produto_especifico",
                "timestamp": timestamp,
                "url_produto": produto.get('link', ''),
                "produto_extraido": True,
                "total_reviews_extraidos": reviews_count,
                "produto_id": product_id,
                "produto_titulo": produto.get('titulo', '')
            },
            "produto": produto
        }
        
        # Salvar JSON
        json_file = pasta_produto / f"produto_especifico_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(dataset_final, f, ensure_ascii=False, indent=2)
        
        if progress_callback:
            progress_callback(1.0, f"Dados salvos em: {json_file.name}")
        
        return json_file
        
    except Exception as e:
        print(f"❌ Erro ao salvar produto: {e}")
        raise


def preparar_reviews_unificado(produto: Dict, data_dir: Path, progress_callback: Optional[Callable] = None) -> Path:
    """
    Cria arquivo reviews_unificado.json a partir do produto extraído
    
    Args:
        produto: Dicionário com dados do produto (deve ter 'todos_reviews')
        data_dir: Diretório base onde salvar o arquivo
        progress_callback: Função callback para reportar progresso
    
    Returns:
        Path do arquivo reviews_unificado.json criado
    """
    try:
        if progress_callback:
            progress_callback(0.5, "Preparando reviews unificado...")
        
        # Extrair dados necessários
        product_id = produto.get('id') or produto.get('product_code') or ''
        reviews = produto.get('todos_reviews', [])
        
        # Criar estrutura esperada pelo pipeline
        payload = [
            {
                "product_id": product_id,
                "reviews": reviews
            }
        ]
        
        # Salvar arquivo
        reviews_file = data_dir / "reviews_unificado.json"
        reviews_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(reviews_file, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        
        if progress_callback:
            progress_callback(1.0, f"Reviews unificado criado: {reviews_file.name}")
        
        return reviews_file
        
    except Exception as e:
        print(f"❌ Erro ao preparar reviews unificado: {e}")
        raise


def preparar_dataset_unificado(produto: Dict, data_dir: Path, progress_callback: Optional[Callable] = None) -> Path:
    """
    Cria dataset_unificado no formato esperado pelo Script 1
    
    Args:
        produto: Dicionário com dados do produto
        data_dir: Diretório base (data/)
        progress_callback: Função callback para reportar progresso
    
    Returns:
        Path do arquivo dataset_completo_unificado criado
    """
    try:
        if progress_callback:
            progress_callback(0.5, "Preparando dataset unificado...")
        
        # Criar pasta se não existir
        script_0_dir = data_dir / "script_0_unificar_dados"
        script_0_dir.mkdir(parents=True, exist_ok=True)
        
        # Converter produto para lista (formato esperado pelo Script 1)
        produtos_lista = [produto]
        
        # Salvar arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unificado_file = script_0_dir / f"dataset_completo_unificado_{timestamp}.json"
        
        with open(unificado_file, 'w', encoding='utf-8') as f:
            json.dump(produtos_lista, f, ensure_ascii=False, indent=2)
        
        if progress_callback:
            progress_callback(1.0, f"Dataset unificado criado: {unificado_file.name}")
        
        return unificado_file
        
    except Exception as e:
        print(f"❌ Erro ao preparar dataset unificado: {e}")
        raise

