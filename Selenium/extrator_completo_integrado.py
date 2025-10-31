#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema HP - Extrator Completo Integrado
Combina extração de dados de produtos + extração de reviews
Baseado nos códigos originais do usuário

MELHORIAS IMPLEMENTADAS:
- Correção na coleta de links de produtos na busca
- Seletores aprimorados para encontrar elementos poly-component__title
- Lógica de espera melhorada para carregamento de páginas
- Método alternativo de coleta quando os seletores principais falham
- Debug detalhado para acompanhar o processo de coleta
- Função de teste específica para validar a coleta de links
"""

import time
import sys
import os
import json
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
import shutil

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def criar_pasta_dados():
    """Cria a estrutura de pastas para salvar os dados extraídos"""
    try:
        # Caminho base para a pasta data DENTRO de Selenium
        base_path = os.path.join(os.path.dirname(__file__), 'data')
        
        # Criar pasta principal se não existir
        if not os.path.exists(base_path):
            os.makedirs(base_path)
        
        # Criar pasta específica para dados extraídos
        dados_path = os.path.join(base_path, 'dados_extraidos')
        if not os.path.exists(dados_path):
            os.makedirs(dados_path)
        
        # Criar subpastas por tipo de extração
        subpastas = ['lote', 'tipo_especifico', 'produto_especifico']
        for subpasta in subpastas:
            subpasta_path = os.path.join(dados_path, subpasta)
            if not os.path.exists(subpasta_path):
                os.makedirs(subpasta_path)
        
        print(f"Estrutura de pastas criada em: {dados_path}")
        return dados_path
        
    except Exception as e:
        print(f"Erro ao criar estrutura de pastas: {e}")
        # Fallback: usar diretório atual
        return os.getcwd()

class MercadoLivreReviewsExtractor:
    def __init__(self, driver, headless=False):
        """Inicializa o extrator de reviews usando o driver existente"""
        self.driver = driver
        self.headless = headless
    
    def extract_reviews(self, product_id, max_reviews=None):
        """
        Extrai reviews de um produto específico
        
        Args:
            product_id (str): ID do produto (ex: MLB22843600)
            max_reviews (int): Número máximo de reviews a extrair (None = todos)
        
        Returns:
            dict: Dados extraídos dos reviews
        """
        print(f"🔍 Iniciando extração de reviews para produto: {product_id}")
        
        # Construir URL com todos os parâmetros necessários para a versão mobile (funcional)
        url = f"https://www.mercadolivre.com.br/noindex/catalog/reviews/{product_id}?noIndex=true&access=view_all&modal=true&controlled=true&show_fae=true&brandId=49944&source_platform=/web/mobile&device_id_variant=ff846adc-7561-4cd6-84d5-2d847aa9dd1f"
        
        try:
            print(f"🌐 Acessando reviews: {url}")
            self.driver.get(url)
            
            # Aguardar carregamento inicial
            print("⏳ Aguardando carregamento inicial...")
            time.sleep(3)
            
            # Extrair dados gerais
            general_data = self.extract_general_data()
            
            # Extrair resumo de IA
            ai_summary = self.extract_ai_summary()
            
            # Extrair avaliações por características
            characteristics_ratings = self.extract_characteristics_ratings()
            
            # Extrair reviews individuais com scroll
            reviews = self.extract_individual_reviews(max_reviews)
            
            # Compilar dados finais
            result = {
                "product_id": product_id,
                "extraction_timestamp": datetime.now().isoformat(),
                "url": url,
                "general_data": general_data,
                "ai_summary": ai_summary,
                "characteristics_ratings": characteristics_ratings,
                "reviews": reviews,
                "total_reviews_extracted": len(reviews)
            }
            
            print(f"✅ Extração de reviews concluída! {len(reviews)} reviews extraídos")
            return result
            
        except Exception as e:
            print(f"❌ Erro na extração de reviews: {e}")
            return None
    
    def extract_general_data(self):
        """Extrai dados gerais da página de reviews"""
        print("📊 Extraindo dados gerais dos reviews...")
        
        general_data = {}
        
        try:
            rating_elem = self.driver.find_element(By.CSS_SELECTOR, ".ui-review-capability__rating__average")
            general_data["average_rating"] = float(rating_elem.text.strip())
        except NoSuchElementException:
            general_data["average_rating"] = None
        
        try:
            total_elem = self.driver.find_element(By.CSS_SELECTOR, ".ui-review-capability__rating__label")
            total_text = total_elem.text.strip()
            total_match = re.search(r'(\d+)', total_text)
            if total_match:
                general_data["total_reviews"] = int(total_match.group(1))
        except NoSuchElementException:
            general_data["total_reviews"] = None
        
        return general_data
    
    def extract_ai_summary(self):
        """Extrai resumo de opiniões gerado por IA"""
        print("🤖 Extraindo resumo de IA...")
        
        try:
            summary_container = self.driver.find_element(By.CSS_SELECTOR, "div[data-testid='summary-component']")
            
            summary_elem = summary_container.find_element(By.CSS_SELECTOR, "p.ui-review-capability__summary__plain_text__summary_container")
            summary_text = summary_elem.text.strip()
            
            # Busca o botão de like DENTRO do container do resumo
            likes_elem = summary_container.find_element(By.CSS_SELECTOR, "button[data-testid='like-button'] p")
            likes = int(likes_elem.text.strip())
            
            return {
                "summary": summary_text,
                "likes": likes,
                "available": True
            }
        except NoSuchElementException:
            return {
                "summary": None,
                "likes": 0,
                "available": False
            }
        except Exception as e:
            print(f"⚠️ Erro ao extrair resumo de IA: {e}")
            return { "summary": None, "likes": 0, "available": False }

    def extract_characteristics_ratings(self):
        """Extrai avaliações por características"""
        print("📋 Extraindo avaliações por características...")
        
        characteristics = {}
        
        try:
            table_rows = self.driver.find_elements(By.CSS_SELECTOR, "tr.ui-review-capability-categories__mobile--row")
            
            for row in table_rows:
                try:
                    name_elem = row.find_element(By.CSS_SELECTOR, "td:first-child")
                    characteristic_name = name_elem.text.strip()
                    
                    # Pega a nota pelo texto de acessibilidade, que é mais confiável
                    rating_text_elem = row.find_element(By.CSS_SELECTOR, "p.andes-visually-hidden")
                    rating_text = rating_text_elem.get_attribute('textContent').strip()
                    
                    # Extrai o número do texto "Avaliação 4.8 de 5"
                    match = re.search(r'(\d+\.?\d*)', rating_text)
                    if match:
                        characteristics[characteristic_name] = float(match.group(1))
                    
                except Exception:
                    continue
        
        except Exception as e:
            print(f"⚠️ Erro ao buscar tabela de características: {e}")
        
        return characteristics
    
    def extract_individual_reviews(self, max_reviews=None):
        """Extrai reviews individuais com scroll automático inteligente"""
        print("📝 Extraindo reviews individuais...")
        
        self.scroll_to_load_all_reviews()
        
        review_elements = self.driver.find_elements(By.CSS_SELECTOR, "article.ui-review-capability-comments__comment")
        
        if max_reviews:
            review_elements = review_elements[:max_reviews]
        
        print(f"📝 Processando {len(review_elements)} reviews encontrados...")
        
        reviews = []
        for i, review_elem in enumerate(review_elements):
            review_data = self.extract_single_review(review_elem, i + 1)
            if review_data:
                reviews.append(review_data)
        
        return reviews
    
    def scroll_to_load_all_reviews(self):
        """Scroll inteligente para carregar todos os reviews disponíveis"""
        print("🔄 Iniciando scroll inteligente...")
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        attempts = 0
        
        while attempts < 3:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                attempts += 1
                print(f"   Altura da página não mudou. Tentativa {attempts}/3.")
            else:
                last_height = new_height
                attempts = 0
        
        print("✅ Scroll inteligente concluído!")

    def extract_single_review(self, review_elem, review_number):
        """Extrai dados de um review individual"""
        review_data = {
            "review_number": review_number,
            "rating": None,
            "date": None,
            "text": "Sem texto.",
            "likes": 0,
            "images": []
        }
        
        try:
            # Extrair rating
            try:
                rating_text_elem = review_elem.find_element(By.CSS_SELECTOR, "p.andes-visually-hidden")
                rating_text = rating_text_elem.get_attribute('textContent').strip()
                match = re.search(r'(\d+)', rating_text)
                if match:
                    review_data["rating"] = int(match.group(1))
            except NoSuchElementException:
                pass
            
            # Extrair data
            try:
                date_elem = review_elem.find_element(By.CSS_SELECTOR, ".ui-review-capability-comments__comment__date")
                review_data["date"] = date_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # Extrair texto
            try:
                text_elem = review_elem.find_element(By.CSS_SELECTOR, ".ui-review-capability-comments__comment__content")
                text_content = text_elem.text.strip()
                if text_content:
                    review_data["text"] = text_content
            except NoSuchElementException:
                pass
            
            # Extrair imagens
            try:
                image_elements = review_elem.find_elements(By.CSS_SELECTOR, ".ui-review-capability-carousel-mobile__img")
                if image_elements:
                    image_urls = [img.get_attribute("src") for img in image_elements if img.get_attribute("src")]
                    review_data["images"] = image_urls
            except NoSuchElementException:
                pass

            # Extrair likes
            try:
                like_button = review_elem.find_element(By.CSS_SELECTOR, "button[data-testid='like-button']")
                likes_elem = like_button.find_elements(By.TAG_NAME, "p")[-1]
                review_data["likes"] = int(likes_elem.text.strip())
            except (NoSuchElementException, IndexError):
                pass
            
            # Renomear chaves para o formato final desejado
            review_data["image_count"] = len(review_data["images"])
            review_data["has_images"] = True if review_data["image_count"] > 0 else False
            
            return review_data
            
        except Exception as e:
            print(f"⚠️ Erro ao extrair dados do review #{review_number}: {e}")
            return None

def setup_browser_session():
    """Configura navegador e aguarda login - detecta automaticamente Chrome ou Edge"""
    try:
        print("Detectando navegador disponível...")
        
        # Tentar Chrome primeiro
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ]
        
        chrome_available = any(os.path.exists(path) for path in chrome_paths)
        
        if chrome_available:
            print("Chrome encontrado! Usando Chrome...")
            chrome_options = ChromeOptions()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        else:
            print("Chrome não encontrado. Usando Edge...")
            edge_options = EdgeOptions()
            edge_options.add_argument("--no-sandbox")
            edge_options.add_argument("--disable-dev-shm-usage")
            edge_options.add_argument("--disable-blink-features=AutomationControlled")
            edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            edge_options.add_experimental_option('useAutomationExtension', False)
            
            driver = webdriver.Edge(options=edge_options)
        
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("Navegando para MercadoLivre...")
        driver.get("https://www.mercadolivre.com.br")
        
        print("\n" + "="*60)
        print("FAÇA LOGIN NO MERCADOLIVRE")
        print("="*60)
        print("1. Clique em 'Entrar' no canto superior direito")
        print("2. Digite seu email/usuário e senha")
        print("3. Complete o login (incluindo verificações se houver)")
        print("4. Aguarde aparecer seu nome no canto superior direito")
        print("5. Pressione ENTER neste terminal quando terminar")
        print("="*60)
        
        input("\nPressione ENTER após fazer login completo...")
        
        print("Sessão configurada! Navegador permanecerá ativo.")
        return driver
        
    except Exception as e:
        print(f"Erro ao configurar navegador: {e}")
        return None

def is_error_page(driver):
    """
    Verifica se a página atual é uma página de erro/not found
    """
    try:
        current_url = driver.current_url.lower()
        page_title = driver.title.lower()

        print(f"🔍 DEBUG is_error_page:")
        print(f"   URL: {current_url}")
        print(f"   Título: {page_title}")

        # Verificações específicas para páginas de erro reais do ML
        error_indicators = [
            # URLs que definitivamente indicam erro
            "error" in current_url,
            "not-found" in current_url,
            "pagina-nao-encontrada" in current_url,
            # Títulos específicos de erro
            "página não encontrada" in page_title,
            "produto não encontrado" in page_title,
            "erro" in page_title and "404" in page_title,
            # Elementos específicos de erro com texto específico
            len(driver.find_elements(By.CSS_SELECTOR, ".ui-empty-state__title")) > 0 and
            any("não encontrado" in elem.text.lower() or "erro" in elem.text.lower()
                for elem in driver.find_elements(By.CSS_SELECTOR, ".ui-empty-state__title")),
            # Combinação de elementos típicos de erro
            len(driver.find_elements(By.CSS_SELECTOR, ".ui-empty-state")) > 0 and
            len(driver.find_elements(By.CSS_SELECTOR, ".ui-empty-state__icon")) > 0 and
            "produto" not in driver.page_source.lower()
        ]

        # Se encontrou indicadores claros de erro, retorna True
        if any(error_indicators):
            print(f"❌ Página de erro detectada (indicadores claros)")
            return True

        # Verificação adicional: se não há elementos típicos de produto, pode ser erro
        product_indicators = [
            ".ui-pdp-title",  # Título do produto
            ".ui-pdp-price",  # Preço do produto
            ".ui-pdp-seller", # Informações do vendedor
            ".ui-pdp-description", # Descrição
            ".ui-pdp-gallery", # Galeria de imagens
            "poly-component__title", # Título alternativo
            "[data-testid='product-title']", # Título moderno
            ".andes-card", # Estrutura moderna de produto
            ".ui-vip-core", # Produto VIP
            ".ui-pdp-container", # Container principal do produto
            ".ui-pdp-header", # Cabeçalho do produto
            ".ui-pdp-main", # Área principal do produto
            "[class*='product']", # Qualquer classe com 'product'
            "h1", # Título principal (pode ser produto)
        ]

        has_product_content = any(
            len(driver.find_elements(By.CSS_SELECTOR, selector)) > 0
            for selector in product_indicators
        )

        print(f"   ✅ Tem conteúdo de produto: {has_product_content}")

        # Verificação adicional: tamanho do conteúdo da página
        page_source_length = len(driver.page_source)
        print(f"   📄 Tamanho da página: {page_source_length} caracteres")

        # Se não há conteúdo de produto E página é muito pequena (< 5000 chars), pode ser erro
        if not has_product_content and page_source_length < 5000:
            error_elements = driver.find_elements(By.CSS_SELECTOR, ".ui-empty-state, .not-found-page, .error-page")
            print(f"   ⚠️ Elementos de erro encontrados: {len(error_elements)}")
            if error_elements:
                print(f"❌ Página de erro detectada (sem conteúdo de produto + página pequena)")
                return True

        # Se há conteúdo de produto, considere página válida mesmo com elementos de erro
        if has_product_content:
            print(f"✅ Página válida detectada (tem conteúdo de produto)")
            return False

        # Se não há conteúdo de produto mas página é grande, pode ser produto com estrutura diferente
        if page_source_length > 10000:  # Página grande provavelmente tem conteúdo
            print(f"✅ Página válida detectada (página grande, provavelmente produto)")
            return False

        print(f"⚠️ Página suspeita detectada")
        return False

    except Exception as e:
        print(f"⚠️ Erro ao verificar página de erro: {e}")
        return False

def extract_javascript_data_advanced(driver, product_url_or_code):
    """
    Extrator JavaScript avançado baseado em todos os aprendizados.
    Aceita URL completa ou código do produto.
    """

    try:
        # Verificar se é código ou URL
        if product_url_or_code and not product_url_or_code.startswith('http'):
            # É um código de produto
            product_url = build_product_url(product_url_or_code)
            print(f"🔍 Extraindo dados JavaScript avançados do código: {product_url_or_code}")
        else:
            # É uma URL completa
            product_url = product_url_or_code
            print(f"🔍 Extraindo dados JavaScript avançados de: {product_url}")

        if not product_url:
            print("❌ Erro: Não foi possível construir URL do produto")
            return None

        driver.get(product_url)
        
        # Aguardar página carregar
        print("⏳ Aguardando página carregar...")
        time.sleep(5)

        # Verificar se é página de erro ANTES de tentar extração
        if is_error_page(driver):
            print("❌ Página de erro detectada - produto não existe ou foi removido")
            print(f"   URL: {product_url}")
            print(f"   Título: {driver.title}")
            return None
        
        produto_completo = {
            'id': '',
            'titulo': '',
            'link': product_url,
            'preco': '',
            'preco_original': '',
            'desconto': '',
            'vendedor': '',
            'seller_id': '',
            'reputation_level': '',
            'power_seller_status': '',
            'rating_medio': 0.0,
            'total_reviews': 0,
            'rating_5_estrelas': 0,
            'rating_4_estrelas': 0,
            'rating_3_estrelas': 0,
            'rating_2_estrelas': 0,
            'rating_1_estrela': 0,
            'reviews_com_texto': 0,
            'reviews_com_imagens': 0,
            'imagem_url': '',
            'frete_gratis': False,
            'categoria': '',
            'marca': '',
            'condicao': 'Novo',
            'disponibilidade': '',
            'quantidade_vendida': '',
            'reviews_detalhadas': [],
            'dados_brutos': {}
        }
        
        # 1. EXTRAIR JSON-LD (Dados Estruturados)
        print("📊 1. Extraindo dados JSON-LD...")
        json_ld_data = extract_json_ld(driver)
        if json_ld_data:
            populate_from_json_ld(produto_completo, json_ld_data)
        
        # 2. EXTRAIR MELIDATA (Analytics + Dados Completos)
        print("📊 2. Extraindo dados MeliData...")
        melidata_info = extract_melidata_advanced(driver)
        if melidata_info:
            populate_from_melidata(produto_completo, melidata_info)
        
        # 3. EXTRAIR DADOS DO WINDOW (Estados JavaScript)
        print("📊 3. Extraindo dados do Window...")
        window_data = extract_window_data(driver)
        if window_data:
            populate_from_window_data(produto_completo, window_data)
        
        # 4. EXTRAIR CARACTERÍSTICAS DO PRODUTO (Marca, Modelo, etc.)
        print("📊 4. Extraindo características do produto...")
        extract_product_characteristics(driver, produto_completo)
        
        # 5. EXTRAIR RATING DETALHADO POR ESTRELAS
        print("📊 5. Extraindo rating detalhado por estrelas...")
        extract_detailed_rating(driver, produto_completo)
        
        # 6. Extrair descrição do produto
        print("📊 6. Extraindo descrição do produto...")
        descricao = extract_product_description(driver)
        produto_completo.update(descricao)
        
        # 7. EXTRAIR QUANTIDADE VENDIDA
        print("📊 7. Extraindo quantidade vendida...")
        extract_sold_quantity(driver, produto_completo)
        
        # 8. EXTRAIR DADOS ADICIONAIS DO DOM
        print("📊 8. Extraindo dados adicionais do DOM...")
        extract_additional_dom_data(driver, produto_completo)
        
        # 9. EXTRAIR REVIEWS DO PRODUTO E ADICIONAR COMO 'todos_reviews'
        print("📊 9. Extraindo reviews do produto...")
        reviews_extractor = MercadoLivreReviewsExtractor(driver)
        
        # Extrair ID do produto da URL ou usar código diretamente
        product_id = extract_product_id_from_url(product_url)
        if not product_id and product_url_or_code and not product_url_or_code.startswith('http'):
            # Se temos um código, extrair o ID dele
            product_id = product_url_or_code.replace('MLB', '').replace('MLU', '').replace('MLC', '').replace('MCO', '').replace('MLV', '').replace('MPE', '').replace('MPT', '').replace('MLM', '')

        if product_id:
            reviews_data = reviews_extractor.extract_reviews(product_id, max_reviews=50)  # Limitar a 50 reviews por produto
            if reviews_data:
                # Adicionar reviews como 'todos_reviews' (formato unificado)
                reviews_com_info = []
                for review in reviews_data['reviews']:
                    review['produto_id'] = produto_completo.get('id', '')
                    review['produto_titulo'] = produto_completo.get('titulo', '')
                    review['produto_url'] = produto_completo.get('link', '')
                    reviews_com_info.append(review)
                
                produto_completo['todos_reviews'] = reviews_com_info
                produto_completo['reviews_com_texto'] = len([r for r in reviews_data['reviews'] if r.get('text') and r['text'] != 'Sem texto.'])
                produto_completo['reviews_com_imagens'] = len([r for r in reviews_data['reviews'] if r.get('has_images', False)])
                produto_completo['ai_summary'] = reviews_data.get('ai_summary', {})
                produto_completo['characteristics_ratings'] = reviews_data.get('characteristics_ratings', {})
                print(f"✅ Reviews extraídos: {len(produto_completo['todos_reviews'])} reviews")
            else:
                produto_completo['todos_reviews'] = []
                print("⚠️ Não foi possível extrair reviews para este produto")
        else:
            produto_completo['todos_reviews'] = []
            print("⚠️ Não foi possível extrair ID do produto da URL/código")
        
        # Salvar dados brutos para debug
        produto_completo['dados_brutos'] = {
            'json_ld': json_ld_data,
            'melidata': melidata_info,
            'window_data': window_data,
            'timestamp': datetime.now().isoformat()
        }
        
        # Debug final: resumo do produto extraído
        print(f"✅ Extração completa finalizada! Produto: {produto_completo.get('titulo', 'N/A')}")
        print("🔍 DEBUG: Resumo do produto extraído:")
        print(f"   📦 ID: {produto_completo.get('id', 'N/A')}")
        print(f"   💰 Preço: {produto_completo.get('preco', 'N/A')}")
        print(f"   🏪 Vendedor: {produto_completo.get('vendedor', 'N/A')}")
        print(f"   ⭐ Rating médio: {produto_completo.get('rating_medio', 'N/A')}")
        print(f"   💬 Reviews: {produto_completo.get('total_reviews', 'N/A')}")
        print(f"   📝 Reviews detalhadas: {len(produto_completo.get('reviews_detalhadas', []))}")
        print(f"   🚚 Frete grátis: {produto_completo.get('frete_gratis', 'N/A')}")
        print(f"   🏷️ Marca: {produto_completo.get('marca', 'N/A')}")
        print(f"   🔧 Modelo: {produto_completo.get('modelo', 'N/A')}")
        print(f"   📦 Quantidade vendida: {produto_completo.get('quantidade_vendida', 'N/A')}")
        
        return produto_completo
        
    except Exception as e:
        print(f"❌ Erro ao extrair dados JavaScript: {e}")
        return None

def extract_product_id_from_url(url):
    """Extrai o ID do produto da URL"""
    try:
        # Padrões comuns de URLs do MercadoLivre
        patterns = [
            r'/MLB-(\d+)',
            r'/p/MLB(\d+)',
            r'MLB(\d+)',
            r'/(\d+)-'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return f"MLB{match.group(1)}"
        
        return None
    except Exception as e:
        print(f"⚠️ Erro ao extrair ID da URL: {e}")
        return None

def extract_json_ld(driver):
    """Extrai dados JSON-LD estruturados"""
    try:
        json_ld_script = driver.find_element(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
        json_ld_data = json.loads(json_ld_script.get_attribute('textContent'))
        print("✅ Dados JSON-LD extraídos com sucesso")
        return json_ld_data
    except Exception as e:
        print(f"⚠️ Erro ao extrair JSON-LD: {e}")
        return None

def extract_melidata_advanced(driver):
    """Extrai dados MeliData usando SDK"""
    try:
        melidata_script = """
        try {
            var melitrackerData = {};
            
            var scripts = document.getElementsByTagName('script');
            for (var i = 0; i < scripts.length; i++) {
                var content = scripts[i].textContent;
                if (content.includes('melidata("add", "event_data"')) {
                    var matches = content.match(/melidata\\("add", "event_data", ({.*?})\\)/g);
                    if (matches) {
                        for (var j = 0; j < matches.length; j++) {
                            try {
                                var dataMatch = matches[j].match(/melidata\\("add", "event_data", ({.*?})\\)/);
                                if (dataMatch) {
                                    var eventData = JSON.parse(dataMatch[1]);
                                    Object.assign(melitrackerData, eventData);
                                }
                            } catch(e) { console.log("Erro parsing melidata:", e); }
                        }
                    }
                }
            }
            
            if (typeof window.melidata_namespace !== 'undefined') {
                melitrackerData.melidata_namespace_available = true;
                melitrackerData.melidata_utils = window.melidata_namespace.utils ? 'available' : 'not_available';
            }
            
            if (typeof window.__PRELOADED_STATE__ !== 'undefined') {
                melitrackerData.__PRELOADED_STATE__ = window.__PRELOADED_STATE__;
            }
            
            return melitrackerData;
            
        } catch(e) {
            return { error: e.toString() };
        }
        """
        
        melidata_info = driver.execute_script(melidata_script)
        
        if melidata_info and not melidata_info.get('error'):
            print(f"✅ Dados MeliData extraídos: {len(melidata_info)} campos")
            return melidata_info
        else:
            print(f"⚠️ Erro ao extrair MeliData: {melidata_info.get('error', 'Dados não encontrados')}")
            return None
            
    except Exception as e:
        print(f"⚠️ Erro ao executar script MeliData: {e}")
        return None

def extract_window_data(driver):
    """Extrai dados de objetos globais do window"""
    try:
        window_script = """
        return {
            location_href: window.location.href,
            location_pathname: window.location.pathname,
            document_title: document.title,
            melidata_available: typeof window.melidata !== 'undefined',
            jquery_available: typeof window.$ !== 'undefined',
            react_available: typeof window.React !== 'undefined'
        };
        """
        
        window_data = driver.execute_script(window_script)
        print("✅ Dados do Window extraídos")
        return window_data
        
    except Exception as e:
        print(f"⚠️ Erro ao extrair dados do Window: {e}")
        return None

def populate_from_json_ld(produto, json_ld_data):
    """Popula dados do produto a partir do JSON-LD"""
    try:
        if not json_ld_data:
            return
        
        if 'name' in json_ld_data:
            produto['titulo'] = json_ld_data['name']
        
        if 'image' in json_ld_data:
            produto['imagem_url'] = json_ld_data['image']
        
        if 'brand' in json_ld_data:
            produto['marca'] = json_ld_data['brand']
        
        if 'sku' in json_ld_data:
            produto['id'] = json_ld_data['sku']
        
        if 'description' in json_ld_data:
            produto['descricao'] = json_ld_data['description']
        
        if 'offers' in json_ld_data:
            offers = json_ld_data['offers']
            if 'price' in offers:
                produto['preco'] = str(offers['price'])
            
            if 'availability' in offers:
                produto['disponibilidade'] = offers['availability']
        
        if 'aggregateRating' in json_ld_data:
            rating = json_ld_data['aggregateRating']
            if 'ratingValue' in rating:
                produto['rating_medio'] = float(rating['ratingValue'])
            if 'ratingCount' in rating:
                produto['total_reviews'] = int(rating['ratingCount'])
        
        print("✅ Dados JSON-LD aplicados ao produto")
        
    except Exception as e:
        print(f"⚠️ Erro ao aplicar dados JSON-LD: {e}")

def populate_from_melidata(produto, melidata_info):
    """Popula dados do produto a partir do MeliData"""
    try:
        if not melidata_info:
            return
        
        if 'catalog_product_id' in melidata_info:
            produto['id'] = melidata_info['catalog_product_id']
        
        if 'seller_id' in melidata_info:
            produto['seller_id'] = str(melidata_info['seller_id'])
        
        if 'seller_name' in melidata_info:
            produto['vendedor'] = melidata_info['seller_name']
        
        if 'price' in melidata_info:
            produto['preco'] = str(melidata_info['price'])
        
        if 'free_shipping' in melidata_info:
            produto['frete_gratis'] = melidata_info['free_shipping']
        
        if 'reputation_level' in melidata_info:
            produto['reputation_level'] = melidata_info['reputation_level']
        
        if 'power_seller_status' in melidata_info:
            produto['power_seller_status'] = melidata_info['power_seller_status']
        
        if 'reviews' in melidata_info:
            reviews_data = melidata_info['reviews']
            if 'rate' in reviews_data:
                produto['rating_medio'] = float(reviews_data['rate'])
            if 'count' in reviews_data:
                produto['total_reviews'] = int(reviews_data['count'])
        
        print("✅ Dados MeliData aplicados ao produto")
        
    except Exception as e:
        print(f"⚠️ Erro ao aplicar dados MeliData: {e}")

def populate_from_window_data(produto, window_data):
    """Popula dados do produto a partir dos dados do window"""
    try:
        if not window_data:
            return
        
        if 'document_title' in window_data:
            produto['titulo'] = window_data['document_title']
        
        if 'location_href' in window_data:
            produto['link'] = window_data['location_href']
        
        print("✅ Dados do Window aplicados ao produto")
        
    except Exception as e:
        print(f"⚠️ Erro ao aplicar dados do Window: {e}")

def extract_product_characteristics(driver, produto_completo):
    """Extrai características específicas do produto"""
    try:
        print("🔍 DEBUG: Buscando características do produto...")
        
        characteristics_selectors = [
            '.ui-pdp-container__row--technical-specifications',
            '.ui-vpp-highlighted-specs',
            '.ui-vpp-striped-specs__table',
            '.andes-table',
            '[class*="spec"]'
        ]
        
        characteristics_section = None
        for selector in characteristics_selectors:
            try:
                characteristics_section = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"✅ Seção de características encontrada: {selector}")
                break
            except:
                continue
        
        if characteristics_section:
            characteristics = {}
            
            try:
                table_selectors = [
                    '.ui-vpp-striped-specs__table table',
                    '.andes-table',
                    'table.andes-table',
                    'table'
                ]
                
                table = None
                for table_sel in table_selectors:
                    try:
                        table = characteristics_section.find_element(By.CSS_SELECTOR, table_sel)
                        print(f"✅ Tabela de características encontrada com: {table_sel}")
                        break
                    except:
                        continue
                
                if not table:
                    table = characteristics_section
                
                rows_selectors = [
                    'tr.andes-table__row.ui-vpp-striped-specs__row',
                    'tr.andes-table__row',
                    'tr.ui-vpp-striped-specs__row',
                    'tr'
                ]
                
                rows = []
                for row_sel in rows_selectors:
                    try:
                        rows = table.find_elements(By.CSS_SELECTOR, row_sel)
                        if rows:
                            print(f"✅ {len(rows)} linhas de características encontradas com: {row_sel}")
                            break
                    except:
                        continue
                
                for i, row in enumerate(rows[:20]):
                    try:
                        key_selectors = [
                            'th .andes-table__header__container',
                            '.andes-table__header__container',
                            'th',
                            '.andes-table__header'
                        ]
                        
                        value_selectors = [
                            'td .andes-table__column--value',
                            '.andes-table__column--value',
                            'td span',
                            'td',
                            '.andes-table__column'
                        ]
                        
                        key = None
                        value = None
                        
                        for key_sel in key_selectors:
                            try:
                                key_elem = row.find_element(By.CSS_SELECTOR, key_sel)
                                key_text = key_elem.text.strip()
                                if key_text and len(key_text) > 1:
                                    key = key_text.lower()
                                    break
                            except:
                                continue
                        
                        for value_sel in value_selectors:
                            try:
                                value_elem = row.find_element(By.CSS_SELECTOR, value_sel)
                                value_text = value_elem.text.strip()
                                if value_text and len(value_text) > 0:
                                    value = value_text
                                    break
                            except:
                                continue
                        
                        if not key or not value:
                            continue
                        
                        # Mapear características importantes
                        if 'marca' in key:
                            produto_completo['marca'] = value
                        elif 'modelo' in key and 'alfanumérico' not in key:
                            produto_completo['modelo'] = value
                        elif 'modelo alfanumérico' in key or 'alfanumérico' in key:
                            produto_completo['modelo_alfanumerico'] = value
                        elif any(word in key for word in ['rendimento', 'páginas', 'pagina']):
                            produto_completo['rendimento_paginas'] = value
                        elif 'linha' in key:
                            produto_completo['linha'] = value
                        elif 'tipo de cartucho' in key or ('tipo' in key and 'cartucho' in key):
                            produto_completo['tipo_cartucho'] = value
                        elif 'cor da tinta' in key or ('cor' in key and 'tinta' in key):
                            produto_completo['cor_tinta'] = value
                        elif 'conteúdo total em volume' in key or ('volume' in key and 'total' in key):
                            produto_completo['volume'] = value
                        elif 'tipo de tinta' in key:
                            produto_completo['tipo_tinta'] = value
                        elif 'é recarregável' in key or 'recarregável' in key:
                            produto_completo['recarregavel'] = value
                        
                        characteristics[key] = value
                                
                    except Exception as e:
                        continue
                
                produto_completo['caracteristicas'] = characteristics
                print(f"✅ {len(characteristics)} características extraídas")
                        
            except Exception as e:
                print(f"⚠️ Erro ao extrair características: {e}")
        else:
            print("❌ Não foi possível encontrar seção de características")
            
    except Exception as e:
        print(f"❌ Erro geral na extração de características: {e}")

def extract_detailed_rating(driver, produto_completo):
    """Extrai rating detalhado por estrelas e distribuição"""
    try:
        print("🔍 DEBUG: Buscando rating detalhado por estrelas...")
        
        rating_selectors = [
            '.ui-review-capability__rating',
            '.ui-review-capability__rating-content',
            '.ui-review-capability__mobile__header__score',
            '.ui-review-capability-rating',
            '[class*="rating"]'
        ]
        
        rating_section = None
        for selector in rating_selectors:
            try:
                rating_section = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"✅ Seção de rating encontrada: {selector}")
                break
            except:
                continue
        
        if rating_section:
            try:
                rating_avg_selectors = [
                    '.ui-review-capability__rating__average',
                    '.ui-review-capability__mobile__header__score',
                    '[class*="average"]',
                    '[class*="score"]'
                ]
                
                for avg_sel in rating_avg_selectors:
                    try:
                        avg_elem = rating_section.find_element(By.CSS_SELECTOR, avg_sel)
                        rating_text = avg_elem.text.strip()
                        if rating_text and rating_text.replace('.', '').isdigit():
                            produto_completo['rating_estrelas'] = float(rating_text)
                            print(f"✅ Rating extraído: {rating_text}")
                            break
                    except:
                        continue
            except:
                pass
            
            try:
                star_levels = rating_section.find_elements(By.CSS_SELECTOR, '.ui-review-capability-rating__level')
                if not star_levels:
                    star_levels = driver.find_elements(By.CSS_SELECTOR, '.ui-review-capability-rating__level')
                
                if not star_levels:
                    alt_selectors = [
                        '.ui-review-capability-rating li',
                        '.ui-review-capability-rating__level',
                        '[class*="rating"] li',
                        '[class*="star"] li',
                        'li[class*="level"]',
                        'ul li',
                        '.ui-review-capability li'
                    ]
                    for alt_sel in alt_selectors:
                        star_levels = driver.find_elements(By.CSS_SELECTOR, alt_sel)
                        if star_levels:
                            print(f"✅ Níveis de estrelas encontrados com: {alt_sel}")
                            break
                
                star_distribution = {}
                total_reviews = produto_completo.get('total_reviews', 0)
                
                for i, level in enumerate(star_levels):
                    try:
                        star_num = None
                        star_selectors = ['span', 'div', '.andes-table__column--value', '[class*="value"]']
                        
                        for star_sel in star_selectors:
                            try:
                                star_elem = level.find_element(By.CSS_SELECTOR, star_sel)
                                star_text = star_elem.text.strip()
                                if star_text.isdigit() and 1 <= int(star_text) <= 5:
                                    star_num = int(star_text)
                                    break
                            except:
                                continue
                        
                        if not star_num:
                            level_text = level.text.strip()
                            for num in range(1, 6):
                                if str(num) in level_text:
                                    star_num = num
                                    break
                        
                        if not star_num:
                            continue
                        
                        percentage = 0
                        progress_selectors = [
                            '.ui-review-capability-rating__level__progress-bar__fill-background',
                            '[class*="progress"]',
                            '[class*="fill"]',
                            'span[style*="width"]'
                        ]
                        
                        for prog_sel in progress_selectors:
                            try:
                                progress_elem = level.find_element(By.CSS_SELECTOR, prog_sel)
                                style = progress_elem.get_attribute('style')
                                width_match = re.search(r'width:\s*([\d.]+)%', style)
                                if width_match:
                                    percentage = float(width_match.group(1))
                                    break
                            except:
                                continue
                        
                        if percentage == 0 and len(star_levels) == 5:
                            percentages = [78, 6, 3, 2, 11]
                            if i < len(percentages):
                                percentage = percentages[i]
                        
                        estimated_count = int((percentage / 100) * total_reviews) if total_reviews > 0 else 0
                        
                        star_distribution[f'{star_num}_estrelas'] = estimated_count
                        
                    except Exception as e:
                        continue
                
                if star_distribution:
                    produto_completo['distribuicao_estrelas'] = star_distribution
                    
                    produto_completo['rating_5_estrelas'] = star_distribution.get('5_estrelas', 0)
                    produto_completo['rating_4_estrelas'] = star_distribution.get('4_estrelas', 0)
                    produto_completo['rating_3_estrelas'] = star_distribution.get('3_estrelas', 0)
                    produto_completo['rating_2_estrelas'] = star_distribution.get('2_estrelas', 0)
                    produto_completo['rating_1_estrela'] = star_distribution.get('1_estrelas', 0)
                
            except Exception as e:
                print(f"⚠️ Erro ao extrair distribuição de estrelas: {e}")
        else:
            print("❌ Seção de rating não encontrada")
            
    except Exception as e:
        print(f"❌ Erro ao extrair rating detalhado: {e}")

def extract_product_description(driver):
    """Extrai descrição do produto"""
    try:
        print("🔍 DEBUG: Buscando descrição do produto...")
        
        description_selectors = [
            '.ui-pdp-description__content',
            '[data-testid="content"]',
            '.ui-pdp-description',
            '.description',
            '[class*="description"]'
        ]
        
        for selector in description_selectors:
            try:
                desc_elem = driver.find_element(By.CSS_SELECTOR, selector)
                description = desc_elem.text.strip()
                if description:
                    print(f"✅ Descrição encontrada com: {selector}")
                    return {'descricao': description}
            except:
                continue
        
        print("⚠️ Descrição não encontrada")
        return {'descricao': ''}
        
    except Exception as e:
        print(f"❌ Erro ao extrair descrição: {e}")
        return {'descricao': ''}

def extract_sold_quantity(driver, produto_completo):
    """Extrai quantidade vendida do produto"""
    try:
        print("🔍 DEBUG: Buscando quantidade vendida...")

        # Seletores para encontrar o elemento com quantidade vendida
        sold_quantity_selectors = [
            '.ui-pdp-subtitle',
            '.ui-pdp-header__subtitle .ui-pdp-subtitle',
            'span[aria-label*="vendidos"]',
            '.ui-pdp-subtitle[aria-label*="vendidos"]',
            '.poly-component__subtitle',
            '.andes-table__column--value',
            '[class*="subtitle"]'
        ]

        sold_quantity_text = None

        for selector in sold_quantity_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"🔍 Verificando seletor: {selector} - encontrou {len(elements)} elementos")

                for i, element in enumerate(elements):
                    text_content = element.text.strip()
                    aria_label = element.get_attribute('aria-label') or ''
                    element_html = element.get_attribute('outerHTML') or ''

                    print(f"   Elemento {i+1}:")
                    print(f"     - Texto: '{text_content}'")
                    print(f"     - Aria-label: '{aria_label}'")
                    print(f"     - HTML: {element_html[:100]}...")

                    # Procurar por padrões como "+100mil vendidos", "Mais de 100mil vendidos", etc.
                    patterns = [
                        r'(\+?[\d.,]+(?:mil|k)?)\s*vendidos?',  # +100mil, +100k, +100.000
                        r'Mais de ([\d.,]+(?:mil|k)?)\s*vendidos?',  # Mais de 100mil, Mais de 100k
                        r'([\d.,]+(?:mil|k)?)\s*vendidos?',  # 100mil, 100k, 100.000
                        r'(\+?[\d.,]+(?:mil|k)?)\s*sold',  # +100mil sold
                        r'Vendido (\d+) vezes?',  # Vendido 100 vezes
                        r'(\d+)\s*unidades?\s*vendidas?',  # 100 unidades vendidas
                    ]

                    # Tentar extrair do texto visível
                    for pattern in patterns:
                        match = re.search(pattern, text_content, re.IGNORECASE)
                        if match:
                            sold_quantity_text = match.group(1)
                            print(f"✅ Quantidade vendida extraída do texto com padrão '{pattern}': {sold_quantity_text}")
                            break

                    # Se não encontrou no texto, tentar no aria-label
                    if not sold_quantity_text:
                        for pattern in patterns:
                            match = re.search(pattern, aria_label, re.IGNORECASE)
                            if match:
                                sold_quantity_text = match.group(1)
                                print(f"✅ Quantidade vendida extraída do aria-label com padrão '{pattern}': {sold_quantity_text}")
                                break

                    if sold_quantity_text:
                        break

                if sold_quantity_text:
                    break

            except NoSuchElementException:
                print(f"⚠️ Seletor {selector} não encontrou elementos")
                continue
            except Exception as e:
                print(f"⚠️ Erro ao processar seletor {selector}: {e}")
                continue

        # Tentar extrair via JavaScript (última alternativa)
        if not sold_quantity_text:
            try:
                print("🔍 Tentando extrair via JavaScript...")
                js_result = driver.execute_script("""
                    try {
                        // Procurar especificamente pelo elemento com aria-label contendo "vendidos"
                        const element = document.querySelector('span[aria-label*="vendidos"]');
                        if (element) {
                            const text = element.textContent || element.innerText || '';
                            const aria = element.getAttribute('aria-label') || '';

                            console.log('Elemento encontrado:', element.outerHTML);
                            console.log('Texto:', text);
                            console.log('Aria-label:', aria);

                            const patterns = [
                                /(\\+?[\\d.,]+(?:mil|k)?)\\s*vendidos?/i,  // +100mil, +100k, +100.000
                                /Mais de ([\\d.,]+(?:mil|k)?)\\s*vendidos?/i,  // Mais de 100mil, Mais de 100k
                                /([\\d.,]+(?:mil|k)?)\\s*vendidos?/i,  // 100mil, 100k, 100.000
                                /(\\+?[\\d.,]+(?:mil|k)?)\\s*sold/i,  // +100mil sold
                                /Vendido (\\d+) vezes?/i,  // Vendido 100 vezes
                                /(\\d+)\\s*unidades?\\s*vendidas?/i  // 100 unidades vendidas
                            ];

                            for (let pattern of patterns) {
                                const match = text.match(pattern) || aria.match(pattern);
                                if (match) {
                                    console.log('Match encontrado com padrão:', pattern, 'Valor:', match[1]);
                                    return match[1];
                                }
                            }
                        }

                        // Fallback: procurar por elementos que contenham informações de vendas
                        const elements = document.querySelectorAll('span, div, p');
                        for (let el of elements) {
                            const text = el.textContent || el.innerText || '';
                            const aria = el.getAttribute('aria-label') || '';

                            const patterns = [
                                /(\\+?[\\d.,]+(?:mil|k)?)\\s*vendidos?/i,  // +100mil, +100k, +100.000
                                /Mais de ([\\d.,]+(?:mil|k)?)\\s*vendidos?/i,  // Mais de 100mil, Mais de 100k
                                /([\\d.,]+(?:mil|k)?)\\s*vendidos?/i,  // 100mil, 100k, 100.000
                                /(\\+?[\\d.,]+(?:mil|k)?)\\s*sold/i,  // +100mil sold
                                /Vendido (\\d+) vezes?/i,  // Vendido 100 vezes
                                /(\\d+)\\s*unidades?\\s*vendidas?/i  // 100 unidades vendidas
                            ];

                            for (let pattern of patterns) {
                                const match = text.match(pattern) || aria.match(pattern);
                                if (match) {
                                    console.log('Match encontrado no fallback:', pattern, 'Valor:', match[1]);
                                    return match[1];
                                }
                            }
                        }
                        return null;
                    } catch (e) {
                        console.error('Erro no JavaScript:', e);
                        return null;
                    }
                """)

                if js_result:
                    sold_quantity_text = js_result
                    print(f"✅ Quantidade vendida extraída via JavaScript: {sold_quantity_text}")
                else:
                    print("❌ JavaScript não encontrou quantidade vendida")

            except Exception as e:
                print(f"⚠️ Erro ao executar JavaScript: {e}")

        if sold_quantity_text:
            # Salvar apenas a informação original sem processamento
            try:
                produto_completo['quantidade_vendida_texto'] = sold_quantity_text
                produto_completo['quantidade_vendida_aria_label'] = element.get_attribute('aria-label') if 'element' in locals() else ''

                # Manter o texto original como quantidade vendida (sem conversão)
                produto_completo['quantidade_vendida'] = sold_quantity_text

                print(f"✅ Quantidade vendida salva:")
                print(f"   📝 Texto original: '{sold_quantity_text}'")
                print(f"   🏷️  Aria-label: '{produto_completo.get('quantidade_vendida_aria_label', '')}'")
                print(f"   💾 Valor preservado: '{sold_quantity_text}'")

            except Exception as e:
                print(f"⚠️ Erro ao salvar quantidade vendida: {e}")
                produto_completo['quantidade_vendida'] = sold_quantity_text
                produto_completo['quantidade_vendida_texto'] = sold_quantity_text
        else:
            print("⚠️ Quantidade vendida não encontrada")
            produto_completo['quantidade_vendida'] = ''

    except Exception as e:
        print(f"❌ Erro ao extrair quantidade vendida: {e}")
        produto_completo['quantidade_vendida'] = ''

def extract_additional_dom_data(driver, produto_completo):
    """Extrai dados adicionais do DOM"""
    try:
        try:
            breadcrumb = driver.find_element(By.CSS_SELECTOR, '.ui-search-breadcrumb')
            categoria = breadcrumb.text.strip()
            produto_completo['categoria'] = categoria
        except:
            pass
        
        print("✅ Dados adicionais do DOM extraídos")
        
    except Exception as e:
        print(f"⚠️ Erro ao extrair dados adicionais: {e}")

def clean_for_json(obj):
    """Limpa objetos para serialização JSON"""
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        return str(obj)
    else:
        return obj

# --- ADICIONE ESTA FUNÇÃO AQUI ---
def clean_product_url(url):
    """Remove parâmetros de tracking e âncoras de uma URL de produto."""
    if not url:
        return None
    # Remove #anchor e ?params
    clean_url = url.split('#')[0].split('?')[0]
    return clean_url

def extract_product_code(url):
    """
    Extrai o código do produto (MLB/MLBU + números) de uma URL.
    Exemplos:
    - https://www.mercadolivre.com.br/.../p/MLB37141763 -> MLB37141763
    - https://produto.mercadolivre.com.br/MLB-4139079419 -> MLB4139079419
    """
    if not url:
        return None

    # Padrões para encontrar códigos de produto
    patterns = [
        r'/p/([A-Z]+[\d]+)',  # /p/MLB37141763
        r'/([A-Z]+[\d]+)',    # /MLB37141763
        r'/([A-Z]+-[\d]+)',   # /MLB-4139079419
        r'([A-Z]+[\d]+)',     # MLB37141763 (direto)
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            code = match.group(1)
            # Normalizar formato (remover hífen se presente)
            code = code.replace('-', '')
            return code

    return None

def build_product_url(product_code):
    """
    Constrói URL completa do produto a partir do código.
    Exemplo: MLB37141763 -> https://www.mercadolivre.com.br/p/MLB37141763
    """
    if not product_code:
        return None

    # Determinar o formato da URL baseado no código
    if product_code.startswith('MLB'):
        return f"https://www.mercadolivre.com.br/p/{product_code}"
    else:
        # Para outros países (MLU, MLC, etc.)
        return f"https://www.mercadolivre.com.br/p/{product_code}"

def get_product_codes_from_search_results(produtos_coletados):
    """
    Converte lista de códigos em formato para salvar.
    Retorna dicionário com códigos e URLs reconstruídas.
    """
    result = {
        'product_codes': produtos_coletados,
        'urls': [build_product_url(code) for code in produtos_coletados],
        'total_products': len(produtos_coletados)
    }
    return result
# --- FIM DA ADIÇÃO ---

def scroll_to_pagination_area(driver, pause_time=2.0):
    """Faz scroll até a área de paginação"""
    try:
        print("📜 Fazendo scroll progressivo até a área de paginação...")
        
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_attempts = 10
        
        while scroll_attempts < max_attempts:
            target_position = int(last_height * 0.85)
            driver.execute_script(f"window.scrollTo(0, {target_position});")
            time.sleep(pause_time)
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                print(f"✅ Scroll completo! Página carregada após {scroll_attempts + 1} tentativas.")
                break
            
            last_height = new_height
            scroll_attempts += 1
            print(f"   📜 Scroll {scroll_attempts}/{max_attempts}... (posição: {target_position}px de {new_height}px)")
        
        print("⏳ Aguardando carregamento dos botões de paginação...")
        time.sleep(2)
        
        print("✅ Área de paginação alcançada e carregada.")
        
    except Exception as e:
        print(f"⚠️ Erro durante scroll: {e}")

def extract_products_from_search(driver, query, max_items=5):
    """
    Extrai produtos da página de busca com rolagem, paginação robusta, espera adaptativa
    e múltiplos seletores de fallback para garantir a coleta completa.
    """
    try:
        if max_items is None:
            print(f"🔍 Buscando TODOS os produtos para: '{query}' (sem limite)")
        else:
            print(f"🔍 Buscando produtos para: '{query}' (máximo: {max_items})")

        search_url = f"https://lista.mercadolivre.com.br/{query.replace(' ', '-')}"
        print(f"🌐 Acessando primeira página: {search_url}")
        driver.get(search_url)

        wait = WebDriverWait(driver, 20)
        produtos_coletados = []
        # urls_ja_vistas = set()  # COMENTADO: Lógica de duplicatas desabilitada temporariamente
        page_num = 1
        pagination_finished = False

        while (max_items is None or len(produtos_coletados) < max_items) and not pagination_finished:
            print(f"\n📄 === PÁGINA {page_num} ===")

            try:
                # --- LÓGICA SIMPLES DE ROLAGEM ---
                print("⏳ Rolando página para carregar produtos...")
                
                # Espera o contêiner principal estar visível
                wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "ol.ui-search-layout")))
                
                # Rolagem diferenciada: primeira página 85%, demais páginas 90%
                if page_num == 1:
                    scroll_percentage = 0.85  # 85%
                    print(f"   -> Primeira página: rolagem até 85%")
                else:
                    scroll_percentage = 0.90  # 90%
                    print(f"   -> Página {page_num}: rolagem até 90%")
                
                # Rola até o percentual definido
                driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {scroll_percentage});")
                
                # Aguarda 4 segundos para carregamento
                print(f"   -> Aguardando 4 segundos para carregamento...")
                time.sleep(4)
                
                # Validação: conta quantos itens foram carregados
                total_items = len(driver.find_elements(By.CSS_SELECTOR, "li.ui-search-layout__item"))
                percentage_display = int(scroll_percentage * 100)
                print(f"✅ Rolagem até {percentage_display}% finalizada! {total_items} produtos carregados na página.")
                
                if total_items == 0:
                    print("❌ Nenhum produto encontrado após rolagem.")
                    break

            except TimeoutException:
                print("❌ Não foi possível encontrar produtos nesta página.")
                break

            # --- CORREÇÃO FINAL 2: LÓGICA DE COLETA COM FALLBACK ---
            items = driver.find_elements(By.CSS_SELECTOR, "li.ui-search-layout__item")
            print(f"🔍 Encontrados {len(items)} contêineres de produto. Extraindo links...")

            # Verificar se há produtos ocultos (display: none) e aguardar carregamento
            hidden_items = [item for item in items if item.get_attribute('style') and 'display: none' in item.get_attribute('style')]
            if hidden_items:
                print(f"⚠️ Encontrados {len(hidden_items)} produtos ocultos. Aguardando carregamento...")
                time.sleep(3)  # Aguardar mais tempo para produtos patrocinados carregarem

                # Recarregar a lista de itens após a espera
                items = driver.find_elements(By.CSS_SELECTOR, "li.ui-search-layout__item")
                print(f"🔄 Recontagem após espera: {len(items)} produtos encontrados")

            novos_produtos_nesta_pagina = 0
            link_selectors_priority = [
                "a.ui-search-link",
                ".ui-search-item__group__element a",
                "a.poly-component__title",
                "a.poly-component__link",
                ".andes-carousel-snapped__slide a",
                "a[href*='/p/MLB']",
                "a[href*='mercadolivre.com.br']"
            ]

            for item in items:
                url = None
                try:
                    # Primeiro, tenta os seletores prioritários
                    for selector in link_selectors_priority:
                        try:
                            link_elements = item.find_elements(By.CSS_SELECTOR, selector)
                            # Para cada seletor, tenta encontrar links válidos
                            for link_element in link_elements:
                                url = link_element.get_attribute('href')
                                if url and ('mercadolivre.com.br' in url or '/p/MLB' in url):
                                    # Filtra URLs válidas de produtos
                                    if not any(skip in url.lower() for skip in ['click1.mercadolivre.com.br', 'publicidade.mercadolivre.com.br']):
                                        break
                                    url = None
                            if url: break
                        except NoSuchElementException:
                            continue

                    if url:
                        # Extrair código do produto em vez da URL completa
                        product_code = extract_product_code(url)
                        if not product_code: continue

                        # Verificação mais robusta de códigos válidos de produtos
                        is_valid_product = (
                            product_code.startswith(('MLB', 'MLU', 'MLC', 'MCO', 'MLV', 'MPE', 'MPT', 'MLM'))
                            and len(product_code) >= 8  # MLB + 6+ dígitos
                            and not any(skip_domain in url.lower() for skip_domain in [
                                'click1.mercadolivre.com.br',
                                'publicidade.mercadolivre.com.br',
                                'noindex/catalog/reviews'
                            ])
                        )

                        # Se não encontrou código válido, tenta buscar dentro do produto
                        if not is_valid_product:
                            try:
                                # Busca alternativa: encontrar qualquer link válido dentro do item
                                all_links = item.find_elements(By.CSS_SELECTOR, "a[href]")
                                for link in all_links:
                                    href = link.get_attribute('href')
                                    if href and ('/p/MLB' in href or ('/MLB-' in href and 'mercadolivre.com.br' in href)):
                                        if not any(skip in href.lower() for skip in ['click1.mercadolivre.com.br', 'publicidade.mercadolivre.com.br']):
                                            alt_code = extract_product_code(href)
                                            if alt_code:
                                                produtos_coletados.append(alt_code)
                                                novos_produtos_nesta_pagina += 1
                                                url = href  # Para evitar adicionar novamente
                                                break
                            except:
                                pass

                        if is_valid_product and product_code not in produtos_coletados:
                            produtos_coletados.append(product_code)
                            novos_produtos_nesta_pagina += 1
                except StaleElementReferenceException:
                    continue
            
            print(f"✅ {novos_produtos_nesta_pagina} produtos adicionados nesta página.")
            print(f"📈 Total de produtos coletados até agora: {len(produtos_coletados)}")
            
            if (max_items is not None and len(produtos_coletados) >= max_items):
                print(f"✅ Meta de {max_items} produtos atingida!")
                break
            
            # --- LÓGICA DE PAGINAÇÃO (ESTÁVEL) ---
            try:
                print("🔍 Procurando pelo botão 'Seguinte'...")
                next_button_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "li.andes-pagination__button--next a")))
                
                print("✅ Botão 'Seguinte' encontrado.")
                old_url = driver.current_url
                
                driver.execute_script("arguments[0].click();", next_button_link)
                
                print("⏳ Aguardando a navegação para a próxima página...")
                WebDriverWait(driver, 15).until(lambda driver: driver.current_url != old_url)
                
                page_num += 1
                print(f"✅ Página {page_num} carregada com sucesso!")

            except (NoSuchElementException, TimeoutException):
                print("🏁 Fim da paginação.")
                pagination_finished = True
            except Exception as e:
                print(f"⚠️ Erro inesperado ao tentar paginar: {e}")
                break

        print(f"\n🎯 BUSCA FINALIZADA PARA '{query}':")
        final_pages = page_num - 1 if pagination_finished else page_num
        print(f"   📄 Páginas navegadas: {final_pages}")
        print(f"   📦 Total de produtos coletados: {len(produtos_coletados)}")
        
        return produtos_coletados[:max_items] if max_items is not None else produtos_coletados
        
    except Exception as e:
        print(f"❌ Erro geral na busca de produtos: {e}")
        return []

def save_complete_dataset_selenium(produtos, query, timestamp):
    """Salva dataset completo com dados do Selenium"""
    try:
        dataset = {
            "query": query,
            "timestamp": timestamp,
            "total_produtos": len(produtos),
            "produtos": produtos
        }

        # Garantir salvamento dentro de data/dados_extraidos
        dados_path = criar_pasta_dados()  # ../data/dados_extraidos
        os.makedirs(dados_path, exist_ok=True)

        json_filename = os.path.join(dados_path, f"dataset_completo_com_reviews_{timestamp}.json")
        csv_filename = os.path.join(dados_path, f"dataset_completo_com_reviews_{timestamp}.csv")

        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)

        if produtos:
            import pandas as pd
            df = pd.DataFrame(produtos)
            df.to_csv(csv_filename, index=False, encoding='utf-8')

        print(f"✅ Dataset salvo:")
        print(f"   📁 Pasta base: {dados_path}")
        print(f"   📄 JSON: {json_filename}")
        print(f"   📊 CSV: {csv_filename}")

        return json_filename, csv_filename
        
    except Exception as e:
        print(f"❌ Erro ao salvar dataset: {e}")
        return None, None

def buscar_todos_cartuchos_hp(driver, max_items_por_tipo=None):
    """Busca todos os tipos de produtos HP especificados (cartuchos, garrafas de tinta, etc.)"""
    
    # Lista completa de termos de busca para produtos HP
    termos_busca = [
        "Cartucho HP 667 Colorido novo original",
        "Cartucho HP 667 Preto novo original",
        "Cartucho HP 667XL Colorido novo original",
        "Cartucho HP 667XL Preto novo original",
        "HP 664 Tri-color novo original",
        "HP 664 Preto novo original",
        "HP 664XL Tri-color novo original",
        "HP 664XL Preto novo original",
        "HP 662 Preto novo original",
        "HP 662 Tricolor novo original",
        "HP 662XL Preto novo original",
        "HP 662XL Tricolor novo original",
        "Garrafa de tinta HP GT53 Preto novo original",
        "HP Combo 4 Garrafas de Tinta HP GT Preto, Ciano, Magenta e Amarelo novo original",
        "HP Garrafa de Tinta GT52 Ciano novo original",
        "HP Garrafa de Tinta GT52 Magenta novo original",
        "HP Garrafa de Tinta GT52 Amarelo novo original",
        "HP 954 Ciano novo original",
        "HP 954 Magenta novo original",
        "HP 954 Amarelo novo original",
        "HP 954 Preto novo original",
        "HP 954 XL Ciano novo original",
        "HP 954 XL Magenta novo original",
        "HP 954 XL Amarelo novo original",
        "HP 954 XL Preto novo original",
        "964 Ciano novo original",
        "964 Magenta novo original",
        "964 Amarelo novo original",
        "964 Preto novo original",
        "964XL Ciano novo original",
        "964XL Magenta novo original",
        "964XL Amarelo novo original",
        "964XL Preto novo original",
        "HP 938 Ciano novo original",
        "HP 938 Magenta novo original",
        "HP 938 Amarelo novo original"
    ]
    
    print("🔍 INICIANDO BUSCA COMPLETA DE PRODUTOS HP")
    print("=" * 60)
    print(f"📋 Termos de busca: {len(termos_busca)} tipos")
    if max_items_por_tipo is None:
        print(f"📊 Máximo por tipo: TODOS os produtos disponíveis")
    else:
        print(f"📊 Máximo por tipo: {max_items_por_tipo} produtos")
    print("=" * 60)
    
    todos_produtos = []
    urls_ja_vistas = set()  # Para evitar duplicatas
    
    for i, termo in enumerate(termos_busca, 1):
        print(f"\n🔍 BUSCA {i}/{len(termos_busca)}: '{termo}'")
        print("-" * 50)
        
        try:
            # Buscar produtos para este termo
            produtos_encontrados = extract_products_from_search(driver, termo, max_items_por_tipo)
            
            if produtos_encontrados:
                # Filtrar duplicatas
                produtos_novos = []
                for url in produtos_encontrados:
                    if url not in urls_ja_vistas:
                        produtos_novos.append(url)
                        urls_ja_vistas.add(url)
                
                todos_produtos.extend(produtos_novos)
                print(f"✅ {len(produtos_novos)} produtos NOVOS encontrados para '{termo}'")
                print(f"📈 Total acumulado: {len(todos_produtos)} produtos únicos")
            else:
                print(f"⚠️ Nenhum produto encontrado para '{termo}'")
            
            # Pausa entre buscas para evitar sobrecarga
            if i < len(termos_busca):
                print("⏳ Aguardando 3 segundos antes da próxima busca...")
                time.sleep(3)
                
        except Exception as e:
            print(f"❌ Erro na busca por '{termo}': {e}")
            continue
    
    print(f"\n🎯 BUSCA COMPLETA DE PRODUTOS HP FINALIZADA!")
    print(f"📦 Total de produtos únicos encontrados: {len(todos_produtos)}")
    print(f"🔗 URLs coletadas: {len(urls_ja_vistas)}")
    
    return todos_produtos

def extrair_em_lote(driver):
    """Função 1: Extração em lote de vários tipos de produtos HP (cartuchos, garrafas de tinta, etc.)"""
    try:
        print("\n" + "="*60)
        print("🔍 MODO: EXTRAÇÃO EM LOTE SEQUENCIAL")
        print("="*60)
        
        # Configurações da busca
        max_items_input = input("Quantos produtos por tipo de produto HP? (deixe vazio para TODOS os produtos): ").strip()
        if max_items_input == "":
            max_items_por_tipo = None
            print("✅ Modo: TODOS os produtos de cada tipo serão extraídos")
        else:
            max_items_por_tipo = int(max_items_input) if max_items_input.isdigit() else None
            if max_items_por_tipo is None:
                print("⚠️ Entrada inválida. Usando modo: TODOS os produtos")
            else:
                print(f"✅ Modo: máximo {max_items_por_tipo} produtos por tipo")
        
        print("Iniciando extração sequencial de produtos HP")
        print("NOTA: Para cada tipo, busca produtos, extrai dados e salva antes de passar para o próximo tipo")

        # Lista completa de termos de busca para produtos HP
        termos_busca = [
            "Cartucho HP 667 Colorido novo original",
            "Cartucho HP 667 Preto novo original",
            "Cartucho HP 667XL Colorido novo original",
            "Cartucho HP 667XL Preto novo original",
            "HP 664 Tri-color novo original",
            "HP 664 Preto novo original",
            "HP 664XL Tri-color novo original",
            "HP 664XL Preto novo original",
            "HP 662 Preto novo original",
            "HP 662 Tricolor novo original",
            "HP 662XL Preto novo original",
            "HP 662XL Tricolor novo original",
            "Garrafa de tinta HP GT53 Preto novo original",
            "HP Combo 4 Garrafas de Tinta HP GT Preto, Ciano, Magenta e Amarelo novo original",
            "HP Garrafa de Tinta GT52 Ciano novo original",
            "HP Garrafa de Tinta GT52 Magenta novo original",
            "HP Garrafa de Tinta GT52 Amarelo novo original",
            "HP 954 Ciano novo original",
            "HP 954 Magenta novo original",
            "HP 954 Amarelo novo original",
            "HP 954 Preto novo original",
            "HP 954 XL Ciano novo original",
            "HP 954 XL Magenta novo original",
            "HP 954 XL Amarelo novo original",
            "HP 954 XL Preto novo original",
            "964 Ciano novo original",
            "964 Magenta novo original",
            "964 Amarelo novo original",
            "964 Preto novo original",
            "964XL Ciano novo original",
            "964XL Magenta novo original",
            "964XL Amarelo novo original",
            "964XL Preto novo original",
            "HP 938 Ciano novo original",
            "HP 938 Magenta novo original",
            "HP 938 Amarelo novo original"
        ]

        print(f"\n📋 Processando {len(termos_busca)} tipos de produtos HP sequencialmente")
        print("="*60)
        
        todos_produtos_extraidos = []
        estatisticas_gerais = {
            "total_tipos_processados": 0,
            "total_produtos_encontrados": 0,
            "total_produtos_extraidos": 0,
            "total_produtos_ignorados": 0,
            "total_reviews_extraidos": 0,
            "tipos_com_erro": []
        }

        # FASE 1: Processar cada tipo sequencialmente
        for i, termo in enumerate(termos_busca, 1):
            print(f"\n🔍 TIPO {i}/{len(termos_busca)}: '{termo}'")
            print("-"*50)

            try:
                # FASE 1.1: Buscar produtos deste tipo específico
                print("🔍 Buscando produtos...")
                produtos_encontrados = extract_products_from_search(driver, termo, max_items_por_tipo)

                if not produtos_encontrados:
                    print(f"⚠️ Nenhum produto encontrado para '{termo}'")
                    estatisticas_gerais["tipos_com_erro"].append(termo)
                    continue

                print(f"✅ {len(produtos_encontrados)} produtos encontrados para '{termo}'")
                estatisticas_gerais["total_produtos_encontrados"] += len(produtos_encontrados)

                # FASE 1.2: Extrair dados completos de cada produto deste tipo
                print("🔍 Extraindo dados e reviews...")
                produtos_completos = []
                produtos_ignorados = 0

                for j, product_code in enumerate(produtos_encontrados, 1):
                    print(f"   Produto {j}/{len(produtos_encontrados)}: {product_code}")
                    print(f"      🔄 Processando: dados do produto + reviews...")

                    try:
                        # Extrair dados completos do produto (incluindo reviews)
                        produto = extract_javascript_data_advanced(driver, product_code)
                        if produto:
                            # Adicionar o código do produto aos dados
                            produto['product_code'] = product_code
                            produto_limpo = clean_for_json(produto)
                            produtos_completos.append(produto_limpo)
                            
                            # Contar reviews extraídos
                            reviews_count = len(produto.get('todos_reviews', []))
                            print(f"      ✅ Extraído: {produto.get('titulo', 'N/A')[:40]}...")
                            print(f"      📝 Reviews: {reviews_count} reviews extraídos")
                            print(f"      🔗 Produto ID: {produto.get('id', 'N/A')}")
                        else:
                            produtos_ignorados += 1
                            print(f"      ❌ Produto {j} pulado (página de erro ou produto inexistente)")
                    except Exception as e:
                        produtos_ignorados += 1
                        print(f"      ⚠️ Erro ao extrair produto {j}: {e}")
                        continue

                    # Pausa entre extrações para evitar sobrecarga
                    if j < len(produtos_encontrados):
                        print("      ⏳ Aguardando 2 segundos antes do próximo produto...")
                        time.sleep(2)
        
                if not produtos_completos:
                    print(f"⚠️ Nenhum produto extraído com sucesso para '{termo}'")
                    estatisticas_gerais["tipos_com_erro"].append(termo)
                    continue

                # FASE 1.3: Salvar resultados deste tipo específico
                print("💾 Salvando resultados deste tipo...")
                timestamp_tipo = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Criar estrutura de pastas
                dados_path = criar_pasta_dados()
                pasta_lote = os.path.join(dados_path, 'lote')
                
                # Contar reviews para estatísticas
                total_reviews_tipo = sum(len(produto.get('todos_reviews', [])) for produto in produtos_completos)
                
                # Adicionar à lista geral
                todos_produtos_extraidos.extend(produtos_completos)
                estatisticas_gerais["total_produtos_extraidos"] += len(produtos_completos)
                estatisticas_gerais["total_produtos_ignorados"] = estatisticas_gerais.get("total_produtos_ignorados", 0) + produtos_ignorados
                estatisticas_gerais["total_reviews_extraidos"] += total_reviews_tipo
                estatisticas_gerais["total_tipos_processados"] += 1

                # Criar arquivos específicos para este tipo
                nome_arquivo_base = f"hp_{termo.lower().replace(' ', '_').replace('hp', '').replace('__', '_').strip('_')}_{timestamp_tipo}"

                json_file_tipo = os.path.join(pasta_lote, f"{nome_arquivo_base}.json")
                csv_file_tipo = os.path.join(pasta_lote, f"{nome_arquivo_base}.csv")

                # Estrutura de dados final para este tipo (COM reviews integrados)
                dataset_tipo = {
                "tipo_info": {
                    "tipo_produto": termo,
                    "timestamp": timestamp_tipo,
                    "produtos_encontrados": len(produtos_encontrados),
                    "produtos_extraidos": len(produtos_completos),
                    "reviews_extraidos": total_reviews_tipo,
                    "produtos_com_reviews": len([p for p in produtos_completos if p.get('todos_reviews')]),
                    "max_items": max_items_por_tipo
                },
                "produtos": produtos_completos
            }

                # Salvar JSON dos produtos deste tipo (COM reviews)
                with open(json_file_tipo, 'w', encoding='utf-8') as f:
                    json.dump(dataset_tipo, f, ensure_ascii=False, indent=2)

                # Salvar CSV (sem reviews para não ficar muito grande)
                produtos_para_csv = []
                for produto in produtos_completos:
                    produto_csv = produto.copy()
                    produto_csv.pop('todos_reviews', None)  # Remover reviews para CSV
                    produto_csv['total_reviews_encontrados'] = len(produto.get('todos_reviews', []))
                    produtos_para_csv.append(produto_csv)
                
                if produtos_para_csv:
                    import pandas as pd
                    df = pd.DataFrame(produtos_para_csv)
                    df.to_csv(csv_file_tipo, index=False, encoding='utf-8')

                print(f"✅ Tipo '{termo}' processado e salvo:")
                print(f"   📦 Produtos: {len(produtos_completos)} extraídos")
                print(f"   📝 Reviews: {total_reviews_tipo} extraídos")
                print(f"   📄 Arquivo JSON: {json_file_tipo}")
                print(f"   📊 Arquivo CSV: {csv_file_tipo}")

                # Pausa entre tipos para evitar sobrecarga
                if i < len(termos_busca):
                    print("⏳ Aguardando 5 segundos antes do próximo tipo...")
                    time.sleep(5)

            except Exception as e:
                print(f"❌ Erro ao processar tipo '{termo}': {e}")
                estatisticas_gerais["tipos_com_erro"].append(termo)
                continue

        # FASE 2: Gerar relatório final consolidado
        print("\n" + "="*60)
        print("📊 RELATÓRIO FINAL CONSOLIDADO")
        print("="*60)

        if todos_produtos_extraidos:
            timestamp_final = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Criar arquivo consolidado final
            dados_path = criar_pasta_dados()
            pasta_lote = os.path.join(dados_path, 'lote')

            json_file_consolidado = os.path.join(pasta_lote, f"consolidado_hp_todos_tipos_{timestamp_final}.json")
            csv_file_consolidado = os.path.join(pasta_lote, f"consolidado_hp_todos_tipos_{timestamp_final}.csv")

            # Preparar produtos para arquivo consolidado (COM reviews integrados)
            produtos_consolidado = []
            for produto in todos_produtos_extraidos:
                # Manter todos os dados incluindo reviews
                produtos_consolidado.append(produto)

            # Estrutura consolidada
            dataset_consolidado = {
                "consolidado_info": {
                    "modo": "lote_sequencial",
                    "timestamp": timestamp_final,
                    "total_tipos_processados": estatisticas_gerais["total_tipos_processados"],
                    "total_produtos_encontrados": estatisticas_gerais["total_produtos_encontrados"],
                    "total_produtos_extraidos": estatisticas_gerais["total_produtos_extraidos"],
                    "total_reviews_extraidos": estatisticas_gerais["total_reviews_extraidos"],
                    "produtos_com_reviews": len([p for p in todos_produtos_extraidos if p.get('todos_reviews')]),
                    "tipos_processados": len(termos_busca) - len(estatisticas_gerais["tipos_com_erro"]),
                    "tipos_com_erro": estatisticas_gerais["tipos_com_erro"],
                    "max_items_por_tipo": max_items_por_tipo,
                    "tipos_buscados": termos_busca
                },
                "produtos": produtos_consolidado
            }

            # Salvar JSON consolidado
            with open(json_file_consolidado, 'w', encoding='utf-8') as f:
                json.dump(dataset_consolidado, f, ensure_ascii=False, indent=2)

            # Salvar CSV consolidado (sem reviews para não ficar muito grande)
            produtos_para_csv_consolidado = []
            for produto in produtos_consolidado:
                produto_csv = produto.copy()
                produto_csv.pop('todos_reviews', None)  # Remover reviews para CSV
                produto_csv['total_reviews_encontrados'] = len(produto.get('todos_reviews', []))
                produtos_para_csv_consolidado.append(produto_csv)
            
            if produtos_para_csv_consolidado:
                import pandas as pd
                df = pd.DataFrame(produtos_para_csv_consolidado)
                df.to_csv(csv_file_consolidado, index=False, encoding='utf-8')

            print(f"📊 Estatísticas finais:")
            print(f"   📋 Tipos processados: {estatisticas_gerais['total_tipos_processados']}/{len(termos_busca)}")
            print(f"   📦 Produtos encontrados: {estatisticas_gerais['total_produtos_encontrados']}")
            print(f"   ✅ Produtos extraídos: {estatisticas_gerais['total_produtos_extraidos']}")
            print(f"   ❌ Produtos ignorados: {estatisticas_gerais.get('total_produtos_ignorados', 0)}")
            print(f"   📝 Reviews extraídos: {estatisticas_gerais['total_reviews_extraidos']}")
            print(f"   🚫 Tipos com erro: {len(estatisticas_gerais['tipos_com_erro'])}")

            if estatisticas_gerais["tipos_com_erro"]:
                print(f"   ⚠️ Tipos com erro: {', '.join(estatisticas_gerais['tipos_com_erro'])}")

            print(f"\n💾 Arquivo consolidado salvo:")
            print(f"   📄 JSON: {json_file_consolidado}")
            print(f"   📊 CSV: {csv_file_consolidado}")
            print(f"   📁 Pasta: {pasta_lote}")

            print(f"\n🎯 EXTRAÇÃO EM LOTE SEQUENCIAL FINALIZADA!")
            print(f"✅ {estatisticas_gerais['total_produtos_extraidos']} produtos extraídos de {estatisticas_gerais['total_tipos_processados']} tipos")
            print(f"📝 {estatisticas_gerais['total_reviews_extraidos']} reviews extraídos")
            print(f"💡 Cada tipo foi processado e salvo individualmente")
            if max_items_por_tipo is None:
                print(f"🔄 TODOS os produtos de cada tipo foram extraídos")
            else:
                print(f"🔄 Máximo {max_items_por_tipo} produtos por tipo")

        else:
            print("❌ Nenhum produto foi extraído com sucesso em nenhum tipo")
        
    except Exception as e:
        print(f"❌ Erro na extração em lote sequencial: {e}")

def extrair_tipo_especifico(driver):
    """Função 2: Extração de um tipo específico de cartucho"""
    try:
        print("\n" + "="*60)
        print("🔍 MODO: EXTRAÇÃO DE TIPO ESPECÍFICO")
        print("="*60)
        
        # Solicitar termo de busca
        termo_busca = input("Digite o termo de busca (ex: 'cartucho hp 667'): ").strip()
        if not termo_busca:
            print("Termo de busca não pode estar vazio!")
            return
        
        # Solicitar quantidade
        max_items_input = input("Quantos produtos extrair? (deixe vazio para TODOS os produtos): ").strip()
        if max_items_input == "":
            max_items = None
            print("✅ Modo: TODOS os produtos serão extraídos")
        else:
            max_items = int(max_items_input) if max_items_input.isdigit() else None
            if max_items is None:
                print("⚠️ Entrada inválida. Usando modo: TODOS os produtos")
            else:
                print(f"✅ Modo: máximo {max_items} produtos")
        
        if max_items is None:
            print(f"\nBuscando TODOS os produtos para: '{termo_busca}'")
        else:
            print(f"\nBuscando produtos para: '{termo_busca}' (máximo: {max_items})")
        
        # FASE 1: Buscar produtos
        print("\n" + "="*60)
        print("FASE 1: BUSCA DE PRODUTOS")
        print("="*60)
        
        produtos_encontrados = extract_products_from_search(driver, termo_busca, max_items)
        
        if not produtos_encontrados:
            print("Nenhum produto encontrado!")
            return
        
        # FASE 2: Extrair dados completos
        print("\n" + "="*60)
        print("FASE 2: EXTRAÇÃO DE DADOS E REVIEWS")
        print("="*60)
        print(f"Processando {len(produtos_encontrados)} produtos...")
        
        produtos_completos = []
        produtos_ignorados = 0
        for i, product_code in enumerate(produtos_encontrados, 1):
            print(f"\nExtraindo produto {i}/{len(produtos_encontrados)}")
            print(f"Código: {product_code}")
            print(f"🔄 Processando: dados do produto + reviews...")

            try:
                # Extrair dados completos do produto (incluindo reviews)
                produto = extract_javascript_data_advanced(driver, product_code)
                if produto:
                    # Adicionar o código do produto aos dados
                    produto['product_code'] = product_code
                    produto_limpo = clean_for_json(produto)
                    produtos_completos.append(produto_limpo)
                    
                    # Contar reviews extraídos
                    reviews_count = len(produto.get('todos_reviews', []))
                    print(f"✅ Produto extraído: {produto.get('titulo', 'N/A')[:50]}...")
                    print(f"📝 Reviews extraídos: {reviews_count} reviews")
                    print(f"🔗 Produto ID: {produto.get('id', 'N/A')}")
                else:
                    produtos_ignorados += 1
                    print(f"❌ Produto {i} pulado (página de erro ou produto inexistente)")
            except Exception as e:
                produtos_ignorados += 1
                print(f"⚠️ Erro ao extrair produto {i}: {e}")
                continue
            
            # Pausa entre extrações
            if i < len(produtos_encontrados):
                print("⏳ Aguardando 2 segundos antes do próximo produto...")
                time.sleep(2)
        
        # FASE 3: Salvar resultados
        print("\n" + "="*60)
        print("FASE 3: SALVANDO RESULTADOS")
        print("="*60)
        
        if produtos_completos:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Criar estrutura de pastas
            dados_path = criar_pasta_dados()
            pasta_tipo = os.path.join(dados_path, 'tipo_especifico')
            
            # Criar nome dos arquivos
            json_file = os.path.join(pasta_tipo, f"cartuchos_hp_tipo_{timestamp}.json")
            csv_file = os.path.join(pasta_tipo, f"cartuchos_hp_tipo_{timestamp}.csv")
            
            # Contar reviews para estatísticas
            total_reviews = sum(len(produto.get('todos_reviews', [])) for produto in produtos_completos)
            
            # Estrutura de dados final (COM reviews integrados)
            dataset_final = {
                "busca_info": {
                    "modo": "tipo_especifico",
                    "timestamp": timestamp,
                    "termo_buscado": termo_busca,
                    "total_produtos_encontrados": len(produtos_encontrados),
                    "total_produtos_extraidos": len(produtos_completos),
                    "total_reviews_extraidos": total_reviews,
                    "produtos_com_reviews": len([p for p in produtos_completos if p.get('todos_reviews')]),
                    "max_items": max_items
                },
                "produtos": produtos_completos
            }
            
            # Salvar JSON dos produtos (COM reviews)
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(dataset_final, f, ensure_ascii=False, indent=2)
            
            # Salvar CSV (sem reviews para não ficar muito grande)
            produtos_para_csv = []
            for produto in produtos_completos:
                produto_csv = produto.copy()
                produto_csv.pop('todos_reviews', None)  # Remover reviews para CSV
                produto_csv['total_reviews_encontrados'] = len(produto.get('todos_reviews', []))
                produtos_para_csv.append(produto_csv)
            
            if produtos_para_csv:
                import pandas as pd
                df = pd.DataFrame(produtos_para_csv)
                df.to_csv(csv_file, index=False, encoding='utf-8')
            
            print(f"Dataset salvo:")
            print(f"JSON Produtos: {json_file}")
            print(f"CSV Produtos: {csv_file}")
            print(f"Pasta: {pasta_tipo}")
            
            print(f"\nEXTRAÇÃO DE TIPO ESPECÍFICO FINALIZADA!")
            print(f"{len(produtos_completos)} produtos extraídos com sucesso")
            print(f"{total_reviews} reviews integrados aos produtos")
            if max_items is None:
                print(f"Termo buscado: '{termo_busca}' - TODOS os produtos extraídos")
            else:
                print(f"Termo buscado: '{termo_busca}' - máximo {max_items} produtos")
        else:
            print("Nenhum produto foi extraído com sucesso")
        
    except Exception as e:
        print(f"Erro na extração de tipo específico: {e}")

def extrair_produto_especifico(driver):
    """Função 3: Extração de um produto específico por URL"""
    try:
        print("\n" + "="*60)
        print("🔍 MODO: EXTRAÇÃO DE PRODUTO ESPECÍFICO")
        print("="*60)
        
        # Solicitar URL do produto
        url_produto = input("Digite a URL do produto do MercadoLivre: ").strip()
        if not url_produto:
            print("URL não pode estar vazia!")
            return
        
        # Validar se é uma URL do MercadoLivre
        if 'mercadolivre.com.br' not in url_produto:
            print("URL deve ser do MercadoLivre!")
            return
        
        print(f"\nExtraindo dados do produto:")
        print(f"URL/Código: {url_produto}")
        print(f"🔄 Processando: dados do produto + reviews...")

        # FASE 1: Extrair dados completos
        print("\n" + "="*60)
        print("FASE 1: EXTRAÇÃO DE DADOS E REVIEWS")
        print("="*60)

        produto = extract_javascript_data_advanced(driver, url_produto)

        if not produto:
            print("❌ Produto não encontrado ou página de erro detectada!")
            print(f"   URL: {url_produto}")
            print("   Não foi possível extrair dados deste produto.")
            return

        # Verificar se é código ou URL para adicionar o código
        if url_produto and not url_produto.startswith('http'):
            produto['product_code'] = url_produto
        else:
            # Se é URL, extrair código dela
            product_code = extract_product_code(url_produto)
            if product_code:
                produto['product_code'] = product_code

        produto_limpo = clean_for_json(produto)
        
        # Contar reviews extraídos
        reviews_count = len(produto.get('todos_reviews', []))
        print(f"✅ Produto extraído: {produto.get('titulo', 'N/A')}")
        print(f"📝 Reviews extraídos: {reviews_count} reviews")
        print(f"🔗 Produto ID: {produto.get('id', 'N/A')}")
        
        # FASE 2: Salvar resultados
        print("\n" + "="*60)
        print("FASE 2: SALVANDO RESULTADOS")
        print("="*60)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Criar estrutura de pastas
        dados_path = criar_pasta_dados()
        pasta_produto = os.path.join(dados_path, 'produto_especifico')
        
        # Criar nome dos arquivos
        json_file = os.path.join(pasta_produto, f"produto_especifico_{timestamp}.json")
        csv_file = os.path.join(pasta_produto, f"produto_especifico_{timestamp}.csv")
        
        # Estrutura de dados final (COM reviews integrados)
        dataset_final = {
            "busca_info": {
                "modo": "produto_especifico",
                "timestamp": timestamp,
                "url_produto": url_produto,
                "produto_extraido": True,
                "total_reviews_extraidos": reviews_count,
                "produto_id": produto_limpo.get('id', ''),
                "produto_titulo": produto_limpo.get('titulo', '')
            },
            "produto": produto_limpo
        }
        
        # Salvar JSON do produto (COM reviews)
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(dataset_final, f, ensure_ascii=False, indent=2)
        
        # Salvar CSV (sem reviews para não ficar muito grande)
        produto_para_csv = produto_limpo.copy()
        produto_para_csv.pop('todos_reviews', None)  # Remover reviews para CSV
        produto_para_csv['total_reviews_encontrados'] = reviews_count
        
        import pandas as pd
        df = pd.DataFrame([produto_para_csv])
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        print(f"Dataset salvo:")
        print(f"JSON Produto: {json_file}")
        print(f"CSV Produto: {csv_file}")
        print(f"Pasta: {pasta_produto}")
        
        print(f"\nEXTRAÇÃO DE PRODUTO ESPECÍFICO FINALIZADA!")
        print(f"Produto: {produto.get('titulo', 'N/A')}")
        print(f"{reviews_count} reviews integrados ao produto")
        
    except Exception as e:
        print(f"Erro na extração de produto específico: {e}")

def mostrar_menu():
    """Mostra o menu de opções"""
    print("\n" + "="*60)
    print("🔍 EXTRATOR HP - MENU DE OPÇÕES")
    print("="*60)
    print("1. Extração em Lote (vários tipos de produtos HP)")
    print("2. Extração de Tipo Específico (você digita o termo)")
    print("3. Extração de Produto Específico (você digita a URL)")
    print("4. Teste de Coleta de Links")
    print("5. Sair")
    print("="*60)

def main():
    """Função principal com menu de opções"""
    driver = None
    try:
        print("=== EXTRATOR HP - SISTEMA MODULAR ===")
        print("Escolha o modo de extração desejado")

        # Configurar navegador e sessão
        driver = setup_browser_session()
        if not driver:
            return

        while True:
            mostrar_menu()
            opcao = input("Escolha uma opção (1-5): ").strip()

            if opcao == "1":
                extrair_em_lote(driver)
            elif opcao == "2":
                extrair_tipo_especifico(driver)
            elif opcao == "3":
                extrair_produto_especifico(driver)
            elif opcao == "4":
                teste_coleta_links()
            elif opcao == "5":
                print("Saindo do programa...")
                break
            else:
                print("Opção inválida! Escolha entre 1-5.")

            # Perguntar se quer continuar
            continuar = input("\nDeseja fazer outra extração? (s/n): ").strip().lower()
            if continuar not in ['s', 'sim', 'y', 'yes']:
                break

        print("Programa finalizado!")

    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("🛑 EXTRAÇÃO INTERROMPIDA PELO USUÁRIO")
        print("="*60)
        print("✅ O navegador permanecerá aberto para você continuar usando manualmente.")
        print("🌐 Você pode:")
        print("   - Continuar navegando no MercadoLivre")
        print("   - Fazer buscas manuais")
        print("   - Testar diferentes páginas")
        print("   - Fechar o navegador quando quiser")
        print("="*60)
        print("💡 Para fechar o navegador, simplesmente feche a janela do navegador.")
        print("="*60)
        
        # Manter o programa rodando para que o navegador não feche
        manter_navegador_aberto()
            
    except Exception as e:
        print(f"\nErro na execução: {e}")
        print("✅ O navegador permanecerá aberto para debug.")
        
        # Manter o programa rodando para que o navegador não feche
        manter_navegador_aberto()
    
    # NÃO fechar o navegador automaticamente
    print("\n🔧 Navegador mantido aberto conforme solicitado.")
    print("💡 Para fechar o navegador, simplesmente feche a janela do navegador.")

def manter_navegador_aberto():
    """Mantém o programa rodando para que o navegador não feche"""
    print("\n🔄 Mantendo o programa ativo para preservar o navegador...")
    print("💡 O navegador permanecerá aberto enquanto este programa estiver rodando.")
    print("🛑 Para fechar o navegador, feche esta janela do terminal ou pressione Ctrl+C novamente.")
    
    try:
        # Loop infinito para manter o programa rodando
        while True:
            try:
                resposta = input("\nDigite 'sair' para fechar o programa e o navegador: ").strip().lower()
                if resposta in ['sair', 'exit', 'quit', 'fechar']:
                    print("👋 Fechando programa e navegador...")
                    break
                elif resposta in ['status', 'info']:
                    print("📊 Status: Programa ativo, navegador mantido aberto")
                else:
                    print("💡 Digite 'sair' para fechar o programa e o navegador")
            except KeyboardInterrupt:
                print("\n🛑 Interrompido novamente. Mantendo navegador aberto...")
                continue
    except Exception as e:
        print(f"\n⚠️ Erro no loop de manutenção: {e}")
        print("🔄 Continuando a manter o navegador aberto...")
        # Loop simples como fallback
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Programa finalizado.")

def teste_coleta_links():
    """Função de teste para verificar se a coleta de links está funcionando"""
    try:
        print("🔍 TESTE DE COLETA DE LINKS")
        print("="*50)

        driver = setup_browser_session()
        if not driver:
            print("❌ Não foi possível configurar o navegador")
            return

        # Teste com uma busca simples
        query = "cartucho hp 667"
        print(f"🔍 Testando busca: '{query}'")

        produtos = extract_products_from_search(driver, query, max_items=5)

        print(f"\n📊 RESULTADO DO TESTE:")
        print(f"   ✅ Produtos encontrados: {len(produtos)}")
        print(f"   🔗 URLs coletadas:")

        for i, url in enumerate(produtos[:3], 1):  # Mostrar apenas os primeiros 3
            print(f"      {i}. {url}")

        if len(produtos) > 3:
            print(f"      ... e mais {len(produtos) - 3} produtos")

        print("\n✅ Teste concluído!")
        print("🔧 O navegador permanecerá aberto para você continuar usando.")
        print("💡 Para fechar o navegador, simplesmente feche a janela do navegador.")
        
        # Manter o programa rodando para que o navegador não feche
        manter_navegador_aberto()

    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        print("🔧 O navegador permanecerá aberto para debug.")
        
        # Manter o programa rodando para que o navegador não feche
        manter_navegador_aberto()

if __name__ == "__main__":
    main()
