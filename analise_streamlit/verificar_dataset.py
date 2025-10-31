#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para verificar se o dataset está no local correto
"""

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
dataset_path = BASE_DIR / "data" / "final_grafo" / "dataset_final_com_grafo.csv"

print("=" * 60)
print("🔍 VERIFICAÇÃO DO DATASET")
print("=" * 60)
print(f"\n📁 Diretório base: {BASE_DIR}")
print(f"📄 Caminho do dataset: {dataset_path}")
print(f"✅ Arquivo existe: {dataset_path.exists()}")

if dataset_path.exists():
    print(f"📊 Tamanho: {dataset_path.stat().st_size / 1024:.2f} KB")
    print(f"🔗 Caminho absoluto: {dataset_path.absolute()}")
    
    # Tentar ler o arquivo
    try:
        import pandas as pd
        df = pd.read_csv(dataset_path)
        print(f"✅ Arquivo pode ser lido!")
        print(f"📈 Linhas: {len(df)}")
        print(f"📋 Colunas: {len(df.columns)}")
        print(f"\nPrimeiras colunas: {list(df.columns[:5])}")
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {e}")
else:
    print("\n❌ PROBLEMA: Arquivo não encontrado!")
    print("\n💡 Possíveis soluções:")
    print("   1. Verifique se o arquivo está em:")
    print(f"      {dataset_path.absolute()}")
    print("   2. Se o arquivo estiver em outro local, copie para o local acima")
    print("   3. Ou execute o pipeline para gerar o dataset")

print("\n" + "=" * 60)

