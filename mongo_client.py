from pymongo import MongoClient

MONGO_HOST = "mongodb://localhost:27017"

def exportar(documento: dict):
    client = None
    try:
        client = MongoClient(MONGO_HOST)

        db = client["app_garra"]   
        colecao = db["garra"]

        resultado = colecao.insert_one(documento)

        print(f"[MongoDB] Inserido com id: {resultado.inserted_id}")

    except Exception as e:
        raise RuntimeError(f"Erro ao exportar: {e}")

    finally:
        if client:
            client.close()