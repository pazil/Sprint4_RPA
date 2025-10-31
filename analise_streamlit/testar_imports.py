#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de Teste Rápido - Verifica se todos os imports estão funcionando
Execute antes de testar no Streamlit
"""

import sys
from pathlib import Path

print("🔍 Testando imports...")
print("=" * 60)

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR.parent / "Selenium"))
sys.path.insert(0, str(BASE_DIR.parent / "pipeline_auto"))

# Teste 1: Imports básicos
print("\n1️⃣ Testando imports básicos...")
try:
    import streamlit as st
    import pandas as pd
    print("   ✅ streamlit, pandas")
except ImportError as e:
    print(f"   ❌ Erro: {e}")

# Teste 2: processamento_anuncio
print("\n2️⃣ Testando processamento_anuncio...")
try:
    from processamento_anuncio import (
        validar_url,
        extrair_dados_selenium,
        salvar_produto_extraido,
        preparar_reviews_unificado
    )
    print("   ✅ Módulo processamento_anuncio importado")
    
    # Teste de validação
    teste_url = "https://www.mercadolivre.com.br/cartucho-hp-667xl-preto-85ml/p/MLB37822949"
    valido, msg = validar_url(teste_url)
    if valido:
        print(f"   ✅ Validação de URL funcionando: {msg}")
    else:
        print(f"   ⚠️ Validação retornou: {msg}")
except ImportError as e:
    print(f"   ❌ Erro ao importar processamento_anuncio: {e}")

# Teste 3: pipeline_executor
print("\n3️⃣ Testando pipeline_executor...")
try:
    from pipeline_executor import PipelineExecutor, executar_pipeline_programatico
    print("   ✅ Módulo pipeline_executor importado")
except ImportError as e:
    print(f"   ❌ Erro ao importar pipeline_executor: {e}")

# Teste 4: utils
print("\n4️⃣ Testando utils...")
try:
    from utils import (
        load_data,
        append_to_dataset,
        clear_streamlit_cache,
        get_anuncio_by_id
    )
    print("   ✅ Módulo utils importado")
except ImportError as e:
    print(f"   ❌ Erro ao importar utils: {e}")

# Teste 5: Extrator Selenium
print("\n5️⃣ Testando extrator Selenium...")
try:
    from extrator_completo_integrado import (
        extract_javascript_data_advanced,
        criar_pasta_dados,
        clean_for_json
    )
    print("   ✅ Módulo extrator_completo_integrado importado")
except ImportError as e:
    print(f"   ❌ Erro ao importar extrator: {e}")

# Teste 6: Verificar arquivos importantes
print("\n6️⃣ Verificando arquivos importantes...")

arquivos_importantes = [
    BASE_DIR / "processamento_anuncio.py",
    BASE_DIR.parent / "pipeline_auto" / "pipeline_executor.py",
    BASE_DIR.parent / "Selenium" / "extrator_completo_integrado.py",
    BASE_DIR / "pages" / "5_Extrair_Analisar_Anuncio.py",
]

for arquivo in arquivos_importantes:
    if arquivo.exists():
        print(f"   ✅ {arquivo.name}")
    else:
        print(f"   ❌ {arquivo.name} NÃO ENCONTRADO")

# Teste 7: Verificar variáveis de ambiente
print("\n7️⃣ Verificando variáveis de ambiente...")
import os
from dotenv import load_dotenv

load_dotenv(str(BASE_DIR.parent / "pipeline_auto" / ".env"), override=False)
load_dotenv(str(BASE_DIR.parent.parent / ".env"), override=False)

if os.getenv("OPENAI_API_KEY"):
    print("   ✅ OPENAI_API_KEY encontrada")
else:
    print("   ⚠️ OPENAI_API_KEY não encontrada (etapas 2 e 4 do pipeline serão puladas)")

print("\n" + "=" * 60)
print("✅ Teste de imports concluído!")
print("\n💡 Se todos os testes passaram, você pode iniciar o Streamlit:")
print("   streamlit run app.py")

