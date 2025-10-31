# 🛡️ Dashboard HP Anti-Fraude - Deploy

Dashboard interativo para análise e detecção de fraudes em anúncios de cartuchos HP no Mercado Livre.

## 🚀 Como Executar

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Executar o Dashboard

```bash
streamlit run app.py
```

O dashboard estará disponível em: `http://localhost:8501`

### 3. Opcional: Executar com Configurações Personalizadas

```bash
streamlit run app.py --server.port 8502 --theme.base "dark"
```

## 📁 Estrutura de Arquivos

```
deploy/
├── app.py                    # Dashboard principal (página inicial)
├── utils.py                   # Funções utilitárias compartilhadas
├── pages/                     # Páginas adicionais do dashboard
│   ├── 2_Investigacao_de_Anuncios.py
│   ├── 3_Analise_de_Vendedores.py
│   └── 4_Rede_de_Fraude.py
├── logo/                      # Assets visuais
│   └── 480px-HP_logo_2012.svg.png
└── requirements.txt           # Dependências Python
```

## 📊 Funcionalidades

### 📊 Dashboard Geral (app.py)
- **Métricas de alto nível:** Total de anúncios, suspeitos, vendedores
- **Análise de riscos:** Distribuição por categoria (Baixo, Médio, Alto, Crítico)
- **Visualizações:** Gráficos interativos de distribuição de scores
- **Análise de preços:** Relação entre preços e suspeita de fraude
- **Análise com ML:** Scores híbridos e comparação de métodos

### 🔬 Investigação de Anúncios
- **Filtros avançados:** Por score, categoria, comunidade, vendedor, preço
- **Tabela interativa:** Com links clicáveis para anúncios
- **Análise detalhada:** Flags de fraude e métricas específicas

### 👥 Análise de Vendedores
- **Ranking:** Top vendedores suspeitos
- **Métricas agregadas:** Taxa de suspeita por vendedor
- **Análise comportamental:** Padrões de comportamento

### 🕸️ Rede de Fraude
- **Análise de comunidades:** Clusters de vendedores
- **Métricas de rede:** Centralidade, PageRank
- **Visualizações:** Grafo de conexões suspeitas

## 📋 Pré-requisitos

1. **Python 3.8+** instalado
2. **Dataset processado:** Os arquivos de dados devem estar em:
   - `../data/script_7_grafo/final_grafo/dataset_final_com_grafo.csv`
   - `../data/script_7_grafo/datasets_scores/dataset_com_scores_hibridos.csv` (opcional)
3. **Dependências** instaladas via `requirements.txt`

## 🔧 Dados Necessários

O dashboard carrega dados da seguinte estrutura:

```
../data/script_7_grafo/
├── final_grafo/
│   └── dataset_final_com_grafo.csv        # Dataset principal
├── datasets_scores/
│   ├── dataset_com_scores_hibridos.csv     # Dataset com scores ML (opcional)
│   └── dataset_com_scores_hibridos_com_preco.csv
└── features/
    └── feature_importance_ridge_classifier.csv  # Feature importance (opcional)
```

### Colunas Esperadas no Dataset Principal:
- `id_anuncio`: Identificador único
- `seller_id`: ID do vendedor
- `vendedor_nome`: Nome do vendedor
- `score_de_suspeita`: Score heurístico (0-10)
- `is_fraud_suspect_v2`: Flag de suspeita (0/1)
- `preco_atual`: Preço atual do produto
- `diferenca_preco_perc`: Diferença percentual do preço
- `grafo_comunidade_id`: ID da comunidade no grafo
- `grafo_taxa_suspeita_comunidade`: Taxa de suspeita da comunidade
- `power_seller_status`: Status do vendedor
- `flag_*`: Flags de fraude específicas
- `link_anuncio`: URL do anúncio

## 🎯 Funcionalidades Avançadas

### Score Híbrido
O dashboard combina scores heurísticos com ML para maior precisão:
- **Score Heurístico:** Baseado em regras de negócio e flags (50%)
- **ML Score:** Predição do modelo de Machine Learning (50%)
- **Score Híbrido:** Combinação ponderada dos dois

### Análise de Grafo
- **Detecção de Comunidades:** Identifica grupos de vendedores suspeitos
- **Métricas de Centralidade:** PageRank, Betweenness, Closeness
- **Análise de Rede:** Visualiza conexões e padrões ocultos

### Configuração de Thresholds
- Thresholds configuráveis para heurística, ML e híbrido
- Análise de impacto de diferentes thresholds
- Comparação de resultados

## 🚨 Solução de Problemas

### Erro: "Dataset não encontrado"
- Verifique se os arquivos de dados existem em `../data/script_7_grafo/`
- Execute o pipeline de processamento de dados completo
- O dashboard irá carregar dados de exemplo se o dataset não for encontrado

### Erro: "ModuleNotFoundError"
```bash
# Instale as dependências
pip install -r requirements.txt
```

### Dashboard não abre no navegador
```bash
# Acesse manualmente
http://localhost:8501
```

### Performance lenta
- Use os filtros para reduzir o volume de dados
- O dashboard usa cache para otimizar carregamento

## 📊 Dados de Exemplo

Se o dataset não for encontrado, o dashboard carregará dados de exemplo automaticamente para demonstração.

## 🌐 Deploy em Produção

### Opção 1: Streamlit Cloud
1. Faça push do código para GitHub/GitLab
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte o repositório
4. Configure os arquivos de dados como secrets

### Opção 2: Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

### Opção 3: Servidor Dedicado
```bash
# Executar em background
nohup streamlit run app.py --server.port 8501 &
```

## 📞 Suporte

Para problemas ou dúvidas:
1. Verifique os logs do terminal
2. Confirme se os datasets foram processados
3. Teste com dados de exemplo
4. Consulte a documentação do [Streamlit](https://docs.streamlit.io)

---

**🛡️ HP Anti-Fraude Dashboard**  
**Versão:** 2.0  
**Desenvolvido com Streamlit**  
**2025**



