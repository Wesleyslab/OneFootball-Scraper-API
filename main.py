import os
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security.api_key import APIKeyHeader
from typing import List

from scraping import coletar_titulos_noticias, coletar_detalhes_noticia
from supabase_handler import verificar_titulos_existentes

app = FastAPI()

# Autenticação via API Key
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
def scrape_onefootball(link: str = Query(..., description="URL da página do clube no OneFootball")):
    """
    1) Coleta todos os títulos de notícias (primeira página).
    2) Verifica no Supabase quais títulos ainda não foram coletados.
    3) Para cada notícia nova, coleta título, texto da matéria, fonte e data de publicação.
    """
    # Passo 1: metadados (titulo, link, fonte) das notícias
    metadados = coletar_titulos_noticias(link)
    titulos = [m["titulo"] for m in metadados]

    # Passo 2: filtra apenas os não processados
    existentes = verificar_titulos_existentes(titulos)
    novos = [m for m in metadados if m["titulo"] not in existentes]

    # Passo 3: para cada novo, extrai detalhes completos
    resultados: List[dict] = []
    for m in novos:
        texto, data_pub = coletar_detalhes_noticia(m["link"])
        resultados.append({
            "titulo": m["titulo"],
            "texto": texto,
            "fonte": m["fonte"],
            "data_publicacao": data_pub
        })

    return {"novas_noticias": resultados}

@app.get("/health")
def health():
    return {"status": "ok"}
