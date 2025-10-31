# ✅ Checklist de Deploy - Dashboard HP Anti-Fraude

## 📋 Estrutura de Arquivos (Deploy)

```
deploy/
├── app.py                              # ✅ Dashboard principal (renomeado de 1_Dashboard_Geral.py)
├── utils.py                            # ✅ Funções utilitárias
├── requirements.txt                     # ✅ Dependências Python
├── README.md                            # ✅ Documentação
├── data/                                # ✅ DATASETS COPIADOS
│   ├── final_grafo/
│   │   └── dataset_final_com_grafo.csv
│   ├── datasets_scores/
│   │   ├── dataset_com_scores_hibridos.csv
│   │   └── dataset_com_scores_hibridos_com_preco.csv
│   └── features/
│       └── feature_importance_ridge_classifier.csv
├── pages/                               # ✅ Páginas adicionais
│   ├── 2_Investigacao_de_Anuncios.py
│   ├── 3_Analise_de_Vendedores.py
│   └── 4_Rede_de_Fraude.py
├── logo/                                # ✅ Assets visuais
│   └── 480px-HP_logo_2012.svg.png
└── .streamlit/                          # ✅ Configurações (se houver)

```

## ✅ Tarefas Completadas

- [x] Renomear dashboard v2 para app.py
- [x] Verificar requirements.txt
- [x] Copiar arquivos necessários para pasta deploy
- [x] Ajustar caminhos nos arquivos do deploy
- [x] Criar requirements.txt para deploy
- [x] Criar README.md para deploy
- [x] Copiar datasets para deploy/data/
- [x] Ajustar todos os caminhos de datasets nos arquivos

## 🎯 Como Executar

```bash
cd deploy
pip install -r requirements.txt
streamlit run app.py
```

Acesse: `http://localhost:8501`

## 📊 Dados Disponíveis

### Dataset Principal
- **Caminho:** `data/final_grafo/dataset_final_com_grafo.csv`
- **Descrição:** Dataset principal com features de grafo
- **Obrigatório:** ✅ SIM

### Scores de ML (Opcional)
- **Caminho:** `data/datasets_scores/dataset_com_scores_hibridos.csv`
- **Descrição:** Dataset com scores de machine learning
- **Obrigatório:** ❌ NÃO (dashboard funciona sem isso)

### Feature Importance (Opcional)
- **Caminho:** `data/features/feature_importance_ridge_classifier.csv`
- **Descrição:** Importância das features para análise
- **Obrigatório:** ❌ NÃO (dashboard funciona sem isso)

## 🔧 Verificações

### 1. Dependências Instaladas?
```bash
cd deploy
pip install -r requirements.txt
```

### 2. Datasets Presentes?
```bash
# Verificar se os arquivos existem
dir data\final_grafo\dataset_final_com_grafo.csv
dir data\datasets_scores\*.csv
```

### 3. App Funciona?
```bash
cd deploy
streamlit run app.py
```

## 🌐 Deploy em Produção

### Opção 1: Streamlit Cloud
1. Faça push do repositório para GitHub
2. Acesse https://share.streamlit.io
3. Conecte o repositório
4. Pasta principal: `deploy`
5. Arquivo principal: `app.py`

### Opção 2: Heroku
```bash
cd deploy
# Criar Procfile
echo "web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0" > Procfile
# Deploy
git init
git add .
git commit -m "Deploy dashboard"
heroku create
git push heroku main
```

### Opção 3: Servidor Dedicado
```bash
cd deploy
# Executar em background
nohup streamlit run app.py --server.port 8501 &
```

## ⚠️ Problemas Comuns

### 1. "ModuleNotFoundError: No module named 'streamlit'"
**Solução:** 
```bash
pip install -r requirements.txt
```

### 2. "Dataset não encontrado"
**Solução:** 
- Verifique se os arquivos estão em `deploy/data/`
- Verifique os caminhos nos arquivos `app.py` e `utils.py`

### 3. "Port already in use"
**Solução:**
```bash
streamlit run app.py --server.port 8502
```

## 📝 Notas Importantes

1. **Todos os datasets estão dentro da pasta deploy/** - Não precisa acessar a pasta pai
2. **Caminhos ajustados** - Todos os arquivos `.py` agora usam caminhos relativos a partir de `deploy/`
3. **Dependências mínimas** - `requirements.txt` contém apenas o necessário para o dashboard
4. **Dados de exemplo** - Se datasets não forem encontrados, o app carrega dados de exemplo

## ✅ Status Final

✅ **Deploy pronto!** Todos os arquivos necessários estão na pasta `deploy/` e prontos para deploy em produção.

---

**Data:** 28/10/2025  
**Versão:** 2.0  
**Status:** ✅ PRONTO PARA DEPLOY



