import logging
import random
import time
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from difflib import SequenceMatcher
from dateutil import parser
import re


from utils import USER_AGENTS

# Configuração de logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def coletar_titulos_noticias(
    link: str,
    max_retries: int = 3,
    backoff_factor: float = 0.5
) -> list:
    """
    Coleta metadados das notícias (titulo, link, fonte e noticia_id) da primeira página de um time no OneFootball.
    Remove duplicatas por noticia_id.

    :param link: URL da página do clube
    :return: lista de dicts com 'titulo', 'link', 'fonte', 'noticia_id'
    """
    # Delay para evitar bloqueios
    time.sleep(random.uniform(1, 2))

    session = requests.Session()
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        response = session.get(link, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Erro ao acessar {link}: {e}")
        raise

    soup = BeautifulSoup(response.text, "html.parser")
    noticias = []

    for a in soup.select("a[href*='/noticias/']"):
        href = a.get('href')
        titulo = a.get_text(strip=True)
        if not titulo or not href:
            continue
        full_link = href if href.startswith('http') else f"https://onefootball.com{href}"
        noticia_id = href.rstrip('/').split('-')[-1]
        noticias.append({
            'titulo': titulo,
            'link': full_link,
            'fonte': 'OneFootball',
            'noticia_id': noticia_id
        })

    logger.info(f"Encontrados {len(noticias)} títulos de notícias em {link}")
    # Deduplica por noticia_id
    unique = {}
    for n in noticias:
        if n['noticia_id'] not in unique:
            unique[n['noticia_id']] = n
    return list(unique.values())


def coletar_detalhes_noticia(link: str) -> tuple:
    time.sleep(random.uniform(1, 2))
    
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        response = session.get(
            link,
            headers=headers,
            timeout=(3.05, 15)  # Timeouts separados
        )
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Erro ao acessar {link}: {e}")
        return "", ""

    soup = BeautifulSoup(response.text, "html.parser")

    # Data de publicação com fallbacks múltiplos
    data_pub = ""
    sources = [
        ('meta', {'property': 'article:published_time'}),
        ('meta', {'property': 'og:article:published_time'}),
        ('meta', {'name': 'publish-date'}),
        ('time', {'datetime': True}),
        ('span', {'class': 'date'})
    ]

    for tag, attrs in sources:
        element = soup.find(tag, attrs)
        if element:
            if element.has_attr('content'):
                data_pub = element['content']
            elif element.has_attr('datetime'):
                data_pub = element['datetime']
            elif element.text.strip():
                data_pub = element.text.strip()
            if data_pub:
                break

    # Padroniza formato da data
    if data_pub:
        try:
            data_pub = parser.parse(data_pub).isoformat()
        except Exception:
            pass

    # Container principal - NOVA ESTRATÉGIA
    container = soup.find('div', class_='XpaLayout_xpaLayoutContainerGridItem__8b0EK')
    
    if not container:
        # Fallback adicional
        container = soup.find('div', class_='XpaLayout_xpaLayoutContainerGridItemComponents__MaerZ')
    
    if not container:
        logger.warning(f"Nenhum container de artigo encontrado para {link}")
        return "", data_pub

    # Remover elementos não-textuais
    for unwanted in container.find_all(['div', 'section', 'hr'], class_=[
        'EmbeddedVideoPlayer_container__OkFxT',
        'ArticleTwitter_container__d_Vqg',
        'HorizontalSeparator_separator__EJ_El',
        'XpaTaboolaPlaceholder_container__S7Qhw',
        'PublisherImprintLink_container__RL6Zd',
        'NativeShare_container__okhFj',
        'CommentsOpenWeb_container__1hvpP'
    ]):
        unwanted.decompose()

    # Extração de parágrafos - ESTRATÉGIA REVISADA
    paragrafos = []
    seen_texts = set()  # Evitar duplicatas
    
    for div in container.find_all('div', class_='ArticleParagraph_articleParagraph__MrxYL'):
        for p in div.find_all('p'):
            txt = p.get_text(strip=True)
            if not txt or txt in seen_texts:
                continue
                
            seen_texts.add(txt)
            
            lower_txt = txt.lower()
            if any(phrase in lower_txt for phrase in [
                'abrir menu', 'siga nosso conteúdo', 'compartilhe',
                'leia mais', 'comentários', 'publicidade', 'veja também:',
                'saiba mais', 'siga-nos', '🔗'
            ]):
                continue
                
            # Filtrar links isolados
            if re.match(r'^https?://\S+$', txt):
                continue
                
            paragrafos.append(txt)

    texto = '\n'.join(paragrafos)
    logger.info(f"Detalhes coletados de {link}: {len(paragrafos)} parágrafos")
    return texto, data_pub