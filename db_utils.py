"""
db_utils.py
Módulo responsável por toda a comunicação com o MongoDB.
Mantém a lógica de banco separada da interface pra deixar
as coisas mais organizadas.
"""

import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

load_dotenv()

# variável global pra reutilizar a conexão (evita abrir nova a cada chamada)
_client = None


def get_client():
    """Retorna um MongoClient, criando um novo apenas se necessário."""
    global _client
    if _client is None:
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return _client


def get_db():
    """Retorna o banco de dados configurado no .env."""
    db_name = os.getenv("DB_NAME", "openf1_data")
    return get_client()[db_name]


def test_connection():
    """
    Testa se a conexão com o MongoDB está funcionando.
    Retorna True se ok, False caso contrário.
    """
    try:
        get_client().admin.command("ping")
        return True
    except ConnectionFailure:
        return False


# --- Funções de consulta às coleções ---

def get_available_years():
    """
    Busca todos os anos distintos disponíveis na coleção sessions.
    Usado pra popular o selectbox de ano na sidebar.
    """
    db = get_db()
    anos = db.sessions.distinct("year")
    # ordena decrescente pra mostrar o mais recente primeiro
    return sorted(anos, reverse=True)


def get_sessions_by_year(year: int, session_type: str = "Race"):
    """
    Retorna lista de sessões de um tipo para um ano específico.
    Cada item tem session_key, session_name, country_name e circuit_short_name.
    """
    db = get_db()
    filtro = {
        "year": year,
        "session_type": session_type
    }
    campos = {
        "_id": 0,
        "session_key": 1,
        "session_name": 1,
        "country_name": 1,
        "circuit_short_name": 1,
        "date_start": 1,
    }
    resultado = list(db.sessions.find(filtro, campos).sort("date_start", 1))
    return resultado


def get_session_details(session_key: int):
    """
    Retorna os detalhes completos de uma sessão específica pelo session_key.
    Usado pra exibir as métricas de contexto no painel principal.
    """
    db = get_db()
    sessao = db.sessions.find_one(
        {"session_key": session_key},
        {"_id": 0}
    )
    return sessao


def get_drivers_in_session(session_key: int):
    """
    Busca todos os pilotos que participaram de uma sessão.
    Retorna lista com driver_number, full_name e team_name.
    """
    db = get_db()
    filtro = {"session_key": session_key}
    campos = {
        "_id": 0,
        "driver_number": 1,
        "full_name": 1,
        "team_name": 1,
        "team_colour": 1,
        "name_acronym": 1,
    }
    pilotos = list(db.drivers.find(filtro, campos).sort("full_name", 1))
    return pilotos


def get_laps_for_drivers(session_key: int, driver_numbers: list):
    """
    Busca os dados de volta de um ou mais pilotos em uma sessão.
    Retorna lista de dicionários com lap_number, lap_duration e driver_number.

    Filtra voltas sem duração registrada (pit stops sem tempo, etc.)
    """
    db = get_db()
    filtro = {
        "session_key": session_key,
        "driver_number": {"$in": driver_numbers},
        "lap_duration": {"$ne": None, "$gt": 0}
    }
    campos = {
        "_id": 0,
        "driver_number": 1,
        "lap_number": 1,
        "lap_duration": 1,
        "duration_sector_1": 1,
        "duration_sector_2": 1,
        "duration_sector_3": 1,
        "is_pit_out_lap": 1,
    }
    voltas = list(
        db.laps.find(filtro, campos).sort([("driver_number", 1), ("lap_number", 1)])
    )
    return voltas
