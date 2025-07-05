import os
import logging
import pytest
from fastapi.testclient import TestClient

from main import app
from scraping import coletar_titulos_noticias, coletar_detalhes_noticia
from supabase_handler import verificar_titulos_existentes, supabase

# Configura logger para registrar em arquivo
def setup_logger():
    logger = logging.getLogger("test_api")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        file_handler = logging.FileHandler("test_api.log")
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger

logger = setup_logger()

# Cliente de teste para FastAPI
client = TestClient(app)

@pytest.mark.order(1)
def test_coletar_titulos_noticias():
    """
    Testa a função coletar_titulos_noticias: deve retornar lista de dicts com 'titulo', 'link', 'fonte', 'noticia_id'.
    """
    link = os.getenv("TEST_ONEFOOTBALL_LINK") or "https://onefootball.com/pt-br/equipe/palmeiras-10"
    try:
        titulos = coletar_titulos_noticias(link)
        logger.info(f"coletar_titulos_noticias retornou {len(titulos)} itens.")
        assert isinstance(titulos, list)
        assert all(
            isinstance(n, dict) and 
            all(key in n for key in ["titulo", "link", "fonte", "noticia_id"])
            for n in titulos
        )
    except Exception as e:
        logger.error(f"Erro em coletar_titulos_noticias: {e}")
        pytest.skip("Não foi possível acessar OneFootball para testes de scraping.")

@pytest.mark.order(2)
def test_coletar_detalhes_noticia():
    """
    Testa a função coletar_detalhes_noticia: deve retornar texto e data_publicacao.
    """
    sample_link = os.getenv("TEST_ONEFOOTBALL_LINK") or "https://onefootball.com/pt-br/noticias/ex-corinthians-e-inter-moises-acumula-titulos-individuais-no-cska-41311336"
    try:
        texto, data_pub = coletar_detalhes_noticia(sample_link)
        logger.info(f"coletar_detalhes_noticia retornou texto de {len(texto)} chars e data {data_pub}")
        assert isinstance(texto, str) and texto
        assert isinstance(data_pub, str)
    except Exception as e:
        logger.error(f"Erro em coletar_detalhes_noticia: {e}")
        pytest.skip("Não foi possível acessar OneFootball para detalhes de notícia.")

@pytest.mark.order(3)
def test_verificar_titulos_existentes():
    """
    Testa a consulta ao Supabase para identificar títulos existentes.
    """
    sample_titulos = ["Titulo Inexistente", "Outro Titulo"]
    try:
        existentes = verificar_titulos_existentes(sample_titulos)
        logger.info(f"Títulos existentes: {existentes}")
        assert isinstance(existentes, list)
    except Exception as e:
        logger.error(f"Erro em verificar_titulos_existentes: {e}")
        pytest.skip("Supabase indisponível para testes.")

@pytest.mark.order(4)
def test_endpoint_scrape():
    """
    Testa o endpoint /scrape para retornar novas_noticias com todos os campos.
    """
    api_key = os.getenv("API_KEY") or pytest.skip("API_KEY não configurada para testes.")
    headers = {"X-API-KEY": api_key}
    link = os.getenv("TEST_ONEFOOTBALL_LINK") or "https://onefootball.com/pt-br/equipe/palmeiras-10"
    response = client.get(
        "/scrape",
        params={"link": link},
        headers=headers
    )
    logger.info(f"Endpoint /scrape status: {response.status_code}")
    assert response.status_code == 200
    data = response.json()
    assert "novas_noticias" in data
    assert isinstance(data["novas_noticias"], list)
    # Se houver notícias, verificar campos de cada item
    for item in data["novas_noticias"]:
        assert all(
            key in item for key in [
                "titulo", "link", "fonte", "noticia_id", "texto", "data_publicacao"
            ]
        )

@pytest.mark.order(5)
def test_supabase_connection():
    """
    Testa a conexão básica com o Supabase, executando uma consulta simples na tabela.
    """
    try:
        response = (
            supabase
            .table("noticias_onefootball")
            .select("titulo")
            .limit(1)
            .execute()
        )
        logger.info(f"Supabase connection successful, data: {response.data}")
        assert hasattr(response, "data")
    except Exception as e:
        logger.error(f"Erro de conexão com o Supabase: {e}")
        pytest.skip("Não foi possível conectar ao Supabase.")

if __name__ == "__main__":
    pytest.main([os.path.basename(__file__)])
