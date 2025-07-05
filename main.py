import os
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security.api_key import APIKeyHeader
import pytest

from scraping import coletar_noticias
from supabase_handler import verificar_noticias_existentes

app = FastAPI()

# Configuração de autenticação via API Key
API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def verify_api_key(api_key: str = Depends(api_key_header)):
    expected = os.getenv("API_KEY")
    if not expected:
        raise HTTPException(status_code=500, detail="API_KEY não configurada")
    if api_key != expected:
        raise HTTPException(status_code=401, detail="Chave de API inválida")
    return True

@app.get("/scrape", dependencies=[Depends(verify_api_key)])
def scrape_onefootball(link: str = Query(..., description="Link da página do time no OneFootball")):
    """
    Executa o scraping de notícias do OneFootball e retorna apenas as novas.
    Requer header X-API-KEY com a chave correta.
    """
    noticias = coletar_noticias(link)
    ids = [n["noticia_id"] for n in noticias]
    ids_existentes = verificar_noticias_existentes(ids)
    novas_noticias = [n for n in noticias if n["noticia_id"] not in ids_existentes]
    return {"novas_noticias": novas_noticias}

@app.get("/health")
def health():
    """Endpoint de health check."""
    return {"status": "ok"}

@app.get("/run-tests", dependencies=[Depends(verify_api_key)])
def run_tests():
    """
    Executa a suíte de testes (tester.py) e retorna status success ou fail.
    Requer header X-API-KEY.
    """
    # Executa pytest na suite de testes
    exit_code = pytest.main(["-q", "--disable-warnings", "--maxfail=1", os.path.join(os.getcwd(), "tester.py")])
    if exit_code == 0:
        return {"status": "success"}
    return {"status": "fail"}
