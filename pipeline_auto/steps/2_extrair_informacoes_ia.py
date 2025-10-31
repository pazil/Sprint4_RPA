"""
=============================================================================
SCRIPT 1: EXTRAIR INFORMAÇÕES COM IA
=============================================================================
Usa GPT-4o-mini para extrair informações estruturadas de títulos/descrições
de produtos de cartuchos HP do Mercado Livre.

INPUT:
- data/script_0_unificar_dados/dataset_completo_unificado_*.json

OUTPUT:
- data/script_1_ia/dados_extraidos_ia_*.json
- data/script_1_ia/dados_extraidos_ia_*.csv

INFORMAÇÕES EXTRAÍDAS:
- tipo_cartucho: modelo (ex: "662", "662xl", "664")
- cores_detalhadas: dict com {"preto": 0/1, "colorido": 0/1}
- quantidade_por_anuncio: número de cartuchos no kit
- usado_seminovo: 0 ou 1
"""

import pandas as pd
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import time
from datetime import datetime
import glob

# Importar configurações
sys.path.append(str(Path(__file__).parent))
from _config import *

# Carregar variáveis de ambiente
load_dotenv()

print("="*80)
print("🤖 SCRIPT 1: EXTRAIR INFORMAÇÕES COM IA")
print("="*80)

# =============================================================================
# 1. VERIFICAR DEPENDÊNCIAS
# =============================================================================

print("\n📦 VERIFICANDO DEPENDÊNCIAS...")
print("-"*80)

# Verificar OpenAI
try:
    from openai import OpenAI
    print("   ✅ openai instalado")
except ImportError:
    print("   ❌ openai não encontrado!")
    print("   Execute: pip install openai")
    sys.exit(1)

# Verificar API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("   ❌ OPENAI_API_KEY não encontrada no .env!")
    print("   Crie um arquivo .env com: OPENAI_API_KEY=sk-...")
    sys.exit(1)
else:
    print(f"   ✅ API Key OpenAI configurada")

client = OpenAI(api_key=OPENAI_API_KEY)

# =============================================================================
# 2. CONFIGURAR ARQUIVOS DE ENTRADA E SAÍDA
# =============================================================================

# Detectar arquivo de entrada mais recente
arquivos_json = list(SCRIPT_0_DIR.glob("dataset_completo_unificado_*.json"))
if not arquivos_json:
    print(f"   ❌ Nenhum arquivo JSON encontrado em {SCRIPT_0_DIR}")
    sys.exit(1)

arquivo_entrada = max(arquivos_json, key=lambda x: x.stat().st_mtime)
print(f"   📂 Arquivo de entrada: {arquivo_entrada.name}")

# Configurar pasta de saída
SCRIPT_2_IA_DIR = DATA_DIR / "script_2_ia"
SCRIPT_2_IA_DIR.mkdir(exist_ok=True)

# Arquivos de saída
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
arquivo_saida_json = SCRIPT_2_IA_DIR / f"dados_extraidos_ia_{timestamp}.json"
arquivo_saida_csv = SCRIPT_2_IA_DIR / f"dados_extraidos_ia_{timestamp}.csv"

# =============================================================================
# 3. CONFIGURAÇÕES DO MODELO
# =============================================================================

MODELO = "gpt-4o-mini"  # Melhor custo-benefício
TEMPERATURA = 0  # Determinístico (sempre mesma resposta)
MAX_RETRIES = 3  # Tentativas em caso de erro

# =============================================================================
# 4. FUNÇÃO DE EXTRAÇÃO COM IA
# =============================================================================

def extrair_informacoes_com_gpt(titulo, descricao=None):
    """
    Extrai informações estruturadas de um título/descrição de produto
    usando GPT-4o-mini com JSON mode.
    """
    
    # Montar o prompt
    texto_analise = f"Título: {titulo}"
    if descricao and str(descricao).strip() and str(descricao) != 'nan':
        texto_analise += f"\nDescrição: {descricao}"
    
    prompt = f"""Analise o seguinte produto de cartucho de tinta HP e extraia as informações de forma PRECISA:

{texto_analise}

NOMENCLATURA DE CARTUCHOS HP:
- 662 Preto, 662 Colorido, 662XL Preto, 662XL Colorido
- 664 Preto, 664 Colorido, 664XL Preto, 664XL Colorido
- 667 Preto, 667 Colorido, 667XL Preto, 667XL Colorido
- 62 Preto, 62 Colorido, 62XL Preto, 62XL Colorido
- Tricolor = Colorido = Tri-color = Color

CÓDIGOS HP (converter para tipo):
- CZ103AB = 662 Preto
- CZ104AB = 662 Colorido
- CZ105AB = 662XL Preto
- CZ106AB = 662XL Colorido
- F6V28AB = 664 Colorido
- F6V29AB = 664 Preto
- F6V30AB = 664XL Colorido
- F6V31AB = 664XL Preto
- 3YM78AB = 667 Colorido
- 3YM79AB = 667 Preto
- 3YM80AB = 667XL Colorido
- 3YM81AB = 667XL Preto

REGRAS IMPORTANTES:
1. tipo_cartucho: Identifique APENAS UM modelo (ex: "662", "662xl", "664", "664xl", "667", "667xl")
   - Se mencionar "XL" ou "xl", retorne o tipo XL (ex: "662xl", NÃO "662xl,662")
   - PRIORIDADE: XL > Standard (se tiver ambos, retorne apenas o XL)
   - Retorne APENAS UM tipo, nunca liste múltiplos separados por vírgula
   - Códigos de referência: CZ103AB=662 Preto, CZ104AB=662 Colorido, CZ105AB=662XL Preto, CZ106AB=662XL Colorido
   - Se houver dúvida entre tipos, escolha o mencionado primeiro no título
   
2. cores_detalhadas: 
   - preto: 1 se tiver cartucho preto/black, 0 se não
   - colorido: 1 se tiver cartucho colorido/tricolor/tri-color/color, 0 se não
   - Se for "kit preto + colorido" ou mencionar ambos: ambos = 1
   
3. quantidade_por_anuncio: Conte TOTAL de cartuchos no anúncio
   - "Kit 2 cartuchos" = 2
   - "Cartucho preto + cartucho colorido" = 2
   - "Cartucho" (singular) = 1
   - "Pack com 4" = 4
   - "2x preto" = 2
   - "Kit preto e colorido" = 2 (1 preto + 1 colorido)
   - "3 unidades preto" = 3
   
   IMPORTANTE: Se o kit tem PRETO E COLORIDO, a quantidade deve ser pelo menos 2!
   
4. usado_seminovo: 
   - 1 se mencionar "usado", "seminovo", "recondicionado", "remanufaturado", "vazio"
   - 0 se mencionar "novo"

⚠️ VALIDAÇÃO CRÍTICA - REGRAS DE CONSISTÊNCIA:
Antes de retornar, VERIFIQUE se os valores batem entre si:

REGRA 1 - Cores vs Quantidade:
- Se preto=1 e colorido=0 → quantidade pode ser qualquer número (ex: "2x preto" = 2)
- Se preto=0 e colorido=1 → quantidade pode ser qualquer número (ex: "3x colorido" = 3)
- Se preto=1 e colorido=1 → quantidade deve ser PAR e >= 2 (kit tem ambas as cores)
  * "Kit preto + colorido" = quantidade 2 (1 de cada)
  * "2 kits preto + colorido" = quantidade 4 (2 de cada)
  * "3 pretos e 2 coloridos" = quantidade 5

REGRA 2 - Tipo único:
- Retorne APENAS UM tipo_cartucho, mesmo se o kit tem múltiplas cores
- "Kit 664 preto + 664 colorido" → tipo_cartucho: "664" (não "664, 664")
- "Kit 662XL" → tipo_cartucho: "662xl"

REGRA 3 - Códigos HP:
- Se encontrar código tipo CZ103AB, converta para o tipo correspondente
- "Kit CZ103AB e CZ104AB" → tipo_cartucho: "662", preto=1, colorido=1, quantidade=2

Exemplos corretos:
  ✅ "2 cartuchos pretos HP 664" → tipo="664", preto=1, colorido=0, quantidade=2
  ✅ "Kit 667 preto + colorido" → tipo="667", preto=1, colorido=1, quantidade=2
  ✅ "Cartucho HP 664XL colorido" → tipo="664xl", preto=0, colorido=1, quantidade=1
  ✅ "3x 662 preto" → tipo="662", preto=1, colorido=0, quantidade=3
  ✅ "Kit CZ103AB e CZ104AB" → tipo="662", preto=1, colorido=1, quantidade=2
  
Exemplos ERRADOS:
  ❌ "Kit preto + colorido" → preto=1, colorido=1, quantidade=1 (ERRADO! kit tem 2)
  ❌ "Cartucho 664" → tipo="664, 664" (ERRADO! apenas "664")
  ❌ "CZ103AB" → tipo="CZ103AB" (ERRADO! converter para "662")

Retorne APENAS o JSON com esta estrutura exata:
{{
    "tipo_cartucho": "string",
    "cores_detalhadas": {{"preto": 0 ou 1, "colorido": 0 ou 1}},
    "quantidade_por_anuncio": número inteiro,
    "usado_seminovo": 0 ou 1
}}"""

    # Fazer a chamada à API com JSON mode
    for tentativa in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=MODELO,
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um especialista em análise de produtos HP. Responda SEMPRE com JSON válido."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=TEMPERATURA,
                response_format={"type": "json_object"}  # Garante JSON válido
            )
            
            # Extrair e parsear o JSON
            conteudo = response.choices[0].message.content
            resultado = json.loads(conteudo)
            
            # Validar estrutura
            assert 'tipo_cartucho' in resultado
            assert 'cores_detalhadas' in resultado
            assert 'quantidade_por_anuncio' in resultado
            assert 'usado_seminovo' in resultado
            assert 'preto' in resultado['cores_detalhadas']
            assert 'colorido' in resultado['cores_detalhadas']
            
            # === VALIDAÇÕES ADICIONAIS ===
            
            # 1. Normalizar tipo_cartucho (remover vírgulas, múltiplos tipos)
            tipo = str(resultado['tipo_cartucho']).lower().strip()
            # Se tem múltiplos tipos separados por vírgula, pegar o primeiro
            if ',' in tipo:
                tipo = tipo.split(',')[0].strip()
            resultado['tipo_cartucho'] = tipo
            
            # 2. Validar cores vs quantidade
            tem_preto = resultado['cores_detalhadas']['preto']
            tem_colorido = resultado['cores_detalhadas']['colorido']
            quantidade = resultado['quantidade_por_anuncio']
            
            # Se tem ambas as cores, quantidade deve ser pelo menos 2
            if tem_preto == 1 and tem_colorido == 1:
                if quantidade < 2:
                    print(f"   ⚠️ Ajuste: Kit com ambas cores, quantidade ajustada de {quantidade} para 2")
                    resultado['quantidade_por_anuncio'] = 2
            
            # Se não tem nenhuma cor, marcar como preto por padrão
            if tem_preto == 0 and tem_colorido == 0:
                print(f"   ⚠️ Ajuste: Nenhuma cor detectada, assumindo preto")
                resultado['cores_detalhadas']['preto'] = 1
            
            # 3. Garantir que quantidade é pelo menos 1
            if quantidade < 1:
                print(f"   ⚠️ Ajuste: Quantidade inválida ({quantidade}), ajustada para 1")
                resultado['quantidade_por_anuncio'] = 1
            
            return resultado
            
        except Exception as e:
            print(f"   ⚠️ Tentativa {tentativa + 1}/{MAX_RETRIES} falhou: {e}")
            if tentativa < MAX_RETRIES - 1:
                time.sleep(1)  # Aguardar 1 segundo antes de tentar novamente
            else:
                # Se todas as tentativas falharem, retornar valores padrão
                print(f"   ❌ Erro ao processar. Usando valores padrão.")
                return {
                    "tipo_cartucho": "desconhecido",
                    "cores_detalhadas": {"preto": 0, "colorido": 0},
                    "quantidade_por_anuncio": 1,
                    "usado_seminovo": 0
                }

# =============================================================================
# 5. CARREGAR DADOS
# =============================================================================

print(f"\n📂 CARREGANDO DADOS...")
print("-"*80)

# Carregar JSON unificado
with open(arquivo_entrada, 'r', encoding='utf-8') as f:
    dados = json.load(f)

print(f"   ✅ {len(dados)} produtos carregados")

# =============================================================================
# 6. PROCESSAR CADA PRODUTO
# =============================================================================

print(f"\n⚙️ PROCESSANDO PRODUTOS COM {MODELO}...")
print("-"*80)

resultados = []
inicio_total = time.time()

for idx, produto in enumerate(dados):
    inicio_produto = time.time()
    
    produto_id = produto.get('id', f'produto_{idx}')
    titulo = produto.get('titulo', '')
    descricao = produto.get('descricao', '')
    
    print(f"\n[{idx + 1}/{len(dados)}] Produto: {produto_id}")
    print(f"   📝 Título: {titulo[:80]}{'...' if len(titulo) > 80 else ''}")
    
    # Extrair informações com IA
    info = extrair_informacoes_com_gpt(titulo, descricao)
    info['id_anuncio'] = produto_id
    
    # Calcular tempo
    tempo_produto = time.time() - inicio_produto
    
    # Exibir resultado
    print(f"   ✅ Extraído em {tempo_produto:.1f}s:")
    print(f"      - Tipo: {info['tipo_cartucho']}")
    print(f"      - Cores: {'Preto' if info['cores_detalhadas']['preto'] else ''}{'/' if info['cores_detalhadas']['preto'] and info['cores_detalhadas']['colorido'] else ''}{'Colorido' if info['cores_detalhadas']['colorido'] else ''}")
    print(f"      - Quantidade: {info['quantidade_por_anuncio']}")
    print(f"      - Usado: {'Sim' if info['usado_seminovo'] else 'Não'}")
    
    resultados.append(info)
    
    # Delay para respeitar rate limits
    time.sleep(0.5)

# =============================================================================
# 7. ESTATÍSTICAS E SALVAMENTO
# =============================================================================

# Calcular estatísticas
tempo_total = time.time() - inicio_total
tempo_medio = tempo_total / len(dados)

print("\n" + "="*80)
print("📊 ESTATÍSTICAS DO PROCESSAMENTO")
print("="*80)
print(f"   Total de produtos: {len(dados)}")
print(f"   Tempo total: {tempo_total:.1f}s")
print(f"   Tempo médio por produto: {tempo_medio:.1f}s")
print(f"   Modelo usado: {MODELO}")

# Análise dos resultados
tipos_encontrados = {}
total_preto = sum(1 for r in resultados if r['cores_detalhadas']['preto'])
total_colorido = sum(1 for r in resultados if r['cores_detalhadas']['colorido'])
total_usado = sum(1 for r in resultados if r['usado_seminovo'])

for r in resultados:
    tipo = r['tipo_cartucho']
    tipos_encontrados[tipo] = tipos_encontrados.get(tipo, 0) + 1

print(f"\n📈 RESUMO DOS DADOS EXTRAÍDOS:")
print("-"*40)
print(f"   Produtos com cartucho PRETO: {total_preto}")
print(f"   Produtos com cartucho COLORIDO: {total_colorido}")
print(f"   Produtos USADOS/SEMINOVOS: {total_usado}")
print(f"\n   Tipos de cartucho encontrados:")
for tipo, count in sorted(tipos_encontrados.items(), key=lambda x: x[1], reverse=True):
    print(f"      - {tipo}: {count} produto(s)")

# Salvar resultados
print(f"\n💾 SALVANDO RESULTADOS...")
print("-"*80)

# Salvar JSON
with open(arquivo_saida_json, 'w', encoding='utf-8') as f:
    json.dump(resultados, f, indent=2, ensure_ascii=False)
print(f"   ✅ JSON salvo em: {arquivo_saida_json.name}")

# Salvar CSV
df_resultados = pd.DataFrame(resultados)
df_resultados.to_csv(arquivo_saida_csv, index=False)
print(f"   ✅ CSV salvo em: {arquivo_saida_csv.name}")

print("\n" + "="*80)
print("✅ SCRIPT 1 CONCLUÍDO COM SUCESSO!")
print("="*80)
