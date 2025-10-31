#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gera data/reviews_unificado.json a partir do JSON mais recente de
Selenium/data/dados_extraidos/produto_especifico.

Formato de saída esperado por 4_processar_reviews_nlp.py:
[
  {
    "product_id": "MLBxxxx",
    "reviews": [ {"rating":..., "text":..., ...}, ... ]
  }
]
"""

from pathlib import Path
import json
from datetime import datetime

# Raiz do repositório
BASE_DIR = Path(__file__).resolve().parents[3]
SRC_DIR = BASE_DIR / "Selenium" / "data" / "dados_extraidos" / "produto_especifico"
DEST_FILE = BASE_DIR / "data" / "reviews_unificado.json"


def main() -> None:
    DEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    arquivos = sorted(SRC_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not arquivos:
        raise FileNotFoundError(f"Nenhum JSON encontrado em {SRC_DIR}")

    src = arquivos[0]
    with open(src, "r", encoding="utf-8") as f:
        dados = json.load(f)

    if isinstance(dados, dict) and "produto" in dados:
        produto = dados["produto"]
    else:
        raise ValueError("Formato inesperado: esperado objeto com chave 'produto'.")

    product_id = produto.get("id") or produto.get("product_id") or produto.get("catalog_product_id")
    reviews = produto.get("todos_reviews") or []

    payload = [
        {
            "product_id": product_id,
            "reviews": reviews,
        }
    ]

    with open(DEST_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"✅ reviews_unificado.json criado em: {DEST_FILE}")


if __name__ == "__main__":
    main()


