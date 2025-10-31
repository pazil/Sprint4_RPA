#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Preparar dataset unificado (Script 0) a partir de extrações de produto_especifico do Selenium.

Busca o JSON mais recente em Selenium/data/dados_extraidos/produto_especifico/
e gera data/script_0_unificar_dados/dataset_completo_unificado_YYYYMMDD_HHMMSS.json
no formato esperado pelos Scripts 1..7 (lista de produtos).
"""

import json
from pathlib import Path
from datetime import datetime

# Repo root (..\..\.. from this file)
BASE_DIR = Path(__file__).resolve().parents[3]
SRC_DIR = BASE_DIR / "Selenium" / "data" / "dados_extraidos" / "produto_especifico"
DEST_DIR = BASE_DIR / "data" / "script_0_unificar_dados"


def main() -> None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    arquivos = sorted(SRC_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not arquivos:
        raise FileNotFoundError(f"Nenhum JSON encontrado em {SRC_DIR}")

    src = arquivos[0]
    with open(src, "r", encoding="utf-8") as f:
        dados = json.load(f)

    # Formatos possíveis: {"produto": {...}} ou já uma lista
    if isinstance(dados, dict) and "produto" in dados:
        produtos = [dados["produto"]]
    elif isinstance(dados, list):
        produtos = dados
    else:
        raise ValueError("Formato inesperado do arquivo de produto_especifico. Esperado chave 'produto' ou lista.")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = DEST_DIR / f"dataset_completo_unificado_{ts}.json"
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(produtos, f, ensure_ascii=False, indent=2)

    print(f"✅ Dataset unificado criado: {destino}")


if __name__ == "__main__":
    main()


