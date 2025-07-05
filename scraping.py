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

def coletar_noticias(
    link: str,
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    min_delay: float = 1,
    max_delay: float = 3
) -> list:
    """
    Coleta notícias do OneFootball de uma página de time.

    Estratégias para reduzir detecção:
    - Randomização de User-Agent e outros headers
    - Delay aleatório entre requisições
    - Retry com backoff exponencial

    :param link: URL da página do time no OneFootball
    :param max_retries: Número máximo de tentativas em caso de erro de conexão
    :param backoff_factor: Fator de backoff para retries exponenciais
    :param min_delay: Delay mínimo aleatório antes da requisição
    :param max_delay: Delay máximo aleatório antes da requisição
    :return: Lista de dicionários com título, fonte, noticia_id e link
    """
    # Delay aleatório antes da requisição
    delay = random.uniform(min_delay, max_delay)
    logger.info(f"Aguardando {delay:.2f}s antes de acessar {link}")
    time.sleep(delay)

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

    # Cabeçalhos randomizados
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://onefootball.com"
    }

    try:
        response = session.get(link, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Erro ao acessar {link}: {e}")
        raise

    soup = BeautifulSoup(response.text, "html.parser")
    noticias = []

    # Seleciona todos os links de notícia
    for a in soup.select("a[href*='/noticias/']"):
        href = a.get('href')
        titulo = a.get_text(strip=True)

        if not titulo or not href:
            continue

        # Extrai ID da notícia a partir do slug
        noticia_id = href.rstrip('/').split('-')[-1]
        # Garante link absoluto
        full_link = href if href.startswith('http') else f"https://onefootball.com{href}"

        noticias.append({
            'titulo': titulo,
            'fonte': 'OneFootball',
            'noticia_id': noticia_id,
            'link': full_link
        })

    logger.info(f"Coletadas {len(noticias)} notícias de {link}")
    return noticias
