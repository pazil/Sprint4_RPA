# pages/5_Extrair_Analisar_Anuncio.py - Extração e Processamento de Anúncio

import streamlit as st
import pandas as pd
import sys
import os
from pathlib import Path
from typing import Optional, Dict

# Adicionar caminhos
BASE_DIR = Path(__file__).resolve().parents[2]  # Sprint4RPA
sys.path.insert(0, str(BASE_DIR / "analise_streamlit"))
sys.path.insert(0, str(BASE_DIR / "Selenium"))
sys.path.insert(0, str(BASE_DIR / "pipeline_auto"))

from processamento_anuncio import (
    validar_url,
    extrair_dados_selenium,
    salvar_produto_extraido,
    preparar_reviews_unificado,
    preparar_dataset_unificado
)
from pipeline_executor import executar_pipeline_programatico
from utils import append_to_dataset, clear_streamlit_cache, get_anuncio_by_id

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="HP Anti-Fraude | Extrair e Analisar Anúncio",
    page_icon="🔍",
    layout="wide"
)

# --- URL PADRÃO ---
URL_PADRAO = "https://www.mercadolivre.com.br/cartucho-hp-667xl-preto-85ml/p/MLB37822949"

# --- TÍTULO E INTRODUÇÃO ---
st.title("🔍 Extrair e Analisar Anúncio")
st.markdown("""
**Extraia dados de um anúncio do Mercado Livre, processe pelo pipeline completo e adicione ao dataset para análise.**

Digite ou cole a URL do anúncio abaixo e clique em "Extrair e Processar" para iniciar o processo completo.
""")

# --- SIDEBAR: Configuração do WebDriver ---
st.sidebar.header("⚙️ Configuração")
st.sidebar.info("""
**Instruções:**
1. Configure o navegador uma vez ao iniciar
2. Faça login no Mercado Livre quando solicitado
3. O navegador será reutilizado durante a sessão
""")

# Estado da sessão para o driver
if 'webdriver_initialized' not in st.session_state:
    st.session_state.webdriver_initialized = False
    st.session_state.driver = None

# --- INPUT DE URL ---
st.subheader("📋 URL do Anúncio")
url_input = st.text_input(
    "URL do Produto:",
    value=URL_PADRAO,
    placeholder="https://www.mercadolivre.com.br/...",
    help="Cole a URL completa do produto ou deixe o padrão"
)

# Validar URL
if url_input:
    url_valida, msg = validar_url(url_input)
    if not url_valida:
        st.warning(f"⚠️ {msg}")
    else:
        st.success(f"✅ {msg}")

# --- BOTÃO DE EXTRAÇÃO ---
st.subheader("🚀 Processamento")
col1, col2 = st.columns([1, 3])

with col1:
    btn_extrair = st.button("🔍 Extrair e Processar", type="primary", use_container_width=True)

# --- PROCESSAMENTO ---
if btn_extrair:
    if not url_input or not validar_url(url_input)[0]:
        st.error("❌ Por favor, forneça uma URL válida do Mercado Livre")
        st.stop()
    
    # Container de progresso
    progress_container = st.container()
    
    with progress_container:
        st.info("🔄 Iniciando processamento...")
        
        # Barra de progresso geral
        progress_bar = st.progress(0)
        status_text = st.empty()
        etapa_text = st.empty()
        
        try:
            # === ETAPA 1: Configurar WebDriver ===
            etapa_text.markdown("**Etapa 1/4: Configurando navegador...**")
            status_text.text("⏳ Preparando navegador...")
            progress_bar.progress(0.05)
            
            # Verificar se driver já está inicializado
            if not st.session_state.webdriver_initialized or st.session_state.driver is None:
                from extrator_completo_integrado import setup_browser_session
                
                with st.spinner("Aguardando configuração do navegador..."):
                    driver = setup_browser_session()
                
                if not driver:
                    st.error("❌ Não foi possível configurar o navegador. Verifique se o Selenium está instalado.")
                    st.stop()
                
                st.session_state.driver = driver
                st.session_state.webdriver_initialized = True
                st.success("✅ Navegador configurado!")
            else:
                driver = st.session_state.driver
                st.info("✅ Reutilizando navegador existente")
            
            progress_bar.progress(0.10)
            
            # === ETAPA 2: Extrair dados com Selenium ===
            etapa_text.markdown("**Etapa 2/4: Extraindo dados do anúncio...**")
            
            def callback_extracao(progresso, mensagem):
                progresso_total = 0.10 + (progresso * 0.15)  # 10% a 25%
                progress_bar.progress(progresso_total)
                status_text.text(f"📊 {mensagem}")
            
            produto = extrair_dados_selenium(url_input, driver, callback_extracao)
            
            if not produto:
                st.error("❌ Não foi possível extrair dados do anúncio. Verifique se a URL está correta.")
                st.stop()
            
            st.success(f"✅ Dados extraídos: {produto.get('titulo', 'N/A')[:50]}...")
            progress_bar.progress(0.25)
            
            # === ETAPA 3: Salvar dados e preparar para pipeline ===
            etapa_text.markdown("**Etapa 3/4: Preparando dados para pipeline...**")
            status_text.text("💾 Salvando dados extraídos...")
            progress_bar.progress(0.30)
            
            # Salvar produto
            json_file = salvar_produto_extraido(produto, lambda p, m: status_text.text(f"💾 {m}"))
            progress_bar.progress(0.40)
            
            # Preparar reviews unificado
            DATA_DIR = BASE_DIR.parent / "data"
            preparar_reviews_unificado(produto, DATA_DIR, lambda p, m: status_text.text(f"📝 {m}"))
            progress_bar.progress(0.50)
            
            # Preparar dataset unificado (script 0 precisa disso)
            # O script 0 busca automaticamente em script_0_unificar_dados, mas vamos preparar também
            preparar_dataset_unificado(produto, DATA_DIR, lambda p, m: status_text.text(f"📦 {m}"))
            progress_bar.progress(0.60)
            
            st.success("✅ Dados preparados para pipeline")
            
            # === ETAPA 4: Executar Pipeline ===
            etapa_text.markdown("**Etapa 4/4: Executando pipeline de processamento...**")
            
            def callback_pipeline(progresso, mensagem, etapa_id, etapa_nome):
                progresso_total = 0.60 + (progresso * 0.35)  # 60% a 95%
                progress_bar.progress(progresso_total)
                if etapa_id >= 0:
                    status_text.text(f"⚙️ Etapa {etapa_id}: {etapa_nome} - {mensagem}")
                else:
                    status_text.text(f"✅ {mensagem}")
            
            sucesso_pipeline = executar_pipeline_programatico(pular=None, progress_callback=callback_pipeline)
            
            if not sucesso_pipeline:
                st.error("❌ Erro durante execução do pipeline. Verifique os logs acima.")
                st.stop()
            
            progress_bar.progress(0.95)
            
            # === ETAPA 5: Mesclar ao dataset final ===
            etapa_text.markdown("**Finalizando: Adicionando ao dataset...**")
            status_text.text("🔗 Mesclando com dataset final...")
            
            # Carregar dataset final processado
            # O pipeline salva em: fraud_analysis/data/script_7_grafo/dataset_final_com_grafo.csv
            dataset_final_path = DATA_DIR / "script_7_grafo" / "dataset_final_com_grafo.csv"
            
            if dataset_final_path.exists():
                df_novo = pd.read_csv(dataset_final_path)
                
                # Filtrar apenas o registro mais recente (do processamento atual)
                # Assumindo que o último registro é o que acabamos de processar
                ultimo_registro = df_novo.tail(1)
                
                # Mesclar com dataset principal (dentro de Sprint4RPA/analise_streamlit/data/)
                dataset_principal_path = BASE_DIR / "analise_streamlit" / "data" / "final_grafo" / "dataset_final_com_grafo.csv"
                
                # Garantir que o diretório existe
                dataset_principal_path.parent.mkdir(parents=True, exist_ok=True)
                
                if append_to_dataset(ultimo_registro, str(dataset_principal_path), backup=True):
                    st.success("✅ Registro adicionado ao dataset principal!")
                else:
                    st.warning("⚠️ Não foi possível adicionar ao dataset principal. Verifique os logs.")
                
                # Invalidar cache do Streamlit
                clear_streamlit_cache()
                progress_bar.progress(1.0)
                
                st.success("🎉 Processamento concluído com sucesso!")
                
                # === EXIBIR PREVIEW ===
                st.subheader("📊 Preview do Anúncio Processado")
                
                col_preview1, col_preview2 = st.columns(2)
                
                with col_preview1:
                    st.json({
                        "ID": produto.get('id', 'N/A'),
                        "Título": produto.get('titulo', 'N/A'),
                        "Preço": produto.get('preco', 'N/A'),
                        "Vendedor": produto.get('vendedor', 'N/A'),
                        "Rating": produto.get('rating_medio', 'N/A'),
                        "Total Reviews": produto.get('total_reviews', 0)
                    })
                
                with col_preview2:
                    if not ultimo_registro.empty:
                        st.dataframe(ultimo_registro[['id_anuncio', 'vendedor_nome', 'score_de_suspeita', 'is_fraud_suspect_v2']].T)
                
                # Botão para ver no dashboard
                st.markdown("---")
                st.markdown("### 🎯 Próximos Passos")
                st.info("""
                O anúncio foi processado e adicionado ao dataset. Você pode:
                - Verificar no **Dashboard Geral** para análises gerais
                - Usar a **Investigação de Anúncios** para filtrar e analisar este anúncio
                - Analisar o **Vendedor** através da página de Análise de Vendedores
                """)
                
            else:
                st.warning(f"⚠️ Dataset final não encontrado em: {dataset_final_path}")
                st.info("O pipeline foi executado, mas o arquivo de saída não foi encontrado.")
        
        except Exception as e:
            st.error(f"❌ Erro durante processamento: {str(e)}")
            import traceback
            with st.expander("📋 Detalhes do Erro"):
                st.code(traceback.format_exc())

# --- SIDEBAR: Informações Adicionais ---
st.sidebar.markdown("---")
st.sidebar.subheader("ℹ️ Informações")
st.sidebar.info("""
**Processo Completo:**
1. Extração de dados via Selenium
2. Processamento pelo pipeline (8 etapas)
3. Geração de features e grafo
4. Merge com dataset principal
5. Invalidação de cache

**Tempo estimado:** 5-15 minutos dependendo da etapa de IA.
""")

# --- FOOTER ---
st.markdown("---")
st.caption("💡 **Dica:** O navegador permanecerá aberto durante a sessão. Configure uma vez e reutilize para múltiplas extrações.")

