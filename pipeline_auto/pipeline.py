#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pipeline HP Anti-Pirataria - Orquestrador
Executa o fluxo completo a partir das saídas do Selenium até o dataset final com grafo.

Fluxo:
  1) (opcional) Consolidar saídas do Selenium antigo: scripts/processar_todos_arquivos_lote.py
  2) Script 0  -> 0_unificar_dados_brutos.py
  3) Script 1  -> 1_filtrar_campos_essenciais.py
  4) Script 2  -> 2_extrair_informacoes_ia.py (requer OPENAI_API_KEY)
  5) Script 3  -> 3_processar_features_basicas.py
  6) Script 4  -> 4_processar_reviews_nlp.py (requer OPENAI_API_KEY)
  7) Script 5  -> 5_baixar_processar_imagens.py
  8) Script 6  -> 6_criar_target_merge.py
  9) Script 7  -> 7_criar_features_grafo.py (gera dataset final com grafo)

Uso:
  python scripts/pipeline_auto/pipeline.py \
    --consolidar-selenium (opcional) \
    --pular "2,4" (pular etapas por id) \
    --parar-em 7

Saídas principais:
  - data/script_7_grafo/dataset_final_com_grafo.csv
"""

from __future__ import annotations

import argparse
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
import shutil
import glob

BASE_DIR = Path(__file__).resolve().parents[2]  # raiz do repo
SCRIPTS_DIR = BASE_DIR / "scripts"
DATA_DIR = BASE_DIR / "data"
# Ajuste: as saídas atuais do Selenium ficam em Selenium/data/dados_extraidos
SELENIUM_DATA_DIR = BASE_DIR / "Selenium" / "data" / "dados_extraidos"
LOCAL_STEPS_DIR = SCRIPTS_DIR / "pipeline_auto" / "steps"
LOCAL_ML_DIR = SCRIPTS_DIR / "pipeline_auto" / "ml"
LOCAL_ML_SCORE_DIR = SCRIPTS_DIR / "pipeline_auto" / "ml_score"


def sh(cmd: List[str], cwd: Optional[Path] = None, env: Optional[dict] = None) -> int:
    print(f"$ {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env)
    return completed.returncode


def validar_ambiente() -> None:
    # Pastas esperadas
    (DATA_DIR / "script_0_unificar_dados").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "script_1_filtrar_campos").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "script_2_ia").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "script_3_features_basicas").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "script_4_nlp").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "script_5_imagens").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "script_6_target_merge").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "script_7_grafo").mkdir(parents=True, exist_ok=True)

    # Pastas locais do pipeline_auto
    LOCAL_STEPS_DIR.mkdir(parents=True, exist_ok=True)
    LOCAL_ML_DIR.mkdir(parents=True, exist_ok=True)
    LOCAL_ML_SCORE_DIR.mkdir(parents=True, exist_ok=True)


def organizar_componentes_locais() -> None:
    """Copia scripts 0..7 e utilitários/ML para dentro de pipeline_auto.
    Executa de forma idempotente (só copia se não existir ou se origem for mais nova)."""
    # Scripts principais do pipeline
    nomes_scripts = [
        "0_unificar_dados_brutos.py",
        "1_filtrar_campos_essenciais.py",
        "2_extrair_informacoes_ia.py",
        "3_processar_features_basicas.py",
        "4_processar_reviews_nlp.py",
        "5_baixar_processar_imagens.py",
        "6_criar_target_merge.py",
        "7_criar_features_grafo.py",
        "processar_todos_arquivos_lote.py",
    ]

    for nome in nomes_scripts:
        src = SCRIPTS_DIR / nome
        dst = LOCAL_STEPS_DIR / nome
        if src.exists():
            try:
                if (not dst.exists()) or (src.stat().st_mtime > dst.stat().st_mtime):
                    shutil.copy2(src, dst)
                    print(f"📎 Copiado: {src.name} → {dst}")
            except Exception as e:
                print(f"⚠️ Falha ao copiar {src} → {dst}: {e}")

    # Copiar apenas ARTEFATOS de modelos já existentes (não treina nem cria novos)
    possiveis_dirs_modelos = [
        BASE_DIR / "models",
        BASE_DIR / "deploy" / "models",
        BASE_DIR / "data",
        SCRIPTS_DIR,
    ]
    padroes_modelos = ("*.pkl", "*.joblib", "*.bin", "*.onnx", "*.pt", "*.pth")
    for d in possiveis_dirs_modelos:
        if d.exists():
            for pattern in padroes_modelos:
                for path_str in glob.glob(str(d / pattern)):
                    src = Path(path_str)
                    dst = LOCAL_ML_DIR / src.name
                    try:
                        if (not dst.exists()) or (src.stat().st_mtime > dst.stat().st_mtime):
                            shutil.copy2(src, dst)
                            print(f"📎 Copiado artefato de modelo: {src} → {dst}")
                    except Exception as e:
                        print(f"⚠️ Falha ao copiar artefato {src} → {dst}: {e}")

    # Copiar possíveis scripts de score
    for pattern in ("*score*.py", "*scoring*.py"):
        for path_str in glob.glob(str(SCRIPTS_DIR / pattern)):
            src = Path(path_str)
            dst = LOCAL_ML_SCORE_DIR / src.name
            try:
                if (not dst.exists()) or (src.stat().st_mtime > dst.stat().st_mtime):
                    shutil.copy2(src, dst)
                    print(f"📎 Copiado ML Score: {src.name} → {dst}")
            except Exception as e:
                print(f"⚠️ Falha ao copiar ML Score {src} → {dst}: {e}")


def detectar_saidas_selenium() -> bool:
    # Verifica se há arquivos do Selenium em data/dados_extraidos
    if not SELENIUM_DATA_DIR.exists():
        return False
    possui_json_csv = any(p.suffix in (".json", ".csv") for p in SELENIUM_DATA_DIR.glob("**/*"))
    if possui_json_csv:
        print(f"✅ Saídas do Selenium detectadas em: {SELENIUM_DATA_DIR}")
    else:
        print(f"⚠️ Pasta {SELENIUM_DATA_DIR} existe, mas não há JSON/CSV.")
    return possui_json_csv


def preparar_reviews_unificado_se_necessario() -> None:
    """Prepara reviews_unificado.json automaticamente se não existir"""
    reviews_unificado = DATA_DIR / "reviews_unificado.json"
    if reviews_unificado.exists():
        print(f"✅ reviews_unificado.json já existe: {reviews_unificado}")
        return
    
    # Tentar criar a partir de produto_especifico
    produto_especifico_dir = SELENIUM_DATA_DIR / "produto_especifico"
    if produto_especifico_dir.exists():
        arquivos = sorted(produto_especifico_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if arquivos:
            print(f"📦 Criando reviews_unificado.json a partir de {arquivos[0].name}...")
            import json
            src = arquivos[0]
            with open(src, "r", encoding="utf-8") as f:
                dados = json.load(f)
            
            if isinstance(dados, dict) and "produto" in dados:
                produto = dados["produto"]
                product_id = produto.get("id") or produto.get("product_id") or produto.get("catalog_product_id")
                reviews = produto.get("todos_reviews") or []
                
                payload = [{"product_id": product_id, "reviews": reviews}]
                
                reviews_unificado.parent.mkdir(parents=True, exist_ok=True)
                with open(reviews_unificado, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
                print(f"✅ reviews_unificado.json criado em: {reviews_unificado}")
                return
    
    print(f"⚠️ Não foi possível criar reviews_unificado.json automaticamente. Execute: python scripts/pipeline_auto/steps/prepare_reviews_unificado_from_produto_especifico.py")


def consolidar_selenium_antigo() -> None:
    # Consolida produtos + reviews antigos (se existirem) em um dataset unificado auxiliar
    alvo = SCRIPTS_DIR / "processar_todos_arquivos_lote.py"
    if not alvo.exists():
        print("ℹ️ Arquivo processar_todos_arquivos_lote.py não encontrado; pulando consolidação.")
        return
    rc = sh([sys.executable, str(alvo)], cwd=SCRIPTS_DIR)
    if rc != 0:
        raise RuntimeError("Falha na consolidação das saídas do Selenium (processar_todos_arquivos_lote.py)")


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


def preparar_dataset_unificado_se_necessario() -> None:
    """Prepara dataset_completo_unificado.json antes da etapa 0 se necessário (produto_especifico)"""
    script_0_dir = DATA_DIR / "script_0_unificar_dados"
    script_0_dir.mkdir(parents=True, exist_ok=True)
    
    arquivos_existentes = list(script_0_dir.glob("dataset_completo_unificado_*.json"))
    if arquivos_existentes:
        print(f"✅ Dataset unificado já existe, usando o mais recente")
        return
    
    # Tentar criar a partir de produto_especifico
    produto_especifico_dir = SELENIUM_DATA_DIR / "produto_especifico"
    if produto_especifico_dir.exists():
        arquivos = sorted(produto_especifico_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if arquivos:
            print(f"📦 Preparando dataset unificado a partir de {arquivos[0].name}...")
            import json
            src = arquivos[0]
            with open(src, "r", encoding="utf-8") as f:
                dados = json.load(f)
            
            if isinstance(dados, dict) and "produto" in dados:
                produto = dados["produto"]
                produtos = [produto]
            elif isinstance(dados, list):
                produtos = dados
            else:
                print(f"⚠️ Formato inesperado no arquivo {src.name}")
                return
            
            # Criar arquivo dataset_completo_unificado
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            destino = script_0_dir / f"dataset_completo_unificado_{timestamp}.json"
            
            with open(destino, "w", encoding="utf-8") as f:
                json.dump(produtos, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Dataset unificado preparado: {destino.name}")
    else:
        print(f"⚠️ Pasta {produto_especifico_dir} não encontrada; etapa 0 tentará usar dados_brutos/")


def executar_steps(pular: List[int], parar_em: Optional[int]) -> None:
    # Preparar dataset unificado antes da etapa 0 se necessário (produto_especifico)
    if 0 not in pular:
        preparar_dataset_unificado_se_necessario()
    
    for step_id, script_name in STEPS:
        if step_id in pular:
            print(f"⏭️  Pulando etapa {step_id}: {script_name}")
            if parar_em is not None and step_id >= parar_em:
                break
            continue

        # Preparar reviews_unificado.json antes da etapa 4 se necessário
        if step_id == 4:
            preparar_reviews_unificado_se_necessario()

        print("\n" + "=" * 80)
        print(f"▶️  Executando etapa {step_id}: {script_name}")
        print("=" * 80)

        # Executar SEMPRE o script original na pasta scripts para manter caminhos relativos e imports
        alvo = SCRIPTS_DIR / script_name
        if not alvo.exists():
            raise FileNotFoundError(f"Script não encontrado: {alvo}")

        # As etapas 2 e 4 requerem OPENAI_API_KEY
        env = os.environ.copy()
        # Garantir que imports relativos (ex.: _config) funcionem
        env["PYTHONPATH"] = str(SCRIPTS_DIR) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        if step_id in (2, 4) and not env.get("OPENAI_API_KEY"):
            raise EnvironmentError("OPENAI_API_KEY ausente no ambiente para executar etapas 2/4.")

        # Executar com cwd = pasta scripts para manter caminhos relativos esperados
        rc = sh([sys.executable, str(alvo)], cwd=SCRIPTS_DIR, env=env)
        if rc != 0:
            raise RuntimeError(f"Falha ao executar etapa {step_id}: {script_name}")

        if parar_em is not None and step_id >= parar_em:
            print(f"🛑 Parando conforme solicitado em --parar-em {parar_em}")
            break


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pipeline HP Anti-Pirataria - Orquestrador")
    parser.add_argument(
        "--consolidar-selenium",
        action="store_true",
        help="Rodar consolidação das saídas legadas do Selenium (processar_todos_arquivos_lote.py)"
    )
    parser.add_argument(
        "--pular",
        type=str,
        default="",
        help="IDs de etapas a pular, separados por vírgula. Ex: --pular 2,4"
    )
    parser.add_argument(
        "--parar-em",
        type=int,
        default=None,
        help="Parar após executar a etapa informada (0..7)"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    # Carregar .env específico do pipeline (se existir)
    load_dotenv(str(SCRIPTS_DIR / "pipeline_auto" / ".env"), override=False)
    # Carregar também um .env na raiz, se existir (sem sobrescrever)
    load_dotenv(str(BASE_DIR / ".env"), override=False)
    validar_ambiente()
    # Preparar cópias locais dos componentes
    organizar_componentes_locais()

    # Detectar saídas do Selenium (informativo)
    detectar_saidas_selenium()

    # Consolidação opcional
    if args.consolidar_selenium:
        print("\n🔗 Consolidando saídas do Selenium (opcional)...")
        consolidar_selenium_antigo()

    # Preparar lista de etapas a pular
    pular = []
    if args.pular.strip():
        try:
            pular = [int(x.strip()) for x in args.pular.split(',') if x.strip()]
        except ValueError:
            raise ValueError("--pular deve conter inteiros separados por vírgula, ex: 2,4")

    # Executar 0→7
    executar_steps(pular=pular, parar_em=args.parar_em)

    print("\n✅ Pipeline concluído com sucesso!")
    caminho_final = DATA_DIR / "script_7_grafo" / "dataset_final_com_grafo.csv"
    if caminho_final.exists():
        print(f"📊 Dataset final: {caminho_final}")
    else:
        print("⚠️ Arquivo final não encontrado; verifique logs das etapas.")


if __name__ == "__main__":
    main()


