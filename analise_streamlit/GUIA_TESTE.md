# 🔍 Guia de Teste - Extração e Análise de Anúncio

## 📋 Pré-requisitos

### 1. Verificar Dependências
Certifique-se de que todas as dependências estão instaladas:

```bash
cd Sprint4RPA/analise_streamlit
pip install -r requirements.txt
```

### 2. Verificar Estrutura de Pastas
Confirme que as seguintes pastas existem:
- ✅ `Sprint4RPA/Selenium/extrator_completo_integrado.py`
- ✅ `Sprint4RPA/pipeline_auto/pipeline_executor.py`
- ✅ `Sprint4RPA/analise_streamlit/processamento_anuncio.py`
- ✅ `Sprint4RPA/analise_streamlit/pages/5_Extrair_Analisar_Anuncio.py`
- ✅ `data/script_7_grafo/dataset_final_com_grafo.csv` (dataset principal)

### 3. Verificar Variáveis de Ambiente
Certifique-se de que o arquivo `.env` existe com a `OPENAI_API_KEY`:

**Localização:** `Sprint4RPA/pipeline_auto/.env` ou raiz do projeto

**Conteúdo mínimo:**
```
OPENAI_API_KEY=sk-...
```

### 4. Verificar Navegador
- Chrome ou Edge deve estar instalado
- WebDriver será baixado automaticamente pelo `webdriver_manager`

## 🚀 Passos para Testar

### Passo 1: Iniciar o Streamlit

```bash
cd Sprint4RPA/analise_streamlit
streamlit run app.py
```

O Streamlit abrirá automaticamente no navegador (geralmente em `http://localhost:8501`).

### Passo 2: Navegar para a Página de Extração

1. No menu lateral esquerdo, clique em **"🔍 Extrair e Analisar Anúncio"**
2. Ou acesse diretamente navegando até a página 5

### Passo 3: Configurar URL do Anúncio

1. Na caixa de texto "URL do Produto", você verá a URL padrão:
   ```
   https://www.mercadolivre.com.br/cartucho-hp-667xl-preto-85ml/p/MLB37822949
   ```

2. Você pode:
   - **Usar a URL padrão** (já preenchida)
   - **Digitar uma nova URL** de um produto do Mercado Livre
   - **Colar uma URL** de outro produto

3. A URL será validada automaticamente:
   - ✅ Verde = URL válida
   - ⚠️ Amarelo = URL inválida (será exibida mensagem de erro)

### Passo 4: Iniciar Extração

1. Clique no botão **"🔍 Extrair e Processar"**

2. **Primeira execução:** Uma janela do navegador (Chrome/Edge) será aberta
   - Faça login no Mercado Livre quando solicitado
   - Aguarde a mensagem de confirmação
   - O navegador permanecerá aberto para reutilização

3. O processamento seguirá estas etapas:

   **Etapa 1: Configuração do Navegador (5%)**
   - Configuração inicial ou reutilização do navegador existente

   **Etapa 2: Extração de Dados (10% - 25%)**
   - Extração de dados do produto via Selenium
   - Extração de reviews
   - Validação dos dados

   **Etapa 3: Preparação para Pipeline (30% - 60%)**
   - Salvamento dos dados extraídos
   - Preparação de `reviews_unificado.json`
   - Preparação do dataset unificado

   **Etapa 4: Execução do Pipeline (60% - 95%)**
   - Script 0: Unificar dados brutos
   - Script 1: Filtrar campos essenciais
   - Script 2: Extrair informações com IA ⚠️ (requer OPENAI_API_KEY)
   - Script 3: Processar features básicas
   - Script 4: Processar reviews NLP ⚠️ (requer OPENAI_API_KEY)
   - Script 5: Baixar e processar imagens
   - Script 6: Criar target e merge
   - Script 7: Criar features de grafo

   **Etapa 5: Mesclagem Final (95% - 100%)**
   - Adição ao dataset principal
   - Invalidação de cache
   - Preview dos resultados

### Passo 5: Verificar Resultados

Após o processamento completo, você verá:

1. **Mensagem de Sucesso:** ✅ "Processamento concluído com sucesso!"

2. **Preview do Anúncio Processado:**
   - Dados JSON do produto extraído
   - Dados processados do dataset final

3. **Próximos Passos:**
   - Navegar para o Dashboard Geral
   - Investigar o anúncio na página de Investigação
   - Analisar o vendedor

### Passo 6: Verificar no Dashboard

1. Vá para **"📊 Dashboard Geral"**
2. Verifique se o novo anúncio aparece nas análises
3. Use os filtros para encontrar o anúncio recém-processado

### Passo 7: Investigar o Anúncio

1. Vá para **"🔬 Investigação de Anúncios"**
2. Use os filtros para encontrar o anúncio pelo:
   - ID do anúncio
   - Vendedor
   - Score de suspeita
   - Link do anúncio

## ⚠️ Possíveis Problemas e Soluções

### Problema 1: "Módulo Selenium não disponível"

**Solução:**
```bash
pip install selenium webdriver-manager
```

### Problema 2: "OPENAI_API_KEY ausente"

**Solução:**
1. Crie o arquivo `.env` em `Sprint4RPA/pipeline_auto/`
2. Adicione: `OPENAI_API_KEY=sua_chave_aqui`
3. Ou exporte a variável de ambiente:
   ```bash
   # Windows PowerShell
   $env:OPENAI_API_KEY="sua_chave_aqui"
   
   # Linux/Mac
   export OPENAI_API_KEY="sua_chave_aqui"
   ```

### Problema 3: Navegador não abre

**Solução:**
- Verifique se Chrome ou Edge是和 instalado
- O WebDriver será baixado automaticamente
- Se persistir, instale manualmente o ChromeDriver

### Problema 4: Erro ao executar pipeline

**Solução:**
- Verifique se todos os scripts existem em `scripts/`
- Verifique se há espaço em disco suficiente
- Verifique os logs de erro no console do Streamlit

### Problema 5: Cache do Streamlit não atualiza

**Solução:**
- Clique em "Rerun" no menu do Streamlit (⋮)
- Ou use `Ctrl+R` / `Cmd+R` para recarregar
- A função `clear_streamlit_cache()` deve ser chamada automaticamente

### Problema 6: Dataset não encontrado

**Solução:**
- Verifique se `data/script_7_grafo/dataset_final_com_grafo.csv` existe
- Verifique se o pipeline foi executado com sucesso
- Verifique os caminhos no código

## 📊 Verificação de Sucesso

O teste foi bem-sucedido se:

- ✅ Navegador abre e faz login no Mercado Livre
- ✅ Dados são extraídos com sucesso
- ✅ Pipeline executa todas as 8 etapas sem erros
- ✅ Anúncio aparece no preview após processamento
- ✅ Anúncio é adicionado ao dataset principal
- ✅ Anúncio aparece nas páginas de análise

## 🔄 Teste Rápido (Sem Pipeline Completo)

Para testar apenas a extração (pular o pipeline completo):

1. Modifique temporariamente a página para pular etapas:
   ```python
   sucesso_pipeline = executar_pipeline_programatico(
       pular=[2, 4, 5],  # Pula IA, NLP e imagens
       progress_callback=callback_pipeline
   )
   ```

2. Ou teste apenas a extração:
   - Remova temporariamente a chamada do pipeline
   - Verifique se os dados são salvos em `Selenium/data/dados_extraidos/produto_especifico/`

## 📝 Notas Importantes

1. **Tempo de Processamento:**
   - Extração: ~2-5 minutos
   - Pipeline completo: ~5-15 minutos (depende da etapa de IA)
   - Total: ~7-20 minutos por anúncio

2. **Reutilização do Navegador:**
   - O navegador permanece aberto durante a sessão do Streamlit
   - Não é necessário fazer login novamente para múltiplas extrações
   - Feche o navegador manualmente se necessário

3. **Backup Automático:**
   - Um backup do dataset é criado antes de adicionar novo registro
   - Backups são salvos em `data/final_grafo/dataset_final_com_grafo_backup_*.csv`

4. **Logs e Debug:**
   - Erros são exibidos na interface do Streamlit
   m- Use "Rerun" para ver logs atualizados
   - Verifique o console do terminal onde o Streamlit está rodando

## 🎯 Teste de Integração Completo

Para um teste completo end-to-end:

1. ✅ Extrair anúncio novo
2. ✅ Verificar no Dashboard Geral
3. ✅ Investigar o anúncio específico
4. ✅ Analisar o vendedor
5. ✅ Verificar rede de fraude (se aplicável)
6. ✅ Exportar resultados

---

**Boa sorte com os testes! 🚀**

Se encontrar problemas, verifique os logs de erro e a seção de problemas acima.

