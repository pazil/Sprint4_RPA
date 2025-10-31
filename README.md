# 🛡️ Sprint4RPA - Sistema HP Anti-Pirataria

Sistema completo para extração, processamento e análise de anúncios de cartuchos HP no Mercado Livre, com detecção automatizada de fraudes através de técnicas de Machine Learning e análise de grafos.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
- [Fluxo de Processamento](#fluxo-de-processamento)
- [Documentação Adicional](#documentação-adicional)
- [Troubleshooting](#troubleshooting)

## 🎯 Visão Geral

Este sistema integra três componentes principais:

1. **Selenium** - Extração automatizada de dados de produtos e reviews do Mercado Livre
2. **Pipeline Auto** - Processamento e enriquecimento de dados com features de ML e análise de grafos
3. **Análise Streamlit** - Dashboard interativo para visualização e análise de resultados

### Funcionalidades Principais

- ✅ Extração automatizada de dados de produtos via web scraping
- ✅ Processamento com IA (OpenAI) para extração de informações estruturadas
- ✅ Análise de NLP em reviews usando VADER e embeddings
- ✅ Processamento de imagens e extração de features visuais
- ✅ Criação de features de grafo para detecção de redes de fraude
- ✅ Dashboard interativo com visualizações e métricas em tempo real
- ✅ Sistema de scoring híbrido (regras + ML) para detecção de fraudes

### 🌐 Deploy e Recursos

- 🚀 **Deploy da Solução:** [https://sprint4frontend.streamlit.app](https://sprint4frontend.streamlit.app)
- 🎥 **Vídeo Explicativo:** [https://youtu.be/SyUYkySEhoM](https://youtu.be/SyUYkySEhoM)
- 📦 **Repositório FrontEnd:** [https://github.com/pazil/Sprint4_FrontEnd](https://github.com/pazil/Sprint4_FrontEnd)

## 📁 Estrutura do Projeto

```
Sprint4RPA/
├── Selenium/
│   ├── extrator_completo_integrado.py    # Extrator principal de dados
│   └── data/
│       └── dados_extraidos/              # Dados extraídos (JSON)
│           ├── lote/
│           ├── tipo_especifico/
│           └── produto_especifico/
│
├── pipeline_auto/
│   ├── pipeline.py                       # Orquestrador principal
│   ├── pipeline_executor.py              # Executor programático (para Streamlit)
│   ├── steps/                            # Scripts de processamento
│   │   ├── 0_unificar_dados_brutos.py
│   │   ├── 1_filtrar_campos_essenciais.py
│   │   ├── 2_extrair_informacoes_ia.py
│   │   ├── 3_processar_features_basicas.py
│   │   ├── 4_processar_reviews_nlp.py
│   │   ├── 5_baixar_processar_imagens.py
│   │   ├── 6_criar_target_merge.py
│   │   └── 7_criar_features_grafo.py
│   ├── ml/                               # Modelos de ML pré-treinados
│   └── ml_score/                         # Scripts de scoring
│
├── analise_streamlit/
│   ├── app.py                            # Dashboard principal
│   ├── pages/                            # Páginas do dashboard
│   │   ├── 2_Investigacao_de_Anuncios.py
│   │   ├── 3_Analise_de_Vendedores.py
│   │   ├── 4_Rede_de_Fraude.py
│   │   └── 5_Extrair_Analisar_Anuncio.py
│   ├── processamento_anuncio.py          # Módulo de processamento
│   ├── utils.py                          # Funções utilitárias
│   ├── data/                             # Datasets processados
│   └── requirements.txt
│
├── README.md                             # Este arquivo
├── requirements.txt                      # Dependências principais
├── .gitignore                            # Arquivos ignorados no Git
└── RELATORIO_FINAL.md                    # Relatório técnico completo
```

## 🚀 Instalação

### Pré-requisitos

- Python 3.8 ou superior
- Chrome ou Microsoft Edge instalado
- Conta no Mercado Livre (para extração de dados)
- OpenAI API Key (para etapas de IA e NLP)

### Passo 1: Clonar/Download do Projeto

```bash
cd Sprint4RPA
```

### Passo 2: Criar Ambiente Virtual (Recomendado)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Passo 3: Instalar Dependências

```bash
pip install -r requirements.txt
```

### Passo 4: Instalar Dependências do Dashboard

```bash
cd analise_streamlit
pip install -r requirements.txt
cd ..
```

## ⚙️ Configuração

### 1. Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto ou em `pipeline_auto/`:

```bash
# pipeline_auto/.env ou .env na raiz
OPENAI_API_KEY=sk-sua-chave-aqui
```

**Importante:** 
- A `OPENAI_API_KEY` é obrigatória para executar os scripts 2 e 4 do pipeline
- Sem ela, você pode pular essas etapas usando `--pular "2,4"`

### 2. Estrutura de Pastas

O sistema criará automaticamente as pastas necessárias, mas você pode verificar:

```bash
# Pastas de dados (serão criadas automaticamente)
data/
├── script_0_unificar_dados/
├── script_1_filtrar_campos/
├── script_2_ia/
├── script_3_features_basicas/
├── script_4_nlp/
├── script_5_imagens/
├── script_6_target_merge/
└── script_7_grafo/

# Dados extraídos pelo Selenium
Selenium/data/dados_extraidos/
├── lote/
├── tipo_especifico/
└── produto_especifico/
```

## 🎮 Uso

### Modo 1: Pipeline via Linha de Comando

#### Executar Pipeline Completo

```bash
python pipeline_auto/pipeline.py
```

#### Executar com Opções

```bash
# Pular etapas de IA (se não tiver OPENAI_API_KEY)
python pipeline_auto/pipeline.py --pular "2,4"

# Parar após uma etapa específica
python pipeline_auto/pipeline.py --parar-em 3

# Consolidar dados antigos do Selenium
python pipeline_auto/pipeline.py --consolidar-selenium
```

### Modo 2: Dashboard Streamlit (Recomendado)

#### Iniciar Dashboard

```bash
cd analise_streamlit
streamlit run app.py
```

O dashboard será aberto automaticamente em `http://localhost:8501`

#### Funcionalidades do Dashboard

1. **Dashboard Geral** - Visão geral com métricas e análises
2. **Investigação de Anúncios** - Filtros e análise detalhada
3. **Análise de Vendedores** - Ranking e métricas por vendedor
4. **Rede de Fraude** - Visualização de comunidades suspeitas
5. **Extrair e Analisar Anúncio** - Extração e processamento de novos produtos

### Modo 3: Extração via Selenium Direto

```python
from Selenium.extrator_completo_integrado import extract_javascript_data_advanced
from selenium import webdriver

driver = webdriver.Chrome()  # ou Edge()
url = "https://www.mercadolivre.com.br/produto/MLB..."
produto = extract_javascript_data_advanced очередные, url)
driver.quit()
```

## 🔄 Fluxo de Processamento

### Pipeline Completo (8 Etapas)

```
┌─────────────────────────────────────────────────────────┐
│ 1. SELENIUM - Extração de Dados                        │
│    └─> produto_especifico_*.json                       │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Script 0 - Unificar Dados Brutos                    │
│    └─> dataset_completo_unificado_*.json               │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Script 1 - Filtrar Campos Essenciais                │
│    └─> dataset_com_campos_essenciais_*.csv             │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Script 2 - Extrair Informações com IA ⚠️            │
│    └─> dataset_com_ia_*.csv                            │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 5. Script 3 - Processar Features Básicas               │
│    └─> dataset_com_features_basicas_*.csv              │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 6. Script 4 - Processar Reviews NLP ⚠️                 │
│    └─> reviews_com_nlp_*.csv                           │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 7. Script 5 - Baixar e Processar Imagens               │
│    └─> dataset_com_imagens_*.csv                       │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 8. Script 6 - Criar Target e Merge                     │
│    └─> dataset_com_target_*.csv                        │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 9. Script 7 - Criar Features de Grafo                  │
│    └─> dataset_final_com_grafo.csv                     │
└─────────────────────────────────────────────────────────┘
```

⚠️ **Nota:** Scripts 2 e 4 requerem `OPENAI_API_KEY`

## 📊 Outputs Principais

### Dataset Final

**Localização:** `data/script_7_grafo/dataset_final_com_grafo.csv`

**Principais Colunas:**
- `id_anuncio` - ID único do anúncio
- `is_fraud_suspect_v2` - Flag de suspeita de fraude (0/1)
- `fraud_score_v2` - Score de fraude (0-100)
- `risk_category` - Categoria de risco (Baixo/Médio/Alto/Crítico)
- `seller_id` - ID do vendedor
- Features de grafo: `community_id`, `degree`, `clustering_coefficient`, etc.
- Features de ML: scores híbridos, embeddings, etc.

### Datasets Intermediários

Cada script gera outputs em suas respectivas pastas em `data/`:
- `script_0_unificar_dados/` - Datasets unificados
- `script_1_filtrar_campos/` - Campos essenciais
- `script_2_ia/` - Features extraídas com IA
- `script_3_features_basicas/` - Features básicas calculadas
- `script_4_nlp/` - Features de NLP
- `script_5_imagens/` - Features de imagens
- `script_6_target_merge/` - Datasets com target
- `script_7_grafo/` - Dataset final com grafo

## 📚 Documentação Adicional

- **GUIA_TESTE.md** - Guia detalhado de testes e troubleshooting
- **RELATORIO_FINAL.md** - Relatório técnico completo do projeto
- **DEPLOY_CHECKLIST.md** - Checklist para deploy do dashboard

## 🔧 Troubleshooting

### Erro: "OPENAI_API_KEY ausente"

**Solução:**
1. Crie arquivo `.env` com sua chave
2. Ou pule as etapas: `--pular "2,4"`

### Erro: "Navegador não encontrado"

**Solução:**
- Instale Chrome ou Edge
- O WebDriver será baixado automaticamente

### Erro: "Dataset não encontrado"

**Solução:**
- Execute o pipeline completo primeiro
- Verifique se os dados do Selenium existem em cue

`Selenium/data/dados_extraidos/`

### Erro: "ModuleNotFoundError"

**Solução:**
```bash
pip install -r requirements.txt
cd analise_streamlit
pip install -r requirements.txt
```

### Erro de Encoding (Windows)

**Solução:**
- O sistema já está configurado para evitar emojis no Windows
- Se persistir, configure o terminal para UTF-8:
  ```powershell
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
  ```

## 📝 Exemplos de Uso

### Exemplo 1: Extrair e Processar Um Produto via Dashboard

1. Abra o Streamlit: `streamlit run analise_streamlit/app.py`
2. Navegue para "Extrair e Analisar Anúncio"
3. Cole a URL do produto do Mercado Livre
4. Clique em "Extrair e Processar"
5. Aguarde o processamento completo (~10-20 minutos)

### Exemplo 2: Processar Dados Já Extraídos

```bash
# Certifique-se de que há dados em Selenium/data/dados_extraidos/
python pipeline_auto/pipeline.py
```

### Exemplo 3: Apenas Análise de Dados Existentes

```bash
# Pular extração e processamento pesado
python pipeline_auto/pipeline.py --pular "0,2,4,5"
```

## 🎯 Próximos Passos

1. **Treinar Modelos:** Ajustar modelos de ML em `pipeline_auto/ml/`
2. **Adicionar Features:** Criar novas features em scripts específicos
3. **Deploy:** Seguir `DEPLOY_CHECKLIST.md` para produção
4. **Monitoramento:** Configurar alertas baseados em scores de fraude


## 📄 Licença

Este projeto foi desenvolvido para HP como parte do sistema de detecção de fraudes.

## 👥 Equipe

Desenvolvido para Sprint4RPA - Sistema HP Anti-Pirataria

---

**Última atualização:** Outubro 2024

Para mais informações, consulte o `RELATORIO_FINAL.md` ou abra uma issue no repositório.

