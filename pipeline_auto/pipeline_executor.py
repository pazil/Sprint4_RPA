#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pipeline Executor Programático
Executa o pipeline com callbacks de progresso para integração com Streamlit
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Optional, Callable, Dict
from dotenv import load_dotenv

# Configurar caminhos
BASE_DIR = Path(__file__).resolve().parents[1]  # Sprint4RPA
SCRIPTS_DIR = BASE_DIR.parent / "scripts"  # fraud_analysis/scripts
DATA_DIR = BASE_DIR.parent / "data"  # fraud_analysis/data

# Carregar .env
load_dotenv(str(BASE_DIR / ".env"), override=False)
load_dotenv(str(BASE_DIR.parent / ".env"), override=False)

STEPS = [
    (0, "0_unificar_dados_brutos.py"),
    (1, "1_filtrar_campos_essenciais.py"),
    (2, "2_extrair_informacoes_ia.py"),
    (3, "3_processar_features_basicas.py"),
    (4, "4_processar_reviews_nlp.py"),
    (5, "5_baixar_processar_imagens.py"),
    (6, "6_criar_target_merge.py"),
    (7, "7_criar_features_grafo.py"),
]


class PipelineExecutor:
    """Executor programático do pipeline com callbacks de progresso"""
    
    def __init__(self, pular: List[int] = None, progress_callback: Optional[Callable] = None):
        """
        Inicializa o executor do pipeline
        
        Args:
            pular: Lista de IDs de etapas a pular
            progress_callback: Função callback(progresso: float, mensagem: str, etapa_id: int, etapa_nome: str)
        """
        self.pular = pular or []
        self.progress_callback = progress_callback
        self.total_etapas = len([s for s in STEPS if s[0] not in self.pular])
    
    def _reportar_progresso(self, etapa_id: int, etapa_nome: str, progresso: float, mensagem: str):
        """Reporta progresso via callback se disponível"""
        if self.progress_callback:
            self.progress_callback(progresso, mensagem, etapa_id, etapa_nome)
    
    def executar_etapa(self, etapa_id: int, script_name: str) -> bool:
        """
        Executa uma etapa do pipeline
        
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            # Caminho do script
            alvo = SCRIPTS_DIR / script_name
            if not alvo.exists():
                self._reportar_progresso(etapa_id, script_name, 0.0, f"❌ Script não encontrado: {alvo}")
                return False
            
            # Preparar ambiente
            env = os.environ.copy()
            env["PYTHONPATH"] = str(SCRIPTS_DIR) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
            
            # Verificar OPENAI_API_KEY para etapas 2 e 4
            if etapa_id in (2, 4) and not env.get("OPENAI_API_KEY"):
                self._reportar_progresso(etapa_id, script_name, 0.0, "❌ OPENAI_API_KEY ausente")
                return False
            
            # Executar script
            self._reportar_progresso(etapa_id, script_name, 0.5, f"Executando {script_name}...")
            
            result = subprocess.run(
                [sys.executable, str(alvo)],
                cwd=str(SCRIPTS_DIR),
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self._reportar_progresso(etapa_id, script_name, 1.0, f"✅ {script_name} concluído")
                return True
            else:
                # Mostrar mais detalhes do erro
                error_msg = result.stderr if result.stderr else result.stdout
                # Pegar últimas linhas do erro (normalmente onde está o traceback)
                error_lines = error_msg.split('\n')
                if len(error_lines) > 20:
                    error_msg = '\n'.join(error_lines[-20:])  # Últimas 20 linhas
                self._reportar_progresso(etapa_id, script_name, 0.0, f"❌ Erro em {script_name}: {error_msg[:500]}")
                # Também imprimir no console para debug
                print(f"\n{'='*80}")
                print(f"ERRO DETALHADO - {script_name}")
                print(f"{'='*80}")
                print("STDOUT:")
                print(result.stdout)
                print("\nSTDERR:")
                print(result.stderr)
                print(f"{'='*80}\n")
                return False
                
        except Exception as e:
            self._reportar_progresso(etapa_id, script_name, 0.0, f"❌ Exceção: {str(e)}")
            return False
    
    def executar(self, preparar_reviews: bool = True) -> bool:
        """
        Executa todas as etapas do pipeline
        
        Args:
            preparar_reviews: Se True, prepara reviews_unificado.json antes da etapa 4
        
        Returns:
            True se todas as etapas foram executadas com sucesso
        """
        etapas_executadas = 0
        etapas_para_executar = [s for s in STEPS if s[0] not in self.pular]
        
        # Preparar dataset unificado antes da etapa 0 se necessário (produto_especifico)
        if 0 not in self.pular:
            self._preparar_dataset_unificado_se_necessario()
        
        # Preparar reviews antes da etapa 4 se necessário
        if preparar_reviews and 4 not in self.pular:
            self._preparar_reviews_se_necessario()
        
        # Executar cada etapa
        for etapa_id, script_name in etapas_para_executar:
            progresso_geral = etapas_executadas / self.total_etapas
            self._reportar_progresso(etapa_id, script_name, progresso_geral, f"Iniciando etapa {etapa_id}: {script_name}")
            
            sucesso = self.executar_etapa(etapa_id, script_name)
            
            if not sucesso:
                return False
            
            etapas_executadas += 1
        
        # Progresso final
        self._reportar_progresso(-1, "Pipeline", 1.0, "✅ Pipeline concluído com sucesso!")
        return True
    
    def _preparar_dataset_unificado_se_necessario(self):
        """Prepara dataset_completo_unificado.json se necessário (antes da etapa 0)"""
        try:
            # Verificar se já existe dataset unificado
            script_0_dir = DATA_DIR / "script_0_unificar_dados"
            script_0_dir.mkdir(parents=True, exist_ok=True)
            
            arquivos_existentes = list(script_0_dir.glob("dataset_completo_unificado_*.json"))
            if arquivos_existentes:
                self._reportar_progresso(0, "Script 0", 0.0, "✅ Dataset unificado já existe")
                return
            
            # Tentar executar prepare_from_produto_especifico.py
            try:
                sys.path.insert(0, str(BASE_DIR / "analise_streamlit"))
                from processamento_anuncio import preparar_dataset_unificado
                
                # Buscar produto mais recente
                selenium_data_dir = BASE_DIR / "Selenium" / "data" / "dados_extraidos" / "produto_especifico"
                
                if selenium_data_dir.exists():
                    arquivos = sorted(selenium_data_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
                    if arquivos:
                        import json
                        with open(arquivos[0], 'r', encoding='utf-8') as f:
                            dados = json.load(f)
                        
                        if isinstance(dados, dict) and "produto" in dados:
                            produto = dados["produto"]
                            preparar_dataset_unificado(produto, DATA_DIR, lambda p, m: None)
                            self._reportar_progresso(0, "Script 0", 0.0, "✅ Dataset unificado preparado")
                            return
            except ImportError:
                pass
            
            # Fallback: usar script prepare_from_produto_especifico.py diretamente
            # O script está em Sprint4RPA/pipeline_auto/steps/
            prepare_script = BASE_DIR / "pipeline_auto" / "steps" / "prepare_from_produto_especifico.py"
            if not prepare_script.exists():
                # Tentar caminho alternativo
                prepare_script = BASE_DIR.parent / "scripts" / "pipeline_auto" / "steps" / "prepare_from_produto_especifico.py"
            
            if prepare_script.exists():
                import subprocess
                # O script prepare_from_produto_especifico.py usa parents[3] 
                # então precisa rodar da raiz fraud_analysis
                # BASE_DIR = Sprint4RPA, então BASE_DIR.parent = fraud_analysis
                repo_root = BASE_DIR.parent
                result = subprocess.run(
                    [sys.executable, str(prepare_script)],
                    capture_output=True,
                    text=True,
                    cwd=str(repo_root)
                )
                if result.returncode == 0:
                    self._reportar_progresso(0, "Script 0", 0.0, "✅ Dataset unificado preparado")
                else:
                    self._reportar_progresso(0, "Script 0", 0.0, f"⚠️ Aviso: {result.stderr[:100]}")
        except Exception as e:
            self._reportar_progresso(0, "Script 0", 0.0, f"⚠️ Aviso preparação: {str(e)[:100]}")
    
    def _preparar_reviews_se_necessario(self):
        """Prepara reviews_unificado.json se necessário"""
        try:
            # Adicionar path para importar processamento_anuncio
            sys.path.insert(0, str(BASE_DIR / "analise_streamlit"))
            from processamento_anuncio import preparar_reviews_unificado
            
            # Buscar produto mais recente em Sprint4RPA/Selenium/data/dados_extraidos/produto_especifico
            selenium_data_dir = BASE_DIR / "Selenium" / "data" / "dados_extraidos" / "produto_especifico"
            
            if selenium_data_dir.exists():
                arquivos = sorted(selenium_data_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
                if arquivos:
                    try:
                        import json
                        with open(arquivos[0], 'r', encoding='utf-8') as f:
                            dados = json.load(f)
                        
                        if isinstance(dados, dict) and "produto" in dados:
                            produto = dados["produto"]
                            preparar_reviews_unificado(produto, DATA_DIR, lambda p, m: None)
                    except Exception as e:
                        print(f"⚠️ Erro ao preparar reviews: {e}")
        except ImportError as e:
            print(f"⚠️ Não foi possível importar processamento_anuncio: {e}")


def executar_pipeline_programatico(pular: List[int] = None, progress_callback: Optional[Callable] = None) -> bool:
    """
    Função de conveniência para executar o pipeline programaticamente
    
    Args:
        pular: Lista de IDs de etapas a pular
        progress_callback: Função callback(progresso, mensagem, etapa_id, etapa_nome)
    
    Returns:
        True se pipeline executado com sucesso
    """
    executor = PipelineExecutor(pular=pular, progress_callback=progress_callback)
    return executor.executar()

