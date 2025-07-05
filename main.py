import os
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security.api_key import APIKeyHeader
from typing import List

from scraping import coletar_titulos_noticias, coletar_detalhes_noticia
from supabase_handler import verificar_links_existentes

app = FastAPI()

# Configuração da autenticação via API Key
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
def scrape_onefootball(
    link: str = Query(..., description="URL da página do clube no OneFootball")
):
    """
    1) Coleta todos os títulos de notícias (primeira página).
    2) Verifica no Supabase quais links ainda não foram coletados.
    3) Para cada notícia nova, adiciona texto e data ao metadado existente.

    Retorna: {"novas_noticias": [metadado_completo, ...]}
    """
    # Passo 1: metadados iniciais (titulo, link, fonte, noticia_id)
    metadados = coletar_titulos_noticias(link)
    links = [m["link"] for m in metadados]

    # Passo 2: filtra links já processados
    existentes = verificar_links_existentes(links)

    # Passo 3: preenche detalhes nas entradas novas
    resultados: List[dict] = []
    for m in metadados:
        if m["link"] in existentes:
            continue
        try:
            texto, data_pub = coletar_detalhes_noticia(m["link"])
        except Exception:
            # Em caso de falha em detalhes, pula essa notícia
            continue
        m["texto"] = texto
        m["data_publicacao"] = data_pub
        resultados.append(m)

    return {"novas_noticias": resultados}

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}
