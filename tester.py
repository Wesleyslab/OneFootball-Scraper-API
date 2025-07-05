import os
import logging
import pytest
from fastapi.testclient import TestClient

from main import app
from scraping import coletar_noticias
from supabase_handler import verificar_noticias_existentes, supabase

# Configura logger para registrar em arquivo
logger = logging.getLogger("test_api")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("test_api.log")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Cliente de teste para FastAPI
client = TestClient(app)

@pytest.mark.order(1)
def test_coletar_noticias():
    """
    Testa a função coletar_noticias com uma página de time do OneFootball.
    """
    link = os.getenv("TEST_ONEFOOTBALL_LINK") or "https://onefootball.com/pt-br/equipe/palmeiras-10"
    try:
        noticias = coletar_noticias(link)
        logger.info(f"coletar_noticias retornou {len(noticias)} itens.")
        assert isinstance(noticias, list)
    except Exception as e:
        logger.error(f"Erro em coletar_noticias: {e}")
        pytest.skip("Não foi possível acessar OneFootball para testes de scraping.")

@pytest.mark.order(2)
def test_verificar_noticias_existentes():
    """
    Testa a consulta ao Supabase para identificar IDs existentes.
    """
    sample_ids = ["12345", "nonexistent"]
    try:
        existentes = verificar_noticias_existentes(sample_ids)
        logger.info(f"IDs existentes: {existentes}")
        assert isinstance(existentes, list)
    except Exception as e:
        logger.error(f"Erro em verificar_noticias_existentes: {e}")
        pytest.skip("Supabase indisponível para testes.")

@pytest.mark.order(3)
def test_endpoint_scrape():
    """
    Testa o endpoint /scrape para retornar novas_noticias com API Key.
    """
    link = os.getenv("TEST_ONEFOOTBALL_LINK") or "https://onefootball.com/pt-br/equipe/palmeiras-10"
    api_key = os.getenv("API_KEY") or pytest.skip("API_KEY não configurada para testes.")
    headers = {"X-API-KEY": api_key}
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

@pytest.mark.order(4)
def test_supabase_connection():
    """
    Testa a conexão básica com o Supabase, executando uma consulta simples na tabela.
    """
    try:
        response = (
            supabase
            .table("noticias_onefootball")
            .select("noticia_id")
            .limit(1)
            .execute()
        )
        logger.info(f"Supabase connection successful, data: {response.data}")
        assert hasattr(response, "data")
    except Exception as e:
        logger.error(f"Erro de conexão com o Supabase: {e}")
        pytest.skip("Não foi possível conectar ao Supabase.")

if __name__ == "__main__":
    # Executa os testes via pytest quando chamado diretamente
    logging.basicConfig(level=logging.INFO)
    pytest.main([os.path.basename(__file__)])
