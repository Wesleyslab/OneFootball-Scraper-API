import os
from dotenv import load_dotenv
from supabase import create_client

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Obtém as credenciais do Supabase a partir das variáveis de ambiente
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Variáveis de ambiente SUPABASE_URL e SUPABASE_KEY devem estar definidas no .env")

# Inicializa o cliente do Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def verificar_noticias_existentes(lista_ids: list) -> list:
    """
    Verifica quais IDs de notícia já existem na tabela `noticias_onefootball`.

    :param lista_ids: Lista de IDs de notícias a verificar
    :return: Lista de IDs que já estão armazenados no Supabase
    """
    response = (
        supabase
        .table("noticias_onefootball")
        .select("noticia_id")
        .in_("noticia_id", lista_ids)
        .execute()
    )

    # Extrai e retorna apenas os IDs presentes
    return [item["noticia_id"] for item in response.data]


def verificar_titulos_existentes(lista_titulos: list) -> list:
    """
    Verifica quais títulos de notícia já existem na tabela `noticias_onefootball`.

    :param lista_titulos: Lista de títulos a verificar
    :return: Lista de títulos que já estão armazenados no Supabase
    """
    response = (
        supabase
        .table("noticias_onefootball")
        .select("titulo")
        .in_("titulo", lista_titulos)
        .execute()
    )

    return [item["titulo"] for item in response.data]
