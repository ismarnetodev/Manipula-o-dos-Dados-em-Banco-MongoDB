import os
import requests

from pymongo import MongoClient
from dotenv import load_dotenv


# =========================
# CONFIGURAÇÃO
# =========================

load_dotenv()

MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017"
)

DB_NAME = os.getenv(
    "DB_NAME",
    "openf1_data"
)

BASE_URL = os.getenv(
    "BASE_URL",
    "https://api.openf1.org/v1"
)

ANO = int(os.getenv("ANO", "2023"))


# =========================
# MONGODB
# =========================

client = MongoClient(MONGODB_URI)

db = client[DB_NAME]

sessions_collection = db["sessions"]
drivers_collection = db["drivers"]
laps_collection = db["laps"]


# =========================
# OPENF1
# =========================

def get_openf1(endpoint, params=None):

    url = f"{BASE_URL}/{endpoint}"

    print(f"\nConsultando: {url}")
    print(f"Parâmetros: {params}")

    response = requests.get(
        url,
        params=params,
        timeout=60
    )

    response.raise_for_status()

    return response.json()


# =========================
# SESSÕES
# =========================

def coletar_sessoes():

    dados = get_openf1(
        "sessions",
        {
            "year": ANO
        }
    )

    if not dados:
        print("Nenhuma sessão encontrada.")
        return []

    print(
        f"\n{len(dados)} sessão(ões) encontrada(s) para {ANO}."
    )

    return dados


# =========================
# SALVAR SESSÃO
# =========================

def salvar_sessao(sessao):

    session_key = sessao.get("session_key")

    if not session_key:
        return

    sessions_collection.update_one(
        {
            "session_key": session_key
        },
        {
            "$set": sessao
        },
        upsert=True
    )


# =========================
# PILOTOS
# =========================

def coletar_drivers(session_key):

    dados = get_openf1(
        "drivers",
        {
            "session_key": session_key
        }
    )

    if not dados:
        print("Nenhum piloto encontrado.")
        return

    drivers_collection.delete_many({
        "session_key": session_key
    })

    drivers_collection.insert_many(dados)

    print(
        f"{len(dados)} piloto(s) inserido(s)."
    )


# =========================
# VOLTAS
# =========================

def coletar_laps(session_key):

    dados = get_openf1(
        "laps",
        {
            "session_key": session_key
        }
    )

    if not dados:
        print("Nenhuma volta encontrada.")
        return

    laps_collection.delete_many({
        "session_key": session_key
    })

    laps_collection.insert_many(dados)

    print(
        f"{len(dados)} volta(s) inserida(s)."
    )


# =========================
# EXECUÇÃO
# =========================

def main():

    print("=" * 60)
    print("OpenF1 Data Collector")
    print("=" * 60)

    print(f"Ano: {ANO}")
    print(f"Banco: {DB_NAME}")
    print(f"API: {BASE_URL}")

    # -------------------------
    # 1. Buscar todas as sessões
    # -------------------------

    print("\n[1/3] Buscando sessões...")

    sessoes = coletar_sessoes()

    if not sessoes:
        print("Nenhuma sessão para processar.")
        return

    # -------------------------
    # 2. Salvar sessões
    # -------------------------

    print("\n[2/3] Salvando sessões...")

    for sessao in sessoes:

        session_key = sessao.get("session_key")
        session_name = sessao.get("session_name")
        session_type = sessao.get("session_type")

        print(
            f"Salvando: "
            f"{session_name} | "
            f"{session_type} | "
            f"session_key={session_key}"
        )

        salvar_sessao(sessao)

    # -------------------------
    # 3. Coletar pilotos e voltas
    # -------------------------

    print("\n[3/3] Coletando pilotos e voltas...")

    for i, sessao in enumerate(sessoes, start=1):

        session_key = sessao.get("session_key")
        session_name = sessao.get("session_name")
        session_type = sessao.get("session_type")

        print("\n" + "=" * 60)
        print(
            f"Sessão {i}/{len(sessoes)}: "
            f"{session_name} | {session_type}"
        )
        print(f"Session Key: {session_key}")
        print("=" * 60)

        try:

            print("\n→ Coletando pilotos...")
            coletar_drivers(session_key)

            print("\n→ Coletando voltas...")
            coletar_laps(session_key)

        except requests.RequestException as erro:

            print(
                f"\nERRO ao coletar sessão "
                f"{session_key}: {erro}"
            )

            continue

    print("\n" + "=" * 60)
    print("COLETA FINALIZADA!")
    print("=" * 60)

    print(
        f"\nSessões no MongoDB: "
        f"{sessions_collection.count_documents({})}"
    )

    print(
        f"Pilotos no MongoDB: "
        f"{drivers_collection.count_documents({})}"
    )

    print(
        f"Voltas no MongoDB: "
        f"{laps_collection.count_documents({})}"
    )


if __name__ == "__main__":
    main()