import logging
import random
import time
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils import USER_AGENTS

# Configuração de logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def coletar_titulos_noticias(link: str, max_retries: int = 3, backoff_factor: float = 0.5) -> list:
    """
    Coleta metadados das notícias (título, link e fonte) da primeira página de um time no OneFootball.
    :param link: URL da página do clube
    :return: lista de dicts com 'titulo', 'link', 'fonte'
    """
    # Configura sessão com retry
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

    # Seleciona apenas links de notícias na primeira página
    for a in soup.select("a[href*='/noticias/']"):  
        href = a.get('href')
        titulo = a.get_text(strip=True)
        if not titulo or not href:
            continue
        full_link = href if href.startswith('http') else f"https://onefootball.com{href}"
        noticias.append({
            'titulo': titulo,
            'link': full_link,
            'fonte': 'OneFootball'
        })

    logger.info(f"Encontrados {len(noticias)} títulos de notícias em {link}")
    # Remover duplicatas baseadas no título
    unique = {n['titulo']: n for n in noticias}.values()
    return list(unique)


def coletar_detalhes_noticia(link: str, max_retries: int = 3, backoff_factor: float = 0.5) -> tuple:
    """
    Coleta o texto completo e data de publicação de uma notícia.
    :param link: URL da notícia
    :return: (texto, data_publicacao) onde data_publicacao está em formato ISO ou vazio
    """
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

    # Data de publicação via meta ou time
    meta = soup.find('meta', property='article:published_time')
    if meta and meta.has_attr('content'):
        data_pub = meta['content']
    else:
        time_tag = soup.find('time')
        data_pub = time_tag['datetime'] if time_tag and time_tag.has_attr('datetime') else ''

    # Extrai parágrafos do corpo da notícia
    # Tenta selecionar contêiner principal; caso não, pega todos os <p>
    container = soup.find('div', attrs={'data-testid': 'article-body'}) or soup
    paragrafos = [p.get_text(strip=True) for p in container.find_all('p')]
    texto = '\n'.join(paragrafos)

    logger.info(f"Detalhes coletados de {link}: {len(paragrafos)} parágrafos e data {data_pub}")
    return texto, data_pub
